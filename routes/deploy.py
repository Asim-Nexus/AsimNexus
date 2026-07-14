"""
Deploy Routes
=============
Endpoints for deployment releases, status, and targets.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Deploy"])

logger = logging.getLogger("AsimNexus.Routes.Deploy")

deploy_manager = None

def init_deploy(app_globals: dict) -> None:
    global deploy_manager
    deploy_manager = app_globals.get("deploy_manager")

@router.get("/api/deploy/releases")
async def deploy_releases():
    """List all deployment releases."""
    try:
        if deploy_manager:
            data = await deploy_manager.list_releases()
            return ok(data=data)
        return ok(data={"releases": [], "count": 0})
    except Exception as e:
        logger.error(f"deploy_releases error: {e}")
        return error(str(e))

@router.get("/api/deploy/status")
async def deploy_status():
    """Get deployment system status."""
    try:
        if deploy_manager:
            data = await deploy_manager.get_status()
            return ok(data=data)
        return ok(data={"status": "active", "last_deploy": None})
    except Exception as e:
        logger.error(f"deploy_status error: {e}")
        return error(str(e))

@router.get("/api/deploy/targets")
async def deploy_targets():
    """List deployment targets."""
    try:
        if deploy_manager:
            data = await deploy_manager.list_targets()
            return ok(data=data)
        return ok(data={"targets": [], "count": 0})
    except Exception as e:
        logger.error(f"deploy_targets error: {e}")
        return error(str(e))
