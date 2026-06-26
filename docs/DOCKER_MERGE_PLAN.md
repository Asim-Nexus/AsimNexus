# AsimNexus Docker - Unified Deployment

## Structure
```
docker/
├── docker-compose.yml      # Main compose file
├── clickhouse/
│   └── init/
├── minio/
│   └── init/
├── postgres/
│   └── init/
├── Dockerfile.backend      # Backend Dockerfile
├── Dockerfile.frontend     # Frontend Dockerfile
└── GIDC_DEPLOYMENT.md    # GIDC deployment guide
```

## Docker Merge Plan
1. Move `DigitalNepal-backend/docker-compose.yml` to `docker/docker-compose.yml`
2. Create Dockerfiles in `docker/`
3. Update paths for unified structure
4. Add GIDC deployment configuration