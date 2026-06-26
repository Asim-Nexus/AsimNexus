"""AsimNexus Over-Automation Guard"""
import asyncio
from typing import Dict, Any

class OverAutomationGuard:
    def __init__(self):
        self.action_limit = 100
        self.actions_count = 0
    
    async def check_action(self, action: str, user_consent: bool = False) -> Dict[str, Any]:
        self.actions_count += 1
        if self.actions_count > self.action_limit and not user_consent:
            return {"allowed": False, "reason": "Human confirmation required"}
        return {"allowed": True}

over_automation_guard = OverAutomationGuard()
__all__ = ["OverAutomationGuard", "over_automation_guard"]
