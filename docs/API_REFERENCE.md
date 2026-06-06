# API Reference

> **Version:** 1.0.0+build42 (RC-1)  
> **Base URL:** `http://localhost:8000`  
> **Auth:** JWT Bearer token (required for most endpoints)  
> **Source:** [`core/api_endpoints.py`](core/api_endpoints.py)

---

## Authentication

### POST `/auth/register`
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure-password",
  "name": "User Name"
}
```

**Response:** `201 Created`
```json
{
  "asim_id": "asim_abc123",
  "email": "user@example.com",
  "name": "User Name",
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### POST `/auth/login`
Authenticate and receive JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure-password"
}
```

**Response:** `200 OK`
```json
{
  "asim_id": "asim_abc123",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "role": "citizen"
}
```

### GET `/auth/me`
Get current user profile. **Auth required.**

**Response:** `200 OK`
```json
{
  "asim_id": "asim_abc123",
  "email": "user@example.com",
  "name": "User Name",
  "role": "citizen",
  "created_at": "2026-05-31T10:00:00Z"
}
```

### GET `/auth/users`
List all registered users. **Auth required (admin).**

---

## Personal OS

All endpoints in this section require authentication.

### GET `/personal/status`
Get Personal OS dashboard status.

**Response:**
```json
{
  "mode": "focus",
  "notifications": [...],
  "clones": [...],
  "documents": [...],
  "recent_memory": [...],
  "rule_count": 3,
  "is_online": true
}
```

### POST `/personal/mode`
Set Personal OS mode.

**Parameters:** `mode` (query) — `focus`, `social`, `creative`, `offline`

### GET `/personal/clones`
Get personal clone configurations.

### POST `/personal/rule`
Add a personal rule.

**Request:** `rule` (query) — Rule description string

---

## Health & Status

### GET `/health`
Full system health check. No auth required.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0+build42",
  "timestamp": "2026-05-31T10:00:00Z",
  "components": {
    "database": "connected",
    "llm": "available",
    "dharma": "active",
    "clones": "initialized",
    "kernel": "running",
    "mesh": "online",
    "memory": "operational"
  }
}
```

### GET `/status`
System status summary with component details.

---

## LLM & Chat

### POST `/llm/chat`
Send a chat message to the LLM.

**Request:**
```json
{
  "message": "Hello, how can you help me?",
  "context": {},
  "model_preference": null
}
```

**Response:**
```json
{
  "response": "I can help you with...",
  "model": "gpt-4",
  "mode": "auto",
  "tokens": 42
}
```

### POST `/llm/chat/stream`
Streaming LLM chat response (Server-Sent Events).

### POST `/api/chat`
API bridge chat endpoint (alternative route).

---

## Clones

### GET `/clones/list`
List all available world clones.

### POST `/clones/chat`
Chat with the clone orchestrator.

**Request:**
```json
{
  "message": "What's the weather like?",
  "context": {}
}
```

### POST `/clones/direct/{role_name}`
Direct message a specific clone by role name.

### POST `/clones/agent-mode`
Enable/disable autonomous agent mode.

**Parameters:** `enabled` (query, default: `true`)

---

## WebSocket

### WebSocket `/api/ws/universal-chat`
Real-time chat with personal context + VETO + LLM + clone status.

**Message format:**
```json
{
  "type": "message",
  "content": "Hello world",
  "context": {}
}
```

**Response format:**
```json
{
  "type": "response",
  "content": "Hello! How can I help?",
  "veto": "pass",
  "clone_status": {...}
}
```

---

## Dharma-Chakra

### GET `/dharma/status`
Get dharma framework status.

### POST `/dharma/process`
Process input through dharma framework.

### POST `/dharma/evaluate`
Evaluate action ethically.

### GET `/dharma/countries`
Get list of configured countries.

### POST `/dharma/country/register`
Register a new country configuration.

### Layer Statistics (GET)
| Endpoint | Description |
|----------|-------------|
| `GET /dharma/layers/pingala` | Pingala layer statistics |
| `GET /dharma/layers/shulba` | Shulba layer statistics |
| `GET /dharma/layers/panini` | Panini layer statistics |
| `GET /dharma/layers/nyaya` | Nyaya layer statistics |
| `GET /dharma/layers/upanishad` | Upanishad layer statistics |
| `GET /dharma/layers/tantra` | Tantra layer statistics |

---

## ZKP (Zero-Knowledge Proofs)

### GET `/zkp/pending`
List pending ZKP confirmations. **Auth required.**

### POST `/zkp/confirm/{token}`
Confirm a pending ZKP request. **Auth required.**

### POST `/zkp/reject/{token}`
Reject a pending ZKP request. **Auth required.**

### GET `/zkp/status/{token}`
Check status of a ZKP request.

### Real ZKP Endpoints

| Endpoint | Description | Auth |
|----------|-------------|------|
| `GET /api/zkp/real/status` | ZKP system status | No |
| `POST /api/zkp/real/create-identity-proof` | Create identity proof | Yes |
| `POST /api/zkp/real/verify` | Verify a proof | Yes |

---

## HDT (Human Digital Twin)

### GET `/hdt/me`
Get current user's HDT profile. **Auth required.**

### POST `/hdt/update`
Update HDT data. **Auth required.**

**Request:**
```json
{
  "affinities": {...},
  "preferences": {...}
}
```

### GET `/hdt/top-clones`
Get top clone affinities. **Auth required.**

---

## Mesh & Network

### GET `/mesh/nodes`
List all mesh network nodes.

### POST `/mesh/join`
Join the mesh network.

**Parameters:** `name` (query, default: `MyNode`), `node_type` (query, default: `citizen`)

---

## LiteLLM & Chaitanya Router

### GET `/litellm/status`
Get LiteLLM status.

### POST `/litellm/complete`
Complete a request with Chaitanya Router.

### GET `/litellm/metrics`
Get model metrics.

### GET `/litellm/knowledge-graph`
Get holographic knowledge graph.

### POST `/litellm/register-node`
Register a node in holographic network.

### GET `/litellm/nodes`
Get all registered nodes.

---

## File Operations

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/files/list` | GET | List files in directory | Some |
| `/files/read` | GET | Read file content | Some |
| `/files/write` | POST | Write/create file | Yes |
| `/files/delete` | DELETE | Delete file or directory | Yes |
| `/files/create_directory` | POST | Create directory | Yes |
| `/files/search` | GET | Search for files | Some |

All file operations path-sanitized via `_safe_path()` to prevent directory traversal.

---

## Tools

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tools/execute` | POST | Execute an ASIMNEXUS tool |
| `/tools/list` | GET | List all available tools |
| `/tools/file/read` | POST | Read a file via tool |
| `/tools/file/write` | POST | Write to a file via tool |
| `/tools/file/delete` | POST | Delete a file via tool |
| `/tools/file/list` | POST | List files via tool |
| `/tools/command/execute` | POST | Execute a system command |
| `/tools/python/execute` | POST | Execute Python code |
| `/tools/network/get` | POST | HTTP GET request |
| `/tools/network/post` | POST | HTTP POST request |

---

## GPU

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/gpu/status` | GET | Comprehensive GPU status |
| `/gpu/available` | GET | Check GPU availability |
| `/gpu/optimal-config` | GET | Get optimal LLM config for GPU |
| `/gpu/recommendations` | GET | GPU optimization recommendations |
| `/gpu/data/process` | POST | Process data with GPU acceleration |
| `/gpu/data/status` | GET | GPU data processor status |

---

## System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/system/scan` | GET | Full system scan |
| `/system/summary` | GET | System summary |
| `/services` | GET | List registered services |
| `/services/{name}` | GET | Get service by name |
| `/services/register` | POST | Register a new service |

---

## Automation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/automation/initialize` | POST | Initialize Automation OS |
| `/automation/status` | GET | Get Automation OS status |
| `/automation/process` | POST | Process autonomous request |
| `/automation/create` | POST | Create automation task |
| `/automation/list` | GET | List all automations |
| `/automation/execute` | POST | Execute automation task |
| `/automation/{task_id}` | DELETE | Delete automation task |

---

## Codebase

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/codebase/index` | GET | Index ASIMNEXUS codebase |
| `/codebase/search` | GET | Search codebase (`?query=...`) |
| `/codebase/file/{path}` | GET | Get file content from codebase |
| `/codebase/summary` | GET | Codebase summary |

---

## Self-Knowledge

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/self_knowledge/description` | GET | ASIMNEXUS self-description |
| `/self_knowledge/query` | POST | Query self-knowledge |

---

## Analytics & Security (Admin)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analytics/overview` | GET | Analytics overview |
| `/api/analytics/performance` | GET | Performance metrics |
| `/api/analytics/usage` | GET | Usage statistics |
| `/api/security/status` | GET | Security status |
| `/api/security/vulnerabilities` | GET | Vulnerability report |
| `/api/security/scan` | POST | Run security scan |
| `/admin/request-logs` | GET | Request logs (admin) |

---

## Virtual Office

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/virtual_office/status` | GET | Virtual office status |
| `/api/virtual_office/join` | POST | Join a virtual room |
| `/api/virtual_office/leave` | POST | Leave a virtual room |

---

## API Bridge & Discovery

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/bridge/providers` | GET | List bridge providers | Yes |
| `/api/bridge/call/{provider}` | POST | Call a provider | Yes |
| `/api/bridge/chat/{provider}` | POST | Chat via provider | Yes |
| `/api/discovery/status` | GET | Discovery service status | No |
| `/api/discovery/start` | POST | Start discovery scan | No |

---

## Local LLM

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/local-llm/status` | GET | Local LLM status |
| `/api/local-llm/models` | GET | Available local models |
| `/api/local-llm/load/{model}` | POST | Load a model |
| `/api/local-llm/chat` | POST | Chat with local LLM |

---

## Evaluation & Scoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/evaluation/code` | POST | Evaluate code quality |
| `/plagiarism/check` | POST | Check for plagiarism |
| `/leaderboard` | GET | Get leaderboard |
| `/scoring/evaluate` | POST | Multi-criteria scoring |
| `/participants/register` | POST | Register participant |
| `/submissions` | POST | Create submission |

---

## Routing

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/router/route` | POST | Route a prompt through privacy-classified model |
| `POST /api/router/chat` | POST | Chat with privacy-aware routing |

---

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (missing/invalid parameters) |
| 401 | Unauthorized (missing/invalid JWT) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 422 | Unprocessable Entity (validation error) |
| 500 | Internal Server Error |

---

## Authentication Header

```http
Authorization: Bearer <jwt-token>
```

For WebSocket connections, pass the token as a query parameter:
```
ws://localhost:8000/api/ws/universal-chat?token=<jwt-token>
```

---

*For the complete source, see [`core/api_endpoints.py`](core/api_endpoints.py) (2,816 lines).*
