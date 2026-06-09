# AsimNexus API Reference

> **One Kernel, Infinite Worlds** — Full-stack World Operating System with AI, Mesh Networking, Digital Identity, and Governance.

**Base URL:** `http://localhost:8000`  
**API Docs (Swagger):** `http://localhost:8000/docs`  
**Protocols:** REST, WebSocket, GraphQL, SOAP, gRPC

---

## Table of Contents

- [Authentication](#authentication)
- [Health & System](#health--system)
- [Auth Endpoints](#auth-endpoints)
- [Chat](#chat)
- [Router](#router)
- [Digital Twin](#digital-twin)
- [AGI Reasoning](#agi-reasoning)
- [Quantum Computing](#quantum-computing)
- [Blockchain Identity](#blockchain-identity)
- [Mesh Network](#mesh-network)
- [Life Protocol](#life-protocol)
- [Local LLM / Brain](#local-llm--brain)
- [Identity System](#identity-system)
- [SVT Sovereign Tokens](#svt-sovereign-tokens)
- [HDT Human Digital Twin](#hdt-human-digital-twin)
- [World OS Dashboard](#world-os-dashboard)
- [Consensus Engine](#consensus-engine)
- [Clones](#clones)
- [Healing System](#healing-system)
- [OS Tools](#os-tools)
- [Dharma Veto](#dharma-veto)
- [Dreaming Engine](#dreaming-engine)
- [Analytics](#analytics)
- [Jobs Marketplace](#jobs-marketplace)
- [Sync / Offline](#sync--offline)
- [Messaging](#messaging)
- [Agent Switch](#agent-switch)
- [File Operations](#file-operations)
- [Codebase](#codebase)
- [Terminal & Automation](#terminal--automation)
- [Security](#security)
- [Virtual Office](#virtual-office)
- [Autonomous Mode](#autonomous-mode)
- [ZKP (Zero-Knowledge Proofs)](#zkp-zero-knowledge-proofs)
- [Universe](#universe)
- [Bridge / WebSocket](#bridge--websocket)
- [Unified Bridge (Multi-Protocol)](#unified-bridge-multi-protocol)
- [NVIDIA NIM Proxy](#nvidia-nim-proxy)
- [Appendices](#appendices)

---

## Authentication

All protected endpoints require a **JWT Bearer token** in the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens use **HS256** signing. Obtain one via `POST /api/auth/login`.

### Token Payload

| Field | Description |
|-------|-------------|
| `user_id` | Unique user identifier |
| `user_role` | Role (e.g. `user`, `admin`) |
| `mode_boundary` | Operational mode: `personal`, `family`, `company`, `community`, `government` |
| `device_trust_posture` | Device trust level |
| `session_risk_score` | Float 0.0–1.0 risk score |
| `consent_scope` | List of granted consent scopes |
| `jurisdiction_tag` | ISO country code for jurisdiction |
| `expires_at` | Token expiry (default 24h) |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIM_JWT_SECRET` | *(insecure fallback)* | JWT signing secret |
| `ASIM_TOKEN_EXPIRY_HOURS` | `24` | Access token lifetime |
| `ASIM_REFRESH_EXPIRY_HOURS` | `168` | Refresh token lifetime (7 days) |

---

## Health & System

### `GET /health`
Health check (always returns 200 if server is running).

**Response:** `{"status": "healthy", "timestamp": "..."}`

### `GET /health/live`
Kubernetes liveness probe — returns 200 if process is alive.

### `GET /health/ready`
Kubernetes readiness probe — checks DB, LLM, core modules, and storage services (Redis, ClickHouse, PostgreSQL, MinIO, ChromaDB).

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "llm": "ok",
    "core_modules": "ok",
    "storage_services": {
      "redis": "ok",
      "postgres": "ok",
      "chromadb": "ok"
    }
  },
  "timestamp": "..."
}
```

### `GET /health/status`
Full system status with detailed metrics for all subsystems.

### `GET /api/stats`
Complete system statistics across all 21 components.

### `GET /api/system/complete`
Full system information (frontend-facing).

### `GET /api/system/info`
Basic system info.

---

## Auth Endpoints

### `POST /api/auth/register`
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "display_name": "User Name",
  "country_code": "NP"
}
```

**Response:** `AuthSession` with token, user_id, mode_boundary, device_trust_posture, session_risk_score, consent_scope, jurisdiction_tag.

### `POST /api/auth/login`
Authenticate and receive a JWT.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "device_id": "unknown_device",
  "mode": "personal"
}
```

**Response:** `AuthSession`

### `POST /api/auth/refresh`
Refresh an expired token.

**Request:** `{"refresh_token": "..."}`

### `POST /api/auth/logout`
Invalidate the current session/token.

---

## Chat

### `POST /api/brain/process`
Process a chat message through the Asim Brain (Qwen3-4B).

**Request:**
```json
{
  "user_id": "string",
  "message": "Hello, Asim!",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "status": "success",
  "response": "Hello! How can I help you today?",
  "session_id": "abc-123"
}
```

### `POST /api/brain/stream`
Stream chat response via Server-Sent Events (SSE).

### `POST /api/ai/chat`
AI-orchestrated chat through the messaging orchestrator.

### `POST /api/router/chat`
Chat with local-first routing, cloud fallback, and privacy classification.

**Request:**
```json
{
  "prompt": "string",
  "privacy_classification": "public",
  "mode": "personal"
}
```

---

## Router

### `POST /api/router/route`
Route a prompt with automatic privacy classification and model-tier selection.

**Request:**
```json
{
  "message": "string",
  "privacy_classification": "public",
  "mode": "personal"
}
```

**Response:** Contains the routed model, intent, tier, and requires_veto/requires_human flags.

### `GET /api/router/metrics`
Get router performance metrics (latency, model usage, success rates).

---

## Digital Twin

### `POST /api/digital-twin`
Create a new digital twin.

**Request:**
```json
{
  "legal_name": "John Doe",
  "date_of_birth": "1990-01-15",
  "nationality": "US",
  "gender": "male",
  "birth_certificate_id": "optional-id"
}
```

### `GET /api/digital-twin/{twin_id}`
Get digital twin by ID.

### `GET /api/digital-twin/{twin_id}/life-events`
Get life events for a specific twin.

---

## AGI Reasoning

### `POST /api/agi/think`
Submit a query to the AGI reasoning engine.

**Request:**
```json
{
  "query": "What is the meaning of life?",
  "reasoning_mode": "analytical",
  "max_depth": 10
}
```

`reasoning_mode` options: `analytical`, `creative`, `critical`, `systems`, `ethical`

### `GET /api/agi/stats`
AGI system statistics.

---

## Quantum Computing

### `POST /api/quantum/job`
Create and run a quantum computing job.

### `GET /api/quantum/stats`
Quantum computing system statistics.

### `GET /api/quantum/devices`
List available quantum devices and providers.

---

## Blockchain Identity

### `POST /api/blockchain/did`
Create a decentralized identifier (DID).

### `POST /api/blockchain/credential`
Issue a verifiable credential.

### `GET /api/blockchain/credentials/{did}`
Get all credentials for a given DID.

### `GET /api/blockchain/sbts/{did}`
Get soulbound tokens (SBTs) for a given DID.

### `POST /api/blockchain/zkproof`
Create a zero-knowledge proof.

---

## Mesh Network

### `GET /api/mesh/status`
Global mesh network status overview.

### `POST /api/mesh/edge-node`
Add an edge computing node to the mesh.

### `GET /api/mesh/peers`
List mesh peer connections.

### `GET /api/mesh/nodes`
List all mesh nodes.

### `POST /api/mesh/node/init`
Initialize a new mesh node.

### `POST /api/mesh/air-gap`
Air-gap a node from the mesh (sovereignty isolation).

### `GET /api/mesh/discover`
Discover reachable mesh nodes.

### `GET /api/mesh/stats`
Mesh network statistics (frontend-facing).

### `GET /api/mesh/nodes/discover`
Discover nodes with additional details.

### `GET /api/mesh/federation/map`
Get federation map.

### `POST /api/mesh/federation/join`
Join a mesh federation.

### `GET /api/mesh/clone/status/{clone_id}`
Get clone status via mesh.

### `POST /api/mesh/clone/sync`
Sync clone via mesh.

### `GET /api/mesh/offline/status/{node_id}`
Get offline sync status for a node.

### `GET /api/mesh/offline/capabilities`
List offline sync capabilities.

### `POST /api/mesh/offline/operation`
Perform an offline operation.

---

## Life Protocol

### `POST /api/life-protocol/event`
Schedule a life event automation.

### `GET /api/life-protocol/tasks`
Get all life protocol automation tasks.

---

## Local LLM / Brain

### `GET /api/local-llm/health`
Check local LLM health (GGUF model availability).

### `POST /api/brain/process`
Process through brain (see [Chat](#chat)).

### `POST /api/brain/stream`
Stream brain response (SSE).

### `POST /llm/chat`
Chat via local LLM (from unified_routes).

**Request:** `{"message": "string"}`

---

## Identity System

### `GET /api/identity/stats`
Identity system statistics (total identities, verified, pending).

### `GET /api/identity/list`
List all registered identities.

### `POST /api/identity/create`
Create a new identity.

**Request:**
```json
{
  "display_name": "string",
  "country_code": "NP",
  "verification_method": "government_id"
}
```

### `POST /api/identity/verify`
Verify an existing identity with evidence.

**Request:**
```json
{
  "identity_id": "string",
  "evidence_hash": "string"
}
```

---

## SVT Sovereign Tokens

### `GET /api/svt/stats`
SVT token system statistics.

### `GET /api/svt/wallet`
Get SVT wallet balance for the authenticated user.

### `POST /api/svt/mint`
Mint new SVT sovereign tokens.

**Request:**
```json
{
  "amount": 100.0,
  "reason": "Service contribution"
}
```

### `GET /api/svt/wallet/{did}`
Get wallet balance for a specific DID.

---

## HDT Human Digital Twin

### `POST /api/hdt/create`
Create a human digital twin profile.

**Request:**
```json
{
  "display_name": "string",
  "capabilities": ["coding", "design"],
  "personality_traits": {}
}
```

### `PUT /api/hdt/status`
Update HDT status (active/paused/archived).

### `POST /api/hdt/skill`
Add a skill to the HDT profile.

### `POST /api/hdt/announce`
Broadcast the HDT availability to the mesh.

### `GET /hdt/me`
Get the authenticated user's HDT.

---

## World OS Dashboard

### `GET /api/quad/status`
Quad federation status (4-quadrant governance model).

### `GET /api/bugs/stats`
Bug triage system statistics.

### `GET /api/dht/status`
Kademlia DHT (Distributed Hash Table) status.

### `GET /api/firewall/status`
Mesh firewall / router status.

---

## Consensus Engine

### `GET /api/consensus/status`
Consensus engine status and current state.

### `POST /api/consensus/vote`
Submit a consensus vote.

**Request:**
```json
{
  "topic": "Proposal title",
  "description": "Details",
  "level": "high"
}
```

### `POST /api/consensus/override`
Override a consensus decision (requires elevated permissions).

**Request:**
```json
{
  "approved": true,
  "reason": "Emergency override"
}
```

### `GET /api/consensus/stats`
Consensus engine statistics.

### `GET /api/consensus/pending`
List pending votes requiring action.

### `GET /api/consensus/list`
List all proposals.

---

## Clones

### `GET /api/clones/specs`
List all clone specifications.

### `GET /api/clones/spec/{clone_id}`
Get clone spec by ID.

### `POST /api/clones/route`
Route a query to the most suitable clone.

**Request:** `{"query": "string"}`

### `GET /clones/list`
List all clones (from unified_routes).

### `GET /clones/status/{clone_id}`
Get clone status.

### `POST /clones/sync/{clone_id}`
Trigger clone synchronization.

### `POST /clones/delegate/{clone_id}`
Delegate a task to a clone.

### `POST /clones/commission`
Commission a new clone.

**Request:**
```json
{
  "specialization": "research",
  "personality": "analytical",
  "capabilities": ["data_analysis", "writing"]
}
```

### `POST /clones/retire/{clone_id}`
Retire/decommission a clone.

---

## Healing System

### `GET /api/healing/status`
Healing system status and metrics.

### `POST /api/healing/balance`
Trigger a system balance/healing cycle.

### `POST /api/healing/heal`
Execute a targeted heal operation.

**Request:** `{"target": "optional-target-module"}`

---

## OS Tools

### `GET /api/os/tools`
List all available OS tools.

### `POST /api/os/execute`
Execute an OS tool through the 6-stage pipeline.

**Request:**
```json
{
  "tool": "tool_name",
  "params": {}
}
```

### `GET /api/os/status`
OS tools subsystem status.

### `GET /api/os/metrics`
OS tools performance metrics.

### `GET /api/os/pending`
List pending tool execution requests requiring approval.

### `POST /api/os/approve/{call_id}`
Approve a pending tool execution.

### `POST /api/os/reject/{call_id}`
Reject a pending tool execution.

### `GET /api/os/audit`
Get OS tools audit log.

### `POST /api/os/clipboard`
Clipboard read/write operation.

**Request:**
```json
{
  "action": "read",
  "content": ""
}
```

---

## Dharma Veto

### `GET /api/dharma/status`
Dharma veto system status (5-layer ethical veto).

### `POST /api/dharma/veto`
Evaluate an action through the Dharma veto system.

**Request:**
```json
{
  "reason": "Action description",
  "severity": "warning"
}
```

`severity` options: `warning`, `block`, `critical`

---

## Dreaming Engine

### `GET /api/dreaming/status`
Dreaming engine status (autonomous system introspection).

### `GET /api/dreaming/briefing`
Get the latest dream briefing — system insights from autonomous analysis.

### `POST /api/dreaming/trigger`
Manually trigger a dreaming cycle.

---

## Analytics

### `GET /api/analytics/overview`
Analytics overview dashboard data.

### `GET /api/analytics/activity`
System activity log with filtering.

### `GET /api/analytics/performance`
System performance analytics (CPU, RAM, response times).

### `GET /api/analytics/usage`
Usage analytics (active users, request counts, endpoint usage).

---

## Jobs Marketplace

### `GET /api/jobs/stats`
Jobs marketplace statistics (total jobs, active, completed).

### `GET /api/jobs/list`
List available jobs with optional category filter.

### `POST /api/jobs/post`
Post a new job to the marketplace.

**Request:**
```json
{
  "title": "Job title",
  "description": "Job description",
  "category": "general",
  "budget": 0.0
}
```

---

## Sync / Offline

### `GET /api/sync/status`
Offline sync engine status.

### `GET /api/sync/queue`
List pending sync operations in the queue.

### `POST /api/sync/enqueue`
Enqueue a sync operation.

**Request:**
```json
{
  "operation_type": "data_sync",
  "payload": {},
  "priority": "normal"
}
```

### `POST /api/sync/flush`
Flush/process all pending sync operations.

---

## Messaging

All under prefix `/api`. Requires messaging connector initialization.

### `POST /api/messaging/whatsapp/send`
Send a WhatsApp message.

**Query Params:** `to` (string), `message` (string)

### `POST /api/messaging/telegram/send`
Send a Telegram message.

**Query Params:** `chat_id` (string), `message` (string)

### `POST /api/messaging/discord/send`
Send a Discord message.

**Query Params:** `channel_id` (string), `message` (string)

### `POST /api/messaging/slack/send`
Send a Slack message.

**Query Params:** `channel` (string), `message` (string)

### `POST /api/messaging/broadcast`
Broadcast a message to multiple platforms.

**Request:**
```json
{
  "platforms": ["whatsapp", "telegram"],
  "recipients": {},
  "message": "Hello all!"
}
```

### `GET /api/messaging/status`
Get messaging connector health status for all platforms.

---

## Agent Switch

### `POST /api/agent/mode/activate`
Activate agent mode for a user.

**Request:**
```json
{
  "user_id": "string",
  "duration_days": 30,
  "skill_focus": "technical",
  "bio": "Optional bio",
  "certifications": [],
  "experience_years": 5
}
```

### `POST /api/agent/mode/deactivate`
Deactivate agent mode.

### `POST /api/agent/task/complete`
Report a task as complete (Human-in-the-Loop confirmation).

### `GET /api/agent/status`
Get agent mode status and current tasks.

### `GET /api/agent/earnings`
Get earnings history from agent mode activities.

---

## File Operations

### `GET /files/list`
List files in a directory.

**Query Param:** `path` (default: root)

### `GET /files/read`
Read file content.

**Query Param:** `path`

### `POST /files/write`
Write content to a file.

**Request:**
```json
{
  "path": "relative/path/to/file.txt",
  "content": "file content"
}
```

### `DELETE /files/delete`
Delete a file.

**Query Param:** `path`

### `POST /files/create_directory`
Create a directory.

**Request:** `{"path": "new/directory"}`

### `GET /files/search`
Search files by pattern.

**Query Param:** `pattern`

---

## Codebase

### `GET /codebase/index`
Index the codebase (build search index).

### `GET /codebase/search`
Search the codebase.

**Query Param:** `q` (search query)

### `GET /codebase/summary`
Get codebase summary (file counts, languages, size).

### `GET /codebase/file/{path}`
Get content of a specific file in the codebase.

---

## Terminal & Automation

### `POST /terminal/execute`
Execute a terminal command (sandboxed).

**Request:** `{"command": "ls -la"}`
**Query Param:** `workdir`

### `POST /automation/create`
Create a new automation task.

**Request:**
```json
{
  "name": "Daily Backup",
  "type": "scheduled",
  "config": {},
  "trigger": "cron:0 0 * * *",
  "action": "backup"
}
```

### `GET /automation/list`
List all automation tasks.

### `POST /automation/execute`
Execute an automation task immediately.

### `DELETE /automation/{task_id}`
Delete an automation task.

---

## Security

### `GET /api/security/status`
System security status overview.

### `GET /api/security/vulnerabilities`
List known vulnerabilities.

### `POST /api/security/scan`
Trigger a security scan.

### `GET /api/security/encryption-algorithms`
List supported encryption algorithms.

---

## Virtual Office

### `GET /api/virtual_office/status`
Virtual office system status.

### `GET /api/virtual_office/rooms`
List available virtual office rooms.

### `POST /api/virtual_office/join`
Join a virtual office room.

**Request:** `{"room_id": "string"}`

### `POST /api/virtual_office/leave`
Leave a virtual office room.

**Request:** `{"room_id": "string"}`

---

## Autonomous Mode

### `GET /api/autonomous/status`
Autonomous mode status.

### `POST /api/autonomous/enable`
Enable autonomous operation mode.

### `POST /api/autonomous/disable`
Disable autonomous operation mode.

---

## ZKP (Zero-Knowledge Proofs)

### `POST /zkp/create`
Create a zero-knowledge proof.

**Request:**
```json
{
  "claim": "I am over 18",
  "evidence_hash": "string",
  "schema": "age_verification"
}
```

### `POST /zkp/verify`
Verify a zero-knowledge proof.

**Request:** `{"proof_id": "string", "proof_data": {}}`

---

## Universe

### `GET /api/universe/{id}/lifecycle`
Get the lifecycle state of a universe instance.

### `POST /api/universal/lifecycle`
Trigger a lifecycle event on a universe.

**Request:**
```json
{
  "action": "create",
  "type": "personal",
  "config": {}
}
```

---

## Bridge / WebSocket

### `WebSocket /ws/{client_id}`
Real-time bidirectional WebSocket connection for the Master Control Dashboard.

**Events (server → client):**
- `system_status` — current system component states
- `agent_update` — agent activity notifications
- `alert` — system alerts
- `metric` — real-time metrics

**Events (client → server):**
- `control` — send control commands to core
- `query` — query system state

### `GET /api/status`
Bridge system status.

### `GET /api/health`
Bridge health check.

### `POST /api/control`
Send a control command through the bridge.

**Request:** `{"command": "restart", "target": "module_name"}`

### `POST /api/safety/check`
Execute a safety check before an operation.

**Request:** `{"action": "delete_file", "target": "/path/to/file"}`

---

## Unified Bridge (Multi-Protocol)

The Unified Bridge exposes a single API surface across multiple protocols.

### REST

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Multi-protocol health check |
| GET | `/api/rest/system/status` | System status (REST) |
| POST | `/api/rest/agents/{agent_id}/command` | Send agent command (REST) |
| GET | `/api/rest/neural/pulse` | Neural pulse stream |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws/realtime` | Real-time multi-protocol WebSocket |

### GraphQL

| Endpoint | Description |
|----------|-------------|
| `/graphql` | GraphQL playground and API |

### SOAP

| Endpoint | Description |
|----------|-------------|
| `/api/soap` | SOAP XML endpoint |

### gRPC

gRPC server available on configurable port (set up via `UnifiedAPIBridge`).

---

## NVIDIA NIM Proxy

### `ANY /{path}`
Proxies requests to `https://integrate.api.nvidia.com/v1/{path}` with automatic API key rotation across 27 keys. Handles rate limiting (HTTP 429) by cycling to the next key transparently.

---

## Appendices

### Standard Error Responses

All endpoints return errors in a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Description |
|-------------|-------------|
| `200` | Success |
| `400` | Bad request — validation error |
| `401` | Unauthorized — missing or invalid token |
| `403` | Forbidden — insufficient permissions |
| `404` | Resource not found |
| `429` | Rate limit exceeded |
| `500` | Internal server error |
| `503` | Service unavailable — dependency missing |

### Rate Limiting

Rate limiting is enforced via `slowapi`. Default limits are configurable through `backend/config/security_config.py`. Exceeding the limit returns HTTP `429`.

### Common Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | For protected routes | `Bearer <jwt_token>` |
| `Content-Type` | For POST/PUT/PATCH | `application/json` |

### Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ASIMNEXUS_ROOT` | `cwd` | Workspace root for file operations |
| `ASIM_DB_PATH` | `data/asim_core.db` | SQLite database path |
| `ASIM_ALLOWED_ORIGINS` | `http://localhost:3000,...` | CORS allowed origins |
| `ASIM_LOG_LEVEL` | `INFO` | Logging level |
| `ASIM_OFFLINE` | *(unset)* | When `"true"`, force local-only mode |

### Data Models

**AuthSession:**
```json
{
  "token": "eyJ...",
  "user_id": "uuid",
  "user_role": "user",
  "mode_boundary": "personal",
  "device_trust_posture": "trusted",
  "session_risk_score": 0.0,
  "consent_scope": ["basic_profile"],
  "jurisdiction_tag": "NP",
  "client_ip": "127.0.0.1",
  "created_at": "2026-01-01T00:00:00",
  "expires_at": "2026-01-02T00:00:00"
}
```

**Message:**
```json
{
  "id": "uuid",
  "role": "user|assistant",
  "content": "string",
  "user_id": "uuid",
  "session_id": "uuid",
  "metadata": {},
  "created_at": "ISO8601",
  "model_used": "qwen3-4b",
  "clone_used": null
}
```

**ChatSession:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "New Chat",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "metadata": {}
}
```

### Privacy Classification

Used by the Router to enforce data handling:

| Classification | Description | Cloud Routing |
|----------------|-------------|---------------|
| `public` | Non-sensitive data | Allowed |
| `confidential` | Private but non-critical | Trusted clouds only |
| `highly_sensitive` | Critical personal data | Local-only, no cloud |

### Mode Boundaries

Operational modes that constrain system behavior:

| Mode | Scope |
|------|-------|
| `personal` | Individual user |
| `family` | Family group |
| `company` | Organization |
| `community` | Community governance |
| `government` | National governance |

### Clone Capabilities

Specializations available for clone commission:

- `healthcare`
- `legal`
- `finance`
- `education`
- `technical`
- `administrative`
- `creative`
- `research`
- `data_analysis`
- `writing`

### Dharma Severity Levels

Used by the 5-layer Dharma veto system:

| Level | Behavior |
|-------|----------|
| `warning` | Advisory — operation allowed with warning |
| `block` | Operation blocked automatically |
| `critical` | Operation blocked and system alert triggered |

---

> **Note:** This API reference is auto-generated from the AsimNexus codebase. Some endpoints may require additional dependencies not yet installed (e.g., `llama-cpp-python` for local LLM, `chromadb` for vector memory). Missing dependencies result in graceful `503` responses rather than crashes.
