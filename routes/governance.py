"""
Governance Routes
=================
Endpoints for the 51% Government Layer — balance monitoring, policy approval,
veto management, constitutional compliance, and audit trails.

These routes expose the PowerBalanceConstitution and GovernmentLayer
to the frontend Government Dashboard.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Query
from pydantic import BaseModel

from routes.response import ok, error, unavailable

router = APIRouter(tags=["Governance"])

logger = logging.getLogger("AsimNexus.Routes.Governance")

# Module-level globals set by app.py at startup
orchestrator = None


def init_governance(app_globals: dict) -> None:
    """Initialize governance module from app.py globals."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ── Pydantic Models ───────────────────────────────────────────────────


class PolicyApprovalRequest(BaseModel):
    policy_id: str = ""
    title: str = ""
    description: str = ""
    sector: str = "general"
    proposed_by: str = "government"
    is_public_decision: bool = True


class VetoRequest(BaseModel):
    target_action: str = ""
    reason: str = ""
    veto_type: str = "policy"  # constitutional, policy, operational, emergency
    initiated_by: str = "government"


class VetoApprovalRequest(BaseModel):
    veto_id: str = ""
    approver: str = "government"


class EmergencyRequest(BaseModel):
    reason: str = ""
    initiated_by: str = "government"


class AmendmentRequest(BaseModel):
    proposed_by: str = ""
    principle: str = ""
    new_text: str = ""
    reason: str = ""


# ── Helper: get governance components ─────────────────────────────────


def _get_power_balance():
    """Get the PowerBalanceConstitution singleton."""
    try:
        from core.security.power_balance_constitution import get_power_balance
        return get_power_balance()
    except Exception as e:
        logger.warning(f"PowerBalanceConstitution unavailable: {e}")
        return None


def _get_government_layer():
    """Get the GovernmentLayer singleton."""
    try:
        from core.governance.government_layer import get_government_layer
        return get_government_layer()
    except Exception as e:
        logger.warning(f"GovernmentLayer unavailable: {e}")
        return None


def _get_dharma_engine():
    """Get the DharmaVetoEngine singleton."""
    try:
        from core.dharma_chakra.veto_engine import get_veto_engine
        return get_veto_engine()
    except Exception as e:
        logger.warning(f"DharmaVetoEngine unavailable: {e}")
        return None


# ── Balance Endpoints ─────────────────────────────────────────────────


@router.get("/api/governance/balance")
async def governance_balance():
    """Get current 51/49 power balance across all sectors."""
    try:
        pb = _get_power_balance()
        if pb:
            stats = pb.get_stats()
            sectors = {}
            for sector_name in [
                "healthcare", "education", "finance", "infrastructure",
                "defense", "justice", "agriculture", "energy",
                "transportation", "communication", "governance",
            ]:
                info = pb.get_sector_info(sector_name)
                if info:
                    sectors[sector_name] = info
            return ok(data={
                "overall": stats,
                "sectors": sectors,
            })
        return ok(data={
            "overall": {
                "total_decisions": 0,
                "public_decisions": 0,
                "private_decisions": 0,
                "public_share": 0.51,
                "private_share": 0.49,
                "total_amendments": 0,
                "total_audit_entries": 0,
            },
            "sectors": {},
            "note": "PowerBalanceConstitution not loaded — showing defaults",
        })
    except Exception as e:
        logger.error(f"governance_balance error: {e}")
        return error(str(e))


@router.get("/api/governance/balance/{sector}")
async def governance_sector_balance(sector: str):
    """Get power balance for a specific sector."""
    try:
        pb = _get_power_balance()
        if pb:
            info = pb.get_sector_info(sector)
            if info:
                return ok(data=info)
            return ok(data={"sector": sector, "error": f"Unknown sector: {sector}"})
        return unavailable("PowerBalanceConstitution")
    except Exception as e:
        logger.error(f"governance_sector_balance error: {e}")
        return error(str(e))


# ── Policy Endpoints ──────────────────────────────────────────────────


@router.get("/api/governance/policies")
async def governance_policies():
    """List all government policies and their approval status."""
    try:
        gl = _get_government_layer()
        if gl:
            veto_history = gl.get_veto_history()
            audit_log = gl.get_audit_log()
            policies = []
            for entry in audit_log:
                policies.append({
                    "id": entry.entry_id,
                    "action": entry.action.value if hasattr(entry.action, 'value') else str(entry.action),
                    "initiated_by": entry.initiated_by,
                    "target": entry.target,
                    "details": entry.details,
                    "timestamp": entry.timestamp,
                })
            return ok(data={
                "policies": policies,
                "veto_history": [
                    {
                        "veto_id": v.veto_id,
                        "veto_type": v.veto_type.value if hasattr(v.veto_type, 'value') else str(v.veto_type),
                        "initiated_by": v.initiated_by,
                        "target_action": v.target_action,
                        "reason": v.reason,
                        "approved": v.approved,
                        "created_at": v.created_at,
                        "resolved_at": v.resolved_at,
                    }
                    for v in veto_history
                ],
            })
        return ok(data={"policies": [], "veto_history": []})
    except Exception as e:
        logger.error(f"governance_policies error: {e}")
        return error(str(e))


@router.post("/api/governance/policy/approve")
async def governance_policy_approve(req: PolicyApprovalRequest):
    """Approve a government policy after constitutional compliance check."""
    try:
        gl = _get_government_layer()
        pb = _get_power_balance()

        if not gl:
            return unavailable("GovernmentLayer")

        # Step 1: Check constitutional compliance
        is_compliant, violation = gl.check_constitutional_compliance(
            req.title, req.sector
        )
        if not is_compliant:
            return ok(data={
                "approved": False,
                "status": "blocked",
                "reason": f"Constitutional violation: {violation}",
            })

        # Step 2: Check power balance
        if pb:
            balance_result = pb.check_decision(
                sector=req.sector,
                is_public_decision=req.is_public_decision,
                weight=1.0,
                context={"policy": req.title, "description": req.description},
            )
            if balance_result.verdict.value == "BLOCK":
                return ok(data={
                    "approved": False,
                    "status": "blocked",
                    "reason": balance_result.message,
                    "balance": balance_result.to_dict(),
                })

        # Step 3: Log the approval
        from core.governance.government_layer import GovernmentAction
        from datetime import datetime
        gl._audit_log.append(type('AuditEntry', (), {
            'entry_id': str(__import__('uuid').uuid4()),
            'action': GovernmentAction.APPROVE_POLICY,
            'initiated_by': req.proposed_by,
            'target': req.title,
            'details': f"Policy approved for sector '{req.sector}': {req.description}",
            'timestamp': datetime.utcnow().isoformat(),
        })())

        return ok(data={
            "approved": True,
            "status": "approved",
            "policy_id": req.policy_id or str(__import__('uuid').uuid4()),
            "sector": req.sector,
            "message": f"Policy '{req.title}' approved with 51% public authority",
        })
    except Exception as e:
        logger.error(f"governance_policy_approve error: {e}")
        return error(str(e))


# ── Veto Endpoints ────────────────────────────────────────────────────


@router.post("/api/governance/veto")
async def governance_veto(req: VetoRequest):
    """Issue a government veto on an action."""
    try:
        gl = _get_government_layer()
        if not gl:
            return unavailable("GovernmentLayer")

        from core.governance.government_layer import VetoType
        veto_type_map = {
            "constitutional": VetoType.CONSTITUTIONAL,
            "policy": VetoType.POLICY,
            "operational": VetoType.OPERATIONAL,
            "emergency": VetoType.EMERGENCY,
        }
        vt = veto_type_map.get(req.veto_type.lower(), VetoType.POLICY)

        record = gl.issue_veto(
            veto_type=vt,
            initiated_by=req.initiated_by,
            target_action=req.target_action,
            reason=req.reason,
        )

        return ok(data={
            "veto_id": record.veto_id,
            "veto_type": record.veto_type.value if hasattr(record.veto_type, 'value') else str(record.veto_type),
            "approved": record.approved,
            "target_action": record.target_action,
            "reason": record.reason,
            "created_at": record.created_at,
            "message": "Veto issued" if record.approved else "Veto pending approval",
        })
    except Exception as e:
        logger.error(f"governance_veto error: {e}")
        return error(str(e))


@router.post("/api/governance/veto/approve")
async def governance_veto_approve(req: VetoApprovalRequest):
    """Approve a pending veto."""
    try:
        gl = _get_government_layer()
        if not gl:
            return unavailable("GovernmentLayer")

        success = gl.approve_veto(req.veto_id, req.approver)
        return ok(data={
            "approved": success,
            "veto_id": req.veto_id,
            "message": "Veto approved" if success else "Veto not found or already approved",
        })
    except Exception as e:
        logger.error(f"governance_veto_approve error: {e}")
        return error(str(e))


# ── Emergency Endpoints ───────────────────────────────────────────────


@router.post("/api/governance/emergency/declare")
async def governance_emergency_declare(req: EmergencyRequest):
    """Declare a government emergency (activates Kill Switch capabilities)."""
    try:
        gl = _get_government_layer()
        if not gl:
            return unavailable("GovernmentLayer")

        gl.declare_emergency(req.initiated_by, req.reason)
        return ok(data={
            "emergency_active": True,
            "reason": req.reason,
            "message": "Government emergency declared — enhanced oversight active",
        })
    except Exception as e:
        logger.error(f"governance_emergency_declare error: {e}")
        return error(str(e))


@router.post("/api/governance/emergency/resolve")
async def governance_emergency_resolve(req: EmergencyRequest):
    """Resolve a government emergency."""
    try:
        gl = _get_government_layer()
        if not gl:
            return unavailable("GovernmentLayer")

        gl.resolve_emergency(req.initiated_by)
        return ok(data={
            "emergency_active": False,
            "message": "Government emergency resolved — normal operations restored",
        })
    except Exception as e:
        logger.error(f"governance_emergency_resolve error: {e}")
        return error(str(e))


# ── Audit Endpoints ───────────────────────────────────────────────────


@router.get("/api/governance/audit")
async def governance_audit(limit: int = Query(100, ge=1, le=1000)):
    """Get government-layer audit log."""
    try:
        gl = _get_government_layer()
        if gl:
            audit_log = gl.get_audit_log(limit)
            return ok(data={
                "entries": [
                    {
                        "entry_id": e.entry_id,
                        "action": e.action.value if hasattr(e.action, 'value') else str(e.action),
                        "initiated_by": e.initiated_by,
                        "target": e.target,
                        "details": e.details,
                        "timestamp": e.timestamp,
                    }
                    for e in audit_log
                ],
                "total": len(audit_log),
            })
        return ok(data={"entries": [], "total": 0})
    except Exception as e:
        logger.error(f"governance_audit error: {e}")
        return error(str(e))


@router.get("/api/governance/stats")
async def governance_stats():
    """Get comprehensive governance statistics."""
    try:
        gl = _get_government_layer()
        pb = _get_power_balance()
        dv = _get_dharma_engine()

        result: Dict[str, Any] = {}

        if gl:
            result["government"] = gl.get_stats()
        else:
            result["government"] = {
                "total_vetoes": 0, "approved_vetoes": 0,
                "pending_vetoes": 0, "emergency_active": False,
            }

        if pb:
            result["power_balance"] = pb.get_stats()
        else:
            result["power_balance"] = {
                "total_decisions": 0, "public_share": 0.51, "private_share": 0.49,
            }

        if dv:
            result["dharma"] = dv.get_stats()
        else:
            result["dharma"] = {
                "total_checked": 0, "passed": 0, "blocked": 0, "warned": 0,
            }

        return ok(data=result)
    except Exception as e:
        logger.error(f"governance_stats error: {e}")
        return error(str(e))


# ── Constitutional Amendment Endpoints ────────────────────────────────


@router.post("/api/governance/amendment/propose")
async def governance_amendment_propose(req: AmendmentRequest):
    """Propose a constitutional amendment (requires supermajority)."""
    try:
        gl = _get_government_layer()
        if not gl:
            return unavailable("GovernmentLayer")

        amendment = gl.propose_constitutional_amendment(
            proposed_by=req.proposed_by,
            principle=req.principle,
            new_text=req.new_text,
            reason=req.reason,
        )
        return ok(data={
            "amendment": amendment,
            "message": "Constitutional amendment proposed — requires supermajority approval",
        })
    except Exception as e:
        logger.error(f"governance_amendment_propose error: {e}")
        return error(str(e))


# ── Dharma Check Endpoints ────────────────────────────────────────────


@router.post("/api/governance/dharma/check")
async def governance_dharma_check(data: dict = Body(...)):
    """Check an action against the Dharma Veto Engine."""
    try:
        dv = _get_dharma_engine()
        if not dv:
            return unavailable("DharmaVetoEngine")

        message = data.get("action", data.get("message", ""))
        agent_id = data.get("agent_id", "government")
        context = data.get("context", {})

        result = dv.check(message=message, agent_id=agent_id, context=context)
        return ok(data=result.to_dict())
    except Exception as e:
        logger.error(f"governance_dharma_check error: {e}")
        return error(str(e))
