#!/usr/bin/env python3
"""
ASIMNEXUS Release Pipeline
==========================
Automated release lifecycle: build, test, publish, deploy, rollback, status.

Usage:
    python scripts/release_pipeline.py --build                  # Build Docker images
    python scripts/release_pipeline.py --test                   # Run pre-release test suite
    python scripts/release_pipeline.py --publish                # Push to container registry
    python scripts/release_pipeline.py --deploy dev             # Deploy to dev
    python scripts/release_pipeline.py --deploy staging         # Deploy to staging
    python scripts/release_pipeline.py --deploy prod            # Deploy to production
    python scripts/release_pipeline.py --rollback v1.0.0        # Rollback to version
    python scripts/release_pipeline.py --version v1.2.3 --build # Build specific version
    python scripts/release_pipeline.py --status                 # Check deployment status
    python scripts/release_pipeline.py --help                   # Show this message

Environment Variables:
    REGISTRY          Container registry URL (default: ghcr.io)
    IMAGE_NAME        Image name (default: asimnexus/asimnexus)
    DOCKER_USERNAME   Registry username
    DOCKER_PASSWORD   Registry password
    KUBECONFIG        Path to kubeconfig file
    AWS_PROFILE       AWS profile for EKS deployments
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

# Add project root to path for backend.release import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ReleasePipeline")

# ─── Constants ───────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_MODULE = "backend.release"
REGISTRY = os.getenv("REGISTRY", "ghcr.io")
IMAGE_NAME = os.getenv("IMAGE_NAME", "asimnexus/asimnexus")
KERNEL_IMAGE = f"{IMAGE_NAME}-kernel"

# Valid semver pattern (strict: major.minor.patch with optional pre-release/build)
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _validate_version(version: Optional[str]) -> Optional[str]:
    """Validate a version string follows semver. Returns the version or None."""
    if version is None:
        return None
    version = version.strip().lstrip("v")
    if not SEMVER_PATTERN.match(version):
        logger.error(
            f"Invalid version format: '{version}'. "
            "Expected semver (e.g. 1.2.3, 1.2.3-rc1, 1.2.3+build42)"
        )
        sys.exit(1)
    return version


def _run_command(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0 and check:
        logger.error(f"Command failed (exit {result.returncode}): {result.stderr}")
        sys.exit(result.returncode)
    if result.stdout:
        logger.info(result.stdout.strip())
    if result.stderr:
        logger.warning(result.stderr.strip())
    return result


def _get_image_tag(version: Optional[str] = None) -> str:
    """Get full image tag from version or use 'latest'."""
    tag = version or "latest"
    return f"{REGISTRY}/{IMAGE_NAME}:{tag}"


def _get_kernel_image_tag(version: Optional[str] = None) -> str:
    """Get full kernel image tag."""
    tag = version or "latest"
    return f"{REGISTRY}/{KERNEL_IMAGE}:{tag}"


def _import_release_module():
    """Dynamically import the backend.release module."""
    try:
        from backend import release
        return release
    except ImportError as e:
        logger.warning(f"Cannot import backend.release: {e}")
        return None


def _bump_version(current: str, part: str = "patch") -> str:
    """Bump a semver version string by major, minor, or patch.
    
    Args:
        current: Current version string (e.g. "1.0.0" or "v1.0.0")
        part: Which part to bump: "major", "minor", or "patch"
    
    Returns:
        Bumped version string without 'v' prefix.
    """
    clean = current.lstrip("v")
    match = SEMVER_PATTERN.match(clean)
    if not match:
        logger.error(f"Cannot bump invalid version: {current}")
        sys.exit(1)
    
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


# ─── Pipeline Steps ──────────────────────────────────────────────────────────


def build(version: Optional[str] = None) -> None:
    """Build Docker images for the project."""
    version = _validate_version(version)
    logger.info("=" * 60)
    logger.info("STEP: Build Docker Images")
    logger.info("=" * 60)

    # Build main image
    tag = _get_image_tag(version)
    logger.info(f"Building main image: {tag}")
    _run_command([
        "docker", "build", "-t", tag,
        "-f", str(PROJECT_ROOT / "Dockerfile"),
        str(PROJECT_ROOT),
    ])

    # Build kernel image if Dockerfile.kernel exists
    kernel_dockerfile = PROJECT_ROOT / "Dockerfile.kernel"
    if kernel_dockerfile.exists():
        kernel_tag = _get_kernel_image_tag(version)
        logger.info(f"Building kernel image: {kernel_tag}")
        _run_command([
            "docker", "build", "-t", kernel_tag,
            "-f", str(kernel_dockerfile),
            str(PROJECT_ROOT),
        ])
    else:
        logger.info("Dockerfile.kernel not found — skipping kernel image build")

    logger.info("✓ Build complete")


def test() -> None:
    """Run the pre-release test suite."""
    logger.info("=" * 60)
    logger.info("STEP: Pre-release Test Suite")
    logger.info("=" * 60)

    # 1. Unit tests
    logger.info("--- Unit Tests ---")
    _run_command([
        sys.executable, "-m", "pytest", "tests/",
        "--ignore=tests/integration", "--ignore=tests/real",
        "-v", "--tb=short", "--junitxml=test-results/unit.xml",
    ])

    # 2. Integration tests
    logger.info("--- Integration Tests ---")
    _run_command([
        sys.executable, "-m", "pytest", "tests/integration/",
        "-v", "--tb=short", "--junitxml=test-results/integration.xml",
    ], check=False)  # Don't fail on integration test issues

    # 3. Lint check
    logger.info("--- Lint Check ---")
    _run_command([
        sys.executable, "-m", "flake8", ".",
        "--count", "--select=E9,F63,F7,F82",
        "--show-source", "--statistics",
    ], check=False)

    # 4. Type check
    logger.info("--- Type Check ---")
    _run_command([
        sys.executable, "-m", "mypy",
        "storage/", "core/federation/", "governance/",
        "--strict",
    ], check=False)

    logger.info("✓ Test suite complete")


def publish(version: Optional[str] = None) -> None:
    """Push images to container registry."""
    version = _validate_version(version)
    logger.info("=" * 60)
    logger.info("STEP: Publish to Container Registry")
    logger.info("=" * 60)

    # Login
    username = os.getenv("DOCKER_USERNAME") or os.getenv("REGISTRY_USER")
    password = os.getenv("DOCKER_PASSWORD") or os.getenv("REGISTRY_PASSWORD")
    if username and password:
        logger.info(f"Logging in to {REGISTRY}...")
        _run_command(["docker", "login", REGISTRY, "-u", username, "-p", password])
    else:
        logger.info("No registry credentials found — attempting anonymous push")

    # Push main image
    tag = _get_image_tag(version)
    logger.info(f"Pushing main image: {tag}")
    _run_command(["docker", "push", tag])

    # Push kernel image if it was built
    if (PROJECT_ROOT / "Dockerfile.kernel").exists():
        kernel_tag = _get_kernel_image_tag(version)
        logger.info(f"Pushing kernel image: {kernel_tag}")
        _run_command(["docker", "push", kernel_tag])

    # Tag and push 'latest' if version specified
    if version:
        latest_tag = _get_image_tag()
        logger.info(f"Tagging {tag} as {latest_tag}")
        _run_command(["docker", "tag", tag, latest_tag])
        _run_command(["docker", "push", latest_tag])

        if (PROJECT_ROOT / "Dockerfile.kernel").exists():
            kernel_latest_tag = _get_kernel_image_tag()
            _run_command(["docker", "tag", kernel_tag, kernel_latest_tag])
            _run_command(["docker", "push", kernel_latest_tag])

    # Record the release
    release = _import_release_module()
    if release:
        checksum = _compute_checksum()
        record = release.publish_release(
            version=version or "latest",
            target="docker",
            checksum=checksum,
        )
        logger.info(f"Release recorded: {json.dumps(record, indent=2)}")
    else:
        logger.warning("Release metadata not recorded (backend.release unavailable)")

    logger.info("✓ Publish complete")


def _compute_checksum() -> str:
    """Compute a SHA-256 checksum of the project's key files as a release fingerprint."""
    import hashlib
    hasher = hashlib.sha256()
    key_files = [
        "main.py",
        "Dockerfile",
        "Dockerfile.kernel",
        "requirements.txt",
        "docker-compose.yml",
        "docker-compose.prod.yml",
        "docker-compose.storage.yml",
    ]
    for path in key_files:
        filepath = PROJECT_ROOT / path
        if filepath.exists():
            hasher.update(filepath.read_bytes())
    return hasher.hexdigest()


def deploy(environment: str, version: Optional[str] = None) -> None:
    """Deploy to a target environment: dev, staging, or prod."""
    version = _validate_version(version)
    logger.info("=" * 60)
    logger.info(f"STEP: Deploy to {environment.upper()}")
    logger.info("=" * 60)

    tag = version or "latest"
    image = _get_image_tag(tag)

    if environment == "dev":
        _deploy_dev(image)
    elif environment == "staging":
        _deploy_staging(image)
    elif environment == "prod":
        _deploy_production(image)
    else:
        logger.error(f"Unknown environment: {environment}")
        sys.exit(1)

    logger.info(f"✓ Deploy to {environment} complete")


def _deploy_dev(image: str) -> None:
    """Deploy to local/dev Docker Compose."""
    logger.info("Deploying to dev environment (Docker Compose)...")
    os.environ["ASIM_IMAGE"] = image
    _run_command([
        "docker", "compose", "-f", "docker-compose.yml",
        "up", "-d", "--no-deps", "backend",
    ])
    _health_check("http://localhost:8000/health")


def _deploy_staging(image: str) -> None:
    """Deploy to staging (Docker Compose + storage)."""
    logger.info("Deploying to staging environment...")
    os.environ["ASIM_IMAGE"] = image
    _run_command([
        "docker", "compose",
        "-f", "docker-compose.yml",
        "-f", "docker-compose.storage.yml",
        "up", "-d",
    ])
    _health_check("http://localhost:8000/health")


def _deploy_production(image: str) -> None:
    """Deploy to production (Kubernetes)."""
    logger.info("Deploying to production (Kubernetes)...")

    # Check for kubectl
    try:
        _run_command(["kubectl", "version", "--short"], check=False)
    except Exception:
        logger.error("kubectl not available — cannot deploy to Kubernetes")
        sys.exit(1)

    # Update deployment image
    _run_command([
        "kubectl", "set", "image",
        "deployment/asimnexus", f"asimnexus={image}",
        "-n", "asimnexus",
    ])

    # Rollout status
    _run_command([
        "kubectl", "rollout", "status",
        "deployment/asimnexus",
        "-n", "asimnexus", "--timeout=5m",
    ])

    # Health check via service
    _run_command([
        "kubectl", "get", "svc", "asimnexus",
        "-n", "asimnexus",
    ])

    logger.info("Production deployment rolled out")


def _health_check(url: str, timeout: int = 120) -> None:
    """Wait for a health endpoint to return 200."""
    import urllib.request
    import urllib.error

    logger.info(f"Waiting for health check: {url}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(url, timeout=10)
            if resp.status == 200:
                logger.info("✓ Health check passed")
                return
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            logger.info(f"  Waiting... ({e})")
        time.sleep(5)
    logger.error(f"Health check timed out after {timeout}s")
    sys.exit(1)


def rollback(version: str, environment: str = "prod") -> None:
    """Rollback to a specified version."""
    version = _validate_version(version)
    logger.info("=" * 60)
    logger.info(f"STEP: Rollback to version {version}")
    logger.info("=" * 60)

    image = _get_image_tag(version)

    if environment == "prod":
        # Kubernetes rollback
        _run_command([
            "kubectl", "set", "image",
            "deployment/asimnexus", f"asimnexus={image}",
            "-n", "asimnexus",
        ])
        _run_command([
            "kubectl", "rollout", "status",
            "deployment/asimnexus",
            "-n", "asimnexus", "--timeout=5m",
        ])
    else:
        # Docker Compose rollback
        os.environ["ASIM_IMAGE"] = image
        _run_command([
            "docker", "compose", "-f", "docker-compose.yml",
            "up", "-d", "--no-deps", "backend",
        ])

    # Record the rollback
    release = _import_release_module()
    if release:
        current = release.current_release(target="docker")
        from_version = current.get("version", "unknown")
        record = release.record_rollback(
            from_version=from_version,
            to_version=version,
            target="docker",
        )
        logger.info(f"Rollback recorded: {json.dumps(record, indent=2)}")

    logger.info(f"✓ Rollback to {version} complete")


def status() -> None:
    """Check and display deployment status."""
    logger.info("=" * 60)
    logger.info("Deployment Status Report")
    logger.info("=" * 60)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "registry": REGISTRY,
        "image": IMAGE_NAME,
    }

    # 1. Check release history
    release = _import_release_module()
    if release:
        current = release.current_release(target="docker")
        releases = release.list_releases(target="docker")
        report["current_release"] = current
        report["release_count"] = len(releases)
        report["recent_releases"] = releases[-5:] if releases else []
        logger.info(f"Current release: {json.dumps(current, indent=2)}")
        logger.info(f"Total releases: {len(releases)}")
    else:
        report["release_module"] = "unavailable"
        logger.info("Release module unavailable")

    # 2. Check Docker images
    logger.info("\n--- Docker Images ---")
    _run_command(["docker", "images", "--format", "table {{.Repository}}:{{.Tag}}\t{{.Size}}",
                   f"{REGISTRY}/{IMAGE_NAME}"], check=False)

    # 3. Check Kubernetes (if available)
    logger.info("\n--- Kubernetes Status ---")
    try:
        result = _run_command([
            "kubectl", "get", "pods",
            "-n", "asimnexus", "-o", "wide",
        ], check=False)
        report["kubernetes"] = "available"
    except Exception:
        report["kubernetes"] = "unavailable"
        logger.info("Kubernetes not available")

    # 4. Check Docker Compose services
    logger.info("\n--- Docker Compose Status ---")
    _run_command([
        "docker", "compose", "ps", "--format", "table",
    ], check=False)

    # Save report
    report_path = PROJECT_ROOT / "deploy" / "release" / "status_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, default=str))
    logger.info(f"\nStatus report saved to: {report_path}")


# ─── Version Bump Command ───────────────────────────────────────────────────


def bump(part: str = "patch") -> None:
    """Bump the version in deploy/release/version.txt."""
    version_file = PROJECT_ROOT / "deploy" / "release" / "version.txt"
    if not version_file.exists():
        logger.error(f"Version file not found: {version_file}")
        sys.exit(1)

    current = version_file.read_text().strip()
    logger.info(f"Current version: {current}")

    new_version = _bump_version(current, part)
    version_file.write_text(new_version + "\n")
    logger.info(f"Version bumped to: {new_version}")


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="ASIMNEXUS Release Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--build", action="store_true", help="Build Docker images")
    parser.add_argument("--test", action="store_true", help="Run pre-release test suite")
    parser.add_argument("--publish", action="store_true", help="Push to container registry")
    parser.add_argument("--deploy", type=str, nargs="?", const="dev",
                        choices=["dev", "staging", "prod"],
                        help="Deploy to target environment (dev/staging/prod)")
    parser.add_argument("--rollback", type=str, metavar="VERSION",
                        help="Rollback to specified version")
    parser.add_argument("--status", action="store_true", help="Check deployment status")
    parser.add_argument("--version", type=str, default=None,
                        help="Version tag for build/publish/deploy")
    parser.add_argument("--env", type=str, default="prod",
                        choices=["dev", "staging", "prod"],
                        help="Target environment for rollback (default: prod)")
    parser.add_argument("--bump", type=str, nargs="?", const="patch",
                        choices=["major", "minor", "patch"],
                        help="Bump version in version.txt (major/minor/patch, default: patch)")

    args = parser.parse_args()

    # ── Validate arguments ──────────────────────────────────────────────
    if not any([args.build, args.test, args.publish, args.deploy,
                args.rollback, args.status, args.bump]):
        parser.print_help()
        sys.exit(0)

    # ── Execute steps in order ──────────────────────────────────────────
    if args.bump:
        bump(args.bump)

    if args.build:
        build(args.version)

    if args.test:
        test()

    if args.publish:
        publish(args.version)

    if args.deploy:
        deploy(args.deploy, args.version)

    if args.rollback:
        rollback(args.rollback, args.env)

    if args.status:
        status()

    logger.info("\n" + "=" * 60)
    logger.info("Release pipeline execution complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
