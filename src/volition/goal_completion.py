"""Caller-admitted, exact-goal completion evidence; no independent trust grant.

This reference admission proves only that a Python caller selected an exact
immutable claim. It cannot authenticate the caller, outcome, or source system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import ProvenanceClass


_ADMISSION_TOKEN = object()
_CURRENT_EXTERNAL = frozenset({
    ProvenanceClass.CURRENT_OBSERVATION,
    ProvenanceClass.CURRENT_STATEMENT,
})


def _text(value: object, *, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise ValueError(f"{field} must be non-empty bounded text")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field} cannot contain control characters")


@dataclass(frozen=True, slots=True)
class GoalCompletionClaim:
    """An asserted successful outcome bound to one goal revision and result."""

    outcome_event_id: str
    goal_id: str
    choice_id: str
    goal_revision: int
    target: str
    result_receipt_id: str
    evidence_ref: str
    source_ref: str
    provenance: ProvenanceClass

    def __post_init__(self) -> None:
        for field in (
            "outcome_event_id", "goal_id", "choice_id", "target",
            "result_receipt_id", "evidence_ref", "source_ref",
        ):
            _text(getattr(self, field), field=field)
        if (
            isinstance(self.goal_revision, bool)
            or not isinstance(self.goal_revision, int)
            or self.goal_revision < 1
        ):
            raise ValueError("goal_revision must be a positive integer")
        if not isinstance(self.provenance, ProvenanceClass) or self.provenance not in _CURRENT_EXTERNAL:
            raise ValueError("goal completion requires typed current external provenance")

    @property
    def effect_authority(self) -> bool:
        return False


@dataclass(frozen=True, slots=True, init=False)
class AdmittedGoalCompletion:
    """Exact caller-selected claim, not independently verified evidence."""

    claim: GoalCompletionClaim
    verifier_id: str

    def __init__(
        self, claim: GoalCompletionClaim, verifier_id: str, *, _token: object | None = None
    ) -> None:
        if _token is not _ADMISSION_TOKEN:
            raise TypeError("goal completion must be caller-admitted")
        object.__setattr__(self, "claim", claim)
        object.__setattr__(self, "verifier_id", verifier_id)

    @property
    def effect_authority(self) -> bool:
        return False


class GoalCompletionVerifier:
    """Reference allowlist supplied by an accountable *external* caller."""

    def __init__(self, accepted: Iterable[GoalCompletionClaim], *, verifier_id: str):
        _text(verifier_id, field="verifier_id")
        claims = frozenset(accepted)
        if not all(isinstance(claim, GoalCompletionClaim) for claim in claims):
            raise TypeError("accepted goal completion claims must be typed")
        self._accepted = claims
        self._verifier_id = verifier_id

    def admit(self, claim: GoalCompletionClaim) -> AdmittedGoalCompletion:
        if not isinstance(claim, GoalCompletionClaim) or claim not in self._accepted:
            raise ValueError("goal completion claim not exact-bound by caller")
        return AdmittedGoalCompletion(
            claim, self._verifier_id, _token=_ADMISSION_TOKEN
        )
