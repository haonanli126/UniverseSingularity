from us_core.systems.motor.actions import ActionLibrary
from us_core.systems.motor.skills import Skill, SkillLibrary


def test_skill_library_register_and_get():
    actions = ActionLibrary()
    lib = SkillLibrary(action_library=actions)

    seq = [
        actions.get_index("MOVE_UP"),
        actions.get_index("MOVE_RIGHT"),
    ]
    skill = Skill(name="go_up_right", action_sequence=seq, description="test skill")
    lib.register(skill)

    retrieved = lib.get("go_up_right")
    assert retrieved.name == "go_up_right"
    assert retrieved.action_sequence == seq


def test_skill_library_with_default_skills_has_explore():
    actions = ActionLibrary()
    lib = SkillLibrary.with_default_skills(action_library=actions)

    names = lib.list_skill_names()
    assert "explore" in names

    explore = lib.get("explore")
    assert len(explore.action_sequence) > 0
