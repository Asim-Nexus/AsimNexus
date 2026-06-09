"""
STATUS: REAL — Core permission matrix for mode-based access control.

ASIMNEXUS Permission Matrix
============================
Provides mode-aware agent and tool permission checks for the Context Router.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("PermissionMatrix")


class PermissionMatrix:
    """
    Mode-aware permission matrix that determines which agents and tools
    are allowed in each operating mode (EMPIRE, GUARDIAN, etc.).

    Enforces MVP boundaries by checking agent and tool permissions
    against the active mode configuration.
    """

    def __init__(self, available_modes: Dict[str, Any]):
        """
        Initialize permission matrix with available mode configurations.

        Args:
            available_modes: Dict mapping mode names to ModeContext objects
                            (from context_router) or dicts with 'active_agents'
                            and 'active_tools' keys.
        """
        self.modes: Dict[str, Any] = {}
        for mode_name, config in available_modes.items():
            # Handle both ModeContext objects (from context_router) and plain dicts
            if hasattr(config, "active_agents"):
                # ModeContext or any object with active_agents attribute
                self.modes[mode_name] = config
            elif isinstance(config, dict):
                # Create a simple namespace object
                from types import SimpleNamespace
                mode_obj = SimpleNamespace(
                    name=mode_name,
                    active_agents=config.get("active_agents", []),
                    active_tools=config.get("active_tools", []),
                    dharma_rules=config.get("dharma_rules", []),
                    data_access=config.get("data_access", "unknown"),
                )
                self.modes[mode_name] = mode_obj
        logger.info(f"PermissionMatrix initialized with {len(self.modes)} modes")

    def is_agent_allowed(self, mode_name: str, agent_name: str) -> bool:
        """
        Check if an agent is permitted in the given mode.

        Args:
            mode_name: The operating mode to check (e.g., 'EMPIRE', 'GUARDIAN').
            agent_name: The agent name to check permission for.

        Returns:
            True if the agent is allowed in the mode, False otherwise.
        """
        mode = self.modes.get(mode_name)
        if not mode:
            logger.warning(f"Mode '{mode_name}' not found in permission matrix")
            return False
        allowed = agent_name in mode.active_agents
        if not allowed:
            logger.debug(f"Agent '{agent_name}' not allowed in mode '{mode_name}'")
        return allowed

    def is_tool_allowed(self, mode_name: str, tool_name: Optional[str]) -> bool:
        """
        Check if a tool is permitted in the given mode.

        Args:
            mode_name: The operating mode to check (e.g., 'EMPIRE', 'GUARDIAN').
            tool_name: The tool name to check permission for. If None, returns True.

        Returns:
            True if the tool is allowed (or no tool specified), False otherwise.
        """
        if tool_name is None:
            return True
        mode = self.modes.get(mode_name)
        if not mode:
            logger.warning(f"Mode '{mode_name}' not found in permission matrix")
            return False
        allowed = tool_name in mode.active_tools
        if not allowed:
            logger.debug(f"Tool '{tool_name}' not allowed in mode '{mode_name}'")
        return allowed

    def get_allowed_agents(self, mode_name: str) -> List[str]:
        """Get all agents allowed in a given mode."""
        mode = self.modes.get(mode_name)
        return list(mode.active_agents) if mode else []

    def get_allowed_tools(self, mode_name: str) -> List[str]:
        """Get all tools allowed in a given mode."""
        mode = self.modes.get(mode_name)
        return list(mode.active_tools) if mode else []

    def get_mode_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all modes and their permissions."""
        return {
            name: {
                "agents": list(mode.active_agents),
                "tools": list(mode.active_tools),
                "dharma_rules": list(mode.dharma_rules),
                "data_access": mode.data_access,
            }
            for name, mode in self.modes.items()
        }
