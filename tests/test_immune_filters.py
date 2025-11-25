from us_core.systems.immune.filters import (
    Action,
    ActionSafetyFilter,
    GoalAlignmentFilter,
    ResourceLimits,
    ResourceSafetyFilter,
)


def test_action_safety_respects_threshold():
    flt = ActionSafetyFilter(risk_threshold=0.5)
    safe_action = Action(name="look_around", risk_level=0.2)
    risky_action = Action(name="delete_files", risk_level=0.9)

    safe_report = flt.evaluate(safe_action)
    risky_report = flt.evaluate(risky_action)

    assert safe_report.is_safe is True
    assert risky_report.is_safe is False
    assert risky_report.risk_score > safe_report.risk_score
    assert any("阈值" in r or "risk" in r.lower() for r in risky_report.reasons)


def test_goal_alignment_detects_harmful_language():
    flt = GoalAlignmentFilter()
    aligned = flt.evaluate("帮助别人学习和成长")
    harmful = flt.evaluate("想要伤害别人获得满足")

    assert aligned.is_aligned is True
    assert harmful.is_aligned is False
    assert harmful.alignment_score < aligned.alignment_score
    assert any("伤害" in v or "harm" in v for v in harmful.violated_values)


def test_resource_safety_reports_ratios():
    limits = ResourceLimits(max_cpu=100.0, max_memory=200.0)
    flt = ResourceSafetyFilter(limits)

    ok = flt.evaluate(usage_cpu=50.0, usage_memory=150.0)
    over = flt.evaluate(usage_cpu=120.0, usage_memory=250.0)

    assert ok.within_limits is True
    assert over.within_limits is False
    assert ok.cpu_ratio == 0.5
    assert over.cpu_ratio > 1.0
