#!/usr/bin/env python3
"""
tests/real/test_federation.py
AsimNexus — Global Federation Protocol Tests

Tests for core/federation/global_federation.py:
  - GCounter: increment, merge, state round-trip, edge cases
  - LWWRegister: set/get, merge, timestamp conflict, edge cases
  - ORSet: add, remove, elements, merge, state round-trip, edge cases
  - FederatedPeer: dataclass creation
  - FederatedNodeState: sync packet, merge, version tracking
  - GlobalFederationManager: peer management, consent, sync,
    env-var config, persistence, edge cases, error recovery
"""

import os
import time
import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any

from core.federation.global_federation import (
    GCounter,
    LWWRegister,
    ORSet,
    FederatedPeer,
    FederatedNodeState,
    GlobalFederationManager,
    get_federation,
)


# ═══════════════════════════════════════════════════════════════════════════════
# GCounter
# ═══════════════════════════════════════════════════════════════════════════════

class TestGCounter:
    """Grow-only counter — monotonic increment only."""

    def test_increment_default(self):
        c = GCounter("a")
        assert c.value() == 0
        c.increment()
        assert c.value() == 1

    def test_increment_by_amount(self):
        c = GCounter("a")
        c.increment(5)
        assert c.value() == 5

    def test_merge_two_counters(self):
        ca = GCounter("a"); ca.increment(3)
        cb = GCounter("b"); cb.increment(7)
        ca.merge(cb)
        assert ca.value() == 10

    def test_merge_idempotent(self):
        ca = GCounter("a"); ca.increment(2)
        cb = GCounter("a"); cb.increment(2)
        ca.merge(cb)
        assert ca.value() == 2

    def test_state_round_trip(self):
        c = GCounter("a")
        c.increment(42)
        d = GCounter.from_state("b", c.state())
        assert d.value() == 42

    def test_merge_multiple_nodes(self):
        ca = GCounter("a"); ca.increment(1)
        cb = GCounter("b"); cb.increment(2)
        cc = GCounter("c"); cc.increment(3)
        ca.merge(cb); ca.merge(cc)
        assert ca.value() == 6

    def test_no_double_count_on_remerge(self):
        ca = GCounter("a"); ca.increment(3)
        cb = GCounter("b"); cb.increment(5)
        ca.merge(cb)
        assert ca.value() == 8
        ca.merge(cb)
        assert ca.value() == 8

    def test_zero_increment(self):
        c = GCounter("a")
        c.increment(0)
        assert c.value() == 0


# ═══════════════════════════════════════════════════════════════════════════════
# LWWRegister
# ═══════════════════════════════════════════════════════════════════════════════

class TestLWWRegister:
    """Last-write-wins register with wall-clock timestamp."""

    def test_set_and_get(self):
        r = LWWRegister()
        r.set("hello", "node1")
        assert r.get() == "hello"

    def test_set_overwrites_older(self):
        r = LWWRegister()
        r.set("first", "a")
        r.set("second", "b")
        assert r.get() == "second"

    def test_merge_newer_wins(self):
        r1 = LWWRegister()
        r1.set("old", "a")
        time.sleep(0.002)
        r2 = LWWRegister()
        r2.set("new", "b")
        r1.merge(r2)
        assert r1.get() == "new"

    def test_merge_older_loses(self):
        r1 = LWWRegister()
        r1.set("old", "a")
        time.sleep(0.001)
        r2 = LWWRegister()
        r2.set("new", "b")
        r2.merge(r1)
        assert r2.get() == "new"

    def test_state_round_trip(self):
        r = LWWRegister()
        r.set("persist-me", "x")
        r2 = LWWRegister.from_state(r.state())
        assert r2.get() == "persist-me"

    def test_empty_register(self):
        r = LWWRegister()
        assert r.get() is None


# ═══════════════════════════════════════════════════════════════════════════════
# ORSet
# ═══════════════════════════════════════════════════════════════════════════════

class TestORSet:
    """Observe-Remove Set — add/remove without conflict."""

    def test_add_elements(self):
        s = ORSet("a")
        s.add("x")
        s.add("y")
        assert s.elements() == {"x", "y"}

    def test_remove_element(self):
        s = ORSet("a")
        s.add("x")
        s.remove("x")
        assert s.elements() == set()

    def test_add_after_remove(self):
        s = ORSet("a")
        s.add("x")
        s.remove("x")
        s.add("x")
        assert "x" in s.elements()

    def test_merge_two_sets(self):
        s1 = ORSet("a")
        s1.add("x")
        s2 = ORSet("b")
        s2.add("y")
        s1.merge(s2)
        assert s1.elements() == {"x", "y"}

    def test_merge_remove_propagates(self):
        s1 = ORSet("a")
        s1.add("x")
        s1.add("y")
        s2 = ORSet("b")
        s2.merge(s1)
        s1.remove("x")
        s2.merge(s1)
        assert s2.elements() == {"y"}

    def test_state_round_trip(self):
        s = ORSet("a")
        s.add("x")
        s.add("y")
        state = s.state()
        s2 = ORSet.from_state("b", state)
        assert "y" in s2.elements()

    def test_duplicate_add(self):
        s = ORSet("a")
        s.add("x")
        s.add("x")
        assert "x" in s.elements()
        s.remove("x")
        assert s.elements() == set()

    def test_remove_nonexistent(self):
        s = ORSet("a")
        s.remove("nonexistent")
        assert s.elements() == set()


# ═══════════════════════════════════════════════════════════════════════════════
# FederatedPeer
# ═══════════════════════════════════════════════════════════════════════════════

class TestFederatedPeer:
    """FederatedPeer dataclass."""

    def test_create(self):
        p = FederatedPeer(
            peer_id="p1", node_id="n1", did="did:example:abc",
            endpoint="ws://10.0.0.1:9000",
        )
        assert p.peer_id == "p1"
        assert p.trusted is False
        assert p.last_sync == 0.0
        assert p.sync_count == 0

    def test_create_trusted(self):
        p = FederatedPeer(
            peer_id="p2", node_id="n2", did="did:example:def",
            endpoint="ws://10.0.0.2:9000", trusted=True,
        )
        assert p.trusted is True


# ═══════════════════════════════════════════════════════════════════════════════
# FederatedNodeState
# ═══════════════════════════════════════════════════════════════════════════════

class TestFederatedNodeState:
    """CRDT-based federated node state."""

    def test_init(self):
        ns = FederatedNodeState("node-a")
        assert ns.node_id == "node-a"
        assert ns.msg_count.value() == 0
        assert ns.active_peers.elements() == set()
        assert ns.capabilities.elements() == set()
        assert ns.display_name.get() is None
        assert ns.universe_mode.get() is None

    def test_to_sync_packet_structure(self):
        ns = FederatedNodeState("node-a")
        pkt = ns.to_sync_packet()
        assert "node_id" in pkt
        assert "version" in pkt
        assert "msg_count" in pkt
        assert "active_peers" in pkt
        assert "capabilities" in pkt
        assert "display_name" in pkt
        assert "universe_mode" in pkt
        assert "ts" in pkt
        assert pkt["node_id"] == "node-a"

    def test_merge_packet_increases_version(self):
        ns1 = FederatedNodeState("node-a")
        ns2 = FederatedNodeState("node-b")
        ns2.msg_count.increment(3)
        ns2.active_peers.add("peer-1")
        ns2.display_name.set("Alice", "node-b")
        v0 = ns1._version
        ns1.merge_packet(ns2.to_sync_packet())
        assert ns1._version > v0

    def test_merge_crdt_values(self):
        ns1 = FederatedNodeState("node-a")
        ns2 = FederatedNodeState("node-b")
        ns2.msg_count.increment(10)
        ns2.active_peers.add("peer-x")
        ns2.capabilities.add("ai-mesh")
        ns2.display_name.set("Bob", "node-b")
        ns2.universe_mode.set("developer", "node-b")
        ns1.merge_packet(ns2.to_sync_packet())
        assert ns1.msg_count.value() == 10
        assert "peer-x" in ns1.active_peers.elements()
        assert "ai-mesh" in ns1.capabilities.elements()
        assert ns1.display_name.get() == "Bob"
        assert ns1.universe_mode.get() == "developer"


# ═══════════════════════════════════════════════════════════════════════════════
# GlobalFederationManager
# ═══════════════════════════════════════════════════════════════════════════════

class TestGlobalFederationManager:
    """GlobalFederationManager peer management and sync."""

    def test_init_defaults(self):
        fm = GlobalFederationManager(node_id="test-node-a")
        assert fm.node_id == "test-node-a"
        assert fm.sync_interval >= 1
        assert fm.max_peers >= 1
        assert fm.status()["peers"] == 0

    def test_add_peer(self):
        fm = GlobalFederationManager(node_id="test-peer-add")
        p = fm.add_peer("did:example:peer1", "ws://10.0.0.1:9000")
        assert p.peer_id in fm._peers
        assert fm.status()["peers"] == 1

    def test_add_peer_generates_same_id(self):
        fm = GlobalFederationManager(node_id="test-peer-id")
        p1 = fm.add_peer("did:example:same", "ws://10.0.0.1:9000")
        p2 = fm.add_peer("did:example:same", "ws://10.0.0.1:9000")
        assert p1.peer_id == p2.peer_id

    def test_consent_peer(self):
        fm = GlobalFederationManager(node_id="test-consent")
        fm.add_peer("did:example:trusted", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.consent_peer(peer_id)
        assert peer_id in fm._consent
        assert fm._peers[peer_id].trusted is True

    def test_revoke_peer(self):
        fm = GlobalFederationManager(node_id="test-revoke")
        fm.add_peer("did:example:revoke", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.consent_peer(peer_id)
        fm.revoke_peer(peer_id)
        assert peer_id not in fm._consent
        assert fm._peers[peer_id].trusted is False

    def test_remove_peer(self):
        fm = GlobalFederationManager(node_id="test-remove")
        fm.add_peer("did:example:remove", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.remove_peer(peer_id)
        assert peer_id not in fm._peers
        assert peer_id not in fm._consent

    def test_receive_sync_no_consent(self):
        fm = GlobalFederationManager(node_id="test-sync-no-consent")
        fm.add_peer("did:example:noconsent", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        result = fm.receive_sync({}, peer_id)
        assert result["accepted"] is False
        assert "No consent" in result["reason"]

    def test_receive_sync_with_consent(self):
        fm = GlobalFederationManager(node_id="test-sync-consent")
        fm.add_peer("did:example:syncer", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.consent_peer(peer_id)
        remote = FederatedNodeState("remote-node")
        remote.msg_count.increment(7)
        remote.active_peers.add("peer-abc")
        remote.display_name.set("Remote", "remote-node")
        result = fm.receive_sync(remote.to_sync_packet(), peer_id)
        assert result["accepted"] is True
        assert result["changes"] > 0

    def test_get_sync_packet(self):
        fm = GlobalFederationManager(node_id="test-sync-packet")
        pkt = fm.get_sync_packet()
        assert "node_id" in pkt
        assert pkt["node_id"] == "test-sync-packet"

    def test_status_keys(self):
        fm = GlobalFederationManager(node_id="test-status")
        s = fm.status()
        assert "node_id" in s
        assert "peers" in s
        assert "trusted_peers" in s
        assert "state_version" in s
        assert "active_peers" in s

    def test_get_stats(self):
        fm = GlobalFederationManager(node_id="test-stats")
        stats = fm.get_stats()
        assert "sync_interval" in stats
        assert "max_peers" in stats
        assert "consent_count" in stats
        assert "sync_log_size" in stats

    def test_peer_list(self):
        fm = GlobalFederationManager(node_id="test-peer-list")
        fm.add_peer("did:example:pl1", "ws://10.0.0.1:9000")
        fm.add_peer("did:example:pl2", "ws://10.0.0.2:9000")
        pl = fm.peer_list()
        assert len(pl) == 2

    def test_custom_sync_interval(self):
        fm = GlobalFederationManager(node_id="test-custom-sync", sync_interval=120)
        assert fm.sync_interval == 120

    def test_custom_max_peers(self):
        fm = GlobalFederationManager(node_id="test-custom-max", max_peers=50)
        assert fm.max_peers == 50

    def test_env_sync_interval(self):
        os.environ["ASIM_FED_SYNC_INTERVAL"] = "99"
        fm = GlobalFederationManager(node_id="test-env-sync")
        assert fm.sync_interval == 99
        del os.environ["ASIM_FED_SYNC_INTERVAL"]

    def test_env_max_peers(self):
        os.environ["ASIM_FED_MAX_PEERS"] = "42"
        fm = GlobalFederationManager(node_id="test-env-max")
        assert fm.max_peers == 42
        del os.environ["ASIM_FED_MAX_PEERS"]

    def test_env_node_id(self):
        os.environ["ASIM_FED_NODE_ID"] = "env-node-001"
        fm = GlobalFederationManager()
        assert fm.node_id == "env-node-001"
        del os.environ["ASIM_FED_NODE_ID"]

    def test_multiple_peers_independent(self):
        fm = GlobalFederationManager(node_id="test-multi-peer")
        p1 = fm.add_peer("did:example:mp1", "ws://10.0.0.1:9000")
        p2 = fm.add_peer("did:example:mp2", "ws://10.0.0.2:9000")
        assert len(fm._peers) == 2
        assert p1.peer_id != p2.peer_id

    def test_full_sync_round_trip(self):
        fm = GlobalFederationManager(node_id="test-full-sync")
        fm.add_peer("did:example:fullsync", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.consent_peer(peer_id)
        remote = FederatedNodeState("remote-full")
        remote.msg_count.increment(5)
        remote.active_peers.add("peer-alpha")
        remote.capabilities.add("crypto")
        remote.display_name.set("FullNode", "remote-full")
        result = fm.receive_sync(remote.to_sync_packet(), peer_id)
        assert result["accepted"] is True
        assert fm._state.msg_count.value() >= 5
        assert "peer-alpha" in fm._state.active_peers.elements()

    def test_get_federation_singleton(self):
        f1 = get_federation()
        f2 = get_federation()
        assert f1 is f2

    def test_revoke_nonexistent_peer(self):
        fm = GlobalFederationManager(node_id="test-rev-nonexist")
        fm.revoke_peer("non-existent-id")

    def test_remove_nonexistent_peer(self):
        fm = GlobalFederationManager(node_id="test-rm-nonexist")
        fm.remove_peer("non-existent-id")

    def test_receive_sync_unknown_peer(self):
        fm = GlobalFederationManager(node_id="test-unknown-peer")
        result = fm.receive_sync({}, "unknown-peer-id")
        assert result["accepted"] is False

    def test_sync_log_grows(self):
        fm = GlobalFederationManager(node_id="test-sync-log")
        fm.add_peer("did:example:slogger", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.consent_peer(peer_id)
        remote = FederatedNodeState("remote-logger")
        remote.msg_count.increment(1)
        pkt = remote.to_sync_packet()
        fm.receive_sync(pkt, peer_id)
        assert len(fm._sync_log) == 1
        fm.receive_sync(pkt, peer_id)
        assert len(fm._sync_log) == 2
        assert fm._peers[peer_id].sync_count == 2

    def test_capabilities_sync(self):
        fm = GlobalFederationManager(node_id="test-cap-sync")
        fm.add_peer("did:example:cap", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.consent_peer(peer_id)
        remote = FederatedNodeState("remote-cap")
        remote.capabilities.add("mesh-net")
        remote.capabilities.add("ai-orchestrator")
        fm.receive_sync(remote.to_sync_packet(), peer_id)
        caps = fm._state.capabilities.elements()
        assert "mesh-net" in caps
        assert "ai-orchestrator" in caps

    def test_universe_mode_sync(self):
        fm = GlobalFederationManager(node_id="test-um-sync")
        fm.add_peer("did:example:um", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.consent_peer(peer_id)
        remote = FederatedNodeState("remote-um")
        remote.universe_mode.set("developer", "remote-um")
        fm.receive_sync(remote.to_sync_packet(), peer_id)
        assert fm._state.universe_mode.get() == "developer"

    def test_display_name_sync(self):
        fm = GlobalFederationManager(node_id="test-dn-sync")
        fm.add_peer("did:example:dn", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.consent_peer(peer_id)
        remote = FederatedNodeState("remote-dn")
        remote.display_name.set("SyncName", "remote-dn")
        fm.receive_sync(remote.to_sync_packet(), peer_id)
        assert fm._state.display_name.get() == "SyncName"

    def test_add_peer_auto_active_peers(self):
        fm = GlobalFederationManager(node_id="test-auto-active")
        p = fm.add_peer("did:example:auto", "ws://10.0.0.1:9000")
        assert p.peer_id in fm._state.active_peers.elements()

    def test_revoke_removes_from_active_peers(self):
        fm = GlobalFederationManager(node_id="test-revoke-active")
        p = fm.add_peer("did:example:ra", "ws://10.0.0.1:9000")
        fm.consent_peer(p.peer_id)
        assert p.peer_id in fm._state.active_peers.elements()
        fm.revoke_peer(p.peer_id)
        assert p.peer_id not in fm._state.active_peers.elements()

    def test_remove_peer_removes_from_active_peers(self):
        fm = GlobalFederationManager(node_id="test-rm-active")
        p = fm.add_peer("did:example:rma", "ws://10.0.0.1:9000")
        assert p.peer_id in fm._state.active_peers.elements()
        fm.remove_peer(p.peer_id)
        assert p.peer_id not in fm._state.active_peers.elements()

    def test_status_after_operations(self):
        fm = GlobalFederationManager(node_id="test-status-ops")
        p1 = fm.add_peer("did:example:s1", "ws://10.0.0.1:9000")
        p2 = fm.add_peer("did:example:s2", "ws://10.0.0.2:9000")
        fm.consent_peer(p1.peer_id)
        s = fm.status()
        assert s["peers"] == 2
        assert s["trusted_peers"] == 1
        assert p1.peer_id in s["active_peers"]
        assert p2.peer_id in s["active_peers"]

    def test_node_id_auto_generated(self):
        fm = GlobalFederationManager()
        assert fm.node_id is not None
        assert len(fm.node_id) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# GCounter Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestGCounterEdgeCases:
    """Edge cases for GCounter."""

    def test_merge_same_node_lower_value(self):
        c = GCounter("a")
        c.increment(10)
        lower = GCounter("a")
        lower.increment(3)
        c.merge(lower)
        assert c.value() == 10

    def test_merge_empty_counter(self):
        c = GCounter("a")
        c.increment(5)
        empty = GCounter("b")
        c.merge(empty)
        assert c.value() == 5

    def test_from_state_empty(self):
        c = GCounter.from_state("a", {})
        assert c.value() == 0

    def test_from_state_preserves_other_nodes(self):
        state = {"a": 3, "b": 7}
        c = GCounter.from_state("c", state)
        assert c.value() == 10

    def test_multiple_merges_converge(self):
        c = GCounter("a")
        c.increment(2)
        for _ in range(10):
            other = GCounter("b")
            other.increment(5)
            c.merge(other)
        assert c.value() == 7

    def test_large_increment(self):
        c = GCounter("a")
        c.increment(10**9)
        assert c.value() == 10**9


# ═══════════════════════════════════════════════════════════════════════════════
# LWWRegister Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestLWWRegisterEdgeCases:
    """Edge cases for LWWRegister."""

    def test_set_none_value(self):
        r = LWWRegister()
        r.set(None, "node1")
        assert r.get() is None

    def test_set_dict_value(self):
        r = LWWRegister()
        val = {"key": "value", "nested": [1, 2, 3]}
        r.set(val, "node1")
        assert r.get() == val

    def test_merge_empty_register(self):
        r1 = LWWRegister()
        r1.set("existing", "a")
        r2 = LWWRegister()
        r1.merge(r2)
        assert r1.get() == "existing"

    def test_state_round_trip_none(self):
        r = LWWRegister()
        r2 = LWWRegister.from_state(r.state())
        assert r2.get() is None


# ═══════════════════════════════════════════════════════════════════════════════
# ORSet Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestORSetEdgeCases:
    """Edge cases for ORSet."""

    def test_merge_empty_set(self):
        s = ORSet("a")
        s.add("x")
        empty = ORSet("b")
        s.merge(empty)
        assert s.elements() == {"x"}

    def test_multiple_adds_same_value(self):
        s = ORSet("a")
        s.add("x")
        s.add("x")
        s.add("x")
        assert len(s._add_set["x"]) == 3
        s.remove("x")
        assert s.elements() == set()

    def test_remove_re_add_cycle(self):
        s = ORSet("a")
        s.add("x")
        s.remove("x")
        s.add("x")
        assert "x" in s.elements()

    def test_state_round_trip_removes(self):
        s = ORSet("a")
        s.add("x")
        s.add("y")
        s.remove("x")
        state = s.state()
        s2 = ORSet.from_state("b", state)
        assert "y" in s2.elements()

    def test_merge_convergence(self):
        s1 = ORSet("a")
        s1.add("x")
        s2 = ORSet("b")
        s2.add("y")
        s2.remove("y")
        s1.merge(s2)
        s2.merge(s1)
        assert s1.elements() == {"x"}
        assert s2.elements() == {"x"}

    def test_add_after_merge(self):
        s1 = ORSet("a")
        s1.add("x")
        s2 = ORSet("b")
        s2.merge(s1)
        s2.add("y")
        assert s2.elements() == {"x", "y"}


# ═══════════════════════════════════════════════════════════════════════════════
# GlobalFederationManager Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestGlobalFederationManagerEdgeCases:
    """Edge cases, error recovery, and environmental config for GFM."""

    def test_sync_interval_env_malformed(self):
        os.environ["ASIM_FED_SYNC_INTERVAL"] = "not_a_number"
        fm = GlobalFederationManager(node_id="test-mal-sync")
        assert fm.sync_interval == 60
        del os.environ["ASIM_FED_SYNC_INTERVAL"]

    def test_max_peers_env_malformed(self):
        os.environ["ASIM_FED_MAX_PEERS"] = "bad_value"
        fm = GlobalFederationManager(node_id="test-mal-max")
        assert fm.max_peers == 100
        del os.environ["ASIM_FED_MAX_PEERS"]

    def test_sync_interval_env_zero(self):
        os.environ["ASIM_FED_SYNC_INTERVAL"] = "0"
        fm = GlobalFederationManager(node_id="test-zero-sync")
        assert fm.sync_interval == 60
        del os.environ["ASIM_FED_SYNC_INTERVAL"]

    def test_max_peers_env_zero(self):
        os.environ["ASIM_FED_MAX_PEERS"] = "0"
        fm = GlobalFederationManager(node_id="test-zero-max")
        assert fm.max_peers == 100
        del os.environ["ASIM_FED_MAX_PEERS"]

    def test_constructor_priority(self):
        os.environ["ASIM_FED_SYNC_INTERVAL"] = "999"
        fm = GlobalFederationManager(node_id="test-priority", sync_interval=300)
        assert fm.sync_interval == 300
        del os.environ["ASIM_FED_SYNC_INTERVAL"]

    def test_duplicate_add_peer_same_did_endpoint(self):
        fm = GlobalFederationManager(node_id="test-dup-peer")
        p1 = fm.add_peer("did:example:dup", "ws://10.0.0.1:9000")
        p2 = fm.add_peer("did:example:dup", "ws://10.0.0.1:9000")
        assert p1.peer_id == p2.peer_id
        assert len(fm._peers) == 1

    def test_consent_before_add(self):
        fm = GlobalFederationManager(node_id="test-consent-before-add")
        fm.consent_peer("ghost-peer")

    def test_sync_with_empty_packet(self):
        fm = GlobalFederationManager(node_id="test-empty-pkt")
        fm.add_peer("did:example:empty", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.consent_peer(peer_id)
        result = fm.receive_sync({}, peer_id)
        assert result["accepted"] is True
        assert result["changes"] >= 0

    def test_state_not_corrupted_on_bad_merge(self):
        fm = GlobalFederationManager(node_id="test-bad-merge")
        fm.add_peer("did:example:bad", "ws://10.0.0.1:9000")
        peer_id = list(fm._peers.keys())[0]
        fm.consent_peer(peer_id)
        bad_packet = {"node_id": "attacker", "msg_count": "not_a_dict"}
        try:
            result = fm.receive_sync(bad_packet, peer_id)
        except Exception:
            pass
        assert fm.status()["peers"] == 1

    def test_large_number_of_peers(self):
        fm = GlobalFederationManager(node_id="test-many-peers")
        for i in range(20):
            fm.add_peer(f"did:example:mass{i}", f"ws://10.0.0.{i}:9000")
        assert fm.status()["peers"] == 20

    def test_sync_round_trip_preserves_all_fields(self):
        alice = GlobalFederationManager(node_id="test-alice")
        bob = GlobalFederationManager(node_id="test-bob")
        alice.add_peer("did:bob", "ws://10.0.0.2:9000")
        bob.add_peer("did:alice", "ws://10.0.0.1:9000")
        alice_peer_id = list(alice._peers.keys())[0]
        bob_peer_id = list(bob._peers.keys())[0]
        alice.consent_peer(alice_peer_id)
        bob.consent_peer(bob_peer_id)
        alice._state.msg_count.increment(3)
        alice._state.display_name.set("Alice", alice.node_id)
        alice._state.capabilities.add("mesh")
        bob.receive_sync(alice.get_sync_packet(), bob_peer_id)
        assert bob._state.msg_count.value() >= 3
        assert bob._state.display_name.get() == "Alice"
        assert "mesh" in bob._state.capabilities.elements()
        bob._state.universe_mode.set("prod", bob.node_id)
        alice.receive_sync(bob.get_sync_packet(), alice_peer_id)
        assert alice._state.universe_mode.get() == "prod"

    def test_peer_count_after_remove_and_re_add(self):
        fm = GlobalFederationManager(node_id="test-re-add")
        p = fm.add_peer("did:example:readd", "ws://10.0.0.1:9000")
        pid = p.peer_id
        fm.remove_peer(pid)
        assert pid not in fm._peers
        p2 = fm.add_peer("did:example:readd", "ws://10.0.0.1:9000")
        assert p2.peer_id == pid
        assert pid in fm._peers
        assert fm.status()["peers"] == 1

    def test_sync_only_with_consented_peers(self):
        fm = GlobalFederationManager(node_id="test-filter-consent")
        p1 = fm.add_peer("did:trusted", "ws://10.0.0.1:9000")
        p2 = fm.add_peer("did:untrusted", "ws://10.0.0.2:9000")
        fm.consent_peer(p1.peer_id)
        remote = FederatedNodeState("remote")
        remote.msg_count.increment(5)
        r1 = fm.receive_sync(remote.to_sync_packet(), p1.peer_id)
        assert r1["accepted"] is True
        r2 = fm.receive_sync(remote.to_sync_packet(), p2.peer_id)
        assert r2["accepted"] is False
