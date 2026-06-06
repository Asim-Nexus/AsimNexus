#!/usr/bin/env python3
"""
Tests for [`core/mesh/air_gap_controller.py`](../../core/mesh/air_gap_controller.py)
— Phase 9: hardened Air Gap Controller with real network filtering.

Covers:
  - 5-level state machine transitions (NORMAL→REDUCED→LAN_ONLY→ISOLATED→EMERGENCY)
  - engage / disengage semantics
  - escalate (auto step-up)
  - network blocking fallback (mocked firewall)
  - get_connection_count parsing
  - is_network_blocked check
  - audit logging
  - traffic rule enforcement
  - singleton factory pattern
"""

import os
import sys
import json
import time
import pytest
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
from pathlib import Path

# Ensure the module path is available
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.mesh.air_gap_controller import (
    AirGapLevel,
    AirGapEvent,
    AirGapController,
    get_air_gap,
    reset_air_gap,
    LEVEL_LABELS,
    LEVEL_RULES,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_system():
    """Reset singleton and clear state before each test."""
    reset_air_gap()
    yield
    reset_air_gap()


@pytest.fixture
def controller():
    """Fresh AirGapController instance with firewall detection mocked."""
    with patch.object(AirGapController, '_check_firewall_available', return_value=False):
        ctrl = AirGapController()
        yield ctrl


# ══════════════════════════════════════════════════════════════════════════════
# Test: AirGapLevel Enum
# ══════════════════════════════════════════════════════════════════════════════

class TestAirGapLevel:
    """Five air-gap levels exist with correct ordering."""

    def test_level_values(self):
        assert AirGapLevel.NORMAL == 0
        assert AirGapLevel.REDUCED == 1
        assert AirGapLevel.LAN_ONLY == 2
        assert AirGapLevel.ISOLATED == 3
        assert AirGapLevel.EMERGENCY == 4

    def test_level_ordering(self):
        assert AirGapLevel.NORMAL < AirGapLevel.REDUCED
        assert AirGapLevel.REDUCED < AirGapLevel.LAN_ONLY
        assert AirGapLevel.LAN_ONLY < AirGapLevel.ISOLATED
        assert AirGapLevel.ISOLATED < AirGapLevel.EMERGENCY

    def test_level_labels(self):
        assert "Normal" in LEVEL_LABELS[AirGapLevel.NORMAL]
        assert "Reduced" in LEVEL_LABELS[AirGapLevel.REDUCED]
        assert "LAN" in LEVEL_LABELS[AirGapLevel.LAN_ONLY]
        assert "Isolated" in LEVEL_LABELS[AirGapLevel.ISOLATED]
        assert "Emergency" in LEVEL_LABELS[AirGapLevel.EMERGENCY]


# ══════════════════════════════════════════════════════════════════════════════
# Test: State Machine Transitions
# ══════════════════════════════════════════════════════════════════════════════

class TestStateTransitions:
    """Full state machine progression through all 5 levels."""

    def test_initial_state_normal(self, controller):
        """Controller starts at NORMAL."""
        status = controller.status()
        assert status["level"] == 0
        assert status["engaged"] is False
        assert status["label"] == "🟢 Normal"

    def test_normal_to_reduced(self, controller):
        """NORMAL → REDUCED transition."""
        result = controller.engage(AirGapLevel.REDUCED, reason="Test", triggered_by="human")
        assert result["status"] == "engaged"
        assert result["level"] == 1
        assert controller._level == AirGapLevel.REDUCED

    def test_reduced_to_lan_only(self, controller):
        """REDUCED → LAN_ONLY transition."""
        controller.engage(AirGapLevel.REDUCED, reason="Step 1", triggered_by="human")
        result = controller.engage(AirGapLevel.LAN_ONLY, reason="Step 2", triggered_by="human")
        assert result["status"] == "engaged"
        assert result["level"] == 2

    def test_lan_only_to_isolated(self, controller):
        """LAN_ONLY → ISOLATED transition."""
        controller.engage(AirGapLevel.LAN_ONLY, reason="Step", triggered_by="human")
        result = controller.engage(AirGapLevel.ISOLATED, reason="Going dark", triggered_by="human")
        assert result["status"] == "engaged"
        assert result["level"] == 3

    def test_isolated_to_emergency(self, controller):
        """ISOLATED → EMERGENCY transition."""
        controller.engage(AirGapLevel.ISOLATED, reason="Threat", triggered_by="human")
        result = controller.engage(AirGapLevel.EMERGENCY, reason="Max threat", triggered_by="human")
        assert result["status"] == "engaged"
        assert result["level"] == 4

    def test_full_progression(self, controller):
        """Complete NORMAL→REDUCED→LAN_ONLY→ISOLATED→EMERGENCY progression."""
        levels = [AirGapLevel.REDUCED, AirGapLevel.LAN_ONLY,
                  AirGapLevel.ISOLATED, AirGapLevel.EMERGENCY]
        for lvl in levels:
            result = controller.engage(lvl, reason=f"Step {lvl}", triggered_by="human")
            assert result["status"] == "engaged"
            assert result["level"] == lvl

        # Final state should be EMERGENCY
        assert controller._level == AirGapLevel.EMERGENCY


# ══════════════════════════════════════════════════════════════════════════════
# Test: Engage / Disengage
# ══════════════════════════════════════════════════════════════════════════════

class TestEngageDisengage:
    """Engage and disengage semantics."""

    def test_engage_at_level(self, controller):
        """Engage at ISOLATED level."""
        result = controller.engage(AirGapLevel.ISOLATED, reason="Security breach")
        assert result["status"] == "engaged"
        assert result["level"] == 3
        assert controller.is_allowed("cloud") is False
        assert controller.is_allowed("lan") is False
        assert controller.is_allowed("loopback") is True

    def test_disengage_by_human(self, controller):
        """Human can disengage."""
        controller.engage(AirGapLevel.ISOLATED, reason="Test", triggered_by="human")
        result = controller.disengage(triggered_by="human")
        assert result["status"] == "normal"
        assert controller._level == AirGapLevel.NORMAL

    def test_disengage_refused_non_human(self, controller):
        """Machine/AI cannot disengage — only human."""
        controller.engage(AirGapLevel.ISOLATED, reason="Test", triggered_by="human")
        result = controller.disengage(triggered_by="auto_dharma")
        assert result["status"] == "refused"
        assert "only be disengaged by human" in result["detail"]

    def test_escalate(self, controller):
        """escalate() steps up one level."""
        result = controller.escalate(reason="Auto-escalation", triggered_by="auto_dharma")
        assert result["level"] == 1  # NORMAL → REDUCED

        result = controller.escalate()
        assert result["level"] == 2  # REDUCED → LAN_ONLY

        result = controller.escalate()
        assert result["level"] == 3  # LAN_ONLY → ISOLATED

        result = controller.escalate()
        assert result["level"] == 4  # ISOLATED → EMERGENCY

        # Can't escalate past EMERGENCY
        result = controller.escalate()
        assert result["level"] == 4

    def test_no_downgrade_on_re_engage(self, controller):
        """Engaging at lower level when already at higher does nothing."""
        controller.engage(AirGapLevel.ISOLATED, reason="High", triggered_by="human")
        # Try to engage at REDUCED (lower) — should be no-op
        result = controller.engage(AirGapLevel.REDUCED, reason="Lower", triggered_by="human")
        assert result["level"] == 3  # stays at ISOLATED


# ══════════════════════════════════════════════════════════════════════════════
# Test: Traffic Rule Enforcement
# ══════════════════════════════════════════════════════════════════════════════

class TestTrafficRules:
    """Traffic permission checks per air-gap level."""

    def test_normal_allows_all(self, controller):
        assert controller.is_allowed("cloud") is True
        assert controller.is_allowed("lan") is True
        assert controller.is_allowed("loopback") is True
        assert controller.is_allowed("outbound") is True

    def test_reduced_blocks_cloud(self, controller):
        controller.engage(AirGapLevel.REDUCED, triggered_by="human")
        assert controller.is_allowed("cloud") is False
        assert controller.is_allowed("lan") is True
        assert controller.is_allowed("loopback") is True

    def test_isolated_blocks_all_but_loopback(self, controller):
        controller.engage(AirGapLevel.ISOLATED, triggered_by="human")
        assert controller.is_allowed("cloud") is False
        assert controller.is_allowed("lan") is False
        assert controller.is_allowed("loopback") is True
        assert controller.is_allowed("outbound") is False

    def test_emergency_blocks_everything(self, controller):
        controller.engage(AirGapLevel.EMERGENCY, triggered_by="human")
        assert controller.is_allowed("cloud") is False
        assert controller.is_allowed("lan") is False
        assert controller.is_allowed("loopback") is False
        assert controller.is_allowed("outbound") is False

    def test_check_request_loopback(self, controller):
        controller.engage(AirGapLevel.ISOLATED, triggered_by="human")
        result = controller.check_request("127.0.0.1", 8080)
        assert result["allowed"] is True
        assert "Loopback" in result["reason"]

    def test_check_request_cloud_blocked(self, controller):
        controller.engage(AirGapLevel.REDUCED, triggered_by="human")
        result = controller.check_request("8.8.8.8", 443)
        assert result["allowed"] is False
        assert "Blocked" in result["reason"]


# ══════════════════════════════════════════════════════════════════════════════
# Test: Network Blocking (Mocked)
# ══════════════════════════════════════════════════════════════════════════════

class TestNetworkBlocking:
    """Network enforcement with firewall fallback."""

    def test_block_network_simulated(self, controller):
        """Block network with simulated fallback."""
        success, msg = controller._block_network("10.0.0.1", 443)
        assert success is True
        assert "Simulated" in msg
        assert controller.is_network_blocked("10.0.0.1", 443) is True

    def test_unblock_network(self, controller):
        """Remove a block."""
        controller._block_network("10.0.0.1", 443)
        success, msg = controller._unblock_network("10.0.0.1", 443)
        assert success is True
        assert "removed" in msg
        assert controller.is_network_blocked("10.0.0.1", 443) is False

    def test_is_network_blocked_no_args(self, controller):
        """is_network_blocked with no args returns True if any blocks exist."""
        assert controller.is_network_blocked() is False
        controller._block_network("10.0.0.1", 443)
        assert controller.is_network_blocked() is True

    def test_get_blocked_rules(self, controller):
        """get_blocked_rules returns all active rules."""
        controller._block_network("10.0.0.1", 443)
        controller._block_network("10.0.0.2", 80)
        rules = controller.get_blocked_rules()
        assert len(rules) == 2
        assert "10.0.0.1:443" in rules


# ══════════════════════════════════════════════════════════════════════════════
# Test: get_connection_count
# ══════════════════════════════════════════════════════════════════════════════

class TestConnectionCount:
    """Connection counting via netstat parsing."""

    @patch("core.mesh.air_gap_controller.subprocess.run")
    def test_get_connection_count_parsing(self, mock_run, controller):
        """Parse netstat output correctly."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            "  TCP    192.168.1.1:54321    10.0.0.1:443       ESTABLISHED\n"
            "  TCP    192.168.1.1:54322    10.0.0.2:80        TIME_WAIT\n"
            "  TCP    192.168.1.1:54323    10.0.0.3:443       ESTABLISHED\n"
        )
        mock_run.return_value.stderr = ""

        count = controller.get_connection_count()
        assert count == 2  # Only ESTABLISHED connections

    @patch("core.mesh.air_gap_controller.subprocess.run")
    def test_get_connection_count_command(self, mock_run, controller):
        """Verify the netstat command is constructed correctly."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        controller.get_connection_count()

        # Verify subprocess.run was called
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "netstat" in call_args

    @patch("core.mesh.air_gap_controller.subprocess.run")
    def test_get_connection_count_error(self, mock_run, controller):
        """Return -1 on netstat failure."""
        mock_run.side_effect = FileNotFoundError("netstat not found")
        count = controller.get_connection_count()
        assert count == -1


# ══════════════════════════════════════════════════════════════════════════════
# Test: Audit Logging
# ══════════════════════════════════════════════════════════════════════════════

class TestAuditLogging:
    """Persistent audit logging of state transitions."""

    def test_audit_log_created_on_engage(self, controller):
        """Engage creates an audit log entry."""
        controller.engage(AirGapLevel.ISOLATED, reason="Test", triggered_by="human")
        audit = controller.get_audit_trail()
        assert len(audit) >= 1
        entry = audit[-1]
        assert entry["level_to"] == 3
        assert entry["reason"] == "Test"
        assert entry["triggered_by"] == "human"

    def test_audit_log_disengage(self, controller):
        """Disengage creates an audit log entry."""
        controller.engage(AirGapLevel.ISOLATED, reason="Test", triggered_by="human")
        controller.disengage(triggered_by="human")
        audit = controller.get_audit_trail()
        # Should have at least 2 entries (engage + disengage)
        assert len(audit) >= 2
        disengage_entry = audit[-1]
        assert disengage_entry["level_to"] == 0
        assert disengage_entry["level_from"] == 3

    def test_audit_log_escalate(self, controller):
        """Escalate creates audit log entries."""
        controller.escalate(reason="Auto", triggered_by="auto_dharma")
        audit = controller.get_audit_trail()
        assert len(audit) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Test: Singleton Factory
# ══════════════════════════════════════════════════════════════════════════════

class TestSingleton:
    """Singleton factory pattern."""

    def test_get_air_gap_returns_same_instance(self):
        """get_air_gap() returns the same instance."""
        reset_air_gap()
        c1 = get_air_gap()
        c2 = get_air_gap()
        assert c1 is c2

    def test_reset_air_gap_creates_new_instance(self):
        """reset_air_gap() creates a fresh instance."""
        reset_air_gap()
        c1 = get_air_gap()
        reset_air_gap()
        c2 = get_air_gap()
        assert c1 is not c2


# ══════════════════════════════════════════════════════════════════════════════
# Test: History & Status
# ══════════════════════════════════════════════════════════════════════════════

class TestHistory:
    """Event history tracking."""

    def test_history_records_events(self, controller):
        """History contains all state transitions."""
        controller.engage(AirGapLevel.REDUCED, reason="Step 1", triggered_by="human")
        controller.engage(AirGapLevel.LAN_ONLY, reason="Step 2", triggered_by="human")
        hist = controller.history()
        assert len(hist) == 2
        assert hist[0]["level_to"] == 1
        assert hist[1]["level_to"] == 2

    def test_status_after_engage(self, controller):
        """Status reflects engaged state."""
        controller.engage(AirGapLevel.ISOLATED, reason="Test", triggered_by="human")
        status = controller.status()
        assert status["engaged"] is True
        assert status["level"] == 3
        assert status["engaged_for_s"] >= 0
        assert "blocked_rules" in status
        assert "active_connections" in status
        assert "firewall_available" in status
