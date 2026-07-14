#!/usr/bin/env python3
"""
End-to-End critical flows for AsimNexus World OS.

Tests the complete lifecycle of key user journeys:
1. Economy Flow: Wallet → Deposit → Transfer → Withdraw
2. Token Flow: Register → Mint → Hold → Burn
3. Escrow Flow: Create → Fund → Dispute → Resolve
4. Marketplace Flow: List → Order → Pay → Deliver → Review
5. Staking Flow: Stake → Unlock → Unstake → Claim
6. ZKP Flow: Commit → Prove → Verify

These tests use the singleton factory pattern directly (no HTTP).
"""

import pytest
import asyncio
import os
from datetime import datetime, timedelta

# ── Import All Economy Modules ───────────────────────────────────────────────

from core.economy.wallet import (
    WalletEngine, get_wallet_engine, reset_wallet_engine,
)
from core.economy.tokens import (
    TokenRegistry, initialize_default_tokens, get_token_registry, reset_token_registry,
)
from core.economy.escrow import (
    EscrowEngine, get_escrow_engine, reset_escrow_engine,
)
from core.economy.marketplace import (
    MarketplaceEngine, get_marketplace_engine, reset_marketplace_engine,
)
from core.economy.staking import (
    StakingEngine, get_staking_engine, reset_staking_engine,
)
from core.security.real_zkp import (
    RealZKPManager, ZKProof, get_zkp_manager_real,
)

# ── Data file paths to clear between tests ───────────────────────────────────

_DATA_FILES = [
    WalletEngine.LEDGER_PATH,
    TokenRegistry.LEDGER_PATH,
    EscrowEngine.LEDGER_PATH,
    MarketplaceEngine.LEDGER_PATH,
    StakingEngine.LEDGER_PATH,
]

# ═════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def reset_all():
    """Reset all singletons and clear data files before each test."""
    for path in _DATA_FILES:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    reset_wallet_engine()
    reset_token_registry()
    reset_escrow_engine()
    reset_marketplace_engine()
    reset_staking_engine()
    yield
    for path in _DATA_FILES:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    reset_wallet_engine()
    reset_token_registry()
    reset_escrow_engine()
    reset_marketplace_engine()
    reset_staking_engine()

@pytest.fixture
def wallet():
    return get_wallet_engine()

@pytest.fixture
def tokens():
    return get_token_registry()

@pytest.fixture
async def initialized_tokens(tokens):
    await initialize_default_tokens(tokens)
    return tokens

@pytest.fixture
def escrow():
    return get_escrow_engine()

@pytest.fixture
def marketplace():
    return get_marketplace_engine()

@pytest.fixture
def staking():
    return get_staking_engine()

@pytest.fixture
def zkp():
    return get_zkp_manager_real()

# ═════════════════════════════════════════════════════════════════════════════
# E2E Flow 1: Economy Wallet — Full Lifecycle
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_e2e_wallet_full_lifecycle(wallet):
    """
    Complete wallet lifecycle:
    1. Create wallet → 2. Deposit NEXUS → 3. Transfer → 4. Withdraw → 5. Freeze → 6. Stats
    """
    # Step 1: Create wallets
    alice = await wallet.create_wallet(owner_id="alice_e2e", owner_type="user")
    bob = await wallet.create_wallet(owner_id="bob_e2e", owner_type="user")
    assert alice.status == "active"
    assert bob.status == "active"

    # Step 2: Deposit NEXUS into Alice's wallet
    success, tx_id = await wallet.deposit(alice.wallet_id, "nexus", 10000.0, reference="e2e_deposit")
    assert success is True

    alice_bal = await wallet.get_balance(alice.wallet_id, "nexus")
    assert alice_bal.available == 10000.0

    # Step 3: Transfer from Alice to Bob
    success, tx_id = await wallet.transfer(
        alice.wallet_id, bob.wallet_id, "nexus", 3000.0,
        description="E2E transfer test",
    )
    assert success is True

    alice_bal = await wallet.get_balance(alice.wallet_id, "nexus")
    bob_bal = await wallet.get_balance(bob.wallet_id, "nexus")
    assert alice_bal.available == 7000.0
    assert bob_bal.available == 3000.0

    # Step 4: Withdraw from Bob's wallet
    success, tx_id = await wallet.withdraw(
        bob.wallet_id, "nexus", 500.0,
        destination="external_address_xyz",
    )
    assert success is True

    bob_bal = await wallet.get_balance(bob.wallet_id, "nexus")
    assert bob_bal.available == 2500.0

    # Step 5: Freeze Alice's wallet
    frozen = await wallet.freeze_wallet(alice.wallet_id, reason="e2e_security_test")
    assert frozen is True

    alice_wallet = await wallet.get_wallet(alice.wallet_id)
    assert alice_wallet.status == "frozen"

    # Step 6: Verify frozen wallet rejects transactions
    success, msg = await wallet.transfer(alice.wallet_id, bob.wallet_id, "nexus", 100.0)
    assert success is False
    assert "frozen" in msg.lower()

    # Step 7: Get stats
    stats = await wallet.get_stats()
    assert stats["total_wallets"] >= 2
    assert stats["total_transactions"] >= 3  # deposit(1), transfer(1), withdraw(1)
    assert stats["frozen_wallets"] == 1

# ═════════════════════════════════════════════════════════════════════════════
# E2E Flow 2: Token Registry — Full Lifecycle
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_e2e_token_full_lifecycle(initialized_tokens):
    """
    Complete token lifecycle:
    1. Initialize defaults → 2. Mint tokens → 3. Check holdings → 4. Lock tokens → 5. Burn
    """
    tokens = initialized_tokens

    # Step 1: Verify default tokens
    nexus = await tokens.get_token_by_symbol("NEXUS")
    assert nexus is not None
    assert nexus.total_supply == 1_000_000_000

    svt = await tokens.get_token_by_symbol("SVT")
    assert svt is not None
    assert svt.is_soul_bound is True

    hdt = await tokens.get_token_by_symbol("HDT")
    assert hdt is not None

    # Step 2: Register a custom token
    custom = await tokens.register_token(
        standard="nexus", name="E2E Test Token", symbol="E2E", total_supply=100000,
    )
    assert custom.symbol == "E2E"

    # Step 3: Mint to user
    success, event_id = await tokens.mint(custom.token_id, 5000.0, "user_e2e", reason="e2e mint")
    assert success is True

    holding = await tokens.get_holding("user_e2e", custom.token_id)
    assert holding.amount == 5000.0

    # Step 4: Lock tokens
    success, msg = await tokens.lock_tokens("user_e2e", custom.token_id, 1000.0)
    assert success is True

    holding = await tokens.get_holding("user_e2e", custom.token_id)
    assert holding.locked_amount == 1000.0
    assert holding.available == 4000.0

    # Step 5: Unlock tokens
    success, msg = await tokens.unlock_tokens("user_e2e", custom.token_id, 500.0)
    assert success is True

    holding = await tokens.get_holding("user_e2e", custom.token_id)
    assert holding.locked_amount == 500.0

    # Step 6: Burn tokens
    success, event_id = await tokens.burn("user_e2e", custom.token_id, 2000.0, reason="e2e burn")
    assert success is True

    holding = await tokens.get_holding("user_e2e", custom.token_id)
    assert holding.amount == 3000.0

    # Step 7: Verify stats
    stats = await tokens.get_stats()
    assert stats["total_tokens"] >= 4  # NEXUS, SVT, HDT, E2E
    assert stats["total_holdings"] >= 1

# ═════════════════════════════════════════════════════════════════════════════
# E2E Flow 3: Escrow — Full Lifecycle with Dispute
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_e2e_escrow_dispute_lifecycle(escrow):
    """
    Complete escrow lifecycle with dispute resolution:
    1. Create escrow → 2. Fund → 3. Dispute → 4. Resolve → 5. Release
    """
    # Step 1: Create escrow
    e = await escrow.create_escrow(
        buyer_id="buyer_e2e", seller_id="seller_e2e",
        token_type="nexus", amount=5000.0, fee=50.0,
        reference="E2E Order #001",
        arbitrator_id="arb_e2e",
    )
    assert e.status == "pending"
    assert e.total_amount == 5050.0

    # Step 2: Fund the escrow
    success, _ = await escrow.fund_escrow(e.escrow_id)
    assert success is True

    funded = await escrow.get_escrow(e.escrow_id)
    assert funded.status == "funded"
    assert funded.funded_at is not None

    # Step 3: Raise a dispute
    success, dispute_id = await escrow.raise_dispute(
        escrow_id=e.escrow_id,
        raised_by="buyer_e2e",
        reason="item_not_received",
        description="Item not delivered within 7 days",
        evidence=[{"type": "message", "content": "Where is my order?"}],
    )
    assert success is True

    disputed = await escrow.get_escrow(e.escrow_id)
    assert disputed.status == "in_dispute"

    # Step 4: Resolve dispute in favor of buyer
    success, _ = await escrow.resolve_dispute(
        dispute_id=dispute_id,
        resolution="Seller failed to provide tracking",
        resolved_by="arb_e2e",
        release_to_seller=False,
    )
    assert success is True

    resolved = await escrow.get_escrow(e.escrow_id)
    assert resolved.status == "refunded"

    # Step 5: Verify dispute records
    disputes = await escrow.get_escrow_disputes(e.escrow_id)
    assert len(disputes) == 1
    assert disputes[0].status == "resolved"

    # Step 6: Stats
    stats = await escrow.get_stats()
    assert stats["total_escrows"] >= 1
    assert stats["resolved_disputes"] >= 1

# ═════════════════════════════════════════════════════════════════════════════
# E2E Flow 4: Marketplace — Full Commerce Lifecycle
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_e2e_marketplace_full_flow(marketplace):
    """
    Complete marketplace flow:
    1. Create listing → 2. Create order → 3. Pay → 4. Ship → 5. Deliver → 6. Complete → 7. Review
    """
    # Step 1: Create a listing
    lst = await marketplace.create_listing(
        seller_id="seller_mkt",
        title="E2E Compute Package",
        description="100 hours GPU compute time",
        category="compute",
        token_type="nexus",
        price=250.0,
        quantity=5,
        tags=["compute", "gpu", "e2e"],
    )
    assert lst.status == "active"
    assert lst.available == 5

    # Step 2: Search and find listing
    results = await marketplace.search_listings(category="compute")
    assert len(results) >= 1
    assert results[0].listing_id == lst.listing_id

    # Step 3: Create order
    success, order_id = await marketplace.create_order(
        listing_id=lst.listing_id,
        buyer_id="buyer_mkt",
        quantity=2,
        notes="Need this urgently",
    )
    assert success is True

    # Step 4: Confirm payment (simulates escrow deposit)
    success, _ = await marketplace.confirm_payment(order_id, escrow_id="esc_mkt_001")
    assert success is True

    # Step 5: Mark shipped
    success, _ = await marketplace.mark_shipped(order_id, "seller_mkt")
    assert success is True

    # Step 6: Buyer confirms delivery
    success, _ = await marketplace.confirm_delivery(order_id, "buyer_mkt")
    assert success is True

    # Step 7: Complete order
    success, _ = await marketplace.complete_order(order_id)
    assert success is True

    # Step 8: Submit review
    success, review_id = await marketplace.submit_review(
        order_id=order_id,
        reviewer_id="buyer_mkt",
        rating=5,
        description="Excellent service!",
    )
    assert success is True

    # Step 9: Verify reputation
    rep = await marketplace.get_user_reputation("seller_mkt")
    assert rep["total_reviews"] == 1
    assert rep["average_rating"] == 5.0

    # Step 10: Stats
    stats = await marketplace.get_stats()
    assert stats["completed_orders"] >= 1
    assert stats["total_revenue"] >= 500.0  # 2 * 250

# ═════════════════════════════════════════════════════════════════════════════
# E2E Flow 5: Staking — Full Rewards Lifecycle
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_e2e_staking_full_lifecycle(staking):
    """
    Complete staking lifecycle:
    1. Register validator → 2. Stake with validator → 3. Wait for unlock → 4. Distribute rewards
    → 5. Unstake → 6. Claim
    """
    # Step 1: Register a validator
    validator = await staking.register_validator(
        owner_id="val_owner_e2e",
        name="E2E Validator Node",
        self_stake=10000.0,
        commission_rate=0.05,
        description="E2E test validator",
    )
    assert validator.status == "active"

    # Step 2: Stake tokens with validator
    success, stake_id = await staking.stake(
        staker_id="staker_e2e",
        token_type="nexus",
        amount=5000.0,
        lock_days=7,
        validator_id=validator.validator_id,
    )
    assert success is True

    # Verify validator updated
    v = await staking.get_validator(validator.validator_id)
    assert v.total_staked == 15000.0  # 10000 self + 5000 delegated
    assert v.delegator_count == 1

    # Step 3: Force unlock (bypass time)
    stake = await staking.get_stake(stake_id)
    stake.locked_until = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    unlocked = await staking.unlock_stakes()
    assert stake_id in unlocked

    stake = await staking.get_stake(stake_id)
    assert stake.status == "active"

    # Step 4: Distribute rewards
    stake.created_at = (datetime.utcnow() - timedelta(days=30)).isoformat()
    count = await staking.distribute_all_rewards()
    assert count >= 1

    stake = await staking.get_stake(stake_id)
    assert stake.rewards_earned > 0

    # Step 5: Initiate unstake
    success, _ = await staking.unstake(stake_id, "staker_e2e")
    assert success is True

    stake = await staking.get_stake(stake_id)
    assert stake.status == "unstaking"

    # Step 6: Claim unstaked
    stake.unstaked_at = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    success, _ = await staking.claim_unstaked(stake_id, "staker_e2e")
    assert success is True

    stake = await staking.get_stake(stake_id)
    assert stake.status == "unstaked"

    # Step 7: Stats
    stats = await staking.get_stats()
    assert stats["total_stake_positions"] >= 1
    assert stats["total_rewards_distributed"] > 0

# ═════════════════════════════════════════════════════════════════════════════
# E2E Flow 6: ZKP — Privacy Proof Lifecycle
# ═════════════════════════════════════════════════════════════════════════════

def test_e2e_zkp_full_lifecycle(zkp):
    """
    Complete ZKP lifecycle:
    1. Create commitment → 2. Prove knowledge → 3. Verify → 4. Identity proof → 5. Batch verify
    """
    # Step 1: Create a Pedersen commitment
    private_data = "e2e_sensitive_data_2026"
    commitment, opening = zkp.create_commitment(private_data, "e2e_context")
    assert commitment is not None
    assert opening is not None

    # Step 2: Prove knowledge of the committed data
    statement = "E2E Flow: Knowledge proof at 2026"
    proof = zkp.prove_knowledge(private_data, commitment, statement)
    assert isinstance(proof, ZKProof)

    # Step 3: Verify the proof
    result = zkp.verify_proof(proof, statement)
    assert result.valid is True
    assert result.confidence > 0.9

    # Step 4: Create and verify identity proof
    identity = {
        "did": "did:asim:e2e_user_001",
        "public_key": "0xe2e_public_key_hash",
        "roles": ["e2e_tester", "developer"],
    }
    nonce = "e2e_test_nonce_001"
    identity_proof = zkp.create_identity_proof(identity, nonce)
    id_statement = identity_proof.public_inputs["statement"]
    id_result = zkp.verify_proof(identity_proof, id_statement)
    assert id_result.valid is True

    # Step 5: Batch verify multiple proofs
    proofs = [proof, identity_proof]
    batch_results = zkp.batch_verify(proofs)
    assert len(batch_results) == 2
    for r in batch_results.values():
        assert r.valid is True

    # Step 6: Get stats
    stats = zkp.get_stats()
    assert stats["total_commitments"] >= 2
    assert "verifier_key_hash" in stats

# ═════════════════════════════════════════════════════════════════════════════
# E2E Flow 7: Cross-System Integration
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_e2e_cross_system_integration(
    wallet, initialized_tokens, escrow, marketplace, staking, zkp,
):
    """
    Cross-system integration test:
    1. Token → Wallet deposit
    2. Marketplace listing → Order with escrow
    3. Escrow funded from wallet
    4. Escrow released → Wallet credited
    5. Wallet funds staked
    6. ZKP proves the whole flow
    """
    tokens = initialized_tokens

    # Step 1: Create wallets for buyer and seller
    buyer_wallet = await wallet.create_wallet(owner_id="buyer_integration", owner_type="user")
    seller_wallet = await wallet.create_wallet(owner_id="seller_integration", owner_type="user")

    # Step 2: Deposit into buyer wallet
    await wallet.deposit(buyer_wallet.wallet_id, "nexus", 10000.0)

    # Step 3: Mint tokens for the seller (SVT)
    svt = await tokens.get_token_by_symbol("SVT")
    await tokens.mint(svt.token_id, 1.0, "seller_integration", reason="E2E SVT mint")

    # Step 4: Create marketplace listing
    lst = await marketplace.create_listing(
        seller_id="seller_integration",
        title="Integration Test Service",
        description="E2E cross-system test",
        category="services",
        token_type="nexus",
        price=2000.0,
        quantity=1,
    )

    # Step 5: Create order
    success, order_id = await marketplace.create_order(
        listing_id=lst.listing_id,
        buyer_id="buyer_integration",
        quantity=1,
    )
    assert success is True

    # Step 6: Create escrow for this transaction
    e = await escrow.create_escrow(
        buyer_id="buyer_integration",
        seller_id="seller_integration",
        token_type="nexus",
        amount=2000.0,
        reference=f"order_{order_id}",
    )

    # Step 7: Fund escrow (simulate wallet → escrow)
    # In real system this would deduct from wallet
    success, _ = await escrow.fund_escrow(e.escrow_id)
    assert success is True

    # Step 8: Confirm payment in marketplace
    success, _ = await marketplace.confirm_payment(order_id, e.escrow_id)
    assert success is True

    # Step 9: Complete escrow cycle
    await escrow.release_to_seller(e.escrow_id)
    await marketplace.mark_shipped(order_id, "seller_integration")
    await marketplace.confirm_delivery(order_id, "buyer_integration")
    await marketplace.complete_order(order_id)

    # Step 10: Stake some tokens
    success, stake_id = await staking.stake(
        staker_id="buyer_integration",
        token_type="nexus",
        amount=3000.0,
        lock_days=30,
    )
    assert success is True

    # Step 11: Create ZKP proof of the entire transaction chain
    flow_data = {
        "buyer": "buyer_integration",
        "seller": "seller_integration",
        "listing": lst.listing_id,
        "order": order_id,
        "escrow": e.escrow_id,
        "amount": 2000.0,
        "token": "nexus",
        "timestamp": datetime.utcnow().isoformat(),
    }
    import json
    flow_str = json.dumps(flow_data, sort_keys=True)
    commitment, _ = zkp.create_commitment(flow_str, "e2e_integration")

    flow_statement = "E2E Integration: Complete transaction chain verified"
    proof = zkp.prove_knowledge(flow_str, commitment, flow_statement)
    result = zkp.verify_proof(proof, flow_statement)
    assert result.valid is True

    # Step 12: Verify final state
    wallet_stats = await wallet.get_stats()
    assert wallet_stats["total_wallets"] >= 2
    assert wallet_stats["total_transactions"] >= 1  # only deposit creates a wallet tx

    market_stats = await marketplace.get_stats()
    assert market_stats["completed_orders"] >= 1
    assert market_stats["total_revenue"] >= 2000.0

    staking_stats = await staking.get_stats()
    assert staking_stats["total_stake_positions"] >= 1

# ═════════════════════════════════════════════════════════════════════════════
# E2E Flow 8: Error Recovery
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_e2e_error_recovery_patterns(wallet, escrow, marketplace):
    """
    Test error handling and recovery:
    1. Invalid operations return proper errors
    2. Failed transactions don't corrupt state
    3. System recovers gracefully
    """
    # Step 1: Invalid transactions should fail gracefully
    success, msg = await wallet.deposit("nonexistent_wallet", "nexus", 100.0)
    assert success is False

    success, msg = await wallet.withdraw("nonexistent_wallet", "nexus", 50.0)
    assert success is False

    # Step 2: Create escrow with invalid params
    with pytest.raises(ValueError):
        await escrow.create_escrow("buyer", "seller", "nexus", -100.0)

    # Step 3: Marketplace edge cases
    lst = await marketplace.create_listing(
        seller_id="seller_err",
        title="Error Test",
        description="T",
        category="other",
        token_type="nexus",
        price=100.0,
        quantity=1,
    )

    # Try to order more than available
    success, msg = await marketplace.create_order(lst.listing_id, "buyer_err", quantity=5)
    assert success is False

    # Order exactly 1 should work
    success, order_id = await marketplace.create_order(lst.listing_id, "buyer_err", quantity=1)
    assert success is True

    # Try to order again (now sold out)
    success, msg = await marketplace.create_order(lst.listing_id, "buyer_err2", quantity=1)
    assert success is False

    # Cancel order, verify availability restored
    success, _ = await marketplace.cancel_order(order_id, "buyer_err")
    assert success is True

    # Now should be able to order again
    success, order_id2 = await marketplace.create_order(lst.listing_id, "buyer_err2", quantity=1)
    assert success is True

    # Step 4: Verify clean state after recovery
    lst_final = await marketplace.get_listing(lst.listing_id)
    assert lst_final.available == 0  # 1 available, 1 ordered

# ═════════════════════════════════════════════════════════════════════════════
# E2E Flow 9: Economy System Statistics
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_e2e_economy_statistics(wallet, initialized_tokens, escrow, marketplace, staking):
    """
    Verify all economy system statistics are coherent after operations.
    """
    # Create wallets
    await wallet.create_wallet(owner_id="stat_user1")
    await wallet.create_wallet(owner_id="stat_user2")
    await wallet.create_wallet(owner_id="stat_user3")

    wallet_stats = await wallet.get_stats()
    assert wallet_stats["total_wallets"] >= 3
    assert wallet_stats["active_wallets"] >= 3

    # Create escrows
    for i in range(3):
        e = await escrow.create_escrow(f"b_stat{i}", f"s_stat{i}", "nexus", 1000.0)
        await escrow.fund_escrow(e.escrow_id)

    escrow_stats = await escrow.get_stats()
    assert escrow_stats["total_escrows"] == 3

    # Create marketplace listings
    for i in range(2):
        await marketplace.create_listing(
            seller_id=f"s_mkt{i}", title=f"Item {i}", description="T",
            category="digital_goods", token_type="nexus", price=100.0,
        )

    market_stats = await marketplace.get_stats()
    assert market_stats["total_listings"] == 2
    assert market_stats["active_listings"] == 2

    # Create stakes
    for i in range(2):
        await staking.stake(f"staker_{i}", "nexus", 1000.0, lock_days=30)

    staking_stats = await staking.get_stats()
    assert staking_stats["total_stake_positions"] == 2
