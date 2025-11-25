"""Core integration & lifecycle management for the digital embryo.

This package does NOT replace existing heartbeat / planner logic yet.
For now it provides:
- CoreOrchestrator: register subsystems and run a single heartbeat
- LifecycleManager: simple CREATED → INITIALIZED → RUNNING → STOPPED lifecycle
- PerformanceMetrics: lightweight metrics over a given embryo object
"""

from .orchestration import CoreOrchestrator, RegisteredSystem
from .lifecycle import LifecycleManager, LifecycleState
from .monitoring import PerformanceMetrics

__all__ = [
    "CoreOrchestrator",
    "RegisteredSystem",
    "LifecycleManager",
    "LifecycleState",
    "PerformanceMetrics",
]
