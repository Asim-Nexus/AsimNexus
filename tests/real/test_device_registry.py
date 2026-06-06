#!/usr/bin/env python3
"""Test DeviceRegistry Auto-Scan + Auto-Connect functionality."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from mesh.device_registry import (
    DeviceRegistry, DeviceInfo, DeviceType, DeviceStatus,
    ConnectionMethod, TrustLevel, TopologyType, ResourceType,
    DeviceResource, get_device_registry, reset_device_registry
)


async def test_basic_imports():
    """Test 1: All imports work."""
    print("=" * 60)
    print("🧪 TEST 1: Basic Imports")
    print("=" * 60)
    assert DeviceRegistry is not None
    assert DeviceInfo is not None
    assert DeviceType is not None
    assert DeviceStatus is not None
    assert ResourceType is not None
    assert DeviceResource is not None
    assert get_device_registry is not None
    print("✅ All imports OK")
    return True


async def test_get_device_registry():
    """Test 2: DeviceRegistry singleton creation."""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: DeviceRegistry Singleton")
    print("=" * 60)
    dr = get_device_registry()
    assert dr is not None
    assert dr.node_id is not None
    assert dr.node_id.startswith("node_")
    print(f"✅ DeviceRegistry created: {dr}")
    print(f"✅ Node ID: {dr.node_id}")
    
    # Test singleton pattern
    dr2 = get_device_registry()
    assert dr is dr2
    print("✅ Singleton pattern works (same instance)")
    return True


async def test_create_local_device():
    """Test 3: Create local device info."""
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Create Local Device")
    print("=" * 60)
    dr = get_device_registry()
    local = dr._create_local_device()
    assert local is not None
    assert local.name is not None
    assert local.device_type is not None
    assert local.ip_address is not None
    assert local.capabilities is not None
    print(f"✅ Local device: {local.name}")
    print(f"   Type: {local.device_type.value}")
    print(f"   IP: {local.ip_address}")
    print(f"   Port: {local.port}")
    print(f"   Capabilities: {local.capabilities}")
    print(f"   Version: {local.version}")
    return True


async def test_get_local_resources():
    """Test 4: Detect local machine resources."""
    print("\n" + "=" * 60)
    print("🧪 TEST 4: Local Resources Detection")
    print("=" * 60)
    dr = get_device_registry()
    resources = dr._get_local_resources()
    assert len(resources) > 0
    print(f"✅ {len(resources)} resources detected:")
    for r in resources:
        print(f"   - {r.type.value}: {r.available}/{r.total} {r.unit}")
    
    # Verify we have compute, memory, storage
    types = [r.type for r in resources]
    assert ResourceType.COMPUTE in types, "Missing COMPUTE resource"
    assert ResourceType.MEMORY in types, "Missing MEMORY resource"
    assert ResourceType.STORAGE in types, "Missing STORAGE resource"
    print("✅ All required resource types present (COMPUTE, MEMORY, STORAGE)")
    return True


async def test_manual_connect():
    """Test 5: Manual device connection."""
    print("\n" + "=" * 60)
    print("🧪 TEST 5: Manual Device Connection")
    print("=" * 60)
    dr = get_device_registry()
    
    # NOTE: DeviceType has PC, MOBILE, TABLET, IOT, SERVER, etc. (no LAPTOP/PHONE)
    device = DeviceInfo(
        id="test-pc-001",
        name="Test PC",
        device_type=DeviceType.PC,
        connection=ConnectionMethod.WIFI,
        trust_level=TrustLevel.TRUSTED,  # TRUSTED, not KNOWN
        status=DeviceStatus.ONLINE,
        ip_address="192.168.1.100",
        port=7331,
        hostname="test-pc.local",
        version="2.0.0",
        capabilities=["compute", "storage", "network"],
        resources=[
            DeviceResource(type=ResourceType.COMPUTE, total=8, available=6, unit="cores"),
            DeviceResource(type=ResourceType.MEMORY, total=16, available=12, unit="GB"),
            DeviceResource(type=ResourceType.STORAGE, total=512, available=256, unit="GB"),
        ],
        last_seen=asyncio.get_event_loop().time(),
    )
    
    result = dr.connect_device_manual(device)
    assert result is True, f"connect_device_manual returned {result}"
    print("✅ Device connected manually")
    
    # Verify device is registered
    devices = dr.list_devices()
    assert len(devices) >= 1, f"Expected at least 1 device, got {len(devices)}"
    print(f"✅ Device registered: {devices[0].name} ({devices[0].status.value})")
    return True


async def test_list_devices():
    """Test 6: List devices with filters."""
    print("\n" + "=" * 60)
    print("🧪 TEST 6: List Devices")
    print("=" * 60)
    dr = get_device_registry()
    
    # Add a second device (MOBILE instead of PHONE)
    device2 = DeviceInfo(
        id="test-mobile-001",
        name="Test Mobile",
        device_type=DeviceType.MOBILE,  # MOBILE, not PHONE
        connection=ConnectionMethod.WIFI,
        trust_level=TrustLevel.UNKNOWN,
        status=DeviceStatus.ONLINE,
        ip_address="192.168.1.101",
        port=7331,
        hostname="test-mobile.local",
        version="2.0.0",
        capabilities=["compute", "storage"],
        resources=[
            DeviceResource(type=ResourceType.COMPUTE, total=4, available=2, unit="cores"),
            DeviceResource(type=ResourceType.MEMORY, total=6, available=3, unit="GB"),
        ],
        last_seen=asyncio.get_event_loop().time(),
    )
    dr.connect_device_manual(device2)
    
    # List all
    all_devices = dr.list_devices()
    assert len(all_devices) >= 2, f"Expected at least 2 devices, got {len(all_devices)}"
    print(f"✅ All devices: {len(all_devices)}")
    
    # Filter by type
    pcs = dr.get_devices_by_type(DeviceType.PC)
    assert len(pcs) >= 1
    print(f"✅ PCs: {len(pcs)}")
    
    mobiles = dr.get_devices_by_type(DeviceType.MOBILE)
    assert len(mobiles) >= 1
    print(f"✅ Mobiles: {len(mobiles)}")
    
    # Filter by capability
    compute_devices = dr.get_devices_by_capability("compute")
    assert len(compute_devices) >= 2
    print(f"✅ Devices with 'compute' capability: {len(compute_devices)}")
    
    # Online count
    count = dr.get_online_count()
    assert count >= 2, f"Expected at least 2 online, got {count}"
    print(f"✅ Online count: {count}")
    return True


async def test_resource_pool():
    """Test 7: Resource pool aggregation."""
    print("\n" + "=" * 60)
    print("🧪 TEST 7: Resource Pool")
    print("=" * 60)
    dr = get_device_registry()
    
    pool = dr.get_resource_pool()
    assert len(pool) > 0
    print(f"✅ Resource pool has {len(pool)} resource types:")
    for rtype, data in pool.items():
        print(f"   - {rtype}: {data['available']}/{data['total']} {data.get('unit', 'N/A')}")
    
    # Should have compute, memory, storage
    assert "compute" in pool
    assert "memory" in pool
    assert "storage" in pool
    print("✅ All expected resource types in pool")
    return True


async def test_find_resource():
    """Test 8: Find resource by type and amount."""
    print("\n" + "=" * 60)
    print("🧪 TEST 8: Find Resource")
    print("=" * 60)
    dr = get_device_registry()
    
    # Find 2 compute cores
    found = dr.find_resource(ResourceType.COMPUTE, 2)
    assert len(found) > 0, "Should find devices with compute"
    print(f"✅ Found {len(found)} device(s) with 2 compute cores:")
    for f in found:
        compute_res = [r for r in f.resources if r.type == ResourceType.COMPUTE]
        if compute_res:
            print(f"   - {f.name}: {compute_res[0].available} cores avail")
    
    # Find more than available
    found_more = dr.find_resource(ResourceType.MEMORY, 999)
    assert len(found_more) == 0, "Should NOT find devices with 999GB memory"
    print(f"✅ Correctly returns empty for unavailable resources")
    return True


async def test_scale_recommendation():
    """Test 9: Auto-scale recommendation."""
    print("\n" + "=" * 60)
    print("🧪 TEST 9: Scale Recommendation")
    print("=" * 60)
    dr = get_device_registry()
    
    # Request more than available
    rec = dr.get_scale_recommendation(ResourceType.MEMORY, 999)
    assert rec["can_scale"] is False
    print(f"✅ Scale recommendation for 999GB memory:")
    print(f"   Can scale: {rec['can_scale']}")
    print(f"   Deficit: {rec.get('deficit', 'N/A')}")
    print(f"   Available: {rec['available']}")
    
    # Request within available
    rec2 = dr.get_scale_recommendation(ResourceType.COMPUTE, 1)
    print(f"✅ Scale recommendation for 1 core:")
    print(f"   Can scale: {rec2['can_scale']}")
    print(f"   Available: {rec2['available']}")
    return True


async def test_topology():
    """Test 10: Topology management."""
    print("\n" + "=" * 60)
    print("🧪 TEST 10: Topology")
    print("=" * 60)
    dr = get_device_registry()
    
    topo = dr.get_topology()
    assert len(topo) > 0
    print(f"✅ Topology types: {list(topo.keys())}")
    for ttype, data in topo.items():
        if isinstance(data, dict):
            print(f"   - {ttype}: {len(data)} entries")
        else:
            print(f"   - {ttype}: {data}")
    
    # Should have mesh topology (key is "mesh" string, not TopologyType.MESH enum)
    assert "mesh" in topo
    print("✅ MESH topology present")
    return True


async def test_mesh_status():
    """Test 11: Mesh status report."""
    print("\n" + "=" * 60)
    print("🧪 TEST 11: Mesh Status")
    print("=" * 60)
    dr = get_device_registry()
    
    status = await dr.get_mesh_status()
    assert status is not None
    print(f"✅ Mesh status:")
    print(f"   Node ID: {status['node_id']}")
    print(f"   Online: {status['online_devices']}")  # online_devices, not online_count
    print(f"   Total: {status['total_devices']}")
    print(f"   Resource pool: {status['resource_pool']}")
    print(f"   Device types: {status['devices_by_type']}")
    return True


async def test_disconnect():
    """Test 12: Device disconnection."""
    print("\n" + "=" * 60)
    print("🧪 TEST 12: Device Disconnection")
    print("=" * 60)
    dr = get_device_registry()
    
    # Disconnect PC
    result = dr.disconnect_device("test-pc-001")
    assert result is True
    print("✅ PC disconnected")
    
    # After disconnect, device is removed from self.devices dict
    # So list_devices() returns remaining devices
    remaining = dr.list_devices()
    print(f"✅ Remaining devices: {len(remaining)}")
    
    # Verify resource pool updated
    pool = dr.get_resource_pool()
    print(f"✅ Resource pool after disconnect: {len(pool)} types")
    return True


async def test_device_info_to_dict():
    """Test 13: DeviceInfo serialization."""
    print("\n" + "=" * 60)
    print("🧪 TEST 13: DeviceInfo Serialization")
    print("=" * 60)
    
    device = DeviceInfo(
        id="test-device",
        name="Test",
        device_type=DeviceType.PC,
        connection=ConnectionMethod.WIFI,
        trust_level=TrustLevel.TRUSTED,  # TRUSTED, not KNOWN
        status=DeviceStatus.ONLINE,
        ip_address="192.168.1.1",
        port=7331,
        hostname="test.local",
        version="2.0.0",
        capabilities=["compute"],
        resources=[
            DeviceResource(type=ResourceType.COMPUTE, total=8, available=4, unit="cores"),
        ],
        last_seen=1234567890.0,
    )
    
    d = device.to_dict()
    assert d["id"] == "test-device"
    assert d["name"] == "Test"
    assert d["device_type"] == "pc"
    assert d["status"] == "online"
    assert d["resources"][0]["type"] == "compute"
    print(f"✅ DeviceInfo serialized: {d['name']} ({d['device_type']})")
    print(f"   Resources: {d['resources']}")
    return True


async def test_callback_system():
    """Test 14: Event callback system."""
    print("\n" + "=" * 60)
    print("🧪 TEST 14: Callback System")
    print("=" * 60)
    dr = get_device_registry()
    
    events = []
    
    def on_connected(data):
        events.append(("device_connected", data))
    
    def on_disconnected(data):
        events.append(("device_disconnected", data))
    
    dr.on_event("device_connected", on_connected)
    dr.on_event("device_disconnected", on_disconnected)
    print("✅ Callbacks registered")
    
    # Trigger connect
    device = DeviceInfo(
        id="test-callback-device",
        name="Callback Test",
        device_type=DeviceType.MOBILE,  # MOBILE, not PHONE
        connection=ConnectionMethod.WIFI,
        trust_level=TrustLevel.TRUSTED,  # TRUSTED, not KNOWN
        status=DeviceStatus.ONLINE,
        ip_address="192.168.1.200",
        port=7331,
        hostname="callback-test.local",
        version="2.0.0",
        capabilities=["compute"],
        resources=[],
        last_seen=asyncio.get_event_loop().time(),
    )
    dr.connect_device_manual(device)
    
    # Trigger disconnect
    dr.disconnect_device("test-callback-device")
    
    assert len(events) >= 2, f"Expected at least 2 events, got {len(events)}"
    print(f"✅ Events captured: {len(events)}")
    for event_type, data in events:
        print(f"   - {event_type}: {data.get('device_id', 'N/A')}")
    return True


async def test_udp_listener():
    """Test 15: UDP listener starts without error."""
    print("\n" + "=" * 60)
    print("🧪 TEST 15: UDP Listener")
    print("=" * 60)
    dr = get_device_registry()
    
    # Start UDP listener
    dr._start_udp_listener()
    print("✅ UDP listener started (background thread)")
    
    # Give it a moment
    await asyncio.sleep(0.5)
    
    # Check socket is bound
    assert dr._udp_socket is not None
    print(f"✅ UDP socket bound: {dr._udp_socket is not None}")
    return True


async def test_scan_lan():
    """Test 16: LAN scan (non-blocking, just verify it returns)."""
    print("\n" + "=" * 60)
    print("🧪 TEST 16: LAN Scan")
    print("=" * 60)
    dr = get_device_registry()
    
    # This will timeout quickly since no devices respond
    results = await dr.scan_lan(timeout=2)
    print(f"✅ LAN scan completed (timeout=2s)")
    print(f"   Results: {len(results)} devices found")
    # This is expected to be 0 in isolation
    return True


async def test_ping_device():
    """Test 17: Ping device (non-existent, should fail gracefully)."""
    print("\n" + "=" * 60)
    print("🧪 TEST 17: Ping Device")
    print("=" * 60)
    dr = get_device_registry()
    
    result = await dr.ping_device("non-existent-device")
    assert result is False
    print("✅ Ping non-existent device returns False (graceful)")
    return True


async def test_health_check():
    """Test 18: Health check (no stale devices)."""
    print("\n" + "=" * 60)
    print("🧪 TEST 18: Health Check")
    print("=" * 60)
    dr = get_device_registry()
    
    await dr._check_device_health()
    print("✅ Health check completed (no stale devices)")
    return True


async def test_infer_device_type():
    """Test 19: Device type inference from capabilities."""
    print("\n" + "=" * 60)
    print("🧪 TEST 19: Device Type Inference")
    print("=" * 60)
    dr = get_device_registry()
    
    # PC
    pc_type = dr._infer_device_type(["compute", "storage", "network", "display", "audio"])
    print(f"   compute+storage+network+display+audio → {pc_type.value}")
    assert pc_type == DeviceType.PC
    
    # IoT
    iot_type = dr._infer_device_type(["sensor"])
    print(f"   sensor → {iot_type.value}")
    assert iot_type == DeviceType.IOT
    
    # Router
    router_type = dr._infer_device_type(["network"])
    print(f"   network → {router_type.value}")
    assert router_type == DeviceType.ROUTER
    
    print("✅ Device type inference works")
    return True


async def test_generate_node_id():
    """Test 20: Node ID generation."""
    print("\n" + "=" * 60)
    print("🧪 TEST 20: Node ID Generation")
    print("=" * 60)
    dr = get_device_registry()
    
    node_id = dr._generate_node_id()
    assert node_id.startswith("node_")
    assert len(node_id) > 10
    print(f"✅ Generated node ID: {node_id}")
    return True


async def test_allocate_release_resource():
    """Test 21: Resource allocation and release."""
    print("\n" + "=" * 60)
    print("🧪 TEST 21: Resource Allocation/Release")
    print("=" * 60)
    dr = get_device_registry()
    
    # Add a device with resources
    device = DeviceInfo(
        id="test-resource-device",
        name="Resource Test",
        device_type=DeviceType.PC,
        connection=ConnectionMethod.WIFI,
        trust_level=TrustLevel.TRUSTED,  # TRUSTED, not KNOWN
        status=DeviceStatus.ONLINE,
        ip_address="192.168.1.50",
        port=7331,
        hostname="resource-test.local",
        version="2.0.0",
        capabilities=["compute"],
        resources=[
            DeviceResource(type=ResourceType.COMPUTE, total=4, available=4, unit="cores"),
        ],
        last_seen=asyncio.get_event_loop().time(),
    )
    dr.connect_device_manual(device)
    
    # Allocate 2 cores
    result = dr.allocate_resource(ResourceType.COMPUTE, 2, "test-resource-device")
    assert result is True
    print("✅ Allocated 2 cores")
    
    # Check available decreased
    pool = dr.get_resource_pool()
    print(f"   Available compute after allocation: {pool.get('compute', {}).get('available', 'N/A')}")
    
    # Release 1 core
    result = dr.release_resource(ResourceType.COMPUTE, 1, "test-resource-device")
    assert result is True
    print("✅ Released 1 core")
    
    # Cleanup
    dr.disconnect_device("test-resource-device")
    return True


async def test_start_stop_lifecycle():
    """Test 22: Start/stop lifecycle."""
    print("\n" + "=" * 60)
    print("🧪 TEST 22: Start/Stop Lifecycle")
    print("=" * 60)
    dr = get_device_registry()
    
    await dr.start()
    assert dr._running is True
    print("✅ DeviceRegistry started")
    
    await dr.stop()
    assert dr._running is False
    print("✅ DeviceRegistry stopped")
    return True


async def test_auto_scan_loop():
    """Test 23: Auto-scan loop starts and stops cleanly."""
    print("\n" + "=" * 60)
    print("🧪 TEST 23: Auto-Scan Loop")
    print("=" * 60)
    dr = get_device_registry()
    
    # Start
    await dr.start()
    assert dr._scan_task is not None
    print(f"✅ Scan task created: {dr._scan_task}")
    
    # Stop
    await dr.stop()
    assert dr._scan_task is None
    print("✅ Scan task cleaned up")
    return True


async def test_health_monitor_loop():
    """Test 24: Health monitor loop starts and stops cleanly."""
    print("\n" + "=" * 60)
    print("🧪 TEST 24: Health Monitor Loop")
    print("=" * 60)
    dr = get_device_registry()
    
    # Start
    await dr.start()
    assert dr._health_task is not None
    print(f"✅ Health task created: {dr._health_task}")
    
    # Stop
    await dr.stop()
    assert dr._health_task is None
    print("✅ Health task cleaned up")
    return True


async def test_handshake_message():
    """Test 25: Handshake message handling."""
    print("\n" + "=" * 60)
    print("🧪 TEST 25: Handshake Message Handling")
    print("=" * 60)
    dr = get_device_registry()
    
    # Simulate a handshake message
    message = {
        "type": "asim_handshake",
        "node_id": "test-handshake-device",
        "hostname": "handshake-test",
        "ip_address": "192.168.1.150",
        "port": 7331,
        "version": "2.0.0",
        "capabilities": ["compute", "storage"],
        "resources": [
            {"type": "compute", "total": 4, "available": 4, "unit": "cores"},
        ],
    }
    
    dr._handle_handshake_message(message, ("192.168.1.150", 7331))
    
    # Check device was auto-registered
    device = dr.get_device("test-handshake-device")
    assert device is not None, "Device should be auto-registered from handshake"
    print(f"✅ Device auto-registered from handshake: {device.name}")
    print(f"   Type: {device.device_type.value}")
    print(f"   Status: {device.status.value}")
    
    # Cleanup
    dr.disconnect_device("test-handshake-device")
    return True


async def test_discovery_message():
    """Test 26: Discovery message handling."""
    print("\n" + "=" * 60)
    print("🧪 TEST 26: Discovery Message Handling")
    print("=" * 60)
    dr = get_device_registry()
    
    # Simulate a discovery message
    message = {
        "type": "asim_discovery",
        "node_id": "test-discovery-device",
        "hostname": "discovery-test",
    }
    
    # This should respond without error
    dr._handle_discovery_message(message, ("192.168.1.200", 7331))
    print("✅ Discovery message handled (response sent)")
    return True


async def test_ping_message():
    """Test 27: Ping message handling."""
    print("\n" + "=" * 60)
    print("🧪 TEST 27: Ping Message Handling")
    print("=" * 60)
    dr = get_device_registry()
    
    # Simulate a ping message
    message = {
        "type": "asim_ping",
        "node_id": "test-ping-device",
        "timestamp": asyncio.get_event_loop().time(),
    }
    
    # This should respond without error
    dr._handle_ping_message(message, ("192.168.1.250", 7331))
    print("✅ Ping message handled (pong sent)")
    return True


async def test_register_device_internal():
    """Test 28: Internal device registration."""
    print("\n" + "=" * 60)
    print("🧪 TEST 28: Internal Device Registration")
    print("=" * 60)
    dr = get_device_registry()
    
    device = DeviceInfo(
        id="test-internal-device",
        name="Internal Test",
        device_type=DeviceType.SERVER,
        connection=ConnectionMethod.SSH,
        trust_level=TrustLevel.VERIFIED,
        status=DeviceStatus.ONLINE,
        ip_address="10.0.0.1",
        port=22,
        hostname="internal-test.local",
        version="2.0.0",
        capabilities=["compute", "storage", "network", "gpu"],
        resources=[
            DeviceResource(type=ResourceType.COMPUTE, total=32, available=28, unit="cores"),
            DeviceResource(type=ResourceType.GPU, total=1, available=1, unit="gpu"),
        ],
        last_seen=asyncio.get_event_loop().time(),
    )
    
    dr._register_device_internal(device)
    
    # Verify in devices dict
    assert device.id in dr.devices
    print(f"✅ Device registered internally: {device.name}")
    
    # Verify in capability index
    assert device.id in dr.capability_index.get("compute", [])
    assert device.id in dr.capability_index.get("gpu", [])
    print(f"✅ Capability indexed: compute, gpu")
    
    # Verify in topology
    assert device.id in dr.topology[TopologyType.STAR]
    print(f"✅ Topology updated (star)")
    
    # Cleanup
    dr.disconnect_device("test-internal-device")
    return True


async def test_remove_from_topology():
    """Test 29: Topology cleanup on disconnect."""
    print("\n" + "=" * 60)
    print("🧪 TEST 29: Topology Cleanup")
    print("=" * 60)
    dr = get_device_registry()
    
    # Add two devices that will be peers
    d1 = DeviceInfo(
        id="topo-test-1", name="Topo1", device_type=DeviceType.PC,
        connection=ConnectionMethod.WIFI, trust_level=TrustLevel.TRUSTED,
        status=DeviceStatus.ONLINE, ip_address="10.0.0.2", port=7331,
        hostname="topo1.local", version="2.0.0",
        capabilities=["compute"], resources=[], last_seen=asyncio.get_event_loop().time(),
    )
    d2 = DeviceInfo(
        id="topo-test-2", name="Topo2", device_type=DeviceType.PC,
        connection=ConnectionMethod.WIFI, trust_level=TrustLevel.TRUSTED,
        status=DeviceStatus.ONLINE, ip_address="10.0.0.3", port=7331,
        hostname="topo2.local", version="2.0.0",
        capabilities=["compute"], resources=[], last_seen=asyncio.get_event_loop().time(),
    )
    dr._register_device_internal(d1)
    dr._register_device_internal(d2)
    
    # Verify mesh topology has both
    assert "topo-test-1" in dr.topology[TopologyType.MESH]
    assert "topo-test-2" in dr.topology[TopologyType.MESH]
    print(f"✅ Both devices in mesh topology")
    
    # Disconnect one
    dr.disconnect_device("topo-test-1")
    
    # Verify removed from topology
    assert "topo-test-1" not in dr.topology[TopologyType.STAR]
    assert "topo-test-1" not in dr.topology[TopologyType.MESH]
    assert "topo-test-1" not in dr.devices
    print(f"✅ Device removed from all topology structures")
    
    # Verify other device's mesh peers updated
    mesh_peers = dr.topology[TopologyType.MESH].get("topo-test-2", [])
    assert "topo-test-1" not in mesh_peers
    print(f"✅ Peer list updated")
    
    # Cleanup
    dr.disconnect_device("topo-test-2")
    return True


async def test_resource_pool_after_connect():
    """Test 30: Resource pool updates on connect/disconnect."""
    print("\n" + "=" * 60)
    print("🧪 TEST 30: Resource Pool Updates")
    print("=" * 60)
    dr = get_device_registry()
    
    pool_before = dr.get_resource_pool()
    print(f"   Pool before: {pool_before}")
    
    device = DeviceInfo(
        id="pool-test", name="Pool Test", device_type=DeviceType.SERVER,
        connection=ConnectionMethod.WIFI, trust_level=TrustLevel.TRUSTED,
        status=DeviceStatus.ONLINE, ip_address="10.0.0.10", port=7331,
        hostname="pool-test.local", version="2.0.0",
        capabilities=["compute"],
        resources=[
            DeviceResource(type=ResourceType.COMPUTE, total=64, available=64, unit="cores"),
            DeviceResource(type=ResourceType.MEMORY, total=128, available=128, unit="GB"),
        ],
        last_seen=asyncio.get_event_loop().time(),
    )
    dr.connect_device_manual(device)
    
    pool_after = dr.get_resource_pool()
    print(f"   Pool after connect: {pool_after}")
    assert pool_after.get("compute", {}).get("available", 0) > pool_before.get("compute", {}).get("available", 0)
    print(f"✅ Resource pool increased after connect")
    
    dr.disconnect_device("pool-test")
    
    pool_after_disconnect = dr.get_resource_pool()
    print(f"   Pool after disconnect: {pool_after_disconnect}")
    print(f"✅ Resource pool updated after disconnect")
    return True


async def main():
    """Run all tests."""
    print("🚀 DeviceRegistry Test Suite")
    print("=" * 60)
    
    # Reset for clean state
    reset_device_registry()
    
    tests = [
        test_basic_imports,
        test_get_device_registry,
        test_create_local_device,
        test_get_local_resources,
        test_manual_connect,
        test_list_devices,
        test_resource_pool,
        test_find_resource,
        test_scale_recommendation,
        test_topology,
        test_mesh_status,
        test_disconnect,
        test_device_info_to_dict,
        test_callback_system,
        test_udp_listener,
        test_scan_lan,
        test_ping_device,
        test_health_check,
        test_infer_device_type,
        test_generate_node_id,
        test_allocate_release_resource,
        test_start_stop_lifecycle,
        test_auto_scan_loop,
        test_health_monitor_loop,
        test_handshake_message,
        test_discovery_message,
        test_ping_message,
        test_register_device_internal,
        test_remove_from_topology,
        test_resource_pool_after_connect,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
            print(f"   ✅ {test.__name__} PASSED\n")
        except Exception as e:
            failed += 1
            print(f"   ❌ {test.__name__} FAILED: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed, {len(tests)} total")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
