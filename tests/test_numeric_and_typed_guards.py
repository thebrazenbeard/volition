"""Untrusted motive values must not manufacture eligibility or corrupt time."""

from dataclasses import replace
import math

import pytest

from volition import DriveKind, Policy, ProvenanceClass, Signal, VolitionEngine, Want


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


def test_snapshot_restore_rejects_goal_score_promotion_over_linked_choice():
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    snapshot = engine.snapshot()
    assert snapshot["active_goal"]["adoption_score"] < 1.0
    snapshot["active_goal"]["adoption_score"] = 1.0
    with pytest.raises(ValueError, match="goal.*score.*choice"):
        VolitionEngine.from_snapshot(snapshot)


def test_snapshot_round_trip_preserves_valid_goal_reappraisal_score():
    engine = VolitionEngine(Policy(goal_reappraisal_seconds=1))
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP, magnitude=0.8)])
    engine.advance(2)
    revised = engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP, magnitude=0.9)])
    assert revised.revision == 2
    assert revised.adoption_score == pytest.approx(0.9)
    assert engine.choices[0].want_score == pytest.approx(0.8)
    assert VolitionEngine.from_snapshot(engine.snapshot()).snapshot() == engine.snapshot()


def test_snapshot_cannot_fake_reappraisal_revision_without_event():
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP, magnitude=0.8)])
    snapshot = engine.snapshot()
    snapshot["active_goal"]["revision"] = 2
    snapshot["active_goal"]["adoption_score"] = 0.99
    with pytest.raises(ValueError, match="reappraisal event"):
        VolitionEngine.from_snapshot(snapshot)


def test_snapshot_reappraisal_revisions_must_be_contiguous():
    engine = VolitionEngine(Policy(goal_reappraisal_seconds=1))
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP, magnitude=0.8)])
    engine.advance(2)
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP, magnitude=0.9)])
    engine.advance(2)
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP, magnitude=0.7)])
    snapshot = engine.snapshot()
    assert snapshot["active_goal"]["revision"] == 3
    assert VolitionEngine.from_snapshot(snapshot).snapshot() == snapshot
    reappraisal = next(
        event for event in snapshot["events"]
        if event["kind"] == "GOAL_REAPPRAISED"
    )
    reappraisal["details"] = [
        (key, "999" if key == "revision" else value)
        for key, value in reappraisal["details"]
    ]
    with pytest.raises(ValueError, match="reappraisal event"):
        VolitionEngine.from_snapshot(snapshot)


@pytest.mark.parametrize("invalid", [True, 1.5, "2", 0, -1, None])
def test_snapshot_rejects_invalid_goal_revision(invalid):
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    snapshot = engine.snapshot()
    snapshot["active_goal"]["revision"] = invalid
    with pytest.raises(ValueError, match="revision.*integer"):
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


@pytest.mark.parametrize("field", ["goal_counter", "choice_counter", "endogenous_turns"])
@pytest.mark.parametrize("invalid", [True, False, 1.9, "1", None])
def test_snapshot_counters_reject_untyped_or_fractional_values(field, invalid):
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    snapshot = engine.snapshot()
    snapshot[field] = invalid
    with pytest.raises(ValueError, match="integer"):
        VolitionEngine.from_snapshot(snapshot)


@pytest.mark.parametrize("invalid", [True, False, 1.9, "1", None])
def test_snapshot_event_sequence_rejects_untyped_or_fractional_values(invalid):
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    snapshot = engine.snapshot()
    snapshot["events"][0]["sequence"] = invalid
    with pytest.raises(ValueError, match="integer"):
        VolitionEngine.from_snapshot(snapshot)


def test_snapshot_valid_integer_counters_and_event_sequence_round_trip():
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    engine.request_cognition()
    snapshot = engine.snapshot()
    assert VolitionEngine.from_snapshot(snapshot).snapshot() == snapshot


def test_snapshot_choice_id_cannot_be_ahead_of_its_counter():
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    snapshot = engine.snapshot()
    snapshot["choices"][0]["choice_id"] = "choice-0002"
    snapshot["active_goal"]["choice_id"] = "choice-0002"
    with pytest.raises(ValueError, match="choice.*counter"):
        VolitionEngine.from_snapshot(snapshot)


def test_snapshot_active_goal_id_cannot_be_ahead_of_its_counter():
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    snapshot = engine.snapshot()
    snapshot["active_goal"]["goal_id"] = "goal-0002"
    with pytest.raises(ValueError, match="goal.*counter"):
        VolitionEngine.from_snapshot(snapshot)


@pytest.mark.parametrize("field,invalid_id", [
    ("choice", "choice-untracked"),
    ("goal", "goal-0000"),
])
def test_snapshot_rejects_noncanonical_generated_ids(field, invalid_id):
    engine = VolitionEngine()
    engine.tick([valid_signal(kind=DriveKind.OPEN_LOOP)])
    snapshot = engine.snapshot()
    if field == "choice":
        snapshot["choices"][0]["choice_id"] = invalid_id
        snapshot["active_goal"]["choice_id"] = invalid_id
    else:
        snapshot["active_goal"]["goal_id"] = invalid_id
    with pytest.raises(ValueError, match="ID is invalid"):
        VolitionEngine.from_snapshot(snapshot)


@pytest.mark.parametrize("forged_score", [math.nan, math.inf, 1.0])
def test_forged_want_cannot_be_adopted_or_minted_as_policy_choice(forged_score):
    engine = VolitionEngine()
    forged = Want(
        target="invented_motive", score=forged_score, contributions=(),
        eligible=True, vetoed=False, reasons=(),
    )
    for attempt in (engine.choose, engine.adopt):
        with pytest.raises(ValueError, match="evaluat"):
            attempt(forged)
    assert engine.choices == ()
    assert engine.active_goal is None
    assert engine.events == ()


def test_want_from_another_engine_cannot_be_selected_as_local_evidence():
    foreign = VolitionEngine().evaluate([valid_signal(kind=DriveKind.OPEN_LOOP)])[0]
    local = VolitionEngine()
    with pytest.raises(ValueError, match="evaluat"):
        local.choose(foreign)
    assert local.choices == ()


def test_previously_evaluated_want_cannot_be_replayed_after_fresh_evaluation():
    engine = VolitionEngine()
    older = engine.evaluate([valid_signal(kind=DriveKind.OPEN_LOOP)])[0]
    current = engine.evaluate([valid_signal(kind=DriveKind.OPEN_LOOP)])[0]
    with pytest.raises(ValueError, match="evaluat"):
        engine.choose(older)
    assert engine.choose(current).want_target == "records"


def test_mutated_evaluated_want_cannot_be_selected():
    engine = VolitionEngine()
    want = engine.evaluate([valid_signal(kind=DriveKind.OPEN_LOOP)])[0]
    object.__setattr__(want, "score", 1.0)
    with pytest.raises(ValueError, match="evaluat"):
        engine.choose(want)
    assert engine.choices == ()


def test_mutated_nested_contribution_cannot_be_selected():
    engine = VolitionEngine()
    want = engine.evaluate([valid_signal(kind=DriveKind.OPEN_LOOP)])[0]
    object.__setattr__(want.contributions[0], "value", math.nan)
    with pytest.raises(ValueError, match="evaluat"):
        engine.adopt(want)
    assert engine.choices == ()


def test_elapsed_time_or_satiation_invalidates_old_evaluated_want():
    for invalidate in (
        lambda engine: engine.advance(1.0),
        lambda engine: engine.record_satisfaction("records", 0.2),
    ):
        engine = VolitionEngine()
        want = engine.evaluate([valid_signal(kind=DriveKind.OPEN_LOOP)])[0]
        invalidate(engine)
        with pytest.raises(ValueError, match="evaluat"):
            engine.choose(want)


def test_single_evaluated_want_cannot_be_chosen_twice():
    engine = VolitionEngine()
    want = engine.evaluate([valid_signal(kind=DriveKind.OPEN_LOOP)])[0]
    engine.choose(want)
    with pytest.raises(ValueError, match="evaluat"):
        engine.choose(want)
    assert len(engine.choices) == 1


@pytest.mark.parametrize("field,invalid", [
    ("target", None), ("target", ""), ("target", "   "),
    ("source", None), ("source", ""), ("source", "   "),
])
def test_untyped_or_blank_signal_identity_cannot_create_goals(field, invalid):
    engine = VolitionEngine()
    with pytest.raises(ValueError, match=field):
        engine.tick([valid_signal(**{field: invalid})])
    assert engine.active_goal is None
    assert engine.choices == ()
