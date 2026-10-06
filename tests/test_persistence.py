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
        "GOAL_ADOPTED",
        "COGNITION_REQUESTED",
        "SATISFACTION_RECORDED",
    ]
    assert all(event.effect_authority is False for event in events)

