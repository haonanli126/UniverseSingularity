from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List


def run(cmd: List[str]) -> None:
    """运行命令并实时打印输出，如果失败则退出。"""
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n命令失败：{' '.join(cmd)}，已中止。", file=sys.stderr)
        sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="保存 UniverseSingularity 进度（测试 + commit + push）")
    parser.add_argument(
        "message",
        nargs="?",
        default="chore: save progress",
        help="git 提交信息（默认：'chore: save progress'）",
    )
    args = parser.parse_args()

    # 1) 跑测试
    run([sys.executable, "-m", "pytest"])

    # 2) git add
    run(["git", "add", "."])

    # 3) git commit
    run(["git", "commit", "-m", args.message])

    # 4) git push
    run(["git", "push", "origin", "main"])

    print("\n✅ 保存完成：测试通过 + 提交 + 推送。")


if __name__ == "__main__":
    main()
