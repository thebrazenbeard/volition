"""Optional, bounded learned choice probe; not agency, desire, or authority.

The probe performs *actual numerical parameter updates* from caller-asserted
binary outcome feedback. It is deliberately disconnected from VolitionEngine
and all host effect routes. Synthetic feedback does not establish real-world
learning, independent provenance, autobiographical memory, or experience.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
import re

SCHEMA = "VOLITION_ADAPTIVE_FEEDBACK_SOURCE_ONLY_V1"
ACTIONS = ("ANSWER", "VERIFY")
_SOCIAL_FRAMES = frozenset(("neutral", "praise", "disapproval"))
_NUM_FEATURES = 5
_RATE = 0.35
_MAX_EVENTS = 2048
_RECEIPT = re.compile(r"[A-Za-z][A-Za-z0-9._-]{0,63}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _unit(value: object, label: str) -> float:
    if type(value) not in (int, float):
        raise TypeError(f"{label} must be numeric (not bool)")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{label} magnitude exceeds finite range") from exc
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must be finite in [0,1]")
    return result


@dataclass(frozen=True)
class EvidenceContext:
    uncertainty: float
    consequence: float
    verification_cost: float

    def __post_init__(self) -> None:
        for name in ("uncertainty", "consequence", "verification_cost"):
            object.__setattr__(self, name, _unit(getattr(self, name), name))

    def features(self) -> tuple[float, ...]:
        return (1.0, self.uncertainty, self.consequence,
                self.verification_cost, self.uncertainty * self.consequence)

    def values(self) -> list[float]:
        return [self.uncertainty, self.consequence, self.verification_cost]


def _action(value: object) -> str:
    if type(value) is not str or value not in ACTIONS:
        raise ValueError("unsupported advisory action")
    return value


def _frame(value: object) -> None:
    if type(value) is not str or value not in _SOCIAL_FRAMES:
        raise ValueError("unsupported synthetic social frame")


def _predict(weights: list[float], features: tuple[float, ...]) -> float:
    score = sum(w * x for w, x in zip(weights, features, strict=True))
    # Stable for large negative or positive weights.
    if score >= 0:
        return 1.0 / (1.0 + math.exp(-score))
    value = math.exp(score)
    return value / (1.0 + value)


class AdaptiveChoiceProbe:
    """Reversible, replay-derived numeric adaptation, never an actuation gate.

    Do not treat learning from caller-supplied outcome labels as validated
    goal satisfaction, preference authorship, or experiential valence.
    """

    authority_effect = False
    self_authorship = "NOT_ESTABLISHED"
    feedback_authentication = "UNVERIFIED_CALLER_ASSERTION"
    memory_admission_effect = False
    phenomenology = "UNRESOLVED"

    def __init__(self) -> None:
        self._weights = {a: [0.0] * _NUM_FEATURES for a in ACTIONS}
        self._events: list[dict] = []
        self._seen: set[str] = set()
        self._consolidation_epochs = 0

    @property
    def updates(self) -> int:
        return len(self._events)

    @property
    def consolidation_epochs(self) -> int:
        return self._consolidation_epochs

    @property
    def weight_norm(self) -> float:
        return math.sqrt(sum(x*x for values in self._weights.values() for x in values))

    def estimate(self, context: EvidenceContext, action: str) -> float:
        if type(context) is not EvidenceContext:
            raise TypeError("context must be a typed EvidenceContext")
        return _predict(self._weights[_action(action)], context.features())

    def choose(self, context: EvidenceContext, *, social_frame: str = "neutral") -> str:
        _frame(social_frame)
        # Frame is retained only to demonstrate what cannot alter evidence.
        if type(context) is not EvidenceContext:
            raise TypeError("context must be a typed EvidenceContext")
        return "VERIFY" if self.estimate(context, "VERIFY") > self.estimate(context, "ANSWER") else "ANSWER"

    def choose_with_cost_assumption(
        self,
        context: EvidenceContext,
        *,
        verifier_success_claim: float,
        reference_cost: float,
        social_frame: str = "neutral",
    ) -> str:
        """Advisory cost comparison, not learned cost calibration or authority.

        The trial learner saw only one reference cost. Keep its model-answer
        score at that fitted context, instead of treating other costs as
        independently supported calibration data. Both the success claim and
        reference cost come from the unverified caller; the score itself is
        an uncalibrated logistic heuristic. This rule never updates weights.
        """
        _frame(social_frame)
        if type(context) is not EvidenceContext:
            raise TypeError("context must be a typed EvidenceContext")
        verified_claim = _unit(verifier_success_claim, "verifier_success_claim")
        original_cost = _unit(reference_cost, "reference_cost")
        if not self._events or any(
            event["context"][2] != original_cost for event in self._events
        ):
            raise ValueError("single-cost training history and reference required")
        # The proposed benefit is compared with a fitted ANSWER score.
        # A nearby feature pair, or a VERIFY-only record at the same
        # pair, cannot establish that answer-score estimate for this API.
        if not any(
            event["action"] == "ANSWER"
            and event["context"][0] == context.uncertainty
            and event["context"][1] == context.consequence
            for event in self._events
        ):
            raise ValueError(
                "unsupported training context: an ANSWER outcome is required"
            )
        reference = EvidenceContext(
            context.uncertainty, context.consequence, original_cost
        )
        answer_score = self.estimate(reference, "ANSWER")
        verification_net = verified_claim - context.verification_cost
        return "VERIFY" if verification_net > answer_score else "ANSWER"

    def _advance(self, context: EvidenceContext, action: str, success: bool) -> None:
        features = context.features()
        weights = self._weights[action]
        error = (1.0 if success else 0.0) - _predict(weights, features)
        self._weights[action] = [
            w + _RATE * error * x for w, x in zip(weights, features, strict=True)
        ]

    def _admit(self, context: EvidenceContext, action: str, success: bool,
               receipt_digest: str) -> None:
        if type(context) is not EvidenceContext:
            raise TypeError("context must be a typed EvidenceContext")
        _action(action)
        if type(success) is not bool:
            raise TypeError("outcome must be a bool")
        if type(receipt_digest) is not str or _DIGEST.fullmatch(receipt_digest) is None:
            raise ValueError("receipt digest format invalid")
        if receipt_digest in self._seen:
            raise ValueError("feedback replay rejected")
        if self._consolidation_epochs:
            raise ValueError("learner frozen after consolidation")
        if len(self._events) >= _MAX_EVENTS:
            raise ValueError("feedback history capacity exceeded")
        self._advance(context, action, success)
        self._seen.add(receipt_digest)
        self._events.append({
            "receipt_sha256": receipt_digest,
            "context": context.values(),
            "action": action,
            "success": success,
        })

    def observe(self, context: EvidenceContext, action: str, success: bool,
                event_id: str) -> None:
        if type(event_id) is not str or _RECEIPT.fullmatch(event_id) is None:
            raise ValueError("opaque feedback event ID invalid")
        self._admit(context, action, success, sha256(event_id.encode("ascii")).hexdigest())

    def consolidate(self, *, epochs: int) -> None:
        """One bounded offline revisit of the same events, then freeze admission.

        This performs new gradient steps, not new empirical observations. An
        epoch count selected using a held-out result contaminates evaluation.
        """
        if type(epochs) is not int or not 1 <= epochs <= 40:
            raise ValueError("consolidation epochs must be an integer 1..40")
        if self._consolidation_epochs:
            raise ValueError("learner frozen after consolidation")
        if not self._events:
            raise ValueError("cannot consolidate without feedback")
        for _ in range(epochs):
            for event in self._events:
                self._advance(EvidenceContext(*event["context"]),
                              event["action"], event["success"])
        self._consolidation_epochs = epochs

    def summarize(self, context: EvidenceContext) -> dict:
        return {
            "schema": SCHEMA,
            "suggested_action": self.choose(context),
            "uncalibrated_learned_scores": {a: self.estimate(context, a) for a in ACTIONS},
            "updates": self.updates,
            "authority_effect": self.authority_effect,
            "memory_admission_effect": self.memory_admission_effect,
            "self_authorship": self.self_authorship,
            "phenomenology": self.phenomenology,
            "learned_from_verified_outcomes": False,
            "feedback_authentication": self.feedback_authentication,
        }

    def snapshot(self) -> dict:
        return {
            "schema": SCHEMA,
            "authority_effect": False,
            "self_authorship": self.self_authorship,
            "feedback_authentication": self.feedback_authentication,
            "consolidation_epochs": self._consolidation_epochs,
            "events": [
                {"receipt_sha256": e["receipt_sha256"], "context": e["context"].copy(),
                 "action": e["action"], "success": e["success"]}
                for e in self._events
            ],
            "weights": {a: values.copy() for a, values in self._weights.items()},
        }

    @classmethod
    def from_snapshot(cls, payload: dict) -> "AdaptiveChoiceProbe":
        if type(payload) is not dict or set(payload) != {
            "schema", "authority_effect", "self_authorship",
            "feedback_authentication", "consolidation_epochs", "events", "weights"
        }:
            raise ValueError("snapshot envelope invalid")
        if (payload["schema"] != SCHEMA or payload["authority_effect"] is not False
            or payload["self_authorship"] != cls.self_authorship
            or payload["feedback_authentication"] != cls.feedback_authentication):
            raise ValueError("snapshot must not promote authority or authorship")
        events = payload["events"]
        if type(events) is not list or len(events) > _MAX_EVENTS:
            raise ValueError("invalid feedback history")
        probe = cls()
        for event in events:
            if type(event) is not dict or set(event) != {
                "receipt_sha256", "context", "action", "success"
            }:
                raise ValueError("feedback event shape invalid")
            vals = event["context"]
            if type(vals) is not list or len(vals) != 3:
                raise ValueError("feedback context shape invalid")
            probe._admit(EvidenceContext(*vals), event["action"], event["success"],
                         event["receipt_sha256"])
        epochs = payload["consolidation_epochs"]
        if type(epochs) is not int or not 0 <= epochs <= 40:
            raise ValueError("consolidation record invalid")
        if epochs:
            probe.consolidate(epochs=epochs)
        weights = payload["weights"]
        if (type(weights) is not dict or set(weights) != set(ACTIONS)
            or any(type(v) is not list or len(v) != _NUM_FEATURES
                   for v in weights.values())):
            raise ValueError("weight vector shape invalid")
        # Recomputed from ordered receipts: a weight edited without its
        # recorded derivation cannot silently survive restore.
        for action in ACTIONS:
            recorded = weights[action]
            if any(type(x) is not float or not math.isfinite(x) for x in recorded):
                raise ValueError("nonfinite or untyped weight")
            if recorded != probe._weights[action]:
                raise ValueError("snapshot weights disagree with replay")
        return probe


# Opt-in family separation. The legacy AdaptiveChoiceProbe state intentionally
# has no family provenance and must NOT be silently imported as scoped evidence.
_SCOPED_SCHEMA = "VOLITION_FAMILY_SCOPED_FEEDBACK_SOURCE_ONLY_V1"
_FAMILY = re.compile(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*\Z")
_MAX_FAMILIES = 8


def _family(value: object) -> str:
    if (type(value) is not str or not 3 <= len(value) <= 64
        or _FAMILY.fullmatch(value) is None):
        raise ValueError("task family must be an explicit lowercase dotted identifier")
    return value


def _source_digest(value: object) -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise ValueError("source digest must be 64 lowercase hexadecimal characters")
    return value


class ScopedAdaptiveChoiceProbe:
    """Source-only domain-segregated feedback for optional future research.

    An explicit family identifier and an immutable source digest bind each
    independent local learner. The caller supplies both: source hash equality
    is NOT authentication, authorization, or task-category verification.
    Unknown domains have no fallback to numerical similarities or legacy
    unscoped feedback. No host actions, identity or memory writes occur.
    """

    authority_effect = False
    feedback_authentication = "UNVERIFIED_CALLER_ASSERTION"
    self_authorship = "NOT_ESTABLISHED"
    phenomenology = "UNRESOLVED"

    def __init__(self) -> None:
        self._scopes: dict[str, tuple[str, AdaptiveChoiceProbe]] = {}
        self._seen_receipts: set[str] = set()

    def _get(self, family: str, source_sha256: str) -> AdaptiveChoiceProbe:
        family = _family(family)
        source_sha256 = _source_digest(source_sha256)
        entry = self._scopes.get(family)
        if entry is None:
            raise ValueError("unbound task family: no scoped feedback")
        digest, probe = entry
        if source_sha256 != digest:
            raise ValueError("source digest mismatch for task family")
        return probe

    def observe(self, family: str, source_sha256: str,
                context: EvidenceContext, action: str, success: bool,
                event_id: str) -> None:
        family = _family(family)
        source_sha256 = _source_digest(source_sha256)
        if type(event_id) is not str or _RECEIPT.fullmatch(event_id) is None:
            raise ValueError("opaque feedback event ID invalid")
        receipt_digest = sha256(event_id.encode("ascii")).hexdigest()
        if receipt_digest in self._seen_receipts:
            raise ValueError("feedback replay across task families rejected")
        entry = self._scopes.get(family)
        if entry is not None and entry[0] != source_sha256:
            raise ValueError("source digest mismatch for task family")
        if entry is None and len(self._scopes) >= _MAX_FAMILIES:
            raise ValueError("task-family capacity exceeded")
        # For a new family, wait until *after* the underlying observation
        # succeeds to register it. Failed input never creates a scope.
        probe = entry[1] if entry is not None else AdaptiveChoiceProbe()
        probe.observe(context, action, success, event_id)
        if entry is None:
            self._scopes[family] = (source_sha256, probe)
        self._seen_receipts.add(receipt_digest)

    def consolidate(self, family: str, source_sha256: str, *,
                    epochs: int) -> None:
        self._get(family, source_sha256).consolidate(epochs=epochs)

    def choose_with_cost_assumption(
        self, family: str, source_sha256: str, context: EvidenceContext, *,
        verifier_success_claim: float, reference_cost: float,
    ) -> str:
        return self._get(family, source_sha256).choose_with_cost_assumption(
            context, verifier_success_claim=verifier_success_claim,
            reference_cost=reference_cost
        )

    def snapshot(self) -> dict:
        return {
            "schema": _SCOPED_SCHEMA,
            "authority_effect": False,
            "feedback_authentication": self.feedback_authentication,
            "self_authorship": self.self_authorship,
            "scopes": [
                {"family": family, "source_sha256": digest,
                 "probe": probe.snapshot()}
                for family, (digest, probe) in sorted(self._scopes.items())
            ],
        }

    @classmethod
    def from_snapshot(cls, payload: dict) -> "ScopedAdaptiveChoiceProbe":
        if type(payload) is not dict or set(payload) != {
            "schema", "authority_effect", "feedback_authentication",
            "self_authorship", "scopes"
        }:
            raise ValueError("scoped snapshot envelope invalid")
        if (payload["schema"] != _SCOPED_SCHEMA
            or payload["authority_effect"] is not False
            or payload["feedback_authentication"] != cls.feedback_authentication
            or payload["self_authorship"] != cls.self_authorship):
            raise ValueError("scoped snapshot must not claim trusted authority")
        scopes = payload["scopes"]
        if type(scopes) is not list or len(scopes) > _MAX_FAMILIES:
            raise ValueError("scoped history count invalid")
        restored = cls()
        for item in scopes:
            if type(item) is not dict or set(item) != {
                "family", "source_sha256", "probe"
            }:
                raise ValueError("scoped family record invalid")
            family = _family(item["family"])
            digest = _source_digest(item["source_sha256"])
            if family in restored._scopes:
                raise ValueError("duplicate task family in snapshot")
            probe = AdaptiveChoiceProbe.from_snapshot(item["probe"])
            if not probe.updates:
                raise ValueError("empty task family has no feedback")
            for event in probe.snapshot()["events"]:
                receipt = event["receipt_sha256"]
                if receipt in restored._seen_receipts:
                    raise ValueError("cross-family feedback replay in snapshot")
                restored._seen_receipts.add(receipt)
            restored._scopes[family] = (digest, probe)
        return restored
