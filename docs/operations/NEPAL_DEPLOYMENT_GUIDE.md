# Nepal Deployment Guide

> **AsimNexus — Nepal Production Deployment**
> Version: 1.0.0-rc.1 | Last Updated: 2025-07-03

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Infrastructure Setup](#3-infrastructure-setup)
4. [Configuration](#4-configuration)
5. [Deployment Steps](#5-deployment-steps)
6. [Nepal-Specific Integrations](#6-nepal-specific-integrations)
7. [Monitoring & Maintenance](#7-monitoring--maintenance)
8. [Security Considerations](#8-security-considerations)
9. [Disaster Recovery](#9-disaster-recovery)
10. [Checklist](#10-checklist)

---

## 1. Overview

This guide covers deploying AsimNexus for production use in Nepal. The system integrates with:

- **Nepal Government Services** — e-Residency, tax filing, ministry portals
- **Nepali Language Support** — Whisper ASR fine-tuned for Nepali
- **Local Infrastructure** — Docker-based deployment on Nepal-hosted servers
- **Digital Identity** — Blockchain-based DID with Nepal citizenship integration
- **Digital Economy** — RBE, DePIN, and financial services for Nepal

### Architecture Diagram

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

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 50 GB SSD | 100+ GB SSD |
| Network | 100 Mbps | 1 Gbps |
| GPU (optional) | NVIDIA T4 | NVIDIA A10+ |

### Software Requirements

- **OS**: Ubuntu 22.04 LTS or Debian 12
- **Docker**: 24.0+ with Docker Compose v2
- **Python**: 3.11+
- **Node.js**: 20 LTS (for frontend builds)
- **PostgreSQL**: 15 (managed or Docker)
- **Redis**: 7 (managed or Docker)

### Domain & SSL

- Domain name (e.g., `asimnexus.com.np` or `api.asimnexus.com`)
- SSL certificate (Let's Encrypt or commercial)
- Nepal `.np` domain registration via [register.com.np](https://register.com.np)

---

## 3. Infrastructure Setup

### 3.1 Docker Compose (Single Server)

```bash
# Clone the repository
git clone https://github.com/your-org/asimnexus.git /opt/asimnexus
cd /opt/asimnexus

# Create required directories
mkdir -p data/postgres data/redis data/prometheus data/grafana
mkdir -p infrastructure/docker/secrets

# Set up environment
cp .env.example .env
# Edit .env with production values (see Section 4)

# Start services
docker compose -f infrastructure/docker/docker-compose.prod.yml up -d

# Verify health
curl http://localhost:8000/health/live
```

### 3.2 Multi-Server (Kubernetes)

For production deployments serving multiple regions in Nepal, use Kubernetes:

```bash
# Using k3s (lightweight Kubernetes)
curl -sfL https://get.k3s.io | sh -

# Apply manifests
kubectl apply -f infrastructure/k8s/
```

### 3.3 Network Configuration

```bash
# Configure firewall
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw allow 8000/tcp    # Backend API (internal only)
ufw allow 9090/tcp    # Prometheus (internal only)
ufw allow 3000/tcp    # Grafana (internal only)
ufw enable
```

---

## 4. Configuration

### 4.1 Environment Variables

Create `.env` file with production values:

```bash
# ── Core ──────────────────────────────────────────────────────
ASIM_ENV=production
ASIM_SECRET_KEY=<generate-with: openssl rand -hex 32>
ASIM_DEBUG=false
ASIM_LOG_LEVEL=INFO
ASIM_LOG_FORMAT=json

# ── Database ──────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://asimnexus:<password>@postgres:5432/asimnexus
POSTGRES_USER=asimnexus
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=asimnexus

# ── Redis ─────────────────────────────────────────────────────
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<redis-password>

# ── Security ──────────────────────────────────────────────────
JWT_SECRET=<generate-with: openssl rand -hex 64>
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
CORS_ORIGINS=https://asimnexus.com.np,https://admin.asimnexus.com.np

# ── Nepal Integration ─────────────────────────────────────────
NEPAL_GOVERNMENT_API_KEY=<api-key-from-nepal-gov>
NEPAL_TAX_API_ENDPOINT=https://api.ird.gov.np
NEPAL_ERESIDENCY_ENDPOINT=https://eresidency.gov.np/api
NEPAL_BANKING_API_KEY=<api-key>
NEPAL_TELECOM_API_KEY=<api-key>

# ── LLM Providers ─────────────────────────────────────────────
OPENAI_API_KEY=<optional>
ANTHROPIC_API_KEY=<optional>
GOOGLE_API_KEY=<optional>
OLLAMA_BASE_URL=http://ollama:11434

# ── Monitoring ────────────────────────────────────────────────
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
GRAFANA_ADMIN_PASSWORD=<grafana-password>

# ── Data Paths ────────────────────────────────────────────────
ASIM_DATA_DIR=/opt/asimnexus/data
ASIM_DB_DIR=/opt/asimnexus/data/database
ASIM_LOGS_DIR=/opt/asimnexus/data/logs
ASIM_BACKUP_DIR=/opt/asimnexus/data/backups
ASIM_MIRROR_DB_PATH=/opt/asimnexus/data/mirror
ASIM_LIFE_DB_PATH=/opt/asimnexus/data/life_journey
ASIM_CONTRACT_DB_PATH=/opt/asimnexus/data/contracts
ASIM_MEMORY_PATH=/opt/asimnexus/data/memory
ASIM_KNOWLEDGE_PATH=/opt/asimnexus/data/knowledge
ASIM_MESH_DB_PATH=/opt/asimnexus/data/mesh
ASIM_CONSENSUS_DB_PATH=/opt/asimnexus/data/consensus
ASIM_AGENT_DB_PATH=/opt/asimnexus/data/agents
ASIM_SELF_AWARENESS_PATH=/opt/asimnexus/data/self_awareness
ASIM_ANALYTICS_PATH=/opt/asimnexus/data/analytics
ASIM_DEPIN_PATH=/opt/asimnexus/data/depin
ASIM_NEPAL_PATH=/opt/asimnexus/data/nepal
ASIM_ORCHESTRATOR_PATH=/opt/asimnexus/data/orchestrator
ASIM_POLICY_PATH=/opt/asimnexus/data/policy
```

### 4.2 Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/asimnexus
server {
    listen 80;
    server_name asimnexus.com.np api.asimnexus.com.np;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.asimnexus.com.np;

    ssl_certificate /etc/letsencrypt/live/api.asimnexus.com.np/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.asimnexus.com.np/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health/live {
        proxy_pass http://127.0.0.1:8000/health/live;
        access_log off;
    }
}

server {
    listen 443 ssl http2;
    server_name asimnexus.com.np;

    ssl_certificate /etc/letsencrypt/live/asimnexus.com.np/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/asimnexus.com.np/privkey.pem;

    root /opt/asimnexus/frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

---

## 5. Deployment Steps

### 5.1 Initial Server Setup

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker

# Install Docker Compose
apt install -y docker-compose-plugin

# Create asimnexus user
useradd -m -s /bin/bash asimnexus
usermod -aG docker asimnexus
```

### 5.2 Deploy Backend

```bash
# As asimnexus user
cd /opt/asimnexus

# Build and start
docker compose -f infrastructure/docker/docker-compose.prod.yml build
docker compose -f infrastructure/docker/docker-compose.prod.yml up -d

# Run database migrations
docker compose -f infrastructure/docker/docker-compose.prod.yml exec backend \
    alembic upgrade head

# Verify
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

### 5.3 Deploy Frontend

```bash
cd /opt/asimnexus/frontend

# Install dependencies
npm ci --production

# Build
npm run build

# The nginx container in docker-compose serves the built frontend
```

### 5.4 SSL Certificate (Let's Encrypt)

```bash
apt install -y certbot python3-certbot-nginx

certbot --nginx -d asimnexus.com.np -d api.asimnexus.com.np

# Auto-renewal
systemctl enable certbot.timer
```

---

## 6. Nepal-Specific Integrations

### 6.1 Government Integration

The system integrates with Nepal government services via [`routes/nepal.py`](../../routes/nepal.py) and [`routes/government.py`](../../routes/government.py):

| Endpoint | Description | Status |
|----------|-------------|--------|
| `GET /api/nepal/status` | Nepal connector system status | ✅ Active |
| `GET /api/nepal/ministries` | List Nepal government ministries | ✅ Active |
| `GET /api/nepal/provinces` | List Nepal provinces | ✅ Active |
| `GET /api/government/status` | Government services status | ✅ Active |
| `POST /api/government/eresidency/apply` | Apply for e-Residency | ✅ Active |

### 6.2 Nepali Language Support

Nepali language ASR via [`models/nepal/whisper_finetune.py`](../../models/nepal/whisper_finetune.py):

```python
from models.nepal.whisper_finetune import NepaliASR

asr = NepaliASR()
await asr.initialize()
result = await asr.transcribe("path/to/nepali_audio.wav")
```

Features:
- Whisper model fine-tuned for Nepali
- Government document transcription
- Company meeting transcription
- Nepali numeral normalization

### 6.3 Nepal Banking Integration

Via [`core/nepal/banking_integrations.py`](../../core/nepal/banking_integrations.py):

- Nepal Rastra Bank compliance
- Local bank API integration
- Digital payment processing

### 6.4 Nepal Telecom Integration

Via [`core/nepal/telecom_integrations.py`](../../core/nepal/telecom_integrations.py):

- SMS gateway for OTP
- USSD integration for rural areas
- Mobile money support

### 6.5 Tax Integration

Via [`core/nepal/tax_llm.py`](../../core/nepal/tax_llm.py):

- Inland Revenue Department (IRD) integration
- Automated tax filing
- Tax calculation engine

---

## 7. Monitoring & Maintenance

### 7.1 Health Checks

```bash
# Liveness probe
curl http://localhost:8000/health/live

# Readiness probe
curl http://localhost:8000/health/ready

# Full status
curl http://localhost:8000/health/status
```

### 7.2 Prometheus Metrics

```bash
# Access metrics
curl http://localhost:8000/metrics

# Prometheus dashboard
open http://localhost:9090

# Grafana dashboard
open http://localhost:3000
# Default: admin / admin (change immediately)
```

### 7.3 Log Management

```bash
# View backend logs
docker compose -f infrastructure/docker/docker-compose.prod.yml logs -f backend

# View all logs
docker compose -f infrastructure/docker/docker-compose.prod.yml logs -f

# JSON log format (set in .env)
ASIM_LOG_FORMAT=json
```

### 7.4 Backup Strategy

```bash
# Database backup
docker compose exec postgres pg_dump -U asimnexus asimnexus > /backups/db_$(date +%Y%m%d).sql

# Automated backup script
./scripts/db_backup.py

# Backup retention: 30 days daily, 12 months monthly
```

### 7.5 Regular Maintenance

| Frequency | Task |
|-----------|------|
| Daily | Check health endpoints, review error logs |
| Weekly | Database vacuum, log rotation, backup verification |
| Monthly | SSL renewal check, dependency updates, security audit |
| Quarterly | Full DR test, performance review, capacity planning |

---

## 8. Security Considerations

### 8.1 Production Security Checklist

- [ ] JWT secret rotated (use `openssl rand -hex 64`)
- [ ] PostgreSQL password changed from default
- [ ] Redis password set
- [ ] CORS origins restricted to known domains
- [ ] SSL/TLS enforced (HTTPS only)
- [ ] Rate limiting enabled (via `core/rate_limiter_middleware.py`)
- [ ] Security headers configured (via `core/monitoring_middleware.py`)
- [ ] Biometric hardware gate configured (via `core/security/biometric_hardware_gate.py`)
- [ ] Audit logging enabled (via `core/security/audit_log.py`)
- [ ] Firewall configured (only necessary ports open)
- [ ] Fail2ban installed for SSH protection
- [ ] Regular security scans scheduled

### 8.2 Nepal-Specific Security

- Data residency: All citizen data stored within Nepal
- Compliance: Nepal IT Bill 2075, Data Protection Act
- Government API keys stored in encrypted vault
- e-Residency data encrypted at rest and in transit

### 8.3 Security Model

Refer to [`SECURITY_MODEL_SUMMARY.md`](./SECURITY_MODEL_SUMMARY.md) for the complete security architecture, including:

- 3-Level Human Confirmation Protocol
- ZKP for Privacy
- YubiHSM Integration
- 15 Clone Consensus
- Dharma Veto Engine
- Power Balance Constitution (51/49)

---

## 9. Disaster Recovery

### 9.1 Backup Restoration

```bash
# Restore database
docker compose exec -T postgres psql -U asimnexus asimnexus < /backups/db_20250101.sql

# Restore data directories
tar -xzf /backups/data_20250101.tar.gz -C /opt/asimnexus/
```

### 9.2 Recovery Time Objectives

| Scenario | RTO | RPO |
|----------|-----|-----|
| Single service failure | 5 minutes | 0 (real-time) |
| Server failure | 30 minutes | 1 hour |
| Data corruption | 2 hours | 24 hours |
| Full site disaster | 4 hours | 1 hour |

### 9.3 Rollback Procedure

```bash
# Rollback to previous Docker image
docker compose -f infrastructure/docker/docker-compose.prod.yml down
docker compose -f infrastructure/docker/docker-compose.prod.yml pull backend:previous
docker compose -f infrastructure/docker/docker-compose.prod.yml up -d

# Database rollback (if needed)
docker compose exec backend alembic downgrade -1
```

---

## 10. Checklist

### Pre-Deployment

- [ ] All 25+ integration tests passing
- [ ] All 80 security tests passing
- [ ] All 28 E2E tests passing
- [ ] Docker images build successfully
- [ ] `.env` configured with production values
- [ ] SSL certificates obtained
- [ ] Domain DNS configured
- [ ] Firewall rules applied
- [ ] Backup strategy in place
- [ ] Monitoring configured (Prometheus + Grafana)

### Deployment

- [ ] Server provisioned and hardened
- [ ] Docker installed and configured
- [ ] PostgreSQL initialized with migrations
- [ ] Redis configured with password
- [ ] Backend containers running
- [ ] Frontend built and served
- [ ] Health checks passing
- [ ] SSL working (HTTPS)
- [ ] WebSocket connections working
- [ ] API endpoints responding

### Post-Deployment

- [ ] Smoke tests passing against production
- [ ] Monitoring dashboards showing data
- [ ] Alerts configured and tested
- [ ] Log aggregation working
- [ ] Backup cron jobs running
- [ ] Security scan completed
- [ ] Load test completed
- [ ] Documentation updated
- [ ] Team notified

### Nepal-Specific

- [ ] Nepal government API keys configured
- [ ] Nepali ASR model deployed
- [ ] Tax integration tested
- [ ] Banking integration tested
- [ ] Telecom/SMS integration tested
- [ ] e-Residency flow verified
- [ ] Nepali language UI verified
- [ ] Data residency compliance confirmed

---

## Appendix A: Useful Commands

```bash
# View running services
docker compose -f infrastructure/docker/docker-compose.prod.yml ps

# View logs
docker compose -f infrastructure/docker/docker-compose.prod.yml logs -f --tail=100

# Restart a service
docker compose -f infrastructure/docker/docker-compose.prod.yml restart backend

# Scale a service
docker compose -f infrastructure/docker/docker-compose.prod.yml up -d --scale backend=3

# Execute command in container
docker compose -f infrastructure/docker/docker-compose.prod.yml exec backend python -c "print('hello')"

# Database shell
docker compose -f infrastructure/docker/docker-compose.prod.yml exec postgres psql -U asimnexus asimnexus

# Redis CLI
docker compose -f infrastructure/docker/docker-compose.prod.yml exec redis redis-cli
```

## Appendix B: Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend won't start | Check `docker compose logs backend` for import errors |
| Database connection failed | Verify `DATABASE_URL` in `.env` and PostgreSQL is running |
| Redis connection failed | Verify `REDIS_HOST` and `REDIS_PASSWORD` |
| 502 Bad Gateway | Check if backend is running on port 8000 |
| WebSocket disconnects | Check nginx WebSocket proxy settings |
| SSL certificate expired | Run `certbot renew` |
| Disk space low | Run `docker system prune -af` and rotate logs |
| High memory usage | Check `docker stats` and adjust container limits |

---

## Appendix C: Nepal Data Centers

| Provider | Location | Type |
|----------|----------|------|
| Nepal Telecom | Various | Tier II |
| Subisu | Kathmandu | Tier II |
| CloudLink | Kathmandu | Tier III |
| WorldLink | Various | Tier II |
| Vianet | Kathmandu | Tier II |

---

*For questions or support, contact the AsimNexus DevOps team.*
