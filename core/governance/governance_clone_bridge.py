"""
Governance Clone Bridge
=======================
Bridge between governance decisions and clone system operations.
"""

import logging

logger = logging.getLogger(__name__)

_instance = None


class GovernanceCloneBridge:
    """Bridge for governance decisions to be executed via the clone system."""

    def __init__(self):
        self._decisions = []
        self._history = []

    def submit_decision(self, title: str, description: str, sector: str = "public",
                        urgency: str = "normal") -> dict:
        """Submit a governance decision to the bridge."""
        import uuid
        decision = {
            "decision_id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "sector": sector,
            "urgency": urgency,
            "status": "submitted",
        }
        self._decisions.append(decision)
        self._history.append(decision)
        return decision

    def get_history(self, limit: int = 10) -> list:
        """Get bridge decision history."""
        return self._history[-limit:] if self._history else []

    def get_stats(self) -> dict:
        """Get bridge statistics."""
        return {
            "total_decisions": len(self._decisions),
            "total_history": len(self._history),
        }


def get_governance_clone_bridge() -> GovernanceCloneBridge:
    """Get or create the singleton GovernanceCloneBridge instance."""
    global _instance
    if _instance is None:
        _instance = GovernanceCloneBridge()
    return _instance


def reset_governance_clone_bridge() -> None:
    """Reset the singleton for testing."""
    global _instance
    _instance = None
