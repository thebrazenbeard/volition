import pytest

from volition import DriveKind, ProvenanceClass, VolitionEngine
from volition.meso_bridge import MesoIntentBridge, MesoIntentEvidence


def intent(kind='approach', *, target_id='x', strength=0.8, source_tendency='approach', source='incentive_salience', effect_authorized=False, can_execute=False):
    return {
        'target_id': target_id,
        'kind': kind,
        'strength': strength,
        'source_tendency': source_tendency,
        'source': source,
        'effect_authorized': effect_authorized,
        'can_execute': can_execute,
    }


def test_approach_intent_becomes_open_loop_model_generated_evidence():
    signal = MesoIntentBridge.to_signals(intent())[0]

    assert signal.target == 'x'
    assert signal.kind is DriveKind.OPEN_LOOP
    assert signal.magnitude == pytest.approx(0.8)
    assert signal.provenance is ProvenanceClass.MODEL_GENERATED
    assert signal.source == 'meso-crct:intent:approach:approach:incentive_salience'


def test_inspect_intent_preserves_strength_as_epistemic_value():
    engine = VolitionEngine()
    signal = MesoIntentBridge.to_signals(
        intent(
            'inspect',
            strength=0.7,
            source_tendency='inspect',
            source='epistemic_value',
        )
    )[0]

    assert signal.kind is DriveKind.EPISTEMIC
    assert signal.expected_information_gain == 1.0
    assert signal.controllability == 1.0
    want = engine.evaluate([signal])[0]
    assert want.score == pytest.approx(0.7)


def test_withdraw_intent_becomes_protection_not_negative_pleasure():
    engine = VolitionEngine()
    signal = MesoIntentBridge.to_signals(
        intent(
            'withdraw',
            strength=0.9,
            source_tendency='protective_withdraw',
            source='protective_state',
        )
    )[0]

    assert signal.kind is DriveKind.PROTECTION
    want = engine.evaluate([signal])[0]
    assert want.vetoed is True
    assert want.eligible is False


def test_hold_intent_produces_no_motive_signal():
    assert MesoIntentBridge.to_signals(
        intent(
            'hold',
            target_id=None,
            strength=0.4,
            source_tendency='uncommitted',
            source='no_selection',
        )
    ) == ()


def test_meso_intent_bridge_never_promotes_evidence_to_choice_or_goal():
    engine = VolitionEngine()
    signals = MesoIntentBridge.to_signals(intent())

    wants = engine.evaluate(list(signals))

    assert wants[0].eligible is True
    assert engine.choices == ()
    assert engine.active_goal is None


def test_authorized_or_executable_meso_intent_fails_closed():
    with pytest.raises(ValueError):
        MesoIntentEvidence.from_value(intent(effect_authorized=True))
    with pytest.raises(ValueError):
        MesoIntentEvidence.from_value(intent(can_execute=True))


def test_salience_only_mapping_is_not_reinterpreted_as_intent():
    with pytest.raises(ValueError):
        MesoIntentEvidence.from_value({
            'target_id': 'x',
            'perceptual_salience': 1.0,
            'semantic_relevance': 1.0,
        })


@pytest.mark.parametrize(
    'bad',
    [
        intent(strength=-0.1),
        intent(strength=1.1),
        intent(target_id=None),
        intent(kind='unknown'),
        intent(source=''),
    ],
)
def test_invalid_meso_intent_contract_fails_closed(bad):
    with pytest.raises(ValueError):
        MesoIntentEvidence.from_value(bad)


@pytest.mark.parametrize(
    'overrides',
    [
        {'effect_authorized': True},
        {'effect_authorized': 1},
        {'kind': 'unsupported'},
        {'strength': -0.1},
        {'strength': 1.1},
        {'strength': float('nan')},
        {'target_id': None},
        {'source_tendency': ''},
    ],
)
def test_direct_typed_meso_evidence_cannot_bypass_contract_validation(overrides):
    # Direct dataclass construction does not invoke from_value's checks.
    raw = intent()
    raw.pop('can_execute')
    raw.update(overrides)
    typed = MesoIntentEvidence(**raw)

    with pytest.raises(ValueError):
        MesoIntentBridge.to_signals(typed)


def test_valid_direct_typed_meso_evidence_matches_mapping_and_hold():
    raw = intent(kind='inspect', source='epistemic_value', source_tendency='inspect')
    raw.pop('can_execute')
    typed = MesoIntentEvidence(**raw)

    assert MesoIntentBridge.to_signals(typed) == MesoIntentBridge.to_signals(raw)
    assert MesoIntentBridge.to_signals(MesoIntentEvidence(
        target_id=None, kind='hold', strength=0.4,
        source_tendency='uncommitted', source='no_selection',
    )) == ()
