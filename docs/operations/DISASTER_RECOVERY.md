# ASIMNEXUS Disaster Recovery Runbook

> **Version:** 1.0.0  
> **Last Updated:** 2026-06-09  
> **Owner:** Platform Engineering Team  
> **SLA:** RTO ≤ 1 hour, RPO ≤ 15 minutes (PostgreSQL WAL), RPO ≤ 24 hours (SQLite)

---

## Table of Contents

1. [Recovery Objectives](#1-recovery-objectives)
2. [Backup Architecture](#2-backup-architecture)
3. [Disaster Scenarios](#3-disaster-scenarios)
   - [3.1 Application Crash / Pod CrashLoop](#31-application-crash--pod-crashloop)
   - [3.2 Database Corruption](#32-database-corruption)
   - [3.3 Full Cluster Failure](#33-full-cluster-failure)
   - [3.4 Cloud Region Outage](#34-cloud-region-outage)
   - [3.5 Data Breach / Compromise](#35-data-breach--compromise)
   - [3.6 Accidental Data Deletion](#36-accidental-data-deletion)
4. [Backup Procedures](#4-backup-procedures)
5. [Restore Procedures](#5-restore-procedures)
6. [Testing & Validation](#6-testing--validation)
7. [Communication Plan](#7-communication-plan)
8. [Post-Incident Review](#8-post-incident-review)
9. [Appendices](#9-appendices)

---

## 1. Recovery Objectives

| Metric | Target | Notes |
|--------|--------|-------|
| **RTO** (Recovery Time Objective) | ≤ 1 hour | Time to restore full service |
| **RPO** (Recovery Point Objective) | ≤ 15 min | PostgreSQL WAL streaming |
| **RPO** (SQLite fallback) | ≤ 24 hours | Daily full backup |
| **Backup Retention** | 14 days local | Auto-purged by CronJob |
| **Off-site Retention** | 30 days | S3-compatible object storage |
| **Testing Frequency** | Monthly | Full restore drill |

---

## 2. Backup Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Production Cluster                   │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │  PostgreSQL   │    │    Redis      │                   │
│  │  (Primary)    │    │  (AOF + RDB)  │                   │
│  └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                            │
│         ▼                   ▼                            │
│  ┌──────────────────────────────────────┐                │
│  │     Backup CronJob (daily 03:00)     │                │
│  │  pg_dump (custom, level 9)          │                │
│  │  redis-cli SAVE → copy RDB          │                │
│  └──────────────┬───────────────────────┘                │
│                 │                                        │
│                 ▼                                        │
│  ┌──────────────────────────────────────┐                │
│  │  PersistentVolume (50Gi)             │                │
│  │  Retention: 14 days                  │                │
│  └──────────────┬───────────────────────┘                │
│                 │                                        │
└─────────────────┼────────────────────────────────────────┘
                  │
                  ▼ (optional)
┌──────────────────────────────────────┐
│  S3-Compatible Object Storage        │
│  (MinIO / AWS S3)                    │
│  Retention: 30 days (lifecycle)      │
└──────────────────────────────────────┘
```

### Backup Types

| Type | Schedule | Tool | Retention | Location |
|------|----------|------|-----------|----------|
| PostgreSQL full | Daily 03:00 UTC | `pg_dump` (custom, compress=9) | 14 days local, 30 days S3 | PVC + optional S3 |
| Redis RDB | Daily 03:00 UTC | `redis-cli SAVE` + copy | 7 days local | PVC |
| SQLite full | Daily via script | `sqlite3 .backup` + gzip | 14 days local | Local filesystem |
| WAL archiving | Continuous (PG) | PostgreSQL WAL | Retain 7 days | PVC |

---

## 3. Disaster Scenarios

### 3.1 Application Crash / Pod CrashLoop

**Symptoms:**
- Pods in `CrashLoopBackOff` or `Error` state
- Alert: `CoreApiPodCrashLoop` firing
- HTTP 503 responses from API

**Severity:** Medium  
**RTO:** ≤ 10 minutes

**Recovery Steps:**

```bash
# 1. Check pod status and logs
kubectl get pods -n asimnexus
kubectl logs -n asimnexus -l app=asimnexus-core --tail=100

# 2. Check events
kubectl get events -n asimnexus --sort-by='.lastTimestamp'

# 3. Describe failing pod to see resource/health check failures
kubectl describe pod -n asimnexus -l app=asimnexus-core

# 4. If OOMKilled: increase memory limits in k8s/asimnexus-deployment.yaml
#    then apply
kubectl apply -f k8s/asimnexus-deployment.yaml

# 5. If liveness probe failing: check /health endpoint manually
kubectl port-forward -n asimnexus svc/asimnexus-core 8000:8000
curl http://localhost:8000/health

# 6. Force restart if needed
kubectl rollout restart -n asimnexus deployment/asimnexus-core

# 7. Monitor recovery
kubectl rollout status -n asimnexus deployment/asimnexus-core
```

**Rollback (if caused by bad deployment):**

```bash
kubectl rollout undo -n asimnexus deployment/asimnexus-core
kubectl rollout status -n asimnexus deployment/asimnexus-core
```

---

### 3.2 Database Corruption

**Symptoms:**
- Application errors referencing "database corruption" or "disk I/O error"
- Alert: `PostgresDown` or `DiskSpaceLow` firing
- Integrity check failures

**Severity:** Critical  
**RTO:** ≤ 30 minutes  
**RPO:** ≤ 15 minutes (WAL)

**Recovery Steps:**

```bash
# 1. STOP THE APPLICATION to prevent further writes
kubectl scale -n asimnexus deployment/asimnexus-core --replicas=0
kubectl scale -n asimnexus deployment/asimnexus-sector-api --replicas=0

# 2. Verify backup exists
./scripts/restore.sh list

# 3. If PostgreSQL:
#    a. Check if WAL replay can fix it
kubectl exec -n asimnexus deploy/postgres -- psql -U asimnexus -d asimnexus -c "SELECT pg_is_in_recovery();"

#    b. If not in recovery, attempt pg_rewind or use backup
kubectl exec -n asimnexus deploy/postgres -- psql -U asimnexus -d asimnexus -c "CHECKPOINT;"

#    c. Restore from latest backup
./scripts/restore.sh pg latest

# 4. If SQLite:
./scripts/restore.sh sqlite latest

# 5. Verify data integrity
kubectl exec -n asimnexus deploy/postgres -- psql -U asimnexus -d asimnexus -c "SELECT count(*) FROM users;"
curl http://localhost:8000/health

# 6. Restart application
kubectl scale -n asimnexus deployment/asimnexus-core --replicas=3
kubectl scale -n asimnexus deployment/asimnexus-sector-api --replicas=2
```

---

### 3.3 Full Cluster Failure

**Symptoms:**
- All pods down across all namespaces
- Kubernetes API server unreachable
- Alert: `CoreApiDown`, `PostgresDown`, `RedisDown` all firing simultaneously

**Severity:** Critical  
**RTO:** ≤ 1 hour

**Recovery Steps:**

```bash
# ── Phase 1: Restore Kubernetes Cluster ───────────────────────────────
# (Follow your cloud provider's cluster recovery procedure)
# This assumes the cluster itself is rebuilt or recovered

# ── Phase 2: Deploy ASIMNEXUS manifests ─────────────────────────────
kubectl apply -k k8s/

# ── Phase 3: Verify core services start ──────────────────────────────
kubectl get pods -n asimnexus -w

# ── Phase 4: Restore database from S3 backup ─────────────────────────
# If PVCs are lost, restore from off-site backup

# Restore PostgreSQL
aws s3 cp s3://asimnexus-backups/postgres/latest.dump.gz /tmp/pg_restore.dump.gz
./scripts/restore.sh pg /tmp/pg_restore.dump.gz

# Restore Redis (RDB file)
aws s3 cp s3://asimnexus-backups/redis/latest.rdb /tmp/redis_dump.rdb
kubectl cp /tmp/redis_dump.rdb asimnexus/redis-pod-0:/data/dump.rdb
kubectl exec -n asimnexus deploy/redis -- redis-cli CONFIG SET dir /data
kubectl exec -n asimnexus deploy/redis -- redis-cli DEBUG RELOAD

# ── Phase 5: Run database migrations ─────────────────────────────────
kubectl create job --from=cronjob/asimnexus-db-migrate db-migrate-manual

# ── Phase 6: Verify full health ──────────────────────────────────────
curl http://localhost:8000/health
curl http://localhost:8001/api/sectors/health
```

---

### 3.4 Cloud Region Outage

**Symptoms:**
- All services in one cloud region unreachable
- Cross-region health checks failing

**Severity:** Critical  
**RTO:** ≤ 1 hour

**Pre-requisites:**
- Multi-region deployment configured (see `k8s/multi-cloud-deployment.yaml`)
- Cross-region PostgreSQL replication
- Global load balancer (Route53 / Cloud DNS)

**Recovery Steps:**

```bash
# 1. Update DNS to route traffic to secondary region
#    (Cloud DNS / Route53 health check should auto-failover)

# 2. Promote secondary PostgreSQL to primary
kubectl exec -n asimnexus deploy/postgres-secondary -- \
  psql -c "SELECT pg_promote();"

# 3. Update application environment to point to new primary
kubectl set env -n asimnexus deployment/asimnexus-core \
  DATABASE_URL=postgresql://asimnexus@postgres-secondary:5432/asimnexus

# 4. Verify traffic flowing to secondary region
curl http://secondary-region-lb/health

# 5. Monitor until primary region is restored
```

---

### 3.5 Data Breach / Compromise

**Symptoms:**
- Security alert: `UnauthorizedAccessAttempts` or `SecurityAuditFailure`
- Suspicious API activity
- Reported unauthorized access

**Severity:** Critical

**Immediate Actions:**

```bash
# 1. ISOLATE the affected component
kubectl label pod -n asimnexus -l app=asimnexus-core quarantine=true
kubectl scale -n asimnexus deployment/asimnexus-core --replicas=0

# 2. Rotate all secrets
kubectl delete secret asimnexus-secrets
kubectl apply -f k8s/secret.yaml  # with new values

# 3. Revoke and reissue JWT signing key
#    Update ASIM_JWT_SECRET in .env and re-deploy

# 4. Force all users to re-authenticate (invalidate sessions)
#    (Drop auth_tokens table or set token_expiry to past)

# 5. Restore database from backup taken before the incident
./scripts/restore.sh pg latest

# 6. Review audit logs
kubectl logs -n asimnexus -l app=asimnexus-core --tail=5000 | grep -i "401\|403\|audit"

# 7. Engage security team for forensic analysis
```

---

### 3.6 Accidental Data Deletion

**Symptoms:**
- User reports missing data
- Database records unexpectedly absent
- `DELETE` or `DROP` operation in recent audit log

**Severity:** High  
**RTO:** ≤ 15 minutes (point-in-time recovery)

**Recovery Steps:**

```bash
# 1. If detected within WAL retention window (< 15 min):
#    a. Stop writes
kubectl scale -n asimnexus deployment/asimnexus-core --replicas=0

#    b. Perform point-in-time recovery to just before the deletion
pg_restore --dbname=asimnexus --clean \
  --use-list=<(echo "SEQUENCE SET 1; DATA SET 2;") \
  --table=affected_table \
  /backups/postgres/latest.dump

# 2. If beyond WAL window, restore full database from latest dump
./scripts/restore.sh pg latest

# 3. Verify data restored
kubectl exec -n asimnexus deploy/postgres -- \
  psql -U asimnexus -d asimnexus -c "SELECT count(*) FROM affected_table;"

# 4. Restart application
kubectl scale -n asimnexus deployment/asimnexus-core --replicas=3
```

---

## 4. Backup Procedures

### 4.1 Automated Backup (Kubernetes CronJob)

Backup runs daily at 03:00 UTC via `k8s/backup-cronjob.yaml`.

Manual trigger:

```bash
kubectl create job --from=cronjob/asimnexus-db-backup manual-backup-$(date +%s)
```

### 4.2 Manual PostgreSQL Backup

```bash
# Using the backup script
./scripts/backup_pg.sh

# With S3 upload
S3_ENDPOINT=https://minio.example.com \
S3_ACCESS_KEY=mykey \
S3_SECRET_KEY=mysecret \
./scripts/backup_pg.sh
```

### 4.3 Manual SQLite Backup

```bash
./scripts/backup_sqlite.sh
```

### 4.4 Verify Backup Integrity

```bash
# List and verify all backups
./scripts/restore.sh list

# Check specific backup
pg_restore --list /backups/postgres/asimnexus-pg-20250101-030000.dump.gz
```

---

## 5. Restore Procedures

### 5.1 Restore PostgreSQL from Local Backup

```bash
# Interactive restore with confirmation prompt
./scripts/restore.sh pg /path/to/backup.dump.gz

# Restore latest backup
./scripts/restore.sh pg latest
```

### 5.2 Restore SQLite from Local Backup

```bash
# Stop the application first
# Then run:
./scripts/restore.sh sqlite /path/to/backup.db.gz

# Or restore latest
./scripts/restore.sh sqlite latest
```

### 5.3 Restore from S3

```bash
# Download backup from S3
aws s3 cp s3://asimnexus-backups/postgres/asimnexus-pg-20250101-030000.dump.gz /tmp/

# Restore
./scripts/restore.sh pg /tmp/asimnexus-pg-20250101-030000.dump.gz
```

---

## 6. Testing & Validation

### Monthly Restore Drill

Run the following on the **first Monday of every month**:

```bash
#!/usr/bin/env bash
# monthly_drill.sh — run in staging environment

set -euo pipefail
echo "=== Monthly DR Drill: $(date) ==="

# 1. Deploy fresh staging environment
kubectl apply -k k8s/ --namespace=asimnexus-staging

# 2. Restore latest production backup into staging
./scripts/restore.sh pg latest

# 3. Run application health checks
curl -f http://staging.asimnexus.local/health
curl -f http://staging.asimnexus.local/api/sectors/health

# 4. Verify data integrity
EXPECTED_USERS=$(kubectl exec deploy/postgres -n asimnexus -- \
  psql -t -c "SELECT count(*) FROM users;" | tr -d ' ')
echo "Users restored: ${EXPECTED_USERS}"

# 5. Run application test suite
python -m pytest tests/real/ -x -q

# 6. Report results
echo "=== DR Drill Complete ==="
echo "Result: PASS"
```

### Validation Checklist

- [ ] PostgreSQL restore completed successfully
- [ ] `pg_restore --list` shows expected tables and row counts
- [ ] Application health endpoints return 200
- [ ] API requests succeed (sample CRUD test)
- [ ] Redis data rehydrated (session cache working)
- [ ] All alerts resolve within 5 minutes of restore completion
- [ ] Restore time documented for SLA tracking

---

## 7. Communication Plan

| Incident Type | Notify | Channel | Within |
|---------------|--------|---------|--------|
| Application crash | On-call engineer | PagerDuty + Slack #ops-alerts | 5 min |
| Database corruption | On-call + DB team | PagerDuty + Slack #ops-alerts | 5 min |
| Full cluster failure | All engineering | PagerDuty + Slack #general | 5 min |
| Data breach | Security team + Legal | PagerDuty + Slack #security-alerts + Email | Immediate |
| Region outage | Platform team | PagerDuty + Slack #ops-alerts | 5 min |

### Escalation Chain

1. **Tier 1:** On-call Engineer (PagerDuty) — 24/7
2. **Tier 2:** Platform Engineering Lead (Phone) — 15 min
3. **Tier 3:** CTO / VP Engineering — 30 min

### Status Page Template

```
Subject: [ASIMNEXUS] {INCIDENT_TYPE} — {STATUS}

Status: Investigating / Identified / Monitoring / Resolved

Start Time: {UTC_TIMESTAMP}
End Time: {UTC_TIMESTAMP} (if resolved)
Impact: {SCOPE} — {% of users affected}

Current Actions:
- {action_1}
- {action_2}

Next Update: {UTC_TIMESTAMP + 30min}
```

---

## 8. Post-Incident Review

After every incident that triggers DR procedures, complete within 5 business days:

1. **Timeline:** Document the full timeline of events
2. **Root Cause:** Determine what caused the incident
3. **Detection:** How was it detected? Could it be faster?
4. **Response:** Were procedures followed? What worked/didn't?
5. **Recovery:** How long did recovery take? Did we meet RTO/RPO?
6. **Improvements:** What changes prevent recurrence?
7. **Action Items:** Assign owners and deadlines

File the review in `docs/operations/postmortems/YYYY-MM-DD-incident-title.md`.

---

## 9. Appendices

### A. Useful Commands

```bash
# Check backup pod status
kubectl get pods -n asimnexus -l app.kubernetes.io/component=backup

# View backup job logs
kubectl logs -n asimnexus -l job-name=$(kubectl get jobs -n asimnexus -o json | jq -r '.items[-1].metadata.name')

# Force immediate backup
kubectl create job --from=cronjob/asimnexus-db-backup immediate-backup

# Check PVC status and usage
kubectl get pvc -n asimnexus asimnexus-backup-pvc
kubectl exec -n asimnexus deploy/postgres -- df -h /backups
```

### B. Key Contacts

| Role | Name | Contact |
|------|------|---------|
| On-call Engineer | (PagerDuty rotation) | `oncall@asimnexus.com` |
| DB Administrator | (PostgreSQL expert) | `dba@asimnexus.com` |
| Security Lead | (Incident response) | `security@asimnexus.com` |
| Platform Lead | (Kubernetes/infra) | `platform@asimnexus.com` |

### C. Related Documentation

- [`k8s/backup-cronjob.yaml`](../../k8s/backup-cronjob.yaml) — K8s CronJob definition
- [`scripts/backup_pg.sh`](../../scripts/backup_pg.sh) — PostgreSQL backup script
- [`scripts/backup_sqlite.sh`](../../scripts/backup_sqlite.sh) — SQLite backup script
- [`scripts/restore.sh`](../../scripts/restore.sh) — Database restore script
- [`docs/operations/DOCKER_SETUP.md`](./DOCKER_SETUP.md) — Docker deployment guide
- [`k8s/network-policy.yaml`](../../k8s/network-policy.yaml) — Network isolation policies
- `docs/operations/postmortems/` — Incident post-mortem archive
