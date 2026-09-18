"""
Qyro Engine Dependency Injection Container & Composition Root.
Wires Ports, Adapters, and Use Cases together following Clean Architecture.
"""

from pathlib import Path
from typing import Any, Dict, Optional

# Ports
from qyro_engine.application.ports.environment import IEnvironmentPort
from qyro_engine.application.ports.resources import IResourcePort
from qyro_engine.application.ports.settings import ISettingsPort
from qyro_engine.application.ports.state import IStatePort
from qyro_engine.application.ports.telemetry import ITelemetryPort
from qyro_engine.application.ports.ui_framework import IUIFrameworkPort

# Adapters
from qyro_engine.adapters.environment.system_environment import SystemEnvironmentAdapter
from qyro_engine.adapters.resources.filesystem_resources import FileSystemResourceAdapter
from qyro_engine.adapters.settings.json_settings import JsonSettingsAdapter
from qyro_engine.adapters.state.reactive_store import ReactiveStoreAdapter
from qyro_engine.adapters.telemetry.console_hook import ConsoleExceptionHookAdapter
from qyro_engine.adapters.telemetry.sentry_hook import SentryExceptionHookAdapter
from qyro_engine.adapters.frameworks.factory import FrameworkFactory

# Use Cases
from qyro_engine.application.use_cases.resolve_resource import ResolveResourceUseCase
from qyro_engine.application.use_cases.load_settings import LoadSettingsUseCase
from qyro_engine.application.use_cases.manage_state import ManageStateUseCase
from qyro_engine.application.use_cases.initialize_engine import InitializeEngineUseCase


class EngineContainer:
    """Composition root for Qyro Engine instances."""

    def __init__(
        self,
        framework_name: Optional[str] = None,
        custom_root: Optional[Path] = None,
        custom_resources_dir: Optional[Path] = None,
        custom_settings_dir: Optional[Path] = None,
        enable_sentry: bool = True,
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        # 1. Initialize Adapters (Infrastructure)
        self.env_adapter: IEnvironmentPort = SystemEnvironmentAdapter(custom_root=custom_root)
        self.settings_adapter: ISettingsPort = JsonSettingsAdapter(
            env_port=self.env_adapter,
            custom_settings_dir=custom_settings_dir,
        )
        self.resource_adapter: IResourcePort = FileSystemResourceAdapter(
            env_port=self.env_adapter,
            custom_resources_dir=custom_resources_dir,
        )
        self.state_adapter: IStatePort = ReactiveStoreAdapter(initial_state=initial_state)

        # Telemetry selection
        raw_settings = self.settings_adapter.get_raw_settings()
        sentry_dsn = raw_settings.get("sentry_dsn", "")
        if enable_sentry and sentry_dsn:
            self.telemetry_adapter: ITelemetryPort = SentryExceptionHookAdapter(
                dsn=sentry_dsn,
                release=raw_settings.get("version", "0.1.0"),
            )
        else:
            self.telemetry_adapter = ConsoleExceptionHookAdapter()

        # Framework Driver:
        # Automatically infer from base.json "binding" or "framework" if not explicitly specified
        effective_framework = (
            framework_name
            or raw_settings.get("binding")
            or raw_settings.get("framework")
        )
        self.framework_adapter: IUIFrameworkPort = FrameworkFactory.create(effective_framework)

        # 2. Initialize Use Cases (Application Core)
        self.resolve_resource_use_case = ResolveResourceUseCase(self.resource_adapter)
        self.load_settings_use_case = LoadSettingsUseCase(self.settings_adapter)
        self.manage_state_use_case = ManageStateUseCase(self.state_adapter)
        self.initialize_engine_use_case = InitializeEngineUseCase(
            env_port=self.env_adapter,
            settings_port=self.settings_adapter,
            framework_port=self.framework_adapter,
            telemetry_port=self.telemetry_adapter,
        )
