# AsimNexus Master Blueprint

> **Version:** 1.1  
> **Date:** 2026-06-01  
> **Status:** LIVING DOCUMENT — Update when components graduate REAL / PARTIAL / CONCEPT  
> **Source of truth for:** Architecture, folder map, database plan, security model, mesh design, learning loop, licensing, launch sequence, missing pieces.

---

## 1. Identity

**AsimNexus is a local-first, human-governed, mesh-connected World Operating System and Civilization Architecture** whose purpose is to give every person a secure Human Digital Twin, keep personal data on-device by default, and route compute through explicit trust tiers under privacy, consent, and jurisdiction rules; its core operates through immutable policy, zero-trust verification, observability, and rollback-safe learning, with memory divided into observed, derived, active, and shadow planes; every tool action must pass a Decision → Selection → Validation → Approval → Execution → Audit pipeline; every mode — Personal, Family, Company, Community, and Government — must enforce separate authority boundaries; no-learning and human-gated zones remain immutable unless explicitly approved; cloud and federation are allowed only through auditable opt-in routing and legal escape-hatch controls; and all irreversible actions require human final authority.


---

## 2. Core Engines

| # | Engine | File(s) | Status | Notes |
|---|--------|---------|--------|-------|
| 1 | **FastAPI Backend** | `simple_backend.py` | **REAL** | 75+ endpoints, JWT auth, SQLite, wired to all downstream modules |
| 2 | **AsimBrain Router** | `core/asim_brain.py`, `connectors/smart_model_router.py` | **REAL** | Local Qwen3 GGUF + cloud fallback, Dharma inline veto |
| 3 | **LLM Gateway** | `connectors/unified_llm_gateway.py` | **REAL** | OpenAI, Anthropic, Gemini, DeepSeek, Groq — no NVIDIA NIM |
| 4 | **Dharma Veto** | `core/dharma/dharma_veto.py` | **REAL** | 5-layer ethics blocker, pattern detection, audit log |
| 5 | **ΔT Engine** | `core/dharma/delta_t_engine.py` | **REAL** | Gini symmetry, PoS attenuation, L_max = 7% |
| 6 | **Job Marketplace** | `core/economy/job_marketplace.py` | **REAL** | Escrow sim, ratings, disputes, Dharma veto on every transaction |
| 7 | **Dreaming Engine** | `core/dreaming/dreaming_engine.py` | **REAL** | Async background loop, SQLite memory consolidation |
| 8 | **Auth & Identity** | `auth/identity_provider.py`, `core/identity/user_identity.py` | **REAL** | JWT generation/validation, registration, login |
| 9 | **15 Founder Clones** | `core/founder_clones/world_clones.py` | **PARTIAL** | Configs and prompts real; NO ensemble consensus vote |
| 10 | **Vector Memory** | `core/vector_memory.py` | **PARTIAL** | SQLite-based semantic search, NOT a true vector DB |
| 11 | **ZKP (SHA3 wrapper)** | `core/security/real_zkp.py` | **PARTIAL** | Commitments/proofs via SHA3; NOT real SNARKs |
| 12 | **Mesh Routing** | `mesh/mesh_routing_agent.py`, `core/mesh/p2p_node.py` | **PARTIAL** | Routing logic real; NO real P2P sockets or hole punching |
| 13 | **ClickHouse Warehouse** | [`storage/clickhouse_engine.py`](storage/clickhouse_engine.py) | **REAL** | 6 tables, TTL retention, SQLite/JSONL fallback |
| 14 | **OLTP DB (PostgreSQL)** | [`storage/oltp_engine.py`](storage/oltp_engine.py) | **REAL** | 10 tables, PostgreSQL -> SQLite -> in-memory fallback |
| 15 | **Object Storage (MinIO/S3)** | [`storage/object_store.py`](storage/object_store.py) | **REAL** | 8 buckets, S3 -> local filesystem fallback |
| 16 | **Vector DB (ChromaDB)** | [`storage/vector_store.py`](storage/vector_store.py) | **REAL** | 4 collections, TTL management, ChromaDB -> SQLite -> in-memory fallback |
| 17 | **Storage Migration CLI** | [`scripts/migrate_storage.py`](scripts/migrate_storage.py) | **REAL** | `--all`, `--clickhouse`, `--oltp`, `--object-store`, `--vector`, `--dry-run`, `--status` |
| 18 | **Federation Protocol** | [`core/federation/federation_protocol_enhanced.py`](core/federation/federation_protocol_enhanced.py) | **REAL** | 4-step DID handshake, CRDT sync, heartbeat monitoring |
| 19 | **Global Federation Governor** | [`core/federation/global_federation_governor.py`](core/federation/global_federation_governor.py) | **REAL** | Peer lifecycle management, integrated with CloneConsensusEngine |
| 20 | **Governance Audit** | [`governance/governance_audit.py`](governance/governance_audit.py) | **REAL** | SHA-256 tamper-evident hash chain audit with 24+ AuditAction types |
| 21 | **Cross-Border Compliance** | [`governance/cross_border_compliance.py`](governance/cross_border_compliance.py) | **REAL** | 8 regional frameworks (GDPR, Nepal IT Bill 2081, India DPDP, US Privacy, China PIPL, Singapore PDPA, Brazil LGPD), 3 sovereignty levels |
| 22 | **Federation CLI** | [`scripts/manage_federation.py`](scripts/manage_federation.py) | **REAL** | CLI tool with 10 commands |
| 23 | **Release Pipeline CLI** | [`scripts/release_pipeline.py`](scripts/release_pipeline.py) | **REAL** | Release automation CLI |
| 24 | **CI/CD Workflows** | `.github/workflows/ci-cd.yml`, `.github/workflows/docker-publish.yml`, `.github/workflows/security-scan.yml` | **REAL** | 3 GitHub Actions workflows |
| 25 | **GitHub Actions Policy** | [`docs/GITHUB_ACTIONS_POLICY.md`](docs/GITHUB_ACTIONS_POLICY.md) | **REAL** | Mandatory SHA pinning rules, 22-row Approved Actions table |
| 26 | **Storage Health Probes** | [`backend/health.py`](backend/health.py) | **REAL** | Health probes for all 5 services (Redis, ClickHouse, PostgreSQL, MinIO, ChromaDB) — live/ready/status |
| 27 | **Prometheus Metrics** | [`monitoring/metrics.py`](monitoring/metrics.py) | **REAL** | 5 metric types (up gauge, latency histogram, connections, errors, disk usage) |
| 28 | **Observability Dashboard** | [`monitoring/observability_dashboard.py`](monitoring/observability_dashboard.py) | **REAL** | Real-time dashboard with health scoring (50% weight for storage) |
| 29 | **Grafana Dashboard** | [`monitoring/grafana/dashboards/storage-pod-stability.json`](monitoring/grafana/dashboards/storage-pod-stability.json) | **REAL** | 5 service rows, 7 panels per service, alerting thresholds |
| 30 | **Storage Recovery Runbook** | [`docs/runbooks/storage-service-recovery.md`](docs/runbooks/storage-service-recovery.md) | **REAL** | 964-line comprehensive recovery runbook |
| 31 | **Storage Monitoring Tests** | [`tests/real/test_storage_monitoring.py`](tests/real/test_storage_monitoring.py) | **REAL** | 51 tests across 5 test classes — ALL PASSING |

**CONCEPT-only engines** (no working code yet): Microkernel (`core/kernel/microkernel.py`), DePIN bridge, Quantum-resistant crypto, TPM/Hardware attestation, National gov layer, Blockchain constitution anchor, Neural interface.

---

## 3. Folder Map

```
AsimNexus/
├── core/                    # 320+ Python files — brain, agents, security, economy, mesh
│   ├── agents/              # 15 founder clones, swarm, base_agent
│   ├── dharma/              # ΔT engine, veto, nepal cultural framework
│   ├── dreaming/            # Memory consolidation, bug triage
│   ├── economy/             # Job marketplace, nexus credits
│   ├── federation/          # Federation protocol, global federation governor
│   ├── founder_clones/      # World clones, specializer
│   ├── hdt/                 # Human Digital Twin data models
│   ├── identity/            # User identity, personal OS
│   ├── kernel/              # Microkernel (CONCEPT)
│   ├── math/                # Complex engine, fractal universe
│   ├── mesh/                # P2P, WebRTC, wave propagation
│   └── security/            # ZKP, encryption, level-3 confirmation
├── connectors/              # 62 files — LLM connectors, APIs, gateways
├── backend/                 # Socket manager, DB pool, metrics, health probes
├── storage/                 # 4-layer storage (ClickHouse, PostgreSQL, MinIO, ChromaDB)
├── monitoring/              # Prometheus metrics, observability dashboard, Grafana
├── governance/              # Governance audit, cross-border compliance, founder structure
├── frontend/                # React app (PersonalOS, UniversalChat, Sidebar)
├── agents/                  # Infra agents (cloud balancer, compute scout)
├── auth/                    # Central vault, identity provider
├── bridge/                  # Cloudflare tunnel, LLM orchestrator, MCP
├── cloud/                   # AWS/Azure/GCP free-tier scripts
├── config/                  # Founder YAMLs, constitution JSON, brain config, storage.yaml
├── data/                    # SQLite DB, backups, HDT DIDs, API keys
├── deploy/                  # K8s, Docker Compose, global deployment
├── deployment/              # Dockerfiles, app-store configs, AWS/Azure scripts
├── docker/                  # Docker init scripts (ClickHouse DDL, PostgreSQL DDL)
├── docs/                    # This blueprint + runbooks + preserved docs + archive
├── economy/                 # Nexus credits (token logic)
├── infrastructure/          # K8s config, Redis, nexus hub spec
├── interface/               # Web components, Next.js, universal UI
├── k8s/                     # Kubernetes YAML manifests (storage services, PVC)
├── kernel/                  # Asim kernel, core
├── litellm/                 # LiteLLM proxy server
├── media/                   # (empty — reserved)
├── memory/                  # Redis backend, checkpoints, learning
├── mesh/                    # Device registry, routing, network intelligence
├── mobile/                  # React Native screens + services
├── models/                  # Local GGUF models (Qwen3)
├── os_control/              # File tools, process tools, sandbox, capability matrix
├── runtime/                 # LLM runtime, MCP connectors, hardware bridge
├── security/                # 33 files — audit, hardening, consent manager
├── tests/                   # e2e, integration, unit, chaos engineering, storage monitoring
├── tools/                   # Smoke tests, import checkers
├── training/                # Asim model trainer
└── ui/                      # Static server, HTML dashboards, logo assets
```

---

## 4. Database Plan

| Tier | Technology | Purpose | Files | Status |
|------|-----------|---------|-------|--------|
| **Primary Relational** | SQLite | Users, messages, jobs, tokens, contracts | `data/asim_core.db` | **REAL** |
| **Primary Warehouse** | ClickHouse | Timeseries, analytics, telemetry (6 tables, TTL-based retention) | [`storage/clickhouse_engine.py`](storage/clickhouse_engine.py) | **REAL** |
| **OLTP / Transactions** | PostgreSQL | App transactions, users, economy, governance (10 tables) | [`storage/oltp_engine.py`](storage/oltp_engine.py) | **REAL** |
| **Object Storage** | MinIO / S3 | Raw files, logs, exports, snapshots (8 buckets) | [`storage/object_store.py`](storage/object_store.py) | **REAL** |
| **Vector Search** | ChromaDB | Embeddings for RAG, semantic memory, agent context (4 collections) | [`storage/vector_store.py`](storage/vector_store.py) | **REAL** |
| **Cache / Session** | Redis | Rate limiting, session store, pub/sub | `backend/redis_integration.py` | **PARTIAL** |
| **Event Log** | SQLite append-only | Audit trail, Dharma veto events | `data/cognitive_firewall.jsonl` | **REAL** |

---

## 5. Security Model

### 10-Layer Checklist

1. **Immutable Constitution** — `config/asim_constitution.json` hashed at boot; any mismatch kills startup.
2. **Dharma Policy Gate** — Every action ≥ risk threshold flows through `core/dharma/dharma_veto.py`.
3. **Capability Matrix** — `os_control/capability_matrix.py` defines what each agent/process may do.
4. **JWT Authentication** — `auth/identity_provider.py` issues/validates short-lived tokens.
5. **Credential Vault** — `auth/central_vault.py` encrypts API keys at rest (AES-GCM).
6. **Sandbox Execution** — `os_control/sandbox/docker_sandbox.py` isolates high-risk operations.
7. **Audit Logging** — Every veto, auth event, and contract mutation is append-only logged.
8. **ZKP Human Verification** — `core/security/real_zkp.py` provides SHA3 commitments (placeholder for real SNARKs).
9. **Level-3 Confirmation** — `core/security/level3_confirmation.py` state machine for high-stakes actions (no biometric hardware gate yet).
10. **Consent Manager** — `security/consent_manager.py` explicit opt-in for data sharing and clone activation.

### Critical Action Flow
```
User Request
    → Auth (JWT valid?)
    → Capability Matrix (agent allowed?)
    → Dharma Veto (ethical?)
    → Level-3 Check (high-stakes?)
    → Sandbox (if high-risk)
    → Execute
    → Audit Log
```

---

## 6. Mesh Design

### 4-Level Hierarchy

| Level | Scope | Node Type | Current Status |
|-------|-------|-----------|----------------|
| **L1 — Personal** | Single user / laptop | Solo node, SQLite, local GGUF | **REAL** |
| **L2 — Family** | 2–10 related users | Star topology, shared secrets | **CONCEPT** |
| **L3 — Community / Enterprise** | 10–10,000 users | Mesh+Tree hybrid, mDNS discovery | **PARTIAL** |
| **L4 — Sovereign / Global** | 10K–8B users | Ring+Mesh federated, BGP-like routing | **CONCEPT** |

**Protocols per level:**
- L1: Local WebSocket + REST on `localhost`
- L2: WiFi LAN sync + QR-code pairing (not built)
- L3: WebRTC data channels + mDNS auto-discovery (stubs exist)
- L4: libp2p / noise-protocol gossip (not built)

**Offline-first rule:** Every node MUST function standalone. Sync is always an augmentation, never a dependency.

---

## 7. Auto-Learning Loop

### 10-Step Adapter Pipeline

1. **Collect** — Interaction logs, API responses, user corrections → SQLite.
2. **Tag** — Auto-label with intent, sentiment, success/failure heuristic.
3. **Consolidate** — Dreaming engine runs nightly, compresses short-term → long-term memory.
4. **Distill** — Extract reusable patterns (e.g., "user always asks for Nepali translation first").
5. **Score** — Rate pattern utility by frequency × success rate.
6. **Prune** — Drop patterns below threshold to prevent bloat.
7. **Package** — Turn top patterns into adapter YAML (prompt prefix, tool sequence, fallback rule).
8. **Validate** — Run adapter against last 7 days of logs; require >80% pass rate.
9. **Stage** — Place in `config/adapters/staging/`; Dharma veto checks for bias/escape.
10. **Deploy** — Move to `config/adapters/active/`; hot-reload without restart.

**Current state:** Steps 1–3 (Collect, Tag, Consolidate) are REAL. Steps 4–10 are CONCEPT.

---

## 8. Licensing Path

| Tier | License | Applies To | Notes |
|------|---------|------------|-------|
| **Core** | AGPLv3 | `core/`, `kernel/`, `auth/`, `governance/` | Any distributed modification must be open-sourced |
| **Enterprise** | Commercial | `connectors/enterprise/`, `deployment/enterprise/` | Closed-source add-ons permitted under separate contract |
| **API / SaaS** | API Terms | Hosted instances | Separate terms of service for cloud offering |

**Action:** Add `LICENSE` file (AGPLv3) to repo root; create `docs/licenses/commercial-license-template.txt` for inbound enterprise inquiries.

---

## 9. Launch Sequence

1. ~~**Stabilize REAL components**~~ — ✅ **DONE** (all 4 expansion areas verified: federation/governance, deployment, testing, observability)
2. **Harden PARTIAL → REAL** — ZKP, Mesh, Vector Memory, Level-3 Confirmation.
3. **Frontend parity** — Ensure every backend endpoint has a UI touchpoint.
4. **Multi-user isolation** — PostgreSQL migration, row-level security, per-user HDT.
5. **Offline-first package** — Electron + Tauri builds with embedded SQLite.
6. **Documentation freeze** — Only `MASTER_BLUEPRINT.md`, `STATUS.md`, `TRUTH.md`, `CONTRIBUTING.md` are canonical; rest archived.
7. **Security audit** — Run `tools/check_status_labels.py`, `gitleaks`, `bandit`, dependency scan.
8. **Public repo cleanup** — Remove secrets, add `.env.example`, archive old deployment scripts.
9. **Release v0.1.0-alpha** — Tag, changelog, community onboarding.

---

## 10. Missing Pieces Checklist

| # | Missing Piece | Priority | Status Target |
|---|--------------|----------|---------------|
| 1 | Unified event schema (JSON Schema for all internal messages) | **HIGH** | PARTIAL → REAL |
| 2 | Adapter registry (hot-reload config + validation) | **HIGH** | CONCEPT → PARTIAL |
| ~~3~~ | ~~Real vector DB integration (Chroma/Qdrant)~~ | **HIGH** | PARTIAL → REAL — ✅ **DONE** ([`storage/vector_store.py`](storage/vector_store.py): 4 collections, TTL management, ChromaDB -> SQLite -> in-memory fallback) |
| 4 | P2P socket layer (hole punching, STUN/TURN) | **HIGH** | PARTIAL → REAL |
| 5 | Multi-user row-level security (PostgreSQL) | **HIGH** | CONCEPT → PARTIAL |
| 6 | Real ZKP circuits (replace SHA3 wrapper) | **MEDIUM** | PARTIAL → REAL |
| ~~7~~ | ~~Biometric Level-3 gate (hardware attestation)~~ | **MEDIUM** | **PARTIAL → REAL** — `security/biometric_hardware_gate.py` (425 lines, async verify_and_lock, emergency_bypass, full audit) |
| 8 | DePIN reward bridge (real network integration) | **MEDIUM** | CONCEPT → PARTIAL |
| 9 | seL4-inspired microkernel (replace Python sim) | **LOW** | CONCEPT → PARTIAL |
| 10 | National gov integration layer (A Line) | **LOW** | CONCEPT |
| 11 | Blockchain constitution anchor | **LOW** | CONCEPT |
| 12 | Quantum-resistant algorithms (production-grade) | **LOW** | CONCEPT |
| 13 | Neural interface stub | **LOW** | CONCEPT |
| 14 | Auto-switching multi-cloud balancer (free-tier monitor) | **MEDIUM** | CONCEPT → PARTIAL |
| 15 | Enterprise SSO / SAML connector | **MEDIUM** | CONCEPT → PARTIAL |
| ~~16~~ | ~~Federation & Global Governance~~ | **HIGH** | CONCEPT → REAL — ✅ **DONE** ([`core/federation/federation_protocol_enhanced.py`](core/federation/federation_protocol_enhanced.py): 4-step DID handshake, CRDT sync, heartbeat; [`governance/cross_border_compliance.py`](governance/cross_border_compliance.py): 8 regional frameworks; [`governance/governance_audit.py`](governance/governance_audit.py): tamper-evident hash chain) |
| ~~17~~ | ~~Production Deployment (Docker/K8s)~~ | **HIGH** | CONCEPT → REAL — ✅ **DONE** ([`docker-compose.storage.yml`](docker-compose.storage.yml): 5 services; `k8s/`: 6 manifests; `docker/clickhouse/init/`, `docker/postgres/init/`: DDL scripts) |
| ~~18~~ | ~~Observability & Monitoring~~ | **HIGH** | CONCEPT → REAL — ✅ **DONE** ([`backend/health.py`](backend/health.py): 5-service health probes; [`monitoring/metrics.py`](monitoring/metrics.py): Prometheus metrics; [`monitoring/observability_dashboard.py`](monitoring/observability_dashboard.py): real-time dashboard; [`monitoring/grafana/dashboards/storage-pod-stability.json`](monitoring/grafana/dashboards/storage-pod-stability.json): Grafana dashboard; [`docs/runbooks/storage-service-recovery.md`](docs/runbooks/storage-service-recovery.md): recovery runbook) |
| ~~19~~ | ~~Storage Monitoring Tests~~ | **HIGH** | CONCEPT → REAL — ✅ **DONE** ([`tests/real/test_storage_monitoring.py`](tests/real/test_storage_monitoring.py): 51 tests across 5 test classes, ALL PASSING) |

---

## 11. Storage Infrastructure

AsimNexus uses a **4-layer storage architecture** with graceful degradation at every layer. All layers are optional — if a primary engine is unavailable, the system degrades without crashing.

| Layer | Class | Primary Engine | Fallback Chain | Key Resources |
|-------|-------|---------------|----------------|---------------|
| **ClickHouse** | `AsimNexusEngine` | ClickHouse | SQLite -> JSONL | [`storage/clickhouse_engine.py`](storage/clickhouse_engine.py) — 6 tables, TTL-based retention |
| **OLTP DB** | `OltpEngine` | PostgreSQL | SQLite -> In-memory | [`storage/oltp_engine.py`](storage/oltp_engine.py) — 10 tables, ACID transactions |
| **Object Storage** | `ObjectStore` | S3/MinIO | Local filesystem | [`storage/object_store.py`](storage/object_store.py) — 8 buckets |
| **Vector DB** | `VectorStore` | ChromaDB | SQLite -> In-memory | [`storage/vector_store.py`](storage/vector_store.py) — 4 collections, TTL management |

### Supporting Components

| Component | File | Purpose |
|-----------|------|---------|
| Central Config | [`config/storage.yaml`](config/storage.yaml) | YAML config with `${VAR:-default}` env var substitution |
| Config Loader | [`storage/config.py`](storage/config.py) | Python typed dataclass access to storage config |
| Migration CLI | [`scripts/migrate_storage.py`](scripts/migrate_storage.py) | Unified CLI for migrating legacy storage to 4-layer architecture |
| JSONL Migrator | [`storage/adapters/jsonl_migrator.py`](storage/adapters/jsonl_migrator.py) | JSONL -> ClickHouse |
| In-Memory Migrator | [`storage/adapters/in_memory_migrator.py`](storage/adapters/in_memory_migrator.py) | RAM-only -> OLTP |
| Vector Migrator | [`storage/adapters/vector_migrator.py`](storage/adapters/vector_migrator.py) | Legacy vectors -> VectorStore |

### Deployment Resources

| Resource | File | Description |
|----------|------|-------------|
| Docker Compose (Storage) | [`docker-compose.storage.yml`](docker-compose.storage.yml) | Docker Compose definition for all 4 storage services + Redis |
| ClickHouse DDL | [`docker/clickhouse/init/01_create_tables.sql`](docker/clickhouse/init/01_create_tables.sql) | 6 tables + 2 materialized views for analytics warehouse |
| PostgreSQL DDL | [`docker/postgres/init/01_create_tables.sql`](docker/postgres/init/01_create_tables.sql) | 10 tables for OLTP transaction store |
| K8s ClickHouse | [`k8s/storage-clickhouse.yaml`](k8s/storage-clickhouse.yaml) | Kubernetes statefulset for ClickHouse |
| K8s PostgreSQL | [`k8s/storage-postgres.yaml`](k8s/storage-postgres.yaml) | Kubernetes statefulset for PostgreSQL |
| K8s MinIO | [`k8s/storage-minio.yaml`](k8s/storage-minio.yaml) | Kubernetes deployment for MinIO object storage |
| K8s ChromaDB | [`k8s/storage-chromadb.yaml`](k8s/storage-chromadb.yaml) | Kubernetes deployment for ChromaDB vector store |
| K8s Redis | [`k8s/storage-redis.yaml`](k8s/storage-redis.yaml) | Kubernetes deployment for Redis cache/session store |
| K8s PVC | [`k8s/storage-pvc.yaml`](k8s/storage-pvc.yaml) | PersistentVolumeClaim for storage services |

### Observability Resources

| Component | File | Description |
|-----------|------|-------------|
| Health Probes | [`backend/health.py`](backend/health.py) | FastAPI health endpoints (live/ready/status) for all 5 storage services |
| Prometheus Metrics | [`monitoring/metrics.py`](monitoring/metrics.py) | 5 metric types per service: up gauge, latency histogram, connections, errors, disk usage |
| Observability Dashboard | [`monitoring/observability_dashboard.py`](monitoring/observability_dashboard.py) | Real-time Python dashboard with health scoring (50% storage weight) |
| Grafana Dashboard | [`monitoring/grafana/dashboards/storage-pod-stability.json`](monitoring/grafana/dashboards/storage-pod-stability.json) | Production Grafana dashboard with 5 service rows, 7 panels each |
| Recovery Runbook | [`docs/runbooks/storage-service-recovery.md`](docs/runbooks/storage-service-recovery.md) | 964-line comprehensive recovery runbook for all storage services |

### Test Resources

| Component | File | Description |
|-----------|------|-------------|
| Storage Monitoring Tests | [`tests/real/test_storage_monitoring.py`](tests/real/test_storage_monitoring.py) | 51 tests across 5 test classes — HealthEndpoints (12), PrometheusStorageMetrics (14), ObservabilityDashboardStorage (9), GrafanaDashboardJSON (11), StorageFallbackMechanisms (5) |

For full architecture details, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#9-storage-architecture-4-layer).

---

## Canonical Document References

- `STATUS.md` — Real-time component status labels (REAL / PARTIAL / CONCEPT)
- `TRUTH.md` — Immutable one-line project description
- `CONTRIBUTING.md` — Labeling rules and PR checklist
- `CONSTITUTION.md` — Dharma-chakra constitutional rules
- `docs/vision/README.md` — Long-term world-OS vision

---

*End of Master Blueprint. Update this file when any engine changes status or when missing pieces are completed.*
