
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Unified Server
========================
Minimal FastAPI-based server to expose MVP mode and routing status.
"""

import logging
from typing import Dict, Any

from fastapi import FastAPI, HTTPException

from core.context_router import get_context_router
from core.event_bus import event_bus, EventType

logger = logging.getLogger("UnifiedServer")
app = FastAPI(title="ASIMNEXUS Unified Server")

try:
    from core.rate_limiter_middleware import RateLimiterMiddleware
    app.add_middleware(RateLimiterMiddleware)
    logger.info("✅ RateLimiterMiddleware registered")
except Exception:
    pass

context_router = get_context_router()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "asim_unified_server"}


@app.get("/mode")
def get_mode() -> Dict[str, Any]:
    return context_router.get_mode()


@app.post("/mode/{mode_name}")
def set_mode(mode_name: str) -> Dict[str, Any]:
    if not context_router.set_mode(mode_name.upper()):
        raise HTTPException(status_code=404, detail=f"Mode not found: {mode_name}")
    return context_router.get_mode()


@app.get("/agents")
def get_agents() -> Dict[str, Any]:
    return {"active_agents": context_router.get_active_agents()}


@app.post("/route")
async def route_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    agent_name = payload.get("agent")
    request_text = payload.get("request", "")
    if not agent_name:
        raise HTTPException(status_code=400, detail="agent field is required")

    try:
        decision = context_router.route_request(agent_name, request_text, metadata=payload.get("metadata"))
        await event_bus.publish_sync(
            EventType.AGENT_MESSAGE,
            {"agent": agent_name, "request": request_text, "mode": context_router.current_mode},
            source="ui.asim_unified_server"
        )
        return decision
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))


@app.get("/status")
def status() -> Dict[str, Any]:
    return {
        "mode": context_router.get_mode(),
        "event_bus": event_bus.get_stats()
    }


def create_app() -> FastAPI:
    return app
