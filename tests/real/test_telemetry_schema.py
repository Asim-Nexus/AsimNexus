#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade telemetry schema tests
ASIMNEXUS Telemetry Schema Tests
=================================
Tests for validate_event, normalize_event, and event_to_json.
"""

import json
import pytest
from core.telemetry_schema import (
    validate_event, normalize_event, event_to_json,
    VALID_COMPONENTS, VALID_ACTIONS, VALID_SEVERITIES,
    VALID_STATUSES, VALID_POSTURES, VALID_PRIVACY_LEVELS, VALID_MODES,
)


class TestNormalizeEvent:
    """Tests for the normalize_event function."""

    def test_normalize_fills_all_defaults(self):
        """normalize_event fills all fields with defaults for empty input."""
        result = normalize_event({})
        assert result["event_id"] is not None
        assert result["timestamp"] is not None
        assert result["trace_id"] is not None
        assert result["span_id"] is not None
        assert result["component"] == "backend"
        assert result["action"] == "request"
        assert result["severity"] == "info"
        assert result["status"] == "ok"
        assert result["latency_ms"] == 0.0
        assert result["privacy_level"] == "public"
        assert result["mode"] == "personal"
        assert result["message"] == ""

    def test_normalize_preserves_provided_values(self):
        """normalize_event preserves explicitly provided values."""
        raw = {
            "component": "core",
            "action": "tool_call",
            "severity": "warning",
            "status": "degraded",
            "latency_ms": 150.5,
            "message": "High latency detected",
        }
        result = normalize_event(raw)
        assert result["component"] == "core"
        assert result["action"] == "tool_call"
        assert result["severity"] == "warning"
        assert result["status"] == "degraded"
        assert result["latency_ms"] == 150.5
        assert result["message"] == "High latency detected"

    def test_normalize_resource_defaults(self):
        """normalize_event fills resource sub-dict with defaults."""
        result = normalize_event({})
        assert result["resource"]["cpu_pct"] == 0.0
        assert result["resource"]["memory_mb"] == 0.0
        assert result["resource"]["disk_mb"] == 0.0
        assert result["resource"]["network_kbps"] == 0.0

    def test_normalize_policy_defaults(self):
        """normalize_event fills policy sub-dict with defaults."""
        result = normalize_event({})
        assert result["policy"]["rule_id"] is None
        assert result["policy"]["decision"] is None
        assert result["policy"]["reason"] is None

    def test_normalize_tool_defaults(self):
        """normalize_event fills tool sub-dict with defaults."""
        result = normalize_event({})
        assert result["tool"]["name"] is None
        assert result["tool"]["selected_model"] is None
        assert result["tool"]["route"] is None

    def test_normalize_audit_and_mesh_refs(self):
        """normalize_event preserves audit_ref and mesh_ref."""
        raw = {"audit_ref": "aud-001", "mesh_ref": "mesh-001"}
        result = normalize_event(raw)
        assert result["audit_ref"] == "aud-001"
        assert result["mesh_ref"] == "mesh-001"


class TestValidateEvent:
    """Tests for the validate_event function."""

    def test_validate_valid_minimal(self):
        """validate_event accepts a valid minimal event."""
        result = validate_event({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "test",
        })
        assert result["component"] == "backend"

    def test_validate_all_valid_components(self):
        """validate_event accepts all valid components."""
        for comp in VALID_COMPONENTS:
            result = validate_event({
                "component": comp,
                "action": "request",
                "severity": "info",
                "status": "ok",
                "message": "test",
            })
            assert result["component"] == comp

    def test_validate_all_valid_actions(self):
        """validate_event accepts all valid actions."""
        for action in VALID_ACTIONS:
            result = validate_event({
                "component": "backend",
                "action": action,
                "severity": "info",
                "status": "ok",
                "message": "test",
            })
            assert result["action"] == action

    def test_validate_all_valid_severities(self):
        """validate_event accepts all valid severities."""
        for sev in VALID_SEVERITIES:
            result = validate_event({
                "component": "backend",
                "action": "request",
                "severity": sev,
                "status": "ok",
                "message": "test",
            })
            assert result["severity"] == sev

    def test_validate_all_valid_statuses(self):
        """validate_event accepts all valid statuses."""
        for status in VALID_STATUSES:
            result = validate_event({
                "component": "backend",
                "action": "request",
                "severity": "info",
                "status": status,
                "message": "test",
            })
            assert result["status"] == status

    def test_validate_all_valid_postures(self):
        """validate_event accepts all valid trust postures."""
        for posture in VALID_POSTURES:
            result = validate_event({
                "component": "backend",
                "action": "request",
                "severity": "info",
                "status": "ok",
                "trust_posture": posture,
                "message": "test",
            })
            assert result["trust_posture"] == posture

    def test_validate_all_valid_privacy_levels(self):
        """validate_event accepts all valid privacy levels."""
        for priv in VALID_PRIVACY_LEVELS:
            result = validate_event({
                "component": "backend",
                "action": "request",
                "severity": "info",
                "status": "ok",
                "privacy_level": priv,
                "message": "test",
            })
            assert result["privacy_level"] == priv

    def test_validate_all_valid_modes(self):
        """validate_event accepts all valid modes."""
        for mode in VALID_MODES:
            result = validate_event({
                "component": "backend",
                "action": "request",
                "severity": "info",
                "status": "ok",
                "mode": mode,
                "message": "test",
            })
            assert result["mode"] == mode

    def test_validate_invalid_component(self):
        """validate_event raises ValueError for invalid component."""
        with pytest.raises(ValueError, match="Invalid component"):
            validate_event({
                "component": "invalid_comp",
                "action": "request",
                "severity": "info",
                "status": "ok",
            })

    def test_validate_invalid_action(self):
        """validate_event raises ValueError for invalid action."""
        with pytest.raises(ValueError, match="Invalid action"):
            validate_event({
                "component": "backend",
                "action": "invalid_action",
                "severity": "info",
                "status": "ok",
            })

    def test_validate_invalid_severity(self):
        """validate_event raises ValueError for invalid severity."""
        with pytest.raises(ValueError, match="Invalid severity"):
            validate_event({
                "component": "backend",
                "action": "request",
                "severity": "catastrophic",
                "status": "ok",
            })

    def test_validate_invalid_status(self):
        """validate_event raises ValueError for invalid status."""
        with pytest.raises(ValueError, match="Invalid status"):
            validate_event({
                "component": "backend",
                "action": "request",
                "severity": "info",
                "status": "unknown",
            })

    def test_validate_invalid_trust_posture(self):
        """validate_event raises ValueError for invalid trust_posture."""
        with pytest.raises(ValueError, match="Invalid trust_posture"):
            validate_event({
                "component": "backend",
                "action": "request",
                "severity": "info",
                "status": "ok",
                "trust_posture": "super_trusted",
            })

    def test_validate_invalid_privacy_level(self):
        """validate_event raises ValueError for invalid privacy_level."""
        with pytest.raises(ValueError, match="Invalid privacy_level"):
            validate_event({
                "component": "backend",
                "action": "request",
                "severity": "info",
                "status": "ok",
                "privacy_level": "secret",
            })

    def test_validate_invalid_mode(self):
        """validate_event raises ValueError for invalid mode."""
        with pytest.raises(ValueError, match="Invalid mode"):
            validate_event({
                "component": "backend",
                "action": "request",
                "severity": "info",
                "status": "ok",
                "mode": "secret_society",
            })

    def test_validate_assigns_event_id(self):
        """validate_event assigns event_id if not provided."""
        result = validate_event({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "test",
        })
        assert "event_id" in result
        assert len(result["event_id"]) > 0


class TestEventToJson:
    """Tests for the event_to_json function."""

    def test_event_to_json_valid(self):
        """event_to_json returns valid JSON for a valid event."""
        result = event_to_json({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": "test",
        })
        parsed = json.loads(result)
        assert parsed["component"] == "backend"
        assert parsed["action"] == "request"

    def test_event_to_json_invalid(self):
        """event_to_json raises ValueError for an invalid event."""
        with pytest.raises(ValueError, match="Invalid component"):
            event_to_json({
                "component": "nonexistent",
                "action": "request",
                "severity": "info",
                "status": "ok",
            })


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
