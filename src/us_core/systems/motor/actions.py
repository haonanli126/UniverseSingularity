from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ActionSpec:
    """肌肉系统里的原始动作定义。"""

    name: str
    index: int
    description: str = ""


class ActionLibrary:
    """
    定义所有原始动作。
    在当前网格世界里，我们约定 6 个基础动作：
    0: MOVE_UP, 1: MOVE_DOWN, 2: MOVE_LEFT, 3: MOVE_RIGHT, 4: STAY, 5: INTERACT
    """

    def __init__(self) -> None:
        self._actions: Dict[str, ActionSpec] = {}
        self._by_index: Dict[int, ActionSpec] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        base = [
            ("MOVE_UP", 0, "向上移动一格"),
            ("MOVE_DOWN", 1, "向下移动一格"),
            ("MOVE_LEFT", 2, "向左移动一格"),
            ("MOVE_RIGHT", 3, "向右移动一格"),
            ("STAY", 4, "保持不动"),
            ("INTERACT", 5, "与当前格子交互（开门/拾取等）"),
        ]
        for name, idx, desc in base:
            spec = ActionSpec(name=name, index=idx, description=desc)
            self._actions[name] = spec
            self._by_index[idx] = spec

    def get_index(self, name: str) -> int:
        return self._actions[name].index

    def get_name(self, index: int) -> str:
        return self._by_index[index].name

    def is_valid_index(self, index: int) -> bool:
        return index in self._by_index

    def list_action_names(self) -> List[str]:
        return list(self._actions.keys())

    def all_specs(self) -> List[ActionSpec]:
        return list(self._actions.values())
