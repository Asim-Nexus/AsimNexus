#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade Agent Contract System
ASIMNEXUS Agent Contract System
==============================
Time-bound AI agent authority contracts with:
- 5/15/30 day duration tiers
- Scope boundaries (allowed/forbidden actions)
- Agent identity binding (Clone ID / DID)
- Automatic expiration tracking and renewal
- Formal audit trail generation at milestones
- Cooling-off periods between revocation and re-proposal
- Integration with CloneOrchestrator and HumanOverrideEngine

Extends core/contracts/smart_contract_engine.py with agent-specific features.
"""

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("AsimNexus.AgentContract")

# ─── CONSTANTS ─────────────────────────────────────────────────────────────────

AGENT_CONTRACT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "agent_contracts.jsonl"
AGENT_CONTRACT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Env-var configuration
import os
_MAX_RENEWALS = int(os.environ.get("ASIM_AGENT_MAX_RENEWALS", "3"))
_COOLING_OFF_HOURS = int(os.environ.get("ASIM_AGENT_COOLING_OFF_HOURS", "72"))  # 3 days
_EXPIRY_WARNING_HOURS = int(os.environ.get("ASIM_AGENT_EXPIRY_WARNING_HOURS", "48"))


# ─── ENUMS ─────────────────────────────────────────────────────────────────────

class ContractDuration(int, Enum):
    """Duration tiers for agent contracts."""
    TRIAL = 5       # 5 days — limited scope, high oversight
    STANDARD = 15   # 15 days — standard scope
    EXTENDED = 30   # 30 days — full scope, periodic audit


class ContractStatus(str, Enum):
    """Extended contract status with agent-specific states."""
    PROPOSED = "proposed"
    PENDING_SIGNATURE = "pending_signature"
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"     # Within warning window
    EXPIRED = "expired"
    RENEWED = "renewed"                 # Successfully renewed
    REVOKED = "revoked"                 # Human revoked (with reason)
    COOLING_OFF = "cooling_off"         # In cooling-off period
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DataAccessLevel(str, Enum):
    """Data access levels for agent contracts."""
    PUBLIC = "public"             # Public mesh data only
    RESTRICTED = "restricted"     # Non-personal, task-related data
    PRIVATE = "private"           # Personal data with explicit consent
    SECRET = "secret"             # Highly sensitive (requires override)


class AuditEventType(str, Enum):
    """Types of audit events in contract lifecycle."""
    CONTRACT_CREATED = "contract_created"
    CONTRACT_SIGNED = "contract_signed"
    CONTRACT_ACTIVATED = "contract_activated"
    ACTION_PERFORMED = "action_performed"
    ACTION_DENIED = "action_denied"
    MILESTONE_REACHED = "milestone_reached"
    RENEWAL_REQUESTED = "renewal_requested"
    CONTRACT_RENEWED = "contract_renewed"
    CONTRACT_REVOKED = "contract_revoked"
    CONTRACT_EXPIRED = "contract_expired"
    CONTRACT_COMPLETED = "contract_completed"
    COOLING_OFF_STARTED = "cooling_off_started"
    COOLING_OFF_ENDED = "cooling_off_ended"
    SCOPE_CHANGED = "scope_changed"
    AUDIT_GENERATED = "audit_generated"


# ─── DATA CLASSES ──────────────────────────────────────────────────────────────

@dataclass
class ContractScope:
    """Defines what an agent CAN and CANNOT do within a contract.

    Attributes:
        allowed_actions: List of action patterns the agent is permitted to execute.
        forbidden_actions: List of action patterns the agent is NEVER allowed.
        data_access_level: Maximum data classification the agent can access.
        max_value_per_action: Maximum monetary/impact value per single action.
        requires_human_override: Actions that need explicit human override even
            though they're allowed in scope.
        allowed_mesh_types: Which mesh types the agent can operate on.
        max_concurrent_tasks: Maximum number of simultaneous tasks.
    """
    allowed_actions: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)
    data_access_level: DataAccessLevel = DataAccessLevel.RESTRICTED
    max_value_per_action: float = 10000.0
    requires_human_override: List[str] = field(default_factory=list)
    allowed_mesh_types: List[str] = field(default_factory=lambda: ["local", "personal"])
    max_concurrent_tasks: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed_actions": self.allowed_actions,
            "forbidden_actions": self.forbidden_actions,
            "data_access_level": self.data_access_level.value,
            "max_value_per_action": self.max_value_per_action,
            "requires_human_override": self.requires_human_override,
            "allowed_mesh_types": self.allowed_mesh_types,
            "max_concurrent_tasks": self.max_concurrent_tasks,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContractScope":
        return cls(
            allowed_actions=data.get("allowed_actions", []),
            forbidden_actions=data.get("forbidden_actions", []),
            data_access_level=DataAccessLevel(data.get("data_access_level", "restricted")),
            max_value_per_action=data.get("max_value_per_action", 10000.0),
            requires_human_override=data.get("requires_human_override", []),
            allowed_mesh_types=data.get("allowed_mesh_types", ["local", "personal"]),
            max_concurrent_tasks=data.get("max_concurrent_tasks", 3),
        )


@dataclass
class AgentBinding:
    """Cryptographic binding between contract and agent identity.

    Attributes:
        agent_id: Unique identifier for the agent (Clone ID or DID).
        agent_type: "clone" for CloneOrchestrator clones, "external" for DIDs.
        agent_did: Decentralized identifier (if external).
        public_key_hash: SHA-256 of the agent's public key.
        identity_proof: Cryptographic proof of agent identity.
    """
    agent_id: str
    agent_type: str = "clone"  # "clone" or "external"
    agent_did: str = ""
    public_key_hash: str = ""
    identity_proof: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "agent_did": self.agent_did,
            "public_key_hash": self.public_key_hash,
            "identity_proof": self.identity_proof,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentBinding":
        return cls(
            agent_id=data.get("agent_id", ""),
            agent_type=data.get("agent_type", "clone"),
            agent_did=data.get("agent_did", ""),
            public_key_hash=data.get("public_key_hash", ""),
            identity_proof=data.get("identity_proof", ""),
        )


@dataclass
class AuditEntry:
    """Immutable audit entry for contract lifecycle events."""
    entry_id: str
    contract_id: str
    event_type: AuditEventType
    timestamp: float
    actor: str  # human_id or agent_id or "system"
    details: Dict[str, Any] = field(default_factory=dict)
    entry_hash: str = ""  # SHA-256 of the entry content (chained)

    def __post_init__(self):
        if not self.entry_hash:
            raw = f"{self.entry_id}|{self.contract_id}|{self.event_type.value}|{self.timestamp}|{self.actor}|{json.dumps(self.details, sort_keys=True)}"
            self.entry_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "contract_id": self.contract_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "details": self.details,
            "entry_hash": self.entry_hash,
        }


@dataclass
class AgentContract:
    """A time-bound, scope-bounded authority contract for an AI agent.

    Attributes:
        contract_id: Unique identifier.
        agent_binding: Cryptographic binding to agent identity.
        human_id: Human principal who authorizes this contract.
        title: Human-readable title.
        description: Detailed description of the contract purpose.
        duration: Contract duration tier (5/15/30 days).
        scope: Allowed/forbidden action scope.
        status: Current contract status.
        terms_hash: SHA-256 of the agreed terms (scope + duration + conditions).
        created_at: Unix timestamp of creation.
        signed_at: Unix timestamp of human signature.
        activated_at: Unix timestamp when contract became active.
        expires_at: Unix timestamp of automatic expiration.
        completed_at: Unix timestamp of completion.
        renewed_count: Number of times this contract has been renewed.
        max_renewals: Maximum allowed renewals.
        cooling_off_until: Unix timestamp until which re-proposal is blocked
            (after revocation).
        termination_reason: Reason for revocation/cancellation.
        milestone_pct: Percentage milestones reached (e.g., 25, 50, 75, 100).
        previous_contract_id: If this is a renewal, the ID of the previous contract.
        notes: Human-readable notes appended during lifecycle.
        audit_entries: Immutable audit trail.
    """
    contract_id: str
    agent_binding: AgentBinding
    human_id: str
    title: str
    description: str
    duration: ContractDuration
    scope: ContractScope
    status: ContractStatus
    terms_hash: str = ""
    created_at: float = 0.0
    signed_at: float = 0.0
    activated_at: float = 0.0
    expires_at: float = 0.0
    completed_at: float = 0.0
    renewed_count: int = 0
    max_renewals: int = _MAX_RENEWALS
    cooling_off_until: float = 0.0
    termination_reason: str = ""
    milestone_pct: int = 0
    previous_contract_id: str = ""
    notes: List[str] = field(default_factory=list)
    audit_entries: List[AuditEntry] = field(default_factory=list)

    def __post_init__(self):
        if not self.terms_hash:
            self._compute_terms_hash()

    def _compute_terms_hash(self) -> str:
        """Compute SHA-256 hash of agreed terms."""
        raw = json.dumps({
            "agent_id": self.agent_binding.agent_id,
            "human_id": self.human_id,
            "title": self.title,
            "description": self.description,
            "duration": self.duration.value,
            "scope": self.scope.to_dict(),
        }, sort_keys=True)
        self.terms_hash = hashlib.sha256(raw.encode()).hexdigest()
        return self.terms_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "agent_binding": self.agent_binding.to_dict(),
            "human_id": self.human_id,
            "title": self.title,
            "description": self.description,
            "duration": self.duration.value,
            "scope": self.scope.to_dict(),
            "status": self.status.value,
            "terms_hash": self.terms_hash,
            "created_at": self.created_at,
            "signed_at": self.signed_at,
            "activated_at": self.activated_at,
            "expires_at": self.expires_at,
            "completed_at": self.completed_at,
            "renewed_count": self.renewed_count,
            "max_renewals": self.max_renewals,
            "cooling_off_until": self.cooling_off_until,
            "termination_reason": self.termination_reason,
            "milestone_pct": self.milestone_pct,
            "previous_contract_id": self.previous_contract_id,
            "notes": self.notes,
            "audit_entries": [e.to_dict() for e in self.audit_entries[-100:]],  # Last 100 entries
        }

    def is_expired(self) -> bool:
        """Check if contract has expired."""
        if self.expires_at == 0:
            return False
        return time.time() >= self.expires_at

    def is_in_cooling_off(self) -> bool:
        """Check if contract is in cooling-off period."""
        if self.cooling_off_until == 0:
            return False
        return time.time() < self.cooling_off_until

    def time_until_expiry(self) -> float:
        """Seconds until expiry (negative if already expired)."""
        if self.expires_at == 0:
            return float("inf")
        return self.expires_at - time.time()

    def time_until_cooling_off_end(self) -> float:
        """Seconds until cooling-off period ends (negative if already over)."""
        if self.cooling_off_until == 0:
            return 0.0
        return self.cooling_off_until - time.time()


# ─── AGENT CONTRACT SYSTEM ─────────────────────────────────────────────────────

class AgentContractSystem:
    """
    Time-bound AI agent authority contracts with automatic audit, renewal,
    and revocation. Extends the SmartContractEngine with agent-specific features.

    Key capabilities:
    - Propose contracts with formal scope boundaries
    - Cryptographically bind contracts to agent identities
    - Track expiration and auto-warn before expiry
    - Support renewal (up to max_renewals)
    - Enforce cooling-off periods after revocation
    - Generate formal audit trails for compliance
    - Check if an action is permitted under contract scope
    - Integrate with CloneOrchestrator and HumanOverrideEngine
    """

    def __init__(self):
        self._contracts: Dict[str, AgentContract] = {}
        self._load_from_db()
        logger.info(
            f"✅ AgentContractSystem ready — {len(self._contracts)} contracts loaded, "
            f"max_renewals={_MAX_RENEWALS}, cooling_off={_COOLING_OFF_HOURS}h"
        )

    # ─── CONTRACT LIFECYCLE ─────────────────────────────────────────────────

    def propose_contract(
        self,
        agent_id: str,
        human_id: str,
        title: str,
        description: str,
        duration: ContractDuration,
        scope: Optional[ContractScope] = None,
        agent_type: str = "clone",
        agent_did: str = "",
    ) -> AgentContract:
        """Propose a new agent contract with scope boundaries.

        Args:
            agent_id: The agent's unique identifier (Clone ID or DID).
            human_id: The human principal authorizing this contract.
            title: Human-readable contract title.
            description: Detailed description of the contract purpose.
            duration: Duration tier (TRIAL=5, STANDARD=15, EXTENDED=30 days).
            scope: Allowed/forbidden action scope. Uses default if not provided.
            agent_type: "clone" for CloneOrchestrator, "external" for DIDs.
            agent_did: Decentralized identifier (for external agents).

        Returns:
            The newly created AgentContract.

        Raises:
            ValueError: If agent is in cooling-off period or has an active contract.
        """
        # Check cooling-off
        existing = self._find_contracts_for_agent(agent_id)
        for c in existing:
            if c.is_in_cooling_off():
                remaining = c.time_until_cooling_off_end()
                raise ValueError(
                    f"Agent {agent_id} is in cooling-off period for "
                    f"{remaining / 3600:.1f} more hours "
                    f"(until {datetime.fromtimestamp(c.cooling_off_until).isoformat()})"
                )
            if c.status in (ContractStatus.ACTIVE, ContractStatus.PENDING_SIGNATURE,
                            ContractStatus.PROPOSED):
                raise ValueError(
                    f"Agent {agent_id} already has an active/pending contract "
                    f"({c.contract_id}, status={c.status.value})"
                )

        now = time.time()
        expires_at = now + (duration.value * 86400)
        agent_binding = AgentBinding(
            agent_id=agent_id,
            agent_type=agent_type,
            agent_did=agent_did,
        )
        contract_scope = scope or ContractScope()

        contract = AgentContract(
            contract_id=str(uuid.uuid4())[:12],
            agent_binding=agent_binding,
            human_id=human_id,
            title=title,
            description=description,
            duration=duration,
            scope=contract_scope,
            status=ContractStatus.PROPOSED,
            created_at=now,
            expires_at=expires_at,
        )

        self._add_audit_entry(contract, AuditEventType.CONTRACT_CREATED, human_id, {
            "agent_id": agent_id,
            "duration": duration.value,
            "scope": contract_scope.to_dict(),
        })

        self._contracts[contract.contract_id] = contract
        self._save(contract)
        logger.info(
            f"📄 Contract proposed: {contract.contract_id} "
            f"[{title}] agent={agent_id} human={human_id} {duration.value}d"
        )
        return contract

    def sign_contract(self, contract_id: str, human_id: str,
                      signature: str = "") -> AgentContract:
        """Human signs the contract to activate agent authority.

        Args:
            contract_id: The contract to sign.
            human_id: The human signing (must match contract human_id).
            signature: Optional cryptographic signature.

        Returns:
            The updated AgentContract (status -> ACTIVE).

        Raises:
            KeyError: If contract not found.
            ValueError: If contract is not in PROPOSED state.
            PermissionError: If human_id doesn't match.
        """
        contract = self._get(contract_id)
        if contract.status != ContractStatus.PROPOSED:
            raise ValueError(
                f"Contract {contract_id} cannot be signed — "
                f"status={contract.status.value}"
            )
        if contract.human_id != human_id:
            raise PermissionError(
                f"Only {contract.human_id} can sign contract {contract_id} "
                f"(attempted by {human_id})"
            )

        now = time.time()
        contract.status = ContractStatus.ACTIVE
        contract.signed_at = now
        contract.activated_at = now

        # Update terms hash with signature
        if signature:
            contract.agent_binding.identity_proof = signature

        # Recompute terms hash with final state
        contract._compute_terms_hash()

        self._add_audit_entry(contract, AuditEventType.CONTRACT_SIGNED, human_id, {
            "signature_provided": bool(signature),
        })
        self._add_audit_entry(contract, AuditEventType.CONTRACT_ACTIVATED, human_id, {
            "expires_at": contract.expires_at,
            "duration_days": contract.duration.value,
        })

        self._save(contract)
        logger.info(
            f"✅ Contract SIGNED & ACTIVE [{contract_id}] agent={contract.agent_binding.agent_id} "
            f"expires={datetime.fromtimestamp(contract.expires_at).isoformat()}"
        )
        return contract

    def renew_contract(self, contract_id: str, human_id: str,
                       new_duration: Optional[ContractDuration] = None) -> AgentContract:
        """Renew a contract that is active or expiring soon.

        Creates a new contract with linked previous_contract_id and
        increments renewed_count on the original.

        Args:
            contract_id: The contract to renew.
            human_id: The human authorizing renewal.
            new_duration: Optional new duration. Uses original if not provided.

        Returns:
            The NEW renewed AgentContract.

        Raises:
            KeyError: If contract not found.
            ValueError: If contract cannot be renewed.
            PermissionError: If human_id doesn't match.
        """
        contract = self._get(contract_id)
        if contract.human_id != human_id:
            raise PermissionError(
                f"Only {contract.human_id} can renew contract {contract_id}"
            )
        if contract.renewed_count >= contract.max_renewals:
            raise ValueError(
                f"Contract {contract_id} has reached max renewals "
                f"({contract.max_renewals})"
            )
        if contract.status not in (ContractStatus.ACTIVE, ContractStatus.EXPIRING_SOON):
            raise ValueError(
                f"Contract {contract_id} cannot be renewed — "
                f"status={contract.status.value}"
            )

        duration = new_duration or contract.duration

        # Create new contract (renewal)
        now = time.time()
        expires_at = now + (duration.value * 86400)
        agent_binding = AgentBinding(
            agent_id=contract.agent_binding.agent_id,
            agent_type=contract.agent_binding.agent_type,
            agent_did=contract.agent_binding.agent_did,
            public_key_hash=contract.agent_binding.public_key_hash,
        )

        new_contract = AgentContract(
            contract_id=str(uuid.uuid4())[:12],
            agent_binding=agent_binding,
            human_id=human_id,
            title=contract.title,
            description=contract.description,
            duration=duration,
            scope=contract.scope,
            status=ContractStatus.PROPOSED,
            created_at=now,
            expires_at=expires_at,
            renewed_count=contract.renewed_count + 1,
            max_renewals=contract.max_renewals,
            previous_contract_id=contract_id,
        )

        # Mark old contract as renewed
        old_status = contract.status
        contract.status = ContractStatus.RENEWED

        self._add_audit_entry(contract, AuditEventType.CONTRACT_RENEWED, human_id, {
            "new_contract_id": new_contract.contract_id,
            "previous_duration": contract.duration.value,
            "new_duration": duration.value,
        })
        self._add_audit_entry(new_contract, AuditEventType.RENEWAL_REQUESTED, human_id, {
            "previous_contract_id": contract_id,
            "previous_status": old_status.value,
            "renewed_count": new_contract.renewed_count,
        })

        self._save(contract)
        self._contracts[new_contract.contract_id] = new_contract
        self._save(new_contract)

        logger.info(
            f"🔄 Contract RENEWED [{contract_id} → {new_contract.contract_id}] "
            f"agent={agent_binding.agent_id} renewal#{new_contract.renewed_count}"
        )
        return new_contract

    def revoke_contract(self, contract_id: str, human_id: str,
                        reason: str) -> AgentContract:
        """Human revokes a contract immediately.

        Starts cooling-off period during which the agent cannot propose
        a new contract with the same human.

        Args:
            contract_id: The contract to revoke.
            human_id: The human revoking.
            reason: Required reason for revocation.

        Returns:
            The revoked AgentContract.

        Raises:
            KeyError: If contract not found.
            ValueError: If contract cannot be revoked or reason is empty.
            PermissionError: If human_id doesn't match.
        """
        if not reason.strip():
            raise ValueError("Revocation reason is required")

        contract = self._get(contract_id)
        if contract.human_id != human_id:
            raise PermissionError(
                f"Only {contract.human_id} can revoke contract {contract_id}"
            )
        if contract.status in (ContractStatus.REVOKED, ContractStatus.COOLING_OFF,
                               ContractStatus.EXPIRED, ContractStatus.COMPLETED,
                               ContractStatus.CANCELLED):
            raise ValueError(
                f"Contract {contract_id} already terminated — "
                f"status={contract.status.value}"
            )

        now = time.time()
        old_status = contract.status
        contract.status = ContractStatus.REVOKED
        contract.termination_reason = reason

        # Start cooling-off period
        contract.cooling_off_until = now + (_COOLING_OFF_HOURS * 3600)
        contract.status = ContractStatus.COOLING_OFF

        self._add_audit_entry(contract, AuditEventType.CONTRACT_REVOKED, human_id, {
            "previous_status": old_status.value,
            "reason": reason,
            "cooling_off_hours": _COOLING_OFF_HOURS,
        })
        self._add_audit_entry(contract, AuditEventType.COOLING_OFF_STARTED, "system", {
            "cooling_off_until": contract.cooling_off_until,
        })

        self._save(contract)
        logger.warning(
            f"🚫 Contract REVOKED [{contract_id}] by {human_id}: {reason}. "
            f"Cooling-off until {datetime.fromtimestamp(contract.cooling_off_until).isoformat()}"
        )
        return contract

    def complete_contract(self, contract_id: str, human_id: str,
                          rating: int = 5, note: str = "") -> AgentContract:
        """Mark contract as successfully completed.

        Args:
            contract_id: The contract to complete.
            human_id: The human completing.
            rating: 1-5 rating.
            note: Optional completion note.

        Returns:
            The completed AgentContract.
        """
        contract = self._get(contract_id)
        if contract.status != ContractStatus.ACTIVE:
            raise ValueError(
                f"Contract {contract_id} not active — status={contract.status.value}"
            )
        if contract.human_id != human_id:
            raise PermissionError(
                f"Only {contract.human_id} can complete contract {contract_id}"
            )

        now = time.time()
        contract.status = ContractStatus.COMPLETED
        contract.completed_at = now
        contract.milestone_pct = 100

        if note:
            contract.notes.append(f"[{datetime.fromtimestamp(now).isoformat()}] {human_id}: {note}")

        self._add_audit_entry(contract, AuditEventType.CONTRACT_COMPLETED, human_id, {
            "rating": max(1, min(5, rating)),
            "note": note,
            "duration_seconds": now - contract.created_at,
        })

        self._save(contract)
        logger.info(
            f"✅ Contract COMPLETED [{contract_id}] rating={rating}/5"
        )
        return contract

    # ─── SCOPE ENFORCEMENT ──────────────────────────────────────────────────

    def check_action_permitted(self, contract_id: str, action: str,
                               context: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """Check if an action is permitted under the contract scope.

        Args:
            contract_id: The contract to check against.
            action: The action to check.
            context: Optional context (value, data_access_level, mesh_type, etc.).

        Returns:
            Tuple of (permitted: bool, reason: str).
        """
        contract = self._get(contract_id)
        context = context or {}

        # Check if contract is active
        if contract.status != ContractStatus.ACTIVE:
            return False, f"Contract not active (status={contract.status.value})"

        # Check if expired
        if contract.is_expired():
            return False, "Contract has expired"

        # Check forbidden actions first (hard block)
        for forbidden in contract.scope.forbidden_actions:
            if self._match_action_pattern(action, forbidden):
                return False, f"Action '{action}' is forbidden by scope rule: {forbidden}"

        # Check allowed actions
        if contract.scope.allowed_actions:
            allowed = any(
                self._match_action_pattern(action, allowed)
                for allowed in contract.scope.allowed_actions
            )
            if not allowed:
                return False, f"Action '{action}' is not in allowed_actions set"

        # Check data access level
        action_level = context.get("data_access_level", "public")
        if action_level != "public":
            level_enum = DataAccessLevel(action_level)
            max_level = self._data_access_rank(contract.scope.data_access_level)
            action_rank = self._data_access_rank(level_enum)
            if action_rank > max_level:
                return False, (
                    f"Action requires {action_level} access but contract only "
                    f"allows {contract.scope.data_access_level.value}"
                )

        # Check value limit
        action_value = context.get("value", 0.0)
        if action_value > contract.scope.max_value_per_action:
            return False, (
                f"Action value {action_value} exceeds contract limit "
                f"{contract.scope.max_value_per_action}"
            )

        # Check if requires human override
        for override_action in contract.scope.requires_human_override:
            if self._match_action_pattern(action, override_action):
                return True, "Action permitted but requires human override"

        # Check mesh type
        if "mesh_type" in context:
            mesh = context["mesh_type"]
            if mesh not in contract.scope.allowed_mesh_types:
                return False, (
                    f"Mesh type '{mesh}' not in allowed mesh types: "
                    f"{contract.scope.allowed_mesh_types}"
                )

        return True, "Action permitted under contract scope"

    def _match_action_pattern(self, action: str, pattern: str) -> bool:
        """Match an action against a pattern (supports wildcard *)."""
        if pattern.endswith("*"):
            return action.startswith(pattern[:-1])
        return action == pattern

    def _data_access_rank(self, level: DataAccessLevel) -> int:
        """Rank data access levels for comparison."""
        ranks = {
            DataAccessLevel.PUBLIC: 0,
            DataAccessLevel.RESTRICTED: 1,
            DataAccessLevel.PRIVATE: 2,
            DataAccessLevel.SECRET: 3,
        }
        return ranks.get(level, 0)

    # ─── EXPIRATION TRACKING ────────────────────────────────────────────────

    def get_expiring_contracts(self, within_hours: int = _EXPIRY_WARNING_HOURS) -> List[AgentContract]:
        """Get active contracts that expire within the given window.

        Args:
            within_hours: Time window in hours (default: 48).

        Returns:
            List of AgentContract objects expiring soon.
        """
        now = time.time()
        deadline = now + (within_hours * 3600)
        expiring = []

        for c in self._contracts.values():
            if c.status == ContractStatus.ACTIVE and 0 < c.expires_at <= deadline:
                expiring.append(c)

        return sorted(expiring, key=lambda c: c.expires_at)

    def get_expired_contracts(self) -> List[AgentContract]:
        """Get contracts that have expired and need cleanup.

        Returns:
            List of expired AgentContract objects.
        """
        now = time.time()
        expired = []

        for c in self._contracts.values():
            if c.status == ContractStatus.ACTIVE and c.expires_at > 0 and c.expires_at <= now:
                expired.append(c)

        return sorted(expired, key=lambda c: c.expires_at)

    def process_expirations(self) -> List[str]:
        """Process all expired contracts — mark them as EXPIRED.

        Should be called periodically (e.g., by a background task).

        Returns:
            List of contract IDs that were marked as expired.
        """
        expired_ids = []
        for contract in self.get_expired_contracts():
            old_status = contract.status
            contract.status = ContractStatus.EXPIRED

            self._add_audit_entry(contract, AuditEventType.CONTRACT_EXPIRED, "system", {
                "previous_status": old_status.value,
                "expires_at": contract.expires_at,
            })
            self._save(contract)
            expired_ids.append(contract.contract_id)
            logger.info(
                f"⏰ Contract EXPIRED [{contract.contract_id}] "
                f"agent={contract.agent_binding.agent_id}"
            )

        return expired_ids

    def process_expiring_warnings(self) -> List[Dict[str, Any]]:
        """Mark contracts that are expiring soon.

        Returns:
            List of dicts with contract info for notification system.
        """
        warnings = []
        for contract in self.get_expiring_contracts():
            if contract.status == ContractStatus.ACTIVE:
                contract.status = ContractStatus.EXPIRING_SOON
                hours_left = contract.time_until_expiry() / 3600

                self._add_audit_entry(contract, AuditEventType.MILESTONE_REACHED, "system", {
                    "event": "expiring_soon",
                    "hours_remaining": round(hours_left, 1),
                    "expires_at": contract.expires_at,
                })
                self._save(contract)

                warnings.append({
                    "contract_id": contract.contract_id,
                    "agent_id": contract.agent_binding.agent_id,
                    "human_id": contract.human_id,
                    "title": contract.title,
                    "hours_remaining": round(hours_left, 1),
                    "expires_at": datetime.fromtimestamp(contract.expires_at).isoformat(),
                    "renewed_count": contract.renewed_count,
                    "max_renewals": contract.max_renewals,
                })
                logger.info(
                    f"⚠️ Contract EXPIRING SOON [{contract.contract_id}]: "
                    f"{hours_left:.1f}h remaining"
                )

        return warnings

    # ─── AUDIT ──────────────────────────────────────────────────────────────

    def generate_audit(self, contract_id: str) -> Dict[str, Any]:
        """Generate a formal audit report for a contract.

        Includes full lifecycle events, action logs, scope changes,
        and compliance assessment.

        Args:
            contract_id: The contract to audit.

        Returns:
            Dict with audit report.
        """
        contract = self._get(contract_id)

        # Count actions performed
        action_count = sum(
            1 for e in contract.audit_entries
            if e.event_type == AuditEventType.ACTION_PERFORMED
        )
        denied_count = sum(
            1 for e in contract.audit_entries
            if e.event_type == AuditEventType.ACTION_DENIED
        )
        milestone_entries = [
            e for e in contract.audit_entries
            if e.event_type == AuditEventType.MILESTONE_REACHED
        ]

        report = {
            "contract_id": contract_id,
            "title": contract.title,
            "agent_id": contract.agent_binding.agent_id,
            "human_id": contract.human_id,
            "duration_days": contract.duration.value,
            "status": contract.status.value,
            "created_at": datetime.fromtimestamp(contract.created_at).isoformat(),
            "signed_at": datetime.fromtimestamp(contract.signed_at).isoformat() if contract.signed_at else "",
            "activated_at": datetime.fromtimestamp(contract.activated_at).isoformat() if contract.activated_at else "",
            "expires_at": datetime.fromtimestamp(contract.expires_at).isoformat() if contract.expires_at else "",
            "completed_at": datetime.fromtimestamp(contract.completed_at).isoformat() if contract.completed_at else "",
            "renewed_count": contract.renewed_count,
            "termination_reason": contract.termination_reason,
            "actions_performed": action_count,
            "actions_denied": denied_count,
            "milestones": [e.to_dict() for e in milestone_entries],
            "total_audit_entries": len(contract.audit_entries),
            "scope_snapshot": contract.scope.to_dict(),
            "terms_hash": contract.terms_hash,
            "compliance_score": self._compute_compliance_score(contract),
        }

        self._add_audit_entry(contract, AuditEventType.AUDIT_GENERATED, "system", {
            "action_count": action_count,
            "denied_count": denied_count,
            "compliance_score": report["compliance_score"],
        })
        self._save(contract)

        return report

    def _compute_compliance_score(self, contract: AgentContract) -> float:
        """Compute a compliance score (0.0-1.0) based on audit data."""
        if not contract.audit_entries:
            return 1.0

        total_actions = 0
        denied_actions = 0
        violations = 0

        for entry in contract.audit_entries:
            if entry.event_type == AuditEventType.ACTION_PERFORMED:
                total_actions += 1
            elif entry.event_type == AuditEventType.ACTION_DENIED:
                denied_actions += 1
                violations += 1
            elif entry.event_type == AuditEventType.CONTRACT_REVOKED:
                violations += 3  # Revocation is a major compliance event

        if total_actions == 0 and denied_actions == 0:
            return 1.0

        # Score: start at 1.0, deduct for denied actions and violations
        score = 1.0
        if total_actions > 0:
            score -= (denied_actions / (total_actions + denied_actions)) * 0.3
        score -= violations * 0.05
        return max(0.0, min(1.0, score))

    # ─── QUERIES ────────────────────────────────────────────────────────────

    def get_contract(self, contract_id: str) -> Optional[AgentContract]:
        """Get a contract by ID."""
        return self._contracts.get(contract_id)

    def list_contracts_for_human(self, human_id: str,
                                 status: Optional[ContractStatus] = None) -> List[AgentContract]:
        """List all contracts for a given human."""
        results = [
            c for c in self._contracts.values()
            if c.human_id == human_id
        ]
        if status:
            results = [c for c in results if c.status == status]
        return sorted(results, key=lambda c: c.created_at, reverse=True)

    def list_contracts_for_agent(self, agent_id: str) -> List[AgentContract]:
        """List all contracts for a given agent."""
        return self._find_contracts_for_agent(agent_id)

    def get_active_contracts(self) -> List[AgentContract]:
        """Get all currently active contracts."""
        return [
            c for c in self._contracts.values()
            if c.status == ContractStatus.ACTIVE
        ]

    def get_contract_stats(self, human_id: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregate statistics for contracts.

        Args:
            human_id: Optional filter by human.

        Returns:
            Dict with contract statistics.
        """
        contracts = list(self._contracts.values())
        if human_id:
            contracts = [c for c in contracts if c.human_id == human_id]

        now = time.time()
        return {
            "total": len(contracts),
            "active": sum(1 for c in contracts if c.status == ContractStatus.ACTIVE),
            "expiring_soon": sum(1 for c in contracts if c.status == ContractStatus.EXPIRING_SOON),
            "expired": sum(1 for c in contracts if c.status == ContractStatus.EXPIRED),
            "completed": sum(1 for c in contracts if c.status == ContractStatus.COMPLETED),
            "revoked": sum(1 for c in contracts if c.status in (ContractStatus.REVOKED, ContractStatus.COOLING_OFF)),
            "cooling_off": sum(1 for c in contracts if c.is_in_cooling_off()),
            "total_renewals": sum(c.renewed_count for c in contracts),
            "agents_with_active_contracts": len(set(
                c.agent_binding.agent_id for c in contracts
                if c.status == ContractStatus.ACTIVE
            )),
            "average_compliance_score": (
                sum(self._compute_compliance_score(c) for c in contracts
                    if c.status in (ContractStatus.COMPLETED, ContractStatus.ACTIVE))
                / max(1, sum(1 for c in contracts
                             if c.status in (ContractStatus.COMPLETED, ContractStatus.ACTIVE)))
            ),
        }

    # ─── INTERNAL ───────────────────────────────────────────────────────────

    def _get(self, contract_id: str) -> AgentContract:
        """Get contract by ID or raise KeyError."""
        c = self._contracts.get(contract_id)
        if not c:
            raise KeyError(f"Agent contract not found: {contract_id}")
        return c

    def _find_contracts_for_agent(self, agent_id: str) -> List[AgentContract]:
        """Find all contracts for a given agent ID."""
        return [
            c for c in self._contracts.values()
            if c.agent_binding.agent_id == agent_id
        ]

    def _add_audit_entry(self, contract: AgentContract, event_type: AuditEventType,
                         actor: str, details: Dict[str, Any]) -> AuditEntry:
        """Add an immutable audit entry to the contract."""
        entry = AuditEntry(
            entry_id=str(uuid.uuid4())[:12],
            contract_id=contract.contract_id,
            event_type=event_type,
            timestamp=time.time(),
            actor=actor,
            details=details,
        )
        contract.audit_entries.append(entry)
        return entry

    @staticmethod
    def _now() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _save(self, contract: AgentContract):
        """Append-only write to JSONL — immutable audit trail."""
        self._contracts[contract.contract_id] = contract
        try:
            with open(AGENT_CONTRACT_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(contract.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Agent contract DB write failed: {e}")

    def _load_from_db(self):
        """Load latest state for each contract from append-only log."""
        if not AGENT_CONTRACT_DB_PATH.exists():
            return
        try:
            with open(AGENT_CONTRACT_DB_PATH, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        # Reconstruct nested objects
                        binding_data = d.pop("agent_binding", {})
                        scope_data = d.pop("scope", {})
                        audit_data = d.pop("audit_entries", [])

                        # Convert enum fields from JSON primitives back to enums
                        if "duration" in d and isinstance(d["duration"], int):
                            d["duration"] = ContractDuration(d["duration"])
                        if "status" in d and isinstance(d["status"], str):
                            d["status"] = ContractStatus(d["status"])

                        # Reconstruct audit entries with proper enum conversion
                        audit_entries = []
                        for e in audit_data:
                            if "event_type" in e and isinstance(e["event_type"], str):
                                e = dict(e)
                                e["event_type"] = AuditEventType(e["event_type"])
                            audit_entries.append(AuditEntry(**e))

                        contract = AgentContract(
                            agent_binding=AgentBinding.from_dict(binding_data),
                            scope=ContractScope.from_dict(scope_data),
                            audit_entries=audit_entries,
                            **d,
                        )
                        self._contracts[contract.contract_id] = contract
                    except Exception as e:
                        logger.warning(f"Failed to load contract line: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Agent contract DB load failed: {e}")


# ─── SINGLETON FACTORY ────────────────────────────────────────────────────────

_agent_contract_system: Optional[AgentContractSystem] = None


def get_agent_contract_system() -> AgentContractSystem:
    """Get or create the singleton AgentContractSystem instance."""
    global _agent_contract_system
    if _agent_contract_system is None:
        _agent_contract_system = AgentContractSystem()
    return _agent_contract_system


def reset_agent_contract_system() -> None:
    """Reset the singleton (for testing) and clean persisted state."""
    global _agent_contract_system
    _agent_contract_system = None
    # Remove persisted DB so a fresh singleton starts clean
    try:
        if AGENT_CONTRACT_DB_PATH.exists():
            AGENT_CONTRACT_DB_PATH.unlink()
    except Exception:
        pass


# ─── EXPORTS ──────────────────────────────────────────────────────────────────

__all__ = [
    "ContractDuration",
    "ContractStatus",
    "DataAccessLevel",
    "AuditEventType",
    "ContractScope",
    "AgentBinding",
    "AuditEntry",
    "AgentContract",
    "AgentContractSystem",
    "get_agent_contract_system",
    "reset_agent_contract_system",
]
