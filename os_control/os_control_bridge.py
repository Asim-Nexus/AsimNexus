"""
ASIMNEXUS OS Control Bridge
============================
Exposes a single ``call_tool()`` async function that is the unified entry
point for every OS Control tool invocation across the ASIM ecosystem.

Consumers
---------
* ASIM kernel actions (``core/kernel/``)
* Founder clones (``core/founder_clones/``)
* Frontend OS Hub (``frontend/``)
* Any agent needing OS-level tool access

Return shape (always a dict)
-----------------------------
.. code-block:: python

    {
        "success": bool,          # True if tool ran without errors
        "result": Any,            # Tool output (present when success=True)
        "permission_denied": bool,# True if capability matrix blocked this call
        "audit_id": str,          # UUID for audit trail correlation
        "error": str | None,      # Human-readable error/denial message
        "execution_ms": float,    # Wall-clock time in milliseconds
        "verdict": str,           # "allowed" | "denied" | "error" | "pending_human"
    }

Security flow
--------------
1. Bridge receives ``(tool_id, params, agent_id)``
2. Delegates to ``OSToolExecutor.execute()``
3. Executor checks CapabilityMatrix → returns denied if blocked
4. Executor checks human confirmation → returns pending if needed
5. Executor routes through sandbox if required
6. All decisions are audit-logged to ``security/audit_log.py``
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .os_tool_executor import OSToolExecutor, get_os_tool_executor
from .tool_registry import ToolVerdict

logger = logging.getLogger("AsimNexus.OSControlBridge")


# ══════════════════════════════════════════════════════════════════════
# Bridge
# ══════════════════════════════════════════════════════════════════════

# Module-level executor reference (lazy-initialised)
_executor: Optional[OSToolExecutor] = None


def _get_executor() -> OSToolExecutor:
    """Return the singleton executor, initialising on first call."""
    global _executor
    if _executor is None:
        _executor = get_os_tool_executor()
    return _executor


async def call_tool(
    tool_id: str,
    params: Dict[str, Any],
    agent_id: str = "AutoModeAgent",
) -> Dict[str, Any]:
    """
    Execute an OS Control tool with full security gating.

    Parameters
    ----------
    tool_id : str
        Tool identifier, e.g. ``"file.read"``, ``"clipboard.write"``,
        ``"system.cpu"``, ``"notification.send"``.
    params : dict
        Keyword arguments passed to the tool implementation.
    agent_id : str
        Name of the agent requesting execution. Used for capability
        lookups against the CapabilityMatrix. Default ``"AutoModeAgent"``.

    Returns
    -------
    dict
        Standardised response (see module docstring for shape).
    """
    executor = _get_executor()

    try:
        response = await executor.execute(
            tool_name=tool_id,
            parameters=params,
            agent_name=agent_id,
            user_id=agent_id,  # bridge uses agent_id as user_id
        )
    except Exception as exc:
        logger.exception(
            f"🚨 Bridge: unhandled exception calling tool '{tool_id}' "
            f"for agent '{agent_id}': {exc}"
        )
        return {
            "success": False,
            "result": None,
            "permission_denied": False,
            "audit_id": "error",
            "error": f"Bridge internal error: {exc}",
            "execution_ms": 0,
            "verdict": ToolVerdict.ERROR.value,
        }

    verdict = response.get("verdict", ToolVerdict.ERROR.value)
    call_id = response.get("call_id", "unknown")

    # Map executor response to bridge contract
    bridge_response: Dict[str, Any] = {
        "success": verdict == ToolVerdict.ALLOWED.value,
        "result": response.get("output"),
        "permission_denied": verdict == ToolVerdict.DENIED.value,
        "audit_id": call_id,
        "error": response.get("error"),
        "execution_ms": response.get("execution_ms", 0),
        "verdict": verdict,
    }

    # Include human_confirmation details when pending
    if verdict == ToolVerdict.PENDING_HUMAN.value:
        bridge_response["requires_human"] = True
        bridge_response["risk_level"] = response.get("risk_level")
        bridge_response["agent"] = response.get("agent")

    # Include sandbox details when applicable
    if response.get("sandboxed"):
        bridge_response["sandboxed"] = True
        bridge_response["container_id"] = (
            response.get("output", {}).get("container_id")
            if isinstance(response.get("output"), dict)
            else None
        )

    logger.info(
        f"🔧 Bridge: tool='{tool_id}' agent='{agent_id}' "
        f"verdict={verdict} call_id={call_id}"
    )
    return bridge_response


async def call_tool_sync(
    tool_id: str,
    params: Dict[str, Any],
    agent_id: str = "AutoModeAgent",
) -> Dict[str, Any]:
    """
    Synchronous wrapper around :func:`call_tool` for callers that cannot
    use ``await`` directly (e.g. some frontend event handlers).

    Usage::

        result = call_tool_sync("system.info", {})
    """
    return await call_tool(tool_id=tool_id, params=params, agent_id=agent_id)


def get_available_tools() -> list:
    """
    Return a list of all registered tools with their metadata, suitable
    for driving the Frontend OS Hub "available tools" display.

    Each entry::

        {
            "tool_id": str,
            "description": str,
            "risk_level": str,
            "required_capabilities": [str, ...],
            "requires_confirmation": bool,
        }
    """
    executor = _get_executor()
    tools = []
    for reg in executor.tool_registry.list_tools():
        tools.append({
            "tool_id": reg.tool_id,
            "description": reg.description,
            "risk_level": reg.risk_level.value,
            "required_capabilities": [c.value for c in reg.required_capabilities],
            "requires_confirmation": reg.requires_confirmation,
        })
    return tools
