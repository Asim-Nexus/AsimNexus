#!/usr/bin/env python3
"""
STATUS: REAL — Release lifecycle management
ASIMNEXUS Release Manager
=========================
Publish, list, retrieve, and rollback releases.
Stores release metadata as JSON in deploy/release/releases.json.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger("AsimNexus.Release")

# Persistent storage file
_BASE = Path(__file__).resolve().parents[1]
RELEASES_FILE = _BASE / "deploy" / "release" / "releases.json"
RELEASES_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_releases() -> List[Dict]:
    if RELEASES_FILE.exists():
        try:
            return json.loads(RELEASES_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_releases(releases: List[Dict]) -> None:
    RELEASES_FILE.write_text(
        json.dumps(releases, indent=2, sort_keys=True), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def publish_release(*, version: str, target: str, checksum: str) -> Dict:
    """Record a new published release.

    Parameters
    ----------
    version : str   – semantic version (e.g. "0.1.0")
    target  : str   – deployment target (e.g. "docker", "pwa")
    checksum: str   – SHA-256 of the artifact

    Returns
    -------
    dict – the release record that was stored.
    """
    releases = _load_releases()
    record = {
        "version": version,
        "target": target,
        "checksum": checksum,
        "published_at": datetime.utcnow().isoformat() + "Z",
        "is_current": True,
    }
    # Un-mark any previous current release for the same target
    for r in releases:
        if r["target"] == target and r.get("is_current"):
            r["is_current"] = False
    releases.append(record)
    _save_releases(releases)
    logger.info("Published release %s for target %s", version, target)
    return record


def list_releases(target: Optional[str] = None) -> List[Dict]:
    """Return all recorded releases, optionally filtered by *target*."""
    releases = _load_releases()
    if target:
        return [r for r in releases if r["target"] == target]
    return releases


def current_release(target: Optional[str] = None) -> Dict:
    """Return the currently-active release record.

    If *target* is given only look at releases for that target,
    otherwise return the latest ``is_current`` release across all targets.
    """
    releases = _load_releases()
    for r in reversed(releases):
        if r.get("is_current"):
            if target is None or r["target"] == target:
                return r
    return {"version": None, "target": target, "status": "no_current_release"}


def set_current_release(*, version: str, target: str) -> None:
    """Mark *version* as the current release for *target*.

    Raises ValueError if the version is not found.
    """
    releases = _load_releases()
    found = False
    for r in releases:
        if r["target"] == target:
            r["is_current"] = r["version"] == version
            if r["version"] == version:
                found = True
    if not found:
        raise ValueError(f"Version {version} not found for target {target}")
    _save_releases(releases)


def record_rollback(*, from_version: str, to_version: str, target: str) -> Dict:
    """Record a rollback event and update the current pointer.

    Returns the rollback record dict.
    """
    set_current_release(version=to_version, target=target)
    record = {
        "action": "rollback",
        "target": target,
        "from_version": from_version,
        "to_version": to_version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    # Append to a rollback log file
    rollback_log = RELEASES_FILE.parent / "rollback_log.jsonl"
    with open(rollback_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    logger.info("Rollback %s → %s for target %s", from_version, to_version, target)
    return record
