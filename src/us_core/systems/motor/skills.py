from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .actions import ActionLibrary


@dataclass
class Skill:
    """一个宏动作：由一串原始动作组成。"""

    name: str
    action_sequence: List[int] = field(default_factory=list)
    description: str = ""


class SkillLibrary:
    """管理技能库，可在原始动作之上注册/组合技能。"""

    def __init__(self, action_library: ActionLibrary) -> None:
        self._action_library = action_library
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill:
        return self._skills[name]

    def list_skill_names(self) -> List[str]:
        return list(self._skills.keys())

    @classmethod
    def with_default_skills(cls, action_library: ActionLibrary) -> "SkillLibrary":
        """创建一个带少量通用技能的技能库。"""
        lib = cls(action_library)

        move_up = action_library.get_index("MOVE_UP")
        move_down = action_library.get_index("MOVE_DOWN")
        move_left = action_library.get_index("MOVE_LEFT")
        move_right = action_library.get_index("MOVE_RIGHT")

        # 一个简单的“巡视”技能：在一个小方形上走一圈
        explore_seq = [move_up, move_right, move_down, move_left]
        lib.register(
            Skill(
                name="explore",
                action_sequence=explore_seq,
                description="简单的方形巡视路径。",
            )
        )

        # 向前两步 + 交互
        advance_and_interact = [
            move_up,
            move_up,
            action_library.get_index("INTERACT"),
        ]
        lib.register(
            Skill(
                name="advance_and_interact",
                action_sequence=advance_and_interact,
                description="向前两步后尝试交互。",
            )
        )

        return lib
