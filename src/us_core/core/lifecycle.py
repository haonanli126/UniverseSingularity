from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from .orchestration import CoreOrchestrator


class LifecycleState(str, Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"


class LifecycleManager:
    """Simple lifecycle wrapper around CoreOrchestrator."""

    def __init__(self, orchestrator: CoreOrchestrator) -> None:
        self.orchestrator = orchestrator
        self.state: LifecycleState = LifecycleState.CREATED
        self.heartbeat_count: int = 0

    def initialize(self) -> None:
        """Move from CREATED → INITIALIZED. Idempotent."""
        if self.state == LifecycleState.CREATED:
            self.state = LifecycleState.INITIALIZED

    def step(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
        """Run one heartbeat and update state."""
        if self.state not in (LifecycleState.INITIALIZED, LifecycleState.RUNNING):
            raise RuntimeError("LifecycleManager must be initialized before stepping")

        self.state = LifecycleState.RUNNING
        self.heartbeat_count += 1
        return self.orchestrator.heartbeat(context or {})

    def shutdown(self) -> None:
        """Move to STOPPED state."""
        self.state = LifecycleState.STOPPED
