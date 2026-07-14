"""
AsimNexus Platform Manager Stub
================================
Stub module for platform/device management.
Provides sensible defaults until full platform implementation is ready.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("AsimNexus.Platform")


class PlatformManager:
    """Platform/device session manager (stub)."""

    def __init__(self):
        self._sessions: List[Dict[str, Any]] = []
        self._downloads: Dict[str, str] = {
            "windows": "https://github.com/AsimNexus/releases/download/v1.0.0-rc2/asimnexus-windows-x64.exe",
            "macos": "https://github.com/AsimNexus/releases/download/v1.0.0-rc2/asimnexus-macos-x64.dmg",
            "linux": "https://github.com/AsimNexus/releases/download/v1.0.0-rc2/asimnexus-linux-x64.AppImage",
            "android": "https://github.com/AsimNexus/releases/download/v1.0.0-rc2/asimnexus-android.apk",
            "ios": "https://github.com/AsimNexus/releases/download/v1.0.0-rc2/asimnexus-ios.ipa",
            "web": "https://asimnexus.io/app",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get platform support status."""
        return {
            "supported_platforms": list(self._downloads.keys()),
            "active_sessions": len(self._sessions),
            "latest_version": "1.0.0-rc2",
            "status": "operational",
        }

    def register_session(self, platform: str, device_id: Optional[str] = None,
                         user_agent: str = "", user_id: str = "anonymous") -> Dict[str, Any]:
        """Register a device/platform session."""
        session = {
            "session_id": f"sess_{len(self._sessions) + 1}",
            "platform": platform,
            "device_id": device_id or "unknown",
            "user_agent": user_agent,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }
        self._sessions.append(session)
        return session

    def get_downloads(self) -> Dict[str, str]:
        """Get download links for all platforms."""
        return self._downloads


# Singleton
_platform_manager: Optional[PlatformManager] = None


def get_platform_manager() -> PlatformManager:
    """Get platform manager singleton."""
    global _platform_manager
    if _platform_manager is None:
        _platform_manager = PlatformManager()
    return _platform_manager
