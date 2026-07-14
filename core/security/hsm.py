"""
AsimNexus HSM Bridge Module
============================
Bridge module providing get_hsm_manager() for routes/security.py.
Delegates to core/security/hsm_integration.py for actual HSM operations.
"""

import logging
from typing import Optional

logger = logging.getLogger("AsimNexus.HSM")

# Re-export from the real HSM integration module
from core.security.hsm_integration import (
    HSMIntegration,
    get_hsm,
)

# Alias for routes/security.py compatibility
def get_hsm_manager() -> HSMIntegration:
    """Get the HSM manager singleton (alias for get_hsm())."""
    return get_hsm()


__all__ = [
    "HSMIntegration",
    "get_hsm",
    "get_hsm_manager",
]
