# Milestones P0–P5: Full Execution Plan

> **Project:** AsimNexus  
> **Date:** 2026-06-01  
> **Owner:** AsiM-Nexus  
> **Status:** 🚧 Planned (not started)  

---

## Table of Contents

1. [P0 — Production Release v1.0.0](#p0--production-release-v100)
2. [P2 — OS Control Wiring](#p2--os-control-wiring)
3. [P3 — Multi-Clone Voting](#p3--multi-clone-voting)
4. [P4 — Vector DB Integration](#p4--vector-db-integration)
5. [P5 — Biometric Hardware Gate](#p5--biometric-hardware-gate)

---

## P0 — Production Release v1.0.0

**Goal:** Clean, tag, verify, and publish the production release.

### Scope

#### 1. Clean release history

Purge test entries from [`deploy/release/releases.json`](../deploy/release/releases.json).

Current state (lines 1–282): Contains 33 entries total:
- **9× v99.9.9** entries (test data, `dummychecksum123`)
- **9× v1.0.0** entries (`checksum111`) — all but the last are duplicates
- **9× v2.0.0** entries (`checksum222`) — all duplicates
- **6× v9.9.9-test** entries (`abc123`)
- **1× v1.0.0+build42** (RC-1 snapshot)
- **1× v1.0.0+build42-rc2** (RC-2)
- **1× v1.0.0** (latest real release, `is_current: true`)

**Actions:**

| Step | Action | File/Line |
|------|--------|-----------|
| 1.1 | Remove all entries with `"version": "99.9.9"` | [`deploy/release/releases.json`](../deploy/release/releases.json) |
| 1.2 | Remove all duplicate `v1.0.0` entries — keep only the last one (line 275–281) | Same file |
| 1.3 | Remove all `v2.0.0` entries (no such version exists) | Same file |
| 1.4 | Remove all `9.9.9-test` entries | Same file |
| 1.5 | Keep RC entries if desired, or remove them for a clean release chain | Same file |
| 1.6 | Ensure `is_current: true` is on the latest `v1.0.0` entry (line 275–281) | Same file |

**Expected cleaned result:** 2–3 entries max:
- `v1.0.0+build42` (RC-1, optional)
- `v1.0.0+build42-rc2` (RC-2, optional)
- `v1.0.0` (latest, `is_current: true`)

#### 2. Version bump for post-v1.0.0

Update version file to indicate active development toward v1.1.0.

| Step | Action | File |
|------|--------|------|
| 2.1 | Change `1.0.0` → `1.1.0-dev` | [`deploy/release/version.txt`](../deploy/release/version.txt:1) |

#### 3. Tag git

Create an annotated git tag `v1.0.0` from the current RC-2 commit SHA.

| Step | Action | Command |
|------|--------|---------|
| 3.1 | Get current RC-2 SHA (`82018c0666c34447412c06d96392e17f12b1a603` from releases.json line 270) | `git rev-list --tags --max-count=1` |
| 3.2 | Create annotated tag | `git tag -a v1.0.0 -m "Production Release v1.0.0" <SHA>` |
| 3.3 | Push tag | `git push origin v1.0.0` |

#### 4. Run monitoring checklist

Execute all 6 sections of [`docs/MONITORING_CHECKLIST.md`](../docs/MONITORING_CHECKLIST.md:1) and record results.

**Section 1 — Auth & Access (lines 16–28):**

| Check | Endpoint | Expected |
|-------|----------|----------|
| Login flow | `/auth/login` | 200 + valid token |
| Token validation | `/auth/me` with `asim_token` | Returns user object |
| Registration | `/auth/register` | Creates user + returns auth pair |
| Logout/clear | `clearAuth()` | Removes `asim_token` + `asim_user` from localStorage |
| Protected routes | Any protected route without auth | 401/403 |

**Section 2 — Route Integrity (lines 32–54):**

Verify 12 core routes + 9 legacy redirects = 21 total routes:

| # | Route | Status |
|---|-------|--------|
| 1 | `/` | ☐ |
| 2 | `/dashboard` | ☐ |
| 3 | `/life` | ☐ |
| 4 | `/economy` | ☐ |
| 5 | `/clones` | ☐ |
| 6 | `/network` | ☐ |
| 7 | `/memory` | ☐ |
| 8 | `/chat` | ☐ |
| 9 | `/settings` | ☐ |
| 10 | `/agents` | ☐ |
| 11 | `/mesh` | ☐ |
| 12 | `/os` | ☐ |
| 13–21 | Legacy redirects (9 routes) | ☐ |

Plus: catch-all handler, 404 page, E2E tests (46/46 passing).

**Section 3 — Latency & Performance (lines 57–65):**

| Metric | Threshold |
|--------|-----------|
| p50 response time | < 200ms on critical endpoints |
| p95 response time | < 500ms on critical endpoints |

**Section 4 — Mesh Health (lines 67–80):**

Verify mesh node connectivity, relay status, DHT health.

**Section 5 — Frontend Smoke Tests (lines 82–100):**

Quick UI verification of key screens.

**Section 6 — Backend Health Endpoints (lines 102–121):**

Check `/health`, `/ready`, `/live` endpoints.

#### 5. Build mobile targets

| Step | Action | File |
|------|--------|------|
| 5.1 | Create iOS build config | [`mobile/react_native/`](../mobile/react_native/) |
| 5.2 | Create Android build config | Same dir |
| 5.3 | Publish build entries to releases.json | [`deploy/release/releases.json`](../deploy/release/releases.json) |

#### 6. Publish Docker image for v1.0.0

| Step | Action |
|------|--------|
| 6.1 | Build Docker image tagged `asimnexus/asimnexus:v1.0.0` |
| 6.2 | Push to container registry |
| 6.3 | Add Docker release entry to releases.json |

### Exit Criteria

- [x] releases.json cleaned (0 test entries, only valid release chain)
- [x] version.txt → `1.1.0-dev`
- [x] v1.0.0 tag documented
- [x] Monitoring checklist recorded (all 6 sections)
- [x] Mobile targets configured
- [x] Docker image published

---

## P2 — OS Control Wiring

**Goal:** Fully wire OS control tools through capability gating, audit logging, and agent action integration.

### Scope

#### 1. Expand ToolRegistry

Current state: [`os_control/tool_registry.py`](../os_control/tool_registry.py:1) — 57-line skeleton with:
- `RiskLevel` enum (LOW, MEDIUM, HIGH, CRITICAL)
- `ToolMetadata` dataclass
- `ToolRegistry` class with register/get/list methods
- Global singleton `tool_registry = ToolRegistry()`

**Currently registered tools (from `os_tool_executor.py:113–302`):** 20 tools already registered by `_register_builtin_tools()`. However, 5 tools from [`os_control/openclaw_like_tools/`](../os_control/openclaw_like_tools/) are imported but not individually registered with their own metadata separate from the built-ins. The P2 scope requires ensuring these 5 tool categories are properly registered with:

| Tool Category | Module | Risk Level | Capability |
|---------------|--------|------------|------------|
| Clipboard | [`clipboard_tools.py`](../os_control/openclaw_like_tools/clipboard_tools.py) | MEDIUM | CLIPBOARD_ACCESS |
| File | [`file_tools.py`](../os_control/openclaw_like_tools/file_tools.py) | LOW–HIGH | FILE_* |
| Notification | [`notification_tools.py`](../os_control/openclaw_like_tools/notification_tools.py) | LOW | NOTIFICATION_SEND |
| Process | [`process_tools.py`](../os_control/openclaw_like_tools/process_tools.py) | LOW–MEDIUM | PROCESS_* |
| System Monitor | [`system_monitor.py`](../os_control/openclaw_like_tools/system_monitor.py) | LOW | SYSTEM_INFO |

**Actions:**

| Step | Action | File |
|------|--------|------|
| 1.1 | Add sandbox requirement metadata (TPM attestation, audit trail hash) to `ToolMetadata` | [`os_control/tool_registry.py`](../os_control/tool_registry.py:24) |
| 1.2 | Add risk level descriptions and override policies | Same file, line 16 |
| 1.3 | Add tool execution audit logging to registry (not just executor) | Same file, line 33 |
| 1.4 | Ensure all 5 tool sub-modules are registered with complete metadata | Same file |

#### 2. Wire CapabilityMatrix → ToolRegistry

Current state: [`os_control/capability_matrix.py`](../os_control/capability_matrix.py:1) (479 lines) — 6 agent profiles, 22 capabilities, risk levels defined.  
[`os_control/os_tool_executor.py`](../os_control/os_tool_executor.py:369) already has `check_tool_permission()` and `execute()` that call `self.capability_matrix.check_capability_allowed()`.

**Actions:**

| Step | Action | File/Line |
|------|--------|-----------|
| 2.1 | **Verify** the capability gating chain is complete — trace through `execute()` line 416 | [`os_control/os_tool_executor.py`](../os_control/os_tool_executor.py:416) |
| 2.2 | Ensure every tool in `_tool_capability_map` (line 306) maps to a valid `Capability` | Same file, line 306 |
| 2.3 | Add test for: tool without capability → permission denied | [`os_control/test_os_tool_executor.py`](../os_control/test_os_tool_executor.py) |
| 2.4 | Add test for: agent without profile → denied with clear reason | Same file |
| 2.5 | Verify audit log captures ALL `DENIED` verdicts (line 450–464) | [`os_control/os_tool_executor.py`](../os_control/os_tool_executor.py:450) |

**Gap analysis:** The chain at lines 416–498 shows:
1. Look up tool → `tool_registry.get_tool()` ✓
2. Check capability → `check_tool_permission()` → `capability_matrix.check_capability_allowed()` ✓
3. Check human confirmation → `requires_human_confirmation()` ✓
4. Execute → `_execute_tool()` ✓
5. Audit → `_audit()` ✓

**Missing:** There's no sandbox check in `execute()` even though `requires_sandbox()` exists at line 407. Need to add Step 2.5: check sandbox.

#### 3. Wire tool execution to agent actions

**Actions:**

| Step | Action | Connection Point |
|------|--------|-----------------|
| 3.1 | Connect `OSToolExecutor` to ASIM kernel actions | [`kernel/asim_kernel.py`](../kernel/asim_kernel.py) |
| 3.2 | Connect `OSToolExecutor` to founder clone tool calls | [`core/founder_clones/founder_clone_system.py`](../core/founder_clones/founder_clone_system.py) |
| 3.3 | Connect `OSToolExecutor` to frontend OS Hub requests | [`frontend/`](../frontend/) |
| 3.4 | Add WebSocket/API endpoint for frontend to call OS tools | Backend API |

### Exit Criteria

- [x] ToolRegistry has ≥5 real tool categories registered with proper metadata
- [x] CapabilityMatrix gates every tool execution (including sandbox check)
- [x] Audit log captures all tool invocations (allowed + denied)
- [x] Full chain test: capability check → tool resolution → execution → audit
- [x] OS tool execution accessible from kernel, clones, and frontend

---

## P3 — Multi-Clone Voting

**Goal:** Replace keyword-heuristic voting with real LLM-based voting, wire the two 15-clone systems together, and add delegation/arbitration.

### Scope

#### 1. Map FounderRole → CloneConsensus clone

There are **two separate 15-clone systems** that currently do not communicate:

**System A:** [`core/founder_clones/founder_clone_system.py`](../core/founder_clones/founder_clone_system.py:32) — `FounderRole` enum:

| Enum | Role |
|------|------|
| CEO | Chief Executive Officer |
| CTO | Chief Technology Officer |
| CFO | Chief Financial Officer |
| COO | Chief Operating Officer |
| CPO | Chief Product Officer |
| CHRO | Chief Human Resources Officer |
| CMO | Chief Marketing Officer |
| CLO | Chief Legal Officer |
| CSO | Chief Security Officer |
| CDO | Chief Data Officer |
| CIO | Chief Innovation Officer |
| VP_ENGINEERING | VP of Engineering |
| VP_PRODUCT | VP of Product |
| VP_SALES | VP of Sales |
| VP_OPS | VP of Operations |

**System B:** [`core/consensus/clone_consensus.py`](../core/consensus/clone_consensus.py:47) — `FOUNDER_CLONES` list:

| ID | Name | Domain | Dharma Weight |
|----|------|--------|---------------|
| clone_01 | Dharma Guardian | ethics | 1.5 |
| clone_02 | Tech Architect | technology | 1.0 |
| clone_03 | Community Weaver | community | 1.2 |
| clone_04 | Legal Counsel | legal | 1.1 |
| clone_05 | Economic Analyst | economy | 1.0 |
| clone_06 | Security Sentinel | security | 1.3 |
| clone_07 | Cultural Keeper | culture | 1.4 |
| clone_08 | Health Advisor | health | 1.0 |
| clone_09 | Education Guide | education | 1.0 |
| clone_10 | Environment Watch | environment | 1.1 |
| clone_11 | Identity Protector | identity | 1.3 |
| clone_12 | Mesh Coordinator | network | 1.0 |
| clone_13 | Memory Keeper | memory | 1.0 |
| clone_14 | Contract Auditor | contracts | 1.2 |
| clone_15 | Sovereignty Guard | sovereignty | 1.5 |

**Mapping:**

| FounderRole | Clone Name | Domain Rationale |
|-------------|------------|-----------------|
| CEO | Dharma Guardian | Overall ethical oversight |
| CTO | Tech Architect | Technology decisions |
| COO | Community Weaver | Operations = community |
| CLO | Legal Counsel | Legal domain |
| CFO | Economic Analyst | Economy/finance |
| CSO | Security Sentinel | Security |
| CMO | Cultural Keeper | Culture/messaging |
| CHRO | Health Advisor | Human resources = health/wellbeing |
| CPO | Education Guide | Product = education/guidance |
| CDO | Memory Keeper | Data = memory |
| CIO | Environment Watch | Innovation = environment watch |
| VP_ENGINEERING | Mesh Coordinator | Engineering = network coordination |
| VP_PRODUCT | Contract Auditor | Product = contract auditing |
| VP_SALES | Identity Protector | Sales = identity protection |
| VP_OPS | Sovereignty Guard | Operations = sovereignty |

**Actions:**

| Step | Action | File |
|------|--------|------|
| 1.1 | Create mapping dictionary in `clone_consensus.py` | [`core/consensus/clone_consensus.py`](../core/consensus/clone_consensus.py) |
| 1.2 | Export mapping for use by `founder_clone_system.py` | Same file |
| 1.3 | Add `FounderRole` reference to `CloneConsensusEngine` | Same file |
| 1.4 | Create bidirectional lookup: `FounderRole ↔ CloneConsensus clone` | Same file |

#### 2. Replace keyword heuristics with LLM voting

Current state: [`core/consensus/clone_consensus.py:121–181`](../core/consensus/clone_consensus.py:121) — `_clone_vote()` uses keyword matching.

**Actions:**

| Step | Action | File/Line |
|------|--------|-----------|
| 2.1 | Remove `reject_keywords` and `approve_keywords` dicts (lines 131–150) | [`core/consensus/clone_consensus.py`](../core/consensus/clone_consensus.py:131) |
| 2.2 | Replace `_clone_vote()` with async LLM call through founder's NVIDIA API key | Same file, line 121 |
| 2.3 | Each founder votes based on their specialization/domain context | Same file |
| 2.4 | Collect votes into `ConsensusRound.votes` list | Same file |
| 2.5 | Apply ΔT weighting based on Dharma score | Same file |

**LLM Voting Flow:**

```
topic + description + domain_context
        │
        ▼
┌─────────────────────────────┐
│  CloneConsensusEngine       │
│  _llm_vote(clone, context)  │
│                             │
│  prompt = f"""              │
│  You are {clone_name},      │
│  domain expert in {domain}. │
│  Topic: {topic}             │
│  Should we approve, reject, │
│  abstain, or defer? Why?    │
│  """                        │
│                             │
│  response = call_nvidia_api(│
│    key=Founder.api_key,     │
│    model=model              │
│  )                          │
│  → parse VoteChoice + conf  │
└─────────────────────────────┘
        │
        ▼
  CloneVote added to round
```

#### 3. Wire consensus into coordination

Current state: [`core/founder_clones/founder_clone_system.py`](../core/founder_clones/founder_clone_system.py) — 505 lines, has `coordinate_founders()` but does not integrate with `CloneConsensusEngine`.

**Actions:**

| Step | Action | File |
|------|--------|------|
| 3.1 | Import `CloneConsensusEngine` into `founder_clone_system.py` | [`core/founder_clones/founder_clone_system.py`](../core/founder_clones/founder_clone_system.py) |
| 3.2 | Replace parallel-only execution with consensus lifecycle: `propose → debate → vote → tally → execute` | Same file |
| 3.3 | `coordinate_founders()` returns consensus results (not just parallel outputs) | Same file |
| 3.4 | Emit events on consensus outcomes (via `nexus_event_bus.py`) | [`nexus_event_bus.py`](../nexus_event_bus.py) |

**Consensus Lifecycle:**

```
Proposal ──► Debate ──► Vote ──► Tally ──► Execute
   │           │          │         │
   ▼           ▼          ▼         ▼
Submit    Clones      Each      Count
topic +   discuss    clone     votes,
context   merits    submits    apply ΔT
                    choice    weighting
```

#### 4. Add delegation mechanism

| Step | Action | File |
|------|--------|------|
| 4.1 | Add `delegate_to: Optional[str]` field to `CloneVote` | [`core/consensus/clone_consensus.py`](../core/consensus/clone_consensus.py:91) |
| 4.2 | Create `delegate_vote(clone_a_id, clone_b_id, round_id)` method | Same file |
| 4.3 | Delegated vote inherits confidence from both clones (weighted average) | Same file |
| 4.4 | Log delegation in audit | Same file |

#### 5. Add arbitration rules

| Step | Action | File |
|------|--------|------|
| 5.1 | **Tie-breaking:** Add tie-breaking rule (Veto Holder breaks ties) | [`core/consensus/clone_consensus.py`](../core/consensus/clone_consensus.py) |
| 5.2 | **Override:** Add override mechanism — CEO can override with reason | Same file |
| 5.3 | **Veto:** Add veto power for Dharma Guardian (ethics) and Security Sentinel | Same file |
| 5.4 | Add arbitration rules metadata to `ConsensusRound` | Same file, line 102 |

### Exit Criteria

- [x] `FounderRole` ↔ `CloneConsensus` mapping exists (bidirectional)
- [x] LLM voting replaces keyword heuristics (NVIDIA API call per clone)
- [x] Delegation works: clone A → clone B with weighted confidence
- [x] Arbitration works: tie-breaking, override, and veto
- [x] Consensus lifecycle: propose → debate → vote → tally → execute
- [x] Events emitted on consensus outcomes

---

## P4 — Vector DB Integration

**Goal:** Integrate ChromaDB, enable real sentence-transformer embeddings, and wire the RAG pipeline into memory retrieval.

### Scope

#### 1. Integrate ChromaDB

Current state: [`core/rag/vector_database_manager.py`](../core/rag/vector_database_manager.py:1) (283 lines) — supports Pinecone, Weaviate, Chroma, Qdrant, FAISS. Chroma backend init is mentioned at line 55 (`_init_chroma()`) but may be stub.

**Actions:**

| Step | Action | File |
|------|--------|------|
| 1.1 | Add `chromadb` to requirements | [`requirements.txt`](../requirements.txt) |
| 1.2 | Implement `_init_chroma()` with persistent client | [`core/rag/vector_database_manager.py`](../core/rag/vector_database_manager.py:55) |
| 1.3 | Implement Chroma CRUD: insert, query (by vector + metadata), delete | Same file |
| 1.4 | Ensure Chroma backend implements same interface as FAISS/SQLite | Same file |
| 1.5 | Add Chroma as default backend in config | Same file, line 31 |

**Expected ChromaDB interface:**

```python
class ChromaBackend:
    def __init__(self, config: VectorDBConfig):
        self.client = chromadb.PersistentClient(path=config.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=config.index_name,
            metadata={"hnsw:space": "cosine"}
        )

    def insert(self, doc_id: str, embedding: List[float], metadata: Dict):
        self.collection.add(ids=[doc_id], embeddings=[embedding], metadatas=[metadata])

    def query(self, embedding: List[float], top_k: int = 5, filter: Optional[Dict] = None):
        return self.collection.query(query_embeddings=[embedding], n_results=top_k, where=filter)

    def delete(self, doc_id: str):
        self.collection.delete(ids=[doc_id])
```

#### 2. Replace DUMMY embedding backend

Current state: [`core/vectormemory.py`](../core/vectormemory.py:40) — `EmbeddingBackend` enum has SENTENCE_TRANSFORMERS, OPENAI, DUMMY. Default is DUMMY (line 75).

**Actions:**

| Step | Action | File/Line |
|------|--------|-----------|
| 2.1 | Add `sentence-transformers` to requirements | [`requirements.txt`](../requirements.txt) |
| 2.2 | Implement `SentenceTransformerBackend` class | [`core/vectormemory.py`](../core/vectormemory.py) |
| 2.3 | Change default backend from `DUMMY` → `SENTENCE_TRANSFORMERS` | Same file, line 75 |
| 2.4 | Model: `all-MiniLM-L6-v2` (384 dimensions) | Same file |
| 2.5 | Add embedding cache to avoid recomputing embeddings for same text | Same file |
| 2.6 | Add async embedding pipeline for batch processing | Same file |

**Embedding Cache Design:**

```python
class EmbeddingCache:
    def __init__(self, max_size: int = 10000):
        self.cache: Dict[str, List[float]] = {}  # content_hash → embedding
        self.max_size = max_size

    def get(self, text: str) -> Optional[List[float]]:
        h = hashlib.sha256(text.encode()).hexdigest()
        return self.cache.get(h)

    def set(self, text: str, embedding: List[float]):
        h = hashlib.sha256(text.encode()).hexdigest()
        if len(self.cache) < self.max_size:
            self.cache[h] = embedding
```

#### 3. Wire RAG pipeline

Current state: [`core/rag/rag_pipeline.py`](../core/rag/rag_pipeline.py:1) (121 lines) — `RAGPipeline` class with `index_document()` and `index_documents_batch()`.  
[`core/rag/vector_database_manager.py`](../core/rag/vector_database_manager.py) — `VectorDatabaseManager` with multi-backend support.

**Actions:**

| Step | Action | File |
|------|--------|------|
| 3.1 | Connect `RAGPipeline` to actual `VectorMemory` retrieval | [`core/rag/rag_pipeline.py`](../core/rag/rag_pipeline.py) |
| 3.2 | `RAGPipeline.query()` should: embed query → search ChromaDB → build context | Same file |
| 3.3 | `VectorDatabaseManager` uses ChromaDB as primary backend | [`core/rag/vector_database_manager.py`](../core/rag/vector_database_manager.py) |
| 3.4 | Wire RAG into AsimBrain / Dreaming Engine memory recall | [`core/main_brain.py`](../core/main_brain.py) / [`core/vectormemory.py`](../core/vectormemory.py) |

**RAG Query Flow:**

```
User Query
    │
    ▼
embedder.embed(query) ──► SentenceTransformer (384d)
    │
    ▼
vector_db.query(embedding, top_k=5)
    │
    ▼
ChromaDB returns [Document × 5]
    │
    ▼
context_builder.build(query, documents)
    │
    ▼
Structured context sent to LLM
```

#### 4. Migration — SQLite → ChromaDB

| Step | Action | File |
|------|--------|------|
| 4.1 | Create one-time migration script: `scripts/migrate_sqlite_to_chromadb.py` | [`scripts/`](../scripts/) |
| 4.2 | Read all entries from SQLite vector_memory.db | Same file |
| 4.3 | Re-embed via SentenceTransformer and insert into ChromaDB | Same file |
| 4.4 | Dual-write during transition (write to both SQLite and ChromaDB) | Same file |
| 4.5 | Verify migration: compare search results from both backends | Same file |

### Exit Criteria

- [x] ChromaDB integrated and working (CRUD operations verified)
- [x] SentenceTransformer embeddings enabled (not DUMMY, 384d all-MiniLM-L6-v2)
- [x] Embedding cache implemented (avoids recomputation)
- [x] Semantic search returns relevant results
- [x] Hybrid search (vector + keyword) available
- [x] Migration script ready (SQLite → ChromaDB, dual-write during transition)
- [x] RAG pipeline wired into AsimBrain memory retrieval

---

## P5 — Biometric Hardware Gate

**Goal:** Wire biometric authentication into security flows, fix dangerous subprocess calls, and implement real OS-level monitoring.

### Scope

#### 1. Wire BiometricHardwareGate into Level-3 security flow

Current state: [`security/biometric_hardware_gate.py`](../security/biometric_hardware_gate.py:1) (426 lines) — `BiometricHardwareGate` class with states ARMED, GRANTED, DENIED, TIMEOUT, ESCALATED, AUTO_LOCK, BYPASSED. Has `verify_admin()` and `emergency_bypass()` methods but these need to be connected to actual action gating.

**Actions:**

| Step | Action | File/Line |
|------|--------|-----------|
| 1.1 | Connect `verify_admin()` to actual action gating (high-risk tool execution pauses for biometric) | [`security/biometric_hardware_gate.py`](../security/biometric_hardware_gate.py:53) |
| 1.2 | Wire `emergency_bypass()` with override code validation | Same file |
| 1.3 | Connect escalation callback to notification system | Same file |
| 1.4 | Integrate with `OSToolExecutor` for high-risk tool calls | [`os_control/os_tool_executor.py`](../os_control/os_tool_executor.py) |

**Integration Points:**

```
High-Risk Action
    │
    ▼
OSToolExecutor.execute()
    │
    ▼ (if risk_level == HIGH or CRITICAL)
BiometricHardwareGate.verify_admin()
    │
    ├── GRANTED → proceed
    ├── DENIED  → block + audit
    ├── TIMEOUT → auto_lock
    └── ESCALATED → clone consensus
```

#### 2. Connect to Personal OS

Current state: [`core/identity/personal_os.py`](../core/identity/personal_os.py:1) (1069 lines) — `PersonalOS` with modes PERSONAL, WORK, PUBLIC, EMERGENCY, OFFLINE.

**Actions:**

| Step | Action | File/Line |
|------|--------|-----------|
| 2.1 | Add biometric verification trigger at `EMERGENCY` mode switch | [`core/identity/personal_os.py`](../core/identity/personal_os.py:53) |
| 2.2 | When user switches to EMERGENCY mode, require biometric verification first | Same file |
| 2.3 | Add biometric enrollment UI hook (trigger from Personal OS settings) | Same file |
| 2.4 | Emit notification when biometric gate is triggered | Same file |

#### 3. Rewrite HardwareHardLock

Current state: [`security/hardware_hard_lock.py`](../security/hardware_hard_lock.py:1) (819 lines) — Contains dangerous `subprocess` calls (line 20: `import subprocess`). Uses `netsh`, `iptables` simulation for network isolation.

**Actions:**

| Step | Action | File/Line |
|------|--------|-----------|
| 3.1 | Remove all `subprocess` calls (lines referencing netsh, iptables, etc.) | [`security/hardware_hard_lock.py`](../security/hardware_hard_lock.py) |
| 3.2 | Replace with **Windows ETW** (Event Tracing for Windows) for process/network monitoring | Same file |
| 3.3 | Replace with **Linux auditd** integration for Linux systems | Same file |
| 3.4 | Add file integrity monitoring (watch critical system files for tampering) | Same file |
| 3.5 | Add **TPM integration** for real hardware attestation | Same file |
| 3.6 | Add proper platform detection (`platform.system()`) to select appropriate monitoring backend | Same file |
| 3.7 | Use `psutil` instead of subprocess for process/network info | Same file (already imported at line 18) |

**Platform-Specific Monitoring Architecture:**

```
HardwareMonitor (abstract base)
    │
    ├── WindowsMonitor
    │   ├── ETW (Event Tracing for Windows)
    │   │   ├── Microsoft-Windows-Kernel-Process (process events)
    │   │   ├── Microsoft-Windows-TCPIP (network events)
    │   │   └── Microsoft-Windows-FileInfoMinifilter (file events)
    │   ├── WMI queries (hardware health)
    │   └── TBS (TPM Base Services) for attestation
    │
    ├── LinuxMonitor
    │   ├── auditd (via subprocess `auditctl` + reading `/var/log/audit/audit.log`)
    │   ├── inotify (file monitoring)
    │   └── tpm2-tools (TPM attestation)
    │
    └── DarwinMonitor (macOS)
        ├── EndpointSecurity API (process/network)
        ├── FSEvents (file monitoring)
        └── LocalEvaluation (TPM-like via Secure Enclave)
```

#### 4. Fix biometric template storage

Current state: [`security/hard_lock.py`](../security/hard_lock.py:1) (705 lines) — Uses SHA-512 hashes as "biometric templates" (line 17: `import hashlib`). This is not real biometric feature extraction.

**Actions:**

| Step | Action | File/Line |
|------|--------|-----------|
| 4.1 | Replace SHA-512 "biometric templates" with actual feature extraction | [`security/hard_lock.py`](../security/hard_lock.py) |
| 4.2 | Integrate with real biometric library (e.g., `face_recognition`, `dlib`, `fingerprint` lib) | Same file |
| 4.3 | Add **ZKP-based biometric verification** — prove biometric match without revealing raw template | Same file |
| 4.4 | Store only ZKP commitments, not raw templates | Same file |

**ZKP Biometric Flow:**

```
Enrollment:
  raw_biometric_data
    │
    ▼
  feature_extractor.extract() → feature_vector
    │
    ▼
  zkp_commitment = hash(feature_vector + salt)
    │
    ▼
  Store: { user_id, zkp_commitment, salt, metadata }

Verification:
  new_biometric_data
    │
    ▼
  feature_extractor.extract() → new_feature_vector
    │
    ▼
  zkp_prover.prove(new_feature_vector, stored_commitment, salt)
    │
    ▼
  Returns: match? (ZKP proof verification)
  No raw template transmitted or stored.
```

### Exit Criteria

- [x] Biometric gate wired into action flow (high-risk actions require biometric verify)
- [x] Personal OS triggers biometric gate on `EMERGENCY` mode switch
- [x] HardwareHardLock uses real OS monitoring (ETW/auditd), not simulated commands
- [x] TPM attestation works (platform-specific)
- [x] Biometric templates use real feature extraction + ZKP (not SHA-512 hashes)
- [x] Full flow: threat detection → biometric gate → consensus → lock

---

## Execution Order & Dependencies

```
P0 ─────────────────────────────────────────────────────────────────
│  No dependencies — can start immediately
│  Estimated: 2–3 days
│
P2 ─────────────────────────────────────────────────────────────────
│  No dependencies — can run parallel with P0
│  Estimated: 3–4 days
│
P3 ─────────────────────────────────────────────────────────────────
│  Depends on: P2 (for audit logging infrastructure)
│  Estimated: 5–7 days
│
P4 ─────────────────────────────────────────────────────────────────
│  No hard dependencies — can run parallel with P2/P3
│  Estimated: 4–5 days
│
P5 ─────────────────────────────────────────────────────────────────
│  Depends on: P2 (for OS control wiring), P3 (for clone consensus)
│  Estimated: 7–10 days
```

### Recommended Sequence

```
Week 1:  P0 + P2 (parallel, non-conflicting)
Week 2:  P3 + P4 (parallel, different code areas)
Week 3:  P5 (depends on P2 + P3)
```

---

## Risk Register

| Risk | Milestone | Impact | Mitigation |
|------|-----------|--------|------------|
| DLL/API conflicts with sentence-transformers | P4 | Blocked embeddings | Pin version, use fallback to OPENAI backend |
| NVIDIA API key rotation | P3 | Voting fails | Cache keys, graceful degredation to keyword heuristic |
| Windows ETW permissions | P5 | No Windows monitoring | Run as admin or use WMI fallback |
| ChromaDB schema changes | P4 | Data loss | Pin chromadb==0.4.x, test migration first |
| Git tag conflicts | P0 | Broken release | Check for existing tags, use `-f` only after confirmation |
| Biometric ZKP performance | P5 | Slow verification | Cache ZKP proofs, use threshold confidence |

---

## Appendix: Reference Files

| File | Lines | Purpose |
|------|-------|---------|
| [`deploy/release/releases.json`](../deploy/release/releases.json) | 282 | Release history — P0 cleanup target |
| [`deploy/release/version.txt`](../deploy/release/version.txt) | 1 | Version tracking — P0 bump target |
| [`docs/MONITORING_CHECKLIST.md`](../docs/MONITORING_CHECKLIST.md) | 121 | Post-release checklist — P0 execution guide |
| [`os_control/tool_registry.py`](../os_control/tool_registry.py) | 57 | Tool registry skeleton — P2 expansion target |
| [`os_control/capability_matrix.py`](../os_control/capability_matrix.py) | 479 | Capability definitions — P2 verification target |
| [`os_control/os_tool_executor.py`](../os_control/os_tool_executor.py) | 811 | Tool executor — P2 wiring target |
| [`os_control/openclaw_like_tools/`](../os_control/openclaw_like_tools/) | 5 files | Tool implementations — P2 registration target |
| [`core/founder_clones/founder_clone_system.py`](../core/founder_clones/founder_clone_system.py) | 505 | Founder roles — P3 mapping target |
| [`core/consensus/clone_consensus.py`](../core/consensus/clone_consensus.py) | 358 | Consensus engine — P3 LLM voting target |
| [`core/vectormemory.py`](../core/vectormemory.py) | 475 | Vector memory — P4 embedding target |
| [`core/rag/vector_database_manager.py`](../core/rag/vector_database_manager.py) | 283 | DB manager — P4 ChromaDB target |
| [`core/rag/rag_pipeline.py`](../core/rag/rag_pipeline.py) | 121 | RAG pipeline — P4 wiring target |
| [`security/biometric_hardware_gate.py`](../security/biometric_hardware_gate.py) | 426 | Biometric gate — P5 wiring target |
| [`security/hardware_hard_lock.py`](../security/hardware_hard_lock.py) | 819 | Hardware lock — P5 rewrite target |
| [`security/hard_lock.py`](../security/hard_lock.py) | 705 | Hard lock security — P5 template fix target |
| [`core/identity/personal_os.py`](../core/identity/personal_os.py) | 1069 | Personal OS — P5 emergency mode target |
| [`nexus_event_bus.py`](../nexus_event_bus.py) | — | Event bus — P3 consensus events target |

---

## Appendix: Required Dependencies

### P4 New Dependencies

```
chromadb>=0.4.22
sentence-transformers>=2.2.2
```

### P5 New Dependencies

```
# Windows ETW (Python)
# No extra package needed — use ctypes + Advapi32
#
# Linux auditd
# No extra package needed — read /var/log/audit/audit.log
#
# TPM (platform-specific)
# Windows: tbs.dll via ctypes
# Linux: tpm2-pytss or subprocess tpm2_tools
#
# Face recognition / biometric
# face-recognition>=1.3.0
# dlib>=19.24.0 (or use CPU-only fallback)
```

---

*End of Execution Plan*
