# ASIM NEXUS — Complete Restructuring Plan

## Vision
Clean, modular monorepo where every role (developer, operator, contributor) can find what they need and operate according to their role — locally or externally.

## Current Problems
1. **Root-level clutter** — 8+ docker-compose files, test scripts, many top-level directories
2. **Duplicate/overlapping directories** — `deploy/`, `deployment/`, `deployment_scripts/` overlap; `api/`, `backend/`, `bridge/` mix concerns
3. **Test files scattered** — Tests mixed inside source directories
4. **Multiple frontend fragments** — `frontend/`, `interface/`, `ui/`, `web/`, `desktop/`
5. **Inconsistent naming** — Mixed singular/plural, camelCase/snake_case

## New Structure

```
asim-nexus/
├── .github/                    # GitHub workflows & CI/CD
├── apps/                       # Runnable applications
│   ├── backend/                # Backend API server
│   │   ├── api/                # API routes
│   │   ├── auth/               # Authentication
│   │   ├── bridge/             # Bridges/gateways
│   │   ├── core/               # Backend-specific core
│   │   └── config/             # Backend configs
│   ├── frontend/               # React SPA
│   │   ├── src/                # React source
│   │   ├── public/             # Static assets
│   │   └── e2e/                # E2E tests
│   └── desktop/                # Tauri desktop app
├── packages/                   # Shared libraries
│   ├── core/                   # Core engine (agi_core, event_bus, etc.)
│   ├── mesh/                   # Mesh networking (P2P, DHT, WebRTC)
│   ├── security/               # Security (ZKP, identity, vault, audit)
│   ├── agents/                 # Agent system
│   ├── connectors/             # External service connectors
│   ├── storage/                # Storage adapters (Postgres, ClickHouse, Vector)
│   ├── data-lake/              # Data lake (ingestion, retrieval, storage)
│   ├── kernel/                 # OS kernel
│   ├── os-control/             # OS control & sandbox
│   └── economy/                # Economy & staking
├── infra/                      # Infrastructure & deployment
│   ├── docker/                 # Dockerfiles & compose
│   │   ├── Dockerfile          # Main app Dockerfile
│   │   ├── Dockerfile.kernel   # Kernel Dockerfile
│   │   ├── docker-compose.yml  # Main compose
│   │   ├── docker-compose.local.yml
│   │   └── docker-compose.prod.yml
│   ├── k8s/                    # Kubernetes manifests
│   ├── scripts/                # Deployment & ops scripts
│   └── monitoring/             # Monitoring configs
├── config/                     # Shared configuration
│   ├── asim_brain_config.json
│   ├── asim_constitution.json
│   ├── litellm_config.yaml
│   └── profiles/               # User profiles
├── docs/                       # Documentation
├── tests/                      # Integration & E2E tests
│   ├── integration/            # Integration tests
│   └── performance/            # Performance benchmarks
├── data/                       # Runtime data (gitignored)
├── .env.example                # Environment template
├── .gitignore
└── README.md
```

## Migration Steps

### Phase 1: Create Directory Skeleton
```
mkdir -p apps/backend/{api,auth,bridge,core,config}
mkdir -p apps/frontend/src
mkdir -p apps/desktop
mkdir -p packages/{core,mesh,security,agents,connectors,storage,data-lake,kernel,os-control,economy}
mkdir -p infra/{docker,k8s,scripts,monitoring}
mkdir -p config/profiles
mkdir -p tests/{integration,performance}
```

### Phase 2: Move Source Code
Each directory will be moved to its new location, preserving git history.

### Phase 3: Update Import Paths
All Python imports referencing moved files must be updated.

### Phase 4: Fix Docker & Deploy Configs
Consolidate docker-compose files, update Dockerfile paths.

### Phase 5: Update CI/CD
Fix GitHub Actions workflows for new paths.

### Phase 6: Clean Root
Remove duplicate/empty directories, move test files.
