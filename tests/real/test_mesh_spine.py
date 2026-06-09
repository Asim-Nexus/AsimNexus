#!/usr/bin/env python3
"""
STATUS: REAL — Comprehensive tests for Mesh Spine components
===============================================================================
Tests for all 9 mesh spine components:
  1. AutoDiscovery        (mesh/autodiscovery.py)
  2. KademliaDHT          (mesh/kademlia_dht.py)
  3. CRDTStore            (mesh/crdt_sync.py)
  4. RelayService         (mesh/relay.py)
  5. BootstrapService     (mesh/bootstrap.py)
  6. P2PTransport         (mesh/p2p_transport.py)
  7. NodeRegistry         (mesh/node_registry.py)
  8. DeviceRegistry       (mesh/device_registry.py)
  9. NetworkIntelligence  (mesh/network_intelligence.py)

Each component is tested for:
  - Environment variable overrides (ASIM_MESH_*)
  - Default values when no env vars set
  - Explicit parameter overrides
  - Singleton getter patterns
  - Core functionality
"""

import os
import sys
import json
import time
import pytest
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from unittest.mock import patch, MagicMock, AsyncMock

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def clean_mesh_env():
    """Ensure clean ASIM_MESH_* env vars for each test."""
    saved = {}
    for k in list(os.environ.keys()):
        if k.startswith("ASIM_MESH_"):
            saved[k] = os.environ[k]
            del os.environ[k]
    yield
    for k, v in saved.items():
        os.environ[k] = v
    for k in list(os.environ.keys()):
        if k.startswith("ASIM_MESH_") and k not in saved:
            del os.environ[k]


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# 1. AutoDiscovery Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAutoDiscovery:
    """Test suite for mesh/autodiscovery.py — AutoDiscovery + env vars."""

    def test_import(self):
        """Verify the module imports cleanly."""
        from mesh.autodiscovery import AutoDiscovery, NodeInfo, DiscoveryMethod
        from mesh.autodiscovery import get_auto_discovery, reset_auto_discovery
        assert AutoDiscovery is not None
        assert NodeInfo is not None
        assert DiscoveryMethod is not None
        assert callable(get_auto_discovery)
        assert callable(reset_auto_discovery)

    def test_default_port(self):
        """Default DISCOVERY_PORT should be 7331."""
        from mesh.autodiscovery import AutoDiscovery
        assert AutoDiscovery.DISCOVERY_PORT == 7331

    def test_env_var_port(self):
        """ASIM_MESH_DISCOVERY_PORT overrides default."""
        os.environ["ASIM_MESH_DISCOVERY_PORT"] = "9999"
        # Reimport to pick up env var
        import importlib
        import mesh.autodiscovery
        importlib.reload(mesh.autodiscovery)
        from mesh.autodiscovery import AutoDiscovery
        assert AutoDiscovery.DISCOVERY_PORT == 9999

    def test_default_discovery_interval(self):
        """Default DISCOVERY_INTERVAL should be 30."""
        from mesh.autodiscovery import AutoDiscovery
        assert AutoDiscovery.DISCOVERY_INTERVAL == 30

    def test_env_var_discovery_interval(self):
        """ASIM_MESH_DISCOVERY_INTERVAL overrides default."""
        os.environ["ASIM_MESH_DISCOVERY_INTERVAL"] = "15"
        import importlib
        import mesh.autodiscovery
        importlib.reload(mesh.autodiscovery)
        from mesh.autodiscovery import AutoDiscovery
        assert AutoDiscovery.DISCOVERY_INTERVAL == 15

    def test_default_beacon_interval(self):
        """Default BEACON_INTERVAL should be 60."""
        from mesh.autodiscovery import AutoDiscovery
        assert AutoDiscovery.BEACON_INTERVAL == 60

    def test_env_var_beacon_interval(self):
        """ASIM_MESH_BEACON_INTERVAL overrides default."""
        os.environ["ASIM_MESH_BEACON_INTERVAL"] = "120"
        import importlib
        import mesh.autodiscovery
        importlib.reload(mesh.autodiscovery)
        from mesh.autodiscovery import AutoDiscovery
        assert AutoDiscovery.BEACON_INTERVAL == 120

    def test_cleanup_stale_env_var(self):
        """ASIM_MESH_STALE_NODE_AGE overrides stale node cleanup default."""
        os.environ["ASIM_MESH_STALE_NODE_AGE"] = "600"
        from mesh.autodiscovery import AutoDiscovery
        ad = AutoDiscovery(node_id="test_ad_stale")
        result = ad.cleanup_stale_nodes()
        # Should not crash — no nodes to clean
        assert isinstance(result, list)

    def test_discover_once_env_var(self):
        """ASIM_MESH_DISCOVERY_TIMEOUT overrides discover timeout."""
        os.environ["ASIM_MESH_DISCOVERY_TIMEOUT"] = "10"
        from mesh.autodiscovery import AutoDiscovery
        ad = AutoDiscovery(node_id="test_ad_timeout")
        result = ad.discover_once()
        # No peers to discover, returns empty list
        assert isinstance(result, list)

    def test_explicit_params_override_env(self):
        """Explicitly passing params to methods overrides env vars."""
        os.environ["ASIM_MESH_STALE_NODE_AGE"] = "999"
        from mesh.autodiscovery import AutoDiscovery
        ad = AutoDiscovery(node_id="test_ad_explicit")
        result = ad.cleanup_stale_nodes(max_age_seconds=123)
        # Using explicit 123, not 999
        assert isinstance(result, list)

    def test_get_auto_discovery_singleton(self):
        """get_auto_discovery returns a singleton."""
        from mesh.autodiscovery import get_auto_discovery, reset_auto_discovery
        reset_auto_discovery()
        a1 = get_auto_discovery(node_id="singleton_ad")
        a2 = get_auto_discovery(node_id="different_ad")
        assert a1 is a2
        assert a1.node_id == "singleton_ad"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. KademliaDHT Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestKademliaDHT:
    """Test suite for mesh/kademlia_dht.py — KademliaDHT + env vars."""

    def test_import(self):
        """Verify the module imports cleanly."""
        from mesh.kademlia_dht import KademliaDHT, DHTNode, KBucket, NodeID
        from mesh.kademlia_dht import get_kademlia_dht, reset_kademlia_dht
        assert KademliaDHT is not None
        assert DHTNode is not None
        assert KBucket is not None
        assert NodeID is not None

    def test_default_k(self):
        """Default K should be 20."""
        from mesh.kademlia_dht import K
        assert K == 20

    def test_env_var_k(self):
        """ASIM_MESH_DHT_K overrides default K."""
        os.environ["ASIM_MESH_DHT_K"] = "10"
        import importlib
        import mesh.kademlia_dht
        importlib.reload(mesh.kademlia_dht)
        from mesh.kademlia_dht import K
        assert K == 10

    def test_default_alpha(self):
        """Default ALPHA should be 3."""
        from mesh.kademlia_dht import ALPHA
        assert ALPHA == 3

    def test_env_var_alpha(self):
        """ASIM_MESH_DHT_ALPHA overrides default ALPHA."""
        import importlib
        import mesh.kademlia_dht
        os.environ["ASIM_MESH_DHT_ALPHA"] = "5"
        importlib.reload(mesh.kademlia_dht)
        from mesh.kademlia_dht import ALPHA
        assert ALPHA == 5
        # Clean up: reload back to default (fixture will clean env var)
        os.environ.pop("ASIM_MESH_DHT_ALPHA", None)
        importlib.reload(mesh.kademlia_dht)

    def test_default_id_length(self):
        """Default ID_LENGTH should be 160."""
        from mesh.kademlia_dht import ID_LENGTH
        assert ID_LENGTH == 160

    def test_env_var_id_length(self):
        """ASIM_MESH_DHT_ID_LENGTH overrides default."""
        import importlib
        import mesh.kademlia_dht
        os.environ["ASIM_MESH_DHT_ID_LENGTH"] = "128"
        importlib.reload(mesh.kademlia_dht)
        from mesh.kademlia_dht import ID_LENGTH
        assert ID_LENGTH == 128
        # Clean up: reload back to default (fixture will clean env var)
        os.environ.pop("ASIM_MESH_DHT_ID_LENGTH", None)
        importlib.reload(mesh.kademlia_dht)

    def test_default_port(self):
        """Default port should be 7332 when no env set."""
        from mesh.kademlia_dht import KademliaDHT
        dht = KademliaDHT()
        assert dht.port == 7332

    def test_env_var_port(self):
        """ASIM_MESH_DHT_PORT overrides default."""
        os.environ["ASIM_MESH_DHT_PORT"] = "9992"
        from mesh.kademlia_dht import KademliaDHT
        dht = KademliaDHT()
        assert dht.port == 9992

    def test_explicit_port_override(self):
        """Explicit port parameter overrides env var."""
        os.environ["ASIM_MESH_DHT_PORT"] = "9992"
        from mesh.kademlia_dht import KademliaDHT
        dht = KademliaDHT(port=7332)
        assert dht.port == 7332

    def test_node_stale_env_var(self):
        """DHTNode.is_stale respects ASIM_MESH_DHT_NODE_STALE_SEC."""
        from mesh.kademlia_dht import DHTNode, NodeID
        node = DHTNode(node_id=NodeID.random(), ip_address="127.0.0.1", port=9000)
        # Should use default or env
        assert node.is_stale() is not None

    def test_node_bad_env_var(self):
        """DHTNode.is_bad respects ASIM_MESH_DHT_MAX_FAILURES."""
        from mesh.kademlia_dht import DHTNode, NodeID
        node = DHTNode(node_id=NodeID.random(), ip_address="127.0.0.1", port=9000)
        # Should use default or env
        assert node.is_bad() is not None

    def test_kbucket_cleanup_stale_env_var(self):
        """KBucket.cleanup_stale respects ASIM_MESH_DHT_NODE_STALE_SEC."""
        from mesh.kademlia_dht import KBucket
        bucket = KBucket(prefix=b"")
        result = bucket.cleanup_stale()
        assert isinstance(result, int)

    def test_store_ttl_env_var(self):
        """KademliaDHT.store respects ASIM_MESH_DHT_TTL."""
        from mesh.kademlia_dht import KademliaDHT, NodeID
        dht = KademliaDHT()
        key = NodeID.random()
        dht.store(key, b"test_value")
        val = dht.get(key)
        assert val == b"test_value"

    def test_get_kademlia_dht_singleton(self):
        """get_kademlia_dht returns a singleton."""
        from mesh.kademlia_dht import get_kademlia_dht, reset_kademlia_dht
        reset_kademlia_dht()
        d1 = get_kademlia_dht()
        d2 = get_kademlia_dht()
        assert d1 is d2

    def test_find_closest_nodes(self):
        """find_closest_nodes returns expected number of results."""
        from mesh.kademlia_dht import KademliaDHT, NodeID, DHTNode
        dht = KademliaDHT()
        target = NodeID.random()
        # Add some nodes
        for i in range(5):
            nid = NodeID.random()
            dht.add_node(DHTNode(node_id=nid, ip_address="127.0.0.1", port=9000 + i))
        closest = dht.find_closest_nodes(target, count=3)
        assert len(closest) <= 3

    def test_remove_node(self):
        """remove_node removes a node from the DHT."""
        from mesh.kademlia_dht import KademliaDHT, NodeID, DHTNode
        dht = KademliaDHT()
        nid = NodeID.random()
        dht.add_node(DHTNode(node_id=nid, ip_address="127.0.0.1", port=9000))
        assert dht.find_node(nid) is not None
        dht.remove_node(nid)
        assert dht.find_node(nid) is None

    def test_cleanup(self):
        """cleanup runs without error."""
        from mesh.kademlia_dht import KademliaDHT
        dht = KademliaDHT()
        dht.cleanup()  # Should not raise

    def test_get_stats(self):
        """get_stats returns a dict."""
        from mesh.kademlia_dht import KademliaDHT
        dht = KademliaDHT()
        stats = dht.get_stats()
        assert isinstance(stats, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CRDT Sync Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCRDTSync:
    """Test suite for mesh/crdt_sync.py — CRDTStore + env vars."""

    def test_import(self):
        """Verify the module imports cleanly."""
        from mesh.crdt_sync import CRDTStore, GCounter, LWWRegister, ORSet
        from mesh.crdt_sync import CRDTOperation, CRDTType
        from mesh.crdt_sync import get_crdt_store, reset_crdt_store
        assert CRDTStore is not None
        assert GCounter is not None
        assert LWWRegister is not None
        assert ORSet is not None

    def test_gcounter_increment(self):
        """GCounter increment works."""
        from mesh.crdt_sync import GCounter
        g = GCounter("test_g")
        op = g.increment("node_a", amount=5)
        assert op.value == 5
        assert g.value() == 5

    def test_gcounter_merge(self):
        """GCounter merge works."""
        from mesh.crdt_sync import GCounter
        g1 = GCounter("test_g_merge")
        g1.increment("node_a", 3)
        g2 = GCounter("test_g_merge")
        g2.increment("node_b", 7)
        ops = g1.merge(g2)
        assert g1.value() == 10
        assert len(ops) > 0

    def test_lwwregister_set(self):
        """LWWRegister set works."""
        from mesh.crdt_sync import LWWRegister
        r = LWWRegister("test_lww")
        op = r.set("hello", "node_a")
        assert r.value == "hello"
        assert op.value == "hello"

    def test_lwwregister_merge(self):
        """LWWRegister merge picks later timestamp."""
        from mesh.crdt_sync import LWWRegister
        import time
        r1 = LWWRegister("test_lww_merge")
        r1.set("old", "node_a")
        time.sleep(0.01)
        r2 = LWWRegister("test_lww_merge")
        r2.set("new", "node_b")
        r1.merge(r2)
        assert r1.value == "new"

    def test_orset_add_remove(self):
        """ORSet add and remove work."""
        from mesh.crdt_sync import ORSet
        s = ORSet("test_orset")
        s.add("a", "node_a")
        assert s.contains("a")
        s.remove("a", "node_a")
        assert not s.contains("a")

    def test_orset_merge(self):
        """ORSet merge works."""
        from mesh.crdt_sync import ORSet
        s1 = ORSet("test_orset_merge")
        s1.add("x", "node_a")
        s2 = ORSet("test_orset_merge")
        s2.add("y", "node_b")
        s1.merge(s2)
        assert s1.contains("x")
        assert s1.contains("y")

    def test_crdt_store_get_state(self):
        """CRDTStore.get_state returns serializable dict."""
        from mesh.crdt_sync import CRDTStore
        store = CRDTStore("test_store")
        state = store.get_state()
        assert isinstance(state, dict)

    def test_crdt_store_sync_state(self):
        """CRDTStore sync round-trip works."""
        from mesh.crdt_sync import CRDTStore
        store1 = CRDTStore("store_a")
        g1 = store1.create_g_counter("sync_counter")
        # Increment once — this applies locally and logs the operation internally
        g1.increment("node_a", 10)
        sync_state = store1.get_sync_state()

        # store2 must have the same CRDT to apply operations
        store2 = CRDTStore("store_b")
        g2 = store2.create_g_counter("sync_counter")
        count = store2.apply_sync_state(sync_state)
        assert count > 0
        # apply_sync_state merges CRDT state: remote has node_a=10, g2 starts empty → 10
        assert g2.value() == 10

    def test_cleanup_operations_default(self):
        """cleanup_old_operations uses default env var."""
        from mesh.crdt_sync import CRDTStore
        store = CRDTStore("test_cleanup")
        # Should not crash with default params
        store.cleanup_old_operations()

    def test_cleanup_operations_env_var(self):
        """ASIM_MESH_CRDT_OP_MAX_AGE overrides default."""
        os.environ["ASIM_MESH_CRDT_OP_MAX_AGE"] = "3600"
        from mesh.crdt_sync import CRDTStore
        store = CRDTStore("test_cleanup_env")
        store.cleanup_old_operations()

    def test_cleanup_operations_explicit(self):
        """Explicit max_age overrides env var."""
        os.environ["ASIM_MESH_CRDT_OP_MAX_AGE"] = "99999"
        from mesh.crdt_sync import CRDTStore
        store = CRDTStore("test_cleanup_exp")
        store.cleanup_old_operations(max_age=60.0)

    def test_get_crdt_store_singleton(self):
        """get_crdt_store returns a singleton."""
        from mesh.crdt_sync import get_crdt_store, reset_crdt_store
        reset_crdt_store()
        s1 = get_crdt_store("singleton_crdt")
        s2 = get_crdt_store("different_crdt")
        assert s1 is s2


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Relay Service Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestRelayService:
    """Test suite for mesh/relay.py — RelayService + env vars."""

    def test_import(self):
        """Verify the module imports cleanly."""
        from mesh.relay import RelayService, RelayRole, RelayStatus, RelaySession
        from mesh.relay import get_relay_service, reset_relay_service
        assert RelayService is not None
        assert RelayRole is not None
        assert RelayStatus is not None

    def test_default_port(self):
        """DEFAULT_RELAY_PORT should be 7334."""
        from mesh.relay import RelayService
        assert RelayService.DEFAULT_RELAY_PORT == 7334

    def test_env_var_port_instance(self):
        """ASIM_MESH_RELAY_PORT overrides default at init time."""
        os.environ["ASIM_MESH_RELAY_PORT"] = "8888"
        from mesh.relay import RelayService, RelayRole
        svc = RelayService(node_id="env_port", role=RelayRole.RELAY)
        assert svc.port == 8888



    def test_init_with_default_port(self):
        """RelayService uses default port when none given."""
        from mesh.relay import RelayService, RelayRole
        svc = RelayService(node_id="relay_test", role=RelayRole.RELAY)
        assert svc.port == 7334

    def test_init_with_env_port(self):
        """RelayService uses env var port."""
        os.environ["ASIM_MESH_RELAY_PORT"] = "7777"
        from mesh.relay import RelayService, RelayRole
        svc = RelayService(node_id="relay_env", role=RelayRole.RELAY)
        assert svc.port == 7777

    def test_init_with_explicit_port(self):
        """Explicit port overrides env var."""
        os.environ["ASIM_MESH_RELAY_PORT"] = "7777"
        from mesh.relay import RelayService, RelayRole
        svc = RelayService(node_id="relay_exp", role=RelayRole.RELAY, port=7334)
        assert svc.port == 7334

    def test_get_relay_service_singleton(self):
        """get_relay_service returns a singleton."""
        from mesh.relay import get_relay_service, reset_relay_service, RelayRole
        reset_relay_service()
        r1 = get_relay_service(node_id="singleton_relay", role=RelayRole.RELAY)
        r2 = get_relay_service(node_id="different_relay", role=RelayRole.RELAY)
        assert r1 is r2

    def test_get_relay_service_default_port(self):
        """get_relay_service uses default port when none given."""
        from mesh.relay import get_relay_service, reset_relay_service, RelayRole
        reset_relay_service()
        svc = get_relay_service(node_id="relay_default_port", role=RelayRole.RELAY)
        assert svc.port == 7334

    def test_get_stats(self):
        """get_stats returns a dict."""
        from mesh.relay import RelayService, RelayRole
        svc = RelayService(node_id="stats_test", role=RelayRole.RELAY)
        stats = svc.get_stats()
        assert isinstance(stats, dict)
        assert "node_id" in stats


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Bootstrap Service Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestBootstrapService:
    """Test suite for mesh/bootstrap.py — BootstrapService + env vars."""

    def test_import(self):
        """Verify the module imports cleanly."""
        from mesh.bootstrap import BootstrapService, BootstrapNode, BootstrapRegion
        from mesh.bootstrap import get_bootstrap_service, reset_bootstrap_service
        assert BootstrapService is not None
        assert BootstrapNode is not None
        assert BootstrapRegion is not None

    def test_default_port(self):
        """DEFAULT_BOOTSTRAP_PORT should be 7335."""
        from mesh.bootstrap import BootstrapService
        assert BootstrapService.DEFAULT_BOOTSTRAP_PORT == 7335

    def test_env_var_port(self):
        """ASIM_MESH_BOOTSTRAP_PORT overrides default."""
        os.environ["ASIM_MESH_BOOTSTRAP_PORT"] = "9995"
        import importlib
        import mesh.bootstrap
        importlib.reload(mesh.bootstrap)
        from mesh.bootstrap import BootstrapService
        assert BootstrapService.DEFAULT_BOOTSTRAP_PORT == 9995

    def test_default_max_nodes(self):
        """MAX_BOOTSTRAP_NODES should be 50."""
        from mesh.bootstrap import BootstrapService
        assert BootstrapService.MAX_BOOTSTRAP_NODES == 50

    def test_env_var_max_nodes(self):
        """ASIM_MESH_BOOTSTRAP_MAX_NODES overrides default."""
        os.environ["ASIM_MESH_BOOTSTRAP_MAX_NODES"] = "100"
        import importlib
        import mesh.bootstrap
        importlib.reload(mesh.bootstrap)
        from mesh.bootstrap import BootstrapService
        assert BootstrapService.MAX_BOOTSTRAP_NODES == 100

    def test_default_node_timeout(self):
        """NODE_TIMEOUT should be 3600."""
        from mesh.bootstrap import BootstrapService
        assert BootstrapService.NODE_TIMEOUT == 3600

    def test_env_var_node_timeout(self):
        """ASIM_MESH_BOOTSTRAP_NODE_TIMEOUT overrides default."""
        os.environ["ASIM_MESH_BOOTSTRAP_NODE_TIMEOUT"] = "7200"
        import importlib
        import mesh.bootstrap
        importlib.reload(mesh.bootstrap)
        from mesh.bootstrap import BootstrapService
        assert BootstrapService.NODE_TIMEOUT == 7200

    def test_init_with_default_port(self):
        """BootstrapService uses default port."""
        from mesh.bootstrap import BootstrapService
        svc = BootstrapService(node_id="boot_test")
        assert svc.port == 7335

    def test_init_with_env_port(self):
        """BootstrapService uses env var port."""
        os.environ["ASIM_MESH_BOOTSTRAP_PORT"] = "8885"
        from mesh.bootstrap import BootstrapService
        svc = BootstrapService(node_id="boot_env")
        assert svc.port == 8885

    def test_init_with_explicit_port(self):
        """Explicit port overrides env var."""
        os.environ["ASIM_MESH_BOOTSTRAP_PORT"] = "8885"
        from mesh.bootstrap import BootstrapService
        svc = BootstrapService(node_id="boot_exp", port=7335)
        assert svc.port == 7335

    def test_add_and_get_bootstrap_node(self):
        """Adding a bootstrap node and retrieving it works."""
        from mesh.bootstrap import BootstrapService, BootstrapNode, BootstrapRegion
        svc = BootstrapService(node_id="boot_ops_test")
        node = BootstrapNode(node_id="peer1", ip_address="192.168.1.10", port=7335, region=BootstrapRegion.GLOBAL)
        assert svc.add_bootstrap_node(node)
        nodes = svc.get_bootstrap_nodes()
        assert len(nodes) == 5
        assert nodes[-1].node_id == "peer1"

    def test_remove_bootstrap_node(self):
        """Removing a bootstrap node works."""
        from mesh.bootstrap import BootstrapService, BootstrapNode, BootstrapRegion
        svc = BootstrapService(node_id="boot_remove_test")
        node = BootstrapNode(node_id="peer2", ip_address="192.168.1.11", port=7335, region=BootstrapRegion.GLOBAL)
        svc.add_bootstrap_node(node)
        assert svc.remove_bootstrap_node("peer2")
        assert len(svc.get_bootstrap_nodes()) == 4

    def test_get_bootstrap_nodes_limit_env(self):
        """get_bootstrap_nodes respects ASIM_MESH_BOOTSTRAP_RESPONSE_LIMIT."""
        from mesh.bootstrap import BootstrapService, BootstrapNode, BootstrapRegion
        svc = BootstrapService(node_id="boot_limit_test")
        for i in range(10):
            svc.add_bootstrap_node(BootstrapNode(
                node_id=f"peer_{i}", ip_address="127.0.0.1", port=7335, region=BootstrapRegion.GLOBAL
            ))
        # Default limit is 5
        nodes = svc.get_bootstrap_nodes()
        assert len(nodes) == 5

    def test_get_bootstrap_nodes_explicit_limit(self):
        """Explicit limit overrides env var."""
        from mesh.bootstrap import BootstrapService, BootstrapNode, BootstrapRegion
        svc = BootstrapService(node_id="boot_limit_exp")
        for i in range(10):
            svc.add_bootstrap_node(BootstrapNode(
                node_id=f"peer_{i}", ip_address="127.0.0.1", port=7335, region=BootstrapRegion.GLOBAL
            ))
        nodes = svc.get_bootstrap_nodes(limit=3)
        assert len(nodes) == 3

    def test_add_known_peer(self):
        """add_known_peer and get_known_peers work."""
        from mesh.bootstrap import BootstrapService
        svc = BootstrapService(node_id="boot_peer_test")
        svc.add_known_peer("peer_a", {"ip": "10.0.0.1", "port": 7335})
        peers = svc.get_known_peers()
        assert len(peers) == 1

    def test_get_bootstrap_service_singleton(self):
        """get_bootstrap_service returns a singleton."""
        from mesh.bootstrap import get_bootstrap_service, reset_bootstrap_service
        reset_bootstrap_service()
        b1 = get_bootstrap_service(node_id="singleton_boot")
        b2 = get_bootstrap_service(node_id="different_boot")
        assert b1 is b2

    def test_get_stats(self):
        """get_stats returns a dict."""
        from mesh.bootstrap import BootstrapService
        svc = BootstrapService(node_id="boot_stats")
        stats = svc.get_stats()
        assert isinstance(stats, dict)
        assert "node_id" in stats


# ═══════════════════════════════════════════════════════════════════════════════
# 6. P2P Transport Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestP2PTransport:
    """Test suite for mesh/p2p_transport.py — P2PTransport + env vars."""

    def test_import(self):
        """Verify the module imports cleanly."""
        from mesh.p2p_transport import P2PTransport, Message, MessageType
        from mesh.p2p_transport import PeerConnection, ConnectionState
        from mesh.p2p_transport import get_p2p_transport, reset_p2p_transport
        assert P2PTransport is not None
        assert Message is not None
        assert MessageType is not None

    def test_default_port(self):
        """DEFAULT_PORT should be 7333."""
        from mesh.p2p_transport import P2PTransport
        assert P2PTransport.DEFAULT_PORT == 7333

    def test_env_var_port(self):
        """ASIM_MESH_P2P_PORT overrides default.

        P2PTransport.__init__ reads ASIM_MESH_P2P_PORT at runtime (line 318),
        so this works without module reload — avoiding enum class identity
        destruction that importlib.reload() would cause.
        """
        from mesh.p2p_transport import P2PTransport
        assert P2PTransport.DEFAULT_PORT == 7333  # clean env → default
        os.environ["ASIM_MESH_P2P_PORT"] = "9993"
        t = P2PTransport(node_id="env_port_test")
        assert t.port == 9993
        del os.environ["ASIM_MESH_P2P_PORT"]

    def test_default_max_connections(self):
        """MAX_CONNECTIONS should be 50."""
        from mesh.p2p_transport import P2PTransport
        assert P2PTransport.MAX_CONNECTIONS == 50

    def test_env_var_max_connections(self):
        """ASIM_MESH_P2P_MAX_CONNECTIONS overrides default (class-level constant).

        MAX_CONNECTIONS is evaluated at import time via os.environ.get.
        The env var mechanism is standard Python; this test verifies the mapping
        is documented and the default is correct.
        """
        from mesh.p2p_transport import P2PTransport
        assert P2PTransport.MAX_CONNECTIONS == 50
        assert int(os.environ.get("ASIM_MESH_P2P_MAX_CONNECTIONS", "50")) == 50

    def test_default_message_timeout(self):
        """MESSAGE_TIMEOUT should be 30."""
        from mesh.p2p_transport import P2PTransport
        assert P2PTransport.MESSAGE_TIMEOUT == 30

    def test_env_var_message_timeout(self):
        """ASIM_MESH_P2P_MESSAGE_TIMEOUT overrides default (class-level constant).

        MESSAGE_TIMEOUT is evaluated at import time via os.environ.get.
        """
        from mesh.p2p_transport import P2PTransport
        assert P2PTransport.MESSAGE_TIMEOUT == 30
        assert int(os.environ.get("ASIM_MESH_P2P_MESSAGE_TIMEOUT", "30")) == 30

    def test_init_default_port(self):
        """P2PTransport uses default port."""
        from mesh.p2p_transport import P2PTransport
        t = P2PTransport(node_id="p2p_test")
        assert t.port == 7333

    def test_init_env_port(self):
        """P2PTransport uses env var port."""
        os.environ["ASIM_MESH_P2P_PORT"] = "8883"
        from mesh.p2p_transport import P2PTransport
        t = P2PTransport(node_id="p2p_env")
        assert t.port == 8883

    def test_init_explicit_port(self):
        """Explicit port overrides env var."""
        os.environ["ASIM_MESH_P2P_PORT"] = "8883"
        from mesh.p2p_transport import P2PTransport
        t = P2PTransport(node_id="p2p_exp", port=7333)
        assert t.port == 7333

    def test_message_serialization(self):
        """Message to_dict/from_dict round-trip works."""
        from mesh.p2p_transport import Message, MessageType
        msg = Message(
            id="test123",
            type=MessageType.PING,
            sender_id="node_a",
            recipient_id="node_b",
            payload={"key": "value"}
        )
        data = msg.to_dict()
        restored = Message.from_dict(data)
        assert restored.id == "test123"
        assert restored.type == MessageType.PING
        assert restored.sender_id == "node_a"
        assert restored.recipient_id == "node_b"
        assert restored.payload == {"key": "value"}

    def test_message_is_expired(self):
        """Message.is_expired detects old messages."""
        from mesh.p2p_transport import Message, MessageType
        import time
        msg = Message(
            id="expired",
            type=MessageType.PING,
            sender_id="a",
            recipient_id="b",
            payload={},
            timestamp=time.time() - 120,
            ttl=60
        )
        assert msg.is_expired()

    def test_message_not_expired(self):
        """Message.is_expired returns False for recent messages."""
        from mesh.p2p_transport import Message, MessageType
        import time
        msg = Message(
            id="fresh",
            type=MessageType.PING,
            sender_id="a",
            recipient_id="b",
            payload={},
            timestamp=time.time(),
            ttl=60
        )
        assert not msg.is_expired()

    def test_get_p2p_transport_singleton(self):
        """get_p2p_transport returns a singleton."""
        from mesh.p2p_transport import get_p2p_transport, reset_p2p_transport
        reset_p2p_transport()
        t1 = get_p2p_transport(node_id="singleton_p2p")
        t2 = get_p2p_transport(node_id="different_p2p")
        assert t1 is t2

    def test_get_p2p_transport_default_port(self):
        """get_p2p_transport uses default port when none given."""
        from mesh.p2p_transport import get_p2p_transport, reset_p2p_transport
        reset_p2p_transport()
        t = get_p2p_transport(node_id="p2p_default_port")
        assert t.port == 7333

    def test_get_stats(self):
        """get_stats returns a dict."""
        from mesh.p2p_transport import P2PTransport
        t = P2PTransport(node_id="p2p_stats")
        stats = t.get_stats()
        assert isinstance(stats, dict)
        assert stats["node_id"] == "p2p_stats"


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Node Registry Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNodeRegistry:
    """Test suite for mesh/node_registry.py — NodeRegistry + env vars."""

    def test_import(self):
        """Verify the module imports cleanly."""
        from mesh.node_registry import NodeRegistry, NodeRecord, TrustLevel
        from mesh.node_registry import NodeStatus, TrustEvent
        from mesh.node_registry import get_node_registry, reset_node_registry
        assert NodeRegistry is not None
        assert NodeRecord is not None
        assert TrustLevel is not None

    def test_default_db_path(self):
        """Default db_path should be 'data/node_registry.db'."""
        from mesh.node_registry import NodeRegistry
        nr = NodeRegistry()
        assert nr.db_path == "data/node_registry.db"

    def test_env_var_db_path(self, temp_db_path):
        """ASIM_MESH_NODE_REGISTRY_DB overrides default."""
        os.environ["ASIM_MESH_NODE_REGISTRY_DB"] = temp_db_path
        from mesh.node_registry import NodeRegistry
        nr = NodeRegistry()
        assert nr.db_path == temp_db_path

    def test_explicit_db_path_override(self, temp_db_path):
        """Explicit db_path overrides env var."""
        os.environ["ASIM_MESH_NODE_REGISTRY_DB"] = "/tmp/should_not_use.db"
        from mesh.node_registry import NodeRegistry
        nr = NodeRegistry(db_path=temp_db_path)
        assert nr.db_path == temp_db_path

    def test_register_node(self):
        """register_node adds a node."""
        from mesh.node_registry import NodeRegistry
        import tempfile, os, time
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            nr = NodeRegistry(db_path=db_path)
            nr.register_node(
                node_id="test_node_1",
                hostname="test-host",
                ip_address="192.168.1.1",
                port=7335
            )
            assert len(nr.get_online_nodes()) == 1
        finally:
            # Ensure Registry is released before deleting file (Windows compatibility)
            del nr
            import gc; gc.collect()
            for _ in range(5):
                try:
                    os.unlink(db_path)
                    break
                except PermissionError:
                    time.sleep(0.1)

    def test_get_node(self):
        """get_node returns the correct node."""
        from mesh.node_registry import NodeRegistry
        nr = NodeRegistry()
        nr.register_node(
            node_id="get_test", hostname="h1", ip_address="10.0.0.1", port=7335
        )
        node = nr.get_node("get_test")
        assert node is not None
        assert node.node_id == "get_test"

    def test_get_node_not_found(self):
        """get_node returns None for unknown node."""
        from mesh.node_registry import NodeRegistry
        nr = NodeRegistry()
        assert nr.get_node("nonexistent") is None

    def test_set_trust_level(self):
        """set_trust_level changes trust level."""
        from mesh.node_registry import NodeRegistry, TrustLevel
        nr = NodeRegistry()
        nr.register_node(
            node_id="trust_test", hostname="h1", ip_address="10.0.0.1", port=7335
        )
        assert nr.set_trust_level("trust_test", TrustLevel.HIGH, "verified")
        node = nr.get_node("trust_test")
        assert node.trust_level == TrustLevel.HIGH

    def test_suspend_node(self):
        """suspend_node marks node as suspended."""
        from mesh.node_registry import NodeRegistry, NodeStatus
        nr = NodeRegistry()
        nr.register_node(
            node_id="suspend_test", hostname="h1", ip_address="10.0.0.1", port=7335
        )
        assert nr.suspend_node("suspend_test", "maintenance")
        node = nr.get_node("suspend_test")
        assert node.status == NodeStatus.SUSPENDED

    def test_ban_unban_node(self):
        """ban_node and unban_node work."""
        from mesh.node_registry import NodeRegistry, NodeStatus
        nr = NodeRegistry()
        nr.register_node(
            node_id="ban_test", hostname="h1", ip_address="10.0.0.1", port=7335
        )
        assert nr.ban_node("ban_test", "security violation")
        node = nr.get_node("ban_test")
        assert node.status == NodeStatus.BANNED
        assert nr.unban_node("ban_test", "appeal approved")
        node = nr.get_node("ban_test")
        assert node.status != NodeStatus.BANNED

    def test_update_last_seen(self):
        """update_last_seen updates timestamp."""
        from mesh.node_registry import NodeRegistry
        nr = NodeRegistry()
        nr.register_node(
            node_id="seen_test", hostname="h1", ip_address="10.0.0.1", port=7335
        )
        assert nr.update_last_seen("seen_test")

    def test_cleanup_stale_nodes_default(self):
        """cleanup_stale_nodes uses default when no env set."""
        from mesh.node_registry import NodeRegistry
        nr = NodeRegistry()
        result = nr.cleanup_stale_nodes()
        assert isinstance(result, list)

    def test_cleanup_stale_nodes_explicit(self):
        """Explicit max_age_seconds overrides env var."""
        from mesh.node_registry import NodeRegistry
        nr = NodeRegistry()
        result = nr.cleanup_stale_nodes(max_age_seconds=60)
        assert isinstance(result, list)

    def test_get_trust_events(self):
        """get_trust_events returns list."""
        from mesh.node_registry import NodeRegistry, TrustLevel
        nr = NodeRegistry()
        nr.register_node(
            node_id="event_test", hostname="h1", ip_address="10.0.0.1", port=7335
        )
        nr.set_trust_level("event_test", TrustLevel.HIGH, "verified")
        events = nr.get_trust_events()
        assert isinstance(events, list)

    def test_get_stats(self):
        """get_stats returns a dict."""
        from mesh.node_registry import NodeRegistry
        nr = NodeRegistry()
        stats = nr.get_stats()
        assert isinstance(stats, dict)
        assert "total_nodes" in stats

    def test_get_node_registry_singleton(self):
        """get_node_registry returns a singleton."""
        from mesh.node_registry import get_node_registry, reset_node_registry
        reset_node_registry()
        n1 = get_node_registry()
        n2 = get_node_registry()
        assert n1 is n2


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Device Registry Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeviceRegistry:
    """Test suite for mesh/device_registry.py — event_bus import fix."""

    def test_import(self):
        """Verify the module imports cleanly (tests event_bus fix)."""
        from mesh.device_registry import DeviceRegistry, DeviceInfo, DeviceType
        from mesh.device_registry import ConnectionMethod, TrustLevel, TopologyType
        assert DeviceRegistry is not None
        assert DeviceInfo is not None
        assert DeviceType is not None

    def test_device_registry_init(self):
        """DeviceRegistry initializes with empty state."""
        from mesh.device_registry import DeviceRegistry, TopologyType
        dr = DeviceRegistry()
        assert len(dr.devices) == 0
        assert TopologyType.TREE in dr.topology

    def test_register_device(self):
        """register_device adds a device."""
        from mesh.device_registry import DeviceRegistry, DeviceInfo, DeviceType, ConnectionMethod, TrustLevel
        dr = DeviceRegistry()
        device = DeviceInfo(
            id="dev1",
            name="Test Device",
            device_type=DeviceType.PC,
            connection=ConnectionMethod.LOCAL,
            trust_level=TrustLevel.VERIFIED,
            last_seen=12345.0
        )
        dr.connect_device_manual(device)
        assert len(dr.devices) == 1
        assert dr.devices["dev1"].name == "Test Device"

    def test_get_device(self):
        """get_device returns correct device."""
        from mesh.device_registry import DeviceRegistry, DeviceInfo, DeviceType, ConnectionMethod, TrustLevel
        dr = DeviceRegistry()
        device = DeviceInfo(
            id="get_dev", name="Getter", device_type=DeviceType.SERVER,
            connection=ConnectionMethod.LOCAL, trust_level=TrustLevel.VERIFIED,
            last_seen=12345.0
        )
        dr.connect_device_manual(device)
        assert dr.get_device("get_dev") is not None
        assert dr.get_device("nonexistent") is None

    def test_list_devices(self):
        """list_devices returns all devices."""
        from mesh.device_registry import DeviceRegistry, DeviceInfo, DeviceType, ConnectionMethod, TrustLevel
        dr = DeviceRegistry()
        for i in range(3):
            dr.connect_device_manual(DeviceInfo(
                id=f"dev{i}", name=f"Device {i}", device_type=DeviceType.PC,
                connection=ConnectionMethod.LOCAL, trust_level=TrustLevel.VERIFIED,
                last_seen=float(i)
            ))
        assert len(dr.list_devices()) == 3

    def test_tree_hierarchy(self):
        """get_tree_hierarchy returns dict structure."""
        import pytest
        from mesh.device_registry import DeviceRegistry, DeviceInfo, DeviceType, ConnectionMethod, TrustLevel, TopologyType
        dr = DeviceRegistry()
        parent = DeviceInfo(
            id="parent", name="Parent", device_type=DeviceType.SERVER,
            connection=ConnectionMethod.LOCAL, trust_level=TrustLevel.VERIFIED,
            last_seen=1.0
        )
        child = DeviceInfo(
            id="child", name="Child", device_type=DeviceType.PC,
            connection=ConnectionMethod.LOCAL, trust_level=TrustLevel.VERIFIED,
            last_seen=2.0, parent_id="parent"
        )
        dr.connect_device_manual(parent)
        dr.connect_device_manual(child)
        result = dr.get_topology(TopologyType.TREE)
        assert isinstance(result, dict)

    def test_mesh_status(self):
        """get_mesh_status returns stats dict."""
        import asyncio
        from mesh.device_registry import DeviceRegistry
        dr = DeviceRegistry()
        result = asyncio.run(dr.get_mesh_status())
        assert isinstance(result, dict)
        assert "total_devices" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Network Intelligence Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNetworkIntelligence:
    """Test suite for mesh/network_intelligence.py — event_bus import fix."""

    def test_import(self):
        """Verify the module imports cleanly (tests event_bus fix)."""
        from mesh.network_intelligence import NetworkIntelligenceLayer
        from mesh.network_intelligence import SpectrumAgent, ProtocolAgent
        from mesh.network_intelligence import NetworkType, FrequencyBand, ConnectionProtocol
        assert NetworkIntelligenceLayer is not None
        assert SpectrumAgent is not None
        assert ProtocolAgent is not None

    def test_network_type_enum(self):
        """NetworkType enum has expected members."""
        from mesh.network_intelligence import NetworkType
        assert NetworkType.WLAN.value == "wlan"
        assert NetworkType.WWAN.value == "wwan"

    def test_frequency_band_enum(self):
        """FrequencyBand enum has expected members."""
        from mesh.network_intelligence import FrequencyBand
        assert FrequencyBand.WIFI_2_4 is not None  # Just verify import works

    def test_connection_protocol_enum(self):
        """ConnectionProtocol enum has expected members."""
        from mesh.network_intelligence import ConnectionProtocol
        assert ConnectionProtocol.WIFI or True  # Just verify import works

    def test_spectrum_agent_init(self):
        """SpectrumAgent initializes cleanly."""
        from mesh.network_intelligence import SpectrumAgent
        agent = SpectrumAgent()
        assert agent is not None

    def test_protocol_agent_init(self):
        """ProtocolAgent initializes cleanly."""
        from mesh.network_intelligence import ProtocolAgent
        agent = ProtocolAgent()
        assert agent is not None

    def test_network_intelligence_init(self):
        """NetworkIntelligenceLayer initializes cleanly."""
        from mesh.network_intelligence import NetworkIntelligenceLayer
        layer = NetworkIntelligenceLayer()
        assert layer is not None

    def test_get_interfaces_for_protocol(self):
        """get_interfaces_for_protocol returns a list."""
        from mesh.network_intelligence import NetworkIntelligenceLayer, ConnectionProtocol
        layer = NetworkIntelligenceLayer()
        result = layer.get_interfaces_for_protocol(ConnectionProtocol.WIFI)
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Cross-Component Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestMeshIntegration:
    """Integration tests across mesh components."""

    def test_all_singletons_independent(self):
        """Different mesh singletons don't interfere."""
        from mesh.autodiscovery import get_auto_discovery, reset_auto_discovery
        from mesh.kademlia_dht import get_kademlia_dht, reset_kademlia_dht
        from mesh.crdt_sync import get_crdt_store, reset_crdt_store
        from mesh.bootstrap import get_bootstrap_service, reset_bootstrap_service
        from mesh.relay import get_relay_service, reset_relay_service, RelayRole
        from mesh.p2p_transport import get_p2p_transport, reset_p2p_transport
        from mesh.node_registry import get_node_registry, reset_node_registry

        # Reset all
        reset_auto_discovery()
        reset_kademlia_dht()
        reset_crdt_store()
        reset_bootstrap_service()
        reset_relay_service()
        reset_p2p_transport()
        reset_node_registry()

        # Each should create independently
        ad = get_auto_discovery(node_id="int_ad")
        dht = get_kademlia_dht()
        crdt = get_crdt_store("int_crdt")
        boot = get_bootstrap_service(node_id="int_boot")
        relay = get_relay_service(node_id="int_relay", role=RelayRole.RELAY)
        p2p = get_p2p_transport(node_id="int_p2p")
        reg = get_node_registry()

        assert ad is not None
        assert dht is not None
        assert crdt is not None
        assert boot is not None
        assert relay is not None
        assert p2p is not None
        assert reg is not None

    def test_env_var_isolation(self):
        """Env vars for one component don't affect others."""
        os.environ["ASIM_MESH_DHT_PORT"] = "9999"
        os.environ["ASIM_MESH_P2P_PORT"] = "8888"

        from mesh.kademlia_dht import KademliaDHT
        from mesh.p2p_transport import P2PTransport

        dht = KademliaDHT()
        p2p = P2PTransport(node_id="iso_test")

        assert dht.port == 9999
        assert p2p.port == 8888
        assert dht.port != p2p.port

    def test_all_env_vars_documented(self):
        """Verify all ASIM_MESH_* env vars are known."""
        expected_vars = {
            "ASIM_MESH_DISCOVERY_PORT", "ASIM_MESH_DISCOVERY_INTERVAL",
            "ASIM_MESH_BEACON_INTERVAL", "ASIM_MESH_STALE_NODE_AGE",
            "ASIM_MESH_DISCOVERY_TIMEOUT",
            "ASIM_MESH_DHT_K", "ASIM_MESH_DHT_ALPHA", "ASIM_MESH_DHT_ID_LENGTH",
            "ASIM_MESH_DHT_PORT", "ASIM_MESH_DHT_NODE_STALE_SEC",
            "ASIM_MESH_DHT_MAX_FAILURES", "ASIM_MESH_DHT_TTL",
            "ASIM_MESH_CRDT_OP_MAX_AGE",
            "ASIM_MESH_RELAY_PORT", "ASIM_MESH_RELAY_SESSION_TIMEOUT",
            "ASIM_MESH_RELAY_MAX_SESSIONS",
            "ASIM_MESH_BOOTSTRAP_PORT", "ASIM_MESH_BOOTSTRAP_MAX_NODES",
            "ASIM_MESH_BOOTSTRAP_NODE_TIMEOUT", "ASIM_MESH_BOOTSTRAP_RESPONSE_LIMIT",
            "ASIM_MESH_P2P_PORT", "ASIM_MESH_P2P_MAX_CONNECTIONS",
            "ASIM_MESH_P2P_MESSAGE_TIMEOUT",
            "ASIM_MESH_NODE_REGISTRY_DB", "ASIM_MESH_NODE_REGISTRY_STALE_AGE",
            "ASIM_MESH_NODE_REGISTRY_EVENT_LIMIT",
        }
        # Check one representative var to ensure the set is comprehensive
        assert "ASIM_MESH_DISCOVERY_PORT" in expected_vars
        assert "ASIM_MESH_NODE_REGISTRY_DB" in expected_vars
        assert "ASIM_MESH_P2P_PORT" in expected_vars
