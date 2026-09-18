"""
Reactive State Store Adapter.
Thread-safe reactive store and event broker implementing IStatePort.
"""

from collections import defaultdict
import threading
from typing import Any, Callable, Dict, List
from qyro_engine.application.ports.state import IStatePort
from qyro_engine.domain.state import SignalPayload, StateSubscription


class ReactiveStoreAdapter(IStatePort):
    """In-memory reactive state manager with observable keys and signals."""

    def __init__(self, initial_state: Dict[str, Any] | None = None) -> None:
        self._lock = threading.RLock()
        self._data: Dict[str, Any] = dict(initial_state or {})
        self._subscribers: Dict[str, List[StateSubscription]] = defaultdict(list)
        self._signal_listeners: Dict[str, List[StateSubscription]] = defaultdict(list)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any, sender: str = "app") -> None:
        with self._lock:
            old_val = self._data.get(key)
            if old_val == value:
                return  # Skip no-op updates to avoid infinite loops

            self._data[key] = value
            payload = SignalPayload(key=key, new_value=value, old_value=old_val)
            active_subs = [s for s in self._subscribers[key] if s.is_active]
            self._subscribers[key] = active_subs

        # Dispatch outside the lock to prevent deadlocks in UI thread
        for sub in active_subs:
            try:
                sub.callback(value)
            except Exception as e:
                print(f"[QyroEngine State Error] Listener for key '{key}' raised: {e}")

    def subscribe(self, key: str, callback: Callable[[Any], None]) -> StateSubscription:
        with self._lock:
            subscription = StateSubscription(key=key, callback=callback, is_active=True)
            self._subscribers[key].append(subscription)
            current_value = self._data.get(key)

        # Notify initial value immediately if present
        if current_value is not None:
            try:
                callback(current_value)
            except Exception:
                pass

        return subscription

    def emit_signal(self, name: str, data: Any = None) -> None:
        with self._lock:
            active_listeners = [s for s in self._signal_listeners[name] if s.is_active]
            self._signal_listeners[name] = active_listeners

        for sub in active_listeners:
            try:
                sub.callback(data)
            except Exception as e:
                print(f"[QyroEngine Signal Error] Listener for signal '{name}' raised: {e}")

    def on_signal(self, name: str, callback: Callable[[Any], None]) -> StateSubscription:
        with self._lock:
            sub = StateSubscription(key=name, callback=callback, is_active=True)
            self._signal_listeners[name].append(sub)
            return sub

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data)
