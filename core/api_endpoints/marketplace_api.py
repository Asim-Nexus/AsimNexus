"""
Marketplace API Routes
======================
FastAPI router for marketplace endpoints (/api/economy/marketplace/*).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/economy/marketplace", tags=["economy-marketplace"])

# Module-level singleton reference (reset by test fixture)
_mp = None


def _get_marketplace():
    global _mp
    if _mp is None:
        from core.economy.marketplace import get_marketplace_engine
        _mp = get_marketplace_engine()
    return _mp


# ── Static routes first ────────────────────────────────────────────────── #


@router.get("/stats")
async def marketplace_stats():
    """Get marketplace statistics."""
    engine = _get_marketplace()
    stats = await engine.get_stats()
    return stats


@router.get("/reputation/{user_id}")
async def user_reputation(user_id: str):
    """Get user reputation."""
    engine = _get_marketplace()
    rep = await engine.get_user_reputation(user_id=user_id)
    return rep


@router.post("/listings/search")
async def search_listings(data: dict):
    """Search listings."""
    engine = _get_marketplace()
    category = data.get("category")
    token_type = data.get("token_type")
    min_price = data.get("min_price")
    max_price = data.get("max_price")
    seller_id = data.get("seller_id")
    query = data.get("query") or data.get("keyword")
    listings = await engine.search_listings(
        category=category,
        token_type=token_type,
        min_price=float(min_price) if min_price is not None else None,
        max_price=float(max_price) if max_price is not None else None,
        seller_id=seller_id,
        query=query,
    )
    return {
        "listings": [
            {
                "listing_id": l.listing_id,
                "seller_id": l.seller_id,
                "title": l.title,
                "description": l.description,
                "price": l.price,
                "token_type": l.token_type,
                "category": l.category,
                "tags": l.tags,
                "status": l.status,
                "created_at": l.created_at,
            }
            for l in listings
        ]
    }


@router.post("/listings")
async def create_listing(data: dict):
    """Create a new listing."""
    engine = _get_marketplace()
    seller_id = data.get("seller_id")
    title = data.get("title")
    description = data.get("description", "")
    price = data.get("price", 0.0)
    token_type = data.get("token_type", "nexus")
    category = data.get("category", "general")
    tags = data.get("tags", [])
    expiry_days = data.get("expiry_days", 30)
    if not seller_id or not title:
        raise HTTPException(status_code=400, detail="seller_id and title are required")
    try:
        listing = await engine.create_listing(
            seller_id=seller_id,
            title=title,
            description=description,
            price=float(price),
            token_type=token_type,
            category=category,
            tags=tags,
            expiry_days=int(expiry_days),
        )
        return {"success": True, "listing_id": listing.listing_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/listings/{listing_id}/cancel")
async def cancel_listing(listing_id: str, data: dict = {}, seller_id: str = ""):
    """Cancel a listing."""
    engine = _get_marketplace()
    # Support seller_id from query param or request body
    sid = seller_id or data.get("seller_id", "")
    if not sid:
        raise HTTPException(status_code=400, detail="seller_id is required")
    success, msg = await engine.cancel_listing(listing_id=listing_id, seller_id=sid)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True}


@router.get("/listings/{listing_id}")
async def get_listing(listing_id: str):
    """Get a listing by ID."""
    engine = _get_marketplace()
    listing = await engine.get_listing(listing_id=listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {
        "listing_id": listing.listing_id,
        "seller_id": listing.seller_id,
        "title": listing.title,
        "description": listing.description,
        "price": listing.price,
        "token_type": listing.token_type,
        "category": listing.category,
        "tags": listing.tags,
        "status": listing.status,
        "created_at": listing.created_at,
        "expires_at": listing.expires_at,
    }


@router.post("/orders")
async def create_order(data: dict):
    """Create an order from a listing."""
    engine = _get_marketplace()
    listing_id = data.get("listing_id")
    buyer_id = data.get("buyer_id")
    quantity = data.get("quantity", 1)
    if not listing_id or not buyer_id:
        raise HTTPException(status_code=400, detail="listing_id and buyer_id are required")
    success, order_id = await engine.create_order(
        listing_id=listing_id,
        buyer_id=buyer_id,
        quantity=int(quantity),
    )
    if not success:
        raise HTTPException(status_code=400, detail=order_id)
    return {"success": True, "order_id": order_id}


@router.post("/reviews")
async def submit_review(data: dict):
    """Submit a review for an order."""
    engine = _get_marketplace()
    listing_id = data.get("listing_id")  # maps to order_id in engine
    reviewer_id = data.get("reviewer_id")
    rating = data.get("rating", 5)
    body = data.get("body", "")
    if not listing_id or not reviewer_id:
        raise HTTPException(status_code=400, detail="listing_id and reviewer_id are required")
    success, msg = await engine.submit_review(
        order_id=listing_id,
        reviewer_id=reviewer_id,
        rating=int(rating),
        description=body,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True}
