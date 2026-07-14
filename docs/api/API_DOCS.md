# AsimNexus API Documentation

> **Version:** RC-2 | **Total Routes:** 634
> **Base URL:** `http://localhost:8000`
> **Auth:** Bearer Token (`Authorization: Bearer <token>`)
> **Content-Type:** `application/json`
> **Source files:** [`routes/`](../routes/) (30+ modules), [`app.py`](../app.py)
> **Consolidated modules:** [`core/consensus/`](../core/consensus/) · [`core/dreaming/`](../core/dreaming/) · [`core/self_awareness/`](../core/self_awareness/)
> **See also:** [`docs/api/API_CONTRACT_INDEX.md`](api/API_CONTRACT_INDEX.md) (legacy reference)

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Health & System](#2-health--system)
3. [Chat & AI](#3-chat--ai)
4. [Self-Awareness](#4-self-awareness)
5. [Mesh & Network](#5-mesh--network)
6. [Identity & Blockchain](#6-identity--blockchain)
7. [Economy & Marketplace](#7-economy--marketplace)
8. [OS Control & Sandbox](#8-os-control--sandbox)
9. [Analytics & Monitoring](#9-analytics--monitoring)
10. [Consensus & Governance](#10-consensus--governance)
11. [Nepal Government Connectors](#11-nepal-government-connectors)
12. [Security & Compliance](#12-security--compliance)
13. [Legacy Routes](#13-legacy-routes)

---

## 1. Authentication

### `POST /auth/login`
Authenticate with email and password.

**Request:**
```json
{ "email": "user@example.com", "password": "secret123" }
```

**Response:**
```json
{ "success": true, "token": "eyJ...", "user": { "id": "...", "display_name": "..." } }
```

### `POST /auth/register`
Create a new account.

**Request:**
```json
{ "email": "user@example.com", "password": "secret123", "display_name": "User" }
```

### `GET /auth/me`
Get current authenticated user profile.

### `POST /auth/logout`
Invalidate current session.

### `POST /auth/refresh`
Refresh authentication token.

### `POST /auth/verify`
Verify authentication token validity.

### `GET /auth/sessions`
List active sessions.

---

## 2. Health & System

### `GET /health`
Basic health check.

**Response:** `{ "status": "ok", "timestamp": "..." }`

### `GET /health/live`
Kubernetes liveness probe.

### `GET /health/ready`
Kubernetes readiness probe with component checks.

**Response:**
```json
{
  "status": "ready",
  "checks": { "database": true, "redis": false, "self_awareness": true },
  "timestamp": "..."
}
```

### `GET /health/status`
Full system health with detailed component checks.

**Response:**
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "components": {
    "database": { "status": "healthy", "latency_ms": 2.3 },
    "self_awareness": { "status": "healthy", "modules": 42, "issues": 5 },
    "mesh": { "status": "healthy", "peers": 3 },
    "evolution": { "status": "healthy", "suggestions": 12 },
    "dreaming": { "status": "healthy", "cycles": 7 }
  }
}
```

### `GET /metrics`
Prometheus-compatible metrics endpoint.

**Content Negotiation:**
- `Accept: text/plain` → Prometheus text format
- `Accept: application/json` → JSON format

### `GET /api/system/info`
System information including version, uptime, and configuration.

### `GET /api/version`
API version information.

---

## 3. Chat & AI

### `POST /chat` | `POST /llm/chat` | `POST /api/v1/chat`
Send a chat message to the AI.

**Request:**
```json
{
  "message": "Hello, AsimNexus!",
  "user_id": 1,
  "conversation_id": "conv_123",
  "model_id": "qwen3-4b"
}
```

### `POST /api/chat`
Alias for chat with additional metadata.

### `POST /api/brain/process`
Process input through the brain/memory system.

### `POST /api/brain/stream`
Stream AI response token-by-token.

### `GET /api/agent/status`
Get agent system status.

### `GET /api/agent/sessions`
List active agent sessions.

### `GET /api/agent/status/{session_id}`
Get status of a specific agent session.

### `POST /api/agent/run`
Execute an agent task.

### `POST /api/agent/cancel`
Cancel a running agent task.

### `GET /api/ai/status`
AI subsystem status.

### `POST /api/ai/finetune/nepali`
Trigger Nepali language fine-tuning.

---

## 4. Self-Awareness

> All self-awareness endpoints are publicly accessible (no auth required).

### `GET /api/self/knowledge/summary`
Get knowledge base summary.

**Response:**
```json
{
  "total_modules": 42,
  "total_packages": 15,
  "total_classes": 120,
  "total_functions": 450,
  "total_routes": 634,
  "total_lines": 45000,
  "total_issues": 8,
  "open_issues": 3,
  "last_scan": "2026-07-03T12:00:00",
  "last_updated": "2026-07-03T12:00:00"
}
```

### `GET /api/self/knowledge/modules`
List all scanned modules.

### `GET /api/self/knowledge/modules/{package}`
Get details for a specific module.

### `GET /api/self/knowledge/routes`
List all detected API routes.

### `GET /api/self/knowledge/issues`
List all detected issues (TODOs, bare excepts, etc.).

### `GET /api/self/knowledge/dependencies`
List module dependency graph.

### `GET /api/self/knowledge/search?q={query}`
Search knowledge base.

### `POST /api/self/scan`
Trigger a full codebase scan.

### `GET /api/self/builder/history`
Get build action history.

### `GET /api/self/builder/stats`
Get builder statistics.

### `GET /api/self/bridge/stats`
Get evolution bridge statistics.

---

## 5. Mesh & Network

### `GET /mesh/nodes`
List all mesh network nodes.

### `GET /api/v1/mesh/status`
Mesh P2P network status.

### `GET /api/v1/mesh/peers`
List connected mesh peers.

### `POST /api/v1/mesh/connect`
Connect to a mesh peer.

### `POST /api/v1/mesh/sync_batch`
Batch sync data across mesh.

### `GET /api/v1/federation/map`
Federation network map.

### `POST /api/v1/federation/join`
Join a federation.

### `GET /api/v1/federation/stats`
Federation statistics.

---

## 6. Identity & Blockchain

### `POST /api/blockchain/did`
Create a Decentralized Identifier (DID).

### `GET /api/blockchain/did/{did}`
Resolve a DID document.

### `GET /api/blockchain/dids`
List all DIDs.

### `POST /api/blockchain/credentials`
Issue a Verifiable Credential.

### `GET /api/blockchain/credentials`
List credentials.

### `GET /api/blockchain/credentials/{vc_id}`
Get credential by ID.

### `POST /api/blockchain/credentials/{vc_id}/revoke`
Revoke a credential.

### `POST /api/blockchain/sbt`
Issue a Soulbound Token.

### `GET /api/blockchain/sbt`
List SBTs.

### `POST /api/blockchain/zkp`
Create a Zero-Knowledge Proof.

### `GET /api/blockchain/zkp/{proof_id}`
Verify a ZKP.

### `GET /api/blockchain/stats`
Blockchain statistics.

---

## 7. Economy & Marketplace

### `GET /api/marketplace/listings`
List marketplace listings.

### `POST /api/marketplace/listings`
Create a listing.

### `GET /api/marketplace/listings/{listing_id}`
Get listing details.

### `POST /api/marketplace/purchase`
Purchase a listing.

### `GET /api/marketplace/orders`
List orders.

### `GET /api/marketplace/orders/{order_id}`
Get order details.

### `GET /api/bridge/pools`
List liquidity pools.

### `POST /api/bridge/pool/create`
Create a liquidity pool.

### `POST /api/bridge/pool/add-liquidity`
Add liquidity to a pool.

### `POST /api/bridge/pool/remove-liquidity`
Remove liquidity from a pool.

### `POST /api/bridge/initiate`
Initiate a cross-chain bridge transfer.

### `GET /api/bridge/fee`
Get bridge fee estimate.

### `GET /api/bridge/transactions`
List bridge transactions.

### `GET /api/bridge/tx/{tx_id}`
Get bridge transaction details.

### `GET /api/bridge/stats`
Bridge statistics.

---

## 8. OS Control & Sandbox

### `POST /api/v1/sandbox/execute`
Execute a command in the sandbox.

### `GET /api/v1/sandbox/status`
Sandbox status.

### `POST /api/v1/mirror/reflect`
Submit an action for mirror reflection.

### `GET /api/v1/mirror/state/{user_id}`
Get mirror state for a user.

### `GET /api/v1/mirror/daily/{user_id}`
Get daily mirror report.

### `POST /api/v1/mirror/dream`
Trigger mirror dream cycle.

### `POST /api/v1/mirror/fine-tune`
Trigger mirror auto fine-tuning.

### `GET /api/os/status`
OS control status.

### `POST /api/os/execute`
Execute an OS control command.

---

## 9. Analytics & Monitoring

### `GET /api/analytics/overview`
System analytics overview.

### `GET /api/analytics/activity`
User activity analytics.

### `GET /api/analytics/clone-agents/feed`
Clone agents activity feed.

### `GET /api/analytics/clone-agents/stats`
Clone agents statistics.

### `GET /api/analytics/depin/coverage`
DePIN coverage map.

### `GET /api/analytics/depin/map`
DePIN network map.

### `GET /api/apis/status`
API endpoints status.

### `GET /api/v1/operator/status`
Operator status.

### `POST /api/v1/rag/query`
Query the RAG knowledge base.

### `POST /api/v1/rag/cosmos/evolve`
Trigger cosmos knowledge evolution.

### `GET /status`
System status overview.

### `GET /healthz`
Simple health check alias.

---

## 10. Consensus & Governance

### `GET /api/v1/consensus/status`
Consensus system status.

### `POST /api/v1/consensus/vote`
Submit a vote.

### `POST /api/v1/consensus/weighted-vote`
Submit a weighted vote.

### `GET /api/consensus/proposals`
List governance proposals.

### `POST /api/consensus/proposals`
Create a proposal.

### `POST /api/consensus/proposals/{proposal_id}/vote`
Vote on a proposal.

---

## 11. Nepal Government Connectors

### `GET /api/v1/np/provinces`
List Nepal provinces.

### `GET /api/v1/np/districts`
List Nepal districts.

### `GET /api/v1/np/palikas`
List Nepal palikas (municipalities).

### `GET /api/v1/np/ministries`
List Nepal government ministries.

### `GET /api/v1/np/banks`
List Nepal banks.

### `GET /api/v1/np/isps`
List Nepal ISPs.

### `GET /api/v1/health/hospitals`
List Nepal hospitals.

### `GET /api/v1/education/schools`
List Nepal schools.

### `GET /api/v1/education/universities`
List Nepal universities.

### `GET /api/v1/tourism/hotels`
List Nepal hotels.

---

## 12. Security & Compliance

### `POST /api/v1/security/hsm/biometric`
Biometric verification via HSM.

### `GET /api/security/audit-log`
Security audit log.

### `GET /api/security/events`
Security events.

### `GET /api/security/metrics`
Security metrics.

---

## 13. Legacy Routes

The following routes exist for backward compatibility:

| Method | Path | Maps To |
|--------|------|---------|
| GET | `/personal/status` | Personal OS status |
| GET | `/personal/clones` | Clone management |
| POST | `/api/v1/auth/login` | Auth login |
| POST | `/api/v1/auth/register` | Auth register |
| POST | `/api/v1/auth/refresh` | Auth refresh |
| GET | `/api/v1/operator/status` | Operator status |
| POST | `/api/v1/orchestrator/process` | Orchestrator process |
| GET | `/api/v1/orchestrator/status` | Orchestrator status |

---

## Error Responses

All endpoints return errors in the following format:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

---

## Rate Limiting

Rate limits are applied per route group:

| Route Group | Requests | Window |
|-------------|----------|--------|
| `/auth/*` | 20 | 60s |
| `/api/chat` | 30 | 60s |
| `/api/self/*` | 60 | 60s |
| `/api/analytics/*` | 30 | 60s |
| Default | 60 | 60s |

---

## WebSocket

### `GET /socket.io/`
Socket.IO endpoint for real-time communication.

Events:
- `chat:message` — Incoming chat messages
- `mesh:peer_update` — Mesh peer status changes
- `self:scan_complete` — Codebase scan completed
- `self:issue_detected` — New issue detected
- `dream:cycle_complete` — Dream cycle completed
- `evolution:suggestion` — New evolution suggestion
