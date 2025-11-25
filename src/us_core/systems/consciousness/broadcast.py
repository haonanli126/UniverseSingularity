from __future__ import annotations

from typing import Any, Callable, Dict, Mapping


SubscriberFn = Callable[[Mapping[str, Any]], None]


class BroadcastSystem:
    """Simple pub-sub style broadcaster for conscious content."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, SubscriberFn] = {}

    def subscribe(self, name: str, callback: SubscriberFn) -> None:
        """Register or replace a subscriber under a given name."""
        self._subscribers[name] = callback

    def unsubscribe(self, name: str) -> None:
        """Remove a subscriber if present."""
        self._subscribers.pop(name, None)

    def broadcast(self, message: Mapping[str, Any]) -> int:
        """Send message to all subscribers.

        Returns the number of subscribers that received the message.
        """
        for cb in self._subscribers.values():
            cb(message)
        return len(self._subscribers)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
