"""
Real pytest tests for ClipboardTools with mocked platform backends
"""

import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def clipboard():
    """Create a ClipboardTools instance mocked to use Windows platform"""
    from os_control.openclaw_like_tools.clipboard_tools import ClipboardTools
    cb = ClipboardTools()
    # Force platform to windows for testing
    cb._platform = "windows"
    # Mock the platform-specific methods
    cb._windows_read = MagicMock(return_value="test clipboard content")
    cb._windows_write = MagicMock(return_value=None)
    # Also mock macos/linux methods to show they shouldn't be called
    cb._macos_read = MagicMock(side_effect=Exception("Should not be called"))
    cb._macos_write = MagicMock(side_effect=Exception("Should not be called"))
    cb._linux_read = MagicMock(side_effect=Exception("Should not be called"))
    cb._linux_write = MagicMock(side_effect=Exception("Should not be called"))
    return cb


# ── Test ClipboardResult Dataclass ─────────────────────────────────────────

class TestClipboardResult:
    """Tests for the ClipboardResult dataclass"""

    def test_create_result_success(self):
        """Create a successful ClipboardResult"""
        from os_control.openclaw_like_tools.clipboard_tools import ClipboardResult
        result = ClipboardResult(
            success=True,
            operation="read",
            content_preview="Hello...",
            content_length=100,
            consented=True,
        )
        assert result.success is True
        assert result.operation == "read"
        assert result.content_preview == "Hello..."
        assert result.content_length == 100
        assert result.consented is True
        assert result.error is None

    def test_create_result_error(self):
        """Create a failed ClipboardResult"""
        from os_control.openclaw_like_tools.clipboard_tools import ClipboardResult
        result = ClipboardResult(
            success=False,
            operation="write",
            error="Permission denied",
            consented=False,
        )
        assert result.success is False
        assert result.error == "Permission denied"


# ── Test Platform Detection ────────────────────────────────────────────────

class TestClipboardToolsPlatform:
    """Tests for platform detection"""

    def test_detect_windows(self, monkeypatch):
        """_detect_platform should return 'windows' on win32"""
        from os_control.openclaw_like_tools.clipboard_tools import ClipboardTools
        cb = ClipboardTools()
        monkeypatch.setattr('sys.platform', 'win32')
        assert cb._detect_platform() == "windows"

    def test_detect_macos(self, monkeypatch):
        """_detect_platform should return 'macos' on darwin"""
        from os_control.openclaw_like_tools.clipboard_tools import ClipboardTools
        cb = ClipboardTools()
        monkeypatch.setattr('sys.platform', 'darwin')
        assert cb._detect_platform() == "macos"

    def test_detect_linux(self, monkeypatch):
        """_detect_platform should return 'linux' on linux"""
        from os_control.openclaw_like_tools.clipboard_tools import ClipboardTools
        cb = ClipboardTools()
        monkeypatch.setattr('sys.platform', 'linux')
        assert cb._detect_platform() == "linux"


# ── Test Consent Flow ──────────────────────────────────────────────────────

class TestClipboardToolsConsent:
    """Tests for the consent management system"""

    def test_require_consent_first_time(self, clipboard):
        """First call for a user/operation should require consent"""
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")
        # Should have created a pending request
        pending = clipboard.list_pending_consents("user1")
        assert len(pending) == 1
        assert pending[0]["operation"] == "read"

    def test_approve_consent(self, clipboard):
        """Approving consent should grant it"""
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")

        pending = clipboard.list_pending_consents("user1")
        request_id = pending[0]["request_id"]

        result = clipboard.approve_consent(request_id, "user1")
        assert result is True

        # Now consent should be cached
        assert clipboard._require_consent("user1", "read") is True

    def test_approve_consent_wrong_user(self, clipboard):
        """Approving with wrong user should fail"""
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")

        pending = clipboard.list_pending_consents("user1")
        request_id = pending[0]["request_id"]

        result = clipboard.approve_consent(request_id, "user2")
        assert result is False

    def test_approve_consent_nonexistent(self, clipboard):
        """Approving a nonexistent request should fail"""
        result = clipboard.approve_consent("nonexistent", "user1")
        assert result is False

    def test_reject_consent(self, clipboard):
        """Rejecting consent should remove the request"""
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")

        pending = clipboard.list_pending_consents("user1")
        request_id = pending[0]["request_id"]

        result = clipboard.reject_consent(request_id, "user1")
        assert result is True
        # Should be removed from pending
        assert len(clipboard.list_pending_consents("user1")) == 0

    def test_reject_consent_nonexistent(self, clipboard):
        """Rejecting a nonexistent request should return False"""
        result = clipboard.reject_consent("nonexistent", "user1")
        assert result is False

    def test_consent_ttl(self, clipboard, monkeypatch):
        """Consent should expire after TTL"""
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired

        # Grant consent
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")
        pending = clipboard.list_pending_consents("user1")
        clipboard.approve_consent(pending[0]["request_id"], "user1")

        # Consent should be valid
        assert clipboard._require_consent("user1", "read") is True

        # Move time forward past TTL
        clipboard._consent_ttl = 300  # 5 minutes
        future_time = time.time() + 301
        monkeypatch.setattr('time.time', lambda: future_time)

        # Now it should require consent again
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")

    def test_list_pending_consents_no_filter(self, clipboard):
        """list_pending_consents with no filter should return all"""
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired

        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user2", "write")

        all_pending = clipboard.list_pending_consents()
        assert len(all_pending) == 2

    def test_list_pending_consents_with_filter(self, clipboard):
        """list_pending_consents should filter by user"""
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired

        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user2", "write")

        user1_pending = clipboard.list_pending_consents("user1")
        assert len(user1_pending) == 1
        assert user1_pending[0]["user_id"] == "user1"

        user2_pending = clipboard.list_pending_consents("user2")
        assert len(user2_pending) == 1
        assert user2_pending[0]["user_id"] == "user2"

    def test_consent_request_has_expiry(self, clipboard):
        """Consent request should have an expires_in field"""
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired

        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")

        pending = clipboard.list_pending_consents("user1")
        assert pending[0]["expires_in"] > 0
        assert pending[0]["expires_in"] <= clipboard._consent_timeout


# ── Test Read Clipboard ────────────────────────────────────────────────────

class TestClipboardToolsRead:
    """Tests for read_clipboard"""

    @pytest.mark.asyncio
    async def test_read_without_consent(self, clipboard):
        """read_clipboard should fail without consent"""
        result = await clipboard.read_clipboard(user_id="user1")
        assert result.success is False
        assert result.consented is False
        assert "consent" in result.error.lower()

    @pytest.mark.asyncio
    async def test_read_with_consent(self, clipboard):
        """read_clipboard should succeed after consent is granted"""
        # First get consent
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")
        pending = clipboard.list_pending_consents("user1")
        clipboard.approve_consent(pending[0]["request_id"], "user1")

        # Now read
        result = await clipboard.read_clipboard(user_id="user1")
        assert result.success is True
        assert result.consented is True
        assert result.content_preview is not None
        assert result.content_length > 0

    @pytest.mark.asyncio
    async def test_read_content_preview(self, clipboard):
        """read_clipboard should return a preview (first 200 chars)"""
        # Grant consent
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")
        pending = clipboard.list_pending_consents("user1")
        clipboard.approve_consent(pending[0]["request_id"], "user1")

        result = await clipboard.read_clipboard(user_id="user1")
        assert result.content_preview == "test clipboard content"
        assert result.content_length == len("test clipboard content")

    @pytest.mark.asyncio
    async def test_read_truncates_long_content(self, clipboard):
        """read_clipboard should truncate content over 200 chars"""
        clipboard._windows_read = MagicMock(return_value="x" * 500)

        # Grant consent
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")
        pending = clipboard.list_pending_consents("user1")
        clipboard.approve_consent(pending[0]["request_id"], "user1")

        result = await clipboard.read_clipboard(user_id="user1")
        assert result.content_preview.endswith("...")
        assert len(result.content_preview) == 203  # 200 + "..."
        assert result.content_length == 500

    @pytest.mark.asyncio
    async def test_read_handles_error(self, clipboard):
        """read_clipboard should handle platform read errors"""
        clipboard._windows_read = MagicMock(side_effect=Exception("Clipboard error"))

        # Grant consent
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")
        pending = clipboard.list_pending_consents("user1")
        clipboard.approve_consent(pending[0]["request_id"], "user1")

        result = await clipboard.read_clipboard(user_id="user1")
        assert result.success is False
        assert "Clipboard error" in result.error

    @pytest.mark.asyncio
    async def test_read_macos_platform(self, clipboard):
        """read_clipboard should call macos read on macos platform"""
        clipboard._platform = "macos"
        macos_result = "macOS clipboard data"
        clipboard._macos_read = MagicMock(return_value=macos_result)
        clipboard._windows_read = MagicMock(side_effect=Exception("Should not be called"))

        # Grant consent
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "read")
        pending = clipboard.list_pending_consents("user1")
        clipboard.approve_consent(pending[0]["request_id"], "user1")

        result = await clipboard.read_clipboard(user_id="user1")
        assert result.success is True
        assert result.content_preview == macos_result
        clipboard._macos_read.assert_called_once()


# ── Test Write Clipboard ───────────────────────────────────────────────────

class TestClipboardToolsWrite:
    """Tests for write_clipboard"""

    @pytest.mark.asyncio
    async def test_write_empty_content(self, clipboard):
        """write_clipboard should reject empty content"""
        result = await clipboard.write_clipboard(text="", user_id="user1")
        assert result.success is False
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_write_without_consent(self, clipboard):
        """write_clipboard should fail without consent"""
        result = await clipboard.write_clipboard(text="hello", user_id="user1")
        assert result.success is False
        assert result.consented is False
        assert "consent" in result.error.lower()

    @pytest.mark.asyncio
    async def test_write_with_consent(self, clipboard):
        """write_clipboard should succeed after consent is granted"""
        # Grant consent
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "write")
        pending = clipboard.list_pending_consents("user1")
        clipboard.approve_consent(pending[0]["request_id"], "user1")

        result = await clipboard.write_clipboard(text="hello world", user_id="user1")
        assert result.success is True
        assert result.consented is True
        assert result.content_length == len("hello world")
        clipboard._windows_write.assert_called_once_with("hello world")

    @pytest.mark.asyncio
    async def test_write_handles_error(self, clipboard):
        """write_clipboard should handle platform write errors"""
        clipboard._windows_write = MagicMock(side_effect=Exception("Write failed"))

        # Grant consent
        from os_control.openclaw_like_tools.clipboard_tools import ConsentRequired
        with pytest.raises(ConsentRequired):
            clipboard._require_consent("user1", "write")
        pending = clipboard.list_pending_consents("user1")
        clipboard.approve_consent(pending[0]["request_id"], "user1")

        result = await clipboard.write_clipboard(text="data", user_id="user1")
        assert result.success is False
        assert "Write failed" in result.error


# ── Test Platform Dispatch ─────────────────────────────────────────────────

class TestClipboardToolsPlatformDispatch:
    """Tests for _platform_read and _platform_write dispatch"""

    def test_platform_read_windows(self, clipboard):
        """_platform_read should call _windows_read on Windows"""
        clipboard._platform = "windows"
        clipboard._windows_read = MagicMock(return_value="data")
        result = clipboard._platform_read()
        assert result == "data"
        clipboard._windows_read.assert_called_once()

    def test_platform_read_macos(self, clipboard):
        """_platform_read should call _macos_read on macOS"""
        clipboard._platform = "macos"
        clipboard._macos_read = MagicMock(return_value="data")
        result = clipboard._platform_read()
        assert result == "data"
        clipboard._macos_read.assert_called_once()

    def test_platform_read_linux(self, clipboard):
        """_platform_read should call _linux_read on Linux"""
        clipboard._platform = "linux"
        clipboard._linux_read = MagicMock(return_value="data")
        result = clipboard._platform_read()
        assert result == "data"
        clipboard._linux_read.assert_called_once()

    def test_platform_read_unsupported(self, clipboard):
        """_platform_read should raise on unsupported platform"""
        clipboard._platform = "unknown"
        from os_control.openclaw_like_tools.clipboard_tools import ClipboardError
        with pytest.raises(ClipboardError, match="Unsupported platform"):
            clipboard._platform_read()

    def test_platform_write_windows(self, clipboard):
        """_platform_write should call _windows_write on Windows"""
        clipboard._platform = "windows"
        clipboard._windows_write = MagicMock()
        clipboard._platform_write("data")
        clipboard._windows_write.assert_called_once_with("data")

    def test_platform_write_unsupported(self, clipboard):
        """_platform_write should raise on unsupported platform"""
        clipboard._platform = "unknown"
        from os_control.openclaw_like_tools.clipboard_tools import ClipboardError
        with pytest.raises(ClipboardError, match="Unsupported platform"):
            clipboard._platform_write("data")


# ── Test Global Singleton ──────────────────────────────────────────────────

class TestGetClipboardTools:
    """Tests for the get_clipboard_tools singleton"""

    def test_get_clipboard_tools_returns_instance(self):
        """get_clipboard_tools should return a ClipboardTools instance"""
        from os_control.openclaw_like_tools.clipboard_tools import get_clipboard_tools
        cb = get_clipboard_tools()
        from os_control.openclaw_like_tools.clipboard_tools import ClipboardTools
        assert isinstance(cb, ClipboardTools)
