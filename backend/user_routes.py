"""
STATUS: REAL — Citizen API routes backend integration

AsimNexus Citizen API Backend
===============================
Integrates with core.api.user_routes for Local-First citizen mode.
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("AsimNexus.CitizenBackend")

def setup_user_routes(app):
    """Register citizen API routes"""
    try:
        from core.api.user_routes import router as user_router
        app.include_router(user_router)
        logger.info("✅ Citizen routes registered: /api/v1/user/*")
    except Exception as e:
        logger.warning(f"⚠️ Citizen routes fallback: {e}")