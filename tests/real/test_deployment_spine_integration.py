#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade deployment spine route tests
ASIMNEXUS Deployment Spine Integration Tests
=============================================
End-to-end validation of all 10 deployment endpoints wired in simple_backend.
Uses FastAPI TestClient to verify route registration and basic request/response.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch


# --------------------------------------------------------------------------- #
# Helper: build a minimal TestClient without launching the full server
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def client():
    """Build a TestClient from simple_backend's create_app factory."""
    from starlette.testclient import TestClient
    import sys
    # Ensure backend package is importable
    backend_dir = Path(__file__).resolve().parents[2] / "backend"
    if str(backend_dir.parent) not in sys.path:
        sys.path.insert(0, str(backend_dir.parent))

    from simple_backend import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
# Phase D — Deployment Route Tests
# --------------------------------------------------------------------------- #

class TestHealthzEndpoint:
    """GET /healthz — container liveness/readiness probe."""

    def test_healthz_returns_ok(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"status": "ok"}


class TestDeployStatusEndpoint:
    """GET /api/deploy/status — full deployment status snapshot."""

    def test_deploy_status_returns_dict(self, client):
        resp = client.get("/api/deploy/status")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestDeployTargetsEndpoint:
    """GET /api/deploy/targets — list of supported targets."""

    def test_deploy_targets_contains_targets(self, client):
        resp = client.get("/api/deploy/targets")
        assert resp.status_code == 200
        data = resp.json()
        assert "targets" in data
        assert len(data["targets"]) > 0
        assert "docker" in data["targets"]


class TestDeployBuildEndpoint:
    """POST /api/deploy/build — build an artifact."""

    def test_deploy_build_missing_target(self, client):
        resp = client.post("/api/deploy/build", json={})
        assert resp.status_code == 400
        assert "target is required" in resp.text

    def test_deploy_build_nonexistent_target(self, client):
        resp = client.post("/api/deploy/build", json={
            "target": "nonexistent_target_xyz",
            "version": "1.0.0",
        })
        assert resp.status_code == 400


class TestDeployRollbackEndpoint:
    """POST /api/deploy/rollback — rollback to a previous version."""

    def test_deploy_rollback_missing_target(self, client):
        resp = client.post("/api/deploy/rollback", json={})
        assert resp.status_code == 400
        assert "target is required" in resp.text

    def test_deploy_rollback_nonexistent_target(self, client):
        resp = client.post("/api/deploy/rollback", json={
            "target": "nonexistent_target_xyz",
        })
        assert resp.status_code == 400


class TestDeployReleaseEndpoint:
    """POST /api/deploy/release — publish a release."""

    def test_deploy_release_missing_params(self, client):
        resp = client.post("/api/deploy/release", json={})
        assert resp.status_code == 400
        assert "version and target are required" in resp.text

    def test_deploy_release_missing_target(self, client):
        resp = client.post("/api/deploy/release", json={"version": "1.0.0"})
        assert resp.status_code == 400
        assert "version and target are required" in resp.text

    def test_deploy_release_success(self, client):
        resp = client.post("/api/deploy/release", json={
            "version": "9.9.9-test",
            "target": "docker",
            "checksum": "abc123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "9.9.9-test"
        assert data["target"] == "docker"
        assert data["checksum"] == "abc123"
        assert data["is_current"] is True


class TestDeployReleasesEndpoint:
    """GET /api/deploy/releases — list releases, optionally filtered."""

    def test_deploy_releases_returns_list(self, client):
        resp = client.get("/api/deploy/releases")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_deploy_releases_filtered(self, client):
        resp = client.get("/api/deploy/releases?target=docker")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestReleaseCurrentEndpoint:
    """GET /api/release/current — current active release."""

    def test_release_current_returns_dict(self, client):
        resp = client.get("/api/release/current")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_release_current_filtered(self, client):
        resp = client.get("/api/release/current?target=docker")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestVersionEndpoint:
    """GET /api/version — version, build ID, git SHA, channel."""

    def test_version_returns_all_fields(self, client):
        resp = client.get("/api/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert "build_id" in data
        assert "git_sha" in data
        assert "channel" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_version_build_id_is_timestamp(self, client):
        resp = client.get("/api/version")
        data = resp.json()
        assert data["build_id"].isdigit()
        assert len(data["build_id"]) == 14


class TestBuildEndpoint:
    """GET /api/build — build ID, git SHA, config validity."""

    def test_build_returns_all_fields(self, client):
        resp = client.get("/api/build")
        assert resp.status_code == 200
        data = resp.json()
        assert "build_id" in data
        assert "git_sha" in data
        assert "config_valid" in data
        assert "issues" in data
        assert isinstance(data["build_id"], str)
        assert isinstance(data["config_valid"], bool)
        assert isinstance(data["issues"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
