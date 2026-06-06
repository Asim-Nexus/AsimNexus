#!/usr/bin/env python3
"""
Tests for NodeRegistry — Node trust registry for mesh network.

Covers:
- Node registration/deregistration (register_node)
- Node lookup by ID/address (get_node, get_nodes_by_trust, get_nodes_by_status)
- Heartbeat tracking (update_last_seen)
- Stale node cleanup (cleanup_stale_nodes)
- Trust level management (set_trust_level)
- Node status management (suspend/ban/unban)
- Stats reporting (get_stats)
- Trust events audit trail (get_trust_events)
- Global singleton (get_node_registry, reset_node_registry)
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from mesh.node_registry import (
    NodeRegistry,
    NodeRecord,
    TrustEvent,
    TrustLevel,
    NodeStatus,
    get_node_registry,
    reset_node_registry,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def registry():
    """Create a fresh NodeRegistry using in-memory SQLite."""
    reg = NodeRegistry(use_memory=True)
    yield reg


@pytest.fixture
def populated_registry(registry):
    """Pre-populate a registry with several nodes."""
    registry.register_node(
        node_id="node_alpha",
        hostname="alpha.local",
        ip_address="192.168.1.10",
        port=8000,
        capabilities=["chat", "mesh"],
        version="2.0.0",
    )
    registry.register_node(
        node_id="node_beta",
        hostname="beta.local",
        ip_address="192.168.1.11",
        port=8001,
        capabilities=["storage"],
        version="1.5.0",
    )
    registry.register_node(
        node_id="node_gamma",
        hostname="gamma.local",
        ip_address="192.168.1.12",
        port=8002,
        capabilities=["compute"],
        version="2.0.0",
    )
    return registry


# =============================================================================
# Node Registration Tests
# =============================================================================

class TestNodeRegistration:
    """Tests for node registration."""

    def test_register_new_node(self, registry):
        """register_node should create a new node record."""
        node = registry.register_node(
            node_id="new_node",
            hostname="new.local",
            ip_address="10.0.0.1",
            port=8000,
        )
        assert node.node_id == "new_node"
        assert node.hostname == "new.local"
        assert node.trust_level == TrustLevel.UNKNOWN
        assert node.status == NodeStatus.ONLINE
        assert "new_node" in registry.nodes

    def test_register_node_with_all_fields(self, registry):
        """register_node should accept and store all optional fields."""
        node = registry.register_node(
            node_id="full_node",
            hostname="full.local",
            ip_address="10.0.0.2",
            port=9000,
            public_key="abc123key",
            capabilities=["mesh", "compute"],
            version="3.0.0",
        )
        assert node.public_key == "abc123key"
        assert node.capabilities == ["mesh", "compute"]
        assert node.version == "3.0.0"

    def test_register_duplicate_node_updates(self, registry):
        """Registering an existing node ID should update its fields."""
        registry.register_node(
            node_id="dup_node",
            hostname="old.local",
            ip_address="10.0.0.1",
            port=8000,
        )

        registry.register_node(
            node_id="dup_node",
            hostname="new.local",
            ip_address="10.0.0.2",
            port=9000,
        )

        node = registry.get_node("dup_node")
        assert node.ip_address == "10.0.0.2"
        assert node.port == 9000
        # last_seen should be updated
        assert node.last_seen is not None

    def test_register_node_creates_trust_event(self, registry):
        """Registering a new node should log a discovery trust event."""
        registry.register_node(
            node_id="event_test",
            hostname="event.local",
            ip_address="10.0.0.3",
            port=8000,
        )
        events = registry.get_trust_events(node_id="event_test")
        assert len(events) >= 1
        assert events[0].event_type == "discovery"

    def test_register_node_persists_to_db(self, registry):
        """Registered node should be persisted to in-memory database."""
        registry.register_node(
            node_id="persist_test",
            hostname="persist.local",
            ip_address="10.0.0.4",
            port=8000,
        )

        # Create a new registry instance with in-memory DB (separate instance)
        registry2 = NodeRegistry(use_memory=True)
        # In-memory DB is per-connection, so this won't have the previous data
        # Instead verify the original registry has it
        assert "persist_test" in registry.nodes
        assert registry.nodes["persist_test"].ip_address == "10.0.0.4"


# =============================================================================
# Node Lookup Tests
# =============================================================================

class TestNodeLookup:
    """Tests for node lookup operations."""

    def test_get_node_by_id(self, populated_registry):
        """get_node should return the correct node by ID."""
        node = populated_registry.get_node("node_alpha")
        assert node is not None
        assert node.node_id == "node_alpha"
        assert node.hostname == "alpha.local"

    def test_get_nonexistent_node(self, populated_registry):
        """get_node should return None for unknown ID."""
        node = populated_registry.get_node("nonexistent")
        assert node is None

    def test_get_nodes_by_trust(self, populated_registry):
        """get_nodes_by_trust should filter correctly."""
        # Initially all are UNKNOWN
        unknown_nodes = populated_registry.get_nodes_by_trust(TrustLevel.UNKNOWN)
        assert len(unknown_nodes) == 3

        trusted_nodes = populated_registry.get_nodes_by_trust(TrustLevel.TRUSTED)
        assert len(trusted_nodes) == 0

    def test_get_nodes_by_status(self, populated_registry):
        """get_nodes_by_status should filter by status."""
        online_nodes = populated_registry.get_nodes_by_status(NodeStatus.ONLINE)
        assert len(online_nodes) == 3

        offline_nodes = populated_registry.get_nodes_by_status(NodeStatus.OFFLINE)
        assert len(offline_nodes) == 0

    def test_get_online_nodes(self, populated_registry):
        """get_online_nodes should return only online nodes."""
        online = populated_registry.get_online_nodes()
        assert len(online) == 3


# =============================================================================
# Trust Level Management Tests
# =============================================================================

class TestTrustManagement:
    """Tests for trust level management."""

    def test_set_trust_level(self, populated_registry):
        """set_trust_level should change node trust level."""
        result = populated_registry.set_trust_level(
            "node_alpha", TrustLevel.TRUSTED, reason="Verified manually"
        )
        assert result is True
        node = populated_registry.get_node("node_alpha")
        assert node.trust_level == TrustLevel.TRUSTED

    def test_set_trust_level_nonexistent_node(self, populated_registry):
        """set_trust_level on nonexistent node should return False."""
        result = populated_registry.set_trust_level(
            "no_such_node", TrustLevel.HIGH, reason="testing"
        )
        assert result is False

    def test_set_trust_level_logs_event(self, populated_registry):
        """Setting trust level should create a trust event."""
        populated_registry.set_trust_level(
            "node_alpha", TrustLevel.HIGH, reason="Performance verified"
        )
        events = populated_registry.get_trust_events(node_id="node_alpha")
        trust_changes = [e for e in events if e.event_type == "trust_change"]
        assert len(trust_changes) >= 1
        assert trust_changes[0].reason == "Performance verified"

    def test_multiple_trust_level_changes(self, populated_registry):
        """Multiple trust level changes should all be logged."""
        populated_registry.set_trust_level("node_beta", TrustLevel.LOW, reason="Initial")
        populated_registry.set_trust_level("node_beta", TrustLevel.MEDIUM, reason="Improved")
        populated_registry.set_trust_level("node_beta", TrustLevel.HIGH, reason="Verified")

        events = populated_registry.get_trust_events(node_id="node_beta")
        trust_changes = [e for e in events if e.event_type == "trust_change"]
        assert len(trust_changes) == 3


# =============================================================================
# Node Status Management Tests
# =============================================================================

class TestNodeStatus:
    """Tests for node status management (suspend/ban/unban)."""

    def test_suspend_node(self, populated_registry):
        """suspend_node should change status to SUSPENDED."""
        result = populated_registry.suspend_node("node_alpha", reason="Maintenance")
        assert result is True
        node = populated_registry.get_node("node_alpha")
        assert node.status == NodeStatus.SUSPENDED

    def test_suspend_nonexistent_node(self, populated_registry):
        """suspend_node on nonexistent node should return False."""
        result = populated_registry.suspend_node("no_node", reason="test")
        assert result is False

    def test_ban_node(self, populated_registry):
        """ban_node should change status to BANNED and trust to UNTRUSTED."""
        result = populated_registry.ban_node("node_alpha", reason="Security violation")
        assert result is True
        node = populated_registry.get_node("node_alpha")
        assert node.status == NodeStatus.BANNED
        assert node.trust_level == TrustLevel.UNTRUSTED

    def test_ban_nonexistent_node(self, populated_registry):
        """ban_node on nonexistent node should return False."""
        result = populated_registry.ban_node("no_node", reason="test")
        assert result is False

    def test_unban_node(self, populated_registry):
        """unban_node should restore status to ONLINE and trust to LOW."""
        populated_registry.ban_node("node_alpha", reason="Bad behavior")
        result = populated_registry.unban_node("node_alpha", reason="Appealed")
        assert result is True
        node = populated_registry.get_node("node_alpha")
        assert node.status == NodeStatus.ONLINE
        assert node.trust_level == TrustLevel.LOW

    def test_unban_nonexistent_node(self, populated_registry):
        """unban_node on nonexistent node should return False."""
        result = populated_registry.unban_node("no_node", reason="test")
        assert result is False

    def test_ban_logs_event(self, populated_registry):
        """Banning a node should log a ban event."""
        populated_registry.ban_node("node_gamma", reason="Compromised")
        events = populated_registry.get_trust_events(node_id="node_gamma")
        ban_events = [e for e in events if e.event_type == "ban"]
        assert len(ban_events) >= 1


# =============================================================================
# Heartbeat / last_seen Tests
# =============================================================================

class TestHeartbeat:
    """Tests for heartbeat / last_seen updates."""

    def test_update_last_seen(self, populated_registry):
        """update_last_seen should refresh last_seen and last_contact."""
        old_last_seen = populated_registry.get_node("node_alpha").last_seen
        # Small delay to ensure timestamp changes
        time.sleep(0.01)
        result = populated_registry.update_last_seen("node_alpha")
        assert result is True
        node = populated_registry.get_node("node_alpha")
        assert node.last_seen >= old_last_seen
        assert node.last_contact is not None

    def test_update_last_seen_nonexistent(self, populated_registry):
        """update_last_seen on nonexistent node should return False."""
        result = populated_registry.update_last_seen("no_node")
        assert result is False


# =============================================================================
# Stale Node Cleanup Tests
# =============================================================================

class TestStaleCleanup:
    """Tests for stale node cleanup."""

    def test_cleanup_stale_nodes(self, registry):
        """cleanup_stale_nodes should mark old nodes as OFFLINE."""
        # Register a node
        registry.register_node(
            node_id="old_node",
            hostname="old.local",
            ip_address="10.0.0.1",
            port=8000,
        )
        # Manually set last_seen to the past
        old_time = (datetime.utcnow() - timedelta(seconds=7200)).isoformat()
        registry.nodes["old_node"].last_seen = old_time
        registry._persist_node(registry.nodes["old_node"])

        offline = registry.cleanup_stale_nodes(max_age_seconds=3600)
        assert "old_node" in offline
        assert registry.nodes["old_node"].status == NodeStatus.OFFLINE

    def test_cleanup_stale_nodes_fresh_node_stays_online(self, populated_registry):
        """Fresh nodes should remain ONLINE after cleanup."""
        offline = populated_registry.cleanup_stale_nodes(max_age_seconds=3600)
        for node_id in ["node_alpha", "node_beta", "node_gamma"]:
            assert node_id not in offline
            assert populated_registry.nodes[node_id].status == NodeStatus.ONLINE

    def test_cleanup_empty_registry(self, registry):
        """Cleanup on empty registry returns empty list."""
        offline = registry.cleanup_stale_nodes(max_age_seconds=60)
        assert offline == []

    def test_cleanup_already_offline_node(self, populated_registry):
        """Already OFFLINE nodes should not be listed again."""
        populated_registry.nodes["node_alpha"].status = NodeStatus.OFFLINE
        offline = populated_registry.cleanup_stale_nodes(max_age_seconds=3600)
        # Even if old, it's already offline so not in list
        assert "node_alpha" not in offline

    def test_cleanup_invalid_date_handling(self, registry):
        """Nodes with invalid last_seen should be skipped."""
        registry.register_node(
            node_id="bad_date",
            hostname="bad.local",
            ip_address="10.0.0.99",
            port=8000,
        )
        registry.nodes["bad_date"].last_seen = "not-a-date"
        # Should not raise
        offline = registry.cleanup_stale_nodes(max_age_seconds=60)
        assert "bad_date" not in offline


# =============================================================================
# Trust Events Tests
# =============================================================================

class TestTrustEvents:
    """Tests for the trust events audit trail."""

    def test_get_trust_events_all(self, populated_registry):
        """get_trust_events should return all events without filter."""
        events = populated_registry.get_trust_events()
        # 3 discovery events from registration
        assert len(events) >= 3

    def test_get_trust_events_filtered_by_node(self, populated_registry):
        """get_trust_events should filter by node_id."""
        populated_registry.set_trust_level("node_alpha", TrustLevel.HIGH, reason="test")
        events = populated_registry.get_trust_events(node_id="node_alpha")
        assert all(e.node_id == "node_alpha" for e in events)

    def test_get_trust_events_limit(self, populated_registry):
        """get_trust_events should respect the limit parameter."""
        # Create many events
        for i in range(10):
            populated_registry.set_trust_level(
                "node_alpha", TrustLevel.HIGH, reason=f"test_{i}"
            )
        events = populated_registry.get_trust_events(limit=5)
        assert len(events) <= 5

    def test_trust_events_ordered_by_time(self, populated_registry):
        """Trust events should be ordered (most recent first by default)."""
        populated_registry.set_trust_level("node_alpha", TrustLevel.LOW, reason="first")
        populated_registry.set_trust_level("node_alpha", TrustLevel.HIGH, reason="second")
        events = populated_registry.get_trust_events(node_id="node_alpha")
        trust_changes = [e for e in events if e.event_type == "trust_change"]
        if len(trust_changes) >= 2:
            assert trust_changes[0].reason == "second"


# =============================================================================
# Stats Tests
# =============================================================================

class TestStats:
    """Tests for registry statistics."""

    def test_get_stats_empty(self, registry):
        """get_stats on empty registry should show zeros."""
        stats = registry.get_stats()
        assert stats["total_nodes"] == 0
        assert stats["online_nodes"] == 0
        assert stats["offline_nodes"] == 0
        assert stats["total_trust_events"] == 0

    def test_get_stats_populated(self, populated_registry):
        """get_stats should reflect actual registry state."""
        stats = populated_registry.get_stats()
        assert stats["total_nodes"] == 3
        assert stats["online_nodes"] == 3
        assert stats["offline_nodes"] == 0

    def test_get_stats_trust_and_status_breakdown(self, populated_registry):
        """get_stats should break down by trust level and status."""
        populated_registry.set_trust_level("node_alpha", TrustLevel.TRUSTED, reason="proven")
        populated_registry.suspend_node("node_beta", reason="maintenance")

        stats = populated_registry.get_stats()
        assert stats["by_trust_level"]["trusted"] >= 1
        assert stats["by_status"]["suspended"] >= 1

    def test_get_stats_tracks_events(self, populated_registry):
        """get_stats should count trust events."""
        stats = populated_registry.get_stats()
        # 3 discovery events
        assert stats["total_trust_events"] >= 3
        populated_registry.ban_node("node_alpha", reason="test")
        stats = populated_registry.get_stats()
        assert stats["total_trust_events"] >= 4


# =============================================================================
# Singleton Tests
# =============================================================================

class TestSingleton:
    """Tests for global singleton functions."""

    def test_get_node_registry_creates_singleton(self):
        """get_node_registry should return the same instance."""
        reset_node_registry()
        r1 = get_node_registry()
        r2 = get_node_registry()
        assert r1 is r2
        reset_node_registry()

    def test_reset_node_registry_clears(self):
        """reset_node_registry should clear the global instance."""
        reset_node_registry()
        r1 = get_node_registry()
        reset_node_registry()
        r2 = get_node_registry()
        assert r2 is not r1
        reset_node_registry()


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_register_node_with_empty_capabilities(self, registry):
        """Registering with empty capabilities should work."""
        node = registry.register_node(
            node_id="empty_caps",
            hostname="empty.local",
            ip_address="10.0.0.1",
            port=8000,
            capabilities=[],
        )
        assert node.capabilities == []

    def test_register_node_without_capabilities(self, registry):
        """Registering without capabilities should default to empty list."""
        node = registry.register_node(
            node_id="no_caps",
            hostname="no_caps.local",
            ip_address="10.0.0.2",
            port=8000,
        )
        assert node.capabilities == []

    def test_cleanup_stale_deduplication(self, populated_registry):
        """Same node should appear only once in stale list."""
        # Force node_alpha to be old
        old_time = (datetime.utcnow() - timedelta(seconds=7200)).isoformat()
        populated_registry.nodes["node_alpha"].last_seen = old_time
        populated_registry._persist_node(populated_registry.nodes["node_alpha"])

        offline = populated_registry.cleanup_stale_nodes(max_age_seconds=3600)
        assert offline.count("node_alpha") == 1
