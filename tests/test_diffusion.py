import math

import pytest

from volition import DriveKind
from volition.temporal import (
    ARIMABaseline,
    BrownianMotion,
    HawkesKernel,
    MotiveTemporalModel,
    OrnsteinUhlenbeck,
)


def test_brownian_motion_uses_sqrt_time_innovation_scaling():
    process = BrownianMotion(value=1.0, drift=0.2, volatility=0.5)

    value = process.advance(4.0, innovation=1.0)

    assert value == pytest.approx(1.0 + 0.2 * 4.0 + 0.5 * math.sqrt(4.0))
    assert process.elapsed_seconds == 4.0


def test_ornstein_uhlenbeck_reverts_toward_mean_without_noise():
    process = OrnsteinUhlenbeck(
        value=1.0,
        mean=0.0,
        reversion_rate=0.5,
        volatility=0.2,
    )

    first = process.advance(1.0, innovation=0.0)
    second = process.advance(1.0, innovation=0.0)

    assert 0.0 < second < first < 1.0


def test_diffusion_adjusts_slow_baseline_without_becoming_hawkes_excitation():
    model = MotiveTemporalModel()
    model.set_baseline(
        "task",
        DriveKind.OPEN_LOOP,
        ARIMABaseline(intercept=0.4),
    )
    model.set_diffusion(
        "task",
        DriveKind.OPEN_LOOP,
        OrnsteinUhlenbeck(
            value=0.2,
            mean=0.0,
            reversion_rate=0.5,
            volatility=0.1,
        ),
    )

    result = model.intensity("task", DriveKind.OPEN_LOOP, at_seconds=1.0)

    assert result.arima_baseline == pytest.approx(0.4)
    assert result.diffusion == pytest.approx(0.2)
    assert result.baseline == pytest.approx(0.6)
    assert result.excitation == 0.0


def test_diffusion_step_is_explicit_and_replayable():
    model = MotiveTemporalModel()
    model.set_diffusion(
        "task",
        DriveKind.OPEN_LOOP,
        BrownianMotion(value=0.0, drift=0.0, volatility=0.3),
    )

    first = model.advance_diffusion(
        "task",
        DriveKind.OPEN_LOOP,
        seconds=4.0,
        innovation=1.0,
    )
    second = model.advance_diffusion(
        "task",
        DriveKind.OPEN_LOOP,
        seconds=4.0,
        innovation=-1.0,
    )

    assert first == pytest.approx(0.6)
    assert second == pytest.approx(0.0)


def test_negative_diffusion_cannot_make_total_intensity_negative():
    model = MotiveTemporalModel()
    model.set_baseline(
        "task",
        DriveKind.OPEN_LOOP,
        ARIMABaseline(intercept=0.1),
    )
    model.set_diffusion(
        "task",
        DriveKind.OPEN_LOOP,
        BrownianMotion(value=-0.5, drift=0.0, volatility=0.0),
    )

    result = model.intensity("task", DriveKind.OPEN_LOOP, at_seconds=0.0)

    assert result.baseline == 0.0
    assert result.total == 0.0
    assert result.activation == 0.0


def test_ou_is_preferred_for_bounded_mean_reverting_noise_but_hawkes_history_remains_separate():
    model = MotiveTemporalModel(
        kernels=[
            HawkesKernel(
                source_kind=DriveKind.OPEN_LOOP,
                target_kind=DriveKind.OPEN_LOOP,
                alpha=0.2,
                beta=1.0,
            )
        ]
    )
    model.set_baseline("x", DriveKind.OPEN_LOOP, ARIMABaseline(intercept=0.3))
    model.set_diffusion(
        "x",
        DriveKind.OPEN_LOOP,
        OrnsteinUhlenbeck(
            value=0.1,
            mean=0.0,
            reversion_rate=0.25,
            volatility=0.05,
        ),
    )
    model.observe_event("x", DriveKind.OPEN_LOOP, at_seconds=0.0)

    result = model.intensity("x", DriveKind.OPEN_LOOP, at_seconds=1.0)

    assert result.diffusion == pytest.approx(0.1)
    assert result.excitation > 0.0
    assert result.total == pytest.approx(result.baseline + result.excitation)
