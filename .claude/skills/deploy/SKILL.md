# /deploy — AsimNexus Infrastructure Management

> **Purpose:** Build, deploy, rollback, and release management for AsimNexus.  
> **Trigger:** `/deploy` command.  
> **Requires:** Docker, SSH access (for remote deploy), GitHub Actions (for CI/CD).

---

## Available Commands

| Command | Endpoint | Description |
|---------|----------|-------------|
| `build` | [`/api/deploy/build`](../../../simple_backend.py:719) | Build Docker image |
| `rollback` | [`/api/deploy/rollback`](../../../simple_backend.py:732) | Rollback to previous release |
| `release` | [`/api/deploy/release`](../../../simple_backend.py:753) | Tag and push a release |
| `status` | [`/api/deploy/releases`](../../../simple_backend.py:766) | List all releases |

---

## Build

### Prerequisites
- Docker installed
- `infra/docker/Dockerfile` exists
- `.dockerignore` configured

### How to Build

```bash
# Local Docker build
docker build -f infra/docker/Dockerfile -t asimnexus:latest .

# Or via API
curl -X POST http://localhost:8000/api/deploy/build \
  -H "Content-Type: application/json" \
  -d '{"tag": "latest", "platform": "linux/amd64"}'
```

### Production Build (GitHub Actions)

The CI/CD pipeline at [`.github/workflows/ci-cd.yml`](../../../.github/workflows/ci-cd.yml) handles:
- Multi-stage Docker build (`linux/amd64`)
- Push to Docker Hub (`asimnexus/asim-nexus`)
- SSH deploy to production (if secrets configured)

Trigger: Push to `main` branch.

---

## Deploy

### API Deploy

```bash
curl -X POST http://localhost:8000/api/deploy/release \
  -H "Content-Type: application/json" \
  -d '{"version": "v1.2.3", "description": "Release notes here"}'
```

### SSH Deploy (Manual)

```bash
# Set required env vars
set SSH_KEY=path/to/key
set SSH_USER=deploy
set SSH_HOST=your-server.com

# Then run deploy
python scripts/deploy_production.sh
```

### Docker Compose Deploy

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

---

## Rollback

### API Rollback

```bash
curl -X POST http://localhost:8000/api/deploy/rollback \
  -H "Content-Type: application/json" \
  -d '{"to_version": "v1.2.2"}'
```

### Manual Rollback

```bash
# Revert to previous Docker image
docker pull asimnexus/asim-nexus:previous-tag
docker stop asimnexus
docker run -d --name asimnexus asimnexus/asim-nexus:previous-tag
```

---

## Release Management

### How Releases Work

1. Feature branches merge to `main`
2. CI/CD builds and pushes Docker image
3. Tag with semantic version: `v{MAJOR}.{MINOR}.{PATCH}`
4. Release notes auto-generated from commit messages

### Check Current Release

```bash
curl http://localhost:8000/api/release/current
```

### List All Releases

```bash
curl http://localhost:8000/api/deploy/releases
```

---

## Infrastructure Map

```
📁 infra/
├── docker/
│   ├── Dockerfile          ← Production Dockerfile
│   └── docker-compose.yml  ← Compose config
📁 k8s/                     ← Kubernetes manifests (if using)
📁 deployment/              ← Deployment scripts
📁 .github/workflows/
├── ci-cd.yml               ← Main CI/CD pipeline
└── docker-publish.yml      ← Docker publish workflow
```

---

## Health Checks

After deploy, verify:

```bash
# Health endpoint
curl http://localhost:8000/health

# Full system status
curl http://localhost:8000/api/system/complete

# Integration health
curl http://localhost:8000/api/integration/health

# Dharma veto status
curl http://localhost:8000/api/dharma/veto-status
```

---

## Rollback Criteria

**Initiate rollback if:**
- Health check fails 3+ times in 60 seconds
- `/api/dharma/veto-status` returns error or inactive
- Integration health shows 2+ connections down
- Error rate > 5% in first 5 minutes

**Rollback command:**
```bash
curl -X POST http://localhost:8000/api/deploy/rollback \
  -H "Content-Type: application/json" \
  -d '{"to_version": "previous"}'
```
