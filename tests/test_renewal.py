import pytest

from volition import DriveKind
from volition.temporal import ARIMABaseline, MotiveTemporalModel, RefractoryRenewalHazard


def test_refractory_renewal_hazard_is_zero_then_recovers_toward_base_rate():
    hazard = RefractoryRenewalHazard(
        base_rate=0.6,
        refractory_seconds=2.0,
        recovery_rate=0.5,
    )

    assert hazard.hazard(0.0) == 0.0
    assert hazard.hazard(2.0) == 0.0
    early = hazard.hazard(3.0)
    late = hazard.hazard(20.0)
    assert 0.0 < early < late < 0.6
    assert late == pytest.approx(0.6, abs=1e-3)


def test_renewal_component_uses_age_since_last_matching_event():
    model = MotiveTemporalModel()
    model.set_renewal_hazard(
        "task",
        DriveKind.OPEN_LOOP,
        RefractoryRenewalHazard(
            base_rate=0.5,
            refractory_seconds=2.0,
            recovery_rate=1.0,
        ),
    )
    model.observe_event("task", DriveKind.OPEN_LOOP, at_seconds=10.0)

    refractory = model.intensity("task", DriveKind.OPEN_LOOP, at_seconds=11.0)
    recovering = model.intensity("task", DriveKind.OPEN_LOOP, at_seconds=13.0)

    assert refractory.renewal == 0.0
    assert recovering.renewal > 0.0
    assert recovering.renewal_age_seconds == pytest.approx(3.0)


def test_new_event_resets_renewal_age_and_refractory_window():
    model = MotiveTemporalModel()
    model.set_renewal_hazard(
        "task",
        DriveKind.OPEN_LOOP,
        RefractoryRenewalHazard(
            base_rate=0.5,
            refractory_seconds=2.0,
            recovery_rate=1.0,
        ),
    )
    model.observe_event("task", DriveKind.OPEN_LOOP, at_seconds=1.0)
    assert model.intensity("task", DriveKind.OPEN_LOOP, at_seconds=5.0).renewal > 0.0

    model.observe_event("task", DriveKind.OPEN_LOOP, at_seconds=5.0)
    reset = model.intensity("task", DriveKind.OPEN_LOOP, at_seconds=6.0)

    assert reset.renewal == 0.0
    assert reset.renewal_age_seconds == pytest.approx(1.0)


def test_renewal_is_separate_from_arima_baseline_and_hawkes_excitation():
    model = MotiveTemporalModel()
    model.set_baseline(
        "task",
        DriveKind.OPEN_LOOP,
        ARIMABaseline(intercept=0.2),
    )
    model.set_renewal_hazard(
        "task",
        DriveKind.OPEN_LOOP,
        RefractoryRenewalHazard(
            base_rate=0.4,
            refractory_seconds=0.0,
            recovery_rate=1.0,
        ),
    )
    model.observe_event("task", DriveKind.OPEN_LOOP, at_seconds=0.0)

    result = model.intensity("task", DriveKind.OPEN_LOOP, at_seconds=2.0)

    assert result.arima_baseline == pytest.approx(0.2)
    assert result.renewal > 0.0
    assert result.excitation == 0.0
    assert result.total == pytest.approx(result.baseline + result.renewal)


def test_no_prior_event_means_no_recurrence_hazard_yet():
    model = MotiveTemporalModel()
    model.set_renewal_hazard(
        "task",
        DriveKind.OPEN_LOOP,
        RefractoryRenewalHazard(base_rate=0.5, recovery_rate=1.0),
    )

    result = model.intensity("task", DriveKind.OPEN_LOOP, at_seconds=100.0)

    assert result.renewal == 0.0
    assert result.renewal_age_seconds is None


def test_renewal_signal_source_is_explicit():
    model = MotiveTemporalModel()
    model.set_baseline("task", DriveKind.OPEN_LOOP, ARIMABaseline(intercept=0.4))
    model.set_renewal_hazard(
        "task",
        DriveKind.OPEN_LOOP,
        RefractoryRenewalHazard(base_rate=0.3, recovery_rate=1.0),
    )
    model.observe_event("task", DriveKind.OPEN_LOOP, at_seconds=0.0)

    signal = model.signal("task", DriveKind.OPEN_LOOP, at_seconds=2.0)

    assert signal.source == "temporal:hawkes-arima-renewal"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"base_rate": -0.1},
        {"base_rate": 0.5, "refractory_seconds": -1.0},
        {"base_rate": 0.5, "recovery_rate": 0.0},
    ],
)
def test_refractory_renewal_hazard_rejects_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        RefractoryRenewalHazard(**kwargs)
