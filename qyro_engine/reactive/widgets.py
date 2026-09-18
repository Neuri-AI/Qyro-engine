"""
Reactive Qt Widgets for Qyro Engine.
Auto-binds Qt UI elements (PySide6, PyQt6, PySide2, PyQt5) to reactive state keys.
Eliminates signal/slot boilerplate with two-way data binding.
"""

from typing import Any, Callable, Optional


def _get_qt_widgets():
    """Dynamically imports QtWidgets from whichever Qt binding is present."""
    for module_name in ["PySide6.QtWidgets", "PyQt6.QtWidgets", "PySide2.QtWidgets", "PyQt5.QtWidgets"]:
        try:
            mod = __import__(module_name, fromlist=["QtWidgets"])
            return mod
        except ImportError:
            continue
    raise ImportError("No Qt binding (PySide6, PyQt6, PySide2, PyQt5) found for ReactiveWidgets.")


class ReactiveWidgetMixin:
    """Mixin for connecting Qt widgets to a Qyro reactive state store."""

    def bind_state(self, store_or_context: Any, state_key: str, read_transform=None, write_transform=None):
        self._qyro_store = getattr(store_or_context, "_container", store_or_context)
        if hasattr(self._qyro_store, "state_adapter"):
            self._qyro_store = self._qyro_store.state_adapter
        self._qyro_key = state_key
        self._read_transform = read_transform or (lambda x: x)
        self._write_transform = write_transform or (lambda x: x)
        self._is_updating = False

        # Subscribe to store changes -> update UI
        self._subscription = self._qyro_store.subscribe(state_key, self._on_store_updated)

    def _on_store_updated(self, new_value: Any):
        if self._is_updating:
            return
        self._is_updating = True
        try:
            self._apply_to_widget(self._read_transform(new_value))
        finally:
            self._is_updating = False

    def _notify_store(self, widget_value: Any):
        if self._is_updating:
            return
        self._is_updating = True
        try:
            self._qyro_store.set(self._qyro_key, self._write_transform(widget_value), sender="widget")
        finally:
            self._is_updating = False

    def _apply_to_widget(self, value: Any):
        raise NotImplementedError


# --- Concrete Reactive Qt Widgets ---

class ReactiveLineEdit(ReactiveWidgetMixin):
    """QLineEdit with bidirectional state binding."""
    def __init__(self, state_key: str = "", store: Any = None, parent: Any = None):
        qt = _get_qt_widgets()
        self._widget = qt.QLineEdit(parent)
        self.bind_state(store, state_key) if store and state_key else None
        self._widget.textChanged.connect(self._notify_store)

    def _apply_to_widget(self, value: Any):
        self._widget.setText(str(value) if value is not None else "")

    def __getattr__(self, name):
        return getattr(self._widget, name)


class ReactiveCheckBox(ReactiveWidgetMixin):
    """QCheckBox with bidirectional boolean state binding."""
    def __init__(self, text: str = "", state_key: str = "", store: Any = None, parent: Any = None):
        qt = _get_qt_widgets()
        self._widget = qt.QCheckBox(text, parent)
        self.bind_state(store, state_key) if store and state_key else None
        self._widget.toggled.connect(self._notify_store)

    def _apply_to_widget(self, value: Any):
        self._widget.setChecked(bool(value))

    def __getattr__(self, name):
        return getattr(self._widget, name)


class ReactiveLabel(ReactiveWidgetMixin):
    """QLabel that auto-refreshes its display text when state changes."""
    def __init__(self, text: str = "", state_key: str = "", store: Any = None, parent: Any = None):
        qt = _get_qt_widgets()
        self._widget = qt.QLabel(text, parent)
        self.bind_state(store, state_key) if store and state_key else None

    def _apply_to_widget(self, value: Any):
        self._widget.setText(str(value) if value is not None else "")

    def __getattr__(self, name):
        return getattr(self._widget, name)


class ReactiveSlider(ReactiveWidgetMixin):
    """QSlider with bidirectional numeric state binding."""
    def __init__(self, orientation: Any = None, state_key: str = "", store: Any = None, parent: Any = None):
        qt = _get_qt_widgets()
        orientation = orientation or 1  # Qt.Horizontal default
        self._widget = qt.QSlider(orientation, parent)
        self.bind_state(store, state_key) if store and state_key else None
        self._widget.valueChanged.connect(self._notify_store)

    def _apply_to_widget(self, value: Any):
        try:
            self._widget.setValue(int(value))
        except (ValueError, TypeError):
            pass

    def __getattr__(self, name):
        return getattr(self._widget, name)


class ReactiveSpinBox(ReactiveWidgetMixin):
    """QSpinBox with bidirectional integer state binding."""
    def __init__(self, state_key: str = "", store: Any = None, parent: Any = None):
        qt = _get_qt_widgets()
        self._widget = qt.QSpinBox(parent)
        self.bind_state(store, state_key) if store and state_key else None
        self._widget.valueChanged.connect(self._notify_store)

    def _apply_to_widget(self, value: Any):
        try:
            self._widget.setValue(int(value))
        except (ValueError, TypeError):
            pass

    def __getattr__(self, name):
        return getattr(self._widget, name)
