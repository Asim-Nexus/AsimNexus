# core/policy/policy_engine.py
# AsimNexus — Policy Engine: Role-based Access Control

from typing import Dict, Tuple
from core.policy.permissions import PermissionsVerifier

class PolicyEngine:
    """
    AsimNexus Policy Engine — Role-based access control + action validation.
    Enforces rules based on mode (citizen/company/government) backed by database/policies/rules.json.
    """

    def __init__(self):
        self.verifier = PermissionsVerifier()

    async def check(self, user_id: str, action: str, mode: str) -> Tuple[bool, str]:
        """
        Check if action is allowed for a given user mode.
        Returns (allowed: bool, reason: str).
        """
        if mode not in self.verifier.policies:
            mode = "citizen"  # degrade to lowest privilege mode
            
        allowed = self.verifier.verify_action(action, mode)
        if not allowed:
            return False, f"Action '{action}' is not allowed in '{mode}' mode."
            
        return True, "OK"

    async def check_action(self, user_id: str, action: str, mode: str) -> Tuple[bool, str]:
        """Alias for check to support multiple backend formats."""
        return await self.check(user_id, action, mode)
