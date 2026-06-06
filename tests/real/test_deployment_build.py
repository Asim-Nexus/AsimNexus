#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade deployment build tests
ASIMNEXUS Deployment Build Tests
=================================
Tests for artifact building, manifest creation, verification, and rollback.
"""

import os
import gc
import json
import time
import pytest
import tarfile
import hashlib
import tempfile
from pathlib import Path
from backend.deployment import (
    build_artifact, create_manifest, verify_artifact,
    package_release, rollback_release, get_deployment_status,
    list_targets, sha256_file, ARTIFACTS_DIR
)


class TestDeploymentBuild:
    """Test suite for deployment build functions."""

    @pytest.fixture(autouse=True)
    def setup_artifacts_dir(self, tmp_path):
        """Override ARTIFACTS_DIR to a temp directory for test isolation."""
        import backend.deployment as dep_mod
        self._original_artifacts_dir = dep_mod.ARTIFACTS_DIR
        dep_mod.ARTIFACTS_DIR = tmp_path / "deploy" / "release"
        dep_mod.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        yield
        dep_mod.ARTIFACTS_DIR = self._original_artifacts_dir

    @pytest.fixture
    def deploy_target_dir(self, tmp_path):
        """Create a mock deploy target directory."""
        target_dir = tmp_path / "deploy" / "pwa"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "index.html").write_text("<html>Test PWA</html>")
        (target_dir / "manifest.json").write_text('{"name": "test"}')
        (target_dir / "sw.js").write_text("// service worker")
        return target_dir

    def test_build_artifact_creates_tar_gz(self, deploy_target_dir):
        """Test that build_artifact creates a valid tar.gz file."""
        import backend.deployment as dep_mod
        dep_mod.BASE_DIR = deploy_target_dir.parent.parent

        artifact = build_artifact(target="pwa", version="1.0.0")

        assert artifact["target"] == "pwa"
        assert artifact["version"] == "1.0.0"
        assert "checksum" in artifact
        assert artifact["path"].endswith(".tar.gz")
        assert Path(artifact["path"]).exists()

        # Verify it's a valid tar.gz
        with tarfile.open(artifact["path"], "r:gz") as tar:
            names = tar.getnames()
            assert any("index.html" in n for n in names)

    def test_build_artifact_target_not_found(self):
        """Test that build_artifact raises error for missing target."""
        with pytest.raises(FileNotFoundError):
            build_artifact(target="nonexistent", version="1.0.0")

    def test_create_manifest(self):
        """Test that create_manifest writes a valid JSON manifest."""
        result = create_manifest(target="pwa", version="1.0.0", checksum="abc123")

        assert "manifest_path" in result
        assert "manifest" in result
        assert result["manifest"]["version"] == "1.0.0"
        assert result["manifest"]["target"] == "pwa"
        assert result["manifest"]["checksum"] == "abc123"

        # Verify manifest file exists and is valid JSON
        manifest_path = Path(result["manifest_path"])
        assert manifest_path.exists()
        manifest_data = json.loads(manifest_path.read_text())
        assert manifest_data["version"] == "1.0.0"

    def test_verify_artifact_valid(self, deploy_target_dir):
        """Test verify_artifact returns True for valid file."""
        import backend.deployment as dep_mod
        dep_mod.BASE_DIR = deploy_target_dir.parent.parent

        artifact = build_artifact(target="pwa", version="1.0.0")
        assert verify_artifact(artifact["path"]) is True

    def test_verify_artifact_with_checksum(self, deploy_target_dir):
        """Test verify_artifact with checksum matching."""
        import backend.deployment as dep_mod
        dep_mod.BASE_DIR = deploy_target_dir.parent.parent

        artifact = build_artifact(target="pwa", version="1.0.0")
        assert verify_artifact(artifact["path"], artifact["checksum"]) is True

    def test_verify_artifact_with_wrong_checksum(self, deploy_target_dir):
        """Test verify_artifact returns False for wrong checksum."""
        import backend.deployment as dep_mod
        dep_mod.BASE_DIR = deploy_target_dir.parent.parent

        artifact = build_artifact(target="pwa", version="1.0.0")
        assert verify_artifact(artifact["path"], "wrongchecksum") is False

    def test_verify_artifact_missing_file(self):
        """Test verify_artifact returns False for missing file."""
        assert verify_artifact("/nonexistent/file.tar.gz") is False

    def test_package_release(self, deploy_target_dir):
        """Test that package_release builds artifact and creates manifest."""
        import backend.deployment as dep_mod
        dep_mod.BASE_DIR = deploy_target_dir.parent.parent

        result = package_release(target="pwa", version="1.0.0")

        assert "artifact" in result
        assert "manifest" in result
        assert result["artifact"]["target"] == "pwa"
        assert result["artifact"]["version"] == "1.0.0"
        assert result["manifest"]["manifest"]["version"] == "1.0.0"

    def test_rollback_release_to_specific_version(self, deploy_target_dir):
        """Test rollback to a specific version."""
        import backend.deployment as dep_mod
        dep_mod.BASE_DIR = deploy_target_dir.parent.parent

        # Build two versions
        package_release(target="pwa", version="1.0.0")
        package_release(target="pwa", version="2.0.0")

        # Rollback to v1
        result = rollback_release(target="pwa", to_version="1.0.0")
        assert result["target"] == "pwa"
        assert result["rolled_back_to"] == "1.0.0"

    def test_rollback_release_no_previous(self, deploy_target_dir):
        """Test rollback when only one version exists."""
        import backend.deployment as dep_mod
        dep_mod.BASE_DIR = deploy_target_dir.parent.parent

        package_release(target="pwa", version="1.0.0")

        with pytest.raises(ValueError, match="Not enough versions"):
            rollback_release(target="pwa")

    def test_rollback_release_target_not_found(self):
        """Test rollback for non-existent target."""
        with pytest.raises(FileNotFoundError, match="No artifacts found"):
            rollback_release(target="nonexistent")

    def test_get_deployment_status(self, deploy_target_dir):
        """Test get_deployment_status returns correct structure."""
        import backend.deployment as dep_mod
        dep_mod.BASE_DIR = deploy_target_dir.parent.parent

        package_release(target="pwa", version="1.0.0")

        status = get_deployment_status()
        assert "pwa" in status
        assert len(status["pwa"]) >= 1
        assert status["pwa"][0]["version"] == "1.0.0"

    def test_list_targets(self):
        """Test list_targets returns supported targets."""
        targets = list_targets()
        assert "web" in targets
        assert "pwa" in targets
        assert "desktop" in targets
        assert "mobile" in targets
        assert "docker" in targets
        assert "kubernetes" in targets

    def test_sha256_file(self, tmp_path):
        """Test SHA-256 calculation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        expected = hashlib.sha256(b"hello world").hexdigest()
        actual = sha256_file(str(test_file))
        assert actual == expected

    def test_sha256_file_large_content(self, tmp_path):
        """Test SHA-256 with larger content (chunked reading)."""
        test_file = tmp_path / "large.bin"
        test_file.write_bytes(b"x" * 100000)  # 100KB

        expected = hashlib.sha256(b"x" * 100000).hexdigest()
        actual = sha256_file(str(test_file))
        assert actual == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
