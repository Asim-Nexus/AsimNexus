#!/usr/bin/env python3
"""
Stakeholder Coordinator — User × Government × Company Integration Layer

Coordinates interactions between the three stakeholder groups in the
AsimNexus Digital Nepal governance model:

  - Government (51%): Sovereign oversight, veto power, constitutional enforcement
  - Enterprise (49%): Commercial licensing, compliance, private sector operations
  - User (100%): Individual sovereignty, agent contracts, mode selection

This module provides a unified interface for multi-stakeholder actions,
ensuring that all decisions respect the power balance constitution and
that each stakeholder's rights and responsibilities are properly enforced.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Enums & Constants
# ═══════════════════════════════════════════════════════════════════

class Stakeholder(Enum):
    """The three stakeholder groups in the governance model."""
    GOVERNMENT = "government"       # 51% public control
    ENTERPRISE = "enterprise"       # 49% private control
    USER = "user"                   # 100% individual sovereignty


class ActionCategory(Enum):
    """Categories of actions that require multi-stakeholder coordination."""
    POLICY = "policy"               # Government policy decisions
    LICENSE = "license"             # Enterprise licensing
    CONTRACT = "contract"           # Agent contract creation
    MODE_CHANGE = "mode_change"     # Agent mode activation/deactivation
    EMERGENCY = "emergency"         # Emergency declarations
    AMENDMENT = "amendment"         # Constitutional amendments
    COMPLIANCE = "compliance"       # Compliance checks
    AUDIT = "audit"                 # Audit trail access


class CoordinationStatus(Enum):
    """Status of a multi-stakeholder coordination action."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"
    ESCALATED = "escalated"
    COMPLETED = "completed"


# ═══════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════

@dataclass
class StakeholderAction:
    """A single action that requires multi-stakeholder coordination."""
    action_id: str
    category: ActionCategory
    initiated_by: Stakeholder
    description: str
    details: Dict[str, Any]
    status: CoordinationStatus = CoordinationStatus.PENDING
    required_approvals: List[Stakeholder] = field(default_factory=list)
    approvals: Dict[str, bool] = field(default_factory=dict)  # stakeholder -> approved
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: Optional[str] = None
    vetoed_by: Optional[str] = None
    veto_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "category": self.category.value,
            "initiated_by": self.initiated_by.value,
            "description": self.description,
            "details": self.details,
            "status": self.status.value,
            "required_approvals": [s.value for s in self.required_approvals],
            "approvals": self.approvals,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "vetoed_by": self.vetoed_by,
            "veto_reason": self.veto_reason,
        }


@dataclass
class StakeholderConsensus:
    """Result of a multi-stakeholder consensus check."""
    action_id: str
    approved: bool
    government_approval: Optional[bool] = None
    enterprise_approval: Optional[bool] = None
    user_approval: Optional[bool] = None
    details: str = ""
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "approved": self.approved,
            "government_approval": self.government_approval,
            "enterprise_approval": self.enterprise_approval,
            "user_approval": self.user_approval,
            "details": self.details,
            "requires_escalation": self.requires_escalation,
            "escalation_reason": self.escalation_reason,
        }


# ═══════════════════════════════════════════════════════════════════
# Stakeholder Coordinator
# ═══════════════════════════════════════════════════════════════════

class StakeholderCoordinator:
    """Coordinates multi-stakeholder actions across government, enterprise, and users.

    The coordinator ensures that:
    1. Government (51%) has veto power over constitutional and policy matters
    2. Enterprise (49%) has autonomy over commercial operations within bounds
    3. Users (100%) have individual sovereignty over their agents and data
    4. All actions respect the power balance constitution
    5. Disputes are escalated through the proper channels
    """

    # Actions that require government approval (51% control)
    GOVERNMENT_REQUIRED_CATEGORIES = {
        ActionCategory.POLICY,
        ActionCategory.EMERGENCY,
        ActionCategory.AMENDMENT,
    }

    # Actions that require enterprise approval (49% control)
    ENTERPRISE_REQUIRED_CATEGORIES = {
        ActionCategory.LICENSE,
        ActionCategory.COMPLIANCE,
    }

    # Actions that require user approval (100% sovereignty)
    USER_REQUIRED_CATEGORIES = {
        ActionCategory.CONTRACT,
        ActionCategory.MODE_CHANGE,
    }

    def __init__(self):
        self._actions: Dict[str, StakeholderAction] = {}
        self._consensus_log: List[StakeholderConsensus] = []
        self._government_layer = None
        self._enterprise_layer = None
        self._power_balance = None
        self._dharma_engine = None

    def initialize(
        self,
        government_layer: Any,
        enterprise_layer: Any,
        power_balance: Any,
        dharma_engine: Any,
    ) -> None:
        """Initialize with references to governance components."""
        self._government_layer = government_layer
        self._enterprise_layer = enterprise_layer
        self._power_balance = power_balance
        self._dharma_engine = dharma_engine
        logger.info("StakeholderCoordinator initialized with all governance layers")

    def propose_action(
        self,
        category: ActionCategory,
        initiated_by: Stakeholder,
        description: str,
        details: Dict[str, Any],
    ) -> StakeholderAction:
        """Propose a new multi-stakeholder action."""
        action_id = str(uuid.uuid4())

        # Determine required approvals based on category
        required: List[Stakeholder] = [initiated_by]

        if category in self.GOVERNMENT_REQUIRED_CATEGORIES:
            if Stakeholder.GOVERNMENT not in required:
                required.append(Stakeholder.GOVERNMENT)

        if category in self.ENTERPRISE_REQUIRED_CATEGORIES:
            if Stakeholder.ENTERPRISE not in required:
                required.append(Stakeholder.ENTERPRISE)

        if category in self.USER_REQUIRED_CATEGORIES:
            if Stakeholder.USER not in required:
                required.append(Stakeholder.USER)

        # Policy and amendment always need both government and enterprise
        if category in (ActionCategory.POLICY, ActionCategory.AMENDMENT):
            if Stakeholder.GOVERNMENT not in required:
                required.append(Stakeholder.GOVERNMENT)
            if Stakeholder.ENTERPRISE not in required:
                required.append(Stakeholder.ENTERPRISE)

        action = StakeholderAction(
            action_id=action_id,
            category=category,
            initiated_by=initiated_by,
            description=description,
            details=details,
            required_approvals=required,
        )

        self._actions[action_id] = action
        logger.info(
            f"Action proposed: {action_id} ({category.value}) by {initiated_by.value}"
        )
        return action

    def approve_action(
        self,
        action_id: str,
        stakeholder: Stakeholder,
        approved: bool,
        reason: Optional[str] = None,
    ) -> StakeholderConsensus:
        """Approve or reject an action from a stakeholder's perspective."""
        action = self._actions.get(action_id)
        if not action:
            raise ValueError(f"Action not found: {action_id}")

        if stakeholder not in action.required_approvals:
            raise ValueError(
                f"{stakeholder.value} approval not required for this action"
            )

        # Record the approval
        action.approvals[stakeholder.value] = approved

        # Check if we have consensus
        return self._check_consensus(action)

    def _check_consensus(self, action: StakeholderAction) -> StakeholderConsensus:
        """Check if all required stakeholders have approved."""
        all_approved = all(
            action.approvals.get(s.value, False) for s in action.required_approvals
        )

        # Check for vetoes
        government_veto = False
        dharma_veto = None

        if (
            Stakeholder.GOVERNMENT in action.required_approvals
            and action.approvals.get(Stakeholder.GOVERNMENT.value) is False
        ):
            government_veto = True

        # Check Dharma Veto Engine for critical actions
        if self._dharma_engine and action.category in (
            ActionCategory.POLICY,
            ActionCategory.AMENDMENT,
            ActionCategory.EMERGENCY,
        ):
            try:
                dharma_result = self._dharma_engine.check(
                    action=action.description,
                    agent_id=f"stakeholder_coordinator_{action.action_id[:8]}",
                    context=action.details,
                )
                dharma_veto = dharma_result
                if dharma_result.level.value in ("block", "require_human"):
                    all_approved = False
                    action.vetoed_by = "dharma_engine"
                    action.veto_reason = dharma_result.reason
            except Exception as e:
                logger.warning(f"Dharma check failed: {e}")

        # Check power balance for policy/amendment actions
        power_balance_ok = True
        if self._power_balance and action.category in (
            ActionCategory.POLICY,
            ActionCategory.AMENDMENT,
        ):
            sector = action.details.get("sector", "general")
            try:
                balance_result = self._power_balance.check_decision(
                    sector=sector,
                    decision=action.description,
                    initiated_by=action.initiated_by.value,
                )
                power_balance_ok = balance_result.allowed
                if not balance_result.allowed:
                    all_approved = False
                    action.vetoed_by = "power_balance"
                    action.veto_reason = balance_result.reason
            except Exception as e:
                logger.warning(f"Power balance check failed: {e}")

        # Determine final status
        if all_approved and power_balance_ok and (not dharma_veto or dharma_veto.allowed):
            action.status = CoordinationStatus.APPROVED
        elif government_veto:
            action.status = CoordinationStatus.REJECTED
        else:
            action.status = CoordinationStatus.REQUIRES_REVIEW

        action.resolved_at = datetime.utcnow().isoformat()

        consensus = StakeholderConsensus(
            action_id=action.action_id,
            approved=action.status == CoordinationStatus.APPROVED,
            government_approval=action.approvals.get(Stakeholder.GOVERNMENT.value),
            enterprise_approval=action.approvals.get(Stakeholder.ENTERPRISE.value),
            user_approval=action.approvals.get(Stakeholder.USER.value),
            details=f"Consensus: {action.status.value}",
            requires_escalation=action.status == CoordinationStatus.REQUIRES_REVIEW,
            escalation_reason=action.veto_reason if action.status == CoordinationStatus.REQUIRES_REVIEW else None,
        )

        self._consensus_log.append(consensus)
        logger.info(
            f"Consensus for {action.action_id}: {consensus.approved} "
            f"(gov={consensus.government_approval}, "
            f"ent={consensus.enterprise_approval}, "
            f"user={consensus.user_approval})"
        )
        return consensus

    def get_action(self, action_id: str) -> Optional[StakeholderAction]:
        """Get a specific action by ID."""
        return self._actions.get(action_id)

    def list_actions(
        self,
        status: Optional[CoordinationStatus] = None,
        category: Optional[ActionCategory] = None,
        limit: int = 50,
    ) -> List[StakeholderAction]:
        """List actions, optionally filtered by status and/or category."""
        results = list(self._actions.values())
        if status:
            results = [a for a in results if a.status == status]
        if category:
            results = [a for a in results if a.category == category]
        results.sort(key=lambda a: a.created_at, reverse=True)
        return results[:limit]

    def get_consensus_log(
        self,
        limit: int = 100,
        approved_only: Optional[bool] = None,
    ) -> List[StakeholderConsensus]:
        """Get the consensus decision log."""
        results = list(self._consensus_log)
        if approved_only is not None:
            results = [c for c in results if c.approved == approved_only]
        results.sort(key=lambda c: c.action_id, reverse=True)
        return results[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive coordinator statistics."""
        total = len(self._actions)
        approved = sum(1 for a in self._actions.values() if a.status == CoordinationStatus.APPROVED)
        rejected = sum(1 for a in self._actions.values() if a.status == CoordinationStatus.REJECTED)
        pending = sum(1 for a in self._actions.values() if a.status == CoordinationStatus.PENDING)
        review = sum(1 for a in self._actions.values() if a.status == CoordinationStatus.REQUIRES_REVIEW)

        category_breakdown: Dict[str, int] = {}
        for a in self._actions.values():
            cat = a.category.value
            category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

        stakeholder_breakdown: Dict[str, int] = {}
        for a in self._actions.values():
            init = a.initiated_by.value
            stakeholder_breakdown[init] = stakeholder_breakdown.get(init, 0) + 1

        return {
            "total_actions": total,
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "requires_review": review,
            "category_breakdown": category_breakdown,
            "stakeholder_breakdown": stakeholder_breakdown,
            "total_consensus_decisions": len(self._consensus_log),
        }


# ═══════════════════════════════════════════════════════════════════
# Singleton Access
# ═══════════════════════════════════════════════════════════════════

_coordinator: Optional[StakeholderCoordinator] = None


def get_coordinator() -> StakeholderCoordinator:
    """Get the singleton StakeholderCoordinator instance."""
    global _coordinator
    if _coordinator is None:
        _coordinator = StakeholderCoordinator()
    return _coordinator


def reset_coordinator() -> None:
    """Reset the singleton (for testing)."""
    global _coordinator
    _coordinator = None
