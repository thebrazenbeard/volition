"""Only exact caller-admitted outcome lineage may complete the current goal."""

from dataclasses import replace

import pytest

from volition import (
    DriveKind,
    GoalCompletionClaim,
    GoalCompletionVerifier,
    Policy,
    ProvenanceClass,
    Signal,
    VolitionEngine,
)


def motive():
    return Signal(target="rest", kind=DriveKind.OPEN_LOOP, magnitude=0.9, source="observer:test")


def claim(goal, *, outcome_event_id="outcome:1", **overrides):
    return replace(
        GoalCompletionClaim(
            outcome_event_id=outcome_event_id,
            goal_id=goal.goal_id,
            choice_id=goal.choice_id,
            goal_revision=goal.revision,
            target=goal.target,
            result_receipt_id="result:1",
            evidence_ref="evidence:independent:1",
            source_ref="observer:host:1",
            provenance=ProvenanceClass.CURRENT_OBSERVATION,
        ),
        **overrides,
    )


def admit(item):
    return GoalCompletionVerifier((item,), verifier_id="caller:outcome-review").admit(item)


def test_stale_same_target_scalar_cannot_complete_new_goal():
    engine = VolitionEngine(Policy(goal_reappraisal_seconds=0))
    previous = engine.tick([motive()])
    assert engine.tick([]) is None
    current = engine.tick([motive()])
    assert previous.goal_id != current.goal_id

    engine.record_satisfaction("rest", 0.8)
    assert engine.active_goal.goal_id == current.goal_id
    assert "GOAL_COMPLETED" not in [event.kind for event in engine.events]
    assert engine.snapshot()["satiation"]["rest"] == pytest.approx(0.8)


def test_bare_goal_completion_claim_has_no_authority():
    engine = VolitionEngine()
    goal = engine.tick([motive()])
    with pytest.raises(TypeError, match="admitted"):
        engine.complete_goal(claim(goal))
    assert engine.active_goal == goal


def test_model_generated_completion_evidence_cannot_be_admitted():
    goal = VolitionEngine().tick([motive()])
    with pytest.raises(ValueError, match="current.*provenance"):
        claim(goal, provenance=ProvenanceClass.MODEL_GENERATED)


def test_valid_caller_admitted_exact_goal_completion_is_non_executable():
    engine = VolitionEngine()
    goal = engine.tick([motive()])
    evidence = claim(goal)
    assert engine.complete_goal(admit(evidence)) is True
    assert engine.active_goal is None
    last = engine.events[-1]
    assert last.kind == "GOAL_COMPLETED"
    assert last.effect_authority is False
    assert dict(last.details)["outcome_event_id"] == evidence.outcome_event_id
    assert dict(last.details)["goal_id"] == goal.goal_id
    assert dict(last.details)["choice_id"] == goal.choice_id
    assert dict(last.details)["verifier_id"] == "caller:outcome-review"


@pytest.mark.parametrize("bad_field,bad_value", [
    ("goal_id", "goal-9999"),
    ("choice_id", "choice-9999"),
    ("target", "other"),
    ("goal_revision", 99),
])
def test_wrong_goal_choice_or_target_cannot_complete(bad_field, bad_value):
    engine = VolitionEngine()
    goal = engine.tick([motive()])
    before = engine.snapshot()
    evidence = claim(goal, **{bad_field: bad_value})
    with pytest.raises(ValueError, match="active goal"):
        engine.complete_goal(admit(evidence))
    assert engine.snapshot() == before


def test_old_goal_outcome_cannot_complete_new_same_target_goal():
    engine = VolitionEngine(Policy(goal_reappraisal_seconds=0))
    previous = engine.tick([motive()])
    assert engine.tick([]) is None
    current = engine.tick([motive()])
    before = engine.snapshot()
    with pytest.raises(ValueError, match="active goal"):
        engine.complete_goal(admit(claim(previous)))
    assert engine.active_goal == current
    assert engine.snapshot() == before


def test_same_outcome_replay_cannot_complete_a_later_goal_after_restore():
    engine = VolitionEngine()
    first = engine.tick([motive()])
    evidence = claim(first)
    assert engine.complete_goal(admit(evidence))
    restored = VolitionEngine.from_snapshot(engine.snapshot())
    second = restored.tick([motive()])
    assert second.goal_id != first.goal_id
    snapshot = restored.snapshot()
    assert restored.complete_goal(admit(evidence)) is False
    assert restored.snapshot() == snapshot
    assert restored.active_goal == second


def test_same_outcome_id_with_conflicting_evidence_fails_after_restore():
    engine = VolitionEngine()
    first = engine.tick([motive()])
    assert engine.complete_goal(admit(claim(first)))
    restored = VolitionEngine.from_snapshot(engine.snapshot())
    second = restored.tick([motive()])
    forged = claim(second, outcome_event_id="outcome:1")
    with pytest.raises(ValueError, match="outcome.*conflict"):
        restored.complete_goal(admit(forged))
    assert restored.active_goal == second


def test_current_goal_completion_does_not_grant_effect_capabilities():
    engine = VolitionEngine()
    goal = engine.tick([motive()])
    engine.complete_goal(admit(claim(goal)))
    assert all(event.effect_authority is False for event in engine.events)
    assert engine.request_cognition() is None


def test_restore_rejects_resurrection_of_completed_goal():
    engine = VolitionEngine()
    goal = engine.tick([motive()])
    still_active = engine.snapshot()["active_goal"]
    assert engine.complete_goal(admit(claim(goal)))
    completed = engine.snapshot()
    assert VolitionEngine.from_snapshot(completed).active_goal is None
    completed["active_goal"] = still_active
    with pytest.raises(ValueError, match="completed goal.*active"):
        VolitionEngine.from_snapshot(completed)


@pytest.mark.parametrize("terminal_kind", ["suspended", "replaced"])
def test_restore_rejects_resurrection_of_legacy_terminal_goal(terminal_kind):
    engine = VolitionEngine(Policy(goal_reappraisal_seconds=0 if terminal_kind == "suspended" else 9999))
    first_signal = motive() if terminal_kind == "suspended" else Signal(
        target="rest", kind=DriveKind.OPEN_LOOP, magnitude=0.5, source="observer:test"
    )
    prior = engine.tick([first_signal])
    still_active = engine.snapshot()["active_goal"]
    if terminal_kind == "suspended":
        assert engine.tick([]) is None
        assert engine.events[-1].kind == "GOAL_SUSPENDED"
    else:
        other = Signal(target="work", kind=DriveKind.OPEN_LOOP, magnitude=1.0, source="observer:test")
        successor = engine.tick([other])
        assert successor.goal_id != prior.goal_id
        assert [event.kind for event in engine.events][-3:] == [
            "GOAL_REPLACED", "CHOICE_RECORDED", "GOAL_ADOPTED"
        ]
    historical = engine.snapshot()
    assert VolitionEngine.from_snapshot(historical).active_goal == engine.active_goal
    historical["active_goal"] = still_active
    with pytest.raises(ValueError, match="(suspended|replaced) goal.*active"):
        VolitionEngine.from_snapshot(historical)


def test_restore_rejects_orphaned_legacy_terminal_receipt():
    engine = VolitionEngine(Policy(goal_reappraisal_seconds=0))
    engine.tick([motive()])
    engine.tick([])
    orphaned = engine.snapshot()
    receipt = orphaned["events"][-1]
    receipt["sequence"] = 1
    orphaned["events"] = [receipt]
    with pytest.raises(ValueError, match="legacy terminal goal lacks an active adoption"):
        VolitionEngine.from_snapshot(orphaned)


def test_restore_rejects_prior_goal_superseded_by_direct_adoption_without_replace_event():
    engine = VolitionEngine()
    previous = engine.tick([motive()])
    old_snapshot_goal = engine.snapshot()["active_goal"]
    candidate = engine.evaluate([
        Signal(target="explore", kind=DriveKind.OPEN_LOOP, magnitude=1.0, source="observer:test")
    ])[0]
    successor_choice = engine.choose(candidate, choice_class="MODEL_PROPOSED", source="observer:test")
    successor = engine.adopt_choice(successor_choice.choice_id)
    assert successor.goal_id != previous.goal_id
    assert all(event.kind != "GOAL_REPLACED" for event in engine.events)
    valid = engine.snapshot()
    assert VolitionEngine.from_snapshot(valid).active_goal == successor
    valid["active_goal"] = old_snapshot_goal
    with pytest.raises(ValueError, match="active goal.*historical adoption"):
        VolitionEngine.from_snapshot(valid)


def test_restore_rejects_dropping_active_goal_without_terminal_event():
    engine = VolitionEngine()
    goal = engine.tick([motive()])
    snapshot = engine.snapshot()
    assert VolitionEngine.from_snapshot(snapshot).active_goal == goal
    snapshot["active_goal"] = None
    with pytest.raises(ValueError, match="active goal.*historical adoption"):
        VolitionEngine.from_snapshot(snapshot)


@pytest.mark.parametrize("forged_kind", ["GOAL_REAPPRAISED", "GOAL_COMPLETED"])
def test_restore_rejects_late_event_for_goal_superseded_by_direct_adoption(forged_kind):
    engine = VolitionEngine()
    old_goal = engine.tick([motive()])
    wants = engine.evaluate([
        Signal(target="explore", kind=DriveKind.OPEN_LOOP, magnitude=1.0, source="observer:test")
    ])
    engine.adopt_choice(engine.choose(wants[0], choice_class="MODEL_PROPOSED", source="observer:test").choice_id)
    snapshot = engine.snapshot()
    forged = dict(snapshot["events"][-1])
    forged["sequence"] = len(snapshot["events"]) + 1
    forged["kind"] = forged_kind
    forged["target"] = old_goal.target
    if forged_kind == "GOAL_REAPPRAISED":
        forged["details"] = [
            ["goal_id", old_goal.goal_id], ["choice_id", old_goal.choice_id],
            ["revision", "2"], ["score", str(old_goal.adoption_score)],
        ]
    else:
        forged["details"] = [["goal_id", old_goal.goal_id], ["choice_id", old_goal.choice_id]]
    snapshot["events"].append(forged)
    with pytest.raises(ValueError, match="not the historically active goal"):
        VolitionEngine.from_snapshot(snapshot)


def test_restore_accepts_legitimate_legacy_completed_receipt():
    engine = VolitionEngine()
    goal = engine.tick([motive()])
    assert engine.complete_goal(admit(claim(goal)))
    snapshot = engine.snapshot()
    snapshot["schema"] = "VOLITION_STATE_V2"
    snapshot["events"][-1]["details"] = [["goal_id", goal.goal_id], ["choice_id", goal.choice_id]]
    assert VolitionEngine.from_snapshot(snapshot).active_goal is None


def test_restore_rejects_duplicate_persisted_goal_completion_outcome_id():
    engine = VolitionEngine()
    first = engine.tick([motive()])
    assert engine.complete_goal(admit(claim(first)))
    snapshot = engine.snapshot()
    duplicate = dict(snapshot["events"][-1])
    duplicate["sequence"] = len(snapshot["events"]) + 1
    snapshot["events"].append(duplicate)
    with pytest.raises(ValueError, match="duplicate.*outcome"):
        VolitionEngine.from_snapshot(snapshot)


def test_restore_rejects_completed_goal_event_claiming_foreign_goal_id():
    engine = VolitionEngine()
    goal = engine.tick([motive()])
    assert engine.complete_goal(admit(claim(goal)))
    snapshot = engine.snapshot()
    completed = snapshot["events"][-1]
    completed["details"] = tuple(
        (key, "goal-9999" if key == "goal_id" else value)
        for key, value in completed["details"]
    )
    with pytest.raises(ValueError, match="completion.*lineage"):
        VolitionEngine.from_snapshot(snapshot)
