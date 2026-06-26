# AsimNexus - Docker Deployment Ready

## Docker Structure Merged
```
docker/
├── docker-compose.yml       # Full stack (4 services: backend, frontend, postgres, clickhouse, minio)
├── Dockerfile.backend       # Python 3.11 slim
├── Dockerfile.frontend      # Node 20 builder + nginx
├── clickhouse/
│   └── init/
├── minio/
│   └── init/
└── postgres/
    └── init/
```

## Run Stack
```bash
# Development (local)
uvicorn app:app --port 8000
cd frontend; npm start

# Production (Docker)
docker-compose -f docker/docker-compose.yml up -d
```

## GIDC Deployment
- `NEPAL_ONLY=true` environment variable set
- All services configured for Nepal hosting
- Use `docker-compose.yml` for GIDC