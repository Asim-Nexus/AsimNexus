
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test ASIMNEXUS P2P Network
===========================

Tests for P2P networking:
- DHT node operations
- Peer discovery
- Message routing
- Mesh network
"""

import asyncio
from core.network.p2p_network import (
    P2PNetwork,
    DHTNode,
    MeshRouter,
    Peer,
    NetworkMessage,
    PeerState
)


def test_dht_node():
    """Test DHT node operations"""
    dht = DHTNode()
    
    # Test node ID generation
    assert dht.node_id is not None
    assert len(dht.node_id) == 40  # SHA-1 hex
    
    # Test distance calculation
    peer1 = Peer(id="1" * 40, address=("localhost", 8001))
    peer2 = Peer(id="2" * 40, address=("localhost", 8002))
    
    dht.add_peer(peer1)
    dht.add_peer(peer2)
    
    # Test closest peers
    closest = dht.find_closest_peers("1" * 40, count=5)
    assert len(closest) >= 1
    
    # Test key-value storage
    dht.store("test_key", {"data": "test_value"})
    value = dht.get("test_key")
    assert value is not None
    assert value["data"] == "test_value"
    
    # Test key removal
    assert dht.remove("test_key")
    assert dht.get("test_key") is None
    
    print("✅ DHT node test passed")


def test_mesh_router():
    """Test mesh router"""
    router = MeshRouter("local_node")
    
    # Add peers
    peer1 = Peer(id="peer1", address=("localhost", 8001), state=PeerState.CONNECTED)
    peer2 = Peer(id="peer2", address=("localhost", 8002), state=PeerState.CONNECTED)
    
    router.add_peer(peer1)
    router.add_peer(peer2)
    
    # Test peer addition
    assert "peer1" in router.peers
    assert "peer2" in router.peers
    
    # Test routing
    message = NetworkMessage(
        id="msg1",
        from_peer="local_node",
        to_peer="peer1",
        message_type="test",
        payload={"data": "test"}
    )
    
    route = router.route_message(message)
    assert "peer1" in route
    
    # Test broadcast
    broadcast_recipients = router.broadcast(message)
    assert len(broadcast_recipients) == 2
    
    # Test peer removal
    assert router.remove_peer("peer1")
    assert "peer1" not in router.peers
    
    print("✅ Mesh router test passed")


def test_network_message():
    """Test network message serialization"""
    message = NetworkMessage(
        id="msg1",
        from_peer="peer1",
        to_peer="peer2",
        message_type="test_type",
        payload={"key": "value"}
    )
    
    # Test to_dict
    msg_dict = message.to_dict()
    assert msg_dict["from_peer"] == "peer1"
    assert msg_dict["to_peer"] == "peer2"
    
    # Test to_json
    msg_json = message.to_json()
    assert msg_json is not None
    
    # Test from_json
    reconstructed = NetworkMessage.from_json(msg_json)
    assert reconstructed.id == message.id
    assert reconstructed.from_peer == message.from_peer
    assert reconstructed.to_peer == message.to_peer
    
    # Test TTL decrement
    assert message.ttl == 10
    message.ttl -= 1
    assert message.ttl == 9
    
    print("✅ Network message test passed")


async def test_p2p_network():
    """Test P2P network"""
    network = P2PNetwork(host="127.0.0.1", port=6881)
    
    # Test initialization
    assert network.node_id is not None
    assert network.host == "127.0.0.1"
    assert network.port == 6881
    
    # Test DHT operations
    network.dht_store("key1", {"value": "data1"})
    value = network.dht_get("key1")
    assert value is not None
    assert value["value"] == "data1"
    
    # Test peer addition
    peer = Peer(id="a" * 40, address=("localhost", 8001))
    network.mesh.add_peer(peer)
    network.dht.add_peer(peer)
    
    # Test get peers
    peers = network.get_peers()
    assert len(peers) >= 1
    
    # Test status
    status = network.get_status()
    assert status["node_id"] == network.node_id
    assert status["peers"] >= 1
    
    print("✅ P2P network test passed")


def test_peer_distance():
    """Test peer distance calculation"""
    peer1 = Peer(id="a" * 40, address=("localhost", 8001))
    peer2 = Peer(id="b" * 40, address=("localhost", 8002))
    
    # Test distance calculation
    distance = peer1.distance_to(peer2.id)
    assert distance >= 0
    assert isinstance(distance, int)
    
    # Test self distance (should be 0)
    self_distance = peer1.distance_to(peer1.id)
    assert self_distance == 0
    
    print("✅ Peer distance test passed")


def test_k_bucket_routing():
    """Test k-bucket routing in DHT"""
    dht = DHTNode(k=3)  # Small k for testing
    
    # Add multiple peers
    for i in range(10):
        peer = Peer(id=str(i).zfill(40), address=("localhost", 8000 + i))
        dht.add_peer(peer)
    
    # Test closest peers
    closest = dht.find_closest_peers("0" * 40, count=5)
    assert len(closest) <= 5
    
    print("✅ K-bucket routing test passed")


if __name__ == "__main__":
    test_dht_node()
    test_mesh_router()
    test_network_message()
    test_peer_distance()
    test_k_bucket_routing()
    asyncio.run(test_p2p_network())
    print("\n🎉 All P2P network tests passed!")
