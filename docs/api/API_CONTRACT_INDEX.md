# API Contract Index

> **AsimNexus v1.0.1** | Last updated: 2026-06-01
> Source files: [`backend/`](../../backend/) modules, [`simple_backend.py`](../../simple_backend.py)

**Route count**: ~270+ registered endpoints across 15+ route modules

---

## 1. Health Probes

**Source**: [`backend/health.py`](../../backend/health.py) · [`HealthChecker`](../../backend/health.py:59)

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/health/live` | [`health_live()`](../../backend/health.py:472) | Liveness probe — returns 200 if process is alive |
| GET | `/health/ready` | [`health_ready()`](../../backend/health.py:476) | Readiness probe — checks all storage backends |
| GET | `/health/status` | [`health_status()`](../../backend/health.py:481) | Comprehensive status of all subsystems |

**Response model** (`/health/ready`):
```json
{
  "status": "ok",
  "checks": {
    "redis": {"status": "ok", "latency_ms": 1.2},
    "clickhouse": {"status": "ok", "latency_ms": 3.4},
    "postgres": {"status": "ok", "latency_ms": 2.1},
    "minio": {"status": "ok", "latency_ms": 5.6},
    "chromadb": {"status": "ok", "latency_ms": 8.9}
  }
}
```

---

## 2. Authentication

**Source**: [`backend/auth.py`](../../backend/auth.py) · [`AuthManager`](../../backend/auth.py:75)

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| POST | `/api/auth/register` | [`register()`](../../backend/auth.py:429) | Register new user account |
| POST | `/api/auth/login` | [`login()`](../../backend/auth.py:440) | Authenticate, return JWT + refresh token |
| POST | `/api/auth/verify` | [`verify()`](../../backend/auth.py:452) | Verify JWT token validity |
| POST | `/api/auth/logout` | [`logout()`](../../backend/auth.py:465) | Revoke session |
| GET | `/api/auth/sessions` | [`get_sessions()`](../../backend/auth.py:474) | List active sessions |
| POST | `/api/auth/refresh` | [`refresh_token()`](../../backend/auth.py:488) | Rotate access token via refresh token |

**Models**:
- [`RegisterRequest`](../../backend/auth.py:47): `username`, `password`, `email`
- [`LoginRequest`](../../backend/auth.py:53): `username`, `password`
- [`RefreshTokenRequest`](../../backend/auth.py:58): `refresh_token`
- [`AuthSession`](../../backend/auth.py:62): `session_id`, `user_id`, `created_at`, `expires_at`, `ip_address`, `user_agent`

**Error codes**: 401 Unauthorized, 403 Lockout, 409 Duplicate user

---

## 3. Override Engine

**Source**: [`backend/deployment.py`](../../backend/deployment.py) (override_router)

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| POST | `/api/override/approve` | [`api_approve_override()`](../../backend/deployment.py:223) | Approve a pending human override |
| POST | `/api/override/reject` | [`api_reject_override()`](../../backend/deployment.py:239) | Reject a pending human override |
| POST | `/api/override/escalate` | [`api_escalate_override()`](../../backend/deployment.py:255) | Escalate to next tier |
| GET | `/api/override/pending` | [`api_list_pending_overrides()`](../../backend/deployment.py:271) | List all pending override requests |

**Models**:
- [`OverrideActionRequest`](../../backend/deployment.py:182): `proposal_id`, `human_id`, `decision` (`approve`/`reject`), `reason`
- [`OverrideActionResponse`](../../backend/deployment.py:188): `status`, `request_id`, `message`, `timestamp`
- [`PendingOverrideItem`](../../backend/deployment.py:203): `request_id`, `proposal_id`, `trigger`, `tier`, `status`, `created_at`
- [`PendingOverridesResponse`](../../backend/deployment.py:217): `overrides`, `total`

---

## 4. Deployment / Release

**Source**: [`backend/deployment.py`](../../backend/deployment.py)

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/api/deploy/status` | [`get_deployment_status()`](../../backend/deployment.py:136) | Current deployment state |
| GET | `/api/deploy/targets` | [`list_targets()`](../../backend/deployment.py:158) | Available deployment targets |
| POST | `/api/deploy/build` | [`build_artifact()`](../../backend/deployment.py:42) | Build deployment artifact |
| POST | `/api/deploy/rollback` | [`rollback_release()`](../../backend/deployment.py:106) | Rollback to previous version |
| POST | `/api/deploy/release` | [`package_release()`](../../backend/deployment.py:95) | Package and mark as release |
| GET | `/api/deploy/releases` | (inline) | List all releases |
| GET | `/api/release/current` | (inline) | Get current active release |

---

## 5. Mesh Network

**Source**: [`backend/mesh.py`](../../backend/mesh.py) · [`setup_mesh_routes()`](../../backend/mesh.py:19)

### 5.1 Discovery

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/mesh/discover` | [`discover_nodes()`](../../backend/mesh.py:75) |
| GET | `/api/mesh/discovered` | [`get_discovered_nodes()`](../../backend/mesh.py:109) |
| POST | `/api/mesh/discovery/start` | [`start_discovery()`](../../backend/mesh.py:129) |
| POST | `/api/mesh/discovery/stop` | [`stop_discovery()`](../../backend/mesh.py:140) |

### 5.2 Node Registry

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/mesh/nodes/register` | [`register_node()`](../../backend/mesh.py:152) |
| GET | `/api/mesh/nodes/{node_id}` | [`get_node()`](../../backend/mesh.py:172) |
| GET | `/api/mesh/nodes` | [`get_nodes()`](../../backend/mesh.py:197) |
| PUT | `/api/mesh/nodes/{node_id}/trust` | [`set_trust_level()`](../../backend/mesh.py:233) |
| GET | `/api/mesh/nodes/stats` | [`get_node_stats()`](../../backend/mesh.py:248) |

### 5.3 DHT Operations

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/mesh/dht/store` | [`dht_store()`](../../backend/mesh.py:260) |
| GET | `/api/mesh/dht/get/{key}` | [`dht_get()`](../../backend/mesh.py:272) |
| GET | `/api/mesh/dht/stats` | [`get_dht_stats()`](../../backend/mesh.py:286) |

### 5.4 P2P Connections

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/mesh/p2p/connect/{peer_id}` | [`connect_peer()`](../../backend/mesh.py:298) |
| POST | `/api/mesh/p2p/disconnect/{peer_id}` | [`disconnect_peer()`](../../backend/mesh.py:308) |
| GET | `/api/mesh/p2p/connections` | [`get_connections()`](../../backend/mesh.py:318) |
| GET | `/api/mesh/p2p/stats` | [`get_p2p_stats()`](../../backend/mesh.py:337) |

### 5.5 CRDT Sync

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/mesh/sync/state` | [`get_sync_state()`](../../backend/mesh.py:349) |
| POST | `/api/mesh/sync/apply` | [`apply_sync_state()`](../../backend/mesh.py:359) |
| GET | `/api/mesh/sync/crdts` | [`get_crdts()`](../../backend/mesh.py:370) |

### 5.6 Relay & Bootstrap

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/mesh/relay/sessions` | [`get_relay_sessions()`](../../backend/mesh.py:382) |
| GET | `/api/mesh/relay/stats` | [`get_relay_stats()`](../../backend/mesh.py:401) |
| GET | `/api/mesh/bootstrap/nodes` | [`get_bootstrap_nodes()`](../../backend/mesh.py:413) |
| POST | `/api/mesh/bootstrap` | [`bootstrap()`](../../backend/mesh.py:440) |
| GET | `/api/mesh/bootstrap/stats` | [`get_bootstrap_stats()`](../../backend/mesh.py:462) |

### 5.7 Status

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/mesh/status` | [`get_mesh_status()`](../../backend/mesh.py:474) |

**Models**:
- [`DiscoveryRequest`](../../backend/mesh.py:41): `discovery_type`, `timeout`, `node_types`
- [`NodeRegistrationRequest`](../../backend/mesh.py:46): `node_id`, `node_type`, `addresses`
- [`TrustLevelRequest`](../../backend/mesh.py:54): `trust_level`
- [`DHTStoreRequest`](../../backend/mesh.py:59): `key`, `value`, `ttl`

---

## 6. Clones & Consensus

**Source**: [`backend/clones.py`](../../backend/clones.py)

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/clones` | [`get_clones()`](../../backend/clones.py:57) |
| GET | `/api/clones/{clone_id}` | [`get_clone()`](../../backend/clones.py:78) |
| GET | `/api/clones/available` | [`get_available_clones()`](../../backend/clones.py:102) |
| GET | `/api/clones/skill/{skill}` | [`get_clones_by_skill()`](../../backend/clones.py:122) |
| POST | `/api/clones/task` | [`create_task()`](../../backend/clones.py:142) |
| POST | `/api/clones/task/{task_id}/assign` | [`assign_task()`](../../backend/clones.py:164) |
| POST | `/api/clones/task/{task_id}/complete` | [`complete_task()`](../../backend/clones.py:183) |
| POST | `/api/clones/consensus` | [`create_consensus()`](../../backend/clones.py:202) |
| POST | `/api/clones/consensus/{decision_id}/vote` | [`cast_vote()`](../../backend/clones.py:238) |
| GET | `/api/clones/consensus/{decision_id}` | [`get_consensus()`](../../backend/clones.py:263) |
| GET | `/api/clones/status` | [`get_clones_status()`](../../backend/clones.py:296) |

---

## 7. Chat

**Source**: [`backend/chat.py`](../../backend/chat.py)

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/chat/session` | [`create_session()`](../../backend/chat.py:300) |
| GET | `/api/chat/sessions/{user_id}` | [`get_sessions()`](../../backend/chat.py:316) |
| GET | `/api/chat/session/{session_id}` | [`get_session()`](../../backend/chat.py:335) |
| POST | `/api/chat/message` | [`send_message()`](../../backend/chat.py:355) |
| GET | `/api/chat/messages/{session_id}` | [`get_messages()`](../../backend/chat.py:390) |
| DELETE | `/api/chat/session/{session_id}` | [`delete_session()`](../../backend/chat.py:410) |
| GET | `/api/chat/stats` | [`get_stats()`](../../backend/chat.py:424) |

---

## 8. Learning & Training

**Source**: [`backend/learning.py`](../../backend/learning.py)

### 8.1 Dataset

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/learning/dataset/capture` | [`capture_sample()`](../../backend/learning.py:99) |
| POST | `/api/learning/dataset/label/{sample_id}` | [`label_sample()`](../../backend/learning.py:114) |
| POST | `/api/learning/dataset/snapshot` | [`create_snapshot()`](../../backend/learning.py:130) |
| GET | `/api/learning/dataset/snapshots` | [`get_snapshots()`](../../backend/learning.py:150) |
| GET | `/api/learning/dataset/snapshot/{snapshot_id}` | [`get_snapshot()`](../../backend/learning.py:171) |
| GET | `/api/learning/dataset/stats` | [`get_dataset_stats()`](../../backend/learning.py:185) |

### 8.2 Training Jobs

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/learning/training/job` | [`create_training_job()`](../../backend/learning.py:197) |
| POST | `/api/learning/training/job/{job_id}/start` | [`start_training()`](../../backend/learning.py:219) |
| POST | `/api/learning/training/job/{job_id}/complete` | [`complete_training()`](../../backend/learning.py:233) |
| POST | `/api/learning/training/job/{job_id}/cancel` | [`cancel_training()`](../../backend/learning.py:247) |
| GET | `/api/learning/training/jobs` | [`get_training_jobs()`](../../backend/learning.py:261) |
| GET | `/api/learning/training/job/{job_id}` | [`get_training_job()`](../../backend/learning.py:285) |
| GET | `/api/learning/training/stats` | [`get_training_stats()`](../../backend/learning.py:299) |

### 8.3 Evaluation

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/learning/evaluator/golden-dataset` | [`create_golden_dataset()`](../../backend/learning.py:311) |
| GET | `/api/learning/evaluator/golden-datasets` | [`get_golden_datasets()`](../../backend/learning.py:344) |
| POST | `/api/learning/evaluator/evaluation` | [`create_evaluation()`](../../backend/learning.py:363) |
| POST | `/api/learning/evaluator/evaluation/{evaluation_id}/start` | [`start_evaluation()`](../../backend/learning.py:381) |
| POST | `/api/learning/evaluator/evaluation/{evaluation_id}/complete` | [`complete_evaluation()`](../../backend/learning.py:395) |
| GET | `/api/learning/evaluator/evaluations` | [`get_evaluations()`](../../backend/learning.py:409) |
| GET | `/api/learning/evaluator/can-promote/{adapter_id}` | [`can_promote()`](../../backend/learning.py:432) |
| GET | `/api/learning/evaluator/stats` | [`get_evaluator_stats()`](../../backend/learning.py:442) |

### 8.4 Adapters

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/learning/adapter/register` | [`register_adapter()`](../../backend/learning.py:454) |
| PUT | `/api/learning/adapter/{adapter_id}/version/{version}/status` | [`update_adapter_status()`](../../backend/learning.py:475) |
| POST | `/api/learning/adapter/{adapter_id}/version/{version}/promote` | [`promote_adapter()`](../../backend/learning.py:490) |
| POST | `/api/learning/adapter/{adapter_id}/rollback` | [`rollback_adapter()`](../../backend/learning.py:507) |
| GET | `/api/learning/adapters` | [`get_adapters()`](../../backend/learning.py:521) |
| GET | `/api/learning/adapter/{adapter_id}` | [`get_adapter()`](../../backend/learning.py:545) |
| GET | `/api/learning/adapter/{adapter_id}/versions` | [`get_adapter_versions()`](../../backend/learning.py:559) |
| GET | `/api/learning/adapter/{adapter_id}/production` | [`get_production_adapter()`](../../backend/learning.py:569) |
| GET | `/api/learning/adapter/rollback-history` | [`get_rollback_history()`](../../backend/learning.py:583) |
| GET | `/api/learning/adapter/stats` | [`get_adapter_stats()`](../../backend/learning.py:603) |

### 8.5 Router

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/learning/router/load` | [`load_adapter()`](../../backend/learning.py:615) |
| POST | `/api/learning/router/swap` | [`swap_adapter()`](../../backend/learning.py:636) |
| GET | `/api/learning/router/status` | [`get_router_status()`](../../backend/learning.py:653) |
| GET | `/api/learning/router/loaded-adapters` | [`get_loaded_adapters()`](../../backend/learning.py:663) |
| GET | `/api/learning/router/swap-history` | [`get_swap_history()`](../../backend/learning.py:673) |

### 8.6 Status

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/learning/status` | [`get_learning_status()`](../../backend/learning.py:685) |

---

## 9. Memory

**Source**: [`backend/memory.py`](../../backend/memory.py)

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/memory/add` | [`add_memory()`](../../backend/memory.py:44) |
| GET | `/api/memory/{memory_id}` | [`get_memory()`](../../backend/memory.py:73) |
| POST | `/api/memory/search` | [`search_memory()`](../../backend/memory.py:97) |
| GET | `/api/memory/user/{user_id}` | [`get_user_memories()`](../../backend/memory.py:137) |
| DELETE | `/api/memory/{memory_id}` | [`delete_memory()`](../../backend/memory.py:169) |
| GET | `/api/memory/stats` | [`get_memory_stats()`](../../backend/memory.py:183) |
| POST | `/api/memory/prune` | [`prune_memories()`](../../backend/memory.py:193) |

---

## 10. Model Registry

**Source**: [`backend/registry.py`](../../backend/registry.py)

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/registry/register` | [`register_model()`](../../backend/registry.py:363) |
| GET | `/api/registry/active/{name}` | [`get_active_model()`](../../backend/registry.py:380) |
| GET | `/api/registry/versions/{name}` | [`list_versions()`](../../backend/registry.py:389) |
| GET | `/api/registry/{name}/{version}` | [`get_model()`](../../backend/registry.py:400) |
| POST | `/api/registry/rollback/{name}` | [`rollback_model()`](../../backend/registry.py:409) |
| GET | `/api/registry/verify/{name}/{version}` | [`verify_integrity()`](../../backend/registry.py:420) |
| GET | `/api/registry/status` | [`get_registry_status()`](../../backend/registry.py:427) |

---

## 11. Router / LLM

**Source**: [`backend/router.py`](../../backend/router.py)

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/router/route` | [`route_prompt()`](../../backend/router.py:231) |
| POST | `/api/router/chat` | [`chat_prompt()`](../../backend/router.py:237) |
| GET | `/api/router/metrics` | [`get_metrics()`](../../backend/router.py:249) |

---

## 12. Tools / OS Control

**Source**: [`backend/tools.py`](../../backend/tools.py)

### 12.1 Tools Module

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/tools/execute` | [`execute_tool()`](../../backend/tools.py:300) |
| GET | `/api/tools/pending` | [`get_pending()`](../../backend/tools.py:311) |
| POST | `/api/tools/approve` | [`approve_tool()`](../../backend/tools.py:315) |
| GET | `/api/tools/audit` | [`get_audit()`](../../backend/tools.py:328) |

### 12.2 OS Tools

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/os/tools` | [`list_os_tools()`](../../backend/tools.py:358) |
| POST | `/api/os/execute` | [`execute_os_tool()`](../../backend/tools.py:367) |
| GET | `/api/os/audit` | [`get_os_audit()`](../../backend/tools.py:389) |

---

## 13. Observability

**Source**: [`backend/observability.py`](../../backend/observability.py)

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/observability/telemetry` | [`get_telemetry_endpoint()`](../../backend/observability.py:29) |
| GET | `/api/observability/posture` | [`get_posture_endpoint()`](../../backend/observability.py:34) |
| GET | `/api/observability/metrics` | [`get_metrics_endpoint()`](../../backend/observability.py:39) |
| GET | `/api/observability/traces` | [`get_traces_endpoint()`](../../backend/observability.py:60) |
| GET | `/api/observability/audit` | [`get_audit_endpoint()`](../../backend/observability.py:70) |
| POST | `/api/observability/event` | [`post_event_endpoint()`](../../backend/observability.py:74) |
| GET | `/api/observability/health` | [`get_health_endpoint()`](../../backend/observability.py:91) |
| GET | `/api/observability/status` | [`get_status_endpoint()`](../../backend/observability.py:95) |

---

## 14. Simple Backend Routes (Legacy / Universal)

**Source**: [`simple_backend.py`](../../simple_backend.py)

### 14.1 System & Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Lightweight health check |
| GET | `/health` | Health status |
| GET | `/api/status` | Health status (alias) |
| GET | `/api/db/health` | Database health |
| GET | `/status` | Detailed status |
| GET | `/api/system/info` | System information |
| GET | `/api/local-llm/health` | LLM health (alias) |
| GET | `/api/version` | API version |
| GET | `/api/build` | Build info |

### 14.2 Dharma (Ethics / ΔT Engine)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dharma/status` | Dharma engine status |
| GET | `/api/dharma/production/status` | Production ΔT status |
| POST | `/api/dharma/veto` | Submit veto |
| POST | `/api/dharma/veto-check` | Check veto applicability |
| POST | `/api/dharma/cultural-check` | Cultural compliance check |
| GET | `/api/dharma/veto-status` | Veto system status |
| GET | `/api/dharma/veto/config` | Get veto configuration |
| POST | `/api/dharma/veto/config` | Update veto configuration |
| GET | `/api/dharma/veto/pending` | List pending vetos |
| GET | `/api/dharma/veto/history` | Veto history |
| POST | `/api/dharma/veto/release/{record_id}` | Release a veto record |
| GET | `/api/dharma/enforcement/status` | Enforcement status |
| GET | `/api/dharma/influence/status` | Influence tracker status |
| GET | `/api/dharma/influence/history` | Influence history |
| POST | `/api/dharma/influence/record` | Record influence event |
| POST | `/api/dharma/veto/manual` | Manual veto input |
| POST | `/api/dharma/monitoring/start` | Start ΔT monitoring |
| POST | `/api/dharma/monitoring/stop` | Stop ΔT monitoring |
| GET | `/api/dharma/mesh/status` | ΔT mesh status |

### 14.3 Chat / LLM

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Universal chat endpoint |
| POST | `/llm/chat` | LLM chat (alias) |
| POST | `/api/chat` | API chat (alias) |

### 14.4 Brain (AI Processor)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/brain/process` | Process input through AI |
| POST | `/api/brain/stream` | Stream AI response |

### 14.5 Personal / Clones

| Method | Path | Description |
|--------|------|-------------|
| GET | `/personal/status` | Personal universe status |
| GET | `/personal/clones` | Personal clones list |
| GET | `/api/clones` | Clones list (alias) |
| GET | `/api/clones/specs` | Clone specialization specs |
| GET | `/api/clones/{clone_id}/spec` | Get clone spec |
| POST | `/api/clones/route` | Route request to clone |

### 14.6 Memory / History

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/memory/stats` | Memory statistics |
| GET | `/api/memory/recent` | Recent memories |
| GET | `/api/memory/search` | Search memories |
| DELETE | `/api/memory/{message_id}` | Delete memory entry |
| GET | `/api/db/conversations/user/{user_id}` | User conversations |

### 14.7 API Keys

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/db/api-keys/{user_id}` | Get API keys |
| POST | `/api/keys/update` | Update API key |

### 14.8 Mesh (Legacy)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/mesh/nodes` | Mesh nodes (legacy) |
| GET | `/api/mesh/nodes` | Mesh nodes (alias) |
| GET | `/api/mesh/discovery/status` | Discovery status |
| POST | `/api/mesh/discover/start` | Start mesh discovery |
| POST | `/api/mesh/discover/add-peer` | Add peer manually |
| GET | `/api/mesh/peers` | Connected peers |

### 14.9 Air-Gap / Sovereignty

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/mesh/air-gap/engage` | Engage air-gap |
| POST | `/api/mesh/air-gap/disengage` | Disengage air-gap |
| GET | `/api/mesh/air-gap/check` | Check air-gap status |
| GET | `/api/sovereignty/airgap/status` | Air-gap status |
| POST | `/api/sovereignty/airgap/activate` | Activate air-gap |
| POST | `/api/sovereignty/airgap/restore` | Restore from air-gap |
| GET | `/api/sovereignty/airgap/history` | Air-gap event history |
| POST | `/api/sovereignty/check` | Cultural compliance check |
| GET | `/api/sovereignty/countries` | List sovereign countries |
| GET | `/api/sovereignty/country/{country_code}` | Country profile |
| GET | `/api/sovereignty/report` | Sovereignty report |

### 14.10 Jobs / Marketplace

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/jobs/post` | Post a job |
| GET | `/api/jobs/list` | List jobs |
| GET | `/api/jobs/stats` | Job statistics |
| GET | `/api/jobs/{job_id}` | Get job details |
| POST | `/api/jobs/{job_id}/apply` | Apply to job |
| POST | `/api/jobs/{job_id}/rate` | Rate job completion |

### 14.11 Dreaming Engine

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dreaming/status` | Dreaming engine status |
| GET | `/api/dreaming/briefing` | Dreaming briefing |
| POST | `/api/dreaming/trigger` | Trigger dreaming cycle |

### 14.12 Smart Contracts (HDT)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/contracts/propose` | Propose contract |
| POST | `/api/contracts/{contract_id}/gate2` | Level-2 gate for contract |
| POST | `/api/contracts/{contract_id}/sign` | Sign contract |
| POST | `/api/contracts/{contract_id}/progress` | Update progress |
| POST | `/api/contracts/{contract_id}/pause` | Pause contract |
| POST | `/api/contracts/{contract_id}/resume` | Resume contract |
| POST | `/api/contracts/{contract_id}/cancel` | Cancel contract |
| POST | `/api/contracts/{contract_id}/complete` | Complete contract |
| GET | `/api/contracts/{contract_id}` | Get contract |
| GET | `/api/contracts` | List contracts |

### 14.13 Theme / Universe

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/theme/set` | Set theme |
| POST | `/api/universe/set` | Set universe config |
| POST | `/api/universe/create` | Create universe |
| GET | `/api/universe/list` | List universes |
| GET | `/api/universe/status` | Universe status |
| GET | `/api/universe/{user_id}/status` | User universe status |
| POST | `/api/universe/{user_id}/layer/activate` | Activate universe layer |
| POST | `/api/universe/{user_id}/archive` | Archive universe |
| POST | `/api/universe/{user_id}/reactivate` | Reactivate universe |
| GET | `/api/universe/{user_id}/lifecycle` | Universe lifecycle |
| GET | `/api/universe/stats` | Universe statistics |
| GET | `/api/universe/containers` | Universe containers |
| POST | `/api/universe/data-flow-check` | Check data flow rules |

### 14.14 API Status / Analytics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/apis/status` | All APIs aggregated status |
| GET | `/api/analytics/overview` | Analytics overview |
| GET | `/api/analytics` | Analytics (alias) |
| GET | `/api/analytics/activity` | Activity analytics |

### 14.15 Bugs / Triage

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/bugs/stats` | Bug statistics |
| POST | `/api/bugs/report` | Report a bug |
| GET | `/api/bugs/pending` | Pending bugs |
| POST | `/api/bugs/{bug_id}/approve` | Approve bug fix |
| GET | `/api/bugs/list` | List bugs |
| POST | `/api/bugs/batch-triage` | Batch triage bugs |

### 14.16 Identity / DIDs

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/identity/create` | Create DID |
| POST | `/api/identity/verify` | Verify identity |
| POST | `/api/identity/{did}/credential` | Issue verifiable credential |
| GET | `/api/identity/{did}/credentials` | List VCs |
| GET | `/api/identity/status` | Identity system status |
| GET | `/api/identity/stats` | Identity statistics |
| GET | `/api/identity/list` | List DIDs |

### 14.17 Cognitive Firewall

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/firewall/check` | Check prompt against firewall |
| POST | `/api/firewall/check-conversation` | Check conversation context |
| GET | `/api/firewall/status` | Firewall status |

### 14.18 DHT / Kademlia

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dht/status` | DHT status |
| POST | `/api/dht/bootstrap` | Bootstrap DHT node |
| POST | `/api/dht/announce` | Announce capability |
| GET | `/api/dht/find` | Find nodes by capability |

### 14.19 Human Digital Twin (HDT)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/hdt/create` | Create HDT |
| POST | `/api/hdt/{did}/skill` | Add skill to HDT |
| POST | `/api/hdt/{did}/announce` | Announce HDT |
| GET | `/api/hdt/{did}/status` | HDT status |
| GET | `/api/hdt/{did}/profile` | HDT profile |
| GET | `/api/hdt/status` | Global HDT status |

### 14.20 Consensus (Simple)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/consensus/vote` | Cast consensus vote |
| POST | `/api/consensus/{round_id}/override` | Override consensus round |
| GET | `/api/consensus/stats` | Consensus statistics |
| GET | `/api/consensus/pending` | Pending consensus rounds |
| GET | `/api/consensus/list` | List consensus rounds |

### 14.21 Sovereign Token (SVT)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/svt/stats` | SVT statistics |
| POST | `/api/svt/wallet` | Create SVT wallet |
| GET | `/api/svt/wallet/{did}` | Wallet info |
| POST | `/api/svt/mint` | Mint SVT tokens |
| POST | `/api/svt/transfer` | Transfer SVT |
| POST | `/api/svt/escrow` | Create escrow |
| POST | `/api/svt/escrow/{eid}/release` | Release escrow |

### 14.22 Quad Mesh

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/quad/status` | Quad mesh status |
| POST | `/api/quad/join` | Join quad mesh |
| GET | `/api/quad/{layer}/peers` | Quad mesh peers by layer |
| POST | `/api/quad/send` | Send via quad mesh |

### 14.23 Zero Trust Runtime

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/runtime/status` | Runtime status |
| POST | `/api/runtime/register` | Register principal |
| GET | `/api/runtime/principals` | List principals |
| GET | `/api/runtime/violations` | List violations |

### 14.24 Self-Evolution

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/evolution/stats` | Evolution statistics |
| POST | `/api/evolution/propose` | Propose evolution patch |
| POST | `/api/evolution/{patch_id}/validate` | Validate patch |
| POST | `/api/evolution/{patch_id}/decide` | Decide on patch |

### 14.25 DePIN

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/depin/status` | DePIN status |
| POST | `/api/depin/register` | Register DePIN node |
| POST | `/api/depin/{node_id}/collect` | Collect from node |

### 14.26 Federation

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/federation/status` | Federation status |
| POST | `/api/federation/peer` | Add federation peer |
| POST | `/api/federation/consent/{peer_id}` | Grant consent |
| GET | `/api/federation/sync-packet` | Get sync packet |

### 14.27 Event Bus

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/events/stats` | Event bus statistics |
| POST | `/api/events/publish` | Publish event |
| GET | `/api/events/recent` | Recent events |
| GET | `/api/events/dlq` | Dead letter queue |

### 14.28 Post-Quantum

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/pq/status` | PQC system status |
| POST | `/api/pq/keygen` | Generate PQC keypair |
| POST | `/api/pq/sign` | Sign with PQC |
| POST | `/api/pq/kem` | KEM encapsulate |

### 14.29 Offline Sync

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sync/status` | Sync status |
| POST | `/api/sync/enqueue` | Enqueue sync operation |
| POST | `/api/sync/flush` | Flush sync queue |
| GET | `/api/sync/queue` | View sync queue |

### 14.30 Nepal Layer

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/nepal/status` | Nepal layer status |

### 14.31 Personal Universe

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/personal/status` | Personal universe status |
| GET | `/api/personal/universe` | Personal universe config |
| GET | `/api/personal/contracts` | Personal contracts |
| POST | `/api/personal/resource-sharing` | Set resource sharing |
| GET | `/api/personal/resource-sharing` | Get resource sharing |

### 14.32 Agent Mode

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/agent/mode/on` | Enable agent mode |
| POST | `/api/agent/mode/off` | Disable agent mode |
| GET | `/api/agent/status` | Agent mode status |

### 14.33 MCP (Model Context Protocol)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/mcp/tools` | List MCP tools |
| POST | `/api/mcp/call` | Call MCP tool |
| POST | `/api/mcp/approve/{call_id}` | Approve MCP call |
| POST | `/api/mcp/reject/{call_id}` | Reject MCP call |
| GET | `/api/mcp/pending` | Pending MCP calls |
| GET | `/api/mcp/audit` | MCP audit log |
| GET | `/api/mcp/status` | MCP system status |

### 14.34 Self-Healing

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/healing/status` | Healing system status |
| POST | `/api/healing/heal` | Trigger self-heal |
| GET | `/api/healing/bugs` | Healing bugs list |
| GET | `/api/healing/connection` | Connection health |
| GET | `/api/healing/balance` | System balance check |
| POST | `/api/healing/fix-connections` | Fix broken connections |

### 14.35 Universal Systems

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/universal/status` | Universal systems status |
| GET | `/api/universal/currencies` | Supported currencies |
| GET | `/api/universal/currencies/{country_code}` | Country currencies |
| POST | `/api/universal/currency/convert` | Currency conversion |
| GET | `/api/universal/countries` | All countries |
| GET | `/api/universal/countries/{country_code}` | Country details |
| GET | `/api/universal/languages` | Supported languages |
| GET | `/api/universal/languages/{lang_code}` | Language details |
| GET | `/api/universal/timezones` | Timezone list |
| GET | `/api/universal/timezones/{country_code}` | Country timezones |
| GET | `/api/universal/meeting-times` | Meeting time planner |

### 14.36 Global Infrastructure

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/infrastructure/status` | Infrastructure status |
| GET | `/api/infrastructure/cdn/locations` | CDN locations |
| GET | `/api/infrastructure/cdn/routing/{country_code}` | CDN routing |
| GET | `/api/infrastructure/cdn/nearest` | Nearest CDN node |
| GET | `/api/infrastructure/mesh/status` | Mesh infrastructure status |
| GET | `/api/infrastructure/mesh/nodes` | Mesh nodes (infra) |
| GET | `/api/infrastructure/mesh/nodes/{node_id}` | Mesh node detail |
| POST | `/api/infrastructure/mesh/join` | Join mesh (infra) |
| GET | `/api/infrastructure/mesh/sovereign-nodes` | Sovereign nodes list |
| POST | `/api/infrastructure/mesh/sync` | Sync mesh state |

### 14.37 Platform / Multi-Device

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/platform/status` | Platform status |
| POST | `/api/platform/register` | Register device |
| GET | `/api/platform/downloads` | Platform downloads |
| GET | `/api/pwa/config` | PWA config |
| POST | `/api/push/subscribe` | Subscribe push notifications |
| POST | `/api/push/send` | Send push notification |
| GET | `/api/offline/data` | Offline data cache |
| POST | `/api/offline/sync` | Sync offline data |

### 14.38 Finance

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/finance/status` | Finance system status |
| GET | `/api/finance/payment-methods/{country}` | Country payment methods |
| POST | `/api/finance/wallet/create` | Create wallet |
| GET | `/api/finance/wallet/{user_id}` | Get wallet |
| GET | `/api/finance/exchange-rates` | Exchange rates |
| POST | `/api/finance/convert` | Convert currency |
| GET | `/api/finance/currencies` | Supported currencies |
| GET | `/api/finance/banking/regions` | Banking regions |
| GET | `/api/finance/banking/banks/{country}` | Banks by country |
| POST | `/api/finance/payment/create` | Create payment |
| POST | `/api/finance/crypto/address` | Generate crypto address |
| GET | `/api/finance/stats` | Finance statistics |

### 14.39 Government Integration

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/government/status` | Government integration status |
| GET | `/api/government/identity/countries` | Supported countries |
| POST | `/api/government/identity/create` | Create government ID |
| POST | `/api/government/identity/verify` | Verify government ID |
| GET | `/api/government/eresidency/programs` | e-Residency programs |
| POST | `/api/government/eresidency/apply` | Apply for e-Residency |
| GET | `/api/government/tax/countries` | Tax countries |
| POST | `/api/government/tax/calculate` | Calculate tax |
| POST | `/api/government/tax/prepare` | Prepare tax return |
| GET | `/api/government/services/{country}` | Government services |
| GET | `/api/government/signatures/regions` | Signature regions |
| GET | `/api/government/stats` | Government statistics |

### 14.40 Mesh Network (Extended)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/mesh/status` | Mesh network status |
| POST | `/api/mesh/node/init` | Initialize mesh node |
| GET | `/api/mesh/nodes/discover` | Discover mesh nodes |
| GET | `/api/mesh/stats` | Mesh statistics |
| POST | `/api/mesh/federation/join` | Join mesh federation |
| GET | `/api/mesh/federation/map` | Federation map |
| POST | `/api/mesh/clone/sync` | Sync clone via mesh |
| GET | `/api/mesh/clone/status/{user_id}` | Clone sync status |
| POST | `/api/mesh/storage/store` | Store in mesh |
| POST | `/api/mesh/offline/operation` | Create offline operation |
| GET | `/api/mesh/offline/status/{user_id}` | Offline sync status |
| GET | `/api/mesh/offline/capabilities` | Offline capabilities |
| GET | `/api/system/complete` | Complete system status |

### 14.41 Level-3 Confirmation (Biometric)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/confirm/level3/initiate` | Initiate Level-3 check |
| POST | `/api/confirm/level3/biometric/request` | Request biometric verification |
| POST | `/api/confirm/level3/biometric/verify` | Verify biometric |
| GET | `/api/confirm/level3/status/{confirmation_id}` | Confirmation status |

### 14.42 OS Control (Simple Backend)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/os/tools` | List OS tools |
| POST | `/api/os/execute` | Execute OS tool |
| POST | `/api/os/approve/{call_id}` | Approve OS execution |
| POST | `/api/os/reject/{call_id}` | Reject OS execution |
| GET | `/api/os/pending` | Pending OS requests |
| GET | `/api/os/audit` | OS audit log |
| GET | `/api/os/status` | OS control status |
| GET | `/api/os/metrics` | OS metrics |
| GET | `/api/os/clipboard/status` | Clipboard status |

### 14.43 Socket.IO Stub

| Method | Path | Description |
|--------|------|-------------|
| GET | `/socket.io/` | Prevents 403 WebSocket errors |

---

## 15. Route Group Summary

| Prefix | Count | Source |
|--------|-------|--------|
| `/health/*` | 3 | [`backend/health.py`](../../backend/health.py) |
| `/api/auth/*` | 6 | [`backend/auth.py`](../../backend/auth.py) |
| `/api/override/*` | 4 | [`backend/deployment.py`](../../backend/deployment.py) |
| `/api/deploy/*` | 7 | [`backend/deployment.py`](../../backend/deployment.py) |
| `/api/mesh/*` | 25 | [`backend/mesh.py`](../../backend/mesh.py) |
| `/api/clones/*` | 11 | [`backend/clones.py`](../../backend/clones.py) |
| `/api/chat/*` | 7 | [`backend/chat.py`](../../backend/chat.py) |
| `/api/learning/*` | 37 | [`backend/learning.py`](../../backend/learning.py) |
| `/api/memory/*` | 7 | [`backend/memory.py`](../../backend/memory.py) |
| `/api/registry/*` | 7 | [`backend/registry.py`](../../backend/registry.py) |
| `/api/router/*` | 3 | [`backend/router.py`](../../backend/router.py) |
| `/api/tools/*` | 4 | [`backend/tools.py`](../../backend/tools.py) |
| `/api/os/*` | 3 | [`backend/tools.py`](../../backend/tools.py) |
| `/api/observability/*` | 8 | [`backend/observability.py`](../../backend/observability.py) |
| Various (simple) | ~140+ | [`simple_backend.py`](../../simple_backend.py) |
| **Total** | **~270+** | **All sources** |

---

## 16. Common Patterns

### 16.1 Authentication Header

Most protected endpoints expect:
```
Authorization: Bearer <jwt_token>
```

### 16.2 Error Response Format

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### 16.3 Health Check Response

```json
{
  "status": "ok" | "degraded" | "error",
  "checks": { "<service>": {"status": "ok", "latency_ms": <float>} },
  "timestamp": "2026-06-01T20:00:00Z"
}
```

---

## References

- [`backend/health.py`](../../backend/health.py) — Health probe endpoints
- [`backend/auth.py`](../../backend/auth.py) — Authentication endpoints
- [`backend/deployment.py`](../../backend/deployment.py) — Override + deployment endpoints
- [`backend/mesh.py`](../../backend/mesh.py) — Mesh network endpoints
- [`backend/clones.py`](../../backend/clones.py) — Clone management endpoints
- [`backend/chat.py`](../../backend/chat.py) — Chat session endpoints
- [`backend/learning.py`](../../backend/learning.py) — ML pipeline endpoints
- [`backend/memory.py`](../../backend/memory.py) — Memory storage endpoints
- [`backend/registry.py`](../../backend/registry.py) — Model registry endpoints
- [`backend/router.py`](../../backend/router.py) — LLM routing endpoints
- [`backend/tools.py`](../../backend/tools.py) — Tool execution endpoints
- [`backend/observability.py`](../../backend/observability.py) — Observability endpoints
- [`simple_backend.py`](../../simple_backend.py) — Legacy/universal endpoints
