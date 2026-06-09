#!/usr/bin/env python3
"""
Tests for economy/marketplace.py — MarketplaceEngine, Listings, Orders, Reviews.
"""

import pytest
import os
from economy.marketplace import (
    MarketplaceEngine, Listing, MarketplaceOrder, Review,
    ListingStatus, OrderStatus, ListingCategory,
    get_marketplace_engine, reset_marketplace_engine,
)


@pytest.fixture(autouse=True)
def reset():
    """Reset singleton and clear data file before each test."""
    try:
        os.remove(MarketplaceEngine.LEDGER_PATH)
    except FileNotFoundError:
        pass
    reset_marketplace_engine()
    yield
    reset_marketplace_engine()


@pytest.fixture
def engine():
    return MarketplaceEngine()


@pytest.mark.asyncio
async def test_create_listing(engine):
    """Create a marketplace listing."""
    lst = await engine.create_listing(
        seller_id="seller_001",
        title="Nexus Compute Pack",
        description="1000 hours of compute time",
        category="compute",
        token_type="nexus",
        price=500.0,
        quantity=10,
        tags=["compute", "gpu"],
    )
    assert lst.listing_id.startswith("lst_")
    assert lst.seller_id == "seller_001"
    assert lst.title == "Nexus Compute Pack"
    assert lst.price == 500.0
    assert lst.available == 10
    assert lst.status == "active"
    assert lst.terms_hash is not None


@pytest.mark.asyncio
async def test_get_listing(engine):
    """Get listing by ID."""
    lst = await engine.create_listing(
        seller_id="seller_002", title="Test Item", description="Desc",
        category="digital_goods", token_type="nexus", price=100.0,
    )
    found = await engine.get_listing(lst.listing_id)
    assert found is not None
    assert found.title == "Test Item"
    assert found.price == 100.0


@pytest.mark.asyncio
async def test_search_listings(engine):
    """Search listings with filters."""
    await engine.create_listing(
        seller_id="s1", title="GPU Time", description="GPU compute",
        category="compute", token_type="nexus", price=300.0, tags=["gpu"],
    )
    await engine.create_listing(
        seller_id="s2", title="Storage Space", description="Cloud storage",
        category="storage", token_type="nexus", price=50.0, tags=["storage"],
    )
    await engine.create_listing(
        seller_id="s1", title="API Access", description="API keys",
        category="api_access", token_type="svt", price=200.0,
    )

    # Filter by category
    compute = await engine.search_listings(category="compute")
    assert len(compute) == 1
    assert compute[0].title == "GPU Time"

    # Filter by seller
    seller_listings = await engine.search_listings(seller_id="s1")
    assert len(seller_listings) == 2

    # Filter by token type
    svt_listings = await engine.search_listings(token_type="svt")
    assert len(svt_listings) == 1


@pytest.mark.asyncio
async def test_cancel_listing(engine):
    """Cancel a listing."""
    lst = await engine.create_listing(
        seller_id="seller_cancel", title="Cancel Test", description="T",
        category="other", token_type="nexus", price=10.0,
    )
    success, msg = await engine.cancel_listing(lst.listing_id, "seller_cancel")
    assert success is True

    cancelled = await engine.get_listing(lst.listing_id)
    assert cancelled.status == "cancelled"


@pytest.mark.asyncio
async def test_cancel_listing_wrong_seller(engine):
    """Only the seller can cancel their listing."""
    lst = await engine.create_listing(
        seller_id="seller_ok", title="Wrong Cancel", description="T",
        category="other", token_type="nexus", price=10.0,
    )
    success, msg = await engine.cancel_listing(lst.listing_id, "impostor")
    assert success is False


@pytest.mark.asyncio
async def test_create_order(engine):
    """Create an order for a listing."""
    lst = await engine.create_listing(
        seller_id="seller_order", title="Order Test", description="T",
        category="digital_goods", token_type="nexus", price=100.0, quantity=5,
    )
    success, order_id = await engine.create_order(
        listing_id=lst.listing_id,
        buyer_id="buyer_001",
        quantity=2,
        notes="Rush delivery",
    )
    assert success is True
    assert order_id.startswith("ord_")

    order = await engine.get_order(order_id)
    assert order is not None
    assert order.buyer_id == "buyer_001"
    assert order.seller_id == "seller_order"
    assert order.total_amount == 200.0  # 2 * 100
    assert order.status == "pending_payment"

    # Verify availability decreased
    listing = await engine.get_listing(lst.listing_id)
    assert listing.available == 3  # 5 - 2


@pytest.mark.asyncio
async def test_create_order_insufficient_quantity(engine):
    """Order more than available should fail."""
    lst = await engine.create_listing(
        seller_id="s_qty", title="Qty Test", description="T",
        category="other", token_type="nexus", price=10.0, quantity=1,
    )
    success, msg = await engine.create_order(lst.listing_id, "buyer_qty", quantity=5)
    assert success is False
    assert "insufficient" in msg.lower()


@pytest.mark.asyncio
async def test_confirm_payment(engine):
    """Confirm payment for an order."""
    lst = await engine.create_listing(
        seller_id="s_pay", title="Pay Test", description="T",
        category="other", token_type="nexus", price=50.0,
    )
    success, order_id = await engine.create_order(lst.listing_id, "buyer_pay")
    assert success is True

    success, msg = await engine.confirm_payment(order_id, escrow_id="esc_test_001")
    assert success is True

    order = await engine.get_order(order_id)
    assert order.status == "paid"
    assert order.escrow_id == "esc_test_001"


@pytest.mark.asyncio
async def test_order_lifecycle(engine):
    """Full order lifecycle: created → paid → shipped → delivered → completed."""
    lst = await engine.create_listing(
        seller_id="s_cycle", title="Lifecycle Test", description="T",
        category="digital_goods", token_type="nexus", price=75.0,
    )
    success, order_id = await engine.create_order(lst.listing_id, "buyer_cycle")
    assert success is True

    # Pay
    success, _ = await engine.confirm_payment(order_id, "esc_cycle")
    assert success is True

    # Ship
    success, _ = await engine.mark_shipped(order_id, "s_cycle")
    assert success is True

    # Deliver
    success, _ = await engine.confirm_delivery(order_id, "buyer_cycle")
    assert success is True

    # Complete
    success, _ = await engine.complete_order(order_id)
    assert success is True

    order = await engine.get_order(order_id)
    assert order.status == "completed"
    assert order.completed_at is not None


@pytest.mark.asyncio
async def test_cancel_order_before_payment(engine):
    """Cancel an order before payment."""
    lst = await engine.create_listing(
        seller_id="s_cancel", title="Cancel Order Test", description="T",
        category="other", token_type="nexus", price=25.0, quantity=3,
    )
    success, order_id = await engine.create_order(lst.listing_id, "buyer_cancel", quantity=1)
    assert success is True

    success, _ = await engine.cancel_order(order_id, "buyer_cancel")
    assert success is True

    order = await engine.get_order(order_id)
    assert order.status == "cancelled"

    # Verify availability restored
    listing = await engine.get_listing(lst.listing_id)
    assert listing.available == 3


@pytest.mark.asyncio
async def test_submit_review(engine):
    """Submit a review for a completed order."""
    lst = await engine.create_listing(
        seller_id="s_rev", title="Review Test", description="T",
        category="digital_goods", token_type="nexus", price=50.0,
    )
    success, order_id = await engine.create_order(lst.listing_id, "buyer_rev")
    await engine.confirm_payment(order_id, "esc_rev")
    await engine.mark_shipped(order_id, "s_rev")
    await engine.confirm_delivery(order_id, "buyer_rev")
    await engine.complete_order(order_id)

    # Submit review as buyer
    success, review_id = await engine.submit_review(
        order_id=order_id,
        reviewer_id="buyer_rev",
        rating=5,
        description="Excellent service!",
    )
    assert success is True
    assert review_id.startswith("rev_")

    # Check reputation
    rep = await engine.get_user_reputation("s_rev")
    assert rep["total_reviews"] == 1
    assert rep["average_rating"] == 5.0


@pytest.mark.asyncio
async def test_submit_review_invalid_rating(engine):
    """Rating outside 1-5 should fail."""
    lst = await engine.create_listing(
        seller_id="s_inv", title="Invalid Review", description="T",
        category="other", token_type="nexus", price=10.0,
    )
    success, order_id = await engine.create_order(lst.listing_id, "buyer_inv")
    await engine.confirm_payment(order_id, "esc_inv")
    await engine.mark_shipped(order_id, "s_inv")
    await engine.confirm_delivery(order_id, "buyer_inv")
    await engine.complete_order(order_id)

    success, msg = await engine.submit_review(order_id, "buyer_inv", rating=6)
    assert success is False
    assert "between 1 and 5" in msg.lower()


@pytest.mark.asyncio
async def test_get_user_reputation_no_reviews(engine):
    """Reputation for user with no reviews."""
    rep = await engine.get_user_reputation("unknown_user")
    assert rep["total_reviews"] == 0
    assert rep["average_rating"] == 0.0


@pytest.mark.asyncio
async def test_get_orders_for_user(engine):
    """Get orders by user role."""
    lst = await engine.create_listing(
        seller_id="s_ord_user", title="Order User Test", description="T",
        category="other", token_type="nexus", price=30.0, quantity=5,
    )
    await engine.create_order(lst.listing_id, "buyer_ord1", quantity=1)
    await engine.create_order(lst.listing_id, "buyer_ord2", quantity=2)

    # Buyer orders
    buyer_orders = await engine.get_orders_for_user("buyer_ord1", role="buyer")
    assert len(buyer_orders) == 1

    # Seller orders
    seller_orders = await engine.get_orders_for_user("s_ord_user", role="seller")
    assert len(seller_orders) == 2


@pytest.mark.asyncio
async def test_check_expired(engine):
    """Check expiry of listings."""
    lst = await engine.create_listing(
        seller_id="s_exp", title="Expiry Test", description="T",
        category="other", token_type="nexus", price=10.0, expiry_days=0,  # Expire immediately
    )
    # Override expires_at to past
    from datetime import datetime, timedelta
    lst.expires_at = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    lst.status = "active"

    expired = await engine.check_expired()
    assert lst.listing_id in expired


@pytest.mark.asyncio
async def test_get_stats(engine):
    """Get marketplace statistics."""
    lst = await engine.create_listing(
        seller_id="s_stat", title="Stats Test", description="T",
        category="digital_goods", token_type="nexus", price=100.0, quantity=3,
    )
    success, order_id = await engine.create_order(lst.listing_id, "buyer_stat", quantity=2)
    await engine.confirm_payment(order_id, "esc_stat")
    await engine.mark_shipped(order_id, "s_stat")
    await engine.confirm_delivery(order_id, "buyer_stat")
    await engine.complete_order(order_id)

    stats = await engine.get_stats()
    assert stats["total_listings"] >= 1
    assert stats["completed_orders"] >= 1
    assert stats["total_revenue"] >= 200.0


@pytest.mark.asyncio
async def test_singleton():
    """Test singleton pattern."""
    e1 = get_marketplace_engine()
    e2 = get_marketplace_engine()
    assert e1 is e2

    reset_marketplace_engine()
    e3 = get_marketplace_engine()
    assert e3 is not e1


@pytest.mark.asyncio
async def test_persistence(tmp_path, engine):
    """Test JSONL persistence."""
    original_path = engine.LEDGER_PATH
    engine.LEDGER_PATH = str(tmp_path / "test_marketplace.jsonl")

    lst = await engine.create_listing(
        seller_id="persist_s", title="Persist Test", description="T",
        category="other", token_type="nexus", price=50.0,
    )
    success, order_id = await engine.create_order(lst.listing_id, "persist_b", quantity=1)

    # Create new engine from same path
    engine2 = MarketplaceEngine()
    engine2.LEDGER_PATH = engine.LEDGER_PATH
    await engine2._ensure_loaded()

    found = await engine2.get_listing(lst.listing_id)
    assert found is not None
    assert found.title == "Persist Test"

    order = await engine2.get_order(order_id)
    assert order is not None
