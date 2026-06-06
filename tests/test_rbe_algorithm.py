
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test ASIMNEXUS RBE Algorithm
=============================

Tests for Resource-Based Economy algorithm:
- Resource management
- Demand allocation
- Equilibrium distribution
- Waste optimization
"""

from core.world.economy.rbe_algorithm import (
    RBEAlgorithm,
    Resource,
    ResourcePool,
    DemandRequest,
    AllocationResult,
    ResourceType,
    PriorityLevel
)


def test_rbe_initialization():
    """Test RBE algorithm initialization"""
    rbe = RBEAlgorithm()
    
    # Check resource pools initialized
    assert len(rbe.resource_pools) == len(ResourceType)
    assert ResourceType.ENERGY in rbe.resource_pools
    assert ResourceType.FOOD in rbe.resource_pools
    
    # Check waste tracker initialized
    assert ResourceType.ENERGY in rbe.waste_tracker
    
    print("✅ RBE initialization test passed")


def test_resource_management():
    """Test resource addition and removal"""
    rbe = RBEAlgorithm()
    
    # Add resource
    resource = Resource(
        id="res1",
        type=ResourceType.ENERGY,
        quantity=1000.0,
        unit="kWh",
        location=(40.7128, -74.0060)
    )
    rbe.add_resource(resource)
    
    # Check resource added
    pool = rbe.resource_pools[ResourceType.ENERGY]
    assert len(pool.resources) == 1
    assert pool.get_available_quantity() == 1000.0
    
    # Remove resource
    result = rbe.remove_resource("res1", ResourceType.ENERGY)
    assert result
    assert len(pool.resources) == 0
    
    print("✅ Resource management test passed")


def test_demand_submission():
    """Test demand request submission"""
    rbe = RBEAlgorithm()
    
    # Submit demand
    request = DemandRequest(
        id="demand1",
        requester_id="user1",
        resource_type=ResourceType.ENERGY,
        quantity=500.0,
        priority=PriorityLevel.HIGH,
        location=(40.7128, -74.0060)
    )
    rbe.submit_demand(request)
    
    # Check demand submitted
    assert len(rbe.demand_requests) == 1
    assert rbe.demand_requests[0].id == "demand1"
    
    print("✅ Demand submission test passed")


def test_resource_allocation():
    """Test resource allocation"""
    rbe = RBEAlgorithm()
    
    # Add resources
    resource1 = Resource(
        id="res1",
        type=ResourceType.ENERGY,
        quantity=1000.0,
        unit="kWh",
        location=(40.7128, -74.0060)
    )
    rbe.add_resource(resource1)
    
    # Submit demand
    request = DemandRequest(
        id="demand1",
        requester_id="user1",
        resource_type=ResourceType.ENERGY,
        quantity=500.0,
        priority=PriorityLevel.HIGH,
        location=(40.7128, -74.0060)
    )
    rbe.submit_demand(request)
    
    # Allocate
    result = rbe.allocate_resources(request)
    
    # Check allocation
    assert result.success
    assert result.allocated_quantity >= 450.0  # 90% threshold
    assert len(result.resource_ids) > 0
    
    print("✅ Resource allocation test passed")


def test_distance_calculation():
    """Test distance calculation"""
    rbe = RBEAlgorithm()
    
    # Test distance between NYC and LA
    nyc = (40.7128, -74.0060)
    la = (34.0522, -118.2437)
    distance = rbe.calculate_distance(nyc, la)
    
    # Should be approximately 3940 km
    assert 3900 < distance < 4000
    
    # Test distance between same location
    same_distance = rbe.calculate_distance(nyc, nyc)
    assert same_distance == 0.0
    
    print("✅ Distance calculation test passed")


def test_nearest_resources():
    """Test finding nearest resources"""
    rbe = RBEAlgorithm()
    
    # Add resources at different locations
    resource1 = Resource(
        id="res1",
        type=ResourceType.ENERGY,
        quantity=500.0,
        unit="kWh",
        location=(40.7128, -74.0060)  # NYC
    )
    resource2 = Resource(
        id="res2",
        type=ResourceType.ENERGY,
        quantity=500.0,
        unit="kWh",
        location=(34.0522, -118.2437)  # LA
    )
    rbe.add_resource(resource1)
    rbe.add_resource(resource2)
    
    # Find nearest to NYC
    nearest = rbe.find_nearest_resources(
        ResourceType.ENERGY,
        (40.7128, -74.0060),
        100.0
    )
    
    # Should find NYC resource
    assert len(nearest) == 1
    assert nearest[0][0].id == "res1"
    
    print("✅ Nearest resources test passed")


def test_equilibrium_score():
    """Test equilibrium score calculation"""
    rbe = RBEAlgorithm()
    
    # Add resources and demands
    resource = Resource(
        id="res1",
        type=ResourceType.ENERGY,
        quantity=1000.0,
        unit="kWh",
        location=(40.7128, -74.0060)
    )
    rbe.add_resource(resource)
    
    request = DemandRequest(
        id="demand1",
        requester_id="user1",
        resource_type=ResourceType.ENERGY,
        quantity=500.0,
        priority=PriorityLevel.HIGH,
        location=(40.7128, -74.0060)
    )
    rbe.submit_demand(request)
    
    # Allocate
    result = rbe.allocate_resources(request)
    
    # Calculate equilibrium score
    score = rbe.calculate_equilibrium_score()
    
    # Should be high (good equilibrium)
    assert 0.5 <= score <= 1.0
    
    print("✅ Equilibrium score test passed")


def test_optimization_recommendations():
    """Test optimization recommendations"""
    rbe = RBEAlgorithm()
    
    # Add resources
    resource = Resource(
        id="res1",
        type=ResourceType.ENERGY,
        quantity=100.0,
        unit="kWh",
        location=(40.7128, -74.0060)
    )
    rbe.add_resource(resource)
    
    # Submit high demand
    request = DemandRequest(
        id="demand1",
        requester_id="user1",
        resource_type=ResourceType.ENERGY,
        quantity=1000.0,
        priority=PriorityLevel.CRITICAL,
        location=(40.7128, -74.0060)
    )
    rbe.submit_demand(request)
    
    # Get recommendations
    recommendations = rbe.optimize_distribution()
    
    # Should recommend increasing production
    assert recommendations["total_recommendations"] > 0
    assert any(
        rec["action"] == "increase_production"
        for rec in recommendations["recommendations"]
    )
    
    print("✅ Optimization recommendations test passed")


def test_resource_status():
    """Test resource status retrieval"""
    rbe = RBEAlgorithm()
    
    # Add resource
    resource = Resource(
        id="res1",
        type=ResourceType.ENERGY,
        quantity=1000.0,
        unit="kWh",
        location=(40.7128, -74.0060)
    )
    rbe.add_resource(resource)
    
    # Get status
    status = rbe.get_resource_status()
    
    # Check energy status
    assert "energy" in status
    assert status["energy"]["available_quantity"] == 1000.0
    assert status["energy"]["resource_count"] == 1
    
    print("✅ Resource status test passed")


def test_demand_status():
    """Test demand status retrieval"""
    rbe = RBEAlgorithm()
    
    # Submit demands
    request1 = DemandRequest(
        id="demand1",
        requester_id="user1",
        resource_type=ResourceType.ENERGY,
        quantity=500.0,
        priority=PriorityLevel.CRITICAL,
        location=(40.7128, -74.0060)
    )
    request2 = DemandRequest(
        id="demand2",
        requester_id="user2",
        resource_type=ResourceType.ENERGY,
        quantity=300.0,
        priority=PriorityLevel.MEDIUM,
        location=(40.7128, -74.0060)
    )
    rbe.submit_demand(request1)
    rbe.submit_demand(request2)
    
    # Get status
    status = rbe.get_demand_status()
    
    # Check status
    assert status["pending_count"] == 2
    assert len(status["pending_requests"]) == 2
    
    print("✅ Demand status test passed")


def test_renewable_resources():
    """Test renewable resource regeneration"""
    rbe = RBEAlgorithm()
    
    # Add renewable resource
    resource = Resource(
        id="res1",
        type=ResourceType.ENERGY,
        quantity=100.0,
        unit="kWh",
        location=(40.7128, -74.0060),
        renewable=True,
        regeneration_rate=10.0  # 10 kWh per day
    )
    rbe.add_resource(resource)
    
    # Regenerate
    rbe.regenerate_resources()
    
    # Check regeneration
    pool = rbe.resource_pools[ResourceType.ENERGY]
    assert pool.get_available_quantity() == 110.0  # 100 + 10
    
    print("✅ Renewable resources test passed")


def test_process_all_demands():
    """Test processing all demands"""
    rbe = RBEAlgorithm()
    
    # Add resources
    resource = Resource(
        id="res1",
        type=ResourceType.ENERGY,
        quantity=1000.0,
        unit="kWh",
        location=(40.7128, -74.0060)
    )
    rbe.add_resource(resource)
    
    # Submit multiple demands
    request1 = DemandRequest(
        id="demand1",
        requester_id="user1",
        resource_type=ResourceType.ENERGY,
        quantity=400.0,
        priority=PriorityLevel.CRITICAL,
        location=(40.7128, -74.0060)
    )
    request2 = DemandRequest(
        id="demand2",
        requester_id="user2",
        resource_type=ResourceType.ENERGY,
        quantity=300.0,
        priority=PriorityLevel.HIGH,
        location=(40.7128, -74.0060)
    )
    rbe.submit_demand(request1)
    rbe.submit_demand(request2)
    
    # Process all
    results = rbe.process_all_demands()
    
    # Check results
    assert len(results) == 2
    assert all(result.success for result in results)
    
    print("✅ Process all demands test passed")


if __name__ == "__main__":
    test_rbe_initialization()
    test_resource_management()
    test_demand_submission()
    test_resource_allocation()
    test_distance_calculation()
    test_nearest_resources()
    test_equilibrium_score()
    test_optimization_recommendations()
    test_resource_status()
    test_demand_status()
    test_renewable_resources()
    test_process_all_demands()
    print("\n🎉 All RBE algorithm tests passed!")
