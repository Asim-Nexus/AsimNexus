#!/usr/bin/env python3
"""
STATUS: REAL — Release API endpoint tests.
Uses test_client fixture from tests/conftest.py.
"""

import json
import pytest
from pathlib import Path
from backend import release as _release_mod

def test_release_api_workflow(test_client):
    """Test release API workflow via TestClient fixture."""

    # Clean release storage temporarily or use custom test version
    test_version = "99.9.9"
    test_target = "pwa"
    
    # 1. Post a new release
    payload = {
        "version": test_version,
        "target": test_target,
        "checksum": "dummychecksum123"
    }
    response = test_client.post("/api/deploy/release", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == test_version
    assert data["target"] == test_target
    assert data["checksum"] == "dummychecksum123"

    # 2. Get current release
    response = test_client.get(f"/api/release/current?target={test_target}")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == test_version

    # 3. List releases
    response = test_client.get(f"/api/deploy/releases?target={test_target}")
    assert response.status_code == 200
    releases = response.json()
    assert isinstance(releases, list)
    assert any(r["version"] == test_version for r in releases)
