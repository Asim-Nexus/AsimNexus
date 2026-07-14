"""
AsimNexus Government Route Module
===================================
Government, e-Residency, tax, digital identity, and signature endpoints.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Government")

router = APIRouter(tags=["Government"])

# Module-level globals (set via init_government)
orchestrator = None


def init_government(app_globals: dict) -> None:
    """Initialize government module with shared app state."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ─── Government Status ───────────────────────────────────────────────────────


@router.get("/api/government/status")
async def government_status():
    """Get government integration status"""
    try:
        from core.government import (
            get_government_manager, GovernmentStatus
        )
        gm = get_government_manager()
        status = gm.get_status()
        return ok(data={
            "status": status.value if hasattr(status, 'value') else str(status),
            "identity_countries": gm.get_identity_countries_count(),
            "eresidency_programs": gm.get_eresidency_programs_count(),
            "tax_countries": gm.get_tax_countries_count(),
            "signature_regions": gm.get_signature_regions_count(),
            "active_identities": gm.get_active_identities_count()
        })
    except Exception as e:
        logger.error(f"Government status error: {e}")
        return error(str(e))


# ─── Digital Identity ────────────────────────────────────────────────────────


@router.get("/api/government/identity/countries")
async def identity_countries():
    """Get countries with e-ID support"""
    try:
        from core.government import get_government_manager
        gm = get_government_manager()
        countries = gm.get_identity_countries()
        return ok(data={
            "countries": countries,
            "count": len(countries)
        })
    except Exception as e:
        logger.error(f"Identity countries error: {e}")
        return error(str(e))


@router.post("/api/government/identity/create")
async def create_identity(data: dict = Body(...)):
    """Create digital identity"""
    try:
        from core.government import get_government_manager
        gm = get_government_manager()
        identity = gm.create_identity(
            user_id=data.get("user_id"),
            country=data.get("country", "NP"),
            identity_type=data.get("identity_type", "basic"),
            metadata=data.get("metadata", {})
        )
        return ok(data=identity)
    except Exception as e:
        logger.error(f"Create identity error: {e}")
        return error(str(e))


@router.post("/api/government/identity/verify")
async def verify_identity(data: dict = Body(...)):
    """Verify identity to a level"""
    try:
        from core.government import get_government_manager
        gm = get_government_manager()
        result = gm.verify_identity(
            identity_id=data.get("identity_id"),
            verification_level=data.get("level", 1),
            documents=data.get("documents", [])
        )
        return ok(data=result)
    except Exception as e:
        logger.error(f"Verify identity error: {e}")
        return error(str(e))


# ─── e-Residency ─────────────────────────────────────────────────────────────


@router.get("/api/government/eresidency/programs")
async def eresidency_programs():
    """Get available e-Residency programs"""
    try:
        from core.government import get_government_manager
        gm = get_government_manager()
        programs = gm.get_eresidency_programs()
        return ok(data={
            "programs": programs,
            "count": len(programs)
        })
    except Exception as e:
        logger.error(f"e-Residency programs error: {e}")
        return error(str(e))


@router.post("/api/government/eresidency/apply")
async def apply_eresidency(data: dict = Body(...)):
    """Apply for e-Residency"""
    try:
        from core.government import get_government_manager
        gm = get_government_manager()
        application = gm.apply_eresidency(
            user_id=data.get("user_id"),
            program_id=data.get("program_id"),
            documents=data.get("documents", []),
            reason=data.get("reason", "")
        )
        return ok(data=application)
    except Exception as e:
        logger.error(f"Apply e-Residency error: {e}")
        return error(str(e))


# ─── Tax ─────────────────────────────────────────────────────────────────────


@router.get("/api/government/tax/countries")
async def tax_countries():
    """Get countries with tax filing support"""
    try:
        from core.government import get_government_manager
        gm = get_government_manager()
        countries = gm.get_tax_countries()
        return ok(data={
            "countries": countries,
            "count": len(countries)
        })
    except Exception as e:
        logger.error(f"Tax countries error: {e}")
        return error(str(e))


@router.post("/api/government/tax/calculate")
async def calculate_tax(data: dict = Body(...)):
    """Calculate tax liability"""
    try:
        from core.government import get_government_manager
        gm = get_government_manager()
        calculation = gm.calculate_tax(
            user_id=data.get("user_id"),
            country=data.get("country", "NP"),
            income=data.get("income", 0),
            deductions=data.get("deductions", []),
            tax_year=data.get("tax_year", 2024)
        )
        return ok(data=calculation)
    except Exception as e:
        logger.error(f"Calculate tax error: {e}")
        return error(str(e))


@router.post("/api/government/tax/prepare")
async def prepare_tax_return(data: dict = Body(...)):
    """Prepare tax return"""
    try:
        from core.government import get_government_manager
        gm = get_government_manager()
        tax_return = gm.prepare_tax_return(
            user_id=data.get("user_id"),
            country=data.get("country", "NP"),
            income=data.get("income", 0),
            deductions=data.get("deductions", []),
            tax_year=data.get("tax_year", 2024),
            filing_status=data.get("filing_status", "single")
        )
        return ok(data=tax_return)
    except Exception as e:
        logger.error(f"Prepare tax return error: {e}")
        return error(str(e))


# ─── Government Services ─────────────────────────────────────────────────────


@router.get("/api/government/services/{country}")
async def get_gov_services(country: str):
    """Get government services for a country"""
    try:
        from core.government import get_government_manager
        gm = get_government_manager()
        services = gm.get_services(country)
        return ok(data={
            "country": country,
            "services": services,
            "count": len(services)
        })
    except Exception as e:
        logger.error(f"Government services error: {e}")
        return error(str(e))


# ─── Signatures ──────────────────────────────────────────────────────────────


@router.get("/api/government/signatures/regions")
async def signature_regions():
    """Get supported signature regions"""
    try:
        from core.government import get_government_manager
        gm = get_government_manager()
        regions = gm.get_signature_regions()
        return ok(data={
            "regions": regions,
            "count": len(regions)
        })
    except Exception as e:
        logger.error(f"Signature regions error: {e}")
        return error(str(e))


# ─── Government Stats ────────────────────────────────────────────────────────


@router.get("/api/government/stats")
async def government_stats():
    """Get comprehensive government stats"""
    try:
        from core.government import (
            get_government_manager, GovernmentStatus
        )
        gm = get_government_manager()
        return ok(data={
            "status": gm.get_status().value if hasattr(gm.get_status(), 'value') else str(gm.get_status()),
            "identity_countries": gm.get_identity_countries_count(),
            "total_identities": gm.get_active_identities_count(),
            "eresidency_programs": gm.get_eresidency_programs_count(),
            "tax_countries": gm.get_tax_countries_count(),
            "signature_regions": gm.get_signature_regions_count(),
            "services_available": gm.get_services_count()
        })
    except Exception as e:
        logger.error(f"Government stats error: {e}")
        return error(str(e))
