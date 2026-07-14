"""
AsimNexus — Governance Audit Module (Legacy Shim)
====================================================
Re-exports from the canonical governance.governance_audit module.
The canonical implementation lives at governance/governance_audit.py.

This shim ensures existing imports from core.governance.governance_audit
continue to work without modification.
"""

import logging
import os
from typing import Any, Optional

# NOTE: Lazy imports below to avoid circular import when
# core/governance/__init__.py triggers loading of this module
# while the root governance package is still being resolved.

logger = logging.getLogger("AsimNexus.Governance.Audit.Shim")

# Canonical DB path for governance audit records
_AUDIT_DB_PATH: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "governance_audit.jsonl",
)

# Re-export for backward compatibility
__all__ = [
    "AuditRecord",
    "GovernanceAudit",
    "_AUDIT_DB_PATH",
    "get_governance_audit",
    "reset_governance_audit",
]


class AuditRecord:
    """
    Legacy AuditRecord wrapper for backward compatibility.
    Delegates to the canonical AuditEntry from governance.governance_audit.
    """
    def __init__(self, audit_id: str, action: str, actor: str, target: str,
                 timestamp: float, details: dict = None, previous_hash: str = None):
        self.audit_id = audit_id
        self.action = action
        self.actor = actor
        self.target = target
        self.timestamp = timestamp
        self.details = details or {}
        self.previous_hash = previous_hash


def _get_root_module():
    """Lazy-import the root governance.governance_audit module."""
    import importlib
    return importlib.import_module("governance.governance_audit")


# Singleton for backward compatibility
_governance_audit: Optional[Any] = None


def get_governance_audit():
    """Get or create the governance audit singleton (sync wrapper)."""
    global _governance_audit
    if _governance_audit is None:
        root = _get_root_module()
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            _governance_audit = loop.run_until_complete(
                root.get_governance_audit()
            )
        except RuntimeError:
            _governance_audit = asyncio.run(
                root.get_governance_audit()
            )
    return _governance_audit


def reset_governance_audit() -> None:
    """Reset the singleton (for testing)."""
    global _governance_audit
    _governance_audit = None
