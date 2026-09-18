"""
Qyro Component Module.
Provides React-inspired component lifecycle architecture for Qt/PySide and desktop GUI widgets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Type, TypeVar
import sys

T = TypeVar("T")


class Component:
    """
    Base class / Mixin for building reactive, lifecycle-driven GUI components.
    Inspired by React class components, tailored for Qt (PySide6/PyQt6/PySide2/PyQt5).

    Single Responsibility: Widget UI Lifecycle management (mount, render, style, responsive).
    Does NOT mix with application-level lifecycle (ApplicationContext).

    Lifecycle Execution Order:
      1. __init__(*args, **kwargs) -> super() constructor (e.g. QWidget.__init__)
      2. component_will_mount()
      3. allow_bg()
      4. render() / render_()
      5. component_did_mount()
      6. set_css() / set_CSS()
      7. responsive_ui() / responsive_UI()
      8. resizeEvent() -> automatically triggers responsive_ui() on widget resize
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        orig_init = cls.__init__

        if not getattr(orig_init, "_qyro_component_wrapped", False):
            def wrapped_init(self: Any, *args: Any, **kw: Any) -> None:
                # 1. Base initialization (calls QWidget.__init__, QMainWindow.__init__, ApplicationContext, etc.)
                if orig_init is object.__init__:
                    orig_init(self)
                else:
                    orig_init(self, *args, **kw)

                # 2. Run component lifecycle exactly once after widget is fully constructed
                if not getattr(self, "_component_lifecycle_mounted", False):
                    self._mount_component_lifecycle()

            wrapped_init._qyro_component_wrapped = True
            cls.__init__ = wrapped_init

        # Wrap resizeEvent so that responsive_ui() is ALWAYS called regardless of MRO order
        orig_resize = getattr(cls, "resizeEvent", None)
        if orig_resize is None or not getattr(orig_resize, "_qyro_resize_wrapped", False):
            def wrapped_resize(self: Any, event: Any = None) -> None:
                try:
                    if hasattr(self, "responsive_ui"):
                        self.responsive_ui()
                    elif hasattr(self, "responsive_UI"):
                        self.responsive_UI()
                except Exception:
                    pass

                if orig_resize and callable(orig_resize) and orig_resize != wrapped_resize:
                    try:
                        orig_resize(self, event)
                    except Exception:
                        pass

            wrapped_resize._qyro_resize_wrapped = True
            cls.resizeEvent = wrapped_resize

    def _mount_component_lifecycle(self) -> None:
        """Executes the complete component mounting lifecycle pipeline."""
        self._component_lifecycle_mounted = True

        # 1. Pre-mount hook
        self.component_will_mount()

        # 2. Enable styled background for QWidget stylesheets
        self.allow_bg()

        # 3. Render UI widgets & layouts (supports both render() and render_())
        has_custom_render = type(self).render != Component.render
        has_custom_render_ = type(self).render_ != Component.render_
        if has_custom_render:
            self.render()
        elif has_custom_render_:
            self.render_()
        else:
            self.render()

        # 4. Post-mount hook
        self.component_did_mount()

        # 5. Apply component stylesheets (supports both set_css() and set_CSS())
        if type(self).set_CSS != Component.set_CSS and type(self).set_css == Component.set_css:
            self.set_CSS()
        else:
            self.set_css()

        # 6. Initial responsive layout calculation (supports both responsive_ui() and responsive_UI())
        if type(self).responsive_UI != Component.responsive_UI and type(self).responsive_ui == Component.responsive_ui:
            self.responsive_UI()
        else:
            self.responsive_ui()

    # Lifecycle Hooks
    def component_will_mount(self) -> None:
        """Hook called immediately before UI rendering starts."""
        pass

    def allow_bg(self) -> None:
        """
        Enables Qt.WA_StyledBackground on the widget so stylesheets (background-color,
        border, border-radius) are properly rendered by Qt on custom QWidget subclasses.
        Agnostic across PySide6, PySide2, PyQt6, and PyQt5.
        """
        if not hasattr(self, "setAttribute"):
            return

        qt_attr = None
        # Determine the active Qt binding from self's MRO or loaded modules in sys.modules
        active_pkgs = []
        for cls in getattr(type(self), "__mro__", []):
            mod = getattr(cls, "__module__", "")
            if mod:
                pkg = mod.split(".")[0]
                if pkg in ("PyQt5", "PySide6", "PyQt6", "PySide2") and pkg not in active_pkgs:
                    active_pkgs.append(pkg)

        for pkg in ("PyQt5", "PySide6", "PyQt6", "PySide2"):
            if (f"{pkg}.QtCore" in sys.modules or pkg in sys.modules) and pkg not in active_pkgs:
                active_pkgs.append(pkg)

        candidates = [f"{pkg}.QtCore" for pkg in active_pkgs] if active_pkgs else [
            "PySide6.QtCore", "PyQt6.QtCore", "PySide2.QtCore", "PyQt5.QtCore"
        ]

        for mod_name in candidates:
            try:
                mod = __import__(mod_name, fromlist=["Qt"])
                Qt = getattr(mod, "Qt", None)
                if Qt is not None:
                    # Qt6: Qt.WidgetAttribute.WA_StyledBackground or Qt.WA_StyledBackground
                    if hasattr(Qt, "WidgetAttribute") and hasattr(Qt.WidgetAttribute, "WA_StyledBackground"):
                        qt_attr = Qt.WidgetAttribute.WA_StyledBackground
                    elif hasattr(Qt, "WA_StyledBackground"):
                        qt_attr = Qt.WA_StyledBackground
                if qt_attr is not None:
                    break
            except ImportError:
                continue

        if qt_attr is not None:
            try:
                self.setAttribute(qt_attr, True)
            except Exception:
                pass

    def render(self) -> None:
        """Override to construct child widgets, layouts, and connections."""
        pass

    def render_(self) -> None:
        """Backward compatibility alias for render()."""
        pass

    def component_did_mount(self) -> None:
        """Hook called immediately after UI widgets are constructed and mounted."""
        pass

    def set_css(self, path_or_qss: Optional[str] = None) -> None:
        """
        Applies a stylesheet to this component.
        Can receive:
          - A stylesheet string: set_css("background: #1e1e2e; color: #fff;")
          - A relative resource path: set_css("styles/card.qss")
          - An absolute path: set_css("/path/to/style.qss")
          - None: checks for a class-level `CSS` or `STYLESHEET` attribute.
        """
        if not hasattr(self, "setStyleSheet"):
            return

        content = path_or_qss
        if content is None:
            content = getattr(self, "CSS", None) or getattr(self, "STYLESHEET", None)

        if not content or not isinstance(content, str):
            return

        stylesheet_text = None

        # 1. Check if direct file exists on disk
        direct_path = Path(content)
        if direct_path.exists() and direct_path.is_file():
            try:
                stylesheet_text = direct_path.read_text(encoding="utf-8")
            except Exception:
                pass

        # 2. Check if relative resource exists
        if stylesheet_text is None and not ("{" in content or ";" in content):
            try:
                segments = [s for s in content.replace("\\", "/").split("/") if s]
                resolved = self.get_resource(*segments, required=False)
                resolved_path = Path(resolved)
                if resolved_path.exists() and resolved_path.is_file():
                    stylesheet_text = resolved_path.read_text(encoding="utf-8")
            except Exception:
                pass

        # 3. Fallback: treat string as inline CSS / QSS
        if stylesheet_text is None:
            stylesheet_text = content

        try:
            self.setStyleSheet(stylesheet_text)
        except Exception:
            pass

    def set_CSS(self, path_or_qss: Optional[str] = None) -> None:
        """Backward compatibility alias for set_css."""
        self.set_css(path_or_qss)

    def responsive_ui(self) -> None:
        """
        Override to implement responsive behavior based on current widget dimensions
        (e.g. self.width(), self.height()). Called automatically on mount and on resizeEvent.
        """
        pass

    def responsive_UI(self) -> None:
        """Backward compatibility alias for responsive_ui."""
        self.responsive_ui()

    def resizeEvent(self, event: Any = None) -> None:
        """
        Qt resize event listener. Automatically calls responsive_ui() and passes
        the event to the superclass in the MRO if present.
        """
        try:
            self.responsive_ui()
        except Exception:
            pass

        # Forward to base QWidget.resizeEvent if available
        base_resize = getattr(super(), "resizeEvent", None)
        if base_resize and callable(base_resize):
            try:
                base_resize(event)
            except Exception:
                pass

    # Destruction & Inspection Helpers
    def destroy_component(self) -> None:
        """Safely detaches the widget from its parent and schedules its deletion."""
        if hasattr(self, "setParent"):
            try:
                self.setParent(None)
            except Exception:
                pass
        if hasattr(self, "deleteLater"):
            try:
                self.deleteLater()
            except Exception:
                pass

    def destroyComponent(self) -> None:
        """Backward compatibility alias for destroy_component."""
        self.destroy_component()

    def find(self, target_type: Any, name: str = "") -> Any:
        """
        Finds a child widget by type and optional objectName.
        Delegates to Qt's findChild.
        """
        if hasattr(self, "findChild") and callable(getattr(self, "findChild")):
            return self.findChild(target_type, name)
        return None

    @staticmethod
    def calc(a: float | int, b: float | int) -> int:
        """
        Computes a percentage-based dimension helper: int((a * b) / 100.0).
        Useful in responsive_ui() calculations.
        Example:
          width = self.calc(self.width(), 50)  # 50% of current width
        """
        return int((float(a) * float(b)) / 100.0)

    # Resource and settings access without coupling to ApplicationContext
    def get_resource(self, *segments: str, required: bool = True) -> str:
        """
        Resolves asset path segments and returns an absolute string path.
        Delegates to the engine resource locator.
        """
        import qyro_engine
        return qyro_engine.get_resource(*segments, required=required)

    @property
    def build_settings(self) -> dict[str, Any]:
        """Project build settings dictionary."""
        import qyro_engine
        return qyro_engine.load_build_settings()

    @property
    def is_frozen(self) -> bool:
        """True if running as a frozen executable."""
        import qyro_engine
        return qyro_engine.is_frozen()

    @property
    def props(self) -> dict[str, Any]:
        """
        Component properties dictionary, similar to React props.
        Provides a safe default {} if not explicitly passed.
        """
        if not hasattr(self, "_props"):
            self._props = {}
        return self._props

    @props.setter
    def props(self, value: dict[str, Any]) -> None:
        self._props = value


def init_lifecycle(cls: Type[T]) -> Type[T]:
    """
    Decorator for manually applying the component lifecycle to a widget class
    if not directly subclassing Component.
    When subclassing Component, the lifecycle is initialized automatically.
    """
    orig_init = cls.__init__

    if not getattr(orig_init, "_qyro_component_wrapped", False):
        def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
            orig_init(self, *args, **kwargs)

            lifecycle = getattr(self, "_mount_component_lifecycle", None)

            if lifecycle:
                lifecycle()
                return

            component_lifecycle = (
                ("component_will_mount", None),
                ("allow_bg", None),
                ("render", "render_"),
                ("component_did_mount", None),
                ("set_css", "set_CSS"),
                ("responsive_ui", "responsive_UI"),
            )

            for primary, fallback in component_lifecycle:
                method = getattr(self, primary, None)

                if method is None and fallback:
                    method = getattr(self, fallback, None)

                if method:
                    method()

        wrapped_init._qyro_component_wrapped = True
        cls.__init__ = wrapped_init

    return cls


# Backward compatibility alias
PPGLifeCycle = Component