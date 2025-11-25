from us_core.systems.motor.actions import ActionLibrary
from us_core.systems.motor.skills import Skill
from us_core.systems.motor.control import ActionController


def test_action_controller_executes_skill_sequence_in_order():
    actions = ActionLibrary()
    seq = [
        actions.get_index("MOVE_UP"),
        actions.get_index("MOVE_RIGHT"),
        actions.get_index("INTERACT"),
    ]
    skill = Skill(name="go_and_interact", action_sequence=seq)

    controller = ActionController()
    controller.queue_skill(skill)

    outputs = []
    while not controller.is_idle():
        action = controller.next_action()
        outputs.append(action)

    assert outputs == seq


def test_action_controller_emergency_halt_clears_queue():
    actions = ActionLibrary()
    seq = [actions.get_index("MOVE_UP")] * 3
    skill = Skill(name="loop", action_sequence=seq)

    controller = ActionController()
    controller.queue_skill(skill)
    assert not controller.is_idle()

    controller.emergency_halt()
    assert controller.is_idle()
    # halt 后再取动作应该得到 None
    assert controller.next_action() is None
