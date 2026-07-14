"""
RBE Algorithm API — Resource-Based Economy endpoints.
======================================================
Exposes the RBEAlgorithm from core/world/economy/rbe_algorithm.py
for resource management, demand submission, allocation, and status.
"""

import logging
from typing import Dict, Any, List, Tuple
from fastapi import APIRouter, Body
from pydantic import BaseModel

from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.RBE")

router = APIRouter(tags=["RBE"])

# ── Singleton ────────────────────────────────────────────────────────────────

_rbe_instance = None


def init_rbe(app_globals: dict) -> None:
    """Initialize RBE module with shared state."""
    global _rbe_instance
    try:
        from core.world.economy.rbe_algorithm import RBEAlgorithm
        _rbe_instance = RBEAlgorithm()
        logger.info("RBEAlgorithm instance created")
    except Exception as e:
        logger.warning(f"RBEAlgorithm not available: {e}")
        _rbe_instance = None


def _get_rbe():
    """Get or create the RBEAlgorithm singleton."""
    global _rbe_instance
    if _rbe_instance is None:
        try:
            from core.world.economy.rbe_algorithm import RBEAlgorithm
            _rbe_instance = RBEAlgorithm()
        except Exception as e:
            logger.error(f"Cannot create RBEAlgorithm: {e}")
    return _rbe_instance


# ── Pydantic Models ──────────────────────────────────────────────────────────

class ResourceModel(BaseModel):
    id: str
    type: str  # ResourceType value
    quantity: float
    unit: str
    location: List[float]  # [lat, lon]
    renewable: bool = False
    regeneration_rate: float = 0.0
    quality_score: float = 1.0


class DemandModel(BaseModel):
    id: str
    requester_id: str
    resource_type: str  # ResourceType value
    quantity: float
    priority: str = "MEDIUM"  # PriorityLevel name
    location: List[float]  # [lat, lon]


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/api/rbe/resources")
async def rbe_add_resource(data: ResourceModel = Body(...)):
    """Add a resource to the RBE system."""
    try:
        rbe = _get_rbe()
        if not rbe:
            return error("RBE algorithm not available")

        from core.world.economy.rbe_algorithm import ResourceType, Resource, PriorityLevel

        rt = ResourceType(data.type)
        resource = Resource(
            id=data.id,
            type=rt,
            quantity=data.quantity,
            unit=data.unit,
            location=tuple(data.location),
            renewable=data.renewable,
            regeneration_rate=data.regeneration_rate,
            quality_score=data.quality_score,
        )
        rbe.add_resource(resource)
        return ok(data={"id": data.id, "type": data.type, "quantity": data.quantity})
    except Exception as e:
        logger.error(f"rbe_add_resource error: {e}")
        return error(str(e))


@router.post("/api/rbe/demand")
async def rbe_submit_demand(data: DemandModel = Body(...)):
    """Submit a demand request to the RBE system."""
    try:
        rbe = _get_rbe()
        if not rbe:
            return error("RBE algorithm not available")

        from core.world.economy.rbe_algorithm import ResourceType, DemandRequest, PriorityLevel

        rt = ResourceType(data.resource_type)
        priority_map = {
            "LOW": PriorityLevel.LOW,
            "MEDIUM": PriorityLevel.MEDIUM,
            "HIGH": PriorityLevel.HIGH,
            "CRITICAL": PriorityLevel.CRITICAL,
        }
        priority = priority_map.get(data.priority.upper(), PriorityLevel.MEDIUM)

        request = DemandRequest(
            id=data.id,
            requester_id=data.requester_id,
            resource_type=rt,
            quantity=data.quantity,
            priority=priority,
            location=tuple(data.location),
        )
        rbe.submit_demand(request)
        return ok(data={"id": data.id, "resource_type": data.resource_type, "quantity": data.quantity})
    except Exception as e:
        logger.error(f"rbe_submit_demand error: {e}")
        return error(str(e))


@router.post("/api/rbe/allocate")
async def rbe_allocate(data: dict = Body(...)):
    """Allocate resources to fulfill a demand request."""
    try:
        rbe = _get_rbe()
        if not rbe:
            return error("RBE algorithm not available")

        from core.world.economy.rbe_algorithm import ResourceType, DemandRequest, PriorityLevel

        request_id = data.get("request_id", "")
        # Find the matching demand request
        for req in rbe.demand_requests:
            if req.id == request_id and not req.fulfilled:
                result = rbe.allocate_resources(req)
                if result.success:
                    req.fulfilled = True
                return ok(data={
                    "success": result.success,
                    "allocated_quantity": result.allocated_quantity,
                    "resource_ids": result.resource_ids,
                    "request_id": result.request_id,
                    "message": result.message,
                })

        return error(f"Pending demand request '{request_id}' not found")
    except Exception as e:
        logger.error(f"rbe_allocate error: {e}")
        return error(str(e))


@router.post("/api/rbe/allocate-all")
async def rbe_allocate_all():
    """Process all pending demand requests, sorted by priority."""
    try:
        rbe = _get_rbe()
        if not rbe:
            return error("RBE algorithm not available")

        results = rbe.process_all_demands()
        return ok(data={
            "total_processed": len(results),
            "results": [
                {
                    "success": r.success,
                    "allocated_quantity": r.allocated_quantity,
                    "resource_ids": r.resource_ids,
                    "request_id": r.request_id,
                    "message": r.message,
                }
                for r in results
            ],
        })
    except Exception as e:
        logger.error(f"rbe_allocate_all error: {e}")
        return error(str(e))


@router.get("/api/rbe/status")
async def rbe_status():
    """Get resource and demand status from the RBE system."""
    try:
        rbe = _get_rbe()
        if not rbe:
            return error("RBE algorithm not available")

        resource_status = rbe.get_resource_status()
        demand_status = rbe.get_demand_status()
        return ok(data={
            "resources": resource_status,
            "demands": demand_status,
        })
    except Exception as e:
        logger.error(f"rbe_status error: {e}")
        return error(str(e))


@router.get("/api/rbe/equilibrium")
async def rbe_equilibrium():
    """Get the equilibrium score of the resource system."""
    try:
        rbe = _get_rbe()
        if not rbe:
            return error("RBE algorithm not available")

        score = rbe.calculate_equilibrium_score()
        optimization = rbe.optimize_distribution()
        return ok(data={
            "equilibrium_score": score,
            "interpretation": (
                "Perfect equilibrium" if score >= 1.0
                else "Good balance" if score >= 0.7
                else "Moderate imbalance" if score >= 0.4
                else "Severe imbalance"
            ),
            "recommendations": optimization.get("recommendations", []),
            "total_recommendations": optimization.get("total_recommendations", 0),
        })
    except Exception as e:
        logger.error(f"rbe_equilibrium error: {e}")
        return error(str(e))


@router.post("/api/rbe/regenerate")
async def rbe_regenerate():
    """Regenerate renewable resources."""
    try:
        rbe = _get_rbe()
        if not rbe:
            return error("RBE algorithm not available")

        rbe.regenerate_resources()
        return ok(data={"message": "Renewable resources regenerated"})
    except Exception as e:
        logger.error(f"rbe_regenerate error: {e}")
        return error(str(e))
