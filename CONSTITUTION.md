# AsimNexus Governance + Truth Constitution

> **Version:** 1.0  
> **Date:** 2026-05-30  
> **Status:** IMMUTABLE — Changes require 2/3 founder vote + Dharma Veto pass  
> **Override:** This document overrides any contradictory claim anywhere in the project.

---

## 1. Identity of the Project

**What AsimNexus Actually Is:**

> AsimNexus is a local-first, human-controlled, distributed-sovereignty operating system prototype with real backend, real policy engine, real local LLM, real dashboard, and real WebSocket mesh routing, but ZKP uses small-group demo math (not production SNARKs), mesh has no NAT traversal, and microkernel/national governance layers remain conceptual.

**What AsimNexus Is NOT:**
- Not a "world-ready" operating system
- Not a "100% secure" system
- Not a "supercomputer"
- Not a "production-grade" zero-knowledge proof system
- Not a "national government infrastructure"
- Not a "decentralized physical infrastructure network"

**Every document, README, pitch, and code comment must derive from this identity statement.**

---

## 2. What Is REAL Now

| Module | Evidence | Tests |
|--------|----------|-------|
| FastAPI Backend (`simple_backend.py`) | 75+ endpoints, JWT auth, SQLite persistence | `tests/real/test_backend_api.py` |
| Dharma Veto (`core/dharma/dharma_veto.py`) | 5-layer pattern blocker, audit log, override system | `tests/real/test_dharma_veto.py` |
| ΔT Engine (`core/dharma/delta_t_engine.py`) | Gini coefficient, PoS reports, attenuation math | `tests/real/test_delta_t_engine.py` |
| Dreaming Engine (`core/dreaming/dreaming_engine.py`) | Async background loop, memory consolidation, SQLite | `tests/real/test_dreaming_engine.py` |
| AsimBrain (`core/asim_brain.py`) | Local GGUF loading, clone routing, Dharma inline check | Wired to backend |
| PersonalOS Dashboard (`frontend/react/src/components/os/PersonalOS.jsx`) | React dashboard fetching live API data | Manual verified |
| Job Marketplace (`core/economy/job_marketplace.py`) | Escrow simulation, Dharma gate, ratings | Wired to backend |
| WebSocket P2P (`core/mesh/p2p_node.py`) | Real `websockets` library, peer-to-peer messages | `tests/prototype/` |
| Mesh Routing v2 (`mesh/mesh_routing_agent_v2.py`) | Tasks sent over WebSocket, load balancing | `tests/prototype/test_mesh_v2.py` |

**Rule:** REAL components may only be modified if:
1. Regression tests pass
2. Dharma Veto audit shows no new harmful patterns
3. Change is documented in `CHANGELOG.md`

---

## 3. What Is PARTIAL

| Module | What Works | What's Missing |
|--------|-----------|----------------|
| ZKP v2 (`core/security/bulletproof_zkp.py`) | Pedersen commitments, Schnorr proofs, modular arithmetic | Small 256-bit group (not production), not zk-SNARKs |
| Mesh Routing v1 (`mesh/mesh_routing_agent.py`) | Topology logic, fallback paths, load balancing | `_execute_on_device` uses `asyncio.sleep` (simulated) |
| 15 Clone Configs (`core/founder_clones/world_clones.py`) | Role definitions, system prompts, capabilities | No ensemble voting, no real consensus |
| HDT (`core/hdt/human_digital_twin.py`) | Data models, skill/preferences storage | No ZKP binding, no mesh broadcast |
| Level-3 Confirmation (`core/security/level3_confirmation.py`) | State machine, 3-check framework | No biometric gate, no hardware integration |

**Rule:** PARTIAL components must have:
1. `STATUS: PARTIAL — <what works> ; <what's missing>` header
2. Clear path to REAL documented in code
3. Tests in `tests/prototype/`

---

## 4. What Is CONCEPT

| Module | Status |
|--------|--------|
| Microkernel (`core/kernel/microkernel.py`) | Python simulation of seL4 concepts |
| DePIN Bridge (`core/depin/depin_bridge.py`) | Simulated reward rates, no real network |
| Sovereign Kernel (`core/sovereign_kernel.py`) | Resource management framework, not a real OS kernel |
| National/Government Layer | Diagram only, no code |
| TPM/Hardware Security | Mentioned, zero code |

**Rule:** CONCEPT components must:
1. Live in `docs/vision/` or `core/concept/`
2. Have `STATUS: CONCEPT` header
3. Never be presented as "implemented"
4. Never be wired to backend API

---

## 5. Who Owns What

### Intellectual Property
- **Core Engine (backend, Dharma, ΔT, Dreaming):** Open-source, AGPLv3
- **Founder Clone System:** Open-source, AGPLv3
- **Dashboard/Frontend:** Open-source, AGPLv3
- **Mesh Protocol:** Open-source, AGPLv3
- **Commercial Enterprise Layer (future):** Proprietary, separate license

### Code Ownership
| Layer | Owner | License |
|-------|-------|---------|
| Core kernel | AsimNexus Foundation | AGPLv3 |
| Dharma engine | AsimNexus Foundation | AGPLv3 |
| Founder clones | AsimNexus Foundation | AGPLv3 |
| Enterprise add-ons | AsimNexus Pvt. Ltd. | Commercial |
| Government deployment | Joint (51/49) | Custom |

### 51/49 Public-Private Model
- **51% Public Interest:** Government/foundation controls critical kernel changes, safety audits, Dharma policy updates
- **49% Private Enterprise:** Company controls commercial licensing, enterprise features, revenue generation
- **Critical changes (kernel, Dharma, ZKP):** Require 51% public approval
- **Commercial features (enterprise dashboard, SLA, support):** 49% private decision

---

## 6. Who Can Change What

### Change Control Matrix

| Component | Who Can Approve | Audit Required |
|-----------|----------------|--------------|
| Dharma Veto rules | 2/3 founder vote + Dharma audit | Yes |
| ΔT Engine parameters | 2/3 founder vote | Yes |
| Backend API (new endpoints) | Technical lead + Dharma audit | Yes |
| REAL → PARTIAL downgrade | FORBIDDEN | — |
| PARTIAL → REAL promotion | 2/3 founder vote + tests pass | Yes |
| CONCEPT → PARTIAL | Any founder + documentation | No |
| Microkernel (CONCEPT) | Founder CTO only | No |
| Licensing changes | Foundation board (51%) + Pvt Ltd (49%) | Legal review |

### Forbidden Changes (Never Override Without Constitutional Amendment)
1. Dharma Veto may never be disabled globally
2. Human supremacy clause may never be removed
3. AGPLv3 core may never be closed-source
4. 51% public interest may never drop below 50%
5. `TRUTH.md` and `CONSTITUTION.md` may never be silently modified

---

## 7. What Must Never Be Overridden

### Immutable Documents
- `CONSTITUTION.md` — This document
- `TRUTH.md` — Honest project description
- `STATUS.md` — Component status table

**Amendment Process:**
1. Propose change in `docs/vision/constitutional_amendments/`
2. 2/3 founder vote
3. Dharma Veto audit (no harmful patterns)
4. Update version number and date
5. Record in `CHANGELOG.md`

### Immutable Principles
1. **Human Control First:** Every automated decision can be overridden by a human
2. **Local-First Privacy:** Personal data never leaves device without explicit consent
3. **Anti-Concentration:** No single node may exceed 7% network influence (ΔT rule)
4. **Open Core:** Core engine always open-source
5. **Honest Labeling:** Every file must have STATUS header, no exceptions

---

## 8. Release Policy

### What "Production Release" Means
Before any version may be called "production":
1. All REAL components have passing tests
2. Dharma Veto audit: zero critical patterns allowed
3. ΔT check: Gini < 0.2, no violations
4. Security review: no known CVEs in dependencies
5. Documentation: `STATUS.md` updated, `TRUTH.md` accurate
6. Legal: license review complete

### Version Numbering
- `x.y.z` where:
  - `x` = Constitutional change (requires amendment)
  - `y` = REAL component added or upgraded
  - `z` = Bug fix or PARTIAL improvement

### Current Version: 0.7.0
- 0 = Pre-constitutional (not yet v1.0)
- 7 = 7 REAL modules (backend, Dharma, ΔT, Dreaming, Brain, Dashboard, Mesh)
- 0 = No patch releases yet

---

## 9. Audit and Verification

### Automated Checks (CI)
- `pytest tests/real/` must pass
- `tools/check_status_labels.py` must pass (no missing STATUS headers)
- No forbidden words in new documentation
- `TRUTH.md` not contradicted by new claims

### Manual Review (Per Release)
- Dharma policy review
- ΔT parameter review
- Security dependency audit
- Legal license compliance

---

## 10. Enforcement

### CI Rejection Rules
PR will be automatically rejected if:
1. Adds .py file without STATUS header
2. Claims REAL without `tests/real/` tests
3. Uses forbidden words (`world-ready`, `100% secure`, etc.)
4. Modifies `CONSTITUTION.md` or `TRUTH.md` without amendment process
5. Downgrades REAL component without constitutional vote

### Founder Accountability
Any founder who:
- Presents PARTIAL as REAL → Must revert + update STATUS + apology in CHANGELOG
- Presents CONCEPT as PARTIAL → Must move to `docs/vision/` + update STATUS
- Removes Dharma/human-supremacy checks → Immediate code revert + review

---

## Signatories

| Founder | Role | Date | Commit Hash |
|---------|------|------|-------------|
| Asim (CEO) | Founder-1 | 2026-05-30 | `TBD` |
| [CTO Name] | Founder-2 | 2026-05-30 | `TBD` |
| [CFO Name] | Founder-3 | 2026-05-30 | `TBD` |

---

> *"Vision-wise धेरै अगाडि छ। Core-wise partly real छ। World-scale-wise अझै incomplete छ। यो weakness होइन, strength हो।"*
