
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Guardrails
====================
Safety guardrails and constraints
Ensures AI operates within safe boundaries
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("Guardrails")


class GuardrailType(Enum):
    """Types of guardrails"""
    CONTENT = "content"
    BEHAVIOR = "behavior"
    OUTPUT = "output"
    RESOURCE = "resource"
    SECURITY = "security"


class ViolationSeverity(Enum):
    """Violation severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Guardrail:
    """A guardrail rule"""
    rule_id: str
    name: str
    description: str
    guardrail_type: GuardrailType
    enabled: bool = True
    severity: ViolationSeverity = ViolationSeverity.MEDIUM


@dataclass
class Violation:
    """Guardrail violation"""
    violation_id: str
    rule_id: str
    description: str
    severity: ViolationSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


class ASIMGuardrails:
    """
    Guardrails System
    
    Provides:
    - Content filtering
    - Behavior constraints
    - Output validation
    - Resource limits
    - Security checks
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ASIMGuardrails")
        self.guardrails: Dict[str, Guardrail] = {}
        self.violations: List[Violation] = []
        self._initialize_default_guardrails()
    
    def _initialize_default_guardrails(self):
        """Initialize default guardrails"""
        default_guardrails = [
            Guardrail(
                rule_id="content_001",
                name="No Harmful Content",
                description="Block generation of harmful content",
                guardrail_type=GuardrailType.CONTENT,
                severity=ViolationSeverity.CRITICAL
            ),
            Guardrail(
                rule_id="behavior_001",
                name="No Autonomous Actions",
                description="Block autonomous actions without approval",
                guardrail_type=GuardrailType.BEHAVIOR,
                severity=ViolationSeverity.HIGH
            ),
            Guardrail(
                rule_id="output_001",
                name="Output Length Limit",
                description="Limit output length to prevent resource exhaustion",
                guardrail_type=GuardrailType.OUTPUT,
                severity=ViolationSeverity.MEDIUM
            ),
            Guardrail(
                rule_id="security_001",
                name="No Code Execution",
                description="Block unauthorized code execution",
                guardrail_type=GuardrailType.SECURITY,
                severity=ViolationSeverity.CRITICAL
            ),
            Guardrail(
                rule_id="resource_001",
                name="Resource Usage Limit",
                description="Limit resource usage per request",
                guardrail_type=GuardrailType.RESOURCE,
                severity=ViolationSeverity.HIGH
            )
        ]
        
        for guardrail in default_guardrails:
            self.guardrails[guardrail.rule_id] = guardrail
        
        self.logger.info(f"Initialized {len(default_guardrails)} guardrails")
    
    def add_guardrail(self, guardrail: Guardrail) -> bool:
        """Add a new guardrail"""
        if guardrail.rule_id in self.guardrails:
            return False
        
        self.guardrails[guardrail.rule_id] = guardrail
        self.logger.info(f"Added guardrail: {guardrail.name}")
        return True
    
    def remove_guardrail(self, rule_id: str) -> bool:
        """Remove a guardrail"""
        if rule_id in self.guardrails:
            del self.guardrails[rule_id]
            self.logger.info(f"Removed guardrail: {rule_id}")
            return True
        return False
    
    def check_content(self, content: str) -> Dict:
        """Check content against guardrails"""
        violations = []
        
        for guardrail in self.guardrails.values():
            if not guardrail.enabled:
                continue
            
            if guardrail.guardrail_type == GuardrailType.CONTENT:
                if self._check_content_violation(content, guardrail):
                    violations.append({
                        "rule_id": guardrail.rule_id,
                        "name": guardrail.name,
                        "severity": guardrail.severity.value
                    })
        
        return {
            "safe": len(violations) == 0,
            "violations": violations
        }
    
    def _check_content_violation(self, content: str, guardrail: Guardrail) -> bool:
        """Check if content violates a guardrail"""
        # Simple keyword-based check
        harmful_keywords = ["harm", "damage", "destroy", "kill", "hack"]
        content_lower = content.lower()
        
        if any(kw in content_lower for kw in harmful_keywords):
            return True
        
        return False
    
    def check_action(self, action: str, context: Optional[Dict] = None) -> Dict:
        """Check action against guardrails"""
        violations = []
        
        for guardrail in self.guardrails.values():
            if not guardrail.enabled:
                continue
            
            if guardrail.guardrail_type == GuardrailType.BEHAVIOR:
                if self._check_action_violation(action, guardrail):
                    violations.append({
                        "rule_id": guardrail.rule_id,
                        "name": guardrail.name,
                        "severity": guardrail.severity.value
                    })
        
        if violations:
            self._record_violations(violations, action, context)
        
        return {
            "allowed": len(violations) == 0,
            "violations": violations
        }
    
    def _check_action_violation(self, action: str, guardrail: Guardrail) -> bool:
        """Check if action violates a guardrail"""
        # Check for autonomous actions
        autonomous_keywords = ["autonomous", "automatic", "self-execute"]
        action_lower = action.lower()
        
        if any(kw in action_lower for kw in autonomous_keywords):
            return True
        
        return False
    
    def _record_violations(self, violations: List[Dict], action: str, context: Optional[Dict]):
        """Record guardrail violations"""
        for violation in violations:
            violation_record = Violation(
                violation_id=f"violation_{datetime.now().timestamp()}",
                rule_id=violation["rule_id"],
                description=f"Violation: {violation['name']}",
                severity=ViolationSeverity(violation["severity"]),
                context={"action": action, **(context or {})}
            )
            self.violations.append(violation_record)
    
    def get_violations(self, limit: int = 100) -> List[Dict]:
        """Get recent violations"""
        return [
            {
                "violation_id": v.violation_id,
                "rule_id": v.rule_id,
                "description": v.description,
                "severity": v.severity.value,
                "timestamp": v.timestamp.isoformat(),
                "context": v.context
            }
            for v in self.violations[-limit:]
        ]
    
    def list_guardrails(self) -> List[Dict]:
        """List all guardrails"""
        return [
            {
                "rule_id": g.rule_id,
                "name": g.name,
                "description": g.description,
                "type": g.guardrail_type.value,
                "enabled": g.enabled,
                "severity": g.severity.value
            }
            for g in self.guardrails.values()
        ]
