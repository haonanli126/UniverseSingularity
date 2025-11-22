from __future__ import annotations

from enum import Enum


class InputChannel(str, Enum):
    """
    感知系统的逻辑输入渠道。

    保持和存储实现解耦，后面要加语音 / Web / 其他前端会比较轻松。
    """

    CLI_NOTE = "cli_note"          # 命令行速记
    CLI_CHECKIN = "cli_checkin"    # 每日心情打卡
    DIALOG = "dialog"              # 对话记录
    JOURNAL = "journal"            # 日记导入
    SYSTEM = "system"              # 系统内部产生的事件

    @classmethod
    def choices(cls) -> list[str]:
        return [c.value for c in cls]

    @classmethod
    def from_str(cls, value: str) -> "InputChannel":
        try:
            return cls(value)
        except ValueError:
            # 未知的渠道时默认 SYSTEM，这样不会崩
            return cls.SYSTEM

    def human_name(self) -> str:
        mapping = {
            InputChannel.CLI_NOTE: "命令行速记",
            InputChannel.CLI_CHECKIN: "每日心情打卡",
            InputChannel.DIALOG: "对话记录",
            InputChannel.JOURNAL: "日记导入",
            InputChannel.SYSTEM: "系统事件",
        }
        return mapping.get(self, self.value)
