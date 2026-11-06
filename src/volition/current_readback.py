"""Opt-in current-observation admission through a host-owned event readback.

The caller supplies the reader; THIS MODULE CANNOT AUTHENTICATE THAT READER.
It does not change the legacy raw VolitionEngine.evaluate simulation API.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import math
from typing import Callable

from .models import DriveKind, ProvenanceClass
from .operational_drive import AdmittedObservation, ObservationClaim, ObservationVerifier

_MAX_PAYLOAD = 65536
_CURRENT = frozenset((ProvenanceClass.CURRENT_STATEMENT, ProvenanceClass.CURRENT_OBSERVATION))


@dataclass(frozen=True, slots=True)
class HostEvent:
    """Current event returned by the integrating host, never by model text."""

    evidence_id: str
    payload: bytes = field(repr=False)
    target: str
    kind: DriveKind
    magnitude: float
    confidence: float
    source_ref: str
    provenance: ProvenanceClass


def _strict_text(value: object, field_name: str) -> str:
    if (not isinstance(value, str) or not value.strip()
            or len(value) > 256
            or any(ord(c) < 32 for c in value)
            or value.strip().casefold() == "unspecified"):
        raise ValueError(f"{field_name} requires bounded, explicit host evidence")
    return value


def _unit(value: object, field_name: str) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not 0 <= value <= 1):
        raise ValueError(f"{field_name} must be finite numeric within [0, 1]")
    return float(value)


class HostEventGateway:
    """Source-only seam; host reader must enforce freshness/authorization."""

    def __init__(self, read_current: Callable[[str], HostEvent | None],
                 *, verifier_id: str):
        if not callable(read_current):
            raise TypeError("trusted-host reader must be callable")
        self._read_current = read_current
        self._verifier_id = _strict_text(verifier_id, "verifier_id")

    def admit(self, evidence_id: str) -> AdmittedObservation:
        _strict_text(evidence_id, "evidence_id")
        try:
            event = self._read_current(evidence_id)
        except Exception as exc:
            raise ValueError("host current-event readback failed") from exc
        if not isinstance(event, HostEvent) or event.evidence_id != evidence_id:
            raise ValueError("host did not return the exact requested current event")
        _strict_text(event.target, "target")
        _strict_text(event.source_ref, "source_ref")
        if not isinstance(event.kind, DriveKind) or event.provenance not in _CURRENT:
            raise ValueError("host event must have current, typed provenance")
        if (type(event.payload) is not bytes or not (0 < len(event.payload) <= _MAX_PAYLOAD)):
            raise ValueError("event payload must be bounded nonempty immutable bytes")
        magnitude = _unit(event.magnitude, "magnitude")
        confidence = _unit(event.confidence, "confidence")
        # Digest covers the *entire scored event*, not payload alone. The
        # same raw text with altered magnitude/source must be a new claim.
        canonical = json.dumps({
            "schema": "VOLITION_HOST_EVENT_V1", "evidence_id": evidence_id,
            "payload_sha256": sha256(event.payload).hexdigest(),
            "target": event.target, "kind": event.kind.value,
            "magnitude": magnitude, "confidence": confidence,
            "source_ref": event.source_ref, "provenance": event.provenance.value,
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        claim = ObservationClaim(
            evidence_id=evidence_id,
            content_digest="sha256:" + sha256(canonical).hexdigest(),
            target=event.target,
            kind=event.kind,
            magnitude=magnitude,
            confidence=confidence,
            source_ref=event.source_ref,
            provenance=event.provenance,
        )
        return ObservationVerifier((claim,), verifier_id=self._verifier_id).admit(claim)
