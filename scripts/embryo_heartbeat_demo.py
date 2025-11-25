"""Simple heartbeat demo for the ConsciousDigitalEmbryo.

Usage (from project root):

    python scripts/embryo_heartbeat_demo.py --steps 5 --delay 0.5
"""

from __future__ import annotations

import argparse
import time
from typing import Any, Dict
import sys
from pathlib import Path

# --- Make sure we can import `us_core` from src/ ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from us_core.core.embryo import ConsciousDigitalEmbryo


def run_demo(steps: int = 5, delay: float = 0.0) -> None:
    """Run a simple heartbeat loop on a demo embryo."""

    embryo = ConsciousDigitalEmbryo.simple_demo()
    ctx: Dict[str, Any] = {}

    print("[UniverseSingularity] ConsciousDigitalEmbryo heartbeat demo")
    print(f"- steps: {steps}")
    print(f"- delay: {delay} seconds between heartbeats\n")

    try:
        for _ in range(steps):
            ctx = embryo.heartbeat(ctx)
            hb_count = embryo.heartbeat_count
            hb_steps = ctx.get("heartbeat_steps")

            print(f"❤️  heartbeat #{hb_count} | ctx.heartbeat_steps = {hb_steps}")

            if delay > 0:
                time.sleep(delay)

    except KeyboardInterrupt:
        print("\n⏹ Interrupted by user, stopping heartbeat loop.")

    print("\n[Summary]")
    print(f"- final heartbeat_count = {embryo.heartbeat_count}")
    if "heartbeat_steps" in ctx:
        print(f"- ctx['heartbeat_steps'] = {ctx['heartbeat_steps']}")
    print("- context keys:", sorted(ctx.keys()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a simple heartbeat demo for the ConsciousDigitalEmbryo.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=5,
        help="Number of heartbeat steps to run (default: 5).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between heartbeats (default: 0, no delay).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_demo(steps=args.steps, delay=args.delay)
