"""
Consensus Routes
================
Endpoints for consensus V1/V2, dharma, governance, evolution.
"""

import logging
from fastapi import APIRouter, Body
from pydantic import BaseModel

from routes.response import ok, error, unavailable

router = APIRouter(tags=["Consensus"])

logger = logging.getLogger("AsimNexus.Routes.Consensus")

# Module-level globals set by app.py at startup
orchestrator = None
consensus_engine = None
dharma_engine = None
evolution_engine = None
governance_engine = None


def init_consensus(app_globals: dict) -> None:
    """Initialize consensus module from app.py globals."""
    global orchestrator, consensus_engine, dharma_engine, evolution_engine, governance_engine
    orchestrator = app_globals.get("orchestrator")
    consensus_engine = app_globals.get("consensus_engine")
    dharma_engine = app_globals.get("dharma_engine")
    evolution_engine = app_globals.get("evolution_engine")
    governance_engine = app_globals.get("governance_engine")


# ── Pydantic Models ───────────────────────────────────────────────────

class VoteRequest(BaseModel):
    topic: str = ""
    description: str = ""
    level: str = "standard"


class OverrideRequest(BaseModel):
    reason: str = ""
    override: bool = False


# ── Consensus V1 ──────────────────────────────────────────────────────

@router.post("/api/consensus/vote")
async def trigger_consensus_vote(req: VoteRequest):
    """Trigger a consensus vote."""
    try:
        if orchestrator and hasattr(orchestrator, "consensus"):
            result = await orchestrator.consensus.vote(req.topic, req.description, req.level)
            return ok(data=result)
        return unavailable("consensus")
    except Exception as e:
        logger.error(f"trigger_consensus_vote error: {e}")
        return error(str(e))


@router.post("/api/consensus/{round_id}/override")
async def consensus_override(round_id: str, req: OverrideRequest):
    """Override a consensus round."""
    try:
        if orchestrator and hasattr(orchestrator, "consensus"):
            result = await orchestrator.consensus.override(round_id, req.reason, req.override)
            return ok(data=result)
        return unavailable("consensus")
    except Exception as e:
        logger.error(f"consensus_override error: {e}")
        return error(str(e))


@router.get("/api/consensus/stats")
async def consensus_stats():
    """Get consensus statistics."""
    try:
        if consensus_engine:
            return ok(data=await consensus_engine.get_stats())
        return ok(data={"rounds": 0, "active": 0, "completed": 0})
    except Exception as e:
        logger.error(f"consensus_stats error: {e}")
        return error(str(e))


@router.get("/api/consensus/list")
async def consensus_list():
    """List consensus rounds."""
    try:
        if consensus_engine:
            return ok(data=await consensus_engine.list_rounds())
        return ok(data={"rounds": [], "count": 0})
    except Exception as e:
        logger.error(f"consensus_list error: {e}")
        return error(str(e))


@router.get("/api/consensus/pending")
async def consensus_pending():
    """Get pending consensus items."""
    try:
        if consensus_engine:
            return ok(data=await consensus_engine.get_pending())
        return ok(data={"pending": [], "count": 0})
    except Exception as e:
        logger.error(f"consensus_pending error: {e}")
        return error(str(e))


# ── Consensus V2 ──────────────────────────────────────────────────────

@router.post("/api/v1/consensus/vote")
async def consensus_v2_vote(data: dict = Body(...)):
    """Cast a consensus vote (V2)."""
    try:
        if consensus_engine:
            return ok(data=await consensus_engine.vote_v2(
                data.get("proposal_id", ""),
                data.get("voter", ""),
                data.get("vote", "abstain"),
                data.get("weight", 1.0)
            ))
        return unavailable("consensus_engine")
    except Exception as e:
        logger.error(f"consensus_v2_vote error: {e}")
        return error(str(e))


@router.post("/api/v1/consensus/weighted-vote")
async def consensus_v2_weighted_vote(data: dict = Body(...)):
    """Cast a weighted consensus vote (V2)."""
    try:
        if consensus_engine:
            return ok(data=await consensus_engine.weighted_vote(
                data.get("proposal_id", ""),
                data.get("voter", ""),
                data.get("vote", "abstain"),
                data.get("weight", 1.0),
                data.get("reasoning", "")
            ))
        return unavailable("consensus_engine")
    except Exception as e:
        logger.error(f"consensus_v2_weighted_vote error: {e}")
        return error(str(e))


@router.get("/api/v1/consensus/status")
async def consensus_v2_status():
    """Get consensus V2 status."""
    try:
        if consensus_engine:
            return ok(data=await consensus_engine.get_status_v2())
        return ok(data={"status": "inactive"})
    except Exception as e:
        logger.error(f"consensus_v2_status error: {e}")
        return error(str(e))


# ── Dharma ────────────────────────────────────────────────────────────

@router.get("/api/dharma/status")
async def dharma_status():
    """Dharma engine status."""
    try:
        if dharma_engine:
            return ok(data=await dharma_engine.get_status())
        return ok(data={"status": "active"})
    except Exception as e:
        logger.error(f"dharma_status error: {e}")
        return error(str(e))


@router.post("/api/dharma/veto")
async def dharma_veto(data: dict = Body(...)):
    """Check an action against Dharma Veto Engine."""
    try:
        if dharma_engine:
            return ok(data=await dharma_engine.check_veto(
                data.get("action", ""),
                data.get("context", {})
            ))
        return ok(data={"vetoed": False}, note="dharma_engine unavailable")
    except Exception as e:
        logger.error(f"dharma_veto error: {e}")
        return error(str(e))


@router.post("/api/dharma/veto-check")
async def dharma_veto_check(data: dict = Body(...)):
    """Check action against Dharma veto rules."""
    try:
        action = data.get("action", "")
        context = data.get("context", {})
        if dharma_engine:
            return ok(data=await dharma_engine.check_veto(action, context))
        # Fallback: try core.dharma_chakra
        try:
            from core.dharma_chakra.veto_engine import VetoEngine
            ve = VetoEngine()
            return ok(data=await ve.evaluate(action, context))
        except Exception:
            return ok(data={"vetoed": False, "confidence": 0.0, "reason": "dharma unavailable"})
    except Exception as e:
        logger.error(f"dharma_veto_check error: {e}")
        return error(str(e))


@router.post("/api/dharma/cultural-check")
async def dharma_cultural_check(data: dict = Body(...)):
    """Check action against cultural compliance."""
    try:
        action = data.get("action", "accept_protocol")
        context = data.get("context", {})
        if dharma_engine:
            return ok(data=await dharma_engine.cultural_check(action, context))
        return ok(data={"compliant": True}, note="dharma_engine unavailable")
    except Exception as e:
        logger.error(f"dharma_cultural_check error: {e}")
        return error(str(e))


@router.get("/api/dharma/veto-status")
async def dharma_veto_status():
    """Get Dharma veto status."""
    try:
        if dharma_engine:
            return ok(data=await dharma_engine.get_veto_status())
        # Fallback
        try:
            from core.dharma_chakra.veto_engine import get_veto_engine
            ve = get_veto_engine()
            return ok(data=await ve.get_status())
        except Exception:
            return ok(data={"status": "inactive"})
    except Exception as e:
        logger.error(f"dharma_veto_status error: {e}")
        return error(str(e))


@router.get("/api/dharma/production/status")
async def dharma_production_status():
    """Get ΔT production engine status."""
    try:
        if dharma_engine:
            return ok(data=await dharma_engine.get_production_status())
        return ok(data={"status": "inactive"})
    except Exception as e:
        logger.error(f"dharma_production_status error: {e}")
        return error(str(e))


# ── Evolution ─────────────────────────────────────────────────────────

@router.get("/api/evolution/stats")
async def evolution_stats():
    """Evolution engine statistics."""
    try:
        if evolution_engine:
            return ok(data=await evolution_engine.get_stats())
        return ok(data={"patches": 0, "active": 0})
    except Exception as e:
        logger.error(f"evolution_stats error: {e}")
        return error(str(e))


@router.post("/api/evolution/propose")
async def evolution_propose(data: dict = Body(...)):
    """Propose an evolution patch."""
    try:
        if evolution_engine:
            return ok(data=await evolution_engine.propose(
                data.get("title", ""),
                data.get("description", ""),
                data.get("changes", {}),
                data.get("author", "")
            ))
        return unavailable("evolution_engine")
    except Exception as e:
        logger.error(f"evolution_propose error: {e}")
        return error(str(e))


@router.post("/api/evolution/{patch_id}/validate")
async def evolution_validate(patch_id: str):
    """Validate an evolution patch."""
    try:
        if evolution_engine:
            return ok(data=await evolution_engine.validate(patch_id))
        return unavailable("evolution_engine")
    except Exception as e:
        logger.error(f"evolution_validate error: {e}")
        return error(str(e))


@router.post("/api/evolution/{patch_id}/decide")
async def evolution_decide(patch_id: str, data: dict = Body(...)):
    """Decide on an evolution patch."""
    try:
        if evolution_engine:
            return ok(data=await evolution_engine.decide(
                patch_id,
                data.get("decision", "pending"),
                data.get("reason", "")
            ))
        return unavailable("evolution_engine")
    except Exception as e:
        logger.error(f"evolution_decide error: {e}")
        return error(str(e))


# ── DePIN ─────────────────────────────────────────────────────────────



@router.post("/api/depin/{node_id}/collect")
async def depin_collect(node_id: str):
    """Collect rewards from a DePIN node."""
    try:
        if orchestrator:
            return ok(data=await orchestrator.depin.collect(node_id))
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"depin_collect error: {e}")
        return error(str(e))


# ── Post-Quantum ──────────────────────────────────────────────────────

@router.get("/api/pq/status")
async def pq_status():
    """Post-quantum cryptography status."""
    try:
        if orchestrator:
            return ok(data=await orchestrator.pq.get_status())
        return ok(data={"status": "inactive"})
    except Exception as e:
        logger.error(f"pq_status error: {e}")
        return error(str(e))


@router.post("/api/pq/keygen")
async def pq_keygen(data: dict = Body(...)):
    """Generate post-quantum keys."""
    try:
        if orchestrator:
            return ok(data=await orchestrator.pq.keygen(data.get("algorithm", "dilithium"), data.get("identity", "")))
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"pq_keygen error: {e}")
        return error(str(e))


@router.post("/api/pq/sign")
async def pq_sign(data: dict = Body(...)):
    """Sign with post-quantum key."""
    try:
        if orchestrator:
            return ok(data=await orchestrator.pq.sign(data.get("message", ""), data.get("key_id", "")))
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"pq_sign error: {e}")
        return error(str(e))


@router.post("/api/pq/kem")
async def pq_kem(data: dict = Body(...)):
    """Post-quantum KEM operation."""
    try:
        if orchestrator:
            return ok(data=await orchestrator.pq.kem(data.get("operation", ""), data.get("params", {})))
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"pq_kem error: {e}")
        return error(str(e))
