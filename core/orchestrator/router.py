# core/orchestrator/router.py
# AsimNexus — Agent and Tool Router

from typing import Dict, Any

class Router:
    """
    Router — Routes the step requests to the correct agent executor.
    """
    
    def route(self, step: Dict[str, Any], agents: Dict[str, Any]) -> Any:
        agent_name = step.get("agent")
        agent = agents.get(agent_name)
        return agent
