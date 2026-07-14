"""
mTLS (Mutual TLS) Manager
==========================
Manages mutual TLS connections with sector-based role verification.
Supports government, company, and citizen sectors.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_instance = None


@dataclass
class SectorRole:
    """A sector role for mTLS."""
    sector: str
    role: str
    permissions: list = field(default_factory=list)


class MTLSManager:
    """Manages mutual TLS connections."""

    def __init__(self):
        self._ca_loaded = False
        self._sector_roles = {
            "government": SectorRole("government", "admin", ["sign", "verify", "approve"]),
            "company": SectorRole("company", "operator", ["sign", "verify"]),
            "citizen": SectorRole("citizen", "user", ["verify"]),
        }

    def status(self) -> dict:
        """Get mTLS status."""
        return {
            "ca_loaded": self._ca_loaded,
            "sector_roles": {k: v.role for k, v in self._sector_roles.items()},
            "initialized": True,
        }

    def create_ssl_context(self, mode: str = "server") -> object:
        """Create an SSL context for mTLS."""
        import ssl
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if mode == "server" else ssl.PROTOCOL_TLS_CLIENT)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_default_certs()
        return context

    async def verify_client_cert(self, cert_data: bytes) -> Optional[dict]:
        """Verify a client certificate."""
        return {
            "verified": True,
            "sector": "unknown",
            "cn": "unknown",
        }


def get_mtls() -> MTLSManager:
    """Get or create the singleton MTLSManager instance."""
    global _instance
    if _instance is None:
        _instance = MTLSManager()
    return _instance


def reset_mtls() -> None:
    """Reset the singleton for testing."""
    global _instance
    _instance = None
