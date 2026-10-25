"""Versioned reappraisal-score evidence must never be silently invented."""

import pytest

from volition import DriveKind, Policy, Signal, VolitionEngine


def signal(magnitude):
    return Signal(target="rest", kind=DriveKind.OPEN_LOOP, magnitude=magnitude, source="current:test")


def revised_engine():
    engine = VolitionEngine(Policy(goal_reappraisal_seconds=1))
    engine.tick([signal(0.7)])
    engine.advance(2)
    engine.tick([signal(0.8)])
    engine.advance(2)
    engine.tick([signal(0.9)])
    assert engine.active_goal.revision == 3
    return engine


def reappraisal_events(snapshot):
    return [item for item in snapshot["events"] if item["kind"] == "GOAL_REAPPRAISED"]


def test_v3_scores_all_reappraisals_and_restores_valid_revisions():
    engine = revised_engine()
    snapshot = engine.snapshot()
    assert snapshot["schema"] == "VOLITION_STATE_V3"
    assert [dict(event["details"])["score"] for event in reappraisal_events(snapshot)] == ["0.8", "0.9"]
    restored = VolitionEngine.from_snapshot(snapshot)
    assert restored.snapshot() == snapshot
    assert restored.active_goal.effect_authority is False


def test_v3_rejects_tampered_active_score_even_with_valid_reappraisal_chain():
    snapshot = revised_engine().snapshot()
    snapshot["active_goal"]["adoption_score"] = 1.0
    with pytest.raises(ValueError, match="reappraisal score"):
        VolitionEngine.from_snapshot(snapshot)


@pytest.mark.parametrize("forged", ["1.0", "nan", "inf", "-0.1", "0.9000", None])
def test_v3_rejects_corrupted_latest_scored_receipt(forged):
    snapshot = revised_engine().snapshot()
    latest = reappraisal_events(snapshot)[-1]
    latest["details"] = [
        (key, forged if key == "score" else value)
        for key, value in latest["details"]
    ]
    with pytest.raises(ValueError, match="reappraisal score|event details"):
        VolitionEngine.from_snapshot(snapshot)


def test_v3_rejects_missing_latest_scored_receipt():
    snapshot = revised_engine().snapshot()
    latest = reappraisal_events(snapshot)[-1]
    latest["details"] = [
        (key, value) for key, value in latest["details"] if key != "score"
    ]
    with pytest.raises(ValueError, match="reappraisal score"):
        VolitionEngine.from_snapshot(snapshot)


@pytest.mark.parametrize("forged_detail", [
    ("goal_id", "goal-9999"),
    ("choice_id", "choice-9999"),
    ("revision", "999"),
    ("score", "0.1"),
    ("surprise", {"nested": "untyped"}),
    ("surprise", "unknown-field"),
])
def test_v3_rejects_duplicate_or_untyped_reappraisal_details(forged_detail):
    snapshot = revised_engine().snapshot()
    latest = reappraisal_events(snapshot)[-1]
    latest["details"] = (forged_detail,) + latest["details"]
    with pytest.raises(ValueError, match="snapshot event details"):
        VolitionEngine.from_snapshot(snapshot)


@pytest.mark.parametrize("malformed", ["goal_id", ("goal_id",), (1, "value"), ("x", None)])
def test_v3_rejects_malformed_event_detail_pairs(malformed):
    snapshot = revised_engine().snapshot()
    event = snapshot["events"][0]
    event["details"] = event["details"] + (malformed,)
    with pytest.raises(ValueError, match="snapshot event details"):
        VolitionEngine.from_snapshot(snapshot)


def test_v3_rejects_unstructured_string_event_details():
    snapshot = revised_engine().snapshot()
    snapshot["events"][0]["details"] = "score=1.0"
    with pytest.raises(ValueError, match="snapshot event details"):
        VolitionEngine.from_snapshot(snapshot)


def test_v2_revised_active_goal_fails_closed_without_scored_custody():
    snapshot = revised_engine().snapshot()
    snapshot["schema"] = "VOLITION_STATE_V2"
    for event in reappraisal_events(snapshot):
        event["details"] = [
            (key, value) for key, value in event["details"] if key != "score"
        ]
    with pytest.raises(ValueError, match="legacy.*unverifiable"):
        VolitionEngine.from_snapshot(snapshot)


def test_v2_revision_downgrade_cannot_hide_existing_reappraisal_events():
    snapshot = revised_engine().snapshot()
    snapshot["schema"] = "VOLITION_STATE_V2"
    snapshot["active_goal"]["revision"] = 1
    snapshot["active_goal"]["adoption_score"] = snapshot["choices"][0]["want_score"]
    with pytest.raises(ValueError, match="revision.*contradicts"):
        VolitionEngine.from_snapshot(snapshot)


def test_v2_unrevised_goal_remains_compatible_without_silent_promotion():
    engine = VolitionEngine()
    engine.tick([signal(0.8)])
    snapshot = engine.snapshot()
    snapshot["schema"] = "VOLITION_STATE_V2"
    restored = VolitionEngine.from_snapshot(snapshot)
    assert restored.active_goal == engine.active_goal
    assert restored.snapshot()["schema"] == "VOLITION_STATE_V3"


def test_v2_unscored_historical_reappraisal_without_active_goal_remains_inert():
    engine = revised_engine()
    engine.record_satisfaction("rest", 0.8)
    assert engine.active_goal is None
    snapshot = engine.snapshot()
    snapshot["schema"] = "VOLITION_STATE_V2"
    for event in reappraisal_events(snapshot):
        event["details"] = [
            (key, value) for key, value in event["details"] if key != "score"
        ]
    restored = VolitionEngine.from_snapshot(snapshot)
    assert restored.active_goal is None
    assert VolitionEngine.from_snapshot(restored.snapshot()).active_goal is None
