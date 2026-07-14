# core/policy/permissions.py
# AsimNexus — Role Permissions Verifier

import json
import os

class PermissionsVerifier:
    """
    PermissionsVerifier — Checks individual actions against JSON role rules.
    """
    
    def __init__(self):
        self.rules_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "database", "policies", "rules.json"
        )
        self.policies = self._load_policies()

    def _load_policies(self):
        if not os.path.exists(self.rules_path):
            return {}
        try:
            with open(self.rules_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def reload(self):
        self.policies = self._load_policies()

    def verify_action(self, action: str, mode: str) -> bool:
        mode_policy = self.policies.get(mode)
        if not mode_policy:
            return False
            
        # Check forbidden first
        if action in mode_policy.get("forbidden_actions", []):
            return False
            
        # Check allowed
        if action in mode_policy.get("allowed_actions", []):
            return True
            
        return False

