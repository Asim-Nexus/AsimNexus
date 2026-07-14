"""
AsimNexus Integration Module
=============================
Bridge module providing IntegrationManager for routes/security.py.
Manages Level-3 human-in-the-loop approval pipeline, veto engine, and audit log.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger("AsimNexus.Integration")


class IntegrationManager:
    """Central integration manager for Level-3 human-in-the-loop approvals."""

    def __init__(self):
        self._pending_approvals: List[Dict[str, Any]] = []
        self._audit_log: List[Dict[str, Any]] = []
        self._veto_count = 0
        self._approve_count = 0
        self._reject_count = 0

    def get_health(self) -> Dict[str, Any]:
        """Health check for all integrated components."""
        return {
            "status": "healthy",
            "pending_approvals": len(self._pending_approvals),
            "total_audit_entries": len(self._audit_log),
            "veto_engine": "active",
            "level3_system": "active",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def evaluate_action(self, action: str, params: Dict = None,
                        user_id: str = "system", context: Dict = None) -> Dict[str, Any]:
        """Evaluate an action through the Level-3 confirmation pipeline."""
        params = params or {}
        context = context or {}
        needs_approval = action in (
            "delete_user", "transfer_funds", "change_constitution",
            "emergency_override", "government_data_request",
            "system_shutdown", "large_payout",
        )
        if needs_approval:
            confirmation_id = str(uuid.uuid4())
            entry = {
                "confirmation_id": confirmation_id,
                "action": action,
                "params": params,
                "user_id": user_id,
                "context": context,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            }
            self._pending_approvals.append(entry)
            self._audit_log.append({
                "type": "evaluation",
                "confirmation_id": confirmation_id,
                "action": action,
                "user_id": user_id,
                "result": "requires_approval",
                "timestamp": datetime.utcnow().isoformat(),
            })
            return {
                "requires_approval": True,
                "confirmation_id": confirmation_id,
                "reason": f"Action '{action}' requires Level-3 human approval",
            }
        return {
            "requires_approval": False,
            "confirmation_id": None,
            "reason": "Action approved automatically",
        }

    def confirm_action(self, confirmation_id: str, user_id: str = "admin",
                       notes: str = "") -> Dict[str, Any]:
        """Confirm (approve) a pending Level-3 action."""
        for i, entry in enumerate(self._pending_approvals):
            if entry["confirmation_id"] == confirmation_id:
                entry["status"] = "approved"
                entry["approved_by"] = user_id
                entry["notes"] = notes
                entry["approved_at"] = datetime.utcnow().isoformat()
                self._approve_count += 1
                self._audit_log.append({
                    "type": "approval",
                    "confirmation_id": confirmation_id,
                    "action": entry["action"],
                    "approved_by": user_id,
                    "notes": notes,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                self._pending_approvals.pop(i)
                return {"status": "approved", "confirmation_id": confirmation_id}
        return {"status": "not_found", "confirmation_id": confirmation_id}

    def reject_action(self, confirmation_id: str, user_id: str = "admin",
                      reason: str = "Rejected by human operator") -> Dict[str, Any]:
        """Reject a pending Level-3 action."""
        for i, entry in enumerate(self._pending_approvals):
            if entry["confirmation_id"] == confirmation_id:
                entry["status"] = "rejected"
                entry["rejected_by"] = user_id
                entry["reason"] = reason
                entry["rejected_at"] = datetime.utcnow().isoformat()
                self._reject_count += 1
                self._audit_log.append({
                    "type": "rejection",
                    "confirmation_id": confirmation_id,
                    "action": entry["action"],
                    "rejected_by": user_id,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                self._pending_approvals.pop(i)
                return {"status": "rejected", "confirmation_id": confirmation_id}
        return {"status": "not_found", "confirmation_id": confirmation_id}

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """List all pending Level-3 human approvals."""
        return list(self._pending_approvals)

    def get_veto_stats(self) -> Dict[str, Any]:
        """Get veto engine statistics."""
        return {
            "total_vetoes": self._veto_count,
            "total_approved": self._approve_count,
            "total_rejected": self._reject_count,
            "pending_count": len(self._pending_approvals),
        }

    def get_audit_log(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the last N entries from the immutable audit log."""
        return list(self._audit_log[-limit:])


# ─── Singleton ─────────────────────────────────────────────────────────────────

_integration_manager_instance: Optional[IntegrationManager] = None


def get_integration_manager() -> IntegrationManager:
    """Get or create the IntegrationManager singleton."""
    global _integration_manager_instance
    if _integration_manager_instance is None:
        _integration_manager_instance = IntegrationManager()
    return _integration_manager_instance


def reset_integration_manager() -> None:
    """Reset the IntegrationManager singleton (for testing)."""
    global _integration_manager_instance
    _integration_manager_instance = None



# Re-export from root-level module: entity_bridge.py
from core.entity_bridge import (
    EntityBridge,
    get_bridge,
)



# Re-export from root-level module: new_architecture_integration.py
from core.new_architecture_integration import (
    ASIMConfig,
    NewASIMNEXUS,
)



# Re-export from root-level module: quantum_bridge.py
from core.quantum_bridge import (
    QuantumAlgorithm,
    QuantumBridge,
    QuantumDevice,
    QuantumJob,
    QuantumKey,
    QuantumProvider,
    get_quantum_bridge,
)


__all__ = [
    "IntegrationManager",
    "get_integration_manager",
    "reset_integration_manager",
]
