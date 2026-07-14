"""
Founder Clones Routes
=====================
REST API endpoints for the Founder Clone System:
- List, spawn, and manage 15 Founder Clones
- Assign tasks and monitor clone status
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Body

from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.FounderClones")

router = APIRouter(prefix="/api/founder-clones", tags=["Founder Clones"])

_app_globals: dict = {}


def init_founder_clones(app_globals: dict) -> None:
    """Store app globals for lazy initialization."""
    global _app_globals
    _app_globals = app_globals


@router.get("/list")
async def founder_clones_list():
    """List all available founder clones."""
    try:
        from core.founder_clones.founder_clone_system import FounderCloneSystem
        system = FounderCloneSystem()
        clones = system.get_all_clones() if hasattr(system, 'get_all_clones') else []
        return ok(data={"clones": clones, "total": len(clones)})
    except Exception as e:
        logger.warning(f"Founder clones list error: {e}")
        return error(str(e), status_code=500)


@router.post("/spawn")
async def founder_clones_spawn(data: dict = Body(...)):
    """Spawn a new founder clone."""
    try:
        from core.founder_clones.founder_clone_system import FounderCloneSystem, FounderRole
        system = FounderCloneSystem()
        role_name = data.get("role", "CTO")
        role = FounderRole[role_name] if role_name in FounderRole.__members__ else FounderRole.CTO
        clone = system.spawn_clone(role, data.get("config", {})) if hasattr(system, 'spawn_clone') else None
        return ok(data={"role": role_name, "clone": clone.to_dict() if clone else None})
    except Exception as e:
        logger.warning(f"Founder clone spawn error: {e}")
        return error(str(e), status_code=500)


@router.get("/{clone_id}/status")
async def founder_clone_status(clone_id: str):
    """Get the status of a specific founder clone."""
    try:
        from core.founder_clones.founder_clone_system import FounderCloneSystem
        system = FounderCloneSystem()
        clone = system.get_clone(clone_id) if hasattr(system, 'get_clone') else None
        if clone is None:
            return error(f"Clone {clone_id} not found", status_code=404)
        return ok(data={"clone_id": clone_id, "status": clone.to_dict() if hasattr(clone, 'to_dict') else {}})
    except Exception as e:
        logger.warning(f"Founder clone status error: {e}")
        return error(str(e), status_code=500)


@router.post("/{clone_id}/assign-task")
async def founder_clone_assign_task(clone_id: str, data: dict = Body(...)):
    """Assign a task to a founder clone."""
    try:
        from core.founder_clones.founder_clone_system import FounderCloneSystem
        system = FounderCloneSystem()
        task = data.get("task", "")
        result = system.assign_task(clone_id, task) if hasattr(system, 'assign_task') else None
        return ok(data={"clone_id": clone_id, "task": task, "result": result})
    except Exception as e:
        logger.warning(f"Founder clone assign task error: {e}")
        return error(str(e), status_code=500)


@router.post("/{clone_id}/terminate")
async def founder_clone_terminate(clone_id: str):
    """Terminate a founder clone."""
    try:
        from core.founder_clones.founder_clone_system import FounderCloneSystem
        system = FounderCloneSystem()
        success = system.terminate_clone(clone_id) if hasattr(system, 'terminate_clone') else False
        return ok(data={"clone_id": clone_id, "terminated": success})
    except Exception as e:
        logger.warning(f"Founder clone terminate error: {e}")
        return error(str(e), status_code=500)
