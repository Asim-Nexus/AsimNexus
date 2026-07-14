# AsimNexus Project Structure

> **Last updated:** 2026-07-03
> **Status:** LIVING — Update as the codebase evolves

---

## Overview

AsimNexus is organized as a **modular monolith** with clear separation of concerns. The `core/` package contains all primary implementations, while root-level packages serve as backward-compatible shims.

---

## Directory Map

```
AsimNexus/
├── app.py                          # FastAPI unified entry point
├── core/                           # PRIMARY: All core engine modules
│   ├── agents/                     #   AI agent system (health, finance, tax, etc.)
│   ├── compliance/                 #   Compliance engine (VAPT, accessibility)
│   ├── consensus/                  #   Clone consensus & voting
│   ├── dharma_chakra/              #   Ethics & governance (veto engine)
│   ├── federation/                 #   World federation protocols
│   ├── gateway/                    #   Unified LLM gateway & connectors
│   ├── governance/                 #   Jurisdiction router, cross-border, country packs
│   ├── knowledge/                  #   RAG engine, embeddings, vector store
│   ├── mesh/                       #   P2P mesh networking (DHT, CRDT, relay, hole-punching)
│   ├── mirror/                     #   Mirror module system
│   ├── nepal/                      #   Nepal-specific integrations
│   ├── orchestrator/               #   OS control, tool registry, planner
│   ├── risk_management/            #   Risk assessment & management
│   ├── security/                   #   ZKP, HSM, biometric, TPM, audit
│   ├── sync/                       #   Offline sync engine
│   ├── universal/                  #   Universal OS (currency, legal, i18n, timezone)
│   ├── agent_contract.py           #   Agent contract system
│   ├── api_endpoints.py            #   API endpoint definitions
│   ├── audit_bus.py                #   Audit event bus
│   ├── depin_bridge.py             #   DePIN bridge
│   ├── hardware_sync.py            #   Hardware sync
│   ├── life_journey.py             #   Digital Twin lifecycle
│   └── quantum_bridge.py           #   Quantum-safe bridge
├── agents/                         # SHIM → core/agents/
├── compliance/                     # SHIM → core/compliance/
├── connectors/                     # SHIM → core/gateway/
├── governance/                     # SHIM → core/governance/
├── knowledge/                      # SHIM → core/knowledge/
├── mesh/                           # SHIM → core/mesh/
├── os_control/                     # SHIM → core/orchestrator/
├── risk_management/                # SHIM → core/risk_management/
├── routes/                         # FastAPI route modules (29 files)
│   ├── analytics.py, auth.py, chat.py, clones.py, ...
│   ├── mesh.py, security.py, os_control.py, ...
│   └── response.py                 # Standardized response helpers
├── tests/                          # Test suite
│   ├── integration/                #   Integration tests
│   ├── real/                       #   Real hardware/integration tests
│   ├── regression/                 #   Regression tests
│   ├── prototype/                  #   Prototype/experimental tests
│   └── e2e/                        #   End-to-end tests
├── frontend/                       # React TypeScript frontend
│   ├── src/
│   │   ├── components/             #   React components
│   │   ├── api/                    #   API client
│   │   ├── services/               #   Frontend services
│   │   ├── hooks/                  #   Custom React hooks
│   │   ├── contexts/               #   React contexts
│   │   └── types/                  #   TypeScript types
│   ├── electron/                   #   Electron shell
│   └── public/                     #   Static assets
├── config/                         # Configuration files
├── database/                       # Database migrations & schemas
├── data/                           # Runtime data (gitignored)
├── docs/                           # Documentation
│   ├── api/                        #   API contract index
│   ├── architecture/               #   System architecture map
│   ├── operations/                 #   Operations guides
│   ├── runbooks/                   #   Incident response runbooks
│   └── releases/                   #   Release roadmaps
├── infrastructure/                 # Docker & deployment configs
├── monitoring/                     # Prometheus, Grafana configs
├── models/                         # ML models
├── plans/                          # Development plans & roadmaps
├── scripts/                        # Utility scripts
└── security/                       # SHIM → core/security/
```

---

## Key Architecture Decisions

### 1. Core-First Package Layout
All primary implementations live under `core/`. Root-level packages (`agents/`, `mesh/`, `connectors/`, etc.) are **backward-compatible shims** that re-export from `core/`. This allows:
- Clean imports: `from core.mesh import MeshNode`
- Backward compatibility: `from mesh import MeshNode` still works
- Gradual migration: Old imports continue to function

### 2. Modular Monolith
- **Single entry point**: `app.py` (FastAPI)
- **Route modules**: 29 files in `routes/`
- **Event-driven**: Modules communicate via `core/audit_bus.py`
- **Dependency injection**: Core domain isolated from external dependencies

### 3. Security Architecture
- **3-Level Human Confirmation**: Autonomous → OTP/PIN → HSM/Biometric
- **ZKP Privacy**: Zero-knowledge proofs for data privacy
- **Power Balance Constitution**: 51/49 human-AI governance
- **HSM Integration**: Hardware Security Module support

### 4. Mesh Networking
- **4 Mesh Types**: LOCAL, PERSONAL, CLOUD, PUBLIC
- **P2P Transport**: WebSocket, UDP, WebRTC
- **DHT**: Kademlia-based distributed hash table
- **CRDT**: Conflict-free replicated data types for offline sync
- **NAT Traversal**: STUN/TURN, hole-punching, relay

---

## Entity Counts (Nepal Context)
- Ministries: 18
- Provinces: 7
- Districts: 77
- Banks: 30
- ISPs: 20
- Universities: 12
- Hospitals: 12
- Hotels: 20
- Palikas: 753
- OS Tools: 47
- React Components: 52

---

## Quick Start

```bash
# Backend
uvicorn app:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm start
```

---

## Related Documents
- [`docs/architecture/SYSTEM_ARCHITECTURE_MAP.md`](architecture/SYSTEM_ARCHITECTURE_MAP.md) — Detailed architecture map
- [`docs/API_DOCS.md`](API_DOCS.md) — API documentation (634+ routes)
- [`docs/TECHNICAL_ARCHITECTURE_SPECIFICATION.md`](TECHNICAL_ARCHITECTURE_SPECIFICATION.md) — Technical architecture spec
- [`docs/Cyber_Security_Framework.md`](Cyber_Security_Framework.md) — Security framework
- [`docs/RELEASE_NOTES_RC2.md`](RELEASE_NOTES_RC2.md) — Release notes
