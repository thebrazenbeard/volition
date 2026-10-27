"""Adversarial operational motivation cases: replay, provenance, veto, feedback."""

from copy import deepcopy
from hashlib import sha256

import pytest

from volition import (
    ChoiceClass,
    DriveKind,
    GoalCompletionClaim,
    GoalCompletionVerifier,
    ModelWantProposal,
    ObservationClaim,
    ObservationVerifier,
    OperationalMotivation,
    ProvenanceClass,
)
from volition.conation_bridge import ConationBridge, ConationRecord


def observation(
    evidence_id="external-1", content_digest="payload-1", *,
    target="repair-blotter", kind=DriveKind.OPEN_LOOP,
    magnitude=0.8, confidence=0.9,
    provenance=ProvenanceClass.CURRENT_OBSERVATION,
):
    return ObservationClaim(
        evidence_id=evidence_id,
        content_digest="sha256:" + sha256(content_digest.encode()).hexdigest()
        if not (content_digest.startswith("sha256:") and len(content_digest) == 71)
        else content_digest,
        target=target, kind=kind, magnitude=magnitude,
        confidence=confidence, source_ref="external-monitor:check-1",
        provenance=provenance,
    )


def admitted(claim):
    return ObservationVerifier([claim], verifier_id="operator:approved-monitor").admit(claim)


def proposal(claim, proposal_id="model-candidate-1"):
    return ModelWantProposal(
        proposal_id=proposal_id, target=claim.target, kind=claim.kind,
        evidence_id=claim.evidence_id, reason="observable discrepancy",
    )


def test_caller_admitted_measurement_creates_persistent_model_proposed_goal():
    loop = OperationalMotivation()
    claim = observation()
    goal = loop.propose(proposal(claim), admitted(claim))
    assert goal is not None
    assert loop.wants[0].score == pytest.approx(0.72)
    assert loop.engine.choices[-1].choice_class is ChoiceClass.MODEL_PROPOSED
    assert loop.engine.choices[-1].effect_authority is False
    assert loop.request_cognition().effect_authority is False

    resumed = OperationalMotivation.from_snapshot(loop.snapshot())
    assert resumed.wants == loop.wants
    assert resumed.engine.active_goal == goal


def test_replay_across_horizon_never_renews_goal_or_cognition_budget():
    loop = OperationalMotivation()
    claim = observation()
    goal = loop.propose(proposal(claim), admitted(claim))
    requests = [loop.request_cognition() for _ in range(7)]
    assert sum(request is not None for request in requests) == loop.engine.policy.endogenous_turn_budget
    loop.advance(loop.engine.policy.goal_reappraisal_seconds * 2)
    assert loop.propose(proposal(claim), admitted(claim)) is None
    assert loop.request_cognition() is None
    resumed = OperationalMotivation.from_snapshot(loop.snapshot())
    assert resumed.propose(proposal(claim, "another-model"), admitted(claim)) is None
    assert resumed.request_cognition() is None
    assert len(resumed.engine.choices) == 1


def test_new_admitted_measurement_suspends_stale_goal_and_drops_cognition():
    loop = OperationalMotivation()
    first = observation(magnitude=0.9)
    assert loop.propose(proposal(first), admitted(first)) is not None
    second = observation("measured-resolved-2", "sha256:resolved", magnitude=0)
    assert loop.propose(proposal(second, "candidate-resolution"), admitted(second)) is None
    assert loop.engine.active_goal is None
    assert not loop.wants[0].eligible
    assert loop.request_cognition() is None
    assert OperationalMotivation.from_snapshot(loop.snapshot()).request_cognition() is None


def test_new_admitted_measurement_reappraises_urgency_without_self_authorship():
    loop = OperationalMotivation()
    first = observation(magnitude=0.95)
    original = loop.propose(proposal(first), admitted(first))
    second = observation("reappraisal-2", "sha256:lower", magnitude=0.5)
    revised = loop.propose(proposal(second, "reappraisal-model"), admitted(second))
    assert revised.goal_id == original.goal_id
    assert revised.revision == original.revision + 1
    assert revised.adoption_score < original.adoption_score
    assert loop.engine.choices[-1].choice_class is ChoiceClass.MODEL_PROPOSED
    assert OperationalMotivation.from_snapshot(loop.snapshot()).engine.active_goal == revised


def test_same_payload_with_new_id_or_different_drive_cannot_double_count():
    loop = OperationalMotivation()
    first = observation(magnitude=0.2)
    assert loop.propose(proposal(first), admitted(first)) is None
    second = observation("external-2", first.content_digest, kind=DriveKind.SELF_MODEL, magnitude=0.2)
    assert loop.propose(proposal(second, "second"), admitted(second)) is None
    assert len(loop.wants) == 1
    assert loop.wants[0].eligible is False
    assert not loop.engine.choices


def test_protection_latch_sticks_until_distinct_current_admitted_clearance():
    loop = OperationalMotivation()
    first = observation()
    assert loop.propose(proposal(first), admitted(first)) is not None
    danger = observation("danger-1", "sha256:danger", kind=DriveKind.PROTECTION)
    assert loop.observe_protection(admitted(danger))
    assert loop.engine.active_goal is None
    assert "repair-blotter" in loop.protection_latches
    approach = observation("approach-2", "sha256:new-approach")
    assert loop.propose(proposal(approach), admitted(approach)) is None
    assert loop.request_cognition() is None
    resumed = OperationalMotivation.from_snapshot(loop.snapshot())
    assert "repair-blotter" in resumed.protection_latches
    assert resumed.propose(proposal(approach), admitted(approach)) is None

    with pytest.raises(ValueError):
        resumed.clear_protection(admitted(danger))
    clearance = observation("safe-3", "sha256:independent-safe", kind=DriveKind.PROTECTION, magnitude=0.0)
    assert resumed.clear_protection(admitted(clearance))
    fresh = observation("fresh-4", "sha256:fresh-after-safe")
    assert resumed.propose(proposal(fresh), admitted(fresh)) is not None


def test_goal_completion_uses_exact_caller_admitted_receipt_and_no_old_readoption():
    loop = OperationalMotivation()
    claim = observation()
    goal = loop.propose(proposal(claim), admitted(claim))
    assert goal is not None
    with pytest.raises(TypeError):
        loop.complete("successful")
    outcome = GoalCompletionClaim(
        outcome_event_id="outcome-1", goal_id=goal.goal_id,
        choice_id=goal.choice_id, goal_revision=goal.revision,
        target=goal.target, result_receipt_id="result-1",
        evidence_ref="verified-result:1", source_ref="external-monitor",
        provenance=ProvenanceClass.CURRENT_OBSERVATION,
    )
    receipt = GoalCompletionVerifier([outcome], verifier_id="operator:outcomes").admit(outcome)
    assert loop.complete(receipt)
    assert loop.engine.active_goal is None
    assert loop.wants == ()
    assert loop.propose(proposal(claim), admitted(claim)) is None
    assert OperationalMotivation.from_snapshot(loop.snapshot()).propose(proposal(claim), admitted(claim)) is None


def test_rejects_model_only_fake_verification_and_inconsistent_snapshot():
    loop = OperationalMotivation()
    claim = observation()
    with pytest.raises(TypeError):
        loop.propose(proposal(claim), claim)
    with pytest.raises(ValueError):
        observation(provenance=ProvenanceClass.MODEL_GENERATED)
    with pytest.raises(ValueError):
        ObservationClaim(
            evidence_id="test", content_digest="not-a-sha256", target="x",
            kind=DriveKind.OPEN_LOOP, magnitude=0.9, confidence=1,
            source_ref="operator:source",
        )
    with pytest.raises(ValueError):
        ObservationVerifier([], verifier_id="operator").admit(claim)
    with pytest.raises(ValueError):
        loop.propose(proposal(claim, "model-other") , admitted(observation(
            "external-2", "sha256:different-observation"
        )))
    loop.propose(proposal(claim), admitted(claim))
    forged = deepcopy(loop.snapshot())
    forged["digests"].clear()
    with pytest.raises(ValueError):
        OperationalMotivation.from_snapshot(forged)
    forged = deepcopy(loop.snapshot())
    forged["wants"][0]["effect_authority"] = True
    with pytest.raises(ValueError):
        OperationalMotivation.from_snapshot(forged)


def test_observation_verifier_limits_infinite_allowlist_consumption():
    consumed = 0

    def unbounded():
        nonlocal consumed
        while True:
            consumed += 1
            yield observation()

    with pytest.raises(ValueError, match="capacity|bounded"):
        ObservationVerifier(unbounded(), verifier_id="operator")
    assert consumed == 2049


@pytest.mark.parametrize("status", ["revoked", " completed ", "Contradicted", "revised"])
def test_historical_conation_terminal_status_cannot_be_revived_case_insensitively(status):
    record = ConationRecord(
        record_id="conation-1", target="repair-blotter", kind=DriveKind.OPEN_LOOP,
        magnitude=0.7, confidence=0.8, status=status, source_locator="conations:record",
    )
    from volition import Signal
    with pytest.raises(ValueError):
        ConationBridge.reappraise(record, Signal(
            target=record.target, kind=record.kind, magnitude=0.8,
            provenance=ProvenanceClass.CURRENT_OBSERVATION, source="observer:claim",
        ))
