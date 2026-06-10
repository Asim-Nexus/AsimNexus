import logging

from fastapi import APIRouter

logger = logging.getLogger("AsimNexus.API.Economy")

router = APIRouter()

def register_economy_routes(app):
    """Register all economy + identity/DID routes on a FastAPI app."""
    # Add rate limiting middleware to the app
    try:
        from core.rate_limiter_middleware import RateLimiterMiddleware
        app.add_middleware(RateLimiterMiddleware)
        logger.info("✅ RateLimiterMiddleware registered on economy API")
    except Exception as e:
        logger.warning(f"⚠️ RateLimiterMiddleware skipped: {e}")

    app.include_router(router)
    logger.info("✅ Economy + Identity/DID routes registered")
    return app

# Legacy economy modules (original core.economy.*)
from . import contracts, credits, identity, did
from . import hybrid_economy_api
from . import reputation_api
from . import task_bus_api
from . import token_bridge_api
from . import marketplace_engine_api  # wraps core.economy.marketplace_engine
from . import marketplace_api           # wraps economy.marketplace (new engine)

# New economy modules (economy/ package: wallet, tokens, escrow, staking)
from . import wallet_api
from . import token_api
from . import escrow_api
from . import staking_api

# Governance modules
from . import governance_api


def register_governance_routes(app):
    """Register all governance routes on a FastAPI app."""
    from fastapi import APIRouter

    gov_router = APIRouter()
    app.include_router(governance_api.router)
    logger.info("✅ Governance routes registered")
    return app
