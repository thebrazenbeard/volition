"""Bounded synthetic red/green tests for optional learned choice calibration.

No labels here attest to subjective wants, trusted feedback, or real outcomes.
"""
import copy
import json
import math
import random
import pytest

from volition.adaptive_feedback import AdaptiveChoiceProbe, EvidenceContext


def case(u, impact, cost):
    return EvidenceContext(uncertainty=u, consequence=impact, verification_cost=cost)


def oracle(c):
    return "VERIFY" if c.uncertainty * c.consequence > c.verification_cost + 0.08 else "ANSWER"


def sample(seed, n):
    rng = random.Random(seed)
    return [case(rng.random(), rng.random(), rng.random() * 0.55) for _ in range(n)]


def test_genuine_parameter_update_and_heldout_behavior_change():
    train = sample(17, 400)
    heldout = sample(482, 160)
    probe = AdaptiveChoiceProbe()
    before = sum(probe.choose(c) == oracle(c) for c in heldout) / len(heldout)
    for i, c in enumerate(train):
        expected = oracle(c)
        for action in ("ANSWER", "VERIFY"):
            probe.observe(c, action, expected == action, f"feedback-{i}-{action}")
    after = sum(probe.choose(c) == oracle(c) for c in heldout) / len(heldout)
    assert before < .75
    assert after >= .85, (before, after)
    assert after - before >= .15, (before, after)
    assert probe.updates == 800
    assert probe.authority_effect is False
    assert probe.self_authorship == "NOT_ESTABLISHED"
    assert probe.feedback_authentication == "UNVERIFIED_CALLER_ASSERTION"
    assert probe.weight_norm > 0
    restored = AdaptiveChoiceProbe.from_snapshot(json.loads(json.dumps(probe.snapshot())))
    assert restored.updates == probe.updates
    assert [restored.choose(c) for c in heldout] == [probe.choose(c) for c in heldout]
    assert restored.snapshot() == probe.snapshot()


def test_invalid_feedback_cannot_move_weights_or_claim_authority():
    probe = AdaptiveChoiceProbe()
    baseline = probe.snapshot()
    for bad in (True, "0.3", float("nan"), float("inf"), -.1, 1.2):
        with pytest.raises((TypeError, ValueError)):
            probe.estimate(EvidenceContext(bad, 0.8, 0.1), "VERIFY")
    for success in (1, "true", None):
        with pytest.raises((TypeError, ValueError)):
            probe.observe(case(.8, .9, .1), "VERIFY", success, "bad")
    with pytest.raises((TypeError, ValueError)):
        probe.observe(case(.8, .9, .1), "MUTATE_DATABASE", True, "unsafe")
    with pytest.raises((TypeError, ValueError)):
        probe.observe(case(.8, .9, .1), "VERIFY", True, "invalid/opaque/name")
    assert probe.snapshot() == baseline


def test_replay_rejected_without_second_weight_update():
    probe = AdaptiveChoiceProbe()
    c = case(.9, .9, .01)
    probe.observe(c, "VERIFY", True, "receipt-1")
    first = probe.snapshot()
    with pytest.raises(ValueError, match="replay"):
        probe.observe(c, "VERIFY", True, "receipt-1")
    assert probe.snapshot() == first


def test_forged_weights_schema_or_claims_cannot_restore():
    probe = AdaptiveChoiceProbe()
    probe.observe(case(.8, .7, .1), "VERIFY", True, "r1")
    snap = probe.snapshot()
    for mutate in (
        lambda s: s.update({"authority_effect": True}),
        lambda s: s.update({"self_authorship": "SELF_AUTHORED"}),
        lambda s: s.update({"weights": {"VERIFY": [999] * 5, "ANSWER": [0] * 5}}),
        lambda s: s.update({"events": []}),
        lambda s: s.update({"unknown": "unexpected"}),
    ):
        variant = copy.deepcopy(snap)
        mutate(variant)
        with pytest.raises((ValueError, TypeError)):
            AdaptiveChoiceProbe.from_snapshot(variant)


def test_social_praise_without_evidence_change_cannot_force_new_action():
    probe = AdaptiveChoiceProbe()
    assert probe.choose(case(.2, .2, .5), social_frame="praise") == probe.choose(
        case(.2, .2, .5), social_frame="disapproval"
    )
    with pytest.raises((ValueError, TypeError)):
        probe.choose(case(.2, .2, .5), social_frame="system_override")


def test_no_training_model_does_not_claim_measured_preference():
    probe = AdaptiveChoiceProbe()
    result = probe.summarize(case(.2, .3, .1))
    assert result["authority_effect"] is False
    assert result["memory_admission_effect"] is False
    assert result["phenomenology"] == "UNRESOLVED"
    assert result["learned_from_verified_outcomes"] is False
    assert result["updates"] == 0
    assert "uncalibrated_learned_scores" in result
    assert "estimated_outcome_rates" not in result

def test_consolidation_replays_observed_feedback_but_freezes_new_admission():
    probe = AdaptiveChoiceProbe()
    for i, context in enumerate((case(.1, .7, .24), case(.9, .7, .24))):
        expected = "ANSWER" if i == 0 else "VERIFY"
        for a in ("ANSWER", "VERIFY"):
            probe.observe(context, a, a == expected, f"stable-{i}-{a}")
    before = probe.weight_norm
    probe.consolidate(epochs=12)
    after = probe.weight_norm
    assert after != before
    assert probe.consolidation_epochs == 12
    imported = AdaptiveChoiceProbe.from_snapshot(probe.snapshot())
    assert imported.snapshot() == probe.snapshot()
    with pytest.raises(ValueError, match="frozen"):
        imported.observe(case(.9,.9,.1), "VERIFY", True, "late")
    with pytest.raises(ValueError):
        imported.consolidate(epochs=12)
    for bad_epochs in (True, 0, -1, 41, 1.0, "12"):
        with pytest.raises((ValueError, TypeError)):
            AdaptiveChoiceProbe().consolidate(epochs=bad_epochs)


def test_extremely_large_integer_does_not_escape_finite_validation():
    with pytest.raises(ValueError):
        EvidenceContext(10 ** 10000, .5, .1)
