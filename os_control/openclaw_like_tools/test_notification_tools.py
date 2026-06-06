"""
Real pytest tests for NotificationTools with mocked backends
"""

import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def notify():
    """Create a NotificationTools instance with a mocked win10toast backend"""
    from os_control.openclaw_like_tools.notification_tools import NotificationTools
    nt = NotificationTools(max_per_minute=10)
    # Force a specific backend for testing
    nt._platform = "windows"
    nt._backend = "win10toast"
    # Mock the platform-specific send methods
    nt._send_win10toast = MagicMock(return_value=None)
    nt._send_plyer = MagicMock(side_effect=Exception("Should not be called"))
    nt._send_osascript = MagicMock(side_effect=Exception("Should not be called"))
    nt._send_notify_send = MagicMock(side_effect=Exception("Should not be called"))
    return nt


# ── Test NotificationResult Dataclass ──────────────────────────────────────

class TestNotificationResult:
    """Tests for the NotificationResult dataclass"""

    def test_create_success(self):
        """Create a successful NotificationResult"""
        from os_control.openclaw_like_tools.notification_tools import NotificationResult
        result = NotificationResult(
            success=True,
            message="Notification sent: Hello",
            notification_id="notif_123_1",
        )
        assert result.success is True
        assert result.message == "Notification sent: Hello"
        assert result.notification_id == "notif_123_1"
        assert result.error is None

    def test_create_error(self):
        """Create a failed NotificationResult"""
        from os_control.openclaw_like_tools.notification_tools import NotificationResult
        result = NotificationResult(
            success=False,
            message="Notification failed",
            error="Backend not available",
        )
        assert result.success is False
        assert result.error == "Backend not available"
        assert result.notification_id is None


# ── Test Platform Detection ────────────────────────────────────────────────

class TestNotificationToolsPlatform:
    """Tests for platform detection"""

    def test_detect_windows(self, monkeypatch):
        """_detect_platform should return 'windows' on win32"""
        from os_control.openclaw_like_tools.notification_tools import NotificationTools
        nt = NotificationTools()
        monkeypatch.setattr('sys.platform', 'win32')
        assert nt._detect_platform() == "windows"

    def test_detect_macos(self, monkeypatch):
        """_detect_platform should return 'macos' on darwin"""
        from os_control.openclaw_like_tools.notification_tools import NotificationTools
        nt = NotificationTools()
        monkeypatch.setattr('sys.platform', 'darwin')
        assert nt._detect_platform() == "macos"

    def test_detect_linux(self, monkeypatch):
        """_detect_platform should return 'linux' on linux"""
        from os_control.openclaw_like_tools.notification_tools import NotificationTools
        nt = NotificationTools()
        monkeypatch.setattr('sys.platform', 'linux')
        assert nt._detect_platform() == "linux"


# ── Test Backend Init ──────────────────────────────────────────────────────

class TestNotificationToolsBackendInit:
    """Tests for backend initialization"""

    def test_init_backend_win10toast(self):
        """_init_backend should detect win10toast on Windows"""
        import sys
        mock_win10toast = MagicMock()
        mock_toast_notifier = MagicMock()
        mock_win10toast.ToastNotifier = mock_toast_notifier
        sys.modules['win10toast'] = mock_win10toast

        from os_control.openclaw_like_tools.notification_tools import NotificationTools
        nt = NotificationTools()
        # Force platform and re-init
        nt._platform = "windows"
        backend = nt._init_backend()
        assert backend == "win10toast"

    def test_init_backend_osascript(self, monkeypatch):
        """_init_backend should return osascript on macOS"""
        from os_control.openclaw_like_tools.notification_tools import NotificationTools
        nt = NotificationTools()
        nt._platform = "macos"
        backend = nt._init_backend()
        assert backend == "osascript"

    def test_init_backend_unknown(self, monkeypatch):
        """_init_backend should return None for unknown platforms"""
        from os_control.openclaw_like_tools.notification_tools import NotificationTools
        nt = NotificationTools()
        nt._platform = "unknown"
        backend = nt._init_backend()
        assert backend is None


# ── Test Rate Limiting ─────────────────────────────────────────────────────

class TestNotificationToolsRateLimit:
    """Tests for rate limiting"""

    def test_rate_limit_allows_within_limit(self, notify):
        """_check_rate_limit should allow calls within the limit"""
        for _ in range(5):
            assert notify._check_rate_limit() is True
        assert len(notify._call_timestamps) == 5

    def test_rate_limit_blocks_after_limit(self, notify):
        """_check_rate_limit should block calls exceeding the limit"""
        # Fill up to max (10)
        for _ in range(10):
            assert notify._check_rate_limit() is True
        # Next should be blocked
        assert notify._check_rate_limit() is False

    def test_rate_limit_resets_after_60s(self, notify, monkeypatch):
        """Rate limit should reset after 60 seconds"""
        base_time = time.time()
        monkeypatch.setattr('time.time', lambda: base_time)

        # Fill up to max
        for _ in range(10):
            assert notify._check_rate_limit() is True

        # Move forward 61 seconds
        monkeypatch.setattr('time.time', lambda: base_time + 61)

        # Should be allowed again
        assert notify._check_rate_limit() is True


# ── Test Send Notification ─────────────────────────────────────────────────

class TestNotificationToolsSend:
    """Tests for send_notification"""

    @pytest.mark.asyncio
    async def test_send_success(self, notify):
        """send_notification should succeed with valid backend"""
        result = await notify.send_notification(
            title="Test", message="Hello", urgency="normal", timeout_seconds=5
        )
        assert result.success is True
        assert result.notification_id is not None
        assert "Test" in result.message
        notify._send_win10toast.assert_called_once_with("Test", "Hello", 5)

    @pytest.mark.asyncio
    async def test_send_rate_limited(self, notify):
        """send_notification should fail when rate limited"""
        # Fill the rate limit
        for _ in range(10):
            notify._call_timestamps.append(time.time())

        result = await notify.send_notification(title="Test", message="Hello")
        assert result.success is False
        assert "rate limited" in result.message.lower()

    @pytest.mark.asyncio
    async def test_send_no_backend(self):
        """send_notification should fail when no backend available"""
        from os_control.openclaw_like_tools.notification_tools import NotificationTools
        nt = NotificationTools()
        nt._backend = None

        result = await nt.send_notification(title="Test", message="Hello")
        assert result.success is False
        assert "no notification backend" in result.message.lower()

    @pytest.mark.asyncio
    async def test_send_calls_win10toast(self, notify):
        """send_notification should call _send_win10toast on windows"""
        result = await notify.send_notification(
            title="Win Test", message="Hello", timeout_seconds=10
        )
        notify._send_win10toast.assert_called_once_with("Win Test", "Hello", 10)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_calls_plyer(self, notify):
        """send_notification should call _send_plyer when backend='plyer'"""
        notify._send_plyer = MagicMock(return_value=None)
        notify._backend = "plyer"

        result = await notify.send_notification(title="Plyer Test", message="Ping")
        notify._send_plyer.assert_called_once_with("Plyer Test", "Ping")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_calls_osascript(self, notify):
        """send_notification should call _send_osascript when backend='osascript'"""
        notify._send_osascript = MagicMock(return_value=None)
        notify._backend = "osascript"

        result = await notify.send_notification(title="Mac Test", message="Hello")
        notify._send_osascript.assert_called_once_with("Mac Test", "Hello")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_calls_notify_send(self, notify):
        """send_notification should call _send_notify_send when backend='notify-send'"""
        notify._send_notify_send = MagicMock(return_value=None)
        notify._backend = "notify-send"

        result = await notify.send_notification(
            title="Linux Test", message="Hi", urgency="critical", timeout_seconds=15
        )
        notify._send_notify_send.assert_called_once_with("Linux Test", "Hi", "critical", 15)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_handles_exception(self, notify):
        """send_notification should handle backend exceptions gracefully"""
        notify._send_win10toast = MagicMock(side_effect=Exception("Backend crash"))

        result = await notify.send_notification(title="Error Test", message="Oops")
        assert result.success is False
        assert "Backend crash" in result.error

    @pytest.mark.asyncio
    async def test_send_generates_notification_id(self, notify):
        """send_notification should generate a notification ID"""
        result = await notify.send_notification(title="ID Test", message="Check")
        assert result.notification_id is not None
        assert result.notification_id.startswith("notif_")


# ── Test Send Alert ────────────────────────────────────────────────────────

class TestNotificationToolsAlert:
    """Tests for send_alert"""

    @pytest.mark.asyncio
    async def test_send_alert_uses_critical_urgency(self, notify):
        """send_alert should use critical urgency and 30s timeout"""
        notify._send_notify_send = MagicMock(return_value=None)
        notify._backend = "notify-send"

        result = await notify.send_alert(title="Alert!", message="Critical issue")
        notify._send_notify_send.assert_called_once_with(
            "Alert!", "Critical issue", "critical", 30
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_alert_calls_send_notification(self, notify):
        """send_alert should delegate to send_notification"""
        result = await notify.send_alert(title="Alert!", message="Something urgent")
        # Should have called the win10toast backend once
        notify._send_win10toast.assert_called_once()


# ── Test Backend Status ────────────────────────────────────────────────────

class TestNotificationToolsBackendStatus:
    """Tests for get_backend_status"""

    def test_get_backend_status_with_backend(self, notify):
        """get_backend_status should show available backend"""
        status = notify.get_backend_status()
        assert status["platform"] == "windows"
        assert status["backend"] == "win10toast"
        assert status["available"] is True
        assert status["rate_limit"]["max_per_minute"] == 10

    def test_get_backend_status_no_backend(self):
        """get_backend_status should show unavailable when no backend"""
        from os_control.openclaw_like_tools.notification_tools import NotificationTools
        nt = NotificationTools()
        nt._backend = None
        status = nt.get_backend_status()
        assert status["available"] is False
        assert status["backend"] is None

    def test_get_backend_status_rate_limit_info(self, notify):
        """get_backend_status should show current rate limit info"""
        # Make a few calls
        notify._call_timestamps.extend([time.time() - i for i in range(3)])
        status = notify.get_backend_status()
        assert status["rate_limit"]["current_rate"] == 3


# ── Test Global Singleton ──────────────────────────────────────────────────

class TestGetNotificationTools:
    """Tests for the get_notification_tools singleton"""

    def test_get_notification_tools_returns_instance(self):
        """get_notification_tools should return a NotificationTools instance"""
        from os_control.openclaw_like_tools.notification_tools import get_notification_tools
        nt = get_notification_tools()
        from os_control.openclaw_like_tools.notification_tools import NotificationTools
        assert isinstance(nt, NotificationTools)
