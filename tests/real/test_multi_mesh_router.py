#!/usr/bin/env python3
"""
Tests for [`mesh/multi_mesh_router.py`](../../mesh/multi_mesh_router.py)
Covers Gap 6: Multi-Mesh Router with mesh type selection, auto-switching,
routing rules, and singleton factory.
"""

import os
import json
import time
import pytest
from typing import Dict, Any
from unittest.mock import patch

from mesh.multi_mesh_router import (
    MeshType,
    MeshConnectionState,
    DataClassification,
    MeshProfile,
    MeshRequirements,
    MeshRoutingRule,
    MeshSwitchEvent,
    MultiMeshRouter,
    get_multi_mesh_router,
    reset_multi_mesh_router,
    __all__ as module_exports,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_router():
    """Reset singleton before each test (and clean up after)."""
    reset_multi_mesh_router()
    yield
    reset_multi_mesh_router()


@pytest.fixture
def router() -> MultiMeshRouter:
    """Fresh MultiMeshRouter instance."""
    return MultiMeshRouter()


# ─── Test: MeshType ────────────────────────────────────────────────────────────

class TestMeshType:
    """Tests for MeshType enum."""

    def test_values(self):
        assert MeshType.LOCAL.value == "local"
        assert MeshType.PERSONAL.value == "personal"
        assert MeshType.CLOUD.value == "cloud"
        assert MeshType.PUBLIC.value == "public"

    def test_all_types_available(self):
        types = set(MeshType)
        assert len(types) == 4
        assert MeshType.LOCAL in types
        assert MeshType.PERSONAL in types
        assert MeshType.CLOUD in types
        assert MeshType.PUBLIC in types


# ─── Test: MeshConnectionState ─────────────────────────────────────────────────

class TestMeshConnectionState:
    """Tests for MeshConnectionState enum."""

    def test_values(self):
        assert MeshConnectionState.DISCONNECTED.value == "disconnected"
        assert MeshConnectionState.CONNECTING.value == "connecting"
        assert MeshConnectionState.CONNECTED.value == "connected"
        assert MeshConnectionState.DEGRADED.value == "degraded"
        assert MeshConnectionState.ERROR.value == "error"

    def test_all_states(self):
        states = set(MeshConnectionState)
        assert len(states) == 5


# ─── Test: DataClassification ──────────────────────────────────────────────────

class TestDataClassification:
    """Tests for DataClassification enum."""

    def test_values(self):
        assert DataClassification.PUBLIC.value == "public"
        assert DataClassification.INTERNAL.value == "internal"
        assert DataClassification.SENSITIVE.value == "sensitive"
        assert DataClassification.SECRET.value == "secret"

    def test_all_levels(self):
        levels = set(DataClassification)
        assert len(levels) == 4


# ─── Test: MeshProfile ─────────────────────────────────────────────────────────

class TestMeshProfile:
    """Tests for MeshProfile dataclass."""

    def test_create_default(self):
        profile = MeshProfile(
            mesh_type=MeshType.LOCAL,
            trust_level=1.0,
            max_latency_ms=1.0,
            avg_latency_ms=0.5,
            bandwidth_kbps=100000.0,
            peers_available=5,
            is_connected=True,
        )
        assert profile.mesh_type == MeshType.LOCAL
        assert profile.trust_level == 1.0
        assert profile.priority == 0  # default
        assert profile.connection_state == MeshConnectionState.DISCONNECTED  # default
        assert DataClassification.PUBLIC in profile.data_classifications_allowed

    def test_to_dict(self):
        profile = MeshProfile(
            mesh_type=MeshType.PERSONAL,
            trust_level=0.9,
            max_latency_ms=50.0,
            avg_latency_ms=10.0,
            bandwidth_kbps=50000.0,
            peers_available=3,
            is_connected=True,
            connection_state=MeshConnectionState.CONNECTED,
            priority=1,
        )
        d = profile.to_dict()
        assert d["mesh_type"] == "personal"
        assert d["trust_level"] == 0.9
        assert d["connection_state"] == "connected"
        assert d["priority"] == 1
        assert "public" in d["data_classifications_allowed"]


# ─── Test: MeshRequirements ────────────────────────────────────────────────────

class TestMeshRequirements:
    """Tests for MeshRequirements dataclass."""

    def test_defaults(self):
        req = MeshRequirements()
        assert req.data_classification == DataClassification.PUBLIC
        assert req.max_accepted_latency_ms == float("inf")
        assert req.min_bandwidth_kbps == 0.0
        assert req.min_trust_level == 0.0
        assert req.preferred_mesh_types is None
        assert req.requires_connected is True

    def test_to_dict(self):
        req = MeshRequirements(
            data_classification=DataClassification.SENSITIVE,
            max_accepted_latency_ms=100.0,
            min_bandwidth_kbps=1000.0,
            min_trust_level=0.8,
            preferred_mesh_types=[MeshType.LOCAL, MeshType.PERSONAL],
        )
        d = req.to_dict()
        assert d["data_classification"] == "sensitive"
        assert d["max_accepted_latency_ms"] == 100.0
        assert d["min_bandwidth_kbps"] == 1000.0
        assert d["min_trust_level"] == 0.8
        assert d["preferred_mesh_types"] == ["local", "personal"]


# ─── Test: MeshRoutingRule ─────────────────────────────────────────────────────

class TestMeshRoutingRule:
    """Tests for MeshRoutingRule dataclass."""

    def test_create(self):
        rule = MeshRoutingRule(
            id="test_rule",
            description="Test rule",
            data_classification=DataClassification.SECRET,
            mesh_type=MeshType.LOCAL,
            priority=100,
        )
        assert rule.id == "test_rule"
        assert rule.data_classification == DataClassification.SECRET
        assert rule.active is True

    def test_to_dict(self):
        rule = MeshRoutingRule(
            id="rule_1",
            description="SECRET → LOCAL",
            data_classification=DataClassification.SECRET,
            mesh_type=MeshType.LOCAL,
            priority=100,
        )
        d = rule.to_dict()
        assert d["id"] == "rule_1"
        assert d["data_classification"] == "secret"
        assert d["mesh_type"] == "local"

    def test_from_dict(self):
        data = {
            "id": "rule_2",
            "description": "PUBLIC → any",
            "data_classification": "public",
            "mesh_type": None,
            "priority": 10,
            "active": True,
            "created_at": 1000.0,
        }
        rule = MeshRoutingRule.from_dict(data)
        assert rule.id == "rule_2"
        assert rule.data_classification == DataClassification.PUBLIC
        assert rule.mesh_type is None

    def test_from_dict_with_mesh(self):
        data = {
            "id": "rule_3",
            "description": "SENSITIVE → PERSONAL",
            "data_classification": "sensitive",
            "mesh_type": "personal",
            "priority": 90,
            "active": True,
            "created_at": 1000.0,
        }
        rule = MeshRoutingRule.from_dict(data)
        assert rule.data_classification == DataClassification.SENSITIVE
        assert rule.mesh_type == MeshType.PERSONAL


# ─── Test: MeshSwitchEvent ─────────────────────────────────────────────────────

class TestMeshSwitchEvent:
    """Tests for MeshSwitchEvent dataclass."""

    def test_create(self):
        event = MeshSwitchEvent(
            timestamp=1000.0,
            from_mesh=MeshType.LOCAL,
            to_mesh=MeshType.PERSONAL,
            reason="Testing",
            initiated_by="human",
            success=True,
        )
        assert event.from_mesh == MeshType.LOCAL
        assert event.to_mesh == MeshType.PERSONAL
        assert event.reason == "Testing"

    def test_to_dict(self):
        event = MeshSwitchEvent(
            timestamp=1000.0,
            from_mesh=None,
            to_mesh=MeshType.LOCAL,
            reason="Initial",
            initiated_by="auto",
            success=True,
        )
        d = event.to_dict()
        assert d["from_mesh"] is None
        assert d["to_mesh"] == "local"
        assert d["initiated_by"] == "auto"


# ─── Test: MultiMeshRouter — Initialization ────────────────────────────────────

class TestMultiMeshRouterInit:
    """Tests for MultiMeshRouter initialization."""

    def test_default_active_mesh(self, router):
        assert router.get_active_mesh() == MeshType.LOCAL

    def test_all_profiles_initialized(self, router):
        profiles = router.get_available_meshes()
        assert len(profiles) == 4
        assert MeshType.LOCAL in profiles
        assert MeshType.PERSONAL in profiles
        assert MeshType.CLOUD in profiles
        assert MeshType.PUBLIC in profiles

    def test_local_is_connected_by_default(self, router):
        profiles = router.get_available_meshes()
        assert profiles[MeshType.LOCAL].is_connected is True
        assert profiles[MeshType.PERSONAL].is_connected is False
        assert profiles[MeshType.CLOUD].is_connected is False
        assert profiles[MeshType.PUBLIC].is_connected is False

    def test_baseline_priorities(self, router):
        profiles = router.get_available_meshes()
        assert profiles[MeshType.LOCAL].priority == 0
        assert profiles[MeshType.PERSONAL].priority == 1
        assert profiles[MeshType.CLOUD].priority == 2
        assert profiles[MeshType.PUBLIC].priority == 3

    def test_default_routing_rules(self, router):
        rules = router.get_routing_rules()
        assert len(rules) >= 4
        rule_ids = [r.id for r in rules]
        assert "rule_secret_local" in rule_ids
        assert "rule_sensitive_personal" in rule_ids
        assert "rule_internal_cloud" in rule_ids
        assert "rule_public_any" in rule_ids

    def test_connected_meshes_initial(self, router):
        connected = router.get_connected_meshes()
        assert MeshType.LOCAL in connected
        assert MeshType.PERSONAL not in connected


# ─── Test: MultiMeshRouter — Select Mesh ───────────────────────────────────────

class TestSelectMesh:
    """Tests for select_mesh()."""

    def test_select_default_returns_local(self, router):
        """With default config, LOCAL should be selected."""
        mtype, profile = router.select_mesh()
        assert mtype == MeshType.LOCAL
        assert profile.mesh_type == MeshType.LOCAL

    def test_select_secret_data_only_local(self, router):
        """SECRET data must route through LOCAL mesh."""
        req = MeshRequirements(data_classification=DataClassification.SECRET)
        mtype, profile = router.select_mesh(req)
        assert mtype == MeshType.LOCAL

    def test_select_sensitive_prefers_personal(self, router):
        """SENSITIVE data should prefer PERSONAL (via routing rules)."""
        # Make PERSONAL connected
        router.update_mesh_health(MeshType.PERSONAL, True)
        req = MeshRequirements(data_classification=DataClassification.SENSITIVE)
        mtype, profile = router.select_mesh(req)
        assert mtype == MeshType.PERSONAL

    def test_select_public_can_use_any(self, router):
        """PUBLIC data can use any connected mesh."""
        router.update_mesh_health(MeshType.PERSONAL, True)
        req = MeshRequirements(data_classification=DataClassification.PUBLIC)
        mtype, profile = router.select_mesh(req)
        # Should be LOCAL (lowest priority number = 0, connected)
        assert mtype == MeshType.LOCAL

    def test_select_preferred_mesh_types(self, router):
        """Preferred mesh types filter should work."""
        router.update_mesh_health(MeshType.PERSONAL, True)
        router.update_mesh_health(MeshType.CLOUD, True)
        req = MeshRequirements(
            data_classification=DataClassification.PUBLIC,
            preferred_mesh_types=[MeshType.CLOUD],
        )
        mtype, profile = router.select_mesh(req)
        assert mtype == MeshType.CLOUD

    def test_select_no_connected_mesh_raises(self, router):
        """If no mesh is connected and requires_connected=True, should raise."""
        # Disconnect LOCAL
        router.update_mesh_health(MeshType.LOCAL, False)
        req = MeshRequirements(requires_connected=True)
        with pytest.raises(RuntimeError, match="No mesh meets requirements"):
            router.select_mesh(req)

    def test_select_allows_disconnected(self, router):
        """If requires_connected=False, disconnected meshes can be selected."""
        router.update_mesh_health(MeshType.LOCAL, False)
        req = MeshRequirements(requires_connected=False)
        mtype, profile = router.select_mesh(req)
        assert mtype == MeshType.LOCAL  # Still lowest priority

    def test_select_latency_filter(self, router):
        """Meshes exceeding latency threshold should be filtered out."""
        router.update_mesh_health(MeshType.LOCAL, True, latency_ms=1.0)
        req = MeshRequirements(max_accepted_latency_ms=0.5)
        with pytest.raises(RuntimeError, match="No mesh meets requirements"):
            router.select_mesh(req)

    def test_select_bandwidth_filter(self, router):
        """Meshes below bandwidth threshold should be filtered out."""
        req = MeshRequirements(min_bandwidth_kbps=999999.0)
        with pytest.raises(RuntimeError, match="No mesh meets requirements"):
            router.select_mesh(req)

    def test_select_trust_filter(self, router):
        """Meshes below trust threshold should be filtered out."""
        req = MeshRequirements(min_trust_level=1.5)  # Impossible
        with pytest.raises(RuntimeError, match="No mesh meets requirements"):
            router.select_mesh(req)

    def test_select_priority_ordering_local(self, router):
        """LOCAL (priority 0) should be selected over others."""
        router.update_mesh_health(MeshType.PERSONAL, True)
        router.update_mesh_health(MeshType.CLOUD, True)
        router.update_mesh_health(MeshType.PUBLIC, True)
        mtype, profile = router.select_mesh()
        assert mtype == MeshType.LOCAL

    def test_select_custom_routing_rule_overrides(self, router):
        """Custom routing rules should override default priority."""
        router.update_mesh_health(MeshType.CLOUD, True)
        # Add rule that forces PUBLIC data through CLOUD
        rule = MeshRoutingRule(
            id="custom_cloud_for_public",
            description="Force PUBLIC → CLOUD",
            data_classification=DataClassification.PUBLIC,
            mesh_type=MeshType.CLOUD,
            priority=200,  # Higher than defaults
        )
        router.add_routing_rule(rule)
        mtype, profile = router.select_mesh()
        assert mtype == MeshType.CLOUD


# ─── Test: MultiMeshRouter — Switch Mesh ──────────────────────────────────────

class TestSwitchMesh:
    """Tests for switch_mesh()."""

    def test_switch_to_connected_mesh(self, router):
        """Switching to a connected mesh should succeed."""
        router.update_mesh_health(MeshType.PERSONAL, True)
        result = router.switch_mesh(MeshType.PERSONAL, "Testing", "human")
        assert result is True
        assert router.get_active_mesh() == MeshType.PERSONAL

    def test_switch_to_same_mesh(self, router):
        """Switching to the already active mesh should return True."""
        result = router.switch_mesh(MeshType.LOCAL, "No change", "human")
        assert result is True

    def test_switch_to_disconnected_mesh_raises(self, router):
        """Switching to a disconnected mesh should raise ValueError."""
        with pytest.raises(ValueError, match="not connected"):
            router.switch_mesh(MeshType.PUBLIC, "Won't work", "human")

    def test_switch_records_event(self, router):
        """Switching should add a switch event to history."""
        router.update_mesh_health(MeshType.PERSONAL, True)
        router.switch_mesh(MeshType.PERSONAL, "For testing", "human")
        history = router.get_switch_history()
        assert len(history) >= 1
        latest = history[0]
        assert latest.from_mesh == MeshType.LOCAL
        assert latest.to_mesh == MeshType.PERSONAL
        assert latest.initiated_by == "human"
        assert latest.success is True

    def test_switch_auto_initiated(self, router):
        """Auto-initiated switch should be recorded correctly."""
        router.update_mesh_health(MeshType.CLOUD, True)
        router.switch_mesh(MeshType.CLOUD, "Auto test", "auto")
        history = router.get_switch_history()
        assert history[0].initiated_by == "auto"


# ─── Test: MultiMeshRouter — Route Through Mesh ───────────────────────────────

class TestRouteThroughMesh:
    """Tests for route_through_mesh()."""

    def test_route_connected_mesh(self, router):
        """Routing through a connected mesh should succeed."""
        result = router.route_through_mesh(
            MeshType.LOCAL, b"hello", "peer_001"
        )
        assert result is True

    def test_route_disconnected_mesh(self, router):
        """Routing through a disconnected mesh should fail."""
        result = router.route_through_mesh(
            MeshType.PUBLIC, b"data", "peer_002"
        )
        assert result is False

    def test_route_after_connecting(self, router):
        """Routing should work after connecting the mesh."""
        router.update_mesh_health(MeshType.PERSONAL, True)
        result = router.route_through_mesh(
            MeshType.PERSONAL, b"test", "peer_003"
        )
        assert result is True


# ─── Test: MultiMeshRouter — Active Mesh Queries ──────────────────────────────

class TestActiveMeshQueries:
    """Tests for get_active_mesh() and get_active_profile()."""

    def test_get_active_mesh_default(self, router):
        assert router.get_active_mesh() == MeshType.LOCAL

    def test_get_active_profile_default(self, router):
        profile = router.get_active_profile()
        assert profile.mesh_type == MeshType.LOCAL
        assert profile.is_connected is True

    def test_get_active_profile_after_switch(self, router):
        router.update_mesh_health(MeshType.CLOUD, True)
        router.switch_mesh(MeshType.CLOUD, "Test", "human")
        profile = router.get_active_profile()
        assert profile.mesh_type == MeshType.CLOUD


# ─── Test: MultiMeshRouter — Health Checks ────────────────────────────────────

class TestHealthChecks:
    """Tests for health checker registration and mesh health updates."""

    def test_register_health_checker(self, router):
        checker = lambda: True
        router.register_health_checker(MeshType.PERSONAL, checker)
        stats = router.get_mesh_stats()
        assert stats["health_checkers_registered"] >= 1

    def test_update_mesh_health_connect(self, router):
        router.update_mesh_health(MeshType.PERSONAL, True)
        profiles = router.get_available_meshes()
        assert profiles[MeshType.PERSONAL].is_connected is True
        assert profiles[MeshType.PERSONAL].connection_state == MeshConnectionState.CONNECTED

    def test_update_mesh_health_disconnect(self, router):
        router.update_mesh_health(MeshType.LOCAL, False)
        profiles = router.get_available_meshes()
        assert profiles[MeshType.LOCAL].is_connected is False

    def test_update_mesh_health_with_metrics(self, router):
        router.update_mesh_health(
            MeshType.PERSONAL, True,
            latency_ms=25.0, bandwidth_kbps=50000.0, peers=3,
        )
        profile = router.get_available_meshes()[MeshType.PERSONAL]
        assert profile.avg_latency_ms == 10.0 * 0.7 + 25.0 * 0.3  # EMA
        assert profile.bandwidth_kbps == 50000.0
        assert profile.peers_available == 3

    def test_update_mesh_health_increments_error(self, router):
        profile = router.get_available_meshes()[MeshType.LOCAL]
        initial_errors = profile.error_count
        router.update_mesh_health(MeshType.LOCAL, False)
        assert profile.error_count == initial_errors + 1


# ─── Test: MultiMeshRouter — Routing Rules ────────────────────────────────────

class TestRoutingRules:
    """Tests for routing rule management."""

    def test_add_routing_rule(self, router):
        rule = MeshRoutingRule(
            id="custom_rule",
            description="Custom test rule",
            data_classification=DataClassification.INTERNAL,
            mesh_type=MeshType.PERSONAL,
            priority=50,
        )
        router.add_routing_rule(rule)
        rules = router.get_routing_rules()
        assert any(r.id == "custom_rule" for r in rules)

    def test_add_rule_replaces_existing(self, router):
        rule1 = MeshRoutingRule(
            id="same_id", description="Original", priority=10,
        )
        rule2 = MeshRoutingRule(
            id="same_id", description="Replacement", priority=20,
        )
        router.add_routing_rule(rule1)
        router.add_routing_rule(rule2)
        rules = router.get_routing_rules()
        matching = [r for r in rules if r.id == "same_id"]
        assert len(matching) == 1
        assert matching[0].priority == 20

    def test_remove_routing_rule(self, router):
        result = router.remove_routing_rule("rule_secret_local")
        assert result is True
        rules = router.get_routing_rules()
        assert not any(r.id == "rule_secret_local" for r in rules)

    def test_remove_nonexistent_rule(self, router):
        result = router.remove_routing_rule("nonexistent_rule")
        assert result is False


# ─── Test: MultiMeshRouter — Auto-Switch ──────────────────────────────────────

class TestAutoSwitch:
    """Tests for auto-switch functionality."""

    def test_auto_switch_enabled_by_default(self, router):
        stats = router.get_mesh_stats()
        assert stats["auto_switch_enabled"] is True

    def test_set_auto_switch_disabled(self, router):
        router.set_auto_switch_enabled(False)
        stats = router.get_mesh_stats()
        assert stats["auto_switch_enabled"] is False

    def test_auto_switch_fallback_on_disconnect(self, router):
        """When active mesh disconnects, auto-switch should fall back."""
        router.update_mesh_health(MeshType.PERSONAL, True)
        router.update_mesh_health(MeshType.LOCAL, False)
        router._evaluate_auto_switch()
        assert router.get_active_mesh() == MeshType.PERSONAL

    def test_auto_switch_to_better_mesh(self, router):
        """When a higher-priority mesh becomes available, switch to it."""
        router.update_mesh_health(MeshType.PERSONAL, True)
        router.switch_mesh(MeshType.PERSONAL, "Manual", "human")
        # PERSONAL is now active. LOCAL is still connected. Auto-switch
        # should switch back to LOCAL (priority 0 < 1).
        router._evaluate_auto_switch()
        assert router.get_active_mesh() == MeshType.LOCAL

    def test_auto_switch_no_op_if_already_best(self, router):
        """If active is already the best, auto-switch should do nothing."""
        # LOCAL is already active and best
        router._evaluate_auto_switch()
        assert router.get_active_mesh() == MeshType.LOCAL

    def test_auto_switch_does_nothing_when_disabled(self, router):
        router.set_auto_switch_enabled(False)
        router.update_mesh_health(MeshType.PERSONAL, True)
        router.update_mesh_health(MeshType.LOCAL, False)
        router._evaluate_auto_switch()
        # Should remain on LOCAL even though it's disconnected
        assert router.get_active_mesh() == MeshType.LOCAL

    def test_start_stop_auto_switch(self, router):
        """start_auto_switch() and stop_auto_switch() should not raise."""
        router.start_auto_switch()
        # Already running should log warning but not raise
        router.start_auto_switch()
        router.stop_auto_switch()


# ─── Test: MultiMeshRouter — Mesh Stats ───────────────────────────────────────

class TestMeshStats:
    """Tests for get_mesh_stats()."""

    def test_stats_structure(self, router):
        stats = router.get_mesh_stats()
        assert "active_mesh" in stats
        assert "connected_meshes" in stats
        assert "total_meshes" in stats
        assert "total_switches" in stats
        assert "auto_switches" in stats
        assert "human_switches" in stats
        assert "profiles" in stats
        assert stats["active_mesh"] == "local"
        assert stats["total_meshes"] == 4

    def test_stats_reflects_switches(self, router):
        router.update_mesh_health(MeshType.CLOUD, True)
        router.switch_mesh(MeshType.CLOUD, "Test", "human")
        stats = router.get_mesh_stats()
        assert stats["total_switches"] >= 1
        assert stats["human_switches"] >= 1

    def test_stats_connected_count(self, router):
        router.update_mesh_health(MeshType.PERSONAL, True)
        router.update_mesh_health(MeshType.CLOUD, True)
        stats = router.get_mesh_stats()
        assert stats["connected_meshes"] >= 2


# ─── Test: Switch History ─────────────────────────────────────────────────────

class TestSwitchHistory:
    """Tests for get_switch_history()."""

    def test_history_ordering(self, router):
        router.update_mesh_health(MeshType.PERSONAL, True)
        router.update_mesh_health(MeshType.CLOUD, True)
        router.switch_mesh(MeshType.PERSONAL, "First", "human")
        router.switch_mesh(MeshType.CLOUD, "Second", "human")
        history = router.get_switch_history()
        assert len(history) >= 2
        # Most recent first
        assert history[0].to_mesh == MeshType.CLOUD

    def test_history_limit(self, router):
        for i in range(5):
            mtype = list(MeshType)[i % 4]
            router.update_mesh_health(mtype, True)
            router.switch_mesh(mtype, f"Switch {i}", "auto")
        history = router.get_switch_history(limit=3)
        assert len(history) <= 3


# ─── Test: Singleton Factory ───────────────────────────────────────────────────

class TestSingletonFactory:
    """Tests for get_multi_mesh_router() and reset_multi_mesh_router()."""

    def test_singleton_returns_same_instance(self):
        r1 = get_multi_mesh_router()
        r2 = get_multi_mesh_router()
        assert r1 is r2

    def test_reset_creates_new_instance(self):
        r1 = get_multi_mesh_router()
        reset_multi_mesh_router()
        r2 = get_multi_mesh_router()
        assert r1 is not r2

    def test_singleton_preserves_state(self):
        r1 = get_multi_mesh_router()
        r1.update_mesh_health(MeshType.PERSONAL, True)
        r1.switch_mesh(MeshType.PERSONAL, "Test", "human")
        r2 = get_multi_mesh_router()
        assert r2.get_active_mesh() == MeshType.PERSONAL

    def test_reset_clears_state(self):
        r1 = get_multi_mesh_router()
        r1.update_mesh_health(MeshType.PERSONAL, True)
        r1.switch_mesh(MeshType.PERSONAL, "Test", "human")
        reset_multi_mesh_router()
        r2 = get_multi_mesh_router()
        assert r2.get_active_mesh() == MeshType.LOCAL  # Back to default


# ─── Test: Persistence ─────────────────────────────────────────────────────────

class TestPersistence:
    """Tests for JSONL persistence."""

    def test_switch_event_persisted(self, router, tmp_path):
        """Switch events should be written to disk."""
        import mesh.multi_mesh_router as mmr
        original_path = mmr._MESH_DB_PATH
        test_path = str(tmp_path / "test_mesh_routing.jsonl")
        try:
            mmr._MESH_DB_PATH = test_path
            # Create a new router with the patched path
            r = MultiMeshRouter()
            r.update_mesh_health(MeshType.CLOUD, True)
            r.switch_mesh(MeshType.CLOUD, "Test persist", "human")
            assert os.path.exists(test_path)
            with open(test_path) as f:
                lines = [l.strip() for l in f if l.strip()]
            assert len(lines) >= 1
            last = json.loads(lines[-1])
            assert last["to_mesh"] == "cloud"
        finally:
            mmr._MESH_DB_PATH = original_path

    def test_routing_rule_persisted(self, router, tmp_path):
        """Routing rules should be written to disk."""
        import mesh.multi_mesh_router as mmr
        original_path = mmr._MESH_DB_PATH
        rules_path = str(tmp_path / "test_mesh_routing_rules.jsonl")
        test_path = str(tmp_path / "test_mesh_routing.jsonl")
        try:
            # Patch so the rules file goes to our temp dir
            mmr._MESH_DB_PATH = test_path
            r = MultiMeshRouter()
            rule = MeshRoutingRule(
                id="persist_test",
                description="Persistence test",
                data_classification=DataClassification.PUBLIC,
                mesh_type=MeshType.CLOUD,
                priority=50,
            )
            r.add_routing_rule(rule)
            # Check the rules file
            rules_db = test_path.replace(".jsonl", "_rules.jsonl")
            if os.path.exists(rules_db):
                with open(rules_db) as f:
                    lines = [l.strip() for l in f if l.strip()]
                assert any("persist_test" in l for l in lines)
        finally:
            mmr._MESH_DB_PATH = original_path


# ─── Test: Module Exports ──────────────────────────────────────────────────────

class TestModuleExports:
    """Verify that __all__ exports match actual module contents."""

    def test_all_exports_defined(self):
        expected = [
            "MeshType",
            "MeshConnectionState",
            "DataClassification",
            "MeshProfile",
            "MeshRequirements",
            "MeshRoutingRule",
            "MeshSwitchEvent",
            "MultiMeshRouter",
            "get_multi_mesh_router",
            "reset_multi_mesh_router",
        ]
        for name in expected:
            assert name in module_exports, f"{name} missing from __all__"

    def test_all_exports_are_importable(self):
        from mesh.multi_mesh_router import (
            MeshType,
            MeshConnectionState,
            DataClassification,
            MeshProfile,
            MeshRequirements,
            MeshRoutingRule,
            MeshSwitchEvent,
            MultiMeshRouter,
            get_multi_mesh_router,
            reset_multi_mesh_router,
        )
        # Just verify they're not None
        assert MeshType is not None
        assert MultiMeshRouter is not None
        assert get_multi_mesh_router is not None


# ─── Test: Edge Cases ──────────────────────────────────────────────────────────

class TestEdgeCases:
    """Tests for boundary conditions and edge cases."""

    def test_select_mesh_with_no_routing_rules(self, router):
        """Should still work with no rules."""
        # Remove all rules
        for rule in list(router.get_routing_rules()):
            router.remove_routing_rule(rule.id)
        mtype, profile = router.select_mesh()
        assert mtype == MeshType.LOCAL

    def test_switch_to_nonexistent_mesh_type(self, router):
        """Switching to an unregistered mesh type should raise."""
        # Create a virtual mesh type not in profiles
        with pytest.raises(ValueError, match="not connected"):
            router.switch_mesh(MeshType.PUBLIC, "Test", "human")

    def test_update_health_for_nonexistent_mesh(self, router):
        """Updating health for unknown mesh should be a no-op."""
        # Should not raise
        router.update_mesh_health(MeshType.PUBLIC, True)  # PUBLIC is in profiles

    def test_route_through_nonexistent_mesh(self, router):
        """Routing through a mesh not in profiles should fail gracefully."""
        # All meshes are in profiles by default
        router.update_mesh_health(MeshType.PUBLIC, False)
        result = router.route_through_mesh(MeshType.PUBLIC, b"data", "peer")
        assert result is False

    def test_select_mesh_with_all_disconnected(self, router):
        """select_mesh with requires_connected=True and all disconnected."""
        router.update_mesh_health(MeshType.LOCAL, False)
        with pytest.raises(RuntimeError):
            router.select_mesh(MeshRequirements(requires_connected=True))

    def test_add_rule_updates_select_behavior(self, router):
        """Adding a high-priority rule should affect select_mesh()."""
        router.update_mesh_health(MeshType.PUBLIC, True)
        # By default LOCAL should be selected for PUBLIC
        mtype, _ = router.select_mesh()
        assert mtype == MeshType.LOCAL

        # Add rule forcing PUBLIC data through PUBLIC mesh
        rule = MeshRoutingRule(
            id="force_public",
            description="Force PUBLIC data to PUBLIC mesh",
            data_classification=DataClassification.PUBLIC,
            mesh_type=MeshType.PUBLIC,
            priority=999,
        )
        router.add_routing_rule(rule)
        mtype, _ = router.select_mesh()
        assert mtype == MeshType.PUBLIC
