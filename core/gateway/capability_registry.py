import re
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

class RiskTier(Enum):
    LOW = "LOW"             # Read-only, safe, auto-allow
    MEDIUM = "MEDIUM"       # Policy check + soft confirm
    HIGH = "HIGH"           # Hard block + human signature
    CRITICAL = "CRITICAL"   # Extreme sensitivity (e.g., modifying .env, core system changes)

@dataclass
class Capability:
    id: str
    base_risk: RiskTier
    description: str
    allowed_patterns: List[str] = field(default_factory=list)  # Regex patterns for allowed targets

class CapabilityRegistry:
    """
    AsimNexus Policy Gateway: Capability Registry
    Operates on a DEFAULT-DENY model. If a capability isn't registered, it cannot be executed.
    """
    
    def __init__(self):
        # Default Deny: Empty registry initially
        self._capabilities: Dict[str, Capability] = {}
        self._register_default_capabilities()

    def _register_default_capabilities(self):
        """Register the baseline allowlist for the system."""
        # ─── Core AsimNexus Capabilities ────────────────────────────────────
        self.register(Capability(
            id="fs:read",
            base_risk=RiskTier.LOW,
            description="Read files from the workspace",
            allowed_patterns=[r"^/workspace/.*", r"^c:/AsimNexus/.*", r"^/data/.*"]
        ))
        self.register(Capability(
            id="fs:write",
            base_risk=RiskTier.HIGH,
            description="Write or modify files in the workspace",
            allowed_patterns=[r"^/workspace/.*", r"^c:/AsimNexus/.*", r"^/data/.*"]
        ))
        self.register(Capability(
            id="sys:exec",
            base_risk=RiskTier.HIGH,
            description="Execute terminal commands",
            allowed_patterns=[r"^ls", r"^cat", r"^echo", r"^python run_tests.py"]
        ))
        self.register(Capability(
            id="net:http",
            base_risk=RiskTier.MEDIUM,
            description="Make outbound HTTP requests",
            allowed_patterns=[r"^https://api\.asim-nexus\.ai/.*", r"^https://[a-zA-Z0-9.-]+\.gov/.*"]
        ))
        self.register(Capability(
            id="net:email_send",
            base_risk=RiskTier.HIGH,
            description="Send outbound emails",
            allowed_patterns=[r".*"]
        ))
        
        # ─── Memory Capabilities ────────────────────────────────────────────
        self.register(Capability(
            id="mem:read",
            base_risk=RiskTier.LOW,
            description="Read from memory/vector store",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="mem:write",
            base_risk=RiskTier.MEDIUM,
            description="Write to memory/vector store",
            allowed_patterns=[r".*"]
        ))
        
        # ─── Agent Control Capabilities ─────────────────────────────────────
        self.register(Capability(
            id="agent:control",
            base_risk=RiskTier.HIGH,
            description="Control agent behavior, tasks, and skills",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="agent:deploy",
            base_risk=RiskTier.CRITICAL,
            description="Deploy new agents or modify agent code",
            allowed_patterns=[r".*"]
        ))
        
        # ─── Configuration Capabilities ─────────────────────────────────────
        self.register(Capability(
            id="config:read",
            base_risk=RiskTier.LOW,
            description="Read configuration settings",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="config:write",
            base_risk=RiskTier.CRITICAL,
            description="Modify configuration settings",
            allowed_patterns=[r".*"]
        ))
        
        # ─── Identity & Auth Capabilities ───────────────────────────────────
        self.register(Capability(
            id="auth:manage",
            base_risk=RiskTier.CRITICAL,
            description="Manage users, roles, and permissions",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="auth:read",
            base_risk=RiskTier.MEDIUM,
            description="Read user/role information",
            allowed_patterns=[r".*"]
        ))
        
        # ─── Mesh Network Capabilities ──────────────────────────────────────
        self.register(Capability(
            id="mesh:connect",
            base_risk=RiskTier.MEDIUM,
            description="Connect to mesh network nodes",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="mesh:sync",
            base_risk=RiskTier.HIGH,
            description="Sync data across mesh network",
            allowed_patterns=[r".*"]
        ))
        
        # ─── Governance Capabilities ────────────────────────────────────────
        self.register(Capability(
            id="gov:policy_read",
            base_risk=RiskTier.LOW,
            description="Read governance policies",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="gov:policy_write",
            base_risk=RiskTier.CRITICAL,
            description="Modify governance policies",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="gov:veto",
            base_risk=RiskTier.CRITICAL,
            description="Execute Dharma Veto",
            allowed_patterns=[r".*"]
        ))
        
        # ─── Data Lake Capabilities ─────────────────────────────────────────
        self.register(Capability(
            id="datalake:ingest",
            base_risk=RiskTier.HIGH,
            description="Ingest data into the Data Lake",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="datalake:query",
            base_risk=RiskTier.LOW,
            description="Query the Data Lake",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="datalake:verify",
            base_risk=RiskTier.MEDIUM,
            description="Verify Data Lake records",
            allowed_patterns=[r".*"]
        ))
        
        # ─── Hardware Control Capabilities ──────────────────────────────────
        self.register(Capability(
            id="hw:status",
            base_risk=RiskTier.LOW,
            description="Read hardware status",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="hw:control",
            base_risk=RiskTier.CRITICAL,
            description="Control hardware devices",
            allowed_patterns=[r".*"]
        ))
        self.register(Capability(
            id="hw:driver",
            base_risk=RiskTier.CRITICAL,
            description="Manage hardware drivers",
            allowed_patterns=[r".*"]
        ))

    def register(self, capability: Capability):
        """Register a new capability in the allowlist."""
        self._capabilities[capability.id] = capability

    def evaluate_risk(self, capability_id: str, target: str) -> RiskTier:
        """
        Evaluate the risk tier of a request based on the capability and the context (target).
        Includes Context-Based Escalation.
        """
        if capability_id not in self._capabilities:
            # Default Deny
            raise PermissionError(f"Capability '{capability_id}' is not registered or allowed.")
        
        cap = self._capabilities[capability_id]
        
        # Verify against allowed patterns (Boundary Check)
        if cap.allowed_patterns:
            matched = any(re.match(pattern, target) for pattern in cap.allowed_patterns)
            if not matched:
                raise PermissionError(f"Target '{target}' is outside the allowed boundary for {capability_id}.")

        # Context-Based Risk Escalation
        if capability_id == "fs:write":
            # Escalate if writing to sensitive configuration files
            if re.search(r"(\.env|secrets/|config/|\.ssh/|\.git/|security/.*\.py)", target):
                return RiskTier.CRITICAL
                
        if capability_id == "sys:exec":
            # Escalate if executing destructive commands
            if re.search(r"(rm -rf|mkfs|chmod -R 777|chown|format)", target):
                return RiskTier.CRITICAL

        # Return the base risk if no escalation occurred
        return cap.base_risk

    def get_capability(self, capability_id: str) -> Optional[Capability]:
        return self._capabilities.get(capability_id)

    def list_capabilities(self) -> List[Dict[str, Any]]:
        """Standardized export of all registered capabilities."""
        return [{"id": c.id, "base_risk": c.base_risk.value, "description": c.description,
                 "allowed_patterns": c.allowed_patterns} for c in self._capabilities.values()]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_capabilities": len(self._capabilities),
                "risk_distribution": {rt.value: sum(1 for c in self._capabilities.values()
                                                     if c.base_risk == rt) for rt in RiskTier}}

# Singleton instance
registry = CapabilityRegistry()
