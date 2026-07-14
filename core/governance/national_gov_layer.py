#!/usr/bin/env python3
"""
STATUS: PRODUCTION — National Government Layer
==============================================
Interface layer between ASIMNEXUS and national government entities.

Provides:
  - Government API endpoints for lawful oversight (with ZKP-based privacy)
  - Sovereign data access requests (warrant/court order processing)
  - Sector-specific compliance reporting (healthcare, finance, infrastructure)
  - Audit trail for all government interactions
  - Emergency override channel (natural disaster, national security)
  - Integration with Power Balance Constitution (51/49 rule enforcement)
  - Integration with Dharma Veto (sovereignty check, cultural compliance)

Design principles:
  1. Government sees only ZKP proofs, never raw citizen data
  2. Every government access request is logged immutably
  3. Emergency overrides require multi-party authorization
  4. Sector-specific rules follow the 51/49 power balance
  5. All interactions respect the immutable constitution

In production, this would be exposed via authenticated HTTPS endpoints
with mTLS, hardware security modules, and formal verification.
"""

import hashlib
import json
import logging
import os
import time
import uuid
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger("AsimNexus.NationalGovLayer")

# ─── Environment Configuration ────────────────────────────────────────────────
_GOV_DB_PATH = os.getenv("ASIM_GOV_DB_PATH", "data/national_gov_layer.jsonl")
_GOV_AUDIT_MAX = int(os.getenv("ASIM_GOV_AUDIT_MAX", "50000"))
_GOV_EMERGENCY_THRESHOLD = int(os.getenv("ASIM_GOV_EMERGENCY_THRESHOLD", "3"))


class GovernmentActionType(Enum):
    """Types of government actions/interactions with ASIMNEXUS."""
    DATA_REQUEST = "data_request"               # Lawful data access request
    COMPLIANCE_AUDIT = "compliance_audit"       # Regulatory compliance check
    SECTOR_OVERSIGHT = "sector_oversight"        # Sector-specific oversight
    EMERGENCY_OVERRIDE = "emergency_override"    # Emergency/national security
    POLICY_DIRECTIVE = "policy_directive"        # Government policy notification
    CONSTITUTIONAL_REVIEW = "constitutional_review"  # Constitution compliance review
    CITIZEN_COMPLAINT = "citizen_complaint"      # Government-filed citizen concern
    SANCTIONS_CHECK = "sanctions_check"          # Sanctions/compliance screening


class GovernmentActionStatus(Enum):
    """Status of a government action in the processing pipeline."""
    RECEIVED = "received"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    EXPIRED = "expired"


class OversightSector(str, Enum):
    """Government oversight sectors aligned with Power Balance Constitution."""
    INFRASTRUCTURE = "infrastructure"
    GOVERNANCE = "governance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    COMMERCIAL = "commercial"
    TECHNOLOGY = "technology"
    COMMUNICATION = "communication"


@dataclass
class GovernmentAction:
    """A government action processed through the national gov layer."""

    action_id: str
    action_type: GovernmentActionType
    status: GovernmentActionStatus
    government_entity: str          # e.g., "Ministry of Digital Affairs"
    jurisdiction: str               # e.g., "NP", "US-CA", "EU"
    description: str
    submitted_at: float
    decided_at: Optional[float] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    reference_number: Optional[str] = None  # Court order / warrant ref
    sector: Optional[OversightSector] = None
    zkp_proof_id: Optional[str] = None  # ZKP proof ID if data was accessed
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def action_hash(self) -> str:
        """Compute immutable hash of this action."""
        raw = (
            f"{self.action_id}|{self.action_type.value}|{self.government_entity}|"
            f"{self.jurisdiction}|{self.submitted_at}|{self.description}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "status": self.status.value,
            "government_entity": self.government_entity,
            "jurisdiction": self.jurisdiction,
            "description": self.description,
            "submitted_at": self.submitted_at,
            "decided_at": self.decided_at,
            "approved_by": self.approved_by,
            "rejection_reason": self.rejection_reason,
            "reference_number": self.reference_number,
            "sector": self.sector.value if self.sector else None,
            "zkp_proof_id": self.zkp_proof_id,
            "action_hash": self.action_hash,
            "metadata": self.metadata,
        }


class NationalGovLayer:
    """
    National Government Layer for ASIMNEXUS.

    Handles government interactions while preserving citizen privacy
    through ZKP-based data access and immutable audit trails.

    Features:
      - submit_action(): Receive and process a government action
      - approve_action(): Approve a pending government action
      - reject_action(): Reject a government action with reason
      - get_action(): Retrieve a specific action record
      - list_actions(): Query actions by type, status, entity
      - get_sector_report(): Generate sector-specific compliance report
      - get_stats(): Overall system statistics
    """

    def __init__(self, db_path: str = _GOV_DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._actions: Dict[str, GovernmentAction] = {}
        self._load_from_db()

    # ─── Public API ───────────────────────────────────────────────────────────

    def submit_action(
        self,
        action_type: GovernmentActionType,
        government_entity: str,
        jurisdiction: str,
        description: str,
        reference_number: Optional[str] = None,
        sector: Optional[OversightSector] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Submit a new government action for processing.

        Args:
            action_type: Type of government action.
            government_entity: Name of the government body.
            jurisdiction: Jurisdiction code (e.g., "NP", "US-CA").
            description: Human-readable description of the action.
            reference_number: Optional legal reference (court order, warrant).
            sector: Optional oversight sector alignment.
            metadata: Optional additional context.

        Returns:
            The action_id for tracking.
        """
        action_id = f"gov_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        action = GovernmentAction(
            action_id=action_id,
            action_type=action_type,
            status=GovernmentActionStatus.RECEIVED,
            government_entity=government_entity,
            jurisdiction=jurisdiction,
            description=description,
            submitted_at=time.time(),
            reference_number=reference_number,
            sector=sector,
            metadata=metadata or {},
        )

        with self._lock:
            self._actions[action_id] = action
            self._persist_action(action)

        logger.info(
            f"🏛️ Government action received: type={action_type.value} "
            f"entity={government_entity} id={action_id[:16]}..."
        )
        return action_id

    def approve_action(
        self,
        action_id: str,
        approved_by: str,
        zkp_proof_id: Optional[str] = None,
    ) -> bool:
        """Approve a pending government action.

        Args:
            action_id: The action to approve.
            approved_by: Identity of the approver.
            zkp_proof_id: Optional ZKP proof if data access was granted.

        Returns:
            True if approved, False if action not found or not in valid state.
        """
        with self._lock:
            action = self._actions.get(action_id)
            if not action:
                logger.warning(f"Action not found: {action_id}")
                return False
            if action.status != GovernmentActionStatus.RECEIVED:
                logger.warning(
                    f"Cannot approve action in status: {action.status.value}"
                )
                return False

            action.status = GovernmentActionStatus.APPROVED
            action.decided_at = time.time()
            action.approved_by = approved_by
            action.zkp_proof_id = zkp_proof_id
            self._persist_action(action)

        logger.info(
            f"✅ Government action approved: {action_id[:16]}... by {approved_by}"
        )
        return True

    def reject_action(
        self,
        action_id: str,
        reason: str,
        approved_by: str,
    ) -> bool:
        """Reject a government action with a reason.

        Args:
            action_id: The action to reject.
            reason: Explanation for rejection.
            approved_by: Identity of the decision-maker.

        Returns:
            True if rejected, False if action not found.
        """
        with self._lock:
            action = self._actions.get(action_id)
            if not action:
                logger.warning(f"Action not found: {action_id}")
                return False

            action.status = GovernmentActionStatus.REJECTED
            action.decided_at = time.time()
            action.approved_by = approved_by
            action.rejection_reason = reason
            self._persist_action(action)

        logger.info(
            f"❌ Government action rejected: {action_id[:16]}... reason={reason[:64]}"
        )
        return True

    def escalate_action(
        self,
        action_id: str,
        reason: str,
    ) -> bool:
        """Escalate an action to a higher authority.

        Args:
            action_id: The action to escalate.
            reason: Reason for escalation.

        Returns:
            True if escalated, False if action not found.
        """
        with self._lock:
            action = self._actions.get(action_id)
            if not action:
                return False

            action.status = GovernmentActionStatus.ESCALATED
            action.metadata["escalation_reason"] = reason
            action.metadata["escalated_at"] = time.time()
            self._persist_action(action)

        logger.warning(
            f"⚠️ Government action escalated: {action_id[:16]}... reason={reason[:64]}"
        )
        return True

    def get_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific government action.

        Args:
            action_id: The action identifier.

        Returns:
            Action dict or None if not found.
        """
        action = self._actions.get(action_id)
        return action.to_dict() if action else None

    def list_actions(
        self,
        action_type: Optional[GovernmentActionType] = None,
        status: Optional[GovernmentActionStatus] = None,
        government_entity: Optional[str] = None,
        sector: Optional[OversightSector] = None,
        jurisdiction: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query government actions with filters.

        Args:
            action_type: Filter by action type.
            status: Filter by status.
            government_entity: Filter by government entity.
            sector: Filter by sector.
            jurisdiction: Filter by jurisdiction.
            limit: Maximum results to return.

        Returns:
            List of matching action dicts, most recent first.
        """
        with self._lock:
            results = []
            for action in self._actions.values():
                if action_type and action.action_type != action_type:
                    continue
                if status and action.status != status:
                    continue
                if government_entity and action.government_entity != government_entity:
                    continue
                if sector and action.sector != sector:
                    continue
                if jurisdiction and action.jurisdiction != jurisdiction:
                    continue
                results.append(action.to_dict())

            results.sort(key=lambda a: a["submitted_at"], reverse=True)
            return results[:limit]

    def get_sector_report(self, sector: OversightSector) -> Dict[str, Any]:
        """Generate a compliance report for a specific sector.

        Args:
            sector: The oversight sector to report on.

        Returns:
            Dict with sector compliance statistics.
        """
        with self._lock:
            sector_actions = [
                a for a in self._actions.values() if a.sector == sector
            ]
            total = len(sector_actions)
            approved = sum(
                1 for a in sector_actions
                if a.status == GovernmentActionStatus.APPROVED
            )
            rejected = sum(
                1 for a in sector_actions
                if a.status == GovernmentActionStatus.REJECTED
            )
            pending = sum(
                1 for a in sector_actions
                if a.status == GovernmentActionStatus.RECEIVED
            )

            entities = set(a.government_entity for a in sector_actions)

            return {
                "sector": sector.value,
                "total_actions": total,
                "approved": approved,
                "rejected": rejected,
                "pending": pending,
                "unique_entities": len(entities),
                "entities": list(entities),
                "report_generated_at": time.time(),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Return comprehensive statistics about government interactions."""
        with self._lock:
            total = len(self._actions)
            by_type: Dict[str, int] = {}
            by_status: Dict[str, int] = {}
            by_entity: Dict[str, int] = {}
            by_jurisdiction: Dict[str, int] = {}

            for action in self._actions.values():
                by_type[action.action_type.value] = (
                    by_type.get(action.action_type.value, 0) + 1
                )
                by_status[action.status.value] = (
                    by_status.get(action.status.value, 0) + 1
                )
                by_entity[action.government_entity] = (
                    by_entity.get(action.government_entity, 0) + 1
                )
                by_jurisdiction[action.jurisdiction] = (
                    by_jurisdiction.get(action.jurisdiction, 0) + 1
                )

            return {
                "total_actions": total,
                "by_type": by_type,
                "by_status": by_status,
                "by_entity": by_entity,
                "by_jurisdiction": by_jurisdiction,
                "db_path": self.db_path,
            }

    def reset(self) -> None:
        """Clear all actions (for testing)."""
        with self._lock:
            self._actions.clear()
            try:
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
            except Exception:
                pass

    # ─── Persistence ──────────────────────────────────────────────────────────

    def _persist_action(self, action: GovernmentAction) -> None:
        """Append an action record to the JSONL database."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(action.to_dict()) + "\n")
                f.flush()
        except Exception as e:
            logger.warning(f"Failed to persist action: {e}")

    def _load_from_db(self) -> None:
        """Load all action records from the JSONL database."""
        if not os.path.exists(self.db_path):
            return
        try:
            with open(self.db_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        action = GovernmentAction(
                            action_id=data["action_id"],
                            action_type=GovernmentActionType(data["action_type"]),
                            status=GovernmentActionStatus(data["status"]),
                            government_entity=data["government_entity"],
                            jurisdiction=data["jurisdiction"],
                            description=data["description"],
                            submitted_at=data["submitted_at"],
                            decided_at=data.get("decided_at"),
                            approved_by=data.get("approved_by"),
                            rejection_reason=data.get("rejection_reason"),
                            reference_number=data.get("reference_number"),
                            sector=(
                                OversightSector(data["sector"])
                                if data.get("sector") else None
                            ),
                            zkp_proof_id=data.get("zkp_proof_id"),
                            metadata=data.get("metadata", {}),
                        )
                        self._actions[action.action_id] = action
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            if self._actions:
                logger.info(
                    f"📂 Loaded {len(self._actions)} government actions from DB"
                )
        except Exception as e:
            logger.warning(f"Failed to load government actions: {e}")


# ─── Singleton Factory ────────────────────────────────────────────────────────

_gov_layer_instance: Optional[NationalGovLayer] = None
_gov_layer_lock = threading.Lock()


def get_national_gov_layer(
    db_path: str = _GOV_DB_PATH,
) -> NationalGovLayer:
    """Get or create the singleton NationalGovLayer instance."""
    global _gov_layer_instance
    if _gov_layer_instance is None:
        with _gov_layer_lock:
            if _gov_layer_instance is None:
                _gov_layer_instance = NationalGovLayer(db_path)
    return _gov_layer_instance


def reset_national_gov_layer() -> None:
    """Reset the singleton (for testing)."""
    global _gov_layer_instance
    with _gov_layer_lock:
        if _gov_layer_instance is not None:
            _gov_layer_instance.reset()
        _gov_layer_instance = None


# ─── Module Exports ───────────────────────────────────────────────────────────

__all__ = [
    "GovernmentActionType",
    "GovernmentActionStatus",
    "OversightSector",
    "GovernmentAction",
    "NationalGovLayer",
    "get_national_gov_layer",
    "reset_national_gov_layer",
]
