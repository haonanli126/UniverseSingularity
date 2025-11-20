from __future__ import annotations

"""
日记导入脚本（Journal Importer v0）

用法（在项目根目录运行）：

(.venv) PS D:/UniverseSingularity> python scripts/import_journal.py

- 从 data/journal/ 读取所有 .txt 文件
- 解析为 JournalEntry
- 转换为 EmbryoEvent(kind="journal_entry")
- 追加写入会话日志（通常是 data/memory/session_log.jsonl）

注意：目前未做去重，多次导入同一文件会产生多条记录。
"""

import sys
from pathlib import Path

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from config.settings import get_settings
from config.genome import get_genome
from src.us_core.utils.logger import setup_logger
from src.us_core.core.journal import load_journal_entries_from_folder, journal_entry_to_event
from src.us_core.core.persistence import append_event_to_jsonl


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("import_journal")

    journal_folder = PROJECT_ROOT / Path("data/journal")
    session_log_path = PROJECT_ROOT / Path(genome.memory.long_term.path)

    print("=== Universe Singularity - Journal Importer v0 ===")
    print(f"环境: {settings.environment}")
    print(f"日记文件夹: {journal_folder}")
    print(f"会话日志路径: {session_log_path}")
    print()

    # 确保目录存在
    journal_folder.mkdir(parents=True, exist_ok=True)
    session_log_path.parent.mkdir(parents=True, exist_ok=True)

    entries = load_journal_entries_from_folder(journal_folder)

    if not entries:
        print("当前 data/journal/ 下没有任何 .txt 日记文件。")
        print("你可以先在该目录放一些 .txt 文件，再重新运行本脚本。")
        return

    print(f"检测到 {len(entries)} 条日记，开始导入...\n")

    for entry in entries:
        event = journal_entry_to_event(entry)
        append_event_to_jsonl(session_log_path, event)
        print(f"[导入] {entry.source_file.name} -> {session_log_path}")

    print()
    print(f"导入完成，本次共写入 {len(entries)} 条日记事件。")
    logger.info("Imported %d journal entries from %s", len(entries), journal_folder)


if __name__ == "__main__":
    main()
