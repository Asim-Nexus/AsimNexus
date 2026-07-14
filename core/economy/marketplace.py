"""
AsimNexus — Marketplace Engine
==============================
Manages listings, orders, and reviews for the decentralized marketplace.
"""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any


LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "marketplace_ledger.jsonl"
)


class ListingStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    SOLD = "sold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PENDING_PAYMENT = "pending_payment"
    CONFIRMED = "confirmed"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ListingCategory(str, Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    SERVICE = "service"
    DIGITAL_GOODS = "digital_goods"
    DIGITAL_GOOD = "digital_good"
    API_ACCESS = "api_access"
    PHYSICAL_GOOD = "physical_good"
    OTHER = "other"


@dataclass
class Listing:
    listing_id: str
    seller_id: str
    title: str
    description: str
    category: str
    token_type: str
    price: float
    quantity: int
    available: int
    tags: List[str] = field(default_factory=list)
    status: str = "active"
    terms_hash: Optional[str] = None
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    expires_at: Optional[str] = None

    def __post_init__(self):
        if self.terms_hash is None:
            self.terms_hash = f"th_{uuid.uuid4().hex[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "seller_id": self.seller_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "token_type": self.token_type,
            "price": self.price,
            "quantity": self.quantity,
            "available": self.available,
            "tags": self.tags,
            "status": self.status,
            "terms_hash": self.terms_hash,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Listing":
        return cls(
            listing_id=data["listing_id"],
            seller_id=data["seller_id"],
            title=data["title"],
            description=data.get("description", ""),
            category=data["category"],
            token_type=data["token_type"],
            price=data["price"],
            quantity=data["quantity"],
            available=data.get("available", data["quantity"]),
            tags=data.get("tags", []),
            status=data.get("status", "active"),
            terms_hash=data.get("terms_hash"),
            created_at=data.get("created_at", 0.0),
            updated_at=data.get("updated_at", 0.0),
            expires_at=data.get("expires_at"),
        )


@dataclass
class MarketplaceOrder:
    order_id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    quantity: int
    unit_price: float
    total_amount: float
    token_type: str
    status: str = "pending_payment"
    escrow_id: Optional[str] = None
    notes: str = ""
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "listing_id": self.listing_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_amount": self.total_amount,
            "token_type": self.token_type,
            "status": self.status,
            "escrow_id": self.escrow_id,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketplaceOrder":
        return cls(
            order_id=data["order_id"],
            listing_id=data["listing_id"],
            buyer_id=data["buyer_id"],
            seller_id=data["seller_id"],
            quantity=data["quantity"],
            unit_price=data["unit_price"],
            total_amount=data.get("total_amount", data.get("total_price", 0.0)),
            token_type=data["token_type"],
            status=data.get("status", "pending_payment"),
            escrow_id=data.get("escrow_id"),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", 0.0),
            updated_at=data.get("updated_at", 0.0),
            completed_at=data.get("completed_at"),
        )


@dataclass
class Review:
    review_id: str
    listing_id: str
    order_id: str
    reviewer_id: str
    rating: int
    description: str = ""
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_id": self.review_id,
            "listing_id": self.listing_id,
            "order_id": self.order_id,
            "reviewer_id": self.reviewer_id,
            "rating": self.rating,
            "description": self.description,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Review":
        return cls(
            review_id=data["review_id"],
            listing_id=data["listing_id"],
            order_id=data["order_id"],
            reviewer_id=data["reviewer_id"],
            rating=data["rating"],
            description=data.get("description", data.get("comment", "")),
            created_at=data.get("created_at", 0.0),
        )


class MarketplaceEngine:
    """Manages marketplace operations."""

    LEDGER_PATH = LEDGER_PATH

    def __init__(self):
        self._listings: Dict[str, Listing] = {}
        self._orders: Dict[str, MarketplaceOrder] = {}
        self._reviews: Dict[str, Review] = {}
        self._lock = threading.Lock()
        self._load()

    async def create_listing(
        self,
        seller_id: str,
        title: str,
        description: str,
        category: str,
        token_type: str,
        price: float,
        quantity: int = 1,
        tags: List[str] = None,
        expiry_days: Optional[int] = None,
    ) -> Listing:
        """Create a new listing."""
        expires_at = None
        if expiry_days is not None:
            expires_at = (datetime.utcnow() + timedelta(days=expiry_days)).isoformat()
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
            tags=tags or [],
            expires_at=expires_at,
        )
        with self._lock:
            self._listings[listing.listing_id] = listing
            self._persist(listing)
        return listing

    async def get_listing(self, listing_id: str) -> Optional[Listing]:
        """Get listing by ID."""
        with self._lock:
            return self._listings.get(listing_id)

    async def search_listings(
        self,
        category: Optional[str] = None,
        seller_id: Optional[str] = None,
        token_type: Optional[str] = None,
        query: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[Listing]:
        """Search listings with filters."""
        with self._lock:
            results = list(self._listings.values())
        if category:
            results = [l for l in results if l.category == category]
        if seller_id:
            results = [l for l in results if l.seller_id == seller_id]
        if token_type:
            results = [l for l in results if l.token_type == token_type]
        if query:
            query_lower = query.lower()
            results = [
                l for l in results
                if query_lower in l.title.lower() or query_lower in l.description.lower()
            ]
        if min_price is not None:
            results = [l for l in results if l.price >= min_price]
        if max_price is not None:
            results = [l for l in results if l.price <= max_price]
        return [l for l in results if l.status == "active"]

    async def cancel_listing(self, listing_id: str, seller_id: str) -> tuple:
        """Cancel a listing."""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing:
                return (False, "Listing not found")
            if listing.seller_id != seller_id:
                return (False, "Only the seller can cancel")
            listing.status = "cancelled"
            listing.updated_at = datetime.utcnow().timestamp()
            self._persist(listing)
        return (True, "Listing cancelled")

    async def create_order(
        self,
        listing_id: str,
        buyer_id: str,
        quantity: int = 1,
        notes: str = "",
    ) -> tuple:
        """Create an order for a listing."""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing or listing.status != "active":
                return (False, "Listing not available")
            if listing.available < quantity:
                return (False, "Insufficient quantity")
            order = MarketplaceOrder(
                order_id=f"ord_{uuid.uuid4().hex[:16]}",
                listing_id=listing_id,
                buyer_id=buyer_id,
                seller_id=listing.seller_id,
                quantity=quantity,
                unit_price=listing.price,
                total_amount=listing.price * quantity,
                token_type=listing.token_type,
                notes=notes,
            )
            listing.available -= quantity
            if listing.available == 0:
                listing.status = "sold"
            listing.updated_at = datetime.utcnow().timestamp()
            self._orders[order.order_id] = order
            self._persist(listing)
            self._persist_order(order)
        return (True, order.order_id)

    async def place_order(
        self, listing_id: str, buyer_id: str, quantity: int = 1
    ) -> Optional[MarketplaceOrder]:
        """Place an order for a listing (legacy)."""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing or listing.status != "active":
                return None
            if listing.available < quantity:
                return None
            order = MarketplaceOrder(
                order_id=f"ord_{uuid.uuid4().hex[:16]}",
                listing_id=listing_id,
                buyer_id=buyer_id,
                seller_id=listing.seller_id,
                quantity=quantity,
                unit_price=listing.price,
                total_amount=listing.price * quantity,
                token_type=listing.token_type,
            )
            listing.available -= quantity
            if listing.available == 0:
                listing.status = "sold"
            listing.updated_at = datetime.utcnow().timestamp()
            self._orders[order.order_id] = order
            self._persist(listing)
        return order

    async def confirm_payment(self, order_id: str, escrow_id: str) -> tuple:
        """Confirm payment for an order."""
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return (False, "Order not found")
            order.status = "paid"
            order.escrow_id = escrow_id
            order.updated_at = datetime.utcnow().timestamp()
        return (True, "Payment confirmed")

    async def mark_shipped(self, order_id: str, seller_id: str) -> tuple:
        """Mark order as shipped."""
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return (False, "Order not found")
            if order.seller_id != seller_id:
                return (False, "Only seller can mark shipped")
            order.status = "shipped"
            order.updated_at = datetime.utcnow().timestamp()
        return (True, "Order shipped")

    async def confirm_delivery(self, order_id: str, buyer_id: str) -> tuple:
        """Confirm delivery of an order."""
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return (False, "Order not found")
            if order.buyer_id != buyer_id:
                return (False, "Only buyer can confirm delivery")
            order.status = "delivered"
            order.updated_at = datetime.utcnow().timestamp()
        return (True, "Delivery confirmed")

    async def complete_order(self, order_id: str) -> tuple:
        """Complete an order."""
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return (False, "Order not found")
            order.status = "completed"
            order.completed_at = datetime.utcnow().timestamp()
            order.updated_at = datetime.utcnow().timestamp()
        return (True, "Order completed")

    async def cancel_order(self, order_id: str, user_id: str) -> tuple:
        """Cancel an order."""
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return (False, "Order not found")
            if order.buyer_id != user_id and order.seller_id != user_id:
                return (False, "Unauthorized")
            # Restore availability
            listing = self._listings.get(order.listing_id)
            if listing:
                listing.available += order.quantity
                if listing.status == "sold":
                    listing.status = "active"
                listing.updated_at = datetime.utcnow().timestamp()
                self._persist(listing)
            order.status = "cancelled"
            order.updated_at = datetime.utcnow().timestamp()
        return (True, "Order cancelled")

    async def submit_review(
        self, order_id: str, reviewer_id: str, rating: int, description: str = ""
    ) -> tuple:
        """Submit a review for a completed order."""
        if rating < 1 or rating > 5:
            return (False, "Rating must be between 1 and 5")
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return (False, "Order not found")
            if order.status != "completed":
                return (False, "Order not completed")
            review = Review(
                review_id=f"rev_{uuid.uuid4().hex[:16]}",
                listing_id=order.listing_id,
                order_id=order_id,
                reviewer_id=reviewer_id,
                rating=rating,
                description=description,
            )
            self._reviews[review.review_id] = review
        return (True, review.review_id)

    async def add_review(
        self, order_id: str, reviewer_id: str, rating: int, comment: str = ""
    ) -> Optional[Review]:
        """Add a review for an order (legacy)."""
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return None
            review = Review(
                review_id=f"rev_{uuid.uuid4().hex[:16]}",
                listing_id=order.listing_id,
                order_id=order_id,
                reviewer_id=reviewer_id,
                rating=rating,
                description=comment,
            )
            self._reviews[review.review_id] = review
        return review

    async def get_user_reputation(self, user_id: str) -> Dict[str, Any]:
        """Get reputation for a user based on reviews received as seller."""
        with self._lock:
            # Find all listings by this seller
            seller_listings = [l.listing_id for l in self._listings.values() if l.seller_id == user_id]
            # Find all reviews for those listings
            reviews = [r for r in self._reviews.values() if r.listing_id in seller_listings]
            total = len(reviews)
            avg = sum(r.rating for r in reviews) / total if total > 0 else 0.0
            return {
                "total_reviews": total,
                "average_rating": avg,
            }

    async def get_order(self, order_id: str) -> Optional[MarketplaceOrder]:
        """Get order by ID."""
        with self._lock:
            return self._orders.get(order_id)

    async def get_orders_for_user(
        self, user_id: str, role: str = "buyer"
    ) -> List[MarketplaceOrder]:
        """Get orders by user role."""
        with self._lock:
            if role == "buyer":
                return [o for o in self._orders.values() if o.buyer_id == user_id]
            else:
                return [o for o in self._orders.values() if o.seller_id == user_id]

    async def list_orders(
        self, buyer_id: Optional[str] = None, seller_id: Optional[str] = None
    ) -> List[MarketplaceOrder]:
        """List orders with optional filters."""
        with self._lock:
            results = list(self._orders.values())
        if buyer_id:
            results = [o for o in results if o.buyer_id == buyer_id]
        if seller_id:
            results = [o for o in results if o.seller_id == seller_id]
        return results

    async def get_listing_reviews(self, listing_id: str) -> List[Review]:
        """Get all reviews for a listing."""
        with self._lock:
            return [r for r in self._reviews.values() if r.listing_id == listing_id]

    async def check_expired(self) -> List[str]:
        """Check expiry of listings."""
        expired = []
        now = datetime.utcnow()
        with self._lock:
            for listing_id, listing in self._listings.items():
                if listing.status == "active" and listing.expires_at:
                    try:
                        exp = datetime.fromisoformat(listing.expires_at)
                        if now > exp:
                            listing.status = "expired"
                            listing.updated_at = now.timestamp()
                            self._persist(listing)
                            expired.append(listing_id)
                    except (ValueError, TypeError):
                        pass
        return expired

    async def get_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics."""
        with self._lock:
            total_listings = len(self._listings)
            active_listings = sum(1 for l in self._listings.values() if l.status == "active")
            completed_orders = sum(1 for o in self._orders.values() if o.status == "completed")
            total_revenue = sum(
                o.total_amount for o in self._orders.values() if o.status == "completed"
            )
            return {
                "total_listings": total_listings,
                "active_listings": active_listings,
                "completed_orders": completed_orders,
                "total_revenue": total_revenue,
            }

    async def _ensure_loaded(self) -> None:
        """Ensure data is loaded (for testing)."""
        self._load()

    def _persist(self, listing: Listing) -> None:
        try:
            os.makedirs(os.path.dirname(self.LEDGER_PATH), exist_ok=True)
            with open(self.LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(listing.to_dict()) + "\n")
        except Exception:
            pass

    def _persist_order(self, order: MarketplaceOrder) -> None:
        """Persist an order to a separate JSONL file."""
        try:
            orders_path = self.LEDGER_PATH.replace(".jsonl", "_orders.jsonl")
            os.makedirs(os.path.dirname(orders_path), exist_ok=True)
            with open(orders_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(order.to_dict()) + "\n")
        except Exception:
            pass

    def _load(self) -> None:
        try:
            if os.path.exists(self.LEDGER_PATH):
                with open(self.LEDGER_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                listing = Listing.from_dict(data)
                                self._listings[listing.listing_id] = listing
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass

        # Load orders from separate file
        try:
            orders_path = self.LEDGER_PATH.replace(".jsonl", "_orders.jsonl")
            if os.path.exists(orders_path):
                with open(orders_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                order = MarketplaceOrder.from_dict(data)
                                self._orders[order.order_id] = order
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass
        except Exception:
            pass


# Singleton support
_marketplace_engine: Optional[MarketplaceEngine] = None
_marketplace_engine_lock = threading.Lock()


def get_marketplace_engine() -> MarketplaceEngine:
    global _marketplace_engine
    if _marketplace_engine is None:
        with _marketplace_engine_lock:
            if _marketplace_engine is None:
                _marketplace_engine = MarketplaceEngine()
    return _marketplace_engine


def reset_marketplace_engine() -> None:
    global _marketplace_engine
    _marketplace_engine = None
