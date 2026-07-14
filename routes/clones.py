"""
Clone Routes
============
Endpoints for clone management: status, tasks, skills, consensus.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Clones"])

logger = logging.getLogger("AsimNexus.Routes.Clones")

clone_manager = None

def init_clones(app_globals: dict) -> None:
    global clone_manager
    clone_manager = app_globals.get("clone_manager")

@router.get("/api/clones/status")
async def clones_status():
    """Get clone system status."""
    try:
        if clone_manager:
            data = await clone_manager.get_status()
            return ok(data=data)
        return ok(data={"status": "active", "active_clones": 0})
    except Exception as e:
        logger.error(f"clones_status error: {e}")
        return error(str(e))

@router.get("/api/clones/available")
async def clones_available():
    """List available clones."""
    try:
        if clone_manager:
            data = await clone_manager.list_available()
            return ok(data=data)
        return ok(data={"clones": [], "count": 0})
    except Exception as e:
        logger.error(f"clones_available error: {e}")
        return error(str(e))

@router.get("/api/clones/{clone_id}")
async def clones_get(clone_id: str):
    """Get clone details by ID."""
    try:
        if clone_manager:
            data = await clone_manager.get_clone(clone_id)
            return ok(data=data)
        return ok(data={"clone_id": clone_id, "status": "unknown"})
    except Exception as e:
        logger.error(f"clones_get error: {e}")
        return error(str(e))

@router.get("/api/clones/skill/{skill}")
async def clones_by_skill(skill: str):
    """Find clones by skill."""
    try:
        if clone_manager:
            data = await clone_manager.find_by_skill(skill)
            return ok(data=data)
        return ok(data={"skill": skill, "clones": [], "count": 0})
    except Exception as e:
        logger.error(f"clones_by_skill error: {e}")
        return error(str(e))

@router.post("/api/clones/task")
async def clones_task(data: dict = Body(...)):
    """Create a clone task."""
    try:
        if clone_manager:
            result = await clone_manager.create_task(data)
            return ok(data=result)
        return ok(data={"status": "created", "task_id": "mock_task"})
    except Exception as e:
        logger.error(f"clones_task error: {e}")
        return error(str(e))

@router.post("/api/clones/task/{task_id}/assign")
async def clones_task_assign(task_id: str, data: dict = Body(...)):
    """Assign a task to a clone."""
    try:
        if clone_manager:
            result = await clone_manager.assign_task(task_id, data.get("clone_id", ""))
            return ok(data=result)
        return ok(data={"status": "assigned", "task_id": task_id})
    except Exception as e:
        logger.error(f"clones_task_assign error: {e}")
        return error(str(e))

@router.post("/api/clones/task/{task_id}/complete")
async def clones_task_complete(task_id: str, data: dict = Body(...)):
    """Mark a clone task as complete."""
    try:
        if clone_manager:
            result = await clone_manager.complete_task(task_id, data)
            return ok(data=result)
        return ok(data={"status": "completed", "task_id": task_id})
    except Exception as e:
        logger.error(f"clones_task_complete error: {e}")
        return error(str(e))

@router.post("/api/clones/consensus")
async def clones_consensus(data: dict = Body(...)):
    """Initiate a consensus vote among clones."""
    try:
        if clone_manager:
            result = await clone_manager.initiate_consensus(data)
            return ok(data=result)
        return ok(data={"status": "initiated", "decision_id": "mock_decision"})
    except Exception as e:
        logger.error(f"clones_consensus error: {e}")
        return error(str(e))

@router.get("/api/clones/consensus/{decision_id}")
async def clones_consensus_get(decision_id: str):
    """Get consensus decision details."""
    try:
        if clone_manager:
            data = await clone_manager.get_consensus(decision_id)
            return ok(data=data)
        return ok(data={"decision_id": decision_id, "status": "unknown"})
    except Exception as e:
        logger.error(f"clones_consensus_get error: {e}")
        return error(str(e))

@router.post("/api/clones/consensus/{decision_id}/vote")
async def clones_consensus_vote(decision_id: str, data: dict = Body(...)):
    """Vote on a consensus decision."""
    try:
        if clone_manager:
            result = await clone_manager.vote_consensus(decision_id, data.get("clone_id", ""), data.get("vote", "abstain"))
            return ok(data=result)
        return ok(data={"status": "voted", "decision_id": decision_id})
    except Exception as e:
        logger.error(f"clones_consensus_vote error: {e}")
        return error(str(e))
