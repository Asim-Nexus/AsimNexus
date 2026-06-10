
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Deploy ASIM NEXUS Mesh Network Nodes
===================================
Script to deploy multiple mesh network nodes for testing
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.networking.mesh_network import get_mesh_network, ASIMMeshNetwork

async def deploy_mesh_nodes(num_nodes: int = 5):
    """Deploy multiple mesh network nodes"""
    print(f"🌐 Deploying {num_nodes} mesh network nodes...")
    
    # Create primary node
    primary = get_mesh_network(port=9000)
    await primary.start()
    print(f"✅ Primary node started: {primary.node_id}")
    
    # Create additional nodes
    nodes = []
    for i in range(num_nodes - 1):
        node = ASIMMeshNetwork(port=9001 + i)
        await node.start()
        
        # Register with primary
        node_info = {
            "node_id": node.node_id,
            "ip_address": "127.0.0.1",
            "port": 9001 + i,
            "role": "edge" if i < num_nodes - 2 else "relay",
            "capabilities": ["routing", "storage"]
        }
        primary.register_node(node_info)
        nodes.append(node)
        print(f"✅ Node {i+1} started: {node.node_id}")
    
    # Distribute some test knowledge
    print("\n📚 Distributing test knowledge...")
    for i in range(3):
        data = {"test_key": f"test_value_{i}", "index": i}
        data_id = primary.distribute_knowledge(data)
        print(f"   - Knowledge distributed: {data_id[:16]}...")
    
    # Get network stats
    print("\n📊 Network Statistics:")
    stats = primary.get_network_stats()
    print(f"   - Total nodes: {stats['total_nodes']}")
    print(f"   - Online nodes: {stats['online_nodes']}")
    print(f"   - Knowledge entries: {stats['knowledge_entries']}")
    
    # List all nodes
    print("\n📋 Node Registry:")
    all_nodes = primary.get_nodes()
    for node_id, node_info in all_nodes.items():
        print(f"   - {node_id}: {node_info['role']} ({node_info['status']})")
    
    print("\n✅ Mesh network deployment complete!")
    print(f"   Primary node: {primary.node_id}")
    print(f"   Additional nodes: {len(nodes)}")
    
    # Keep running for testing
    print("\nPress Ctrl+C to stop all nodes...")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down mesh network...")
        await primary.stop()
        for node in nodes:
            await node.stop()
        print("✅ All nodes stopped")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Deploy ASIM NEXUS mesh network nodes")
    parser.add_argument("--nodes", type=int, default=5, help="Number of nodes to deploy")
    args = parser.parse_args()
    
    try:
        asyncio.run(deploy_mesh_nodes(args.nodes))
    except KeyboardInterrupt:
        print("\n🛑 Deployment cancelled")
