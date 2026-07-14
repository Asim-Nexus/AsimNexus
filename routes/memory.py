"""
Memory Routes
=============
Endpoints for memory, database, conversations, API keys.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Memory"])

logger = logging.getLogger("AsimNexus.Routes.Memory")

# Module-level globals set by app.py at startup
orchestrator = None
memory_manager = None
db_manager = None


def _get_db():
    """Get DB manager — prefer injected globals, fall back to singleton."""
    if db_manager is not None:
        return db_manager
    try:
        from database import get_db
        return get_db()
    except Exception:
        return None


def init_memory(app_globals: dict) -> None:
    """Initialize memory module from app.py globals."""
    global orchestrator, memory_manager, db_manager
    orchestrator = app_globals.get("orchestrator")
    memory_manager = app_globals.get("memory_manager")
    db_manager = app_globals.get("db_manager")


# ── Memory ────────────────────────────────────────────────────────────

@router.get("/api/memory/stats")
async def memory_stats():
    """Memory system statistics."""
    try:
        if memory_manager:
            data = await memory_manager.get_stats()
            return ok(data=data)
        return ok(data={"total_messages": 0, "total_conversations": 0})
    except Exception as e:
        logger.error(f"memory_stats error: {e}")
        return error(str(e))


@router.get("/api/memory/recent")
async def memory_recent():
    """Recent memory entries."""
    try:
        if memory_manager:
            data = await memory_manager.get_recent()
            return ok(data=data)
        return ok(data={"messages": [], "count": 0})
    except Exception as e:
        logger.error(f"memory_recent error: {e}")
        return error(str(e))


@router.get("/api/memory/search")
async def memory_search(query: str = "", limit: int = 20):
    """Search memory entries."""
    try:
        if memory_manager:
            data = await memory_manager.search(query, limit)
            return ok(data=data)
        return ok(data={"results": [], "count": 0})
    except Exception as e:
        logger.error(f"memory_search error: {e}")
        return error(str(e))


@router.delete("/api/memory/{message_id}")
async def memory_delete(message_id: str):
    """Delete a memory entry."""
    try:
        if memory_manager:
            data = await memory_manager.delete(message_id)
            return ok(data=data)
        return unavailable("memory_manager")
    except Exception as e:
        logger.error(f"memory_delete error: {e}")
        return error(str(e))


# ── Database ──────────────────────────────────────────────────────────

@router.get("/api/db/conversations/user/{user_id}")
async def db_conversations(user_id: str):
    """Get conversations for a user."""
    try:
        db = _get_db()
        if db:
            data = await db.get_conversations(user_id)
            return ok(data=data)
        return ok(data={"conversations": [], "count": 0})
    except Exception as e:
        logger.error(f"db_conversations error: {e}")
        return error(str(e))


@router.get("/api/db/api-keys/{user_id}")
async def db_api_keys(user_id: str):
    """Get API keys for a user."""
    try:
        db = _get_db()
        if db:
            data = await db.get_api_keys(user_id)
            return ok(data=data)
        return ok(data={"keys": [], "count": 0})
    except Exception as e:
        logger.error(f"db_api_keys error: {e}")
        return error(str(e))


@router.post("/api/keys/update")
async def keys_update(data: dict = Body(...)):
    """Update API keys."""
    try:
        db = _get_db()
        if db:
            result = await db.update_keys(
                data.get("user_id", ""),
                data.get("keys", {})
            )
            return ok(data=result)
        return unavailable("db_manager")
    except Exception as e:
        logger.error(f"keys_update error: {e}")
        return error(str(e))


@router.get("/api/db/health")
async def db_health():
    """Database health check."""
    try:
        db = _get_db()
        if db:
            data = await db.health_check()
            return ok(data=data)
        return ok(data={"status": "healthy"})
    except Exception as e:
        logger.error(f"db_health error: {e}")
        return error(str(e))


# ── Personal OS ───────────────────────────────────────────────────────

@router.get("/personal/status")
async def personal_status():
    """Personal OS status."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.get_status()
            return ok(data=data)
        return ok(data={"status": "active"})
    except Exception as e:
        logger.error(f"personal_status error: {e}")
        return error(str(e))


@router.get("/personal/clones")
async def personal_clones():
    """Personal OS clones."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.get_clones()
            return ok(data=data)
        return ok(data={"clones": [], "count": 0})
    except Exception as e:
        logger.error(f"personal_clones error: {e}")
        return error(str(e))


@router.get("/api/personal/status")
async def api_personal_status():
    """Personal OS API status."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.get_api_status()
            return ok(data=data)
        return ok(data={"status": "active"})
    except Exception as e:
        logger.error(f"api_personal_status error: {e}")
        return error(str(e))


@router.get("/api/personal/universe")
async def api_personal_universe():
    """Personal universe info."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.get_universe()
            return ok(data=data)
        return ok(data={"universe": {}})
    except Exception as e:
        logger.error(f"api_personal_universe error: {e}")
        return error(str(e))


@router.get("/api/personal/contracts")
async def api_personal_contracts():
    """Personal contracts."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.get_contracts()
            return ok(data=data)
        return ok(data={"contracts": [], "count": 0})
    except Exception as e:
        logger.error(f"api_personal_contracts error: {e}")
        return error(str(e))


@router.post("/api/agent/mode/on")
async def agent_mode_on():
    """Enable agent mode."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.agent_mode_on()
            return ok(data=data)
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"agent_mode_on error: {e}")
        return error(str(e))


@router.post("/api/agent/mode/off")
async def agent_mode_off():
    """Disable agent mode."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.agent_mode_off()
            return ok(data=data)
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"agent_mode_off error: {e}")
        return error(str(e))


@router.get("/api/agent/status")
async def agent_status():
    """Agent status."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.get_agent_status()
            return ok(data=data)
        return ok(data={"status": "inactive"})
    except Exception as e:
        logger.error(f"agent_status error: {e}")
        return error(str(e))


@router.get("/api/universe/status")
async def universe_status():
    """Universe status."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.get_universe_status()
            return ok(data=data)
        return ok(data={"status": "active"})
    except Exception as e:
        logger.error(f"universe_status error: {e}")
        return error(str(e))


@router.get("/api/personal/resource-sharing")
async def personal_resource_sharing():
    """Get resource sharing settings."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.get_resource_sharing()
            return ok(data=data)
        return ok(data={"enabled": False})
    except Exception as e:
        logger.error(f"personal_resource_sharing error: {e}")
        return error(str(e))


@router.post("/api/personal/resource-sharing")
async def personal_resource_sharing_update(data: dict = Body(...)):
    """Update resource sharing settings."""
    try:
        if orchestrator:
            result = await orchestrator.personal_os.set_resource_sharing(
                data.get("enabled", False),
                data.get("resources", [])
            )
            return ok(data=result)
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"personal_resource_sharing_update error: {e}")
        return error(str(e))


# ── Universe (additional) ─────────────────────────────────────────────

@router.get("/api/universe/list")
async def universe_list():
    """List universes."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.list_universes()
            return ok(data=data)
        return ok(data={"universes": [], "count": 0})
    except Exception as e:
        logger.error(f"universe_list error: {e}")
        return error(str(e))


@router.get("/api/universe/containers")
async def universe_containers(did: str = ""):
    """Get universe containers."""
    try:
        if orchestrator:
            data = await orchestrator.personal_os.get_containers(did)
            return ok(data=data)
        return ok(data={"containers": [], "count": 0})
    except Exception as e:
        logger.error(f"universe_containers error: {e}")
        return error(str(e))


@router.post("/api/universe/data-flow-check")
async def universe_data_flow(data: dict = Body(...)):
    """Check universe data flow."""
    try:
        if orchestrator:
            result = await orchestrator.personal_os.check_data_flow(
                data.get("source", ""),
                data.get("destination", ""),
                data.get("data_type", "")
            )
            return ok(data=result)
        return ok(data={"allowed": True}, note="orchestrator unavailable")
    except Exception as e:
        logger.error(f"universe_data_flow error: {e}")
        return error(str(e))

# ── Contract-mandated Memory Routes ──────────────────────────────────

@router.post("/api/memory/add")
async def api_memory_add(data: dict = Body(...)):
    """Add a memory entry."""
    try:
        if memory_manager:
            result = await memory_manager.add(data)
            return ok(data=result)
        return unavailable("memory_manager")
    except Exception as e:
        logger.error(f"api_memory_add error: {e}")
        return error(str(e))


@router.post("/api/memory/search")
async def api_memory_search(query: str = "", limit: int = 20):
    """Search memory entries."""
    try:
        if memory_manager:
            result = await memory_manager.search(query, limit=limit)
            return ok(data=result)
        return unavailable("memory_manager")
    except Exception as e:
        logger.error(f"api_memory_search error: {e}")
        return error(str(e))


@router.post("/api/memory/prune")
async def api_memory_prune(data: dict = Body(...)):
    """Prune old memory entries."""
    try:
        if memory_manager:
            result = await memory_manager.prune(data)
            return ok(data=result)
        return unavailable("memory_manager")
    except Exception as e:
        logger.error(f"api_memory_prune error: {e}")
        return error(str(e))


@router.get("/api/memory/user/{user_id}")
async def api_memory_user(user_id: str):
    """Get memory entries for a user."""
    try:
        if memory_manager:
            result = await memory_manager.get_by_user(user_id)
            return ok(data=result)
        return unavailable("memory_manager")
    except Exception as e:
        logger.error(f"api_memory_user error: {e}")
        return error(str(e))


@router.get("/api/memory/{memory_id}")
async def api_memory_get(memory_id: str):
    """Get a specific memory entry."""
    try:
        if memory_manager:
            result = await memory_manager.get(memory_id)
            return ok(data=result)
        return unavailable("memory_manager")
    except Exception as e:
        logger.error(f"api_memory_get error: {e}")
        return error(str(e))


@router.delete("/api/memory/{memory_id}")
async def api_memory_delete(memory_id: str):
    """Delete a memory entry."""
    try:
        if memory_manager:
            result = await memory_manager.delete(memory_id)
            return ok(data=result)
        return unavailable("memory_manager")
    except Exception as e:
        logger.error(f"api_memory_delete error: {e}")
        return error(str(e))
