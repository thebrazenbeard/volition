from __future__ import annotations

from dataclasses import dataclass
import math

from .models import DriveKind, ProvenanceClass, Signal


_CURRENT_PROVENANCE = frozenset({
    ProvenanceClass.CURRENT_OBSERVATION,
    ProvenanceClass.CURRENT_STATEMENT,
})

_NON_REANIMATABLE = frozenset({
    'COMPLETED',
    'REVOKED',
    'CONTRADICTED',
    'REVISED',
})


def _unit(value: float, *, name: str) -> float:
    try:
        resolved = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{name} must be numeric') from exc
    if not math.isfinite(resolved) or not 0.0 <= resolved <= 1.0:
        raise ValueError(f'{name} must be finite and in [0, 1]')
    return resolved


@dataclass(frozen=True, slots=True)
class ConationRecord:
    """Normalized historical conation evidence; never current by storage alone."""

    record_id: str
    target: str
    kind: DriveKind
    magnitude: float
    confidence: float
    status: str
    source_locator: str

    def __post_init__(self) -> None:
        for name in ('record_id', 'target', 'status', 'source_locator'):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'{name} must be a non-empty string')
        try:
            kind = DriveKind(self.kind)
        except ValueError as exc:
            raise ValueError('unsupported drive kind') from exc
        object.__setattr__(self, 'kind', kind)
        object.__setattr__(self, 'magnitude', _unit(self.magnitude, name='magnitude'))
        object.__setattr__(self, 'confidence', _unit(self.confidence, name='confidence'))


class ConationBridge:
    """Admit conation history without promoting storage into current desire."""

    @staticmethod
    def historical_signal(record: ConationRecord) -> Signal:
        if not isinstance(record, ConationRecord):
            raise ValueError('record must be a ConationRecord')
        return Signal(
            target=record.target,
            kind=record.kind,
            magnitude=record.magnitude,
            confidence=record.confidence,
            provenance=ProvenanceClass.HISTORICAL_EVIDENCE,
            source=(
                f'conations:{record.record_id}:{record.status}:'
                f'{record.source_locator}'
            ),
            current_reappraisal=False,
        )

    @staticmethod
    def reappraise(
        record: ConationRecord,
        current: Signal,
    ) -> tuple[Signal, Signal]:
        if not isinstance(record, ConationRecord):
            raise ValueError('record must be a ConationRecord')
        if not isinstance(current, Signal):
            raise ValueError('current evidence must be a Signal')
        if record.status in _NON_REANIMATABLE:
            raise ValueError('terminal or superseded conation requires a new current record')
        if current.provenance not in _CURRENT_PROVENANCE:
            raise ValueError('conation reappraisal requires fresh current evidence')
        if current.target != record.target:
            raise ValueError('current evidence target does not match conation record')
        if current.kind is not record.kind:
            raise ValueError('current evidence drive family does not match conation record')
        if not current.source or current.source == 'unspecified':
            raise ValueError('current evidence requires an explicit source')

        historical = Signal(
            target=record.target,
            kind=record.kind,
            magnitude=min(record.magnitude, _unit(current.magnitude, name='current magnitude')),
            confidence=min(record.confidence, _unit(current.confidence, name='current confidence')),
            provenance=ProvenanceClass.HISTORICAL_EVIDENCE,
            source=(
                f'conations-reappraised:{record.record_id}:{record.status}:'
                f'{record.source_locator}|current:{current.source}'
            ),
            expected_information_gain=current.expected_information_gain,
            learning_progress=current.learning_progress,
            controllability=current.controllability,
            predicted_deficit_reduction=current.predicted_deficit_reduction,
            current_reappraisal=True,
        )
        return historical, current
