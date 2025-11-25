from us_core.systems.motor.actions import ActionLibrary


def test_action_library_defines_six_base_actions():
    lib = ActionLibrary()
    names = set(lib.list_action_names())
    assert names == {
        "MOVE_UP",
        "MOVE_DOWN",
        "MOVE_LEFT",
        "MOVE_RIGHT",
        "STAY",
        "INTERACT",
    }

    for name in names:
        idx = lib.get_index(name)
        assert lib.is_valid_index(idx)
        back_name = lib.get_name(idx)
        assert back_name == name


def test_all_specs_returns_non_empty_list():
    lib = ActionLibrary()
    specs = lib.all_specs()
    assert len(specs) == 6
    assert {s.name for s in specs} == set(lib.list_action_names())
