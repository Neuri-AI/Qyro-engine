"""
State and Reactivity Port Contract.
Provides reactive state store, signal dispatcher, and subscriptions.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict
from qyro_engine.domain.state import StateSubscription


class IStatePort(ABC):
    """Abstract port for managing reactive application state and signals."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a state property value."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, sender: str = "app") -> None:
        """Sets a state property and notifies subscribers."""
        pass

    @abstractmethod
    def subscribe(self, key: str, callback: Callable[[Any], None]) -> StateSubscription:
        """Subscribes a callback to changes of a specific key."""
        pass

    @abstractmethod
    def emit_signal(self, name: str, data: Any = None) -> None:
        """Broadcasts a named signal."""
        pass

    @abstractmethod
    def on_signal(self, name: str, callback: Callable[[Any], None]) -> StateSubscription:
        """Listens to a named signal."""
        pass

    @abstractmethod
    def snapshot(self) -> Dict[str, Any]:
        """Returns an immutable dictionary snapshot of current state."""
        pass
