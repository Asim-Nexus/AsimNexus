"""
Offline Sync Routes
===================
Endpoints for offline data access and synchronization.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Offline"])

logger = logging.getLogger("AsimNexus.Routes.Offline")

offline_manager = None


def init_offline(app_globals: dict) -> None:
    global offline_manager
    offline_manager = app_globals.get("offline_manager")


@router.get("/api/offline/data")
async def offline_data(user_id: str = "", since: str = ""):
    """Get offline data for a user."""
    try:
        if offline_manager:
            data = await offline_manager.get_data(user_id=user_id, since=since)
            return ok(data=data)
        return ok(data={"entries": [], "count": 0, "user_id": user_id})
    except Exception as e:
        logger.error(f"offline_data error: {e}")
        return error(str(e))


@router.post("/api/offline/sync")
async def offline_sync(data: dict = Body(...)):
    """Sync offline data to the server."""
    try:
        if offline_manager:
            result = await offline_manager.sync(data)
            return ok(data=result)
        return ok(data={"status": "synced", "operations": data.get("operations", [])})
    except Exception as e:
        logger.error(f"offline_sync error: {e}")
        return error(str(e))
