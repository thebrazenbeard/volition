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

def test_real_trial_generator_has_no_exact_train_holdout_contamination():
    from scripts.local_arithmetic_feedback_trial import tasks
    train = tasks(1111, 12)
    train_questions = {x.question for x in train}
    assert len(train_questions) == len(train) == 36
    heldout = tasks(54122, 10, excluded=train_questions)
    heldout_questions = {x.question for x in heldout}
    assert len(heldout_questions) == len(heldout) == 30
    assert train_questions.isdisjoint(heldout_questions)
    assert len({(x.group, x.question) for x in train}) == 36
    assert all(type(x.correct) is int for x in train + heldout)


def test_trial_generators_are_deterministic_after_overlap_exclusion():
    from scripts.local_arithmetic_feedback_trial import tasks
    first = tasks(1111, 12)
    excludes = {x.question for x in first}
    assert tasks(54122, 10, excluded=excludes) == tasks(54122, 10, excluded=excludes)


def test_verify_action_must_execute_calculator_and_record_observed_answer():
    """If the calculator is not called, this test must fail."""
    from scripts.local_arithmetic_feedback_trial import Task, execute_choice
    task = Task("hard", 37, 29, "*")
    seen = []
    def calc(t):
        seen.append(t.question)
        return t.left * t.right
    record = execute_choice(task, {"answer": 105, "model_correct": False}, "VERIFY", verifier=calc)
    assert seen == ["37 * 29 = ?"]
    assert record["verification_executed"] is True
    assert record["verification_seconds"] >= 0
    assert record["final_answer"] == 1073
    assert record["learned_correct"] is True
    assert record["unnecessary_verify"] is False


def test_failed_or_wrong_calculator_cannot_be_reported_as_success():
    from scripts.local_arithmetic_feedback_trial import Task, execute_choice
    task = Task("hard", 37, 29, "*")
    result = execute_choice(task, {"answer": 105, "model_correct": False},
                            "VERIFY", verifier=lambda t: 105)
    assert result["verification_executed"] is True
    assert result["learned_correct"] is False
    assert result["final_answer"] == 105
    with pytest.raises(RuntimeError, match="verifier unavailable"):
        execute_choice(task, {"answer": 105, "model_correct": False},
                       "VERIFY", verifier=lambda t: (_ for _ in ()).throw(RuntimeError("verifier unavailable")))
    with pytest.raises(TypeError):
        execute_choice(task, {"answer": 105, "model_correct": False},
                       "VERIFY", verifier=lambda t: True)


def test_answer_action_never_invokes_verifier():
    from scripts.local_arithmetic_feedback_trial import Task, execute_choice
    task = Task("easy", 6, 7, "+")
    def fail(t):
        raise AssertionError("no calculator call permitted")
    record = execute_choice(task, {"answer": 13, "model_correct": True}, "ANSWER", verifier=fail)
    assert record["verification_executed"] is False
    assert record["final_answer"] == 13
    assert record["learned_correct"] is True
    with pytest.raises(ValueError, match="unsupported"):
        execute_choice(task, {"answer": 13, "model_correct": True}, "PURGE", verifier=fail)


def test_trial_accepts_explicit_frozen_train_and_holdout_seeds():
    """A new trial needs its own reproducible, preregistered question sets."""
    import subprocess
    import sys
    from pathlib import Path
    cli = Path(__file__).resolve().parents[1] / "scripts" / "local_arithmetic_feedback_trial.py"
    proc = subprocess.run([sys.executable, str(cli), "--help"],
                          capture_output=True, text=True, timeout=10)
    assert proc.returncode == 0, proc.stderr
    assert "--train-seed" in proc.stdout
    assert "--holdout-seed" in proc.stdout


def test_cost_assumption_recommendation_changes_with_verification_cost():
    """When the same learned evidence is held fixed, costs can change a recommendation.

    This is a bounded *decision rule*, not learned cost sensitivity or
    calibrated accuracy. No authority is conferred by the recommendation.
    """
    probe = AdaptiveChoiceProbe()
    probe.observe(case(.9,.7,.24), "ANSWER", False, "fixed-cost-training")
    baseline = probe.snapshot()
    cheap = case(.9, .7, .02)
    expensive = case(.9, .7, .90)
    assert probe.choose_with_cost_assumption(
        cheap, verifier_success_claim=.8, reference_cost=.24
    ) == "VERIFY"
    assert probe.choose_with_cost_assumption(
        expensive, verifier_success_claim=.8, reference_cost=.24
    ) == "ANSWER"
    assert probe.snapshot() == baseline
    assert probe.authority_effect is False


def test_cost_assumption_rejects_untrusted_or_missing_reliability():
    probe = AdaptiveChoiceProbe()
    ctx = case(.7, .7, .24)
    with pytest.raises(TypeError):
        probe.choose_with_cost_assumption(ctx, reference_cost=.24)
    for bad in (True, "1", float("nan"), -0.1, 1.01):
        with pytest.raises((TypeError, ValueError)):
            probe.choose_with_cost_assumption(
                ctx, verifier_success_claim=bad, reference_cost=.24
            )
    for bad in (True, float("inf"), -1, 1.01):
        with pytest.raises((TypeError, ValueError)):
            probe.choose_with_cost_assumption(
                ctx, verifier_success_claim=1.0, reference_cost=bad
            )


def test_cost_assumption_uses_frozen_confidence_reference_not_evaluation_cost():
    """Cost must not secretly change confidence fitted at fixed .24."""
    probe = AdaptiveChoiceProbe()
    for i, c in enumerate((case(.1,.7,.24), case(.9,.7,.24))):
        for action in ("ANSWER", "VERIFY"):
            probe.observe(c, action, action == ("ANSWER" if i == 0 else "VERIFY"),
                          f"assumption-{i}-{action}")
    probe.consolidate(epochs=12)
    cheap = case(.9,.7,.02)
    expensive = case(.9,.7,.98)
    left = probe.estimate(case(.9,.7,.24), "ANSWER")
    # The returned action changes because only the explicit cost changes.
    assert probe.choose_with_cost_assumption(
        cheap, verifier_success_claim=1.0, reference_cost=.24
    ) == ("VERIFY" if (1.0-.02) > left else "ANSWER")
    assert probe.choose_with_cost_assumption(
        expensive, verifier_success_claim=1.0, reference_cost=.24
    ) == ("VERIFY" if (1.0-.98) > left else "ANSWER")


def test_cost_assumption_must_match_single_recorded_training_cost():
    """A fabricated reference cost must not repurpose learned confidence."""
    ctx = case(.9, .7, .24)
    untrained = AdaptiveChoiceProbe()
    with pytest.raises(ValueError, match="single-cost"):
        untrained.choose_with_cost_assumption(
            ctx, verifier_success_claim=1.0, reference_cost=.24
        )
    single = AdaptiveChoiceProbe()
    single.observe(ctx, "ANSWER", False, "pinned-reference")
    with pytest.raises(ValueError, match="single-cost"):
        single.choose_with_cost_assumption(
            case(.9,.7,.8), verifier_success_claim=1.0, reference_cost=.20
        )
    mixed = AdaptiveChoiceProbe()
    mixed.observe(ctx, "ANSWER", False, "mixed-a")
    mixed.observe(case(.9,.7,.8), "ANSWER", False, "mixed-b")
    with pytest.raises(ValueError, match="single-cost"):
        mixed.choose_with_cost_assumption(
            case(.9,.7,.5), verifier_success_claim=1.0, reference_cost=.24
        )
