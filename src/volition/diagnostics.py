from __future__ import annotations

from dataclasses import dataclass
from math import exp, inf, isfinite, log, sqrt
from typing import Iterable

from .models import DriveKind
from .temporal import MotiveTemporalModel


@dataclass(frozen=True, slots=True)
class PoissonNullModel:
    """Homogeneous Poisson null model for event-arrival comparison."""

    rate: float

    def __post_init__(self) -> None:
        if self.rate < 0:
            raise ValueError("Poisson rate must be non-negative")

    @staticmethod
    def _duration(start: float, end: float) -> float:
        start = float(start)
        end = float(end)
        if end < start:
            raise ValueError("end must be greater than or equal to start")
        return end - start

    def expected_count(self, start: float, end: float) -> float:
        return self.rate * self._duration(start, end)

    def log_likelihood(
        self,
        event_times: Iterable[float],
        *,
        start: float,
        end: float,
    ) -> float:
        duration = self._duration(start, end)
        times = tuple(float(value) for value in event_times)
        if any(value < start or value > end for value in times):
            raise ValueError("event time falls outside observation window")
        if self.rate == 0.0:
            return 0.0 if not times else -inf
        return len(times) * log(self.rate) - self.rate * duration


@dataclass(frozen=True, slots=True)
class MartingaleResidual:
    """Observed count minus compensator for one target/drive/window."""

    observed_count: int
    compensator: float
    residual: float
    start: float
    end: float


def integrated_intensity(
    model: MotiveTemporalModel,
    target: str,
    kind: DriveKind,
    *,
    start: float,
    end: float,
    steps: int = 1000,
) -> float:
    """Numerically integrate point-process intensity over a time window.

    Midpoint quadrature avoids assigning special numerical weight to jump
    discontinuities at exact event timestamps. Events at the left boundary can
    influence the following open interval, while an event at the right boundary
    contributes only on the next interval, matching predictable-intensity use.
    """

    start = float(start)
    end = float(end)
    if end < start:
        raise ValueError("end must be greater than or equal to start")
    if steps <= 0:
        raise ValueError("steps must be positive")
    if end == start:
        return 0.0

    width = (end - start) / steps
    total = 0.0
    for index in range(steps):
        midpoint = start + (index + 0.5) * width
        total += model.intensity(target, kind, at_seconds=midpoint).total * width
    return total


def martingale_residual(
    model: MotiveTemporalModel,
    target: str,
    kind: DriveKind,
    *,
    start: float,
    end: float,
    steps: int = 1000,
) -> MartingaleResidual:
    """Return N(start,end] - integral lambda(t)dt."""

    compensator = integrated_intensity(
        model,
        target,
        kind,
        start=start,
        end=end,
        steps=steps,
    )
    observed = sum(
        1
        for event in model.events
        if event.target == target
        and event.kind is kind
        and start < event.at_seconds <= end
    )
    return MartingaleResidual(
        observed_count=observed,
        compensator=compensator,
        residual=observed - compensator,
        start=float(start),
        end=float(end),
    )


def time_rescaled_intervals(
    model: MotiveTemporalModel,
    target: str,
    kind: DriveKind,
    *,
    start: float,
    end: float,
    steps_per_interval: int = 1000,
) -> tuple[float, ...]:
    """Integrate intensity from the previous boundary to each observed event.

    Under the time-rescaling theorem, a correctly specified simple point process
    maps event times through compensator increments to unit-rate exponential
    inter-arrival variables under standard conditions. This function returns the
    transformed intervals only; it does not perform a distributional test.
    """

    if end < start:
        raise ValueError("end must be greater than or equal to start")
    if steps_per_interval <= 0:
        raise ValueError("steps_per_interval must be positive")

    times = sorted(
        event.at_seconds
        for event in model.events
        if event.target == target
        and event.kind is kind
        and start < event.at_seconds <= end
    )
    previous = float(start)
    transformed: list[float] = []
    for event_time in times:
        transformed.append(
            integrated_intensity(
                model,
                target,
                kind,
                start=previous,
                end=event_time,
                steps=steps_per_interval,
            )
        )
        previous = event_time
    return tuple(transformed)



@dataclass(frozen=True, slots=True)
class TimeRescalingDiagnostics:
    """Distributional screening statistics for rescaled intervals."""

    count: int
    mean_interval: float | None
    variance_interval: float | None
    uniform_ks_statistic: float | None
    lag1_correlation: float | None
    uniform_values: tuple[float, ...]


def evaluate_time_rescaled_intervals(
    intervals: Iterable[float],
) -> TimeRescalingDiagnostics:
    """Evaluate Exp(1) and serial-structure implications without p-values."""

    values = tuple(float(value) for value in intervals)
    if any(value < 0.0 or not isfinite(value) for value in values):
        raise ValueError("rescaled intervals must be finite and non-negative")

    count = len(values)
    if count == 0:
        return TimeRescalingDiagnostics(
            count=0,
            mean_interval=None,
            variance_interval=None,
            uniform_ks_statistic=None,
            lag1_correlation=None,
            uniform_values=(),
        )

    mean_interval = sum(values) / count
    variance_interval = sum(
        (value - mean_interval) ** 2 for value in values
    ) / count

    uniform_values = tuple(1.0 - exp(-value) for value in values)
    ordered = sorted(uniform_values)
    d_plus = max(
        (index / count) - value
        for index, value in enumerate(ordered, start=1)
    )
    d_minus = max(
        value - ((index - 1) / count)
        for index, value in enumerate(ordered, start=1)
    )
    ks_statistic = max(d_plus, d_minus)

    lag1_correlation: float | None = None
    if count >= 3:
        left = values[:-1]
        right = values[1:]
        left_mean = sum(left) / len(left)
        right_mean = sum(right) / len(right)
        left_ss = sum((value - left_mean) ** 2 for value in left)
        right_ss = sum((value - right_mean) ** 2 for value in right)
        denominator = sqrt(left_ss * right_ss)
        if denominator > 0.0:
            covariance = sum(
                (x - left_mean) * (y - right_mean)
                for x, y in zip(left, right)
            )
            lag1_correlation = covariance / denominator

    return TimeRescalingDiagnostics(
        count=count,
        mean_interval=mean_interval,
        variance_interval=variance_interval,
        uniform_ks_statistic=ks_statistic,
        lag1_correlation=lag1_correlation,
        uniform_values=uniform_values,
    )


def time_rescaling_diagnostics(
    model: MotiveTemporalModel,
    target: str,
    kind: DriveKind,
    *,
    start: float,
    end: float,
    steps_per_interval: int = 1000,
) -> TimeRescalingDiagnostics:
    """Generate time-rescaled intervals and evaluate their diagnostics."""

    return evaluate_time_rescaled_intervals(
        time_rescaled_intervals(
            model,
            target,
            kind,
            start=start,
            end=end,
            steps_per_interval=steps_per_interval,
        )
    )
