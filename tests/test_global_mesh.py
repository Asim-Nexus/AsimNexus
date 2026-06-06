
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test Global Mesh Network Integration
====================================

Test the Global Mesh Network component.
"""

import asyncio
from core.global_mesh import GlobalMeshNetwork, get_global_mesh_network, Region


async def test_global_mesh_network():
    """Test Global Mesh Network"""
    print("=" * 60)
    print("Testing Global Mesh Network")
    print("=" * 60)
    
    mesh = get_global_mesh_network()
    
    # Check default bootstrap nodes
    print("\n✅ Checking default bootstrap nodes...")
    status = mesh.get_network_status()
    print(f"  Total bootstrap nodes: {status['bootstrap_nodes']['total']}")
    print(f"  Online bootstrap nodes: {status['bootstrap_nodes']['online']}")
    print(f"  Total capacity: {status['bootstrap_nodes']['total_capacity']}")
    
    print("\n  Bootstrap nodes by region:")
    for region, count in status['bootstrap_nodes']['by_region'].items():
        print(f"    {region}: {count}")
    
    # Add edge node
    print("\n✅ Adding edge node...")
    node_id = mesh.add_edge_node(
        region=Region.ASIA,
        location=(27.7172, 85.3240),  # Kathmandu
        compute_capacity=200,
        memory_gb=32,
        gpu_available=True
    )
    print(f"  Added edge node: {node_id}")
    
    # Find optimal edge node
    print("\n✅ Finding optimal edge node...")
    optimal_node = mesh.find_optimal_edge_node(
        required_compute=100,
        required_memory=16,
        required_gpu=True,
        region=Region.ASIA
    )
    if optimal_node:
        print(f"  Found optimal node: {optimal_node.node_id}")
        print(f"  Compute capacity: {optimal_node.compute_capacity}")
        print(f"  GPU available: {optimal_node.gpu_available}")
    
    # Find nearest bootstrap node
    print("\n✅ Finding nearest bootstrap node...")
    nearest = mesh.get_nearest_bootstrap_node(
        location=(27.7172, 85.3240),  # Kathmandu
        max_distance_km=5000
    )
    if nearest:
        print(f"  Nearest node: {nearest.node_id}")
        print(f"  Region: {nearest.region.value}")
        print(f"  Host: {nearest.host}")
    
    # Calculate mesh route
    print("\n✅ Calculating mesh route...")
    route = mesh.calculate_mesh_route("node_1", "node_2")
    if route:
        print(f"  Route ID: {route.route_id}")
        print(f"  Path: {' -> '.join(route.path)}")
        print(f"  Latency: {route.latency_ms}ms")
    
    # Health check
    print("\n✅ Running health check...")
    await mesh.health_check_all_nodes()
    
    # Get final status
    print("\n📊 Final network status:")
    status = mesh.get_network_status()
    print(f"  Bootstrap nodes: {status['bootstrap_nodes']['online']}/{status['bootstrap_nodes']['total']}")
    print(f"  Edge nodes: {status['edge_nodes']['online']}/{status['edge_nodes']['total']}")
    print(f"  Edge compute utilization: {status['edge_nodes']['utilization_percent']:.1f}%")
    
    print("\n" + "=" * 60)
    print("✅ Global Mesh Network Test Passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_global_mesh_network())
