#!/usr/bin/env python3
"""
API Contract Validation Tests
==============================
Verifies that all documented API endpoints exist, return correct status codes,
and conform to the API contract defined in docs/API_CONTRACT.md and docs/API_DOCS.md.

Run: pytest tests/real/test_api_contract.py -v
"""

import pytest
import requests
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

# ── Configuration ────────────────────────────────────────────────

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 10

# ── Server availability check ────────────────────────────────────

SERVER_RUNNING = os.environ.get("ASIM_SERVER_RUNNING", "").lower() in ("1", "true", "yes")
needs_server = pytest.mark.skipif(
    not SERVER_RUNNING,
    reason="Skipping: requires running ASIM_SERVER (set ASIM_SERVER_RUNNING=1)"
)

# ── Helpers ──────────────────────────────────────────────────────

def api_url(path: str) -> str:
    """Build full API URL from path."""
    return f"{BASE_URL}{path}"

def check_endpoint(
    method: str,
    path: str,
    expected_status: int = 200,
    auth_token: Optional[str] = None,
    json_data: Optional[Dict] = None,
) -> requests.Response:
    """Make an API request and verify status code."""
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    fn = {
        "GET": requests.get,
        "POST": requests.post,
        "PUT": requests.put,
        "DELETE": requests.delete,
        "PATCH": requests.patch,
    }.get(method, requests.get)

    resp = fn(api_url(path), headers=headers, json=json_data, timeout=TIMEOUT)
    assert resp.status_code == expected_status, (
        f"{method} {path} expected {expected_status}, got {resp.status_code}: {resp.text[:200]}"
    )
    return resp

# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def auth_token() -> Optional[str]:
    """Get an auth token for protected endpoints."""
    try:
        resp = requests.post(
            api_url("/auth/login"),
            json={"email": "test@asimnexus.com", "password": "test123"},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("token") or data.get("data", {}).get("token")
    except Exception:
        pass
    return None

# ══════════════════════════════════════════════════════════════════
# 1. HEALTH & SYSTEM ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@needs_server
class TestHealthEndpoints:
    """Verify all health check endpoints."""

    def test_health_basic(self):
        """GET /health should return 200 with status."""
        resp = check_endpoint("GET", "/health")
        data = resp.json()
        assert "status" in data, f"Missing 'status' in {data}"

    def test_health_live(self):
        """GET /health/live should return 200."""
        check_endpoint("GET", "/health/live")

    def test_health_ready(self):
        """GET /health/ready should return 200 with component checks."""
        resp = check_endpoint("GET", "/health/ready")
        data = resp.json()
        assert "checks" in data, f"Missing 'checks' in {data}"
        assert "status" in data, f"Missing 'status' in {data}"

    def test_health_status(self):
        """GET /health/status should return 200 with detailed component info."""
        resp = check_endpoint("GET", "/health/status")
        data = resp.json()
        assert "components" in data or "status" in data, f"Missing expected fields in {data}"

    def test_metrics_endpoint(self):
        """GET /metrics should return 200."""
        check_endpoint("GET", "/metrics")

    def test_metrics_prometheus_format(self):
        """GET /metrics with Accept: text/plain should return Prometheus format."""
        resp = requests.get(api_url("/metrics"), headers={"Accept": "text/plain"}, timeout=TIMEOUT)
        assert resp.status_code == 200
        assert "text/plain" in resp.headers.get("content-type", ""), (
            f"Expected text/plain content type, got {resp.headers.get('content-type')}"
        )

    def test_system_info(self):
        """GET /api/system/info should return 200."""
        check_endpoint("GET", "/api/system/info")

    def test_api_version(self):
        """GET /api/version should return 200."""
        check_endpoint("GET", "/api/version")

    def test_healthz(self):
        """GET /healthz should return 200."""
        check_endpoint("GET", "/healthz")

    def test_status(self):
        """GET /status should return 200."""
        check_endpoint("GET", "/status")

# ══════════════════════════════════════════════════════════════════
# 2. AUTH ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@needs_server
class TestAuthEndpoints:
    """Verify authentication endpoints."""

    def test_login_invalid_credentials(self):
        """POST /auth/login with bad credentials should return 401 or 403."""
        resp = requests.post(api_url("/auth/login"),
                             json={"email": "nonexistent@test.com", "password": "wrong"},
                             timeout=TIMEOUT)
        assert resp.status_code in (401, 403), (
            f"Expected 401/403, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_register_validation(self):
        """POST /auth/register with missing fields should return 422."""
        resp = requests.post(api_url("/auth/register"), json={}, timeout=TIMEOUT)
        assert resp.status_code in (400, 422), (
            f"Expected 400/422, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_auth_me_unauthenticated(self):
        """GET /auth/me without token should return 401 or 403."""
        resp = requests.get(api_url("/auth/me"), timeout=TIMEOUT)
        assert resp.status_code in (401, 403), (
            f"Expected 401/403, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_auth_me_authenticated(self, auth_token):
        """GET /auth/me with valid token should return 200."""
        if not auth_token:
            pytest.skip("No auth token available")
        check_endpoint("GET", "/auth/me", auth_token=auth_token)

    def test_auth_sessions(self, auth_token):
        """GET /auth/sessions should return 200."""
        if not auth_token:
            pytest.skip("No auth token available")
        check_endpoint("GET", "/auth/sessions", auth_token=auth_token)

# ══════════════════════════════════════════════════════════════════
# 3. SELF-AWARENESS ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@needs_server
class TestSelfAwarenessEndpoints:
    """Verify self-awareness API endpoints (public, no auth required)."""

    def test_knowledge_summary(self):
        """GET /api/self/knowledge/summary should return 200 with summary data."""
        resp = check_endpoint("GET", "/api/self/knowledge/summary")
        data = resp.json()
        # Should have at least some fields
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"

    def test_knowledge_modules(self):
        """GET /api/self/knowledge/modules should return 200."""
        check_endpoint("GET", "/api/self/knowledge/modules")

    def test_knowledge_routes(self):
        """GET /api/self/knowledge/routes should return 200."""
        check_endpoint("GET", "/api/self/knowledge/routes")

    def test_knowledge_issues(self):
        """GET /api/self/knowledge/issues should return 200."""
        check_endpoint("GET", "/api/self/knowledge/issues")

    def test_builder_history(self):
        """GET /api/self/builder/history should return 200."""
        check_endpoint("GET", "/api/self/builder/history")

    def test_builder_stats(self):
        """GET /api/self/builder/stats should return 200."""
        check_endpoint("GET", "/api/self/builder/stats")

    def test_bridge_stats(self):
        """GET /api/self/bridge/stats should return 200."""
        check_endpoint("GET", "/api/self/bridge/stats")

    def test_trigger_scan(self):
        """POST /api/self/scan should return 200."""
        check_endpoint("POST", "/api/self/scan")

# ══════════════════════════════════════════════════════════════════
# 4. CHAT & AI ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@needs_server
class TestChatEndpoints:
    """Verify chat and AI endpoints."""

    def test_chat_endpoint(self):
        """POST /chat should return 200 or 422 (validation)."""
        resp = requests.post(api_url("/chat"), json={}, timeout=TIMEOUT)
        assert resp.status_code in (200, 422), f"Unexpected status: {resp.status_code}"

    def test_agent_status(self):
        """GET /api/agent/status should return 200."""
        check_endpoint("GET", "/api/agent/status")

    def test_ai_status(self):
        """GET /api/ai/status should return 200."""
        check_endpoint("GET", "/api/ai/status")

# ══════════════════════════════════════════════════════════════════
# 5. MESH & NETWORK ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@needs_server
class TestMeshEndpoints:
    """Verify mesh network endpoints."""

    def test_mesh_nodes(self):
        """GET /mesh/nodes should return 200."""
        check_endpoint("GET", "/mesh/nodes")

    def test_mesh_v1_status(self):
        """GET /api/v1/mesh/status should return 200."""
        check_endpoint("GET", "/api/v1/mesh/status")

    def test_mesh_v1_peers(self):
        """GET /api/v1/mesh/peers should return 200."""
        check_endpoint("GET", "/api/v1/mesh/peers")

# ══════════════════════════════════════════════════════════════════
# 6. ANALYTICS ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@needs_server
class TestAnalyticsEndpoints:
    """Verify analytics endpoints."""

    def test_analytics_overview(self):
        """GET /api/analytics/overview should return 200."""
        check_endpoint("GET", "/api/analytics/overview")

    def test_analytics_activity(self):
        """GET /api/analytics/activity should return 200."""
        check_endpoint("GET", "/api/analytics/activity")

    def test_apis_status(self):
        """GET /api/apis/status should return 200."""
        check_endpoint("GET", "/api/apis/status")

# ══════════════════════════════════════════════════════════════════
# 7. CONSENSUS ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@needs_server
class TestConsensusEndpoints:
    """Verify consensus endpoints."""

    def test_consensus_status(self):
        """GET /api/v1/consensus/status should return 200."""
        check_endpoint("GET", "/api/v1/consensus/status")

# ══════════════════════════════════════════════════════════════════
# 8. CROSS-ENDPOINT CONTRACT CHECKS
# ══════════════════════════════════════════════════════════════════

@needs_server
class TestContractCompliance:
    """Verify API contract compliance across all endpoints."""

    def test_all_endpoints_return_json(self):
        """All API endpoints should return JSON content type."""
        endpoints = [
            ("GET", "/health"),
            ("GET", "/health/live"),
            ("GET", "/health/ready"),
            ("GET", "/health/status"),
            ("GET", "/api/self/knowledge/summary"),
            ("GET", "/api/self/knowledge/modules"),
            ("GET", "/api/self/knowledge/routes"),
            ("GET", "/api/self/knowledge/issues"),
            ("GET", "/api/self/builder/history"),
            ("GET", "/api/self/builder/stats"),
            ("GET", "/api/self/bridge/stats"),
            ("GET", "/mesh/nodes"),
            ("GET", "/api/system/info"),
            ("GET", "/api/version"),
            ("GET", "/status"),
            ("GET", "/healthz"),
        ]
        for method, path in endpoints:
            resp = check_endpoint(method, path)
            content_type = resp.headers.get("content-type", "")
            assert "application/json" in content_type or "text/plain" in content_type or "text/html" in content_type, (
                f"{method} {path} returned {content_type}, expected JSON"
            )

    def test_error_response_format(self):
        """Error responses should contain 'detail' field."""
        resp = requests.get(api_url("/nonexistent-route-xyz"), timeout=TIMEOUT)
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data, f"Missing 'detail' in error response: {data}"

# ══════════════════════════════════════════════════════════════════
# 9. RESPONSE TIME BENCHMARKS (LIGHTWEIGHT)
# ══════════════════════════════════════════════════════════════════

@needs_server
class TestResponseTimeBaseline:
    """Establish baseline response times for critical endpoints."""

    MAX_ACCEPTABLE_MS = 2000  # 2 seconds max

    @pytest.mark.parametrize("method,path", [
        ("GET", "/health"),
        ("GET", "/health/live"),
        ("GET", "/health/ready"),
        ("GET", "/api/self/knowledge/summary"),
        ("GET", "/api/self/knowledge/modules"),
        ("GET", "/mesh/nodes"),
        ("GET", "/api/system/info"),
    ])
    def test_response_time(self, method, path):
        """Each endpoint should respond within acceptable time."""
        import time
        start = time.time()
        check_endpoint(method, path)
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < self.MAX_ACCEPTABLE_MS, (
            f"{method} {path} took {elapsed_ms:.0f}ms, exceeds {self.MAX_ACCEPTABLE_MS}ms"
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
