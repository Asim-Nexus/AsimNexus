#!/usr/bin/env python3
"""
STATUS: NEW — Phase 1d Odysseus Integration
Veto Integration — Dharma Chakra constitutional guard for agent tools.

Routes every agent tool call through the Dharma Chakra veto engine for
ethical, security, and constitutional validation before execution.

The flow:
1. AgentLoop._execute_tool() calls the veto hook
2. Veto hook calls check_tool(tool_name, tool_args, user_id, clone_id)
3. check_tool() queries Dharma Chakra veto_engine
4. If blocked: returns {"allowed": false, "reason": "...", "severity": "warning|critical"}
5. If allowed: returns {"allowed": true, "reason": ""}
6. For dangerous tools (bash, file_write, etc.): requires Level-2 or Level-3 confirmation

Integration with existing modules:
- core/dharma_chakra/veto_engine.py — the existing DharmaVetoEngine class
- security/power_balance_constitution.py — constitution rules
- core/reputation.py — agent reputation checks
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# ─── Tool Security Level Mapping ───────────────────────────────────────────────
# Maps each agent tool name to its constitutional security level.
# Used by VetoIntegration to determine how strictly to check each tool.

TOOL_SECURITY_MAP: Dict[str, str] = {
    # Dangerous tools — require veto + confirmation
    "execute_bash": "dangerous",
    "execute_python": "dangerous",
    "file_write": "dangerous",
    "file_edit": "dangerous",
    "file_upload": "dangerous",
    "mesh_broadcast": "dangerous",

    # Sensitive tools — require veto check
    "memory_store": "sensitive",
    "memory_search": "sensitive",
    "web_search": "sensitive",
    "web_fetch": "sensitive",
    "code_review": "sensitive",
    "mesh_send": "sensitive",

    # Secure tools — informational only
    "read_file": "secure",
    "file_read": "secure",
    "file_list": "secure",
    "file_search": "secure",
    "web_scrape": "secure",
    "memory_recall": "secure",
    "code_analyze": "secure",
    "code_format": "secure",
    "code_explain": "secure",
    "mesh_discover": "secure",
    "mesh_status": "secure",
    "list_files": "secure",
}


class VetoIntegration:
    """Bridges agent tool execution with Dharma Chakra constitution.

    Installed as a veto hook on AgentLoop so that every tool call is
    validated against the constitutional rules before being allowed to
    proceed.

    Usage:
        agent_loop = AgentLoop()
        veto = VetoIntegration()
        agent_loop.set_veto_hook(veto.check_tool)
    """

    def __init__(self, veto_engine=None, constitution=None):
        self._veto_engine = veto_engine   # from core/dharma_chakra/veto_engine.py
        self._constitution = constitution  # from security/power_balance_constitution.py
        self._fail_open = True             # When True, allow if veto_engine unavailable
        logger.info("VetoIntegration initialized (fail_open=%s)", self._fail_open)

    # ── Public API ─────────────────────────────────────────────────────────────

    async def check_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_id: str = "anonymous",
        clone_id: Optional[str] = None,
    ) -> Dict:
        """Check tool execution against Dharma Chakra constitution.

        Called by AgentLoop._check_veto() before every tool execution.

        Args:
            tool_name: Name of the tool being invoked.
            tool_args: Arguments passed to the tool.
            user_id: Identifier of the user or agent requesting the action.
            clone_id: Optional Digital Clone identifier.

        Returns:
            Dict with keys:
                allowed (bool): Whether the tool is permitted.
                reason (str): Human-readable explanation if blocked.
                severity (str): "warning" or "critical" when blocked; "" if allowed.
                level (str): Security level of the tool ("secure", "sensitive", "dangerous").
        """
        # 1. Look up security level
        level = self.get_security_level(tool_name)

        # 2. Secure tools — always allowed (no veto needed)
        if level == "secure":
            return {"allowed": True, "reason": "", "severity": "", "level": level}

        # 3. Sensitive tools — check veto engine if available
        if level == "sensitive":
            return await self._check_with_veto(tool_name, tool_args, user_id, clone_id, level)

        # 4. Dangerous tools — check veto engine AND constitution, require both
        if level == "dangerous":
            veto_result = await self._check_with_veto(
                tool_name, tool_args, user_id, clone_id, level
            )
            if not veto_result.get("allowed", True):
                return veto_result

            # Also check constitution for dangerous tools
            constitution_result = self._check_constitution(
                tool_name, tool_args, user_id
            )
            if not constitution_result.get("allowed", True):
                return constitution_result

            return veto_result

        # 5. Unknown tool — default to veto check (conservative)
        logger.warning("Unknown tool security level for '%s'; defaulting to veto check", tool_name)
        return await self._check_with_veto(tool_name, tool_args, user_id, clone_id, "sensitive")

    # ── Internal Checks ────────────────────────────────────────────────────────

    async def _check_with_veto(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_id: str,
        clone_id: Optional[str],
        level: str,
    ) -> Dict:
        """Check tool against DharmaVetoEngine.

        Returns:
            Dict with allowed, reason, severity, level.
        """
        if self._veto_engine is None:
            if self._fail_open:
                logger.warning(
                    "No veto engine set — allowing '%s' (fail-open). "
                    "Set veto_engine via set_veto_engine() or configure ASIM_VETO_FAIL_CLOSED.",
                    tool_name,
                )
                return {"allowed": True, "reason": "", "severity": "", "level": level}
            logger.error(
                "No veto engine set and fail_open=False — blocking '%s'",
                tool_name,
            )
            return {
                "allowed": False,
                "reason": "Veto engine unavailable (fail-closed mode)",
                "severity": "critical",
                "level": level,
            }

        try:
            # Build a message for the veto engine from tool_name + args
            message = self._build_veto_message(tool_name, tool_args)

            # Determine sector from tool context
            sector = tool_args.get("sector", "general")

            # Run the Dharma Chakra check (synchronous under the hood)
            result = self._veto_engine.check(
                message=message,
                sector=sector,
                agent_id=user_id,
                context={"tool_name": tool_name, "tool_args": tool_args},
            )

            if result.allowed:
                return {"allowed": True, "reason": "", "severity": "", "level": level}

            return {
                "allowed": False,
                "reason": result.reason,
                "severity": "critical" if result.level.name == "BLOCK" else "warning",
                "level": level,
            }

        except Exception as e:
            logger.error("Veto engine check failed for '%s': %s", tool_name, e)
            if self._fail_open:
                return {"allowed": True, "reason": "", "severity": "", "level": level}
            return {
                "allowed": False,
                "reason": f"Veto engine error: {e}",
                "severity": "critical",
                "level": level,
            }

    def _check_constitution(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_id: str,
    ) -> Dict:
        """Check tool against PowerBalanceConstitution for dangerous tools.

        Returns:
            Dict with allowed, reason, severity, level.
        """
        if self._constitution is None:
            return {"allowed": True, "reason": "", "severity": "", "level": "dangerous"}

        try:
            sector = tool_args.get("sector", "general")
            is_public = tool_args.get("is_public_decision", False)
            weight = tool_args.get("decision_weight", 1.0)

            balance_result = self._constitution.check_decision(
                sector=sector,
                is_public_decision=is_public,
                weight=weight,
                context={"tool_name": tool_name, "agent_id": user_id},
            )

            if balance_result.verdict.name == "BLOCK":
                return {
                    "allowed": False,
                    "reason": f"Constitution blocked: {balance_result.message}",
                    "severity": "critical",
                    "level": "dangerous",
                }

            return {"allowed": True, "reason": "", "severity": "", "level": "dangerous"}

        except Exception as e:
            logger.error("Constitution check failed for '%s': %s", tool_name, e)
            return {"allowed": True, "reason": "", "severity": "", "level": "dangerous"}

    # ── Helpers ────────────────────────────────────────────────────────────────

    def get_security_level(self, tool_name: str) -> str:
        """Get the constitutional security level for a tool.

        Args:
            tool_name: Name of the tool.

        Returns:
            "dangerous", "sensitive", or "secure". Defaults to "sensitive" for
            unknown tools.
        """
        return TOOL_SECURITY_MAP.get(tool_name, "sensitive")

    def _build_veto_message(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Build a human-readable message describing the tool action.

        Used as input to the DharmaVetoEngine pattern matcher.
        """
        args_summary = ", ".join(
            f"{k}={v}" for k, v in tool_args.items()
            if not isinstance(v, (bytes, bytearray))
        )
        return f"Execute tool '{tool_name}' with arguments: {args_summary}"

    # ── Configuration ──────────────────────────────────────────────────────────

    def set_veto_engine(self, engine):
        """Set the Dharma Chakra veto engine instance.

        Args:
            engine: A DharmaVetoEngine instance (duck-typed; must have
                    a ``.check(message, sector, agent_id, context)`` method).
        """
        self._veto_engine = engine
        logger.info("Veto engine registered with VetoIntegration")

    def set_constitution(self, constitution):
        """Set the power balance constitution instance.

        Args:
            constitution: A PowerBalanceConstitution instance (duck-typed; must have
                          a ``.check_decision(sector, is_public_decision, weight, context)`` method).
        """
        self._constitution = constitution
        logger.info("Constitution registered with VetoIntegration")

    def set_fail_open(self, fail_open: bool):
        """Configure fail-open vs fail-closed behaviour.

        When True (default): if the veto engine is unavailable, tools are
        allowed through with a warning. Set to False for production deployments
        where blocked tools must stay blocked if the engine is down.
        """
        self._fail_open = fail_open
        logger.info("VetoIntegration fail_open=%s", fail_open)


# ─── Factory ────────────────────────────────────────────────────────────────────

async def create_default_veto_hook(
    veto_engine=None,
    constitution=None,
    fail_open: bool = True,
) -> Callable:
    """Factory that creates a properly wired default veto hook.

    Attempts to import the standard DharmaVetoEngine and PowerBalanceConstitution
    singletons if no explicit instances are provided.  Gracefully degrades if
    imports are unavailable (useful for development / offline scenarios).

    Args:
        veto_engine: Optional DharmaVetoEngine instance.  If None, attempts to
                     load via ``core.dharma_chakra.veto_engine.get_veto_engine``.
        constitution: Optional PowerBalanceConstitution instance.  If None,
                      attempts to load via
                      ``security.power_balance_constitution.get_power_balance``.
        fail_open: Whether to allow tools when the veto engine is down.

    Returns:
        An async callable ``(tool_name, tool_args, user_id, clone_id=None) -> dict``
        suitable for passing to ``AgentLoop.set_veto_hook()``.
    """
    integration = VetoIntegration(veto_engine=None, constitution=None)
    integration.set_fail_open(fail_open)

    # Try to wire up the veto engine
    if veto_engine is not None:
        integration.set_veto_engine(veto_engine)
    else:
        try:
            from core.dharma_chakra.veto_engine import get_veto_engine
            integration.set_veto_engine(get_veto_engine())
            logger.info("Auto-wired DharmaVetoEngine singleton")
        except ImportError:
            logger.warning(
                "DharmaVetoEngine not available — veto checks disabled. "
                "Install core.dharma_chakra or pass veto_engine explicitly."
            )
        except Exception as e:
            logger.warning("Failed to load DharmaVetoEngine: %s", e)

    # Try to wire up the constitution
    if constitution is not None:
        integration.set_constitution(constitution)
    else:
        try:
            from security.power_balance_constitution import get_power_balance
            integration.set_constitution(get_power_balance())
            logger.info("Auto-wired PowerBalanceConstitution singleton")
        except ImportError:
            logger.info(
                "PowerBalanceConstitution not available — "
                "constitution checks will be skipped for dangerous tools."
            )
        except Exception as e:
            logger.warning("Failed to load PowerBalanceConstitution: %s", e)

    return integration.check_tool


# ─── Module Exports ─────────────────────────────────────────────────────────────

__all__ = [
    "TOOL_SECURITY_MAP",
    "VetoIntegration",
    "create_default_veto_hook",
]
