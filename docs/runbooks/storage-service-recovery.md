# Storage Service Incident Runbook

> **Purpose:** Operational guide for diagnosing and recovering any of the 5 AsimNexus storage services.
> **Applies to:** Redis, ClickHouse, PostgreSQL, MinIO, ChromaDB
> **Last updated:** 2026-06-01

---

## Quick Triage — Decision Tree

Use this table to identify the likely culprit and jump to the correct recovery section.

| Symptom / Alert | Likely Service(s) | First Action | Section |
|---|---|---|---|
| `GET /health/ready` returns `503` | One or more storage services | Check `ready.checks.*` in response body | [Health endpoint](#health-endpoint-reference) |
| Grafana panel `asimmers_storage_up{service=X}` shows `0` | Specific service | Jump to that service's section | [Per-service sections](#service-recovery-procedures) |
| App reports "connection refused" or "timeout" | Network issue or process crash | Verify Docker/OS process is running | [Common diagnostics](#common-diagnostics) |
| App reports "disk full" or "no space left" | **Any** — likely MinIO or PostgreSQL | Check disk usage on host + data volume | [Disk full procedure](#disk-full-procedure) |
| Redis PING fails | Redis | Check `redis-cli ping` from host | [Redis recovery](#1-redis-cache-layer) |
| ClickHouse HTTP `/ping` returns non-200 | ClickHouse | Check ClickHouse server logs | [ClickHouse recovery](#2-clickhouse-analytics-layer) |
| PostgreSQL `pg_isready` fails | PostgreSQL | Check `docker logs asimnexus-postgres` | [PostgreSQL recovery](#3-postgresql-oltp-layer) |
| MinIO `/minio/health/live` returns non-200 | MinIO | Check minio process + disk | [MinIO recovery](#4-minio-object-storage) |
| ChromaDB `/api/v1/heartbeat` returns non-200 | ChromaDB | Check chromadb server logs | [ChromaDB recovery](#5-chromadb-vector-db) |
| Vector queries slow / failing | ChromaDB or Redis cache | Check latency metrics + cache hit rate | [Latency troubleshooting](#latency-troubleshooting) |

---

## Health Endpoint Reference

All storage health probes are implemented in [`backend/health.py`](/backend/health.py) and exposed via three HTTP endpoints:

| Endpoint | Purpose | Returns |
|---|---|---|
| `GET /health/live` | Process is alive | Always `200` if the backend process is running |
| `GET /health/ready` | All dependencies ready | `200` if all storage services respond; `503` otherwise |
| `GET /health/status` | Full diagnostic dump | Detailed status of each service + system metrics |

**Example readiness check:**

```bash
curl -s http://localhost:8000/health/ready | jq .
{
  "status": "not_ready",
  "checks": {
    "redis": { "ready": false, "message": "Redis error: Connection refused" },
    "clickhouse": { "ready": true, "message": "ClickHouse reachable at ..." },
    ...
  },
  "all_ready": false
}
```

### Storage Probe Details per Service

| Service | Probe URI | Client/Dependency | Env Config Keys |
|---|---|---|---|
| Redis | `redis.Redis().ping()` | `redis-py` | `REDIS_HOST`, `REDIS_PORT` |
| ClickHouse | `GET /ping` (HTTP) | `requests` | `CLICKHOUSE_HOST`, `CLICKHOUSE_HTTP_PORT`, `CLICKHOUSE_NATIVE_PORT` |
| PostgreSQL | `psycopg2.connect()` | `psycopg2` | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` |
| MinIO | `GET /minio/health/live` | `requests` / `minio-py` | `MINIO_HOST`, `MINIO_API_PORT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` |
| ChromaDB | `GET /api/v1/heartbeat` | `requests` | `CHROMADB_HOST`, `CHROMADB_PORT` |

Environment defaults are set in [`backend/health.py`](/backend/health.py:22) — all services default to `localhost` when no env var is provided.

---

## Monitoring & Alerting

### Prometheus Metrics

Defined in [`monitoring/metrics.py`](/monitoring/metrics.py:180) — the `MetricsCollector` polls every 15 seconds:

| Metric Name | Type | Labels | Description |
|---|---|---|---|
| `asimmers_storage_up` | Gauge | `service` | 1 = reachable, 0 = down |
| `asimmers_storage_query_latency_ms` | Histogram | `service`, `operation` | Query round-trip latency |
| `asimmers_storage_connections_active` | Gauge | `service` | Active connections |
| `asimmers_storage_errors_total` | Counter | `service`, `error_type` | Accumulated error count |
| `asimmers_storage_disk_usage_bytes` | Gauge | `service` | Data directory size |

### Grafana Dashboard

A dedicated dashboard ["Storage Pod Stability"](/monitoring/grafana/dashboards/storage-pod-stability.json) provides:
- Uptime/reachability stat panel for all 5 services
- Query latency time-series (p50/p95)
- Connection count + disk usage gauges per service
- Alert thresholds: latency > 200ms (warning), > 1000ms (critical); disk > 10GB (warning), > 50GB (critical)

### Alert Thresholds

Set in [`monitoring/metrics.py`](/monitoring/metrics.py:246):

| Threshold | Warning | Critical |
|---|---|---|
| Storage service up | 0 (down) | 0 (down) |
| Query latency | > 200 ms | > 1000 ms |
| Active connections | > 80 | > 150 |
| Disk usage | > 10 GB | > 50 GB |
| CPU | > 70% | > 90% |
| Memory | > 80% | > 95% |

---

## Common Diagnostics

These steps apply to **any** storage service incident.

### 1. Check the Health Endpoint

```bash
# Readiness check
curl -s http://localhost:8000/health/ready | jq .checks

# Full status dump
curl -s http://localhost:8000/health/status | jq .storage
```

### 2. Check Docker Container Status

```bash
docker ps --filter "name=asimnexus" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 3. Check Container Logs

```bash
# Replace SERVICE with: redis | postgres | clickhouse | minio | chromadb
docker logs asimnexus-SERVICE --tail 100
```

### 4. Check Host Resources

```bash
# Disk usage
df -h

# Memory
free -h

# Docker volume disk usage
docker system df -v
```

### 5. Verify Network Connectivity

```bash
# From the backend container
docker exec asimnexus-backend ping -c 3 SERVICE_HOSTNAME
```

Where `SERVICE_HOSTNAME` is the Docker service name (e.g., `redis`, `postgres`, `clickhouse`, `minio`, `chromadb`).

---

## Disk Full Procedure

Applies to **any** service when disk space is the root cause.

**Symptoms:**
- "No space left on device" errors in logs
- Docker containers restarting with exit code 137 (OOM-killed) or disk-write failures
- `asimmers_storage_disk_usage_bytes` above 50 GB

**Diagnosis:**

```bash
# 1. Check host disk
df -h

# 2. Check Docker volume sizes
docker system df -v | grep -E "(VOLUME|postgres|redis|clickhouse|minio|chromadb)"

# 3. Check specific data directories
# Linux host:
du -sh /var/lib/docker/volumes/*/data
```

**Recovery:**

1. Identify the largest consumer using the commands above.
2. If **PostgreSQL**: Consider removing old data or archiving — see [PostgreSQL recovery](#3-postgresql-oltp-layer).
3. If **ClickHouse**: Check TTL settings in [`docker/clickhouse/init/01_create_tables.sql`](/docker/clickhouse/init/01_create_tables.sql) — tables have 3–12 month TTLs by default. Run `ALTER TABLE ... DROP PARTITION` for old partitions.
4. If **MinIO**: Use the MinIO console (`http://host:9001`) to browse and delete unused objects. Review buckets: models, data, backups, logs, memory, config, federation, artifacts.
5. If **Redis**: Run `redis-cli MEMORY STATS` and consider `redis-cli MEMORY PURGE`. Check `maxmemory` policy in [`config/redis.conf`](/config/redis.conf).
6. If **ChromaDB**: Purge old collections via the ChromaDB API (`DELETE /api/v1/collections/{name}`). The data directory defaults to `data/chromadb`.
7. After cleanup, verify the service recovers:

```bash
curl -s http://localhost:8000/health/ready | jq .status
```

**Escalation:** If disk usage is consistently above 80%, request a volume expansion from infrastructure team.

---

## Service Recovery Procedures

---

### 1. Redis (Cache Layer)

**Role:** Session cache, real-time data, state manager backend.
**Port:** `6379`
**Docker image:** `redis:7-alpine` ([`docker-compose.full.yml`](/docker-compose.full.yml:122))
**Config:** [`config/redis.conf`](/config/redis.conf)

#### Symptoms

| Alert | Meaning |
|---|---|
| `storage_redis_up = 0` | Redis unreachable |
| Redis PING timeout in health check | High latency or connection exhaustion |
| High `redis_fallbacks` metric | State manager falling back to in-memory store |
| Session/auth failures | Users cannot log in or maintain sessions |

#### Health Check

```bash
# Programmatic
curl -s http://localhost:8000/health/ready | jq .checks.redis

# Direct
docker exec asimnexus-redis redis-cli ping
# Expected: PONG
```

#### Common Causes

| Cause | Frequency | Indicator |
|---|---|---|
| Process crash / OOM | Medium | Container exited, OOM in dmesg |
| Disk full (AOF/RDB persistence) | Low | Redis logs: "Can't save in background" |
| Connection exhaustion | Medium | `redis-cli CLIENT LIST` shows max clients |
| Config error | Low | Invalid `redis.conf`, port conflict |
| Network issue | Low | `redis-cli ping` times out from other containers |
| Authentication failure | Low | Redis configured with `requirepass` but health probe has wrong/no password |

#### Diagnosis Steps

```bash
# 1. Is the process running?
docker ps --filter "name=asimnexus-redis"

# 2. Check logs
docker logs asimnexus-redis --tail 50

# 3. Test connectivity
docker exec asimnexus-redis redis-cli ping

# 4. Check Redis INFO
docker exec asimnexus-redis redis-cli INFO server
docker exec asimnexus-redis redis-cli INFO memory
docker exec asimnexus-redis redis-cli INFO clients

# 5. Check for slow queries
docker exec asimnexus-redis redis-cli SLOWLOG GET 5

# 6. Check keyspace
docker exec asimnexus-redis redis-cli INFO keyspace
```

#### Recovery Steps

**A. Container restart (quick recovery):**

```bash
docker restart asimnexus-redis
# Wait 5 seconds, then verify
docker exec asimnexus-redis redis-cli ping
```

**B. Full Redis reset (clears all cache data):**

```bash
# WARNING: This flushes all Redis data. Only if cache rebuild is acceptable.
docker exec asimnexus-redis redis-cli FLUSHALL
docker exec asimnexus-redis redis-cli BGREWRITEAOF
```

**C. Persistent failure — config review:**

1. Check [`config/redis.conf`](/config/redis.conf) for `maxmemory`, `maxmemory-policy`, `bind`, and `requirepass`.
2. Ensure `REDIS_HOST`/`REDIS_PORT` environment variables match the config.
3. Verify port mapping: `docker port asimnexus-redis 6379`.

**D. AOF / RDB corruption recovery:**

```bash
# 1. Stop the container
docker stop asimnexus-redis

# 2. Remove corrupted persistence files
rm -f /path/to/redis-data/appendonly.aof /path/to/redis-data/dump.rdb

# 3. Restart (DB will be empty — repopulates from upstream)
docker start asimnexus-redis
```

#### Escalation

| Condition | Escalate To |
|---|---|
| Restart doesn't resolve after 3 attempts | Backend/infra team |
| Redis AOF/RDB file corruption | Infra team for volume recovery |
| `maxmemory` consistently exceeded | Architecture team to review cache sizing |
| Cluster mode issues (not currently used) | Infra team |

---

### 2. ClickHouse (Analytics Layer)

**Role:** Time-series analytics, event logging, telemetry, mesh metrics.
**HTTP port:** `8123` | **Native port:** `9000`
**Tables defined in:** [`docker/clickhouse/init/01_create_tables.sql`](/docker/clickhouse/init/01_create_tables.sql)
**Config:** [`storage/config.py`](/storage/config.py:81)

#### Symptoms

| Alert | Meaning |
|---|---|
| `storage_clickhouse_up = 0` | ClickHouse unreachable |
| Analytics queries fail | Dashboards and reports show no data |
| Mesh/telemetry events can't be written | Event pipeline backlog |
| HTTP `/ping` returns non-200 | Server may be starting up or crashed |

#### Health Check

```bash
# Programmatic
curl -s http://localhost:8000/health/ready | jq .checks.clickhouse

# Direct
curl -s http://localhost:8123/ping
# Expected: Ok.

# Query test
curl -s "http://localhost:8123/?query=SELECT count() FROM system.tables"
```

#### Common Causes

| Cause | Frequency | Indicator |
|---|---|---|
| Process crash / OOM | Medium | Container exited |
| Disk full | Medium | MergeTree writes fail |
| Corrupted table data | Low | Query errors: "Cannot read from file" |
| Configuration error | Low | Invalid `config.xml` |
| Port conflict | Low | `8123` or `9000` already in use |
| MergeTree merge storm | Low | High CPU, slow queries, many parts |

#### Diagnosis Steps

```bash
# 1. Process status
docker ps --filter "name=asimnexus-clickhouse"

# 2. Container logs
docker logs asimnexus-clickhouse --tail 100

# 3. System health query
curl -s "http://localhost:8123/?query=SELECT version(),uptime()"

# 4. Check merge backlog
curl -s "http://localhost:8123/?query=SELECT count() FROM system.merges"

# 5. Check disk space on ClickHouse volumes
curl -s "http://localhost:8123/?query=SELECT name,path,formatReadableSize(free_space) FROM system.disks"

# 6. Check recent errors
curl -s "http://localhost:8123/?query=SELECT * FROM system.errors ORDER BY last_error_time DESC LIMIT 10"
```

#### Recovery Steps

**A. Container restart:**

```bash
docker restart asimnexus-clickhouse
# Wait 15–30 seconds for startup
curl -s http://localhost:8123/ping
```

**B. Re-create tables (schema intact, data may be lost):**

If the initialization SQL is in place as a Docker entrypoint:

```bash
# Restart forces re-run of init scripts if mounted as docker-entrypoint-initdb.d
docker restart asimnexus-clickhouse
```

If tables are missing, re-run from the DDL file:

```bash
cat docker/clickhouse/init/01_create_tables.sql | curl -s "http://localhost:8123/?query=" --data-binary @-
```

**C. Drop and recreate a corrupted partition:**

```sql
-- Identify the problematic table and partition
SELECT database, table, partition, active FROM system.parts WHERE active = 0 AND database = 'asimnexus';

-- Drop a specific partition
ALTER TABLE asimnexus.mesh_events DROP PARTITION '202601';
```

**D. Full ClickHouse reset (last resort):**

```bash
docker stop asimnexus-clickhouse
docker rm asimnexus-clickhouse
docker volume rm clickhouse-data   # WARNING: Destroys all analytics data
docker-compose -f docker-compose.full.yml up -d clickhouse
```

#### Escalation

| Condition | Escalate To |
|---|---|
| Multiple table corruptions | DBA / infra team |
| Merge pipeline stuck for > 1 hour | ClickHouse specialist |
| Data loss from partition corruption | Restore from backup (backups team) |
| OOM on moderate queries | Architecture team to review query patterns |

---

### 3. PostgreSQL (OLTP Layer)

**Role:** Primary transactional database — users, sessions, credits, governance, DIDs, mesh nodes, federation, notifications.
**Port:** `5432`
**Docker image:** `postgres:15-alpine` ([`docker-compose.full.yml`](/docker-compose.full.yml:99))
**Schema:** [`docker/postgres/init/01_create_tables.sql`](/docker/postgres/init/01_create_tables.sql)
**Config:** [`storage/config.py`](/storage/config.py:104)

#### Symptoms

| Alert | Meaning |
|---|---|
| `storage_postgres_up = 0` | PostgreSQL unreachable |
| Login/auth failures | Users cannot log in |
| Credit transactions fail | Economy system broken |
| Governance proposals fail | Consensus/voting system unavailable |
| `pg_isready` returns "no response" | Server not accepting connections |

#### Health Check

```bash
# Programmatic
curl -s http://localhost:8000/health/ready | jq .checks.postgres

# Direct
docker exec asimnexus-postgres pg_isready -U asimnexus
# Expected: /var/run/postgresql:5432 - accepting connections

# Query test
docker exec asimnexus-postgres psql -U asimnexus -d asimnexus -c "SELECT 1"
```

#### Common Causes

| Cause | Frequency | Indicator |
|---|---|---|
| Process crash | Medium | Container exited |
| Disk full | High | PostgreSQL stops writing, "no space left" |
| Connection exhaustion | Medium | `FATAL: remaining connection slots are reserved` |
| Corrupted index | Low | Query errors: "index corruption" |
| Replication lag (if replica) | N/A | Not currently configured with replicas |
| Config error | Low | `postgresql.conf` changes, port conflict |
| Long-running query / lock | Medium | Queries hanging, `pg_stat_activity` shows `waiting` |

#### Diagnosis Steps

```bash
# 1. Process status
docker ps --filter "name=asimnexus-postgres"

# 2. Logs
docker logs asimnexus-postgres --tail 100

# 3. Active connections
docker exec asimnexus-postgres psql -U asimnexus -d asimnexus -c "
  SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
"
# 4. Blocked queries
docker exec asimnexus-postgres psql -U asimnexus -d asimnexus -c "
  SELECT blocked.pid AS blocked_pid,
         blocker.pid AS blocking_pid,
         blocked.query AS blocked_query
  FROM pg_catalog.pg_locks blocked_locks
  JOIN pg_catalog.pg_stat_activity blocked ON blocked.pid = blocked_locks.pid
  JOIN pg_catalog.pg_locks blocker_locks ON ...
  WHERE NOT blocked_locks.granted;
"

# 5. Database size
docker exec asimnexus-postgres psql -U asimnexus -d asimnexus -c "
  SELECT pg_database_size('asimnexus') AS bytes,
         pg_size_pretty(pg_database_size('asimnexus')) AS pretty;
"

# 6. Check disk
df -h | grep postgres
```

#### Recovery Steps

**A. Container restart:**

```bash
docker restart asimnexus-postgres
# Wait 10–20 seconds for WAL recovery + startup
docker exec asimnexus-postgres pg_isready -U asimnexus
```

**B. Terminate blocking queries:**

```bash
# Find blocking PIDs from diagnosis step 4, then:
docker exec asimnexus-postgres psql -U asimnexus -d asimnexus -c "
  SELECT pg_terminate_backend(<BLOCKED_PID>);
"
```

**C. Increase max_connections (config change):**

Edit the PostgreSQL config or pass environment variable:

```yaml
# In docker-compose.full.yml, add:
environment:
  - POSTGRES_CONFIG=max_connections=200
```

Then restart:

```bash
docker restart asimnexus-postgres
```

**D. Disk full — free space:**

```bash
# 1. Find largest tables
docker exec asimnexus-postgres psql -U asimnexus -d asimnexus -c "
  SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
  FROM pg_catalog.pg_statio_user_tables
  ORDER BY pg_total_relation_size(relid) DESC
  LIMIT 10;
"

# 2. Vacuum and analyze (doesn't free disk space to OS, but marks for reuse)
docker exec asimnexus-postgres psql -U asimnexus -d asimnexus -c "VACUUM ANALYZE;"

# 3. If you need actual disk back, truncate old data (after backup!)
docker exec asimnexus-postgres psql -U asimnexus -d asimnexus -c "
  -- Remove old notifications (keep last 30 days)
  DELETE FROM notifications WHERE created_at < NOW() - INTERVAL '30 days';
"
```

**E. Full restore from backup:**

```bash
# Stop and remove the container
docker stop asimnexus-postgres
docker rm asimnexus-postgres

# Restore from backup file
# (Assumes backup at /backups/postgres/asimnexus_YYYYMMDD.sql)
cat /backups/postgres/asimnexus_latest.sql | docker exec -i asimnexus-postgres psql -U asimnexus -d asimnexus

# Or if starting fresh:
docker-compose -f docker-compose.full.yml up -d postgres
# The init SQL will recreate tables if the volume is fresh
```

#### Escalation

| Condition | Escalate To |
|---|---|
| Data corruption detected | DBA team immediately |
| WAL file issues | DBA team |
| Replication required | Infrastructure team |
| Disk full with no cleanup path | Infrastructure team for volume expansion |
| Queries consistently slow (> 1s) | Architecture team for query optimization |

---

### 4. MinIO (Object Storage)

**Role:** Object/blob storage — ML models, data assets, backups, logs, memory snapshots, config files, federation artifacts, build artifacts.
**API port:** `9000` | **Console port:** `9001`
**Buckets:** `models`, `data`, `backups`, `logs`, `memory`, `config`, `federation`, `artifacts`
**Init script:** [`docker/minio/init/create_buckets.sh`](/docker/minio/init/create_buckets.sh)
**Config:** [`storage/config.py`](/storage/config.py:127)

#### Symptoms

| Alert | Meaning |
|---|---|
| `storage_minio_up = 0` | MinIO unreachable |
| File uploads/downloads fail | Object store operations hang |
| Model loading fails | LLM models stored in MinIO unavailable |
| Mesh federation artifacts missing | Cross-instance sync broken |
| Console (port 9001) inaccessible | Web UI for administration down |

#### Health Check

```bash
# Programmatic
curl -s http://localhost:8000/health/ready | jq .checks.minio

# Direct
curl -s http://localhost:9000/minio/health/live
# Expected: 200 OK (no body or "OK")

# List buckets (requires credentials)
docker exec asimnexus-minio mc ls asimnexus/
```

#### Common Causes

| Cause | Frequency | Indicator |
|---|---|---|
| Process crash | Medium | Container exited |
| Disk full | High | MinIO returns 500 errors on write |
| Access key rotation | Low | Credentials mismatch |
| Network issue | Low | Other containers can't reach `minio:9000` |
| Bucket corruption | Low | Listing buckets fails |

#### Diagnosis Steps

```bash
# 1. Process status
docker ps --filter "name=asimnexus-minio"

# 2. Logs
docker logs asimnexus-minio --tail 100

# 3. Health endpoint
curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live

# 4. Bucket listing
docker exec asimnexus-minio mc ls asimnexus/

# 5. Disk usage on MinIO volume
df -h | grep minio

# 6. Check environment variables match MINIO_ACCESS_KEY / MINIO_SECRET_KEY
docker inspect asimnexus-minio --format='{{range .Config.Env}}{{println .}}{{end}}' | grep MINIO
```

#### Recovery Steps

**A. Container restart:**

```bash
docker restart asimnexus-minio
# Wait 10 seconds
curl -s http://localhost:9000/minio/health/live
```

**B. Recreate missing buckets:**

```bash
# If init script is mounted:
docker exec asimnexus-minio /bin/sh /docker-entrypoint-initdb.d/create_buckets.sh

# Or manually:
docker exec asimnexus-minio mc mb asimnexus/models asimnexus/data asimnexus/backups asimnexus/logs asimnexus/memory asimnexus/config asimnexus/federation asimnexus/artifacts
```

**C. Credential mismatch (update env vars):**

Ensure these match what the application expects:

```bash
# In .env or docker-compose:
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_HOST=minio
MINIO_API_PORT=9000
```

**D. Disk full — cleanup old objects:**

```bash
# Using MinIO client:
docker exec asimnexus-minio mc rm --recursive --older-than 30d asimnexus/logs/
docker exec asimnexus-minio mc rm --recursive --older-than 90d asimnexus/backups/

# Or use the console at http://localhost:9001
```

#### Escalation

| Condition | Escalate To |
|---|---|
| Disk full, no cleanup possible | Infrastructure team for volume expansion |
| Data integrity issues | Infra team + backups restoration |
| Access key compromise | Security team for key rotation |
| Multi-node setup issues (not currently used) | Infrastructure team |

---

### 5. ChromaDB (Vector DB)

**Role:** Vector embeddings storage, semantic search, memory retrieval.
**Port:** `8000`
**Data path:** `data/chromadb` (configurable via [`storage/config.py`](/storage/config.py:166))
**API:** `http://chromadb:8000/api/v1`

#### Symptoms

| Alert | Meaning |
|---|---|
| `storage_chromadb_up = 0` | ChromaDB unreachable |
| Vector search fails/returns errors | Semantic memory/retrieval broken |
| Agent memories not retrievable | AI agents lose context |
| Collection listing returns empty | Collections may be corrupted or missing |
| Heartbeat returns non-200 | Server not responding |

#### Health Check

```bash
# Programmatic
curl -s http://localhost:8000/health/ready | jq .checks.chromadb

# Direct heartbeat
curl -s http://localhost:8000/api/v1/heartbeat
# Expected: {"nanosecond heartbeat": <epoch_ns>}

# List collections
curl -s http://localhost:8000/api/v1/collections
# Expected: [...]
```

#### Common Causes

| Cause | Frequency | Indicator |
|---|---|---|
| Process crash / OOM | Medium | Container exited |
| Disk full | Medium | ChromaDB fails to write / compact |
| Corrupted index | Low | Search returns errors |
| Port conflict | Low | Port 8000 already in use |
| Embedding dimension mismatch | Low | Cannot add vectors with wrong dimension |

#### Diagnosis Steps

```bash
# 1. Process status
docker ps --filter "name=asimnexus-chromadb"

# 2. Container logs
docker logs asimnexus-chromadb --tail 100

# 3. Heartbeat
curl -s http://localhost:8000/api/v1/heartbeat

# 4. Collection health
curl -s http://localhost:8000/api/v1/collections | python -m json.tool

# 5. Check data directory size
du -sh data/chromadb

# 6. Count collections and items
curl -s http://localhost:8000/api/v1/collections | python -c "
import json,sys
cols = json.load(sys.stdin)
print(f'Collection count: {len(cols)}')
for c in cols:
    print(f'  - {c[\"name\"]}: {c.get(\"count\", \"?\")} items')
"
```

#### Recovery Steps

**A. Container restart:**

```bash
docker restart asimnexus-chromadb
# Wait 5–10 seconds
curl -s http://localhost:8000/api/v1/heartbeat
```

**B. Re-create collections (empty — data repopulates from application):**

```bash
# Delete and recreate via API
curl -s -X DELETE http://localhost:8000/api/v1/collections/collection_name
curl -s -X POST http://localhost:8000/api/v1/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "collection_name", "metadata": {"hnsw:space": "cosine"}}'
```

**C. Full reset (destroys all vector data):**

```bash
docker stop asimnexus-chromadb
rm -rf data/chromadb/*
docker start asimnexus-chromadb
# Collections will be recreated by the application on first use
```

**D. Embedding dimension mismatch fix:**

Check the configured dimension in [`storage/config.py`](/storage/config.py:149):

```python
# Default:
dimension = 384  # all-MiniLM-L6-v2
```

If the model changed, you must either:
- Re-embed all documents with the new model
- Or delete and recreate collections with the correct dimension

#### Escalation

| Condition | Escalate To |
|---|---|
| Index corruption | Infra team + restore from vector backup |
| Persistent OOM | Architecture team to review collection sizing |
| Embedding model changes | ML/AI team |
| Data loss from reset | Restore from backup (backups team) |

---

## Latency Troubleshooting

When storage services are **up** but **slow** (latency > 200ms):

### 1. Identify the Service

Check the Grafana latency dashboard or:

```bash
curl -s http://localhost:8000/health/status | jq '.storage | to_entries[] | {service: .key, status: .value.status}'
```

### 2. Common Latency Patterns

| Pattern | Likely Cause | Action |
|---|---|---|
| All services slow | Host resource contention | Check host CPU/memory/disk IO |
| Single service slow | Service-specific overload | Check that service's connections |
| Spikes correlate with high request volume | Application load | Scale up or rate-limit |
| Gradual degradation over time | Resource leak / data growth | Review data retention policies |

### 3. General Latency Diagnosis

```bash
# Host resources
top -bn1 | head -20
iostat -x 1 3

# Docker resource usage
docker stats --no-stream

# Network latency between containers
docker exec asimnexus-backend ping -c 3 postgres
```

---

## Rollback Procedure

If a configuration change or deployment caused the storage service failure:

### Docker-based rollback

```bash
# 1. Revert docker-compose change
git checkout HEAD~1 -- docker-compose.full.yml

# 2. Recreate the specific service
docker-compose -f docker-compose.full.yml up -d --force-recreate SERVICE_NAME

# 3. Verify
curl -s http://localhost:8000/health/ready
```

### Config file rollback

```bash
# Revert storage config
git checkout HEAD~1 -- config/storage.yaml
docker restart asimnexus-backend
```

### Data volume rollback

```bash
# If a Docker volume was corrupted, restore from snapshot:
# (Snapshots are expected to be managed by infrastructure team)
docker volume rm postgres-data
docker volume create postgres-data
# Then restore from backup
```

---

## Escalation Contacts

| Role | Responsibility | Contact |
|---|---|---|
| **On-call Engineer** | First responder for any incident | PagerDuty / OpsGenie |
| **DBA Team** | PostgreSQL, ClickHouse data issues | #dba Slack channel |
| **Infrastructure Team** | Volume expansion, network, Docker host | #infra Slack channel |
| **Security Team** | Credential compromise, key rotation | #security Slack channel |
| **Architecture Team** | Capacity planning, config review | #architecture Slack channel |

### When to Escalate

- **Immediately:** Data corruption, security breach, complete storage layer outage
- **After 15 minutes:** Service not recovering after standard restart
- **After 30 minutes:** Need for data restore from backup
- **Any time:** Unclear root cause or need for specialized knowledge

---

## Appendices

### A. Environment Variables Summary

| Service | Key Variables | Defined In |
|---|---|---|
| Redis | `REDIS_HOST`, `REDIS_PORT` | [`backend/health.py:22`](/backend/health.py:22) |
| ClickHouse | `CLICKHOUSE_HOST`, `CLICKHOUSE_HTTP_PORT`, `CLICKHOUSE_NATIVE_PORT` | [`backend/health.py:28`](/backend/health.py:28) |
| PostgreSQL | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | [`backend/health.py:34`](/backend/health.py:34) |
| MinIO | `MINIO_HOST`, `MINIO_API_PORT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | [`backend/health.py:42`](/backend/health.py:42) |
| ChromaDB | `CHROMADB_HOST`, `CHROMADB_PORT` | [`backend/health.py:50`](/backend/health.py:50) |

### B. Relevant Source Files

| File | Purpose |
|---|---|
| [`backend/health.py`](/backend/health.py) | Health probe implementations for all 5 services |
| [`monitoring/metrics.py`](/monitoring/metrics.py) | Prometheus metrics collection loop (15s interval) |
| [`monitoring/observability_dashboard.py`](/monitoring/observability_dashboard.py) | Real-time terminal dashboard with storage status |
| [`monitoring/grafana/dashboards/storage-pod-stability.json`](/monitoring/grafana/dashboards/storage-pod-stability.json) | Grafana dashboard for storage health visualization |
| [`monitoring/test_storage_integration.py`](/monitoring/test_storage_integration.py) | Integration tests for storage probes and metrics |
| [`storage/config.py`](/storage/config.py) | Storage configuration loader with env var substitution |
| [`docker-compose.full.yml`](/docker-compose.full.yml) | Full deployment with Redis + PostgreSQL containers |
| [`docker/postgres/init/01_create_tables.sql`](/docker/postgres/init/01_create_tables.sql) | PostgreSQL DDL (10 tables) |
| [`docker/clickhouse/init/01_create_tables.sql`](/docker/clickhouse/init/01_create_tables.sql) | ClickHouse DDL (6 tables + 2 materialized views) |
| [`docker/minio/init/create_buckets.sh`](/docker/minio/init/create_buckets.sh) | MinIO bucket creation script (8 buckets) |
| [`.env.example`](/.env.example) | All environment variable defaults |

### C. Prometheus Metric Prefix

All storage metrics use the `asimmers_` prefix (`AsimNexus Storage Metrics`):

- `asimmers_storage_up{service="..."}`
- `asimmers_storage_query_latency_ms_bucket{service="...",le="..."}`
- `asimmers_storage_connections_active{service="..."}`
- `asimmers_storage_errors_total{service="...",error_type="..."}`
- `asimmers_storage_disk_usage_bytes{service="..."}`

---

*This runbook is maintained as part of the AsimNexus project. Update it whenever storage service configurations, health probes, or recovery procedures change.*
