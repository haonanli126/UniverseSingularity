from __future__ import annotations

r"""
tasks_cli.py

Phase 3-S05：任务查看 & 手动编辑 CLI。

用法示例（在 venv 已激活的前提下）：

  1）列出当前任务（默认只显示前 50 条）：
      python .\scripts\tasks_cli.py list

  2）列出所有任务：
      python .\scripts\tasks_cli.py list --all

  3）给任务改标题：
      python .\scripts\tasks_cli.py rename --id <TASK_ID> --title "新的标题"

  4）调整优先级：
      python .\scripts\tasks_cli.py set-priority --id <TASK_ID> --priority 10

  5）修改状态（如标记完成）：
      python .\scripts\tasks_cli.py set-status --id <TASK_ID> --status done
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.core.task_store import (
    load_tasks,
    save_tasks,
    update_task_title,
    update_task_priority,
    update_task_status,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity · 任务管理 CLI",
    )

    parser.add_argument(
        "--tasks-file",
        type=str,
        default="",
        help="任务 JSONL 文件路径，默认使用 data/tasks/tasks.jsonl。",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser("list", help="列出当前任务")
    p_list.add_argument(
        "--all",
        action="store_true",
        help="显示所有任务（默认只显示前 50 条）。",
    )

    # rename
    p_rename = subparsers.add_parser("rename", help="修改任务标题")
    p_rename.add_argument("--id", required=True, help="任务 id。")
    p_rename.add_argument("--title", required=True, help="新的标题。")

    # set-priority
    p_priority = subparsers.add_parser("set-priority", help="调整任务优先级")
    p_priority.add_argument("--id", required=True, help="任务 id。")
    p_priority.add_argument(
        "--priority",
        required=True,
        type=int,
        help="新的优先级（整数，数值越大越重要）。",
    )

    # set-status
    p_status = subparsers.add_parser("set-status", help="修改任务状态")
    p_status.add_argument("--id", required=True, help="任务 id。")
    p_status.add_argument(
        "--status",
        required=True,
        help='新的状态（如 "open" / "in_progress" / "done"）。',
    )

    return parser


def _resolve_tasks_path(tasks_file_arg: str) -> Path:
    if tasks_file_arg:
        return Path(tasks_file_arg)
    return PROJECT_ROOT / "data" / "tasks" / "tasks.jsonl"


def _print_task(task: dict, index: int) -> None:
    tid = task.get("id") or task.get("task_id") or "?"
    title = task.get("title") or task.get("description") or "(无标题任务)"
    status = task.get("status") or "open"
    priority = task.get("priority", 0)

    print(f"[{index}] ({tid}) [{status}] priority={priority}")
    print(f"     {title}")
    tags = task.get("tags") or task.get("labels") or []
    if tags:
        if isinstance(tags, (list, tuple)):
            tag_str = ", ".join(str(t) for t in tags)
        else:
            tag_str = str(tags)
        print(f"     tags: {tag_str}")
    print()


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    tasks_path = _resolve_tasks_path(args.tasks_file)
    tasks = load_tasks(tasks_path)

    if args.command == "list":
        if not tasks:
            print(f"任务文件为空或不存在：{tasks_path}")
            return

        limit = None if args.all else 50

        print("==============================================")
        print(" Universe Singularity · 任务列表")
        print("==============================================")
        print(f"任务文件: {tasks_path}")
        print(f"总任务数: {len(tasks)}")
        if limit is not None and len(tasks) > limit:
            print(f"显示前 {limit} 条任务（使用 --all 查看全部）。")
        print()

        shown = tasks if limit is None else tasks[:limit]
        for idx, task in enumerate(shown, start=1):
            _print_task(task, idx)
        return

    # 下面是需要写回文件的操作
    if args.command in {"rename", "set-priority", "set-status"} and not tasks:
        print(f"任务文件为空或不存在：{tasks_path}")
        return

    changed = False

    if args.command == "rename":
        ok = update_task_title(tasks, args.id, args.title)
        if not ok:
            print(f"[失败] 未找到 id={args.id} 的任务。")
            return
        changed = True
        print(f"[成功] 已将任务 {args.id} 的标题更新为：{args.title}")

    elif args.command == "set-priority":
        ok = update_task_priority(tasks, args.id, args.priority)
        if not ok:
            print(f"[失败] 未找到 id={args.id} 的任务。")
            return
        changed = True
        print(f"[成功] 已将任务 {args.id} 的优先级更新为：{args.priority}")

    elif args.command == "set-status":
        ok = update_task_status(tasks, args.id, args.status)
        if not ok:
            print(f"[失败] 未找到 id={args.id} 的任务。")
            return
        changed = True
        print(f"[成功] 已将任务 {args.id} 的状态更新为：{args.status}")

    if changed:
        save_tasks(tasks_path, tasks)
        print(f"[已保存] 任务文件已写回：{tasks_path}")


if __name__ == "__main__":
    main()
