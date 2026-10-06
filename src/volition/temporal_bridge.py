from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .engine import VolitionEngine
from .models import DriveKind
from .temporal import MotiveEvent, MotiveTemporalModel


_REQUIRED_FIELDS = ("id", "timestamp", "source", "event")


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty string")
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"invalid ISO-8601 timestamp: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed


def canonical_temporal_timestamp(value: str | datetime) -> str:
    if isinstance(value, datetime):
        parsed = value
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
    else:
        parsed = _parse_timestamp(value)
    utc = parsed.astimezone(timezone.utc)
    timespec = "microseconds" if utc.microsecond else "seconds"
    return utc.isoformat(timespec=timespec).replace("+00:00", "Z")


def _require_stored_canonical(value: str) -> datetime:
    parsed = _parse_timestamp(value)
    canonical = canonical_temporal_timestamp(parsed)
    if value != canonical:
        raise ValueError("stored timestamp must be canonical UTC ending in Z")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class TemporalRecord:
    """Validated record compatible with Temporal Watch V1 storage."""

    id: str
    timestamp: str
    source: str
    event: str
    local_timestamp: str | None = None
    refs: tuple[str, ...] = ()
    metadata: Mapping[str, Any] | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TemporalRecord":
        if not isinstance(value, Mapping):
            raise ValueError("event record must be a mapping")
        missing = [field for field in _REQUIRED_FIELDS if field not in value]
        if missing:
            raise ValueError(
                f"event record missing required fields: {', '.join(missing)}"
            )
        for key in ("id", "source", "event"):
            field_value = value[key]
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"event field {key!r} must be a non-empty string")
        timestamp = value["timestamp"]
        if not isinstance(timestamp, str):
            raise ValueError("timestamp must be a string")
        _require_stored_canonical(timestamp)
        local_timestamp = value.get("local_timestamp")
        if local_timestamp is not None:
            if not isinstance(local_timestamp, str):
                raise ValueError("local_timestamp must be a string")
            _parse_timestamp(local_timestamp)
        raw_refs = value.get("refs", ())
        if not isinstance(raw_refs, (list, tuple)) or not all(
            isinstance(ref, str) and bool(ref) for ref in raw_refs
        ):
            raise ValueError("refs must be a list or tuple of non-empty strings")
        metadata = value.get("metadata")
        if metadata is not None and not isinstance(metadata, Mapping):
            raise ValueError("metadata must be a mapping")
        return cls(
            id=value["id"],
            timestamp=timestamp,
            source=value["source"],
            event=value["event"],
            local_timestamp=local_timestamp,
            refs=tuple(raw_refs),
            metadata=metadata,
        )


@dataclass(frozen=True, slots=True)
class TemporalAnchor:
    """Maps canonical Temporal UTC timestamps onto Volition-relative seconds."""

    timestamp: str
    _instant: datetime = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_instant", _require_stored_canonical(self.timestamp))

    def seconds_for(self, timestamp: str) -> float:
        instant = _require_stored_canonical(timestamp)
        seconds = (instant - self._instant).total_seconds()
        if seconds < 0:
            raise ValueError("Temporal event precedes Volition anchor")
        return seconds


class TemporalEventBridge:
    """Chronology-only bridge from Temporal records into motive events."""

    def __init__(self, anchor: TemporalAnchor) -> None:
        self.anchor = anchor

    def ingest(
        self,
        model: MotiveTemporalModel,
        record: TemporalRecord | Mapping[str, Any],
        *,
        target: str,
        kind: DriveKind,
        weight: float = 1.0,
    ) -> MotiveEvent:
        parsed = (
            record
            if isinstance(record, TemporalRecord)
            else TemporalRecord.from_mapping(record)
        )
        at_seconds = self.anchor.seconds_for(parsed.timestamp)
        return model.observe_event(
            target,
            kind,
            at_seconds=at_seconds,
            weight=weight,
            temporal_event_id=parsed.id,
            temporal_timestamp=parsed.timestamp,
            temporal_source=parsed.source,
            temporal_refs=parsed.refs,
        )

    def ingest_many(
        self,
        model: MotiveTemporalModel,
        records: Iterable[TemporalRecord | Mapping[str, Any]],
        *,
        target: str,
        kind: DriveKind,
        weight: float = 1.0,
    ) -> tuple[MotiveEvent, ...]:
        parsed = [
            record
            if isinstance(record, TemporalRecord)
            else TemporalRecord.from_mapping(record)
            for record in records
        ]
        ids = [record.id for record in parsed]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate Temporal event id in batch")
        parsed.sort(
            key=lambda record: (
                _require_stored_canonical(record.timestamp),
                record.id,
            )
        )
        return tuple(
            self.ingest(
                model,
                record,
                target=target,
                kind=kind,
                weight=weight,
            )
            for record in parsed
        )


class TemporalClockBridge:
    """Synchronize VolitionEngine logical time to canonical Temporal time."""

    def __init__(self, anchor: TemporalAnchor) -> None:
        self.anchor = anchor

    def advance_engine_to(
        self,
        engine: VolitionEngine,
        timestamp: str,
    ) -> float:
        target_seconds = self.anchor.seconds_for(timestamp)
        current_seconds = engine.elapsed_seconds
        if target_seconds < current_seconds:
            raise ValueError("Temporal clock cannot rewind VolitionEngine")
        engine.advance(target_seconds - current_seconds)
        return engine.elapsed_seconds
