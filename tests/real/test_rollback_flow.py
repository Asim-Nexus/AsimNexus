#!/usr/bin/env python3
"""
STATUS: REAL — Rollback flow tests.
Uses test_client fixture from tests/conftest.py.
"""

import os
import json
import pytest
from pathlib import Path
from backend import release as _release_mod
from backend import deployment as _deploy_mod

def test_rollback_flow_logic(test_client, tmp_path):
    """Test rollback logic via API using TestClient fixture."""

    # Set up multiple dummy releases for testing rollback
    target = "docker"
    v1 = "1.0.0"
    v2 = "2.0.0"
    
    # Clean/setup release state via release module
    _release_mod.publish_release(version=v1, target=target, checksum="checksum111")
    _release_mod.publish_release(version=v2, target=target, checksum="checksum222")

    # Create matching dummy tar.gz artifacts so build_artifact/rollback_release finds them
    t1_path = _deploy_mod.ARTIFACTS_DIR / f"asimnexus-{target}-{v1}.tar.gz"
    t2_path = _deploy_mod.ARTIFACTS_DIR / f"asimnexus-{target}-{v2}.tar.gz"
    
    t1_path.write_bytes(b"dummy artifact v1")
    t2_path.write_bytes(b"dummy artifact v2")

    try:
        # Assert current is v2
        curr = _release_mod.current_release(target=target)
        assert curr["version"] == v2

        # Perform rollback to v1 via API
        payload = {
            "target": target,
            "to_version": v1
        }
        res = test_client.post("/api/deploy/rollback", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["target"] == target
        assert data["rolled_back_to"] == v1

        # Check current is now v1
        curr = _release_mod.current_release(target=target)
        assert curr["version"] == v1
    finally:
        # Clean up files
        t1_path.unlink(missing_ok=True)
        t2_path.unlink(missing_ok=True)
        # Cleanup release metadata if needed
