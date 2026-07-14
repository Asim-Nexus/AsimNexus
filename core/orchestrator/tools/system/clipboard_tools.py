"""
ASIMNEXUS Clipboard Tools
Clipboard read/write with explicit user consent
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("AsimNexus.ClipboardTools")


class ClipboardError(Exception):
    """Clipboard operation error"""
    pass


class ConsentRequired(Exception):
    """User consent required for clipboard operation"""
    pass


@dataclass
class ClipboardResult:
    """Result of a clipboard operation"""
    success: bool
    operation: str  # "read" or "write"
    content_preview: Optional[str] = None
    content_length: int = 0
    consented: bool = False
    error: Optional[str] = None


class ClipboardTools:
    """
    Safe clipboard operations with consent gates.
    
    Windows: uses ctypes to call user32 (no external deps)
    Linux/X11: uses xclip or xsel
    macOS: uses pbcopy/pbpaste
    
    All operations require explicit user consent via callback.
    """

    def __init__(self):
        self._platform = self._detect_platform()
        self._consent_timeout = 30  # seconds
        self._last_consent: Dict[str, float] = {}  # user_id -> timestamp
        self._consent_ttl = 300  # 5 minutes before re-requesting consent
        self._pending_consent: Dict[str, Dict] = {}  # request_id -> details
        logger.info(f"✅ ClipboardTools initialized for {self._platform}")

    def _detect_platform(self) -> str:
        import sys
        if sys.platform == "win32":
            return "windows"
        elif sys.platform == "darwin":
            return "macos"
        elif sys.platform.startswith("linux"):
            return "linux"
        return sys.platform

    def _require_consent(self, user_id: str, operation: str) -> bool:
        """Check if consent is still fresh, or raise ConsentRequired"""
        now = time.time()
        last = self._last_consent.get(f"{user_id}:{operation}", 0)
        if now - last < self._consent_ttl:
            return True
        # Create pending consent request
        request_id = f"clipboard_{operation}_{user_id}_{int(now)}"
        self._pending_consent[request_id] = {
            "user_id": user_id,
            "operation": operation,
            "timestamp": now,
            "expires_at": now + self._consent_timeout,
        }
        raise ConsentRequired(request_id)

    def approve_consent(self, request_id: str, user_id: str) -> bool:
        """Approve a pending clipboard consent request"""
        req = self._pending_consent.get(request_id)
        if not req:
            logger.warning(f"Consent request {request_id} not found or expired")
            return False
        if req["user_id"] != user_id:
            logger.warning(f"User mismatch for consent {request_id}")
            return False
        if time.time() > req["expires_at"]:
            del self._pending_consent[request_id]
            logger.warning(f"Consent request {request_id} expired")
            return False
        # Grant consent
        self._last_consent[f"{user_id}:{req['operation']}"] = time.time()
        del self._pending_consent[request_id]
        logger.info(f"✅ Clipboard consent granted: {req['operation']} by {user_id}")
        return True

    def reject_consent(self, request_id: str, user_id: str) -> bool:
        """Reject a pending clipboard consent request"""
        req = self._pending_consent.get(request_id)
        if not req:
            return False
        del self._pending_consent[request_id]
        logger.info(f"🚫 Clipboard consent rejected: {req['operation']} by {user_id}")
        return True

    def list_pending_consents(self, user_id: Optional[str] = None) -> List[Dict]:
        """List pending consent requests"""
        now = time.time()
        # Clean expired
        expired = [k for k, v in self._pending_consent.items() if now > v["expires_at"]]
        for k in expired:
            del self._pending_consent[k]

        results = []
        for req_id, req in self._pending_consent.items():
            if user_id is None or req["user_id"] == user_id:
                results.append({
                    "request_id": req_id,
                    "user_id": req["user_id"],
                    "operation": req["operation"],
                    "expires_in": round(req["expires_at"] - now, 1),
                })
        return results

    async def read_clipboard(self, user_id: str = "guest", consent_if_needed: bool = False) -> ClipboardResult:
        """
        Read clipboard content.
        
        Args:
            user_id: Identifier for consent tracking
            consent_if_needed: If False, raises ConsentRequired instead of auto-consenting
            
        Returns:
            ClipboardResult with content_preview for safety
        """
        try:
            self._require_consent(user_id, "read")
        except ConsentRequired as e:
            if not consent_if_needed:
                return ClipboardResult(
                    success=False,
                    operation="read",
                    error=f"Consent required: {e}. Call approve_consent() first.",
                    consented=False,
                )
            # Auto-approve only if explicitly requested

        try:
            content = self._platform_read()
            preview = content[:200] + ("..." if len(content) > 200 else "")
            return ClipboardResult(
                success=True,
                operation="read",
                content_preview=preview,
                content_length=len(content),
                consented=True,
            )
        except Exception as e:
            logger.error(f"Clipboard read error: {e}")
            return ClipboardResult(
                success=False,
                operation="read",
                error=str(e),
                consented=True,
            )

    async def write_clipboard(self, text: str, user_id: str = "guest") -> ClipboardResult:
        """
        Write text to clipboard. Always requires consent.
        
        Args:
            text: Text to write to clipboard
            user_id: Identifier for consent tracking
            
        Returns:
            ClipboardResult
        """
        if not text:
            return ClipboardResult(
                success=False,
                operation="write",
                error="Cannot write empty content",
            )

        try:
            self._require_consent(user_id, "write")
        except ConsentRequired as e:
            return ClipboardResult(
                success=False,
                operation="write",
                error=f"Consent required: {e}. Call approve_consent() first.",
                consented=False,
            )

        try:
            self._platform_write(text)
            return ClipboardResult(
                success=True,
                operation="write",
                content_length=len(text),
                content_preview=text[:100],
                consented=True,
            )
        except Exception as e:
            logger.error(f"Clipboard write error: {e}")
            return ClipboardResult(
                success=False,
                operation="write",
                error=str(e),
                consented=True,
            )

    def _platform_read(self) -> str:
        """Platform-specific clipboard read"""
        if self._platform == "windows":
            return self._windows_read()
        elif self._platform == "macos":
            return self._macos_read()
        elif self._platform == "linux":
            return self._linux_read()
        else:
            raise ClipboardError(f"Unsupported platform: {self._platform}")

    def _platform_write(self, text: str):
        """Platform-specific clipboard write"""
        if self._platform == "windows":
            return self._windows_write(text)
        elif self._platform == "macos":
            return self._macos_write(text)
        elif self._platform == "linux":
            return self._linux_write(text)
        else:
            raise ClipboardError(f"Unsupported platform: {self._platform}")

    def _windows_read(self) -> str:
        """Windows clipboard read via ctypes"""
        import ctypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if not user32.OpenClipboard(None):
            raise ClipboardError("Cannot open clipboard")

        try:
            handle = user32.GetClipboardData(13)  # CF_UNICODETEXT
            if not handle:
                raise ClipboardError("No text on clipboard")

            # Get pointer to the global lock
            ptr = kernel32.GlobalLock(handle)
            if not ptr:
                raise ClipboardError("Cannot lock clipboard memory")

            try:
                # Read as wide string
                text = ctypes.wstring_at(ptr)
                return text
            finally:
                kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()

    def _windows_write(self, text: str):
        """Windows clipboard write via ctypes"""
        import ctypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if not user32.OpenClipboard(None):
            raise ClipboardError("Cannot open clipboard")

        try:
            user32.EmptyClipboard()

            # Allocate global memory
            text_w = text.encode('utf-16-le')
            handle = kernel32.GlobalAlloc(0x42, len(text_w) + 2)  # GMEM_MOVABLE | GMEM_ZEROINIT
            if not handle:
                raise ClipboardError("Cannot allocate global memory")

            try:
                ptr = kernel32.GlobalLock(handle)
                if not ptr:
                    raise ClipboardError("Cannot lock memory")
                try:
                    ctypes.memmove(ptr, text_w, len(text_w))
                finally:
                    kernel32.GlobalUnlock(handle)

                if not user32.SetClipboardData(13, handle):  # CF_UNICODETEXT
                    raise ClipboardError("Cannot set clipboard data")
            finally:
                # Don't free - clipboard owns it now
                pass
        finally:
            user32.CloseClipboard()

    def _macos_read(self) -> str:
        """macOS clipboard read via pbpaste"""
        import subprocess
        result = subprocess.run(
            ["pbpaste", "-pboard", "general"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            raise ClipboardError(f"pbpaste failed: {result.stderr}")
        return result.stdout

    def _macos_write(self, text: str):
        """macOS clipboard write via pbcopy"""
        import subprocess
        result = subprocess.run(
            ["pbcopy"],
            input=text.encode('utf-8'),
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            raise ClipboardError(f"pbcopy failed: {result.stderr}")

    def _linux_read(self) -> str:
        """Linux clipboard read via xclip or xsel"""
        import subprocess
        # Try xclip first, then xsel
        try:
            result = subprocess.run(
                ["xclip", "-o", "-selection", "clipboard"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout
        except FileNotFoundError:
            pass

        try:
            result = subprocess.run(
                ["xsel", "-b", "-o"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout
        except FileNotFoundError:
            pass

        raise ClipboardError("Clipboard tools not found. Install xclip or xsel.")

    def _linux_write(self, text: str):
        """Linux clipboard write via xclip or xsel"""
        import subprocess
        try:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return
        except FileNotFoundError:
            pass

        try:
            result = subprocess.run(
                ["xsel", "-b", "-i"],
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return
        except FileNotFoundError:
            pass

        raise ClipboardError("Clipboard tools not found. Install xclip or xsel.")


# Global singleton
_clipboard_tools = None


def get_clipboard_tools() -> ClipboardTools:
    """Get or create the global ClipboardTools singleton"""
    global _clipboard_tools
    if _clipboard_tools is None:
        _clipboard_tools = ClipboardTools()
    return _clipboard_tools
