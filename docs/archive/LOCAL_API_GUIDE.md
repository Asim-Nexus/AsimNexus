# ASIMNEXUS Local API Guide

## 🏠 Local Development Setup

**Base URL:** `http://localhost:8000`
**No Authentication Required** (Local mode)
**Content-Type:** `application/json`

---

## ✅ Working Endpoints

### 1. Health Check
```http
GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "active": true,
  "verified": true
}
```

### 2. LLM Chat (Gemma 4) ✅ WORKING
```http
POST http://localhost:8000/llm/chat
Content-Type: application/json

{
  "message": "Hello ASIMNEXUS",
  "max_tokens": 512,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "Generated text from Gemma 4...",
  "model": "gemma-4-7b-it",
  "tokens_used": 61,
  "device": "cuda"
}
```

**Test Command:**
```bash
python -c "import requests; r = requests.post('http://localhost:8000/llm/chat', json={'message': 'Hello'}); print(r.json()['response'])"
```

### 3. LLM Status
```http
GET http://localhost:8000/llm/status
```

**Response:**
```json
{
  "model_loaded": true,
  "model_path": "./models/gemma-4-E4B-it-IQ4_XS.gguf",
  "device": "cuda"
}
```

### 4. Root Endpoint
```http
GET http://localhost:8000/
```

**Response:**
```json
{
  "message": "ASIMNEXUS API v2.0",
  "status": "operational",
  "endpoints": {
    "health": "/health",
    "status": "/status",
    "llm_chat": "/llm/chat",
    "llm_status": "/llm/status"
  }
}
```

---

## ⚠️ WebSocket Frontend Issue

**Problem:** WebSocket (ws://localhost:3000) times out when calling LLM
**Cause:** Gemma 4 takes 84+ seconds, exceeds WebSocket keepalive timeout
**Solution:** Use HTTP API directly or implement polling (Option B)

---

## 🚀 Quick Start

```bash
# Start ASIMNEXUS
python main.py

# Test LLM (working)
python -c "import requests; r = requests.post('http://localhost:8000/llm/chat', json={'message': 'Hello'}); print(r.json())"
```

---

## 📊 System Status

- **Backend API:** ✅ Running (http://localhost:8000)
- **LLM Engine:** ✅ Loaded (Gemma 4, CUDA GPU)
- **WebSocket:** ⚠️ Running but LLM timeout
- **HTTP Frontend:** ❌ Not started

---

## 🔧 Troubleshooting

**LLM Timeout:**
- Backend API works (60s timeout)
- WebSocket fails (84s+ response time)
- Use HTTP API directly for now

**Model Not Loaded:**
- Check model file: `./models/gemma-4-E4B-it-IQ4_XS.gguf`
- Check CUDA: `nvidia-smi`
