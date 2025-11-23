from __future__ import annotations

import time
from typing import Callable


def measure_step_throughput(step_fn: Callable[[], None], num_steps: int = 100) -> float:
    """简单性能监控：测量每秒可执行多少次 step_fn。

    Args:
        step_fn: 一个无参数的函数，用来执行单步环境 step。
        num_steps: 重复次数，默认 100。

    Returns:
        每秒可执行的步数（steps / second）。
    """
    if num_steps <= 0:
        raise ValueError("num_steps must be positive")

    start = time.perf_counter()
    for _ in range(num_steps):
        step_fn()
    duration = time.perf_counter() - start
    if duration <= 0:
        return float("inf")
    return num_steps / duration
