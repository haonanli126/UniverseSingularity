"""Global workspace (consciousness) subsystem.

This package provides:
- GlobalWorkspaceSystem: competition & selection of conscious content
- Attention* helpers: filtering, allocation and monitoring of attention
- BroadcastSystem: fan-out of conscious content to subscribers
"""

from .global_workspace import GlobalWorkspaceSystem, WorkspaceItem
from .attention import AttentionFilter, AttentionAllocator, AttentionMonitor, AttentionSnapshot
from .broadcast import BroadcastSystem

__all__ = [
    "GlobalWorkspaceSystem",
    "WorkspaceItem",
    "AttentionFilter",
    "AttentionAllocator",
    "AttentionMonitor",
    "AttentionSnapshot",
    "BroadcastSystem",
]
