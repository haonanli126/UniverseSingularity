from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Set


DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


@dataclass
class Task:
    """统一任务模型，兼容现有 tasks.jsonl 的字段设计。

    尽量容错：未知字段存到 raw 里。
    """

    id: str
    title: str
    status: str = "open"
    priority: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    estimated_minutes: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        # id 容错：id / task_id / uuid / _id 都尝试一下
        task_id = (
            str(
                data.get(
                    "id",
                    data.get(
                        "task_id",
                        data.get("uuid", data.get("_id", "unknown")),
                    ),
                )
            )
        )

        title = str(data.get("title") or data.get("name") or "Untitled task")

        status = str(data.get("status", "open"))

        # priority 允许是 int / str("1"/"high")
        priority_raw = data.get("priority")
        priority: Optional[int]
        if isinstance(priority_raw, int):
            priority = priority_raw
        elif isinstance(priority_raw, str) and priority_raw.strip().isdigit():
            priority = int(priority_raw.strip())
        else:
            # 如果有 high/medium/low 映射一下
            mapping = {"low": 1, "medium": 2, "high": 3}
            priority = mapping.get(str(priority_raw).lower()) if priority_raw is not None else None

        tags_raw = data.get("tags") or data.get("labels") or []
        if isinstance(tags_raw, str):
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        elif isinstance(tags_raw, Sequence):
            tags = [str(t).strip() for t in tags_raw if str(t).strip()]
        else:
            tags = []

        est_raw = data.get("estimated_minutes") or data.get("estimate")
        if isinstance(est_raw, (int, float)):
            estimated_minutes = int(est_raw)
        elif isinstance(est_raw, str) and est_raw.strip().isdigit():
            estimated_minutes = int(est_raw.strip())
        else:
            estimated_minutes = None

        created_at = parse_dt(data.get("created_at") or data.get("createdAt"))
        updated_at = parse_dt(data.get("updated_at") or data.get("updatedAt"))
        due_date = parse_dt(data.get("due_date") or data.get("dueDate"))

        # 把已知字段剔除，剩下的都塞进 raw
        known_keys: Set[str] = {
            "id",
            "task_id",
            "uuid",
            "_id",
            "title",
            "name",
            "status",
            "priority",
            "tags",
            "labels",
            "estimated_minutes",
            "estimate",
            "created_at",
            "createdAt",
            "updated_at",
            "updatedAt",
            "due_date",
            "dueDate",
        }
        raw = {k: v for k, v in data.items() if k not in known_keys}

        return cls(
            id=task_id,
            title=title,
            status=status,
            priority=priority,
            tags=tags,
            estimated_minutes=estimated_minutes,
            created_at=created_at,
            updated_at=updated_at,
            due_date=due_date,
            raw=raw,
        )


@dataclass
class FilterSpec:
    """任务过滤条件。都为 None 时不生效。"""

    statuses: Optional[Set[str]] = None
    min_priority: Optional[int] = None
    max_priority: Optional[int] = None
    include_tags: Optional[Set[str]] = None
    exclude_tags: Optional[Set[str]] = None
    search: Optional[str] = None


@dataclass
class PlanConfig:
    """规划配置，主要是模式 + 数量控制。"""

    mode: str  # "rest" / "balance" / "focus"
    max_tasks: int = 5
    duration_minutes: int = 90
    default_task_minutes: int = 25


@dataclass
class PlannedTask:
    """带有评分和解释的任务。"""

    task: Task
    score: float
    reasons: Dict[str, float]

    @property
    def estimated_minutes(self) -> int:
        return self.task.estimated_minutes or 0


@dataclass
class PlanResult:
    """规划结果。"""

    mode: str
    total_estimated_minutes: int
    tasks: List[PlannedTask]
