"""
Production HSM Shim (Consolidated)
===================================
Re-exports from hsm_production.py for backward compatibility.
The primary HSM implementation is in hsm_integration.py and hsm_client.py.
"""

from core.security.hsm_production import (
    ProductionHSM, HSMProduction, get_hsm,
)

__all__ = ["ProductionHSM", "HSMProduction", "get_hsm"]
