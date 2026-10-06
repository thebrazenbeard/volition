import pytest

from volition import DriveKind, ProvenanceClass
from volition.temporal import ARIMABaseline, HawkesKernel, MotiveTemporalModel


def test_arima_baseline_remembers_path_not_just_present_level():
    rising = ARIMABaseline(ar=(0.6,), difference_order=1)
    jagged = ARIMABaseline(ar=(0.6,), difference_order=1)

    for value in (1.0, 2.0, 3.0):
        rising.observe(value)
    for value in (1.0, 1.0, 3.0):
        jagged.observe(value)

    assert rising.last_level == jagged.last_level == 3.0
    assert rising.forecast() != jagged.forecast()


def test_hawkes_self_excitation_decays_but_remains_history_dependent():
    model = MotiveTemporalModel(
        kernels=[
            HawkesKernel(
                source_kind=DriveKind.OPEN_LOOP,
                target_kind=DriveKind.OPEN_LOOP,
                alpha=0.4,
                beta=0.5,
            )
        ]
    )
    model.observe_event("question", DriveKind.OPEN_LOOP, at_seconds=0.0)

    near = model.intensity("question", DriveKind.OPEN_LOOP, at_seconds=1.0)
    far = model.intensity("question", DriveKind.OPEN_LOOP, at_seconds=10.0)

    assert near.excitation > far.excitation > 0.0
    assert near.total > far.total


def test_hawkes_cross_excitation_is_typed():
    model = MotiveTemporalModel(
        kernels=[
            HawkesKernel(
                source_kind=DriveKind.EPISTEMIC,
                target_kind=DriveKind.COMPETENCE,
                alpha=0.3,
                beta=1.0,
            )
        ]
    )
    model.observe_event("research", DriveKind.EPISTEMIC, at_seconds=0.0)

    competence = model.intensity("research", DriveKind.COMPETENCE, at_seconds=1.0)
    unrelated = model.intensity("research", DriveKind.SOCIAL, at_seconds=1.0)

    assert competence.excitation > 0.0
    assert unrelated.excitation == 0.0


def test_arima_baseline_and_hawkes_excitation_combine_without_collapsing_components():
    baseline = ARIMABaseline(intercept=0.2, ar=(0.5,), difference_order=0)
    baseline.observe(0.4)
    model = MotiveTemporalModel(
        kernels=[
            HawkesKernel(
                source_kind=DriveKind.OPEN_LOOP,
                target_kind=DriveKind.OPEN_LOOP,
                alpha=0.25,
                beta=0.5,
            )
        ]
    )
    model.set_baseline("task", DriveKind.OPEN_LOOP, baseline)
    model.observe_event("task", DriveKind.OPEN_LOOP, at_seconds=0.0)

    result = model.intensity("task", DriveKind.OPEN_LOOP, at_seconds=1.0)

    assert result.baseline > 0.0
    assert result.excitation > 0.0
    assert result.total == pytest.approx(result.baseline + result.excitation)
    assert 0.0 < result.activation < 1.0


def test_temporal_model_emits_system_state_signal_for_engine():
    model = MotiveTemporalModel()
    baseline = ARIMABaseline(intercept=0.6)
    model.set_baseline("finish", DriveKind.OPEN_LOOP, baseline)

    signal = model.signal("finish", DriveKind.OPEN_LOOP, at_seconds=5.0)

    assert signal.target == "finish"
    assert signal.kind is DriveKind.OPEN_LOOP
    assert signal.provenance is ProvenanceClass.SYSTEM_STATE
    assert 0.0 < signal.magnitude < 1.0
    assert signal.source == "temporal:hawkes-arima"


def test_supercritical_positive_excitation_fails_closed():
    with pytest.raises(ValueError, match="supercritical"):
        MotiveTemporalModel(
            kernels=[
                HawkesKernel(
                    source_kind=DriveKind.OPEN_LOOP,
                    target_kind=DriveKind.OPEN_LOOP,
                    alpha=1.0,
                    beta=0.5,
                )
            ]
        )


def test_inhibitory_kernel_can_reduce_intensity_but_not_make_it_negative():
    baseline = ARIMABaseline(intercept=0.2)
    model = MotiveTemporalModel(
        kernels=[
            HawkesKernel(
                source_kind=DriveKind.PROTECTION,
                target_kind=DriveKind.OPEN_LOOP,
                alpha=-0.5,
                beta=0.25,
            )
        ]
    )
    model.set_baseline("task", DriveKind.OPEN_LOOP, baseline)
    model.observe_event("task", DriveKind.PROTECTION, at_seconds=0.0)

    result = model.intensity("task", DriveKind.OPEN_LOOP, at_seconds=0.1)

    assert result.excitation < 0.0
    assert result.total == 0.0
    assert result.activation == 0.0
