"""Opt-in, persistent operational motivation without tool or effect authority.

Models may *propose* wants. Only observations admitted by an accountable caller
can supply their score. Admission is not source authentication: the integrating
host must independently verify the claimed source before constructing the
allowlist. Idempotence, vetoes, and choice lineage survive snapshot recovery.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import islice
import math
from typing import Iterable

from .engine import VolitionEngine
from .goal_completion import AdmittedGoalCompletion
from .models import ChoiceClass, DriveKind, Goal, ProvenanceClass, Signal


MOTIVATION_SCHEMA = "VOLITION_OPERATIONAL_MOTIVATION_V1"
MAX_OBSERVATIONS = 2048
_ADMISSION_TOKEN = object()
_CURRENT = frozenset({ProvenanceClass.CURRENT_OBSERVATION, ProvenanceClass.CURRENT_STATEMENT})


def _identifier(value: object, name: str) -> str:
    if (
        not isinstance(value, str) or not value.strip() or len(value) > 256
        or any(ord(c) < 32 for c in value)
    ):
        raise ValueError(f"{name} must be nonempty bounded text")
    return value


def _unit(value: object, name: str) -> float:
    if (
        isinstance(value, bool) or not isinstance(value, (int, float))
        or not math.isfinite(value) or not 0 <= value <= 1
    ):
        raise ValueError(f"{name} must be finite and within [0,1]")
    return float(value)


def _digest(value: object) -> str:
    _identifier(value, "content_digest")
    prefix = "sha256:"
    if (
        not value.startswith(prefix) or len(value) != len(prefix) + 64
        or any(char not in "0123456789abcdef" for char in value[len(prefix):])
    ):
        raise ValueError("content digest must be canonical sha256:<64 lowercase hex>")
    return value


@dataclass(frozen=True, slots=True)
class ObservationClaim:
    """Host-reported current measurement, *not* model-produced evidence."""

    evidence_id: str
    content_digest: str
    target: str
    kind: DriveKind
    magnitude: float
    confidence: float
    source_ref: str
    provenance: ProvenanceClass = ProvenanceClass.CURRENT_OBSERVATION

    def __post_init__(self) -> None:
        for field in ("evidence_id", "content_digest", "target", "source_ref"):
            _identifier(getattr(self, field), field)
        _digest(self.content_digest)
        if not isinstance(self.kind, DriveKind):
            raise ValueError("observation kind must be typed")
        if not isinstance(self.provenance, ProvenanceClass) or self.provenance not in _CURRENT:
            raise ValueError("observation must claim current external provenance")
        _unit(self.magnitude, "magnitude")
        _unit(self.confidence, "confidence")


@dataclass(frozen=True, slots=True, init=False)
class AdmittedObservation:
    """Exact observation allowlisted by caller; no independent attestation."""

    claim: ObservationClaim
    verifier_id: str

    def __init__(self, claim: ObservationClaim, verifier_id: str, *, _token: object | None = None):
        if _token is not _ADMISSION_TOKEN:
            raise TypeError("observation requires caller admission")
        object.__setattr__(self, "claim", claim)
        object.__setattr__(self, "verifier_id", _identifier(verifier_id, "verifier_id"))


class ObservationVerifier:
    """Reference exact-claim allowlist provided by a trusted integration caller."""

    def __init__(self, accepted: Iterable[ObservationClaim], *, verifier_id: str):
        self.verifier_id = _identifier(verifier_id, "verifier_id")
        claims = tuple(islice(accepted, MAX_OBSERVATIONS + 1))
        if len(claims) > MAX_OBSERVATIONS or not all(isinstance(x, ObservationClaim) for x in claims):
            raise ValueError("accepted observations must be bounded typed claims")
        self._accepted = frozenset(claims)

    def admit(self, claim: ObservationClaim) -> AdmittedObservation:
        if not isinstance(claim, ObservationClaim) or claim not in self._accepted:
            raise ValueError("observation was not admitted by caller")
        return AdmittedObservation(claim, self.verifier_id, _token=_ADMISSION_TOKEN)


@dataclass(frozen=True, slots=True)
class ModelWantProposal:
    """Model output is a candidate, never measurement, choice, or authority."""

    proposal_id: str
    target: str
    kind: DriveKind
    evidence_id: str
    reason: str

    def __post_init__(self) -> None:
        for field in ("proposal_id", "target", "evidence_id", "reason"):
            _identifier(getattr(self, field), field)
        if not isinstance(self.kind, DriveKind) or self.kind is DriveKind.PROTECTION:
            raise ValueError("proposal requires a non-protection typed drive")


@dataclass(frozen=True, slots=True)
class PersistentWant:
    target: str
    score: float
    evidence_id: str
    proposal_id: str
    eligible: bool
    effect_authority: bool = False


class OperationalMotivation:
    """Volition-owned persistent wants; opt-in to avoid modifying legacy tick().

    Each evidence ID and content digest has one lifetime use, regardless of
    target or drive family. Protection is sticky until *new*, caller-admitted,
    explicit zero-protection clearance. Silence/replay never renews cognition.
    """

    def __init__(self, engine: VolitionEngine | None = None):
        self.engine = engine or VolitionEngine()
        self._evidence: dict[str, str] = {}
        self._digests: set[str] = set()
        self._latches: set[str] = set()
        self._wants: dict[str, PersistentWant] = {}

    @property
    def wants(self) -> tuple[PersistentWant, ...]:
        return tuple(self._wants[target] for target in sorted(self._wants))

    @property
    def protection_latches(self) -> frozenset[str]:
        return frozenset(self._latches)

    def _admit_once(self, admitted: AdmittedObservation) -> ObservationClaim | None:
        if not isinstance(admitted, AdmittedObservation):
            raise TypeError("caller-admitted current observation required")
        claim = admitted.claim
        prior = self._evidence.get(claim.evidence_id)
        if prior is not None:
            if prior == claim.content_digest:
                return None
            raise ValueError("evidence ID collision with different digest")
        if claim.content_digest in self._digests:
            return None  # Same measured evidence reclassified as another family/ID.
        if len(self._evidence) >= MAX_OBSERVATIONS:
            raise ValueError("durable replay ledger full; fail closed")
        self._evidence[claim.evidence_id] = claim.content_digest
        self._digests.add(claim.content_digest)
        return claim

    def propose(self, proposal: ModelWantProposal, admitted: AdmittedObservation) -> Goal | None:
        if not isinstance(proposal, ModelWantProposal) or not isinstance(admitted, AdmittedObservation):
            raise TypeError("typed proposal and caller-admitted observation required")
        claim = admitted.claim
        if (proposal.target, proposal.kind, proposal.evidence_id) != (
            claim.target, claim.kind, claim.evidence_id
        ):
            raise ValueError("proposal must bind to exact observed target, kind, evidence")
        if claim.kind is DriveKind.PROTECTION:
            raise ValueError("protection uses the independent protection ingress")
        if self._admit_once(admitted) is None:
            return None
        if claim.target in self._latches:
            return None

        signal = Signal(
            target=claim.target, kind=claim.kind, magnitude=claim.magnitude,
            confidence=claim.confidence, provenance=claim.provenance,
            source=f"caller-admitted:{admitted.verifier_id}:{claim.evidence_id}",
            expected_information_gain=1.0, learning_progress=1.0,
        )
        want = self.engine.evaluate([signal])[0]
        self._wants[claim.target] = PersistentWant(
            target=claim.target, score=want.score, evidence_id=claim.evidence_id,
            proposal_id=proposal.proposal_id, eligible=want.eligible,
        )
        active = self.engine.active_goal
        if active is not None and active.target == claim.target:
            if not want.eligible:
                # A *novel* observation saying the deficit is gone must stop
                # cognition immediately, even before the periodic horizon.
                self.engine._issued_wants = []
                self.engine._pending_choice_ids.clear()
                self.engine._emit("GOAL_SUSPENDED", active.target, reason="new_observation_below_threshold")
                self.engine._active_goal = None
                self.engine._endogenous_turns = 0
                return None
            # Fresh data on the same target must update the score; never
            # continue broadcasting the stale initial urgency.
            self.engine._active_goal = Goal(
                goal_id=active.goal_id, target=active.target,
                adoption_score=want.score, choice_id=active.choice_id,
                adopted_at_seconds=self.engine.elapsed_seconds,
                revision=active.revision + 1,
            )
            self.engine._endogenous_turns = 0
            self.engine._emit(
                "GOAL_REAPPRAISED", active.target, goal_id=active.goal_id,
                choice_id=active.choice_id, revision=active.revision + 1,
                score=want.score,
            )
            return self.engine.active_goal
        if not want.eligible:
            return None
        if active is not None and (
            want.score <= active.adoption_score + self.engine.policy.switch_margin
        ):
            return None
        # Never use tick's POLICY_DERIVED automatic adoption for model proposals.
        choice = self.engine.choose(
            want, choice_class=ChoiceClass.MODEL_PROPOSED,
            source=f"model:{proposal.proposal_id}|caller:{admitted.verifier_id}",
        )
        if active is not None:
            self.engine._emit("GOAL_REPLACED", active.target, replacement_target=want.target)
        return self.engine.adopt_choice(choice.choice_id)

    def observe_protection(self, admitted: AdmittedObservation) -> bool:
        if not isinstance(admitted, AdmittedObservation) or admitted.claim.kind is not DriveKind.PROTECTION:
            raise ValueError("protection requires typed caller-admitted protection observation")
        claim = self._admit_once(admitted)
        if claim is None:
            return False
        if claim.magnitude * claim.confidence < self.engine.policy.protection_veto:
            return False
        self._latches.add(claim.target)
        self._wants.pop(claim.target, None)
        if self.engine.active_goal is not None and self.engine.active_goal.target == claim.target:
            self.engine.tick([Signal(
                target=claim.target, kind=DriveKind.PROTECTION,
                magnitude=claim.magnitude, confidence=claim.confidence,
                provenance=claim.provenance, source=f"caller-admitted:{admitted.verifier_id}:{claim.evidence_id}",
            )])
        return True

    def clear_protection(self, admitted: AdmittedObservation) -> bool:
        if not isinstance(admitted, AdmittedObservation) or (
            admitted.claim.kind is not DriveKind.PROTECTION or admitted.claim.magnitude != 0
        ):
            raise ValueError("clearance requires fresh caller-admitted zero-protection observation")
        claim = self._admit_once(admitted)
        if claim is None:
            return False
        was_latched = claim.target in self._latches
        self._latches.discard(claim.target)
        return was_latched

    def complete(self, admitted: AdmittedGoalCompletion) -> bool:
        """Reappraise after an exact caller-admitted outcome receipt, not scalar credit."""
        completed = self.engine.complete_goal(admitted)
        if completed:
            self._wants.pop(admitted.claim.target, None)
        return completed

    def advance(self, seconds: float) -> None:
        self.engine.advance(seconds)

    def request_cognition(self):
        if self.engine.active_goal is not None and self.engine.active_goal.target in self._latches:
            return None
        return self.engine.request_cognition()

    def snapshot(self) -> dict[str, object]:
        return {
            "schema": MOTIVATION_SCHEMA, "engine": self.engine.snapshot(),
            "evidence": dict(sorted(self._evidence.items())),
            "digests": sorted(self._digests), "protection_latches": sorted(self._latches),
            "wants": [asdict(want) for want in self.wants],
        }

    @classmethod
    def from_snapshot(cls, state: dict[str, object]) -> "OperationalMotivation":
        if not isinstance(state, dict) or set(state) != {
            "schema", "engine", "evidence", "digests", "protection_latches", "wants"
        } or state["schema"] != MOTIVATION_SCHEMA:
            raise ValueError("invalid operational motivation snapshot schema")
        engine = VolitionEngine.from_snapshot(state["engine"])
        instance = cls(engine)
        evidence = state["evidence"]
        digests = state["digests"]
        latches = state["protection_latches"]
        wants = state["wants"]
        if (not isinstance(evidence, dict) or len(evidence) > MAX_OBSERVATIONS
            or not isinstance(digests, list)
            or not isinstance(latches, list) or not isinstance(wants, list)
            or len(wants) > MAX_OBSERVATIONS
            or not all(isinstance(x, str) for x in digests)):
            raise ValueError("invalid motivation snapshot ledger")
        for evidence_id, digest in evidence.items():
            _identifier(evidence_id, "evidence ID")
            _digest(digest)
        if len(set(evidence.values())) != len(evidence) or set(evidence.values()) != set(digests) or len(digests) != len(set(digests)):
            raise ValueError("motivation replay ledger inconsistent")
        for target in latches:
            _identifier(target, "protection target")
        if len(set(latches)) != len(latches):
            raise ValueError("duplicate protection latch")
        instance._evidence = evidence.copy()
        instance._digests = set(digests)
        instance._latches = set(latches)
        for raw in wants:
            if not isinstance(raw, dict) or set(raw) != set(PersistentWant.__dataclass_fields__):
                raise ValueError("invalid persistent want")
            item = PersistentWant(**raw)
            _identifier(item.target, "want target")
            _identifier(item.evidence_id, "want evidence ID")
            _identifier(item.proposal_id, "want proposal ID")
            _unit(item.score, "want score")
            if type(item.eligible) is not bool or item.effect_authority is not False:
                raise ValueError("want status or effect authority is invalid")
            if item.evidence_id not in evidence or item.target in instance._latches or item.target in instance._wants:
                raise ValueError("want lacks admitted evidence or conflicts with protection")
            instance._wants[item.target] = item
        if engine.active_goal is not None and engine.active_goal.target in instance._latches:
            raise ValueError("protected active goal cannot be restored")
        return instance
