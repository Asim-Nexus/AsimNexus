"""
AsimNexus — Context Router
===========================
Mode-based context routing system for the MVP framework.
Manages operational modes and agent permissions.
"""

import threading
from typing import Dict, List, Optional, Any

# Available modes
MODES = {
    "EMPIRE": {
        "description": "Full system control mode",
        "allowed_agents": ["economy_agent", "health_agent", "schedule_agent", "admin_agent"],
    },
    "GUARDIAN": {
        "description": "Security-focused mode",
        "allowed_agents": ["health_agent", "security_agent"],
    },
    "CREATOR": {
        "description": "Development and creation mode",
        "allowed_agents": ["economy_agent", "schedule_agent"],
    },
}

# Tool-level permission matrix: maps agent -> allowed tools
# If an agent is not listed, all tools are allowed (subject to mode check)
TOOL_PERMISSIONS = {
    "health_agent": ["health_data", "patient_record", "vital_signs"],
    "economy_agent": ["budget", "finance", "transaction"],
    "schedule_agent": ["calendar", "appointment"],
    "security_agent": ["security_scan", "access_log"],
}


class ContextRouter:
    """Mode-based context router for managing operational modes."""

    def __init__(self):
        self._lock = threading.Lock()
        self._mode = "EMPIRE"
        self._mode_history: List[str] = []

    def get_mode(self) -> Dict[str, Any]:
        """Get the current operational mode."""
        with self._lock:
            mode_info = MODES.get(self._mode, {})
            return {
                "mode": self._mode,
                "description": mode_info.get("description", ""),
                "allowed_agents": mode_info.get("allowed_agents", []),
            }

    def set_mode(self, mode: str) -> bool:
        """Set the operational mode."""
        if mode not in MODES:
            return False
        with self._lock:
            self._mode_history.append(self._mode)
            self._mode = mode
        return True

    def is_agent_allowed(self, agent_name: str) -> bool:
        """Check if an agent is allowed in the current mode."""
        with self._lock:
            mode_info = MODES.get(self._mode, {})
            return agent_name in mode_info.get("allowed_agents", [])

    def route_request(self, agent_name: str, request: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route a request to an agent if allowed in the current mode.
        
        Args:
            agent_name: Name of the agent to route to.
            request: The request string.
            metadata: Optional metadata (e.g., {"tool": "code_edit"}).
            
        Returns:
            Dict with routing result.
            
        Raises:
            PermissionError: If the agent is not allowed in the current mode
                            or the requested tool is not permitted for this agent.
        """
        if not self.is_agent_allowed(agent_name):
            raise PermissionError(f"Agent '{agent_name}' not allowed in mode '{self._mode}'")
        
        # Check tool-level permissions
        if metadata and "tool" in metadata:
            tool = metadata["tool"]
            allowed_tools = TOOL_PERMISSIONS.get(agent_name)
            if allowed_tools is not None and tool not in allowed_tools:
                raise PermissionError(
                    f"Tool '{tool}' not allowed for agent '{agent_name}' in mode '{self._mode}'"
                )
        
        return {
            "allowed": True,
            "status": "routed",
            "agent": agent_name,
            "mode": self._mode,
            "request": request,
            "metadata": metadata or {},
        }
    
    def get_mode_history(self) -> List[str]:
        """Get the mode change history."""
        with self._lock:
            return list(self._mode_history)


# Singleton
_context_router: Optional[ContextRouter] = None
_context_router_lock = threading.Lock()


def initialize_context_router() -> ContextRouter:
    """Initialize the context router singleton (resets state)."""
    global _context_router
    with _context_router_lock:
        _context_router = ContextRouter()
    return _context_router


def get_context_router() -> ContextRouter:
    """Get the context router singleton."""
    global _context_router
    if _context_router is None:
        return initialize_context_router()
    return _context_router


def reset_context_router() -> None:
    """Reset the singleton (for testing)."""
    global _context_router
    with _context_router_lock:
        _context_router = None
