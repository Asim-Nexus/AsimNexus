# core/agents/base_agent.py
# AsimNexus — Base Agent Class

from abc import ABC, abstractmethod
from typing import Dict

class BaseAgent(ABC):
    """
    Abstract Base Class for all domain-specific agents in AsimNexus.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, tool: str, params: Dict, user_id: str, mode: str) -> Dict:
        """
        Executes a specific action/tool on behalf of the user.
        """
        pass
