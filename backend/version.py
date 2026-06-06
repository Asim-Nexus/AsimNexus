#!/usr/bin/env python3
"""
STATUS: REAL — Version & build metadata
ASIMNEXUS Version Module
========================
Exposes version, build-id, git SHA, and release channel.
Reads version.txt from deploy/release/ as the single source of truth.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

_BASE = Path(__file__).resolve().parents[1]
VERSION_FILE = _BASE / "deploy" / "release" / "version.txt"


def get_version() -> str:
    """Return the current semantic version string.

    Reads from ``deploy/release/version.txt``.  Falls back to ``"0.1.0"``
    if the file does not exist yet.
    """
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.1.0"


def get_build_id() -> str:
    """Return a timestamp-based build identifier."""
    return datetime.utcnow().strftime("%Y%m%d%H%M%S")


def get_git_sha() -> str:
    """Return the current HEAD git SHA, or ``'unknown'`` if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(_BASE),
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def get_release_channel() -> str:
    """Return the release channel.

    Defaults to ``"stable"`` unless overridden by env ``ASIM_RELEASE_CHANNEL``.
    """
    return os.getenv("ASIM_RELEASE_CHANNEL", "stable")
