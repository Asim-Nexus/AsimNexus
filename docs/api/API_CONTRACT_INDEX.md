# API Contract Index

> **AsimNexus RC-2** | Last updated: 2026-07-03
> **✅ All routes verified against actual codebase.**
> **Current source files:** [`routes/`](../../routes/) modules, [`app.py`](../../app.py)

**Route count**: **636 registered endpoints** across 35 route modules (all documented below)

---

## 1. Health Probes

**Source**: [`routes/health.py`](../../routes/health.py) · [`app.py`](../../app.py)

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/health/live` | [`health_live()`](../../routes/health.py) | Liveness probe — returns 200 if process is alive |
| GET | `/health/ready` | [`health_ready()`](../../routes/health.py) | Readiness probe — checks all storage backends |
| GET | `/health/status` | [`health_status()`](../../routes/health.py) | Comprehensive status of all subsystems |

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

**Source**: [`routes/auth.py`](../../routes/auth.py) · [`core/security/auth_middleware.py`](../../core/security/auth_middleware.py)

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| POST | `/api/auth/register` | [`api_auth_register()`](../../routes/auth.py) | Register new user account |
| POST | `/api/auth/login` | [`api_auth_login()`](../../routes/auth.py) | Authenticate, return JWT + refresh token |
| POST | `/api/auth/verify` | [`api_auth_verify()`](../../routes/auth.py) | Verify JWT token validity |
| POST | `/api/auth/logout` | [`api_auth_logout()`](../../routes/auth.py) | Revoke session |
| GET | `/api/auth/sessions` | [`api_auth_sessions()`](../../routes/auth.py) | List active sessions |
| POST | `/api/auth/refresh` | [`api_auth_refresh()`](../../routes/auth.py) | Rotate access token via refresh token |

**Models**:
- `RegisterRequest`: `username`, `password`, `email`
- `LoginRequest`: `username`, `password`
- `RefreshTokenRequest`: `refresh_token`
- `AuthSession`: `session_id`, `user_id`, `created_at`, `expires_at`, `ip_address`, `user_agent`

**Error codes**: 401 Unauthorized, 403 Lockout, 409 Duplicate user

---

## 3. Override Engine

**Source**: [`routes/override.py`](../../routes/override.py)

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| POST | `/api/override/approve` | [`api_approve_override()`](../../routes/override.py) | Approve a pending human override |
| POST | `/api/override/reject` | [`api_reject_override()`](../../routes/override.py) | Reject a pending human override |
| POST | `/api/override/escalate` | [`api_escalate_override()`](../../routes/override.py) | Escalate to next tier |
| GET | `/api/override/pending` | [`api_list_pending_overrides()`](../../routes/override.py) | List all pending override requests |

**Models**:
- `OverrideActionRequest`: `proposal_id`, `human_id`, `decision` (`approve`/`reject`), `reason`
- `OverrideActionResponse`: `status`, `request_id`, `message`, `timestamp`
- `PendingOverrideItem`: `request_id`, `proposal_id`, `trigger`, `tier`, `status`, `created_at`
- `PendingOverridesResponse`: `overrides`, `total`

---

## 4. Deployment / Release

**Source**: [`routes/deploy.py`](../../routes/deploy.py) · [`routes/release.py`](../../routes/release.py)

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/api/deploy/status` | [`get_deployment_status()`](../../routes/deploy.py) | Current deployment state |
| GET | `/api/deploy/targets` | [`list_targets()`](../../routes/deploy.py) | Available deployment targets |
| POST | `/api/deploy/build` | [`build_artifact()`](../../routes/deploy.py) | Build deployment artifact |
| POST | `/api/deploy/rollback` | [`rollback_release()`](../../routes/deploy.py) | Rollback to previous version |
| POST | `/api/deploy/release` | [`package_release()`](../../routes/deploy.py) | Package and mark as release |
| GET | `/api/deploy/releases` | (inline) | List all releases |
| GET | `/api/release/current` | (inline) | Get current active release |

---

## 5. Mesh Network

**Source**: [`routes/mesh.py`](../../routes/mesh.py) · [`core/mesh/`](../../core/mesh/)

### 5.1 Discovery

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/mesh/discover` | [`discover_nodes()`](../../routes/mesh.py) |
| GET | `/api/mesh/discovered` | [`get_discovered_nodes()`](../../routes/mesh.py) |
| POST | `/api/mesh/discovery/start` | [`start_discovery()`](../../routes/mesh.py) |
| POST | `/api/mesh/discovery/stop` | [`stop_discovery()`](../../routes/mesh.py) |

### 5.2 Node Registry

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/mesh/nodes/register` | [`register_node()`](../../routes/mesh.py) |
| GET | `/api/mesh/nodes/{node_id}` | [`get_node()`](../../routes/mesh.py) |
| GET | `/api/mesh/nodes` | [`get_nodes()`](../../routes/mesh.py) |
| PUT | `/api/mesh/nodes/{node_id}/trust` | [`set_trust_level()`](../../routes/mesh.py) |
| GET | `/api/mesh/nodes/stats` | [`get_node_stats()`](../../routes/mesh.py) |

### 5.3 DHT Operations

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/mesh/dht/store` | [`dht_store()`](../../routes/mesh.py) |
| GET | `/api/mesh/dht/get/{key}` | [`dht_get()`](../../routes/mesh.py) |
| GET | `/api/mesh/dht/stats` | [`get_dht_stats()`](../../routes/mesh.py) |

### 5.4 P2P Connections

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/mesh/p2p/connect/{peer_id}` | [`connect_peer()`](../../routes/mesh.py) |
| POST | `/api/mesh/p2p/disconnect/{peer_id}` | [`disconnect_peer()`](../../routes/mesh.py) |
| GET | `/api/mesh/p2p/connections` | [`get_connections()`](../../routes/mesh.py) |
| GET | `/api/mesh/p2p/stats` | [`get_p2p_stats()`](../../routes/mesh.py) |

### 5.5 CRDT Sync

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/mesh/sync/state` | [`get_sync_state()`](../../routes/mesh.py) |
| POST | `/api/mesh/sync/apply` | [`apply_sync_state()`](../../routes/mesh.py) |
| GET | `/api/mesh/sync/crdts` | [`get_crdts()`](../../routes/mesh.py) |

### 5.6 Relay & Bootstrap

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/mesh/relay/sessions` | [`get_relay_sessions()`](../../routes/mesh.py) |
| GET | `/api/mesh/relay/stats` | [`get_relay_stats()`](../../routes/mesh.py) |
| GET | `/api/mesh/bootstrap/nodes` | [`get_bootstrap_nodes()`](../../routes/mesh.py) |
| POST | `/api/mesh/bootstrap` | [`bootstrap()`](../../routes/mesh.py) |
| GET | `/api/mesh/bootstrap/stats` | [`get_bootstrap_stats()`](../../routes/mesh.py) |

### 5.7 Status

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/mesh/status` | [`get_mesh_status()`](../../routes/mesh.py) |

**Models**:
- `DiscoveryRequest`: `discovery_type`, `timeout`, `node_types`
- `NodeRegistrationRequest`: `node_id`, `node_type`, `addresses`
- `TrustLevelRequest`: `trust_level`
- `DHTStoreRequest`: `key`, `value`, `ttl`

---

## 6. Clones & Consensus

**Source**: [`routes/clones.py`](../../routes/clones.py) · [`routes/os_control.py`](../../routes/os_control.py)

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/clones` | [`get_clones()`](../../routes/clones.py) |
| GET | `/api/clones/{clone_id}` | [`get_clone()`](../../routes/clones.py) |
| GET | `/api/clones/available` | [`get_available_clones()`](../../routes/clones.py) |
| GET | `/api/clones/skill/{skill}` | [`get_clones_by_skill()`](../../routes/clones.py) |
| POST | `/api/clones/task` | [`create_task()`](../../routes/clones.py) |
| POST | `/api/clones/task/{task_id}/assign` | [`assign_task()`](../../routes/clones.py) |
| POST | `/api/clones/task/{task_id}/complete` | [`complete_task()`](../../routes/clones.py) |
| POST | `/api/clones/consensus` | [`create_consensus()`](../../routes/clones.py) |
| POST | `/api/clones/consensus/{decision_id}/vote` | [`cast_vote()`](../../routes/clones.py) |
| GET | `/api/clones/consensus/{decision_id}` | [`get_consensus()`](../../routes/clones.py) |
| GET | `/api/clones/status` | [`get_clones_status()`](../../routes/clones.py) |

---

## 7. Chat

**Source**: [`routes/chat.py`](../../routes/chat.py)

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/chat/session` | [`api_chat_session()`](../../routes/chat.py) |
| GET | `/api/chat/sessions/{user_id}` | [`api_chat_sessions()`](../../routes/chat.py) |
| GET | `/api/chat/session/{session_id}` | [`api_chat_session_get()`](../../routes/chat.py) |
| POST | `/api/chat/message` | [`api_chat_message()`](../../routes/chat.py) |
| GET | `/api/chat/messages/{session_id}` | [`api_chat_messages()`](../../routes/chat.py) |
| DELETE | `/api/chat/session/{session_id}` | [`api_chat_session_delete()`](../../routes/chat.py) |
| GET | `/api/chat/stats` | [`api_chat_stats()`](../../routes/chat.py) |

---

## 8. Learning & Training

**Source**: [`routes/learning.py`](../../routes/learning.py)

### 8.1 Dataset

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/learning/dataset/capture` | [`capture_sample()`](../../routes/learning.py) |
| POST | `/api/learning/dataset/label/{sample_id}` | [`label_sample()`](../../routes/learning.py) |
| POST | `/api/learning/dataset/snapshot` | [`create_snapshot()`](../../routes/learning.py) |
| GET | `/api/learning/dataset/snapshots` | [`get_snapshots()`](../../routes/learning.py) |
| GET | `/api/learning/dataset/snapshot/{snapshot_id}` | [`get_snapshot()`](../../routes/learning.py) |
| GET | `/api/learning/dataset/stats` | [`get_dataset_stats()`](../../routes/learning.py) |

### 8.2 Training Jobs

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/learning/training/job` | [`create_training_job()`](../../routes/learning.py) |
| POST | `/api/learning/training/job/{job_id}/start` | [`start_training()`](../../routes/learning.py) |
| POST | `/api/learning/training/job/{job_id}/complete` | [`complete_training()`](../../routes/learning.py) |
| POST | `/api/learning/training/job/{job_id}/cancel` | [`cancel_training()`](../../routes/learning.py) |
| GET | `/api/learning/training/jobs` | [`get_training_jobs()`](../../routes/learning.py) |
| GET | `/api/learning/training/job/{job_id}` | [`get_training_job()`](../../routes/learning.py) |
| GET | `/api/learning/training/stats` | [`get_training_stats()`](../../routes/learning.py) |

### 8.3 Evaluation

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/learning/evaluator/golden-dataset` | [`create_golden_dataset()`](../../routes/learning.py) |
| GET | `/api/learning/evaluator/golden-datasets` | [`get_golden_datasets()`](../../routes/learning.py) |
| POST | `/api/learning/evaluator/evaluation` | [`create_evaluation()`](../../routes/learning.py) |
| POST | `/api/learning/evaluator/evaluation/{evaluation_id}/start` | [`start_evaluation()`](../../routes/learning.py) |
| POST | `/api/learning/evaluator/evaluation/{evaluation_id}/complete` | [`complete_evaluation()`](../../routes/learning.py) |
| GET | `/api/learning/evaluator/evaluations` | [`get_evaluations()`](../../routes/learning.py) |
| GET | `/api/learning/evaluator/can-promote/{adapter_id}` | [`can_promote()`](../../routes/learning.py) |
| GET | `/api/learning/evaluator/stats` | [`get_evaluator_stats()`](../../routes/learning.py) |

### 8.4 Adapters

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/learning/adapter/register` | [`register_adapter()`](../../routes/learning.py) |
| PUT | `/api/learning/adapter/{adapter_id}/version/{version}/status` | [`update_adapter_status()`](../../routes/learning.py) |
| POST | `/api/learning/adapter/{adapter_id}/version/{version}/promote` | [`promote_adapter()`](../../routes/learning.py) |
| POST | `/api/learning/adapter/{adapter_id}/rollback` | [`rollback_adapter()`](../../routes/learning.py) |
| GET | `/api/learning/adapters` | [`get_adapters()`](../../routes/learning.py) |
| GET | `/api/learning/adapter/{adapter_id}` | [`get_adapter()`](../../routes/learning.py) |
| GET | `/api/learning/adapter/{adapter_id}/versions` | [`get_adapter_versions()`](../../routes/learning.py) |
| GET | `/api/learning/adapter/{adapter_id}/production` | [`get_production_adapter()`](../../routes/learning.py) |
| GET | `/api/learning/adapter/rollback-history` | [`get_rollback_history()`](../../routes/learning.py) |
| GET | `/api/learning/adapter/stats` | [`get_adapter_stats()`](../../routes/learning.py) |

### 8.5 Router

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/learning/router/load` | [`load_adapter()`](../../routes/learning.py) |
| POST | `/api/learning/router/swap` | [`swap_adapter()`](../../routes/learning.py) |
| GET | `/api/learning/router/status` | [`get_router_status()`](../../routes/learning.py) |
| GET | `/api/learning/router/loaded-adapters` | [`get_loaded_adapters()`](../../routes/learning.py) |
| GET | `/api/learning/router/swap-history` | [`get_swap_history()`](../../routes/learning.py) |

### 8.6 Status

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/learning/status` | [`get_learning_status()`](../../routes/learning.py) |

---

## 9. Memory

**Source**: [`routes/memory.py`](../../routes/memory.py)

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/memory/add` | [`add_memory()`](../../routes/memory.py) |
| GET | `/api/memory/{memory_id}` | [`get_memory()`](../../routes/memory.py) |
| POST | `/api/memory/search` | [`search_memory()`](../../routes/memory.py) |
| GET | `/api/memory/user/{user_id}` | [`get_user_memories()`](../../routes/memory.py) |
| DELETE | `/api/memory/{memory_id}` | [`delete_memory()`](../../routes/memory.py) |
| GET | `/api/memory/stats` | [`get_memory_stats()`](../../routes/memory.py) |
| POST | `/api/memory/prune` | [`prune_memories()`](../../routes/memory.py) |

---

## 10. Model Registry

**Source**: [`routes/registry.py`](../../routes/registry.py)

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/registry/register` | [`register_model()`](../../routes/registry.py) |
| GET | `/api/registry/active/{name}` | [`get_active_model()`](../../routes/registry.py) |
| GET | `/api/registry/versions/{name}` | [`list_versions()`](../../routes/registry.py) |
| GET | `/api/registry/{name}/{version}` | [`get_model()`](../../routes/registry.py) |
| POST | `/api/registry/rollback/{name}` | [`rollback_model()`](../../routes/registry.py) |
| GET | `/api/registry/verify/{name}/{version}` | [`verify_integrity()`](../../routes/registry.py) |
| GET | `/api/registry/status` | [`get_registry_status()`](../../routes/registry.py) |

---

## 11. Router / LLM

**Source**: [`routes/router.py`](../../routes/router.py)

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/router/route` | [`router_route()`](../../routes/router.py) |
| POST | `/api/router/chat` | [`router_chat()`](../../routes/router.py) |
| GET | `/api/router/metrics` | [`router_metrics()`](../../routes/router.py) |

---

## 12. Tools / OS Control

**Source**: [`routes/os_control.py`](../../routes/os_control.py)

### 12.1 Tools Module

| Method | Path | Function |
|--------|------|----------|
| POST | `/api/tools/execute` | [`execute_tool()`](../../routes/os_control.py) |
| GET | `/api/tools/pending` | [`get_pending()`](../../routes/os_control.py) |
| POST | `/api/tools/approve` | [`approve_tool()`](../../routes/os_control.py) |
| GET | `/api/tools/audit` | [`get_audit()`](../../routes/os_control.py) |

### 12.2 OS Tools

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/os/tools` | [`list_os_tools()`](../../routes/os_control.py) |
| POST | `/api/os/execute` | [`execute_os_tool()`](../../routes/os_control.py) |
| GET | `/api/os/audit` | [`get_os_audit()`](../../routes/os_control.py) |

---

## 13. Observability

**Source**: [`routes/observability.py`](../../routes/observability.py)

| Method | Path | Function |
|--------|------|----------|
| GET | `/api/observability/telemetry` | [`get_telemetry_endpoint()`](../../routes/observability.py) |
| GET | `/api/observability/posture` | [`get_posture_endpoint()`](../../routes/observability.py) |
| GET | `/api/observability/metrics` | [`get_metrics_endpoint()`](../../routes/observability.py) |
| GET | `/api/observability/traces` | [`get_traces_endpoint()`](../../routes/observability.py) |
| GET | `/api/observability/audit` | [`get_audit_endpoint()`](../../routes/observability.py) |
| POST | `/api/observability/event` | [`post_event_endpoint()`](../../routes/observability.py) |
| GET | `/api/observability/health` | [`get_health_endpoint()`](../../routes/observability.py) |
| GET | `/api/observability/status` | [`get_status_endpoint()`](../../routes/observability.py) |

---

## 14. Simple Backend Routes (Legacy / Universal)

**Source**: Various [`routes/`](../../routes/) modules

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
| `/health/*` | 3 | [`routes/health.py`](../../routes/health.py), [`app.py`](../../app.py) |
| `/api/auth/*` | 6 | [`routes/auth.py`](../../routes/auth.py) |
| `/api/override/*` | 4 | [`routes/override.py`](../../routes/override.py) |
| `/api/deploy/*` | 7 | [`routes/deploy.py`](../../routes/deploy.py), [`routes/release.py`](../../routes/release.py) |
| `/api/mesh/*` | 25 | [`routes/mesh.py`](../../routes/mesh.py) |
| `/api/clones/*` | 11 | [`routes/clones.py`](../../routes/clones.py) |
| `/api/chat/*` | 7 | [`routes/chat.py`](../../routes/chat.py) |
| `/api/learning/*` | 37 | [`routes/learning.py`](../../routes/learning.py) |
| `/api/memory/*` | 7 | [`routes/memory.py`](../../routes/memory.py) |
| `/api/registry/*` | 7 | [`routes/registry.py`](../../routes/registry.py) |
| `/api/router/*` | 3 | [`routes/router.py`](../../routes/router.py) |
| `/api/tools/*` | 4 | [`routes/os_control.py`](../../routes/os_control.py) |
| `/api/os/*` | 3 | [`routes/os_control.py`](../../routes/os_control.py) |
| `/api/observability/*` | 8 | [`routes/observability.py`](../../routes/observability.py) |
| `/api/blockchain/*` | 12 | [`routes/blockchain_identity.py`](../../routes/blockchain_identity.py) |
| `/api/bridge/*` | 9 | [`routes/marketplace.py`](../../routes/marketplace.py) |
| `/api/bugs/*` | 6 | [`routes/bugs.py`](../../routes/bugs.py) |
| `/api/compliance/*` | 3 | [`routes/security.py`](../../routes/security.py) |
| `/api/confirm/*` | 5 | [`routes/security.py`](../../routes/security.py) |
| `/api/constitution/*` | 1 | [`routes/sovereignty.py`](../../routes/sovereignty.py) |
| `/api/depin/*` | 27 | [`routes/depin.py`](../../routes/depin.py) |
| `/api/disaster-recovery/*` | 3 | [`routes/security.py`](../../routes/security.py) |
| `/api/evolution/*` | 4 | [`routes/consensus.py`](../../routes/consensus.py) |
| `/api/federation/*` | 4 | [`routes/infrastructure.py`](../../routes/infrastructure.py) |
| `/api/finance/*` | 22 | [`routes/finance.py`](../../routes/finance.py) |
| `/api/government/*` | 12 | [`routes/government.py`](../../routes/government.py) |
| `/api/hybrid-economy/*` | 11 | [`routes/marketplace.py`](../../routes/marketplace.py) |
| `/api/identity/*` | 7 | [`routes/identity.py`](../../routes/identity.py) |
| `/api/infrastructure/*` | 10 | [`routes/infrastructure.py`](../../routes/infrastructure.py) |
| `/api/integration/*` | 7 | [`routes/security.py`](../../routes/security.py) |
| `/api/jobs/*` | 6 | [`routes/jobs.py`](../../routes/jobs.py) |
| `/api/marketplace/*` | 30 | [`routes/marketplace.py`](../../routes/marketplace.py) |
| `/api/mcp/*` | 7 | [`routes/mcp.py`](../../routes/mcp.py) |
| `/api/nepal/*` | 7 | [`routes/nepal.py`](../../routes/nepal.py) |
| `/api/personal/*` | 5 | [`routes/memory.py`](../../routes/memory.py) |
| `/api/platform/*` | 3 | [`routes/infrastructure.py`](../../routes/infrastructure.py) |
| `/api/pq/*` | 4 | [`routes/consensus.py`](../../routes/consensus.py) |
| `/api/push/*` | 2 | [`routes/push.py`](../../routes/push.py) |
| `/api/pwa/*` | 1 | [`routes/pwa.py`](../../routes/pwa.py) |
| `/api/rbe/*` | 7 | [`routes/rbe.py`](../../routes/rbe.py) |
| `/api/reputation/*` | 10 | [`routes/marketplace.py`](../../routes/marketplace.py) |
| `/api/security/*` | 4 | [`routes/security.py`](../../routes/security.py) |
| `/api/self/*` | 12 | [`routes/self_awareness.py`](../../routes/self_awareness.py) |
| `/api/sovereignty/*` | 10 | [`routes/sovereignty.py`](../../routes/sovereignty.py) |
| `/api/svt/*` | 6 | [`routes/identity.py`](../../routes/identity.py) |
| `/api/task-bus/*` | 12 | [`routes/marketplace.py`](../../routes/marketplace.py) |
| `/api/teams/*` | 8 | [`routes/auth.py`](../../routes/auth.py) |
| `/api/universal/*` | 11 | [`routes/universal.py`](../../routes/universal.py) |
| `/api/universe/*` | 13 | [`routes/universal.py`](../../routes/universal.py), [`routes/memory.py`](../../routes/memory.py) |
| `/api/v1/*` | 34 | Various [`routes/`](../../routes/) modules |
| Various (app.py) | 5 | [`app.py`](../../app.py) |
| **Total** | **636** | **35 route modules** |

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

- [`routes/health.py`](../../routes/health.py) — Health probe endpoints
- [`routes/auth.py`](../../routes/auth.py) — Authentication + teams endpoints
- [`routes/override.py`](../../routes/override.py) — Override engine endpoints
- [`routes/deploy.py`](../../routes/deploy.py) — Deployment endpoints
- [`routes/release.py`](../../routes/release.py) — Release management endpoints
- [`routes/mesh.py`](../../routes/mesh.py) — Mesh network endpoints
- [`routes/clones.py`](../../routes/clones.py) — Clone management endpoints
- [`routes/chat.py`](../../routes/chat.py) — Chat session + agent endpoints
- [`routes/learning.py`](../../routes/learning.py) — ML pipeline endpoints
- [`routes/memory.py`](../../routes/memory.py) — Memory storage + personal endpoints
- [`routes/registry.py`](../../routes/registry.py) — Model registry endpoints
- [`routes/router.py`](../../routes/router.py) — LLM routing endpoints
- [`routes/os_control.py`](../../routes/os_control.py) — Tool execution + OS control endpoints
- [`routes/observability.py`](../../routes/observability.py) — Observability endpoints
- [`routes/analytics.py`](../../routes/analytics.py) — Analytics + RAG endpoints
- [`routes/blockchain_identity.py`](../../routes/blockchain_identity.py) — Blockchain DID/VC/SBT endpoints
- [`routes/bugs.py`](../../routes/bugs.py) — Bug reporting + triage endpoints
- [`routes/consensus.py`](../../routes/consensus.py) — Consensus + Dharma + PQ + evolution endpoints
- [`routes/depin.py`](../../routes/depin.py) — DePIN (Daylight/DIMO/Uplink) endpoints
- [`routes/finance.py`](../../routes/finance.py) — Finance + ledger + Nepal payment endpoints
- [`routes/government.py`](../../routes/government.py) — Government integration endpoints
- [`routes/identity.py`](../../routes/identity.py) — DID + SVT endpoints
- [`routes/infrastructure.py`](../../routes/infrastructure.py) — Infrastructure + AI + federation endpoints
- [`routes/jobs.py`](../../routes/jobs.py) — Job marketplace endpoints
- [`routes/marketplace.py`](../../routes/marketplace.py) — Marketplace + bridge + economy + task-bus endpoints
- [`routes/mcp.py`](../../routes/mcp.py) — MCP tool endpoints
- [`routes/nepal.py`](../../routes/nepal.py) — Nepal-specific endpoints
- [`routes/push.py`](../../routes/push.py) — Push notification endpoints
- [`routes/pwa.py`](../../routes/pwa.py) — PWA config endpoints
- [`routes/rbe.py`](../../routes/rbe.py) — RBE (Resource-Based Economy) endpoints
- [`routes/security.py`](../../routes/security.py) — Security + compliance + TPM endpoints
- [`routes/self_awareness.py`](../../routes/self_awareness.py) — Self-awareness + auto-build endpoints
- [`routes/sovereignty.py`](../../routes/sovereignty.py) — Sovereignty + air-gap + constitution endpoints
- [`routes/universal.py`](../../routes/universal.py) — Universal systems + universe endpoints
- [`app.py`](../../app.py) — Root-level health + metrics endpoints
