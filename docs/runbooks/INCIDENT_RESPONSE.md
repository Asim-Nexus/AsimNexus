# Incident Response Runbook

> **AsimNexus v1.0.1** | Last updated: 2026-06-01
> Severity definitions: **P0** = Critical (system down), **P1** = High (major feature broken), **P2** = Medium (partial degradation), **P3** = Low (minor issue)

---

## Incident Types

| # | Incident | Severity | Typical SLA |
|---|----------|----------|-------------|
| 1 | [Mesh Network Down](#1-mesh-network-down) | P0 | 15 min |
| 2 | [Storage Service Down](#2-storage-service-down) | P0/P1 | 15 min |
| 3 | [Override Quorum Stuck](#3-override-quorum-stuck) | P1 | 30 min |
| 4 | [Security Gate Lockout](#4-security-gate-lockout) | P1/P2 | 30 min |
| 5 | [Release Rollback Failure](#5-release-rollback-failure) | P1 | 20 min |

---

## 1. Mesh Network Down

**Severity**: P0 — All P2P communication degraded

### Symptoms
- Mesh health check failures: [`GET /api/mesh/status`](../../backend/mesh.py:474) returns `{"status": "error"}`
- Peer connection count drops to 0: [`GET /api/mesh/p2p/connections`](../../backend/mesh.py:318)
- DHT operations timeout: [`GET /api/mesh/dht/stats`](../../backend/mesh.py:286)
- Bootstrap returns no nodes: [`GET /api/mesh/bootstrap/nodes`](../../backend/mesh.py:413)
- Log entries showing `ConnectionRefusedError` or `TimeoutError`

### Diagnosis Steps

```
1. Check mesh status          → GET /api/mesh/status
2. Check P2P connections      → GET /api/mesh/p2p/connections
3. Check DHT health           → GET /api/mesh/dht/stats
4. Check bootstrap nodes      → GET /api/mesh/bootstrap/nodes
5. Check bootstrap stats      → GET /api/mesh/bootstrap/stats
6. Check all relay sessions   → GET /api/mesh/relay/sessions
```

### Immediate Actions

| Step | Action | Command / Reference |
|------|--------|-------------------|
| 1 | Restart the bootstrap service | [`POST /api/mesh/bootstrap`](../../backend/mesh.py:440) |
| 2 | Verify UDP port (default `7336`) is open | `netstat -an \| findstr :7336` |
| 3 | Verify TCP bootstrap ports are open | `netstat -an \| findstr :<bootstrap_port>` |
| 4 | Restart hole-punching subsystem | [`get_hole_puncher()`](../../mesh/hole_punching.py:1290) |
| 5 | Reinitialize Kademlia DHT | [`POST /api/mesh/dht/store`](../../backend/mesh.py:260) (send a test store) |
| 6 | Restart P2P transport | [`p2p_transport.py`](../../mesh/p2p_transport.py) restart |

### Recovery Verification

```python
# Expected healthy state
GET /api/mesh/status → {"status": "active", "peers": <N>}
GET /api/mesh/p2p/connections → {"connections": [<list>]}
GET /api/mesh/dht/stats → {"buckets": <N>, "nodes": <N>}
```

### Root Cause Analysis

| Log Pattern | Likely Cause |
|-------------|--------------|
| `ConnectionRefusedError` | Target peer not running or firewall blocking |
| `TimeoutError` on bootstrap | Bootstrap server unreachable |
| `KBucket full` repeated | DHT routing table needs pruning |
| `NAT classification failed` | STUN/TURN server unreachable |
| `PunchStatus.TIMEOUT` | Hole-punching failed (both peers symmetric NAT) |

### Related Runbooks

- [`MESH_NETWORKING_RUNBOOK.md`](./MESH_NETWORKING_RUNBOOK.md) — Full mesh operations guide

---

## 2. Storage Service Down

**Severity**: P0 (primary) / P1 (secondary)

### Symptoms
- [`GET /health/ready`](../../backend/health.py:476) returns `{"status": "degraded"}`
- Specific service check fails in health response
- Backend logs show connection errors to storage
- API calls returning 503 Service Unavailable

### Diagnosis Steps

```
1. Check full health status   → GET /health/status
2. Check per-service status   → GET /health/ready (parse checks)
3. Check Docker container     → docker ps | grep <service>
4. Check service logs         → docker logs <service> --tail 100
5. Verify network reachable   → curl <service>:<port>/health
```

### Immediate Actions by Service

#### Redis (Port 6379)

| Step | Action |
|------|--------|
| 1 | Restart container: `docker restart asimnexus-redis-1` |
| 2 | Check with redis-cli: `redis-cli ping` (expects `PONG`) |
| 3 | Verify persistence: `redis-cli info persistence` |
| 4 | Fallback: Session data degrades to in-memory cache |

#### PostgreSQL (Port 5432)

| Step | Action |
|------|--------|
| 1 | Restart container: `docker restart asimnexus-postgres-1` |
| 2 | Check connectivity: `psql -U asimnexus -c "SELECT 1"` |
| 3 | Verify replication: `psql -c "SELECT * FROM pg_stat_replication"` |
| 4 | Fallback: Read from replica; writes queued to disk |

#### ClickHouse (Port 8123)

| Step | Action |
|------|--------|
| 1 | Restart container: `docker restart asimnexus-clickhouse-1` |
| 2 | Check HTTP ping: `curl http://localhost:8123/ping` |
| 3 | Verify table engines: `clickhouse-client -q "SHOW TABLES"` |
| 4 | Fallback: Analytics data queued in memory buffer |

#### MinIO (Port 9000)

| Step | Action |
|------|--------|
| 1 | Restart container: `docker restart asimnexus-minio-1` |
| 2 | Check health: `curl http://localhost:9000/minio/health/live` |
| 3 | Verify buckets: `mc ls myminio/` |
| 4 | Fallback: File operations return 503 until restored |

#### ChromaDB (Port 8000)

| Step | Action |
|------|--------|
| 1 | Restart container: `docker restart asimnexus-chromadb-1` |
| 2 | Check heartbeat: `curl http://localhost:8000/api/v1/heartbeat` |
| 3 | Fallback: Vector search disabled; keyword search only |

### Recovery Verification

```python
# All services healthy
GET /health/ready → {
  "status": "ok",
  "checks": {
    "redis": {"status": "ok"},
    "clickhouse": {"status": "ok"},
    "postgres": {"status": "ok"},
    "minio": {"status": "ok"},
    "chromadb": {"status": "ok"}
  }
}
```

### Related Runbooks

- [`STORAGE_MONITORING_RUNBOOK.md`](./STORAGE_MONITORING_RUNBOOK.md) — Full storage operations guide
- [`docker-compose.storage.yml`](../../docker-compose.storage.yml) — Storage service definitions

---

## 3. Override Quorum Stuck

**Severity**: P1 — Human-in-the-loop decisions blocked

### Symptoms
- Override request remains `PENDING` beyond `QUORUM_TIMEOUT` (default 300s)
- [`GET /api/override/pending`](../../backend/deployment.py:271) returns requests that never resolve
- [`GET /api/consensus/pending`](../../simple_backend.py:2156) shows unresolved rounds
- Alert: "Override quorum timeout exceeded"

### Diagnosis Steps

```
1. List pending overrides     → GET /api/override/pending
2. Check specific request     → Use request_id from step 1
3. Check consensus pending    → GET /api/consensus/pending
4. Verify HOE stats           → Check HumanOverrideEngine.get_stats()
5. Review audit log           → security/audit_log.py query
```

### Immediate Actions

| Step | Action | Reference |
|------|--------|-----------|
| 1 | Check quorum configuration | [`HOE.set_quorum()`](../../core/human_override_engine.py:618) — verify N-of-M settings |
| 2 | Verify trusted circle membership | [`HOE.add_to_trusted_circle()`](../../core/human_override_engine.py:598) |
| 3 | Check if FINAL_THREE triggered | [`HOE.is_override_required`](../../core/human_override_engine.py:238) |
| 4 | Escalate pending override | [`POST /api/override/escalate`](../../backend/deployment.py:255) |
| 5 | Force-approve (emergency) | [`POST /api/override/approve`](../../backend/deployment.py:223) with reason |

### Escalation Path

```mermaid
flowchart LR
    P[PENDING] --> Q[QUORUM_PENDING]
    Q -->|Timeout >300s| E[ESCALATED]
    E -->|Up one tier| T1[Personal]
    T1 --> T2[Trusted Circle]
    T2 --> T3[Independent]
    T3 -->|Last resort| FA[Force-approve via API]
```

### Recovery Verification

```
1. POST /api/override/approve → {"status": "success", "request_id": "..."}
2. GET /api/override/pending  → {"overrides": []}  (empty list)
3. Verify consensus resolved  → GET /api/consensus/pending
```

### Root Cause Analysis

| Symptom | Likely Cause |
|---------|--------------|
| All humans unreachable | No authorized humans configured in trusted circles |
| Quorum timeout repeatedly | `QUORUM_TIMEOUT` too low (default 300s) or N > available humans |
| FINAL_THREE auto-trigger | System made 3 decisions without human confirmation |
| Escalation loop | All tiers exhausted — configure Independent tier humans |

---

## 4. Security Gate Lockout

**Severity**: P1 (gate armed) / P2 (false positive)

### Symptoms
- Biometric gate in `AUTO_LOCK` state: [`gate.get_gate_status()`](../../security/biometric_hardware_gate.py:487)
- All Level-3 operations fail with security error
- Log entries: `BiometricHardwareGate: AUTO_LOCK activated`
- Threat confidence elevated: [`HardwareHardLock.detect_threats()`](../../security/hardware_hard_lock.py:904)
- Pattern: Multiple failed biometric attempts detected

### Diagnosis Steps

```
1. Check gate status          → gate.get_gate_status()  // BiometricGateState
2. Check threat level         → hardware_lock.get_hardware_lock_status()
3. Review threat indicators   → detect_threats() result
4. Check recent records       → gate.get_records(limit=20)
5. Verify hardware integrity  → hardware_lock.get_integrity_report()
```

### Immediate Actions

| Severity | Step | Action |
|----------|------|--------|
| AUTO_LOCK | 1 | Verify this is not an actual intrusion |
| AUTO_LOCK | 2 | Use emergency bypass code: [`gate.emergency_bypass(code)`](../../security/biometric_hardware_gate.py:456) |
| AUTO_LOCK | 3 | Reset gate state: `reset_biometric_gate()` |
| COMPROMISED | 4 | Execute hard lock: [`_execute_hardware_hard_lock()`](../../security/hardware_hard_lock.py:1024) |
| RECOVERING | 5 | Verify system integrity before re-arming |

### Bypass Procedure

```
1.  Obtain override code from secure store (not in source control)
2.  Call gate.emergency_bypass(override_code)
3.  If returned True: gate resets to ARMED
4.  If False: code rejected — check override_code validity
5.  After bypass: immediately investigate biometric failure cause
```

### Recovery Verification

```python
gate.get_gate_status()
# → {"state": "ARMED", "armed_since": "2026-06-01T20:00:00Z"}

hardware_lock.get_hardware_lock_status()
# → {"hardware_state": "NORMAL", "active_threats": 0}
```

### Root Cause Analysis

| Symptom | Likely Cause |
|---------|--------------|
| False positive on threat | Hardware monitoring too sensitive — tune threat thresholds |
| Repeated biometric failures | Hardware sensor issue or biometric template corruption |
| Government attack detected | Actual intrusion attempt — escalate to sovereign council |
| File integrity mismatch | Legitimate update — re-snapshot via [`_scan_file_integrity()`](../../security/hardware_hard_lock.py:654) |

---

## 5. Release Rollback Failure

**Severity**: P1 — Deployment pipeline blocked

### Symptoms
- [`POST /api/deploy/rollback`](../../backend/deployment.py:106) returns error
- [`release_pipeline.py`](../../scripts/release_pipeline.py) `--rollback` flag fails
- Docker containers crash after rollback
- Rollback log shows inconsistencies: [`rollback_log.jsonl`](../../deploy/release/rollback_log.jsonl)
- Version mismatch between components

### Diagnosis Steps

```
1. Check current deploy status   → GET /api/deploy/status
2. List available targets         → GET /api/deploy/targets
3. Check rollback log             → type deploy/release/rollback_log.jsonl
4. Check version file             → type deploy/release/version.txt
5. Verify artifact checksums      → sha256sum <artifact_path>
```

### Immediate Actions

| Step | Action | Command |
|------|--------|---------|
| 1 | Stop current deployment | `docker-compose -f docker-compose.prod.yml down` |
| 2 | Pull previous version image | `docker pull asimnexus/backend:<previous_tag>` |
| 3 | Update version file | `echo "<previous_version>" > deploy/release/version.txt` |
| 4 | Restart with previous image | Update `.env` `BACKEND_TAG=<previous_tag>` then `docker-compose up -d` |
| 5 | Verify health | `curl http://localhost/health/ready` |

### Manual Rollback Procedure

```bash
# 1. Identify current and target versions
cat deploy/release/version.txt
cat deploy/release/v1.0.0-release-notes.md | head -5

# 2. Pull the old image
docker pull asimnexus/backend:v1.0.0

# 3. Update version tracking
echo "v1.0.0" > deploy/release/version.txt

# 4. Redeploy with old image
$env:BACKEND_TAG="v1.0.0"
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify rollback
curl -s http://localhost/api/version
# → {"version": "v1.0.0"}
```

### Database Rollback (if needed)

```bash
# PostgreSQL: restore from backup
pg_restore -U asimnexus -d asimnexus /backups/pre_release_v1.0.1.dump

# Redis: reload from RDB snapshot
redis-cli CONFIG SET dir /backups/
redis-cli CONFIG SET dbfilename pre_release.rdb
redis-cli DEBUG RELOAD
```

### Recovery Verification

```
1.  GET /health/ready         → {"status": "ok"}
2.  GET /api/version          → {"version": "<previous_version>"}
3.  GET /api/deploy/status    → {"current_version": "<previous_version>"}
4.  Verify all storage probes → /health/status checks all 5 services
5.  Run smoke tests           → pytest tests/smoke/
```

### Rollback Logging

All rollback events are recorded in [`deploy/release/rollback_log.jsonl`](../../deploy/release/rollback_log.jsonl):

```json
{"timestamp": "2026-06-01T20:00:00Z", "action": "rollback", "from": "v1.0.1", "to": "v1.0.0", "reason": "Post-deployment health check failed", "status": "completed"}
```

### Related Documents

- [`RELEASE_ROLLBACK_GUIDE.md`](../operations/RELEASE_ROLLBACK_GUIDE.md) — Full release procedures
- [`scripts/release_pipeline.py`](../../scripts/release_pipeline.py) — CLI release tool
- [`.github/RELEASE_FREEZE.md`](../../.github/RELEASE_FREEZE.md) — Freeze branch policy

---

## Generic Emergency Contacts

| Role | Contact |
|------|---------|
| Mesh Administrator | — |
| Storage Administrator | — |
| Security Officer | — |
| Release Manager | — |
| Sovereign Council | — |

*(Populate with actual contacts in production deployment)*

---

## Post-Incident Checklist

- [ ] Incident documented in runbook with timestamp
- [ ] Root cause identified and logged
- [ ] Affected users notified (if applicable)
- [ ] Monitoring alerts tuned/updated
- [ ] Runbook updated with lessons learned
- [ ] Fix ticket created in bug tracker
- [ ] Post-mortem scheduled (within 48 hours for P0)

---

## References

- [`MESH_NETWORKING_RUNBOOK.md`](./MESH_NETWORKING_RUNBOOK.md) — Mesh operations
- [`STORAGE_MONITORING_RUNBOOK.md`](./STORAGE_MONITORING_RUNBOOK.md) — Storage operations
- [`OVERRIDE_CONSENSUS_GUIDE.md`](../operations/OVERRIDE_CONSENSUS_GUIDE.md) — Override/consensus behavior
- [`SECURITY_MODEL_SUMMARY.md`](../operations/SECURITY_MODEL_SUMMARY.md) — Security architecture
- [`RELEASE_ROLLBACK_GUIDE.md`](../operations/RELEASE_ROLLBACK_GUIDE.md) — Deployment procedures
- [`SYSTEM_ARCHITECTURE_MAP.md`](../architecture/SYSTEM_ARCHITECTURE_MAP.md) — Overall architecture
- [`API_CONTRACT_INDEX.md`](../api/API_CONTRACT_INDEX.md) — API endpoint reference
