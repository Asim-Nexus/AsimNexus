#!/usr/bin/env python3
"""
STATUS: REAL — Version metadata tests.
Uses test_client fixture from tests/conftest.py.
"""

import pytest
from pathlib import Path
from backend import version as _version_mod

def test_version_module_functions():
    ver = _version_mod.get_version()
    assert isinstance(ver, str)
    assert len(ver.split(".")) >= 3

    build_id = _version_mod.get_build_id()
    assert isinstance(build_id, str)
    assert build_id.isdigit()

    sha = _version_mod.get_git_sha()
    assert isinstance(sha, str)

    channel = _version_mod.get_release_channel()
    assert channel in ["stable", "beta", "alpha", "dev"]

def test_version_endpoints(test_client):
    """Test /api/version and /api/build endpoints via TestClient fixture."""

    # /api/version
    res = test_client.get("/api/version")
    assert res.status_code == 200
    data = res.json()
    assert "version" in data
    assert "build_id" in data
    assert "git_sha" in data
    assert "channel" in data

    # /api/build
    res = test_client.get("/api/build")
    assert res.status_code == 200
    data = res.json()
    assert "build_id" in data
    assert "git_sha" in data
    assert "config_valid" in data
    assert "issues" in data
