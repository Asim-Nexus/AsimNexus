#!/usr/bin/env python3
"""
Tests for [`core/economy/`](../../core/economy/) — Phase 3A: Economy Wiring.

Covers:
  - ContractExecutor: FSM validation, contract lifecycle, audit trail, persistence
  - NexusCredits (user-facing): credit creation, package purchase, rewards, transfers
  - FSM invalid transition blocking
  - JSONL persistence round-trip for both systems
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.economy.contract_executor import (
    ContractExecutor,
    ContractStatus,
    ContractDuration,
    ContractType,
    get_contract_executor,
    reset_contract_executor,
)
from economy.nexus_credits import (
    NexusCredits,
    NexusCredit,
    Transaction,
    TransactionType,
    TransactionStatus,
    PackageType,
    get_nexus_credits,
    reset_nexus_credits,
    ZeroKnowledgeProof,
)


# ─── Paths ──────────────────────────────────────────────────────────────────────

NEXUS_CREDITS_DB = Path(__file__).resolve().parent.parent.parent / "data" / "nexus_credits.jsonl"
CONTRACTS_DB = Path(__file__).resolve().parent.parent.parent / "data" / "contracts.jsonl"


# ─── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_db():
    """Clean JSONL databases and reset singletons before each test."""
    reset_contract_executor()
    reset_nexus_credits()
    for p in [NEXUS_CREDITS_DB, CONTRACTS_DB]:
        if p.exists():
            p.unlink()
    yield
    reset_contract_executor()
    reset_nexus_credits()


@pytest.fixture
async def executor() -> ContractExecutor:
    """Fresh ContractExecutor instance."""
    return get_contract_executor()


@pytest.fixture
async def credits() -> NexusCredits:
    """Fresh NexusCredits instance."""
    return get_nexus_credits()


# ══════════════════════════════════════════════════════════════════════════════
# Test: Contract Executor — FSM Validation
# ══════════════════════════════════════════════════════════════════════════════

class TestContractExecutorFSM:
    """Contract lifecycle with FSM validation."""

    async def test_full_lifecycle(self, executor: ContractExecutor, credits: NexusCredits):
        """PENDING -> ACCEPTED -> ACTIVE -> COMPLETED -> APPROVED -> PAID
        with credit transfer via NexusCredits."""
        # Seed credits for client so release_payment can transfer to worker
        await credits.create_credit("client_001", 5000)

        c = await executor.create_contract(
            "job_001", "client_001", "worker_001",
            ContractDuration.SHORT,
            {"title": "Test", "payment": 500.0, "currency": "NPR"},
        )
        assert c.status == "pending"

        ok = await executor.accept_contract(c.id, "worker_001")
        assert ok
        assert executor.contracts[c.id].status == "accepted"

        ok = await executor.start_contract(c.id, "worker_001")
        assert ok
        assert executor.contracts[c.id].status == "active"

        ok = await executor.complete_contract(c.id, "worker_001")
        assert ok
        assert executor.contracts[c.id].status == "completed"

        r = await executor.approve_contract(c.id, "client_001")
        assert r["success"] is True

        # Verify balances before payment
        assert credits.get_balance("client_001") == 5000
        assert credits.get_balance("worker_001") == 0

        r = await executor.release_payment(c.id, "client_001")
        assert r["success"] is True
        assert r["amount"] == 500.0
        assert r["transfer_tx_id"] is not None

        # Verify credit transfer happened
        assert credits.get_balance("client_001") == 4500  # 5000 - 500
        assert credits.get_balance("worker_001") == 500    # worker received payment

        # At least 6 audit entries for the full lifecycle
        assert len(executor.audit_trail) >= 6

    async def test_dispute_then_resolve(self, executor: ContractExecutor):
        """ACTIVE -> DISPUTED -> ACTIVE -> COMPLETED."""
        c = await executor.create_contract(
            "job_disp", "client_d", "worker_d",
            ContractDuration.SHORT,
            {"title": "Dispute Test", "payment": 300.0, "currency": "NPR"},
        )
        await executor.accept_contract(c.id, "worker_d")
        await executor.start_contract(c.id, "worker_d")

        # Raise dispute
        ok = await executor.dispute_contract(c.id, "worker_d", "Missing deliverables")
        assert ok is True
        assert executor.contracts[c.id].status == "disputed"

        # Resolve back to active (DISPUTED -> ACTIVE is valid per FSM)
        ok = await executor.start_contract(c.id, "worker_d")
        assert ok is True
        assert executor.contracts[c.id].status == "active"

        # Complete as normal
        ok = await executor.complete_contract(c.id, "worker_d")
        assert ok
        assert executor.contracts[c.id].status == "completed"

    async def test_cancel_contract(self, executor: ContractExecutor):
        """PENDING -> CANCELLED."""
        c = await executor.create_contract(
            "job_cancel", "client_c", "worker_c",
            ContractDuration.SHORT,
            {"title": "Cancel Test", "payment": 100.0, "currency": "NPR"},
        )
        ok = await executor.cancel_contract(c.id, "client_c", "No longer needed")
        assert ok is True
        assert executor.contracts[c.id].status == "cancelled"

    async def test_invalid_transition_blocked(self, executor: ContractExecutor):
        """Verify invalid state transitions are rejected."""
        c = await executor.create_contract(
            "job_inv", "client_i", "worker_i",
            ContractDuration.SHORT,
            {"title": "Invalid Test", "payment": 200.0, "currency": "NPR"},
        )
        # Cannot complete before accepting
        ok = await executor.complete_contract(c.id, "worker_i")
        assert ok is False

        await executor.accept_contract(c.id, "worker_i")
        await executor.start_contract(c.id, "worker_i")
        await executor.complete_contract(c.id, "worker_i")

        # Cannot pay before approving
        r = await executor.release_payment(c.id, "client_i")
        assert r["success"] is False

        # Cannot cancel after completion (only dispute/approve allowed)
        ok = await executor.cancel_contract(c.id, "client_i", "Too late")
        assert ok is False


# ══════════════════════════════════════════════════════════════════════════════
# Test: Contract Executor — Audit Trail
# ══════════════════════════════════════════════════════════════════════════════

class TestContractAudit:
    """Audit trail integrity."""

    async def test_audit_entries_created(self, executor: ContractExecutor):
        """Each transition creates an audit entry."""
        c = await executor.create_contract(
            "job_audit", "client_a", "worker_a",
            ContractDuration.SHORT,
            {"title": "Audit", "payment": 100.0, "currency": "NPR"},
        )
        assert len(executor.audit_trail) >= 1

        await executor.accept_contract(c.id, "worker_a")
        await executor.start_contract(c.id, "worker_a")
        assert len(executor.audit_trail) >= 3

    async def test_audit_has_entry_hash(self, executor: ContractExecutor):
        """Each audit entry has a non-empty entry_hash."""
        c = await executor.create_contract(
            "job_hash", "client_h", "worker_h",
            ContractDuration.SHORT,
            {"title": "Hash", "payment": 100.0, "currency": "NPR"},
        )
        entry = executor.audit_trail[0]
        assert entry.entry_hash != ""
        assert len(entry.entry_hash) == 16  # SHA256 hexdigest[:16]

    async def test_audit_filter_by_contract(self, executor: ContractExecutor):
        """get_audit_trail() filters by contract_id."""
        c1 = await executor.create_contract(
            "job_f1", "client_f", "worker_f",
            ContractDuration.SHORT,
            {"title": "Filter1", "payment": 50.0, "currency": "NPR"},
        )
        c2 = await executor.create_contract(
            "job_f2", "client_f", "worker_f",
            ContractDuration.SHORT,
            {"title": "Filter2", "payment": 50.0, "currency": "NPR"},
        )
        trail = executor.get_audit_trail(contract_id=c2.id)
        for entry in trail:
            assert entry["contract_id"] == c2.id


# ══════════════════════════════════════════════════════════════════════════════
# Test: Nexus Credits
# ══════════════════════════════════════════════════════════════════════════════

class TestNexusCredits:
    """User-facing Nexus Credits operations."""

    async def test_create_credit(self, credits: NexusCredits):
        """Creating a credit adds balance to the user."""
        credit = await credits.create_credit("user_001", 10000)
        assert credit.credit_id is not None
        assert credit.owner_id == "user_001"
        assert credit.amount == 10000
        assert credits.get_balance("user_001") == 10000

    async def test_purchase_package(self, credits: NexusCredits):
        """Purchasing a package deducts the correct amount."""
        await credits.create_credit("user_002", 1200)
        txn = await credits.purchase_package("user_002", PackageType.FIVE_DAYS)
        assert txn.transaction_id is not None
        assert txn.transaction_type == TransactionType.PACKAGE_PURCHASE.value
        assert credits.get_balance("user_002") == 700  # 1200 - 500

    async def test_reward_task_completion(self, credits: NexusCredits):
        """Rewarding a task adds credits to the agent.

        reward_task_completion sends from 'system'; seed system balance first.
        """
        await credits.create_credit("system", 999999)  # system can mint rewards
        txn = await credits.reward_task_completion("agent_001", "task_abc", 1000)
        assert txn.transaction_id is not None
        assert txn.status == TransactionStatus.COMPLETED.value
        assert credits.get_balance("agent_001") == 1000

    async def test_transfer_credits(self, credits: NexusCredits):
        """Transfer moves credits between users."""
        await credits.create_credit("alice", 5000)
        await credits.create_credit("bob", 1000)
        txn = await credits.transfer_credits("alice", "bob", 500)
        assert txn.transaction_id is not None
        assert credits.get_balance("alice") == 4500
        assert credits.get_balance("bob") == 1500

    async def test_transaction_history(self, credits: NexusCredits):
        """Transaction history returns relevant records."""
        await credits.create_credit("system", 999999)
        await credits.create_credit("user_hist", 3000)
        await credits.purchase_package("user_hist", PackageType.FIVE_DAYS)
        await credits.reward_task_completion("agent_hist", "task_xyz", 200)
        history = credits.get_transaction_history("user_hist")
        assert len(history) >= 1  # purchase_package transaction (create_credit does not produce a Transaction)

    async def test_economy_statistics(self, credits: NexusCredits):
        """Economy statistics return expected shape."""
        await credits.create_credit("system", 999999)
        await credits.create_credit("stat_user", 10000)
        await credits.reward_task_completion("stat_agent", "t1", 500)
        await credits.transfer_credits("stat_user", "stat_agent", 200)
        stats = credits.get_economy_statistics()
        assert "total_transactions" in stats
        assert stats["total_transactions"] >= 2  # reward + transfer (create_credit does not produce Transactions)


# ══════════════════════════════════════════════════════════════════════════════
# Test: Persistence
# ══════════════════════════════════════════════════════════════════════════════

class TestPersistence:
    """JSONL persistence round-trip."""

    async def test_contract_persistence_roundtrip(self, executor: ContractExecutor):
        """Contracts survive reset + reload."""
        c = await executor.create_contract(
            "job_persist", "client_p", "worker_p",
            ContractDuration.MEDIUM,
            {"title": "Persist Test", "payment": 1000.0, "currency": "NPR"},
        )
        await executor.accept_contract(c.id, "worker_p")
        await executor.start_contract(c.id, "worker_p")
        await executor.complete_contract(c.id, "worker_p")

        contract_id = c.id
        reset_contract_executor()
        ex2 = get_contract_executor()

        reloaded = ex2.get_contract(contract_id)
        assert reloaded is not None
        assert reloaded.status == "completed"
        assert reloaded.job_id == "job_persist"

    async def test_audit_persists_across_restart(self, executor: ContractExecutor):
        """Audit trail entries survive reset + reload."""
        c = await executor.create_contract(
            "job_audit_p", "client_ap", "worker_ap",
            ContractDuration.SHORT,
            {"title": "Audit Persist", "payment": 500.0, "currency": "NPR"},
        )
        await executor.accept_contract(c.id, "worker_ap")

        reset_contract_executor()
        ex2 = get_contract_executor()

        trail = ex2.get_audit_trail(contract_id=c.id)
        assert len(trail) >= 2  # create + accept

    async def test_nexus_credits_persistence(self, credits: NexusCredits):
        """Nexus credits state survives reset + reload."""
        await credits.create_credit("user_persist", 5000)
        await credits.purchase_package("user_persist", PackageType.FIVE_DAYS)

        reset_nexus_credits()
        nc2 = get_nexus_credits()

        assert nc2.get_balance("user_persist") == 4500  # 5000 - 500

    async def test_reset_does_not_delete_db(self, executor: ContractExecutor):
        """reset_contract_executor() preserves the JSONL file."""
        c = await executor.create_contract(
            "job_nodelete", "client_nd", "worker_nd",
            ContractDuration.SHORT,
            {"title": "No Delete", "payment": 100.0, "currency": "NPR"},
        )
        cid = c.id
        reset_contract_executor()

        assert CONTRACTS_DB.exists(), "JSONL file should still exist after reset"

        ex2 = get_contract_executor()
        reloaded = ex2.get_contract(cid)
        assert reloaded is not None
