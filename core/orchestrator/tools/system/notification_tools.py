"""
ASIMNEXUS Notification Tools
System notifications with consent and rate limiting
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("AsimNexus.NotificationTools")


@dataclass
class NotificationResult:
    """Result of a notification operation"""
    success: bool
    message: str
    notification_id: Optional[str] = None
    error: Optional[str] = None


class NotificationTools:
    """
    System notification tools.
    
    Windows: win10toast or plyer
    macOS: osascript (native notifications)
    Linux: notify-send (libnotify)
    
    Rate-limited to prevent spam.
    """

    def __init__(self, max_per_minute: int = 10):
        self._max_per_minute = max_per_minute
        self._call_timestamps: List[float] = []
        self._platform = self._detect_platform()
        self._backend = self._init_backend()
        self._notification_counter = 0
        logger.info(f"✅ NotificationTools initialized for {self._platform}")

    def _detect_platform(self) -> str:
        import sys
        if sys.platform == "win32":
            return "windows"
        elif sys.platform == "darwin":
            return "macos"
        elif sys.platform.startswith("linux"):
            return "linux"
        return sys.platform

    def _init_backend(self) -> Optional[str]:
        """Detect available notification backend"""
        if self._platform == "windows":
            try:
                from win10toast import ToastNotifier
                return "win10toast"
            except ImportError:
                try:
                    import plyer
                    return "plyer"
                except ImportError:
                    return None
        elif self._platform == "macos":
            return "osascript"
        elif self._platform == "linux":
            import subprocess
            try:
                subprocess.run(
                    ["which", "notify-send"],
                    capture_output=True, timeout=3
                )
                return "notify-send"
            except Exception:
                return None
        return None

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = time.time()
        # Remove timestamps older than 60 seconds
        self._call_timestamps = [t for t in self._call_timestamps if now - t < 60]
        if len(self._call_timestamps) >= self._max_per_minute:
            return False
        self._call_timestamps.append(now)
        return True

    async def send_notification(
        self,
        title: str,
        message: str,
        urgency: str = "normal",
        timeout_seconds: int = 5,
    ) -> NotificationResult:
        """
        Send a system notification.
        
        Args:
            title: Notification title
            message: Notification body
            urgency: "low", "normal", or "critical"
            timeout_seconds: How long to show the notification
            
        Returns:
            NotificationResult
        """
        if not self._check_rate_limit():
            return NotificationResult(
                success=False,
                message="Notification rate limited",
                error=f"Max {self._max_per_minute} notifications per minute exceeded",
            )

        if self._backend is None:
            return NotificationResult(
                success=False,
                message="No notification backend available",
                error="Install win10toast (Windows) or notify-send (Linux)",
            )

        try:
            self._notification_counter += 1
            nid = f"notif_{int(time.time())}_{self._notification_counter}"

            if self._backend == "win10toast":
                self._send_win10toast(title, message, timeout_seconds)
            elif self._backend == "plyer":
                self._send_plyer(title, message)
            elif self._backend == "osascript":
                self._send_osascript(title, message)
            elif self._backend == "notify-send":
                self._send_notify_send(title, message, urgency, timeout_seconds)

            logger.info(f"🔔 Notification sent: '{title}' ({nid})")
            return NotificationResult(
                success=True,
                message=f"Notification sent: {title}",
                notification_id=nid,
            )
        except Exception as e:
            logger.error(f"Notification error: {e}")
            return NotificationResult(
                success=False,
                message="Notification failed",
                error=str(e),
            )

    def _send_win10toast(self, title: str, message: str, timeout: int):
        """Windows notification via win10toast"""
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=timeout)

    def _send_plyer(self, title: str, message: str):
        """Cross-platform notification via plyer"""
        from plyer import notification
        notification.notify(title=title, message=message)

    def _send_osascript(self, title: str, message: str):
        """macOS notification via osascript"""
        import subprocess
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, timeout=10
        )

    def _send_notify_send(self, title: str, message: str, urgency: str, timeout: int):
        """Linux notification via notify-send"""
        import subprocess
        urgency_map = {
            "low": "low",
            "normal": "normal",
            "critical": "critical",
        }
        subprocess.run(
            [
                "notify-send",
                "-u", urgency_map.get(urgency, "normal"),
                "-t", str(timeout * 1000),
                title, message,
            ],
            capture_output=True, timeout=10
        )

    async def send_alert(self, title: str, message: str) -> NotificationResult:
        """Send a critical/high-urgency notification"""
        return await self.send_notification(
            title=title, message=message,
            urgency="critical", timeout_seconds=30,
        )

    def get_backend_status(self) -> Dict[str, Any]:
        """Get notification backend status"""
        return {
            "platform": self._platform,
            "backend": self._backend,
            "rate_limit": {
                "max_per_minute": self._max_per_minute,
                "current_rate": len(self._call_timestamps),
            },
            "available": self._backend is not None,
        }


# Global singleton
_notification_tools = None


def get_notification_tools() -> NotificationTools:
    """Get or create the global NotificationTools singleton"""
    global _notification_tools
    if _notification_tools is None:
        _notification_tools = NotificationTools()
    return _notification_tools
