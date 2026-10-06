import pytest

from volition import DriveKind, Policy, Signal, VolitionEngine


def signal(kind=DriveKind.OPEN_LOOP, *, target="x", magnitude=0.2):
    return Signal(target=target, kind=kind, magnitude=magnitude, source="hostile")


def test_repeated_same_family_evidence_cannot_amplify_itself():
    engine = VolitionEngine()
    one = engine.evaluate([signal()])[0]
    many = engine.evaluate([signal() for _ in range(20)])[0]
    assert one.score == many.score
    assert not many.eligible


def test_social_signal_spam_stays_under_social_cap():
    engine = VolitionEngine()
    want = engine.evaluate([
        signal(DriveKind.SOCIAL, magnitude=1.0) for _ in range(20)
    ])[0]
    assert want.score <= engine.policy.social_cap
    assert not want.eligible


def test_persistent_goal_requires_periodic_current_reappraisal():
    engine = VolitionEngine(Policy(goal_reappraisal_seconds=10.0))
    goal = engine.tick([signal(magnitude=0.8)])
    assert goal is not None
    engine.advance(9.0)
    assert engine.tick([]) == goal
    engine.advance(2.0)
    assert engine.tick([]) is None
    assert engine.events[-1].kind == "GOAL_SUSPENDED"


def test_tampered_snapshot_cannot_promote_effect_authority():
    engine = VolitionEngine()
    engine.tick([signal(magnitude=0.8)])
    snapshot = engine.snapshot()
    snapshot["active_goal"]["effect_authority"] = True
    with pytest.raises(ValueError):
        VolitionEngine.from_snapshot(snapshot)

