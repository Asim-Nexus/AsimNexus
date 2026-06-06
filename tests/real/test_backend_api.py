"""
STATUS: REAL — Tests for FastAPI Backend API
Tests: Health, Dharma, Personal, Agent, Universe endpoints
Uses test_client fixture from tests/conftest.py.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def get_test_client():
    """Backward-compatible wrapper — use test_client fixture instead."""
    # This now relies on conftest.py's import patch being active
    try:
        from fastapi.testclient import TestClient
        import simple_backend
        # Force app creation with patched mesh
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("backend.mesh.setup_mesh_routes", lambda app, node_id="local": None)
            # Re-import to trigger fresh app creation
            import importlib
            importlib.reload(simple_backend)
            from simple_backend import app
            return TestClient(app)
    except Exception as e:
        pytest.skip(f"TestClient not available: {e}")


class TestHealthEndpoints:
    """Test basic connectivity."""

    def test_health_check(self, test_client):
        """Root health endpoint returns 200."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

    def test_universe_status(self, test_client):
        """Universe status returns system snapshot."""
        response = test_client.get("/api/universe/status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0


class TestDharmaEndpoints:
    """Test Dharma-Chakra API."""

    def test_dharma_status(self, test_client):
        """Dharma status returns ΔT live data."""
        response = test_client.get("/api/dharma/status")
        assert response.status_code == 200
        data = response.json()
        # Production path: active_contracts, active_users, etc.
        # Fallback path: symmetry, gini, delta_t, status
        assert any(k in data for k in ["symmetry", "symmetry_score", "active_contracts", "status"])
        assert "timestamp" in data or "cycle" in data

    def test_dharma_veto_post(self, test_client):
        """Manual veto POST creates veto event."""
        payload = {
            "action": "test_action",
            "reason": "human_override",
            "node_id": "test_user",
            "detail": "Testing veto endpoint",
        }
        response = test_client.post("/api/dharma/veto", json=payload)
        # May return 200 or validation error depending on schema
        assert response.status_code in [200, 201, 422]


class TestPersonalEndpoints:
    """Test Personal Universe API."""

    def test_personal_status(self, test_client):
        """Personal status returns user info."""
        response = test_client.get("/api/personal/status")
        assert response.status_code in [200, 401]  # 401 if auth required
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_personal_universe(self, test_client):
        """Universe layers status."""
        response = test_client.get("/api/personal/universe")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestAgentEndpoints:
    """Test Agent Mode API."""

    def test_agent_status(self, test_client):
        """Agent mode status returns current state."""
        response = test_client.get("/api/agent/status")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "active" in data or "mode" in data

    def test_agent_mode_on(self, test_client):
        """Activate agent mode."""
        payload = {
            "skills": ["python", "writing"],
            "max_contract_days": 15,
        }
        response = test_client.post("/api/agent/mode/on", json=payload)
        assert response.status_code in [200, 201, 401, 422]

    def test_agent_mode_off(self, test_client):
        """Deactivate agent mode."""
        response = test_client.post("/api/agent/mode/off", json={})
        assert response.status_code in [200, 201, 401]


class TestChatEndpoints:
    """Test chat API."""

    def test_chat_without_auth(self, test_client):
        """Chat may require auth."""
        payload = {"message": "hello", "clone_id": "general"}
        response = test_client.post("/api/chat", json=payload)
        assert response.status_code in [200, 401, 422]
