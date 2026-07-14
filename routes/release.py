"""
Release Routes
==============
Endpoints for release management.
"""

import logging
from fastapi import APIRouter
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Release"])

logger = logging.getLogger("AsimNexus.Routes.Release")

release_manager = None


def init_release(app_globals: dict) -> None:
    global release_manager
    release_manager = app_globals.get("release_manager")


@router.get("/api/release/current")
async def release_current():
    """Get current release information."""
    try:
        if release_manager:
            data = await release_manager.get_current()
            return ok(data=data)
        return ok(data={
            "version": "2.0.0",
            "build": "RC-2",
            "release_date": "2026-07-01",
            "status": "stable",
        })
    except Exception as e:
        logger.error(f"release_current error: {e}")
        return error(str(e))
