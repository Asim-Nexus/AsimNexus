"""
AsimNexus MCP (Dharma-Gated) Route Module
===========================================
MCP tool management, approval, rejection, audit, and status.
"""

import logging
from fastapi import APIRouter, Body, HTTPException
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.MCP")

router = APIRouter(tags=["MCP"])

# Module-level globals (set via init_mcp)
_mcp = None


def init_mcp(app_globals: dict) -> None:
    """Initialize MCP router with shared application globals."""
    global _mcp
    _mcp = app_globals.get("_mcp")


# ──────────────────────────────────────────────
#  MCP Tool Endpoints
# ──────────────────────────────────────────────


@router.get("/api/mcp/tools")
async def mcp_list_tools():
    """List all registered Dharma-Gated MCP tools."""
    if not _mcp:
        return ok(data={"tools": [], "status": "mcp_unavailable"})
    return ok(data={
        "tools": _mcp.list_tools(),
        "total": len(_mcp.list_tools()),
        "dharma_gated": True,
        "layers": ["dharma_veto", "delta_t_check", "final3_confirmation", "audit_log"],
    })


@router.post("/api/mcp/call")
async def mcp_call(data: dict = Body(...)):
    """
    Execute a Dharma-Gated MCP tool call.
    Body: { tool_name, parameters, context }
    """
    if not _mcp:
        raise HTTPException(status_code=503, detail="DharmaMCP Server not available")
    user_id = data.get("user_id", "web_user") or "guest"
    tool_name = data.get("tool_name", "")
    parameters = data.get("parameters", {})
    context = data.get("context", "")
    if not tool_name:
        raise HTTPException(status_code=400, detail="tool_name required")
    # Always inject user_id into parameters for sandboxing
    parameters["user_id"] = user_id
    result = await _mcp.call(tool_name, parameters, user_id=user_id, context=context)
    return ok(data={
        "call_id": result.call_id,
        "tool_name": result.tool_name,
        "verdict": result.verdict.value,
        "output": result.output,
        "error": result.error,
        "veto_reason": result.veto_reason,
        "requires_human": result.requires_human,
        "execution_ms": result.execution_ms,
        "dharma_score": result.dharma_score,
        "audit_hash": result.audit_hash,
    })


@router.post("/api/mcp/approve/{call_id}")
async def mcp_approve(call_id: str, data: dict = Body(...)):
    """Human approves a pending Final-3 MCP call."""
    if not _mcp:
        raise HTTPException(status_code=503, detail="DharmaMCP Server not available")
    user_id = data.get("user_id", "web_user")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required to approve actions")
    result = await _mcp.approve(call_id, approver_id=user_id)
    return ok(data={
        "call_id": result.call_id,
        "verdict": result.verdict.value,
        "output": result.output,
        "error": result.error,
        "approved_by": user_id,
    })


@router.post("/api/mcp/reject/{call_id}")
async def mcp_reject(call_id: str, data: dict = Body(...)):
    """Human rejects a pending Final-3 MCP call."""
    if not _mcp:
        raise HTTPException(status_code=503, detail="DharmaMCP Server not available")
    user_id = data.get("user_id", "web_user")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    result = _mcp.reject(call_id, rejecter_id=user_id)
    return ok(data={
        "call_id": result.call_id,
        "verdict": result.verdict.value,
        "rejected_by": user_id,
        "message": "Action rejected. AsimNexus respects your decision.",
    })


@router.get("/api/mcp/pending")
async def mcp_pending(data: dict = Body(...)):
    """List pending Final-3 approvals for this user."""
    if not _mcp:
        return ok(data={"pending": []})
    user_id = data.get("user_id", "web_user") or "guest"
    pending = _mcp.pending_calls(user_id=user_id)
    return ok(data={"pending": pending, "count": len(pending)})


@router.get("/api/mcp/audit")
async def mcp_audit(data: dict = Body(...), limit: int = 30):
    """Return recent audit log for this user."""
    if not _mcp:
        return ok(data={"audit": []})
    user_id = data.get("user_id", "web_user") or "guest"
    entries = _mcp.audit_log(limit=limit, user_id=user_id)
    return ok(data={"audit": entries, "total": len(entries)})


@router.get("/api/mcp/status")
async def mcp_status(data: dict = Body(...)):
    """DharmaMCP Server status."""
    if not _mcp:
        return ok(data={"status": "unavailable"})
    user_id = data.get("user_id", "web_user") or "guest"
    pending = _mcp.pending_calls(user_id=user_id)
    recent = _mcp.audit_log(limit=5, user_id=user_id)
    return ok(data={
        "status": "active",
        "dharma_gated": True,
        "tools_registered": len(_mcp._tools),
        "pending_approvals": len(pending),
        "recent_calls": len(recent),
        "layers": {
            "dharma_veto": True,
            "delta_t_engine": _mcp._dt_engine is not None,
            "final3_confirmation": True,
            "audit_log": True,
            "sandboxed_fs": True,
        },
    })
