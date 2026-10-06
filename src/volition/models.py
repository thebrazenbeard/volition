from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProvenanceClass(StrEnum):
    CURRENT_OBSERVATION = "current_observation"
    CURRENT_STATEMENT = "current_statement"
    INFERENCE = "inference"
    HISTORICAL_EVIDENCE = "historical_evidence"
    MODEL_GENERATED = "model_generated"
    SYSTEM_STATE = "system_state"


class DriveKind(StrEnum):
    HOMEOSTATIC = "homeostatic"
    EPISTEMIC = "epistemic"
    COMPETENCE = "competence"
    EMPOWERMENT = "empowerment"
    OPEN_LOOP = "open_loop"
    SOCIAL = "social"
    SELF_MODEL = "self_model"
    PROTECTION = "protection"


@dataclass(frozen=True, slots=True)
class Signal:
    target: str
    kind: DriveKind
    magnitude: float
    confidence: float = 1.0
    provenance: ProvenanceClass = ProvenanceClass.CURRENT_OBSERVATION
    source: str = "unspecified"
    expected_information_gain: float = 0.0
    learning_progress: float = 0.0
    controllability: float = 1.0
    predicted_deficit_reduction: float = 1.0
    current_reappraisal: bool = False


@dataclass(frozen=True, slots=True)
class DriveContribution:
    kind: DriveKind
    value: float
    source: str
    provenance: ProvenanceClass


@dataclass(frozen=True, slots=True)
class Want:
    target: str
    score: float
    contributions: tuple[DriveContribution, ...]
    eligible: bool
    vetoed: bool
    reasons: tuple[str, ...]
    effect_authority: bool = False


@dataclass(frozen=True, slots=True)
class Goal:
    goal_id: str
    target: str
    adoption_score: float
    revision: int = 1
    status: str = "ACTIVE"
    effect_authority: bool = False


@dataclass(frozen=True, slots=True)
class CognitionRequest:
    goal_id: str
    target: str
    urgency: float
    source: str = "ENDOGENOUS"
    effect_authority: bool = False


@dataclass(frozen=True, slots=True)
class TransitionEvent:
    sequence: int
    kind: str
    target: str
    at_seconds: float
    details: tuple[tuple[str, str], ...] = ()
    effect_authority: bool = False
