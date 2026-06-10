
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
Resource-Based Economy (RBE) Algorithm
======================================

Implementation of Resource-Based Economy principles based on The Venus Project:
- Equilibrium resource distribution
- Waste reduction through optimization
- Sustainable resource allocation
- Needs-based rather than profit-based allocation

Key concepts:
- Resources held as common heritage
- Equilibrium distribution based on need
- Optimization for waste reduction
- Dynamic resource monitoring
"""

import logging
import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Resource types in RBE"""
    ENERGY = "energy"
    WATER = "water"
    FOOD = "food"
    MATERIALS = "materials"
    COMPUTING = "computing"
    TRANSPORTATION = "transportation"
    HOUSING = "housing"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    INFORMATION = "information"


class PriorityLevel(Enum):
    """Priority levels for demand requests"""
    CRITICAL = 1  # Survival needs
    HIGH = 2      # Essential services
    MEDIUM = 3    # Quality of life
    LOW = 4       # Luxury/optional


@dataclass
class Resource:
    """Individual resource unit"""
    id: str
    type: ResourceType
    quantity: float
    unit: str
    location: Tuple[float, float]  # (lat, lon)
    quality: float = 1.0  # 0.0 to 1.0
    renewable: bool = False
    regeneration_rate: float = 0.0  # units per day
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ResourcePool:
    """Pool of resources of a specific type"""
    resource_type: ResourceType
    resources: List[Resource] = field(default_factory=list)
    total_quantity: float = 0.0
    
    def add_resource(self, resource: Resource) -> None:
        """Add resource to pool"""
        if resource.type == self.resource_type:
            self.resources.append(resource)
            self.total_quantity += resource.quantity
    
    def remove_resource(self, resource_id: str) -> bool:
        """Remove resource from pool"""
        for i, resource in enumerate(self.resources):
            if resource.id == resource_id:
                self.total_quantity -= resource.quantity
                self.resources.pop(i)
                return True
        return False
    
    def get_available_quantity(self) -> float:
        """Get total available quantity"""
        return sum(r.quantity for r in self.resources)
    
    def get_average_quality(self) -> float:
        """Get average quality of resources"""
        if not self.resources:
            return 0.0
        return sum(r.quality for r in self.resources) / len(self.resources)


@dataclass
class DemandRequest:
    """Demand request for resources"""
    id: str
    requester_id: str
    resource_type: ResourceType
    quantity: float
    priority: PriorityLevel
    location: Tuple[float, float]
    urgency: float = 1.0  # 0.0 to 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def calculate_score(self) -> float:
        """Calculate allocation score based on priority and urgency"""
        priority_weight = {PriorityLevel.CRITICAL: 1.0, PriorityLevel.HIGH: 0.8, 
                          PriorityLevel.MEDIUM: 0.6, PriorityLevel.LOW: 0.4}
        return priority_weight[self.priority] * self.urgency


@dataclass
class AllocationResult:
    """Result of resource allocation"""
    request_id: str
    allocated_quantity: float
    resource_ids: List[str]
    success: bool
    waste_generated: float = 0.0
    efficiency_score: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class RBEAlgorithm:
    """
    Resource-Based Economy Algorithm
    
    Implements equilibrium resource distribution:
    - Needs-based allocation
    - Waste minimization
    - Distance optimization
    - Quality matching
    - Dynamic rebalancing
    """
    
    def __init__(self):
        self.resource_pools: Dict[ResourceType, ResourcePool] = {}
        self.demand_requests: List[DemandRequest] = []
        self.allocation_history: List[AllocationResult] = []
        self.waste_tracker: Dict[ResourceType, float] = {}
        self.lock = None
        
        # Initialize resource pools for all types
        for resource_type in ResourceType:
            self.resource_pools[resource_type] = ResourcePool(resource_type)
            self.waste_tracker[resource_type] = 0.0
        
        logger.info("RBE Algorithm initialized")
    
    def add_resource(self, resource: Resource) -> None:
        """Add resource to appropriate pool"""
        pool = self.resource_pools.get(resource.type)
        if pool:
            pool.add_resource(resource)
            logger.info(f"Resource added: {resource.id} ({resource.type.value})")
    
    def remove_resource(self, resource_id: str, resource_type: ResourceType) -> bool:
        """Remove resource from pool"""
        pool = self.resource_pools.get(resource_type)
        if pool:
            return pool.remove_resource(resource_id)
        return False
    
    def submit_demand(self, request: DemandRequest) -> None:
        """Submit demand request"""
        self.demand_requests.append(request)
        logger.info(f"Demand submitted: {request.id} ({request.resource_type.value})")
    
    def calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate distance between two locations (Haversine formula)"""
        lat1, lon1 = loc1
        lat2, lon2 = loc2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in km
        r = 6371
        return c * r
    
    def find_nearest_resources(
        self,
        resource_type: ResourceType,
        location: Tuple[float, float],
        quantity: float,
        max_distance: float = 1000.0  # km
    ) -> List[Tuple[Resource, float]]:
        """Find nearest resources of given type"""
        pool = self.resource_pools.get(resource_type)
        if not pool:
            return []
        
        resources_with_distance = []
        for resource in pool.resources:
            distance = self.calculate_distance(location, resource.location)
            if distance <= max_distance:
                resources_with_distance.append((resource, distance))
        
        # Sort by distance
        resources_with_distance.sort(key=lambda x: x[1])
        
        return resources_with_distance
    
    def allocate_resources(self, request: DemandRequest) -> AllocationResult:
        """Allocate resources for demand request"""
        pool = self.resource_pools.get(request.resource_type)
        if not pool:
            return AllocationResult(
                request_id=request.id,
                allocated_quantity=0.0,
                resource_ids=[],
                success=False
            )
        
        # Find nearest resources
        nearby_resources = self.find_nearest_resources(
            request.resource_type,
            request.location,
            request.quantity
        )
        
        allocated_quantity = 0.0
        allocated_resources = []
        waste_generated = 0.0
        
        # Allocate from nearest resources
        for resource, distance in nearby_resources:
            if allocated_quantity >= request.quantity:
                break
            
            # Calculate allocation amount
            remaining_needed = request.quantity - allocated_quantity
            available = resource.quantity
            allocation = min(remaining_needed, available)
            
            # Calculate waste based on distance (transportation losses)
            transport_efficiency = max(0.5, 1.0 - (distance / 2000.0))  # 50% efficiency at 2000km
            actual_received = allocation * transport_efficiency
            waste = allocation - actual_received
            
            allocated_quantity += actual_received
            waste_generated += waste
            allocated_resources.append(resource.id)
            
            # Update resource quantity
            resource.quantity -= allocation
        
        success = allocated_quantity >= request.quantity * 0.9  # 90% fulfillment threshold
        
        # Calculate efficiency score
        efficiency_score = 1.0 - (waste_generated / max(request.quantity, 1.0))
        
        result = AllocationResult(
            request_id=request.id,
            allocated_quantity=allocated_quantity,
            resource_ids=allocated_resources,
            success=success,
            waste_generated=waste_generated,
            efficiency_score=efficiency_score
        )
        
        # Track waste
        self.waste_tracker[request.resource_type] += waste_generated
        
        # Record allocation
        self.allocation_history.append(result)
        
        # Remove fulfilled request
        if success:
            self.demand_requests = [r for r in self.demand_requests if r.id != request.id]
        
        logger.info(f"Allocation: {request.id} - {allocated_quantity:.2f}/{request.quantity:.2f} units, "
                   f"efficiency: {efficiency_score:.2f}")
        
        return result
    
    def optimize_distribution(self) -> Dict[str, Any]:
        """
        Optimize resource distribution using equilibrium algorithm
        
        Returns optimization recommendations
        """
        recommendations = []
        
        # Analyze each resource type
        for resource_type, pool in self.resource_pools.items():
            available = pool.get_available_quantity()
            
            # Calculate total demand for this resource type
            total_demand = sum(
                r.quantity for r in self.demand_requests 
                if r.resource_type == resource_type
            )
            
            # Calculate surplus/deficit
            balance = available - total_demand
            
            if balance < 0:
                # Deficit - need to produce or import
                recommendations.append({
                    "resource_type": resource_type.value,
                    "action": "increase_production",
                    "quantity": abs(balance),
                    "priority": "high" if balance < -100 else "medium"
                })
            elif balance > 0:
                # Surplus - can redistribute or store
                recommendations.append({
                    "resource_type": resource_type.value,
                    "action": "redistribute_or_store",
                    "quantity": balance,
                    "priority": "low"
                })
        
        # Analyze waste
        total_waste = sum(self.waste_tracker.values())
        if total_waste > 100:
            recommendations.append({
                "resource_type": "all",
                "action": "reduce_transportation_losses",
                "quantity": total_waste,
                "priority": "high"
            })
        
        return {
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_equilibrium_score(self) -> float:
        """
        Calculate overall equilibrium score
        
        Returns score from 0.0 to 1.0, where 1.0 is perfect equilibrium
        """
        if not self.allocation_history:
            return 1.0  # Perfect equilibrium if no allocations yet
        
        # Calculate average efficiency
        avg_efficiency = sum(
            result.efficiency_score for result in self.allocation_history
        ) / len(self.allocation_history)
        
        # Calculate waste penalty
        total_allocated = sum(result.allocated_quantity for result in self.allocation_history)
        total_waste = sum(result.waste_generated for result in self.allocation_history)
        waste_penalty = 1.0 - (total_waste / max(total_allocated, 1.0))
        
        # Calculate demand fulfillment rate
        fulfilled_requests = sum(1 for result in self.allocation_history if result.success)
        fulfillment_rate = fulfilled_requests / len(self.allocation_history)
        
        # Combine metrics
        equilibrium_score = (avg_efficiency * 0.4) + (waste_penalty * 0.3) + (fulfillment_rate * 0.3)
        
        return max(0.0, min(1.0, equilibrium_score))
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get status of all resources"""
        status = {}
        
        for resource_type, pool in self.resource_pools.items():
            total_demand = sum(
                r.quantity for r in self.demand_requests 
                if r.resource_type == resource_type
            )
            
            status[resource_type.value] = {
                "available_quantity": pool.get_available_quantity(),
                "average_quality": pool.get_average_quality(),
                "total_demand": total_demand,
                "balance": pool.get_available_quantity() - total_demand,
                "waste_generated": self.waste_tracker[resource_type],
                "resource_count": len(pool.resources)
            }
        
        return status
    
    def get_demand_status(self) -> Dict[str, Any]:
        """Get status of demand requests"""
        pending_requests = [
            {
                "id": r.id,
                "requester_id": r.requester_id,
                "resource_type": r.resource_type.value,
                "quantity": r.quantity,
                "priority": r.priority.name,
                "urgency": r.urgency,
                "score": r.calculate_score()
            }
            for r in self.demand_requests
        ]
        
        # Sort by score (highest priority first)
        pending_requests.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "pending_count": len(self.demand_requests),
            "pending_requests": pending_requests[:10],  # Top 10
            "total_fulfilled": len(self.allocation_history),
            "fulfillment_rate": sum(1 for r in self.allocation_history if r.success) / max(len(self.allocation_history), 1)
        }
    
    def process_all_demands(self) -> List[AllocationResult]:
        """Process all pending demand requests"""
        # Sort requests by score (priority)
        sorted_requests = sorted(
            self.demand_requests,
            key=lambda r: r.calculate_score(),
            reverse=True
        )
        
        results = []
        for request in sorted_requests:
            result = self.allocate_resources(request)
            results.append(result)
        
        return results
    
    def regenerate_resources(self) -> None:
        """Regenerate renewable resources"""
        for resource_type, pool in self.resource_pools.items():
            for resource in pool.resources:
                if resource.renewable and resource.regeneration_rate > 0:
                    # Regenerate up to original capacity
                    resource.quantity = min(
                        resource.quantity + resource.regeneration_rate,
                        resource.quantity * 2  # Cap at double current amount
                    )


# Global RBE algorithm instance
_rbe_algorithm: Optional[RBEAlgorithm] = None


def get_rbe_algorithm() -> RBEAlgorithm:
    """Get global RBE algorithm instance (lazy load)"""
    global _rbe_algorithm
    if _rbe_algorithm is None:
        _rbe_algorithm = RBEAlgorithm()
    return _rbe_algorithm
