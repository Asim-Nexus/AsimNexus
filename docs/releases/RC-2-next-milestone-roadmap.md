# Next Milestone Roadmap — After RC-2

> **Current Release:** `1.0.0+build42-rc2` (hardened, published, frozen)  
> **Date:** 2026-05-31  
> **Owner:** AsiM-Nexus

---

## Recommended Execution Order

```
Priority │ Milestone                         │ Risk    │ Value    │ Dependencies
─────────┼───────────────────────────────────┼─────────┼──────────┼─────────────
   P0    │ 1. Production release v1.0.0       │ Low     │ Critical │ None
   P1    │ 2. Real mesh networking             │ High    │ High     │ #1 stable
   P2    │ 3. OS Control wiring                │ Medium  │ High     │ #1 stable
   P3    │ 4. Multi-clone voting               │ Medium  │ Medium   │ #2 (mesh)
   P4    │ 5. Vector DB integration             │ Medium  │ Medium   │ #1 stable
   P5    │ 6. Biometric hardware gate           │ High    │ Low*     │ #1, #3 stable
```

> **Strategy:** Stability first → infrastructure depth → user-facing power.  
> This gives the strongest foundation for everything else.

---

## Milestone 1 — Production Release v1.0.0 (P0)

### Goal
Promote RC-2 to stable `v1.0.0` and publish production artifacts for Docker, PWA, and mobile targets.

### Scope
- Run full RC-2 release process (already done for `docker` target)
- Publish for `pwa`, `desktop`, `mobile` targets
- Run monitoring checklist ([`MONITORING_CHECKLIST.md`](../MONITORING_CHECKLIST.md)) for 24h observation window
- Tag `v1.0.0` from RC-2 (or RC-2 + hotfixes if any)
- Freeze `docs/STATUS.md` with production version
- Update `deploy/pwa/manifest.json` version
- Update `frontend/react/package.json` version

### Dependencies
- None — RC-2 is already published and frozen

### Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Hidden auth/route regression | Low | Full E2E suite (46/46) + route verification (23 routes) already done |
| Staging vs production config drift | Low | Smoke test + monitoring checklist will catch drift |
| PWA manifest not updated | Low | Included in scope |

### Exit Criteria
- [ ] `v1.0.0` tag published on `main`
- [ ] Docker image published and verified
- [ ] PWA manifest version matches release version
- [ ] Mobile app config updated
- [ ] Monitoring checklist clean for 24h observation
- [ ] 0 critical regressions
- [ ] E2E suite: 46/46 passing
- [ ] All health endpoints responding on production port

### Test Plan
1. `npx playwright test` — 46/46 E2E
2. Route verification — all 12 core + 9 legacy redirects
3. Health endpoints — `/health/live`, `/health/ready`, `/health/status`
4. Auth flow — register → login → token validation → protected routes
5. Proxy verification — frontend :3000 ↔ backend :8000
6. Monitoring checklist — 24h observation

---

## Milestone 2 — Real Mesh Networking (P1)

### Goal
Replace simulated mesh behavior with actual P2P sockets. Implement real Kademlia DHT, real CRDT sync, and hole-punching for NAT traversal.

### Scope
- **Kademlia DHT** — [`mesh/kademlia_dht.py`](../../mesh/kademlia_dht.py)
  - Find node → real UDP-based peer lookup
  - Store/find value → actual distributed hash table operations
  - Bootstrap → seed node discovery via hardcoded or DNS seed list
- **CRDT Sync** — [`mesh/crdt_sync.py`](../../mesh/crdt_sync.py)
  - Replace simulated merge with WebSocket-based real-time sync
  - Conflict resolution → actual LWW (last-writer-wins) or MV-register merge
  - Sync queue → drain via real TCP/WebSocket connections
- **Auto-Discovery** — [`mesh/autodiscovery.py`](../../mesh/autodiscovery.py)
  - LAN discovery → UDP broadcast/mDNS
  - WAN discovery → DHT bootstrap + relay nodes
- **NAT Traversal**
  - UDP hole punching for peer-to-peer connections
  - Relay fallback when hole-punching fails
- **Mesh Router** — [`mesh/mesh_routing_agent_v2.py`](../../mesh/mesh_routing_agent_v2.py)
  - Route messages through actual P2P overlay
  - Multi-hop routing if direct P2P unavailable

### Dependencies
- Milestone 1 (stable production base to test against)

### Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| NAT traversal fails on restrictive networks | High | Implement relay fallback (TURN-style) |
| DHT bootstrap latency on fresh network | Medium | Hardcode 3-5 seed nodes |
| CRDT conflict resolution edge cases | Medium | Rigorous property-based testing |
| P2P socket security | Medium | MTLS + noise protocol on all P2P channels |
| Firewall blocking UDP | Medium | Fall back to TCP WebSocket relay |

### Exit Criteria
- [ ] Two mesh nodes can discover each other via DHT (LAN)
- [ ] CRDT state syncs between two nodes in < 1s (same LAN)
- [ ] CRDT conflict resolution produces deterministic output
- [ ] Hole-punching succeeds on at least one NAT type (cone NAT)
- [ ] Relay fallback works when hole-punching fails
- [ ] Existing mesh API endpoints return real data (not simulated)
- [ ] All existing E2E tests still pass (frontend mesh pages)
- [ ] Mesh dashboard shows real peer connections

### Test Plan
1. Unit tests — Kademlia DHT operations (find_node, store, find_value)
2. Unit tests — CRDT merge functions (add-wins set, LWW register, MV-register)
3. Unit tests — Auto-discovery (UDP broadcast receive/respond)
4. Integration — Two-node LAN mesh: discovery → DHT bootstrap → CRDT sync
5. Integration — Three-node mesh: multi-hop message routing
6. Integration — NAT hole-punching (run node behind cone NAT, verify P2P)
7. Integration — Relay fallback (block UDP, verify TCP relay kicks in)
8. E2E — `npx playwright test` — mesh pages show real data
9. Stress — 10-node mesh: sync propagation time

---

## Milestone 3 — OS Control Wiring (P2)

### Goal
Connect Tool Registry and Capability Matrix to real desktop/mobile OS control. This transforms AsimNexus from a dashboard into an operating layer.

### Scope
- **Tool Registry** — [`os_control/tool_registry.py`](../../os_control/tool_registry.py)
  - Register real OS tools (file, process, network, clipboard, media)
  - Permission gating via Capability Matrix
  - MCP-style tool calls from frontend
- **Capability Matrix** — [`os_control/capability_matrix.py`](../../os_control/capability_matrix.py)
  - Define per-user capability grants
  - Runtime enforcement on every tool call
  - Audit logging for all tool executions
- **Desktop Control**
  - File manager integration (already partial in frontend)
  - Process management (start/stop/list processes)
  - System monitoring (CPU, memory, disk, network)
  - Clipboard read/write (with consent)
- **Mobile Control** (if applicable)
  - Camera/gallery access (with consent)
  - File system access
  - Notification relay
- **Frontend Integration**
  - OS Hub ([`OSHub.jsx`](../../frontend/react/src/components/pages/OSHub.jsx)) shows real OS state
  - Tool execution UI with capability indicators
  - Permission request/reject flow

### Dependencies
- Milestone 1 (stable production base)
- [`os_control/sandbox/`](../../os_control/sandbox/) — Docker sandbox, low-priv user runner, WASM sandbox already exist

### Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Security sandbox bypass | High | Defense-in-depth: Docker + low-priv user + capability checks |
| Cross-platform OS differences | High | Abstract OS calls behind `os_wrapper.py` interface |
| Permission UX too complex | Medium | Simple approve/deny/reject-permanently dialog |
| Tool injection via unrestricted commands | Medium | Strict input validation + allowlist-based routing |

### Exit Criteria
- [ ] Tool Registry has ≥ 5 real OS tools registered (file, process, system, clipboard, notification)
- [ ] Capability Matrix enforces grants on every tool call
- [ ] Permission request UI works end-to-end (request → approve/reject → execute)
- [ ] OS Hub shows real system metrics (CPU, memory, disk)
- [ ] File browser tool can navigate the real filesystem (sandboxed)
- [ ] All tool executions are audit-logged
- [ ] Existing E2E tests still pass
- [ ] No sandbox escape in 100 attempted bypass scenarios

### Test Plan
1. Unit — Tool Registry: register, list, call, unregister
2. Unit — Capability Matrix: grant, revoke, check, audit
3. Unit — Sandbox: file read/write isolation, process isolation
4. Integration — Permission flow: request → UI shows → approve → tool executes
5. Integration — Tool execution through MCP-style API endpoint
6. Security — Attempt sandbox bypass (path traversal, command injection, symlink attacks)
7. E2E — OS Hub renders with real data
8. E2E — Permission dialog appears and blocks tool until approved

---

## Milestone 4 — Multi-Clone Voting (P3)

### Goal
Upgrade consensus from partial to ensemble-based decision flow. Enable governance, delegation, and agent arbitration through multi-clone voting.

### Scope
- **World Clones** — [`core/founder_clones/world_clones.py`](../../core/founder_clones/world_clones.py)
  - Implement ensemble voting (majority, supermajority, unanimous)
  - Vote lifecycle: propose → debate → vote → tally → execute
  - Clone identity-based voting power
- **Founder Clones** — [`core/founder_clones/founder_clone_system.py`](../../core/founder_clones/founder_clone_system.py)
  - Delegation mechanism (clone A delegates vote to clone B)
  - Arbitration rules (tie-breaking, override, veto)
- **Consensus Engine** — [`core/consensus/clone_consensus.py`](../../core/consensus/clone_consensus.py)
  - Raft-like consensus for distributed state
  - Leader election among clone nodes
  - Log replication for decision history
- **Frontend UI**
  - Vote proposal form
  - Voting dashboard (current proposals, vote tally, history)

### Dependencies
- Milestone 2 (mesh networking) — inter-clone communication needs P2P

### Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Consensus turns into bike-shedding | High | Time-bound voting rounds with auto-escalation |
| Clone identity spoofing | Medium | Vote signatures via DID/HDT keys |
| Network partition splits vote | Medium | Raft-style leader lease + stale-read fallback |

### Exit Criteria
- [ ] Ensemble voting works: propose → vote → tally → execute
- [ ] Delegation works: clone A delegates to clone B, B votes for both
- [ ] Arbitration works: tie-breaking and veto
- [ ] Raft consensus: leader election, log replication, failover
- [ ] Frontend voting dashboard renders live proposals
- [ ] E2E: create proposal → cast votes → see result

### Test Plan
1. Unit — Voting math: majority, supermajority, unanimous, weighted
2. Unit — Delegation chain (A→B→C)
3. Integration — 5-clone ensemble: all vote, tally, execute
4. Integration — Raft: leader crash → new leader elected → log consistency
5. Integration — Network partition: split 3-2, verify stale-read fallback
6. E2E — Frontend voting flow

---

## Milestone 5 — Vector DB Integration (P4)

### Goal
Move memory from SQLite-centric storage toward Chroma/Pinecone-style vector retrieval for semantic search and scale.

### Scope
- **Vector Store Backend**
  - Integrate Chroma (local, open-source) or Pinecone (cloud, managed)
  - Embedding generation via local model (Qwen3) or cloud API
  - CRUD: insert, query (by vector + metadata filter), delete, update
- **Semantic Search**
  - Replace SQLite `LIKE` queries with vector similarity search
  - Hybrid search: vector + keyword (BM25 or reciprocal rank fusion)
- **Memory Pipeline** — [`core/vectormemory.py`](../../core/vectormemory.py)
  - Chunking strategy for long documents
  - Embedding cache (avoid re-computing for same text)
  - Metadata index for filtered queries
- **Migration**
  - One-time migration script: SQLite messages → vector store
  - Dual-write during transition (SQLite + vector)
  - Cutover after verification

### Dependencies
- Milestone 1 (stable production base)

### Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Embedding model too slow for real-time | Medium | Async embedding pipeline + cache |
| Vector store cost (Pinecone) | Medium | Start with Chroma (local, free) |
| Migration data loss | Low | Dual-write + verification step |
| Query latency too high | Medium | HNSW index + metadata pre-filtering |

### Exit Criteria
- [ ] Chroma or Pinecone integrated as vector backend
- [ ] Embedding pipeline generates vectors for new messages
- [ ] Semantic search returns relevant results (MRR > 0.7 on test queries)
- [ ] Hybrid search (vector + keyword) available
- [ ] One-time migration completes successfully (all SQLite messages indexed)
- [ ] Existing memory API endpoints work with new backend
- [ ] E2E: chat → memory recall → semantic search returns context

### Test Plan
1. Unit — Embedding: consistent vector output for same input
2. Unit — Vector store CRUD: insert, query, delete, update
3. Unit — Hybrid search: reciprocal rank fusion
4. Integration — Chat message → stored in vector store → recalled via semantic query
5. Integration — Migration: SQLite → vector store, verify count + content
6. Performance — Query latency p50/p95 for 10K, 100K, 1M vectors
7. E2E — `/api/memory/search` returns semantically relevant results

---

## Milestone 6 — Biometric Hardware Gate (P5)

### Goal
Implement Level-3 security with actual biometric hardware attestation. This is the most security-heavy item and is saved for last.

### Scope
- **Hardware Gate** — [`security/hardware_hard_lock.py`](../../security/hardware_hard_lock.py)
  - Fingerprint scanner integration (libfprint or vendor SDK)
  - Webcam-based face recognition (OpenCV + local model)
  - Hardware security module (HSM) key generation
- **Identity Binding**
  - Bind biometric hash to DID (decentralized identity)
  - ZKP-based biometric verification (prove match without revealing template)
- **Fallback**
  - Time-based one-time password (TOTP) as alternative
  - Recovery codes printed at setup

### Dependencies
- Milestone 1 (stable platform)
- Milestone 3 (OS Control) — biometric gate needs OS-level device access

### Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| No fingerprint reader on target device | High | Camera-based face recognition as primary, TOTP as universal fallback |
| Biometric template security | High | Store only ZKP proof, never raw template |
| False acceptance / false rejection | Medium | Configurable threshold + multiple attempt retry |
| OS permission complexity | Medium | Abstract behind `os_wrapper.py` |

### Exit Criteria
- [ ] Fingerprint enrollment and verification (on devices with reader)
- [ ] Face recognition enrollment and verification (on devices with camera)
- [ ] Biometric → DID binding with ZKP proof
- [ ] TOTP fallback as alternative
- [ ] Recovery codes generated and printable
- [ ] All existing auth flows still work
- [ ] E2E: biometric gate blocks sensitive action → biometric verify → action proceeds

### Test Plan
1. Unit — ZKP biometric verification: prove match without revealing template
2. Unit — DID binding: link biometric proof to decentralized identity
3. Integration — Enrollment → verify → action gate → bypass if fail
4. Integration — TOTP fallback works when biometric unavailable
5. Security — Attempt replay attack on biometric proof
6. E2E — Biometric gate UI flow (enroll → verify → gate opens)

---

## Summary — What to Do Now

1. **Verify RC-2 monitoring** — run [`MONITORING_CHECKLIST.md`](../MONITORING_CHECKLIST.md) for 24h
2. **If clean** → promote to `v1.0.0` (Milestone 1)
3. **Begin mesh networking** (Milestone 2) — highest architectural impact
4. **Parallel** — start OS Control wireframes and permission UX design (Milestone 3)
5. **Sequence** remaining milestones by dependency chain

> **Phasing note:** Milestones 2 and 3 can overlap partially — mesh networking enables inter-process tool execution, while OS Control provides the UI for mesh node management. They reinforce each other.

---

*See [`../RELEASE_PROCESS.md`](../RELEASE_PROCESS.md) for release workflow.*  
*See [`../MONITORING_CHECKLIST.md`](../MONITORING_CHECKLIST.md) for post-release monitoring.*  
*See [`../RELEASE_NOTES_RC2.md`](../RELEASE_NOTES_RC2.md) for current release details.*
