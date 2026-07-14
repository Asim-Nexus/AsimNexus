"""
RBE Algorithm — Resource-Based Economy core engine.
=====================================================
Implements a Resource-Based Economy (RBE) algorithm for managing
resources, processing demand requests, and optimizing distribution.

Exports:
    ResourceType       — enum of resource types (ENERGY, FOOD, WATER, etc.)
    PriorityLevel      — enum of demand priority levels
    Resource           — dataclass for a single resource entry
    ResourcePool       — dataclass for a pool of resources of the same type
    DemandRequest      — dataclass for a demand request
    AllocationResult   — dataclass for allocation results
    RBEAlgorithm       — main class with resource management and allocation
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple


class ResourceType(Enum):
    """Types of resources managed by the RBE."""
    ENERGY = "energy"
    FOOD = "food"
    WATER = "water"
    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    RAW_MATERIALS = "raw_materials"
    WASTE = "waste"


class PriorityLevel(Enum):
    """Priority levels for demand requests."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Resource:
    """A single resource entry."""
    id: str
    type: ResourceType
    quantity: float
    unit: str
    location: Tuple[float, float]
    renewable: bool = False
    regeneration_rate: float = 0.0
    quality_score: float = 1.0


@dataclass
class ResourcePool:
    """A pool of resources of the same type."""
    resource_type: ResourceType
    resources: List[Resource] = field(default_factory=list)

    def get_available_quantity(self) -> float:
        """Return total available quantity across all resources in the pool."""
        return sum(r.quantity for r in self.resources)

    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the pool."""
        self.resources.append(resource)

    def remove_resource(self, resource_id: str) -> bool:
        """Remove a resource from the pool by ID."""
        for i, r in enumerate(self.resources):
            if r.id == resource_id:
                self.resources.pop(i)
                return True
        return False


@dataclass
class DemandRequest:
    """A demand request for resources."""
    id: str
    requester_id: str
    resource_type: ResourceType
    quantity: float
    priority: PriorityLevel
    location: Tuple[float, float]
    fulfilled: bool = False


@dataclass
class AllocationResult:
    """Result of a resource allocation."""
    success: bool
    allocated_quantity: float
    resource_ids: List[str]
    request_id: str = ""
    message: str = ""


class RBEAlgorithm:
    """Resource-Based Economy algorithm for managing and allocating resources."""

    def __init__(self):
        # Initialize resource pools for all resource types
        self.resource_pools: Dict[ResourceType, ResourcePool] = {
            rt: ResourcePool(resource_type=rt) for rt in ResourceType
        }
        self.demand_requests: List[DemandRequest] = []
        self.waste_tracker: Dict[ResourceType, float] = {
            rt: 0.0 for rt in ResourceType
        }

    # ── Resource Management ─────────────────────────────────────────────────

    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the appropriate pool."""
        pool = self.resource_pools[resource.type]
        pool.add_resource(resource)

    def remove_resource(self, resource_id: str, resource_type: ResourceType) -> bool:
        """Remove a resource from its pool by ID and type."""
        pool = self.resource_pools.get(resource_type)
        if not pool:
            return False
        return pool.remove_resource(resource_id)

    # ── Demand Management ───────────────────────────────────────────────────

    def submit_demand(self, request: DemandRequest) -> None:
        """Submit a demand request."""
        self.demand_requests.append(request)

    # ── Distance Calculation ────────────────────────────────────────────────

    @staticmethod
    def calculate_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate Haversine distance between two (lat, lon) points in km."""
        lat1, lon1 = math.radians(loc1[0]), math.radians(loc1[1])
        lat2, lon2 = math.radians(loc2[0]), math.radians(loc2[1])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # Earth radius in km
        R = 6371.0
        return R * c

    # ── Resource Allocation ─────────────────────────────────────────────────

    def find_nearest_resources(
        self,
        resource_type: ResourceType,
        location: Tuple[float, float],
        max_distance_km: float = float("inf"),
    ) -> List[Tuple[Resource, float]]:
        """Find resources of a given type nearest to a location.

        Args:
            resource_type: Type of resource to search for
            location: (lat, lon) target location
            max_distance_km: Maximum distance in km (default: unlimited)

        Returns:
            List of (Resource, distance_km) tuples sorted by distance
        """
        pool = self.resource_pools.get(resource_type)
        if not pool:
            return []

        results: List[Tuple[Resource, float]] = []
        for resource in pool.resources:
            if resource.quantity <= 0:
                continue
            distance = self.calculate_distance(location, resource.location)
            if distance <= max_distance_km:
                results.append((resource, distance))

        # Sort by distance
        results.sort(key=lambda x: x[1])
        return results

    def allocate_resources(self, request: DemandRequest) -> AllocationResult:
        """Allocate resources to fulfill a demand request.

        Args:
            request: The demand request to fulfill

        Returns:
            AllocationResult with success status and details
        """
        pool = self.resource_pools.get(request.resource_type)
        if not pool:
            return AllocationResult(
                success=False,
                allocated_quantity=0.0,
                resource_ids=[],
                request_id=request.id,
                message=f"No pool for resource type {request.resource_type}",
            )

        # Find nearest resources
        nearest = self.find_nearest_resources(request.resource_type, request.location)
        if not nearest:
            return AllocationResult(
                success=False,
                allocated_quantity=0.0,
                resource_ids=[],
                request_id=request.id,
                message="No resources available",
            )

        allocated = 0.0
        resource_ids: List[str] = []

        for resource, _ in nearest:
            if allocated >= request.quantity:
                break

            needed = request.quantity - allocated
            take = min(resource.quantity, needed)

            resource.quantity -= take
            allocated += take
            resource_ids.append(resource.id)

        success = allocated >= request.quantity * 0.9  # 90% threshold
        return AllocationResult(
            success=success,
            allocated_quantity=allocated,
            resource_ids=resource_ids,
            request_id=request.id,
            message="Allocated successfully" if success else f"Partial allocation: {allocated}/{request.quantity}",
        )

    # ── Equilibrium Score ───────────────────────────────────────────────────

    def calculate_equilibrium_score(self) -> float:
        """Calculate the equilibrium score of the resource system.

        A score of 1.0 means perfect equilibrium (supply meets demand),
        0.0 means complete imbalance.

        Returns:
            Float between 0.0 and 1.0
        """
        total_supply = 0.0
        total_demand = 0.0

        for rt, pool in self.resource_pools.items():
            supply = pool.get_available_quantity()
            total_supply += supply

            # Sum demand for this resource type
            demand = sum(
                r.quantity for r in self.demand_requests
                if r.resource_type == rt and not r.fulfilled
            )
            total_demand += demand

        if total_demand == 0:
            return 1.0  # No demand = perfect equilibrium

        ratio = total_supply / total_demand
        # Clamp to [0, 1]
        return min(1.0, max(0.0, ratio))

    # ── Optimization ────────────────────────────────────────────────────────

    def optimize_distribution(self) -> Dict[str, Any]:
        """Generate optimization recommendations based on supply/demand analysis.

        Returns:
            Dict with recommendations
        """
        recommendations: List[Dict[str, Any]] = []

        for rt, pool in self.resource_pools.items():
            supply = pool.get_available_quantity()
            demand = sum(
                r.quantity for r in self.demand_requests
                if r.resource_type == rt and not r.fulfilled
            )

            if demand > supply:
                recommendations.append({
                    "resource_type": rt.value,
                    "action": "increase_production",
                    "reason": f"Demand ({demand}) exceeds supply ({supply})",
                    "priority": "high",
                })
            elif supply > demand * 2:
                recommendations.append({
                    "resource_type": rt.value,
                    "action": "reduce_waste",
                    "reason": f"Supply ({supply}) far exceeds demand ({demand})",
                    "priority": "medium",
                })

        return {
            "total_recommendations": len(recommendations),
            "recommendations": recommendations,
            "equilibrium_score": self.calculate_equilibrium_score(),
        }

    # ── Status ──────────────────────────────────────────────────────────────

    def get_resource_status(self) -> Dict[str, Any]:
        """Get status of all resource pools.

        Returns:
            Dict keyed by resource type name with pool stats
        """
        status: Dict[str, Any] = {}
        for rt, pool in self.resource_pools.items():
            status[rt.value] = {
                "available_quantity": pool.get_available_quantity(),
                "resource_count": len(pool.resources),
                "waste": self.waste_tracker.get(rt, 0.0),
            }
        return status

    def get_demand_status(self) -> Dict[str, Any]:
        """Get status of all demand requests.

        Returns:
            Dict with pending count and pending requests
        """
        pending = [r for r in self.demand_requests if not r.fulfilled]
        return {
            "pending_count": len(pending),
            "pending_requests": [
                {
                    "id": r.id,
                    "requester_id": r.requester_id,
                    "resource_type": r.resource_type.value,
                    "quantity": r.quantity,
                    "priority": r.priority.name,
                }
                for r in pending
            ],
        }

    # ── Renewable Resources ─────────────────────────────────────────────────

    def regenerate_resources(self) -> None:
        """Regenerate renewable resources based on their regeneration rates."""
        for pool in self.resource_pools.values():
            for resource in pool.resources:
                if resource.renewable and resource.regeneration_rate > 0:
                    resource.quantity += resource.regeneration_rate

    # ── Process All Demands ─────────────────────────────────────────────────

    def process_all_demands(self) -> List[AllocationResult]:
        """Process all pending demand requests, sorted by priority.

        Returns:
            List of AllocationResult for each processed demand
        """
        pending = [r for r in self.demand_requests if not r.fulfilled]

        # Sort by priority (highest first), then by quantity (smallest first)
        pending.sort(key=lambda r: (-r.priority.value, r.quantity))

        results: List[AllocationResult] = []
        for request in pending:
            result = self.allocate_resources(request)
            if result.success:
                request.fulfilled = True
            results.append(result)

        return results
