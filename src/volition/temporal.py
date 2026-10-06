from __future__ import annotations

from dataclasses import dataclass, field
from math import exp

from .models import DriveKind, ProvenanceClass, Signal


@dataclass(slots=True)
class ARIMABaseline:
    """Small deterministic ARIMA filter/forecaster.

    V1 supports d in {0, 1}. Coefficients are supplied by configuration or an
    external estimator; this class performs stateful filtering and one-step
    forecasting without introducing a heavy estimation dependency.
    """

    intercept: float = 0.0
    ar: tuple[float, ...] = ()
    ma: tuple[float, ...] = ()
    difference_order: int = 0
    _levels: list[float] = field(default_factory=list, init=False, repr=False)
    _diffs: list[float] = field(default_factory=list, init=False, repr=False)
    _residuals: list[float] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.difference_order not in (0, 1):
            raise ValueError("V1 supports ARIMA difference_order 0 or 1 only")

    @property
    def last_level(self) -> float | None:
        return self._levels[-1] if self._levels else None

    @property
    def observations(self) -> tuple[float, ...]:
        return tuple(self._levels)

    def _stationary_forecast(self, series: list[float]) -> float:
        prediction = float(self.intercept)
        for lag, coefficient in enumerate(self.ar, start=1):
            if len(series) >= lag:
                prediction += coefficient * series[-lag]
        for lag, coefficient in enumerate(self.ma, start=1):
            if len(self._residuals) >= lag:
                prediction += coefficient * self._residuals[-lag]
        return prediction

    def observe(self, value: float) -> float:
        value = float(value)
        if self.difference_order == 0:
            prediction = self._stationary_forecast(self._levels)
            self._residuals.append(value - prediction)
            self._levels.append(value)
            return prediction

        if not self._levels:
            self._levels.append(value)
            return value

        difference = value - self._levels[-1]
        prediction = self._stationary_forecast(self._diffs)
        self._residuals.append(difference - prediction)
        self._diffs.append(difference)
        self._levels.append(value)
        return self._levels[-2] + prediction

    def forecast(self) -> float:
        if self.difference_order == 0:
            return self._stationary_forecast(self._levels)
        if not self._levels:
            return float(self.intercept)
        return self._levels[-1] + self._stationary_forecast(self._diffs)


@dataclass(frozen=True, slots=True)
class HawkesKernel:
    source_kind: DriveKind
    target_kind: DriveKind
    alpha: float
    beta: float

    def __post_init__(self) -> None:
        if self.beta <= 0:
            raise ValueError("Hawkes beta must be positive")


@dataclass(frozen=True, slots=True)
class MotiveEvent:
    target: str
    kind: DriveKind
    at_seconds: float
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class TemporalIntensity:
    target: str
    kind: DriveKind
    at_seconds: float
    baseline: float
    excitation: float
    total: float
    activation: float


class MotiveTemporalModel:
    """ARIMA baseline plus typed multivariate Hawkes excitation.

    Slow state is represented by per-target/per-drive ARIMA baselines. Fast
    path-dependent bursts are represented by Hawkes kernels over motive events.
    Positive excitation is constrained to a conservative subcritical regime.
    """

    def __init__(
        self,
        kernels: list[HawkesKernel] | tuple[HawkesKernel, ...] = (),
        *,
        stability_limit: float = 1.0,
    ) -> None:
        if not 0.0 < stability_limit <= 1.0:
            raise ValueError("stability_limit must be in (0, 1]")
        self.kernels = tuple(kernels)
        self.stability_limit = float(stability_limit)
        self._baselines: dict[tuple[str, DriveKind], ARIMABaseline] = {}
        self._events: list[MotiveEvent] = []
        self._validate_subcritical()

    @property
    def events(self) -> tuple[MotiveEvent, ...]:
        return tuple(self._events)

    def _validate_subcritical(self) -> None:
        incoming_mass: dict[DriveKind, float] = {}
        for kernel in self.kernels:
            if kernel.alpha <= 0:
                continue
            incoming_mass[kernel.target_kind] = (
                incoming_mass.get(kernel.target_kind, 0.0)
                + kernel.alpha / kernel.beta
            )
        if any(value >= self.stability_limit for value in incoming_mass.values()):
            raise ValueError("supercritical Hawkes excitation is not allowed")

    def set_baseline(
        self,
        target: str,
        kind: DriveKind,
        baseline: ARIMABaseline,
    ) -> None:
        self._baselines[(target, kind)] = baseline

    def baseline(self, target: str, kind: DriveKind) -> ARIMABaseline | None:
        return self._baselines.get((target, kind))

    def observe_baseline(
        self,
        target: str,
        kind: DriveKind,
        value: float,
    ) -> float:
        baseline = self._baselines.get((target, kind))
        if baseline is None:
            baseline = ARIMABaseline()
            self._baselines[(target, kind)] = baseline
        return baseline.observe(value)

    def observe_event(
        self,
        target: str,
        kind: DriveKind,
        *,
        at_seconds: float,
        weight: float = 1.0,
    ) -> MotiveEvent:
        if at_seconds < 0:
            raise ValueError("event time must be non-negative")
        if weight < 0:
            raise ValueError("event weight must be non-negative")
        event = MotiveEvent(
            target=target,
            kind=kind,
            at_seconds=float(at_seconds),
            weight=float(weight),
        )
        self._events.append(event)
        return event

    def intensity(
        self,
        target: str,
        kind: DriveKind,
        *,
        at_seconds: float,
    ) -> TemporalIntensity:
        if at_seconds < 0:
            raise ValueError("query time must be non-negative")

        baseline_model = self._baselines.get((target, kind))
        baseline = 0.0 if baseline_model is None else max(0.0, baseline_model.forecast())

        excitation = 0.0
        for kernel in self.kernels:
            if kernel.target_kind is not kind:
                continue
            for event in self._events:
                if event.target != target or event.kind is not kernel.source_kind:
                    continue
                if event.at_seconds > at_seconds:
                    continue
                elapsed = at_seconds - event.at_seconds
                excitation += (
                    kernel.alpha
                    * event.weight
                    * exp(-kernel.beta * elapsed)
                )

        total = max(0.0, baseline + excitation)
        activation = 1.0 - exp(-total)
        return TemporalIntensity(
            target=target,
            kind=kind,
            at_seconds=float(at_seconds),
            baseline=baseline,
            excitation=excitation,
            total=total,
            activation=activation,
        )

    def signal(
        self,
        target: str,
        kind: DriveKind,
        *,
        at_seconds: float,
        confidence: float = 1.0,
    ) -> Signal:
        result = self.intensity(target, kind, at_seconds=at_seconds)
        return Signal(
            target=target,
            kind=kind,
            magnitude=result.activation,
            confidence=confidence,
            provenance=ProvenanceClass.SYSTEM_STATE,
            source="temporal:hawkes-arima",
        )
