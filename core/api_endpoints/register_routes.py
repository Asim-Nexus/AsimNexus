#!/usr/bin/env python3
"""
STATUS: REAL — AsimNexus Route Registration

AsimNexus Route Registration
============================
Central registration for all API route modules.
This is imported by simple_backend.py and other entry points.
"""

import logging

logger = logging.getLogger("AsimNexus.API.Register")


def register_all_routes(app):
    """Register all API route modules on a FastAPI app."""

    # ─── Core Routes ─────────────────────────────────────────────────────
    try:
        from core.api_endpoints import register_economy_routes, register_governance_routes
        register_economy_routes(app)
        register_governance_routes(app)
        logger.info("✅ Core economy + governance routes registered")
    except Exception as e:
        logger.warning("⚠️ Core route registration skipped: %s", e)

    # ─── Sector Routes ───────────────────────────────────────────────────
    try:
        from core.api_endpoints.sector_api import router as sector_router
        app.include_router(sector_router)
        logger.info("✅ Sector routes registered (hospital, hotel, education, banking)")
    except Exception as e:
        logger.warning("⚠️ Sector route registration skipped: %s", e)

    # ─── Real-Time Data Routes ─────────────────────────────────────────────
    try:
        from core.api.real_time_api import router as real_time_router
        app.include_router(real_time_router)
        logger.info("✅ Real-time API routes registered (weather, market, hydropower)")
    except Exception as e:
        logger.warning("⚠️ Real-time route registration skipped: %s", e)

    # ─── Core Kernel Routes ────────────────────────────────────────────────
    try:
        from core.api.core_kernel_api import router as core_kernel_router
        app.include_router(core_kernel_router)
        logger.info("✅ Core Kernel routes registered (hardware, os detection)")
    except Exception as e:
        logger.warning("⚠️ Core Kernel route registration skipped: %s", e)

    # ─── Global Agent Routes ─────────────────────────────────────────────
    try:
        from core.api_endpoints.global_agent_api import router as global_agent_router
        app.include_router(global_agent_router)
        logger.info("✅ Global Agent routes registered")
    except Exception as e:
        logger.warning("⚠️ Global Agent route registration skipped: %s", e)

    # ─── Hardening Routes ────────────────────────────────────────────────
    try:
        from core.api_endpoints.hardening_api import router as hardening_router
        app.include_router(hardening_router)
        logger.info("✅ Hardening routes registered")
    except Exception as e:
        logger.warning("⚠️ Hardening route registration skipped: %s", e)

    return app
