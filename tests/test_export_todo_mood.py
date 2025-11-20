from __future__ import annotations

"""
测试情绪感知 TODO 导出器的核心逻辑：select_recommended_tasks

我们不测试文件读写，只测试：
- 不同情绪分数下，推荐任务数量是否符合预期
"""

from datetime import datetime, timezone

from scripts import export_todo_mood as m
from src.us_core.core.events import EmbryoEvent, EventType


def _make_task(hour: int, text: str) -> EmbryoEvent:
    return EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=datetime(2025, 1, 1, hour, 0, tzinfo=timezone.utc),
        payload={"status": "open", "intent": "command", "text": text},
    )


def test_select_recommended_tasks_count_by_mood():
    tasks = [
        _make_task(9, "任务1"),
        _make_task(10, "任务2"),
        _make_task(11, "任务3"),
        _make_task(12, "任务4"),
        _make_task(13, "任务5"),
    ]

    # 情绪明显偏负面：1 条
    rec_neg = m.select_recommended_tasks(-1.2, tasks)
    assert len(rec_neg) == 1
    assert rec_neg[0].payload["text"] == "任务1"

    # 略偏负面：2 条
    rec_slight_neg = m.select_recommended_tasks(-0.3, tasks)
    assert len(rec_slight_neg) == 2

    # 中性：3 条
    rec_neutral = m.select_recommended_tasks(0.2, tasks)
    assert len(rec_neutral) == 3

    # 明显偏正：最多 5 条
    rec_pos = m.select_recommended_tasks(1.3, tasks)
    assert len(rec_pos) == 5

    # 无情绪样本：默认 3 条
    rec_none = m.select_recommended_tasks(None, tasks)
    assert len(rec_none) == 3
