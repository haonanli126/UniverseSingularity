from __future__ import annotations

"""
测试 daily_cycle.py 的基本行为：

- main() 会依次调用各个子脚本的 main()
- 不关心具体输出，只关心步骤顺序是否正确
"""

from scripts import daily_cycle as m


def test_daily_cycle_calls_steps_in_order(monkeypatch):
    called: list[str] = []

    def make_stub(tag: str):
        def _stub():
            called.append(tag)
        return _stub

    # 避免真的去读配置 / genome，给一个最小假对象
    class FakeSettings:
        environment = "test"

    class FakeEmbryo:
        codename = "TEST-EMBRYO"

    class FakeGenome:
        embryo = FakeEmbryo()

    monkeypatch.setattr(m, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(m, "get_genome", lambda: FakeGenome())

    # 替换各脚本的 main 函数，记录调用顺序
    monkeypatch.setattr(m.import_journal, "main", make_stub("journal"))
    monkeypatch.setattr(m.collect_long_term, "main", make_stub("long_term"))
    monkeypatch.setattr(m.collect_tasks, "main", make_stub("tasks"))
    monkeypatch.setattr(m.show_mood, "main", make_stub("mood"))
    monkeypatch.setattr(m.planning_session, "main", make_stub("planning"))
    monkeypatch.setattr(m.export_todo_mood, "main", make_stub("todo_mood"))
    monkeypatch.setattr(m.show_status, "main", make_stub("status"))
    monkeypatch.setattr(m.show_workspace, "main", make_stub("workspace"))

    m.main()

    # 期望的调用顺序
    assert called == [
        "journal",
        "long_term",
        "tasks",
        "mood",
        "planning",
        "todo_mood",
        "status",
        "workspace",
    ]
