"""
Nepal Connector Routes
======================
Endpoints for Nepal-specific data: ministries, provinces, districts,
banks, ISPs, schools, hospitals, palikas, hotels.
"""

import logging
from fastapi import APIRouter
from routes.response import ok, error

router = APIRouter(tags=["Nepal Connectors"])

logger = logging.getLogger("AsimNexus.Routes.Nepal")

# These globals are set by app.py at import time
MINISTRIES = {}
PROVINCES = {}
DISTRICTS = {}
BANKS = {}
ISPS = {}
UNIVERSITIES = {}
SCHOOLS = {}
HOSPITALS = {}
PALIKAS = {}
HOTELS = {}


def init_nepal_data(app_globals: dict) -> None:
    """Initialize Nepal connector data from app.py globals."""
    global MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS
    global UNIVERSITIES, SCHOOLS, HOSPITALS, PALIKAS, HOTELS
    MINISTRIES = app_globals.get("MINISTRIES", {})
    PROVINCES = app_globals.get("PROVINCES", {})
    DISTRICTS = app_globals.get("DISTRICTS", {})
    BANKS = app_globals.get("BANKS", {})
    ISPS = app_globals.get("ISPS", {})
    UNIVERSITIES = app_globals.get("UNIVERSITIES", {})
    SCHOOLS = app_globals.get("SCHOOLS", {})
    HOSPITALS = app_globals.get("HOSPITALS", {})
    PALIKAS = app_globals.get("PALIKAS", {})
    HOTELS = app_globals.get("HOTELS", {})


@router.get("/api/nepal/status")
async def nepal_status():
    """Get Nepal connector system status."""
    try:
        return ok(data={
            "status": "active",
            "region": "nepal",
            "connectors": {
                "ministries": len(MINISTRIES),
                "provinces": len(PROVINCES),
                "districts": len(DISTRICTS),
                "banks": len(BANKS),
                "isps": len(ISPS),
                "schools": len(SCHOOLS),
                "hospitals": len(HOSPITALS),
                "palikas": len(PALIKAS),
                "hotels": len(HOTELS),
            },
        })
    except Exception as e:
        logger.error(f"nepal_status error: {e}")
        return error(str(e))


@router.get("/api/v1/np/ministries")
async def ministries():
    return ok(data={"count": len(MINISTRIES), "ministries": [m for m in MINISTRIES.values()]})


@router.get("/api/v1/np/provinces")
async def provinces():
    return ok(data={"count": len(PROVINCES), "provinces": list(PROVINCES.values())})


@router.get("/api/v1/np/districts")
async def districts():
    return ok(data={"count": len(DISTRICTS), "districts": list(DISTRICTS.values())})


@router.get("/api/v1/np/banks")
async def banks():
    return ok(data={"count": len(BANKS), "banks": list(BANKS.values())})


@router.get("/api/v1/np/isps")
async def isps():
    return ok(data={"count": len(ISPS), "isps": list(ISPS.values())})


@router.get("/api/v1/education/universities")
async def universities():
    return ok(data={"count": len(UNIVERSITIES), "universities": list(UNIVERSITIES.values())})


@router.get("/api/v1/education/schools")
async def schools():
    return ok(data={"count": len(SCHOOLS), "schools": list(SCHOOLS.values())})


@router.get("/api/v1/health/hospitals")
async def hospitals():
    return ok(data={"count": len(HOSPITALS), "hospitals": list(HOSPITALS.values())})


@router.get("/api/v1/np/palikas")
async def palikas():
    return ok(data={"count": len(PALIKAS), "palikas": list(PALIKAS.values())[:50]})


@router.get("/api/v1/tourism/hotels")
async def hotels():
    return ok(data={"count": len(HOTELS), "hotels": list(HOTELS.values())})


@router.get("/api/nepal/status")
async def api_nepal_status():
    """Get Nepal system status."""
    try:
        return ok(data={
            "status": "operational",
            "region": "nepal",
            "features": ["ministries", "provinces", "districts", "gov-layer", "tourism"]
        })
    except Exception as e:
        logger.error(f"api_nepal_status error: {e}")
        return error(str(e))
