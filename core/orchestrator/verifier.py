# core/orchestrator/verifier.py
# AsimNexus — Plan Verifier

from typing import Dict

class Verifier:
    """
    Verifier — Basic plan verification.
    """
    
    async def verify(self, plan: Dict) -> bool:
        steps = plan.get("steps", [])
        if not steps:
            return False
        for step in steps:
            if not step.get("agent") or not step.get("action"):
                return False
        return True
