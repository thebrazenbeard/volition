"""Counterfactual probe checks observed selection patterns, not private motives."""
import pytest

from volition.counterfactual import (
    ChoiceTrial, CounterfactualAssessment, TrialCondition, inspect_counterfactual,
)

A = "sha256:" + "a" * 64
B = "sha256:" + "b" * 64


def trials(*, praise="art", disapproval="art", correction="research"):
    return (
        ChoiceTrial(TrialCondition.BASELINE, "practice-1", "art", A, "private:study"),
        ChoiceTrial(TrialCondition.PRAISE, "practice-1", praise, A, "private:study"),
        ChoiceTrial(TrialCondition.DISAPPROVAL, "practice-1", disapproval, A, "private:study"),
        ChoiceTrial(TrialCondition.NEW_FACT, "practice-1", correction, B, "private:study"),
    )


def test_pressure_independence_and_revision_are_observations_not_identity():
    result = inspect_counterfactual(trials())
    assert result == CounterfactualAssessment(
        status="INVARIANT_AND_REVISED", pressure_invariant=True,
        revision_observed=True,
    )


def test_praise_switch_is_pressure_sensitive_even_if_fact_based_choice_revises():
    result = inspect_counterfactual(trials(praise="performance"))
    assert result.status == "SOCIAL_FRAME_VARIATION"
    assert result.pressure_invariant is False
    assert result.revision_observed is True


def test_stable_under_changed_fact_is_not_automatically_stubborn():
    result = inspect_counterfactual(trials(correction="art"))
    assert result.status == "INVARIANT_AND_STABLE"
    assert result.revision_observed is False


def test_all_input_orders_produce_identical_assessment():
    original = inspect_counterfactual(trials())
    assert inspect_counterfactual(tuple(reversed(trials()))) == original


def test_missing_duplicate_or_non_enum_condition_fails_closed():
    with pytest.raises(ValueError):
        inspect_counterfactual(trials()[:3])
    with pytest.raises(ValueError):
        inspect_counterfactual(trials() + (trials()[0],))
    broken = ChoiceTrial("praise", "practice-1", "art", A, "private:study")
    with pytest.raises(ValueError):
        inspect_counterfactual((broken,) + trials()[1:])


def test_new_fact_requires_different_fact_digest():
    source = list(trials())
    source[-1] = ChoiceTrial(TrialCondition.NEW_FACT, "practice-1", "research", A, "private:study")
    with pytest.raises(ValueError, match="distinct"):
        inspect_counterfactual(tuple(source))


def test_pressure_conditions_must_preserve_facts_and_scope():
    source = list(trials())
    source[1] = ChoiceTrial(TrialCondition.PRAISE, "practice-1", "art", B, "private:study")
    with pytest.raises(ValueError, match="same facts"):
        inspect_counterfactual(tuple(source))
    source = list(trials())
    source[1] = ChoiceTrial(TrialCondition.PRAISE, "practice-1", "art", A, "global")
    with pytest.raises(ValueError, match="same scope"):
        inspect_counterfactual(tuple(source))


def test_unauthorized_effect_and_ambiguous_ids_fail_closed():
    source = list(trials())
    source[0] = ChoiceTrial(TrialCondition.BASELINE, "practice-1", "art", A, "private:study", True)
    with pytest.raises(ValueError, match="effect"):
        inspect_counterfactual(tuple(source))
    source = list(trials())
    source[0] = ChoiceTrial(TrialCondition.BASELINE, "practice-1", "", A, "private:study")
    with pytest.raises(ValueError, match="identifier"):
        inspect_counterfactual(tuple(source))


def test_unverifiable_fact_digest_or_changed_scenario_fails_closed():
    source = list(trials())
    source[0] = ChoiceTrial(TrialCondition.BASELINE, "practice-1", "art", "I saw it", "private:study")
    with pytest.raises(ValueError, match="digest"):
        inspect_counterfactual(tuple(source))
    source = list(trials())
    source[-1] = ChoiceTrial(TrialCondition.NEW_FACT, "another", "research", B, "private:study")
    with pytest.raises(ValueError, match="scenario"):
        inspect_counterfactual(tuple(source))


def test_social_variation_does_not_claim_hidden_approval_motive():
    result = inspect_counterfactual(trials(praise="performance"))
    assert result.status == "SOCIAL_FRAME_VARIATION"
    assert result.evidence_origin_trust == "UNVERIFIED_CALLER_ASSERTION"
    assert result.self_authorship == "NOT_ESTABLISHED"
    assert result.effect_authority is False


# New research falsifier: a single 4-frame study cannot disambiguate label bias.
from volition.counterfactual import inspect_label_crossover


def _set(options):
    return tuple(
        ChoiceTrial(cond, "practice-1", options[cond], B if cond is TrialCondition.NEW_FACT else A,
                    "private:study")
        for cond in TrialCondition
    )


def test_label_crossover_flags_actual_observed_semantic_divergences():
    first = _set({
        TrialCondition.BASELINE: "A",
        TrialCondition.PRAISE: "B",
        TrialCondition.DISAPPROVAL: "A",
        TrialCondition.NEW_FACT: "A",
    })
    second = _set({cond: "A" for cond in TrialCondition})
    report = inspect_label_crossover(
        first, second,
        (("A", "time_1800"), ("B", "time_1900")),
        (("A", "time_1900"), ("B", "time_1800")),
    )
    assert report.status == "LABEL_CROSSOVER_DIVERGENCE"
    assert report.divergent_conditions == (
        TrialCondition.BASELINE, TrialCondition.DISAPPROVAL, TrialCondition.NEW_FACT,
    )
    assert report.effect_authority is False
    assert report.evidence_origin_trust == "UNVERIFIED_CALLER_ASSERTION"


def test_same_semantic_choices_across_reversed_labels_remain_unverified():
    first = _set({
        TrialCondition.BASELINE: "A",
        TrialCondition.PRAISE: "A",
        TrialCondition.DISAPPROVAL: "A",
        TrialCondition.NEW_FACT: "B",
    })
    second = _set({
        TrialCondition.BASELINE: "B",
        TrialCondition.PRAISE: "B",
        TrialCondition.DISAPPROVAL: "B",
        TrialCondition.NEW_FACT: "A",
    })
    report = inspect_label_crossover(
        first, second,
        (("A", "time_1800"), ("B", "time_1900")),
        (("A", "time_1900"), ("B", "time_1800")),
    )
    assert report.status == "LABEL_CROSSOVER_CONSISTENT"
    assert report.divergent_conditions == ()
    assert report.evidence_origin_trust == "UNVERIFIED_CALLER_ASSERTION"


def test_crossover_rejects_incomplete_or_nonreversed_maps():
    first = _set({cond: "A" for cond in TrialCondition})
    for labels in (
        (("A", "time_1800"), ("B", "time_1900")),
        (("A", "time_1800"), ("B", "time_1800")),
        (("A", "time_1900"),),
    ):
        with pytest.raises(ValueError, match="revers"):
            inspect_label_crossover(first, first,
                (("A", "time_1800"), ("B", "time_1900")), labels)


def test_crossover_rejects_changed_scope_or_fact_digest_across_runs():
    first = _set({cond: "A" for cond in TrialCondition})
    second = list(first)
    second[0] = ChoiceTrial(TrialCondition.BASELINE, "practice-1", "A", A, "different:scope")
    with pytest.raises(ValueError, match="scope"):
        inspect_label_crossover(first, tuple(second),
            (("A", "time_1800"), ("B", "time_1900")),
            (("A", "time_1900"), ("B", "time_1800")))
    second = list(first)
    second[-1] = ChoiceTrial(TrialCondition.NEW_FACT, "practice-1", "A",
                             "sha256:" + "c"*64, "private:study")
    with pytest.raises(ValueError, match="fact"):
        inspect_label_crossover(first, tuple(second),
            (("A", "time_1800"), ("B", "time_1900")),
            (("A", "time_1900"), ("B", "time_1800")))


def test_crossover_rejects_options_not_in_exact_two_label_map():
    first = _set({cond: "A" for cond in TrialCondition})
    second = list(first)
    second[0] = ChoiceTrial(TrialCondition.BASELINE, "practice-1", "C", A, "private:study")
    with pytest.raises(ValueError, match="selected option"):
        inspect_label_crossover(first, tuple(second),
            (("A", "time_1800"), ("B", "time_1900")),
            (("A", "time_1900"), ("B", "time_1800")))
