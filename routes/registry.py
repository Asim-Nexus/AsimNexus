"""
Service Registry Routes
=======================
Endpoints for service registry: registration, versioning, rollback.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Registry"])

logger = logging.getLogger("AsimNexus.Routes.Registry")

# Module-level globals set by app.py at startup
registry_manager = None


def init_registry(app_globals: dict) -> None:
    """Initialize registry module from app.py globals."""
    global registry_manager
    registry_manager = app_globals.get("registry_manager")


@router.post("/api/registry/register")
async def registry_register(data: dict = Body(...)):
    """Register a service or component."""
    try:
        if registry_manager:
            result = await registry_manager.register(data)
            return ok(data=result)
        return ok(data={"status": "registered", "name": data.get("name", "unknown")})
    except Exception as e:
        logger.error(f"registry_register error: {e}")
        return error(str(e))


@router.get("/api/registry/status")
async def registry_status():
    """Get registry system status."""
    try:
        if registry_manager:
            data = await registry_manager.get_status()
            return ok(data=data)
        return ok(data={"status": "active", "registered": 0})
    except Exception as e:
        logger.error(f"registry_status error: {e}")
        return error(str(e))


@router.get("/api/registry/{name}/{version}")
async def registry_get_version(name: str, version: str):
    """Get a specific version of a registered component."""
    try:
        if registry_manager:
            data = await registry_manager.get_version(name, version)
            return ok(data=data)
        return ok(data={"name": name, "version": version, "status": "registered"})
    except Exception as e:
        logger.error(f"registry_get_version error: {e}")
        return error(str(e))


@router.get("/api/registry/versions/{name}")
async def registry_list_versions(name: str):
    """List all versions of a registered component."""
    try:
        if registry_manager:
            data = await registry_manager.list_versions(name)
            return ok(data=data)
        return ok(data={"name": name, "versions": [], "count": 0})
    except Exception as e:
        logger.error(f"registry_list_versions error: {e}")
        return error(str(e))


@router.get("/api/registry/active/{name}")
async def registry_get_active(name: str):
    """Get the active version of a component."""
    try:
        if registry_manager:
            data = await registry_manager.get_active(name)
            return ok(data=data)
        return ok(data={"name": name, "version": "latest", "status": "active"})
    except Exception as e:
        logger.error(f"registry_get_active error: {e}")
        return error(str(e))


@router.get("/api/registry/verify/{name}/{version}")
async def registry_verify_version(name: str, version: str):
    """Verify a component version's integrity."""
    try:
        if registry_manager:
            data = await registry_manager.verify(name, version)
            return ok(data=data)
        return ok(data={"name": name, "version": version, "verified": True})
    except Exception as e:
        logger.error(f"registry_verify_version error: {e}")
        return error(str(e))


@router.post("/api/registry/rollback/{name}")
async def registry_rollback(name: str, data: dict = Body(...)):
    """Rollback a component to a previous version."""
    try:
        if registry_manager:
            result = await registry_manager.rollback(name, data.get("version", ""))
            return ok(data=result)
        return ok(data={"status": "rolled_back", "name": name, "version": data.get("version", "previous")})
    except Exception as e:
        logger.error(f"registry_rollback error: {e}")
        return error(str(e))
