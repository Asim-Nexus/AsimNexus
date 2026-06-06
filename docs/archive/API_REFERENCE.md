# AsimNexus API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
Most endpoints require JWT Bearer token:
```
Authorization: Bearer <token>
```

---

## Core Endpoints

### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "checks": {
    "identity": {"status": "ok", "users": 5},
    "veto": {"status": "ok", "checks_total": 42},
    "router": {"status": "ok", "sector": "general"},
    "clones": {"status": "ok", "count": 15},
    "zkp": {"status": "ok", "pending_count": 0}
  },
  "uptime_seconds": 3600
}
```

---

## Authentication

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "display_name": "Ram Bahadur",
  "email": "ram@example.com",
  "password": "secure123",
  "phone": "+977-98XXXXXXXX",
  "country_code": "NP",
  "national_id": "XX-XX-XX-XXXXX"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "ram@example.com",
  "password": "secure123"
}
```

Response:
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "asim_id": "asim_abc123",
    "display_name": "Ram Bahadur",
    "role": "citizen"
  }
}
```

---

## Chat & AI

### Universal Chat
```http
POST /llm/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "नेपालको इतिहास बताउनुहोस्",
  "sector": "general"
}
```

### Chat with Specific Clone
```http
POST /clones/direct/{role_name}
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "What are the best investment strategies?",
  "sector": "finance"
}
```

Roles: `Tech Architect`, `Financial Oracle`, `Legal Guardian`, `Health Sage`, etc.

### Auto-Routed Clone Chat
```http
POST /clones/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "I need help with both coding and legal advice"
}
```

---

## 15 Founder Clones

### List All Clones
```http
GET /clones/list
Authorization: Bearer <token>
```

Response:
```json
{
  "clones": [
    {
      "role": "Tech Architect",
      "status": "active",
      "capabilities": ["code", "architecture", "review"]
    },
    {
      "role": "Financial Oracle",
      "status": "active",
      "capabilities": ["investment", "budget", "tax"]
    }
  ]
}
```

### Toggle Agent Mode
```http
POST /clones/agent-mode?enabled=true
Authorization: Bearer <token>
```

---

## Human Digital Twin (HDT)

### Get My HDT
```http
GET /hdt/me
Authorization: Bearer <token>
```

Response:
```json
{
  "asim_id": "asim_abc123",
  "bio": "Software developer from Nepal",
  "skills": ["Python", "React", "AI"],
  "values": ["Privacy", "Open Source", "Education"],
  "goals": ["Build helpful AI", "Learn continuously"],
  "top_clones": ["Tech Architect", "Research Explorer"],
  "interaction_count": 42
}
```

### Update HDT
```http
POST /hdt/update
Authorization: Bearer <token>
Content-Type: application/json

{
  "bio": "Updated bio",
  "skills": ["Python", "React", "AI", "Rust"],
  "goals": ["New goal added"]
}
```

### Get Top Clones (by affinity)
```http
GET /hdt/top-clones
Authorization: Bearer <token>
```

---

## ZKP (Zero-Knowledge Proof)

### List Pending Confirmations
```http
GET /zkp/pending
Authorization: Bearer <token>
```

### Confirm Action
```http
POST /zkp/confirm/{token}
Authorization: Bearer <token>
```

### Reject Action
```http
POST /zkp/reject/{token}
Authorization: Bearer <token>
```

### Real ZKP - Create Identity Proof
```http
POST /api/zkp/real/create-identity-proof
Authorization: Bearer <token>
Content-Type: application/json

{
  "identity": {
    "name": "Ram Bahadur",
    "verified": true
  },
  "nonce": "random-nonce-123"
}
```

### Real ZKP - Verify Proof
```http
POST /api/zkp/real/verify
Content-Type: application/json

{
  "proof": {
    "commitment": "abc123...",
    "proof": "def456...",
    "public_inputs": {"statement": "Valid identity"},
    "timestamp": "2024-01-15T10:00:00",
    "verifier_key_hash": "xyz789..."
  },
  "statement": "Valid identity"
}
```

---

## Universal API Bridge

### List Providers
```http
GET /api/bridge/providers
Authorization: Bearer <token>
```

Response:
```json
{
  "available": true,
  "providers": [
    {"name": "OpenAI", "provider": "openai", "enabled": true},
    {"name": "Google AI", "provider": "google", "enabled": true}
  ]
}
```

### Call External API
```http
POST /api/bridge/call/{provider}
Authorization: Bearer <token>
Content-Type: application/json

{
  "endpoint": "chat/completions",
  "method": "POST",
  "payload": {
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}]
  }
}
```

### Unified Chat
```http
POST /api/bridge/chat/{provider}
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Explain quantum computing",
  "model": "gpt-4"
}
```

---

## Auto Discovery

### Get Discovery Status
```http
GET /api/discovery/status
```

Response:
```json
{
  "available": true,
  "running": true,
  "node_id": "asim-node-ram",
  "nearby_nodes": [
    {
      "node_id": "asim-node-sita",
      "ip": "192.168.1.45",
      "type": "personal",
      "capabilities": ["chat", "file_share"],
      "latency_ms": 12.5
    }
  ]
}
```

### Start Discovery
```http
POST /api/discovery/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "node_id": "my-node-123",
  "node_type": "personal"
}
```

---

## Local LLM (Offline)

### Get Status
```http
GET /api/local-llm/status
```

Response:
```json
{
  "available": true,
  "current_model": "llama-2-7b",
  "total_models": 3,
  "loaded_models": 1,
  "hardware": {
    "cpu_count": 8,
    "gpu_available": false
  }
}
```

### List Models
```http
GET /api/local-llm/models
```

### Load Model
```http
POST /api/local-llm/load/{model_name}
Authorization: Bearer <token>
```

### Local Chat (Offline)
```http
POST /api/local-llm/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "What is machine learning?",
  "system_prompt": "You are a helpful assistant.",
  "stream": false
}
```

---

## WebSocket

Connect to real-time chat:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'chat',
    message: 'Hello',
    token: 'your-jwt-token'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

Message Types:
- `chat` — Send message
- `clone_status_request` — Get clone status
- `zkp_confirm` — Confirm via WebSocket
- `zkp_reject` — Reject via WebSocket

---

## Analytics & Admin

### System Overview
```http
GET /api/analytics/overview
```

### Performance Metrics
```http
GET /api/analytics/performance
```

### Request Logs (Admin)
```http
GET /admin/request-logs?limit=100
Authorization: Bearer <token>
```

---

## File Manager

### List Files
```http
GET /files/list?path=docs
Authorization: Bearer <token>
```

### Read File
```http
GET /files/read?path=docs/readme.txt
Authorization: Bearer <token>
```

### Write File
```http
POST /files/write
Authorization: Bearer <token>
Content-Type: application/json

{
  "path": "docs/notes.txt",
  "content": "My notes here"
}
```

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Get valid token |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Slow down requests |
| 500 | Server Error | Check logs |
| 503 | Service Unavailable | Component not ready |

---

## Rate Limits

- Standard: 100 requests/minute
- Chat: 60 messages/minute
- File operations: 30/minute
- Admin endpoints: 10/minute

---

For full interactive docs, visit: `http://localhost:8000/docs`
