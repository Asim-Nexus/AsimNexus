#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade deployment config tests
ASIMNEXUS Deploy Config Tests
===============================
Tests for configuration loading, validation, and target-specific overrides.
"""

import os
import pytest
from pathlib import Path
from backend.config import (
    load_deploy_config, validate_deploy_env, get_target_config,
    SUPPORTED_TARGETS, _DEFAULTS
)


class TestDeployConfig:
    """Test suite for deployment configuration functions."""

    def test_load_deploy_config_returns_defaults(self):
        """load_deploy_config returns default values when no env vars are set."""
        # Clear relevant env vars for this test
        for key in _DEFAULTS:
            if key in os.environ:
                del os.environ[key]

        config = load_deploy_config()
        assert config["ASIM_DEPLOY_NAMESPACE"] == "asimnexus"
        assert config["ASIM_RELEASE_CHANNEL"] == "stable"
        assert config["ASIM_CONTAINER_IMAGE"] == "asimnexus/backend"
        assert config["ASIM_CONTAINER_PORT"] == "8080"
        assert config["ASIM_INGRESS_HOST"] == "asimnexus.local"
        assert config["ASIM_REMOTE_PUBLISH"] == "false"

    def test_load_deploy_config_env_overrides(self, monkeypatch):
        """load_deploy_config respects environment variable overrides."""
        monkeypatch.setenv("ASIM_DEPLOY_NAMESPACE", "my-custom-ns")
        monkeypatch.setenv("ASIM_CONTAINER_PORT", "3000")
        monkeypatch.setenv("ASIM_RELEASE_CHANNEL", "beta")

        config = load_deploy_config()
        assert config["ASIM_DEPLOY_NAMESPACE"] == "my-custom-ns"
        assert config["ASIM_CONTAINER_PORT"] == "3000"
        assert config["ASIM_RELEASE_CHANNEL"] == "beta"

    def test_load_deploy_config_partial_override(self, monkeypatch):
        """load_deploy_config merges env overrides with remaining defaults."""
        monkeypatch.setenv("ASIM_INGRESS_HOST", "example.com")

        config = load_deploy_config()
        assert config["ASIM_INGRESS_HOST"] == "example.com"
        assert config["ASIM_DEPLOY_NAMESPACE"] == "asimnexus"  # still default

    # ------------------------------------------------------------------ #
    # validate_deploy_env
    # ------------------------------------------------------------------ #

    def test_validate_deploy_env_valid_defaults(self, monkeypatch):
        """validate_deploy_env returns valid=True for default config."""
        for key in _DEFAULTS:
            if key in os.environ:
                del os.environ[key]

        result = validate_deploy_env()
        assert result["valid"] is True
        assert result["issues"] == []
        assert "config" in result

    def test_validate_deploy_env_creates_missing_release_dir(self, tmp_path, monkeypatch):
        """validate_deploy_env creates the release directory if missing."""
        fake_release_dir = str(tmp_path / "deploy" / "release")
        monkeypatch.setenv("ASIM_RELEASE_DIR", fake_release_dir)

        result = validate_deploy_env()
        assert result["valid"] is True
        assert Path(fake_release_dir).exists()

    def test_validate_deploy_env_invalid_port(self, monkeypatch):
        """validate_deploy_env reports invalid port."""
        monkeypatch.setenv("ASIM_CONTAINER_PORT", "not-a-number")

        result = validate_deploy_env()
        assert result["valid"] is False
        assert any("Invalid container port" in issue for issue in result["issues"])

    def test_validate_deploy_env_port_out_of_range(self, monkeypatch):
        """validate_deploy_env reports port out of valid range."""
        monkeypatch.setenv("ASIM_CONTAINER_PORT", "99999")

        result = validate_deploy_env()
        assert result["valid"] is False
        assert any("Invalid container port" in issue for issue in result["issues"])

    def test_validate_deploy_env_port_zero(self, monkeypatch):
        """validate_deploy_env rejects port 0."""
        monkeypatch.setenv("ASIM_CONTAINER_PORT", "0")

        result = validate_deploy_env()
        assert result["valid"] is False
        assert any("Invalid container port" in issue for issue in result["issues"])

    # ------------------------------------------------------------------ #
    # get_target_config
    # ------------------------------------------------------------------ #

    def test_get_target_config_docker(self):
        """get_target_config returns docker-specific overrides."""
        cfg = get_target_config("docker")
        assert cfg["target"] == "docker"
        assert cfg["base_image"] == "python:3.11-slim"
        assert cfg["expose_port"] == "8080"
        assert cfg["healthcheck_path"] == "/healthz"

    def test_get_target_config_kubernetes(self):
        """get_target_config returns kubernetes-specific overrides."""
        cfg = get_target_config("kubernetes")
        assert cfg["target"] == "kubernetes"
        assert cfg["namespace"] == "asimnexus"
        assert cfg["image"] == "asimnexus/backend:latest"
        assert cfg["replicas"] == 2

    def test_get_target_config_pwa(self):
        """get_target_config returns PWA-specific overrides."""
        cfg = get_target_config("pwa")
        assert cfg["target"] == "pwa"
        assert cfg["start_url"] == "/"
        assert cfg["display"] == "standalone"
        assert cfg["theme_color"] == "#0a0a2e"
        assert cfg["background_color"] == "#0a0a2e"

    def test_get_target_config_desktop(self):
        """get_target_config returns desktop-specific overrides."""
        cfg = get_target_config("desktop")
        assert cfg["target"] == "desktop"
        assert cfg["framework"] == "tauri"
        assert cfg["bundle_id"] == "com.asimnexus.app"

    def test_get_target_config_mobile(self):
        """get_target_config returns mobile-specific overrides."""
        cfg = get_target_config("mobile")
        assert cfg["target"] == "mobile"
        assert cfg["framework"] == "pwa-wrapper"
        assert cfg["bundle_id"] == "com.asimnexus.mobile"

    def test_get_target_config_unknown_target(self):
        """get_target_config returns base config with target set for unknown target."""
        cfg = get_target_config("custom-target")
        assert cfg["target"] == "custom-target"
        # Should not contain any target-specific override keys
        assert "base_image" not in cfg
        assert "framework" not in cfg

    def test_get_target_config_includes_base_config(self):
        """get_target_config includes all base config keys."""
        cfg = get_target_config("pwa")
        assert cfg["ASIM_DEPLOY_NAMESPACE"] == "asimnexus"
        assert cfg["ASIM_CONTAINER_PORT"] == "8080"
        assert cfg["ASIM_RELEASE_CHANNEL"] == "stable"

    def test_get_target_config_env_overrides_propagate(self, monkeypatch):
        """get_target_config picks up env var overrides in base config."""
        monkeypatch.setenv("ASIM_CONTAINER_PORT", "9090")

        cfg = get_target_config("docker")
        assert cfg["expose_port"] == "9090"

    # ------------------------------------------------------------------ #
    # SUPPORTED_TARGETS
    # ------------------------------------------------------------------ #

    def test_supported_targets_contains_all(self):
        """SUPPORTED_TARGETS includes all expected deployment targets."""
        assert "docker" in SUPPORTED_TARGETS
        assert "kubernetes" in SUPPORTED_TARGETS
        assert "pwa" in SUPPORTED_TARGETS
        assert "desktop" in SUPPORTED_TARGETS
        assert "mobile" in SUPPORTED_TARGETS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
