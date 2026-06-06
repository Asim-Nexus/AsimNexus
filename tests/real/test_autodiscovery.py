#!/usr/bin/env python3
"""
Tests for AutoDiscovery — LAN device discovery for mesh network.

Covers:
- Peer discovery mechanisms (broadcast, multicast, mDNS)
- Discovery protocol messages (beacon, listen, parse)
- Timeout handling (discover_once with timeout)
- Network scan (one-time discovery)
- mDNS/DNS-SD fallback behavior
- Error recovery (invalid messages, socket errors)
- Callback registration and invocation
- Stale node cleanup
- Global singleton get/reset
"""

import json
import time
import socket
import threading
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, ANY

import pytest

from mesh.autodiscovery import (
    AutoDiscovery,
    NodeInfo,
    DiscoveryMethod,
    get_auto_discovery,
    reset_auto_discovery,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_global():
    """Reset the global auto-discovery singleton after each test."""
    yield
    reset_auto_discovery()


@pytest.fixture
def auto_discovery():
    """Create a fresh AutoDiscovery instance with a deterministic node_id."""
    ad = AutoDiscovery(node_id="test_node_001", port=9999)
    yield ad
    ad.stop()


# =============================================================================
# NodeInfo Tests
# =============================================================================

class TestNodeInfo:
    """Tests for the NodeInfo dataclass."""

    def test_node_info_defaults(self):
        """NodeInfo should set sensible defaults."""
        info = NodeInfo(
            node_id="node1",
            hostname="host1",
            ip_address="192.168.1.10",
            port=8000,
        )
        assert info.node_id == "node1"
        assert info.hostname == "host1"
        assert info.ip_address == "192.168.1.10"
        assert info.port == 8000
        assert info.capabilities == []
        assert info.version == "1.0.0"
        assert info.metadata == {}
        # last_seen should be an ISO-formatted string
        datetime.fromisoformat(info.last_seen)

    def test_node_info_with_all_fields(self):
        """NodeInfo should accept all fields."""
        info = NodeInfo(
            node_id="node2",
            hostname="host2",
            ip_address="10.0.0.1",
            port=9000,
            capabilities=["chat", "mesh"],
            version="2.0.0",
            metadata={"os": "linux"},
        )
        assert info.node_id == "node2"
        assert info.capabilities == ["chat", "mesh"]
        assert info.version == "2.0.0"
        assert info.metadata == {"os": "linux"}


# =============================================================================
# AutoDiscovery Init Tests
# =============================================================================

class TestAutoDiscoveryInit:
    """Tests for AutoDiscovery initialization."""

    def test_default_node_id_generation(self):
        """Should generate a node ID when none is provided."""
        ad = AutoDiscovery(port=9998)
        assert ad.node_id.startswith("node_")
        assert len(ad.node_id) > 5
        ad.stop()

    def test_custom_node_id(self):
        """Should use provided node_id."""
        ad = AutoDiscovery(node_id="custom_node", port=9997)
        assert ad.node_id == "custom_node"
        ad.stop()

    def test_initial_state(self):
        """Should start with empty discovered nodes and no callbacks."""
        ad = AutoDiscovery(node_id="state_test", port=9996)
        assert ad.discovered_nodes == {}
        assert ad.discovery_callbacks == []
        assert ad._running is False
        assert ad._socket is None
        assert ad._beacon_thread is None
        assert ad._listener_thread is None
        ad.stop()

    def test_get_node_info(self, auto_discovery):
        """get_node_info should return correct NodeInfo for this node."""
        info = auto_discovery.get_node_info()
        assert info.node_id == "test_node_001"
        assert info.hostname == socket.gethostname()
        assert info.port == 9999
        assert "mesh" in info.capabilities
        assert info.version == "2.0.0"

    def test_get_local_ip_returns_string(self, auto_discovery):
        """_get_local_ip should return a valid IP string."""
        ip = auto_discovery._get_local_ip()
        parts = ip.split(".")
        assert len(parts) == 4
        assert all(p.isdigit() for p in parts)


# =============================================================================
# Discovery Method Enum Tests
# =============================================================================

class TestDiscoveryMethod:
    """Tests for the DiscoveryMethod enum."""

    def test_enum_values(self):
        """DiscoveryMethod should have correct values."""
        assert DiscoveryMethod.BROADCAST.value == "broadcast"
        assert DiscoveryMethod.MULTICAST.value == "multicast"
        assert DiscoveryMethod.MDNS.value == "mdns"


# =============================================================================
# Discovery Core Logic Tests
# =============================================================================

class TestDiscoveryCallbacks:
    """Tests for discovery callback mechanism."""

    def test_register_callback(self, auto_discovery):
        """on_discovery should add a callback."""
        def cb(node_info):
            pass

        auto_discovery.on_discovery(cb)
        assert len(auto_discovery.discovery_callbacks) == 1
        assert auto_discovery.discovery_callbacks[0] == cb

    def test_register_multiple_callbacks(self, auto_discovery):
        """Multiple callbacks should all be registered."""
        def cb1(ni):
            pass
        def cb2(ni):
            pass

        auto_discovery.on_discovery(cb1)
        auto_discovery.on_discovery(cb2)
        assert len(auto_discovery.discovery_callbacks) == 2

    def test_callback_invoked_on_discovery(self, auto_discovery):
        """Callbacks should be called when a node is discovered."""
        received = []

        def cb(node_info):
            received.append(node_info)

        auto_discovery.on_discovery(cb)

        node = NodeInfo(
            node_id="remote_1",
            hostname="remote_host",
            ip_address="192.168.1.20",
            port=8000,
        )
        auto_discovery._on_node_discovered(node)

        assert len(received) == 1
        assert received[0].node_id == "remote_1"

    def test_callback_error_does_not_block(self, auto_discovery):
        """A failing callback should not prevent other callbacks from running."""
        received = []

        def failing_cb(ni):
            raise ValueError("oops")

        def good_cb(ni):
            received.append(ni)

        auto_discovery.on_discovery(failing_cb)
        auto_discovery.on_discovery(good_cb)

        node = NodeInfo(
            node_id="remote_2",
            hostname="remote2",
            ip_address="10.0.0.2",
            port=8000,
        )
        # Should not raise
        auto_discovery._on_node_discovered(node)

        assert len(received) == 1


class TestDiscoveredNodesManagement:
    """Tests for managing the discovered nodes map."""

    def test_new_node_added(self, auto_discovery):
        """A new node should be added to discovered_nodes."""
        node = NodeInfo(
            node_id="new_node",
            hostname="new_host",
            ip_address="10.0.0.5",
            port=8000,
        )
        auto_discovery._on_node_discovered(node)

        assert "new_node" in auto_discovery.discovered_nodes
        assert auto_discovery.discovered_nodes["new_node"].ip_address == "10.0.0.5"

    def test_existing_node_updated(self, auto_discovery):
        """An existing node's IP/port should be updated."""
        node = NodeInfo(
            node_id="existing",
            hostname="host",
            ip_address="10.0.0.1",
            port=8000,
        )
        auto_discovery._on_node_discovered(node)

        # Discover again with new IP
        node2 = NodeInfo(
            node_id="existing",
            hostname="host",
            ip_address="10.0.0.2",
            port=9000,
        )
        auto_discovery._on_node_discovered(node2)

        assert auto_discovery.discovered_nodes["existing"].ip_address == "10.0.0.2"
        assert auto_discovery.discovered_nodes["existing"].port == 9000

    def test_get_discovered_nodes(self, auto_discovery):
        """get_discovered_nodes should return all discovered nodes."""
        n1 = NodeInfo(node_id="a", hostname="ha", ip_address="1.1.1.1", port=8000)
        n2 = NodeInfo(node_id="b", hostname="hb", ip_address="2.2.2.2", port=8000)
        auto_discovery._on_node_discovered(n1)
        auto_discovery._on_node_discovered(n2)

        nodes = auto_discovery.get_discovered_nodes()
        assert len(nodes) == 2
        ids = {n.node_id for n in nodes}
        assert ids == {"a", "b"}

    def test_self_discovery_not_filtered_by_handler(self, auto_discovery):
        """_on_node_discovered does NOT filter self (filtering is in listener methods).
        Verify the handler adds self to discovered nodes."""
        node = NodeInfo(
            node_id=auto_discovery.node_id,
            hostname=auto_discovery.hostname,
            ip_address=auto_discovery.ip_address,
            port=auto_discovery.port,
        )
        auto_discovery._on_node_discovered(node)
        # The handler adds the node; filtering happens in _broadcast_listener / discover_once
        assert auto_discovery.node_id in auto_discovery.discovered_nodes

    def test_self_discovery_ignored_in_listener_message(self, auto_discovery):
        """The broadcast listener should skip messages from self."""
        msg = {
            "node_id": auto_discovery.node_id,
            "hostname": auto_discovery.hostname,
            "ip_address": auto_discovery.ip_address,
            "port": auto_discovery.port,
        }
        # Simulate what _broadcast_listener does: skip if node_id == self.node_id
        if msg.get("node_id") != auto_discovery.node_id:
            node_info = NodeInfo(
                node_id=msg["node_id"],
                hostname=msg["hostname"],
                ip_address=msg["ip_address"],
                port=msg["port"],
            )
            auto_discovery._on_node_discovered(node_info)
        # Because we skipped, the node should NOT be in discovered_nodes
        assert auto_discovery.node_id not in auto_discovery.discovered_nodes


class TestStaleNodeCleanup:
    """Tests for cleanup_stale_nodes."""

    def test_cleanup_removes_old_nodes(self, auto_discovery):
        """Nodes older than max_age should be removed.
        Note: _on_node_discovered overwrites last_seen, so we inject directly."""
        old_time = (datetime.utcnow() - timedelta(seconds=600)).isoformat()
        old_node = NodeInfo(
            node_id="old_node",
            hostname="old",
            ip_address="10.0.0.1",
            port=8000,
            last_seen=old_time,
        )
        fresh_node = NodeInfo(
            node_id="fresh_node",
            hostname="fresh",
            ip_address="10.0.0.2",
            port=8000,
        )
        # Inject directly into discovered_nodes (bypass _on_node_discovered which overwrites last_seen)
        auto_discovery.discovered_nodes["old_node"] = old_node
        auto_discovery.discovered_nodes["fresh_node"] = fresh_node

        stale = auto_discovery.cleanup_stale_nodes(max_age_seconds=300)
        assert "old_node" in stale
        assert "fresh_node" not in stale
        assert "old_node" not in auto_discovery.discovered_nodes
        assert "fresh_node" in auto_discovery.discovered_nodes

    def test_cleanup_no_stale_nodes(self, auto_discovery):
        """No nodes should be removed if all are fresh."""
        node = NodeInfo(
            node_id="fresh",
            hostname="fresh",
            ip_address="10.0.0.1",
            port=8000,
        )
        auto_discovery._on_node_discovered(node)

        stale = auto_discovery.cleanup_stale_nodes(max_age_seconds=3600)
        assert stale == []

    def test_cleanup_with_empty_registry(self, auto_discovery):
        """Cleanup on empty registry should return empty list."""
        stale = auto_discovery.cleanup_stale_nodes(max_age_seconds=60)
        assert stale == []

    def test_cleanup_invalid_date_handling(self, auto_discovery):
        """Nodes with invalid last_seen should be skipped gracefully."""
        node = NodeInfo(
            node_id="bad_date",
            hostname="bad",
            ip_address="10.0.0.1",
            port=8000,
            last_seen="not-a-date",
        )
        auto_discovery._on_node_discovered(node)

        # Should not raise
        stale = auto_discovery.cleanup_stale_nodes(max_age_seconds=60)
        assert "bad_date" not in stale


# =============================================================================
# Start / Stop Tests
# =============================================================================

class TestStartStop:
    """Tests for starting and stopping discovery."""

    def test_start_broadcast_creates_threads(self, auto_discovery):
        """Starting broadcast should create listener and beacon threads."""
        auto_discovery.start(DiscoveryMethod.BROADCAST)
        assert auto_discovery._running is True
        assert auto_discovery._listener_thread is not None
        assert auto_discovery._listener_thread.is_alive()
        assert auto_discovery._beacon_thread is not None
        assert auto_discovery._beacon_thread.is_alive()
        auto_discovery.stop()

    def test_stop_halts_threads(self, auto_discovery):
        """Stopping should halt threads and close socket."""
        auto_discovery.start(DiscoveryMethod.BROADCAST)
        auto_discovery.stop()
        assert auto_discovery._running is False

    def test_double_start_noop(self, auto_discovery):
        """Starting twice should not create duplicate threads."""
        auto_discovery.start(DiscoveryMethod.BROADCAST)
        t1 = auto_discovery._listener_thread
        auto_discovery.start(DiscoveryMethod.BROADCAST)
        t2 = auto_discovery._listener_thread
        # Should be the same thread object since second start is a noop
        assert t1 is t2
        auto_discovery.stop()

    def test_start_multicast(self, auto_discovery):
        """Starting multicast should work."""
        auto_discovery.start(DiscoveryMethod.MULTICAST)
        assert auto_discovery._running is True
        auto_discovery.stop()

    def test_start_mdns_fallback_on_missing_lib(self, auto_discovery):
        """mDNS start should fall back to broadcast if zeroconf is missing."""
        with patch.dict('sys.modules', {'zeroconf': None}):
            auto_discovery.start(DiscoveryMethod.MDNS)
            # Should have started broadcast as fallback
            assert auto_discovery._running is True
            auto_discovery.stop()


# =============================================================================
# Message Processing Tests
# =============================================================================

class TestMessageProcessing:
    """Tests for processing discovery protocol messages."""

    def test_parse_valid_broadcast_message(self, auto_discovery):
        """A valid JSON beacon message should be parsed into a NodeInfo."""
        msg = {
            "node_id": "sender_1",
            "hostname": "sender_host",
            "ip_address": "192.168.1.99",
            "port": 8000,
            "capabilities": ["chat"],
            "version": "2.0.0",
            "metadata": {}
        }
        # Simulate what _broadcast_listener does
        node_info = NodeInfo(
            node_id=msg["node_id"],
            hostname=msg["hostname"],
            ip_address=msg["ip_address"],
            port=msg["port"],
            capabilities=msg.get("capabilities", []),
            version=msg.get("version", "1.0.0"),
            metadata=msg.get("metadata", {}),
        )
        assert node_info.node_id == "sender_1"
        assert node_info.ip_address == "192.168.1.99"

    def test_parse_message_missing_optional_fields(self, auto_discovery):
        """A message missing optional fields should use defaults."""
        msg = {
            "node_id": "minimal",
            "hostname": "min",
            "ip_address": "10.0.0.1",
            "port": 8000,
        }
        node_info = NodeInfo(
            node_id=msg["node_id"],
            hostname=msg["hostname"],
            ip_address=msg["ip_address"],
            port=msg["port"],
            capabilities=msg.get("capabilities", []),
            version=msg.get("version", "1.0.0"),
            metadata=msg.get("metadata", {}),
        )
        assert node_info.capabilities == []
        assert node_info.version == "1.0.0"


# =============================================================================
# discover_once Tests
# =============================================================================

class TestDiscoverOnce:
    """Tests for discover_once — one-time discovery scan."""

    @patch("mesh.autodiscovery.socket.socket")
    def test_discover_once_broadcasts_and_listens(self, mock_socket_ctor, auto_discovery):
        """discover_once should broadcast a beacon and listen for responses."""
        mock_sock = MagicMock()
        mock_socket_ctor.return_value = mock_sock

        # Simulate one response then timeout
        response_data = json.dumps({
            "node_id": "peer_1",
            "hostname": "peer_host",
            "ip_address": "10.0.0.50",
            "port": 8001,
            "capabilities": ["mesh"],
            "version": "2.0.0",
            "metadata": {},
        }).encode()

        mock_sock.recvfrom.side_effect = [
            (response_data, ("10.0.0.50", 8001)),
            socket.timeout("timed out"),
        ]

        nodes = auto_discovery.discover_once(timeout=2)

        # Should have sent a broadcast
        mock_sock.sendto.assert_called_once()
        # Should have parsed the response
        assert len(nodes) == 1
        assert nodes[0].node_id == "peer_1"

    @patch("mesh.autodiscovery.socket.socket")
    def test_discover_once_timeout_no_nodes(self, mock_socket_ctor, auto_discovery):
        """discover_once should handle timeout gracefully with no nodes."""
        mock_sock = MagicMock()
        mock_socket_ctor.return_value = mock_sock

        # Immediate timeout
        mock_sock.recvfrom.side_effect = socket.timeout("timed out")

        nodes = auto_discovery.discover_once(timeout=1)
        assert nodes == []

    @patch("mesh.autodiscovery.socket.socket")
    def test_discover_once_invalid_json_ignored(self, mock_socket_ctor, auto_discovery):
        """Invalid JSON responses should be silently ignored."""
        mock_sock = MagicMock()
        mock_socket_ctor.return_value = mock_sock

        mock_sock.recvfrom.side_effect = [
            (b"not json", ("10.0.0.1", 8000)),
            socket.timeout("timed out"),
        ]

        nodes = auto_discovery.discover_once(timeout=1)
        assert nodes == []

    @patch("mesh.autodiscovery.socket.socket")
    def test_discover_once_self_message_ignored(self, mock_socket_ctor, auto_discovery):
        """Messages from self should be ignored during discover_once."""
        mock_sock = MagicMock()
        mock_socket_ctor.return_value = mock_sock

        self_msg = json.dumps({
            "node_id": auto_discovery.node_id,
            "hostname": auto_discovery.hostname,
            "ip_address": auto_discovery.ip_address,
            "port": auto_discovery.port,
        }).encode()

        mock_sock.recvfrom.side_effect = [
            (self_msg, (auto_discovery.ip_address, auto_discovery.port)),
            socket.timeout("timed out"),
        ]

        nodes = auto_discovery.discover_once(timeout=1)
        assert nodes == []

    @patch("mesh.autodiscovery.socket.socket")
    def test_discover_once_socket_error_handled(self, mock_socket_ctor, auto_discovery):
        """Socket errors during discover_once should be handled gracefully."""
        mock_sock = MagicMock()
        mock_socket_ctor.return_value = mock_sock
        mock_sock.sendto.side_effect = OSError("Network error")

        # Should not raise
        nodes = auto_discovery.discover_once(timeout=1)
        assert nodes == []


# =============================================================================
# Singleton Tests
# =============================================================================

class TestSingleton:
    """Tests for the global singleton functions."""

    def test_get_auto_discovery_creates_singleton(self):
        """get_auto_discovery should create and return the same instance."""
        reset_auto_discovery()
        ad1 = get_auto_discovery(node_id="singleton_test", port=7777)
        ad2 = get_auto_discovery()
        assert ad1 is ad2
        assert ad1.node_id == "singleton_test"
        reset_auto_discovery()

    def test_reset_auto_discovery_stops_and_clears(self):
        """reset_auto_discovery should stop and clear the global instance."""
        ad = get_auto_discovery(node_id="reset_test", port=7776)
        ad.start(DiscoveryMethod.BROADCAST)
        reset_auto_discovery()
        ad2 = get_auto_discovery()
        assert ad2 is not ad
        assert ad2._running is False
        reset_auto_discovery()


# =============================================================================
# Error Recovery Tests
# =============================================================================

class TestErrorRecovery:
    """Tests for error recovery in discovery operations."""

    def test_start_fallback_on_mdns_import_error(self, auto_discovery):
        """mDNS start should fall back to broadcast on ImportError."""
        # Patch zeroconf import to be missing, so _start_mdns_discovery falls back internally
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'zeroconf':
                raise ImportError("No zeroconf available")
            return original_import(name, *args, **kwargs)

        with patch.dict('sys.modules', {'zeroconf': None}):
            with patch('builtins.__import__', side_effect=mock_import):
                auto_discovery.start(DiscoveryMethod.MDNS)
                # Should have started broadcast as fallback
                assert auto_discovery._running is True
                auto_discovery.stop()

    def test_stop_without_start(self, auto_discovery):
        """Stopping without starting should not raise."""
        auto_discovery.stop()  # Should be safe
        assert auto_discovery._running is False

    def test_stop_multiple_times(self, auto_discovery):
        """Multiple stops should be safe."""
        auto_discovery.start(DiscoveryMethod.BROADCAST)
        auto_discovery.stop()
        auto_discovery.stop()  # Second stop
        assert auto_discovery._running is False
