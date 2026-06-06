# AsimNexus — Refined Execution Plan (2026-06-02)

> **Approved by user.** Structured into 7 phases with clear dependency ordering.

---

## Phase 0: Fix Remaining Test Failures (IMMEDIATE — TODAY)

**Why first:** Failing tests hide regressions when doing other work.

### Tasks:

1. [`tests/stress_test.py`](tests/stress_test.py:25) — Fix `kill_switch` import path
2. [`tests/test_conftest.py`](tests/test_conftest.py:21) — Fix `conftest` import issue + `NameError: name 'module_name'`
3. [`tests/test_hybrid_router.py`](tests/test_hybrid_router.py:9) — Fix missing `KeywordClassifier` import/export in [`core/routing/hybrid_router.py`](core/routing/hybrid_router.py)
4. [`tests/test_integration_stress_test.py`](tests/test_integration_stress_test.py:21) — Fix broken import paths
5. [`tests/test_integration_test_suite.py`](tests/test_integration_test_suite.py:21) — Fix broken import paths
6. [`tests/test_load_test.py`](tests/test_load_test.py:21) — Fix broken import paths
7. [`tests/test_mock_modules.py`](tests/test_mock_modules.py:21) — Fix broken import paths
8. [`tests/test_multi_agent.py`](tests/test_multi_agent.py:19) — Add missing `import logging`
9. Run [`tests/real/`](tests/real/) full suite — Isolate remaining F/E markers and fix them

---

## Phase 1: Mesh Networking → REAL (BIGGEST WORK)

### Subphase 1A: Transport Layer (wire to real sockets first)
- [`mesh/p2p_transport.py`](mesh/p2p_transport.py) — Replace simulated UDP with real `asyncio.DatagramProtocol`
- [`mesh/bootstrap.py`](mesh/bootstrap.py) — Wire to real TCP sockets + seed node discovery
- [`mesh/relay.py`](mesh/relay.py) — Wire relay to real connections
- [`mesh/autodiscovery.py`](mesh/autodiscovery.py) — Wire to real broadcast/multicast/mDNS
- [`mesh/stun_turn.py`](mesh/stun_turn.py) — Wire to real STUN servers (Google, Cloudflare)
- [`mesh/hole_punching.py`](mesh/hole_punching.py) — Wire all 4 strategies to real UDP sockets

### Subphase 1B: Discovery & Routing (after transport is stable)
- [`mesh/kademlia_dht.py`](mesh/kademlia_dht.py) — Wire to real UDP-based node discovery
- [`mesh/crdt_sync.py`](mesh/crdt_sync.py) — Wire to real P2P sync
- [`mesh/p2p_integration.py`](mesh/p2p_integration.py) — Wire orchestrator
- [`mesh/multi_mesh_router.py`](mesh/multi_mesh_router.py) — Wire to real transport metrics

---

## Phase 2: Security Upgrades (after mesh stable)

- [`core/security/level3_confirmation.py`](core/security/level3_confirmation.py) — Add biometric gate + cooldown timer
- [`core/security/security_manager.py`](core/security/security_manager.py) — Harden framework
- [`security/zkp_privacy.py`](security/zkp_privacy.py) — Prepare for real ZK path
- **Deferred:** hardware lock, immutable constitution enforcement

---

## Phase 3: Identity & Universe

- [`core/identity/user_identity.py`](core/identity/user_identity.py) — Complete role integration
- [`core/identity/did_system.py`](core/identity/did_system.py) — Complete DID flows
- [`core/universe/personal_universe.py`](core/universe/personal_universe.py) — Fix state correctness + integration consistency

---

## Phase 4: Economy

- [`core/economy/contract_executor.py`](core/economy/contract_executor.py) — Complete lifecycle
- [`economy/nexus_credits.py`](economy/nexus_credits.py) — Make cleaner, deterministic, auditable
- **Note:** Blockchain dependency not enforced unless truly required

---

## Phase 5: World Clones

- [`core/founder_clones/world_clones.py`](core/founder_clones/world_clones.py) — Integrate ensemble consensus voting
- Connect with governance logic + clone delegation correctness

---

## Phase 6: Frontend/Backend Wiring

- [`frontend/react/src/App.js`](frontend/react/src/App.js) — Wire routes to real data
- [`frontend/react/src/api/asimnexus.js`](frontend/react/src/api/asimnexus.js) — Align API layer
- [`desktop/electron/main.js`](desktop/electron/main.js) — Stabilize Electron shell
- **Deferred:** React Native mobile app skeleton

---

## Execution Strategy

```
Today:     Phase 0 — Test suite green, import/path bugs fixed, tests/real/ failures isolated
Next:      Phase 1A — Mesh transport to real sockets, STUN/TURN + hole punching confirmed
Then:      Phase 1B — DHT + CRDT + router wiring
Finally:   Phases 2-6 — Identity, economy, clones, frontend polish
```
