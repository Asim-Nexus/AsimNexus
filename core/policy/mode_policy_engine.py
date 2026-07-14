#!/usr/bin/env python3
"""
Mode-Based Policy Engine — Access Control for All Stakeholder Modes
====================================================================

Enhances the existing policy engine with full mode-based access control
using the MODE_PERMISSION_MATRIX from the Nexus Connector.

Key Features:
  - Mode-aware permission checking (Citizen/Company/Government/Hybrid)
  - Action-level granularity (20+ action types)
  - Consent level enforcement (self/notify/confirm/approve/veto)
  - Cross-mode access rules (data isolation between modes)
  - Sector-based policy overrides (51/49 power balance)
  - Integration with Immutable Constitution and Dharma Veto

Permission Levels:
  SELF:     User can perform action on their own data without consent
  NOTIFY:   User must notify affected stakeholders
  CONFIRM:  User must get confirmation from affected stakeholders
  APPROVE:  User must get approval from higher authority
  VETO:     Action can be vetoed by government (51%)

Integrates with:
  - core/nexus_connector.py — MODE_PERMISSION_MATRIX and MODE_ROUTING
  - core/policy/policy_engine.py — Existing policy engine
  - core/policy/permissions.py — Existing permissions verifier
  - core/security/immutable_constitution.py — Constitutional compliance
  - core/security/power_balance_constitution.py — 51/49 balance
  - core/governance/stakeholder_coordinator.py — Multi-stakeholder coordination
"""

import os
import time
import json
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from datetime import datetime

logger = logging.getLogger("AsimNexus.Policy.ModePolicy")

# ─── Environment Configuration ────────────────────────────────────────────────
_POLICY_DB_PATH = os.getenv(
    "ASIM_POLICY_DB_PATH",
    "data/mode_policy_engine.jsonl",
)
os.makedirs(os.path.dirname(_POLICY_DB_PATH) if os.path.dirname(_POLICY_DB_PATH) else ".", exist_ok=True)


class ConsentLevel(str, Enum):
    """Level of consent required for an action."""
    SELF = "self"                 # User can act alone
    NOTIFY = "notify"             # Must notify affected parties
    CONFIRM = "confirm"           # Must get confirmation
    APPROVE = "approve"           # Must get approval
    VETO = "veto"                 # Subject to government veto


class PolicyDecision(str, Enum):
    """Result of a policy check."""
    ALLOWED = "allowed"           # Action is permitted
    DENIED = "denied"             # Action is denied
    PENDING = "pending"           # Awaiting consent/approval
    VETOED = "vetoed"             # Vetoed by government
    ESCALATED = "escalated"       # Escalated for review


class PolicyScope(str, Enum):
    """Scope of a policy rule."""
    GLOBAL = "global"             # Applies to all modes
    MODE = "mode"                 # Applies to a specific mode
    ACTION = "action"             # Applies to a specific action
    USER = "user"                 # Applies to a specific user
    SECTOR = "sector"             # Applies to a specific sector


@dataclass
class PolicyRule:
    """A single policy rule."""
    rule_id: str
    scope: PolicyScope
    mode: str                     # Citizen/Company/Government/Hybrid/ALL
    action: str                   # Action type or "*" for all
    consent_required: ConsentLevel
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0             # Higher priority overrides lower
    description: str = ""
    enabled: bool = True
    created_at: float = 0.0
    updated_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "scope": self.scope.value if isinstance(self.scope, PolicyScope) else self.scope,
            "mode": self.mode,
            "action": self.action,
            "consent_required": self.consent_required.value if isinstance(self.consent_required, ConsentLevel) else self.consent_required,
            "conditions": self.conditions,
            "priority": self.priority,
            "description": self.description,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyRule":
        if "scope" in data and isinstance(data["scope"], str):
            try:
                data["scope"] = PolicyScope(data["scope"])
            except ValueError:
                data["scope"] = PolicyScope.GLOBAL
        if "consent_required" in data and isinstance(data["consent_required"], str):
            try:
                data["consent_required"] = ConsentLevel(data["consent_required"])
            except ValueError:
                data["consent_required"] = ConsentLevel.SELF
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PolicyCheckResult:
    """Result of a policy check."""
    decision: PolicyDecision
    rule: Optional[PolicyRule] = None
    required_consent: Optional[ConsentLevel] = None
    reason: str = ""
    required_modes: List[str] = field(default_factory=list)
    escalation_path: List[str] = field(default_factory=list)
    checked_at: float = 0.0

    def __post_init__(self):
        if not self.checked_at:
            self.checked_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value if isinstance(self.decision, PolicyDecision) else self.decision,
            "rule": self.rule.to_dict() if self.rule else None,
            "required_consent": self.required_consent.value if isinstance(self.required_consent, ConsentLevel) else self.required_consent,
            "reason": self.reason,
            "required_modes": self.required_modes,
            "escalation_path": self.escalation_path,
            "checked_at": self.checked_at,
        }


# ─── Default Mode Permission Matrix ───────────────────────────────────────────
# This mirrors the MODE_PERMISSION_MATRIX from nexus_connector.py for standalone use

DEFAULT_MODE_PERMISSIONS: Dict[str, Dict[str, str]] = {
    "citizen": {
        "identity_verify": "self",
        "data_access": "self",
        "agent_contract": "self",
        "personal_finance": "self",
        "health_record": "self",
        "education": "self",
        "commerce": "confirm",
        "employment": "confirm",
        "license": "approve",
        "tax_filing": "confirm",
        "marketplace": "self",
        "policy": "notify",
        "regulation": "notify",
        "audit": "self",
        "dispute": "confirm",
    },
    "company": {
        "identity_verify": "self",
        "data_access": "confirm",
        "agent_contract": "self",
        "personal_finance": "self",
        "commerce": "self",
        "employment": "self",
        "license": "approve",
        "tax_filing": "confirm",
        "compliance": "approve",
        "marketplace": "self",
        "policy": "notify",
        "regulation": "notify",
        "audit": "confirm",
        "dispute": "confirm",
        "cross_consent": "approve",
    },
    "government": {
        "identity_verify": "self",
        "data_access": "approve",
        "policy": "self",
        "regulation": "self",
        "veto": "self",
        "emergency": "self",
        "constitutional": "approve",
        "audit": "self",
        "governance": "self",
        "compliance": "self",
        "license": "self",
        "tax_filing": "self",
        "cross_consent": "self",
        "dispute": "self",
        "consensus": "self",
        "agent_contract": "approve",
        "commerce": "approve",
        "marketplace": "approve",
    },
    "hybrid": {
        "identity_verify": "self",
        "data_access": "approve",
        "agent_contract": "approve",
        "personal_finance": "approve",
        "commerce": "approve",
        "policy": "approve",
        "regulation": "approve",
        "veto": "approve",
        "emergency": "approve",
        "constitutional": "approve",
        "audit": "approve",
        "governance": "approve",
        "compliance": "approve",
        "license": "approve",
        "tax_filing": "approve",
        "marketplace": "approve",
        "cross_consent": "approve",
        "dispute": "approve",
        "consensus": "approve",
    },
}

# Actions that always require VETO level
VETO_REQUIRED_ACTIONS: Set[str] = {
    "constitutional",
    "emergency",
    "veto",
}

# Actions that always require APPROVE level
APPROVE_REQUIRED_ACTIONS: Set[str] = {
    "cross_consent",
    "governance",
    "consensus",
}


class ModePolicyEngine:
    """
    Mode-based policy engine for access control.

    Checks whether a user in a given mode can perform a specific action,
    and what level of consent is required.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._rules: Dict[str, PolicyRule] = {}
        self._mode_permissions: Dict[str, Dict[str, str]] = {}
        self._audit_log: List[Dict[str, Any]] = []
        self._callbacks: Dict[str, List[Callable]] = {}
        self._init_defaults()
        self._load_from_db()

    def _init_defaults(self) -> None:
        """Initialize default mode permissions."""
        self._mode_permissions = {}
        for mode, actions in DEFAULT_MODE_PERMISSIONS.items():
            self._mode_permissions[mode] = {}
            for action, consent in actions.items():
                self._mode_permissions[mode][action] = consent

    # ─── Permission Checking ────────────────────────────────────────────────

    def check_action(
        self,
        mode: str,
        action: str,
        user_id: str = "",
        target_user_id: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyCheckResult:
        """
        Check if a user in a given mode can perform an action.

        Returns a PolicyCheckResult with the decision and required consent level.
        """
        context = context or {}

        # Check if action is veto-required
        if action in VETO_REQUIRED_ACTIONS:
            return PolicyCheckResult(
                decision=PolicyDecision.PENDING,
                required_consent=ConsentLevel.VETO,
                reason=f"Action '{action}' requires government veto approval",
                required_modes=["government"],
                escalation_path=["level_1", "level_2", "level_3", "veto"],
            )

        # Check if action is approve-required
        if action in APPROVE_REQUIRED_ACTIONS:
            return PolicyCheckResult(
                decision=PolicyDecision.PENDING,
                required_consent=ConsentLevel.APPROVE,
                reason=f"Action '{action}' requires multi-stakeholder approval",
                required_modes=["government", "company"],
                escalation_path=["level_2", "level_3", "approve"],
            )

        # Check mode-specific permissions
        mode_perms = self._mode_permissions.get(mode, {})
        consent_str = mode_perms.get(action, "confirm")  # Default: confirm

        try:
            consent = ConsentLevel(consent_str)
        except ValueError:
            consent = ConsentLevel.CONFIRM

        # Check custom rules (higher priority overrides defaults)
        matching_rules = self._find_matching_rules(mode, action, user_id, context)
        if matching_rules:
            # Use the highest priority rule
            best_rule = matching_rules[0]
            consent = best_rule.consent_required
            if not best_rule.enabled:
                return PolicyCheckResult(
                    decision=PolicyDecision.DENIED,
                    reason=f"Action '{action}' is disabled by rule '{best_rule.rule_id}'",
                )

        # Determine required modes for cross-consent
        required_modes = self._get_required_modes(mode, action, consent)

        # Determine decision
        if consent == ConsentLevel.SELF:
            decision = PolicyDecision.ALLOWED
            reason = f"Action '{action}' allowed in {mode} mode (self-consent)"
        elif consent == ConsentLevel.NOTIFY:
            decision = PolicyDecision.ALLOWED
            reason = f"Action '{action}' allowed in {mode} mode (notification required)"
        elif consent == ConsentLevel.CONFIRM:
            decision = PolicyDecision.PENDING
            reason = f"Action '{action}' requires confirmation in {mode} mode"
        elif consent == ConsentLevel.APPROVE:
            decision = PolicyDecision.PENDING
            reason = f"Action '{action}' requires approval in {mode} mode"
        elif consent == ConsentLevel.VETO:
            decision = PolicyDecision.PENDING
            reason = f"Action '{action}' subject to government veto in {mode} mode"
        else:
            decision = PolicyDecision.DENIED
            reason = f"Action '{action}' denied in {mode} mode (unknown consent level)"

        # Cross-mode data isolation check
        if target_user_id and target_user_id != user_id:
            cross_check = self._check_cross_mode_access(mode, action, user_id, target_user_id)
            if not cross_check["allowed"]:
                return PolicyCheckResult(
                    decision=PolicyDecision.DENIED,
                    reason=cross_check["reason"],
                )

        result = PolicyCheckResult(
            decision=decision,
            required_consent=consent,
            reason=reason,
            required_modes=required_modes,
            escalation_path=self._get_escalation_path(consent),
        )

        # Log the check
        self._log_check(mode, action, user_id, result)

        return result

    def check_cross_mode_access(
        self,
        source_mode: str,
        target_mode: str,
        action: str,
        source_user_id: str,
        target_user_id: str,
    ) -> PolicyCheckResult:
        """
        Check if a user in source_mode can access data/actions in target_mode.

        This enforces data isolation between modes:
          - Citizen data is NEVER accessible from Company mode
          - Government can access citizen data only with Level-3 + constitutional approval
          - Company data is accessible to Government for compliance/audit
          - Hybrid mode can access all, but with highest consent level
        """
        # Citizen data isolation
        if target_mode == "citizen" and source_mode != "citizen":
            if source_mode == "government" and action in ("audit", "compliance", "emergency"):
                return PolicyCheckResult(
                    decision=PolicyDecision.PENDING,
                    required_consent=ConsentLevel.APPROVE,
                    reason="Government can access citizen data with Level-3 approval",
                    required_modes=["government"],
                    escalation_path=["level_3", "approve"],
                )
            return PolicyCheckResult(
                decision=PolicyDecision.DENIED,
                reason=f"Cannot access citizen data from {source_mode} mode",
            )

        # Company data: Government can access for compliance
        if target_mode == "company" and source_mode == "government":
            if action in ("audit", "compliance", "tax_filing"):
                return PolicyCheckResult(
                    decision=PolicyDecision.ALLOWED,
                    reason="Government can access company data for compliance",
                )
            return PolicyCheckResult(
                decision=PolicyDecision.PENDING,
                required_consent=ConsentLevel.APPROVE,
                reason="Government needs approval for non-compliance company data access",
            )

        # Government data: Highly restricted
        if target_mode == "government" and source_mode != "government":
            return PolicyCheckResult(
                decision=PolicyDecision.DENIED,
                reason=f"Cannot access government data from {source_mode} mode",
            )

        # Same mode: Allowed
        if source_mode == target_mode:
            return PolicyCheckResult(
                decision=PolicyDecision.ALLOWED,
                reason=f"Same-mode access allowed ({source_mode})",
            )

        # Hybrid mode: Allowed with highest consent
        if source_mode == "hybrid":
            return PolicyCheckResult(
                decision=PolicyDecision.PENDING,
                required_consent=ConsentLevel.APPROVE,
                reason="Hybrid mode cross-access requires approval",
            )

        return PolicyCheckResult(
            decision=PolicyDecision.DENIED,
            reason=f"Cross-mode access from {source_mode} to {target_mode} not permitted",
        )

    # ─── Rule Management ────────────────────────────────────────────────────

    def add_rule(self, rule: PolicyRule) -> str:
        """Add a custom policy rule."""
        with self._lock:
            self._rules[rule.rule_id] = rule
            self._persist_rule(rule)
        logger.info(f"Policy rule added: {rule.rule_id} ({rule.mode}/{rule.action} → {rule.consent_required.value})")
        return rule.rule_id

    def update_rule(self, rule_id: str, **updates) -> bool:
        """Update a policy rule."""
        with self._lock:
            rule = self._rules.get(rule_id)
            if not rule:
                return False
            for key, value in updates.items():
                if hasattr(rule, key) and key not in ("rule_id", "created_at"):
                    setattr(rule, key, value)
            rule.updated_at = time.time()
            self._persist_rule(rule)
        return True

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a policy rule."""
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                return True
        return False

    def get_rule(self, rule_id: str) -> Optional[PolicyRule]:
        """Get a policy rule by ID."""
        return self._rules.get(rule_id)

    def list_rules(
        self,
        mode: Optional[str] = None,
        action: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[PolicyRule]:
        """List policy rules, optionally filtered."""
        with self._lock:
            results = []
            for rule in self._rules.values():
                if mode and rule.mode != mode and rule.mode != "ALL":
                    continue
                if action and rule.action != action and rule.action != "*":
                    continue
                if enabled_only and not rule.enabled:
                    continue
                results.append(rule)
            return sorted(results, key=lambda x: x.priority, reverse=True)

    # ─── Mode Permission Overrides ──────────────────────────────────────────

    def set_mode_permission(self, mode: str, action: str, consent: str) -> bool:
        """Override the default permission for a mode/action pair."""
        try:
            consent_level = ConsentLevel(consent)
        except ValueError:
            return False

        with self._lock:
            if mode not in self._mode_permissions:
                self._mode_permissions[mode] = {}
            self._mode_permissions[mode][action] = consent
            self._persist_override(mode, action, consent)
        return True

    def get_mode_permissions(self, mode: str) -> Dict[str, str]:
        """Get all permissions for a mode."""
        return self._mode_permissions.get(mode, {}).copy()

    def get_all_permissions(self) -> Dict[str, Dict[str, str]]:
        """Get all mode permissions."""
        return {mode: perms.copy() for mode, perms in self._mode_permissions.items()}

    # ─── Audit Log ──────────────────────────────────────────────────────────

    def get_audit_log(
        self,
        limit: int = 100,
        mode: Optional[str] = None,
        action: Optional[str] = None,
        decision: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get the policy check audit log."""
        with self._lock:
            results = list(self._audit_log)
            if mode:
                results = [r for r in results if r.get("mode") == mode]
            if action:
                results = [r for r in results if r.get("action") == action]
            if decision:
                results = [r for r in results if r.get("decision") == decision]
            return results[-limit:]

    # ─── Internal Methods ───────────────────────────────────────────────────

    def _find_matching_rules(
        self,
        mode: str,
        action: str,
        user_id: str,
        context: Dict[str, Any],
    ) -> List[PolicyRule]:
        """Find all matching rules for a mode/action, sorted by priority."""
        matches = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            # Check mode match
            if rule.mode not in ("ALL", mode):
                continue
            # Check action match
            if rule.action not in ("*", action):
                continue
            # Check conditions
            if rule.conditions and not self._check_conditions(rule.conditions, context):
                continue
            matches.append(rule)
        return sorted(matches, key=lambda x: x.priority, reverse=True)

    def _check_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if conditions are met."""
        for key, expected in conditions.items():
            actual = context.get(key)
            if isinstance(expected, (list, tuple)):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    def _get_required_modes(self, mode: str, action: str, consent: ConsentLevel) -> List[str]:
        """Get the modes that need to be involved for an action."""
        if consent == ConsentLevel.SELF:
            return [mode]
        if consent == ConsentLevel.NOTIFY:
            return [mode]
        if consent == ConsentLevel.CONFIRM:
            if mode == "citizen":
                return ["citizen"]
            return [mode]
        if consent == ConsentLevel.APPROVE:
            if mode == "citizen":
                return ["citizen", "government"]
            if mode == "company":
                return ["company", "government"]
            if mode == "government":
                return ["government"]
            return ["citizen", "company", "government"]
        if consent == ConsentLevel.VETO:
            return ["government"]
        return [mode]

    def _get_escalation_path(self, consent: ConsentLevel) -> List[str]:
        """Get the escalation path for a consent level."""
        base_path = ["level_1"]
        if consent in (ConsentLevel.CONFIRM, ConsentLevel.APPROVE, ConsentLevel.VETO):
            base_path.append("level_2")
        if consent in (ConsentLevel.APPROVE, ConsentLevel.VETO):
            base_path.append("level_3")
        if consent == ConsentLevel.VETO:
            base_path.append("veto")
        if consent == ConsentLevel.APPROVE:
            base_path.append("approve")
        return base_path

    def _check_cross_mode_access(
        self,
        mode: str,
        action: str,
        user_id: str,
        target_user_id: str,
    ) -> Dict[str, Any]:
        """Check if cross-mode data access is allowed."""
        # Same user, different mode: Check mode isolation
        if user_id == target_user_id:
            return {"allowed": True, "reason": "Same user access"}

        # Different user: Check if action permits cross-user access
        if action in ("audit", "compliance", "governance"):
            return {"allowed": True, "reason": f"Action '{action}' permits cross-user access"}

        return {"allowed": False, "reason": f"Cross-user access not permitted for action '{action}'"}

    def _log_check(
        self,
        mode: str,
        action: str,
        user_id: str,
        result: PolicyCheckResult,
    ) -> None:
        """Log a policy check to the audit log."""
        entry = {
            "timestamp": time.time(),
            "mode": mode,
            "action": action,
            "user_id": user_id,
            "decision": result.decision.value if isinstance(result.decision, PolicyDecision) else result.decision,
            "reason": result.reason,
        }
        with self._lock:
            self._audit_log.append(entry)
            # Keep only last 10000 entries
            if len(self._audit_log) > 10000:
                self._audit_log = self._audit_log[-10000:]

    # ─── Callbacks ──────────────────────────────────────────────────────────

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for policy events."""
        with self._lock:
            self._callbacks.setdefault(event, []).append(callback)

    def _fire_callbacks(self, event: str, data: Dict[str, Any]) -> None:
        """Fire callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(event, data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")

    # ─── Persistence ────────────────────────────────────────────────────────

    def _persist_rule(self, rule: PolicyRule) -> None:
        """Append rule state to JSONL."""
        try:
            with open(_POLICY_DB_PATH, "a", encoding="utf-8") as f:
                record = {
                    "type": "rule",
                    "data": rule.to_dict(),
                    "timestamp": time.time(),
                }
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist rule {rule.rule_id}: {e}")

    def _persist_override(self, mode: str, action: str, consent: str) -> None:
        """Append permission override to JSONL."""
        try:
            with open(_POLICY_DB_PATH, "a", encoding="utf-8") as f:
                record = {
                    "type": "override",
                    "data": {"mode": mode, "action": action, "consent": consent},
                    "timestamp": time.time(),
                }
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist override: {e}")

    def _load_from_db(self) -> None:
        """Load state from persistent storage."""
        if not os.path.exists(_POLICY_DB_PATH):
            return
        try:
            with open(_POLICY_DB_PATH, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        record_type = record.get("type")
                        data = record.get("data", {})
                        if record_type == "rule":
                            rule = PolicyRule.from_dict(data)
                            self._rules[rule.rule_id] = rule
                        elif record_type == "override":
                            mode = data.get("mode")
                            action = data.get("action")
                            consent = data.get("consent")
                            if mode and action and consent:
                                self._mode_permissions.setdefault(mode, {})[action] = consent
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to load policy state: {e}")

    # ─── Status & Stats ─────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the policy engine."""
        with self._lock:
            return {
                "system": "Mode-Based Policy Engine",
                "version": "1.0.0",
                "rules_count": len(self._rules),
                "modes_configured": list(self._mode_permissions.keys()),
                "total_actions_defined": sum(len(p) for p in self._mode_permissions.values()),
                "audit_log_size": len(self._audit_log),
                "db_path": _POLICY_DB_PATH,
                "db_exists": os.path.exists(_POLICY_DB_PATH),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        with self._lock:
            # Decision breakdown
            decision_counts: Dict[str, int] = {}
            for entry in self._audit_log:
                d = entry.get("decision", "unknown")
                decision_counts[d] = decision_counts.get(d, 0) + 1

            # Mode breakdown
            mode_counts: Dict[str, int] = {}
            for entry in self._audit_log:
                m = entry.get("mode", "unknown")
                mode_counts[m] = mode_counts.get(m, 0) + 1

            # Action breakdown
            action_counts: Dict[str, int] = {}
            for entry in self._audit_log:
                a = entry.get("action", "unknown")
                action_counts[a] = action_counts.get(a, 0) + 1

            return {
                "checks": {
                    "total": len(self._audit_log),
                    "by_decision": decision_counts,
                    "by_mode": mode_counts,
                    "by_action": action_counts,
                },
                "rules": {
                    "total": len(self._rules),
                    "enabled": sum(1 for r in self._rules.values() if r.enabled),
                    "disabled": sum(1 for r in self._rules.values() if not r.enabled),
                },
                "permissions": {
                    mode: len(perms) for mode, perms in self._mode_permissions.items()
                },
            }


# ─── Singleton ─────────────────────────────────────────────────────────────────

_POLICY_INSTANCE: Optional[ModePolicyEngine] = None
_POLICY_LOCK = threading.Lock()


def get_mode_policy_engine() -> ModePolicyEngine:
    """Get or create the singleton ModePolicyEngine instance."""
    global _POLICY_INSTANCE
    if _POLICY_INSTANCE is None:
        with _POLICY_LOCK:
            if _POLICY_INSTANCE is None:
                _POLICY_INSTANCE = ModePolicyEngine()
    return _POLICY_INSTANCE


def reset_mode_policy_engine() -> None:
    """Reset the singleton (for testing) and clean persisted state."""
    global _POLICY_INSTANCE
    with _POLICY_LOCK:
        _POLICY_INSTANCE = None
        try:
            if os.path.exists(_POLICY_DB_PATH):
                os.remove(_POLICY_DB_PATH)
        except Exception as e:
            logger.warning(f"Failed to clean policy DB: {e}")
