from __future__ import annotations

from dataclasses import dataclass

from .models import (
    CognitionRequest,
    DriveContribution,
    DriveKind,
    Goal,
    ProvenanceClass,
    Signal,
    Want,
)


def _unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True, slots=True)
class Policy:
    want_threshold: float = 0.35
    protection_veto: float = 0.60
    switch_margin: float = 0.15
    social_cap: float = 0.25
    empowerment_cap: float = 0.40
    endogenous_turn_budget: int = 3
    satiation_half_life_seconds: float = 3600.0


class VolitionEngine:
    """Deterministic motive arbitration.

    This engine can generate wants, adopt goals, and request cognition. It has no
    effect-dispatch API and never manufactures effect authority.
    """

    def __init__(self, policy: Policy | None = None) -> None:
        self.policy = policy or Policy()
        self._active_goal: Goal | None = None
        self._goal_counter = 0
        self._endogenous_turns = 0
        self._satiation: dict[str, float] = {}

    @property
    def active_goal(self) -> Goal | None:
        return self._active_goal

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
        grouped: dict[str, list[Signal]] = {}
        for signal in signals:
            grouped.setdefault(signal.target, []).append(signal)

        wants: list[Want] = []
        for target, target_signals in grouped.items():
            contributions: list[DriveContribution] = []
            protection = 0.0
            positive = 0.0
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
                if (
                    signal.provenance is ProvenanceClass.HISTORICAL_EVIDENCE
                    and not signal.current_reappraisal
                ):
                    reasons.append("historical_requires_current_reappraisal")
                if signal.kind is DriveKind.PROTECTION:
                    protection = max(protection, value)
                else:
                    positive += value

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
        return wants

    def adopt(self, want: Want) -> Goal:
        if not want.eligible or want.vetoed:
            raise ValueError("want is not eligible for goal adoption")
        self._goal_counter += 1
        goal = Goal(
            goal_id=f"goal-{self._goal_counter:04d}",
            target=want.target,
            adoption_score=want.score,
        )
        self._active_goal = goal
        self._endogenous_turns = 0
        return goal

    def tick(self, signals: list[Signal]) -> Goal | None:
        wants = self.evaluate(signals)

        if self._active_goal is not None:
            active_candidate = next(
                (want for want in wants if want.target == self._active_goal.target),
                None,
            )
            if active_candidate is not None and active_candidate.vetoed:
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
            return self.adopt(best)
        return self._active_goal

    def record_satisfaction(self, target: str, amount: float) -> None:
        amount = _unit(amount)
        self._satiation[target] = _unit(self._satiation.get(target, 0.0) + amount)
        if self._active_goal is not None and self._active_goal.target == target and amount >= 0.7:
            self._active_goal = None
            self._endogenous_turns = 0

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("seconds must be non-negative")
        if seconds == 0:
            return
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
        self._endogenous_turns = 0

    def request_cognition(self) -> CognitionRequest | None:
        if self._active_goal is None:
            return None
        if self._endogenous_turns >= self.policy.endogenous_turn_budget:
            return None
        self._endogenous_turns += 1
        return CognitionRequest(
            goal_id=self._active_goal.goal_id,
            target=self._active_goal.target,
            urgency=_unit(self._active_goal.adoption_score),
        )
