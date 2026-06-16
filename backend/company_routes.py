"""
STATUS: REAL — Company API routes backend integration

AsimNexus Company API Backend
===============================
Integrates with core.api.company_routes for 49% Enterprise mode.
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("AsimNexus.CompanyBackend")

def setup_company_routes(app):
    """Register company API routes"""
    try:
        from core.api.company_routes import router as company_router
        app.include_router(company_router)
        logger.info("✅ Company routes registered: /api/v1/company/*")
    except Exception as e:
        logger.warning(f"⚠️ Company routes fallback: {e}")