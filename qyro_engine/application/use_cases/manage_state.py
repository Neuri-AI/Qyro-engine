"""
Manage State Use Case.
Orchestrates reads, writes, subscriptions, and signals across reactive UI components.
"""

from typing import Any, Callable, Dict
from qyro_engine.application.ports.state import IStatePort
from qyro_engine.domain.state import StateSubscription


class ManageStateUseCase:
    """Coordinates interaction with the reactive store."""

    def __init__(self, state_port: IStatePort) -> None:
        self._state_port = state_port

    def get_value(self, key: str, default: Any = None) -> Any:
        return self._state_port.get(key, default)

    def set_value(self, key: str, value: Any, sender: str = "app") -> None:
        self._state_port.set(key, value, sender=sender)

    def subscribe(self, key: str, callback: Callable[[Any], None]) -> StateSubscription:
        return self._state_port.subscribe(key, callback)

    def emit_signal(self, name: str, data: Any = None) -> None:
        self._state_port.emit_signal(name, data)

    def on_signal(self, name: str, callback: Callable[[Any], None]) -> StateSubscription:
        return self._state_port.on_signal(name, callback)

    def get_snapshot(self) -> Dict[str, Any]:
        return self._state_port.snapshot()
