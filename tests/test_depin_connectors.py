
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test ASIMNEXUS DePIN Connectors
=================================

Tests for DePIN network connectors:
- Uplink: Decentralized internet connectivity
- Daylight: Decentralized energy distribution
- DIMO: Connected vehicles and IoT
"""

import asyncio
from core.depin.uplink_connector import (
    UplinkConnector,
    UplinkNode,
    UplinkNodeState
)
from core.depin.daylight_connector import (
    DaylightConnector,
    EnergyDevice,
    DeviceType,
    EnergyState
)
from core.depin.dimo_connector import (
    DIMOConnector,
    Vehicle,
    VehicleState,
    DataType
)


async def test_uplink_connector():
    """Test Uplink connector"""
    connector = UplinkConnector(api_key="test_key")
    
    # Test initialization
    assert connector.api_key == "test_key"
    assert not connector.connected
    
    # Test connection (will fail without real API, but that's OK for testing)
    try:
        await connector.connect()
    except Exception:
        pass  # Connection may fail in test environment
    
    # Test node registration (works without connection)
    node = await connector.register_node(
        node_id="node1",
        address="192.168.1.100",
        bandwidth_capacity=1000.0
    )
    assert node.id == "node1"
    assert node.bandwidth_capacity == 1000.0
    
    # Test traffic offloading
    result = await connector.offload_traffic("node1", 500.0)
    assert result
    assert node.current_usage == 500.0
    
    # Test release traffic
    result = await connector.release_traffic("node1", 200.0)
    assert result
    assert node.current_usage == 300.0
    
    # Test rewards claiming
    rewards = await connector.claim_rewards("node1")
    assert rewards > 0
    
    # Test network stats
    stats = connector.get_network_stats()
    assert stats["total_nodes"] == 1
    assert stats["total_bandwidth_capacity_mbps"] == 1000.0
    
    # Test disconnect
    await connector.disconnect()
    assert not connector.connected
    
    print("✅ Uplink connector test passed")


async def test_daylight_connector():
    """Test Daylight connector"""
    connector = DaylightConnector(api_key="test_key")
    
    # Test initialization
    assert connector.api_key == "test_key"
    
    # Test connection (will fail without real API, but that's OK for testing)
    try:
        await connector.connect()
    except Exception:
        pass  # Connection may fail in test environment
    
    # Test device registration (works without connection)
    device = await connector.register_device(
        device_id="solar1",
        device_type=DeviceType.SOLAR_INVERTER,
        capacity_kwh=10.0
    )
    assert device.id == "solar1"
    assert device.capacity_kwh == 10.0
    
    # Test energy output update
    result = await connector.update_energy_output(
        "solar1",
        5.0,
        EnergyState.PRODUCING
    )
    assert result
    assert device.current_output_kwh == 5.0
    
    # Test energy selling
    result = await connector.sell_energy("solar1", 3.0, 0.15)
    assert result["success"]
    
    # Test energy buying
    result = await connector.buy_energy(2.0, 0.20)
    assert result["success"]
    
    # Test carbon credits claiming
    credits = await connector.claim_carbon_credits("solar1")
    assert credits >= 0
    
    # Test network stats
    stats = connector.get_network_stats()
    assert stats["total_devices"] == 1
    assert stats["total_capacity_kwh"] == 10.0
    
    print("✅ Daylight connector test passed")


async def test_dimo_connector():
    """Test DIMO connector"""
    connector = DIMOConnector(api_key="test_key")
    
    # Test initialization
    assert connector.api_key == "test_key"
    
    # Test connection (will fail without real API, but that's OK for testing)
    try:
        await connector.connect()
    except Exception:
        pass  # Connection may fail in test environment
    
    # Test vehicle registration (works without connection)
    vehicle = await connector.register_vehicle(
        vehicle_id="vehicle1",
        vin="1HGCM82633A123456",
        make="Honda",
        model="Civic",
        year=2020
    )
    assert vehicle.id == "vehicle1"
    assert vehicle.make == "Honda"
    assert vehicle.model == "Civic"
    
    # Test telemetry update
    result = await connector.update_telemetry("vehicle1", DataType.SPEED, 65.0)
    assert result
    assert vehicle.get_telemetry(DataType.SPEED) == 65.0
    
    # Test data sharing
    result = await connector.share_data(
        "vehicle1",
        [DataType.LOCATION, DataType.SPEED],
        60
    )
    assert result["success"]
    
    # Test permission grant
    result = await connector.grant_permission("vehicle1", "location", "service_provider")
    assert result
    
    # Test permission revoke
    result = await connector.revoke_permission("vehicle1", "location", "service_provider")
    assert result
    
    # Test rewards claiming
    rewards = await connector.claim_rewards("vehicle1")
    assert rewards >= 0
    
    # Test network stats
    stats = connector.get_network_stats()
    assert stats["total_vehicles"] == 1
    assert "Honda" in stats["vehicle_makes"]
    
    print("✅ DIMO connector test passed")


def test_uplink_node():
    """Test Uplink node"""
    node = UplinkNode(
        id="test_node",
        address="192.168.1.1",
        bandwidth_capacity=1000.0
    )
    
    # Test available bandwidth
    assert node.available_bandwidth() == 1000.0
    
    # Test utilization rate
    node.current_usage = 500.0
    assert node.utilization_rate() == 50.0
    
    print("✅ Uplink node test passed")


def test_energy_device():
    """Test energy device"""
    device = EnergyDevice(
        id="solar_panel",
        device_type=DeviceType.SOLAR_INVERTER,
        capacity_kwh=10.0
    )
    
    # Test available capacity
    assert device.available_capacity() == 10.0
    
    # Test utilization rate
    device.current_output_kwh = 5.0
    assert device.utilization_rate() == 50.0
    
    print("✅ Energy device test passed")


def test_vehicle():
    """Test vehicle"""
    vehicle = Vehicle(
        id="car1",
        vin="TEST123",
        make="Tesla",
        model="Model 3",
        year=2023
    )
    
    # Test telemetry
    vehicle.add_telemetry(DataType.SPEED, 70.0)
    assert vehicle.get_telemetry(DataType.SPEED) == 70.0
    
    print("✅ Vehicle test passed")


if __name__ == "__main__":
    test_uplink_node()
    test_energy_device()
    test_vehicle()
    asyncio.run(test_uplink_connector())
    asyncio.run(test_daylight_connector())
    asyncio.run(test_dimo_connector())
    print("\n🎉 All DePIN connector tests passed!")
