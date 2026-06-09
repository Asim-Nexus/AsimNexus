#!/usr/bin/env python3
"""
ASIMNEXUS Global Agent Mode API Tests
=======================================
Tests for all global agent endpoints: activation, region management,
agent registration, deployment, status, and overview.
"""

import sys
import os
import json
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from fastapi import FastAPI

# Need to reset module-level singletons between tests
from core.api_endpoints import global_agent_api


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_global_agent():
    """Reset the singleton between tests."""
    global_agent_api.reset_global_agent()
    yield
    global_agent_api.reset_global_agent()


@pytest.fixture
def client():
    """Create test client with real GlobalAgentMode (no mocking needed)."""
    app = FastAPI()
    from core.api_endpoints.global_agent_api import router
    app.include_router(router)
    return TestClient(app)


# ─── Activation/Deactivation Tests ───────────────────────────────────────────


class TestGlobalAgentActivation:
    """Tests for global agent mode activation and deactivation."""

    def test_activate_global_mode_default(self, client):
        """POST /api/global/activate activates with default config."""
        response = client.post("/api/global/activate", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "activated"
        assert data["government_share"] == 0.51
        assert data["private_share"] == 0.49
        assert data["personal_os"] is True

    def test_activate_global_mode_custom(self, client):
        """POST /api/global/activate with custom config."""
        response = client.post("/api/global/activate", json={
            "config": {
                "mode": "government",
                "government_share": 0.75,
                "private_share": 0.25,
                "max_agents": 500,
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "activated"
        assert data["government_share"] == 0.75

    def test_deactivate_global_mode(self, client):
        """POST /api/global/deactivate deactivates."""
        # Activate first
        client.post("/api/global/activate", json={})
        # Then deactivate
        response = client.post("/api/global/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deactivated"

    def test_deactivate_when_not_active(self, client):
        """Deactivating when not active still returns success."""
        response = client.post("/api/global/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deactivated"


# ─── Region Management Tests ─────────────────────────────────────────────────


class TestGlobalRegionManagement:
    """Tests for region registration and deployment."""

    def test_register_region_success(self, client):
        """POST /api/global/regions registers a new region."""
        response = client.post("/api/global/regions", json={
            "region_id": "us_east",
            "name": "US East Coast",
            "endpoint": "https://us-east.asimnexus.io",
            "region_type": "auto",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "registered"
        assert data["region_id"] == "us_east"

    def test_register_region_duplicate(self, client):
        """Registering the same region twice returns error."""
        client.post("/api/global/regions", json={
            "region_id": "us_east",
            "name": "US East",
            "endpoint": "https://us-east.asimnexus.io",
        })
        response = client.post("/api/global/regions", json={
            "region_id": "us_east",
            "name": "US East Again",
            "endpoint": "https://us-east.asimnexus.io",
        })
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_register_multiple_regions(self, client):
        """Register multiple regions successfully."""
        regions = [
            ("us_east", "US East", "https://us-east.asimnexus.io"),
            ("eu_west", "EU West", "https://eu-west.asimnexus.io"),
            ("ap_south", "Asia South", "https://ap-south.asimnexus.io"),
        ]
        for rid, name, endpoint in regions:
            response = client.post("/api/global/regions", json={
                "region_id": rid, "name": name, "endpoint": endpoint,
            })
            assert response.status_code == 200
            assert response.json()["status"] == "registered"

    def test_deploy_to_region(self, client):
        """POST /api/global/regions/{id}/deploy deploys to a region."""
        # Register first
        client.post("/api/global/regions", json={
            "region_id": "us_east", "name": "US East",
            "endpoint": "https://us-east.asimnexus.io",
        })
        # Then deploy
        response = client.post("/api/global/regions/us_east/deploy", json={
            "config": {"replicas": 3, "instance_type": "t3.medium"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deployed"
        assert data["region_id"] == "us_east"

    def test_deploy_to_unregistered_region(self, client):
        """Deploying to unregistered region returns error."""
        response = client.post("/api/global/regions/nonexistent/deploy", json={})
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


# ─── Agent Registration Tests ────────────────────────────────────────────────


class TestGlobalAgentRegistration:
    """Tests for global agent registration."""

    def test_register_agent_success(self, client):
        """POST /api/global/agents registers a new agent."""
        # Register region first
        client.post("/api/global/regions", json={
            "region_id": "us_east", "name": "US East",
            "endpoint": "https://us-east.asimnexus.io",
        })
        # Register agent
        response = client.post("/api/global/agents", json={
            "agent_id": "agent_001",
            "agent_type": "discovery",
            "region_id": "us_east",
            "capabilities": ["mesh_discovery", "peer_routing"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "registered"
        assert data["agent_id"] == "agent_001"

    def test_register_agent_region_not_found(self, client):
        """Registering agent to unknown region returns error."""
        response = client.post("/api/global/agents", json={
            "agent_id": "agent_002",
            "agent_type": "discovery",
            "region_id": "nonexistent",
        })
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_register_agent_duplicate(self, client):
        """Registering the same agent twice returns error."""
        client.post("/api/global/regions", json={
            "region_id": "us_east", "name": "US East",
            "endpoint": "https://us-east.asimnexus.io",
        })
        client.post("/api/global/agents", json={
            "agent_id": "agent_001", "agent_type": "discovery",
            "region_id": "us_east",
        })
        response = client.post("/api/global/agents", json={
            "agent_id": "agent_001", "agent_type": "discovery",
            "region_id": "us_east",
        })
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


# ─── Status & Overview Tests ─────────────────────────────────────────────────


class TestGlobalAgentStatus:
    """Tests for status and overview endpoints."""

    def test_global_status_before_activation(self, client):
        """GET /api/global/status shows inactive state."""
        response = client.get("/api/global/status")
        assert response.status_code == 200
        data = response.json()
        assert data["mode_active"] is False
        assert data["regions"] == 0
        assert data["active_agents"] == 0

    def test_global_status_after_activation(self, client):
        """Status reflects activation and registered resources."""
        # Activate
        client.post("/api/global/activate", json={})
        # Register region and agent
        client.post("/api/global/regions", json={
            "region_id": "us_east", "name": "US East",
            "endpoint": "https://us-east.asimnexus.io",
        })
        client.post("/api/global/agents", json={
            "agent_id": "agent_001", "agent_type": "discovery",
            "region_id": "us_east",
        })

        response = client.get("/api/global/status")
        data = response.json()
        assert data["mode_active"] is True
        assert data["regions"] == 1
        assert data["active_agents"] == 1

    def test_global_overview(self, client):
        """GET /api/global/overview returns full deployment overview."""
        # Set up some data
        client.post("/api/global/activate", json={})
        client.post("/api/global/regions", json={
            "region_id": "us_east", "name": "US East",
            "endpoint": "https://us-east.asimnexus.io",
        })
        client.post("/api/global/agents", json={
            "agent_id": "agent_001", "agent_type": "discovery",
            "region_id": "us_east",
        })

        response = client.get("/api/global/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["global_mode"] is True
        assert data["total_regions"] == 1
        assert data["total_agents"] == 1
        assert len(data["regions"]) == 1
        assert len(data["agents"]) == 1
        assert data["regions"][0]["region_id"] == "us_east"
        assert data["agents"][0]["agent_id"] == "agent_001"

    def test_global_overview_empty(self, client):
        """Overview with no data shows zeros."""
        response = client.get("/api/global/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["global_mode"] is False
        assert data["total_regions"] == 0
        assert data["total_agents"] == 0


# ─── Full Workflow Test ──────────────────────────────────────────────────────


class TestGlobalAgentWorkflow:
    """End-to-end workflow test."""

    def test_full_global_workflow(self, client):
        """Complete workflow: activate → register regions → register agents → status → deactivate."""
        # Step 1: Activate
        resp = client.post("/api/global/activate", json={})
        assert resp.json()["status"] == "activated"

        # Step 2: Register 3 regions
        for region in [
            ("us_east", "US East", "https://us-east.asimnexus.io"),
            ("eu_west", "EU West", "https://eu-west.asimnexus.io"),
            ("ap_south", "Asia Pacific", "https://ap-south.asimnexus.io"),
        ]:
            resp = client.post("/api/global/regions", json={
                "region_id": region[0], "name": region[1], "endpoint": region[2],
            })
            assert resp.json()["status"] == "registered"

        # Step 3: Deploy to one region
        resp = client.post("/api/global/regions/us_east/deploy", json={
            "config": {"replicas": 5}
        })
        assert resp.json()["status"] == "deployed"

        # Step 4: Register agents in each region
        for i, region in enumerate(["us_east", "eu_west", "ap_south"]):
            resp = client.post("/api/global/agents", json={
                "agent_id": f"agent_{i:03d}",
                "agent_type": "orchestrator",
                "region_id": region,
                "capabilities": ["deploy", "monitor", "sync"],
            })
            assert resp.json()["status"] == "registered"

        # Step 5: Verify status
        resp = client.get("/api/global/status")
        status = resp.json()
        assert status["mode_active"] is True
        assert status["regions"] == 3
        assert status["active_agents"] == 3

        # Step 6: Verify overview
        resp = client.get("/api/global/overview")
        overview = resp.json()
        assert overview["total_regions"] == 3
        assert overview["total_agents"] == 3

        # Step 7: Deactivate
        resp = client.post("/api/global/deactivate")
        assert resp.json()["status"] == "deactivated"
