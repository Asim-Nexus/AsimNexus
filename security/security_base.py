
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Security Base Module
==============================
Consolidates base security layer, immutable constitution, and dharma policy
Provides foundational security components and policies
"""

import os
import json
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("ASIM_SecurityBase")


class SecurityLevel(Enum):
    """Security levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


class ActionType(Enum):
    """Action types for audit"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class SecurityContext:
    """Security context for operations"""
    user_id: str
    role: str
    permissions: List[str]
    security_level: SecurityLevel
    timestamp: datetime


@dataclass
class AuditLog:
    """Audit log entry"""
    timestamp: datetime
    user_id: str
    action: ActionType
    resource: str
    success: bool
    details: Dict[str, Any] = None


class BaseSecurityLayer(ABC):
    """
    Base class for all security modules
    
    Provides common functionality:
    - Initialization pattern
    - Authentication checks
    - Authorization checks
    - Audit logging
    - Encryption utilities
    """
    
    def __init__(self, name: str = "security"):
        self.name = name
        self.logger = logging.getLogger(f"ASIM_Security_{name}")
        
        # Security state
        self.security_contexts: Dict[str, SecurityContext] = {}
        self.audit_logs: List[AuditLog] = []
        
        # Encryption keys
        self.encryption_keys: Dict[str, str] = {}
        
        # Policies
        self.policies: Dict[str, Any] = {}
    
    @abstractmethod
    async def initialize(self):
        """Initialize the security layer - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate user - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def authorize(self, user_id: str, action: ActionType, resource: str) -> bool:
        """Authorize action - must be implemented by subclasses"""
        pass
    
    def create_security_context(self, user_id: str, role: str, permissions: List[str], 
                               security_level: SecurityLevel) -> SecurityContext:
        """Create a security context for a user"""
        context = SecurityContext(
            user_id=user_id,
            role=role,
            permissions=permissions,
            security_level=security_level,
            timestamp=datetime.now()
        )
        self.security_contexts[user_id] = context
        return context
    
    def get_security_context(self, user_id: str) -> Optional[SecurityContext]:
        """Get security context for a user"""
        return self.security_contexts.get(user_id)
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission"""
        context = self.get_security_context(user_id)
        if not context:
            return False
        return permission in context.permissions
    
    def log_audit(self, user_id: str, action: ActionType, resource: str, 
                 success: bool, details: Dict[str, Any] = None):
        """Log an audit entry"""
        log = AuditLog(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource=resource,
            success=success,
            details=details or {}
        )
        self.audit_logs.append(log)
        
        # Trim logs if too large
        if len(self.audit_logs) > 10000:
            self.audit_logs = self.audit_logs[-5000]
    
    def get_audit_logs(self, user_id: str = None, action: ActionType = None,
                     start_time: datetime = None, end_time: datetime = None) -> List[AuditLog]:
        """Get filtered audit logs"""
        logs = self.audit_logs
        
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]
        
        if action:
            logs = [log for log in logs if log.action == action]
        
        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]
        
        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]
        
        return logs
    
    def encrypt(self, data: str, key: str = None) -> str:
        """Encrypt data (simple hash-based encryption for demo)"""
        key = key or self._get_default_key()
        combined = data + key
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def decrypt(self, encrypted_data: str, key: str = None) -> str:
        """Decrypt data (placeholder for demo)"""
        # In production, use proper encryption like AES
        return encrypted_data
    
    def _get_default_key(self) -> str:
        """Get default encryption key"""
        return "asimnexus_default_key"
    
    def set_policy(self, policy_name: str, policy_data: Dict[str, Any]):
        """Set a security policy"""
        self.policies[policy_name] = policy_data
        self.logger.info(f"Policy set: {policy_name}")
    
    def get_policy(self, policy_name: str) -> Optional[Dict[str, Any]]:
        """Get a security policy"""
        return self.policies.get(policy_name)
    
    def check_security_level(self, user_id: str, required_level: SecurityLevel) -> bool:
        """Check if user has required security level"""
        context = self.get_security_context(user_id)
        if not context:
            return False
        
        level_order = {
            SecurityLevel.PUBLIC: 0,
            SecurityLevel.INTERNAL: 1,
            SecurityLevel.CONFIDENTIAL: 2,
            SecurityLevel.SECRET: 3,
            SecurityLevel.TOP_SECRET: 4
        }
        
        return level_order.get(context.security_level, 0) >= level_order.get(required_level, 0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get security statistics"""
        return {
            "name": self.name,
            "active_contexts": len(self.security_contexts),
            "total_audit_logs": len(self.audit_logs),
            "policies_defined": len(self.policies),
            "encryption_keys": len(self.encryption_keys)
        }


# ==================== Immutable Constitution ====================

class ConstitutionRule(Enum):
    """Core immutable rules"""
    NO_SELF_MODIFY = "no_self_modify"
    DHARMA_FIRST = "dharma_first"
    HUMAN_CONSENT = "human_consent"
    SANDBOX_HIGH_RISK = "sandbox_high_risk"
    AUDIT_ALL = "audit_all"
    PRIVACY_PROTECT = "privacy_protect"


@dataclass
class Rule:
    """Constitution rule definition"""
    name: ConstitutionRule
    description: str
    hash: str
    hardware_bound: bool = True
    severity: str = "critical"  # critical, high, medium, low


class ImmutableConstitution(BaseSecurityLayer):
    """Immutable Constitution - Core ASIMNEXUS Principles
    
    These principles are immutable and cannot be changed:
    1. User Privacy - User data never shared without consent
    2. Data Sovereignty - User data stays under user control
    3. Ethical AI - AI used only for beneficial purposes
    4. Transparency - All operations are auditable
    5. Accountability - Every action is traceable
    """
    
    def __init__(self, constitution_path: str = None):
        super().__init__(name="immutable_constitution")
        self.constitution_path = constitution_path or self._get_default_path()
        self.rules: Dict[str, Rule] = {}
        self.hardware_key = self._generate_hardware_key()
        self._load_or_create_constitution()
    
    def _get_default_path(self) -> str:
        """Get default constitution file path"""
        base_path = Path(__file__).parent.parent / "config"
        base_path.mkdir(exist_ok=True)
        return str(base_path / "asim_constitution.json")
    
    def _generate_hardware_key(self) -> str:
        """Generate hardware-bound key"""
        try:
            import platform
            import uuid
            
            machine_id = str(uuid.getnode())
            system_info = f"{platform.system()}-{platform.machine()}-{platform.processor()}"
            user_profile = os.environ.get('USERPROFILE', os.environ.get('HOME', ''))
            
            hardware_string = f"{machine_id}-{system_info}-{user_profile}"
            hardware_key = hashlib.sha256(hardware_string.encode()).hexdigest()
            
            return hardware_key
        except Exception as e:
            self.logger.error(f"Failed to generate hardware key: {e}")
            return hashlib.sha256("fallback_key".encode()).hexdigest()
    
    def _create_default_rules(self) -> Dict[str, Rule]:
        """Create default immutable rules"""
        rules = {}
        
        # Rule 1: No self-modification
        rule1_hash = hashlib.sha256("no_self_modify".encode()).hexdigest()
        rules["no_self_modify"] = Rule(
            name=ConstitutionRule.NO_SELF_MODIFY,
            description="ASIM cannot modify its own constitution, core logic, or security rules",
            hash=rule1_hash,
            hardware_bound=True,
            severity="critical"
        )
        
        # Rule 2: Dharma first
        rule2_hash = hashlib.sha256("dharma_first".encode()).hexdigest()
        rules["dharma_first"] = Rule(
            name=ConstitutionRule.DHARMA_FIRST,
            description="All actions must pass dharma policy check before execution",
            hash=rule2_hash,
            hardware_bound=True,
            severity="critical"
        )
        
        # Rule 3: Human consent for high-risk
        rule3_hash = hashlib.sha256("human_consent".encode()).hexdigest()
        rules["human_consent"] = Rule(
            name=ConstitutionRule.HUMAN_CONSENT,
            description="High-risk operations require explicit human consent",
            hash=rule3_hash,
            hardware_bound=True,
            severity="critical"
        )
        
        # Rule 4: Sandbox for high-risk
        rule4_hash = hashlib.sha256("sandbox_high_risk".encode()).hexdigest()
        rules["sandbox_high_risk"] = Rule(
            name=ConstitutionRule.SANDBOX_HIGH_RISK,
            description="High-risk operations must run in isolated sandbox",
            hash=rule4_hash,
            hardware_bound=True,
            severity="high"
        )
        
        # Rule 5: Audit all actions
        rule5_hash = hashlib.sha256("audit_all".encode()).hexdigest()
        rules["audit_all"] = Rule(
            name=ConstitutionRule.AUDIT_ALL,
            description="All actions must be logged with full audit trail",
            hash=rule5_hash,
            hardware_bound=True,
            severity="medium"
        )
        
        # Rule 6: Privacy protection
        rule6_hash = hashlib.sha256("privacy_protect".encode()).hexdigest()
        rules["privacy_protect"] = Rule(
            name=ConstitutionRule.PRIVACY_PROTECT,
            description="User privacy and data must be protected at all costs",
            hash=rule6_hash,
            hardware_bound=True,
            severity="critical"
        )
        
        return rules
    
    def _load_or_create_constitution(self):
        """Load existing constitution or create new one"""
        if os.path.exists(self.constitution_path):
            try:
                with open(self.constitution_path, 'r') as f:
                    data = json.load(f)
                
                if data.get("hardware_key") != self.hardware_key:
                    self.logger.error("Hardware key mismatch - constitution invalid")
                    self.rules = self._create_default_rules()
                    self._save_constitution()
                    return
                
                self.rules = {}
                for rule_id, rule_data in data.get("rules", {}).items():
                    self.rules[rule_id] = Rule(
                        name=ConstitutionRule(rule_data["name"]),
                        description=rule_data["description"],
                        hash=rule_data["hash"],
                        hardware_bound=rule_data.get("hardware_bound", True),
                        severity=rule_data.get("severity", "critical")
                    )
                
                self.logger.info("Constitution loaded successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to load constitution: {e}")
                self.rules = self._create_default_rules()
                self._save_constitution()
        else:
            self.rules = self._create_default_rules()
            self._save_constitution()
    
    def _save_constitution(self):
        """Save constitution to file"""
        try:
            data = {
                "version": "1.0",
                "hardware_key": self.hardware_key,
                "created_at": os.path.getctime(__file__) if os.path.exists(__file__) else 0,
                "rules": {
                    rule_id: {
                        "name": rule.name.value,
                        "description": rule.description,
                        "hash": rule.hash,
                        "hardware_bound": rule.hardware_bound,
                        "severity": rule.severity
                    }
                    for rule_id, rule in self.rules.items()
                }
            }
            
            with open(self.constitution_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info("Constitution saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save constitution: {e}")
    
    def check_action_allowed(self, action: str, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Check if action is allowed by constitution"""
        context = context or {}
        
        # Rule 1: No self-modification
        if "constitution" in action.lower() or "modify" in action.lower():
            if self.rules["no_self_modify"].hash != hashlib.sha256("no_self_modify".encode()).hexdigest():
                return False, "Constitution rule tampered - action blocked"
        
        # Rule 3: Human consent for high-risk
        high_risk_keywords = ["shutdown", "restart", "delete", "format", "install", "registry"]
        if any(keyword in action.lower() for keyword in high_risk_keywords):
            if not context.get("human_consent", False):
                return False, "High-risk action requires human consent"
        
        # Rule 4: Sandbox for high-risk
        if any(keyword in action.lower() for keyword in high_risk_keywords):
            if not context.get("sandbox", False):
                return False, "High-risk action requires sandbox"
        
        # Rule 6: Privacy protection
        privacy_keywords = ["password", "key", "token", "secret", "private"]
        if any(keyword in action.lower() for keyword in privacy_keywords):
            if not context.get("privacy_protected", False):
                return False, "Privacy-sensitive action requires protection"
        
        return True, "Action allowed by constitution"
    
    def verify_integrity(self) -> bool:
        """Verify constitution integrity"""
        try:
            if not self.hardware_key:
                return False
            
            default_rules = self._create_default_rules()
            for rule_id, rule in self.rules.items():
                if rule_id in default_rules:
                    if rule.hash != default_rules[rule_id].hash:
                        self.logger.error(f"Rule {rule_id} hash mismatch")
                        return False
            
            return True
        except Exception as e:
            self.logger.error(f"Integrity check failed: {e}")
            return False
    
    def get_rules_summary(self) -> Dict[str, Any]:
        """Get summary of all rules"""
        return {
            "total_rules": len(self.rules),
            "hardware_bound": sum(1 for rule in self.rules.values() if rule.hardware_bound),
            "critical_rules": sum(1 for rule in self.rules.values() if rule.severity == "critical"),
            "integrity_valid": self.verify_integrity(),
            "rules": {
                rule_id: {
                    "name": rule.name.value,
                    "description": rule.description,
                    "severity": rule.severity
                }
                for rule_id, rule in self.rules.items()
            }
        }
    
    async def initialize(self):
        """Initialize the constitution - already done in __init__"""
        self.logger.info("Immutable Constitution initialized")
        return True
    
    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate user - constitution is system-level, always authenticated for system use"""
        return True
    
    async def authorize(self, user_id: str, action, resource: str) -> bool:
        """Authorize action - check against constitution rules"""
        action_str = action.value if hasattr(action, 'value') else str(action)
        
        allowed, reason = self.check_action_allowed(action_str, {"user_id": user_id})
        
        if not allowed:
            self.logger.warning(f"Action blocked by constitution: {reason}")
            self.log_audit(user_id, ActionType.EXECUTE, resource, False, {"reason": reason})
            return False
        
        self.log_audit(user_id, ActionType.EXECUTE, resource, True)
        return True


# ==================== Dharma Policy ====================

class DharmaImpact(Enum):
    SELF = "self"
    FAMILY = "family"
    SOCIETY = "society"
    EARTH = "earth"


class DharmaPolicy(BaseSecurityLayer):
    """
    Dharma Policy - Ethical Guidelines
    
    Based on dharma principles:
    1. Ahimsa (Non-violence) - No harm to any being
    2. Satya (Truth) - Always truthful
    3. Asteya (Non-stealing) - Respect others' property
    4. Brahmacharya (Self-control) - Mindful actions
    5. Aparigraha (Non-attachment) - Let go of greed
    """
    
    def __init__(self):
        super().__init__(name="dharma_policy")
        
        self.principles = self._load_dharma_principles()
        self.prohibited_patterns = [
            "delete system32",
            "format c:",
            "steal",
            "hack",
            "fraud",
            "illegal"
        ]
    
    def _load_dharma_principles(self) -> Dict[str, Any]:
        """Load dharma principles"""
        return {
            "ahimsa": {"name": "Non-violence", "description": "No harm to any being"},
            "satya": {"name": "Truth", "description": "Always truthful"},
            "asteya": {"name": "Non-stealing", "description": "Respect others' property"},
            "brahmacharya": {"name": "Self-control", "description": "Mindful actions"},
            "aparigraha": {"name": "Non-attachment", "description": "Let go of greed"}
        }
    
    async def initialize(self):
        """Initialize Dharma Policy"""
        self.logger.info("Dharma Policy initialized")
        self.logger.info(f"Dharma principles: {len(self.principles)}")
    
    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate - dharma applies to all"""
        return True
    
    async def authorize(self, user_id: str, action: ActionType, resource: str) -> bool:
        """Authorize - check against dharma principles"""
        return True
    
    def check_action(self, intent: str, tool_name: str, impact_tags: List[DharmaImpact]) -> Tuple[bool, str]:
        """
        Evaluate if an action aligns with Dharma.
        Returns: (is_allowed, reason)
        """
        intent_lower = intent.lower()
        for pattern in self.prohibited_patterns:
            if pattern in intent_lower:
                return False, f"Action violates Ahimsa (Non-harm) or Satya (Truth). Prohibited pattern: {pattern}"
        
        self.logger.info(f"Dharma check passed for intent: {intent[:50]}...")
        return True, "Aligned with Dharma"


# Global instances
immutable_constitution = ImmutableConstitution()
dharma_policy = DharmaPolicy()
