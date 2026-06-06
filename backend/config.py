#!/usr/bin/env python3
"""
STATUS: REAL — Deployment configuration loader
ASIMNEXUS Deploy Config
=======================
Loads environment variables and default values for the deployment spine.
All settings can be overridden via env vars prefixed with ``ASIM_``.
"""

import os
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger("AsimNexus.Config")

_BASE = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
_DEFAULTS: Dict[str, str] = {
    "ASIM_DEPLOY_NAMESPACE": "asimnexus",
    "ASIM_RELEASE_DIR": str(_BASE / "deploy" / "release"),
    "ASIM_RELEASE_CHANNEL": "stable",
    "ASIM_CONTAINER_IMAGE": "asimnexus/backend",
    "ASIM_CONTAINER_PORT": "8080",
    "ASIM_INGRESS_HOST": "asimnexus.local",
    "ASIM_SIGNING_KEY_PATH": str(_BASE / "deploy" / "release" / "signing.key"),
    "ASIM_REMOTE_PUBLISH": "false",  # disabled by default per user decision
}

# Supported deployment targets
SUPPORTED_TARGETS = ["docker", "kubernetes", "pwa", "desktop", "mobile"]


def load_deploy_config() -> Dict[str, str]:
    """Load deployment configuration from environment with defaults.

    Returns a dict of all ``ASIM_*`` config keys and their resolved values.
    """
    config = {}
    for key, default in _DEFAULTS.items():
        config[key] = os.getenv(key, default)
    return config


def validate_deploy_env() -> Dict:
    """Validate that all required environment/config values are present.

    Returns a dict with ``valid`` (bool) and ``issues`` (list of strings).
    """
    config = load_deploy_config()
    issues = []

    release_dir = Path(config["ASIM_RELEASE_DIR"])
    if not release_dir.exists():
        try:
            release_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create release dir {release_dir}: {e}")

    port = config["ASIM_CONTAINER_PORT"]
    if not port.isdigit() or not (1 <= int(port) <= 65535):
        issues.append(f"Invalid container port: {port}")

    return {"valid": len(issues) == 0, "issues": issues, "config": config}


def get_target_config(target: str) -> Dict:
    """Return target-specific configuration.

    Includes base config plus any target-level overrides.
    """
    base = load_deploy_config()
    target_overrides: Dict[str, Dict] = {
        "docker": {
            "base_image": "python:3.11-slim",
            "expose_port": base["ASIM_CONTAINER_PORT"],
            "healthcheck_path": "/healthz",
        },
        "kubernetes": {
            "namespace": base["ASIM_DEPLOY_NAMESPACE"],
            "image": f"{base['ASIM_CONTAINER_IMAGE']}:latest",
            "replicas": 2,
            "healthcheck_path": "/healthz",
        },
        "pwa": {
            "start_url": "/",
            "display": "standalone",
            "theme_color": "#0a0a2e",
            "background_color": "#0a0a2e",
        },
        "desktop": {
            "framework": "tauri",
            "bundle_id": "com.asimnexus.app",
        },
        "mobile": {
            "framework": "pwa-wrapper",
            "bundle_id": "com.asimnexus.mobile",
        },
    }
    return {**base, "target": target, **target_overrides.get(target, {})}
