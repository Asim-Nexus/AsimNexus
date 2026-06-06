# Release & Rollback Guide — AsimNexus v1.0.1

> **Document:** `docs/operations/RELEASE_ROLLBACK_GUIDE.md`
> **Version:** v1.0.1
> **Status:** RELEASE-FROZEN as of 2026-06-01

---

## 1. Release Pipeline Flow

The release pipeline is automated via [`scripts/release_pipeline.py`](../../scripts/release_pipeline.py) — a Python CLI that orchestrates build, test, publish, deploy, and rollback workflows.

### Pipeline Stages

```
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │  --build │───▶│  --test  │───▶│ --publish│───▶│ --deploy │───▶│ --status │
  │  Docker  │    │ Pre-rel. │    │ Container│    │ dev/stag/│    │ Verify   │
  │  images  │    │ test suite│   │ registry │    │ prod     │    │ health   │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### CLI Usage

```bash
# Build Docker images
python scripts/release_pipeline.py --build

# Build a specific version
python scripts/release_pipeline.py --version v1.0.1 --build

# Run pre-release test suite
python scripts/release_pipeline.py --test

# Push to container registry
python scripts/release_pipeline.py --publish

# Deploy to environment
python scripts/release_pipeline.py --deploy dev
python scripts/release_pipeline.py --deploy staging
python scripts/release_pipeline.py --deploy prod

# Rollback to version
python scripts/release_pipeline.py --rollback v1.0.0

# Check deployment status
python scripts/release_pipeline.py --status
```

### Semver Validation

The pipeline enforces strict semver via [`SEMVER_PATTERN`](../../scripts/release_pipeline.py:59):

```python
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
```

Accepted formats: `1.0.1`, `1.0.1-rc1`, `1.0.1+build42`

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REGISTRY` | `ghcr.io` | Container registry URL |
| `IMAGE_NAME` | `asimnexus/asimnexus` | Image name |
| `DOCKER_USERNAME` | — | Registry username |
| `DOCKER_PASSWORD` | — | Registry password |
| `KUBECONFIG` | — | Path to kubeconfig file |
| `AWS_PROFILE` | — | AWS profile for EKS deployments |

### Key Image Tags

- `asimnexus/asimnexus:latest` — Latest stable
- `asimnexus/asimnexus:kernel` — Kernel image
- `asimnexus/asimnexus:v1.0.1` — Versioned release

---

## 2. Docker Build

### Multi-Stage Dockerfile

The [`Dockerfile`](../../Dockerfile) uses a two-stage build:

**Stage 1: Builder** (`python:3.11-slim`)
- Installs build deps: `gcc`, `g++`, `make`, `libssl-dev`, `libffi-dev`, `libpq-dev`
- Installs Python dependencies from `requirements.txt`

**Stage 2: Runtime** (`python:3.11-slim`)
- Installs runtime deps: `curl`, `libpq5`, `sqlite3`
- Copies site-packages from builder stage
- Copies application code: `main.py`, `simple_backend.py`, `backend/`, `core/`, `mesh/`, `security/`, `storage/`, etc.
- Creates non-root user `asimnexus` (UID 1000)
- Runs as non-root user

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
# ... install build deps + pip install -r requirements.txt

FROM python:3.11-slim AS runtime
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# ... copy app code
USER asimnexus
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Production Services

The [`docker-compose.prod.yml`](../../docker-compose.prod.yml) defines **8 services**:

| Service | Image/Context | Port(s) | Resource Limits |
|---------|--------------|---------|-----------------|
| `backend` | Custom Dockerfile | 8000, 8766 | CPUs: 4, Memory: 8G |
| `frontend` | `./frontend/react/Dockerfile` | 3000 | — |
| `postgres` | `postgres:15-alpine` | 5432 | — |
| `redis` | `redis:7-alpine` | 6379 | — |
| `clickhouse` | `clickhouse/clickhouse-server:24.3` | 8123, 9000 | — |
| `minio` | `minio/minio:latest` | 9000, 9001 | — |
| `chromadb` | `chromadb/chroma:latest` | 8000 | — |
| `nginx` | `nginx:alpine` | 80, 443 | — |

Backend depends on all 5 storage services with health condition checks.

---

## 3. Release Checklist

### Pre-Release

- [ ] All tests passing: `python scripts/release_pipeline.py --test`
- [ ] Semver validated: pipeline rejects invalid version strings
- [ ] All 5 storage services healthy: `curl localhost:8000/health/ready`
- [ ] Mesh networking operational: `curl localhost:8000/api/mesh/status`
- [ ] No unresolved CRITICAL/HIGH security issues
- [ ] `STATUS.md` has accurate component statuses
- [ ] `MASTER_BLUEPRINT.md` is up-to-date
- [ ] Version tag created: `git tag v1.0.1`
- [ ] Release branch exists: `release/v1.0.1`

### Release

- [ ] Run build: `python scripts/release_pipeline.py --version v1.0.1 --build`
- [ ] Run publish: `python scripts/release_pipeline.py --version v1.0.1 --publish`
- [ ] Deploy to staging: `python scripts/release_pipeline.py --deploy staging`
- [ ] Run smoke tests against staging
- [ ] Deploy to production: `python scripts/release_pipeline.py --deploy prod`
- [ ] Verify health probes: `curl -f http://localhost:8000/health`
- [ ] Verify API endpoints respond: `curl -f http://localhost:8000/api/version`
- [ ] Record release via backend: `/api/deploy/release`

### Post-Release

- [ ] Monitor storage health for 30 minutes
- [ ] Check mesh peer count > 0
- [ ] Verify consensus engine operational
- [ ] Confirm override endpoints functional: `/api/override/pending`
- [ ] Update `STATUS.md` freeze date if applicable
- [ ] Archive release artifacts in `deploy/release/`

---

## 4. Rollback Procedure

### 4.1 Docker Compose Rollback

```bash
# 1. Identify the current version
python scripts/release_pipeline.py --status

# 2. Rollback to previous version
python scripts/release_pipeline.py --rollback v1.0.0

# 3. Or target a specific version
python scripts/release_pipeline.py --rollback v0.9.0

# 4. Restart services with previous image tag
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify
curl -f http://localhost:8000/health
python scripts/release_pipeline.py --status
```

### 4.2 API-Based Rollback

The [`backend/deployment.py`](../../backend/deployment.py) provides programmatic rollback:

```python
# Via API
POST /api/deploy/rollback
{
  "target": "web",
  "to_version": "v1.0.0"
}

# Response
{
  "target": "web",
  "rolled_back_to": "v1.0.0",
  "artifact_path": "deploy/release/asimnexus-web-v1.0.0.tar.gz",
  "timestamp": "2026-06-01T12:00:00Z"
}
```

The `rollback_release()` function:
- Finds existing artifact files matching `asimnexus-{target}-*.tar.gz`
- If no `to_version` specified, selects the second-latest version
- Records rollback metadata (intent only; actual deployment handled by orchestrator)

### 4.3 Database Rollback

```bash
# PostgreSQL
docker exec asimnexus-postgres pg_dump -U asimnexus asimnexus > pre_rollback_backup.sql
# Restore from backup
cat backup_before_release.sql | docker exec -i asimnexus-postgres psql -U asimnexus asimnexus

# ClickHouse
# Tables use TTL-based retention; rollback via data re-import from backup bucket

# MinIO
mc cp -r backup-bucket/ asimnexus-minio/data/
```

### 4.4 Single Binary Rollback

```bash
# 1. Stop current process
systemctl stop asimnexus

# 2. Restore previous binary from deploy/release/
cp deploy/release/asimnexus-web-v1.0.0.tar.gz /opt/asimnexus/
cd /opt/asimnexus && tar xzf asimnexus-web-v1.0.0.tar.gz

# 3. Restart
systemctl start asimnexus

# 4. Verify
curl -f http://localhost:8000/health
```

---

## 5. Version Tags

### Tag Naming Convention

| Tag Pattern | Example | Purpose |
|-------------|---------|---------|
| `v{major}.{minor}.{patch}` | `v1.0.1` | Standard release |
| `v{major}.{minor}.{patch}-rc{N}` | `v1.0.1-rc1` | Release candidate |
| `v{major}.{minor}.{patch}-hotfix.{N}` | `v1.0.1-hotfix.1` | Urgent bugfix |
| `v{major}.{minor}.{patch}+build{B}` | `v1.0.1+build42` | Build metadata |

### Tag Management

```bash
# Create release tag
git tag -a v1.0.1 -m "AsimNexus v1.0.1 release"
git push origin v1.0.1

# Create hotfix tag
git tag -a v1.0.1-hotfix.1 -m "Hotfix: critical security patch"
git push origin v1.0.1-hotfix.1

# List tags
git tag -l "v1.0.*"

# Delete tag (if needed)
git tag -d v1.0.1-rc1
git push origin :refs/tags/v1.0.1-rc1
```

---

## 6. Branch Strategy

### Branch Structure

```
main                          # Active development for v1.2+
  └── release/v1.0.1          # ❄️ FROZEN release candidate (no direct commits)
       ├── hotfix/security-*  # Critical security patches
       ├── hotfix/critical-*  # Data-loss bugfixes
       └── docs/*             # Documentation updates (with review)
```

### Rules (from [`.github/RELEASE_FREEZE.md`](../../.github/RELEASE_FREEZE.md))

| State | Status |
|-------|--------|
| Release freeze | ❄️ **FROZEN** as of 2026-06-01 |
| `release/v1.0.1` | No direct commits allowed |
| New features for v1.0.1 | **BLOCKED** |
| Protocol/API changes | **BLOCKED** |
| Dependency version bumps | **BLOCKED** |
| Refactoring beyond bugfix scope | **BLOCKED** |

### What IS Allowed

- Critical security patches → `hotfix/security-*`
- Data-loss bugfixes → `hotfix/critical-*`
- Documentation updates → direct to `release/v1.0.1` with review

### Hotfix Procedure

```bash
# 1. Checkout release branch
git checkout release/v1.0.1

# 2. Create hotfix branch
git checkout -b hotfix/critical-auth-fix

# 3. Fix + test
# ... make changes ...
python scripts/release_pipeline.py --test

# 4. PR into BOTH release branch AND main
git push origin hotfix/critical-auth-fix
# → Open PR to release/v1.0.1
# → Open PR to main

# 5. Tag
git tag v1.0.1-hotfix.1
git push origin v1.0.1-hotfix.1
```

### Release Cadence

| Version | Status | Notes |
|---------|--------|-------|
| v1.0.1 | ❄️ Frozen | Current release |
| v1.2 | In development | Post-freeze (desktop/mobile platform, advanced UX) |

---

## 7. Deployment Artifacts

Artifacts are stored in `deploy/release/` and follow naming convention:

```
asimnexus-{target}-{version}.tar.gz
manifest-{version}.json
```

Supported targets: `web`, `pwa`, `desktop`, `mobile`, `docker`, `kubernetes`

Each artifact is SHA-256 checksummed and accompanied by a JSON manifest:

```json
{
  "version": "1.0.1",
  "target": "web",
  "checksum": "a1b2c3d4...",
  "generated": "2026-06-01T12:00:00Z"
}
```

---

*Last updated: 2026-06-01 for v1.0.1 release documentation*
