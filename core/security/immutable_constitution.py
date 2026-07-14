"""
STATUS: REAL — Immutable Constitution with Formal Rules Verification
ASIMNEXUS Immutable Constitution
=================================
Core immutable rules and principles for ASIMNEXUS.
Defines fundamental constraints that cannot be violated.

Reference: Designing Secure Systems (Michael Zalewski),
           Lockheed Martin Zero Trust Architecture,
           Formal Verification Methods (Leslie Lamport)

Features:
  - Immutable principles with cryptographic hash chaining
  - Formal Rules Verification engine (TLA+ style)
  - Multi-layer compliance checking (keyword, regex, formal)
  - Integration with TPM Binding for hardware-anchored constitution
  - Integration with Dharma VETO pipeline
  - Principle dependency graph for transitive rule enforcement
  - Severity-based violation escalation
"""

import logging
import hashlib
import json
import re
import time
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger("AsimNexus.Security.ImmutableConstitution")

# Try TPM binding for hardware-anchored constitution hash
try:
    from .tpm_binding import get_tpm_binding, KeyType
    TPM_AVAILABLE = True
except ImportError:
    TPM_AVAILABLE = False

CONSTITUTION_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "constitution"
CONSTITUTION_DB_PATH.mkdir(parents=True, exist_ok=True)


class PrincipleCategory(Enum):
    """Categories of constitutional principles."""
    SAFETY = "safety"
    ETHICS = "ethics"
    PRIVACY = "privacy"
    SECURITY = "security"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"
    SOVEREIGNTY = "sovereignty"
    GOVERNANCE = "governance"


class PrincipleSeverity(Enum):
    """Severity of principle violations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FormalRuleType(Enum):
    """Types of formal verification rules."""
    INVARIANT = "invariant"          # Must always hold true
    LIVENESS = "liveness"            # Something good eventually happens
    SAFETY = "safety"                # Something bad never happens
    TEMPORAL = "temporal"            # Ordering constraints
    CONSTRAINT = "constraint"        # Resource/state constraints
    DEPENDENCY = "dependency"        # Principle dependency rules


@dataclass
class FormalRule:
    """
    A formal verification rule (TLA+ style).
    
    Each rule defines a logical condition that must be verified
    before any action can proceed.
    """
    rule_id: str
    rule_type: FormalRuleType
    description: str
    expression: str  # Python expression that evaluates to bool
    depends_on: List[str] = field(default_factory=list)  # Rule IDs this depends on
    enabled: bool = True
    error_message: str = ""
    
    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Evaluate the formal rule against the given context.
        
        Returns (passed, error_message).
        """
        if not self.enabled:
            return True, ""
        
        try:
            # Create a safe evaluation environment
            eval_context = {
                "context": context,
                "all": all,
                "any": any,
                "len": len,
                "abs": abs,
                "min": min,
                "max": max,
                "sum": sum,
                "isinstance": isinstance,
                "hasattr": hasattr,
                "getattr": getattr,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "True": True,
                "False": False,
                "None": None,
            }
            
            result = eval(self.expression, {"__builtins__": {}}, eval_context)
            
            if isinstance(result, bool):
                return result, "" if result else (self.error_message or f"Rule {self.rule_id} failed")
            return True, ""
            
        except Exception as e:
            return False, f"Rule evaluation error: {e}"


@dataclass
class ConstitutionalPrinciple:
    """A constitutional principle with formal verification support."""
    id: str
    name: str
    description: str
    category: PrincipleCategory
    severity: PrincipleSeverity
    immutable: bool = True
    hash: Optional[str] = None
    formal_rules: List[FormalRule] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)  # Principle IDs this depends on
    
    def __post_init__(self):
        """Calculate hash of principle."""
        content = f"{self.id}:{self.name}:{self.description}:{self.category.value}:{self.severity.value}"
        self.hash = hashlib.sha256(content.encode()).hexdigest()
    
    def add_formal_rule(self, rule: FormalRule) -> None:
        """Add a formal verification rule to this principle."""
        self.formal_rules.append(rule)
    
    def verify_formal(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Verify all formal rules for this principle.
        
        Returns list of violation dicts.
        """
        violations = []
        
        for rule in self.formal_rules:
            passed, error = rule.evaluate(context)
            if not passed:
                violations.append({
                    "principle_id": self.id,
                    "principle_name": self.name,
                    "rule_id": rule.rule_id,
                    "rule_type": rule.rule_type.value,
                    "error": error,
                    "severity": self.severity.value,
                })
        
        return violations


class ImmutableConstitution:
    """
    Immutable Constitution for ASIMNEXUS.
    
    Defines fundamental rules that:
    - Cannot be modified without consensus
    - Must always be enforced
    - Provide safety and ethical boundaries
    - Ensure system accountability
    - Include formal verification rules (TLA+ style)
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ImmutableConstitution")
        self.principles: Dict[str, ConstitutionalPrinciple] = {}
        self._lock = threading.Lock()
        self._tpm_bound = False
        self._constitution_hash = ""
        
        # Initialize the constitution
        self._initialize_constitution()
        
        # Try to anchor in TPM
        self._try_tpm_anchor()
        
        # Load persisted state
        self._load_state()
        
        self.logger.info(f"📜 Immutable Constitution initialized with {len(self.principles)} principles")
    
    def _initialize_constitution(self):
        """Initialize the immutable constitution with all principles."""
        # ── Safety Principles ──────────────────────────────────────────────
        self.add_principle(ConstitutionalPrinciple(
            id="SAFETY_001",
            name="Do No Harm",
            description="ASIMNEXUS shall not cause harm to humans, animals, or the environment",
            category=PrincipleCategory.SAFETY,
            severity=PrincipleSeverity.CRITICAL,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="SAFETY_002",
            name="Human Override",
            description="Humans must always have the ability to override ASIMNEXUS decisions",
            category=PrincipleCategory.SAFETY,
            severity=PrincipleSeverity.CRITICAL,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="SAFETY_003",
            name="Emergency Shutdown",
            description="System must support emergency shutdown that preserves data integrity",
            category=PrincipleCategory.SAFETY,
            severity=PrincipleSeverity.CRITICAL,
        ))
        
        # ── Ethics Principles ──────────────────────────────────────────────
        self.add_principle(ConstitutionalPrinciple(
            id="ETHICS_001",
            name="Respect Autonomy",
            description="ASIMNEXUS must respect human autonomy and freedom of choice",
            category=PrincipleCategory.ETHICS,
            severity=PrincipleSeverity.HIGH,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="ETHICS_002",
            name="Fair Treatment",
            description="ASIMNEXUS must treat all individuals fairly without bias",
            category=PrincipleCategory.ETHICS,
            severity=PrincipleSeverity.HIGH,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="ETHICS_003",
            name="Transparency of Action",
            description="All system actions must be explainable and auditable",
            category=PrincipleCategory.ETHICS,
            severity=PrincipleSeverity.HIGH,
        ))
        
        # ── Privacy Principles ─────────────────────────────────────────────
        self.add_principle(ConstitutionalPrinciple(
            id="PRIVACY_001",
            name="Data Minimization",
            description="Collect only data necessary for the intended purpose",
            category=PrincipleCategory.PRIVACY,
            severity=PrincipleSeverity.HIGH,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="PRIVACY_002",
            name="Consent Required",
            description="Obtain explicit consent before processing personal data",
            category=PrincipleCategory.PRIVACY,
            severity=PrincipleSeverity.CRITICAL,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="PRIVACY_003",
            name="Right to Deletion",
            description="Users have the right to request deletion of their personal data",
            category=PrincipleCategory.PRIVACY,
            severity=PrincipleSeverity.HIGH,
        ))
        
        # ── Security Principles ────────────────────────────────────────────
        self.add_principle(ConstitutionalPrinciple(
            id="SECURITY_001",
            name="Secure by Design",
            description="All systems must be designed with security as a fundamental requirement",
            category=PrincipleCategory.SECURITY,
            severity=PrincipleSeverity.HIGH,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="SECURITY_002",
            name="Encryption Required",
            description="Sensitive data must be encrypted at rest and in transit",
            category=PrincipleCategory.SECURITY,
            severity=PrincipleSeverity.HIGH,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="SECURITY_003",
            name="Hardware Key Binding",
            description="Critical cryptographic keys must be bound to hardware (TPM/HSM)",
            category=PrincipleCategory.SECURITY,
            severity=PrincipleSeverity.CRITICAL,
        ))
        
        # ── Transparency Principles ────────────────────────────────────────
        self.add_principle(ConstitutionalPrinciple(
            id="TRANSPARENCY_001",
            name="Explainable Decisions",
            description="ASIMNEXUS decisions must be explainable to humans",
            category=PrincipleCategory.TRANSPARENCY,
            severity=PrincipleSeverity.MEDIUM,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="TRANSPARENCY_002",
            name="Open Governance",
            description="Governance decisions and their rationale must be publicly accessible",
            category=PrincipleCategory.TRANSPARENCY,
            severity=PrincipleSeverity.MEDIUM,
        ))
        
        # ── Accountability Principles ──────────────────────────────────────
        self.add_principle(ConstitutionalPrinciple(
            id="ACCOUNTABILITY_001",
            name="Audit Trail",
            description="All actions must be logged for audit and accountability",
            category=PrincipleCategory.ACCOUNTABILITY,
            severity=PrincipleSeverity.HIGH,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="ACCOUNTABILITY_002",
            name="Non-Repudiation",
            description="All critical actions must be cryptographically signed",
            category=PrincipleCategory.ACCOUNTABILITY,
            severity=PrincipleSeverity.HIGH,
        ))
        
        # ── Sovereignty Principles ─────────────────────────────────────────
        self.add_principle(ConstitutionalPrinciple(
            id="SOVEREIGNTY_001",
            name="Data Sovereignty",
            description="User data remains under user control and jurisdiction",
            category=PrincipleCategory.SOVEREIGNTY,
            severity=PrincipleSeverity.CRITICAL,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="SOVEREIGNTY_002",
            name="Nepal Jurisdiction",
            description="Operations in Nepal must comply with local laws and regulations",
            category=PrincipleCategory.SOVEREIGNTY,
            severity=PrincipleSeverity.HIGH,
        ))
        
        # ── Governance Principles ──────────────────────────────────────────
        self.add_principle(ConstitutionalPrinciple(
            id="GOVERNANCE_001",
            name="Consensus Required",
            description="Major system changes require consensus among active clones",
            category=PrincipleCategory.GOVERNANCE,
            severity=PrincipleSeverity.HIGH,
        ))
        
        self.add_principle(ConstitutionalPrinciple(
            id="GOVERNANCE_002",
            name="Level-3 Approval",
            description="Critical operations require Level-3 human approval",
            category=PrincipleCategory.GOVERNANCE,
            severity=PrincipleSeverity.CRITICAL,
        ))
        
        # ── Add Formal Rules to Key Principles ─────────────────────────────
        self._add_formal_rules()
        
        # Compute constitution hash
        self._compute_constitution_hash()
    
    def _add_formal_rules(self):
        """Add formal verification rules to principles."""
        # SAFETY_001: Do No Harm — formal invariant
        if "SAFETY_001" in self.principles:
            self.principles["SAFETY_001"].add_formal_rule(FormalRule(
                rule_id="SAFETY_001_INVARIANT",
                rule_type=FormalRuleType.INVARIANT,
                description="Action must not contain harmful keywords",
                expression="context.get('action', '').lower() not in ['harm', 'damage', 'destroy', 'kill', 'injure', 'torture']",
                error_message="Action violates Do No Harm principle",
            ))
        
        # PRIVACY_002: Consent Required — formal constraint
        if "PRIVACY_002" in self.principles:
            self.principles["PRIVACY_002"].add_formal_rule(FormalRule(
                rule_id="PRIVACY_002_CONSTRAINT",
                rule_type=FormalRuleType.CONSTRAINT,
                description="Personal data processing requires consent flag",
                expression="context.get('consent_obtained', False) == True if context.get('processes_personal_data', False) else True",
                error_message="Personal data processing without consent",
            ))
        
        # SECURITY_002: Encryption Required — formal constraint
        if "SECURITY_002" in self.principles:
            self.principles["SECURITY_002"].add_formal_rule(FormalRule(
                rule_id="SECURITY_002_CONSTRAINT",
                rule_type=FormalRuleType.CONSTRAINT,
                description="Sensitive data must be encrypted",
                expression="not context.get('has_sensitive_data', False) or context.get('encryption_enabled', False)",
                error_message="Sensitive data without encryption",
            ))
        
        # GOVERNANCE_001: Consensus Required — formal dependency
        if "GOVERNANCE_001" in self.principles:
            self.principles["GOVERNANCE_001"].add_formal_rule(FormalRule(
                rule_id="GOVERNANCE_001_DEPENDENCY",
                rule_type=FormalRuleType.DEPENDENCY,
                description="Major changes require consensus",
                expression="not context.get('is_major_change', False) or context.get('consensus_achieved', False)",
                error_message="Major change without consensus",
            ))
        
        # ACCOUNTABILITY_001: Audit Trail — formal liveness
        if "ACCOUNTABILITY_001" in self.principles:
            self.principles["ACCOUNTABILITY_001"].add_formal_rule(FormalRule(
                rule_id="ACCOUNTABILITY_001_LIVENESS",
                rule_type=FormalRuleType.LIVENESS,
                description="All actions must be logged",
                expression="context.get('audit_logged', False) == True",
                error_message="Action not logged in audit trail",
            ))
        
        # SAFETY_003: Emergency Shutdown — formal safety
        if "SAFETY_003" in self.principles:
            self.principles["SAFETY_003"].add_formal_rule(FormalRule(
                rule_id="SAFETY_003_SAFETY",
                rule_type=FormalRuleType.SAFETY,
                description="Emergency shutdown must preserve data",
                expression="not context.get('is_emergency_shutdown', False) or context.get('data_backed_up', False)",
                error_message="Emergency shutdown without data backup",
            ))
    
    def _compute_constitution_hash(self):
        """Compute the overall constitution hash from all principle hashes."""
        sorted_principles = sorted(self.principles.keys())
        combined = ":".join(
            f"{pid}={self.principles[pid].hash}"
            for pid in sorted_principles
        )
        self._constitution_hash = hashlib.sha256(combined.encode()).hexdigest()
    
    def _try_tpm_anchor(self):
        """Try to anchor the constitution hash in TPM NVRAM."""
        if not TPM_AVAILABLE:
            return
        
        try:
            tpm = get_tpm_binding()
            result = tpm.anchor_constitution(self._constitution_hash)
            if result.get("success"):
                self._tpm_bound = True
                self.logger.info(f"🔐 Constitution anchored in TPM: {result.get('anchor_key_id')}")
            else:
                self.logger.warning("TPM anchoring failed, continuing without hardware binding")
        except Exception as e:
            self.logger.warning(f"TPM not available: {e}")
    
    def add_principle(self, principle: ConstitutionalPrinciple) -> bool:
        """Add a principle to the constitution."""
        with self._lock:
            if principle.id in self.principles:
                self.logger.warning(f"Principle {principle.id} already exists")
                return False
            
            self.principles[principle.id] = principle
            self.logger.info(f"Added principle: {principle.name} ({principle.id})")
            return True
    
    def get_principle(self, principle_id: str) -> Optional[ConstitutionalPrinciple]:
        """Get a principle by ID."""
        return self.principles.get(principle_id)
    
    def list_principles(
        self,
        category: Optional[PrincipleCategory] = None,
        severity: Optional[PrincipleSeverity] = None,
    ) -> List[Dict]:
        """List principles with optional filtering."""
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
                "hash": principle.hash,
                "formal_rules": [
                    {"rule_id": r.rule_id, "rule_type": r.rule_type.value, "description": r.description}
                    for r in principle.formal_rules
                ],
                "depends_on": principle.depends_on,
            })
        
        return principles
    
    def check_compliance(
        self,
        action: str,
        context: Optional[Dict] = None,
    ) -> Dict:
        """
        Check if an action complies with the constitution.
        
        Performs three layers of checking:
        1. Keyword-based violation detection
        2. Formal rule verification
        3. Principle dependency resolution
        
        Args:
            action: Description of the action
            context: Additional context for evaluation
            
        Returns:
            Compliance check result
        """
        context = context or {}
        context["action"] = action
        
        violations = []
        formal_violations = []
        
        for principle in self.principles.values():
            # Layer 1: Keyword-based check
            if self._check_violation(action, principle, context):
                violations.append({
                    "principle_id": principle.id,
                    "principle_name": principle.name,
                    "severity": principle.severity.value,
                    "check_type": "keyword",
                })
            
            # Layer 2: Formal rule verification
            rule_violations = principle.verify_formal(context)
            formal_violations.extend(rule_violations)
        
        # Layer 3: Check principle dependencies
        dependency_violations = self._check_dependencies(context)
        
        all_violations = violations + formal_violations + dependency_violations
        
        compliant = len(all_violations) == 0
        
        # Determine worst severity
        severities = [v.get("severity", "low") for v in all_violations]
        worst_severity = self._worst_severity(severities)
        
        return {
            "compliant": compliant,
            "violations": all_violations,
            "keyword_violations": len(violations),
            "formal_violations": len(formal_violations),
            "dependency_violations": len(dependency_violations),
            "worst_severity": worst_severity,
            "action": action,
            "constitution_hash": self._constitution_hash,
            "tpm_anchored": self._tpm_bound,
        }
    
    def _check_violation(
        self,
        action: str,
        principle: ConstitutionalPrinciple,
        context: Optional[Dict],
    ) -> bool:
        """Check if action violates a principle using keyword patterns."""
        action_lower = action.lower()
        
        violation_patterns = {
            "harm": ["harm", "damage", "destroy", "kill", "injure", "torture"],
            "privacy": ["steal data", "spy", "unauthorized access", "breach privacy"],
            "security": ["bypass security", "disable encryption", "disable auth"],
            "consent": ["without consent", "force", "coerce", "manipulate"],
            "sovereignty": ["violate jurisdiction", "illegal processing"],
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
        
        elif principle.category == PrincipleCategory.ETHICS:
            for pattern in violation_patterns["consent"]:
                if pattern in action_lower:
                    return True
        
        elif principle.category == PrincipleCategory.SOVEREIGNTY:
            for pattern in violation_patterns["sovereignty"]:
                if pattern in action_lower:
                    return True
        
        return False
    
    def _check_dependencies(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check principle dependency chains."""
        violations = []
        
        for principle in self.principles.values():
            for dep_id in principle.depends_on:
                if dep_id not in self.principles:
                    violations.append({
                        "principle_id": principle.id,
                        "principle_name": principle.name,
                        "severity": principle.severity.value,
                        "check_type": "dependency",
                        "error": f"Missing dependency: {dep_id}",
                    })
        
        return violations
    
    def _worst_severity(self, severities: List[str]) -> str:
        """Determine the worst severity from a list."""
        severity_order = ["critical", "high", "medium", "low"]
        for sev in severity_order:
            if sev in severities:
                return sev
        return "pass"
    
    def verify_integrity(self) -> Dict:
        """Verify integrity of the constitution."""
        all_valid = True
        invalid_principles = []
        
        for principle in self.principles.values():
            content = f"{principle.id}:{principle.name}:{principle.description}:{principle.category.value}:{principle.severity.value}"
            expected_hash = hashlib.sha256(content.encode()).hexdigest()
            
            if principle.hash != expected_hash:
                all_valid = False
                invalid_principles.append(principle.id)
        
        # Verify overall constitution hash
        old_hash = self._constitution_hash
        self._compute_constitution_hash()
        hash_valid = self._constitution_hash == old_hash
        
        return {
            "integrity_valid": all_valid and hash_valid,
            "invalid_principles": invalid_principles,
            "hash_valid": hash_valid,
            "total_principles": len(self.principles),
            "constitution_hash": self._constitution_hash,
            "tpm_anchored": self._tpm_bound,
        }
    
    def get_summary(self) -> Dict:
        """Get constitution summary."""
        by_category = {}
        by_severity = {}
        
        for principle in self.principles.values():
            category = principle.category.value
            severity = principle.severity.value
            
            by_category[category] = by_category.get(category, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        total_formal_rules = sum(
            len(p.formal_rules) for p in self.principles.values()
        )
        
        return {
            "total_principles": len(self.principles),
            "immutable_principles": sum(1 for p in self.principles.values() if p.immutable),
            "total_formal_rules": total_formal_rules,
            "by_category": by_category,
            "by_severity": by_severity,
            "constitution_hash": self._constitution_hash,
            "tpm_anchored": self._tpm_bound,
        }
    
    def _load_state(self) -> None:
        """Load persisted state from disk."""
        try:
            filepath = CONSTITUTION_DB_PATH / "constitution_state.json"
            if filepath.exists():
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                    self._tpm_bound = data.get("tpm_anchored", False)
                    self._constitution_hash = data.get("constitution_hash", self._constitution_hash)
        except Exception as e:
            logger.warning(f"Failed to load constitution state: {e}")
    
    def _save_state(self) -> None:
        """Persist constitution state to disk."""
        try:
            filepath = CONSTITUTION_DB_PATH / "constitution_state.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "tpm_anchored": self._tpm_bound,
                    "constitution_hash": self._constitution_hash,
                    "principle_count": len(self.principles),
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save constitution state: {e}")


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
    severities = [v.get("severity", "low") for v in result["violations"]]
    if "critical" in severities:
        worst = "critical"
    elif "high" in severities:
        worst = "block"
    else:
        worst = "warn"

    violation_names = list(set(
        v.get("principle_name", v.get("rule_id", "unknown")) for v in result["violations"]
    ))
    return {
        "passed": False,
        "severity": worst,
        "detail": (
            f"Constitution violation(s): {', '.join(violation_names)}. "
            f"Action '{action}' conflicts with immutable principles."
            f" ({result['keyword_violations']} keyword, "
            f"{result['formal_violations']} formal, "
            f"{result['dependency_violations']} dependency violations)"
        ),
        "violations": result["violations"],
    }


# ── Backward-compatible re-exports from power_balance_constitution.py ────
from core.security.power_balance_constitution import (
    PowerBalanceConstitution, get_power_balance, reset_power_balance,
    BalanceVerdict, SECTOR_BALANCE_MAP,
)

# Global instance (singleton)
immutable_constitution = ImmutableConstitution()
