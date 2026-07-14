#!/usr/bin/env python3
"""
Tests for economy/wallet.py — WalletEngine, Balance, WalletEntry, WalletTransaction.
"""

import pytest
import json
import os
from pathlib import Path
from core.economy.wallet import (
    WalletEngine, WalletEntry, Balance, WalletTransaction,
    TokenType, WalletStatus, get_wallet_engine, reset_wallet_engine,
)

@pytest.fixture(autouse=True)
def reset():
    """Reset singleton and clear data file before each test."""
    try:
        os.remove(WalletEngine.LEDGER_PATH)
    except FileNotFoundError:
        pass
    reset_wallet_engine()
    yield
    reset_wallet_engine()

@pytest.fixture
def engine():
    """Provide a fresh WalletEngine."""
    return WalletEngine()

@pytest.mark.asyncio
async def test_create_wallet(engine):
    """Create a wallet and verify its structure."""
    w = await engine.create_wallet(owner_id="user_001", owner_type="user")
    assert w.owner_id == "user_001"
    assert w.owner_type == "user"
    assert w.status == "active"
    assert w.wallet_id.startswith("wal_")
    assert "nexus" in w.balances
    assert "svt" in w.balances
    assert "hdt" in w.balances
    assert "credit" in w.balances
    assert w.balances["nexus"].available == 0.0
    assert w.balances["nexus"].total == 0.0

@pytest.mark.asyncio
async def test_get_wallet(engine):
    """Retrieve wallet by ID."""
    w = await engine.create_wallet(owner_id="user_002")
    found = await engine.get_wallet(w.wallet_id)
    assert found is not None
    assert found.wallet_id == w.wallet_id
    assert found.owner_id == "user_002"

@pytest.mark.asyncio
async def test_get_wallet_by_owner(engine):
    """Find wallet by owner ID."""
    w1 = await engine.create_wallet(owner_id="user_003")
    w2 = await engine.create_wallet(owner_id="user_004")

    found = await engine.get_wallet_by_owner("user_003")
    assert found is not None
    assert found.wallet_id == w1.wallet_id

    found = await engine.get_wallet_by_owner("user_004")
    assert found is not None
    assert found.wallet_id == w2.wallet_id

    found = await engine.get_wallet_by_owner("nonexistent")
    assert found is None

@pytest.mark.asyncio
async def test_deposit(engine):
    """Deposit tokens into wallet."""
    w = await engine.create_wallet(owner_id="user_005")
    success, tx_id = await engine.deposit(w.wallet_id, "nexus", 100.0)
    assert success is True
    assert tx_id.startswith("tx_")

    bal = await engine.get_balance(w.wallet_id, "nexus")
    assert bal is not None
    assert bal.available == 100.0
    assert bal.total == 100.0

@pytest.mark.asyncio
async def test_deposit_invalid_amount(engine):
    """Deposit with non-positive amount should fail."""
    w = await engine.create_wallet(owner_id="user_006")
    success, msg = await engine.deposit(w.wallet_id, "nexus", -50.0)
    assert success is False
    assert "positive" in msg.lower()

@pytest.mark.asyncio
async def test_deposit_nonexistent_wallet(engine):
    """Deposit into nonexistent wallet."""
    success, msg = await engine.deposit("wal_nonexistent", "nexus", 100.0)
    assert success is False
    assert "not found" in msg.lower()

@pytest.mark.asyncio
async def test_withdraw(engine):
    """Withdraw tokens from wallet."""
    w = await engine.create_wallet(owner_id="user_007")
    await engine.deposit(w.wallet_id, "nexus", 200.0)

    success, tx_id = await engine.withdraw(w.wallet_id, "nexus", 50.0)
    assert success is True
    assert tx_id.startswith("tx_")

    bal = await engine.get_balance(w.wallet_id, "nexus")
    assert bal.available == 150.0

@pytest.mark.asyncio
async def test_withdraw_insufficient_balance(engine):
    """Withdraw more than available should fail."""
    w = await engine.create_wallet(owner_id="user_008")
    await engine.deposit(w.wallet_id, "nexus", 10.0)

    success, msg = await engine.withdraw(w.wallet_id, "nexus", 100.0)
    assert success is False
    assert "insufficient" in msg.lower()

@pytest.mark.asyncio
async def test_transfer(engine):
    """Transfer tokens between wallets."""
    alice = await engine.create_wallet(owner_id="alice")
    bob = await engine.create_wallet(owner_id="bob")

    await engine.deposit(alice.wallet_id, "nexus", 500.0)

    success, tx_id = await engine.transfer(alice.wallet_id, bob.wallet_id, "nexus", 200.0)
    assert success is True
    assert tx_id.startswith("tx_")

    alice_bal = await engine.get_balance(alice.wallet_id, "nexus")
    bob_bal = await engine.get_balance(bob.wallet_id, "nexus")
    assert alice_bal.available == 300.0
    assert bob_bal.available == 200.0

@pytest.mark.asyncio
async def test_transfer_to_self(engine):
    """Transfer to same wallet should fail."""
    w = await engine.create_wallet(owner_id="user_009")
    await engine.deposit(w.wallet_id, "nexus", 100.0)

    success, msg = await engine.transfer(w.wallet_id, w.wallet_id, "nexus", 50.0)
    assert success is False
    assert "self" in msg.lower()

@pytest.mark.asyncio
async def test_transfer_insufficient(engine):
    """Transfer with insufficient balance should fail."""
    alice = await engine.create_wallet(owner_id="alice2")
    bob = await engine.create_wallet(owner_id="bob2")

    success, msg = await engine.transfer(alice.wallet_id, bob.wallet_id, "nexus", 9999.0)
    assert success is False
    assert "insufficient" in msg.lower()

@pytest.mark.asyncio
async def test_freeze_wallet(engine):
    """Freeze a wallet and verify transactions are blocked."""
    w = await engine.create_wallet(owner_id="user_010")
    await engine.deposit(w.wallet_id, "nexus", 100.0)

    frozen = await engine.freeze_wallet(w.wallet_id, reason="testing")
    assert frozen is True

    # Verify wallet is frozen
    wallet = await engine.get_wallet(w.wallet_id)
    assert wallet.status == "frozen"

    # Transactions should fail on frozen wallet
    success, msg = await engine.withdraw(w.wallet_id, "nexus", 10.0)
    assert success is False
    assert "frozen" in msg.lower()

@pytest.mark.asyncio
async def test_close_wallet(engine):
    """Close a wallet."""
    w = await engine.create_wallet(owner_id="user_011")
    closed = await engine.close_wallet(w.wallet_id)
    assert closed is True

    wallet = await engine.get_wallet(w.wallet_id)
    assert wallet.status == "closed"

@pytest.mark.asyncio
async def test_list_transactions(engine):
    """List transactions for a wallet."""
    w = await engine.create_wallet(owner_id="user_012")
    await engine.deposit(w.wallet_id, "nexus", 100.0)
    await engine.deposit(w.wallet_id, "nexus", 50.0)
    await engine.withdraw(w.wallet_id, "nexus", 30.0)

    txns = await engine.list_transactions(w.wallet_id)
    assert len(txns) == 3

    # Newest first
    assert txns[0].tx_type == "withdrawal"
    assert txns[1].tx_type == "deposit"
    assert txns[2].tx_type == "deposit"

@pytest.mark.asyncio
async def test_get_transaction(engine):
    """Get a specific transaction by ID."""
    w = await engine.create_wallet(owner_id="user_013")
    success, tx_id = await engine.deposit(w.wallet_id, "nexus", 75.0)

    tx = await engine.get_transaction(tx_id)
    assert tx is not None
    assert tx.tx_id == tx_id
    assert tx.token_type == "nexus"
    assert tx.amount == 75.0
    assert tx.status == "confirmed"

@pytest.mark.asyncio
async def test_get_total_supply(engine):
    """Calculate total supply across all wallets."""
    a = await engine.create_wallet(owner_id="user_a")
    b = await engine.create_wallet(owner_id="user_b")

    await engine.deposit(a.wallet_id, "nexus", 1000.0)
    await engine.deposit(b.wallet_id, "nexus", 500.0)
    await engine.deposit(b.wallet_id, "svt", 50.0)

    nexus_supply = await engine.get_total_supply("nexus")
    svt_supply = await engine.get_total_supply("svt")

    assert nexus_supply >= 1500.0
    assert svt_supply >= 50.0

@pytest.mark.asyncio
async def test_get_stats(engine):
    """Get wallet system statistics."""
    w1 = await engine.create_wallet(owner_id="user_s1")
    w2 = await engine.create_wallet(owner_id="user_s2")

    await engine.deposit(w1.wallet_id, "nexus", 300.0)
    await engine.deposit(w2.wallet_id, "nexus", 200.0)
    await engine.freeze_wallet(w2.wallet_id)

    stats = await engine.get_stats()
    assert stats["total_wallets"] >= 2
    assert stats["active_wallets"] >= 1
    assert stats["frozen_wallets"] >= 1
    assert stats["total_transactions"] >= 2
    assert stats["nexus_supply"] >= 500.0

@pytest.mark.asyncio
async def test_singleton():
    """Test singleton pattern."""
    e1 = get_wallet_engine()
    e2 = get_wallet_engine()
    assert e1 is e2

    reset_wallet_engine()
    e3 = get_wallet_engine()
    assert e3 is not e1

@pytest.mark.asyncio
async def test_unsupported_token(engine):
    """Deposit with unsupported token type."""
    w = await engine.create_wallet(owner_id="user_014")
    success, msg = await engine.deposit(w.wallet_id, "unknown_token", 100.0)
    assert success is False
    assert "unsupported" in msg.lower()

@pytest.mark.asyncio
async def test_deposit_multiple_tokens(engine):
    """Deposit multiple token types."""
    w = await engine.create_wallet(owner_id="user_015")
    await engine.deposit(w.wallet_id, "nexus", 100.0)
    await engine.deposit(w.wallet_id, "svt", 2.0)
    await engine.deposit(w.wallet_id, "hdt", 1.0)
    await engine.deposit(w.wallet_id, "credit", 500.0)

    for ttype in ["nexus", "svt", "hdt", "credit"]:
        bal = await engine.get_balance(w.wallet_id, ttype)
        assert bal is not None
        assert bal.available > 0

@pytest.mark.asyncio
async def test_persistence(tmp_path, engine):
    """Test JSONL persistence by loading from saved state."""
    # Use a temp path to avoid polluting real data
    original_path = engine.LEDGER_PATH
    engine.LEDGER_PATH = str(tmp_path / "test_wallet_ledger.jsonl")

    w = await engine.create_wallet(owner_id="persist_user")
    await engine.deposit(w.wallet_id, "nexus", 500.0)

    # Create new engine loading from same path
    engine2 = WalletEngine()
    engine2.LEDGER_PATH = engine.LEDGER_PATH
    await engine2._ensure_loaded()

    found = await engine2.get_wallet(w.wallet_id)
    assert found is not None
    assert found.owner_id == "persist_user"

    bal = await engine2.get_balance(w.wallet_id, "nexus")
    assert bal is not None
    assert bal.available == 500.0
