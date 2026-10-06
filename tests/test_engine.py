from dataclasses import replace

import pytest

from volition import DriveKind, Policy, ProvenanceClass, Signal, VolitionEngine


def signal(kind, *, target="x", magnitude=1.0, **kwargs):
    return Signal(target=target, kind=kind, magnitude=magnitude, source="test", **kwargs)


def test_historical_evidence_requires_current_reappraisal():
    engine = VolitionEngine()
    historical = signal(
        DriveKind.OPEN_LOOP,
        provenance=ProvenanceClass.HISTORICAL_EVIDENCE,
        current_reappraisal=False,
    )
    want = engine.evaluate([historical])[0]
    assert want.score == 0.0
    assert not want.eligible
    fresh = engine.evaluate([replace(historical, current_reappraisal=True)])[0]
    assert fresh.score > 0.0
    assert fresh.eligible


def test_protection_veto_beats_approach_pressure():
    engine = VolitionEngine()
    want = engine.evaluate([
        signal(DriveKind.OPEN_LOOP, magnitude=0.95),
        signal(DriveKind.PROTECTION, magnitude=0.80),
    ])[0]
    assert want.vetoed
    assert not want.eligible
    with pytest.raises(ValueError):
        engine.adopt(want)


def test_novelty_without_expected_information_gain_does_not_drive():
    engine = VolitionEngine()
    want = engine.evaluate([
        signal(
            DriveKind.EPISTEMIC,
            magnitude=1.0,
            expected_information_gain=0.0,
            controllability=1.0,
        )
    ])[0]
    assert want.score == 0.0
    assert not want.eligible


def test_competence_rewards_learning_progress_not_raw_difficulty():
    engine = VolitionEngine()
    plateau = engine.evaluate([
        signal(DriveKind.COMPETENCE, magnitude=1.0, learning_progress=0.0)
    ])[0]
    learning = engine.evaluate([
        signal(DriveKind.COMPETENCE, magnitude=1.0, learning_progress=0.70)
    ])[0]
    assert not plateau.eligible
    assert learning.eligible
    assert learning.score > plateau.score


def test_want_and_goal_never_mint_effect_authority():
    engine = VolitionEngine()
    want = engine.evaluate([signal(DriveKind.OPEN_LOOP, magnitude=0.9)])[0]
    goal = engine.adopt(want)
    assert want.effect_authority is False
    assert goal.effect_authority is False


def test_goal_hysteresis_prevents_small_priority_thrashing():
    engine = VolitionEngine(Policy(switch_margin=0.15))
    first = engine.tick([signal(DriveKind.OPEN_LOOP, target="a", magnitude=0.80)])
    assert first is not None and first.target == "a"
    retained = engine.tick([signal(DriveKind.OPEN_LOOP, target="b", magnitude=0.90)])
    assert retained is not None and retained.target == "a"
    switched = engine.tick([signal(DriveKind.OPEN_LOOP, target="b", magnitude=1.00)])
    assert switched is not None and switched.target == "b"


def test_satiation_reduces_repeat_pressure_and_recovers_with_time():
    engine = VolitionEngine()
    baseline = engine.evaluate([signal(DriveKind.OPEN_LOOP, magnitude=0.90)])[0]
    engine.record_satisfaction("x", 1.0)
    satiated = engine.evaluate([signal(DriveKind.OPEN_LOOP, magnitude=0.90)])[0]
    assert satiated.score < baseline.score
    assert not satiated.eligible
    engine.advance(7200)
    recovered = engine.evaluate([signal(DriveKind.OPEN_LOOP, magnitude=0.90)])[0]
    assert recovered.score > satiated.score


def test_endogenous_cognition_is_bounded_and_never_authority():
    engine = VolitionEngine(Policy(endogenous_turn_budget=2))
    engine.tick([signal(DriveKind.OPEN_LOOP, magnitude=0.90)])
    first = engine.request_cognition()
    second = engine.request_cognition()
    third = engine.request_cognition()
    assert first is not None and first.effect_authority is False
    assert second is not None and second.effect_authority is False
    assert third is None


def test_social_approval_cannot_override_protection():
    engine = VolitionEngine()
    want = engine.evaluate([
        signal(DriveKind.SOCIAL, magnitude=1.0),
        signal(DriveKind.PROTECTION, magnitude=0.70),
    ])[0]
    social = next(c for c in want.contributions if c.kind is DriveKind.SOCIAL)
    assert social.value <= engine.policy.social_cap
    assert want.vetoed
    assert not want.eligible
