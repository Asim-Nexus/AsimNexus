"""
PWA Configuration Routes
========================
Endpoints for Progressive Web App configuration.
"""

import logging
from fastapi import APIRouter
from routes.response import ok, error, unavailable

router = APIRouter(tags=["PWA"])

logger = logging.getLogger("AsimNexus.Routes.PWA")

pwa_manager = None


def init_pwa(app_globals: dict) -> None:
    global pwa_manager
    pwa_manager = app_globals.get("pwa_manager")


@router.get("/api/pwa/config")
async def pwa_config():
    """Get PWA configuration."""
    try:
        if pwa_manager:
            data = await pwa_manager.get_config()
            return ok(data=data)
        return ok(data={
            "name": "Asim Nexus",
            "short_name": "AsimNexus",
            "theme_color": "#1a1a2e",
            "background_color": "#16213e",
            "display": "standalone",
            "orientation": "portrait",
            "start_url": "/",
            "icons": [],
        })
    except Exception as e:
        logger.error(f"pwa_config error: {e}")
        return error(str(e))
