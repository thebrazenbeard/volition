from copy import deepcopy

import pytest

from volition import DriveKind, Policy, Signal, VolitionEngine


def signal(target="x", magnitude=0.9):
    return Signal(
        target=target,
        kind=DriveKind.OPEN_LOOP,
        magnitude=magnitude,
        source="persistence-test",
    )


def test_snapshot_restore_preserves_goal_satiation_and_cognition_budget():
    engine = VolitionEngine(Policy(endogenous_turn_budget=2))
    goal = engine.tick([signal()])
    assert goal is not None
    assert engine.request_cognition() is not None
    engine.record_satisfaction("x", 0.50)
    engine.advance(600)

    restored = VolitionEngine.from_snapshot(engine.snapshot())

    assert restored.active_goal == engine.active_goal
    before = restored.evaluate([signal()])[0].score
    assert before < 0.9
    assert restored.request_cognition() is not None
    assert restored.request_cognition() is None


def test_snapshot_schema_fails_closed():
    engine = VolitionEngine()
    snapshot = engine.snapshot()
    snapshot["schema"] = "UNKNOWN_STATE"
    with pytest.raises(ValueError):
        VolitionEngine.from_snapshot(snapshot)


def test_transition_events_are_ordered_and_never_effect_authority():
    engine = VolitionEngine()
    engine.tick([signal()])
    engine.request_cognition()
    engine.record_satisfaction("x", 0.2)

    events = engine.events
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    assert [event.kind for event in events] == [
        "CHOICE_RECORDED",
        "GOAL_ADOPTED",
        "COGNITION_REQUESTED",
        "SATISFACTION_RECORDED",
    ]
    assert all(event.effect_authority is False for event in events)


def test_restored_adoption_score_cannot_contradict_persisted_adoption_receipt():
    engine = VolitionEngine()
    engine.tick([signal(magnitude=0.7)])
    valid = engine.snapshot()
    assert VolitionEngine.from_snapshot(valid).active_goal == engine.active_goal

    forged = deepcopy(valid)
    forged["choices"][0]["want_score"] = 1.0
    forged["active_goal"]["adoption_score"] = 1.0
    forged["events"][0]["details"] = [
        (key, "1.0" if key == "score" else value)
        for key, value in forged["events"][0]["details"]
    ]
    # Choice, its receipt, and goal agree, but contradict GOAL_ADOPTED.
    with pytest.raises(ValueError, match="adoption.*score|score.*adoption"):
        VolitionEngine.from_snapshot(forged)


def test_restored_choice_cannot_contradict_persisted_choice_receipt():
    engine = VolitionEngine()
    engine.tick([signal(magnitude=0.7)])
    forged = deepcopy(engine.snapshot())
    forged["choices"][0]["want_score"] = 1.0
    forged["active_goal"]["adoption_score"] = 1.0
    # The Choice record now conflicts with CHOICE_RECORDED.
    with pytest.raises(ValueError, match="choice.*receipt"):
        VolitionEngine.from_snapshot(forged)


@pytest.mark.parametrize("tamper", ["missing_choice", "late_choice"])
def test_restored_adoption_requires_prior_recorded_choice(tamper):
    engine = VolitionEngine()
    engine.tick([signal(magnitude=0.7)])
    forged = deepcopy(engine.snapshot())
    assert [event["kind"] for event in forged["events"]] == [
        "CHOICE_RECORDED", "GOAL_ADOPTED"
    ]
    if tamper == "missing_choice":
        forged["events"].pop(0)
    else:
        forged["events"].reverse()
    for index, event in enumerate(forged["events"], start=1):
        event["sequence"] = index
    with pytest.raises(ValueError, match="choice.*receipt|choice.*adoption"):
        VolitionEngine.from_snapshot(forged)


def test_restored_history_cannot_reuse_choice_for_two_goal_adoptions():
    engine = VolitionEngine()
    engine.tick([signal(magnitude=0.7)])
    forged = deepcopy(engine.snapshot())
    second_adoption = deepcopy(forged["events"][-1])
    second_adoption["sequence"] = len(forged["events"]) + 1
    second_adoption["details"] = [
        (key, "goal-0002" if key == "goal_id" else value)
        for key, value in second_adoption["details"]
    ]
    forged["events"].append(second_adoption)
    forged["active_goal"]["goal_id"] = "goal-0002"
    forged["goal_counter"] = 2
    # Live adopt_choice consumes choice-0001; replay cannot admit a second goal.
    with pytest.raises(ValueError, match="choice.*reus|reus.*choice"):
        VolitionEngine.from_snapshot(forged)
