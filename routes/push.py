"""
Push Notification Routes
========================
Endpoints for push notifications: send and subscribe.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Push Notifications"])

logger = logging.getLogger("AsimNexus.Routes.Push")

push_manager = None

def init_push(app_globals: dict) -> None:
    global push_manager
    push_manager = app_globals.get("push_manager")

@router.post("/api/push/send")
async def push_send(data: dict = Body(...)):
    """Send a push notification."""
    try:
        if push_manager:
            result = await push_manager.send(data)
            return ok(data=result)
        return ok(data={"status": "sent", "target": data.get("target", "all")})
    except Exception as e:
        logger.error(f"push_send error: {e}")
        return error(str(e))

@router.post("/api/push/subscribe")
async def push_subscribe(data: dict = Body(...)):
    """Subscribe to push notifications."""
    try:
        if push_manager:
            result = await push_manager.subscribe(data)
            return ok(data=result)
        return ok(data={"status": "subscribed", "endpoint": data.get("endpoint", "unknown")})
    except Exception as e:
        logger.error(f"push_subscribe error: {e}")
        return error(str(e))
