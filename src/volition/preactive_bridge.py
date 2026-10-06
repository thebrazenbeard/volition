from __future__ import annotations

from dataclasses import dataclass
import math

from .models import CognitionRequest


_TOOL_NAME = "pre_active.request_turn"
_SOURCE = "ENDOGENOUS"
_MAX_REASON_LENGTH = 2000
_TRUNCATION_SUFFIX = "[truncated]"


def _bounded_reason(request: CognitionRequest) -> str:
    reason = (
        f"Volition cognition request for goal {request.goal_id}; "
        f"target={request.target}; urgency={float(request.urgency):.6f}. "
        "Continue bounded cognition for the existing durable run; "
        "no new capabilities or effect authority are granted."
    )
    if len(reason) <= _MAX_REASON_LENGTH:
        return reason
    keep = _MAX_REASON_LENGTH - len(_TRUNCATION_SUFFIX)
    return reason[:keep] + _TRUNCATION_SUFFIX


@dataclass(frozen=True, slots=True)
class PreActiveReentryProposal:
    """Non-dispatching proposal for Pre-Active's reserved re-entry primitive."""

    goal_id: str
    target: str
    urgency: float
    reason: str
    delay_seconds: float
    tool_name: str = _TOOL_NAME
    source: str = _SOURCE
    capabilities: tuple[str, ...] = ()
    scheduled: bool = False
    effect_authority: bool = False

    def tool_arguments(self) -> dict[str, object]:
        return {
            "reason": self.reason,
            "delay_seconds": self.delay_seconds,
        }


class PreActiveCognitionBridge:
    """Translate Volition cognition evidence without bypassing Pre-Active gates."""

    @staticmethod
    def from_request(
        request: CognitionRequest,
        *,
        delay_seconds: float = 0.0,
    ) -> PreActiveReentryProposal:
        if not isinstance(request, CognitionRequest):
            raise ValueError("request must be a CognitionRequest")
        if request.effect_authority:
            raise ValueError("cognition request cannot carry effect authority")
        if request.source != _SOURCE:
            raise ValueError("cognition request source must be ENDOGENOUS")
        if not isinstance(request.goal_id, str) or not request.goal_id.strip():
            raise ValueError("goal_id must be a non-empty string")
        if not isinstance(request.target, str) or not request.target.strip():
            raise ValueError("target must be a non-empty string")

        urgency = float(request.urgency)
        if not math.isfinite(urgency) or not 0.0 <= urgency <= 1.0:
            raise ValueError("urgency must be finite and in [0, 1]")

        delay = float(delay_seconds)
        if not math.isfinite(delay) or delay < 0.0:
            raise ValueError("delay_seconds must be finite and >= 0")

        return PreActiveReentryProposal(
            goal_id=request.goal_id,
            target=request.target,
            urgency=urgency,
            reason=_bounded_reason(request),
            delay_seconds=delay,
        )
