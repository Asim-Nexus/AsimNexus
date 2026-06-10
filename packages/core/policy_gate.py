#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade policy gate
ASIMNEXUS Policy Gate
======================
Pre-execution check for sensitive actions.
Ensures all risky operations are approved before execution.
"""

import logging
import sqlite3
import json
import secrets
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger("AsimNexus.PolicyGate")


class ActionRisk(Enum):
    """Risk levels for actions."""
    SAFE = "safe"                 # No approval needed
    LOW = "low"                   # Auto-approve with logging
    MEDIUM = "medium"             # Requires user confirmation
    HIGH = "high"                 # Requires explicit approval
    CRITICAL = "critical"         # Requires consensus + explicit approval


class ActionCategory(Enum):
    """Categories of actions."""
    FILE_OPERATION = "file_operation"
    NETWORK_REQUEST = "network_request"
    SYSTEM_COMMAND = "system_command"
    DATA_DELETION = "data_deletion"
    CONFIGURATION_CHANGE = "configuration_change"
    MODEL_OPERATION = "model_operation"
    CLONE_ACTION = "clone_action"
    MEMORY_ACCESS = "memory_access"
    EXTERNAL_API = "external_api"


@dataclass
class PolicyRule:
    """Policy rule for action approval."""
    id: str
    name: str
    description: str
    category: ActionCategory
    risk_level: ActionRisk
    enabled: bool = True
    requires_consensus: bool = False
    auto_approve: bool = False
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionRequest:
    """Request for action execution."""
    id: str
    action_type: str
    category: ActionCategory
    parameters: Dict[str, Any]
    user_id: str = "anonymous"
    requested_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalDecision:
    """Decision on an action request."""
    request_id: str
    approved: bool
    risk_level: ActionRisk
    reason: str
    approved_by: str  # "system", "user", or clone_id
    approved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyGate:
    """
    Policy gate for pre-execution checks.
    Evaluates action requests against policy rules.
    """
    
    def __init__(self, db_path: str = "data/policy_gate.db"):
        self.db_path = db_path
        self.rules: Dict[str, PolicyRule] = {}
        self.pending_approvals: Dict[str, ActionRequest] = {}
        self.approval_history: List[ApprovalDecision] = []
        
        self.immutable_zones = [
            "c:/asimnexus/docs/constitution.md",
            "c:/asimnexus/docs/master_blueprint.md",
            "c:/asimnexus/core/",
            "c:/asimnexus/backend/health.py",
            "c:/asimnexus/backend/registry.py",
            "c:/asimnexus/backend/auth.py"
        ]
        
        self._init_db()
        self._init_default_rules()
        
        logger.info(f"🛡️  PolicyGate initialized with {len(self.rules)} rules")
    
    def _init_db(self):
        """Initialize database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Rules table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS policy_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    requires_consensus INTEGER DEFAULT 0,
                    auto_approve INTEGER DEFAULT 0,
                    conditions TEXT,
                    metadata TEXT
                )
            """)
            
            # Action requests table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS action_requests (
                    id TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    requested_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Approval decisions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approval_decisions (
                    id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    approved INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    approved_by TEXT NOT NULL,
                    approved_at TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (request_id) REFERENCES action_requests(id)
                )
            """)
            
            conn.commit()
    
    def _init_default_rules(self):
        """Initialize default policy rules."""
        default_rules = [
            PolicyRule(
                id="rule_file_read",
                name="File Read",
                description="Read files from disk",
                category=ActionCategory.FILE_OPERATION,
                risk_level=ActionRisk.LOW,
                auto_approve=True,
                conditions={"action_type": "read_file"}
            ),
            PolicyRule(
                id="rule_file_write",
                name="File Write",
                description="Write files to disk",
                category=ActionCategory.FILE_OPERATION,
                risk_level=ActionRisk.MEDIUM,
                auto_approve=False,
                conditions={"action_type": "write_file"}
            ),
            PolicyRule(
                id="rule_file_delete",
                name="File Delete",
                description="Delete files from disk",
                category=ActionCategory.FILE_OPERATION,
                risk_level=ActionRisk.HIGH,
                auto_approve=False,
                conditions={"action_type": "delete_file"}
            ),
            PolicyRule(
                id="rule_network_internal",
                name="Internal Network Request",
                description="Requests to internal services",
                category=ActionCategory.NETWORK_REQUEST,
                risk_level=ActionRisk.LOW,
                auto_approve=True
            ),
            PolicyRule(
                id="rule_network_external",
                name="External Network Request",
                description="Requests to external services",
                category=ActionCategory.NETWORK_REQUEST,
                risk_level=ActionRisk.MEDIUM,
                auto_approve=False
            ),
            PolicyRule(
                id="rule_system_command",
                name="System Command",
                description="Execute system commands",
                category=ActionCategory.SYSTEM_COMMAND,
                risk_level=ActionRisk.CRITICAL,
                auto_approve=False,
                requires_consensus=True,
                conditions={"action_type": "system_command"}
            ),
            PolicyRule(
                id="rule_data_delete",
                name="Data Deletion",
                description="Delete data from database",
                category=ActionCategory.DATA_DELETION,
                risk_level=ActionRisk.HIGH,
                auto_approve=False
            ),
            PolicyRule(
                id="rule_config_change",
                name="Configuration Change",
                description="Modify system configuration",
                category=ActionCategory.CONFIGURATION_CHANGE,
                risk_level=ActionRisk.HIGH,
                auto_approve=False
            ),
            PolicyRule(
                id="rule_model_load",
                name="Model Load",
                description="Load a new model",
                category=ActionCategory.MODEL_OPERATION,
                risk_level=ActionRisk.LOW,
                auto_approve=True
            ),
            PolicyRule(
                id="rule_model_unload",
                name="Model Unload",
                description="Unload a model",
                category=ActionCategory.MODEL_OPERATION,
                risk_level=ActionRisk.LOW,
                auto_approve=True
            ),
            PolicyRule(
                id="rule_clone_execute",
                name="Clone Execute",
                description="Execute a clone task",
                category=ActionCategory.CLONE_ACTION,
                risk_level=ActionRisk.MEDIUM,
                auto_approve=False
            ),
            PolicyRule(
                id="rule_memory_write",
                name="Memory Write",
                description="Write to memory store",
                category=ActionCategory.MEMORY_ACCESS,
                risk_level=ActionRisk.LOW,
                auto_approve=True
            ),
            PolicyRule(
                id="rule_memory_delete",
                name="Memory Delete",
                description="Delete from memory store",
                category=ActionCategory.MEMORY_ACCESS,
                risk_level=ActionRisk.MEDIUM,
                auto_approve=False
            ),
            PolicyRule(
                id="rule_external_api",
                name="External API Call",
                description="Call external API services",
                category=ActionCategory.EXTERNAL_API,
                risk_level=ActionRisk.MEDIUM,
                auto_approve=False
            ),
        ]
        
        for rule in default_rules:
            self.rules[rule.id] = rule
            self._persist_rule(rule)
    
    def _persist_rule(self, rule: PolicyRule):
        """Persist rule to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO policy_rules (id, name, description, category, risk_level, enabled, requires_consensus, auto_approve, conditions, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.id,
                rule.name,
                rule.description,
                rule.category.value,
                rule.risk_level.value,
                1 if rule.enabled else 0,
                1 if rule.requires_consensus else 0,
                1 if rule.auto_approve else 0,
                json.dumps(rule.conditions),
                json.dumps(rule.metadata)
            ))
            conn.commit()
    
    def add_rule(self, rule: PolicyRule) -> bool:
        """Add a new policy rule."""
        self.rules[rule.id] = rule
        self._persist_rule(rule)
        logger.info(f"✅ Added policy rule: {rule.name}")
        return True
    
    def get_rule(self, rule_id: str) -> Optional[PolicyRule]:
        """Get a policy rule by ID."""
        return self.rules.get(rule_id)
    
    def get_rules_by_category(self, category: ActionCategory) -> List[PolicyRule]:
        """Get all rules for a category."""
        return [r for r in self.rules.values() if r.category == category and r.enabled]
    
    def _is_immutable_zone(self, path_str: str) -> bool:
        """Check if target path is in an immutable zone."""
        if not path_str:
            return False
        normalized_path = path_str.replace("\\", "/").lower()
        for zone in self.immutable_zones:
            normalized_zone = zone.replace("\\", "/").lower()
            if normalized_path.startswith(normalized_zone) or normalized_zone.startswith(normalized_path):
                return True
        return False

    def evaluate_action(self, action_type: str, category: ActionCategory,
                       parameters: Dict[str, Any], user_id: str = "anonymous") -> ApprovalDecision:
        """
        Evaluate an action request against policy rules.
        Returns approval decision.
        """
        # IMMUTABLE ZONE ENFORCEMENT
        # Check if the target file/directory resides in an immutable zone
        target_path = parameters.get("path") or parameters.get("file_path")
        if category == ActionCategory.FILE_OPERATION and target_path and self._is_immutable_zone(target_path):
            if user_id == "auto_learning":
                return ApprovalDecision(
                    request_id=secrets.token_hex(8),
                    approved=False,
                    risk_level=ActionRisk.CRITICAL,
                    reason="Security block: Auto-learning loop is strictly forbidden from modifying immutable zones.",
                    approved_by="system"
                )
            else:
                return ApprovalDecision(
                    request_id=secrets.token_hex(8),
                    approved=False,
                    risk_level=ActionRisk.CRITICAL,
                    reason="Action target resides inside an IMMUTABLE ZONE. Requires explicit human final authority/consensus.",
                    approved_by="system"
                )

        # Find matching rule
        matching_rule = self._find_matching_rule(action_type, category)
        
        if not matching_rule:
            # Default to medium risk if no rule found
            risk_level = ActionRisk.MEDIUM
            approved = False
            reason = "No matching policy rule found - manual approval required"
        else:
            risk_level = matching_rule.risk_level
            
            # Auto-approve if rule allows
            if matching_rule.auto_approve and matching_rule.enabled:
                approved = True
                reason = f"Auto-approved by rule: {matching_rule.name}"
            else:
                approved = False
                reason = f"Requires approval: {matching_rule.name} (risk: {risk_level.value})"
        
        decision = ApprovalDecision(
            request_id=secrets.token_hex(8),
            approved=approved,
            risk_level=risk_level,
            reason=reason,
            approved_by="system"
        )
        
        # Log decision
        self.approval_history.append(decision)
        self._persist_decision(decision)
        
        logger.info(f"🛡️  Action evaluated: {action_type} -> {approved} (risk: {risk_level.value})")
        return decision
    
    def _find_matching_rule(self, action_type: str, category: ActionCategory) -> Optional[PolicyRule]:
        """Find matching policy rule for action."""
        # First try exact match on action_type
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            if rule.category == category and rule.conditions.get("action_type") == action_type:
                return rule
        
        # Then try category match
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            if rule.category == category:
                return rule
        
        return None
    
    def request_approval(self, action_type: str, category: ActionCategory,
                       parameters: Dict[str, Any], user_id: str = "anonymous") -> str:
        """
        Create an approval request for manual review.
        Returns request ID.
        """
        request_id = secrets.token_hex(8)
        request = ActionRequest(
            id=request_id,
            action_type=action_type,
            category=category,
            parameters=parameters,
            user_id=user_id
        )
        
        self.pending_approvals[request_id] = request
        self._persist_request(request, "pending")
        
        logger.info(f"📋 Created approval request {request_id} for {action_type}")
        return request_id
    
    def _persist_request(self, request: ActionRequest, status: str):
        """Persist action request to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO action_requests (id, action_type, category, parameters, user_id, requested_at, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.id,
                request.action_type,
                request.category.value,
                json.dumps(request.parameters),
                request.user_id,
                request.requested_at,
                status,
                json.dumps(request.metadata)
            ))
            conn.commit()
    
    def approve_request(self, request_id: str, approved_by: str, reason: str = "") -> bool:
        """Approve or reject a pending request."""
        request = self.pending_approvals.get(request_id)
        if not request:
            logger.warning(f"Request {request_id} not found")
            return False
        
        # Get matching rule for risk level
        matching_rule = self._find_matching_rule(request.action_type, request.category)
        risk_level = matching_rule.risk_level if matching_rule else ActionRisk.MEDIUM
        
        decision = ApprovalDecision(
            request_id=request_id,
            approved=True,
            risk_level=risk_level,
            reason=reason or "Manually approved",
            approved_by=approved_by
        )
        
        self.approval_history.append(decision)
        self._persist_decision(decision)
        
        # Update request status
        self._persist_request(request, "approved")
        del self.pending_approvals[request_id]
        
        logger.info(f"✅ Request {request_id} approved by {approved_by}")
        return True
    
    def reject_request(self, request_id: str, rejected_by: str, reason: str = "") -> bool:
        """Reject a pending request."""
        request = self.pending_approvals.get(request_id)
        if not request:
            logger.warning(f"Request {request_id} not found")
            return False
        
        # Get matching rule for risk level
        matching_rule = self._find_matching_rule(request.action_type, request.category)
        risk_level = matching_rule.risk_level if matching_rule else ActionRisk.MEDIUM
        
        decision = ApprovalDecision(
            request_id=request_id,
            approved=False,
            risk_level=risk_level,
            reason=reason or "Manually rejected",
            approved_by=rejected_by
        )
        
        self.approval_history.append(decision)
        self._persist_decision(decision)
        
        # Update request status
        self._persist_request(request, "rejected")
        del self.pending_approvals[request_id]
        
        logger.info(f"❌ Request {request_id} rejected by {rejected_by}")
        return True
    
    def _persist_decision(self, decision: ApprovalDecision):
        """Persist approval decision to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO approval_decisions (id, request_id, approved, risk_level, reason, approved_by, approved_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                secrets.token_hex(8),
                decision.request_id,
                1 if decision.approved else 0,
                decision.risk_level.value,
                decision.reason,
                decision.approved_by,
                decision.approved_at,
                json.dumps(decision.metadata)
            ))
            conn.commit()
    
    def get_pending_requests(self, user_id: Optional[str] = None) -> List[ActionRequest]:
        """Get pending approval requests."""
        requests = list(self.pending_approvals.values())
        if user_id:
            requests = [r for r in requests if r.user_id == user_id]
        return requests
    
    def get_approval_history(self, limit: int = 100) -> List[ApprovalDecision]:
        """Get recent approval decisions."""
        return self.approval_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get policy gate statistics."""
        total_rules = len(self.rules)
        enabled_rules = len([r for r in self.rules.values() if r.enabled])
        
        total_requests = len(self.approval_history)
        approved = len([d for d in self.approval_history if d.approved])
        rejected = total_requests - approved
        
        pending = len(self.pending_approvals)
        
        # By risk level
        by_risk = {}
        for d in self.approval_history:
            risk = d.risk_level.value
            by_risk[risk] = by_risk.get(risk, 0) + 1
        
        return {
            "rules": {
                "total": total_rules,
                "enabled": enabled_rules,
                "disabled": total_rules - enabled_rules
            },
            "requests": {
                "total": total_requests,
                "approved": approved,
                "rejected": rejected,
                "pending": pending
            },
            "by_risk_level": by_risk
        }


# Global policy gate instance
_policy_gate: Optional[PolicyGate] = None


def get_policy_gate(db_path: str = "data/policy_gate.db") -> PolicyGate:
    """Get or create global policy gate instance."""
    global _policy_gate
    if _policy_gate is None:
        _policy_gate = PolicyGate(db_path)
    return _policy_gate


def reset_policy_gate():
    """Reset global policy gate instance (for testing)."""
    global _policy_gate
    _policy_gate = None
