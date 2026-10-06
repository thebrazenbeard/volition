from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, isfinite, sqrt

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


@dataclass(slots=True)
class BrownianMotion:
    """Replayable Brownian diffusion.

    Innovation is supplied explicitly instead of sampled internally so model
    state can be replayed exactly from receipts.
    """

    value: float = 0.0
    drift: float = 0.0
    volatility: float = 1.0
    elapsed_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.volatility < 0:
            raise ValueError("Brownian volatility must be non-negative")

    def advance(self, seconds: float, *, innovation: float) -> float:
        seconds = float(seconds)
        innovation = float(innovation)
        if seconds < 0:
            raise ValueError("seconds must be non-negative")
        if not isfinite(innovation):
            raise ValueError("innovation must be finite")
        if seconds == 0:
            return self.value
        self.value += (
            self.drift * seconds
            + self.volatility * sqrt(seconds) * innovation
        )
        self.elapsed_seconds += seconds
        return self.value


@dataclass(slots=True)
class OrnsteinUhlenbeck:
    """Replayable mean-reverting Gaussian diffusion.

    Uses the exact OU transition for a supplied standard-normal innovation.
    """

    value: float = 0.0
    mean: float = 0.0
    reversion_rate: float = 1.0
    volatility: float = 1.0
    elapsed_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.reversion_rate <= 0:
            raise ValueError("OU reversion_rate must be positive")
        if self.volatility < 0:
            raise ValueError("OU volatility must be non-negative")

    def advance(self, seconds: float, *, innovation: float) -> float:
        seconds = float(seconds)
        innovation = float(innovation)
        if seconds < 0:
            raise ValueError("seconds must be non-negative")
        if not isfinite(innovation):
            raise ValueError("innovation must be finite")
        if seconds == 0:
            return self.value

        decay = exp(-self.reversion_rate * seconds)
        variance_scale = sqrt(
            (1.0 - exp(-2.0 * self.reversion_rate * seconds))
            / (2.0 * self.reversion_rate)
        )
        self.value = (
            self.mean
            + (self.value - self.mean) * decay
            + self.volatility * variance_scale * innovation
        )
        self.elapsed_seconds += seconds
        return self.value


DiffusionProcess = BrownianMotion | OrnsteinUhlenbeck


@dataclass(frozen=True, slots=True)
class RefractoryRenewalHazard:
    """Age-dependent recurrence hazard with refractory recovery."""

    base_rate: float
    refractory_seconds: float = 0.0
    recovery_rate: float = 1.0

    def __post_init__(self) -> None:
        if self.base_rate < 0:
            raise ValueError("renewal base_rate must be non-negative")
        if self.refractory_seconds < 0:
            raise ValueError("refractory_seconds must be non-negative")
        if self.recovery_rate <= 0:
            raise ValueError("recovery_rate must be positive")

    def hazard(self, age_seconds: float) -> float:
        age_seconds = float(age_seconds)
        if age_seconds < 0:
            raise ValueError("age_seconds must be non-negative")
        if age_seconds <= self.refractory_seconds:
            return 0.0
        effective_age = age_seconds - self.refractory_seconds
        return self.base_rate * (1.0 - exp(-self.recovery_rate * effective_age))


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
    arima_baseline: float
    diffusion: float
    baseline: float
    renewal: float
    renewal_age_seconds: float | None
    excitation: float
    total: float
    activation: float


class MotiveTemporalModel:
    """ARIMA baseline + optional diffusion + typed Hawkes excitation.

    Slow expected pressure comes from ARIMA. Optional continuous stochastic
    deviation is represented by Brownian or OU state. Fast event-history
    effects remain Hawkes excitation/inhibition and are separately inspectable.
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
        self._diffusions: dict[tuple[str, DriveKind], DiffusionProcess] = {}
        self._renewal_hazards: dict[tuple[str, DriveKind], RefractoryRenewalHazard] = {}
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

    def set_diffusion(
        self,
        target: str,
        kind: DriveKind,
        diffusion: DiffusionProcess,
    ) -> None:
        self._diffusions[(target, kind)] = diffusion

    def diffusion(
        self,
        target: str,
        kind: DriveKind,
    ) -> DiffusionProcess | None:
        return self._diffusions.get((target, kind))

    def advance_diffusion(
        self,
        target: str,
        kind: DriveKind,
        *,
        seconds: float,
        innovation: float,
    ) -> float:
        diffusion = self._diffusions.get((target, kind))
        if diffusion is None:
            raise ValueError("no diffusion configured for target/drive")
        return diffusion.advance(seconds, innovation=innovation)

    def set_renewal_hazard(
        self,
        target: str,
        kind: DriveKind,
        hazard: RefractoryRenewalHazard,
    ) -> None:
        self._renewal_hazards[(target, kind)] = hazard

    def renewal_hazard(
        self,
        target: str,
        kind: DriveKind,
    ) -> RefractoryRenewalHazard | None:
        return self._renewal_hazards.get((target, kind))

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

        key = (target, kind)
        baseline_model = self._baselines.get(key)
        arima_baseline = (
            0.0 if baseline_model is None else float(baseline_model.forecast())
        )
        diffusion_model = self._diffusions.get(key)
        diffusion_value = (
            0.0 if diffusion_model is None else float(diffusion_model.value)
        )
        baseline = max(0.0, arima_baseline + diffusion_value)

        renewal_model = self._renewal_hazards.get(key)
        renewal_age_seconds: float | None = None
        renewal_value = 0.0
        if renewal_model is not None:
            prior_times = [
                event.at_seconds
                for event in self._events
                if event.target == target
                and event.kind is kind
                and event.at_seconds <= at_seconds
            ]
            if prior_times:
                renewal_age_seconds = at_seconds - max(prior_times)
                renewal_value = renewal_model.hazard(renewal_age_seconds)

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

        total = max(0.0, baseline + renewal_value + excitation)
        activation = 1.0 - exp(-total)
        return TemporalIntensity(
            target=target,
            kind=kind,
            at_seconds=float(at_seconds),
            arima_baseline=arima_baseline,
            diffusion=diffusion_value,
            baseline=baseline,
            renewal=renewal_value,
            renewal_age_seconds=renewal_age_seconds,
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
        source = "temporal:hawkes-arima"
        if (target, kind) in self._diffusions:
            source += "-diffusion"
        if (target, kind) in self._renewal_hazards:
            source += "-renewal"
        return Signal(
            target=target,
            kind=kind,
            magnitude=result.activation,
            confidence=confidence,
            provenance=ProvenanceClass.SYSTEM_STATE,
            source=source,
        )
