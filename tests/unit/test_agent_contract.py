"""
Tests for core.agent_contract
=============================
"""

from __future__ import annotations

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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

class TestContractDuration:
    """Tests for ContractDuration enum."""

    def test_enum_values(self):
        """Test that ContractDuration has expected values."""
        assert ContractDuration.TRIAL == 5
        assert ContractDuration.STANDARD == 15
        assert ContractDuration.EXTENDED == 30

    def test_enum_members(self):
        """Test enum membership."""
        assert ContractDuration(5) == ContractDuration.TRIAL
        assert ContractDuration(15) == ContractDuration.STANDARD
        assert ContractDuration(30) == ContractDuration.EXTENDED

class TestContractStatus:
    """Tests for ContractStatus enum."""

    def test_enum_values(self):
        """Test that ContractStatus has expected values."""
        assert ContractStatus.PROPOSED is not None
        assert ContractStatus.ACTIVE is not None
        assert ContractStatus.PENDING_SIGNATURE is not None
        assert ContractStatus.EXPIRING_SOON is not None
        assert ContractStatus.EXPIRED is not None

class TestDataAccessLevel:
    """Tests for DataAccessLevel enum."""

    def test_enum_values(self):
        """Test that DataAccessLevel has expected values."""
        assert DataAccessLevel.PUBLIC is not None
        assert DataAccessLevel.RESTRICTED is not None
        assert DataAccessLevel.PRIVATE is not None
        assert DataAccessLevel.SECRET is not None

class TestAuditEventType:
    """Tests for AuditEventType enum."""

    def test_enum_values(self):
        """Test that AuditEventType has expected values."""
        assert AuditEventType.CONTRACT_CREATED is not None
        assert AuditEventType.CONTRACT_SIGNED is not None
        assert AuditEventType.CONTRACT_ACTIVATED is not None
        assert AuditEventType.ACTION_PERFORMED is not None
        assert AuditEventType.ACTION_DENIED is not None

class TestContractScope:
    """Tests for ContractScope dataclass."""

    def test_initialization(self):
        """Test that ContractScope initializes correctly."""
        scope = ContractScope(allowed_actions=["read", "write"], forbidden_actions=["delete"])
        assert scope is not None
        assert "read" in scope.allowed_actions
        assert "delete" in scope.forbidden_actions

class TestAgentBinding:
    """Tests for AgentBinding dataclass."""

    def test_initialization(self):
        """Test that AgentBinding initializes correctly."""
        binding = AgentBinding(agent_id="clone_1")
        assert binding is not None
        assert binding.agent_id == "clone_1"
        assert binding.agent_type == "clone"

class TestAuditEntry:
    """Tests for AuditEntry dataclass."""

    def test_initialization(self):
        """Test that AuditEntry initializes correctly."""
        entry = AuditEntry(
            entry_id="e1",
            contract_id="contract_1",
            event_type=AuditEventType.CONTRACT_CREATED,
            timestamp=time.time(),
            actor="test_actor",
            details={"note": "Test entry"}
        )
        assert entry is not None
        assert entry.event_type == AuditEventType.CONTRACT_CREATED
        assert entry.contract_id == "contract_1"
        assert entry.entry_hash != ""  # auto-generated

class TestAgentContract:
    """Tests for AgentContract dataclass."""

    def test_initialization(self):
        """Test that AgentContract initializes correctly."""
        binding = AgentBinding(agent_id="a1")
        scope = ContractScope(allowed_actions=["read"], forbidden_actions=[])
        contract = AgentContract(
            contract_id="c1",
            agent_binding=binding,
            human_id="human_1",
            title="Test Contract",
            description="A test contract",
            duration=ContractDuration.TRIAL,
            scope=scope,
            status=ContractStatus.PROPOSED
        )
        assert contract is not None
        assert contract.contract_id == "c1"
        assert contract.duration == ContractDuration.TRIAL
        assert contract.agent_binding.agent_id == "a1"

class TestAgentContractSystem:
    """Tests for AgentContractSystem."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test that AgentContractSystem initializes correctly."""
        system = AgentContractSystem()
        assert system is not None

@pytest.mark.asyncio
async def test_get_agent_contract_system():
    """Test the get_agent_contract_system function."""
    system = get_agent_contract_system()
    assert system is not None

@pytest.mark.asyncio
async def test_reset_agent_contract_system():
    """Test the reset_agent_contract_system function."""
    reset_agent_contract_system()
    system = get_agent_contract_system()
    assert system is not None
