import math

import pytest

from volition import CognitionRequest
from volition.preactive_bridge import PreActiveCognitionBridge, PreActiveReentryProposal


def request(*, urgency=0.7, effect_authority=False):
    return CognitionRequest(
        goal_id='goal-0042',
        target='reconsider-open-loop',
        urgency=urgency,
        source='ENDOGENOUS',
        effect_authority=effect_authority,
    )


def test_cognition_request_maps_to_reserved_preactive_reentry_proposal():
    proposal = PreActiveCognitionBridge.from_request(request(), delay_seconds=12.5)

    assert isinstance(proposal, PreActiveReentryProposal)
    assert proposal.tool_name == 'pre_active.request_turn'
    assert proposal.source == 'ENDOGENOUS'
    assert proposal.goal_id == 'goal-0042'
    assert proposal.target == 'reconsider-open-loop'
    assert proposal.urgency == pytest.approx(0.7)
    assert proposal.delay_seconds == pytest.approx(12.5)
    assert proposal.effect_authority is False
    assert proposal.capabilities == ()


def test_tool_arguments_match_preactive_reserved_tool_shape_only():
    proposal = PreActiveCognitionBridge.from_request(request(), delay_seconds=0.0)

    arguments = proposal.tool_arguments()

    assert set(arguments) == {'reason', 'delay_seconds'}
    assert arguments['delay_seconds'] == 0.0
    assert 'goal-0042' in arguments['reason']
    assert 'reconsider-open-loop' in arguments['reason']
    assert '0.700000' in arguments['reason']
    assert 'capabil' not in arguments


def test_bridge_does_not_schedule_or_claim_dispatch():
    proposal = PreActiveCognitionBridge.from_request(request())

    assert not hasattr(proposal, 'event_id')
    assert not hasattr(proposal, 'run_id')
    assert not hasattr(proposal, 'request_id')
    assert proposal.scheduled is False


def test_effect_authority_on_cognition_request_fails_closed():
    with pytest.raises(ValueError, match='effect authority'):
        PreActiveCognitionBridge.from_request(request(effect_authority=True))


@pytest.mark.parametrize('delay', [-1.0, float('nan'), float('inf')])
def test_invalid_delay_fails_closed(delay):
    with pytest.raises(ValueError):
        PreActiveCognitionBridge.from_request(request(), delay_seconds=delay)


@pytest.mark.parametrize('urgency', [-0.1, 1.1, float('nan'), float('inf')])
def test_invalid_urgency_fails_closed(urgency):
    with pytest.raises(ValueError):
        PreActiveCognitionBridge.from_request(request(urgency=urgency))


def test_request_source_must_be_endogenous():
    bad = CognitionRequest(
        goal_id='goal-1',
        target='x',
        urgency=0.5,
        source='EXTERNAL',
        effect_authority=False,
    )
    with pytest.raises(ValueError, match='ENDOGENOUS'):
        PreActiveCognitionBridge.from_request(bad)


def test_reason_length_stays_within_preactive_tool_contract():
    long_target = 'x' * 5000
    proposal = PreActiveCognitionBridge.from_request(
        CognitionRequest(
            goal_id='goal-long',
            target=long_target,
            urgency=0.5,
            source='ENDOGENOUS',
            effect_authority=False,
        )
    )

    reason = proposal.tool_arguments()['reason']
    assert 1 <= len(reason) <= 2000
    assert reason.endswith('[truncated]')
