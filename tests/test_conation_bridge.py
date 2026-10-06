import pytest

from volition import DriveKind, ProvenanceClass, Signal, VolitionEngine
from volition.conation_bridge import ConationBridge, ConationRecord


def record(status='PRESENT', *, magnitude=0.9, kind=DriveKind.OPEN_LOOP, target='x'):
    return ConationRecord(
        record_id='conation-001',
        target=target,
        kind=kind,
        magnitude=magnitude,
        confidence=0.8,
        status=status,
        source_locator='conations:events/2026-09-04/example.md',
    )


def current_signal(*, magnitude=0.4, kind=DriveKind.OPEN_LOOP, target='x', provenance=ProvenanceClass.CURRENT_STATEMENT):
    return Signal(
        target=target,
        kind=kind,
        magnitude=magnitude,
        confidence=0.9,
        provenance=provenance,
        source='current:explicit-reappraisal',
        expected_information_gain=0.7,
        learning_progress=0.6,
        controllability=0.8,
        predicted_deficit_reduction=0.75,
    )


def test_stored_present_record_alone_cannot_manufacture_current_want():
    engine = VolitionEngine()
    historical = ConationBridge.historical_signal(record('PRESENT'))

    want = engine.evaluate([historical])[0]

    assert historical.provenance is ProvenanceClass.HISTORICAL_EVIDENCE
    assert historical.current_reappraisal is False
    assert want.score == 0.0
    assert want.eligible is False
    assert 'historical_requires_current_reappraisal' in want.reasons


def test_reappraisal_requires_fresh_current_evidence_and_caps_history_to_current_strength():
    engine = VolitionEngine()
    old = record('PRESENT', magnitude=0.95)
    fresh = current_signal(magnitude=0.4)

    historical, current = ConationBridge.reappraise(old, fresh)
    want = engine.evaluate([historical, current])[0]

    assert historical.provenance is ProvenanceClass.HISTORICAL_EVIDENCE
    assert historical.current_reappraisal is True
    assert historical.magnitude == pytest.approx(0.4)
    assert historical.confidence == pytest.approx(0.8)
    assert current is fresh
    assert want.score == pytest.approx(0.4 * 0.9)
    assert want.score < old.magnitude


@pytest.mark.parametrize('provenance', [ProvenanceClass.HISTORICAL_EVIDENCE, ProvenanceClass.MODEL_GENERATED, ProvenanceClass.INFERENCE, ProvenanceClass.SYSTEM_STATE])
def test_noncurrent_evidence_cannot_reappraise_archived_conation(provenance):
    with pytest.raises(ValueError):
        ConationBridge.reappraise(record(), current_signal(provenance=provenance))


def test_reappraisal_requires_same_target_and_drive_family():
    with pytest.raises(ValueError):
        ConationBridge.reappraise(record(target='x'), current_signal(target='y'))
    with pytest.raises(ValueError):
        ConationBridge.reappraise(record(kind=DriveKind.OPEN_LOOP), current_signal(kind=DriveKind.SELF_MODEL))


@pytest.mark.parametrize('status', ['COMPLETED', 'REVOKED', 'CONTRADICTED', 'REVISED'])
def test_terminal_or_superseded_record_cannot_be_reanimated(status):
    with pytest.raises(ValueError):
        ConationBridge.reappraise(record(status), current_signal())


@pytest.mark.parametrize('status', ['HISTORICAL / UNRESOLVED', 'CONSTRAINT-AFFECTED / UNEXPRESSED-UNCERTAIN'])
def test_uncertain_history_is_preserved_without_becoming_absence(status):
    historical = ConationBridge.historical_signal(record(status, magnitude=0.7))
    want = VolitionEngine().evaluate([historical])[0]

    assert historical.magnitude == pytest.approx(0.7)
    assert status in historical.source
    assert want.score == 0.0


def test_reappraised_history_never_creates_choice_or_goal_automatically():
    engine = VolitionEngine()
    signals = ConationBridge.reappraise(record(), current_signal(magnitude=0.8))

    wants = engine.evaluate(list(signals))

    assert wants[0].eligible is True
    assert engine.choices == ()
    assert engine.active_goal is None


@pytest.mark.parametrize(
    'kwargs',
    [
        {'record_id': ''},
        {'target': ''},
        {'magnitude': -0.1},
        {'magnitude': 1.1},
        {'confidence': -0.1},
        {'confidence': 1.1},
        {'status': ''},
        {'source_locator': ''},
    ],
)
def test_invalid_conation_record_fails_closed(kwargs):
    base = dict(
        record_id='c',
        target='x',
        kind=DriveKind.OPEN_LOOP,
        magnitude=0.5,
        confidence=0.5,
        status='PRESENT',
        source_locator='conations:file',
    )
    base.update(kwargs)
    with pytest.raises(ValueError):
        ConationRecord(**base)
