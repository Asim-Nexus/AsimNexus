#!/usr/bin/env python3
"""
Tests for economy/escrow.py — EscrowEngine, Dispute resolution, timeouts.
"""

import pytest
import os
from datetime import datetime, timedelta
from economy.escrow import (
    EscrowEngine, EscrowTransaction, Dispute, EscrowRelease,
    EscrowStatus, DisputeReason,
    get_escrow_engine, reset_escrow_engine,
)


@pytest.fixture(autouse=True)
def reset():
    """Reset singleton and clear data file before each test."""
    try:
        os.remove(EscrowEngine.LEDGER_PATH)
    except FileNotFoundError:
        pass
    reset_escrow_engine()
    yield
    reset_escrow_engine()


@pytest.fixture
def engine():
    return EscrowEngine()


@pytest.mark.asyncio
async def test_create_escrow(engine):
    """Create an escrow transaction."""
    escrow = await engine.create_escrow(
        buyer_id="buyer_001",
        seller_id="seller_001",
        token_type="nexus",
        amount=1000.0,
        fee=10.0,
        reference="Order #1234",
    )
    assert escrow.escrow_id.startswith("esc_")
    assert escrow.buyer_id == "buyer_001"
    assert escrow.seller_id == "seller_001"
    assert escrow.amount == 1000.0
    assert escrow.fee == 10.0
    assert escrow.total_amount == 1010.0
    assert escrow.status == "pending"
    assert escrow.expires_at is not None


@pytest.mark.asyncio
async def test_create_escrow_invalid_amount(engine):
    """Create escrow with invalid amount."""
    with pytest.raises(ValueError, match="positive"):
        await engine.create_escrow("buyer", "seller", "nexus", -100.0)

    with pytest.raises(ValueError, match="positive"):
        await engine.create_escrow("buyer", "seller", "nexus", 0)


@pytest.mark.asyncio
async def test_create_escrow_negative_fee(engine):
    """Create escrow with negative fee."""
    with pytest.raises(ValueError, match="non-negative"):
        await engine.create_escrow("buyer", "seller", "nexus", 100.0, fee=-5.0)


@pytest.mark.asyncio
async def test_fund_escrow(engine):
    """Fund an escrow."""
    escrow = await engine.create_escrow("buyer_fund", "seller_fund", "nexus", 500.0)
    success, msg = await engine.fund_escrow(escrow.escrow_id)
    assert success is True

    funded = await engine.get_escrow(escrow.escrow_id)
    assert funded.status == "funded"
    assert funded.funded_at is not None


@pytest.mark.asyncio
async def test_fund_nonexistent_escrow(engine):
    """Fund non-existent escrow."""
    success, msg = await engine.fund_escrow("esc_nonexistent")
    assert success is False
    assert "not found" in msg.lower()


@pytest.mark.asyncio
async def test_fund_already_released(engine):
    """Fund already released escrow."""
    escrow = await engine.create_escrow("b1", "s1", "nexus", 100.0)
    await engine.fund_escrow(escrow.escrow_id)
    await engine.release_to_seller(escrow.escrow_id)

    success, msg = await engine.fund_escrow(escrow.escrow_id)
    assert success is False
    assert "not pending" in msg.lower()


@pytest.mark.asyncio
async def test_release_to_seller(engine):
    """Release funds to seller."""
    escrow = await engine.create_escrow("b_rel", "s_rel", "nexus", 1000.0)
    await engine.fund_escrow(escrow.escrow_id)

    success, release_id = await engine.release_to_seller(escrow.escrow_id, released_by="system")
    assert success is True
    assert release_id.startswith("rel_")

    released = await engine.get_escrow(escrow.escrow_id)
    assert released.status == "released"
    assert released.released_at is not None

    # Verify release record
    release_found = engine._releases.get(release_id)
    assert release_found is not None
    assert release_found.recipient_id == "s_rel"


@pytest.mark.asyncio
async def test_refund_to_buyer(engine):
    """Refund funds to buyer."""
    escrow = await engine.create_escrow("b_ref", "s_ref", "nexus", 500.0)
    await engine.fund_escrow(escrow.escrow_id)

    success, release_id = await engine.refund_to_buyer(escrow.escrow_id, refunded_by="arbitrator")
    assert success is True

    refunded = await engine.get_escrow(escrow.escrow_id)
    assert refunded.status == "refunded"


@pytest.mark.asyncio
async def test_refund_partial_amount(engine):
    """Partial refund to buyer."""
    escrow = await engine.create_escrow("b_part", "s_part", "nexus", 1000.0)
    await engine.fund_escrow(escrow.escrow_id)

    success, _ = await engine.refund_to_buyer(
        escrow.escrow_id, partial_amount=750.0, reason="partial refund"
    )
    assert success is True

    refunded = await engine.get_escrow(escrow.escrow_id)
    assert refunded.status == "refunded"


@pytest.mark.asyncio
async def test_raise_dispute(engine):
    """Raise a dispute on an escrow."""
    escrow = await engine.create_escrow("b_disp", "s_disp", "nexus", 300.0)
    await engine.fund_escrow(escrow.escrow_id)

    success, dispute_id = await engine.raise_dispute(
        escrow_id=escrow.escrow_id,
        raised_by="b_disp",
        reason="item_not_received",
        description="Item never arrived",
        evidence=[{"type": "message", "content": "Where is my item?"}],
    )
    assert success is True
    assert dispute_id.startswith("disp_")

    disputed = await engine.get_escrow(escrow.escrow_id)
    assert disputed.status == "in_dispute"

    dispute = await engine.get_dispute(dispute_id)
    assert dispute is not None
    assert dispute.reason == "item_not_received"
    assert dispute.status == "open"
    assert len(dispute.evidence) == 1


@pytest.mark.asyncio
async def test_raise_dispute_unauthorized(engine):
    """Only buyer, seller, or arbitrator can raise disputes."""
    escrow = await engine.create_escrow("b_auth", "s_auth", "nexus", 100.0)
    await engine.fund_escrow(escrow.escrow_id)

    success, msg = await engine.raise_dispute(escrow.escrow_id, "stranger", "other")
    assert success is False


@pytest.mark.asyncio
async def test_resolve_dispute_release(engine):
    """Resolve dispute by releasing to seller."""
    escrow = await engine.create_escrow("b_res", "s_res", "nexus", 500.0)
    await engine.fund_escrow(escrow.escrow_id)

    success, dispute_id = await engine.raise_dispute(escrow.escrow_id, "b_res", "item_defective")
    assert success is True

    success, _ = await engine.resolve_dispute(
        dispute_id=dispute_id,
        resolution="Seller provided valid tracking",
        resolved_by="arbitrator_001",
        release_to_seller=True,
    )
    assert success is True

    resolved = await engine.get_escrow(escrow.escrow_id)
    assert resolved.status == "released"


@pytest.mark.asyncio
async def test_resolve_dispute_refund(engine):
    """Resolve dispute by refunding buyer."""
    escrow = await engine.create_escrow("b_ref2", "s_ref2", "nexus", 500.0)
    await engine.fund_escrow(escrow.escrow_id)

    success, dispute_id = await engine.raise_dispute(escrow.escrow_id, "b_ref2", "misrepresentation")
    assert success is True

    success, _ = await engine.resolve_dispute(
        dispute_id=dispute_id,
        resolution="Item not as described",
        resolved_by="arbitrator_002",
        release_to_seller=False,
    )
    assert success is True

    resolved = await engine.get_escrow(escrow.escrow_id)
    assert resolved.status == "refunded"


@pytest.mark.asyncio
async def test_double_dispute_resolution(engine):
    """Resolving already resolved dispute should fail."""
    escrow = await engine.create_escrow("b_dbl", "s_dbl", "nexus", 100.0)
    await engine.fund_escrow(escrow.escrow_id)

    success, dispute_id = await engine.raise_dispute(escrow.escrow_id, "b_dbl", "other")
    assert success is True

    await engine.resolve_dispute(dispute_id, "resolved", "arb", release_to_seller=True)

    success, msg = await engine.resolve_dispute(dispute_id, "again", "arb", release_to_seller=True)
    assert success is False
    assert "already resolved" in msg.lower()


@pytest.mark.asyncio
async def test_get_escrows_for_user(engine):
    """Get escrows where user is buyer or seller."""
    await engine.create_escrow("buyer_u", "seller_u", "nexus", 100.0)
    await engine.create_escrow("buyer_u", "another_s", "nexus", 200.0)
    await engine.create_escrow("other_b", "seller_u", "nexus", 300.0)

    # As buyer
    buyer_escrows = await engine.get_escrows_for_user("buyer_u")
    assert len(buyer_escrows) == 2

    # As seller
    seller_escrows = await engine.get_escrows_for_user("seller_u")
    assert len(seller_escrows) == 2

    # Filtered by status
    pending = await engine.get_escrows_for_user("buyer_u", status="pending")
    assert len(pending) == 2

    funded = await engine.get_escrows_for_user("buyer_u", status="funded")
    assert len(funded) == 0


@pytest.mark.asyncio
async def test_get_escrow_disputes(engine):
    """Get all disputes for an escrow."""
    escrow1 = await engine.create_escrow("b_ed1", "s_ed1", "nexus", 100.0)
    escrow2 = await engine.create_escrow("b_ed2", "s_ed2", "nexus", 200.0)

    await engine.fund_escrow(escrow1.escrow_id)
    await engine.fund_escrow(escrow2.escrow_id)

    await engine.raise_dispute(escrow1.escrow_id, "b_ed1", "other")
    await engine.raise_dispute(escrow1.escrow_id, "b_ed1", "other")  # Second dispute

    disputes1 = await engine.get_escrow_disputes(escrow1.escrow_id)
    assert len(disputes1) == 2

    disputes2 = await engine.get_escrow_disputes(escrow2.escrow_id)
    assert len(disputes2) == 0


@pytest.mark.asyncio
async def test_check_expired(engine):
    """Expire escrows past their timeout."""
    escrow = await engine.create_escrow(
        "b_exp", "s_exp", "nexus", 100.0,
        timeout_hours=0,  # Immediate expiry
    )
    # Override expires_at to past
    escrow.expires_at = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    expired = await engine.check_expired()
    assert escrow.escrow_id in expired

    expired_escrow = await engine.get_escrow(escrow.escrow_id)
    assert expired_escrow.status == "expired"


@pytest.mark.asyncio
async def test_get_stats(engine):
    """Get escrow statistics."""
    escrow = await engine.create_escrow("b_stat", "s_stat", "nexus", 500.0)
    await engine.fund_escrow(escrow.escrow_id)

    stats = await engine.get_stats()
    assert stats["total_escrows"] >= 1
    assert stats["open_disputes"] == 0


@pytest.mark.asyncio
async def test_singleton():
    """Test singleton pattern."""
    e1 = get_escrow_engine()
    e2 = get_escrow_engine()
    assert e1 is e2

    reset_escrow_engine()
    e3 = get_escrow_engine()
    assert e3 is not e1


@pytest.mark.asyncio
async def test_persistence(tmp_path, engine):
    """Test JSONL persistence."""
    original_path = engine.LEDGER_PATH
    engine.LEDGER_PATH = str(tmp_path / "test_escrow.jsonl")

    escrow = await engine.create_escrow("b_persist", "s_persist", "nexus", 1000.0)
    await engine.fund_escrow(escrow.escrow_id)

    engine2 = EscrowEngine()
    engine2.LEDGER_PATH = engine.LEDGER_PATH
    await engine2._ensure_loaded()

    found = await engine2.get_escrow(escrow.escrow_id)
    assert found is not None
    assert found.buyer_id == "b_persist"
    assert found.status == "funded"
