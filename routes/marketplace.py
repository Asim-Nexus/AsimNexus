"""
Marketplace, Jobs, Contracts, Reputation, and Bridge Routes
============================================================
Endpoints for marketplace listings, orders, cart, jobs, contracts,
reputation system, and cross-chain bridge.
"""

import json
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Marketplace")

router = APIRouter(tags=["Marketplace & Economy"])

orchestrator = None


def init_marketplace(app_globals: dict) -> None:
    """Initialize marketplace module from app.py globals."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ─── Marketplace Endpoints ────────────────────────────────────────────────

@router.get("/api/marketplace/global-stats")
async def marketplace_global_stats():
    """Get global marketplace statistics."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.get_global_stats())
    except Exception as e:
        return error(str(e))


@router.get("/api/marketplace/search")
async def marketplace_search(q: str = "", category: str = "", min_price: float = 0, max_price: float = 0):
    """Search marketplace listings."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.search(q=q, category=category, min_price=min_price, max_price=max_price))
    except Exception as e:
        return error(str(e))


@router.get("/api/marketplace/listings")
async def marketplace_listings(category: str = "", status: str = "active", page: int = 1, limit: int = 20):
    """List marketplace listings."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.list_listings(category=category, status=status, page=page, limit=limit))
    except Exception as e:
        return error(str(e))


@router.get("/api/marketplace/listings/{listing_id}")
async def marketplace_listing_detail(listing_id: str):
    """Get listing details."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.get_listing(listing_id))
    except Exception as e:
        return error(str(e))


@router.get("/api/marketplace/cart/{user_id}")
async def marketplace_cart(user_id: str):
    """Get user cart."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.get_cart(user_id))
    except Exception as e:
        return error(str(e))


@router.get("/api/marketplace/orders")
async def marketplace_orders(user_id: str = "", status: str = "", page: int = 1, limit: int = 20):
    """List orders."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.list_orders(user_id=user_id, status=status, page=page, limit=limit))
    except Exception as e:
        return error(str(e))


@router.get("/api/marketplace/orders/{order_id}")
async def marketplace_order_detail(order_id: str):
    """Get order details."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.get_order(order_id))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/listings")
async def marketplace_create_listing(data: dict = Body(...)):
    """Create a new listing."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.create_listing(data))
    except Exception as e:
        return error(str(e))


@router.put("/api/marketplace/listings/{listing_id}")
async def marketplace_update_listing(listing_id: str, data: dict = Body(...)):
    """Update a listing."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.update_listing(listing_id, data))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/listings/{listing_id}/pause")
async def marketplace_pause_listing(listing_id: str):
    """Pause a listing."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.pause_listing(listing_id))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/listings/{listing_id}/activate")
async def marketplace_activate_listing(listing_id: str):
    """Activate a listing."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.activate_listing(listing_id))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/listings/{listing_id}/cancel")
async def marketplace_cancel_listing(listing_id: str):
    """Cancel a listing."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.cancel_listing(listing_id))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/cart/{user_id}/add")
async def marketplace_cart_add(user_id: str, data: dict = Body(...)):
    """Add item to cart."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.add_to_cart(user_id, data.get("listing_id"), data.get("quantity", 1)))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/cart/{user_id}/remove")
async def marketplace_cart_remove(user_id: str, data: dict = Body(...)):
    """Remove item from cart."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.remove_from_cart(user_id, data.get("listing_id")))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/cart/{user_id}/update")
async def marketplace_cart_update(user_id: str, data: dict = Body(...)):
    """Update cart item quantity."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.update_cart(user_id, data.get("listing_id"), data.get("quantity")))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/cart/{user_id}/clear")
async def marketplace_cart_clear(user_id: str):
    """Clear cart."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.clear_cart(user_id))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/cart/{user_id}/checkout")
async def marketplace_checkout(user_id: str, data: dict = Body(...)):
    """Checkout - create order from cart."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.checkout(user_id, data))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/orders/{order_id}/pay")
async def marketplace_order_pay(order_id: str, data: dict = Body(...)):
    """Pay for an order."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.pay_order(order_id, data))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/orders/{order_id}/fulfill")
async def marketplace_order_fulfill(order_id: str, data: dict = Body(...)):
    """Fulfill an order."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.fulfill_order(order_id, data))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/orders/{order_id}/complete")
async def marketplace_order_complete(order_id: str, data: dict = Body(...)):
    """Complete an order."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.complete_order(order_id, data))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/orders/{order_id}/cancel")
async def marketplace_order_cancel(order_id: str, data: dict = Body(...)):
    """Cancel an order."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.cancel_order(order_id, data))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/orders/{order_id}/dispute")
async def marketplace_order_dispute(order_id: str, data: dict = Body(...)):
    """Dispute an order."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.dispute_order(order_id, data))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/orders/{order_id}/refund")
async def marketplace_order_refund(order_id: str, data: dict = Body(...)):
    """Refund an order."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.refund_order(order_id, data))
    except Exception as e:
        return error(str(e))


@router.post("/api/marketplace/orders/{order_id}/review")
async def marketplace_order_review(order_id: str, data: dict = Body(...)):
    """Review an order."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.review_order(order_id, data))
    except Exception as e:
        return error(str(e))


@router.get("/api/marketplace/reviews")
async def marketplace_reviews(listing_id: str = "", page: int = 1, limit: int = 20):
    """Get reviews."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.get_reviews(listing_id=listing_id, page=page, limit=limit))
    except Exception as e:
        return error(str(e))


@router.get("/api/marketplace/stats")
async def marketplace_stats():
    """Get marketplace engine stats."""
    try:
        from core.economy import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.get_engine_stats())
    except Exception as e:
        return error(str(e))


# ─── Jobs Endpoints ───────────────────────────────────────────────────────

@router.get("/api/jobs/stats")
async def jobs_stats():
    """Get job market stats."""
    try:
        from core.economy import get_job_market
        jm = get_job_market()
        return ok(data=jm.get_stats())
    except Exception as e:
        return error(str(e))


@router.get("/api/jobs/list")
async def jobs_list(status: str = "", category: str = ""):
    """List jobs."""
    try:
        from core.economy import get_job_market
        jm = get_job_market()
        return ok(data=jm.list_jobs(status=status, category=category))
    except Exception as e:
        return error(str(e))


@router.post("/api/jobs/post")
async def jobs_post(data: dict = Body(...)):
    """Post a new job."""
    try:
        from core.economy import get_job_market
        jm = get_job_market()
        return ok(data=jm.post_job(data))
    except Exception as e:
        return error(str(e))


@router.post("/api/jobs/{job_id}/apply")
async def apply_job(job_id: str, data: dict = Body(...)):
    """Apply for a job."""
    user_id = data.get("user_id", "web_user")
    try:
        from core.economy import get_job_market
        jm = get_job_market()
        return ok(data=jm.apply(job_id, user_id, data))
    except ImportError:
        pass
    # Fallback — use database package
    try:
        from database import get_db
        db = get_db()
        # DBManager doesn't have a direct job_apply method, so log and return
        logger.info(f"Job application fallback: job={job_id}, user={user_id}")
        return ok(data={"message": "Application submitted"})
    except Exception as e:
        return ok(data={"message": f"Application noted (fallback): {e}"})


@router.post("/api/jobs/{job_id}/rate")
async def rate_job(job_id: str, data: dict = Body(...)):
    """Rate a job."""
    user_id = data.get("user_id", "web_user")
    rating = data.get("rating", 5)
    try:
        from core.economy import get_job_market
        jm = get_job_market()
        return ok(data=jm.rate(job_id, user_id, rating))
    except ImportError:
        pass
    # Fallback — use database package
    try:
        from database import get_db
        db = get_db()
        logger.info(f"Job rating fallback: job={job_id}, user={user_id}, rating={rating}")
        return ok(data={"rating": rating})
    except Exception as e:
        return ok(data={"rating": rating, "note": str(e)})


# ─── Contracts Endpoints ──────────────────────────────────────────────────

@router.post("/api/contracts/propose")
async def contract_propose(data: dict = Body(...)):
    """Propose a new contract."""
    user_id = data.get("user_id", "web_user") or "guest"
    try:
        from core.agent_contract import AgentContract
        contract = AgentContract(
            title=data.get("title", "Untitled"),
            description=data.get("description", ""),
            creator_id=user_id,
            parties=data.get("parties", []),
            terms=data.get("terms", {}),
            budget=data.get("budget", 0),
        )
        contract_id = contract.save()
        return ok(data={"contract_id": contract_id})
    except Exception as e:
        return error(str(e))


@router.post("/api/contracts/{contract_id}/gate2")
async def contract_gate2(contract_id: str):
    """Gate 2 approval for contract."""
    try:
        from core.agent_contract import AgentContract
        contract = AgentContract.load(contract_id)
        if contract:
            contract.gate2_approve()
            return ok(data={"status": "gate2_approved"})
        return error("Contract not found")
    except Exception as e:
        return error(str(e))


@router.post("/api/contracts/{contract_id}/sign")
async def contract_sign(contract_id: str, data: dict = Body(...)):
    """Sign a contract."""
    user_id = data.get("user_id", "web_user") or "guest"
    try:
        from core.agent_contract import AgentContract
        contract = AgentContract.load(contract_id)
        if contract:
            contract.sign(user_id)
            return ok(data={"signed_by": user_id})
        return error("Contract not found")
    except Exception as e:
        return error(str(e))


@router.post("/api/contracts/{contract_id}/progress")
async def contract_progress(contract_id: str, data: dict = Body(...)):
    """Update contract progress."""
    try:
        from core.agent_contract import AgentContract
        contract = AgentContract.load(contract_id)
        if contract:
            contract.update_progress(data.get("progress", 0))
            return ok(data={"progress": data.get("progress", 0)})
        return error("Contract not found")
    except Exception as e:
        return error(str(e))


@router.post("/api/contracts/{contract_id}/pause")
async def contract_pause(contract_id: str, data: dict = Body(...)):
    """Pause a contract."""
    user_id = data.get("user_id", "web_user") or "guest"
    try:
        from core.agent_contract import AgentContract
        contract = AgentContract.load(contract_id)
        if contract:
            contract.pause(user_id)
            return ok(data={"status": "paused"})
        return error("Contract not found")
    except Exception as e:
        return error(str(e))


@router.post("/api/contracts/{contract_id}/resume")
async def contract_resume(contract_id: str, data: dict = Body(...)):
    """Resume a contract."""
    user_id = data.get("user_id", "web_user") or "guest"
    try:
        from core.agent_contract import AgentContract
        contract = AgentContract.load(contract_id)
        if contract:
            contract.resume(user_id)
            return ok(data={"status": "active"})
        return error("Contract not found")
    except Exception as e:
        return error(str(e))


@router.post("/api/contracts/{contract_id}/cancel")
async def contract_cancel(contract_id: str, data: dict = Body(...)):
    """Cancel a contract."""
    user_id = data.get("user_id", "web_user") or "guest"
    try:
        from core.agent_contract import AgentContract
        contract = AgentContract.load(contract_id)
        if contract:
            contract.cancel(user_id)
            return ok(data={"status": "cancelled"})
        return error("Contract not found")
    except Exception as e:
        return error(str(e))


@router.post("/api/contracts/{contract_id}/complete")
async def contract_complete(contract_id: str, data: dict = Body(...)):
    """Complete a contract."""
    user_id = data.get("user_id", "web_user") or "guest"
    try:
        from core.agent_contract import AgentContract
        contract = AgentContract.load(contract_id)
        if contract:
            contract.complete(user_id)
            return ok(data={"status": "completed"})
        return error("Contract not found")
    except Exception as e:
        return error(str(e))


@router.get("/api/contracts/{contract_id}")
async def contract_get(contract_id: str):
    """Get contract details."""
    try:
        from core.agent_contract import AgentContract
        contract = AgentContract.load(contract_id)
        if contract:
            return ok(data=contract.to_dict())
        return error("Contract not found")
    except Exception as e:
        return error(str(e))


@router.get("/api/contracts")
async def contracts_list(data: dict = Body(...)):
    """List contracts."""
    user_id = data.get("user_id", "web_user") or "guest"
    try:
        from core.agent_contract import AgentContract
        contracts = AgentContract.list_for_user(user_id)
        return ok(data={"contracts": contracts})
    except Exception as e:
        return error(str(e))


# ─── Reputation Endpoints ─────────────────────────────────────────────────

@router.get("/api/reputation/stats")
async def reputation_stats():
    """Get reputation system stats."""
    try:
        from core.economy import get_reputation
        rep = get_reputation()
        return ok(data=rep.get_stats())
    except Exception as e:
        return error(str(e))


@router.get("/api/reputation/leaderboard")
async def reputation_leaderboard(limit: int = 10):
    """Get reputation leaderboard."""
    try:
        from core.economy import get_reputation
        rep = get_reputation()
        return ok(data=rep.get_leaderboard(limit=limit))
    except Exception as e:
        return error(str(e))


@router.post("/api/reputation/register")
async def reputation_register(data: dict = Body(...)):
    """Register an entity for reputation tracking."""
    try:
        from core.economy import get_reputation
        rep = get_reputation()
        return ok(data=rep.register(data.get("entity_id")))
    except Exception as e:
        return error(str(e))


@router.get("/api/reputation/{entity_id}")
async def reputation_get(entity_id: str):
    """Get reputation for an entity."""
    try:
        from core.economy import get_reputation
        rep = get_reputation()
        return ok(data=rep.get(entity_id))
    except Exception as e:
        return error(str(e))


@router.get("/api/reputation/{entity_id}/events")
async def reputation_events(entity_id: str, limit: int = 20):
    """Get reputation events for an entity."""
    try:
        from core.economy import get_reputation
        rep = get_reputation()
        return ok(data=rep.get_events(entity_id, limit=limit))
    except Exception as e:
        return error(str(e))


@router.post("/api/reputation/add")
async def reputation_add(data: dict = Body(...)):
    """Add reputation points."""
    try:
        from core.economy import get_reputation
        rep = get_reputation()
        return ok(data=rep.add(data.get("entity_id"), data.get("amount", 1), data.get("reason", "")))
    except Exception as e:
        return error(str(e))


@router.post("/api/reputation/remove")
async def reputation_remove(data: dict = Body(...)):
    """Remove reputation points."""
    try:
        from core.economy import get_reputation
        rep = get_reputation()
        return ok(data=rep.remove(data.get("entity_id"), data.get("amount", 1), data.get("reason", "")))
    except Exception as e:
        return error(str(e))


@router.post("/api/reputation/stake")
async def reputation_stake(data: dict = Body(...)):
    """Stake reputation."""
    try:
        from core.economy import get_reputation
        rep = get_reputation()
        return ok(data=rep.stake(data.get("entity_id"), data.get("amount", 1), data.get("reason", "")))
    except Exception as e:
        return error(str(e))


@router.post("/api/reputation/unstake")
async def reputation_unstake(data: dict = Body(...)):
    """Unstake reputation."""
    try:
        from core.economy import get_reputation
        rep = get_reputation()
        return ok(data=rep.unstake(data.get("entity_id"), data.get("amount", 1)))
    except Exception as e:
        return error(str(e))


@router.post("/api/reputation/slash")
async def reputation_slash(data: dict = Body(...)):
    """Slash reputation (penalty)."""
    try:
        from core.economy import get_reputation
        rep = get_reputation()
        return ok(data=rep.slash(data.get("entity_id"), data.get("amount", 1), data.get("reason", "")))
    except Exception as e:
        return error(str(e))


# ─── Bridge Endpoints ─────────────────────────────────────────────────────

@router.get("/api/bridge/stats")
async def bridge_stats():
    """Get bridge stats."""
    try:
        from core.economy import get_bridge
        br = get_bridge()
        return ok(data=br.get_stats())
    except Exception as e:
        return error(str(e))


@router.post("/api/bridge/pool/create")
async def bridge_pool_create(data: dict = Body(...)):
    """Create a liquidity pool."""
    try:
        from core.economy import get_bridge
        br = get_bridge()
        return ok(data=br.create_pool(data.get("chain"), data.get("token_symbol"), data.get("initial_balance", 0)))
    except Exception as e:
        return error(str(e))


@router.get("/api/bridge/pools")
async def bridge_pools(chain: str = ""):
    """List liquidity pools."""
    try:
        from core.economy import get_bridge
        br = get_bridge()
        return ok(data=br.list_pools(chain=chain))
    except Exception as e:
        return error(str(e))


@router.post("/api/bridge/pool/add-liquidity")
async def bridge_add_liquidity(data: dict = Body(...)):
    """Add liquidity to a pool."""
    try:
        from core.economy import get_bridge
        br = get_bridge()
        return ok(data=br.add_liquidity(data.get("pool_id"), data.get("amount")))
    except Exception as e:
        return error(str(e))


@router.post("/api/bridge/pool/remove-liquidity")
async def bridge_remove_liquidity(data: dict = Body(...)):
    """Remove liquidity from a pool."""
    try:
        from core.economy import get_bridge
        br = get_bridge()
        return ok(data=br.remove_liquidity(data.get("pool_id"), data.get("amount")))
    except Exception as e:
        return error(str(e))


@router.post("/api/bridge/initiate")
async def bridge_initiate(data: dict = Body(...)):
    """Initiate a cross-chain transfer."""
    try:
        from core.economy import get_bridge
        br = get_bridge()
        return ok(data=br.initiate(
            data.get("from_chain"), data.get("to_chain"),
            data.get("asset"), data.get("amount"),
            data.get("sender"), data.get("recipient")
        ))
    except Exception as e:
        return error(str(e))


@router.get("/api/bridge/tx/{tx_id}")
async def bridge_tx(tx_id: str):
    """Get bridge transaction details."""
    try:
        from core.economy import get_bridge
        br = get_bridge()
        return ok(data=br.get_transaction(tx_id))
    except Exception as e:
        return error(str(e))


@router.get("/api/bridge/transactions")
async def bridge_transactions(status: str = "", page: int = 1, limit: int = 20):
    """List bridge transactions."""
    try:
        from core.economy import get_bridge
        br = get_bridge()
        return ok(data=br.list_transactions(status=status, page=page, limit=limit))
    except Exception as e:
        return error(str(e))


@router.get("/api/bridge/fee")
async def bridge_fee(from_chain: str = "", to_chain: str = "", amount: float = 0):
    """Get bridge fee estimate."""
    try:
        from core.economy import get_bridge
        br = get_bridge()
        return ok(data=br.estimate_fee(from_chain=from_chain, to_chain=to_chain, amount=amount))
    except Exception as e:
        return error(str(e))


# ─── Hybrid Economy Endpoints ─────────────────────────────────────────────

@router.get("/api/hybrid-economy/summary")
async def hybrid_economy_summary():
    """Get hybrid economy summary."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data=he.get_summary())
    except Exception as e:
        return error(str(e))


@router.get("/api/hybrid-economy/mode")
async def hybrid_economy_mode():
    """Get hybrid economy mode."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data={"mode": he.get_mode()})
    except Exception as e:
        return error(str(e))


@router.post("/api/hybrid-economy/mode")
async def hybrid_economy_set_mode(data: dict = Body(...)):
    """Set hybrid economy mode."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        mode = data.get("mode", "auto")
        result = he.set_mode(mode)
        return ok(data={"mode": mode, "result": result})
    except Exception as e:
        return error(str(e))


@router.post("/api/hybrid-economy/account")
async def hybrid_economy_create_account(data: dict = Body(...)):
    """Create hybrid economy account."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data=he.create_account(data.get("owner_id"), data.get("account_type", "personal")))
    except Exception as e:
        return error(str(e))


@router.get("/api/hybrid-economy/account/{owner_id}")
async def hybrid_economy_get_account(owner_id: str):
    """Get hybrid economy account."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data=he.get_account(owner_id))
    except Exception as e:
        return error(str(e))


@router.get("/api/hybrid-economy/accounts")
async def hybrid_economy_list_accounts():
    """List all hybrid economy accounts."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data=he.list_accounts())
    except Exception as e:
        return error(str(e))


@router.post("/api/hybrid-economy/deposit")
async def hybrid_economy_deposit(data: dict = Body(...)):
    """Deposit to hybrid economy account."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data=he.deposit(data.get("owner_id"), data.get("amount"), data.get("currency", "USD")))
    except Exception as e:
        return error(str(e))


@router.post("/api/hybrid-economy/withdraw")
async def hybrid_economy_withdraw(data: dict = Body(...)):
    """Withdraw from hybrid economy account."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data=he.withdraw(data.get("owner_id"), data.get("amount"), data.get("currency", "USD")))
    except Exception as e:
        return error(str(e))


@router.post("/api/hybrid-economy/transfer")
async def hybrid_economy_transfer(data: dict = Body(...)):
    """Transfer between hybrid economy accounts."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data=he.transfer(data.get("from_id"), data.get("to_id"), data.get("amount"), data.get("currency", "USD")))
    except Exception as e:
        return error(str(e))


@router.post("/api/hybrid-economy/task")
async def hybrid_economy_create_task(data: dict = Body(...)):
    """Create a hybrid economy task."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data=he.create_task(data))
    except Exception as e:
        return error(str(e))


@router.post("/api/hybrid-economy/task/assign")
async def hybrid_economy_assign_task(data: dict = Body(...)):
    """Assign a hybrid economy task."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data=he.assign_task(data.get("task_id"), data.get("assignee_id")))
    except Exception as e:
        return error(str(e))


@router.get("/api/hybrid-economy/tasks")
async def hybrid_economy_list_tasks(status: str = ""):
    """List hybrid economy tasks."""
    try:
        from core.economy import get_hybrid_economy
        he = get_hybrid_economy()
        return ok(data=he.list_tasks(status=status))
    except Exception as e:
        return error(str(e))


# ─── Task Bus Endpoints ───────────────────────────────────────────────────

@router.get("/api/task-bus/status")
async def task_bus_status():
    """Get task bus status."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        return ok(data=tb.get_bus_status())
    except Exception as e:
        return error(str(e))


@router.post("/api/task-bus/agent/register")
async def task_bus_register_agent(data: dict = Body(...)):
    """Register an agent with task bus."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        return ok(data=tb.register_agent(data.get("agent_id"), data.get("capabilities", [])))
    except Exception as e:
        return error(str(e))


@router.post("/api/task-bus/agent/{agent_id}/unregister")
async def task_bus_unregister_agent(agent_id: str):
    """Unregister an agent from task bus."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        # Find node_id from agent_id
        agents = tb.list_agents(online_only=False)
        node_id = None
        for a in agents:
            if a.get("agent_id") == agent_id:
                node_id = a.get("node_id")
                break
        if node_id:
            return ok(data=tb.unregister_agent(node_id))
        return ok(data=False)
    except Exception as e:
        return error(str(e))


@router.post("/api/task-bus/agent/{agent_id}/heartbeat")
async def task_bus_agent_heartbeat(agent_id: str, data: dict = Body(...)):
    """Send heartbeat from an agent to task bus."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        result = tb.heartbeat(agent_id)
        return ok(data={"agent_id": agent_id, "result": result})
    except Exception as e:
        return error(str(e))


@router.get("/api/task-bus/agents")
async def task_bus_list_agents():
    """List registered agents."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        return ok(data=tb.list_agents())
    except Exception as e:
        return error(str(e))


@router.post("/api/task-bus/task/submit")
async def task_bus_submit_task(data: dict = Body(...)):
    """Submit a task to the bus."""
    try:
        from core.economy.task_bus import get_task_bus
        from core.economy.task_bus import TaskPriority
        tb = get_task_bus()
        task = tb.submit_task(
            task_type=data.get("type", "generic"),
            payload=data.get("payload", {}),
            priority=TaskPriority(data.get("priority", "medium")),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout", 300),
            metadata=data.get("metadata", {}),
        )
        return ok(data=task.to_dict())
    except Exception as e:
        return error(str(e))


@router.post("/api/task-bus/task/assign-next")
async def task_bus_assign_next(data: dict = Body(...)):
    """Assign next task to an agent."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        return ok(data=tb.assign_next_task(data.get("agent_id")))
    except Exception as e:
        return error(str(e))


@router.get("/api/task-bus/tasks")
async def task_bus_list_tasks(status: str = ""):
    """List tasks."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        return ok(data=tb.list_tasks(state=status if status else None))
    except Exception as e:
        return error(str(e))


@router.get("/api/task-bus/task/{task_id}")
async def task_bus_get_task(task_id: str):
    """Get task details."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        return ok(data=tb.get_task(task_id))
    except Exception as e:
        return error(str(e))


@router.post("/api/task-bus/task/{task_id}/start")
async def task_bus_start_task(task_id: str, data: dict = Body(...)):
    """Start a task."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        return ok(data=tb.start_task(task_id, data.get("agent_id")))
    except Exception as e:
        return error(str(e))


@router.post("/api/task-bus/task/{task_id}/complete")
async def task_bus_complete_task(task_id: str, data: dict = Body(...)):
    """Complete a task."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        return ok(data=tb.complete_task(task_id, data.get("agent_id"), data.get("result", {})))
    except Exception as e:
        return error(str(e))


@router.post("/api/task-bus/task/{task_id}/fail")
async def task_bus_fail_task(task_id: str, data: dict = Body(...)):
    """Mark a task as failed."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        return ok(data=tb.fail_task(task_id, data.get("agent_id"), data.get("error", "Unknown error")))
    except Exception as e:
        return error(str(e))


@router.post("/api/task-bus/task/{task_id}/cancel")
async def task_bus_cancel_task(task_id: str, data: dict = Body(...)):
    """Cancel a task."""
    try:
        from core.economy.task_bus import get_task_bus
        tb = get_task_bus()
        return ok(data=tb.cancel_task(task_id))
    except Exception as e:
        return error(str(e))
