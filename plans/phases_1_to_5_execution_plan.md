# AsimNexus — Phase 1–5 Execution Plan (Single-Machine)

> **Status:** Planning | **Deployment Model:** Single-Machine (localhost only)
> **Pre-requisite:** Phase 0 complete — 2424 passed, 13 expected launch_spine failures
> **Key Insight:** All mesh components are **REAL**, not simulated. This plan **adapts** them for single-machine, not rebuilds.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    SINGLE MACHINE DEPLOYMENT                  │
│                    =========================                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              P2PTransport (127.0.0.1)                 │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │    │
│  │  │  Node A   │  │  Node B   │  │    Node C...     │   │    │
│  │  │ :7332/7333│  │ :8332/8333│  │  :9332/9333      │   │    │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │    │
│  │       │               │               │              │    │
│  │       └───────────────┼───────────────┘              │    │
│  │                       │ (UDP + WebSocket)             │    │
│  │              ┌────────┴────────┐                      │    │
│  │              │   event_bus     │                      │    │
│  │              └─────────────────┘                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │            P2PIntegration (Orchestrator)              │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │    │
│  │  │Kademlia   │  │ CRDT     │  │ Bootstrap        │   │    │
│  │  │ DHT       │  │ Sync     │  │ Service          │   │    │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              MultiMeshRouter (8 types → 1 active)    │    │
│  │  All meshes map to LOCAL type on single machine      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │Security│ │Economy │ │Identity│ │ World  │ │Govern- │    │
│  │Upgrades│ │Credits │ │  & DID │ │ Clones │ │ ance   │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## Current State Assessment (Verified by Code Review)

### Mesh Components — ACTUAL Status vs. Documented Status

| Component | File | Lines | Actual Status | Documented Status | Key Evidence |
|-----------|------|-------|---------------|-------------------|--------------|
| P2P Transport | [`mesh/p2p_transport.py`](../mesh/p2p_transport.py) | 1426 | **REAL** | "PARTIAL" | Real `asyncio.DatagramProtocol`, `asyncio.start_server()`, HELLO/ACK handshake, session state machine, env-var config |
| Bootstrap | [`mesh/bootstrap.py`](../mesh/bootstrap.py) | 794 | **REAL** | "PARTIAL" | Real TCP server, registration/discovery protocol, env vars |
| Relay | [`mesh/relay.py`](../mesh/relay.py) | 425 | **REAL** | "PARTIAL" | Relay sessions, cleanup, env vars, event_bus integration |
| AutoDiscovery | [`mesh/autodiscovery.py`](../mesh/autodiscovery.py) | 506 | **REAL** | "PARTIAL" | Broadcast/multicast/mDNS, threads+raw sockets, env vars |
| Kademlia DHT | [`mesh/kademlia_dht.py`](../mesh/kademlia_dht.py) | 759 | **REAL** | "PARTIAL" | Full Kademlia protocol, P2PTransport integration, env vars |
| CRDT Sync | [`mesh/crdt_sync.py`](../mesh/crdt_sync.py) | 651 | **REAL** | "PARTIAL" | GCounter, LWWRegister, ORSet, sync protocol |
| P2P Integration | [`mesh/p2p_integration.py`](../mesh/p2p_integration.py) | 758 | **REAL** | "PARTIAL" | Bridges P2P↔MultiMeshRouter, DHT+CRDT+Bootstrap wiring, event_bus |
| NAT Traversal | [`mesh/nat_traversal.py`](../mesh/nat_traversal.py) | 513 | **REAL** | "PARTIAL" | NAT detection, hole-punching, relay fallback |
| STUN/TURN | [`mesh/stun_turn.py`](../mesh/stun_turn.py) | 898 | **REAL/INTEGRATED** | "PARTIAL" | RFC 5389 STUN + RFC 5766 TURN client |
| Multi-Hop Router | [`mesh/multi_hop_router.py`](../mesh/multi_hop_router.py) | 1098 | **REAL** | "NEW" | Path discovery, store-and-forward, env vars |
| MultiMesh Router | [`mesh/multi_mesh_router.py`](../mesh/multi_mesh_router.py) | 781 | **REAL** | "REAL" | 8 mesh types, auto-switching, health checks |
| Node Registry | [`mesh/node_registry.py`](../mesh/node_registry.py) | 430 | **REAL** | "REAL" | SQLite node registry, trust levels, cleanup |
| Device Registry | [`mesh/device_registry.py`](../mesh/device_registry.py) | 1232 | **REAL** | "PARTIAL" | Device discovery, resource pooling, topology |
| Offline Sync | [`mesh/offline_sync_engine.py`](../mesh/offline_sync_engine.py) | 872 | **REAL** | "REAL" | CRDT offline sync, conflict resolution |
| Network Intel | [`mesh/network_intelligence.py`](../mesh/network_intelligence.py) | 693 | **PARTIAL** | "PARTIAL" | Network analysis, frequency bands |

### Event Bus — Already Ready
- [`core/event_bus.py`](../core/event_bus.js) — REAL (275 lines)
- `EventType` already has: `PEER_CONNECTED`, `PEER_DISCONNECTED`, `RPC_TIMEOUT`, `TRANSPORT_STATE_CHANGE`, `BOOTSTRAP_COMPLETE`, `BOOTSTRAP_FAILED`, `PEER_REGISTERED`
- `p2p_integration.py` already subscribes to `PEER_CONNECTED` / `PEER_DISCONNECTED`
- `p2p_transport.py` already imports `event_bus`, `ASIMEvent`, `EventType` (lines 26-27 confirmed)

### Non-Mesh Components

| Component | File | Lines | Status | Notes |
|-----------|------|-------|--------|-------|
| World Clones | [`core/founder_clones/world_clones.py`](../core/founder_clones/world_clones.py) | 908 | **REAL** | 15 clone configs + prompts, local-first routing, ConsensusEngine integrated |
| User Identity | [`core/identity/user_identity.py`](../core/identity/user_identity.py) | 559 | **REAL** | Identity lifecycle, DID generation, credential issuance, ZKP auth |
| DID System | [`core/identity/did_system.py`](../core/identity/did_system.py) | — | Needs check | Referenced by user_identity |
| Immutable Constitution | [`security/immutable_constitution.py`](../security/immutable_constitution.py) | 316 | **CONCEPT→REAL** | Code exists with 10 principles, need enforcement wiring |
| mTLS | [`security/security_mtls.py`](../security/security_mtls.py) | 457 | **PARTIAL** | Certificate management, needs integration with P2PTransport |
| Security Framework | [`security/security_framework.py`](../security/security_framework.py) | ~200 | **PARTIAL** | Multiple security modules exist |
| ZKP Privacy | [`security/zkp_privacy.py`](../security/zkp_privacy.py) | 600 | **PARTIAL** | Framework exists, needs cryptographic verification |
| Nexus Credits | [`economy/nexus_credits.py`](../economy/nexus_credits.py) | 413 | **CONCEPT→REAL** | Code exists with transactions, ZKP proofs, packages |
| Contract Executor | [`core/economy/contract_executor.py`](../core/economy/contract_executor.py) | — | Needs check | Referenced in step_by_step_execution.md |

---

## Phase 1: Mesh Networking — Single-Machine Adaptation

### Core Principle for Single-Machine

All mesh components run on `127.0.0.1` with **port-based isolation**. Each "node" is a separate `P2PTransport` instance with unique ports:

```
Node A: UDP=17332, WS=17333
Node B: UDP=17334, WS=17335
Node C: UDP=17336, WS=17337
...
```

The following components are **not needed** on single-machine and should be short-circuited or skipped:
- **NAT Traversal** — No NAT on localhost
- **STUN/TURN** — No NAT on localhost
- **Multi-Hop Routing** — Direct connections only
- **Relay** — Direct connections only
- **AutoDiscovery (broadcast/multicast)** — Windows loopback doesn't support broadcast discovery; use direct config-based discovery instead

### Phase 1A: Transport Foundation

**Goal:** Harden the already-real P2PTransport with TLS, event emission, error types, rate limiting, and auto-reconnect.

**Files to modify:**
1. [`mesh/p2p_transport.py`](../mesh/p2p_transport.py) — Add TLS support, finish event emission, add structured error types
2. [`mesh/bootstrap.py`](../mesh/bootstrap.py) — Add TLS support, DNS seed discovery, retry with backoff
3. [`tests/real/test_mesh_transport.py`](../tests/real/test_mesh_transport.py) — Add TLS, fragmentation, auto-reconnect, rate-limit tests
4. New: [`tests/real/test_mesh_transport_tls.py`](../tests/real/test_mesh_transport_tls.py) — TLS-specific tests

**Detailed steps:**
1. Add `ssl_context` parameter to `P2PTransport.__init__()` — pass to `asyncio.start_server()` and `asyncio.open_connection()`
2. Add `is_secure` property, update `get_stats()`
3. Verify event emission in `p2p_transport.py` — `_handle_peer_hello`, `_handle_ws_connection` finally, `rpc_call`, `start()/stop()` already wired to `event_bus`
4. Add structured error types (`TransportError`, `ConnectionError`, `HandshakeError`, `MessageTooLargeError`, `RateLimitError`, `SecurityError`)
5. Add connection rate limiting in `connect_peer()`
6. Add `ssl_context` to `BootstrapService.__init__()`, `start()`, `request_bootstrap()`
7. Add DNS seed discovery in `bootstrap._load_default_bootstraps()`
8. Add bootstrap retry with exponential backoff

**Tests to add:**
- `test_tls_handshake` — Two transports connect with self-signed TLS certs
- `test_large_payload_chunking` — 2MB payload chunking and reassembly
- `test_peer_reconnects_after_drop` — Auto-reconnect after server restart
- `test_rate_limit_exceeded` — Connection rate limiting
- `test_dns_resolution` — Bootstrap DNS seed discovery

**Verification:**
```powershell
python -m pytest tests/real/test_mesh_transport.py -v --timeout=120
python -m pytest tests/real/test_mesh_transport_tls.py -v --timeout=120
```

---

### Phase 1B: NAT Traversal — Skip for Single-Machine

**Decision:** All NAT components are **bypassed** for single-machine deployment.

**Files to modify:**
1. [`mesh/nat_traversal.py`](../mesh/nat_traversal.py) — Add `is_localhost()` check at start, skip STUN if `127.0.0.1`
2. [`mesh/stun_turn.py`](../mesh/stun_turn.py) — Same `is_localhost()` short-circuit
3. [`tests/real/test_nat_traversal.py`](../tests/real/test_nat_traversal.py) — Add test for localhost short-circuit

**Short-circuit pattern:**
```python
async def detect_nat_type(self, host: str = "0.0.0.0") -> NATType:
    if host in ("127.0.0.1", "::1", "localhost"):
        return NATType.FULL_CONE  # No NAT on localhost
    # ... rest of detection logic
```

**Verification:**
```powershell
python -m pytest tests/real/test_mesh_transport.py::TestConcurrentConnections -v --timeout=60
```

---

### Phase 1C: Discovery & Routing — Single-Machine Focused

**Goal:** Make discovery and routing work on single-machine where broadcast/multicast doesn't work and multi-hop routing isn't needed.

**Files to modify:**
1. [`mesh/autodiscovery.py`](../mesh/autodiscovery.py) — Add config-based peer discovery (static peer list from env var), short-circuit broadcast on localhost
2. [`mesh/kademlia_dht.py`](../mesh/kademlia_dht.py) — Add single-machine optimizations (shorter refresh intervals, direct node insertion)
3. [`mesh/multi_hop_router.py`](../mesh/multi_hop_router.py) — Short-circuit to single-hop for localhost
4. [`mesh/multi_mesh_router.py`](../mesh/multi_mesh_router.py) — Map all mesh types to LOCAL when on single machine
5. New env var: `ASIM_SINGLE_MACHINE_PEERS="node_a:host:port_udp:port_ws,node_b:..."`

**Discovery flow on single-machine:**
```
1. Read ASIM_SINGLE_MACHINE_PEERS env var
2. Parse peer list: "node_a:127.0.0.1:17332:17333,node_b:127.0.0.1:17334:17335"
3. For each peer, call P2PTransport.add_peer() + KademliaDHT.add_node()
4. Start WebSocket connection to each peer
5. Bootstrap registration + discovery on localhost
```

**Tests to add/update:**
- [`tests/real/test_mesh_spine.py`](../tests/real/test_mesh_spine.py) — Already exists, passes
- Add test for `ASIM_SINGLE_MACHINE_PEERS` parsing
- Add test for auto-discovery localhost short-circuit

**Verification:**
```powershell
python -m pytest tests/real/test_mesh_spine.py -v --timeout=60
python -m pytest tests/real/test_mesh_transport.py -v --timeout=120
```

---

### Phase 1D: Sync & Orchestration

**Goal:** Wire the full stack together via `p2p_integration.py` and verify end-to-end CRDT sync works across multiple localhost nodes.

**Files to modify:**
1. [`mesh/p2p_integration.py`](../mesh/p2p_integration.py) — **Mostly already complete** (758 lines). Verify event bus subscriptions, add single-machine startup helper
2. [`mesh/crdt_sync.py`](../mesh/crdt_sync.py) — Already REAL (651 lines). Verify sync across localhost nodes
3. New: [`tests/real/test_mesh_full_stack.py`](../tests/real/test_mesh_full_stack.py) — End-to-end test with 3 nodes

**E2E flow to verify:**
```
1. Start Node A (P2PTransport + KademliaDHT + CRDTStore + BootstrapService)
2. Start Node B (same stack on different ports)
3. Start Node C (same stack on different ports)
4. Bootstrap A → B learns about C
5. CRDT write on A → sync to B via WS → verify B has data
6. CRDT write on B → sync to C via WS → verify C has data
7. All 3 nodes converge
```

**Verification:**
```powershell
# Existing tests (should still pass)
python -m pytest tests/real/test_mesh_sync.py -v --timeout=120
python -m pytest tests/real/test_mesh_v2_integration.py -v --timeout=120
python -m pytest tests/real/test_mesh_full_stack.py -v --timeout=120
```

---

## Phase 2: Security Upgrades

### 2A: mTLS Integration with Mesh
**Goal:** Wire the existing `security_mtls.py` into `P2PTransport` and `BootstrapService`.

**Files to modify:**
1. [`security/security_mtls.py`](../security/security_mtls.py) — Add helper function `create_self_signed_cert()` for test/dev, add `load_cert_chain()` for production
2. [`mesh/p2p_transport.py`](../mesh/p2p_transport.py) — Import and use `mTLSConfig` for `ssl_context` creation
3. [`tests/real/test_mesh_transport_tls.py`](../tests/real/test_mesh_transport_tls.py) — Add mTLS test

### 2B: Immutable Constitution Enforcement
**Goal:** Wire `ImmutableConstitution.check_compliance()` into the Dharma VETO pipeline.

**Files to modify:**
1. [`security/immutable_constitution.py`](../security/immutable_constitution.py) — Already has 316 lines of code, add integration hooks
2. [`core/dharma/dharma_veto.py`](../core/dharma/dharma_veto.py) — Add ImmutableConstitution check as Layer 0 (before all other layers)
3. [`tests/real/test_power_balance_constitution.py`](../tests/real/test_power_balance_constitution.py) — Add constitution compliance tests

### 2C: ZKP Privacy Improvements
**Goal:** Harden the ZKP framework with real cryptographic primitives.

**Files to modify:**
1. [`security/zkp_privacy.py`](../security/zkp_privacy.py) — Replace SHA3 wrapper with proper ZK-SNARK/STARK interfaces, add proof verification
2. [`core/identity/zkp_local.py`](../core/identity/zkp_local.py) — Wire local ZKP for identity verification

**Verification:**
```powershell
python -m pytest tests/real/test_power_balance_constitution.py -v
python -m pytest tests/security/ -v
```

---

## Phase 3: Economy

### 3A: Nexus Credits Wiring
**Goal:** Wire the existing `nexus_credits.py` into the backend API.

**Files to modify:**
1. [`economy/nexus_credits.py`](../economy/nexus_credits.py) — Already has 413 lines with transactions, ZKP proofs, packages. Add persistence layer (JSONL)
2. [`core/economy/contract_executor.py`](../core/economy/contract_executor.py) — Complete contract lifecycle
3. [`core/economy/`](../core/economy/) — Wire all economy modules together
4. [`core/api_endpoints.py`](../core/api_endpoints.py) — Add `/api/economy/*` endpoints

### 3B: Contract Executor
**Goal:** Complete the contract execution lifecycle with deterministic and auditable transactions.

**Files to modify:**
1. [`core/economy/contract_executor.py`](../core/economy/contract_executor.py) — Add contract state machine, execution hooks, audit trail
2. [`economy/nexus_credits.py`](../economy/nexus_credits.py) — Wire credit transfers to contract execution

**Verification:**
```powershell
python -m pytest tests/real/test_economy.py -v
```

---

## Phase 4: Identity & Universe

### 4A: Identity Role Integration
**Goal:** Complete the identity system with full role-based access control wired to backend API.

**Files to modify:**
1. [`core/identity/user_identity.py`](../core/identity/user_identity.py) — Already has 559 lines, add role-to-capability mapping
2. [`core/api_endpoints.py`](../core/api_endpoints.py) — Add full identity lifecycle endpoints
3. [`auth/identity_provider.py`](../auth/identity_provider.py) — Wire JWT + identity together

### 4B: DID System Completion
**Goal:** Complete the DID (Decentralized Identifier) flows.

**Files to modify:**
1. [`core/identity/did_system.py`](../core/identity/did_system.py) — Complete DID document management, resolution, verification
2. [`core/identity/user_identity.py`](../core/identity/user_identity.py) — Wire DID creation into identity lifecycle

### 4C: Fix launch_spine Failures
**Goal:** Fix the 13 remaining test failures in `test_launch_spine.py`.

**Root cause:** `No module named 'core.universal/platform/government'` — these modules don't exist yet.

**Required work:**
1. Create `core/universal/__init__.py`, `core/platform/__init__.py`, `core/government/__init__.py`
2. Create stub modules or real implementations as needed
3. Verify all 13 tests pass

**Verification:**
```powershell
python -m pytest tests/real/test_launch_spine.py -v --timeout=30
# Expected: 0 failures
```

---

## Phase 5: World Clones — Ensemble Consensus

### 5A: Ensemble Consensus Voting
**Goal:** Implement the consensus voting system for World Clones to make collective decisions.

**Files to modify:**
1. [`core/founder_clones/world_clones.py`](../core/founder_clones/world_clones.py) — Already has 908 lines, `ConsensusEngine` already integrated. Add:
   - Multi-clone voting on critical decisions
   - Weighted voting (by expertise relevance)
   - Escalation to human override
2. [`core/founder_clones/consensus_engine.py`](../core/founder_clones/consensus_engine.py) — Already exists, verify integration

### 5B: Governance Delegation
**Goal:** Connect governance logic to clone delegation.

**Files to modify:**
1. [`governance/`](../governance/) — Wire governance decisions to clone voting
2. [`core/founder_clones/world_clones.py`](../core/founder_clones/world_clones.py) — Add delegation mechanism

**Verification:**
```powershell
python -m pytest tests/real/test_world_clones.py -v
python -m pytest tests/real/test_governance.py -v
```

---

## Implementation Order & Dependencies

```
Phase 1A ──► Phase 1C ──► Phase 1D
   │                           │
   ▼                           ▼
Phase 2A (mTLS)           Phase 3 (Economy)
   │                           │
   ▼                           ▼
Phase 2B (Constitution)   Phase 4 (Identity)
   │                           │
   ▼                           ▼
Phase 2C (ZKP)            Phase 5 (Clones)
```

**Rationale:**
1. **Phase 1A first** — Transport foundation is prerequisite for all mesh features
2. **Phase 1C then 1D** — Discovery before sync
3. **Phase 2A in parallel** — mTLS depends on P2PTransport changes from 1A
4. **Phase 3 after 1D** — Economy needs mesh sync for distributed transactions
5. **Phase 4 after 2** — Identity needs security layer
6. **Phase 5 last** — Consensus needs identity to know who's voting

---

## Detailed Per-File Change Summary

### Phase 1A: Transport Foundation (6 files)

| File | Change Type | Lines Changed (est.) | Risk |
|------|-------------|---------------------|------|
| [`mesh/p2p_transport.py`](../mesh/p2p_transport.py) | Modify | +120 | Medium |
| [`mesh/bootstrap.py`](../mesh/bootstrap.py) | Modify | +80 | Medium |
| [`tests/real/test_mesh_transport.py`](../tests/real/test_mesh_transport.py) | Modify | +300 | Low |
| [`tests/real/test_mesh_transport_tls.py`](../tests/real/test_mesh_transport_tls.py) | New | +200 | Low |
| [`docs/operations/MESH_CONFIG.md`](../docs/operations/MESH_CONFIG.md) | New | +100 | Low |
| [`scripts/run_benchmarks.py`](../scripts/run_benchmarks.py) | Modify | +50 | Low |

### Phase 1B: NAT Traversal Skip (2 files)

| File | Change Type | Lines Changed (est.) | Risk |
|------|-------------|---------------------|------|
| [`mesh/nat_traversal.py`](../mesh/nat_traversal.py) | Modify | +20 | Low |
| [`mesh/stun_turn.py`](../mesh/stun_turn.py) | Modify | +20 | Low |

### Phase 1C: Discovery & Routing (4 files)

| File | Change Type | Lines Changed (est.) | Risk |
|------|-------------|---------------------|------|
| [`mesh/autodiscovery.py`](../mesh/autodiscovery.py) | Modify | +50 | Medium |
| [`mesh/kademlia_dht.py`](../mesh/kademlia_dht.py) | Modify | +30 | Low |
| [`mesh/multi_hop_router.py`](../mesh/multi_hop_router.py) | Modify | +15 | Low |
| [`mesh/multi_mesh_router.py`](../mesh/multi_mesh_router.py) | Modify | +10 | Low |

### Phase 1D: Sync & Orchestration (2 files)

| File | Change Type | Lines Changed (est.) | Risk |
|------|-------------|---------------------|------|
| [`mesh/p2p_integration.py`](../mesh/p2p_integration.py) | Modify | +30 | Low |
| [`tests/real/test_mesh_full_stack.py`](../tests/real/test_mesh_full_stack.py) | New | +250 | Medium |

### Phase 2: Security (5 files)

| File | Change Type | Lines Changed (est.) | Risk |
|------|-------------|---------------------|------|
| [`security/security_mtls.py`](../security/security_mtls.py) | Modify | +100 | Medium |
| [`security/immutable_constitution.py`](../security/immutable_constitution.py) | Modify | +80 | Low |
| [`security/zkp_privacy.py`](../security/zkp_privacy.py) | Modify | +150 | High |
| [`core/dharma/dharma_veto.py`](../core/dharma/dharma_veto.py) | Modify | +20 | Low |
| [`core/identity/zkp_local.py`](../core/identity/zkp_local.py) | Modify | +60 | Medium |

### Phase 3: Economy (4 files)

| File | Change Type | Lines Changed (est.) | Risk |
|------|-------------|---------------------|------|
| [`economy/nexus_credits.py`](../economy/nexus_credits.py) | Modify | +100 | Medium |
| [`core/economy/contract_executor.py`](../core/economy/contract_executor.py) | Modify | +150 | Medium |
| [`core/api_endpoints.py`](../core/api_endpoints.py) | Modify | +80 | Low |
| New test file | New | +200 | Low |

### Phase 4: Identity (5 files)

| File | Change Type | Lines Changed (est.) | Risk |
|------|-------------|---------------------|------|
| [`core/identity/user_identity.py`](../core/identity/user_identity.py) | Modify | +100 | Medium |
| [`core/identity/did_system.py`](../core/identity/did_system.py) | Modify | +150 | Medium |
| [`core/api_endpoints.py`](../core/api_endpoints.py) | Modify | +100 | Low |
| New: `core/universal/__init__.py` | New | +10 | Low |
| New: `core/platform/__init__.py` | New | +10 | Low |
| New: `core/government/__init__.py` | New | +10 | Low |
| [`auth/identity_provider.py`](../auth/identity_provider.py) | Modify | +50 | Medium |

### Phase 5: World Clones (3 files)

| File | Change Type | Lines Changed (est.) | Risk |
|------|-------------|---------------------|------|
| [`core/founder_clones/world_clones.py`](../core/founder_clones/world_clones.py) | Modify | +120 | Medium |
| [`core/founder_clones/consensus_engine.py`](../core/founder_clones/consensus_engine.py) | Modify | +60 | Low |
| [`governance/`](../governance/) | Modify | +80 | Medium |

---

## Verification Commands (per phase)

### Phase 1A Completion
```powershell
python -m pytest tests/real/test_mesh_transport.py -v --timeout=120
python -m pytest tests/real/test_mesh_transport_tls.py -v --timeout=120
python -m pytest tests/real/test_mesh_spine.py -v --timeout=60
```

### Phase 1B Completion
```powershell
python -m pytest tests/real/test_mesh_transport.py -v --timeout=120
```

### Phase 1C Completion
```powershell
python -m pytest tests/real/test_mesh_spine.py -v --timeout=60
python -m pytest tests/real/test_mesh_transport.py -v --timeout=120
```

### Phase 1D Completion
```powershell
python -m pytest tests/real/test_mesh_sync.py -v --timeout=120
python -m pytest tests/real/test_mesh_v2_integration.py -v --timeout=120
python -m pytest tests/real/test_mesh_full_stack.py -v --timeout=120
```

### Full Suite Regression
```powershell
python -m pytest tests/real/ -v --timeout=120 2>&1 | findstr /C:"passed" /C:"failed"
# Expected: 0 failures (13 launch_spine will pass after Phase 4C)
```

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| TLS cert generation complex in tests | Medium | Medium | Use `trustme` library or write fixture with `cryptography` |
| Event bus circular imports | Low | High | Already imported with lazy patterns; verify no regressions |
| Windows loopback broadcast doesn't work | High | Low | Config-based discovery instead; broadcast already has fallback |
| Single-machine port conflicts | Low | High | Use dynamic `find_free_port()` pattern from existing tests |
| Existing tests regress after changes | Low | High | Run full suite after each subphase |
| launch_spine module creation exposes missing deps | Medium | Medium | Create stub modules first, fill in real implementations |
