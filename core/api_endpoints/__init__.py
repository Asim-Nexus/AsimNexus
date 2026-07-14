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

    # Register economy API routers
    try:
        from .wallet_api import router as wallet_router
        app.include_router(wallet_router)
        logger.info("✅ Wallet API routes registered")
    except Exception as e:
        logger.warning(f"⚠️ Wallet API routes skipped: {e}")

    try:
        from .token_api import router as token_router
        app.include_router(token_router)
        logger.info("✅ Token API routes registered")
    except Exception as e:
        logger.warning(f"⚠️ Token API routes skipped: {e}")

    try:
        from .escrow_api import router as escrow_router
        app.include_router(escrow_router)
        logger.info("✅ Escrow API routes registered")
    except Exception as e:
        logger.warning(f"⚠️ Escrow API routes skipped: {e}")

    try:
        from .marketplace_api import router as marketplace_router
        app.include_router(marketplace_router)
        logger.info("✅ Marketplace API routes registered")
    except Exception as e:
        logger.warning(f"⚠️ Marketplace API routes skipped: {e}")

    try:
        from .staking_api import router as staking_router
        app.include_router(staking_router)
        logger.info("✅ Staking API routes registered")
    except Exception as e:
        logger.warning(f"⚠️ Staking API routes skipped: {e}")

    app.include_router(router)
    logger.info("✅ Economy + Identity/DID routes registered")
    return app


def register_governance_routes(app):
    """Register all governance routes on a FastAPI app."""
    from fastapi import APIRouter

    # Lazy import to avoid circular imports
    try:
        from .governance_api import router as gov_router
        app.include_router(gov_router)
        logger.info("✅ Governance routes registered")
    except Exception as e:
        logger.warning(f"⚠️ Governance routes skipped: {e}")

    return app
