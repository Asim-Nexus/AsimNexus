# AsimNexus Installation Guide

> **Version:** 1.0.0+build42 (RC-1)  
> **Last updated:** 2026-05-31  
> **See also:** [`docs/ARCHITECTURE.md`](ARCHITECTURE.md), [`docs/RELEASE_PROCESS.md`](RELEASE_PROCESS.md)

---

## Prerequisites

| Dependency | Minimum Version | Purpose |
|------------|----------------|---------|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend build/runtime |
| npm | 9+ | Frontend package manager |
| Docker (optional) | 24+ | Containerized deployment |
| Git | 2.30+ | Version control |

---

## Quick Start (Local Development)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AsimNexus
```

### 2. Backend Setup

```bash
# Create virtual environment (recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
# source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

**Note:** If `requirements.txt` is not present, the system falls back gracefully — missing optional dependencies produce warning logs but do not block startup.

### 3. Frontend Setup

```bash
cd frontend/react
npm install
cd ../..
```

### 4. Environment Configuration

Copy the example environment file:

```bash
copy .env.example .env
# or on Linux/Mac:
# cp .env.example .env
```

Configure at minimum:

```ini
# Required
JWT_SECRET=your-256-bit-secret-key-here

# Optional — LLM providers (at least one recommended)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
DEEPSEEK_API_KEY=...

# Optional — NVIDIA for Founder Clones
NVIDIA_API_KEY=nvapi-...
```

### 5. Run the Application

```bash
# Start both backend (port 8000) and frontend (port 3000)
python main.py

# Or start separately:
# Backend only:
# python main.py --port 8000
#
# Frontend only:
# cd frontend/react && npm start
```

### 6. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "ok",
#   "version": "1.0.0+build42",
#   "components": {
#     "database": "connected",
#     "llm": "available|unavailable",
#     "dharma": "active",
#     "clones": "initialized",
#     "kernel": "running"
#   }
# }
```

---

## Docker Deployment

### Build and Run

```bash
# Build all services
docker-compose build

# Start in detached mode
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify health
curl http://localhost:8000/health
```

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | FastAPI server |
| `frontend` | 3000 | React SPA (if configured) |

---

## Kubernetes Deployment

```bash
# Create namespace
kubectl apply -f k8s/asimnexus-namespace.yaml

# Deploy all resources
kubectl apply -f k8s/

# Verify
kubectl get pods -n asimnexus
kubectl get svc -n asimnexus
```

**Note:** K8s deployment requires proper configuration of secrets, ingress, and storage. See [`k8s/`](k8s/) for manifests.

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | — | **Required.** JWT signing secret (256-bit minimum) |
| `ASIM_RELEASE_CHANNEL` | `stable` | Release channel (`stable`, `rc`, `beta`, `dev`) |
| `OPENAI_API_KEY` | — | OpenAI API key for cloud LLM |
| `ANTHROPIC_API_KEY` | — | Anthropic API key for Claude |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `DEEPSEEK_API_KEY` | — | DeepSeek API key |
| `NVIDIA_API_KEY` | — | NVIDIA API key for Founder Clones |

### Data Directories

| Path | Purpose |
|------|---------|
| `data/asim_core.db` | Core database (users, messages, jobs) |
| `data/users/{asim_id}/` | Per-user workspace (personal OS data) |
| `deploy/release/version.txt` | Single source of truth for version |
| `deploy/release/releases.json` | Release history |
| `deploy/release/rollback_log.jsonl` | Rollback audit trail |

---

## Troubleshooting

### Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError` | Missing dependency | `pip install -r requirements.txt` |
| Port 8000 in use | Another process | `python main.py --port 8001` |
| LLM not responding | No API key configured | Set `OPENAI_API_KEY` or use local GGUF |
| Frontend can't connect | Backend not running | Start backend first, verify port |
| Database errors | Corrupted DB | Delete `data/asim_core.db` and restart |

### Logs

```bash
# Backend logs go to stdout/stderr
# Look for:
# - "AsimNexus" prefix in log lines
# - WARNING for missing optional dependencies
# - ERROR for critical failures

# Example: check if Dharma VETO is active
python -c "from core.dharma.dharma_veto import get_dharma_veto; print(get_dharma_veto().status())"
```

### Reset

```bash
# Full reset (deletes all data)
rm -rf data/
rm -f deploy/release/releases.json

# Recreate structure
python main.py  # auto-creates directories on startup
```

---

## Next Steps

- Read the [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for system understanding
- Explore the API via [`docs/API_REFERENCE.md`](API_REFERENCE.md)
- Review component status in [`docs/STATUS.md`](STATUS.md)
- Check release notes in [`docs/RELEASE_NOTES_RC1.md`](RELEASE_NOTES_RC1.md)
