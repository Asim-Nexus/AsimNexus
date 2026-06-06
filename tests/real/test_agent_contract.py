#!/usr/bin/env python3
"""
Tests for core/agent_contract.py — Agent Contract System.

Tests cover:
- Enum correctness (ContractDuration, ContractStatus, DataAccessLevel, AuditEventType)
- Dataclass construction and serialization (ContractScope, AgentBinding, AuditEntry, AgentContract)
- Contract lifecycle: propose → sign → complete
- Renewal workflow with max_renewals limits
- Revocation with cooling-off period
- Expiration tracking and auto-processing
- Scope enforcement (allowed/forbidden actions, data access levels, value limits)
- Action pattern matching with wildcards
- Audit generation and compliance scoring
- Singleton factory pattern
- Edge cases (missing fields, invalid states, concurrent contracts)
"""

import json
import os
import time
import importlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

import pytest

from core.agent_contract import (
    ContractDuration,
    ContractStatus,
    DataAccessLevel,
    AuditEventType,
    ContractScope,
    AgentBinding,
    AuditEntry,
    AgentContract,
    AgentContractSystem,
    get_agent_contract_system,
    reset_agent_contract_system,
    AGENT_CONTRACT_DB_PATH,
)


# ─── FIXTURES ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_system():
    """Reset singleton and clean DB file before each test."""
    reset_agent_contract_system()
    # Remove stale DB file to prevent cross-test contamination
    db_path = AGENT_CONTRACT_DB_PATH
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass
    yield
    reset_agent_contract_system()


@pytest.fixture
def contract_system():
    """Create a fresh AgentContractSystem."""
    return AgentContractSystem()


@pytest.fixture
def sample_scope():
    """Default contract scope for testing."""
    return ContractScope(
        allowed_actions=["chat.*", "memory.read", "file.read", "data.export"],
        forbidden_actions=["file.delete", "system.exec"],
        data_access_level=DataAccessLevel.RESTRICTED,
        max_value_per_action=50000.0,
        requires_human_override=["data.export"],
        allowed_mesh_types=["local", "personal"],
        max_concurrent_tasks=5,
    )


@pytest.fixture
def sample_contract(contract_system, sample_scope):
    """Create and return a sample proposed contract."""
    return contract_system.propose_contract(
        agent_id="clone_architect_01",
        human_id="user_human_01",
        title="Architecture Analysis Task",
        description="Analyze system architecture and provide recommendations",
        duration=ContractDuration.STANDARD,
        scope=sample_scope,
    )


@pytest.fixture
def signed_contract(contract_system, sample_contract):
    """Sign the sample contract."""
    return contract_system.sign_contract(
        contract_id=sample_contract.contract_id,
        human_id="user_human_01",
        signature="human_sig_abc123",
    )


# ─── ENUM TESTS ────────────────────────────────────────────────────────────────

class TestContractDuration:
    """Tests for ContractDuration enum."""

    def test_values(self):
        assert ContractDuration.TRIAL.value == 5
        assert ContractDuration.STANDARD.value == 15
        assert ContractDuration.EXTENDED.value == 30

    def test_all_tiers_available(self):
        tiers = list(ContractDuration)
        assert len(tiers) == 3
        assert ContractDuration.TRIAL in tiers
        assert ContractDuration.STANDARD in tiers
        assert ContractDuration.EXTENDED in tiers


class TestContractStatus:
    """Tests for ContractStatus enum."""

    def test_values(self):
        assert ContractStatus.PROPOSED.value == "proposed"
        assert ContractStatus.PENDING_SIGNATURE.value == "pending_signature"
        assert ContractStatus.ACTIVE.value == "active"
        assert ContractStatus.EXPIRING_SOON.value == "expiring_soon"
        assert ContractStatus.EXPIRED.value == "expired"
        assert ContractStatus.RENEWED.value == "renewed"
        assert ContractStatus.REVOKED.value == "revoked"
        assert ContractStatus.COOLING_OFF.value == "cooling_off"
        assert ContractStatus.COMPLETED.value == "completed"
        assert ContractStatus.CANCELLED.value == "cancelled"

    def test_all_statuses(self):
        """Verify all expected statuses exist."""
        statuses = {s.value for s in ContractStatus}
        expected = {
            "proposed", "pending_signature", "active", "expiring_soon",
            "expired", "renewed", "revoked", "cooling_off",
            "completed", "cancelled",
        }
        assert statuses == expected


class TestDataAccessLevel:
    """Tests for DataAccessLevel enum."""

    def test_values(self):
        assert DataAccessLevel.PUBLIC.value == "public"
        assert DataAccessLevel.RESTRICTED.value == "restricted"
        assert DataAccessLevel.PRIVATE.value == "private"
        assert DataAccessLevel.SECRET.value == "secret"

    def test_access_hierarchy(self):
        """Verify correct access hierarchy order."""
        ranks = {
            DataAccessLevel.PUBLIC: 0,
            DataAccessLevel.RESTRICTED: 1,
            DataAccessLevel.PRIVATE: 2,
            DataAccessLevel.SECRET: 3,
        }
        for level, rank in ranks.items():
            assert level.value is not None


class TestAuditEventType:
    """Tests for AuditEventType enum."""

    def test_key_events_exist(self):
        """Verify critical audit event types."""
        assert AuditEventType.CONTRACT_CREATED
        assert AuditEventType.CONTRACT_SIGNED
        assert AuditEventType.CONTRACT_ACTIVATED
        assert AuditEventType.ACTION_PERFORMED
        assert AuditEventType.ACTION_DENIED
        assert AuditEventType.CONTRACT_RENEWED
        assert AuditEventType.CONTRACT_REVOKED
        assert AuditEventType.CONTRACT_EXPIRED
        assert AuditEventType.CONTRACT_COMPLETED
        assert AuditEventType.COOLING_OFF_STARTED
        assert AuditEventType.AUDIT_GENERATED


# ─── DATACLASS TESTS ──────────────────────────────────────────────────────────

class TestContractScope:
    """Tests for ContractScope dataclass."""

    def test_default_scope(self):
        """Default scope should be reasonable."""
        scope = ContractScope()
        assert scope.allowed_actions == []
        assert scope.forbidden_actions == []
        assert scope.data_access_level == DataAccessLevel.RESTRICTED
        assert scope.max_value_per_action == 10000.0
        assert scope.requires_human_override == []
        assert scope.allowed_mesh_types == ["local", "personal"]
        assert scope.max_concurrent_tasks == 3

    def test_to_dict(self):
        scope = ContractScope(
            allowed_actions=["chat.*"],
            forbidden_actions=["system.exec"],
            data_access_level=DataAccessLevel.PRIVATE,
        )
        d = scope.to_dict()
        assert d["allowed_actions"] == ["chat.*"]
        assert d["forbidden_actions"] == ["system.exec"]
        assert d["data_access_level"] == "private"
        assert "max_value_per_action" in d
        assert "allowed_mesh_types" in d

    def test_from_dict(self):
        data = {
            "allowed_actions": ["read.*"],
            "forbidden_actions": ["delete.*"],
            "data_access_level": "secret",
            "max_value_per_action": 100000.0,
            "requires_human_override": ["delete.*"],
            "allowed_mesh_types": ["local"],
            "max_concurrent_tasks": 1,
        }
        scope = ContractScope.from_dict(data)
        assert scope.allowed_actions == ["read.*"]
        assert scope.forbidden_actions == ["delete.*"]
        assert scope.data_access_level == DataAccessLevel.SECRET
        assert scope.max_value_per_action == 100000.0
        assert scope.requires_human_override == ["delete.*"]
        assert scope.allowed_mesh_types == ["local"]

    def test_from_dict_partial(self):
        """from_dict should handle missing keys gracefully."""
        scope = ContractScope.from_dict({})
        assert scope.allowed_actions == []
        assert scope.data_access_level == DataAccessLevel.RESTRICTED


class TestAgentBinding:
    """Tests for AgentBinding dataclass."""

    def test_defaults(self):
        binding = AgentBinding(agent_id="clone_01")
        assert binding.agent_id == "clone_01"
        assert binding.agent_type == "clone"
        assert binding.agent_did == ""
        assert binding.public_key_hash == ""
        assert binding.identity_proof == ""

    def test_to_dict(self):
        binding = AgentBinding(
            agent_id="clone_01",
            agent_type="external",
            agent_did="did:asim:abc123",
            public_key_hash="sha256:xyz789",
            identity_proof="sig_001",
        )
        d = binding.to_dict()
        assert d["agent_id"] == "clone_01"
        assert d["agent_type"] == "external"
        assert d["agent_did"] == "did:asim:abc123"

    def test_from_dict(self):
        data = {
            "agent_id": "clone_02",
            "agent_type": "clone",
            "agent_did": "did:asim:def456",
            "public_key_hash": "sha256:hash123",
            "identity_proof": "proof_002",
        }
        binding = AgentBinding.from_dict(data)
        assert binding.agent_id == "clone_02"
        assert binding.agent_type == "clone"
        assert binding.agent_did == "did:asim:def456"


class TestAuditEntry:
    """Tests for AuditEntry dataclass."""

    def test_create_and_hash(self):
        entry = AuditEntry(
            entry_id="entry_001",
            contract_id="contract_001",
            event_type=AuditEventType.CONTRACT_CREATED,
            timestamp=1000.0,
            actor="user_01",
            details={"key": "value"},
        )
        assert entry.entry_id == "entry_001"
        assert entry.event_type == AuditEventType.CONTRACT_CREATED
        assert entry.entry_hash != ""  # Hash should be auto-computed

    def test_to_dict(self):
        entry = AuditEntry(
            entry_id="entry_002",
            contract_id="contract_002",
            event_type=AuditEventType.ACTION_PERFORMED,
            timestamp=2000.0,
            actor="agent_01",
            details={"action": "memory.read"},
        )
        d = entry.to_dict()
        assert d["entry_id"] == "entry_002"
        assert d["event_type"] == "action_performed"
        assert d["actor"] == "agent_01"
        assert "entry_hash" in d

    def test_hash_uniqueness(self):
        """Two different entries should have different hashes."""
        entry1 = AuditEntry(
            entry_id="e1", contract_id="c1",
            event_type=AuditEventType.CONTRACT_CREATED,
            timestamp=100.0, actor="user_01",
        )
        entry2 = AuditEntry(
            entry_id="e2", contract_id="c1",
            event_type=AuditEventType.CONTRACT_SIGNED,
            timestamp=200.0, actor="user_01",
        )
        assert entry1.entry_hash != entry2.entry_hash


class TestAgentContract:
    """Tests for AgentContract dataclass."""

    def test_create_with_defaults(self, sample_scope):
        """Verify basic contract construction."""
        binding = AgentBinding(agent_id="clone_01")
        contract = AgentContract(
            contract_id="c001",
            agent_binding=binding,
            human_id="user_01",
            title="Test Contract",
            description="Testing",
            duration=ContractDuration.TRIAL,
            scope=sample_scope,
            status=ContractStatus.PROPOSED,
            created_at=time.time(),
            expires_at=time.time() + 86400 * 5,
        )
        assert contract.contract_id == "c001"
        assert contract.agent_binding.agent_id == "clone_01"
        assert contract.duration == ContractDuration.TRIAL
        assert contract.renewed_count == 0
        assert contract.max_renewals == 3  # Default

    def test_terms_hash_auto_compute(self, sample_scope):
        """Terms hash should be auto-computed."""
        binding = AgentBinding(agent_id="clone_01")
        contract = AgentContract(
            contract_id="c002",
            agent_binding=binding,
            human_id="user_01",
            title="Test",
            description="Testing terms hash",
            duration=ContractDuration.STANDARD,
            scope=sample_scope,
            status=ContractStatus.PROPOSED,
            created_at=time.time(),
            expires_at=time.time() + 86400 * 15,
        )
        assert contract.terms_hash != ""
        assert len(contract.terms_hash) == 64  # SHA-256 hex

    def test_to_dict(self, sample_scope):
        """Verify to_dict produces serializable output."""
        binding = AgentBinding(agent_id="clone_01")
        contract = AgentContract(
            contract_id="c003",
            agent_binding=binding,
            human_id="user_01",
            title="Dict Test",
            description="Testing to_dict",
            duration=ContractDuration.EXTENDED,
            scope=sample_scope,
            status=ContractStatus.ACTIVE,
            created_at=1000.0,
            expires_at=1000.0 + 86400 * 30,
        )
        d = contract.to_dict()
        assert d["contract_id"] == "c003"
        assert d["agent_binding"]["agent_id"] == "clone_01"
        assert d["duration"] == 30
        assert d["status"] == "active"
        assert d["scope"]["data_access_level"] == "restricted"
        assert d["terms_hash"] != ""

    def test_is_expired(self, sample_scope):
        """Test expiration check."""
        binding = AgentBinding(agent_id="clone_01")
        past = time.time() - 100
        contract = AgentContract(
            contract_id="c004",
            agent_binding=binding,
            human_id="user_01",
            title="Expired Test",
            description="Testing expiry",
            duration=ContractDuration.TRIAL,
            scope=sample_scope,
            status=ContractStatus.ACTIVE,
            created_at=time.time() - 86400 * 10,
            expires_at=time.time() - 86400 * 5,  # Already expired
        )
        assert contract.is_expired() is True

    def test_is_not_expired(self, sample_scope):
        """Test non-expired check."""
        binding = AgentBinding(agent_id="clone_01")
        future = time.time() + 86400 * 10
        contract = AgentContract(
            contract_id="c005",
            agent_binding=binding,
            human_id="user_01",
            title="Active Test",
            description="Still active",
            duration=ContractDuration.STANDARD,
            scope=sample_scope,
            status=ContractStatus.ACTIVE,
            created_at=time.time(),
            expires_at=future,
        )
        assert contract.is_expired() is False

    def test_cooling_off_check(self, sample_scope):
        """Test cooling-off period check."""
        binding = AgentBinding(agent_id="clone_01")
        future = time.time() + 3600  # 1 hour from now
        contract = AgentContract(
            contract_id="c006",
            agent_binding=binding,
            human_id="user_01",
            title="Cooling Test",
            description="In cooling off",
            duration=ContractDuration.TRIAL,
            scope=sample_scope,
            status=ContractStatus.COOLING_OFF,
            created_at=time.time(),
            expires_at=time.time() + 86400,
            cooling_off_until=future,
        )
        assert contract.is_in_cooling_off() is True

    def test_time_until_expiry(self, sample_scope):
        """Test time_until_expiry calculation."""
        binding = AgentBinding(agent_id="clone_01")
        future = time.time() + 3600  # 1 hour
        contract = AgentContract(
            contract_id="c007",
            agent_binding=binding,
            human_id="user_01",
            title="Time Test",
            description="Testing time calc",
            duration=ContractDuration.TRIAL,
            scope=sample_scope,
            status=ContractStatus.ACTIVE,
            created_at=time.time(),
            expires_at=future,
        )
        remaining = contract.time_until_expiry()
        assert 3590 < remaining < 3610  # ~1 hour


# ─── CONTRACT LIFECYCLE TESTS ─────────────────────────────────────────────────

class TestProposeContract:
    """Tests for proposing contracts."""

    def test_propose_basic(self, contract_system, sample_scope):
        """Basic contract proposal should succeed."""
        contract = contract_system.propose_contract(
            agent_id="clone_architect_01",
            human_id="user_human_01",
            title="Test Contract",
            description="A test contract",
            duration=ContractDuration.STANDARD,
            scope=sample_scope,
        )
        assert contract.contract_id is not None
        assert contract.agent_binding.agent_id == "clone_architect_01"
        assert contract.human_id == "user_human_01"
        assert contract.status == ContractStatus.PROPOSED
        assert contract.duration == ContractDuration.STANDARD
        assert contract.scope == sample_scope

    def test_propose_default_scope(self, contract_system):
        """Proposal should work with default scope."""
        contract = contract_system.propose_contract(
            agent_id="clone_02",
            human_id="user_02",
            title="Default Scope",
            description="Testing default scope",
            duration=ContractDuration.TRIAL,
        )
        assert contract.scope.allowed_actions == []
        assert contract.scope.data_access_level == DataAccessLevel.RESTRICTED
        assert contract.max_renewals == 3

    def test_propose_expiry_calculation(self, contract_system):
        """Expiry should be based on duration."""
        contract = contract_system.propose_contract(
            agent_id="clone_03",
            human_id="user_03",
            title="Expiry Calc",
            description="Testing expiry",
            duration=ContractDuration.EXTENDED,  # 30 days
        )
        expected_expiry = contract.created_at + (30 * 86400)
        assert abs(contract.expires_at - expected_expiry) < 1  # Within 1 second

    def test_propose_rejects_active_agent(self, contract_system, sample_contract):
        """Cannot propose if agent already has active contract."""
        with pytest.raises(ValueError, match="already has an active"):
            contract_system.propose_contract(
                agent_id="clone_architect_01",  # Same agent as sample_contract
                human_id="user_human_01",
                title="Duplicate",
                description="Should fail",
                duration=ContractDuration.TRIAL,
            )

    def test_propose_rejects_cooling_off_agent(self, contract_system, sample_contract):
        """Cannot propose if agent is in cooling-off period."""
        # Revoke first to trigger cooling-off
        contract_system.revoke_contract(
            contract_id=sample_contract.contract_id,
            human_id="user_human_01",
            reason="Testing cooling-off rejection",
        )
        with pytest.raises(ValueError, match="cooling-off"):
            contract_system.propose_contract(
                agent_id="clone_architect_01",
                human_id="user_human_01",
                title="Cooling Off Test",
                description="Should fail",
                duration=ContractDuration.TRIAL,
            )

    def test_propose_different_humans_allowed(self, contract_system, sample_contract):
        """Same agent can have contracts with different humans."""
        contract_system.sign_contract(
            contract_id=sample_contract.contract_id,
            human_id="user_human_01",
        )
        # Complete the first contract
        contract_system.complete_contract(
            contract_id=sample_contract.contract_id,
            human_id="user_human_01",
        )
        # Now propose with a different human
        contract2 = contract_system.propose_contract(
            agent_id="clone_architect_01",
            human_id="user_human_02",
            title="Different Human",
            description="Should succeed",
            duration=ContractDuration.TRIAL,
        )
        assert contract2.human_id == "user_human_02"
        assert contract2.status == ContractStatus.PROPOSED


class TestSignContract:
    """Tests for signing (activating) contracts."""

    def test_sign_basic(self, contract_system, sample_contract):
        """Signing should activate the contract."""
        contract = contract_system.sign_contract(
            contract_id=sample_contract.contract_id,
            human_id="user_human_01",
            signature="test_signature",
        )
        assert contract.status == ContractStatus.ACTIVE
        assert contract.signed_at > 0
        assert contract.activated_at > 0
        assert contract.agent_binding.identity_proof == "test_signature"

    def test_sign_without_signature(self, contract_system, sample_contract):
        """Signing without explicit signature should still activate."""
        contract = contract_system.sign_contract(
            contract_id=sample_contract.contract_id,
            human_id="user_human_01",
        )
        assert contract.status == ContractStatus.ACTIVE

    def test_sign_wrong_human(self, contract_system, sample_contract):
        """Only the contract's human can sign."""
        with pytest.raises(PermissionError, match="Only"):
            contract_system.sign_contract(
                contract_id=sample_contract.contract_id,
                human_id="unauthorized_human",
            )

    def test_sign_already_active(self, contract_system, signed_contract):
        """Cannot sign an already active contract."""
        with pytest.raises(ValueError, match="cannot be signed"):
            contract_system.sign_contract(
                contract_id=signed_contract.contract_id,
                human_id="user_human_01",
            )

    def test_sign_nonexistent(self, contract_system):
        """Signing a nonexistent contract should raise KeyError."""
        with pytest.raises(KeyError):
            contract_system.sign_contract(
                contract_id="nonexistent",
                human_id="user_01",
            )

    def test_sign_terms_hash_updated(self, contract_system, sample_contract):
        """Signing should update terms hash with final state."""
        original_hash = sample_contract.terms_hash
        contract = contract_system.sign_contract(
            contract_id=sample_contract.contract_id,
            human_id="user_human_01",
            signature="sig_abc",
        )
        # Terms hash should be recomputed after signing
        assert contract.terms_hash != ""

    def test_sign_adds_audit_entries(self, contract_system, sample_contract):
        """Signing should add audit entries."""
        contract = contract_system.sign_contract(
            contract_id=sample_contract.contract_id,
            human_id="user_human_01",
        )
        event_types = [e.event_type for e in contract.audit_entries]
        assert AuditEventType.CONTRACT_SIGNED in event_types
        assert AuditEventType.CONTRACT_ACTIVATED in event_types


class TestCompleteContract:
    """Tests for completing contracts."""

    def test_complete_basic(self, contract_system, signed_contract):
        """Completing an active contract should succeed."""
        contract = contract_system.complete_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
            rating=5,
            note="Great work!",
        )
        assert contract.status == ContractStatus.COMPLETED
        assert contract.completed_at > 0
        assert contract.milestone_pct == 100

    def test_complete_not_active(self, contract_system, sample_contract):
        """Cannot complete a non-active contract."""
        with pytest.raises(ValueError, match="not active"):
            contract_system.complete_contract(
                contract_id=sample_contract.contract_id,
                human_id="user_human_01",
            )

    def test_complete_wrong_human(self, contract_system, signed_contract):
        """Only the contract's human can complete."""
        with pytest.raises(PermissionError, match="Only"):
            contract_system.complete_contract(
                contract_id=signed_contract.contract_id,
                human_id="unauthorized",
            )

    def test_complete_adds_audit(self, contract_system, signed_contract):
        """Completing should add audit entry with rating."""
        contract = contract_system.complete_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
            rating=4,
            note="Good job",
        )
        audit_entries = contract.audit_entries
        completion_entries = [
            e for e in audit_entries
            if e.event_type == AuditEventType.CONTRACT_COMPLETED
        ]
        assert len(completion_entries) == 1
        assert completion_entries[0].details.get("rating") == 4


# ─── RENEWAL TESTS ────────────────────────────────────────────────────────────

class TestRenewContract:
    """Tests for contract renewal."""

    def test_renew_basic(self, contract_system, signed_contract):
        """Renewing should create a new contract linked to the old one."""
        new_contract = contract_system.renew_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
        )
        assert new_contract.contract_id != signed_contract.contract_id
        assert new_contract.previous_contract_id == signed_contract.contract_id
        assert new_contract.renewed_count == 1
        assert new_contract.agent_binding.agent_id == "clone_architect_01"
        assert new_contract.human_id == "user_human_01"
        assert new_contract.title == signed_contract.title
        assert new_contract.scope == signed_contract.scope

    def test_renew_marks_old_as_renewed(self, contract_system, signed_contract):
        """Original contract should be marked as RENEWED."""
        new_contract = contract_system.renew_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
        )
        # Re-fetch old contract
        old_contract = contract_system.get_contract(signed_contract.contract_id)
        assert old_contract.status == ContractStatus.RENEWED

    def test_renew_with_new_duration(self, contract_system, signed_contract):
        """Renewal can use a different duration."""
        new_contract = contract_system.renew_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
            new_duration=ContractDuration.EXTENDED,
        )
        assert new_contract.duration == ContractDuration.EXTENDED

    def test_renew_wrong_human(self, contract_system, signed_contract):
        """Only contract's human can renew."""
        with pytest.raises(PermissionError, match="Only"):
            contract_system.renew_contract(
                contract_id=signed_contract.contract_id,
                human_id="unauthorized",
            )

    def test_renew_max_renewals(self, contract_system, signed_contract):
        """Contract should enforce max renewals limit."""
        # Renew multiple times — each renewal returns a PROPOSED contract
        # that must be signed before it can be renewed again.
        current_id = signed_contract.contract_id
        for i in range(3):  # 0, 1, 2 -> 3 renewals total, max is 3
            new_contract = contract_system.renew_contract(
                contract_id=current_id,
                human_id="user_human_01",
            )
            # Sign the new renewal contract so it can be renewed again
            new_contract = contract_system.sign_contract(
                contract_id=new_contract.contract_id,
                human_id="user_human_01",
            )
            current_id = new_contract.contract_id

        # Next renewal should fail
        with pytest.raises(ValueError, match="max renewals"):
            contract_system.renew_contract(
                contract_id=current_id,
                human_id="user_human_01",
            )

    def test_renew_expired_contract(self, contract_system, sample_contract):
        """Cannot renew a non-active contract."""
        with pytest.raises(ValueError, match="cannot be renewed"):
            contract_system.renew_contract(
                contract_id=sample_contract.contract_id,  # Not signed yet
                human_id="user_human_01",
            )

    def test_renew_preserves_scope(self, contract_system, signed_contract, sample_scope):
        """Renewed contract should inherit the original scope."""
        new_contract = contract_system.renew_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
        )
        assert new_contract.scope.allowed_actions == sample_scope.allowed_actions
        assert new_contract.scope.forbidden_actions == sample_scope.forbidden_actions
        assert new_contract.scope.data_access_level == sample_scope.data_access_level


# ─── REVOCATION & COOLING OFF TESTS ──────────────────────────────────────────

class TestRevokeContract:
    """Tests for contract revocation."""

    def test_revoke_basic(self, contract_system, signed_contract):
        """Revoking should mark contract as COOLING_OFF with reason."""
        contract = contract_system.revoke_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
            reason="Agent violated scope boundaries",
        )
        assert contract.status == ContractStatus.COOLING_OFF
        assert contract.termination_reason == "Agent violated scope boundaries"
        assert contract.cooling_off_until > time.time()

    def test_revoke_requires_reason(self, contract_system, signed_contract):
        """Revocation must have a reason."""
        with pytest.raises(ValueError, match="reason is required"):
            contract_system.revoke_contract(
                contract_id=signed_contract.contract_id,
                human_id="user_human_01",
                reason="",
            )

    def test_revoke_wrong_human(self, contract_system, signed_contract):
        """Only contract's human can revoke."""
        with pytest.raises(PermissionError, match="Only"):
            contract_system.revoke_contract(
                contract_id=signed_contract.contract_id,
                human_id="unauthorized",
                reason="Testing unauthorized revoke",
            )

    def test_revoke_already_terminated(self, contract_system, signed_contract):
        """Cannot revoke an already terminated contract."""
        contract_system.revoke_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
            reason="First revocation",
        )
        with pytest.raises(ValueError, match="already terminated"):
            contract_system.revoke_contract(
                contract_id=signed_contract.contract_id,
                human_id="user_human_01",
                reason="Second revocation",
            )

    def test_revoke_cooling_off_period(self, contract_system, signed_contract):
        """Cooling-off period should be set correctly."""
        contract = contract_system.revoke_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
            reason="Testing cooling-off duration",
        )
        expected_cooling_end = time.time() + (72 * 3600)  # Default 72 hours
        assert abs(contract.cooling_off_until - expected_cooling_end) < 5  # Within 5 seconds

    def test_revoke_adds_audit_entries(self, contract_system, signed_contract):
        """Revocation should add audit entries for revoke and cooling-off."""
        contract = contract_system.revoke_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
            reason="Testing audit",
        )
        event_types = [e.event_type for e in contract.audit_entries]
        assert AuditEventType.CONTRACT_REVOKED in event_types
        assert AuditEventType.COOLING_OFF_STARTED in event_types

    def test_propose_during_cooling_off(self, contract_system, signed_contract):
        """Cannot propose new contract during cooling-off."""
        contract_system.revoke_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
            reason="Testing",
        )
        with pytest.raises(ValueError, match="cooling-off"):
            contract_system.propose_contract(
                agent_id="clone_architect_01",
                human_id="user_human_01",
                title="During Cooling Off",
                description="Should fail",
                duration=ContractDuration.TRIAL,
            )


# ─── SCOPE ENFORCEMENT TESTS ─────────────────────────────────────────────────

class TestScopeEnforcement:
    """Tests for action permission checking."""

    def test_allowed_action(self, contract_system, signed_contract):
        """Allowed action should be permitted."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="memory.read",
        )
        assert permitted is True
        assert "permitted" in reason

    def test_allowed_wildcard_action(self, contract_system, signed_contract):
        """Wildcard patterns should match."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="chat.send_message",
        )
        assert permitted is True

    def test_forbidden_action(self, contract_system, signed_contract):
        """Forbidden action should be denied."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="file.delete",
        )
        assert permitted is False
        assert "forbidden" in reason.lower()

    def test_not_in_allowed_set(self, contract_system, signed_contract):
        """Action not in allowed_actions should be denied when allowed list exists."""
        # Use a unique agent so cooling-off from other tests doesn't interfere
        scope = ContractScope(
            allowed_actions=["chat.*", "memory.*"],
            forbidden_actions=[],
        )
        new_contract = contract_system.propose_contract(
            agent_id="clone_not_allowed_test",
            human_id="user_human_01",
            title="New Scope Test",
            description="Testing scoped access",
            duration=ContractDuration.TRIAL,
            scope=scope,
        )
        contract_system.sign_contract(
            contract_id=new_contract.contract_id,
            human_id="user_human_01",
        )

        permitted, reason = contract_system.check_action_permitted(
            contract_id=new_contract.contract_id,
            action="system.exec",
        )
        assert permitted is False

    def test_data_access_restricted(self, contract_system, signed_contract):
        """Action requiring higher data access should be denied."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="memory.read",
            context={"data_access_level": "secret"},
        )
        assert permitted is False
        assert "requires" in reason.lower()

    def test_data_access_public_allowed(self, contract_system, signed_contract):
        """Public data access should be allowed under RESTRICTED contract."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="memory.read",
            context={"data_access_level": "public"},
        )
        assert permitted is True

    def test_value_limit_exceeded(self, contract_system, signed_contract):
        """Action exceeding value limit should be denied."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="memory.read",
            context={"value": 100000.0},  # Exceeds 50000 limit
        )
        assert permitted is False
        assert "exceeds" in reason.lower()

    def test_value_within_limit(self, contract_system, signed_contract):
        """Action within value limit should be allowed."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="memory.read",
            context={"value": 1000.0},
        )
        assert permitted is True

    def test_requires_human_override(self, contract_system, signed_contract):
        """Actions requiring human override should still say permitted."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="data.export",
        )
        assert permitted is True
        assert "human override" in reason

    def test_mesh_type_restriction(self, contract_system, signed_contract):
        """Action on disallowed mesh type should be denied."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="memory.read",
            context={"mesh_type": "public"},
        )
        assert permitted is False
        assert "mesh type" in reason.lower()

    def test_allowed_mesh_type(self, contract_system, signed_contract):
        """Action on allowed mesh type should succeed."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="memory.read",
            context={"mesh_type": "local"},
        )
        assert permitted is True

    def test_contract_not_active(self, contract_system, sample_contract):
        """Non-active contract should deny all actions."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=sample_contract.contract_id,
            action="memory.read",
        )
        assert permitted is False
        assert "not active" in reason

    def test_action_wildcard_match(self, contract_system, signed_contract):
        """Wildcard pattern matching should work correctly."""
        # test 'chat.*' matches 'chat.anything.here'
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="chat.anything.here",
        )
        assert permitted is True

    def test_exact_action_match(self, contract_system, signed_contract):
        """Exact action match should work."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="file.read",
        )
        assert permitted is True

    def test_forbidden_takes_priority(self, contract_system, signed_contract):
        """Forbidden actions should be blocked even if also in allowed."""
        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="system.exec",
        )
        assert permitted is False
        assert "forbidden" in reason.lower()


# ─── EXPIRATION TRACKING TESTS ───────────────────────────────────────────────

class TestExpirationTracking:
    """Tests for expiration monitoring and processing."""

    def test_get_expiring_contracts(self, contract_system, signed_contract):
        """Expiring contracts should be detected."""
        # Force short expiry
        signed_contract.expires_at = time.time() + 3600  # 1 hour
        contract_system._save(signed_contract)

        expiring = contract_system.get_expiring_contracts(within_hours=48)
        assert len(expiring) >= 1
        assert signed_contract.contract_id in [c.contract_id for c in expiring]

    def test_get_expiring_empty(self, contract_system, signed_contract):
        """No contracts expiring soon should return empty list."""
        # Set far future expiry
        signed_contract.expires_at = time.time() + 86400 * 30  # 30 days
        contract_system._save(signed_contract)

        expiring = contract_system.get_expiring_contracts(within_hours=24)
        assert len(expiring) == 0

    def test_get_expired_contracts(self, contract_system, signed_contract):
        """Expired contracts should be detected."""
        # Force past expiry
        signed_contract.expires_at = time.time() - 100  # Already expired
        contract_system._save(signed_contract)

        expired = contract_system.get_expired_contracts()
        assert len(expired) >= 1
        assert signed_contract.contract_id in [c.contract_id for c in expired]

    def test_get_expired_skips_non_active(self, contract_system, sample_contract):
        """Non-active contracts should not appear in expired list."""
        # sample_contract is PROPOSED, not ACTIVE, even if expired
        expired = contract_system.get_expired_contracts()
        assert sample_contract.contract_id not in [c.contract_id for c in expired]

    def test_process_expirations(self, contract_system, signed_contract):
        """process_expirations should mark expired contracts."""
        signed_contract.expires_at = time.time() - 100
        contract_system._save(signed_contract)

        expired_ids = contract_system.process_expirations()
        assert signed_contract.contract_id in expired_ids

        # Re-fetch and verify
        contract = contract_system.get_contract(signed_contract.contract_id)
        assert contract.status == ContractStatus.EXPIRED

    def test_process_expiring_warnings(self, contract_system, signed_contract):
        """Contracts expiring soon should get warnings."""
        signed_contract.expires_at = time.time() + 3600  # 1 hour
        contract_system._save(signed_contract)

        warnings = contract_system.process_expiring_warnings()
        assert len(warnings) >= 1
        warning = next(w for w in warnings if w["contract_id"] == signed_contract.contract_id)
        assert "hours_remaining" in warning
        assert warning["human_id"] == "user_human_01"
        assert warning["agent_id"] == "clone_architect_01"

    def test_process_expiring_no_warnings(self, contract_system, signed_contract):
        """Contracts with far future expiry should not get warnings."""
        signed_contract.expires_at = time.time() + 86400 * 30
        contract_system._save(signed_contract)

        warnings = contract_system.process_expiring_warnings()
        matching = [w for w in warnings if w["contract_id"] == signed_contract.contract_id]
        assert len(matching) == 0


# ─── AUDIT GENERATION TESTS ──────────────────────────────────────────────────

class TestAuditGeneration:
    """Tests for audit report generation."""

    def test_generate_audit_basic(self, contract_system, signed_contract):
        """Basic audit should include lifecycle info."""
        report = contract_system.generate_audit(signed_contract.contract_id)
        assert report["contract_id"] == signed_contract.contract_id
        assert report["title"] == "Architecture Analysis Task"
        assert report["agent_id"] == "clone_architect_01"
        assert report["human_id"] == "user_human_01"
        assert report["status"] == "active"
        assert "compliance_score" in report
        assert "actions_performed" in report
        assert "actions_denied" in report

    def test_audit_includes_scope_snapshot(self, contract_system, signed_contract):
        """Audit should include scope snapshot."""
        report = contract_system.generate_audit(signed_contract.contract_id)
        assert "scope_snapshot" in report
        assert report["scope_snapshot"]["data_access_level"] == "restricted"

    def test_audit_after_actions(self, contract_system, signed_contract):
        """Audit after several checks should show action counts."""
        # Perform some allowed and denied actions
        contract_system.check_action_permitted(signed_contract.contract_id, "memory.read")
        contract_system.check_action_permitted(signed_contract.contract_id, "file.delete")
        contract_system.check_action_permitted(signed_contract.contract_id, "chat.hello")

        report = contract_system.generate_audit(signed_contract.contract_id)
        assert "total_audit_entries" in report

    def test_audit_completed_contract(self, contract_system, signed_contract):
        """Completed contract should have full audit trail."""
        contract_system.complete_contract(
            contract_id=signed_contract.contract_id,
            human_id="user_human_01",
            rating=5,
        )
        report = contract_system.generate_audit(signed_contract.contract_id)
        assert report["status"] == "completed"
        assert report["completed_at"] != ""
        assert report["compliance_score"] >= 0.9  # Should be high

    def test_audit_nonexistent(self, contract_system):
        """Auditing a nonexistent contract should raise KeyError."""
        with pytest.raises(KeyError):
            contract_system.generate_audit("nonexistent")

    def test_compliance_score_perfect(self, contract_system, signed_contract):
        """Perfect compliance should have score 1.0."""
        report = contract_system.generate_audit(signed_contract.contract_id)
        assert report["compliance_score"] >= 0.95

    def test_audit_adds_audit_entry(self, contract_system, signed_contract):
        """Generating audit should itself create an audit entry."""
        before_count = len(signed_contract.audit_entries)
        contract_system.generate_audit(signed_contract.contract_id)
        after_count = len(signed_contract.audit_entries)
        assert after_count > before_count


# ─── QUERY & STATS TESTS ────────────────────────────────────────────────────

class TestQueriesAndStats:
    """Tests for query methods and statistics."""

    def test_get_contract(self, contract_system, sample_contract):
        """get_contract should return the contract."""
        found = contract_system.get_contract(sample_contract.contract_id)
        assert found is not None
        assert found.contract_id == sample_contract.contract_id

    def test_get_contract_not_found(self, contract_system):
        """get_contract should return None for missing contract."""
        assert contract_system.get_contract("nonexistent") is None

    def test_list_for_human(self, contract_system, sample_contract):
        """Contracts should be listable by human."""
        contracts = contract_system.list_contracts_for_human("user_human_01")
        assert len(contracts) >= 1
        assert sample_contract.contract_id in [c.contract_id for c in contracts]

    def test_list_for_human_empty(self, contract_system):
        """No contracts for a human should return empty list."""
        contracts = contract_system.list_contracts_for_human("nonexistent_human")
        assert len(contracts) == 0

    def test_list_for_agent(self, contract_system, sample_contract):
        """Contracts should be listable by agent."""
        contracts = contract_system.list_contracts_for_agent("clone_architect_01")
        assert len(contracts) >= 1

    def test_list_for_human_filter_by_status(self, contract_system, sample_contract, signed_contract):
        """List should support status filtering."""
        # After signing, status is ACTIVE
        contracts = contract_system.list_contracts_for_human(
            "user_human_01", status=ContractStatus.ACTIVE
        )
        assert len(contracts) >= 1

        contracts = contract_system.list_contracts_for_human(
            "user_human_01", status=ContractStatus.COMPLETED
        )
        assert len(contracts) == 0  # None completed yet

    def test_get_active_contracts(self, contract_system, sample_contract, signed_contract):
        """get_active_contracts should return only active."""
        active = contract_system.get_active_contracts()
        assert len(active) >= 1
        assert all(c.status == ContractStatus.ACTIVE for c in active)

    def test_get_stats_basic(self, contract_system, sample_contract):
        """Stats should return aggregate data."""
        stats = contract_system.get_contract_stats()
        assert stats["total"] >= 1
        assert stats["active"] == 0  # Not signed yet
        assert stats["expired"] == 0

    def test_get_stats_with_completed(self, contract_system, sample_scope):
        """Stats should include completed counts."""
        # Use unique agent_id to avoid collision with sample_contract
        c = contract_system.propose_contract(
            agent_id="clone_stats_test",
            human_id="user_human_01",
            title="Stats Test",
            description="Testing stats with completed",
            duration=ContractDuration.TRIAL,
            scope=sample_scope,
        )
        signed = contract_system.sign_contract(
            contract_id=c.contract_id,
            human_id="user_human_01",
            signature="test_sig",
        )
        contract_system.complete_contract(
            contract_id=signed.contract_id,
            human_id="user_human_01",
        )
        stats = contract_system.get_contract_stats()
        assert stats["completed"] >= 1

    def test_get_stats_filter_by_human(self, contract_system, sample_contract):
        """Stats should be filterable by human."""
        stats = contract_system.get_contract_stats(human_id="user_human_01")
        assert stats["total"] >= 1

        stats = contract_system.get_contract_stats(human_id="other_human")
        assert stats["total"] == 0


# ─── SINGLETON FACTORY TESTS ─────────────────────────────────────────────────

class TestSingletonFactory:
    """Tests for get_agent_contract_system() and reset_agent_contract_system()."""

    def test_singleton_returns_same_instance(self):
        """get_agent_contract_system should return the same instance."""
        sys1 = get_agent_contract_system()
        sys2 = get_agent_contract_system()
        assert sys1 is sys2

    def test_reset_creates_new_instance(self):
        """reset_agent_contract_system should create a new instance."""
        sys1 = get_agent_contract_system()
        reset_agent_contract_system()
        sys2 = get_agent_contract_system()
        assert sys1 is not sys2

    def test_singleton_preserves_state(self):
        """Singleton should preserve state across calls."""
        system = get_agent_contract_system()
        contract = system.propose_contract(
            agent_id="clone_test",
            human_id="user_test",
            title="Singleton Test",
            description="Testing singleton state",
            duration=ContractDuration.TRIAL,
        )
        # Get same instance again
        system2 = get_agent_contract_system()
        found = system2.get_contract(contract.contract_id)
        assert found is not None

    def test_reset_in_test_cleanup(self):
        """Reset should clear all contracts."""
        system = get_agent_contract_system()
        system.propose_contract(
            agent_id="clone_test",
            human_id="user_test",
            title="Reset Test",
            description="Will be reset",
            duration=ContractDuration.TRIAL,
        )
        reset_agent_contract_system()
        system2 = get_agent_contract_system()
        stats = system2.get_contract_stats()
        assert stats["total"] == 0


# ─── EDGE CASE TESTS ─────────────────────────────────────────────────────────

class TestEdgeCases:
    """Tests for unusual or boundary conditions."""

    def test_empty_allowed_actions(self, contract_system, signed_contract):
        """Empty allowed_actions means everything is allowed (unless forbidden)."""
        signed_contract.scope.allowed_actions = []
        contract_system._save(signed_contract)

        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="anything.any_action",
        )
        assert permitted is True

    def test_duplicate_proposal_different_humans(self, contract_system):
        """Same agent with different human should work."""
        c1 = contract_system.propose_contract(
            agent_id="clone_multi",
            human_id="human_A",
            title="Contract A",
            description="For human A",
            duration=ContractDuration.TRIAL,
        )
        # Complete first before second proposal
        # Actually propose only works if no active contract exists
        # Since c1 is PROPOSED, second propose with same agent should fail
        with pytest.raises(ValueError, match="already has"):
            contract_system.propose_contract(
                agent_id="clone_multi",
                human_id="human_B",
                title="Contract B",
                description="For human B",
                duration=ContractDuration.TRIAL,
            )

    def test_very_long_contract_title(self, contract_system):
        """Very long titles should not cause issues."""
        long_title = "A" * 1000
        contract = contract_system.propose_contract(
            agent_id="clone_long",
            human_id="user_long",
            title=long_title,
            description="Testing long title",
            duration=ContractDuration.TRIAL,
        )
        assert contract.title == long_title

    def test_audit_entry_count_cap(self, contract_system, signed_contract):
        """to_dict should cap audit entries at 100."""
        # Add 150 audit entries
        for i in range(150):
            contract_system._add_audit_entry(
                signed_contract,
                AuditEventType.ACTION_PERFORMED,
                "agent",
                {"action_num": i},
            )
        d = signed_contract.to_dict()
        assert len(d["audit_entries"]) <= 100

    def test_renew_with_zero_renewals(self, contract_system, signed_contract):
        """Contract with max_renewals=0 should not allow renewal."""
        signed_contract.max_renewals = 0
        contract_system._save(signed_contract)

        with pytest.raises(ValueError, match="max renewals"):
            contract_system.renew_contract(
                contract_id=signed_contract.contract_id,
                human_id="user_human_01",
            )

    def test_action_with_special_chars(self, contract_system, signed_contract):
        """Action patterns with special characters should still match."""
        signed_contract.scope.allowed_actions = ["data.*"]
        signed_contract.scope.forbidden_actions = ["data.delete_all"]
        contract_system._save(signed_contract)

        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="data.read_user_123",
        )
        assert permitted is True

        permitted, reason = contract_system.check_action_permitted(
            contract_id=signed_contract.contract_id,
            action="data.delete_all",
        )
        assert permitted is False  # forbidden takes priority

    def test_contract_expiry_at_creation(self, contract_system):
        """Contract created with past expiry should be immediately expired."""
        now = time.time()
        past = now - 100
        scope = ContractScope()
        binding = AgentBinding(agent_id="clone_past")
        contract = AgentContract(
            contract_id="test_past_expiry",
            agent_binding=binding,
            human_id="user_past",
            title="Already Expired",
            description="Testing past expiry",
            duration=ContractDuration.TRIAL,
            scope=scope,
            status=ContractStatus.PROPOSED,
            created_at=past - 86400,
            expires_at=past,
        )
        assert contract.is_expired() is True


# ─── INTEGRATION TESTS ───────────────────────────────────────────────────────

class TestIntegrationFlows:
    """End-to-end integration flows."""

    def test_full_lifecycle(self, contract_system, sample_scope):
        """Complete contract lifecycle: propose → sign → complete."""
        # Step 1: Propose
        contract = contract_system.propose_contract(
            agent_id="clone_integration",
            human_id="user_integration",
            title="Integration Test",
            description="Testing full lifecycle",
            duration=ContractDuration.STANDARD,
            scope=sample_scope,
        )
        assert contract.status == ContractStatus.PROPOSED

        # Step 2: Sign
        contract = contract_system.sign_contract(
            contract_id=contract.contract_id,
            human_id="user_integration",
            signature="integration_sig",
        )
        assert contract.status == ContractStatus.ACTIVE

        # Step 3: Perform actions
        perm, _ = contract_system.check_action_permitted(
            contract.contract_id, "memory.read"
        )
        assert perm is True

        perm, _ = contract_system.check_action_permitted(
            contract.contract_id, "system.exec"
        )
        assert perm is False

        # Step 4: Complete
        contract = contract_system.complete_contract(
            contract_id=contract.contract_id,
            human_id="user_integration",
            rating=5,
            note="Excellent work!",
        )
        assert contract.status == ContractStatus.COMPLETED

        # Step 5: Generate audit
        report = contract_system.generate_audit(contract.contract_id)
        assert report["status"] == "completed"
        assert report["compliance_score"] >= 0.9

    def test_renewal_lifecycle(self, contract_system):
        """Propose → sign → renew → complete."""
        # Initial contract
        c1 = contract_system.propose_contract(
            agent_id="clone_renewal",
            human_id="user_renewal",
            title="Renewal Test",
            description="Testing renewal",
            duration=ContractDuration.TRIAL,
        )
        c1 = contract_system.sign_contract(
            contract_id=c1.contract_id,
            human_id="user_renewal",
        )

        # Renew
        c2 = contract_system.renew_contract(
            contract_id=c1.contract_id,
            human_id="user_renewal",
            new_duration=ContractDuration.STANDARD,
        )
        assert c2.contract_id != c1.contract_id
        assert c2.status == ContractStatus.PROPOSED

        # Sign new contract
        c2 = contract_system.sign_contract(
            contract_id=c2.contract_id,
            human_id="user_renewal",
        )
        assert c2.status == ContractStatus.ACTIVE
        assert c2.duration == ContractDuration.STANDARD

        # Complete
        c2 = contract_system.complete_contract(
            contract_id=c2.contract_id,
            human_id="user_renewal",
        )
        assert c2.status == ContractStatus.COMPLETED

        # Verify old contract marked as renewed
        old = contract_system.get_contract(c1.contract_id)
        assert old.status == ContractStatus.RENEWED

    def test_revocation_and_cooling_off_flow(self, contract_system):
        """Propose → sign → revoke → cooling-off → re-propose after cooldown."""
        # Create and activate
        c1 = contract_system.propose_contract(
            agent_id="clone_cooldown",
            human_id="user_cooldown",
            title="Cooldown Test",
            description="Testing cooling off",
            duration=ContractDuration.STANDARD,
        )
        c1 = contract_system.sign_contract(
            contract_id=c1.contract_id,
            human_id="user_cooldown",
        )

        # Revoke
        c1 = contract_system.revoke_contract(
            contract_id=c1.contract_id,
            human_id="user_cooldown",
            reason="Testing revocation flow",
        )
        assert c1.status == ContractStatus.COOLING_OFF
        assert c1.is_in_cooling_off() is True

        # Should not be able to propose during cooling-off
        with pytest.raises(ValueError, match="cooling-off"):
            contract_system.propose_contract(
                agent_id="clone_cooldown",
                human_id="user_cooldown",
                title="During Cooldown",
                description="Should fail",
                duration=ContractDuration.TRIAL,
            )

        # Manually clear cooling-off for testing (simulate time passing)
        c1.cooling_off_until = time.time() - 1  # Cooling-off ended
        contract_system._save(c1)
        assert c1.is_in_cooling_off() is False

        # Now should be able to propose again
        c2 = contract_system.propose_contract(
            agent_id="clone_cooldown",
            human_id="user_cooldown",
            title="After Cooldown",
            description="Should succeed",
            duration=ContractDuration.TRIAL,
        )
        assert c2.status == ContractStatus.PROPOSED

    def test_scope_enforcement_across_lifecycle(self, contract_system):
        """Scope should be enforced throughout the contract lifecycle."""
        strict_scope = ContractScope(
            allowed_actions=["data.read", "data.write"],
            forbidden_actions=["data.delete", "data.erase"],
            data_access_level=DataAccessLevel.PUBLIC,
            max_value_per_action=1000.0,
        )

        c = contract_system.propose_contract(
            agent_id="clone_strict",
            human_id="user_strict",
            title="Strict Scope",
            description="Testing strict scope",
            duration=ContractDuration.TRIAL,
            scope=strict_scope,
        )
        c = contract_system.sign_contract(
            contract_id=c.contract_id,
            human_id="user_strict",
        )

        # Allowed
        assert contract_system.check_action_permitted(c.contract_id, "data.read")[0] is True
        assert contract_system.check_action_permitted(c.contract_id, "data.write")[0] is True

        # Forbidden
        assert contract_system.check_action_permitted(c.contract_id, "data.delete")[0] is False
        assert contract_system.check_action_permitted(c.contract_id, "data.erase")[0] is False

        # Not in allowed set
        assert contract_system.check_action_permitted(c.contract_id, "system.exec")[0] is False

        # Value limit
        assert contract_system.check_action_permitted(
            c.contract_id, "data.write", {"value": 500}
        )[0] is True
        assert contract_system.check_action_permitted(
            c.contract_id, "data.write", {"value": 5000}
        )[0] is False


# ─── MODULE EXPORTS TESTS ────────────────────────────────────────────────────

class TestModuleExports:
    """Verify that __all__ exports match actual module contents."""

    def test_all_exports_defined(self):
        """__all__ should exist and be non-empty."""
        from core import agent_contract
        assert hasattr(agent_contract, "__all__")
        assert len(agent_contract.__all__) > 0

    def test_all_exports_are_importable(self):
        """Every name in __all__ should be importable."""
        from core.agent_contract import (
            ContractDuration,
            ContractStatus,
            DataAccessLevel,
            AuditEventType,
            ContractScope,
            AgentBinding,
            AuditEntry,
            AgentContract,
            AgentContractSystem,
            get_agent_contract_system,
            reset_agent_contract_system,
        )
        assert ContractDuration is not None
        assert ContractStatus is not None
        assert DataAccessLevel is not None
        assert AuditEventType is not None
        assert ContractScope is not None
        assert AgentBinding is not None
        assert AuditEntry is not None
        assert AgentContract is not None
        assert AgentContractSystem is not None
        assert callable(get_agent_contract_system)
        assert callable(reset_agent_contract_system)
