#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade observability route tests
ASIMNEXUS Observability Route Tests
=====================================
Tests all 8 observability API endpoints via FastAPI TestClient.
Verifies route registration, response format, and error handling.
"""

import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(scope="module")
def client():
    """Build a TestClient from simple_backend's create_app factory."""
    from starlette.testclient import TestClient
    import sys
    backend_dir = Path(__file__).resolve().parents[2] / "backend"
    if str(backend_dir.parent) not in sys.path:
        sys.path.insert(0, str(backend_dir.parent))

    from simple_backend import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestTelemetryEndpoint:
    """GET /api/observability/telemetry — buffered telemetry events."""

    def test_telemetry_returns_list(self, client):
        resp = client.get("/api/observability/telemetry")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_telemetry_with_limit(self, client):
        resp = client.get("/api/observability/telemetry?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestPostureEndpoint:
    """GET /api/observability/posture — trust posture assessment."""

    def test_posture_returns_dict(self, client):
        resp = client.get("/api/observability/posture")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert "score" in data
        assert "level" in data
        assert "metrics" in data
        assert "reason" in data


class TestMetricsEndpoint:
    """GET /api/observability/metrics — aggregated metrics."""

    def test_metrics_returns_expected_fields(self, client):
        resp = client.get("/api/observability/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "error_rate" in data
        assert "average_latency_ms" in data
        assert "total_events_buffered" in data
        assert isinstance(data["total_requests"], int)
        assert isinstance(data["error_rate"], float)
        assert isinstance(data["average_latency_ms"], float)

    def test_metrics_zero_state(self, client):
        """Metrics returns sensible zero-state values."""
        resp = client.get("/api/observability/metrics")
        data = resp.json()
        assert data["total_requests"] >= 0
        assert 0.0 <= data["error_rate"] <= 1.0


class TestTracesEndpoint:
    """GET /api/observability/traces — trace events."""

    def test_traces_returns_list(self, client):
        resp = client.get("/api/observability/traces")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_traces_with_trace_id(self, client):
        resp = client.get("/api/observability/traces?trace_id=nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestAuditEndpoint:
    """GET /api/observability/audit — audit trail records."""

    def test_audit_returns_list(self, client):
        resp = client.get("/api/observability/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_audit_with_limit(self, client):
        resp = client.get("/api/observability/audit?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_audit_with_cursor(self, client):
        resp = client.get("/api/observability/audit?cursor=nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestEventEndpoint:
    """POST /api/observability/event — record a new event."""

    def test_post_event_valid(self, client):
        resp = client.post("/api/observability/event", json={
            "component": "backend",
            "action": "request",
            "severity": "info",
            "message": "Test event via API",
            "latency_ms": 10.0,
            "status": "ok",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "recorded"
        assert "event" in data

    def test_post_event_invalid_component(self, client):
        resp = client.post("/api/observability/event", json={
            "component": "nonexistent",
            "action": "request",
            "severity": "info",
            "message": "Invalid",
        })
        # Should return 422 from Pydantic validation or 500 from internal error
        assert resp.status_code in (422, 500)


class TestHealthEndpoint:
    """GET /api/observability/health — health check."""

    def test_health_returns_healthy(self, client):
        resp = client.get("/api/observability/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["subsystem"] == "observability"


class TestStatusEndpoint:
    """GET /api/observability/status — full observability status."""

    def test_status_returns_expected_fields(self, client):
        resp = client.get("/api/observability/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_mode" in data
        assert "policy_score" in data
        assert "audit_bus" in data
        assert "buffered_events_count" in data
        assert isinstance(data["policy_score"], float)
        assert isinstance(data["buffered_events_count"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
