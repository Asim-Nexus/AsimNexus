#!/usr/bin/env python3
"""
Tests for economy/tokens.py — TokenRegistry, TokenDefinition, TokenHolding, mint/burn.
"""

import pytest
import os
from pathlib import Path
from core.economy.tokens import (
    TokenRegistry, TokenDefinition, TokenHolding, TokenMintEvent,
    TokenStandard, TokenStatus,
    initialize_default_tokens, DEFAULT_TOKENS,
    get_token_registry, reset_token_registry,
    HOLDINGS_LEDGER_PATH,
)

@pytest.fixture(autouse=True)
def reset():
    """Reset singleton and clear data file before each test."""
    try:
        os.remove(TokenRegistry.LEDGER_PATH)
    except FileNotFoundError:
        pass
    try:
        os.remove(HOLDINGS_LEDGER_PATH)
    except FileNotFoundError:
        pass
    reset_token_registry()
    yield
    reset_token_registry()

@pytest.fixture
def registry():
    """Provide a fresh TokenRegistry."""
    return TokenRegistry()

@pytest.fixture
async def initialized_registry(registry):
    """Provide a TokenRegistry with default tokens initialized."""
    await initialize_default_tokens(registry)
    return registry

@pytest.mark.asyncio
async def test_register_token(registry):
    """Register a new token definition."""
    token = await registry.register_token(
        standard="nexus",
        name="Test Token",
        symbol="TST",
        total_supply=1_000_000,
    )
    assert token.token_id.startswith("tok_")
    assert token.standard == "nexus"
    assert token.symbol == "TST"
    assert token.total_supply == 1_000_000
    assert token.is_transferable is True
    assert token.is_soul_bound is False

@pytest.mark.asyncio
async def test_register_soul_bound_token(registry):
    """Register a soul-bound (non-transferable) token."""
    token = await registry.register_token(
        standard="svt",
        name="Soul-Bound Test",
        symbol="SBT",
        is_soul_bound=True,
    )
    assert token.is_soul_bound is True
    assert token.is_transferable is False

@pytest.mark.asyncio
async def test_get_token(registry):
    """Get token by ID."""
    token = await registry.register_token(standard="nexus", name="Get Test", symbol="GET")
    found = await registry.get_token(token.token_id)
    assert found is not None
    assert found.symbol == "GET"

@pytest.mark.asyncio
async def test_get_token_by_symbol(registry):
    """Find token by symbol."""
    await registry.register_token(standard="nexus", name="Symbol Test", symbol="SYM")
    found = await registry.get_token_by_symbol("SYM")
    assert found is not None
    assert found.symbol == "SYM"
    assert found.name == "Symbol Test"

    # Case insensitive
    found_lower = await registry.get_token_by_symbol("sym")
    assert found_lower is not None

@pytest.mark.asyncio
async def test_list_tokens(initialized_registry):
    """List all registered tokens."""
    tokens = await initialized_registry.list_tokens()
    assert len(tokens) >= 3  # NEXUS, SVT, HDT

@pytest.mark.asyncio
async def test_list_tokens_filtered(initialized_registry):
    """List tokens filtered by standard."""
    nexus_tokens = await initialized_registry.list_tokens(standard="nexus")
    assert len(nexus_tokens) == 1
    assert nexus_tokens[0].standard == "nexus"

@pytest.mark.asyncio
async def test_mint(registry):
    """Mint tokens to a recipient."""
    token = await registry.register_token(standard="nexus", name="Mint Test", symbol="MNT")
    success, event_id = await registry.mint(token.token_id, 1000.0, "user_001", reason="test mint")
    assert success is True
    assert event_id.startswith("mint_")

    # Verify token supply increased
    token_updated = await registry.get_token(token.token_id)
    assert token_updated.total_supply == 1000.0
    assert token_updated.circulating_supply == 1000.0

    # Verify holding created
    holding = await registry.get_holding("user_001", token.token_id)
    assert holding is not None
    assert holding.amount == 1000.0

@pytest.mark.asyncio
async def test_mint_invalid_amount(registry):
    """Mint with non-positive amount."""
    token = await registry.register_token(standard="nexus", name="Invalid Mint", symbol="INV")
    success, msg = await registry.mint(token.token_id, -100.0, "user_002")
    assert success is False
    assert "positive" in msg.lower()

@pytest.mark.asyncio
async def test_mint_nonexistent_token(registry):
    """Mint non-existent token."""
    success, msg = await registry.mint("tok_nonexistent", 100.0, "user_003")
    assert success is False
    assert "not found" in msg.lower()

@pytest.mark.asyncio
async def test_burn(registry):
    """Burn tokens from a holding."""
    token = await registry.register_token(standard="nexus", name="Burn Test", symbol="BRN")
    await registry.mint(token.token_id, 500.0, "user_004")

    success, event_id = await registry.burn("user_004", token.token_id, 200.0, reason="test burn")
    assert success is True
    assert event_id.startswith("burn_")

    holding = await registry.get_holding("user_004", token.token_id)
    assert holding.amount == 300.0

    token_updated = await registry.get_token(token.token_id)
    assert token_updated.total_supply == 300.0

@pytest.mark.asyncio
async def test_burn_insufficient(registry):
    """Burn more than available."""
    token = await registry.register_token(standard="nexus", name="Insuff Burn", symbol="INS")
    await registry.mint(token.token_id, 50.0, "user_005")

    success, msg = await registry.burn("user_005", token.token_id, 100.0)
    assert success is False
    assert "insufficient" in msg.lower()

@pytest.mark.asyncio
async def test_get_owner_holdings(registry):
    """Get all holdings for an owner."""
    tok1 = await registry.register_token(standard="nexus", name="Owner Test 1", symbol="OW1")
    tok2 = await registry.register_token(standard="svt", name="Owner Test 2", symbol="OW2", is_soul_bound=True)

    await registry.mint(tok1.token_id, 100.0, "multi_user")
    await registry.mint(tok2.token_id, 1.0, "multi_user")

    holdings = await registry.get_owner_holdings("multi_user")
    assert len(holdings) == 2

    # Check available balances
    bal1 = await registry.get_owner_balance("multi_user", tok1.token_id)
    bal2 = await registry.get_owner_balance("multi_user", tok2.token_id)
    assert bal1 == 100.0
    assert bal2 == 1.0

@pytest.mark.asyncio
async def test_lock_unlock_tokens(registry):
    """Lock and unlock tokens."""
    token = await registry.register_token(standard="nexus", name="Lock Test", symbol="LCK")
    await registry.mint(token.token_id, 500.0, "lock_user")

    # Lock 200 tokens
    success, msg = await registry.lock_tokens("lock_user", token.token_id, 200.0)
    assert success is True

    holding = await registry.get_holding("lock_user", token.token_id)
    assert holding.locked_amount == 200.0
    assert holding.available == 300.0

    # Try to lock more than available
    success, msg = await registry.lock_tokens("lock_user", token.token_id, 400.0)
    assert success is False
    assert "insufficient" in msg.lower()

    # Unlock 100 tokens
    success, msg = await registry.unlock_tokens("lock_user", token.token_id, 100.0)
    assert success is True

    holding = await registry.get_holding("lock_user", token.token_id)
    assert holding.locked_amount == 100.0

@pytest.mark.asyncio
async def test_get_stats(initialized_registry):
    """Get token registry statistics."""
    stats = await initialized_registry.get_stats()
    assert stats["total_tokens"] >= 3
    assert stats["total_holdings"] == 0
    assert stats["nexus_supply"] == 1_000_000_000  # Default NEXUS supply

@pytest.mark.asyncio
async def test_initialize_default_tokens(registry):
    """Initialize default tokens (NEXUS, SVT, HDT)."""
    result = await initialize_default_tokens(registry)
    assert result is registry

    nexus = await registry.get_token_by_symbol("NEXUS")
    assert nexus is not None
    assert nexus.total_supply == 1_000_000_000

    svt = await registry.get_token_by_symbol("SVT")
    assert svt is not None
    assert svt.is_soul_bound is True

    hdt = await registry.get_token_by_symbol("HDT")
    assert hdt is not None
    assert hdt.is_soul_bound is True

    # Idempotent: re-initializing should not duplicate
    await initialize_default_tokens(registry)
    tokens = await registry.list_tokens()
    nexus_tokens = [t for t in tokens if t.symbol == "NEXUS"]
    assert len(nexus_tokens) == 1

@pytest.mark.asyncio
async def test_multiple_mints_to_same_user(registry):
    """Mint multiple times to same user accumulates holdings."""
    token = await registry.register_token(standard="nexus", name="Multi Mint", symbol="MMT")
    await registry.mint(token.token_id, 100.0, "multi_user")
    await registry.mint(token.token_id, 200.0, "multi_user")
    await registry.mint(token.token_id, 300.0, "multi_user")

    holding = await registry.get_holding("multi_user", token.token_id)
    assert holding.amount == 600.0

@pytest.mark.asyncio
async def test_singleton():
    """Test singleton pattern."""
    r1 = get_token_registry()
    r2 = get_token_registry()
    assert r1 is r2

    reset_token_registry()
    r3 = get_token_registry()
    assert r3 is not r1

@pytest.mark.asyncio
async def test_persistence(tmp_path, registry):
    """Test JSONL persistence."""
    original_path = registry.LEDGER_PATH
    registry.LEDGER_PATH = str(tmp_path / "test_tokens.jsonl")

    # Create token and mint
    token = await registry.register_token(standard="nexus", name="Persist", symbol="PST")
    await registry.mint(token.token_id, 1000.0, "persist_user")

    # Create fresh registry loading from same path
    registry2 = TokenRegistry()
    registry2.LEDGER_PATH = registry.LEDGER_PATH
    await registry2._ensure_loaded()

    found = await registry2.get_token_by_symbol("PST")
    assert found is not None
    assert found.total_supply == 1000.0

    holding = await registry2.get_holding("persist_user", token.token_id)
    assert holding is not None
    assert holding.amount == 1000.0
