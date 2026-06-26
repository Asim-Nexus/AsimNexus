"""
Phase 3: Monitoring & Security Tests
"""
import pytest
from fastapi.testclient import TestClient


def test_monitoring_middleware_exists():
    """Monitoring middleware module exists and has required class."""
    from core.monitoring_middleware import PrometheusMonitoringMiddleware
    assert PrometheusMonitoringMiddleware is not None


def test_security_headers_middleware_exists():
    """Security headers middleware module exists and has required class."""
    from core.security_headers_middleware import SecurityHeadersMiddleware
    assert SecurityHeadersMiddleware is not None


def test_metrics_endpoint():
    """Metrics endpoint returns valid structure."""
    from app import app
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "status" in response.json()


def test_security_headers_present():
    """Security headers are present in responses."""
    from app import app
    client = TestClient(app)
    response = client.get("/health")
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" in response.headers


def test_vapt_status_endpoint():
    """VAPT status endpoint returns security check results."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/compliance/vapt-status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "data" in data
    assert "checks" in data.get("data", {})


def test_disaster_recovery_backup():
    """Disaster recovery backup endpoint works."""
    from app import app
    client = TestClient(app)
    response = client.post("/api/disaster-recovery/backup")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_disaster_recovery_list_backups():
    """List backups endpoint works."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/disaster-recovery/backups")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data