from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional

from .skills import Skill


@dataclass
class ActionController:
    """
    动作控制器：负责按顺序执行排队好的技能动作序列。

    这里做一个同步、极简版本：
    - queue_skill(skill): 把技能展开成原始动作队列
    - next_action(): 取出下一个要执行的动作 index
    - emergency_halt(): 立即清空队列
    """

    _queue: Deque[int] = field(default_factory=deque)

    def queue_skill(self, skill: Skill) -> None:
        for idx in skill.action_sequence:
            self._queue.append(int(idx))

    def next_action(self) -> Optional[int]:
        if not self._queue:
            return None
        return self._queue.popleft()

    def is_idle(self) -> bool:
        return not bool(self._queue)

    def emergency_halt(self) -> None:
        """清空所有待执行动作。"""
        self._queue.clear()
