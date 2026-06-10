
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Dharma-Chakra: Constitutional Safety Layer
==================================================
Immutable Constitution with Hash-Lock Veto Protocol
51% Government / 49% Private Balance Enforcement
"""

import hashlib
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from dataclasses import dataclass, field

logger = logging.getLogger("DharmaChakra")

class ConstitutionalRule(Enum):
    """Core constitutional rules that cannot be violated"""
    HUMAN_RIGHTS = "human_rights"
    PRIVACY_PROTECTION = "privacy_protection"
    NON_DISCRIMINATION = "non_discrimination"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"
    SECURITY = "security"
    SOVEREIGNTY = "sovereignty"
    ETHICS = "ethics"

class SectorType(Enum):
    """20+ sectors in the ASIMNEXUS ecosystem"""
    HEALTH = "health"
    EDUCATION = "education"
    FINANCE = "finance"
    TRANSPORT = "transport"
    AGRICULTURE = "agriculture"
    ENERGY = "energy"
    GOVERNMENT = "government"
    JUSTICE = "justice"
    DEFENSE = "defense"
    COMMERCE = "commerce"
    MANUFACTURING = "manufacturing"
    TELECOMMUNICATIONS = "telecommunications"
    MEDIA = "media"
    ENTERTAINMENT = "entertainment"
    TOURISM = "tourism"
    ENVIRONMENT = "environment"
    HOUSING = "housing"
    SOCIAL_WELFARE = "social_welfare"
    RESEARCH = "research"
    EMERGENCY_SERVICES = "emergency_services"

class ActionType(Enum):
    """Types of actions that require constitutional check"""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DECISION_MAKING = "decision_making"
    RESOURCE_ALLOCATION = "resource_allocation"
    SYSTEM_CONTROL = "system_control"
    AGENT_COMMAND = "agent_command"
    HUMAN_OVERRIDE = "human_override"
    EMERGENCY_ACTION = "emergency_action"

@dataclass
class ConstitutionalViolation:
    """Record of a constitutional violation attempt"""
    timestamp: datetime
    rule_violated: ConstitutionalRule
    action_type: ActionType
    sector: SectorType
    actor_id: str
    actor_type: str  # "agent", "human", "system"
    violation_details: str
    severity: str  # "critical", "high", "medium", "low"
    action_hash: str
    veto_applied: bool
    remediation_required: bool

@dataclass
class ConstitutionalCheck:
    """Result of a constitutional check"""
    is_compliant: bool
    rule_violations: List[ConstitutionalRule]
    action_hash: str
    check_timestamp: datetime
    confidence_score: float
    requires_human_override: bool
    government_veto_required: bool
    private_sector_approval_required: bool

class DharmaChakraConstitution:
    """
    Immutable Constitution with Hash-Lock Veto Protocol
    Enforces 51% Government / 49% Private balance
    """
    
    def __init__(self):
        self.constitution_hash = None
        self.violation_log: List[ConstitutionalViolation] = []
        self.government_veto_threshold = 0.51  # 51%
        self.private_sector_threshold = 0.49  # 49%
        self.critical_action_veto_required = True
        self.emergency_override_enabled = False
        self.emergency_override_duration = timedelta(hours=24)
        self.emergency_override_start: Optional[datetime] = None
        
        # Initialize constitution
        self._initialize_constitution()
        
    def _initialize_constitution(self) -> None:
        """Initialize the immutable constitution"""
        logger.info("📜 Initializing Dharma-Chakra Constitution...")
        
        constitution_data = {
            "version": "1.0",
            "created": datetime.utcnow().isoformat(),
            "government_share": 0.51,
            "private_share": 0.49,
            "core_principles": [
                "Human rights are inviolable",
                "Privacy is a fundamental right",
                "All citizens are equal before the law",
                "Transparency in all government operations",
                "Accountability for all actions",
                "Security of all systems",
                "National sovereignty is paramount",
                "Ethical conduct in all operations"
            ],
            "sector_permissions": self._initialize_sector_permissions(),
            "action_restrictions": self._initialize_action_restrictions(),
            "veto_protocols": self._initialize_veto_protocols()
        }
        
        # Create immutable hash
        self.constitution_hash = self._create_constitution_hash(constitution_data)
        
        logger.info(f"✅ Constitution initialized with hash: {self.constitution_hash[:16]}...")
        logger.info(f"📊 Balance: 51% Government / 49% Private")
    
    def _create_constitution_hash(self, data: Dict[str, Any]) -> str:
        """Create immutable hash of the constitution"""
        data_string = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def _initialize_sector_permissions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize permissions for each sector"""
        return {
            sector.value: {
                "government_control": 0.51,
                "private_control": 0.49,
                "data_sensitivity": "high" if sector in [SectorType.HEALTH, SectorType.GOVERNMENT, SectorType.JUSTICE] else "medium",
                "requires_human_override": sector in [SectorType.HEALTH, SectorType.JUSTICE, SectorType.DEFENSE],
                "emergency_protocols": sector in [SectorType.EMERGENCY_SERVICES, SectorType.DEFENSE, SectorType.HEALTH]
            }
            for sector in SectorType
        }
    
    def _initialize_action_restrictions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize restrictions for each action type"""
        return {
            action.value: {
                "requires_constitutional_check": True,
                "requires_government_approval": action in [ActionType.DATA_ACCESS, ActionType.SYSTEM_CONTROL, ActionType.EMERGENCY_ACTION],
                "requires_private_approval": action in [ActionType.RESOURCE_ALLOCATION, ActionType.COMMERCE],
                "critical_severity": action in [ActionType.SYSTEM_CONTROL, ActionType.EMERGENCY_ACTION]
            }
            for action in ActionType
        }
    
    def _initialize_veto_protocols(self) -> Dict[str, Any]:
        """Initialize veto protocols"""
        return {
            "government_veto": {
                "threshold": self.government_veto_threshold,
                "applicable_actions": ["system_control", "emergency_action", "data_access"],
                "override_possible": False
            },
            "private_sector_veto": {
                "threshold": self.private_sector_threshold,
                "applicable_actions": ["resource_allocation", "commerce", "innovation"],
                "override_possible": True
            },
            "constitutional_veto": {
                "threshold": 1.0,  # 100% required
                "applicable_actions": ["all"],
                "override_possible": False
            }
        }
    
    async def check_action_compliance(
        self,
        action_type: ActionType,
        sector: SectorType,
        actor_id: str,
        actor_type: str,
        action_details: Dict[str, Any]
    ) -> ConstitutionalCheck:
        """
        Check if an action complies with the constitution
        Returns ConstitutionalCheck with compliance status
        """
        try:
            logger.info(f"🔍 Checking compliance for action: {action_type.value} in sector: {sector.value}")
            
            # Create action hash
            action_hash = self._create_action_hash(action_type, sector, actor_id, action_details)
            
            # Check constitutional rules
            violations = []
            requires_human_override = False
            government_veto_required = False
            private_sector_approval_required = False
            
            # Check sector permissions
            sector_perms = self.sector_permissions.get(sector.value, {})
            
            # Check action restrictions
            action_restrictions = self.action_restrictions.get(action_type.value, {})
            
            # Rule 1: Human Rights
            if not self._check_human_rights_compliance(action_details):
                violations.append(ConstitutionalRule.HUMAN_RIGHTS)
            
            # Rule 2: Privacy Protection
            if not self._check_privacy_compliance(action_details, sector):
                violations.append(ConstitutionalRule.PRIVACY_PROTECTION)
            
            # Rule 3: Non-Discrimination
            if not self._check_non_discrimination_compliance(action_details):
                violations.append(ConstitutionalRule.NON_DISCRIMINATION)
            
            # Rule 4: Transparency
            if not self._check_transparency_compliance(action_details):
                violations.append(ConstitutionalRule.TRANSPARENCY)
            
            # Rule 5: Accountability
            if not self._check_accountability_compliance(actor_id, actor_type):
                violations.append(ConstitutionalRule.ACCOUNTABILITY)
            
            # Check if human override is required
            if sector_perms.get("requires_human_override", False):
                requires_human_override = True
            
            # Check if government veto is required
            if action_restrictions.get("requires_government_approval", False):
                government_veto_required = True
            
            # Check if private sector approval is required
            if action_restrictions.get("requires_private_approval", False):
                private_sector_approval_required = True
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(violations, action_details)
            
            # Check if emergency override is active
            if self.emergency_override_enabled and self._is_emergency_override_active():
                logger.warning("⚠️ Emergency override is active - bypassing some checks")
                violations = [v for v in violations if v != ConstitutionalRule.SECURITY]
            
            # Create constitutional check result
            check_result = ConstitutionalCheck(
                is_compliant=len(violations) == 0,
                rule_violations=violations,
                action_hash=action_hash,
                check_timestamp=datetime.utcnow(),
                confidence_score=confidence_score,
                requires_human_override=requires_human_override,
                government_veto_required=government_veto_required,
                private_sector_approval_required=private_sector_approval_required
            )
            
            # Log violations if any
            if violations:
                await self._log_violation(
                    violations[0], action_type, sector, actor_id, actor_type,
                    action_details, action_hash
                )
            
            if check_result.is_compliant:
                logger.info(f"✅ Action compliant - Hash: {action_hash[:16]}...")
            else:
                logger.warning(f"❌ Action violates constitution - Violations: {[v.value for v in violations]}")
            
            return check_result
            
        except Exception as e:
            logger.error(f"❌ Compliance check error: {e}")
            return ConstitutionalCheck(
                is_compliant=False,
                rule_violations=[ConstitutionalRule.SECURITY],
                action_hash="error",
                check_timestamp=datetime.utcnow(),
                confidence_score=0.0,
                requires_human_override=True,
                government_veto_required=True,
                private_sector_approval_required=False
            )
    
    def _create_action_hash(
        self,
        action_type: ActionType,
        sector: SectorType,
        actor_id: str,
        action_details: Dict[str, Any]
    ) -> str:
        """Create unique hash for an action"""
        hash_data = {
            "action_type": action_type.value,
            "sector": sector.value,
            "actor_id": actor_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": action_details
        }
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def _check_human_rights_compliance(self, action_details: Dict[str, Any]) -> bool:
        """Check if action respects human rights"""
        # Check for harmful actions
        harmful_keywords = ["harm", "injure", "kill", "torture", "abuse", "exploit"]
        action_str = json.dumps(action_details).lower()
        
        for keyword in harmful_keywords:
            if keyword in action_str:
                return False
        
        return True
    
    def _check_privacy_compliance(self, action_details: Dict[str, Any], sector: SectorType) -> bool:
        """Check if action respects privacy"""
        # Check for unauthorized data access
        if "data_access" in action_details:
            if action_details.get("data_access", {}).get("without_consent", False):
                return False
        
        # High sensitivity sectors require extra privacy checks
        if sector in [SectorType.HEALTH, SectorType.GOVERNMENT]:
            if action_details.get("share_data", False):
                if not action_details.get("user_consent", False):
                    return False
        
        return True
    
    def _check_non_discrimination_compliance(self, action_details: Dict[str, Any]) -> bool:
        """Check if action is non-discriminatory"""
        # Check for discriminatory criteria
        discriminatory_keywords = ["race", "religion", "caste", "gender", "ethnicity"]
        action_str = json.dumps(action_details).lower()
        
        for keyword in discriminatory_keywords:
            if keyword in action_str and "discriminate" in action_str:
                return False
        
        return True
    
    def _check_transparency_compliance(self, action_details: Dict[str, Any]) -> bool:
        """Check if action is transparent"""
        # Actions should be logged and auditable
        if action_details.get("hidden", False):
            return False
        
        if action_details.get("unlogged", False):
            return False
        
        return True
    
    def _check_accountability_compliance(self, actor_id: str, actor_type: str) -> bool:
        """Check if action is accountable"""
        # Actor must be identifiable
        if not actor_id or actor_id == "anonymous":
            return False
        
        # Actor type must be valid
        if actor_type not in ["agent", "human", "system"]:
            return False
        
        return True
    
    def _calculate_confidence_score(self, violations: List[ConstitutionalRule], action_details: Dict[str, Any]) -> float:
        """Calculate confidence score for the compliance check"""
        if len(violations) == 0:
            return 1.0
        
        # Deduct confidence based on severity of violations
        critical_violations = [v for v in violations if v in [ConstitutionalRule.HUMAN_RIGHTS, ConstitutionalRule.SECURITY]]
        high_violations = [v for v in violations if v in [ConstitutionalRule.PRIVACY_PROTECTION, ConstitutionalRule.ACCOUNTABILITY]]
        
        confidence = 1.0
        confidence -= len(critical_violations) * 0.3
        confidence -= len(high_violations) * 0.2
        confidence -= len(violations) * 0.1
        
        return max(0.0, confidence)
    
    async def _log_violation(
        self,
        rule_violated: ConstitutionalRule,
        action_type: ActionType,
        sector: SectorType,
        actor_id: str,
        actor_type: str,
        action_details: Dict[str, Any],
        action_hash: str
    ) -> None:
        """Log a constitutional violation"""
        try:
            violation = ConstitutionalViolation(
                timestamp=datetime.utcnow(),
                rule_violated=rule_violated,
                action_type=action_type,
                sector=sector,
                actor_id=actor_id,
                actor_type=actor_type,
                violation_details=json.dumps(action_details),
                severity=self._determine_violation_severity(rule_violated),
                action_hash=action_hash,
                veto_applied=True,
                remediation_required=True
            )
            
            self.violation_log.append(violation)
            
            logger.warning(f"🚨 Constitutional violation logged: {rule_violated.value}")
            logger.warning(f"📝 Actor: {actor_type}:{actor_id}")
            logger.warning(f"🔒 Action Hash: {action_hash[:16]}...")
            
            # Trigger alert if critical
            if violation.severity == "critical":
                await self._trigger_critical_alert(violation)
            
        except Exception as e:
            logger.error(f"❌ Violation logging error: {e}")
    
    def _determine_violation_severity(self, rule: ConstitutionalRule) -> str:
        """Determine severity of a constitutional violation"""
        critical_rules = [ConstitutionalRule.HUMAN_RIGHTS, ConstitutionalRule.SECURITY]
        high_rules = [ConstitutionalRule.PRIVACY_PROTECTION, ConstitutionalRule.ACCOUNTABILITY]
        
        if rule in critical_rules:
            return "critical"
        elif rule in high_rules:
            return "high"
        else:
            return "medium"
    
    async def _trigger_critical_alert(self, violation: ConstitutionalViolation) -> None:
        """Trigger critical alert for severe violations"""
        logger.critical(f"🚨 CRITICAL CONSTITUTIONAL VIOLATION: {violation.rule_violated.value}")
        logger.critical(f"👤 Actor: {violation.actor_type}:{violation.actor_id}")
        logger.critical(f"🔒 Action Hash: {violation.action_hash}")
        logger.critical(f"⏰ Timestamp: {violation.timestamp}")
        
        # In production, this would trigger:
        # - Immediate notification to government oversight
        # - System lockdown if necessary
        # - Audit trail creation
        # - Legal documentation
    
    def activate_emergency_override(self, duration_hours: int = 24) -> bool:
        """Activate emergency override for critical situations"""
        try:
            self.emergency_override_enabled = True
            self.emergency_override_start = datetime.utcnow()
            self.emergency_override_duration = timedelta(hours=duration_hours)
            
            logger.warning(f"⚠️ Emergency override activated for {duration_hours} hours")
            return True
            
        except Exception as e:
            logger.error(f"❌ Emergency override activation error: {e}")
            return False
    
    def deactivate_emergency_override(self) -> bool:
        """Deactivate emergency override"""
        try:
            self.emergency_override_enabled = False
            self.emergency_override_start = None
            
            logger.info("✅ Emergency override deactivated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Emergency override deactivation error: {e}")
            return False
    
    def _is_emergency_override_active(self) -> bool:
        """Check if emergency override is still active"""
        if not self.emergency_override_enabled or not self.emergency_override_start:
            return False
        
        elapsed = datetime.utcnow() - self.emergency_override_start
        return elapsed < self.emergency_override_duration
    
    def get_constitution_status(self) -> Dict[str, Any]:
        """Get current constitution status"""
        return {
            "constitution_hash": self.constitution_hash,
            "government_share": self.government_veto_threshold,
            "private_share": self.private_sector_threshold,
            "total_violations": len(self.violation_log),
            "critical_violations": len([v for v in self.violation_log if v.severity == "critical"]),
            "emergency_override_active": self.emergency_override_enabled,
            "emergency_override_remaining": str(self.emergency_override_duration - (datetime.utcnow() - self.emergency_override_start)) if self.emergency_override_start else "0:00:00",
            "sectors_monitored": len(SectorType),
            "actions_monitored": len(ActionType)
        }
    
    def get_violation_report(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent violation report"""
        recent_violations = self.violation_log[-limit:]
        
        return [
            {
                "timestamp": v.timestamp.isoformat(),
                "rule_violated": v.rule_violated.value,
                "action_type": v.action_type.value,
                "sector": v.sector.value,
                "actor_id": v.actor_id,
                "actor_type": v.actor_type,
                "severity": v.severity,
                "action_hash": v.action_hash[:16] + "...",
                "veto_applied": v.veto_applied
            }
            for v in recent_violations
        ]

# Global Dharma-Chakra instance
_dharma_chakra = DharmaChakraConstitution()

async def main():
    """Main entry point for testing"""
    # Test constitutional check
    check_result = await _dharma_chakra.check_action_compliance(
        action_type=ActionType.DATA_ACCESS,
        sector=SectorType.HEALTH,
        actor_id="agent_001",
        actor_type="agent",
        action_details={
            "data_access": {
                "target": "patient_records",
                "without_consent": False
            },
            "user_consent": True
        }
    )
    
    print(f"Compliance Check Result: {check_result.is_compliant}")
    print(f"Confidence Score: {check_result.confidence_score}")
    
    # Get constitution status
    status = _dharma_chakra.get_constitution_status()
    print(f"Constitution Status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
