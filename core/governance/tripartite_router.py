"""
Tripartite Router
=================
Routes requests between Government (51%), Company (49%), and Citizen (Local-First) systems.
"""

from enum import Enum
import logging

logger = logging.getLogger(__name__)

_instance = None


class OperationMode(Enum):
    """Operational modes for tripartite routing."""
    GOVERNMENT = "government"
    COMPANY = "company"
    CITIZEN = "citizen"
    CONSENSUS = "consensus"


class RoutingDecision:
    """Result of a routing decision."""

    def __init__(self, mode: OperationMode, target: str, confidence: float = 1.0):
        self.mode = mode
        self.target = target
        self.confidence = confidence


class TripartiteRouter:
    """Routes requests between Government, Company, and Citizen systems."""

    def __init__(self):
        self._routes = {
            "tax": OperationMode.GOVERNMENT,
            "regulation": OperationMode.GOVERNMENT,
            "commerce": OperationMode.COMPANY,
            "employment": OperationMode.COMPANY,
            "identity": OperationMode.CITIZEN,
            "personal_data": OperationMode.CITIZEN,
        }

    async def route_request(self, action: str, category: str) -> RoutingDecision:
        """Route a request to the appropriate system based on category."""
        mode = self._routes.get(category, OperationMode.CONSENSUS)
        return RoutingDecision(mode=mode, target=f"{mode.value}_{action}")

    def status(self) -> dict:
        """Get router status."""
        return {
            "modes": [m.value for m in OperationMode],
            "routes_configured": len(self._routes),
        }

    def get_stats(self) -> dict:
        """Get router statistics."""
        return {
            "routes_configured": len(self._routes),
            "modes": [m.value for m in OperationMode],
        }


def get_tripartite_router() -> TripartiteRouter:
    """Get or create the singleton TripartiteRouter instance."""
    global _instance
    if _instance is None:
        _instance = TripartiteRouter()
    return _instance


def reset_tripartite_router() -> None:
    """Reset the singleton for testing."""
    global _instance
    _instance = None
