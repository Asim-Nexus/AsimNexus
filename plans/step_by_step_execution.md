# Step-by-Step Execution Plan

## Phase 0: Fix Known Test Import Bugs

### Todo List:

- [ ] Fix `tests/stress_test.py` — Fix `kill_switch` import path (line 25)
- [ ] Fix `tests/test_conftest.py` — Fix `NameError: module_name` + conftest import (line 21)
- [ ] Fix `tests/test_hybrid_router.py` — Add `KeywordClassifier` export in `core/routing/hybrid_router.py` (line 9)
- [ ] Fix `tests/test_integration_stress_test.py` — Fix broken import paths (line 21)
- [ ] Fix `tests/test_integration_test_suite.py` — Fix broken import paths (line 21)
- [ ] Fix `tests/test_load_test.py` — Fix broken import paths (line 21)
- [ ] Fix `tests/test_mock_modules.py` — Fix broken import paths (line 21)
- [ ] Fix `tests/test_multi_agent.py` — Add `import logging` (line 19)
- [ ] Run `tests/real/` full suite — Isolate remaining failures and fix them
- [ ] Run full project test suite — Confirm green

---

## Phase 1: Mesh Networking → Real

### Subphase 1A: Transport Foundation
- [ ] `mesh/p2p_transport.py` — Replace simulated UDP with real `asyncio.DatagramProtocol`, add peer handshake (HELLO/ACK), session state machine
- [ ] `mesh/bootstrap.py` — Wire to real TCP sockets, add seed node discovery
- [ ] `mesh/relay.py` — Wire relay to real connections
- [ ] `mesh/autodiscovery.py` — Wire to real broadcast/multicast/mDNS
- [ ] Real transport integration test passes

### Subphase 1B: NAT Traversal
- [ ] `mesh/stun_turn.py` — Wire to real STUN servers (Google: `stun.l.google.com:19302`, Cloudflare)
- [ ] `mesh/hole_punching.py` — Wire all 4 strategies to real UDP sockets
- [ ] NAT traversal integration test passes

### Subphase 1C: Discovery & Routing
- [ ] `mesh/kademlia_dht.py` — Wire to real UDP-based node discovery
- [ ] `mesh/multi_mesh_router.py` — Wire to real transport metrics
- [ ] Discovery & routing integration test passes

### Subphase 1D: Sync & Orchestration
- [ ] `mesh/crdt_sync.py` — Wire to real P2P sync
- [ ] `mesh/p2p_integration.py` — Wire full orchestrator
- [ ] Full mesh integration test passes

---

## Phase 2: Security Upgrades
- [ ] `core/security/level3_confirmation.py` — Add biometric gate + cooldown timer
- [ ] `core/security/security_manager.py` — Harden security framework
- [ ] `security/zkp_privacy.py` — Prepare real ZK proof path

## Phase 3: Economy
- [ ] `core/economy/contract_executor.py` — Complete contract lifecycle
- [ ] `economy/nexus_credits.py` — Make cleaner, deterministic, auditable

## Phase 4: Identity & Universe
- [ ] `core/identity/user_identity.py` — Complete role integration
- [ ] `core/identity/did_system.py` — Complete DID flows
- [ ] `core/universe/personal_universe.py` — Fix state correctness

## Phase 5: World Clones
- [ ] `core/founder_clones/world_clones.py` — Integrate ensemble consensus voting
- [ ] `governance/` — Connect governance logic + clone delegation
