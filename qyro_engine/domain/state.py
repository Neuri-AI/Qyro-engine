"""
Domain State and Reactivity Contracts.
Clean models for signals, state mutations, and subscriptions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class SignalPayload(Generic[T]):
    """Event emitted when a signal fires or a state property changes."""
    key: str
    new_value: T
    old_value: Optional[T] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StateEvent:
    """Audit entry or replay event for state tracking."""
    key: str
    value: Any
    sender: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StateSubscription:
    """Handle to a reactive subscription allowing clean unsubscription."""
    key: str
    callback: Callable[[Any], None]
    is_active: bool = True

    def unsubscribe(self) -> None:
        self.is_active = False
