"""
Router Routes
=============
Endpoints for AI router: chat routing, metrics, and route management.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Router"])

logger = logging.getLogger("AsimNexus.Routes.Router")

router_manager = None


def init_router(app_globals: dict) -> None:
    global router_manager
    router_manager = app_globals.get("router_manager")


@router.post("/api/router/chat")
async def router_chat(data: dict = Body(...)):
    """Route a chat message to the appropriate AI model."""
    try:
        if router_manager:
            result = await router_manager.route_chat(data)
            return ok(data=result)
        return ok(data={"response": "Routed via default model", "model": "default"})
    except Exception as e:
        logger.error(f"router_chat error: {e}")
        return error(str(e))


@router.get("/api/router/metrics")
async def router_metrics():
    """Get router performance metrics."""
    try:
        if router_manager:
            data = await router_manager.get_metrics()
            return ok(data=data)
        return ok(data={
            "total_routes": 0,
            "avg_latency_ms": 0,
            "models": {},
            "uptime": "0s",
        })
    except Exception as e:
        logger.error(f"router_metrics error: {e}")
        return error(str(e))


@router.post("/api/router/route")
async def router_route(data: dict = Body(...)):
    """Route a request to the appropriate service."""
    try:
        if router_manager:
            result = await router_manager.route_request(data)
            return ok(data=result)
        return ok(data={"status": "routed", "target": data.get("target", "default")})
    except Exception as e:
        logger.error(f"router_route error: {e}")
        return error(str(e))
