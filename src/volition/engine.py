from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import asdict, dataclass

from .models import (
    ChoiceClass,
    ChoiceRecord,
    CognitionRequest,
    DriveContribution,
    DriveKind,
    Goal,
    ProvenanceClass,
    Signal,
    TransitionEvent,
    Want,
)


STATE_SCHEMA = "VOLITION_STATE_V3"
LEGACY_STATE_SCHEMA = "VOLITION_STATE_V2"


def _finite(value: float, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be finite and numeric")
    try:
        resolved = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be finite and numeric") from exc
    if not math.isfinite(resolved):
        raise ValueError(f"{name} must be finite")
    return resolved


def _bounded(value: float, *, name: str) -> float:
    resolved = _finite(value, name=name)
    if not 0.0 <= resolved <= 1.0:
        raise ValueError(f"{name} must be within [0, 1]")
    return resolved


def _nonnegative_integer(value: object, *, name: str) -> int:
    """Reject snapshot numeric coercion that conceals invalid persisted counts."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _generated_id_number(value: object, *, prefix: str) -> int:
    """Read only canonical engine-generated IDs, never untrusted aliases."""
    if not isinstance(value, str) or not value.startswith(f"{prefix}-"):
        raise ValueError(f"snapshot {prefix} ID is invalid")
    suffix = value[len(prefix) + 1:]
    if not suffix or not all("0" <= digit <= "9" for digit in suffix):
        raise ValueError(f"snapshot {prefix} ID is invalid")
    try:
        number = int(suffix)
    except ValueError as exc:
        raise ValueError(f"snapshot {prefix} ID is invalid") from exc
    if number < 1 or value != f"{prefix}-{number:04d}":
        raise ValueError(f"snapshot {prefix} ID is invalid")
    return number


def _reappraisal_receipt_score(details: tuple[tuple[str, str], ...]) -> float:
    """Decode only the exact float text emitted by this engine's V3 receipt."""
    candidates = [value for key, value in details if key == "score"]
    if len(candidates) != 1 or not isinstance(candidates[0], str):
        raise ValueError("snapshot reappraisal score receipt is missing or malformed")
    try:
        score = float(candidates[0])
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("snapshot reappraisal score receipt is invalid") from exc
    score = _bounded(score, name="snapshot reappraisal score")
    if str(score) != candidates[0]:
        raise ValueError("snapshot reappraisal score receipt is noncanonical")
    return score


def _unit(value: float) -> float:
    return max(0.0, min(1.0, _finite(value, name="normalized value")))


def _validated_signal(signal: Signal) -> None:
    if not isinstance(signal, Signal):
        raise ValueError("signal must be a typed Signal")
    for field_name in ("target", "source"):
        value = getattr(signal, field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"signal {field_name} must be non-empty text")
    if not isinstance(signal.kind, DriveKind):
        raise ValueError("signal kind must be a DriveKind enum")
    if not isinstance(signal.provenance, ProvenanceClass):
        raise ValueError("signal provenance must be a ProvenanceClass enum")
    if not isinstance(signal.current_reappraisal, bool):
        raise ValueError("signal current_reappraisal must be boolean")
    for field_name in (
        "magnitude", "confidence", "expected_information_gain",
        "learning_progress", "controllability", "predicted_deficit_reduction",
    ):
        _finite(getattr(signal, field_name), name=f"signal {field_name}")


@dataclass(frozen=True, slots=True)
class Policy:
    want_threshold: float = 0.35
    protection_veto: float = 0.60
    switch_margin: float = 0.15
    social_cap: float = 0.25
    empowerment_cap: float = 0.40
    endogenous_turn_budget: int = 3
    satiation_half_life_seconds: float = 3600.0
    goal_reappraisal_seconds: float = 21600.0

    def __post_init__(self) -> None:
        for field_name in (
            "want_threshold", "protection_veto", "switch_margin", "social_cap",
            "empowerment_cap",
        ):
            _bounded(getattr(self, field_name), name=f"policy {field_name}")
        for field_name in ("satiation_half_life_seconds", "goal_reappraisal_seconds"):
            _finite(getattr(self, field_name), name=f"policy {field_name}")
        if (not isinstance(self.endogenous_turn_budget, int)
                or isinstance(self.endogenous_turn_budget, bool)
                or self.endogenous_turn_budget < 0):
            raise ValueError("policy cognition budget must be a non-negative integer")


class VolitionEngine:
    """Deterministic motive arbitration with explicit choice and no effect dispatch."""

    def __init__(self, policy: Policy | None = None) -> None:
        self.policy = policy or Policy()
        self._active_goal: Goal | None = None
        self._goal_counter = 0
        self._choice_counter = 0
        self._choices: dict[str, ChoiceRecord] = {}
        self._endogenous_turns = 0
        self._satiation: dict[str, float] = {}
        self._elapsed_seconds = 0.0
        self._events: list[TransitionEvent] = []
        # Ephemeral one-evaluation custody, intentionally excluded from snapshots.
        self._issued_wants: list[tuple[Want, Want]] = []

    @property
    def elapsed_seconds(self) -> float:
        return self._elapsed_seconds

    @property
    def active_goal(self) -> Goal | None:
        return self._active_goal

    @property
    def choices(self) -> tuple[ChoiceRecord, ...]:
        return tuple(self._choices.values())

    @property
    def events(self) -> tuple[TransitionEvent, ...]:
        return tuple(self._events)

    def _emit(self, kind: str, target: str, **details: object) -> None:
        self._events.append(
            TransitionEvent(
                sequence=len(self._events) + 1,
                kind=kind,
                target=target,
                at_seconds=self._elapsed_seconds,
                details=tuple(sorted((key, str(value)) for key, value in details.items())),
            )
        )

    def _signal_value(self, signal: Signal) -> float:
        if (
            signal.provenance is ProvenanceClass.HISTORICAL_EVIDENCE
            and not signal.current_reappraisal
        ):
            return 0.0

        magnitude = _unit(signal.magnitude)
        confidence = _unit(signal.confidence)
        if signal.kind is DriveKind.EPISTEMIC:
            return (
                magnitude
                * confidence
                * _unit(signal.expected_information_gain)
                * _unit(signal.controllability)
            )
        if signal.kind is DriveKind.COMPETENCE:
            return magnitude * confidence * _unit(signal.learning_progress)
        if signal.kind is DriveKind.HOMEOSTATIC:
            return magnitude * confidence * _unit(signal.predicted_deficit_reduction)
        if signal.kind is DriveKind.SOCIAL:
            return min(magnitude * confidence, self.policy.social_cap)
        if signal.kind is DriveKind.EMPOWERMENT:
            return min(magnitude * confidence, self.policy.empowerment_cap)
        return magnitude * confidence

    def evaluate(self, signals: list[Signal]) -> list[Want]:
        self._issued_wants = []
        grouped: dict[str, list[Signal]] = {}
        for signal in signals:
            _validated_signal(signal)
            grouped.setdefault(signal.target, []).append(signal)

        wants: list[Want] = []
        for target, target_signals in grouped.items():
            contributions: list[DriveContribution] = []
            family_values: dict[DriveKind, float] = {}
            reasons: list[str] = []

            for signal in target_signals:
                value = self._signal_value(signal)
                contributions.append(
                    DriveContribution(
                        kind=signal.kind,
                        value=value,
                        source=signal.source,
                        provenance=signal.provenance,
                    )
                )
                family_values[signal.kind] = max(
                    family_values.get(signal.kind, 0.0),
                    value,
                )
                if (
                    signal.provenance is ProvenanceClass.HISTORICAL_EVIDENCE
                    and not signal.current_reappraisal
                ):
                    reasons.append("historical_requires_current_reappraisal")

            protection = family_values.get(DriveKind.PROTECTION, 0.0)
            positive = sum(
                value
                for kind, value in family_values.items()
                if kind is not DriveKind.PROTECTION
            )
            satiation = _unit(self._satiation.get(target, 0.0))
            score = _unit(positive) * (1.0 - satiation)
            vetoed = protection >= self.policy.protection_veto
            if vetoed:
                reasons.append("protection_veto")
            if satiation > 0.0:
                reasons.append("satiation")
            eligible = score >= self.policy.want_threshold and not vetoed
            wants.append(
                Want(
                    target=target,
                    score=score,
                    contributions=tuple(contributions),
                    eligible=eligible,
                    vetoed=vetoed,
                    reasons=tuple(dict.fromkeys(reasons)),
                )
            )

        wants.sort(key=lambda want: (-want.score, want.target))
        self._issued_wants = [(want, deepcopy(want)) for want in wants]
        return wants

    def choose(
        self,
        want: Want,
        *,
        choice_class: ChoiceClass | str = ChoiceClass.POLICY_DERIVED,
        source: str = "volition:policy",
    ) -> ChoiceRecord:
        issued_index = next(
            (index for index, (issued, _) in enumerate(self._issued_wants)
             if issued is want), None
        )
        if issued_index is None:
            raise ValueError("want must originate from this engine's current evaluation")
        _, issued_snapshot = self._issued_wants[issued_index]
        if want != issued_snapshot:
            raise ValueError("evaluated want was modified after arbitration")
        _bounded(want.score, name="evaluated want score")
        if not want.eligible or want.vetoed:
            raise ValueError("want is not eligible for choice")
        try:
            resolved_class = ChoiceClass(choice_class)
        except ValueError as exc:
            raise ValueError("unsupported choice class") from exc
        if not source:
            raise ValueError("choice source is required")

        del self._issued_wants[issued_index]
        self._choice_counter += 1
        choice = ChoiceRecord(
            choice_id=f"choice-{self._choice_counter:04d}",
            want_target=want.target,
            want_score=want.score,
            choice_class=resolved_class,
            source=source,
        )
        self._choices[choice.choice_id] = choice
        self._emit(
            "CHOICE_RECORDED",
            choice.want_target,
            choice_id=choice.choice_id,
            choice_class=choice.choice_class.value,
            source=choice.source,
            score=choice.want_score,
        )
        return choice

    def adopt_choice(self, choice_id: str) -> Goal:
        choice = self._choices.get(choice_id)
        if choice is None:
            raise ValueError("unknown choice")
        self._issued_wants = []
        self._goal_counter += 1
        goal = Goal(
            goal_id=f"goal-{self._goal_counter:04d}",
            target=choice.want_target,
            adoption_score=choice.want_score,
            choice_id=choice.choice_id,
            adopted_at_seconds=self._elapsed_seconds,
        )
        self._active_goal = goal
        self._endogenous_turns = 0
        self._emit(
            "GOAL_ADOPTED",
            goal.target,
            goal_id=goal.goal_id,
            choice_id=goal.choice_id,
            score=goal.adoption_score,
        )
        return goal

    def adopt(self, want: Want) -> Goal:
        return self.adopt_choice(
            self.choose(
                want,
                choice_class=ChoiceClass.POLICY_DERIVED,
                source="volition:policy",
            ).choice_id
        )

    def _reappraise_active_goal(self, wants: list[Want]) -> None:
        if self._active_goal is None:
            return
        horizon = self.policy.goal_reappraisal_seconds
        due = horizon <= 0 or (
            self._elapsed_seconds - self._active_goal.adopted_at_seconds
        ) >= horizon
        if not due:
            return

        candidate = next(
            (want for want in wants if want.target == self._active_goal.target),
            None,
        )
        if candidate is None or not candidate.eligible or candidate.vetoed:
            self._emit(
                "GOAL_SUSPENDED",
                self._active_goal.target,
                reason="current_reappraisal_due",
            )
            self._active_goal = None
            self._endogenous_turns = 0
            return

        previous = self._active_goal
        self._active_goal = Goal(
            goal_id=previous.goal_id,
            target=previous.target,
            adoption_score=candidate.score,
            choice_id=previous.choice_id,
            adopted_at_seconds=self._elapsed_seconds,
            revision=previous.revision + 1,
        )
        self._endogenous_turns = 0
        self._emit(
            "GOAL_REAPPRAISED",
            previous.target,
            goal_id=previous.goal_id,
            choice_id=previous.choice_id,
            revision=self._active_goal.revision,
            score=self._active_goal.adoption_score,
        )

    def tick(self, signals: list[Signal]) -> Goal | None:
        wants = self.evaluate(signals)
        self._reappraise_active_goal(wants)

        if self._active_goal is not None:
            active_candidate = next(
                (want for want in wants if want.target == self._active_goal.target),
                None,
            )
            if active_candidate is not None and active_candidate.vetoed:
                self._emit("GOAL_SUSPENDED", self._active_goal.target, reason="protection_veto")
                self._active_goal = None
                self._endogenous_turns = 0
                return None

        eligible = [want for want in wants if want.eligible]
        if not eligible:
            return self._active_goal

        best = eligible[0]
        if self._active_goal is None:
            return self.adopt(best)
        if best.target == self._active_goal.target:
            return self._active_goal
        if best.score > self._active_goal.adoption_score + self.policy.switch_margin:
            self._emit(
                "GOAL_REPLACED",
                self._active_goal.target,
                replacement_target=best.target,
            )
            return self.adopt(best)
        return self._active_goal

    def record_satisfaction(self, target: str, amount: float) -> None:
        amount = _unit(amount)
        self._issued_wants = []
        self._satiation[target] = _unit(self._satiation.get(target, 0.0) + amount)
        self._emit("SATISFACTION_RECORDED", target, amount=amount)
        if (
            self._active_goal is not None
            and self._active_goal.target == target
            and amount >= 0.7
        ):
            self._emit(
                "GOAL_COMPLETED",
                target,
                goal_id=self._active_goal.goal_id,
                choice_id=self._active_goal.choice_id,
            )
            self._active_goal = None
            self._endogenous_turns = 0

    def advance(self, seconds: float) -> None:
        seconds = _finite(seconds, name="advance seconds")
        if seconds < 0:
            raise ValueError("seconds must be non-negative")
        if seconds == 0:
            return
        new_elapsed = _finite(
            self._elapsed_seconds + seconds, name="accumulated elapsed time"
        )
        self._issued_wants = []
        self._elapsed_seconds = new_elapsed
        half_life = self.policy.satiation_half_life_seconds
        if half_life <= 0:
            self._satiation.clear()
        else:
            decay = 0.5 ** (seconds / half_life)
            self._satiation = {
                target: value * decay
                for target, value in self._satiation.items()
                if value * decay > 1e-9
            }

    def request_cognition(self) -> CognitionRequest | None:
        if self._active_goal is None:
            return None
        if self._endogenous_turns >= self.policy.endogenous_turn_budget:
            return None
        self._issued_wants = []
        self._endogenous_turns += 1
        request = CognitionRequest(
            goal_id=self._active_goal.goal_id,
            target=self._active_goal.target,
            urgency=_unit(self._active_goal.adoption_score),
        )
        self._emit(
            "COGNITION_REQUESTED",
            request.target,
            goal_id=request.goal_id,
            ordinal=self._endogenous_turns,
        )
        return request

    def snapshot(self) -> dict[str, object]:
        return {
            "schema": STATE_SCHEMA,
            "policy": asdict(self.policy),
            "active_goal": asdict(self._active_goal) if self._active_goal else None,
            "goal_counter": self._goal_counter,
            "choice_counter": self._choice_counter,
            "choices": [
                {
                    "choice_id": choice.choice_id,
                    "want_target": choice.want_target,
                    "want_score": choice.want_score,
                    "choice_class": choice.choice_class.value,
                    "source": choice.source,
                    "effect_authority": choice.effect_authority,
                }
                for choice in self._choices.values()
            ],
            "endogenous_turns": self._endogenous_turns,
            "satiation": dict(self._satiation),
            "elapsed_seconds": self._elapsed_seconds,
            "events": [asdict(event) for event in self._events],
        }

    @classmethod
    def from_snapshot(cls, snapshot: dict[str, object]) -> "VolitionEngine":
        schema = snapshot.get("schema")
        if schema not in (STATE_SCHEMA, LEGACY_STATE_SCHEMA):
            raise ValueError("unsupported or missing Volition state schema")
        raw_policy = snapshot.get("policy")
        if not isinstance(raw_policy, dict):
            raise ValueError("snapshot policy is invalid")
        engine = cls(Policy(**raw_policy))

        raw_choices = snapshot.get("choices", [])
        if not isinstance(raw_choices, list):
            raise ValueError("snapshot choices are invalid")
        for raw_choice in raw_choices:
            if not isinstance(raw_choice, dict) or raw_choice.get("effect_authority") is not False:
                raise ValueError("snapshot choice violates authority boundary")
            choice = ChoiceRecord(
                choice_id=str(raw_choice["choice_id"]),
                want_target=str(raw_choice["want_target"]),
                want_score=_bounded(raw_choice["want_score"], name="snapshot choice score"),
                choice_class=ChoiceClass(str(raw_choice["choice_class"])),
                source=str(raw_choice["source"]),
                effect_authority=False,
            )
            if choice.choice_id in engine._choices:
                raise ValueError("snapshot contains duplicate choice")
            engine._choices[choice.choice_id] = choice

        raw_goal = snapshot.get("active_goal")
        if raw_goal is not None:
            if not isinstance(raw_goal, dict) or raw_goal.get("effect_authority") is not False:
                raise ValueError("snapshot goal violates authority boundary")
            goal_fields = dict(raw_goal)
            goal_fields["adoption_score"] = _bounded(
                goal_fields["adoption_score"], name="snapshot goal adoption_score"
            )
            goal_fields["adopted_at_seconds"] = _finite(
                goal_fields["adopted_at_seconds"], name="snapshot goal adopted_at_seconds"
            )
            revision = _nonnegative_integer(
                goal_fields["revision"], name="snapshot goal revision"
            )
            if revision == 0:
                raise ValueError("snapshot goal revision must be a positive integer")
            engine._active_goal = Goal(**goal_fields)
            if engine._active_goal.choice_id not in engine._choices:
                raise ValueError("snapshot active goal has unknown choice")
            linked_choice = engine._choices[engine._active_goal.choice_id]
            if engine._active_goal.target != linked_choice.want_target:
                raise ValueError("snapshot goal target does not match choice")
            if revision == 1 and engine._active_goal.adoption_score != linked_choice.want_score:
                raise ValueError("snapshot goal adoption score does not match choice")
            if schema == LEGACY_STATE_SCHEMA and revision > 1:
                raise ValueError("legacy V2 reappraisal score is unverifiable; current reappraisal required")

        engine._goal_counter = _nonnegative_integer(
            snapshot.get("goal_counter", 0), name="snapshot goal counter"
        )
        engine._choice_counter = _nonnegative_integer(
            snapshot.get("choice_counter", 0), name="snapshot choice counter"
        )
        engine._endogenous_turns = _nonnegative_integer(
            snapshot.get("endogenous_turns", 0), name="snapshot endogenous turns"
        )
        if engine._choice_counter < len(engine._choices):
            raise ValueError("snapshot choice counter is inconsistent")
        if any(
            _generated_id_number(choice_id, prefix="choice") > engine._choice_counter
            for choice_id in engine._choices
        ):
            raise ValueError("snapshot choice ID exceeds choice counter")
        if engine._active_goal is not None and (
            _generated_id_number(engine._active_goal.goal_id, prefix="goal")
            > engine._goal_counter
        ):
            raise ValueError("snapshot goal ID exceeds goal counter")
        if engine._endogenous_turns > engine.policy.endogenous_turn_budget:
            raise ValueError("snapshot cognition budget is inconsistent")

        raw_satiation = snapshot.get("satiation", {})
        if not isinstance(raw_satiation, dict):
            raise ValueError("snapshot satiation is invalid")
        engine._satiation = {
            str(key): _bounded(value, name=f"snapshot satiation {key}")
            for key, value in raw_satiation.items()
        }
        engine._elapsed_seconds = _finite(
            snapshot.get("elapsed_seconds", 0.0), name="snapshot elapsed_seconds"
        )
        if engine._elapsed_seconds < 0:
            raise ValueError("snapshot elapsed time must be non-negative")
        if engine._active_goal is not None:
            adopted_at = engine._active_goal.adopted_at_seconds
            if adopted_at < 0 or adopted_at > engine._elapsed_seconds:
                raise ValueError("snapshot goal has invalid or future adoption time")

        raw_events = snapshot.get("events", [])
        if not isinstance(raw_events, list):
            raise ValueError("snapshot events are invalid")
        for raw_event in raw_events:
            if not isinstance(raw_event, dict) or raw_event.get("effect_authority") is not False:
                raise ValueError("snapshot event violates authority boundary")
            event = TransitionEvent(
                sequence=_nonnegative_integer(
                    raw_event["sequence"], name="snapshot event sequence"
                ),
                kind=str(raw_event["kind"]),
                target=str(raw_event["target"]),
                at_seconds=_finite(raw_event["at_seconds"], name="snapshot event at_seconds"),
                details=tuple(tuple(item) for item in raw_event.get("details", ())),
                effect_authority=False,
            )
            if event.sequence != len(engine._events) + 1:
                raise ValueError("snapshot event sequence is not contiguous")
            if event.at_seconds > engine._elapsed_seconds:
                raise ValueError("snapshot event time exceeds elapsed time")
            if event.at_seconds < 0 or (
                engine._events and event.at_seconds < engine._events[-1].at_seconds
            ):
                raise ValueError("snapshot event time is not monotonic")
            engine._events.append(event)
        if engine._active_goal is not None:
            goal = engine._active_goal
            reappraisals = [
                event for event in engine._events
                if event.kind == "GOAL_REAPPRAISED"
                and event.target == goal.target
                and dict(event.details).get("goal_id") == goal.goal_id
                and dict(event.details).get("choice_id") == goal.choice_id
            ]
            if goal.revision == 1:
                if reappraisals:
                    raise ValueError("snapshot goal revision contradicts historical reappraisal events")
            else:
                if (
                    len(reappraisals) != goal.revision - 1
                    or any(
                        dict(event.details).get("revision") != str(index)
                        for index, event in enumerate(reappraisals, start=2)
                    )
                    or reappraisals[-1].at_seconds != goal.adopted_at_seconds
                ):
                    raise ValueError("snapshot goal revision has no matching reappraisal event lineage")
                for event in reappraisals:
                    recorded_score = _reappraisal_receipt_score(event.details)
                    if event is reappraisals[-1] and recorded_score != goal.adoption_score:
                        raise ValueError("snapshot reappraisal score disagrees with active goal")
        return engine
