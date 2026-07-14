# Deployment Guide

> **AsimNexus — Comprehensive Deployment Guide**
> Version: 1.0.0-rc.2 | Last Updated: 2025-07-03

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Docker Deployment](#3-docker-deployment)
4. [Bare-Metal Deployment](#4-bare-metal-deployment)
5. [Cloud Deployment](#5-cloud-deployment)
6. [Nepal-Specific Deployment](#6-nepal-specific-deployment)
7. [Environment Configuration](#7-environment-configuration)
8. [Database Setup](#8-database-setup)
9. [Mesh Networking Setup](#9-mesh-networking-setup)
10. [Monitoring & Observability](#10-monitoring--observability)
11. [Security Hardening](#11-security-hardening)
12. [Backup & Disaster Recovery](#12-backup--disaster-recovery)
13. [Deployment Checklist](#13-deployment-checklist)

---

## 1. Overview

AsimNexus can be deployed in multiple configurations:

| Configuration | Use Case | Resources |
|--------------|----------|-----------|
| **Single-node Docker** | Development / Small team | 2 CPU, 4 GB RAM |
| **Multi-node Docker Swarm** | Medium production | 4+ nodes, 8 GB RAM each |
| **Kubernetes** | Large-scale production | 6+ nodes, 16 GB RAM each |
| **Bare-metal** | High-security / Nepal gov | Dedicated servers |
| **Hybrid (Cloud + On-prem)** | Nepal deployment | Cloud + local mesh |

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer (HAProxy/Nginx)            │
├───────────────────────┬─────────────────────────────────────┤
│   Backend (FastAPI)   │   Frontend (React + PWA)            │
│   :8000               │   :3000 / :443                      │
├───────────┬───────────┴─────────────────────────────────────┤
│  PostgreSQL 15  │  Redis 7  │  Prometheus  │  Grafana       │
├───────────┴─────────────────────────────────────────────────┤
│  Docker Compose / Kubernetes (Production)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 8+ cores |
| RAM | 4 GB | 16+ GB |
| Disk | 20 GB SSD | 100+ GB NVMe |
| Network | 100 Mbps | 1 Gbps |
| OS | Ubuntu 22.04 / Windows Server 2022 | Ubuntu 24.04 LTS |

### Software Requirements

- **Docker** 24.0+ (with Compose v2)
- **Python** 3.11+
- **Node.js** 20 LTS+
- **PostgreSQL** 15+
- **Redis** 7+
- **Git** 2.40+

### Network Ports

| Port | Protocol | Service |
|------|----------|---------|
| 8000 | TCP | Main API (REST) |
| 8080 | TCP | Alternative API |
| 3000 | TCP | Frontend (dev) |
| 443 | TCP | Frontend (prod HTTPS) |
| 7331 | UDP | LAN Discovery |
| 7332 | UDP | Kademlia DHT |
| 7333 | TCP | WebSocket P2P |
| 7334 | TCP | Relay Service |
| 7335 | TCP | Bootstrap Service |
| 7336 | UDP | Rendezvous Service |
| 9090 | TCP | Prometheus |
| 3001 | TCP | Grafana |

---

## 3. Docker Deployment

### 3.1 Quick Start (Single Node)

```bash
# Clone the repository
git clone https://github.com/AsimNexus/asimnexus.git
cd asimnexus

# Copy environment configuration
cp .env.example .env
# Edit .env with your settings

# Build and start all services
docker compose up -d

# Verify deployment
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

### 3.2 Production Docker Compose

```bash
# Production deployment
docker compose -f docker-compose.prod.yml up -d

# Scale backend nodes
docker compose -f docker-compose.prod.yml up -d --scale asimnexus=3
```

### 3.3 Multi-Stage Build

The Dockerfile uses multi-stage builds for smaller images:

```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/ .
RUN npm ci && npm run build

# Stage 2: Build backend
FROM python:3.11-slim AS backend
WORKDIR /app
COPY --from=frontend-builder /app/frontend/build ./frontend/build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.4 Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml asimnexus

# List services
docker service ls

# Scale a service
docker service scale asimnexus_backend=5
```

---

## 4. Bare-Metal Deployment

### 4.1 Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python -m database.migrate

# Start the server
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4.2 Frontend Setup

```bash
cd frontend
npm ci
npm run build

# Serve with Nginx
# Copy build/ to /var/www/asimnexus/
```

### 4.3 Process Management (systemd)

```ini
# /etc/systemd/system/asimnexus.service
[Unit]
Description=AsimNexus Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=asimnexus
WorkingDirectory=/opt/asimnexus
ExecStart=/opt/asimnexus/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5
Environment=ASIM_ENV=production

[Install]
WantedBy=multi-user.target
```

---

## 5. Cloud Deployment

### 5.1 AWS Deployment

```bash
# Using ECS with Fargate
aws ecs create-cluster --cluster-name asimnexus

# Using EC2 with Auto Scaling
# See infra/cloudformation/ for templates
```

### 5.2 GCP Deployment

```bash
# Using Cloud Run
gcloud run deploy asimnexus \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 5.3 Azure Deployment

```bash
# Using Azure Container Instances
az container create \
  --resource-group asimnexus \
  --name asimnexus-backend \
  --image asimnexus/backend:latest \
  --ports 8000
```

---

## 6. Nepal-Specific Deployment

See [`docs/operations/NEPAL_DEPLOYMENT_GUIDE.md`](../operations/NEPAL_DEPLOYMENT_GUIDE.md) for the full Nepal deployment guide.

### Key Considerations

1. **Data Sovereignty** — All citizen data must remain within Nepal's borders
2. **Language Support** — Nepali language models and UI pre-configured
3. **Government Integration** — e-Residency, tax filing, ministry portals
4. **Local Infrastructure** — Nepal-hosted servers with mesh networking
5. **Regulatory Compliance** — Nepal IT Bill 2075, Data Protection Act

### Quick Nepal Deployment

```bash
# Set Nepal-specific environment
cp .env.nepal.example .env

# Deploy with Nepal configuration
docker compose -f docker-compose.nepal.yml up -d

# Verify Nepal integrations
curl http://localhost:8000/api/nepal/status
```

---

## 7. Environment Configuration

### Core Variables

```bash
# .env — Core Configuration
ASIM_ENV=production
SECRET_KEY=<generate-with: openssl rand -hex 32>
DATABASE_URL=postgresql://user:pass@localhost:5432/asimnexus
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO

# Mesh Networking
MESH_ENABLED=true
MESH_PORT=7333
MESH_BOOTSTRAP_NODES=node1.asimnexus.io:7335,node2.asimnexus.io:7335

# Security
HARD_LOCK_ENABLED=true
BIOMETRIC_GATE_ENABLED=true
TPM_ENABLED=false

# Governance
GOVERNMENT_LAYER_ENABLED=true
ENTERPRISE_LAYER_ENABLED=true
POWER_BALANCE_ENABLED=true

# Agent Contracts
AGENT_CONTRACT_ENABLED=true
AGENT_CONTRACT_DB_PATH=data/agent_contracts.jsonl

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
SENTRY_DSN=
```

### Environment-Specific Files

| File | Purpose |
|------|---------|
| `.env.example` | Template with all variables |
| `.env.production` | Production settings |
| `.env.staging` | Staging/QA settings |
| `.env.nepal` | Nepal-specific settings |
| `.env.development` | Local development |

---

## 8. Database Setup

### PostgreSQL

```bash
# Create database
createdb asimnexus

# Run migrations
python -m database.migrate

# Verify
python -c "from database import check_connection; print(check_connection())"
```

### Redis

```bash
# Verify Redis connection
redis-cli ping
# Should return: PONG
```

### Vector Database (ChromaDB)

ChromaDB is used for vector embeddings and runs in-process. Data is stored at `data/chromadb/`.

---

## 9. Mesh Networking Setup

### Single Node

Mesh networking is optional for single-node deployments. Set `MESH_ENABLED=false` in `.env`.

### Multi-Node

```bash
# On each node, set:
MESH_ENABLED=true
MESH_BOOTSTRAP_NODES=<comma-separated list of bootstrap nodes>

# Verify mesh connectivity
curl http://localhost:8000/api/mesh/nodes
```

### Mesh Components

| Component | Description |
|-----------|-------------|
| Kademlia DHT | Distributed hash table for node discovery |
| CRDT Sync | Conflict-free replicated data types for data sync |
| Hole Punching | NAT traversal for peer-to-peer connections |
| STUN/TURN | Relay server for NAT'd clients |
| Auto-Discovery | LAN broadcast/multicast discovery |
| Multi-Mesh Router | Load-balanced routing across mesh networks |

---

## 10. Monitoring & Observability

### Prometheus

Metrics are exposed at `/metrics`. Configure Prometheus to scrape:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'asimnexus'
    static_configs:
      - targets: ['localhost:8000']
```

### Grafana

Import the dashboard from [`monitoring/grafana_dashboard.json`](../monitoring/grafana_dashboard.json).

### Key Metrics

| Metric | Description |
|--------|-------------|
| `asim_requests_total` | Total API requests |
| `asim_request_duration_seconds` | Request latency |
| `asim_active_connections` | Active WebSocket connections |
| `asim_mesh_nodes` | Connected mesh nodes |
| `asim_contracts_active` | Active agent contracts |
| `asim_governance_actions` | Governance actions taken |

---

## 11. Security Hardening

### Production Security Checklist

- [ ] Set strong `SECRET_KEY` (min 32 bytes, cryptographically random)
- [ ] Enable HTTPS with valid TLS certificate
- [ ] Enable `HARD_LOCK_ENABLED=true`
- [ ] Enable `BIOMETRIC_GATE_ENABLED=true` if biometric hardware available
- [ ] Configure rate limiting on API endpoints
- [ ] Set up WAF (Web Application Firewall)
- [ ] Enable database encryption at rest
- [ ] Configure network firewalls (only expose ports 443 and 8000)
- [ ] Set up intrusion detection (fail2ban, OSSEC)
- [ ] Regular security audits using `scripts/security_audit.py`

### Network Security

```bash
# Example iptables rules
iptables -A INPUT -p tcp --dport 8000 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

---

## 12. Backup & Disaster Recovery

### Automated Backups

```bash
# Database backup
python scripts/db_backup.py

# Configuration backup
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env config/

# Full system backup
tar -czf asimnexus-backup-$(date +%Y%m%d).tar.gz \
  --exclude=venv \
  --exclude=node_modules \
  --exclude=__pycache__ \
  .
```

### Recovery Steps

1. Restore database from backup
2. Restore configuration files
3. Rebuild and restart services
4. Verify mesh connectivity
5. Run health checks

### Disaster Recovery Plan

See [`docs/operations/DISASTER_RECOVERY.md`](../operations/DISASTER_RECOVERY.md) for the full DR plan.

---

## 13. Deployment Checklist

### Pre-Deployment

- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] Security audit clean: `python scripts/security_audit.py`
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] SSL/TLS certificates obtained
- [ ] Firewall rules configured
- [ ] Backup system verified

### Deployment

- [ ] Build Docker images
- [ ] Push to container registry
- [ ] Pull on target servers
- [ ] Start services
- [ ] Verify health endpoints
- [ ] Verify mesh connectivity
- [ ] Verify governance layer
- [ ] Verify agent contract system

### Post-Deployment

- [ ] Monitoring alerts configured
- [ ] Log aggregation working
- [ ] Backup schedule active
- [ ] Incident response plan documented
- [ ] Rollback procedure tested
- [ ] Performance baseline recorded

---

## Related Documentation

| Document | Location |
|----------|----------|
| Docker Setup | [`docs/operations/DOCKER_SETUP.md`](../operations/DOCKER_SETUP.md) |
| Nepal Deployment | [`docs/operations/NEPAL_DEPLOYMENT_GUIDE.md`](../operations/NEPAL_DEPLOYMENT_GUIDE.md) |
| Disaster Recovery | [`docs/operations/DISASTER_RECOVERY.md`](../operations/DISASTER_RECOVERY.md) |
| Security Model | [`docs/operations/SECURITY_MODEL_SUMMARY.md`](../operations/SECURITY_MODEL_SUMMARY.md) |
| Mesh Configuration | [`docs/operations/MESH_CONFIG.md`](../operations/MESH_CONFIG.md) |
| Architecture | [`docs/architecture/STRUCTURE.md`](../architecture/STRUCTURE.md) |
