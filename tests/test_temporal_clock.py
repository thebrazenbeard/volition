import pytest

from volition import DriveKind, Policy, Signal, VolitionEngine
from volition.temporal_bridge import TemporalAnchor, TemporalClockBridge


def motive_signal():
    return Signal(
        target='x',
        kind=DriveKind.OPEN_LOOP,
        magnitude=0.9,
        source='temporal-clock-test',
    )


def test_temporal_clock_bridge_advances_engine_to_absolute_timestamp():
    engine = VolitionEngine()
    clock = TemporalClockBridge(TemporalAnchor('2026-10-06T14:00:00Z'))

    assert clock.advance_engine_to(engine, '2026-10-06T14:00:10Z') == pytest.approx(10.0)
    assert engine.elapsed_seconds == pytest.approx(10.0)
    assert clock.advance_engine_to(engine, '2026-10-06T14:00:15Z') == pytest.approx(15.0)
    assert engine.elapsed_seconds == pytest.approx(15.0)


def test_temporal_clock_bridge_rejects_engine_rewind():
    engine = VolitionEngine()
    clock = TemporalClockBridge(TemporalAnchor('2026-10-06T14:00:00Z'))
    clock.advance_engine_to(engine, '2026-10-06T14:00:10Z')

    with pytest.raises(ValueError):
        clock.advance_engine_to(engine, '2026-10-06T14:00:09Z')


def test_goal_reappraisal_horizon_uses_temporal_clock():
    engine = VolitionEngine(
        Policy(
            goal_reappraisal_seconds=10.0,
            want_threshold=0.2,
        )
    )
    clock = TemporalClockBridge(TemporalAnchor('2026-10-06T14:00:00Z'))
    clock.advance_engine_to(engine, '2026-10-06T14:00:05Z')

    first = engine.tick([motive_signal()])
    assert first is not None
    assert first.adopted_at_seconds == pytest.approx(5.0)
    assert first.revision == 1

    clock.advance_engine_to(engine, '2026-10-06T14:00:16Z')
    revised = engine.tick([motive_signal()])

    assert revised is not None
    assert revised.goal_id == first.goal_id
    assert revised.revision == 2
    assert revised.adopted_at_seconds == pytest.approx(16.0)


def test_temporal_clock_drives_satiation_decay_without_hidden_random_time():
    engine = VolitionEngine(Policy(satiation_half_life_seconds=10.0))
    clock = TemporalClockBridge(TemporalAnchor('2026-10-06T14:00:00Z'))
    engine.record_satisfaction('x', 0.8)
    before = engine.evaluate([motive_signal()])[0].score

    clock.advance_engine_to(engine, '2026-10-06T14:00:10Z')
    after = engine.evaluate([motive_signal()])[0].score

    assert after > before
    assert engine.elapsed_seconds == pytest.approx(10.0)


def test_temporal_clock_requires_canonical_stored_timestamp():
    engine = VolitionEngine()
    clock = TemporalClockBridge(TemporalAnchor('2026-10-06T14:00:00Z'))

    with pytest.raises(ValueError):
        clock.advance_engine_to(engine, '2026-10-06T10:00:05-04:00')
