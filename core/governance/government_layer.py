"""Government Layer — Sovereign governance for the 51% public sector.

Implements the 51% public control mechanism:
- Constitutional rule enforcement
- Sovereign veto power over critical kernel changes
- Policy pack approval for government-layer rules
- Audit oversight for all government actions
- Emergency override procedures

This is the 51% public side of the 51/49 governance model.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class VetoType(Enum):
    """Types of sovereign veto power."""
    CONSTITUTIONAL = "constitutional"   # Blocks changes to immutable principles
    POLICY = "policy"                   # Blocks policy pack changes
    OPERATIONAL = "operational"         # Blocks specific operations
    EMERGENCY = "emergency"             # Emergency system-wide halt


class GovernmentAction(Enum):
    """Types of government-layer actions."""
    APPROVE_POLICY = "approve_policy"
    VETO_ACTION = "veto_action"
    OVERRIDE = "override"
    AUDIT_REVIEW = "audit_review"
    EMERGENCY_DECLARE = "emergency_declare"
    CONSTITUTIONAL_AMENDMENT = "constitutional_amendment"


@dataclass
class VetoRecord:
    """Record of a sovereign veto action."""
    veto_id: str
    veto_type: VetoType
    initiated_by: str
    target_action: str
    reason: str
    approved: bool
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: Optional[str] = None


@dataclass
class GovernmentAuditEntry:
    """An audit entry for government-layer actions."""
    entry_id: str
    action: GovernmentAction
    initiated_by: str
    target: str
    details: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class GovernmentLayer:
    """Government governance layer — 51% public control.

    Manages sovereign oversight, veto power, constitutional enforcement,
    and audit trails for all government-layer actions.
    """

    # Immutable constitutional principles that cannot be overridden
    CONSTITUTIONAL_PRINCIPLES = [
        "individual_sovereignty",
        "human_in_the_loop",
        "data_ownership",
        "transparent_governance",
        "non_discrimination",
        "right_to_explain",
        "right_to_opt_out",
        "audit_trail_integrity",
    ]

    def __init__(self):
        self._veto_records: List[VetoRecord] = []
        self._audit_log: List[GovernmentAuditEntry] = []
        self._emergency_active = False
        self._constitutional_amendments: List[Dict[str, Any]] = []

    def check_constitutional_compliance(
        self, action: str, target: str
    ) -> Tuple[bool, Optional[str]]:
        """Check if an action violates constitutional principles.

        Args:
            action: The action being checked.
            target: What the action targets.

        Returns:
            Tuple of (is_compliant, violation_reason).
        """
        # Check if action targets a constitutional principle
        for principle in self.CONSTITUTIONAL_PRINCIPLES:
            if principle in target.lower() or principle in action.lower():
                return False, f"Action violates constitutional principle: {principle}"

        return True, None

    def issue_veto(
        self,
        veto_type: VetoType,
        initiated_by: str,
        target_action: str,
        reason: str,
    ) -> VetoRecord:
        """Issue a sovereign veto.

        Args:
            veto_type: Type of veto (constitutional, policy, operational, emergency).
            initiated_by: Who is issuing the veto.
            target_action: The action being vetoed.
            reason: Why the veto is being issued.

        Returns:
            VetoRecord with the result.
        """
        veto_id = str(uuid.uuid4())

        # Constitutional vetoes are automatically approved
        approved = veto_type == VetoType.CONSTITUTIONAL

        record = VetoRecord(
            veto_id=veto_id,
            veto_type=veto_type,
            initiated_by=initiated_by,
            target_action=target_action,
            reason=reason,
            approved=approved,
            resolved_at=datetime.utcnow().isoformat() if approved else None,
        )
        self._veto_records.append(record)

        # Log audit
        self._audit_log.append(GovernmentAuditEntry(
            entry_id=str(uuid.uuid4()),
            action=GovernmentAction.VETO_ACTION,
            initiated_by=initiated_by,
            target=target_action,
            details=f"{veto_type.value} veto: {reason} (approved={approved})",
        ))

        logger.warning(
            f"{veto_type.value} veto issued by {initiated_by} "
            f"on '{target_action}': {reason}"
        )
        return record

    def approve_veto(self, veto_id: str, approver: str) -> bool:
        """Approve a pending veto (policy/operational vetoes need approval)."""
        for record in self._veto_records:
            if record.veto_id == veto_id and not record.approved:
                record.approved = True
                record.resolved_at = datetime.utcnow().isoformat()
                self._audit_log.append(GovernmentAuditEntry(
                    entry_id=str(uuid.uuid4()),
                    action=GovernmentAction.APPROVE_POLICY,
                    initiated_by=approver,
                    target=record.target_action,
                    details=f"Veto {veto_id} approved",
                ))
                return True
        return False

    def declare_emergency(
        self, initiated_by: str, reason: str
    ) -> bool:
        """Declare a government-layer emergency.

        During emergency, the Kill Switch can be activated
        and certain operations may be restricted.
        """
        self._emergency_active = True
        self._audit_log.append(GovernmentAuditEntry(
            entry_id=str(uuid.uuid4()),
            action=GovernmentAction.EMERGENCY_DECLARE,
            initiated_by=initiated_by,
            target="system",
            details=f"Emergency declared: {reason}",
        ))
        logger.critical(f"GOVERNMENT EMERGENCY declared by {initiated_by}: {reason}")
        return True

    def resolve_emergency(self, initiated_by: str) -> bool:
        """Resolve a government-layer emergency."""
        self._emergency_active = False
        self._audit_log.append(GovernmentAuditEntry(
            entry_id=str(uuid.uuid4()),
            action=GovernmentAction.OVERRIDE,
            initiated_by=initiated_by,
            target="system",
            details="Emergency resolved",
        ))
        return True

    def propose_constitutional_amendment(
        self, proposed_by: str, principle: str, new_text: str, reason: str
    ) -> Dict[str, Any]:
        """Propose a constitutional amendment.

        Amendments require supermajority approval and are logged
        as immutable audit entries.
        """
        amendment = {
            "amendment_id": str(uuid.uuid4()),
            "proposed_by": proposed_by,
            "principle": principle,
            "new_text": new_text,
            "reason": reason,
            "status": "proposed",
            "proposed_at": datetime.utcnow().isoformat(),
        }
        self._constitutional_amendments.append(amendment)
        self._audit_log.append(GovernmentAuditEntry(
            entry_id=str(uuid.uuid4()),
            action=GovernmentAction.CONSTITUTIONAL_AMENDMENT,
            initiated_by=proposed_by,
            target=f"constitution:{principle}",
            details=f"Amendment proposed: {reason}",
        ))
        return amendment

    def get_veto_history(self) -> List[VetoRecord]:
        """Get all veto records."""
        return self._veto_records

    def get_audit_log(
        self, limit: int = 100
    ) -> List[GovernmentAuditEntry]:
        """Get government-layer audit log."""
        return self._audit_log[:limit]

    def is_emergency_active(self) -> bool:
        """Check if a government emergency is active."""
        return self._emergency_active

    def get_stats(self) -> Dict[str, Any]:
        """Get government layer statistics."""
        return {
            "total_vetoes": len(self._veto_records),
            "approved_vetoes": sum(1 for v in self._veto_records if v.approved),
            "pending_vetoes": sum(1 for v in self._veto_records if not v.approved),
            "veto_types": {
                t.value: sum(1 for v in self._veto_records if v.veto_type == t)
                for t in VetoType
            },
            "total_audit_entries": len(self._audit_log),
            "emergency_active": self._emergency_active,
            "constitutional_amendments": len(self._constitutional_amendments),
        }
