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

