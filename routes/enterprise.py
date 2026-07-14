"""
Enterprise Routes — 49% Private Sector API

Provides API endpoints for enterprise licensing, compliance checking,
agent hiring, and commercial governance. Integrates with the
EnterpriseLayer from core/governance/enterprise_layer.py.

This is the 49% private side of the 51/49 governance model.
"""
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body
from pydantic import BaseModel

from routes.response import ok, error, unavailable

logger = logging.getLogger(__name__)

router = APIRouter(tags=["enterprise"])

# ── Pydantic Models ───────────────────────────────────────────────────────

class LicenseRegisterRequest(BaseModel):
    organization: str
    tier: str = "starter"
    jurisdiction: str = "np"
    max_users: int = 10
    max_agents: int = 5
    features: Optional[list[str]] = None

class ComplianceCheckRequest(BaseModel):
    organization: str
    action: str
    current_users: int = 0
    current_agents: int = 0
    required_feature: Optional[str] = None

class LicenseDeactivateRequest(BaseModel):
    license_id: str

# ── Singleton Access ──────────────────────────────────────────────────────

_enterprise_layer: Optional[Any] = None

def init_enterprise(app_globals: dict) -> None:
    """Initialize enterprise layer singleton."""
    global _enterprise_layer
    try:
        from core.governance.enterprise_layer import EnterpriseLayer
        _enterprise_layer = EnterpriseLayer()
        app_globals["enterprise_layer"] = _enterprise_layer
        logger.info("Enterprise layer initialized")
    except Exception as e:
        logger.warning(f"Enterprise layer init failed: {e}")
        _enterprise_layer = None

def _get_enterprise_layer():
    """Get or create enterprise layer singleton."""
    global _enterprise_layer
    if _enterprise_layer is None:
        try:
            from core.governance.enterprise_layer import EnterpriseLayer
            _enterprise_layer = EnterpriseLayer()
        except Exception as e:
            logger.error(f"Cannot create enterprise layer: {e}")
    return _enterprise_layer

# ── API Endpoints ─────────────────────────────────────────────────────────

@router.get("/api/enterprise/status")
async def enterprise_status():
    """Get enterprise layer system status."""
    layer = _get_enterprise_layer()
    if not layer:
        return unavailable("Enterprise layer not available")
    try:
        stats = layer.get_stats()
        return ok({
            "status": "active",
            "stats": stats,
        })
    except Exception as e:
        logger.error(f"Enterprise status error: {e}")
        return error(str(e))


@router.get("/api/enterprise/licenses")
async def list_licenses():
    """List all registered enterprise licenses."""
    layer = _get_enterprise_layer()
    if not layer:
        return unavailable("Enterprise layer not available")
    try:
        stats = layer.get_stats()
        licenses = []
        for org in stats.get("organizations", []):
            # Find license for each org
            for lid, lic in layer._licenses.items():
                if lic.organization == org:
                    licenses.append({
                        "license_id": lid,
                        "organization": lic.organization,
                        "tier": lic.tier.value,
                        "jurisdiction": lic.jurisdiction,
                        "max_users": lic.max_users,
                        "max_agents": lic.max_agents,
                        "features": lic.features,
                        "active": lic.active,
                        "created_at": lic.created_at,
                        "expires_at": lic.expires_at,
                    })
        return ok({"licenses": licenses})
    except Exception as e:
        logger.error(f"List licenses error: {e}")
        return error(str(e))


@router.post("/api/enterprise/license/register")
async def register_license(req: LicenseRegisterRequest):
    """Register a new enterprise license."""
    layer = _get_enterprise_layer()
    if not layer:
        return unavailable("Enterprise layer not available")
    try:
        from core.governance.enterprise_layer import EnterpriseTier
        tier_map = {
            "free": EnterpriseTier.FREE,
            "starter": EnterpriseTier.STARTER,
            "business": EnterpriseTier.BUSINESS,
            "enterprise": EnterpriseTier.ENTERPRISE,
            "government": EnterpriseTier.GOVERNMENT,
        }
        tier = tier_map.get(req.tier.lower(), EnterpriseTier.STARTER)
        license = layer.register_license(
            organization=req.organization,
            tier=tier,
            jurisdiction=req.jurisdiction,
            max_users=req.max_users,
            max_agents=req.max_agents,
            features=req.features,
        )
        return ok({
            "license_id": license.license_id,
            "organization": license.organization,
            "tier": license.tier.value,
            "active": license.active,
            "message": f"License registered for {req.organization}",
        })
    except Exception as e:
        logger.error(f"Register license error: {e}")
        return error(str(e))


@router.post("/api/enterprise/license/deactivate")
async def deactivate_license(req: LicenseDeactivateRequest):
    """Deactivate an enterprise license."""
    layer = _get_enterprise_layer()
    if not layer:
        return unavailable("Enterprise layer not available")
    try:
        result = layer.deactivate_license(req.license_id)
        if result:
            return ok({"message": f"License {req.license_id} deactivated"})
        return error(f"License {req.license_id} not found")
    except Exception as e:
        logger.error(f"Deactivate license error: {e}")
        return error(str(e))


@router.post("/api/enterprise/compliance/check")
async def check_compliance(req: ComplianceCheckRequest):
    """Check if an action is compliant with enterprise policies."""
    layer = _get_enterprise_layer()
    if not layer:
        return unavailable("Enterprise layer not available")
    try:
        context = {
            "current_users": req.current_users,
            "current_agents": req.current_agents,
        }
        if req.required_feature:
            context["required_feature"] = req.required_feature

        record = layer.check_compliance(
            organization=req.organization,
            action=req.action,
            context=context,
        )
        return ok({
            "record_id": record.record_id,
            "organization": record.organization,
            "action": record.action,
            "status": record.status.value,
            "details": record.details,
            "checked_at": record.checked_at,
        })
    except Exception as e:
        logger.error(f"Compliance check error: {e}")
        return error(str(e))


@router.get("/api/enterprise/compliance/log")
async def compliance_log(organization: Optional[str] = None, limit: int = 100):
    """Get enterprise compliance check history."""
    layer = _get_enterprise_layer()
    if not layer:
        return unavailable("Enterprise layer not available")
    try:
        records = layer.get_compliance_log(organization=organization, limit=limit)
        return ok({
            "entries": [
                {
                    "record_id": r.record_id,
                    "organization": r.organization,
                    "action": r.action,
                    "status": r.status.value,
                    "details": r.details,
                    "checked_at": r.checked_at,
                }
                for r in records
            ],
            "total": len(records),
        })
    except Exception as e:
        logger.error(f"Compliance log error: {e}")
        return error(str(e))


@router.get("/api/enterprise/stats")
async def enterprise_stats():
    """Get comprehensive enterprise layer statistics."""
    layer = _get_enterprise_layer()
    if not layer:
        return unavailable("Enterprise layer not available")
    try:
        stats = layer.get_stats()
        return ok(stats)
    except Exception as e:
        logger.error(f"Enterprise stats error: {e}")
        return error(str(e))
