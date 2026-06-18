# AsimNexus World OS - Digital Nepal Prototype

## Vision
AsimNexus = World Operating System. One OS, All Countries, All Cultures, All Languages.

## Quick Start

```bash
cd DigitalNepal-backend
pip install -r requirements.txt
python app.py
# Server: http://localhost:8000
```

## Endpoints

| Endpoint | Purpose | Countries |
|----------|---------|-----------|
| GET / | API status | Global |
| POST /api/v1/user/create | Citizen digital twin | NP, IN, US, UK |
| POST /api/v1/user/chat | Protected chat | Global |
| POST /api/v1/gov/propose | Government 51% check | Country-specific |
| POST /api/v1/company/action | Company 49% check | Country-specific |
| POST /api/v1/gov/vote | Founder Clones voting | Global |
| POST /api/v1/mesh/sync | Offline sync queue | Global |
| GET /api/v1/mesh/status | Sync status | Global |
| GET /api/v1/status | Full system stats | Global |

## Test

```bash
python run_tests.py
```

## Architecture

### Core Layers
- **Governance Base**: Dharma Veto (5 layers) + Power Balance (51/49) + Founder Clones (8/15 voting)
- **User Base**: Digital Twin lifecycle (birth→education→work→family→retirement→inheritance)
- **Mesh Base**: Offline-first sync with CRDT, SMS fallback
- **Country Layer**: Nepal, India, USA, UK templates (expandable)

## World Expansion

```
DigitalNepal-backend/
├── connectors/
│   ├── world_manager.py        # World OS manager
│   ├── country_template.py     # Universal country template
│   ├── ministry_template.py    # Universal ministry template
│   ├── nepal/                  # 🇳🇵 18 ministries + 7 provinces + 77 districts
│   ├── india/                  # 🇮🇳 9 ministries + 14 states + 774 districts  
│   └── usa/                    # 🇺🇸 10 departments + 7 states + 3,000 counties
├── docker-compose.yml          # Docker deployment
├── Dockerfile.backend          # Backend container
└── k8s-deployment.yaml         # Kubernetes manifest
```

## Deploy to Production

```bash
# Docker
docker-compose up -d

# Kubernetes
kubectl apply -f k8s-deployment.yaml
```