
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Context Router
=========================
Provides mode-based routing decisions, active-agent enforcement,
and EMPIRE/GUARDIAN policy enforcement for MVP.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from core.event_bus import event_bus, EventType
from core.permission_matrix import PermissionMatrix
from config.mvp_definition import MVP_MODES

logger = logging.getLogger("ContextRouter")


@dataclass
class ModeContext:
    name: str
    active_agents: List[str]
    active_tools: List[str]
    dharma_rules: List[str]
    data_access: str


class ContextRouter:
    """Mode-aware context router for MVP enforcement."""

    def __init__(self):
        self.logger = logging.getLogger("ContextRouter")
        self.available_modes = self._load_modes()
        self.permission_matrix = PermissionMatrix(self.available_modes)
        self.current_mode = "EMPIRE" if "EMPIRE" in self.available_modes else next(iter(self.available_modes), "EMPIRE")
        self.history: List[Dict[str, Any]] = []
        self._publish_state_change("initialized", self.current_mode)

    def _load_modes(self) -> Dict[str, ModeContext]:
        modes: Dict[str, ModeContext] = {}
        for mode_name, config in MVP_MODES.items():
            modes[mode_name] = ModeContext(
                name=mode_name,
                active_agents=config.get("active_agents", []),
                active_tools=config.get("active_tools", []),
                dharma_rules=config.get("dharma_rules", []),
                data_access=config.get("data_access", "unknown")
            )
        return modes

    def set_mode(self, mode_name: str) -> bool:
        if mode_name not in self.available_modes:
            self.logger.error(f"Mode not recognized: {mode_name}")
            return False

        old_mode = self.current_mode
        self.current_mode = mode_name
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "from": old_mode,
            "to": mode_name,
        })
        self._publish_state_change("mode_changed", {"from": old_mode, "to": mode_name})
        self.logger.info(f"ContextRouter switched mode from {old_mode} to {mode_name}")
        return True

    def get_mode(self) -> Dict[str, Any]:
        mode = self.available_modes.get(self.current_mode)
        return {
            "mode": self.current_mode,
            "active_agents": mode.active_agents if mode else [],
            "active_tools": mode.active_tools if mode else [],
            "dharma_rules": mode.dharma_rules if mode else [],
            "data_access": mode.data_access if mode else "unknown",
            "history": list(self.history[-10:])
        }

    def get_active_agents(self) -> List[str]:
        mode = self.available_modes.get(self.current_mode)
        return mode.active_agents if mode else []

    def is_agent_allowed(self, agent_name: str) -> bool:
        return self.permission_matrix.is_agent_allowed(self.current_mode, agent_name)

    def is_tool_allowed(self, tool_name: Optional[str]) -> bool:
        return self.permission_matrix.is_tool_allowed(self.current_mode, tool_name)

    def route_request(self, agent_name: str, request: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.is_agent_allowed(agent_name):
            reason = f"Agent '{agent_name}' is not permitted in mode '{self.current_mode}'"
            self.logger.warning(reason)
            self._publish_state_change("route_rejected", {"agent": agent_name, "reason": reason})
            raise PermissionError(reason)

        metadata = metadata or {}
        tool_name = metadata.get("tool")
        if tool_name is not None and not self.is_tool_allowed(tool_name):
            reason = f"Tool '{tool_name}' is not permitted in mode '{self.current_mode}'"
            self.logger.warning(reason)
            self._publish_state_change("route_rejected", {"agent": agent_name, "tool": tool_name, "reason": reason})
            raise PermissionError(reason)

        decision = {
            "agent": agent_name,
            "request": request,
            "mode": self.current_mode,
            "allowed": True,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata,
        }
        self._publish_state_change("route_accepted", decision)
        return decision

    def _publish_state_change(self, event_tag: str, payload: Any) -> None:
        try:
            coroutine = event_bus.publish_sync(
                EventType.STATE_CHANGED,
                {
                    "context_router": {
                        "event": event_tag,
                        "payload": payload,
                        "mode": self.current_mode,
                    }
                },
                source="core.context_router"
            )
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(coroutine)
            except RuntimeError:
                asyncio.run(coroutine)
        except Exception as exc:
            self.logger.debug(f"Event bus unavailable; continuing without publish: {exc}")


_context_router: Optional[ContextRouter] = None


def initialize_context_router() -> bool:
    global _context_router
    if _context_router is None:
        _context_router = ContextRouter()
    return True


def get_context_router() -> ContextRouter:
    global _context_router
    if _context_router is None:
        initialize_context_router()
    return _context_router


context_router = get_context_router()