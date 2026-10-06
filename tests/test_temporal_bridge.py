import pytest

from volition import DriveKind, MotiveTemporalModel
from volition.temporal_bridge import TemporalAnchor, TemporalEventBridge, TemporalRecord


def record(event_id='evt-1', timestamp='2026-10-06T14:00:05Z', source='github', event='Observed event', refs=None):
    value = {
        'id': event_id,
        'timestamp': timestamp,
        'source': source,
        'event': event,
    }
    if refs is not None:
        value['refs'] = refs
    return value


def test_temporal_anchor_converts_canonical_utc_to_nonnegative_relative_seconds():
    anchor = TemporalAnchor('2026-10-06T14:00:00Z')

    assert anchor.seconds_for('2026-10-06T14:00:05Z') == pytest.approx(5.0)
    assert anchor.seconds_for('2026-10-06T14:00:00.500000Z') == pytest.approx(0.5)


def test_temporal_record_requires_stored_canonical_utc_timestamp():
    with pytest.raises(ValueError):
        TemporalRecord.from_mapping(record(timestamp='2026-10-06T10:00:05-04:00'))
    with pytest.raises(ValueError):
        TemporalRecord.from_mapping(record(timestamp='2026-10-06T14:00:05.123Z'))


def test_temporal_anchor_rejects_event_before_anchor():
    anchor = TemporalAnchor('2026-10-06T14:00:05Z')

    with pytest.raises(ValueError):
        anchor.seconds_for('2026-10-06T14:00:04Z')


def test_bridge_preserves_temporal_provenance_but_requires_explicit_volition_semantics():
    model = MotiveTemporalModel()
    bridge = TemporalEventBridge(TemporalAnchor('2026-10-06T14:00:00Z'))

    event = bridge.ingest(
        model,
        record(
            event_id='evt-42',
            event='This text must not become the target',
            refs=['thebrazenbeard/temporal'],
        ),
        target='explicit-target',
        kind=DriveKind.OPEN_LOOP,
        weight=0.7,
    )

    assert event.target == 'explicit-target'
    assert event.kind is DriveKind.OPEN_LOOP
    assert event.at_seconds == pytest.approx(5.0)
    assert event.weight == pytest.approx(0.7)
    assert event.temporal_event_id == 'evt-42'
    assert event.temporal_timestamp == '2026-10-06T14:00:05Z'
    assert event.temporal_source == 'github'
    assert event.temporal_refs == ('thebrazenbeard/temporal',)


def test_model_rejects_duplicate_temporal_id_even_across_bridge_instances():
    model = MotiveTemporalModel()
    first = TemporalEventBridge(TemporalAnchor('2026-10-06T14:00:00Z'))
    second = TemporalEventBridge(TemporalAnchor('2026-10-06T14:00:00Z'))
    item = record(event_id='stable-id')

    first.ingest(model, item, target='x', kind=DriveKind.OPEN_LOOP)
    with pytest.raises(ValueError):
        second.ingest(model, item, target='x', kind=DriveKind.OPEN_LOOP)


def test_batch_ingest_uses_temporal_timestamp_then_stable_id_order():
    model = MotiveTemporalModel()
    bridge = TemporalEventBridge(TemporalAnchor('2026-10-06T14:00:00Z'))

    events = bridge.ingest_many(
        model,
        [
            record(event_id='b', timestamp='2026-10-06T14:00:05Z'),
            record(event_id='c', timestamp='2026-10-06T14:00:06Z'),
            record(event_id='a', timestamp='2026-10-06T14:00:05Z'),
        ],
        target='x',
        kind=DriveKind.OPEN_LOOP,
    )

    assert [event.temporal_event_id for event in events] == ['a', 'b', 'c']
    assert [event.at_seconds for event in events] == [5.0, 5.0, 6.0]


def test_temporal_optional_fields_follow_temporal_validation_contract():
    good = record(refs=['repo:a', 'repo:b'])
    good['local_timestamp'] = '2026-10-06T10:00:05-04:00'
    parsed = TemporalRecord.from_mapping(good)
    assert parsed.local_timestamp == '2026-10-06T10:00:05-04:00'

    bad_refs = record()
    bad_refs['refs'] = ['ok', '']
    with pytest.raises(ValueError):
        TemporalRecord.from_mapping(bad_refs)

    bad_local = record()
    bad_local['local_timestamp'] = '2026-10-06T10:00:05'
    with pytest.raises(ValueError):
        TemporalRecord.from_mapping(bad_local)
