import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from datetime import datetime, timedelta

from us_core.systems.memory.organization import (
    AutobiographicalOrganizer,
    SchemaBuilder,
    MemoryIndexer,
)
from us_core.systems.memory.types import EpisodicMemory, SemanticMemory


def test_autobiographical_organizer_sorts_by_time():
    base = datetime(2025, 1, 1, 12, 0, 0)
    e1 = EpisodicMemory(id="e1", timestamp=base + timedelta(minutes=10), content="later")
    e2 = EpisodicMemory(id="e2", timestamp=base, content="earlier")

    org = AutobiographicalOrganizer()
    org.add(e1)
    org.add(e2)

    timeline = org.timeline()
    assert [m.id for m in timeline] == ["e2", "e1"]

    slice_ = org.between(base, base + timedelta(minutes=5))
    assert [m.id for m in slice_.episodes] == ["e2"]


def test_schema_builder_groups_by_tags():
    m1 = SemanticMemory(id="1", key="python", value="lang", tags=["programming", "language"])
    m2 = SemanticMemory(id="2", key="java", value="lang", tags=["programming"])
    m3 = SemanticMemory(id="3", key="tea", value="drink", tags=[])

    builder = SchemaBuilder()
    schemas = builder.build_schemas([m1, m2, m3])

    assert "programming" in schemas
    assert set(mem.id for mem in schemas["programming"]) == {"1", "2"}
    # 没有 tag 时会 fallback 用 key
    assert "tea" in schemas
    assert schemas["tea"][0].id == "3"


def test_memory_indexer_search_orders_by_frequency():
    indexer = MemoryIndexer()
    indexer.index("m1", "learn python and deep learning")
    indexer.index("m2", "learn python and cooking")

    # python 在两个里都出现，deep 只在 m1 里出现
    result = indexer.search("python deep")
    assert result[0] == "m1"
    assert set(result) == {"m1", "m2"}
