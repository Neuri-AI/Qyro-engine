"""
Platform Detection Adapter.
Detects OS and desktop environment with fine-grained distro support.
"""

import os
import platform
import sys
from qyro_engine.domain.entities import PlatformType


class PlatformDetector:
    """Detects host operating system, architecture, and desktop flavors."""

    @staticmethod
    def get_platform() -> PlatformType:
        if sys.platform.startswith("win"):
            return PlatformType.WINDOWS
        elif sys.platform == "darwin":
            return PlatformType.MACOS
        elif sys.platform.startswith("linux"):
            return PlatformType.LINUX
        elif "android" in sys.platform:
            return PlatformType.ANDROID
        return PlatformType.UNKNOWN

    @classmethod
    def is_windows(cls) -> bool:
        return cls.get_platform() == PlatformType.WINDOWS

    @classmethod
    def is_mac(cls) -> bool:
        return cls.get_platform() == PlatformType.MACOS

    @classmethod
    def is_linux(cls) -> bool:
        return cls.get_platform() == PlatformType.LINUX

    @classmethod
    def is_ubuntu(cls) -> bool:
        return cls._linux_distro_id() == "ubuntu"

    @classmethod
    def is_fedora(cls) -> bool:
        return cls._linux_distro_id() == "fedora"

    @classmethod
    def is_arch(cls) -> bool:
        return cls._linux_distro_id() in ("arch", "manjaro")

    @classmethod
    def is_gnome(cls) -> bool:
        de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        return "gnome" in de

    @classmethod
    def is_kde(cls) -> bool:
        de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        return "kde" in de

    @staticmethod
    def _linux_distro_id() -> str:
        if not sys.platform.startswith("linux"):
            return ""
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("ID="):
                        return line.strip().split("=")[1].strip('"').lower()
        except Exception:
            pass
        return ""
