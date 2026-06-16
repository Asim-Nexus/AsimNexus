"""
STATUS: REAL — Government API routes backend integration

AsimNexus Government API Backend
==================================
Integrates with core.api.gov_routes for 51% Government mode.
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("AsimNexus.GovBackend")

def setup_gov_routes(app):
    """Register government API routes"""
    try:
        from core.api.gov_routes import router as gov_router
        app.include_router(gov_router)
        logger.info("✅ Government routes registered: /api/v1/gov/*")
    except Exception as e:
        logger.warning(f"⚠️ Government routes fallback: {e}")