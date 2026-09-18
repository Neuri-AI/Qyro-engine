# Qyro Engine 🚀

> **Clean Architecture Runtime Engine for Python Desktop Applications (PySide6, PyQt6, Kivy, Tkinter)**
> Completely decoupled from CLI build tools, standalone and production-ready.

---

## 🏛️ Clean Architecture Structure

`qyro_engine` is built strictly according to **Clean Architecture** and the **Ports & Adapters (Hexagonal)** pattern:

```text
qyro_engine/
├── domain/                          # [Enterprise Business Rules]
│   ├── entities.py                  # PlatformType, ExecutionMode, AppMetadata, ResourceQuery
│   ├── errors.py                    # Domain exceptions (ResourceNotFoundError, etc.)
│   └── state.py                     # SignalPayload, StateSubscription, StateEvent
│
├── application/                     # [Application Business Rules]
│   ├── ports/                       # Interfaces / Protocols (SPI)
│   │   ├── environment.py           # IEnvironmentPort (frozen vs source detection)
│   │   ├── resources.py             # IResourcePort (asset resolver contract)
│   │   ├── settings.py              # ISettingsPort (build config loader contract)
│   │   ├── state.py                 # IStatePort (reactive store & bus contract)
│   │   ├── ui_framework.py          # IUIFrameworkPort (lifecycle & event loop contract)
│   │   └── telemetry.py             # ITelemetryPort (unhandled exception hook contract)
│   └── use_cases/                   # Orchestration / Interactors
│       ├── resolve_resource.py      # ResolveResourceUseCase
│       ├── load_settings.py         # LoadSettingsUseCase
│       ├── manage_state.py          # ManageStateUseCase
│       └── initialize_engine.py     # InitializeEngineUseCase (Bootstrap)
│
├── adapters/                        # [Interface Adapters]
│   ├── environment/
│   │   └── system_environment.py    # PyInstaller sys._MEIPASS + Source detection
│   ├── settings/
│   │   └── json_settings.py         # base.json + os-specific JSON parser & merger
│   ├── resources/
│   │   └── filesystem_resources.py  # Multi-tiered resource finder (base, os, bundle)
│   ├── state/
│   │   └── reactive_store.py        # Thread-safe in-memory store & signal dispatcher
│   ├── telemetry/
│   │   ├── console_hook.py          # Formatted stderr crash diagnostics
│   │   └── sentry_hook.py           # Optional sentry-sdk cloud crash reporter
│   ├── platform/
│   │   └── detector.py              # OS (Windows/macOS/Linux distros: Ubuntu/Fedora/Arch)
│   └── frameworks/                  # Primary / Driving UI Toolkit Adapters
│       ├── base.py                  # BaseUIFrameworkAdapter
│       ├── qt_base.py               # Shared Qt application lifecycle
│       ├── pyside6_adapter.py       # PySide6 (Qt 6 official)
│       ├── pyqt6_adapter.py         # PyQt6 (Riverbank)
│       ├── pyside2_adapter.py       # PySide2 (Qt 5)
│       ├── pyqt5_adapter.py         # PyQt5 (Qt 5)
│       ├── kivy_adapter.py          # Kivy (Mobile/Desktop multi-touch)
│       ├── tkinter_adapter.py       # Tkinter (Zero-dependency fallback)
│       └── factory.py               # Dynamic framework loader & auto-detection
│
├── reactive/                        # [Reactive UI Bindings]
│   └── widgets.py                   # Two-way data bound widgets (ReactiveLineEdit, CheckBox, etc.)
│
├── client/                          # [Public Facade]
│   └── context.py                   # Ergonomic ApplicationContext for end users
│
├── container.py                     # [Composition Root & Dependency Injection]
└── __init__.py                      # Package entrypoint & convenience helpers
```

---

## ⚡ Quick Start

### 1. Minimal Application (`main.py`)

La clase principal puede heredar directamente de `QMainWindow` y `ApplicationContext` como Mixin, exactamente igual a la experiencia tradicional pero con cero acoplamiento:

```python
import sys
from qyro_engine import ApplicationContext, app_is_frozen
from PySide6.QtWidgets import QMainWindow, QLabel

class MyApp(QMainWindow, ApplicationContext):
    def __init__(self):
        super().__init__()
        # ¡El título de la ventana y el icono de la app se configuran AUTOMÁTICAMENTE!
        # - Título: tomado de "app_name" en base.json
        # - Icono: auto-descubierto desde icons/app.ico, app.png o "icon" en base.json
        self.setMinimumSize(640, 480)

        # Si deseas cambiar el título o icono dinámicamente en cualquier momento:
        # self.window_title = "Nuevo Título"
        # self.set_window_icon("icons/dirty.ico")

        label = QLabel(
            f"Título: {self.window_title}\n"
            f"Icono activo: {self.app_icon}\n"
            f"Plataforma: {self.platform.value} (Frozen: {self.is_frozen})",
            parent=self
        )
        label.move(50, 50)

if __name__ == "__main__":
    # ¡Cero boilerplate! No necesitas pasar framework="pyside6".
    # Qyro Engine lee automáticamente "binding": "PySide6" desde settings/base.json.
    window = MyApp()
    window.show()

    # Ejecución compatible universal con Qt5, Qt6, etc.
    sys.exit(window.exec())
```

> **Manejo Automático de Título e Iconos:**  
> - `ApplicationContext` lee `"app_name"` de `settings/base.json` y lo aplica directamente como título de la ventana (`setWindowTitle`, `title()`, o `title`).
> - Busca automáticamente el icono en `resources/base/icons/Icon.ico` (Windows), `resources/mac/icons/*.png` (macOS) o `resources/linux/icons/*.png` (Linux/Mobile), y lo asigna tanto a la aplicación como a la ventana.
> - Dispones de las propiedades reactivas `self.window_title` y `self.app_icon`.

> **¿Cómo resuelve `get_resource` la estructura de Qyro?**  
> En un proyecto estándar de Qyro:
> ```text
> demo/
>  ├── resources/
>  │    ├── base/icons/ (Icon.ico, 16.png, 24.png, 32.png, 64.png)
>  │    ├── linux/icons/ (128.png, 256.png, 512.png, 1024.png)
>  │    └── mac/icons/ (128.png, 256.png, 512.png, 1024.png)
>  └── settings/
>       ├── base.json
>       ├── linux.json
>       └── mac.json
> ```
> Cuando invocas:
> - `self.get_resource("icons", "Icon.ico")`: busca en `resources/<os>/icons` y luego en `resources/base/icons/Icon.ico`.
> - `self.get_resource("icons", "512.png")`: en Linux resuelve automáticamente `resources/linux/icons/512.png`.
> - `self.get_resource("base", "icons", "Icon.ico")`: resolución explícita directamente en `resources/`.
> - En binarios congelados (`is_frozen`), busca de forma idéntica dentro del bundle empaquetado de PyInstaller (`sys._MEIPASS`).

> **¿Cómo detecta el binding?**  
> `ApplicationContext` consulta `settings/base.json` (clave `"binding"` o `"framework"`). Si tu `base.json` contiene `"binding": "PySide6"`, el motor arranca `PySide6` automáticamente sin obligar al desarrollador a duplicar esa información en el código.


### 2. Soporte Agnóstico: Kivy (Mobile / Touch) y Tkinter (Built-in)

¿Cómo funciona exactamente con **Kivy** o **Tkinter**? Exactamente igual de natural y ergonómico.

#### Ejemplo con Kivy (`"binding": "kivy"` en `base.json`):
```python
from kivy.app import App
from kivy.uix.label import Label
from qyro_engine import ApplicationContext

# Mixin con kivy.app.App
class MyMobileApp(App, ApplicationContext):
    def build(self):
        # Acceso transparente a settings/base.json
        app_name = self.build_settings.get("app_name", "Kivy Mobile App")
        self.title = app_name

        # Resolución segura de recursos en Android/iOS o Desktop:
        # logo_path = self.get_resource("images", "logo.png")

        return Label(text=f"Bienvenido a {app_name}!\nPlataforma: {self.platform.value}")

if __name__ == "__main__":
    app = MyMobileApp()
    app.run()
```

#### Ejemplo con Tkinter (`"binding": "tkinter"` en `base.json`):
```python
import tkinter as tk
from qyro_engine import ApplicationContext

# Mixin con tk.Tk
class MyTkApp(tk.Tk, ApplicationContext):
    def __init__(self):
        super().__init__()
        self.title(self.build_settings.get("app_name", "Tkinter Desktop"))
        self.geometry("400x250")

        lbl = tk.Label(self, text=f"Modo ejecución: {self.execution_mode.value}")
        lbl.pack(pady=40)

if __name__ == "__main__":
    app = MyTkApp()
    app.exec()  # o app.mainloop()
```

Todos los servicios del motor (`build_settings`, `get_resource`, `is_frozen`, `get_state`, `set_state`, `subscribe`, `emit_signal`) funcionan de manera 100% agnóstica al binding.


### 3. Reactive State & Two-Way Binding

```python
from qyro_engine import ApplicationContext
from qyro_engine.reactive.widgets import ReactiveLineEdit, ReactiveLabel

class ReactiveApp(ApplicationContext):
    def run(self):
        # Set initial reactive state
        self.set_state("username", "Ada Lovelace")

        # Two-way bound widget: editing text automatically updates the state store!
        input_field = ReactiveLineEdit(state_key="username", store=self)

        # Reactive label: repaints immediately when state changes
        display_label = ReactiveLabel(state_key="username", store=self)

        # Listen to state changes programmatically
        self.subscribe("username", lambda new_val: print(f"Username changed to: {new_val}"))
```

### 3. Decoupling from CLI (`qyro-cli` / `ppg`)

- **Old Model (`ppg_runtime`)**: Deeply coupled with `ppg` internal folder structures, assuming specific build commands and global module state.
- **New Model (`qyro_engine`)**:
  - Independent runtime package installable via `pip` or `poetry`.
  - Zero dependency on the CLI tool.
  - Pluggable framework adapters (swap `pyside6` for `kivy` or `tkinter` without changing application code).
  - Testable with 100% mocked adapters in CI/CD without requiring GUI displays.
