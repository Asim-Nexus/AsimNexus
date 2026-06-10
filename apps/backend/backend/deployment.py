import os
import json
import hashlib
import tarfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.override_integrator import (
    approve_with_override,
    reject_with_override,
    escalate_with_override,
    list_pending_overrides,
)

logger = logging.getLogger("deployment.override")

# Root of the project
BASE_DIR = Path(os.getenv('ASIM_ROOT', Path.cwd()))

# Directory where built artifacts are stored
ARTIFACTS_DIR = BASE_DIR / 'deploy' / 'release'
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def _artifact_path(target: str, version: str) -> Path:
    """Return the full path for a given target and version."""
    filename = f"asimnexus-{target}-{version}.tar.gz"
    return ARTIFACTS_DIR / filename

def _write_manifest(manifest: dict, version: str) -> Path:
    """Write a JSON manifest file for the release.
    Returns the path to the written file."""
    manifest_path = ARTIFACTS_DIR / f"manifest-{version}.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return manifest_path

def build_artifact(*, target: str, version: str, entrypoint: Optional[str] = None) -> dict:
    """Package the selected target into a tar.gz.
    * target – one of the supported targets (web, pwa, desktop, mobile, docker, kubernetes).
    * version – semantic version string.
    * entrypoint – optional path inside the target that should be the start point (e.g., index.html).
    Returns a dict with artifact metadata.
    """
    # Resolve source directory for the target
    src_dir = BASE_DIR / 'deploy' / target
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Target source directory not found: {src_dir}")

    out_path = _artifact_path(target, version)
    # Create tar.gz archive
    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(src_dir, arcname=target)

    checksum = sha256_file(str(out_path))
    artifact = {
        "target": target,
        "version": version,
        "path": str(out_path),
        "checksum": checksum,
        "entrypoint": entrypoint or "index.html",
        "created": datetime.utcnow().isoformat() + "Z",
    }
    return artifact

def create_manifest(*, target: str, version: str, checksum: str) -> dict:
    """Create a release manifest JSON for a single artifact.
    The manifest follows the schema used by the release spine.
    """
    manifest = {
        "version": version,
        "target": target,
        "checksum": checksum,
        "generated": datetime.utcnow().isoformat() + "Z",
    }
    manifest_path = _write_manifest(manifest, version)
    return {
        "manifest_path": str(manifest_path),
        "manifest": manifest,
    }

def verify_artifact(path: str, checksum: Optional[str] = None) -> bool:
    """Verify that the file exists and its SHA‑256 matches the provided checksum (if any)."""
    if not os.path.isfile(path):
        return False
    actual = sha256_file(path)
    if checksum and actual != checksum:
        return False
    return True

def package_release(*, target: str, version: str) -> dict:
    """Convenience wrapper that builds the artifact, creates its manifest and returns both.
    This is the main entry‑point used by the deployment API.
    """
    artifact = build_artifact(target=target, version=version)
    manifest_info = create_manifest(target=target, version=version, checksum=artifact["checksum"])
    return {
        "artifact": artifact,
        "manifest": manifest_info,
    }

def rollback_release(*, target: str, to_version: Optional[str] = None) -> dict:
    """Rollback the given target to a previous version.
    * to_version – explicit version; if omitted, the previous version (lexicographically) is chosen.
    The function simply records the rollback intent; actual deployment is handled by the orchestrator.
    """
    # Find existing artifact files for the target
    pattern = f"asimnexus-{target}-*.tar.gz"
    candidates = sorted(ARTIFACTS_DIR.glob(pattern))
    if not candidates:
        raise FileNotFoundError(f"No artifacts found for target {target}")
    # Determine target version
    if to_version:
        target_path = _artifact_path(target, to_version)
        if not target_path.exists():
            raise FileNotFoundError(f"Requested rollback version not found: {to_version}")
    else:
        # previous version is the one before the latest
        if len(candidates) < 2:
            raise ValueError("Not enough versions to rollback")
        target_path = candidates[-2]
        to_version = target_path.stem.split('-')[-1]
    # Record rollback metadata (could be extended to write to a DB)
    rollback_info = {
        "target": target,
        "rolled_back_to": to_version,
        "artifact_path": str(target_path),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    return rollback_info

def get_deployment_status() -> dict:
    """Return a snapshot of all built artifacts grouped by target.
    The result is suitable for the `/api/deploy/status` endpoint.
    """
    status = {}
    for artifact in ARTIFACTS_DIR.glob('*.tar.gz'):
        # Remove .tar.gz suffix to get base name
        name = artifact.name.replace('.tar.gz', '')  # asimnexus-<target>-<version>
        parts = name.split('-')
        if len(parts) < 3:
            continue
        target = parts[1]
        version = '-'.join(parts[2:])  # Handle versions with dots like "1.0.0"
        entry = {
            "path": str(artifact),
            "checksum": sha256_file(str(artifact)),
            "size_bytes": artifact.stat().st_size,
            "version": version,
        }
        status.setdefault(target, []).append(entry)
    return status

def list_targets() -> list[str]:
    """Return the list of supported deployment targets.
    The hard‑coded list mirrors `release.packager.list_supported_targets()`.
    """
    return ["web", "pwa", "desktop", "mobile", "docker", "kubernetes"]

def sha256_file(path: str) -> str:
    """Calculate SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# =============================================================================
# Override Integrator — FastAPI Endpoints
# =============================================================================
# These endpoints wire the Human Override Engine into the runtime API.
# They use the convenience wrappers from core.override_integrator.

override_router = APIRouter(prefix="/api/override", tags=["override"])


class OverrideActionRequest(BaseModel):
    """Request body for approve/reject/escalate endpoints."""
    request_id: str
    reason: str = ""


class OverrideActionResponse(BaseModel):
    """Response from approve/reject/escalate endpoints."""
    success: bool
    request_id: str
    status: str = ""
    human_id: str = ""
    signature: str = ""
    error: str = ""
    escalated_to: str = ""
    escalated_tier: str = ""
    approved_by: List[str] = []
    quorum_required: int = 0
    quorum_remaining: int = 0


class PendingOverrideItem(BaseModel):
    """A single pending override request for the list endpoint."""
    request_id: str
    action_preview: str
    trigger: str
    tier: str
    requested_by: str
    created_at: float
    expires_at: float
    status: str
    approved_by: List[str] = []
    quorum_required: int = 0


class PendingOverridesResponse(BaseModel):
    """Response from the pending list endpoint."""
    pending: List[PendingOverrideItem]
    total: int


@override_router.post("/approve", response_model=OverrideActionResponse)
async def api_approve_override(body: OverrideActionRequest):
    """Approve a pending override request.

    The human confirms they want to override the AI decision.
    Returns the cryptographic signature of the override.
    """
    logger.info(f"Override approve request: {body.request_id}")
    result = approve_with_override(
        request_id=body.request_id,
        human_id="api_user",
        reason=body.reason,
    )
    return _build_response(result)


@override_router.post("/reject", response_model=OverrideActionResponse)
async def api_reject_override(body: OverrideActionRequest):
    """Reject a pending override request.

    The human disagrees with the override — the AI decision stands.
    May auto-escalate to next tier for critical triggers.
    """
    logger.info(f"Override reject request: {body.request_id}")
    result = reject_with_override(
        request_id=body.request_id,
        human_id="api_user",
        reason=body.reason,
    )
    return _build_response(result)


@override_router.post("/escalate", response_model=OverrideActionResponse)
async def api_escalate_override(body: OverrideActionRequest):
    """Reject and escalate an override request to the next tier.

    For constitutional or policy-critical triggers, this moves the
    decision to the next tier (e.g., PERSONAL → TRUSTED_CIRCLE).
    """
    logger.info(f"Override escalate request: {body.request_id}")
    result = escalate_with_override(
        request_id=body.request_id,
        human_id="api_user",
        reason=body.reason,
    )
    return _build_response(result)


@override_router.get("/pending", response_model=PendingOverridesResponse)
async def api_list_pending_overrides():
    """List all pending override requests.

    Returns requests waiting for human review, including
    quorum_pending requests waiting for trusted circle votes.
    """
    pending = list_pending_overrides()
    items = []
    for p in pending:
        items.append(PendingOverrideItem(
            request_id=p.get("request_id", ""),
            action_preview=p.get("action_preview", ""),
            trigger=p.get("trigger", ""),
            tier=p.get("tier", ""),
            requested_by=p.get("requested_by", ""),
            created_at=p.get("created_at", 0.0),
            expires_at=p.get("expires_at", 0.0),
            status=p.get("status", ""),
            approved_by=p.get("approved_by", []),
            quorum_required=p.get("quorum_required", 0),
        ))
    return PendingOverridesResponse(pending=items, total=len(items))


def _build_response(result: Dict[str, Any]) -> OverrideActionResponse:
    """Convert engine result dict to OverrideActionResponse."""
    return OverrideActionResponse(
        success=result.get("success", False),
        request_id=result.get("request_id", ""),
        status=result.get("status", ""),
        human_id=result.get("human_id", ""),
        signature=result.get("signature", ""),
        error=result.get("error", ""),
        escalated_to=result.get("escalated_to", ""),
        escalated_tier=result.get("escalated_tier", ""),
        approved_by=result.get("approved_by", []),
        quorum_required=result.get("quorum_required", 0),
        quorum_remaining=result.get("quorum_remaining", 0),
    )
