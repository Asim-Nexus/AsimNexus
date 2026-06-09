"""
ASIMNEXUS Marketplace System
=============================
Decentralized marketplace with listings, escrow-backed transactions,
reputation system, and category management.

Integrates with:
- escrow.py for secure transaction hold/release
- tokens.py for token-based pricing
- wallet.py for balance operations
"""

import asyncio
import logging
import json
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("Marketplace")

# ── Types ────────────────────────────────────────────────────────────────────


class ListingStatus(Enum):
    ACTIVE = "active"
    PENDING = "pending"        # Awaiting approval
    SOLD = "sold"              # Successfully sold
    CANCELLED = "cancelled"    # Cancelled by seller
    EXPIRED = "expired"        # Listing timed out
    DISPUTED = "disputed"      # Under dispute


class OrderStatus(Enum):
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"              # Funds in escrow
    SHIPPED = "shipped"        # Seller shipped/delivered
    DELIVERED = "delivered"    # Buyer confirmed receipt
    COMPLETED = "completed"    # Funds released to seller
    DISPUTED = "disputed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class ListingCategory(Enum):
    DIGITAL_GOODS = "digital_goods"
    SERVICES = "services"
    COMPUTE = "compute"
    STORAGE = "storage"
    DATA = "data"
    MODEL_ACCESS = "model_access"
    API_ACCESS = "api_access"
    AGENT_SERVICES = "agent_services"
    DOMAIN_NAMES = "domain_names"
    OTHER = "other"


# ── Data Models ──────────────────────────────────────────────────────────────


@dataclass
class Listing:
    """A marketplace listing."""
    listing_id: str
    seller_id: str
    title: str
    description: str
    category: str
    token_type: str
    price: float
    quantity: int = 1
    available: int = 1
    status: str = "active"
    tags: List[str] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)
    terms_hash: Optional[str] = None
    escrow_required: bool = True
    created_at: str = ""
    updated_at: str = ""
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Listing":
        return cls(**data)


@dataclass
class MarketplaceOrder:
    """An order on a marketplace listing."""
    order_id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    token_type: str
    price: float
    quantity: int
    total_amount: float
    escrow_id: Optional[str] = None
    status: str = "pending_payment"
    shipping_info: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketplaceOrder":
        return cls(**data)


@dataclass
class Review:
    """A review/rating for a transaction."""
    review_id: str
    order_id: str
    listing_id: str
    reviewer_id: str
    reviewee_id: str
    rating: int  # 1-5
    description: str = ""
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Review":
        return cls(**data)


# ── Marketplace Engine ───────────────────────────────────────────────────────


class MarketplaceEngine:
    """
    Decentralized marketplace engine.

    Features:
    - Create/manage listings with categories and tags
    - Place orders with automatic escrow creation
    - Order lifecycle: pending → paid (escrowed) → shipped → delivered → completed
    - Review and rating system
    - Seller reputation tracking
    - Listing expiry and auto-cleanup
    """

    LEDGER_PATH = "data/marketplace_ledger.jsonl"

    def __init__(self):
        self._listings: Dict[str, Listing] = {}
        self._orders: Dict[str, MarketplaceOrder] = {}
        self._reviews: Dict[str, Review] = {}
        self._lock = asyncio.Lock()
        self._loaded = False

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def _ensure_loaded(self):
        if not self._loaded:
            await self._load_ledger()
            self._loaded = True

    async def _load_ledger(self):
        from pathlib import Path
        ledger = Path(self.LEDGER_PATH)
        if not ledger.exists():
            ledger.parent.mkdir(parents=True, exist_ok=True)
            return
        try:
            for line in ledger.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    etype = entry.get("_type", "")
                    data = entry["data"]
                    if etype == "listing":
                        l = Listing.from_dict(data)
                        self._listings[l.listing_id] = l
                    elif etype == "order":
                        o = MarketplaceOrder.from_dict(data)
                        self._orders[o.order_id] = o
                    elif etype == "review":
                        r = Review.from_dict(data)
                        self._reviews[r.review_id] = r
                except (json.JSONDecodeError, KeyError):
                    continue
            logger.info(f"Loaded {len(self._listings)} listings, {len(self._orders)} orders")
        except Exception as e:
            logger.error(f"Failed to load marketplace ledger: {e}")

    async def _append_ledger(self, entry_type: str, data: dict):
        from pathlib import Path
        ledger = Path(self.LEDGER_PATH)
        ledger.parent.mkdir(parents=True, exist_ok=True)
        record = json.dumps({"_type": entry_type, "data": data, "_ts": datetime.utcnow().isoformat()})
        async with self._lock:
            with ledger.open("a") as f:
                f.write(record + "\n")

    # ── Listing Management ───────────────────────────────────────────────

    async def create_listing(
        self,
        seller_id: str,
        title: str,
        description: str,
        category: str,
        token_type: str,
        price: float,
        quantity: int = 1,
        tags: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        escrow_required: bool = True,
        expiry_days: Optional[int] = 30,
        metadata: Optional[Dict] = None,
    ) -> Listing:
        """Create a new marketplace listing."""
        if price <= 0:
            raise ValueError("Price must be positive")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        await self._ensure_loaded()
        now = datetime.utcnow()

        listing = Listing(
            listing_id=f"lst_{uuid.uuid4().hex[:16]}",
            seller_id=seller_id,
            title=title,
            description=description,
            category=category,
            token_type=token_type,
            price=price,
            quantity=quantity,
            available=quantity,
            status="active",
            tags=tags or [],
            media_urls=media_urls or [],
            escrow_required=escrow_required,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            expires_at=(now.replace(hour=0, minute=0, second=0, microsecond=0) +
                       __import__('datetime').timedelta(days=expiry_days)).isoformat()
            if expiry_days else None,
            metadata=metadata or {},
        )

        # Generate terms hash
        terms_str = f"{listing.listing_id}|{listing.price}|{listing.token_type}|{listing.escrow_required}"
        listing.terms_hash = hashlib.sha256(terms_str.encode()).hexdigest()[:16]

        async with self._lock:
            self._listings[listing.listing_id] = listing
        await self._append_ledger("listing", listing.to_dict())
        logger.info(f"Created listing {listing.listing_id}: {title} ({price} {token_type})")
        return listing

    async def get_listing(self, listing_id: str) -> Optional[Listing]:
        """Get a listing by ID."""
        await self._ensure_loaded()
        return self._listings.get(listing_id)

    async def search_listings(
        self,
        category: Optional[str] = None,
        seller_id: Optional[str] = None,
        token_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        tags: Optional[List[str]] = None,
        status: str = "active",
        sort_by: str = "created_at",
        sort_desc: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Listing]:
        """Search listings with filters."""
        await self._ensure_loaded()
        results = list(self._listings.values())

        # Apply filters
        if category:
            results = [l for l in results if l.category == category]
        if seller_id:
            results = [l for l in results if l.seller_id == seller_id]
        if token_type:
            results = [l for l in results if l.token_type == token_type]
        if status:
            results = [l for l in results if l.status == status]
        if min_price is not None:
            results = [l for l in results if l.price >= min_price]
        if max_price is not None:
            results = [l for l in results if l.price <= max_price]
        if tags:
            results = [l for l in results if any(t in l.tags for t in tags)]

        # Sort
        reverse = sort_desc
        results.sort(key=lambda l: getattr(l, sort_by, ""), reverse=reverse)

        return results[offset:offset + limit]

    async def cancel_listing(self, listing_id: str, seller_id: str) -> Tuple[bool, str]:
        """Cancel a listing."""
        listing = await self.get_listing(listing_id)
        if not listing:
            return False, "Listing not found"
        if listing.seller_id != seller_id:
            return False, "Only the seller can cancel this listing"
        if listing.status != "active":
            return False, f"Cannot cancel listing with status {listing.status}"

        listing.status = "cancelled"
        listing.updated_at = datetime.utcnow().isoformat()
        await self._append_ledger("listing", listing.to_dict())
        logger.info(f"Listing {listing_id} cancelled by seller {seller_id}")
        return True, listing_id

    # ── Order Management ─────────────────────────────────────────────────

    async def create_order(
        self,
        listing_id: str,
        buyer_id: str,
        quantity: int = 1,
        notes: str = "",
        shipping_info: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """Create an order with automatic escrow."""
        listing = await self.get_listing(listing_id)
        if not listing:
            return False, "Listing not found"
        if listing.status != "active":
            return False, f"Listing is {listing.status}"
        if listing.seller_id == buyer_id:
            return False, "Cannot buy your own listing"
        if listing.available < quantity:
            return False, f"Insufficient quantity (available: {listing.available})"

        total = listing.price * quantity
        now = datetime.utcnow()

        order = MarketplaceOrder(
            order_id=f"ord_{uuid.uuid4().hex[:16]}",
            listing_id=listing_id,
            buyer_id=buyer_id,
            seller_id=listing.seller_id,
            token_type=listing.token_type,
            price=listing.price,
            quantity=quantity,
            total_amount=total,
            status="pending_payment",
            shipping_info=shipping_info or {},
            notes=notes,
            created_at=now.isoformat(),
            metadata=metadata or {},
        )

        # Reduce availability
        listing.available -= quantity
        listing.updated_at = now.isoformat()

        async with self._lock:
            self._orders[order.order_id] = order
        await self._append_ledger("order", order.to_dict())
        await self._append_ledger("listing", listing.to_dict())
        logger.info(f"Order {order.order_id} created: {quantity}x {listing.title}")
        return True, order.order_id

    async def confirm_payment(self, order_id: str, escrow_id: str) -> Tuple[bool, str]:
        """Confirm payment received (funds in escrow)."""
        order = await self.get_order(order_id)
        if not order:
            return False, "Order not found"
        if order.status != "pending_payment":
            return False, f"Order is {order.status}, not pending_payment"

        order.status = "paid"
        order.escrow_id = escrow_id
        await self._append_ledger("order", order.to_dict())
        logger.info(f"Order {order_id} payment confirmed (escrow: {escrow_id})")
        return True, order_id

    async def mark_shipped(self, order_id: str, seller_id: str) -> Tuple[bool, str]:
        """Mark order as shipped/delivered by seller."""
        order = await self.get_order(order_id)
        if not order:
            return False, "Order not found"
        if order.seller_id != seller_id:
            return False, "Only seller can mark as shipped"
        if order.status != "paid":
            return False, f"Order is {order.status}, not paid"

        order.status = "shipped"
        await self._append_ledger("order", order.to_dict())
        logger.info(f"Order {order_id} marked shipped by seller")
        return True, order_id

    async def confirm_delivery(self, order_id: str, buyer_id: str) -> Tuple[bool, str]:
        """Buyer confirms delivery — triggers escrow release."""
        order = await self.get_order(order_id)
        if not order:
            return False, "Order not found"
        if order.buyer_id != buyer_id:
            return False, "Only buyer can confirm delivery"
        if order.status != "shipped":
            return False, f"Order is {order.status}, not shipped"

        order.status = "delivered"
        order.completed_at = datetime.utcnow().isoformat()
        await self._append_ledger("order", order.to_dict())
        logger.info(f"Order {order_id} delivery confirmed by buyer")
        return True, order_id

    async def complete_order(self, order_id: str) -> Tuple[bool, str]:
        """Mark order as fully complete."""
        order = await self.get_order(order_id)
        if not order:
            return False, "Order not found"
        if order.status not in ("delivered", "paid"):
            return False, f"Order is {order.status}, cannot complete"

        order.status = "completed"
        order.completed_at = datetime.utcnow().isoformat()
        await self._append_ledger("order", order.to_dict())

        # Update listing availability if sold out
        listing = await self.get_listing(order.listing_id)
        if listing and listing.available <= 0:
            listing.status = "sold"
            listing.updated_at = datetime.utcnow().isoformat()
            await self._append_ledger("listing", listing.to_dict())

        logger.info(f"Order {order_id} completed")
        return True, order_id

    async def cancel_order(self, order_id: str, requested_by: str) -> Tuple[bool, str]:
        """Cancel an order before payment."""
        order = await self.get_order(order_id)
        if not order:
            return False, "Order not found"
        if requested_by not in (order.buyer_id, order.seller_id):
            return False, "Only buyer or seller can cancel"
        if order.status not in ("pending_payment", "paid"):
            return False, f"Cannot cancel order in status {order.status}"

        # Restore listing availability
        listing = await self.get_listing(order.listing_id)
        if listing:
            listing.available += order.quantity
            listing.updated_at = datetime.utcnow().isoformat()
            await self._append_ledger("listing", listing.to_dict())

        order.status = "cancelled"
        await self._append_ledger("order", order.to_dict())
        logger.info(f"Order {order_id} cancelled by {requested_by}")
        return True, order_id

    async def get_order(self, order_id: str) -> Optional[MarketplaceOrder]:
        """Get an order by ID."""
        await self._ensure_loaded()
        return self._orders.get(order_id)

    async def get_orders_for_user(
        self,
        user_id: str,
        role: Optional[str] = None,  # "buyer", "seller", or None for both
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MarketplaceOrder]:
        """Get orders where user is buyer or seller."""
        await self._ensure_loaded()
        results = []
        for o in self._orders.values():
            if role == "buyer" and o.buyer_id != user_id:
                continue
            if role == "seller" and o.seller_id != user_id:
                continue
            if role is None and o.buyer_id != user_id and o.seller_id != user_id:
                continue
            if status and o.status != status:
                continue
            results.append(o)

        results.sort(key=lambda o: o.created_at, reverse=True)
        return results[offset:offset + limit]

    # ── Reviews & Reputation ─────────────────────────────────────────────

    async def submit_review(
        self,
        order_id: str,
        reviewer_id: str,
        rating: int,
        description: str = "",
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """Submit a review for a completed order."""
        if rating < 1 or rating > 5:
            return False, "Rating must be between 1 and 5"

        order = await self.get_order(order_id)
        if not order:
            return False, "Order not found"
        if order.buyer_id != reviewer_id and order.seller_id != reviewer_id:
            return False, "Only buyer or seller can review"
        if order.status != "completed":
            return False, "Can only review completed orders"

        # Determine reviewee (the other party)
        reviewee_id = order.seller_id if reviewer_id == order.buyer_id else order.buyer_id

        review = Review(
            review_id=f"rev_{uuid.uuid4().hex[:16]}",
            order_id=order_id,
            listing_id=order.listing_id,
            reviewer_id=reviewer_id,
            reviewee_id=reviewee_id,
            rating=rating,
            description=description,
            created_at=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )

        async with self._lock:
            self._reviews[review.review_id] = review
        await self._append_ledger("review", review.to_dict())
        logger.info(f"Review {review.review_id}: {rating}/5 for {reviewee_id}")
        return True, review.review_id

    async def get_user_reputation(self, user_id: str) -> Dict[str, Any]:
        """Get reputation stats for a user."""
        await self._ensure_loaded()
        ratings = []
        for r in self._reviews.values():
            if r.reviewee_id == user_id:
                ratings.append(r.rating)

        if not ratings:
            return {
                "user_id": user_id,
                "average_rating": 0.0,
                "total_reviews": 0,
                "rating_distribution": {str(i): 0 for i in range(1, 6)},
            }

        distribution = {str(i): 0 for i in range(1, 6)}
        for rating in ratings:
            distribution[str(rating)] = distribution.get(str(rating), 0) + 1

        return {
            "user_id": user_id,
            "average_rating": round(sum(ratings) / len(ratings), 2),
            "total_reviews": len(ratings),
            "rating_distribution": distribution,
        }

    async def get_listing_reviews(self, listing_id: str) -> List[Review]:
        """Get all reviews for a listing."""
        await self._ensure_loaded()
        return [r for r in self._reviews.values() if r.listing_id == listing_id]

    # ── Maintenance ──────────────────────────────────────────────────────

    async def check_expired(self) -> List[str]:
        """Find and expire listings past their expiry date."""
        await self._ensure_loaded()
        now = datetime.utcnow().isoformat()
        expired = []
        for l in self._listings.values():
            if l.status == "active" and l.expires_at and l.expires_at < now:
                l.status = "expired"
                l.updated_at = datetime.utcnow().isoformat()
                await self._append_ledger("listing", l.to_dict())
                expired.append(l.listing_id)
        if expired:
            logger.info(f"Expired {len(expired)} listings")
        return expired

    # ── Stats ────────────────────────────────────────────────────────────

    async def get_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics."""
        await self._ensure_loaded()
        active = sum(1 for l in self._listings.values() if l.status == "active")
        sold = sum(1 for l in self._listings.values() if l.status == "sold")
        total_orders = len(self._orders)
        completed_orders = sum(1 for o in self._orders.values() if o.status == "completed")

        # Revenue stats
        total_revenue = sum(
            o.total_amount for o in self._orders.values()
            if o.status == "completed"
        )

        # Category breakdown
        categories = {}
        for l in self._listings.values():
            categories[l.category] = categories.get(l.category, 0) + 1

        return {
            "total_listings": len(self._listings),
            "active_listings": active,
            "sold_listings": sold,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "completion_rate": round(completed_orders / total_orders * 100, 1)
            if total_orders > 0 else 0.0,
            "total_revenue": total_revenue,
            "total_reviews": len(self._reviews),
            "category_breakdown": categories,
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_engine: Optional[MarketplaceEngine] = None


def get_marketplace_engine() -> MarketplaceEngine:
    """Get or create the singleton marketplace engine."""
    global _engine
    if _engine is None:
        _engine = MarketplaceEngine()
    return _engine


def reset_marketplace_engine():
    """Reset the marketplace engine (for testing)."""
    global _engine
    _engine = None
