"""
AsimNexus Security Audit Module (Consolidated)
===============================================
Consolidated from: audit_log.py, audit_logger.py

Re-exports all audit-related classes from the primary implementations.
"""

# Re-export from audit_log.py (237 lines, primary implementation)
from core.security.audit_log import (
    AuditLog, audit_log,
    AuditEventType, AuditSeverity,
)

# Re-export from audit_logger.py (105 lines)
from core.security.audit_logger import (
    AuditLogger, AuditAction,
)

__all__ = [
    "AuditLog", "audit_log",
    "AuditEventType", "AuditSeverity",
    "AuditLogger", "AuditAction",
]
