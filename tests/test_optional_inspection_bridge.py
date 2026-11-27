"""Explicit opportunity inspection is not measured epistemic motive evidence."""
import pytest
from volition import Policy, VolitionEngine
from volition.meso_bridge import MesoIntentBridge
from test_meso_bridge import intent

@pytest.mark.parametrize("strength", [0.2, 0.8])
def test_explicit_exploration_does_not_invent_a_motive(strength):
    proposal = intent("inspect", strength=strength, source_tendency="inspect",
                      source="exploration_requested")
    signals = MesoIntentBridge.to_signals(proposal)
    assert signals == ()
    engine = VolitionEngine(Policy(want_threshold=0.1))
    assert engine.tick(list(signals)) is None
    assert engine.request_cognition() is None

def test_legacy_epistemic_inspect_retains_existing_contract():
    signal, = MesoIntentBridge.to_signals(intent("inspect", strength=0.7,
        source_tendency="inspect", source="epistemic_value"))
    assert VolitionEngine().evaluate([signal])[0].score == pytest.approx(0.7)

def test_optional_inspection_still_validates_authority():
    with pytest.raises(ValueError):
        MesoIntentBridge.to_signals(intent("inspect", source_tendency="inspect",
            source="exploration_requested", effect_authorized=True))
