from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from .models import DriveKind, ProvenanceClass, Signal


_ALLOWED_INTENT_KINDS = frozenset({"withdraw", "approach", "inspect", "hold"})
_MISSING = object()


def _field(value: object, name: str, default: object = _MISSING) -> Any:
    if isinstance(value, Mapping):
        if name in value:
            return value[name]
    elif hasattr(value, name):
        return getattr(value, name)
    if default is not _MISSING:
        return default
    raise ValueError(f"MESO intent missing required field: {name}")


def _kind_value(value: object) -> str:
    raw = getattr(value, "value", value)
    if not isinstance(raw, str) or not raw:
        raise ValueError("MESO intent kind must be a non-empty string/enum value")
    return raw


@dataclass(frozen=True, slots=True)
class MesoIntentEvidence:
    """Normalized non-executable MESO-CRCT intent evidence."""

    target_id: str | None
    kind: str
    strength: float
    source_tendency: str
    source: str
    effect_authorized: bool = False

    @classmethod
    def from_value(cls, value: object) -> "MesoIntentEvidence":
        kind = _kind_value(_field(value, "kind"))
        if kind not in _ALLOWED_INTENT_KINDS:
            raise ValueError(f"unsupported MESO intent kind: {kind}")

        raw_strength = _field(value, "strength")
        try:
            strength = float(raw_strength)
        except (TypeError, ValueError) as exc:
            raise ValueError("MESO intent strength must be numeric") from exc
        if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
            raise ValueError("MESO intent strength must be finite and in [0, 1]")

        target_id = _field(value, "target_id")
        if target_id is not None:
            if not isinstance(target_id, str) or not target_id.strip():
                raise ValueError("MESO target_id must be non-empty when present")
        elif kind != "hold":
            raise ValueError("committed MESO intent requires target_id")

        source_tendency = _field(value, "source_tendency")
        source = _field(value, "source")
        for name, item in (
            ("source_tendency", source_tendency),
            ("source", source),
        ):
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"MESO intent {name} must be non-empty")

        effect_authorized = _field(value, "effect_authorized")
        if effect_authorized is not False:
            raise ValueError("authorized MESO intent cannot enter Volition motive bridge")
        can_execute = _field(value, "can_execute", False)
        if can_execute is not False:
            raise ValueError("executable MESO intent cannot enter Volition motive bridge")

        return cls(
            target_id=target_id,
            kind=kind,
            strength=strength,
            source_tendency=source_tendency,
            source=source,
            effect_authorized=False,
        )


class MesoIntentBridge:
    """Translate gated MESO intent proposals into typed motive evidence only."""

    @staticmethod
    def to_signals(value: object) -> tuple[Signal, ...]:
        evidence = (
            value
            if isinstance(value, MesoIntentEvidence)
            else MesoIntentEvidence.from_value(value)
        )
        if evidence.kind == "hold":
            return ()

        assert evidence.target_id is not None
        source = (
            f"meso-crct:intent:{evidence.kind}:"
            f"{evidence.source_tendency}:{evidence.source}"
        )

        if evidence.kind == "approach":
            kind = DriveKind.OPEN_LOOP
            return (
                Signal(
                    target=evidence.target_id,
                    kind=kind,
                    magnitude=evidence.strength,
                    provenance=ProvenanceClass.MODEL_GENERATED,
                    source=source,
                ),
            )

        if evidence.kind == "inspect":
            return (
                Signal(
                    target=evidence.target_id,
                    kind=DriveKind.EPISTEMIC,
                    magnitude=evidence.strength,
                    provenance=ProvenanceClass.MODEL_GENERATED,
                    source=source,
                    expected_information_gain=1.0,
                    controllability=1.0,
                ),
            )

        return (
            Signal(
                target=evidence.target_id,
                kind=DriveKind.PROTECTION,
                magnitude=evidence.strength,
                provenance=ProvenanceClass.MODEL_GENERATED,
                source=source,
            ),
        )
