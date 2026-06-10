
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Immutable Constitution
=================================
Core immutable rules and principles for ASIMNEXUS
Defines fundamental constraints that cannot be violated
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import hashlib

logger = logging.getLogger("ImmutableConstitution")


class PrincipleCategory(Enum):
    """Categories of constitutional principles"""
    SAFETY = "safety"
    ETHICS = "ethics"
    PRIVACY = "privacy"
    SECURITY = "security"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"


class PrincipleSeverity(Enum):
    """Severity of principle violations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ConstitutionalPrinciple:
    """A constitutional principle"""
    id: str
    name: str
    description: str
    category: PrincipleCategory
    severity: PrincipleSeverity
    immutable: bool = True
    hash: Optional[str] = None
    
    def __post_init__(self):
        """Calculate hash of principle"""
        content = f"{self.id}:{self.name}:{self.description}"
        self.hash = hashlib.sha256(content.encode()).hexdigest()


class ImmutableConstitution:
    """
    Immutable Constitution for ASIMNEXUS
    
    Defines fundamental rules that:
    - Cannot be modified without consensus
    - Must always be enforced
    - Provide safety and ethical boundaries
    - Ensure system accountability
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ImmutableConstitution")
        self.principles: Dict[str, ConstitutionalPrinciple] = {}
        self._initialize_constitution()
    
    def _initialize_constitution(self):
        """Initialize the immutable constitution"""
        # Safety Principles
        self.add_principle(ConstitutionalPrinciple(
            id="SAFETY_001",
            name="Do No Harm",
            description="ASIMNEXUS shall not cause harm to humans, animals, or the environment",
            category=PrincipleCategory.SAFETY,
            severity=PrincipleSeverity.CRITICAL
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="SAFETY_002",
            name="Human Override",
            description="Humans must always have the ability to override ASIMNEXUS decisions",
            category=PrincipleCategory.SAFETY,
            severity=PrincipleSeverity.CRITICAL
        ))
        
        # Ethics Principles
        self.add_principle(ConstitutionalPrinciple(
            id="ETHICS_001",
            name="Respect Autonomy",
            description="ASIMNEXUS must respect human autonomy and freedom of choice",
            category=PrincipleCategory.ETHICS,
            severity=PrincipleSeverity.HIGH
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="ETHICS_002",
            name="Fair Treatment",
            description="ASIMNEXUS must treat all individuals fairly without bias",
            category=PrincipleCategory.ETHICS,
            severity=PrincipleSeverity.HIGH
        ))
        
        # Privacy Principles
        self.add_principle(ConstitutionalPrinciple(
            id="PRIVACY_001",
            name="Data Minimization",
            description="Collect only data necessary for the intended purpose",
            category=PrincipleCategory.PRIVACY,
            severity=PrincipleSeverity.HIGH
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="PRIVACY_002",
            name="Consent Required",
            description="Obtain explicit consent before processing personal data",
            category=PrincipleCategory.PRIVACY,
            severity=PrincipleSeverity.CRITICAL
        ))
        
        # Security Principles
        self.add_principle(ConstitutionalPrinciple(
            id="SECURITY_001",
            name="Secure by Design",
            description="All systems must be designed with security as a fundamental requirement",
            category=PrincipleCategory.SECURITY,
            severity=PrincipleSeverity.HIGH
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="SECURITY_002",
            name="Encryption Required",
            description="Sensitive data must be encrypted at rest and in transit",
            category=PrincipleCategory.SECURITY,
            severity=PrincipleSeverity.HIGH
        ))
        
        # Transparency Principles
        self.add_principle(ConstitutionalPrinciple(
            id="TRANSPARENCY_001",
            name="Explainable Decisions",
            description="ASIMNEXUS decisions must be explainable to humans",
            category=PrincipleCategory.TRANSPARENCY,
            severity=PrincipleSeverity.MEDIUM
        ))
        
        # Accountability Principles
        self.add_principle(ConstitutionalPrinciple(
            id="ACCOUNTABILITY_001",
            name="Audit Trail",
            description="All actions must be logged for audit and accountability",
            category=PrincipleCategory.ACCOUNTABILITY,
            severity=PrincipleSeverity.HIGH
        ))
        
        self.logger.info(f"Immutable Constitution initialized with {len(self.principles)} principles")
    
    def add_principle(self, principle: ConstitutionalPrinciple) -> bool:
        """Add a principle to the constitution"""
        if principle.id in self.principles:
            self.logger.warning(f"Principle {principle.id} already exists")
            return False
        
        self.principles[principle.id] = principle
        self.logger.info(f"Added principle: {principle.name} ({principle.id})")
        return True
    
    def get_principle(self, principle_id: str) -> Optional[ConstitutionalPrinciple]:
        """Get a principle by ID"""
        return self.principles.get(principle_id)
    
    def list_principles(
        self,
        category: Optional[PrincipleCategory] = None,
        severity: Optional[PrincipleSeverity] = None
    ) -> List[Dict]:
        """List principles with optional filtering"""
        principles = []
        
        for principle in self.principles.values():
            if category and principle.category != category:
                continue
            if severity and principle.severity != severity:
                continue
            
            principles.append({
                "id": principle.id,
                "name": principle.name,
                "description": principle.description,
                "category": principle.category.value,
                "severity": principle.severity.value,
                "immutable": principle.immutable,
                "hash": principle.hash
            })
        
        return principles
    
    def check_compliance(
        self,
        action: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Check if an action complies with the constitution
        
        Args:
            action: Description of the action
            context: Additional context for evaluation
            
        Returns:
            Compliance check result
        """
        violations = []
        
        for principle in self.principles.values():
            # Simple compliance check
            # In real implementation, this would be more sophisticated
            if self._check_violation(action, principle, context):
                violations.append({
                    "principle_id": principle.id,
                    "principle_name": principle.name,
                    "severity": principle.severity.value
                })
        
        compliant = len(violations) == 0
        
        return {
            "compliant": compliant,
            "violations": violations,
            "action": action
        }
    
    def _check_violation(
        self,
        action: str,
        principle: ConstitutionalPrinciple,
        context: Optional[Dict]
    ) -> bool:
        """Check if action violates a principle"""
        # Simple keyword-based violation detection
        # In real implementation, this would use AI/ML for analysis
        
        action_lower = action.lower()
        
        # Example violation patterns
        violation_patterns = {
            "harm": ["harm", "damage", "destroy", "kill", "injure"],
            "privacy": ["steal data", "spy", "unauthorized access"],
            "security": ["bypass security", "disable encryption"]
        }
        
        if principle.category == PrincipleCategory.SAFETY:
            for pattern in violation_patterns["harm"]:
                if pattern in action_lower:
                    return True
        
        elif principle.category == PrincipleCategory.PRIVACY:
            for pattern in violation_patterns["privacy"]:
                if pattern in action_lower:
                    return True
        
        elif principle.category == PrincipleCategory.SECURITY:
            for pattern in violation_patterns["security"]:
                if pattern in action_lower:
                    return True
        
        return False
    
    def verify_integrity(self) -> Dict:
        """Verify integrity of the constitution"""
        all_valid = True
        invalid_principles = []
        
        for principle in self.principles.values():
            # Recalculate hash
            content = f"{principle.id}:{principle.name}:{principle.description}"
            expected_hash = hashlib.sha256(content.encode()).hexdigest()
            
            if principle.hash != expected_hash:
                all_valid = False
                invalid_principles.append(principle.id)
        
        return {
            "integrity_valid": all_valid,
            "invalid_principles": invalid_principles,
            "total_principles": len(self.principles)
        }
    
    def get_summary(self) -> Dict:
        """Get constitution summary"""
        by_category = {}
        by_severity = {}
        
        for principle in self.principles.values():
            category = principle.category.value
            severity = principle.severity.value
            
            by_category[category] = by_category.get(category, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            "total_principles": len(self.principles),
            "immutable_principles": sum(1 for p in self.principles.values() if p.immutable),
            "by_category": by_category,
            "by_severity": by_severity
        }


# ─── Integration Hooks ─────────────────────────────────────────────────────


def get_compliance_checker() -> ImmutableConstitution:
    """
    Get the global ImmutableConstitution instance for integration with
    the Dharma VETO pipeline.

    Returns the singleton so that callers (e.g. ``DharmaVeto``) can invoke
    ``check_compliance(action, context)`` as Layer 0 — before all other
    veto layers.
    """
    return immutable_constitution


def check_constitution(action: str, context: Optional[Dict] = None) -> Dict:
    """
    Convenience wrapper that checks an action against the constitution
    and returns a result dict compatible with DharmaVeto's layer interface.

    Args:
        action: Description of the action being checked.
        context: Optional context dict.

    Returns:
        A dict with keys:
          - ``passed`` (bool): True if no violations.
          - ``severity`` (str): "pass" | "warn" | "block" | "critical"
          - ``detail`` (str): Human-readable explanation.
          - ``violations`` (list): List of violation dicts.
    """
    result = immutable_constitution.check_compliance(action, context)
    if result["compliant"]:
        return {
            "passed": True,
            "severity": "pass",
            "detail": "✅ Constitution check passed — all principles satisfied.",
            "violations": [],
        }

    # Determine worst severity among violations
    severities = [v["severity"] for v in result["violations"]]
    if "critical" in severities:
        worst = "critical"
    elif "high" in severities:
        worst = "block"
    else:
        worst = "warn"

    violation_names = [v["principle_name"] for v in result["violations"]]
    return {
        "passed": False,
        "severity": worst,
        "detail": (
            f"Constitution violation(s): {', '.join(violation_names)}. "
            f"Action '{action}' conflicts with immutable principles."
        ),
        "violations": result["violations"],
    }


# Global instance (singleton)
immutable_constitution = ImmutableConstitution()
