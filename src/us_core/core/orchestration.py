from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

StepFn = Callable[[Dict[str, Any]], Dict[str, Any]]


@dataclass
class RegisteredSystem:
    name: str
    step_fn: StepFn
    enabled: bool = True


class CoreOrchestrator:
    """Very small orchestrator: runs one heartbeat across all subsystems.

    - You can register named systems with a step function.
    - `heartbeat(context)` will call each enabled system in registration order.
    """

    def __init__(self) -> None:
        self._systems: Dict[str, RegisteredSystem] = {}

    # -------- registration & configuration --------
    def register_system(self, name: str, step_fn: StepFn, enabled: bool = True) -> None:
        self._systems[name] = RegisteredSystem(name=name, step_fn=step_fn, enabled=enabled)

    def enable_system(self, name: str) -> None:
        system = self._systems.get(name)
        if system is not None:
            system.enabled = True

    def disable_system(self, name: str) -> None:
        system = self._systems.get(name)
        if system is not None:
            system.enabled = False

    def list_systems(self) -> List[str]:
        return list(self._systems.keys())

    # -------- execution --------
    def heartbeat(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
        """Run one heartbeat across all enabled systems.

        Returns a dict mapping system name → system step result.
        """
        if context is None:
            context = {}
        # 使用浅拷贝，保证各系统看到相同的输入
        base_context = dict(context)

        results: Dict[str, Dict[str, Any]] = {}
        for name, system in self._systems.items():
            if not system.enabled:
                continue
            result = system.step_fn(dict(base_context))
            if not isinstance(result, dict):
                raise TypeError(f"System {name!r} returned non-dict result: {type(result)!r}")
            results[name] = result
        return results
