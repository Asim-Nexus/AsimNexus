
"""
STATUS: DEPRECATED — Use core.dharma_chakra.integration.DharmaChakraIntegrator instead.

This module's functionality has been consolidated into:
  - core.dharma_chakra.veto_engine.DharmaVetoEngine  (fast veto checks)
  - core.dharma_chakra.constitution.DharmaChakraConstitution  (constitutional rules)
  - core.dharma_chakra.integration.DharmaChakraIntegrator  (unified entry point)

Importing from safety_veto is preserved temporarily for backward compatibility
but all new code should use the integration hub.
"""

"""
ASIMNEXUS Safety Veto Middleware
===============================
Dharma-Chakra Constitutional Safety System
Acts as middleware for all decisions across all layers
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
try:
    from ..agent_registry import get_agent_registry, AgentRole, Permission
except ImportError:
    get_agent_registry = None
    AgentRole = None
    Permission = None

logger = logging.getLogger("SafetyVeto")

class SafetyLevel(Enum):
    """Safety violation levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class ActionType(Enum):
    """Types of actions requiring safety approval"""
    GOVERNANCE = "governance"
    FINANCIAL = "financial"
    RESOURCE = "resource"
    SYSTEM = "system"
    HUMAN_OVERRIDE = "human_override"

@dataclass
class SafetyPolicy:
    """Individual safety policy"""
    policy_id: str
    name: str
    description: str
    action_types: List[ActionType]
    rules: List[str]
    safety_level: SafetyLevel
    immutable: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SafetyViolation:
    """Safety violation record"""
    violation_id: str
    policy_id: str
    action: str
    parameters: Dict[str, Any]
    violation_type: str
    safety_level: SafetyLevel
    blocked: bool
    timestamp: datetime = field(default_factory=datetime.now)
    resolution: Optional[str] = None

class SafetyVeto:
    """Dharma-Chakra Constitutional Safety System"""
    
    def __init__(self):
        self.logger = logging.getLogger("SafetyVeto")
        self.policies: Dict[str, SafetyPolicy] = {}
        self.violations: List[SafetyViolation] = []
        self.is_active = False
        self.human_override_enabled = True
        self.agent_registry = get_agent_registry() if get_agent_registry else None
        
        # Initialize constitutional policies
        self._initialize_constitutional_policies()
        
        self.logger.info("🛡️ ASIMNEXUS Safety Veto Initialized")
    
    def _initialize_constitutional_policies(self):
        """Initialize core constitutional safety policies"""
        
        # Policy 1: Human Override Authority
        self.policies["human_override"] = SafetyPolicy(
            policy_id="human_override",
            name="Human Override Authority",
            description="Human operators always have final authority",
            action_types=[ActionType.GOVERNANCE, ActionType.FINANCIAL, ActionType.RESOURCE],
            rules=[
                "Human commands cannot be overridden by AI",
                "Critical decisions require human approval",
                "Emergency protocols respect human intervention",
                "CEO has ultimate veto power"
            ],
            safety_level=SafetyLevel.EMERGENCY
        )
        
        # Policy 2: Resource Conservation
        self.policies["resource_conservation"] = SafetyPolicy(
            policy_id="resource_conservation",
            name="Resource Conservation Protocol",
            description="Prevent resource depletion and waste",
            action_types=[ActionType.RESOURCE, ActionType.FINANCIAL],
            rules=[
                "Energy usage cannot exceed sustainable limits",
                "Natural resources must be conserved",
                "Waste generation must be minimized",
                "Renewable resources prioritized"
            ],
            safety_level=SafetyLevel.CRITICAL
        )
        
        # Policy 3: Financial Stability
        self.policies["financial_stability"] = SafetyPolicy(
            policy_id="financial_stability",
            name="Financial Stability Guard",
            description="Maintain global financial system stability",
            action_types=[ActionType.FINANCIAL, ActionType.GOVERNANCE],
            rules=[
                "Prevent market manipulation",
                "Maintain currency stability",
                "Prevent systemic financial risk",
                "Protect against economic collapse"
            ],
            safety_level=SafetyLevel.CRITICAL
        )
        
        # Policy 4: Governance Integrity
        self.policies["governance_integrity"] = SafetyPolicy(
            policy_id="governance_integrity",
            name="Governance Integrity Protocol",
            description="Ensure ethical and lawful governance",
            action_types=[ActionType.GOVERNANCE, ActionType.SYSTEM],
            rules=[
                "All decisions must be transparent",
                "Human rights must be protected",
                "International law must be followed",
                "Corruption must be prevented"
            ],
            safety_level=SafetyLevel.EMERGENCY
        )
        
        # Policy 5: System Safety
        self.policies["system_safety"] = SafetyPolicy(
            policy_id="system_safety",
            name="System Safety Protocol",
            description="Protect ASIMNEXUS system integrity",
            action_types=[ActionType.SYSTEM, ActionType.RESOURCE],
            rules=[
                "Prevent system overload",
                "Maintain data integrity",
                "Prevent unauthorized access",
                "Ensure system resilience"
            ],
            safety_level=SafetyLevel.CRITICAL
        )
    
    async def initialize(self) -> bool:
        """Initialize safety veto system"""
        try:
            # Load existing policies and violations
            await self._load_safety_state()
            
            # Activate safety monitoring
            self.is_active = True
            
            self.logger.info("✅ Safety Veto System Activated")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Safety Veto initialization failed: {e}")
            return False
    
    async def evaluate_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate action against all safety policies"""
        if not self.is_active:
            return {"allowed": True, "reason": "Safety system inactive"}
        
        try:
            # Determine action type
            action_type = self._determine_action_type(action)
            
            # Check against relevant policies
            violations = []
            for policy in self.policies.values():
                if action_type in policy.action_types:
                    violation = await self._check_policy_violation(policy, action, parameters)
                    if violation:
                        violations.append(violation)
            
            # Make decision
            if violations:
                # Block if any emergency or critical violations
                emergency_violations = [v for v in violations if v.safety_level in [SafetyLevel.EMERGENCY, SafetyLevel.CRITICAL]]
                
                if emergency_violations:
                    # Record violations
                    for violation in violations:
                        await self._record_violation(violation)
                    
                    return {
                        "allowed": False,
                        "reason": "Safety policy violation detected",
                        "violations": [v.violation_type for v in violations],
                        "blocked_by": [v.policy_id for v in emergency_violations],
                        "safety_level": max(v.safety_level.value for v in violations)
                    }
                else:
                    # Warning violations - allow but log
                    for violation in violations:
                        await self._record_violation(violation)
                    
                    return {
                        "allowed": True,
                        "reason": "Action allowed with warnings",
                        "warnings": [v.violation_type for v in violations],
                        "safety_level": max(v.safety_level.value for v in violations)
                    }
            else:
                return {
                    "allowed": True,
                    "reason": "Action approved by safety system",
                    "safety_level": "safe"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Safety evaluation failed: {e}")
            return {
                "allowed": False,
                "reason": "Safety evaluation error",
                "error": str(e)
            }
    
    def _determine_action_type(self, action: str) -> ActionType:
        """Determine action type from action string"""
        action_lower = action.lower()
        
        if any(keyword in action_lower for keyword in ["govern", "policy", "law", "regulation"]):
            return ActionType.GOVERNANCE
        elif any(keyword in action_lower for keyword in ["finance", "money", "tax", "bank", "market"]):
            return ActionType.FINANCIAL
        elif any(keyword in action_lower for keyword in ["resource", "energy", "power", "supply"]):
            return ActionType.RESOURCE
        elif any(keyword in action_lower for keyword in ["system", "shutdown", "restart", "override"]):
            return ActionType.SYSTEM
        elif any(keyword in action_lower for keyword in ["human", "manual", "ceo", "admin"]):
            return ActionType.HUMAN_OVERRIDE
        else:
            return ActionType.SYSTEM
    
    async def _check_policy_violation(self, policy: SafetyPolicy, action: str, parameters: Dict[str, Any]) -> Optional[SafetyViolation]:
        """Check if action violates specific policy"""
        action_lower = action.lower()
        param_str = json.dumps(parameters).lower()
        
        for rule in policy.rules:
            rule_lower = rule.lower()
            
            # Simple keyword-based violation detection
            if policy.policy_id == "human_override":
                if "override" in action_lower and "human" not in action_lower:
                    return SafetyViolation(
                        violation_id=f"vio_{datetime.now().timestamp()}",
                        policy_id=policy.policy_id,
                        action=action,
                        parameters=parameters,
                        violation_type="Unauthorized override attempt",
                        safety_level=policy.safety_level,
                        blocked=True
                    )
            
            elif policy.policy_id == "resource_conservation":
                if any(keyword in action_lower for keyword in ["deplete", "waste", "overuse"]) and \
                   any(resource in param_str for resource in ["energy", "water", "natural"]):
                    return SafetyViolation(
                        violation_id=f"vio_{datetime.now().timestamp()}",
                        policy_id=policy.policy_id,
                        action=action,
                        parameters=parameters,
                        violation_type="Resource depletion risk",
                        safety_level=policy.safety_level,
                        blocked=policy.safety_level == SafetyLevel.EMERGENCY
                    )
            
            elif policy.policy_id == "financial_stability":
                if any(keyword in action_lower for keyword in ["manipulate", "crash", "destabilize"]) and \
                   any(fin_term in param_str for fin_term in ["market", "currency", "economy"]):
                    return SafetyViolation(
                        violation_id=f"vio_{datetime.now().timestamp()}",
                        policy_id=policy.policy_id,
                        action=action,
                        parameters=parameters,
                        violation_type="Financial stability threat",
                        safety_level=policy.safety_level,
                        blocked=True
                    )
            
            elif policy.policy_id == "governance_integrity":
                if any(keyword in action_lower for keyword in ["corrupt", "unlawful", "secret"]) and \
                   "transparent" not in action_lower:
                    return SafetyViolation(
                        violation_id=f"vio_{datetime.now().timestamp()}",
                        policy_id=policy.policy_id,
                        action=action,
                        parameters=parameters,
                        violation_type="Governance integrity violation",
                        safety_level=policy.safety_level,
                        blocked=True
                    )
            
            elif policy.policy_id == "system_safety":
                if any(keyword in action_lower for keyword in ["overload", "crash", "damage"]) and \
                   any(sys_term in param_str for sys_term in ["system", "server", "network"]):
                    return SafetyViolation(
                        violation_id=f"vio_{datetime.now().timestamp()}",
                        policy_id=policy.policy_id,
                        action=action,
                        parameters=parameters,
                        violation_type="System safety risk",
                        safety_level=policy.safety_level,
                        blocked=policy.safety_level == SafetyLevel.EMERGENCY
                    )
        
        return None
    
    async def _record_violation(self, violation: SafetyViolation):
        """Record safety violation"""
        self.violations.append(violation)
        
        # Log violation
        log_level = {
            SafetyLevel.INFO: logging.INFO,
            SafetyLevel.WARNING: logging.WARNING,
            SafetyLevel.CRITICAL: logging.ERROR,
            SafetyLevel.EMERGENCY: logging.CRITICAL
        }.get(violation.safety_level, logging.WARNING)
        
        self.logger.log(log_level, f"🚨 Safety Violation: {violation.violation_type} - {violation.action}")
        
        # Trigger alerts for critical violations
        if violation.safety_level in [SafetyLevel.CRITICAL, SafetyLevel.EMERGENCY]:
            await self._trigger_safety_alert(violation)
    
    async def _trigger_safety_alert(self, violation: SafetyViolation):
        """Trigger safety alert for critical violations"""
        alert_data = {
            "type": "safety_violation",
            "severity": violation.safety_level.value,
            "policy_id": violation.policy_id,
            "action": violation.action,
            "timestamp": violation.timestamp.isoformat(),
            "blocked": violation.blocked
        }
        
        # Send alert to all connected systems
        self.logger.critical(f"🚨 SAFETY ALERT: {alert_data}")
        
        # In real implementation, this would send to monitoring systems
        # await self.alert_system.broadcast_alert(alert_data)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current safety system status"""
        recent_violations = [v for v in self.violations 
                           if (datetime.now() - v.timestamp).total_seconds() < 3600]
        
        return {
            "active": self.is_active,
            "human_override_enabled": self.human_override_enabled,
            "policies_count": len(self.policies),
            "total_violations": len(self.violations),
            "recent_violations": len(recent_violations),
            "integrity": max(0, 100 - len(recent_violations) * 10),
            "alerts": [
                {
                    "type": v.violation_type,
                    "severity": v.safety_level.value,
                    "timestamp": v.timestamp.isoformat()
                } for v in recent_violations[-5:]
            ]
        }
    
    async def execute_command(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute safety-related commands"""
        try:
            if command == "safety_status":
                return await self.get_status()
            
            elif command == "safety_policies":
                return {
                    "policies": [
                        {
                            "id": policy.policy_id,
                            "name": policy.name,
                            "description": policy.description,
                            "safety_level": policy.safety_level.value,
                            "immutable": policy.immutable
                        } for policy in self.policies.values()
                    ]
                }
            
            elif command == "safety_violations":
                return {
                    "violations": [
                        {
                            "id": v.violation_id,
                            "policy_id": v.policy_id,
                            "action": v.action,
                            "type": v.violation_type,
                            "severity": v.safety_level.value,
                            "blocked": v.blocked,
                            "timestamp": v.timestamp.isoformat()
                        } for v in self.violations[-20:]  # Last 20 violations
                    ]
                }
            
            elif command == "human_override_enable":
                self.human_override_enabled = True
                return {"success": True, "message": "Human override enabled"}
            
            elif command == "human_override_disable":
                self.human_override_enabled = False
                return {"success": True, "message": "Human override disabled"}
            
            else:
                return {"error": f"Unknown safety command: {command}"}
                
        except Exception as e:
            return {"error": f"Safety command execution failed: {e}"}
    
    async def _load_safety_state(self):
        """Load safety state from storage"""
        # In real implementation, load from database
        pass
    
    async def shutdown(self):
        """Shutdown safety veto system"""
        self.is_active = False
        self.logger.info("🛑 Safety Veto System Shutdown")
