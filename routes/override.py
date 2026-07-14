"""
Override Engine Routes
======================
Endpoints for override management: approve, reject, escalate, pending.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Override"])

logger = logging.getLogger("AsimNexus.Routes.Override")

override_manager = None


def init_override(app_globals: dict) -> None:
    global override_manager
    override_manager = app_globals.get("override_manager")


@router.post("/api/override/approve")
async def override_approve(data: dict = Body(...)):
    """Approve an override request."""
    try:
        if override_manager:
            result = await override_manager.approve(data)
            return ok(data=result)
        return ok(data={"status": "approved", "override_id": data.get("override_id", "mock")})
    except Exception as e:
        logger.error(f"override_approve error: {e}")
        return error(str(e))


@router.post("/api/override/reject")
async def override_reject(data: dict = Body(...)):
    """Reject an override request."""
    try:
        if override_manager:
            result = await override_manager.reject(data)
            return ok(data=result)
        return ok(data={"status": "rejected", "override_id": data.get("override_id", "mock")})
    except Exception as e:
        logger.error(f"override_reject error: {e}")
        return error(str(e))


@router.post("/api/override/escalate")
async def override_escalate(data: dict = Body(...)):
    """Escalate an override request."""
    try:
        if override_manager:
            result = await override_manager.escalate(data)
            return ok(data=result)
        return ok(data={"status": "escalated", "override_id": data.get("override_id", "mock")})
    except Exception as e:
        logger.error(f"override_escalate error: {e}")
        return error(str(e))


@router.get("/api/override/pending")
async def override_pending(user_id: str = ""):
    """List pending override requests."""
    try:
        if override_manager:
            data = await override_manager.list_pending(user_id=user_id)
            return ok(data=data)
        return ok(data={"overrides": [], "count": 0})
    except Exception as e:
        logger.error(f"override_pending error: {e}")
        return error(str(e))
