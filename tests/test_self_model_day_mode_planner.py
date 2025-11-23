from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.self_model import day_mode_planner as dmp  # type: ignore
from us_core.self_model.insights import PlannerInsights, TagStats  # type: ignore


def _make_insights(total_events: int, overall_rate: float, tags: list[TagStats]) -> PlannerInsights:
    return PlannerInsights(
        total_tasks=len(tags),
        total_planned_events=total_events,
        total_completed_events=int(total_events * overall_rate),
        overall_completion_rate=overall_rate,
        tag_stats=tags,
    )


def test_plan_day_with_mood_and_self_model_uses_mood_when_no_history(monkeypatch):
    # 没有任何历史：应该完全听情绪 → final_mode == mood_mode
    insights = _make_insights(total_events=0, overall_rate=0.0, tags=[])

    captured: dict[str, object] = {}

    def fake_build_day_plan_with_history(base_mode, block_specs, filter_spec=None):
        captured["base_mode"] = base_mode
        captured["block_specs"] = block_specs
        captured["filter_spec"] = filter_spec
        # 返回一个简单的哑对象即可，类型检查不会在运行时强制
        return object()

    # 注意要 patch 到 day_mode_planner 模块内部引用的名字上
    monkeypatch.setattr(dmp, "build_day_plan_with_history", fake_build_day_plan_with_history)

    result = dmp.plan_day_with_mood_and_self_model(
        mood_mode="focus",
        insights=insights,
    )

    assert result.decision.final_mode == "focus"
    assert result.decision.mood_mode == "focus"
    assert result.decision.self_model_mode is None

    # 确认传入 build_day_plan_with_history 的 base_mode 正确
    assert captured["base_mode"] == "focus"

    # block 配置应该是早/午/晚 3 个
    block_specs = captured["block_specs"]
    names = [b.name for b in block_specs]  # type: ignore[attr-defined]
    assert names == ["morning", "afternoon", "evening"]


def test_plan_day_with_mood_and_self_model_uses_balance_on_strong_conflict(monkeypatch):
    # 构造一个整体完成率很低的自我模型 → 推荐 rest
    tags = [
        TagStats(tag="self-care", times_planned=5, times_completed=1),
        TagStats(tag="universe", times_planned=5, times_completed=1),
    ]
    insights = _make_insights(total_events=10, overall_rate=0.2, tags=tags)

    captured: dict[str, object] = {}

    def fake_build_day_plan_with_history(base_mode, block_specs, filter_spec=None):
        captured["base_mode"] = base_mode
        captured["block_specs"] = block_specs
        captured["filter_spec"] = filter_spec
        return object()

    monkeypatch.setattr(dmp, "build_day_plan_with_history", fake_build_day_plan_with_history)

    # 情绪说 focus，自我模型说 rest → strong conflict → balance
    result = dmp.plan_day_with_mood_and_self_model(
        mood_mode="focus",
        insights=insights,
    )

    assert result.decision.mood_mode == "focus"
    assert result.decision.self_model_mode == "rest"
    assert result.decision.final_mode == "balance"

    assert captured["base_mode"] == "balance"
