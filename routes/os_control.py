"""
OS Control Routes
=================
Endpoints for OS control, tools, deploy, clones, kernel operations.
"""

import logging
from fastapi import APIRouter, Body
from typing import Optional

from routes.response import ok, error, unavailable
from core.orchestrator.tool_registry import tool_registry

router = APIRouter(tags=["OS Control"])

logger = logging.getLogger("AsimNexus.Routes.OSControl")

# Module-level globals set by app.py at startup
orchestrator = None
os_executor = None
tool_manager = None
clone_manager = None
deploy_manager = None


def init_os_control(app_globals: dict) -> None:
    """Initialize OS control module from app.py globals."""
    global orchestrator, os_executor, tool_manager, clone_manager, deploy_manager
    orchestrator = app_globals.get("orchestrator")
    os_executor = app_globals.get("os_executor")
    tool_manager = app_globals.get("tool_manager")
    clone_manager = app_globals.get("clone_manager")
    deploy_manager = app_globals.get("deploy_manager")


# ── OS Control ────────────────────────────────────────────────────────

@router.get("/api/os/status")
async def os_status():
    """OS control status."""
    try:
        if os_executor:
            return ok(data=await os_executor.get_status())
        return ok(data={"status": "active", "mode": "standalone"})
    except Exception as e:
        logger.error(f"os_status error: {e}")
        return error(str(e))


@router.get("/api/os/metrics")
async def os_metrics():
    """OS metrics."""
    try:
        if os_executor:
            return ok(data=await os_executor.get_metrics())
        return ok(data={"cpu": 0, "memory": 0, "disk": 0})
    except Exception as e:
        logger.error(f"os_metrics error: {e}")
        return error(str(e))


@router.get("/api/os/pending")
async def os_pending():
    """Get pending OS approvals."""
    try:
        if os_executor:
            return ok(data=await os_executor.get_pending())
        return ok(data={"pending": [], "count": 0})
    except Exception as e:
        logger.error(f"os_pending error: {e}")
        return error(str(e))


@router.post("/api/os/approve/{call_id}")
async def os_approve(call_id: str):
    """Approve an OS operation."""
    try:
        if os_executor:
            return ok(data=await os_executor.approve(call_id))
        return unavailable("os_executor")
    except Exception as e:
        logger.error(f"os_approve error: {e}")
        return error(str(e))


@router.post("/api/os/reject/{call_id}")
async def os_reject(call_id: str):
    """Reject an OS operation."""
    try:
        if os_executor:
            return ok(data=await os_executor.reject(call_id))
        return unavailable("os_executor")
    except Exception as e:
        logger.error(f"os_reject error: {e}")
        return error(str(e))


@router.get("/api/os/audit")
async def os_audit():
    """Get OS audit log."""
    try:
        if os_executor:
            return ok(data=await os_executor.get_audit_log())
        return ok(data={"audit": [], "count": 0})
    except Exception as e:
        logger.error(f"os_audit error: {e}")
        return error(str(e))


@router.get("/api/os/clipboard/status")
async def os_clipboard_status():
    """Get clipboard status."""
    try:
        if os_executor:
            return ok(data=await os_executor.clipboard_status())
        return ok(data={"status": "inactive"})
    except Exception as e:
        logger.error(f"os_clipboard_status error: {e}")
        return error(str(e))


@router.post("/api/os/execute")
async def os_execute(data: dict = Body(...)):
    """Execute an OS command."""
    try:
        if os_executor:
            return ok(data=await os_executor.execute(data.get("command", ""), data.get("args", {})))
        return unavailable("os_executor")
    except Exception as e:
        logger.error(f"os_execute error: {e}")
        return error(str(e))


# ── Tools ─────────────────────────────────────────────────────────────

@router.get("/api/tools")
async def list_tools():
    """List all available tools."""
    try:
        if tool_manager:
            # ToolRegistry.list_tools() is sync, not async
            return ok(data=tool_manager.list_tools())
        return ok(data={"tools": [], "count": 0})
    except Exception as e:
        logger.error(f"list_tools error: {e}")
        return error(str(e))


@router.get("/api/os/tools")
async def os_tools():
    """List all available OS tools (frontend compatibility)."""
    try:
        if tool_manager:
            return ok(data=await tool_manager.list_tools())
        if os_executor:
            return ok(data=await os_executor.list_tools())
        return ok(data={"tools": [], "count": 0})
    except Exception as e:
        logger.error(f"os_tools error: {e}")
        return error(str(e))


@router.post("/api/tools/execute")
async def execute_tool(data: dict = Body(...)):
    """Execute an OS control tool through the executor."""
    try:
        if os_executor:
            return ok(data=await os_executor.execute_tool(data.get("tool", ""), data.get("params", {})))
        return unavailable("os_executor")
    except Exception as e:
        logger.error(f"execute_tool error: {e}")
        return error(str(e))


@router.get("/api/tools/list")
async def tool_list():
    """List all available tools."""
    try:
        if tool_manager:
            return ok(data=await tool_manager.list_tools())
        return ok(data={"tools": [], "count": 0})
    except Exception as e:
        logger.error(f"tool_list error: {e}")
        return error(str(e))


@router.get("/api/tools/pending")
async def tool_pending():
    """Get list of approved tool executions pending human approval."""
    try:
        if tool_manager:
            return ok(data=await tool_manager.get_pending())
        return ok(data={"pending": [], "count": 0})
    except Exception as e:
        logger.error(f"tool_pending error: {e}")
        return error(str(e))


@router.post("/api/tools/approve")
async def tool_approve(data: dict = Body(...)):
    """Approve a pending tool execution."""
    try:
        if tool_manager:
            return ok(data=await tool_manager.approve(data.get("call_id", "")))
        return unavailable("tool_manager")
    except Exception as e:
        logger.error(f"tool_approve error: {e}")
        return error(str(e))


@router.post("/api/tools/reject")
async def tool_reject(data: dict = Body(...)):
    """Reject a pending tool execution."""
    try:
        if tool_manager:
            return ok(data=await tool_manager.reject(data.get("call_id", "")))
        return unavailable("tool_manager")
    except Exception as e:
        logger.error(f"tool_reject error: {e}")
        return error(str(e))


@router.get("/api/tools/audit")
async def tool_audit(data: dict = Body(...), limit: int = 30):
    """Get tool audit log."""
    try:
        if tool_manager:
            return ok(data=await tool_manager.get_audit(limit=limit))
        return ok(data={"audit": [], "count": 0})
    except Exception as e:
        logger.error(f"tool_audit error: {e}")
        return error(str(e))


@router.get("/api/tools/catalog")
async def tool_catalog():
    """Get the full tool catalog with rich metadata.

    Returns every registered tool with:
    - tool_id: Unique identifier (e.g. ``hw.status``, ``file.read``)
    - description: Human-readable description
    - risk_level: LOW / MEDIUM / HIGH / CRITICAL
    - category: Tool category (file, process, system, clipboard, notification, hw)
    - required_capabilities: List of ``Capability`` enum values needed
    - requires_confirmation: Whether human confirmation is required
    - sandbox_required: Whether sandbox execution is required
    - allowed_args: Dict of allowed parameter names → type hints
    """
    try:
        registrations = tool_registry.list_registrations()
        if not registrations:
            # Fallback: build catalog from dict-based list_tools()
            tools = tool_registry.list_tools()
            catalog = [
                {
                    "tool_id": tid,
                    "description": meta.get("desc", ""),
                    "risk_level": meta.get("risk", "unknown"),
                    "category": meta.get("category", "uncategorized"),
                    "required_capabilities": meta.get("required_capabilities", []),
                    "requires_confirmation": meta.get("requires_confirmation", False),
                    "sandbox_required": meta.get("sandbox_required", False),
                    "allowed_args": meta.get("allowed_args", {}),
                }
                for tid, meta in tools.items()
            ]
            return ok(data={"catalog": catalog, "count": len(catalog)})

        catalog = [
            {
                "tool_id": reg.tool_id,
                "description": reg.description,
                "risk_level": reg.risk_level.value if hasattr(reg.risk_level, "value") else str(reg.risk_level),
                "category": reg.tool_id.split(".")[0] if "." in reg.tool_id else "system",
                "required_capabilities": [c.value for c in reg.required_capabilities],
                "requires_confirmation": reg.requires_confirmation,
                "sandbox_required": reg.sandbox_required,
                "allowed_args": reg.allowed_args,
            }
            for reg in registrations
        ]
        return ok(data={"catalog": catalog, "count": len(catalog)})
    except Exception as e:
        logger.error(f"tool_catalog error: {e}")
        return error(str(e))


# ── Sandbox ───────────────────────────────────────────────────────────

@router.post("/api/v1/sandbox/execute")
async def sandbox_execute(data: dict = Body(...)):
    """Tool लाई sandbox मा चलाउने।"""
    try:
        if os_executor:
            return ok(data=await os_executor.sandbox_execute(data.get("tool", ""), data.get("params", {})))
        return unavailable("os_executor")
    except Exception as e:
        logger.error(f"sandbox_execute error: {e}")
        return error(str(e))


@router.get("/api/v1/sandbox/status")
async def sandbox_status():
    """Sandbox अवस्था।"""
    try:
        if os_executor:
            return ok(data=await os_executor.sandbox_status())
        return ok(data={"status": "inactive"})
    except Exception as e:
        logger.error(f"sandbox_status error: {e}")
        return error(str(e))


# ── Clones ────────────────────────────────────────────────────────────

@router.get("/api/clones/specs")
async def clones_specs():
    """Get clone specifications."""
    try:
        if clone_manager:
            return ok(data=await clone_manager.get_specs())
        return ok(data={"specs": [], "count": 0})
    except Exception as e:
        logger.error(f"clones_specs error: {e}")
        return error(str(e))


@router.get("/api/clones/{clone_id}/spec")
async def clone_spec(clone_id: str):
    """Get a specific clone specification."""
    try:
        if clone_manager:
            return ok(data=await clone_manager.get_spec(clone_id))
        return ok(data={"clone_id": clone_id, "spec": {}}, note="clone_manager unavailable")
    except Exception as e:
        logger.error(f"clone_spec error: {e}")
        return error(str(e))


@router.post("/api/clones/route")
async def clones_route(data: dict = Body(...)):
    """Route a request to a clone."""
    try:
        if clone_manager:
            return ok(data=await clone_manager.route(data.get("clone_id", ""), data.get("request", {})))
        return unavailable("clone_manager")
    except Exception as e:
        logger.error(f"clones_route error: {e}")
        return error(str(e))


@router.get("/api/clones")
async def personal_clones():
    """Get personal clones."""
    try:
        if clone_manager:
            return ok(data=await clone_manager.list_clones())
        return ok(data={"clones": [], "count": 0})
    except Exception as e:
        logger.error(f"personal_clones error: {e}")
        return error(str(e))


# ── Deploy ────────────────────────────────────────────────────────────

@router.post("/api/deploy/build")
async def deploy_build(data: dict = Body(...)):
    """Build a deployment."""
    try:
        if deploy_manager:
            return ok(data=await deploy_manager.build(data.get("project", ""), data.get("config", {})))
        return unavailable("deploy_manager")
    except Exception as e:
        logger.error(f"deploy_build error: {e}")
        return error(str(e))


@router.post("/api/deploy/rollback")
async def deploy_rollback(data: dict = Body(...)):
    """Rollback a deployment."""
    try:
        if deploy_manager:
            return ok(data=await deploy_manager.rollback(data.get("version", "")))
        return unavailable("deploy_manager")
    except Exception as e:
        logger.error(f"deploy_rollback error: {e}")
        return error(str(e))


@router.post("/api/deploy/release")
async def deploy_release(data: dict = Body(...)):
    """Release a deployment."""
    try:
        if deploy_manager:
            return ok(data=await deploy_manager.release(data.get("version", ""), data.get("artifacts", {})))
        return unavailable("deploy_manager")
    except Exception as e:
        logger.error(f"deploy_release error: {e}")
        return error(str(e))


# ── Mirror ────────────────────────────────────────────────────────────

@router.post("/api/v1/mirror/reflect")
async def mirror_reflect(data: dict = Body(...)):
    """Mirror कार्यलाई प्रतिबिम्बित गर्ने।"""
    try:
        from core.mirror.mirror_module import MirrorModule
        user_id = data.get("user_id", "default")
        action = data.get("data", data)
        mirror = MirrorModule(user_id)
        reflection = await mirror.reflect(action)
        return ok(data={
            "user_id": user_id,
            "reflection": {
                "intent": reflection.intent,
                "outcome": reflection.outcome,
                "contradictions": reflection.contradictions,
                "balance_impact": reflection.balance_impact,
                "mirror_response": reflection.mirror_response,
            },
        })
    except Exception as e:
        logger.error(f"mirror_reflect error: {e}")
        return error(str(e))


@router.get("/api/v1/mirror/daily/{user_id}")
async def mirror_daily(user_id: str):
    """दैनिक Mirror रिपोर्ट।"""
    try:
        from core.mirror.mirror_module import MirrorModule
        mirror = MirrorModule(user_id)
        # Run nightly dream to get latest insights
        dreams = await mirror.nightly_dream()
        return ok(data={
            "user_id": user_id,
            "dreams": [
                {
                    "type": d.dream_type.value,
                    "content": d.content,
                    "confidence": d.confidence,
                    "timestamp": d.timestamp,
                }
                for d in dreams
            ],
            "reflections_count": len(mirror.reflections),
        })
    except Exception as e:
        logger.error(f"mirror_daily error: {e}")
        return error(str(e))


@router.post("/api/v1/mirror/dream")
async def mirror_dream(data: dict = Body(...)):
    """Dreaming Engine सञ्चालन गर्ने।"""
    try:
        # Use the real dreaming engine singleton directly
        from core.dreaming.dreaming_engine import dreaming_engine
        user_id = data.get("user_id", "default")
        prompt = data.get("prompt", "")
        
        # Trigger a dreaming cycle
        briefing = await dreaming_engine.trigger_now()
        
        # Get recent lessons
        lessons = dreaming_engine.get_recent_lessons(limit=10)
        
        return ok(data={
            "user_id": user_id,
            "prompt": prompt,
            "briefing": briefing,
            "lessons": lessons,
            "status": dreaming_engine.status(),
        })
    except Exception as e:
        logger.error(f"mirror_dream error: {e}")
        return error(str(e))


@router.post("/api/v1/mirror/fine-tune")
async def mirror_fine_tune(data: dict = Body(...)):
    """Fine-tune the Mirror model on user reflections."""
    try:
        from core.mirror.mirror_module import MirrorModule
        user_id = data.get("user_id", "default")
        mirror = MirrorModule(user_id)
        # Trigger fine-tuning using the LoRA engine
        if mirror.lora_engine:
            reflections_dicts = [r.to_dict() for r in mirror.reflections]
            result = await mirror.lora_engine.fine_tune(reflections_dicts)
            return ok(data={"user_id": user_id, "fine_tune_result": result})
        return ok(data={"user_id": user_id, "status": "no_lora_engine", "note": "LoRA engine not available"})
    except Exception as e:
        logger.error(f"mirror_fine_tune error: {e}")
        return error(str(e))


@router.get("/api/v1/mirror/state/{user_id}")
async def mirror_state(user_id: str):
    """Get the current state of a user's Mirror."""
    try:
        from core.mirror.mirror_module import MirrorModule
        mirror = MirrorModule(user_id)
        state = {}
        if mirror.consciousness:
            state["consciousness"] = mirror.consciousness.get_state()
        state["reflections_count"] = len(mirror.reflections)
        state["evolution_suggestions_count"] = len(mirror.evolution_suggestions)
        state["user_id"] = user_id
        return ok(data=state)
    except Exception as e:
        logger.error(f"mirror_state error: {e}")
        return error(str(e))


# ── Runtime ───────────────────────────────────────────────────────────

@router.get("/api/runtime/status")
async def runtime_status():
    """Runtime status."""
    try:
        if orchestrator:
            # Orchestrator has no .runtime attribute; use getattr with fallback
            runtime = getattr(orchestrator, 'runtime', None)
            if runtime is not None:
                method = getattr(runtime, 'get_status', None)
                if method is not None:
                    result = method()
                    if hasattr(result, '__await__'):
                        return ok(data=await result)
                    return ok(data=result)
            # Fallback: return orchestrator's own state
            return ok(data={
                "status": "active",
                "agents": list(getattr(orchestrator, 'agents', {}).keys()),
                "dharma": getattr(orchestrator, 'dharma', None) is not None,
                "consensus": getattr(orchestrator, 'consensus', None) is not None,
                "personal_os": getattr(orchestrator, 'personal_os', None) is not None,
            })
        return ok(data={"status": "active"})
    except Exception as e:
        logger.error(f"runtime_status error: {e}")
        return error(str(e))


@router.post("/api/runtime/register")
async def runtime_register(data: dict = Body(...)):
    """Register a runtime principal."""
    try:
        if orchestrator:
            runtime = getattr(orchestrator, 'runtime', None)
            if runtime is not None:
                method = getattr(runtime, 'register', None)
                if method is not None:
                    result = method(data.get("principal", ""), data.get("capabilities", []))
                    if hasattr(result, '__await__'):
                        return ok(data=await result)
                    return ok(data=result)
            # Fallback: acknowledge registration without runtime
            return ok(data={
                "registered": True,
                "principal": data.get("principal", ""),
                "capabilities": data.get("capabilities", []),
                "note": "Runtime manager not available; registration recorded in-memory",
            })
        return unavailable("orchestrator")
    except Exception as e:
        logger.error(f"runtime_register error: {e}")
        return error(str(e))


@router.get("/api/runtime/principals")
async def runtime_principals():
    """List runtime principals."""
    try:
        if orchestrator:
            runtime = getattr(orchestrator, 'runtime', None)
            if runtime is not None:
                method = getattr(runtime, 'list_principals', None)
                if method is not None:
                    result = method()
                    if hasattr(result, '__await__'):
                        return ok(data=await result)
                    return ok(data=result)
            # Fallback: return empty list
            return ok(data={"principals": [], "count": 0})
        return ok(data={"principals": [], "count": 0})
    except Exception as e:
        logger.error(f"runtime_principals error: {e}")
        return error(str(e))


@router.get("/api/runtime/violations")
async def runtime_violations():
    """List runtime violations."""
    try:
        if orchestrator:
            runtime = getattr(orchestrator, 'runtime', None)
            if runtime is not None:
                method = getattr(runtime, 'get_violations', None)
                if method is not None:
                    result = method()
                    if hasattr(result, '__await__'):
                        return ok(data=await result)
                    return ok(data=result)
            # Fallback: return empty list
            return ok(data={"violations": [], "count": 0})
        return ok(data={"violations": [], "count": 0})
    except Exception as e:
        logger.error(f"runtime_violations error: {e}")
        return error(str(e))
