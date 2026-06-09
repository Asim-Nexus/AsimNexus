"""
core/platform/__init__.py
AsimNexus — Platform subsystem stub module.

Provides stub implementations for platform detection, session management,
and download link generation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class PlatformType(Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    PWA = "pwa"
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class PlatformInfo:
    """Stub platform information."""
    def __init__(self, platform_type: PlatformType = PlatformType.WEB,
                 os_name: str = "web", os_version: str = "",
                 browser: str = "", is_mobile: bool = False):
        self.platform_type = platform_type
        self.os_name = os_name
        self.os_version = os_version
        self.browser = browser
        self.is_mobile = is_mobile

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform_type": self.platform_type.value,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "browser": self.browser,
            "is_mobile": self.is_mobile,
        }


_STUB_DOWNLOAD_LINKS: Dict[str, str] = {
    "windows": "https://github.com/AsimNexus/releases/download/v1.0.0/asimnexus-windows-x64.exe",
    "macos": "https://github.com/AsimNexus/releases/download/v1.0.0/asimnexus-macos-x64.dmg",
    "linux": "https://github.com/AsimNexus/releases/download/v1.0.0/asimnexus-linux-x64.AppImage",
    "pwa": "https://asimnexus.app",
    "ios": "https://apps.apple.com/app/asimnexus",
    "android": "https://play.google.com/store/apps/details?id=com.asimnexus.app",
}

_INSTALL_INSTRUCTIONS: Dict[str, List[str]] = {
    "windows": ["Download the .exe installer", "Run the installer", "Follow the setup wizard"],
    "macos": ["Download the .dmg file", "Drag to Applications folder", "Right-click and Open (first time)"],
    "linux": ["Download the .AppImage file", "Make executable: chmod +x *.AppImage", "Run the AppImage"],
    "pwa": ["Open the URL in Chrome/Edge", "Click 'Install' in the address bar", "Use as a standalone app"],
}

_PLATFORM_CONFIGS: Dict[str, Dict[str, Any]] = {
    "windows": {"auto_update": True, "system_tray": True, "startup_register": True},
    "macos": {"auto_update": True, "system_tray": True, "startup_register": True},
    "linux": {"auto_update": False, "system_tray": True, "startup_register": False},
    "pwa": {"auto_update": True, "system_tray": False, "startup_register": False},
    "web": {"auto_update": True, "system_tray": False, "startup_register": False},
}


class PlatformManager:
    """Stub platform manager."""

    def detect_platform(self, user_agent: str, platform_hint: Optional[str] = None) -> PlatformInfo:
        if platform_hint == "web" or not platform_hint:
            return PlatformInfo(PlatformType.WEB, "web", "", "", False)
        hint_map = {
            "windows": PlatformInfo(PlatformType.WINDOWS, "Windows", "10", "", False),
            "macos": PlatformInfo(PlatformType.MACOS, "macOS", "14", "", False),
            "linux": PlatformInfo(PlatformType.LINUX, "Linux", "", "", False),
            "ios": PlatformInfo(PlatformType.IOS, "iOS", "17", "", True),
            "android": PlatformInfo(PlatformType.ANDROID, "Android", "14", "", True),
        }
        return hint_map.get(platform_hint, PlatformInfo(PlatformType.WEB, "web"))

    def register_session(self, session_id: str, platform_info: PlatformInfo) -> None:
        pass  # Stub — no-op

    def get_platform_config(self, platform_type: PlatformType) -> Dict[str, Any]:
        return _PLATFORM_CONFIGS.get(platform_type.value, {})

    def get_install_instructions(self, platform_type: PlatformType) -> List[str]:
        return _INSTALL_INSTRUCTIONS.get(platform_type.value, ["Download and run"])

    def get_download_links(self) -> Dict[str, str]:
        return dict(_STUB_DOWNLOAD_LINKS)


_PLATFORM_MANAGER: Optional[PlatformManager] = None


def get_platform_manager() -> PlatformManager:
    global _PLATFORM_MANAGER
    if _PLATFORM_MANAGER is None:
        _PLATFORM_MANAGER = PlatformManager()
    return _PLATFORM_MANAGER


__all__ = [
    "PlatformType", "PlatformInfo", "PlatformManager",
    "get_platform_manager",
]
