"""
MarketplaceEngine REST API endpoints for ASIMNEXUS.

Provides REST API access to MarketplaceEngine operations including:
listing creation/search, order lifecycle, reviews, and statistics.
NOTE: This wraps the new economy.marketplace module, not the legacy core.economy.marketplace_engine.
"""

from typing import Optional, List
from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_marketplace = None

def _get_mp():
    global _marketplace
    if _marketplace is None:
        try:
            from economy.marketplace import get_marketplace_engine
            _marketplace = get_marketplace_engine()
            logger.info("MarketplaceEngine (new) loaded")
        except Exception as e:
            logger.warning(f"MarketplaceEngine (new) unavailable: {e}")
    return _marketplace


# ─── Request Models ───────────────────────────────────────────────────────────


class CreateListingRequest(BaseModel):
    seller_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    price: float = Field(..., gt=0)
    token_type: str = "nexus"
    category: str = "general"
    quantity: int = Field(default=1, ge=1)
    tags: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class SearchListingsRequest(BaseModel):
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    tags: Optional[List[str]] = None
    seller_id: Optional[str] = None
    query: str = ""


class CreateOrderRequest(BaseModel):
    listing_id: str
    buyer_id: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1)
    shipping_address: str = ""
    notes: str = ""


class UpdateOrderStatusRequest(BaseModel):
    order_id: str
    status: str = Field(..., pattern="^(paid|shipped|delivered|cancelled)$")


class SubmitReviewRequest(BaseModel):
    listing_id: str
    reviewer_id: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    title: str = ""
    body: str = ""


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/api/economy/marketplace/listings", tags=["Economy Marketplace"])
async def create_listing(req: CreateListingRequest):
    """Create a new marketplace listing."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    try:
        listing = await m.create_listing(
            seller_id=req.seller_id,
            title=req.title,
            description=req.description,
            price=req.price,
            token_type=req.token_type,
            category=req.category,
            quantity=req.quantity,
            tags=req.tags,
            metadata=req.metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "listing_id": listing.listing_id, "listing": listing.to_dict()}


@router.get("/api/economy/marketplace/listings/{listing_id}", tags=["Economy Marketplace"])
async def get_listing(listing_id: str):
    """Get a listing by ID."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    listing = await m.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found")
    return listing.to_dict()


@router.post("/api/economy/marketplace/listings/search", tags=["Economy Marketplace"])
async def search_listings(req: SearchListingsRequest):
    """Search for listings with filters."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    listings = await m.search_listings(
        category=req.category,
        min_price=req.min_price,
        max_price=req.max_price,
        tags=req.tags,
        seller_id=req.seller_id,
    )
    return {"listings": [l.to_dict() for l in listings], "count": len(listings)}


@router.post("/api/economy/marketplace/listings/{listing_id}/cancel", tags=["Economy Marketplace"])
async def cancel_listing(listing_id: str, seller_id: str = Query(..., description="Seller ID for authorization")):
    """Cancel a listing."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    result = await m.cancel_listing(listing_id, seller_id)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "listing_id": listing_id}


@router.post("/api/economy/marketplace/orders", tags=["Economy Marketplace"])
async def create_order(req: CreateOrderRequest):
    """Create a new order from a listing."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    result = await m.create_order(
        listing_id=req.listing_id,
        buyer_id=req.buyer_id,
        quantity=req.quantity,
        shipping_info={"address": req.shipping_address} if req.shipping_address else None,
        notes=req.notes,
    )
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "order_id": result[1]}


@router.post("/api/economy/marketplace/orders/status", tags=["Economy Marketplace"])
async def update_order_status(req: UpdateOrderStatusRequest):
    """Update order status (paid/shipped/delivered/cancelled)."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    result = await m.update_order_status(req.order_id, req.status)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "order_id": req.order_id, "status": req.status}


@router.get("/api/economy/marketplace/orders/user/{user_id}", tags=["Economy Marketplace"])
async def get_orders_for_user(user_id: str, role: Optional[str] = Query(None, pattern="^(buyer|seller)$")):
    """Get all orders for a user, optionally filtered by role."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    orders = await m.get_orders_for_user(user_id, role=role)
    return {"user_id": user_id, "orders": orders, "count": len(orders)}


@router.post("/api/economy/marketplace/reviews", tags=["Economy Marketplace"])
async def submit_review(req: SubmitReviewRequest):
    """Submit a review for a listing."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    result = await m.submit_review(
        order_id=req.listing_id,
        reviewer_id=req.reviewer_id,
        rating=req.rating,
        description=f"{req.title}: {req.body}" if req.title and req.body else (req.title or req.body or ""),
    )
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "review_id": result[1]}


@router.get("/api/economy/marketplace/reputation/{user_id}", tags=["Economy Marketplace"])
async def get_user_reputation(user_id: str):
    """Get reputation score for a user based on reviews."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    reputation = await m.get_user_reputation(user_id)
    return {"user_id": user_id, "reputation": reputation}


@router.post("/api/economy/marketplace/check-expired", tags=["Economy Marketplace"])
async def check_expired_listings():
    """Check and expire old listings."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    expired = await m.check_expired()
    return {"expired_count": len(expired), "expired_ids": expired}


@router.get("/api/economy/marketplace/stats", tags=["Economy Marketplace"])
async def marketplace_stats():
    """Get marketplace engine statistics."""
    m = _get_mp()
    if not m:
        raise HTTPException(status_code=503, detail="MarketplaceEngine not available")
    return await m.get_stats()
