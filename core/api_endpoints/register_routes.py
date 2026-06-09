#!/usr/bin/env python3
"""
ASIMNEXUS Route Registration
=============================
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
