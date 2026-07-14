"""
Identity Routes
===============
Endpoints for identity management: SVT, HDT, blockchain, credentials.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Identity"])

logger = logging.getLogger("AsimNexus.Routes.Identity")

# Module-level globals set by app.py at startup
orchestrator = None
identity_manager = None
svt_manager = None
hdt_manager = None


def init_identity(app_globals: dict) -> None:
    """Initialize identity module from app.py globals."""
    global orchestrator, identity_manager, svt_manager, hdt_manager
    orchestrator = app_globals.get("orchestrator")
    identity_manager = app_globals.get("identity_manager")
    svt_manager = app_globals.get("svt_manager")
    hdt_manager = app_globals.get("hdt_manager")


# ── Identity ──────────────────────────────────────────────────────────

@router.get("/api/identity/stats")
async def identity_stats():
    """Identity system statistics."""
    try:
        if identity_manager:
            data = await identity_manager.get_stats()
            return ok(data=data)
        return ok(data={"identities": 0, "active": 0})
    except Exception as e:
        logger.error(f"identity_stats error: {e}")
        return error(str(e))


@router.get("/api/identity/list")
async def identity_list():
    """List all identities."""
    try:
        if identity_manager:
            data = await identity_manager.list_identities()
            return ok(data=data)
        return ok(data={"identities": [], "count": 0})
    except Exception as e:
        logger.error(f"identity_list error: {e}")
        return error(str(e))


@router.post("/api/identity/create")
async def identity_create(data: dict = Body(...)):
    """Create a new identity."""
    try:
        if identity_manager:
            result = await identity_manager.create_identity(
                data.get("did", ""),
                data.get("public_key", ""),
                data.get("metadata", {})
            )
            return ok(data=result)
        return unavailable("identity_manager")
    except Exception as e:
        logger.error(f"identity_create error: {e}")
        return error(str(e))


@router.post("/api/identity/verify")
async def identity_verify(data: dict = Body(...)):
    """Verify an identity."""
    try:
        if identity_manager:
            result = await identity_manager.verify_identity(
                data.get("did", ""),
                data.get("challenge", ""),
                data.get("signature", "")
            )
            return ok(data=result)
        return ok(data={"verified": False}, note="identity_manager unavailable")
    except Exception as e:
        logger.error(f"identity_verify error: {e}")
        return error(str(e))


@router.post("/api/identity/{did}/credential")
async def identity_issue_vc(did: str, data: dict = Body(...)):
    """Issue a verifiable credential to an identity."""
    try:
        if identity_manager:
            result = await identity_manager.issue_credential(
                did,
                data.get("type", ""),
                data.get("claims", {})
            )
            return ok(data=result)
        return unavailable("identity_manager")
    except Exception as e:
        logger.error(f"identity_issue_vc error: {e}")
        return error(str(e))


@router.get("/api/identity/{did}/credentials")
async def identity_get_vcs(did: str):
    """Get verifiable credentials for an identity."""
    try:
        if identity_manager:
            data = await identity_manager.get_credentials(did)
            return ok(data=data)
        return ok(data={"credentials": [], "count": 0})
    except Exception as e:
        logger.error(f"identity_get_vcs error: {e}")
        return error(str(e))


@router.get("/api/identity/status")
async def identity_status():
    """Identity system status."""
    try:
        if identity_manager:
            data = await identity_manager.get_system_status()
            return ok(data=data)
        return ok(data={"status": "active"})
    except Exception as e:
        logger.error(f"identity_status error: {e}")
        return error(str(e))


# ── SVT (Soulbound Value Token) ──────────────────────────────────────

@router.get("/api/svt/stats")
async def svt_stats():
    """SVT (Soulbound Value Token) statistics."""
    try:
        if svt_manager:
            data = await svt_manager.get_stats()
            return ok(data=data)
        return ok(data={"total_supply": 0, "holders": 0})
    except Exception as e:
        logger.error(f"svt_stats error: {e}")
        return error(str(e))


@router.get("/api/svt/wallet")
async def svt_wallet():
    """Get SVT wallet info."""
    try:
        if svt_manager:
            data = await svt_manager.get_wallet()
            return ok(data=data)
        return ok(data={"balance": 0, "tokens": []})
    except Exception as e:
        logger.error(f"svt_wallet error: {e}")
        return error(str(e))


@router.post("/api/svt/wallet")
async def svt_create_wallet(data: dict = Body(...)):
    """Create a new SVT wallet for a DID (frontend compatibility)."""
    try:
        did = data.get("did", "")
        if svt_manager:
            result = await svt_manager.create_wallet(did)
            return ok(data=result)
        return ok(data={"did": did, "balance": 0, "tokens": [], "status": "created"})
    except Exception as e:
        logger.error(f"svt_create_wallet error: {e}")
        return error(str(e))


@router.post("/api/svt/mint")
async def svt_mint(data: dict = Body(...)):
    """Mint new SVT tokens."""
    try:
        if svt_manager:
            result = await svt_manager.mint(
                data.get("to", ""),
                data.get("amount", 0),
                data.get("reason", "")
            )
            return ok(data=result)
        return unavailable("svt_manager")
    except Exception as e:
        logger.error(f"svt_mint error: {e}")
        return error(str(e))


@router.get("/api/svt/wallet/{did}")
async def svt_wallet_did(did: str):
    """Get SVT wallet for a specific DID."""
    try:
        if svt_manager:
            data = await svt_manager.get_wallet_for_did(did)
            return ok(data=data)
        return ok(data={"did": did, "balance": 0, "tokens": []})
    except Exception as e:
        logger.error(f"svt_wallet_did error: {e}")
        return error(str(e))


@router.post("/api/svt/transfer")
async def svt_transfer(data: dict = Body(...)):
    """Transfer SVT tokens."""
    try:
        if svt_manager:
            result = await svt_manager.transfer(
                data.get("from", ""),
                data.get("to", ""),
                data.get("amount", 0)
            )
            return ok(data=result)
        return unavailable("svt_manager")
    except Exception as e:
        logger.error(f"svt_transfer error: {e}")
        return error(str(e))


@router.post("/api/svt/escrow")
async def svt_escrow(data: dict = Body(...)):
    """Create an SVT escrow."""
    try:
        if svt_manager:
            result = await svt_manager.create_escrow(
                data.get("from", ""),
                data.get("to", ""),
                data.get("amount", 0),
                data.get("condition", "")
            )
            return ok(data=result)
        return unavailable("svt_manager")
    except Exception as e:
        logger.error(f"svt_escrow error: {e}")
        return error(str(e))


@router.post("/api/svt/escrow/{eid}/release")
async def svt_escrow_release(eid: str, data: dict = Body(...)):
    """Release an SVT escrow."""
    try:
        if svt_manager:
            result = await svt_manager.release_escrow(eid, data.get("approved", False))
            return ok(data=result)
        return unavailable("svt_manager")
    except Exception as e:
        logger.error(f"svt_escrow_release error: {e}")
        return error(str(e))


# ── HDT (Human Digital Twin) ──────────────────────────────────────────

@router.post("/api/hdt/create")
async def hdt_create(data: dict = Body(...)):
    """Create a new HDT (Human Digital Twin)."""
    try:
        if hdt_manager:
            result = await hdt_manager.create_hdt(
                data.get("did", ""),
                data.get("profile", {}),
                data.get("capabilities", [])
            )
            return ok(data=result)
        return unavailable("hdt_manager")
    except Exception as e:
        logger.error(f"hdt_create error: {e}")
        return error(str(e))


@router.get("/api/hdt/{did}/status")
async def hdt_status(did: str):
    """Get HDT status."""
    try:
        if hdt_manager:
            data = await hdt_manager.get_status(did)
            return ok(data=data)
        return ok(data={"did": did, "status": "unknown"})
    except Exception as e:
        logger.error(f"hdt_status error: {e}")
        return error(str(e))


@router.post("/api/hdt/{did}/skill")
async def hdt_add_skill(did: str, data: dict = Body(...)):
    """Add a skill to HDT."""
    try:
        if hdt_manager:
            result = await hdt_manager.add_skill(did, data.get("skill", ""), data.get("level", 0))
            return ok(data=result)
        return unavailable("hdt_manager")
    except Exception as e:
        logger.error(f"hdt_add_skill error: {e}")
        return error(str(e))


@router.post("/api/hdt/{did}/announce")
async def hdt_announce(did: str, data: dict = Body(...)):
    """Announce HDT capability."""
    try:
        if hdt_manager:
            result = await hdt_manager.announce(did, data.get("capability", ""))
            return ok(data=result)
        return unavailable("hdt_manager")
    except Exception as e:
        logger.error(f"hdt_announce error: {e}")
        return error(str(e))


@router.get("/api/hdt/{did}/profile")
async def hdt_profile(did: str):
    """Get HDT profile."""
    try:
        if hdt_manager:
            data = await hdt_manager.get_profile(did)
            return ok(data=data)
        return ok(data={"did": did, "profile": {}})
    except Exception as e:
        logger.error(f"hdt_profile error: {e}")
        return error(str(e))


@router.get("/api/hdt/status")
async def hdt_status_global():
    """Global HDT status."""
    try:
        if hdt_manager:
            data = await hdt_manager.get_global_status()
            return ok(data=data)
        return ok(data={"status": "active", "twins": 0})
    except Exception as e:
        logger.error(f"hdt_status_global error: {e}")
        return error(str(e))


# ── Quadrants ─────────────────────────────────────────────────────────

@router.get("/api/quad/status")
async def quad_status():
    """Quadrant system status."""
    try:
        if orchestrator:
            data = await orchestrator.quad.get_status()
            return ok(data=data)
        return ok(data={"status": "active"})
    except Exception as e:
        logger.error(f"quad_status error: {e}")
        return error(str(e))


@router.post("/api/quad/join")
async def quad_join(data: dict = Body(...)):
    """Join a quadrant."""
    try:
        if orchestrator:
            result = await orchestrator.quad.join(
                data.get("did", ""),
                data.get("layer", ""),
                data.get("capabilities", [])
            )
            return ok(data=result)
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"quad_join error: {e}")
        return error(str(e))


@router.get("/api/quad/{layer}/peers")
async def quad_peers(layer: str):
    """Get peers in a quadrant layer."""
    try:
        if orchestrator:
            data = await orchestrator.quad.get_peers(layer)
            return ok(data=data)
        return ok(data={"peers": [], "count": 0})
    except Exception as e:
        logger.error(f"quad_peers error: {e}")
        return error(str(e))


@router.post("/api/quad/send")
async def quad_send(data: dict = Body(...)):
    """Send message within quadrant."""
    try:
        if orchestrator:
            result = await orchestrator.quad.send(
                data.get("from", ""),
                data.get("to", ""),
                data.get("message", ""),
                data.get("layer", "")
            )
            return ok(data=result)
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"quad_send error: {e}")
        return error(str(e))


# ── Firewall ──────────────────────────────────────────────────────────

@router.post("/api/firewall/check")
async def firewall_check(data: dict = Body(...)):
    """Check text against firewall."""
    try:
        if orchestrator:
            result = await orchestrator.firewall.check(data.get("text", ""))
            return ok(data=result)
        return ok(data={"allowed": True}, note="orchestrator unavailable")
    except Exception as e:
        logger.error(f"firewall_check error: {e}")
        return error(str(e))


@router.post("/api/firewall/check-conversation")
async def firewall_check_conversation(data: dict = Body(...)):
    """Check conversation against firewall."""
    try:
        if orchestrator:
            result = await orchestrator.firewall.check_conversation(data.get("messages", []))
            return ok(data=result)
        return ok(data={"allowed": True}, note="orchestrator unavailable")
    except Exception as e:
        logger.error(f"firewall_check_conversation error: {e}")
        return error(str(e))


@router.get("/api/firewall/status")
async def firewall_status():
    """Firewall status."""
    try:
        if orchestrator:
            data = await orchestrator.firewall.get_status()
            return ok(data=data)
        return ok(data={"status": "active"})
    except Exception as e:
        logger.error(f"firewall_status error: {e}")
        return error(str(e))


# ── Events ────────────────────────────────────────────────────────────

@router.get("/api/events/stats")
async def events_stats():
    """Event system statistics."""
    try:
        if orchestrator:
            data = await orchestrator.events.get_stats()
            return ok(data=data)
        return ok(data={"total": 0, "recent": 0})
    except Exception as e:
        logger.error(f"events_stats error: {e}")
        return error(str(e))


@router.post("/api/events/publish")
async def events_publish(data: dict = Body(...)):
    """Publish an event."""
    try:
        if orchestrator:
            result = await orchestrator.events.publish(
                data.get("type", ""),
                data.get("payload", {})
            )
            return ok(data=result)
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"events_publish error: {e}")
        return error(str(e))


@router.get("/api/events/recent")
async def events_recent():
    """Get recent events."""
    try:
        if orchestrator:
            data = await orchestrator.events.get_recent()
            return ok(data=data)
        return ok(data={"events": [], "count": 0})
    except Exception as e:
        logger.error(f"events_recent error: {e}")
        return error(str(e))


@router.get("/api/events/dlq")
async def events_dlq():
    """Get dead letter queue."""
    try:
        if orchestrator:
            data = await orchestrator.events.get_dlq()
            return ok(data=data)
        return ok(data={"dlq": [], "count": 0})
    except Exception as e:
        logger.error(f"events_dlq error: {e}")
        return error(str(e))
