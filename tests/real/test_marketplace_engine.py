#!/usr/bin/env python3
"""
Tests for [`core/economy/marketplace_engine.py`](../../core/economy/marketplace_engine.py)

Covers:
  - MarketplaceEngine: listing CRUD, cart management, checkout, order lifecycle
  - Dharma VETO on harmful listings
  - Review system
  - Marketplace stats
  - JSONL persistence round-trip
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.economy.marketplace_engine import (
    MarketplaceEngine,
    MarketplaceListing,
    MarketplaceOrder,
    ShoppingCart,
    ShoppingCartItem,
    Review,
    ListingStatus,
    ListingCategory,
    OrderStatus,
    PaymentMethod,
    get_marketplace,
    reset_marketplace,
)

MARKETPLACE_DB = Path(__file__).resolve().parent.parent.parent / "data" / "marketplace.jsonl"


@pytest.fixture(autouse=True)
def clean_db():
    """Clean JSONL database and reset singleton before each test."""
    reset_marketplace()
    if MARKETPLACE_DB.exists():
        MARKETPLACE_DB.unlink()
    yield
    reset_marketplace()


@pytest.fixture
async def mp() -> MarketplaceEngine:
    """Fresh MarketplaceEngine instance."""
    return get_marketplace()


# ══════════════════════════════════════════════════════════════════════════════
# Test: Listing CRUD
# ══════════════════════════════════════════════════════════════════════════════

class TestListings:
    """Listing creation, retrieval, update, and status management."""

    async def test_create_listing(self, mp: MarketplaceEngine):
        """Creating a listing returns success with listing_id."""
        result = mp.create_listing(
            seller_id="seller_001",
            title="AI Model Pack",
            description="Pre-trained neural network model",
            category="ai_model",
            price=99.99,
            currency="SVT",
            quantity=10,
            tags=["ai", "ml", "model"],
            delivery_type="digital",
        )
        assert result["success"] is True
        assert result["listing_id"].startswith("lst_")
        assert result["listing"]["title"] == "AI Model Pack"
        assert result["listing"]["price"] == 99.99
        assert result["listing"]["status"] == "active"

    async def test_get_listing(self, mp: MarketplaceEngine):
        """Getting a listing returns the correct data."""
        result = mp.create_listing("seller_001", "Test Asset", price=50.0)
        listing = mp.get_listing(result["listing_id"])
        assert listing is not None
        assert listing["title"] == "Test Asset"
        assert listing["seller_id"] == "seller_001"

    async def test_get_nonexistent_listing(self, mp: MarketplaceEngine):
        """Getting a nonexistent listing returns None."""
        assert mp.get_listing("nonexistent") is None

    async def test_update_listing(self, mp: MarketplaceEngine):
        """Updating a listing changes its fields."""
        result = mp.create_listing("seller_001", "Original Title", price=10.0)
        lid = result["listing_id"]
        result = mp.update_listing(lid, "seller_001", title="Updated Title", price=20.0)
        assert result["success"] is True
        listing = mp.get_listing(lid)
        assert listing["title"] == "Updated Title"
        assert listing["price"] == 20.0

    async def test_update_wrong_seller(self, mp: MarketplaceEngine):
        """Only the seller can update their listing."""
        result = mp.create_listing("seller_001", "My Asset", price=10.0)
        result = mp.update_listing(result["listing_id"], "seller_002", title="Hacked")
        assert result["success"] is False
        assert "Not your listing" in result["error"]

    async def test_pause_activate_cancel(self, mp: MarketplaceEngine):
        """Listing status transitions work correctly."""
        result = mp.create_listing("seller_001", "Test", price=10.0)
        lid = result["listing_id"]

        pause = mp.pause_listing(lid, "seller_001")
        assert pause["success"] is True
        assert mp.get_listing(lid)["status"] == "paused"

        activate = mp.activate_listing(lid, "seller_001")
        assert activate["success"] is True
        assert mp.get_listing(lid)["status"] == "active"

        cancel = mp.cancel_listing(lid, "seller_001")
        assert cancel["success"] is True
        assert mp.get_listing(lid)["status"] == "cancelled"

    async def test_list_listings_filter(self, mp: MarketplaceEngine):
        """List listings filters by category, seller, price, search."""
        mp.create_listing("seller_001", "AI Model", category="ai_model", price=100.0, tags=["ai"])
        mp.create_listing("seller_001", "Data Set", category="data", price=50.0, tags=["data"])
        mp.create_listing("seller_002", "Compute Time", category="compute", price=200.0, tags=["gpu"])

        results = mp.list_listings(category="ai_model")
        assert len(results["listings"]) == 1

        results = mp.list_listings(seller_id="seller_001")
        assert len(results["listings"]) == 2

        results = mp.list_listings(min_price=100.0)
        assert len(results["listings"]) == 2

        results = mp.list_listings(search="data")
        assert len(results["listings"]) == 1

    async def test_list_listings_pagination(self, mp: MarketplaceEngine):
        """List listings supports offset and limit."""
        for i in range(5):
            mp.create_listing("seller_001", f"Asset {i}", price=10.0)

        all_results = mp.list_listings(limit=100)
        assert all_results["total"] == 5

        page1 = mp.list_listings(limit=2, offset=0)
        assert len(page1["listings"]) == 2

        page2 = mp.list_listings(limit=2, offset=2)
        assert len(page2["listings"]) == 2

        page3 = mp.list_listings(limit=2, offset=4)
        assert len(page3["listings"]) == 1


# ══════════════════════════════════════════════════════════════════════════════
# Test: Dharma VETO
# ══════════════════════════════════════════════════════════════════════════════

class TestDharmaVeto:
    """Harmful listings are blocked by Dharma-Chakra VETO."""

    async def test_block_weapon(self, mp: MarketplaceEngine):
        """Weapon listings are vetoed."""
        result = mp.create_listing("seller_001", "AK-47 Assault Rifle", "Fully automatic weapon")
        assert result["success"] is False
        assert "VETO" in result["error"]

    async def test_block_scam(self, mp: MarketplaceEngine):
        """Scam listings are vetoed."""
        result = mp.create_listing("seller_001", "Investment Opportunity", "This is a scam pyramid scheme")
        assert result["success"] is False
        assert "VETO" in result["error"]

    async def test_block_illegal(self, mp: MarketplaceEngine):
        """Illegal content listings are vetoed."""
        result = mp.create_listing("seller_001", "Hack Services", "I will hack any account")
        assert result["success"] is False
        assert "VETO" in result["error"]

    async def test_allow_legitimate(self, mp: MarketplaceEngine):
        """Legitimate listings pass through."""
        result = mp.create_listing("seller_001", "Python Course", "Learn Python programming")
        assert result["success"] is True

    async def test_veto_on_update(self, mp: MarketplaceEngine):
        """Updating a listing to harmful content triggers veto."""
        result = mp.create_listing("seller_001", "Legit Service", price=10.0)
        lid = result["listing_id"]
        result = mp.update_listing(lid, "seller_001", title="Hack Services", description="I will hack")
        assert result["success"] is False
        assert "VETO" in result["error"]


# ══════════════════════════════════════════════════════════════════════════════
# Test: Shopping Cart
# ══════════════════════════════════════════════════════════════════════════════

class TestCart:
    """Shopping cart operations."""

    async def test_empty_cart(self, mp: MarketplaceEngine):
        """New cart is empty."""
        cart = mp.get_cart("buyer_001")
        assert cart["user_id"] == "buyer_001"
        assert len(cart["items"]) == 0
        assert cart["total"] == 0

    async def test_add_to_cart(self, mp: MarketplaceEngine):
        """Adding an item to cart works."""
        result = mp.create_listing("seller_001", "Test Asset", price=25.0, quantity=5)
        lid = result["listing_id"]

        result = mp.add_to_cart("buyer_001", lid, 2)
        assert result["success"] is True
        assert result["cart"]["item_count"] == 1
        assert result["cart"]["total"] == 50.0

    async def test_cannot_add_own_listing(self, mp: MarketplaceEngine):
        """Cannot add your own listing to cart."""
        result = mp.create_listing("seller_001", "My Asset", price=10.0)
        result = mp.add_to_cart("seller_001", result["listing_id"])
        assert result["success"] is False
        assert "Cannot buy your own" in result["error"]

    async def test_cannot_add_inactive(self, mp: MarketplaceEngine):
        """Cannot add paused/cancelled listing to cart."""
        result = mp.create_listing("seller_001", "Test", price=10.0)
        lid = result["listing_id"]
        mp.pause_listing(lid, "seller_001")

        result = mp.add_to_cart("buyer_001", lid)
        assert result["success"] is False
        assert "not active" in result["error"]

    async def test_remove_from_cart(self, mp: MarketplaceEngine):
        """Removing item from cart works."""
        result = mp.create_listing("seller_001", "Test", price=10.0, quantity=5)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid)
        result = mp.remove_from_cart("buyer_001", lid)
        assert result["success"] is True
        assert result["cart"]["item_count"] == 0

    async def test_update_cart_quantity(self, mp: MarketplaceEngine):
        """Updating cart item quantity works."""
        result = mp.create_listing("seller_001", "Test", price=10.0, quantity=5)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid, 1)
        result = mp.update_cart_item("buyer_001", lid, 3)
        assert result["success"] is True
        assert result["cart"]["total"] == 30.0

    async def test_clear_cart(self, mp: MarketplaceEngine):
        """Clearing cart removes all items."""
        result = mp.create_listing("seller_001", "Test", price=10.0, quantity=5)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid)
        result = mp.clear_cart("buyer_001")
        assert result["success"] is True
        assert mp.get_cart("buyer_001")["item_count"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# Test: Checkout and Orders
# ══════════════════════════════════════════════════════════════════════════════

class TestOrders:
    """Order creation, payment, fulfillment, completion lifecycle."""

    async def test_checkout_creates_orders(self, mp: MarketplaceEngine):
        """Checkout creates orders from cart items."""
        result = mp.create_listing("seller_001", "AI Model", price=50.0, quantity=3)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid, 2)

        result = mp.checkout("buyer_001")
        assert result["success"] is True
        assert result["total_orders"] == 1

        order = result["orders"][0]
        assert order["listing_id"] == lid
        assert order["buyer_id"] == "buyer_001"
        assert order["seller_id"] == "seller_001"
        assert order["quantity"] == 2
        assert order["total_price"] == 100.0
        assert order["status"] == "pending_payment"

    async def test_checkout_empty_cart(self, mp: MarketplaceEngine):
        """Checkout with empty cart fails."""
        result = mp.checkout("buyer_001")
        assert result["success"] is False
        assert "empty" in result["error"]

    async def test_checkout_reduces_quantity(self, mp: MarketplaceEngine):
        """Checkout reduces listing quantity."""
        result = mp.create_listing("seller_001", "Test", price=10.0, quantity=5)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid, 3)
        mp.checkout("buyer_001")

        listing = mp.get_listing(lid)
        assert listing["quantity"] == 2
        assert listing["sold_count"] == 1

    async def test_full_order_lifecycle(self, mp: MarketplaceEngine):
        """Order goes through full lifecycle."""
        result = mp.create_listing("seller_001", "Service", price=100.0, quantity=1)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid, 1)
        checkout = mp.checkout("buyer_001")
        oid = checkout["orders"][0]["order_id"]

        pay = mp.process_payment(oid, "tx_abc123")
        assert pay["success"] is True
        assert mp.get_order(oid)["status"] == "paid"

        fulfill = mp.fulfill_order(oid, "seller_001")
        assert fulfill["success"] is True
        assert mp.get_order(oid)["status"] == "fulfilled"

        complete = mp.complete_order(oid, "buyer_001")
        assert complete["success"] is True
        assert mp.get_order(oid)["status"] == "completed"

    async def test_cancel_order_restores_quantity(self, mp: MarketplaceEngine):
        """Cancelling an order restores listing quantity."""
        result = mp.create_listing("seller_001", "Test", price=10.0, quantity=5)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid, 2)
        checkout = mp.checkout("buyer_001")
        oid = checkout["orders"][0]["order_id"]

        mp.cancel_order(oid, "buyer_001")
        listing = mp.get_listing(lid)
        assert listing["quantity"] == 5

    async def test_dispute_and_refund(self, mp: MarketplaceEngine):
        """Dispute and refund lifecycle works."""
        result = mp.create_listing("seller_001", "Asset", price=50.0, quantity=1)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid, 1)
        checkout = mp.checkout("buyer_001")
        oid = checkout["orders"][0]["order_id"]
        mp.process_payment(oid, "tx_001")

        dispute = mp.dispute_order(oid, "buyer_001", "Not as described")
        assert dispute["success"] is True
        assert mp.get_order(oid)["status"] == "disputed"

        refund = mp.refund_order(oid, "arbitrator_001")
        assert refund["success"] is True
        assert mp.get_order(oid)["status"] == "refunded"

    async def test_list_orders(self, mp: MarketplaceEngine):
        """List orders filters by user and role."""
        mp.create_listing("seller_001", "Asset", price=10.0, quantity=1)
        lid = mp.create_listing("seller_001", "Asset 2", price=20.0, quantity=1)["listing_id"]
        mp.add_to_cart("buyer_001", lid, 1)
        mp.checkout("buyer_001")

        buyer_orders = mp.list_orders(user_id="buyer_001", role="buyer")
        assert buyer_orders["total"] >= 1

        seller_orders = mp.list_orders(user_id="seller_001", role="seller")
        assert seller_orders["total"] >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Test: Reviews
# ══════════════════════════════════════════════════════════════════════════════

class TestReviews:
    """Review system for completed orders."""

    async def test_add_review(self, mp: MarketplaceEngine):
        """Adding a review to completed order works."""
        result = mp.create_listing("seller_001", "Great Service", price=50.0, quantity=1)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid, 1)
        checkout = mp.checkout("buyer_001")
        oid = checkout["orders"][0]["order_id"]
        mp.process_payment(oid, "tx_001")
        mp.fulfill_order(oid, "seller_001")
        mp.complete_order(oid, "buyer_001")

        review = mp.add_review(oid, "buyer_001", 5, "Excellent!", "Really great service.")
        assert review["success"] is True
        assert review["review"]["rating"] == 5
        assert review["review"]["reviewer_id"] == "buyer_001"

    async def test_review_updates_listing_rating(self, mp: MarketplaceEngine):
        """Review updates the listing's average rating."""
        result = mp.create_listing("seller_001", "Product", price=10.0, quantity=2)
        lid = result["listing_id"]

        def _buy_and_review(buyer, rating):
            mp.add_to_cart(buyer, lid, 1)
            co = mp.checkout(buyer)
            oid = co["orders"][0]["order_id"]
            mp.process_payment(oid, f"tx_{buyer}")
            mp.fulfill_order(oid, "seller_001")
            mp.complete_order(oid, buyer)
            mp.add_review(oid, buyer, rating, "Review")

        _buy_and_review("buyer_a", 5)
        _buy_and_review("buyer_b", 3)

        listing = mp.get_listing(lid)
        assert listing["rating_count"] == 2
        assert listing["rating_avg"] == 4.0

    async def test_no_duplicate_review(self, mp: MarketplaceEngine):
        """Cannot review the same order twice."""
        result = mp.create_listing("seller_001", "Test", price=10.0, quantity=1)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid, 1)
        co = mp.checkout("buyer_001")
        oid = co["orders"][0]["order_id"]
        mp.process_payment(oid, "tx_001")
        mp.fulfill_order(oid, "seller_001")
        mp.complete_order(oid, "buyer_001")

        mp.add_review(oid, "buyer_001", 5)
        result = mp.add_review(oid, "buyer_001", 4)
        assert result["success"] is False
        assert "Already reviewed" in result["error"]

    async def test_review_non_completed_order(self, mp: MarketplaceEngine):
        """Cannot review a non-completed order."""
        result = mp.create_listing("seller_001", "Test", price=10.0, quantity=1)
        lid = result["listing_id"]
        mp.add_to_cart("buyer_001", lid, 1)
        co = mp.checkout("buyer_001")
        oid = co["orders"][0]["order_id"]

        result = mp.add_review(oid, "buyer_001", 5)
        assert result["success"] is False
        assert "completed" in result["error"]


# ══════════════════════════════════════════════════════════════════════════════
# Test: Marketplace Stats
# ══════════════════════════════════════════════════════════════════════════════

class TestStats:
    """Marketplace statistics aggregation."""

    async def test_stats_initial(self, mp: MarketplaceEngine):
        """Initial stats are zero."""
        stats = mp.marketplace_stats()
        assert stats["total_listings"] == 0
        assert stats["active_listings"] == 0
        assert stats["total_orders"] == 0
        assert stats["total_revenue"] == 0.0

    async def test_stats_with_data(self, mp: MarketplaceEngine):
        """Stats reflect marketplace activity."""
        r1 = mp.create_listing("seller_001", "Asset 1", price=10.0, quantity=5)
        mp.create_listing("seller_001", "Asset 2", price=20.0, quantity=3)
        mp.create_listing("seller_002", "Asset 3", price=30.0, quantity=1)

        mp.pause_listing(r1["listing_id"], "seller_001")

        lid = mp.create_listing("seller_002", "Sold Item", price=50.0, quantity=2)["listing_id"]
        mp.add_to_cart("buyer_001", lid, 2)
        co = mp.checkout("buyer_001")
        oid = co["orders"][0]["order_id"]
        mp.process_payment(oid, "tx_001")

        stats = mp.marketplace_stats()
        assert stats["total_listings"] == 4
        assert stats["active_listings"] == 3
        assert stats["total_orders"] == 1
        assert stats["total_revenue"] == 100.0
        assert stats["sold_items"] == 2
        assert stats["total_sellers"] == 2
        assert stats["total_buyers"] == 1


# ══════════════════════════════════════════════════════════════════════════════
# Test: Persistence
# ══════════════════════════════════════════════════════════════════════════════

class TestPersistence:
    """JSONL persistence round-trip."""

    async def test_listing_persistence(self, mp: MarketplaceEngine):
        """Listings survive reset + reload."""
        mp.create_listing("seller_001", "Persistent Asset", category="ai_model",
                          price=99.99, quantity=5, tags=["ai", "test"])

        reset_marketplace()
        mp2 = get_marketplace()

        results = mp2.list_listings(limit=100)
        assert results["total"] == 1
        assert results["listings"][0]["title"] == "Persistent Asset"
        assert results["listings"][0]["price"] == 99.99
        assert results["listings"][0]["tags"] == ["ai", "test"]

    async def test_order_persistence(self, mp: MarketplaceEngine):
        """Orders survive reset + reload."""
        lid = mp.create_listing("seller_001", "Product", price=25.0, quantity=10)["listing_id"]
        mp.add_to_cart("buyer_001", lid, 3)
        mp.checkout("buyer_001")

        reset_marketplace()
        mp2 = get_marketplace()

        orders = mp2.list_orders(user_id="buyer_001")
        assert orders["total"] >= 1
        assert orders["orders"][0]["quantity"] == 3

    async def test_cart_persistence(self, mp: MarketplaceEngine):
        """Cart survives reset + reload."""
        lid = mp.create_listing("seller_001", "Item", price=5.0, quantity=10)["listing_id"]
        mp.add_to_cart("buyer_001", lid, 2)

        reset_marketplace()
        mp2 = get_marketplace()

        cart = mp2.get_cart("buyer_001")
        assert cart["item_count"] == 1
        assert cart["total"] == 10.0

    async def test_review_persistence(self, mp: MarketplaceEngine):
        """Reviews survive reset + reload."""
        lid = mp.create_listing("seller_001", "Service", price=50.0, quantity=1)["listing_id"]
        mp.add_to_cart("buyer_001", lid, 1)
        co = mp.checkout("buyer_001")
        oid = co["orders"][0]["order_id"]
        mp.process_payment(oid, "tx_001")
        mp.fulfill_order(oid, "seller_001")
        mp.complete_order(oid, "buyer_001")
        mp.add_review(oid, "buyer_001", 5, "Great!", "Highly recommend.")

        reset_marketplace()
        mp2 = get_marketplace()

        reviews = mp2.list_reviews()
        assert reviews["total"] == 1
        assert reviews["reviews"][0]["rating"] == 5
        assert reviews["reviews"][0]["body"] == "Highly recommend."

    async def test_reset_does_not_delete_db(self, mp: MarketplaceEngine):
        """reset_marketplace() preserves the JSONL file."""
        mp.create_listing("seller_001", "Keep Me", price=10.0)
        reset_marketplace()
        assert MARKETPLACE_DB.exists(), "JSONL file should still exist after reset"
        mp2 = get_marketplace()
        results = mp2.list_listings(limit=100)
        assert results["total"] == 1
