from typing import Dict, Any, Optional, List

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_marketplace = None
def _get_mp():
    global _marketplace
    if _marketplace is None:
        try:
            from core.economy.marketplace_engine import get_marketplace
            _marketplace = get_marketplace()
            logger.info("MarketplaceEngine loaded")
        except Exception as e:
            logger.warning(f"MarketplaceEngine unavailable: {e}")
    return _marketplace


class CreateListingRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    category: str = "other"
    price: float = Field(default=0.0, ge=0)
    currency: str = "SVT"
    quantity: int = Field(default=1, ge=1)
    tags: List[str] = Field(default_factory=list)
    media_urls: List[str] = Field(default_factory=list)
    delivery_type: str = "digital"
    location: str = "virtual"
    universe_scope: str = "global"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateListingRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    quantity: Optional[int] = None
    tags: Optional[List[str]] = None
    media_urls: Optional[List[str]] = None
    delivery_type: Optional[str] = None
    location: Optional[str] = None
    universe_scope: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AddToCartRequest(BaseModel):
    listing_id: str
    quantity: int = Field(default=1, ge=1)


class UpdateCartItemRequest(BaseModel):
    listing_id: str
    quantity: int = Field(..., ge=0)


class CheckoutRequest(BaseModel):
    payment_method: str = "svt"
    delivery_notes: str = ""
    shipping_address: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessPaymentRequest(BaseModel):
    payment_tx_id: str


class AddReviewRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: str = ""
    body: str = ""


class DisputeRequest(BaseModel):
    reason: str = ""


# ── LISTINGS ────────────────────────────────────────────────────────────────

@router.post("/api/marketplace/listings")
async def create_listing(req: CreateListingRequest, seller_id: str = Query(...)):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.create_listing(
        seller_id=seller_id,
        title=req.title,
        description=req.description,
        category=req.category,
        price=req.price,
        currency=req.currency,
        quantity=req.quantity,
        tags=req.tags,
        media_urls=req.media_urls,
        delivery_type=req.delivery_type,
        location=req.location,
        universe_scope=req.universe_scope,
        metadata=req.metadata,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Create failed"))
    return result


@router.get("/api/marketplace/listings")
async def list_listings(
    category: Optional[str] = Query(None),
    status: str = Query("active"),
    seller_id: Optional[str] = Query(None),
    universe_scope: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    tag_list = tags.split(",") if tags else None
    return mp.list_listings(
        category=category,
        status=status,
        seller_id=seller_id,
        universe_scope=universe_scope,
        min_price=min_price,
        max_price=max_price,
        search=search,
        tags=tag_list,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/api/marketplace/listings/{listing_id}")
async def get_listing(listing_id: str):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    listing = mp.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.put("/api/marketplace/listings/{listing_id}")
async def update_listing(listing_id: str, req: UpdateListingRequest, seller_id: str = Query(...)):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    updates = {k: v for k, v in req.dict(exclude_unset=True).items() if v is not None}
    result = mp.update_listing(listing_id, seller_id, **updates)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Update failed"))
    return result


@router.post("/api/marketplace/listings/{listing_id}/pause")
async def pause_listing(listing_id: str, seller_id: str = Query(...)):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.pause_listing(listing_id, seller_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Pause failed"))
    return result


@router.post("/api/marketplace/listings/{listing_id}/activate")
async def activate_listing(listing_id: str, seller_id: str = Query(...)):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.activate_listing(listing_id, seller_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Activate failed"))
    return result


@router.post("/api/marketplace/listings/{listing_id}/cancel")
async def cancel_listing(listing_id: str, seller_id: str = Query(...)):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.cancel_listing(listing_id, seller_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cancel failed"))
    return result


# ── CART ────────────────────────────────────────────────────────────────────

@router.get("/api/marketplace/cart/{user_id}")
async def get_cart(user_id: str):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    return mp.get_cart(user_id)


@router.post("/api/marketplace/cart/{user_id}/add")
async def add_to_cart(user_id: str, req: AddToCartRequest):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.add_to_cart(user_id, req.listing_id, req.quantity)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Add to cart failed"))
    return result


@router.post("/api/marketplace/cart/{user_id}/remove")
async def remove_from_cart(user_id: str, listing_id: str = Query(...)):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    return mp.remove_from_cart(user_id, listing_id)


@router.post("/api/marketplace/cart/{user_id}/update")
async def update_cart_item(user_id: str, req: UpdateCartItemRequest):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.update_cart_item(user_id, req.listing_id, req.quantity)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Update cart failed"))
    return result


@router.post("/api/marketplace/cart/{user_id}/clear")
async def clear_cart(user_id: str):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    return mp.clear_cart(user_id)


@router.post("/api/marketplace/cart/{user_id}/checkout")
async def checkout(user_id: str, req: CheckoutRequest):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.checkout(
        user_id=user_id,
        payment_method=req.payment_method,
        delivery_notes=req.delivery_notes,
        shipping_address=req.shipping_address,
        metadata=req.metadata,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Checkout failed"))
    return result


# ── ORDERS ──────────────────────────────────────────────────────────────────

@router.get("/api/marketplace/orders")
async def list_orders(
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    listing_id: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    return mp.list_orders(user_id=user_id, status=status, listing_id=listing_id,
                          role=role, limit=limit, offset=offset)


@router.get("/api/marketplace/orders/{order_id}")
async def get_order(order_id: str):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    order = mp.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/api/marketplace/orders/{order_id}/pay")
async def process_payment(order_id: str, req: ProcessPaymentRequest):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.process_payment(order_id, req.payment_tx_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Payment failed"))
    return result


@router.post("/api/marketplace/orders/{order_id}/fulfill")
async def fulfill_order(order_id: str, seller_id: str = Query(...)):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.fulfill_order(order_id, seller_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Fulfill failed"))
    return result


@router.post("/api/marketplace/orders/{order_id}/complete")
async def complete_order(order_id: str, buyer_id: str = Query(...)):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.complete_order(order_id, buyer_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Complete failed"))
    return result


@router.post("/api/marketplace/orders/{order_id}/cancel")
async def cancel_order(order_id: str, user_id: str = Query(...)):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.cancel_order(order_id, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cancel failed"))
    return result


@router.post("/api/marketplace/orders/{order_id}/dispute")
async def dispute_order(order_id: str, user_id: str = Query(...), req: DisputeRequest = None):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    reason = req.reason if req else ""
    result = mp.dispute_order(order_id, user_id, reason)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Dispute failed"))
    return result


@router.post("/api/marketplace/orders/{order_id}/refund")
async def refund_order(order_id: str, resolver_id: str = Query(...)):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    result = mp.refund_order(order_id, resolver_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Refund failed"))
    return result


# ── REVIEWS ─────────────────────────────────────────────────────────────────

@router.post("/api/marketplace/orders/{order_id}/review")
async def add_review(order_id: str, reviewer_id: str = Query(...), req: AddReviewRequest = None):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    rating = req.rating if req else 5
    title = req.title if req else ""
    body = req.body if req else ""
    result = mp.add_review(order_id, reviewer_id, rating, title, body)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Review failed"))
    return result


@router.get("/api/marketplace/reviews")
async def list_reviews(
    listing_id: Optional[str] = Query(None),
    reviewer_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    return mp.list_reviews(listing_id=listing_id, reviewer_id=reviewer_id, limit=limit, offset=offset)


# ── STATS ───────────────────────────────────────────────────────────────────

@router.get("/api/marketplace/stats")
async def marketplace_stats():
    mp = _get_mp()
    if not mp:
        raise HTTPException(status_code=503, detail="Marketplace not available")
    return mp.marketplace_stats()
