"""
STATUS: REAL — Sector Routes Backend Integration

AsimNexus Sector Routes Backend
=================================
Integrates all sector connectors for Nepal Digital Ecosystem.
"""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger("AsimNexus.SectorBackend")


def setup_sector_routes(app):
    """Register all sector connector routes"""
    sector_router = APIRouter(prefix="/api/v1/sector", tags=["sectors"])
    
    # Agriculture
    @sector_router.get("/agriculture")
    async def agriculture_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("agriculture")
        return connector.status() if connector else {"error": "Not available"}
    
    # Tourism
    @sector_router.get("/tourism")
    async def tourism_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("tourism")
        return connector.status() if connector else {"error": "Not available"}
    
    # Banking
    @sector_router.get("/banking")
    async def banking_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("banking")
        return connector.status() if connector else {"error": "Not available"}
    
    # Telecom
    @sector_router.get("/telecom")
    async def telecom_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("telecom")
        return connector.status() if connector else {"error": "Not available"}
    
    # Fintech
    @sector_router.get("/fintech")
    async def fintech_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("fintech")
        return connector.status() if connector else {"error": "Not available"}
    
    # ISP
    @sector_router.get("/isp")
    async def isp_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("isp")
        return connector.status() if connector else {"error": "Not available"}
    
    # Hydropower
    @sector_router.get("/hydropower")
    async def hydropower_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("hydropower")
        return connector.status() if connector else {"error": "Not available"}
    
    # Education
    @sector_router.get("/education")
    async def education_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("education")
        return connector.status() if connector else {"error": "Not available"}
    
    # Health
    @sector_router.get("/health")
    async def health_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("health")
        return connector.status() if connector else {"error": "Not available"}
    
    # Government
    @sector_router.get("/government")
    async def government_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("government")
        return connector.status() if connector else {"error": "Not available"}
    
    # E-commerce
    @sector_router.get("/ecommerce")
    async def ecommerce_status():
        from connectors.sector_connectors import get_sector_connector
        connector = get_sector_connector("ecommerce")
        return connector.status() if connector else {"error": "Not available"}
    
    app.include_router(sector_router)
    logger.info("✅ Sector routes registered: /api/v1/sector/*")