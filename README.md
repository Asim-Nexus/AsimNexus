# AsimNexus — Constitutional Digital Platform Prototype

> **Version 0.7.0** — See [`CONSTITUTION.md`](CONSTITUTION.md) for governance rules.

**AsimNexus is a local-first, human-controlled, constitutional digital platform prototype** where AI operates within a constitution, human approval, and audit trail. It is **not** a World OS, not production-grade infrastructure, and not a commercial product.

---

## What It Is

A functional prototype demonstrating how AI can be constrained by:
- **A constitution** (ethical rules that AI cannot override)
- **Human approval** (3-step confirmation before critical actions)
- **Audit trail** (every decision logged and queryable)

Built with FastAPI backend, SQLite persistence, local LLM support, WebSocket mesh networking, and a React dashboard.

## What It Is NOT

- Not a "world-ready" operating system
- Not a "100% secure" system
- Not a supercomputer
- Not production-grade zero-knowledge proof system
- Not national government infrastructure
- Not a decentralized physical infrastructure network

---

## 7 Core Modules

| # | Module | What It Does |
|---|--------|-------------|
| 1 | **Universal Chat + Agent Runner** | Multi-LLM chat (local/cloud), agent loop with tool execution |
| 2 | **Dharma Veto** | Constitutional AI check — blocks unethical actions before execution |
| 3 | **Identity + HDT** | Digital identity creation/verification, Human Digital Twin profiles |
| 4 | **Finance/Wallet** | Multi-currency wallet, payments, escrow, exchange rates |
| 5 | **Mesh/Offline Sync** | Peer-to-peer mesh networking, offline operation queue, air-gap mode |
| 6 | **Government/Service Connector** | Digital identity, tax calculation, e-Residency, government service discovery |
| 7 | **Audit/Logging + Recovery** | Tool audit log, MCP audit, Level-3 confirmation, system healing |

---

## One-Screen Flow

```
Identity → What You Want → Dharma Check → Human Approval (3-step) → Execute → Audit
```

This is the core constitutional loop: every action passes through all gates before execution.

---

## Quick Start

```bash
pip install -r requirements.txt
python simple_backend.py
# API:      http://localhost:8000
# Docs:     http://localhost:8000/docs
# Health:   http://localhost:8000/health
```

Or use the launcher:
```bash
python PROTOTYPE_LAUNCHER.py
```

---

## Target Audiences

| Audience | What They See |
|----------|--------------|
| **Government** | Digital identity, tax filing, service requests, grievance tracking, policy compliance |
| **Company** | Contracts, hiring workflow, payments, customer support, automation |
| **Citizen** | Personal assistant, memory/schedule management, health tracking, secure data vault |

---

## Build Status

| Component | Status | Tests |
|-----------|--------|-------|
| FastAPI Backend | ✅ REAL | `tests/real/test_backend_api.py` |
| Dharma Veto | ✅ REAL | `tests/real/test_dharma_veto.py` |
| ΔT Engine | ✅ REAL | `tests/real/test_delta_t_engine.py` |
| Dreaming Engine | ✅ REAL | `tests/real/test_dreaming_engine.py` |
| AsimBrain | ✅ REAL | Wired to backend |
| PersonalOS Dashboard | ✅ REAL | Manual verified |
| Job Marketplace | ✅ REAL | Wired to backend |
| WebSocket P2P | ✅ REAL | `tests/prototype/` |
| ZKP | ⚠️ PARTIAL | Small-group math, not production |
| Mesh Routing | ⚠️ PARTIAL | Some components simulated |
| HDT | ⚠️ PARTIAL | No ZKP binding yet |
| Microkernel | 🔶 CONCEPT | Python simulation |
| National Gov Layer | 🔶 CONCEPT | Diagram only |

See [`CONSTITUTION.md`](CONSTITUTION.md) for full component classification and governance rules.

---

## Project Structure

```
backend/       → FastAPI backend (simple_backend.py)
frontend/      → React dashboard
docs/          → Constitution, architecture, operations
infra/docker/  → Docker Compose files
infra/k8s/     → Kubernetes manifests
tests/         → Test suites (unit, integration, real, prototype)
```

---

## License

Core engine: AGPLv3. Enterprise add-ons: Commercial. Government deployment: Custom 51/49 model.
See [`CONSTITUTION.md`](CONSTITUTION.md#5-who-owns-what) for full licensing details.
