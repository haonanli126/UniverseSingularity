import sys
from pathlib import Path

# 确保 src 在 sys.path 里，这样可以导入 us_core
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from datetime import datetime

from us_core.systems.memory.types import (
    EpisodicMemory,
    SemanticMemory,
    ProceduralMemory,
    WorkingMemory,
)


def test_episodic_memory_defaults_and_emotion_update():
    ts = datetime.utcnow()
    mem = EpisodicMemory(id="e1", timestamp=ts, content="测试事件")

    assert mem.emotion_tags == []
    assert 0.0 <= mem.importance <= 1.0

    updated = mem.with_added_emotion("happy")
    assert "happy" in updated.emotion_tags
    # 原对象不变风格
    assert mem is not updated


def test_semantic_memory_tags_and_confidence():
    mem = SemanticMemory(
        id="s1",
        key="python",
        value="a programming language",
        confidence=0.8,
        tags=["programming", "language"],
    )
    assert "programming" in mem.tags
    assert mem.confidence == 0.8


def test_procedural_memory_length():
    mem = ProceduralMemory(
        id="p1",
        name="make_tea",
        steps=["boil_water", "add_tea", "wait", "serve"],
    )
    assert mem.length() == 4


def test_working_memory_capacity_and_fifo_behavior():
    wm = WorkingMemory(capacity=3)
    wm.add("a")
    wm.add("b")
    wm.add("c")
    assert wm.items() == ["a", "b", "c"]

    # 超过容量，会丢弃最早的
    wm.add("d")
    assert wm.items() == ["b", "c", "d"]

    wm.clear()
    assert wm.items() == []
