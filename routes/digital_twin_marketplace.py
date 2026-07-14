"""
Digital Twin Marketplace API Routes — Give Work & Do Work
==========================================================

REST API endpoints for the Digital Twin Marketplace where:
  - Every person's Digital Twin/Clone can offer services
  - Work types: coding, video, music, design, and any digital service
  - 5/15/30 day contracts with 3-confirmation
  - Escrow system for secure payments
  - Reputation staking for quality signaling

Integrates with:
  - core/marketplace/digital_twin_marketplace.py — Core marketplace logic
  - core/nexus_connector.py — Mode routing and cross-consent
  - core/security/mode_confirmation.py — 3-Confirmation system
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Digital Twin Marketplace"])

# ─── Singleton Reference ──────────────────────────────────────────────────────
_dtm = None


def init_digital_twin_marketplace(app_globals: dict) -> None:
    """Initialize the Digital Twin Marketplace singleton."""
    global _dtm
    try:
        from core.marketplace.digital_twin_marketplace import get_digital_twin_marketplace
        _dtm = get_digital_twin_marketplace()
        logger.info("Digital Twin Marketplace initialized")
    except Exception as e:
        logger.warning(f"Digital Twin Marketplace not available: {e}")


def _get_dtm():
    """Get the marketplace instance."""
    if _dtm is None:
        try:
            from core.marketplace.digital_twin_marketplace import get_digital_twin_marketplace
            globals()["_dtm"] = get_digital_twin_marketplace()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Marketplace unavailable: {e}")
    return _dtm


# ─── Request Models ───────────────────────────────────────────────────────────

class CreateListingRequest(BaseModel):
    user_id: str
    twin_id: str
    mode: str = "citizen"
    title: str
    description: str
    category: str = "custom"
    agent_mode: str = "private"
    skills: List[str] = []
    portfolio: List[str] = []
    price_min: float = 0.0
    price_max: float = 0.0
    currency: str = "NPR"


class ProposeContractRequest(BaseModel):
    listing_id: str
    client_id: str
    title: str
    description: str
    tier: str = "trial"
    price: float = 0.0
    currency: str = "NPR"
    milestones: List[Dict[str, Any]] = []
    confirmation_level: str = "level_1"


class ConfirmContractRequest(BaseModel):
    user_id: str
    confirmation_data: Optional[Dict[str, Any]] = None


class CompleteContractRequest(BaseModel):
    user_id: str
    deliverables: List[str] = []


class CancelContractRequest(BaseModel):
    user_id: str
    reason: str = ""


class DisputeContractRequest(BaseModel):
    user_id: str
    reason: str


class ResolveDisputeRequest(BaseModel):
    resolver_id: str
    resolution: str  # "release", "refund", "partial"
    partial_amount: float = 0.0


class RateContractRequest(BaseModel):
    user_id: str
    rating: float


class StakeReputationRequest(BaseModel):
    user_id: str
    amount: float


# ─── Listing Endpoints ────────────────────────────────────────────────────────

@router.post("/api/dtm/listings")
async def create_listing(req: CreateListingRequest):
    """Create a new Digital Twin service listing."""
    try:
        dtm = _get_dtm()
        from core.marketplace.digital_twin_marketplace import WorkCategory, AgentMode
        listing = dtm.create_listing(
            user_id=req.user_id,
            twin_id=req.twin_id,
            mode=req.mode,
            title=req.title,
            description=req.description,
            category=WorkCategory(req.category) if hasattr(WorkCategory, req.category.upper()) else WorkCategory.CUSTOM,
            agent_mode=AgentMode(req.agent_mode) if hasattr(AgentMode, req.agent_mode.upper()) else AgentMode.PRIVATE,
            skills=req.skills,
            portfolio=req.portfolio,
            price_min=req.price_min,
            price_max=req.price_max,
            currency=req.currency,
        )
        return {"success": True, "data": listing.to_dict()}
    except Exception as e:
        logger.error(f"Failed to create listing: {e}")
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/listings/{listing_id}/publish")
async def publish_listing(listing_id: str, user_id: str = Body(..., embed=True)):
    """Publish a listing (DRAFT → ACTIVE)."""
    try:
        dtm = _get_dtm()
        result = dtm.publish_listing(listing_id, user_id)
        if result:
            return {"success": True, "data": {"listing_id": listing_id, "status": "active"}}
        return {"success": False, "error": "Cannot publish listing"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.put("/api/dtm/listings/{listing_id}")
async def update_listing(listing_id: str, data: dict = Body(...)):
    """Update a listing."""
    try:
        dtm = _get_dtm()
        user_id = data.pop("user_id", None)
        if not user_id:
            return {"success": False, "error": "user_id required"}
        listing = dtm.update_listing(listing_id, user_id, **data)
        if listing:
            return {"success": True, "data": listing.to_dict()}
        return {"success": False, "error": "Listing not found or unauthorized"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/listings/{listing_id}/pause")
async def pause_listing(listing_id: str, user_id: str = Body(..., embed=True)):
    """Pause a listing."""
    try:
        dtm = _get_dtm()
        result = dtm.pause_listing(listing_id, user_id)
        return {"success": result, "data": {"listing_id": listing_id, "status": "paused" if result else "error"}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/listings/{listing_id}/activate")
async def activate_listing(listing_id: str, user_id: str = Body(..., embed=True)):
    """Activate a paused listing."""
    try:
        dtm = _get_dtm()
        result = dtm.activate_listing(listing_id, user_id)
        return {"success": result, "data": {"listing_id": listing_id, "status": "active" if result else "error"}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/listings/{listing_id}/archive")
async def archive_listing(listing_id: str, user_id: str = Body(..., embed=True)):
    """Archive a listing."""
    try:
        dtm = _get_dtm()
        result = dtm.archive_listing(listing_id, user_id)
        return {"success": result, "data": {"listing_id": listing_id, "status": "archived" if result else "error"}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/dtm/listings/{listing_id}")
async def get_listing(listing_id: str):
    """Get listing details."""
    try:
        dtm = _get_dtm()
        listing = dtm.get_listing(listing_id)
        if listing:
            return {"success": True, "data": listing.to_dict()}
        return {"success": False, "error": "Listing not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/dtm/listings")
async def search_listings(
    category: str = "",
    query: str = "",
    min_price: float = 0,
    max_price: float = 0,
    mode: str = "",
    agent_mode: str = "",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Search for active listings."""
    try:
        dtm = _get_dtm()
        listings, total = dtm.search_listings(
            category=category or None,
            query=query or None,
            min_price=min_price,
            max_price=max_price,
            mode=mode or None,
            agent_mode=agent_mode or None,
            page=page,
            limit=limit,
        )
        return {
            "success": True,
            "data": {
                "listings": [l.to_dict() for l in listings],
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/dtm/user/{user_id}/listings")
async def get_user_listings(user_id: str, status: str = ""):
    """Get all listings for a user."""
    try:
        dtm = _get_dtm()
        listings = dtm.get_user_listings(user_id, status or None)
        return {"success": True, "data": {"listings": [l.to_dict() for l in listings]}}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Contract Endpoints ───────────────────────────────────────────────────────

@router.post("/api/dtm/contracts/propose")
async def propose_contract(req: ProposeContractRequest):
    """Propose a new work contract."""
    try:
        dtm = _get_dtm()
        from core.marketplace.digital_twin_marketplace import ContractTier, ConfirmationLevel
        contract = dtm.propose_contract(
            listing_id=req.listing_id,
            client_id=req.client_id,
            title=req.title,
            description=req.description,
            tier=ContractTier(req.tier) if hasattr(ContractTier, req.tier.upper()) else ContractTier.TRIAL,
            price=req.price,
            currency=req.currency,
            milestones=req.milestones,
            confirmation_level=ConfirmationLevel(req.confirmation_level) if hasattr(ConfirmationLevel, req.confirmation_level.upper()) else ConfirmationLevel.LEVEL_1,
        )
        if contract:
            return {"success": True, "data": contract.to_dict()}
        return {"success": False, "error": "Cannot propose contract (listing may not be active)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/contracts/{contract_id}/confirm")
async def confirm_contract(contract_id: str, req: ConfirmContractRequest):
    """Confirm a contract with 3-confirmation."""
    try:
        dtm = _get_dtm()
        result = dtm.confirm_contract(contract_id, req.user_id, req.confirmation_data)
        return {"success": result, "data": {"contract_id": contract_id, "status": "confirmed" if result else "pending"}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/contracts/{contract_id}/complete")
async def complete_contract(contract_id: str, req: CompleteContractRequest):
    """Complete a contract (agent submits deliverables)."""
    try:
        dtm = _get_dtm()
        result = dtm.complete_contract(contract_id, req.user_id, req.deliverables)
        return {"success": result, "data": {"contract_id": contract_id, "status": "completed" if result else "error"}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/contracts/{contract_id}/cancel")
async def cancel_contract(contract_id: str, req: CancelContractRequest):
    """Cancel a contract."""
    try:
        dtm = _get_dtm()
        result = dtm.cancel_contract(contract_id, req.user_id, req.reason)
        return {"success": result, "data": {"contract_id": contract_id, "status": "cancelled" if result else "error"}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/contracts/{contract_id}/dispute")
async def dispute_contract(contract_id: str, req: DisputeContractRequest):
    """Raise a dispute on a contract."""
    try:
        dtm = _get_dtm()
        result = dtm.dispute_contract(contract_id, req.user_id, req.reason)
        return {"success": result, "data": {"contract_id": contract_id, "status": "disputed" if result else "error"}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/contracts/{contract_id}/resolve")
async def resolve_dispute(contract_id: str, req: ResolveDisputeRequest):
    """Resolve a dispute."""
    try:
        dtm = _get_dtm()
        result = dtm.resolve_dispute(contract_id, req.resolver_id, req.resolution, req.partial_amount)
        return {"success": result, "data": {"contract_id": contract_id, "resolution": req.resolution}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/contracts/{contract_id}/rate")
async def rate_contract(contract_id: str, req: RateContractRequest):
    """Rate a completed contract (1-5 stars)."""
    try:
        dtm = _get_dtm()
        result = dtm.rate_contract(contract_id, req.user_id, req.rating)
        return {"success": result, "data": {"contract_id": contract_id, "rating": req.rating}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/dtm/contracts/{contract_id}")
async def get_contract(contract_id: str):
    """Get contract details."""
    try:
        dtm = _get_dtm()
        contract = dtm.get_contract(contract_id)
        if contract:
            return {"success": True, "data": contract.to_dict()}
        return {"success": False, "error": "Contract not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/dtm/user/{user_id}/contracts")
async def get_user_contracts(user_id: str, status: str = ""):
    """Get all contracts for a user."""
    try:
        dtm = _get_dtm()
        contracts = dtm.get_user_contracts(user_id, status or None)
        return {"success": True, "data": {"contracts": [c.to_dict() for c in contracts]}}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Escrow Endpoints ─────────────────────────────────────────────────────────

@router.get("/api/dtm/escrow/{escrow_id}")
async def get_escrow(escrow_id: str):
    """Get escrow transaction details."""
    try:
        dtm = _get_dtm()
        escrow = dtm.get_escrow(escrow_id)
        if escrow:
            return {"success": True, "data": escrow.to_dict()}
        return {"success": False, "error": "Escrow not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/dtm/contracts/{contract_id}/escrow")
async def get_contract_escrow(contract_id: str):
    """Get escrow for a contract."""
    try:
        dtm = _get_dtm()
        escrow = dtm.get_contract_escrow(contract_id)
        if escrow:
            return {"success": True, "data": escrow.to_dict()}
        return {"success": False, "error": "No escrow found for this contract"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Reputation Staking Endpoints ─────────────────────────────────────────────

@router.post("/api/dtm/listings/{listing_id}/stake")
async def stake_reputation(listing_id: str, req: StakeReputationRequest):
    """Stake reputation on a listing."""
    try:
        dtm = _get_dtm()
        result = dtm.stake_reputation(listing_id, req.user_id, req.amount)
        return {"success": result, "data": {"listing_id": listing_id, "staked": req.amount}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/dtm/listings/{listing_id}/unstake")
async def unstake_reputation(listing_id: str, req: StakeReputationRequest):
    """Unstake reputation from a listing."""
    try:
        dtm = _get_dtm()
        result = dtm.unstake_reputation(listing_id, req.user_id, req.amount)
        return {"success": result, "data": {"listing_id": listing_id, "unstaked": req.amount}}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Agent Mode Endpoints ─────────────────────────────────────────────────────

@router.get("/api/dtm/contracts/{contract_id}/agent-instructions")
async def get_agent_instructions(contract_id: str, user_id: str = Query(...)):
    """Get instructions for an agent's Digital Twin to start working."""
    try:
        dtm = _get_dtm()
        instructions = dtm.get_agent_instructions(contract_id, user_id)
        if instructions:
            return {"success": True, "data": instructions}
        return {"success": False, "error": "Cannot get instructions"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Status & Stats Endpoints ─────────────────────────────────────────────────

@router.get("/api/dtm/status")
async def dtm_status():
    """Get marketplace system status."""
    try:
        dtm = _get_dtm()
        return {"success": True, "data": dtm.get_status()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/dtm/stats")
async def dtm_stats():
    """Get comprehensive marketplace statistics."""
    try:
        dtm = _get_dtm()
        return {"success": True, "data": dtm.get_stats()}
    except Exception as e:
        return {"success": False, "error": str(e)}
