import math

import pytest

from volition import ARIMABaseline, DriveKind, HawkesKernel, MotiveTemporalModel
from volition.diagnostics import (
    PoissonNullModel,
    integrated_intensity,
    martingale_residual,
    time_rescaled_intervals,
)


def test_poisson_null_expected_count_and_log_likelihood():
    null = PoissonNullModel(rate=0.5)

    assert null.expected_count(0.0, 4.0) == pytest.approx(2.0)
    assert null.log_likelihood([0.5, 1.5], start=0.0, end=4.0) == pytest.approx(
        2 * math.log(0.5) - 2.0
    )


def test_poisson_null_rejects_invalid_rate_and_window():
    with pytest.raises(ValueError):
        PoissonNullModel(rate=-0.1)
    null = PoissonNullModel(rate=0.5)
    with pytest.raises(ValueError):
        null.expected_count(2.0, 1.0)


def test_martingale_residual_is_zero_for_matching_constant_rate_count():
    model = MotiveTemporalModel()
    model.set_baseline(
        "x",
        DriveKind.OPEN_LOOP,
        ARIMABaseline(intercept=0.5),
    )
    model.observe_event("x", DriveKind.OPEN_LOOP, at_seconds=1.0)
    model.observe_event("x", DriveKind.OPEN_LOOP, at_seconds=3.0)

    residual = martingale_residual(
        model,
        "x",
        DriveKind.OPEN_LOOP,
        start=0.0,
        end=4.0,
        steps=400,
    )

    assert residual.observed_count == 2
    assert residual.compensator == pytest.approx(2.0, abs=1e-3)
    assert residual.residual == pytest.approx(0.0, abs=1e-3)


def test_hawkes_history_increases_compensator_relative_to_poisson_baseline():
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
    model.set_baseline(
        "x",
        DriveKind.OPEN_LOOP,
        ARIMABaseline(intercept=0.5),
    )
    model.observe_event("x", DriveKind.OPEN_LOOP, at_seconds=1.0)

    hawkes_mass = integrated_intensity(
        model,
        "x",
        DriveKind.OPEN_LOOP,
        start=0.0,
        end=4.0,
        steps=1200,
    )

    assert hawkes_mass > 2.0


def test_diagnostics_filter_events_by_target_and_drive_kind():
    model = MotiveTemporalModel()
    model.set_baseline("x", DriveKind.OPEN_LOOP, ARIMABaseline(intercept=0.25))
    model.observe_event("x", DriveKind.OPEN_LOOP, at_seconds=1.0)
    model.observe_event("y", DriveKind.OPEN_LOOP, at_seconds=1.0)
    model.observe_event("x", DriveKind.SOCIAL, at_seconds=1.0)

    residual = martingale_residual(
        model,
        "x",
        DriveKind.OPEN_LOOP,
        start=0.0,
        end=4.0,
        steps=200,
    )

    assert residual.observed_count == 1
    assert residual.compensator == pytest.approx(1.0, abs=1e-3)


def test_integrated_intensity_rejects_invalid_steps_or_window():
    model = MotiveTemporalModel()
    with pytest.raises(ValueError):
        integrated_intensity(
            model,
            "x",
            DriveKind.OPEN_LOOP,
            start=2.0,
            end=1.0,
        )
    with pytest.raises(ValueError):
        integrated_intensity(
            model,
            "x",
            DriveKind.OPEN_LOOP,
            start=0.0,
            end=1.0,
            steps=0,
        )


def test_time_rescaling_integrates_between_events():
    model = MotiveTemporalModel()
    model.set_baseline(
        "x",
        DriveKind.OPEN_LOOP,
        ARIMABaseline(intercept=0.5),
    )
    model.observe_event("x", DriveKind.OPEN_LOOP, at_seconds=1.0)
    model.observe_event("x", DriveKind.OPEN_LOOP, at_seconds=3.0)

    intervals = time_rescaled_intervals(
        model,
        "x",
        DriveKind.OPEN_LOOP,
        start=0.0,
        end=4.0,
        steps_per_interval=400,
    )

    assert intervals == pytest.approx((0.5, 1.0), abs=1e-3)


def test_integrated_hawkes_mass_respects_predictable_jump_boundary():
    model = MotiveTemporalModel(
        kernels=[
            HawkesKernel(
                source_kind=DriveKind.OPEN_LOOP,
                target_kind=DriveKind.OPEN_LOOP,
                alpha=0.4,
                beta=1.0,
            )
        ]
    )
    model.observe_event("x", DriveKind.OPEN_LOOP, at_seconds=1.0)

    mass = integrated_intensity(
        model,
        "x",
        DriveKind.OPEN_LOOP,
        start=0.0,
        end=2.0,
        steps=4000,
    )

    expected = 0.4 * (1.0 - math.exp(-1.0))
    assert mass == pytest.approx(expected, rel=2e-3)
