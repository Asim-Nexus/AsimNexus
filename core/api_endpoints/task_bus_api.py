from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_bus = None
def _get_bus():
    global _bus
    if _bus is None:
        try:
            from core.economy.task_bus import get_task_bus, TaskPriority
            _bus = get_task_bus()
            logger.info("TaskBus loaded")
        except Exception as e:
            logger.warning(f"TaskBus unavailable: {e}")
    return _bus


class RegisterAgentRequest(BaseModel):
    agent_id: str
    capabilities: List[str] = Field(default_factory=list)
    display_name: str = ""
    max_concurrent: int = 5
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SubmitTaskRequest(BaseModel):
    task_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "medium"
    max_retries: int = 3
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AssignNextRequest(BaseModel):
    agent_id: str

class TaskActionRequest(BaseModel):
    task_id: str
    agent_id: str

class FailTaskRequest(BaseModel):
    task_id: str
    agent_id: str
    error: str


@router.get("/api/task-bus/status")
async def task_bus_status():
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    return bus.get_bus_status()


@router.post("/api/task-bus/agent/register")
async def task_bus_register_agent(req: RegisterAgentRequest):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    agent = bus.register_agent(req.agent_id, req.capabilities, req.display_name,
                               req.max_concurrent, req.metadata)
    return {"success": True, "agent": agent.to_dict()}


@router.post("/api/task-bus/agent/{agent_id}/unregister")
async def task_bus_unregister_agent(agent_id: str):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    for node_id in list(bus.agents.keys()):
        if bus.agents[node_id].agent_id == agent_id:
            bus.unregister_agent(node_id)
            return {"success": True}
    raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")


@router.get("/api/task-bus/agents")
async def task_bus_list_agents(online_only: bool = Query(False)):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    return {"agents": bus.list_agents(online_only)}


@router.post("/api/task-bus/task/submit")
async def task_bus_submit_task(req: SubmitTaskRequest):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    try:
        from core.economy.task_bus import TaskPriority
        priority = TaskPriority(req.priority)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {req.priority}")
    task = bus.submit_task(req.task_type, req.payload, priority,
                           req.max_retries, req.timeout_seconds, req.metadata)
    return {"success": True, "task": task.to_dict()}


@router.post("/api/task-bus/task/assign-next")
async def task_bus_assign_next(req: AssignNextRequest):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    task = bus.assign_next_task(req.agent_id)
    if not task:
        return {"success": False, "message": "No task available"}
    return {"success": True, "task": task}


@router.post("/api/task-bus/task/{task_id}/start")
async def task_bus_start_task(task_id: str, agent_id: str = Query(...)):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    ok = bus.start_task(task_id, agent_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to start task")
    return {"success": True, "status": "running"}


@router.post("/api/task-bus/task/{task_id}/complete")
async def task_bus_complete_task(task_id: str, req: TaskActionRequest):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    ok = bus.complete_task(task_id, req.agent_id, {})
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to complete task")
    return {"success": True, "status": "completed"}


@router.post("/api/task-bus/task/{task_id}/fail")
async def task_bus_fail_task(task_id: str, req: FailTaskRequest):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    ok = bus.fail_task(task_id, req.agent_id, req.error)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to fail task")
    return {"success": True}


@router.post("/api/task-bus/task/{task_id}/cancel")
async def task_bus_cancel_task(task_id: str):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    ok = bus.cancel_task(task_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to cancel task")
    return {"success": True, "status": "cancelled"}


@router.get("/api/task-bus/tasks")
async def task_bus_list_tasks(
    state: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    return {"total": len(bus.tasks), "tasks": bus.list_tasks(state, task_type, limit)}


@router.get("/api/task-bus/task/{task_id}")
async def task_bus_get_task(task_id: str):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    task = bus.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return task


@router.get("/api/task-bus/agent/{agent_id}/tasks")
async def task_bus_agent_tasks(agent_id: str, limit: int = Query(50, ge=1, le=500)):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    return {"agent_id": agent_id, "tasks": bus.get_agent_tasks(agent_id, limit)}


@router.post("/api/task-bus/agent/{agent_id}/heartbeat")
async def task_bus_heartbeat(agent_id: str):
    bus = _get_bus()
    if not bus:
        raise HTTPException(status_code=503, detail="TaskBus not available")
    ok = bus.heartbeat(agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {"success": True, "status": "online"}
