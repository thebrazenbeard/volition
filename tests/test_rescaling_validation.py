import math

import pytest

from volition import ARIMABaseline, DriveKind, MotiveTemporalModel
from volition.diagnostics import (
    evaluate_time_rescaled_intervals,
    time_rescaling_diagnostics,
)


def exponential_quantiles(count):
    return tuple(
        -math.log(1.0 - ((index + 0.5) / count))
        for index in range(count)
    )


def test_exponential_quantiles_have_small_uniform_ks_distance():
    result = evaluate_time_rescaled_intervals(exponential_quantiles(40))

    assert result.count == 40
    assert result.uniform_ks_statistic < 0.03
    assert result.mean_interval == pytest.approx(1.0, abs=0.05)
    assert len(result.uniform_values) == 40


def test_badly_compressed_intervals_have_large_uniform_ks_distance():
    result = evaluate_time_rescaled_intervals([0.01] * 20)

    assert result.uniform_ks_statistic > 0.9
    assert result.mean_interval == pytest.approx(0.01)


def test_lag1_correlation_exposes_serial_structure_as_screening_statistic():
    result = evaluate_time_rescaled_intervals([0.1, 0.2, 0.3, 0.4, 0.5])

    assert result.lag1_correlation == pytest.approx(1.0)


def test_empty_intervals_return_no_distributional_claim():
    result = evaluate_time_rescaled_intervals([])

    assert result.count == 0
    assert result.mean_interval is None
    assert result.variance_interval is None
    assert result.uniform_ks_statistic is None
    assert result.lag1_correlation is None
    assert result.uniform_values == ()


@pytest.mark.parametrize('bad', [[-0.1], [float('nan')], [float('inf')]])
def test_invalid_rescaled_intervals_fail_closed(bad):
    with pytest.raises(ValueError):
        evaluate_time_rescaled_intervals(bad)


def test_model_wrapper_evaluates_generated_rescaled_intervals():
    model = MotiveTemporalModel()
    model.set_baseline(
        'x',
        DriveKind.OPEN_LOOP,
        ARIMABaseline(intercept=0.5),
    )
    model.observe_event('x', DriveKind.OPEN_LOOP, at_seconds=1.0)
    model.observe_event('x', DriveKind.OPEN_LOOP, at_seconds=3.0)

    result = time_rescaling_diagnostics(
        model,
        'x',
        DriveKind.OPEN_LOOP,
        start=0.0,
        end=4.0,
        steps_per_interval=400,
    )

    assert result.count == 2
    assert result.mean_interval == pytest.approx(0.75, abs=1e-3)
    assert result.uniform_ks_statistic is not None
