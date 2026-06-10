"""
AsimNexus Policy Gateway Package
=================================
Secure Core components for the Gateway layer.

Modules:
  - capability_registry: Default-Deny allowlist with context-based risk escalation
  - versioned_packs: Layered policy engine (Session > User > Org > Country > Global)
  - audit_ledger: Actor-split immutable audit ledger with hash-chaining
  - router: Central gateway router with replay protection
  - kill_switch: Emergency shutdown mechanism
  - rollback_manager: Snapshot and rollback management
"""

from core.gateway.capability_registry import CapabilityRegistry, RiskTier, registry
from core.gateway.versioned_packs import VersionedPolicyEngine, PolicyLayer, PolicyEffect, PolicyPack, PolicyRule, policy_engine
from core.gateway.audit_ledger import AuditLedger, AuditAction, AuditEntry, ledger
from core.gateway.router import GatewayRouter, GatewayRequest, GatewayResponse, RequestStatus, ReplayProtection, HighRiskPromptSchema, router
from core.gateway.kill_switch import KillSwitch, ShutdownMode, KillSwitchState, KillSwitchEvent, kill_switch
from core.gateway.rollback_manager import RollbackManager, Snapshot, SnapshotType, SnapshotState, RollbackEvent, rollback_manager

__all__ = [
    "CapabilityRegistry", "RiskTier", "registry",
    "VersionedPolicyEngine", "PolicyLayer", "PolicyEffect", "PolicyPack", "PolicyRule", "policy_engine",
    "AuditLedger", "AuditAction", "AuditEntry", "ledger",
    "GatewayRouter", "GatewayRequest", "GatewayResponse", "RequestStatus", "ReplayProtection", "HighRiskPromptSchema", "router",
    "KillSwitch", "ShutdownMode", "KillSwitchState", "KillSwitchEvent", "kill_switch",
    "RollbackManager", "Snapshot", "SnapshotType", "SnapshotState", "RollbackEvent", "rollback_manager",
]
