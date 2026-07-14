# AsimNexus — Universal AI Operating System

**AsimNexus** is a world operating system with Human Digital Twin, local-first privacy, mesh networking, AI orchestration, digital economy, and constitutional governance — built for Nepal and the world.

## Status: RC1 Stabilization

All core systems are integrated, tested, and passing:

| System | Status | Tests |
|--------|--------|-------|
| **Mirror (Digital Twin)** | ✅ Complete | 88/88 real, 28/28 E2E |
| **Clone Consensus Voting** | ✅ Complete | 88/88 real, 28/28 E2E |
| **ZKP Privacy Layer** | ✅ Complete | 88/88 real, 28/28 E2E |
| **Dharma Veto Engine** | ✅ Complete | 88/88 real, 28/28 E2E |
| **Life Journey** | ✅ Complete | 88/88 real, 28/28 E2E |
| **Power Balance Constitution** | ✅ Complete | 88/88 real, 28/28 E2E |
| **Mesh P2P Networking** | ✅ Complete | 88/88 real, 28/28 E2E |
| **Offline Sync Engine** | ✅ Complete | 88/88 real, 28/28 E2E |
| **Multi-Mesh Router** | ✅ Complete | 88/88 real, 28/28 E2E |
| **RAG Knowledge Engine** | ✅ Complete | 470/470 integration |
| **API Response Standardization** | ✅ Complete | 211 usages across 18 route modules |
| **Integration Tests** | ✅ Complete | 470 passed, 4 skipped |
| **E2E Tests** | ✅ Complete | 28/28 passed |
| **Real Tests** | ✅ Complete | 88/88 passed |

## Architecture

```
AsimNexus/
├── app.py                    # FastAPI unified entry (684+ routes)
├── core/
│   ├── mirror/               # Digital Twin (consciousness, dreaming, lora)
│   ├── consensus/            # 15 Founder Clone voting (CloneConsensusVoting)
│   ├── dharma_chakra/        # Ethical veto engine (DharmaVetoEngine, SafetyVeto)
│   ├── economy/              # Hybrid economy (NexusCredits, Marketplace, TokenBridge)
│   ├── government/           # Government services (Identity, Tax, e-Residency)
│   ├── security/             # Security layer (ZKP, HSM, encryption, auth)
│   ├── mcp/                  # Model Context Protocol manager
│   ├── tools/                # Agent tool registry (20+ tools, 6 categories)
│   ├── healing/              # System health monitoring & auto-healing
│   ├── federation/           # Global federation protocol
│   ├── gateway/              # Capability registry, policy engine, audit ledger
│   ├── identity/             # User identity & DID system
│   ├── founder_clones/       # Founder clone system & autonomous agents
│   ├── world/                # World systems orchestrator
│   ├── universe/             # Personal universe management
│   ├── universal/            # Currency, legal, timezone, i18n stubs
│   ├── platform/             # Platform detection & management
│   ├── nepal/                # Nepal-specific integrations
│   ├── routing/              # Hybrid routing system
│   ├── mesh/                 # Mesh coordinator & clone sync
│   ├── network/              # P2P networking
│   ├── infrastructure/       # Global CDN, federated mesh
│   ├── knowledge_graph/      # Knowledge graph
│   ├── depin/                # DePIN (Decentralized Physical Infrastructure)
│   ├── dharma/               # Dharma modules (Nyaya, Panini, Pingala, etc.)
│   ├── life/                 # Life journey module
│   ├── constitution/         # Constitution module
│   ├── agent/                # Agent backward-compatibility shim
│   ├── agents/               # Base agent + sector agents
│   ├── sectors/              # Sector modules (banking, education, hospital, hotel)
│   ├── policy/               # Policy engine & human approval
│   ├── sync/                 # Sync engine
│   ├── api_endpoints/        # Economy & governance route registration
│   └── governance/           # Governance + country packs
├── routes/
│   ├── __init__.py           # register_routes() — wires all 18 route modules
│   ├── response.py           # Standardized API response helpers (ok, error, paginated)
│   ├── auth.py               # Authentication routes
│   ├── chat.py               # Chat & brain processing routes
│   ├── analytics.py          # Analytics, health, status, RAG, dreaming routes
│   └── ...                   # 14 more route modules
├── mesh/
│   ├── offline_sync_engine.py # CRDT-based offline sync
│   ├── multi_mesh_router.py   # Multi-mesh routing
│   ├── auto_discovery_v1.py   # P2P auto-discovery
│   └── ...
├── security/
│   ├── power_balance_constitution.py  # 51/49 constitutional rule
│   └── ...
├── agents/
│   ├── digital_twin.py        # Human Digital Twin
│   └── agent_matching.py      # Agent matching system
├── connectors/
│   ├── nepal/                 # Nepal government connectors
│   └── sector_connectors/     # 11 sector connectors (agriculture, tourism, banking, etc.)
├── governance/
│   └── country_packs/         # Country-specific policy packs (Nepal, India, US, EU)
├── knowledge/
│   └── rag_engine.py          # RAG engine (ChromaDB-backed)
├── tests/
│   ├── real/                  # 88 real integration tests
│   ├── e2e/                   # 28 end-to-end tests
│   ├── integration/           # 470 integration tests
│   ├── unit/                  # Unit tests
│   ├── performance/           # Performance tests
│   └── security/              # Security tests
├── infrastructure/            # AI infrastructure (NVIDIA, Modal)
├── monitoring/                # Observability, MLflow, Grafana
├── risk_management/           # Guardrails, compliance, detectors
├── compliance/                # VAPT process, accessibility compliance
├── database/                  # PostgreSQL migration
├── asim_tools/                # Tool registry, capability matrix, system tools
├── os_control/                # Sandboxed tool execution
├── data/                      # Data files
├── config/                    # Configuration
├── certs/                     # Certificates
├── docker/                    # Dockerfiles
└── frontend/                  # React dashboard
```

## Quick Start

```bash
# Backend
uvicorn app:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm start

# Run all real tests
pytest tests/real/ -v

# Run integration tests
pytest tests/integration/ -v

# Run E2E tests
pytest tests/e2e/ -v

# Run full test suite
pytest tests/real/ tests/e2e/ tests/integration/ -v
```

## Test Results

| Suite | Count | Status |
|-------|-------|--------|
| Real Tests | 88/88 | ✅ All passing |
| E2E Tests | 28/28 | ✅ All passing |
| Integration Tests | 470/470 (4 skipped) | ✅ All passing |

## API Response Format

All endpoints use standardized response format from [`routes/response.py`](routes/response.py):

```python
# Success
{"status": "ok", "data": {...}, "timestamp": "..."}

# Error
{"status": "error", "detail": "...", "code": 400, "timestamp": "..."}

# Paginated
{"status": "ok", "data": [...], "pagination": {"page": 1, "per_page": 20, "total": 100}, "timestamp": "..."}
```

## Key API Endpoints

- `POST /api/v1/auth/login` — JWT authentication
- `POST /api/v1/chat` — Chat with Asim Brain
- `POST /api/v1/rag/query` — Knowledge base query
- `GET /api/v1/operator/status` — Operator status
- `GET /api/system/complete` — Complete system status
- `GET /healthz` — Health check
- `GET /metrics` — Prometheus metrics

## Security

- **JWT Authentication**: Bearer token via `AuthMiddleware` ([`core/security/auth_middleware.py`](core/security/auth_middleware.py))
- **ZKP Privacy**: Zero-knowledge proofs via [`core/security_layer.py`](core/security_layer.py) `ZKPBridge`
- **HSM Integration**: Hardware Security Module support
- **Dharma Veto**: Ethical guardrails via [`core/dharma_chakra/veto_engine.py`](core/dharma_chakra/veto_engine.py)
- **Power Balance**: 51/49 constitutional rule via [`security/power_balance_constitution.py`](security/power_balance_constitution.py)

## License

Proprietary — All rights reserved.
