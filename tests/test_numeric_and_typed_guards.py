"""Untrusted motive values must not manufacture eligibility or corrupt time."""

from dataclasses import replace
import math

import pytest

from volition import DriveKind, Policy, ProvenanceClass, Signal, VolitionEngine


def valid_signal(**overrides):
    return replace(
        Signal(
            target="records",
            kind=DriveKind.EPISTEMIC,
            magnitude=0.8,
            expected_information_gain=0.5,
            source="test:observed",
        ),
        **overrides,
    )


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize(
    "field",
    [
        "magnitude", "confidence", "expected_information_gain",
        "learning_progress", "controllability", "predicted_deficit_reduction",
    ],
)
def test_nonfinite_signal_fields_are_rejected_before_arbitration(field, invalid):
    engine = VolitionEngine()
    with pytest.raises(ValueError, match="finite"):
        engine.evaluate([valid_signal(**{field: invalid})])
    assert not engine.choices
    assert engine.active_goal is None


def test_raw_string_historical_provenance_cannot_bypass_currentness_gate():
    engine = VolitionEngine()
    with pytest.raises(ValueError, match="provenance"):
        engine.evaluate([
            valid_signal(
                kind=DriveKind.OPEN_LOOP,
                provenance=ProvenanceClass.HISTORICAL_EVIDENCE.value,
                current_reappraisal=False,
            )
        ])
    historical = valid_signal(
        kind=DriveKind.OPEN_LOOP,
        provenance=ProvenanceClass.HISTORICAL_EVIDENCE,
        current_reappraisal=False,
    )
    want = engine.evaluate([historical])[0]
    assert want.score == 0
    assert not want.eligible


def test_raw_string_epistemic_kind_cannot_bypass_information_gain_gate():
    engine = VolitionEngine()
    with pytest.raises(ValueError, match="kind"):
        engine.evaluate([valid_signal(kind=DriveKind.EPISTEMIC.value, expected_information_gain=0)])
    want = engine.evaluate([valid_signal(expected_information_gain=0)])[0]
    assert want.score == 0
    assert not want.eligible


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf])
def test_nonfinite_clock_advance_fails_without_mutating_state(invalid):
    engine = VolitionEngine()
    engine.advance(2.5)
    with pytest.raises(ValueError, match="finite"):
        engine.advance(invalid)
    assert engine.elapsed_seconds == 2.5


@pytest.mark.parametrize(
    "field",
    [
        "want_threshold", "protection_veto", "switch_margin", "social_cap",
        "empowerment_cap", "satiation_half_life_seconds",
        "goal_reappraisal_seconds",
    ],
)
def test_nonfinite_policy_fields_rejected(field):
    with pytest.raises(ValueError, match="finite"):
        Policy(**{field: math.nan})


def test_cognition_budget_must_be_bounded_integer():
    for invalid in (math.inf, math.nan, -1, 1.2, True):
        with pytest.raises(ValueError, match="budget"):
            Policy(endogenous_turn_budget=invalid)


@pytest.mark.parametrize("field", ["elapsed_seconds", "satiation", "choice_score", "goal_time", "event_time"])
def test_snapshot_restore_rejects_nonfinite_state(field):
    engine = VolitionEngine()
    want = engine.evaluate([valid_signal(kind=DriveKind.OPEN_LOOP, magnitude=0.9)])[0]
    engine.adopt(want)
    snapshot = engine.snapshot()
    if field == "elapsed_seconds":
        snapshot["elapsed_seconds"] = math.nan
    elif field == "satiation":
        snapshot["satiation"]["records"] = math.inf
    elif field == "choice_score":
        snapshot["choices"][0]["want_score"] = math.nan
    elif field == "goal_time":
        snapshot["active_goal"]["adopted_at_seconds"] = math.inf
    else:
        snapshot["events"][0]["at_seconds"] = math.nan
    with pytest.raises(ValueError, match="finite"):
        VolitionEngine.from_snapshot(snapshot)


def test_valid_typed_signals_and_snapshot_round_trip_remain_unchanged():
    engine = VolitionEngine()
    typed = valid_signal()
    want = engine.evaluate([typed])[0]
    assert want.score == pytest.approx(0.4)
    assert want.eligible
    engine.adopt(want)
    assert VolitionEngine.from_snapshot(engine.snapshot()).snapshot() == engine.snapshot()


def test_snapshot_restore_rejects_forged_goal_choice_target_lineage():
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP, target="approved_target")])
    snapshot = engine.snapshot()
    assert snapshot["active_goal"]["target"] == snapshot["choices"][0]["want_target"]
    snapshot["active_goal"]["target"] = "different_target"
    with pytest.raises(ValueError, match="goal target does not match choice"):
        VolitionEngine.from_snapshot(snapshot)


def test_snapshot_restore_rejects_future_goal_adoption_time():
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    snapshot = engine.snapshot()
    snapshot["active_goal"]["adopted_at_seconds"] = 24 * 3600.0
    with pytest.raises(ValueError, match="future adoption"):
        VolitionEngine.from_snapshot(snapshot)


def test_snapshot_restore_rejects_future_or_reordered_transition_receipts():
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    snapshot = engine.snapshot()
    snapshot["events"][-1]["at_seconds"] = 24 * 3600.0
    with pytest.raises(ValueError, match="event time exceeds"):
        VolitionEngine.from_snapshot(snapshot)

    engine.advance(5.0)
    engine.record_satisfaction("records", 0.1)
    snapshot = engine.snapshot()
    assert snapshot["events"][-1]["at_seconds"] == 5.0
    snapshot["events"][-1]["at_seconds"] = -1.0
    with pytest.raises(ValueError, match="event time is not monotonic"):
        VolitionEngine.from_snapshot(snapshot)


@pytest.mark.parametrize("value", [True, False, "0.5", "1", None])
def test_numeric_fields_reject_bool_string_or_null_coercion(value):
    engine = VolitionEngine()
    with pytest.raises(ValueError, match="numeric"):
        engine.evaluate([valid_signal(magnitude=value)])
    with pytest.raises(ValueError, match="numeric"):
        Policy(want_threshold=value)
    with pytest.raises(ValueError, match="numeric"):
        engine.advance(value)


@pytest.mark.parametrize("field", [
    "want_threshold", "protection_veto", "switch_margin", "social_cap", "empowerment_cap",
])
@pytest.mark.parametrize("invalid", [-0.01, 1.01])
def test_unit_policy_controls_reject_out_of_range_thresholds(field, invalid):
    with pytest.raises(ValueError, match=r"within \[0, 1\]"):
        Policy(**{field: invalid})


@pytest.mark.parametrize("field", ["choice", "goal", "satiation"])
def test_snapshot_restore_rejects_out_of_range_want_goal_satiation(field):
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    snapshot = engine.snapshot()
    if field == "choice":
        snapshot["choices"][0]["want_score"] = 1e100
    elif field == "goal":
        snapshot["active_goal"]["adoption_score"] = 1e100
    else:
        snapshot["satiation"] = {"records": -1.0}
    with pytest.raises(ValueError, match=r"within \[0, 1\]"):
        VolitionEngine.from_snapshot(snapshot)


def test_clock_advance_rejects_accumulation_overflow_atomically():
    engine = VolitionEngine()
    engine.advance(1e308)
    snapshot = engine.snapshot()
    with pytest.raises(ValueError, match="finite"):
        engine.advance(1e308)
    assert engine.snapshot() == snapshot
