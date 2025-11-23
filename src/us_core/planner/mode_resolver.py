from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


@dataclass
class ModeResolutionInfo:
    """用来描述 mode 是怎么推断出来的，方便调试 / 日志."""

    mode: str
    source: str  # e.g. "fallback", "data/mood/today_mood.json"
    reason: str


def _project_root_from_this_file() -> Path:
    # 当前文件: src/us_core/planner/mode_resolver.py
    # parents[0] = planner
    # parents[1] = us_core
    # parents[2] = src
    # parents[3] = project root
    return Path(__file__).resolve().parents[3]


def _safe_load_json(path: Path) -> Optional[Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError:
        return None

    text = text.strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _normalize_mode(value: str) -> Optional[str]:
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    if v in {"rest", "balance", "focus"}:
        return v
    return None


def _infer_mode_from_payload(payload: Any) -> Optional[str]:
    """尝试从一个 JSON payload 中推断 mode."""

    if isinstance(payload, list) and payload:
        # 有些文件可能是 list[dict]，我们只看最后一条
        payload = payload[-1]

    if not isinstance(payload, dict):
        return None

    # 1) 直接 key: mode / today_mode / recommended_mode / plan_mode
    for key in ("mode", "today_mode", "recommended_mode", "plan_mode"):
        v = payload.get(key)
        m = _normalize_mode(v) if isinstance(v, str) else None
        if m:
            return m

    # 2) dominant_mood / energy / stress 等间接映射
    dominant = str(payload.get("dominant_mood", "")).lower()
    energy = str(payload.get("energy", "")).lower()
    stress = str(payload.get("stress", "")).lower()

    # 非常简单的启发式映射，可以后续迭代：
    # - 明显疲惫 / 压力大的 -> rest
    # - 明显高能量 / 兴奋 -> focus
    # - 其他 -> balance
    tired_words = {"tired", "exhausted", "sad", "low", "burnout"}
    high_energy_words = {"excited", "motivated", "high", "hyper", "flow"}

    if dominant in tired_words or energy in {"low"} or stress in {"high", "very high"}:
        return "rest"
    if dominant in high_energy_words or energy in {"high"}:
        return "focus"

    # 3) 如果有简单的 mode_hint
    hint = payload.get("mode_hint")
    if isinstance(hint, str):
        m = _normalize_mode(hint)
        if m:
            return m

    return None


def resolve_mode_from_mood_files(
    *,
    preferred_mode: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> ModeResolutionInfo:
    """尝试从 data/mood 下的若干 JSON 文件推断今日 mode。

    优先级：
    1. data/mood/today_mood.json
    2. data/mood/today_summary.json
    3. data/mood/daily_mood.json
    4. data/mood/mood_today.json
    各文件内部再用 _infer_mode_from_payload 做推断。

    如果所有文件都不可用 / 推断失败：
    - 如果 preferred_mode 是合法的，就用 preferred_mode；
    - 否则回退到 "balance"。
    """
    if base_dir is None:
        project_root = _project_root_from_this_file()
    else:
        project_root = Path(base_dir)

    mood_dir = project_root / "data" / "mood"

    candidates = [
        mood_dir / "today_mood.json",
        mood_dir / "today_summary.json",
        mood_dir / "daily_mood.json",
        mood_dir / "mood_today.json",
    ]

    for path in candidates:
        if not path.exists():
            continue

        payload = _safe_load_json(path)
        if payload is None:
            continue

        inferred = _infer_mode_from_payload(payload)
        if inferred:
            return ModeResolutionInfo(
                mode=inferred,
                source=str(path.relative_to(project_root)),
                reason="inferred from JSON content",
            )

    # 全部失败，使用 preferred_mode 或默认 balance
    fallback_mode = _normalize_mode(preferred_mode) or "balance"
    if preferred_mode is None:
        reason = "no mood files found, fallback to default"
    else:
        reason = f"no mood files found, fallback to preferred_mode={preferred_mode!r}"

    return ModeResolutionInfo(
        mode=fallback_mode,
        source="fallback",
        reason=reason,
    )
