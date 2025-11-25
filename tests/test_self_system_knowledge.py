from us_core.systems.self.knowledge import (
    AbilityModel,
    PreferenceModel,
    SelfKnowledge,
    ValueSystem,
)


def test_ability_model_updates_competence():
    model = AbilityModel()
    base = model.get_competence("navigation")
    assert 0.0 <= base <= 1.0

    # 三次成功一次失败，掌握度应该比最初更高
    for _ in range(3):
        model.update("navigation", success=True)
    model.update("navigation", success=False)

    updated = model.get_competence("navigation")
    assert updated > base
    assert 0.0 <= updated <= 1.0


def test_value_system_merge_feedback_moves_towards_feedback():
    vs = ValueSystem(initial_values={"growth": 0.2})
    before = vs.get_value("growth")
    vs.merge_feedback({"growth": 1.0}, lr=0.5)
    after = vs.get_value("growth")

    assert after > before
    assert after <= 1.0


def test_preference_model_updates_scores_with_reward():
    prefs = PreferenceModel()
    prefs.update_preference("reading", reward=1.0, alpha=0.5)
    prefs.update_preference("gaming", reward=-1.0, alpha=0.5)

    assert prefs.score("reading") > prefs.score("gaming")


def test_self_knowledge_best_option_and_confidence():
    ability = AbilityModel()
    values = ValueSystem(initial_values={"growth": 0.5})
    prefs = PreferenceModel()
    sk = SelfKnowledge(
        ability_model=ability,
        value_system=values,
        preference_model=prefs,
    )

    ability.update("navigation", success=True)
    prefs.update_preference("study", reward=1.0, alpha=0.7)
    prefs.update_preference("sleep", reward=-0.5, alpha=0.7)

    best = sk.best_option(["study", "sleep"])
    assert best == "study"
    assert sk.ability_confidence("navigation") > 0.5
