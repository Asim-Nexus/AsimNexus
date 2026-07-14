"""
STATUS: REAL — Phase 4 Priority 1: Chaos Fallback Integration Test

Tests the DePIN bridge's ability to gracefully fall back through
hardware protocol layers when the primary protocol fails.

Scenario: WiFi Direct fail → auto-fallback to Bluetooth → LoRaWAN
This simulates real-world conditions in rural Nepal where mesh nodes
may lose WiFi connectivity and must fall back to lower-bandwidth protocols.

Reference: DDIA Chapter 8 ("The Trouble with Distributed Systems"),
           Netflix Chaos Monkey pattern
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.depin_bridge import DePINBridge, get_depin_bridge, reset_depin_bridge
from core.mesh.hardware_drivers.driver_manager import DriverManager, get_driver_manager, reset_driver_manager

# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_state():
    """Reset singletons before each test."""
    reset_depin_bridge()
    reset_driver_manager()
    yield
    reset_depin_bridge()
    reset_driver_manager()

@pytest.fixture
async def depin_bridge():
    """Get a fresh DePINBridge singleton."""
    bridge = get_depin_bridge()
    return bridge

@pytest.fixture
async def driver_manager():
    """Get a fresh DriverManager singleton."""
    dm = get_driver_manager()
    return dm

# ── Chaos Fallback Tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_wifi_direct_failure_fallbacks_to_bluetooth(depin_bridge, driver_manager):
    """
    Chaos Test 1: WiFi Direct fails → auto-fallback to Bluetooth.

    Simulates a scenario where a DePIN node in a remote Nepal village
    loses WiFi connectivity. The system should automatically detect
    the failure and route the message via Bluetooth instead.
    """
    # Register a node with WiFi Direct + Bluetooth support
    node = await depin_bridge.register_node(
        node_id="test-node-001",
        location="Gorkha, Nepal",
        protocols=["wifi_direct", "bluetooth", "lorawan"],
        hardware_capabilities={"storage_gb": 10, "compute_cores": 2},
    )
    assert node["status"] == "registered"

    # Mock WiFi Direct driver to fail
    with patch.object(
        driver_manager, "send_via_protocol", wraps=driver_manager.send_via_protocol
    ) as mock_send:
        # Make WiFi Direct raise an exception
        async def _failing_send(protocol, node_id, message):
            if protocol == "wifi_direct":
                raise ConnectionError("WiFi Direct signal lost — node out of range")
            # Bluetooth and LoRaWAN work fine
            return {"status": "sent", "protocol": protocol, "node_id": node_id}

        mock_send.side_effect = _failing_send

        # Attempt to route a message — should fall back to Bluetooth
        result = await depin_bridge.route_message(
            sender_id="test-node-001",
            recipient_id="test-node-002",
            message={"type": "ping", "payload": "hello"},
            preferred_protocol="wifi_direct",
        )

        # Verify fallback occurred
        assert result["status"] == "sent"
        assert result["protocol_used"] == "bluetooth"
        assert result["fallback_chain"] == ["wifi_direct", "bluetooth"]

@pytest.mark.asyncio
async def test_full_chaos_fallback_chain(depin_bridge, driver_manager):
    """
    Chaos Test 2: Full fallback chain — WiFi Direct → Bluetooth → LoRaWAN.

    Simulates the worst-case scenario where both WiFi Direct AND Bluetooth
    are unavailable. The system must fall all the way back to LoRaWAN
    (long-range, low-bandwidth radio).
    """
    # Register a node with all three protocols
    node = await depin_bridge.register_node(
        node_id="test-node-003",
        location="Mustang, Nepal",
        protocols=["wifi_direct", "bluetooth", "lorawan"],
        hardware_capabilities={"storage_gb": 5, "compute_cores": 1},
    )
    assert node["status"] == "registered"

    # Mock all protocols to fail except LoRaWAN
    with patch.object(
        driver_manager, "send_via_protocol", wraps=driver_manager.send_via_protocol
    ) as mock_send:
        call_count = 0

        async def _cascading_fail(protocol, node_id, message):
            nonlocal call_count
            call_count += 1
            if protocol == "wifi_direct":
                raise ConnectionError("WiFi Direct unavailable")
            if protocol == "bluetooth":
                raise ConnectionError("Bluetooth pairing failed")
            # LoRaWAN succeeds
            return {"status": "sent", "protocol": "lorawan", "node_id": node_id}

        mock_send.side_effect = _cascading_fail

        # Attempt to route — should cascade through all fallbacks
        result = await depin_bridge.route_message(
            sender_id="test-node-003",
            recipient_id="test-node-004",
            message={"type": "emergency_alert", "payload": {"severity": "high"}},
            preferred_protocol="wifi_direct",
        )

        # Verify full cascade
        assert result["status"] == "sent"
        assert result["protocol_used"] == "lorawan"
        assert result["fallback_chain"] == ["wifi_direct", "bluetooth", "lorawan"]
        assert call_count == 3  # All three protocols were tried

@pytest.mark.asyncio
async def test_all_protocols_fail_returns_error(depin_bridge, driver_manager):
    """
    Chaos Test 3: All protocols fail → graceful error with diagnostics.

    Simulates a complete network outage where no protocol is available.
    The system should return a clear error with diagnostic information
    rather than crashing or hanging indefinitely.
    """
    # Register a node
    await depin_bridge.register_node(
        node_id="test-node-005",
        location="Remote Area, Nepal",
        protocols=["wifi_direct", "bluetooth", "lorawan"],
        hardware_capabilities={"storage_gb": 1, "compute_cores": 1},
    )

    # Mock ALL protocols to fail
    with patch.object(
        driver_manager, "send_via_protocol", wraps=driver_manager.send_via_protocol
    ) as mock_send:
        async def _all_fail(protocol, node_id, message):
            raise ConnectionError(f"{protocol} unavailable")

        mock_send.side_effect = _all_fail

        # Attempt to route — should fail gracefully
        result = await depin_bridge.route_message(
            sender_id="test-node-005",
            recipient_id="test-node-006",
            message={"type": "data", "payload": "test"},
            preferred_protocol="wifi_direct",
        )

        # Verify graceful failure with diagnostics
        assert result["status"] == "failed"
        assert "error" in result
        assert "fallback_chain" in result
        assert len(result["fallback_chain"]) == 3  # All three tried
        assert result["protocol_used"] is None

@pytest.mark.asyncio
async def test_chaos_broadcast_with_partial_failure(depin_bridge, driver_manager):
    """
    Chaos Test 4: Broadcast with partial protocol failure.

    Simulates a broadcast message where some recipients are reachable
    via WiFi Direct but others require Bluetooth fallback.
    """
    # Register multiple nodes with different protocol support
    await depin_bridge.register_node(
        node_id="node-a", location="Kathmandu", protocols=["wifi_direct", "bluetooth"]
    )
    await depin_bridge.register_node(
        node_id="node-b", location="Pokhara", protocols=["wifi_direct"]
    )
    await depin_bridge.register_node(
        node_id="node-c", location="Chitwan", protocols=["bluetooth", "lorawan"]
    )

    # Mock: WiFi Direct works for node-b, fails for node-c
    with patch.object(
        driver_manager, "send_via_protocol", wraps=driver_manager.send_via_protocol
    ) as mock_send:
        async def _partial_fail(protocol, node_id, message):
            if protocol == "wifi_direct" and node_id == "node-c":
                raise ConnectionError("node-c out of WiFi range")
            return {"status": "sent", "protocol": protocol, "node_id": node_id}

        mock_send.side_effect = _partial_fail

        # Broadcast to all nodes
        result = await depin_bridge.broadcast_message(
            sender_id="node-a",
            message={"type": "sync", "payload": "data"},
            preferred_protocol="wifi_direct",
        )

        # Verify broadcast results
        assert result["status"] == "completed"
        assert result["total_nodes"] == 3
        assert result["successful_nodes"] == 3  # All got through via some protocol
        assert result["protocols_used"] == ["wifi_direct", "bluetooth"]

@pytest.mark.asyncio
async def test_chaos_recovery_after_fallback(depin_bridge, driver_manager):
    """
    Chaos Test 5: Recovery after fallback — primary protocol comes back online.

    Simulates a node that falls back to Bluetooth, then WiFi Direct
    recovers. The system should detect recovery and prefer the
    higher-bandwidth protocol on the next attempt.
    """
    await depin_bridge.register_node(
        node_id="node-recovery",
        location="Lalitpur",
        protocols=["wifi_direct", "bluetooth"],
    )

    # First attempt: WiFi Direct fails → falls back to Bluetooth
    with patch.object(
        driver_manager, "send_via_protocol", wraps=driver_manager.send_via_protocol
    ) as mock_send:
        call_log = []

        async def _recovery_scenario(protocol, node_id, message):
            call_log.append(protocol)
            if protocol == "wifi_direct" and len(call_log) <= 1:
                raise ConnectionError("WiFi Direct temporarily down")
            return {"status": "sent", "protocol": protocol, "node_id": node_id}

        mock_send.side_effect = _recovery_scenario

        # First message — falls back to Bluetooth
        result1 = await depin_bridge.route_message(
            sender_id="node-recovery",
            recipient_id="node-other",
            message={"type": "ping"},
            preferred_protocol="wifi_direct",
        )
        assert result1["protocol_used"] == "bluetooth"

        # Second message — WiFi Direct has recovered
        result2 = await depin_bridge.route_message(
            sender_id="node-recovery",
            recipient_id="node-other",
            message={"type": "ping"},
            preferred_protocol="wifi_direct",
        )
        assert result2["protocol_used"] == "wifi_direct"
