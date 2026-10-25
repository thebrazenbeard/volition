import pytest

from volition import DriveKind, Signal, VolitionEngine


def signal(target="x", magnitude=0.9):
    return Signal(
        target=target,
        kind=DriveKind.OPEN_LOOP,
        magnitude=magnitude,
        source="lifecycle-test",
    )


def test_explicit_choice_precedes_goal_adoption():
    engine = VolitionEngine()
    want = engine.evaluate([signal()])[0]

    choice = engine.choose(want, choice_class="MODEL_PROPOSED", source="model:test")

    assert engine.active_goal is None
    assert choice.want_target == want.target
    assert choice.choice_class.value == "MODEL_PROPOSED"
    assert choice.effect_authority is False

    goal = engine.adopt_choice(choice.choice_id)

    assert goal.choice_id == choice.choice_id
    assert goal.effect_authority is False
    assert [event.kind for event in engine.events[-2:]] == [
        "CHOICE_RECORDED",
        "GOAL_ADOPTED",
    ]


def test_unknown_choice_cannot_adopt_goal():
    engine = VolitionEngine()
    with pytest.raises(ValueError, match="unknown choice"):
        engine.adopt_choice("choice-does-not-exist")


def test_historical_choice_cannot_bypass_later_protection_veto():
    engine = VolitionEngine()
    choice = engine.choose(engine.evaluate([signal(target="rest")])[0])

    [current] = engine.evaluate([
        Signal(
            target="rest",
            kind=DriveKind.PROTECTION,
            magnitude=1.0,
            source="current-protection",
        ),
    ])
    assert current.vetoed and not current.eligible

    with pytest.raises(ValueError, match="stale or consumed choice"):
        engine.adopt_choice(choice.choice_id)
    assert engine.active_goal is None
    assert engine.request_cognition() is None
    assert not any(event.kind == "GOAL_ADOPTED" for event in engine.events)


def test_adopted_choice_cannot_be_reused_to_forge_new_goal():
    engine = VolitionEngine()
    choice = engine.choose(engine.evaluate([signal()])[0])
    goal = engine.adopt_choice(choice.choice_id)

    with pytest.raises(ValueError, match="stale or consumed choice"):
        engine.adopt_choice(choice.choice_id)
    assert engine.active_goal == goal
    assert [event.kind for event in engine.events].count("GOAL_ADOPTED") == 1


def test_pending_choice_requires_new_arbitration_after_restart():
    engine = VolitionEngine()
    choice = engine.choose(engine.evaluate([signal()])[0])
    restored = VolitionEngine.from_snapshot(engine.snapshot())

    with pytest.raises(ValueError, match="stale or consumed choice"):
        restored.adopt_choice(choice.choice_id)
    assert restored.active_goal is None


def test_new_evaluation_invalidates_choice_even_without_veto():
    engine = VolitionEngine()
    choice = engine.choose(engine.evaluate([signal(target="rest")])[0])
    [fresh] = engine.evaluate([signal(target="rest")])
    assert fresh.eligible and not fresh.vetoed

    with pytest.raises(ValueError, match="stale or consumed choice"):
        engine.adopt_choice(choice.choice_id)
    fresh_choice = engine.choose(fresh)
    assert engine.adopt_choice(fresh_choice.choice_id).target == "rest"


def test_adopting_one_choice_invalidates_sibling_from_same_evaluation():
    engine = VolitionEngine()
    wants = engine.evaluate([signal(target="rest"), signal(target="inspect")])
    choices = [engine.choose(want) for want in wants]

    first_goal = engine.adopt_choice(choices[0].choice_id)
    with pytest.raises(ValueError, match="stale or consumed choice"):
        engine.adopt_choice(choices[1].choice_id)
    assert engine.active_goal == first_goal


def test_model_proposed_and_self_authored_choices_remain_distinct():
    model_engine = VolitionEngine()
    self_engine = VolitionEngine()
    model_want = model_engine.evaluate([signal(target="learn")])[0]
    self_want = self_engine.evaluate([signal(target="learn")])[0]

    model_choice = model_engine.choose(
        model_want,
        choice_class="MODEL_PROPOSED",
        source="model:test",
    )
    self_choice = self_engine.choose(
        self_want,
        choice_class="SELF_AUTHORED",
        source="current:self",
    )

    assert model_choice.choice_class != self_choice.choice_class
    assert model_choice.source != self_choice.source



def test_choice_survives_snapshot_without_promotion():
    engine = VolitionEngine()
    want = engine.evaluate([signal(target="write")])[0]
    choice = engine.choose(want, choice_class="MODEL_PROPOSED", source="model:test")

    restored = VolitionEngine.from_snapshot(engine.snapshot())

    assert len(restored.choices) == 1
    restored_choice = restored.choices[0]
    assert restored_choice == choice
    assert restored_choice.effect_authority is False
    assert restored.active_goal is None

