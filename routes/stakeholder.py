"""
Stakeholder Coordinator API Routes

Provides REST API endpoints for multi-stakeholder coordination between
government (51%), enterprise (49%), and users (100%).

Endpoints:
  - GET  /api/stakeholder/status        — Coordinator system status
  - POST /api/stakeholder/action         — Propose a new multi-stakeholder action
  - POST /api/stakeholder/action/{id}/approve — Approve/reject an action
  - GET  /api/stakeholder/action/{id}    — Get action details
  - GET  /api/stakeholder/actions        — List actions (filtered)
  - GET  /api/stakeholder/consensus      — Get consensus decision log
  - GET  /api/stakeholder/stats          — Coordinator statistics
"""

import logging
from typing import Optional

from fastapi import APIRouter, Body
from pydantic import BaseModel

from core.governance.stakeholder_coordinator import (
    ActionCategory,
    CoordinationStatus,
    Stakeholder,
    get_coordinator,
)
from routes.response import error, ok, unavailable

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level globals
_coordinator = None


def init_stakeholder(app_globals: dict) -> None:
    """Initialize stakeholder coordinator singleton."""
    global _coordinator
    try:
        from core.governance.stakeholder_coordinator import get_coordinator
        _coordinator = get_coordinator()

        # Try to initialize with governance layers if available
        try:
            from core.governance.government_layer import get_government_layer
            from core.governance.enterprise_layer import get_enterprise_layer
            from core.security.power_balance_constitution import get_power_balance
            from core.dharma_chakra.veto_engine import get_veto_engine

            _coordinator.initialize(
                government_layer=get_government_layer(),
                enterprise_layer=get_enterprise_layer(),
                power_balance=get_power_balance(),
                dharma_engine=get_veto_engine(),
            )
            logger.info("Stakeholder coordinator initialized with all governance layers")
        except Exception as e:
            logger.warning(f"Could not initialize governance layers: {e}")

        logger.info("Stakeholder coordinator initialized")
    except Exception as e:
        logger.error(f"Failed to init stakeholder coordinator: {e}")


def _get_coordinator():
    """Get the coordinator singleton."""
    global _coordinator
    if _coordinator is None:
        _coordinator = get_coordinator()
    return _coordinator


# ═══════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════

class ProposeActionRequest(BaseModel):
    category: str  # ActionCategory value
    initiated_by: str  # Stakeholder value
    description: str
    details: dict = {}


class ApproveActionRequest(BaseModel):
    stakeholder: str  # Stakeholder value
    approved: bool = True
    reason: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════════

@router.get("/api/stakeholder/status")
async def stakeholder_status():
    """Get stakeholder coordinator system status."""
    try:
        coord = _get_coordinator()
        return ok(data={
            "initialized": coord is not None,
            "total_actions": len(coord._actions) if coord else 0,
            "total_consensus": len(coord._consensus_log) if coord else 0,
        })
    except Exception as e:
        logger.error(f"stakeholder_status error: {e}")
        return error(str(e))


@router.post("/api/stakeholder/action")
async def propose_action(req: ProposeActionRequest):
    """Propose a new multi-stakeholder action."""
    try:
        coord = _get_coordinator()

        # Validate category
        try:
            category = ActionCategory(req.category)
        except ValueError:
            return error(f"Invalid category: {req.category}. Valid: {[c.value for c in ActionCategory]}")

        # Validate stakeholder
        try:
            stakeholder = Stakeholder(req.initiated_by)
        except ValueError:
            return error(f"Invalid stakeholder: {req.initiated_by}. Valid: {[s.value for s in Stakeholder]}")

        action = coord.propose_action(
            category=category,
            initiated_by=stakeholder,
            description=req.description,
            details=req.details,
        )
        return ok(data=action.to_dict())
    except Exception as e:
        logger.error(f"propose_action error: {e}")
        return error(str(e))


@router.post("/api/stakeholder/action/{action_id}/approve")
async def approve_action(action_id: str, req: ApproveActionRequest):
    """Approve or reject a multi-stakeholder action."""
    try:
        coord = _get_coordinator()

        try:
            stakeholder = Stakeholder(req.stakeholder)
        except ValueError:
            return error(f"Invalid stakeholder: {req.stakeholder}")

        consensus = coord.approve_action(
            action_id=action_id,
            stakeholder=stakeholder,
            approved=req.approved,
            reason=req.reason,
        )
        return ok(data=consensus.to_dict())
    except ValueError as e:
        return error(str(e))
    except Exception as e:
        logger.error(f"approve_action error: {e}")
        return error(str(e))


@router.get("/api/stakeholder/action/{action_id}")
async def get_action(action_id: str):
    """Get details of a specific action."""
    try:
        coord = _get_coordinator()
        action = coord.get_action(action_id)
        if not action:
            return error(f"Action not found: {action_id}")
        return ok(data=action.to_dict())
    except Exception as e:
        logger.error(f"get_action error: {e}")
        return error(str(e))


@router.get("/api/stakeholder/actions")
async def list_actions(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
):
    """List stakeholder actions, optionally filtered."""
    try:
        coord = _get_coordinator()

        status_enum = None
        if status:
            try:
                status_enum = CoordinationStatus(status)
            except ValueError:
                return error(f"Invalid status: {status}")

        category_enum = None
        if category:
            try:
                category_enum = ActionCategory(category)
            except ValueError:
                return error(f"Invalid category: {category}")

        actions = coord.list_actions(
            status=status_enum,
            category=category_enum,
            limit=limit,
        )
        return ok(data={
            "actions": [a.to_dict() for a in actions],
            "total": len(actions),
        })
    except Exception as e:
        logger.error(f"list_actions error: {e}")
        return error(str(e))


@router.get("/api/stakeholder/consensus")
async def get_consensus_log(
    limit: int = 100,
    approved_only: Optional[bool] = None,
):
    """Get the consensus decision log."""
    try:
        coord = _get_coordinator()
        log = coord.get_consensus_log(
            limit=limit,
            approved_only=approved_only,
        )
        return ok(data={
            "consensus_log": [c.to_dict() for c in log],
            "total": len(log),
        })
    except Exception as e:
        logger.error(f"get_consensus_log error: {e}")
        return error(str(e))


@router.get("/api/stakeholder/stats")
async def stakeholder_stats():
    """Get comprehensive stakeholder coordinator statistics."""
    try:
        coord = _get_coordinator()
        return ok(data=coord.get_stats())
    except Exception as e:
        logger.error(f"stakeholder_stats error: {e}")
        return error(str(e))
