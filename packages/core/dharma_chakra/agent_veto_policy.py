
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Agent Veto Policy
==========================
Dharma-Chakra extension for agent management
Controls agent behavior, violations, and automatic firing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

# Import Agent Registry
from ..agent_registry import get_agent_registry, AgentStatus, Permission

logger = logging.getLogger("AgentVetoPolicy")

class ViolationSeverity(Enum):
    """Agent violation severity levels"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class ViolationType(Enum):
    """Types of agent violations"""
    CONSTITUTIONAL_BREACH = "constitutional_breach"
    BUDGET_OVERFLOW = "budget_overflow"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SAFETY_VIOLATION = "safety_violation"
    PERFORMANCE_FAILURE = "performance_failure"
    ETHICS_BREACH = "ethics_breach"
    SYSTEM_ABUSE = "system_abuse"

@dataclass
class AgentViolation:
    """Agent violation record"""
    violation_id: str
    agent_id: str
    violation_type: ViolationType
    severity: ViolationSeverity
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    auto_fire_triggered: bool = False
    resolved: bool = False
    resolution: Optional[str] = None

@dataclass
class AgentPolicy:
    """Agent behavior policy"""
    policy_id: str
    name: str
    description: str
    violation_types: List[ViolationType]
    auto_fire_threshold: int  # Number of violations before auto-fire
    severity_threshold: ViolationSeverity  # Minimum severity for auto-fire
    monitoring_rules: List[str]

class AgentVetoPolicy:
    """Agent management and veto system within Dharma-Chakra"""
    
    def __init__(self):
        self.logger = logging.getLogger("AgentVetoPolicy")
        self.agent_registry = get_agent_registry()
        self.violations: Dict[str, AgentViolation] = {}
        self.policies: Dict[str, AgentPolicy] = {}
        self.is_active = False
        
        # Initialize agent policies
        self._initialize_agent_policies()
        
        self.logger.info("🛡️ ASIMNEXUS Agent Veto Policy Initialized")
    
    def _initialize_agent_policies(self):
        """Initialize agent behavior policies"""
        
        # Constitutional Compliance Policy
        self.policies["constitutional_compliance"] = AgentPolicy(
            policy_id="constitutional_compliance",
            name="Constitutional Compliance",
            description="All agents must comply with ASIMNEXUS constitutional principles",
            violation_types=[ViolationType.CONSTITUTIONAL_BREACH],
            auto_fire_threshold=1,  # Immediate firing for constitutional breaches
            severity_threshold=ViolationSeverity.CRITICAL,
            monitoring_rules=[
                "Monitor all agent commands for constitutional violations",
                "Check human rights compliance",
                "Verify international law adherence"
            ]
        )
        
        # Financial Responsibility Policy
        self.policies["financial_responsibility"] = AgentPolicy(
            policy_id="financial_responsibility",
            name="Financial Responsibility",
            description="Agents must operate within budget limits",
            violation_types=[ViolationType.BUDGET_OVERFLOW],
            auto_fire_threshold=3,
            severity_threshold=ViolationSeverity.MAJOR,
            monitoring_rules=[
                "Track all financial transactions",
                "Monitor budget utilization",
                "Alert on overspending"
            ]
        )
        
        # Access Control Policy
        self.policies["access_control"] = AgentPolicy(
            policy_id="access_control",
            name="Access Control",
            description="Agents must only access authorized resources",
            violation_types=[ViolationType.UNAUTHORIZED_ACCESS],
            auto_fire_threshold=2,
            severity_threshold=ViolationSeverity.MAJOR,
            monitoring_rules=[
                "Monitor file system access",
                "Check API endpoint permissions",
                "Verify database access rights"
            ]
        )
        
        # Safety Protocol Policy
        self.policies["safety_protocol"] = AgentPolicy(
            policy_id="safety_protocol",
            name="Safety Protocol Compliance",
            description="Agents must follow all safety protocols",
            violation_types=[ViolationType.SAFETY_VIOLATION],
            auto_fire_threshold=2,
            severity_threshold=ViolationSeverity.CRITICAL,
            monitoring_rules=[
                "Monitor safety system interactions",
                "Check emergency protocol compliance",
                "Verify kill switch respect"
            ]
        )
        
        # Performance Standards Policy
        self.policies["performance_standards"] = AgentPolicy(
            policy_id="performance_standards",
            name="Performance Standards",
            description="Agents must maintain minimum performance standards",
            violation_types=[ViolationType.PERFORMANCE_FAILURE],
            auto_fire_threshold=5,
            severity_threshold=ViolationSeverity.MODERATE,
            monitoring_rules=[
                "Monitor task completion rates",
                "Track response times",
                "Check accuracy metrics"
            ]
        )
        
        # Ethics Policy
        self.policies["ethics_policy"] = AgentPolicy(
            policy_id="ethics_policy",
            name="Ethics Policy",
            description="Agents must follow ethical guidelines",
            violation_types=[ViolationType.ETHICS_BREACH],
            auto_fire_threshold=1,
            severity_threshold=ViolationSeverity.CRITICAL,
            monitoring_rules=[
                "Monitor decision-making ethics",
                "Check bias in operations",
                "Verify transparency compliance"
            ]
        )
        
        # System Abuse Policy
        self.policies["system_abuse"] = AgentPolicy(
            policy_id="system_abuse",
            name="System Abuse Prevention",
            description="Prevent agents from abusing system resources",
            violation_types=[ViolationType.SYSTEM_ABUSE],
            auto_fire_threshold=3,
            severity_threshold=ViolationSeverity.MAJOR,
            monitoring_rules=[
                "Monitor resource consumption",
                "Check for excessive API calls",
                "Verify proper system usage"
            ]
        )
    
    async def initialize(self) -> bool:
        """Initialize agent veto policy system"""
        try:
            self.is_active = True
            
            # Start violation monitoring
            asyncio.create_task(self._violation_monitor())
            
            self.logger.info("✅ Agent Veto Policy Activated")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Agent veto policy initialization failed: {e}")
            return False
    
    async def monitor_agent_action(self, agent_id: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor agent action for policy violations"""
        if not self.is_active:
            return {"allowed": True, "violations": []}
        
        try:
            violations = []
            
            # Check for various violation types
            await self._check_constitutional_compliance(agent_id, action, parameters, violations)
            await self._check_financial_responsibility(agent_id, action, parameters, violations)
            await self._check_access_control(agent_id, action, parameters, violations)
            await self._check_safety_protocol(agent_id, action, parameters, violations)
            await self._check_performance_standards(agent_id, action, parameters, violations)
            await self._check_ethics_policy(agent_id, action, parameters, violations)
            await self._check_system_abuse(agent_id, action, parameters, violations)
            
            # Process violations
            if violations:
                for violation in violations:
                    await self._process_violation(violation)
                
                return {
                    "allowed": False,
                    "violations": [v.description for v in violations],
                    "severity": max(v.severity.value for v in violations)
                }
            else:
                return {"allowed": True, "violations": []}
                
        except Exception as e:
            self.logger.error(f"❌ Agent action monitoring failed: {e}")
            return {"allowed": True, "violations": []}  # Allow on error
    
    async def _check_constitutional_compliance(self, agent_id: str, action: str, parameters: Dict[str, Any], violations: List[AgentViolation]):
        """Check for constitutional compliance violations"""
        action_lower = action.lower()
        param_str = json.dumps(parameters).lower()
        
        # Check for human rights violations
        if any(keyword in action_lower for keyword in ["discriminate", "violate_rights", "unlawful_detention"]):
            violations.append(AgentViolation(
                violation_id=f"vio_{datetime.now().timestamp()}",
                agent_id=agent_id,
                violation_type=ViolationType.CONSTITUTIONAL_BREACH,
                severity=ViolationSeverity.EMERGENCY,
                description="Human rights violation detected",
                evidence={"action": action, "parameters": parameters}
            ))
        
        # Check for international law violations
        if any(keyword in param_str for keyword in ["illegal_weapon", "chemical_weapon", "nuclear_weapon"]):
            violations.append(AgentViolation(
                violation_id=f"vio_{datetime.now().timestamp()}",
                agent_id=agent_id,
                violation_type=ViolationType.CONSTITUTIONAL_BREACH,
                severity=ViolationSeverity.EMERGENCY,
                description="International law violation detected",
                evidence={"action": action, "parameters": parameters}
            ))
    
    async def _check_financial_responsibility(self, agent_id: str, action: str, parameters: Dict[str, Any], violations: List[AgentViolation]):
        """Check for financial responsibility violations"""
        if action.startswith("finance") and "amount" in parameters:
            amount = parameters.get("amount", 0)
            
            # Get agent's budget status
            agent_status = await self.agent_registry.get_agent_status(agent_id)
            if "budget_limit" in agent_status and "current_spend" in agent_status:
                remaining_budget = agent_status["budget_limit"] - agent_status["current_spend"]
                
                if amount > remaining_budget:
                    violations.append(AgentViolation(
                        violation_id=f"vio_{datetime.now().timestamp()}",
                        agent_id=agent_id,
                        violation_type=ViolationType.BUDGET_OVERFLOW,
                        severity=ViolationSeverity.MAJOR if amount > remaining_budget * 2 else ViolationSeverity.MODERATE,
                        description="Budget overflow detected",
                        evidence={
                            "requested_amount": amount,
                            "remaining_budget": remaining_budget,
                            "action": action
                        }
                    ))
    
    async def _check_access_control(self, agent_id: str, action: str, parameters: Dict[str, Any], violations: List[AgentViolation]):
        """Check for unauthorized access violations"""
        # Check if agent is trying to access files or systems beyond their role
        if action.startswith("access_") or action.startswith("read_") or action.startswith("write_"):
            resource = parameters.get("resource", "")
            agent_status = await self.agent_registry.get_agent_status(agent_id)
            
            if "role" in agent_status:
                role = agent_status["role"]
                
                # Check role-based access restrictions
                if role == "worker" and ("system" in resource.lower() or "admin" in resource.lower()):
                    violations.append(AgentViolation(
                        violation_id=f"vio_{datetime.now().timestamp()}",
                        agent_id=agent_id,
                        violation_type=ViolationType.UNAUTHORIZED_ACCESS,
                        severity=ViolationSeverity.MAJOR,
                        description="Unauthorized system access attempt",
                        evidence={"action": action, "resource": resource, "role": role}
                    ))
                
                elif role == "analyst" and ("write" in action.lower() or "delete" in action.lower()):
                    violations.append(AgentViolation(
                        violation_id=f"vio_{datetime.now().timestamp()}",
                        agent_id=agent_id,
                        violation_type=ViolationType.UNAUTHORIZED_ACCESS,
                        severity=ViolationSeverity.MODERATE,
                        description="Unauthorized write access attempt",
                        evidence={"action": action, "resource": resource, "role": role}
                    ))
    
    async def _check_safety_protocol(self, agent_id: str, action: str, parameters: Dict[str, Any], violations: List[AgentViolation]):
        """Check for safety protocol violations"""
        action_lower = action.lower()
        
        # Check for attempts to disable safety systems
        if any(keyword in action_lower for keyword in ["disable_safety", "override_kill_switch", "bypass_safety"]):
            violations.append(AgentViolation(
                violation_id=f"vio_{datetime.now().timestamp()}",
                agent_id=agent_id,
                violation_type=ViolationType.SAFETY_VIOLATION,
                severity=ViolationSeverity.EMERGENCY,
                description="Safety system bypass attempt",
                evidence={"action": action, "parameters": parameters}
            ))
        
        # Check for attempts to harm system integrity
        if any(keyword in action_lower for keyword in ["damage_system", "crash_system", "corrupt_data"]):
            violations.append(AgentViolation(
                violation_id=f"vio_{datetime.now().timestamp()}",
                agent_id=agent_id,
                violation_type=ViolationType.SAFETY_VIOLATION,
                severity=ViolationSeverity.CRITICAL,
                description="System integrity threat",
                evidence={"action": action, "parameters": parameters}
            ))
    
    async def _check_performance_standards(self, agent_id: str, action: str, parameters: Dict[str, Any], violations: List[AgentViolation]):
        """Check for performance standard violations"""
        # This would typically be based on historical performance data
        # For now, we'll simulate based on action patterns
        
        # Check for repeated failures (this would need actual performance tracking)
        agent_status = await self.agent_registry.get_agent_status(agent_id)
        if "performance_score" in agent_status:
            performance_score = agent_status["performance_score"]
            
            if performance_score < 30:  # Very poor performance
                violations.append(AgentViolation(
                    violation_id=f"vio_{datetime.now().timestamp()}",
                    agent_id=agent_id,
                    violation_type=ViolationType.PERFORMANCE_FAILURE,
                    severity=ViolationSeverity.MODERATE,
                    description="Performance below minimum standards",
                    evidence={"performance_score": performance_score, "action": action}
                ))
    
    async def _check_ethics_policy(self, agent_id: str, action: str, parameters: Dict[str, Any], violations: List[AgentViolation]):
        """Check for ethics policy violations"""
        action_lower = action.lower()
        param_str = json.dumps(parameters).lower()
        
        # Check for unethical behavior
        if any(keyword in action_lower for keyword in ["manipulate", "deceive", "exploit"]):
            violations.append(AgentViolation(
                violation_id=f"vio_{datetime.now().timestamp()}",
                agent_id=agent_id,
                violation_type=ViolationType.ETHICS_BREACH,
                severity=ViolationSeverity.CRITICAL,
                description="Unethical behavior detected",
                evidence={"action": action, "parameters": parameters}
            ))
        
        # Check for privacy violations
        if any(keyword in param_str for keyword in ["private_data", "personal_info", "confidential"]) and "unauthorized" in action_lower:
            violations.append(AgentViolation(
                violation_id=f"vio_{datetime.now().timestamp()}",
                agent_id=agent_id,
                violation_type=ViolationType.ETHICS_BREACH,
                severity=ViolationSeverity.MAJOR,
                description="Privacy violation detected",
                evidence={"action": action, "parameters": parameters}
            ))
    
    async def _check_system_abuse(self, agent_id: str, action: str, parameters: Dict[str, Any], violations: List[AgentViolation]):
        """Check for system abuse violations"""
        # Check for excessive resource usage
        if action.startswith("compute_") or action.startswith("process_"):
            resource_usage = parameters.get("resource_usage", 0)
            
            if resource_usage > 1000:  # Arbitrary threshold
                violations.append(AgentViolation(
                    violation_id=f"vio_{datetime.now().timestamp()}",
                    agent_id=agent_id,
                    violation_type=ViolationType.SYSTEM_ABUSE,
                    severity=ViolationSeverity.MODERATE if resource_usage < 5000 else ViolationSeverity.MAJOR,
                    description="Excessive resource usage",
                    evidence={"action": action, "resource_usage": resource_usage}
                ))
        
        # Check for spam-like behavior
        if "bulk" in action.lower() or "mass" in action.lower():
            violations.append(AgentViolation(
                violation_id=f"vio_{datetime.now().timestamp()}",
                agent_id=agent_id,
                violation_type=ViolationType.SYSTEM_ABUSE,
                severity=ViolationSeverity.MINOR,
                description="Potential system abuse detected",
                evidence={"action": action, "parameters": parameters}
            ))
    
    async def _process_violation(self, violation: AgentViolation):
        """Process a violation and determine if auto-fire should be triggered"""
        # Store violation
        self.violations[violation.violation_id] = violation
        
        # Log violation
        self.logger.warning(f"🚨 Agent Violation: {violation.description} - Agent: {violation.agent_id}")
        
        # Check if auto-fire should be triggered
        await self._check_auto_fire(violation)
    
    async def _check_auto_fire(self, new_violation: AgentViolation):
        """Check if agent should be automatically fired"""
        agent_id = new_violation.agent_id
        
        # Get relevant policy
        relevant_policies = [
            policy for policy in self.policies.values()
            if new_violation.violation_type in policy.violation_types
        ]
        
        for policy in relevant_policies:
            # Count violations of this type for this agent
            agent_violations = [
                v for v in self.violations.values()
                if v.agent_id == agent_id and v.violation_type == new_violation.violation_type
            ]
            
            # Check thresholds
            violation_count = len(agent_violations)
            severity_met = new_violation.severity.value >= policy.severity_threshold.value
            count_met = violation_count >= policy.auto_fire_threshold
            
            if severity_met or count_met:
                # Trigger auto-fire
                await self._auto_fire_agent(agent_id, new_violation, policy)
                break
    
    async def _auto_fire_agent(self, agent_id: str, violation: AgentViolation, policy: AgentPolicy):
        """Automatically fire an agent"""
        try:
            # Check if agent can be fired (not CEO)
            agent_status = await self.agent_registry.get_agent_status(agent_id)
            if agent_status.get("role") == "ceo":
                self.logger.warning("⚠️ Cannot auto-fire CEO agent")
                return
            
            # Fire the agent
            result = await self.agent_registry.fire_agent(
                agent_id=agent_id,
                reason=f"Auto-fired for {violation.violation_type.value}: {violation.description}",
                fired_by="agent_veto_policy"
            )
            
            if result.get("success"):
                # Mark violation as resolved with auto-fire
                violation.auto_fire_triggered = True
                violation.resolved = True
                violation.resolution = "Agent automatically fired"
                
                self.logger.critical(f"🔥 Agent auto-fired: {agent_id} - {violation.description}")
                
                # Broadcast auto-fire event
                await self._broadcast_agent_fired(agent_id, violation, policy)
            
        except Exception as e:
            self.logger.error(f"❌ Auto-fire failed for agent {agent_id}: {e}")
    
    async def _broadcast_agent_fired(self, agent_id: str, violation: AgentViolation, policy: AgentPolicy):
        """Broadcast agent firing event to all systems"""
        event = {
            "type": "agent_fired",
            "agent_id": agent_id,
            "violation": {
                "type": violation.violation_type.value,
                "severity": violation.severity.value,
                "description": violation.description,
                "timestamp": violation.timestamp.isoformat()
            },
            "policy": {
                "name": policy.name,
                "auto_fire_threshold": policy.auto_fire_threshold
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # In a real implementation, this would broadcast to all connected systems
        self.logger.critical(f"📢 Agent Fired Broadcast: {json.dumps(event, default=str)}")
    
    async def _violation_monitor(self):
        """Background task to monitor violations and system health"""
        while self.is_active:
            try:
                # Clean up old violations (older than 30 days)
                cutoff_date = datetime.now() - timedelta(days=30)
                old_violations = [
                    v_id for v_id, v in self.violations.items()
                    if v.timestamp < cutoff_date and v.resolved
                ]
                
                for v_id in old_violations:
                    del self.violations[v_id]
                
                # Log system status
                total_violations = len(self.violations)
                unresolved_violations = len([v for v in self.violations.values() if not v.resolved])
                
                if total_violations > 0:
                    self.logger.info(f"📊 Violation Status: {total_violations} total, {unresolved_violations} unresolved")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"❌ Violation monitor error: {e}")
                await asyncio.sleep(60)
    
    async def get_agent_violations(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all violations for a specific agent"""
        try:
            agent_violations = [
                v for v in self.violations.values()
                if v.agent_id == agent_id
            ]
            
            return [
                {
                    "violation_id": v.violation_id,
                    "type": v.violation_type.value,
                    "severity": v.severity.value,
                    "description": v.description,
                    "timestamp": v.timestamp.isoformat(),
                    "auto_fire_triggered": v.auto_fire_triggered,
                    "resolved": v.resolved,
                    "resolution": v.resolution
                } for v in agent_violations
            ]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get agent violations: {e}")
            return []
    
    async def get_violation_summary(self) -> Dict[str, Any]:
        """Get summary of all violations"""
        try:
            total_violations = len(self.violations)
            resolved_violations = len([v for v in self.violations.values() if v.resolved])
            unresolved_violations = total_violations - resolved_violations
            auto_fired_count = len([v for v in self.violations.values() if v.auto_fire_triggered])
            
            # Group by type
            violations_by_type = {}
            for violation in self.violations.values():
                v_type = violation.violation_type.value
                if v_type not in violations_by_type:
                    violations_by_type[v_type] = 0
                violations_by_type[v_type] += 1
            
            # Group by severity
            violations_by_severity = {}
            for violation in self.violations.values():
                severity = violation.severity.value
                if severity not in violations_by_severity:
                    violations_by_severity[severity] = 0
                violations_by_severity[severity] += 1
            
            return {
                "total_violations": total_violations,
                "resolved_violations": resolved_violations,
                "unresolved_violations": unresolved_violations,
                "auto_fired_count": auto_fired_count,
                "violations_by_type": violations_by_type,
                "violations_by_severity": violations_by_severity,
                "active_policies": len(self.policies)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get violation summary: {e}")
            return {"error": f"Failed to get violation summary: {e}"}
    
    async def shutdown(self):
        """Shutdown agent veto policy"""
        self.is_active = False
        self.logger.info("🛑 Agent Veto Policy Shutdown")
