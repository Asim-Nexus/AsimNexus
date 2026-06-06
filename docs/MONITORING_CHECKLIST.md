# Post-Release Monitoring Checklist

> **Release:** `1.0.0+build42-rc2` (RC-2)  
> **Deploy Date:** 2026-05-31  
> **Owner:** AsiM-Nexus

---

## Instructions

Check each item after the release is deployed to staging/production.  
Mark `[x]` when verified. Log any anomalies in the **Notes** section.

---

## 1. Auth & Access

- [ ] **Login flow** — `/auth/login` returns 200 with valid token
- [ ] **Token validation** — `/auth/me` accepts `asim_token` and returns user object
- [ ] **Registration** — `/auth/register` creates new user and returns auth pair
- [ ] **Logout/clear** — `clearAuth()` removes both `asim_token` and `asim_user` from localStorage
- [ ] **Protected routes** — unauthenticated requests return 401/403 (not 200)

**Expected auth keys (frozen contract):**
| Key | Source |
|-----|--------|
| `asim_token` | [`unified_api.js:65`](../frontend/react/src/api/unified_api.js#L65) |
| `asim_user` | [`unified_api.js:66`](../frontend/react/src/api/unified_api.js#L66) |

---

## 2. Route Integrity

- [ ] **All 12 core routes** resolve without 404
- [ ] **Legacy redirects** (9 routes) map to new paths
- [ ] **Catch-all handler** logs unknown routes
- [ ] **404 page** renders for truly invalid paths
- [ ] **E2E tests** — `npx playwright test` yields 46/46 passing

| Route | Status |
|-------|--------|
| `/` | — |
| `/dashboard` | — |
| `/life` | — |
| `/economy` | — |
| `/clones` | — |
| `/network` | — |
| `/memory` | — |
| `/chat` | — |
| `/settings` | — |
| `/agents` | — |
| `/mesh` | — |
| `/os` | — |

---

## 3. API Latency & Reliability

- [ ] **p50 response time** < 200ms on critical endpoints
- [ ] **p95 response time** < 500ms on critical endpoints
- [ ] **Health endpoints** all return 200 within 100ms
  - `/health/live`
  - `/health/ready`
  - `/health/status`
- [ ] **No 5xx errors** in a 5-minute window of continuous requests
- [ ] **No 4xx spikes** (excluding known auth failures for unauthenticated calls)

---

## 4. Mesh & Offline Sync

- [ ] **Mesh status** — `/api/mesh/status` returns healthy
- [ ] **Node registry** — `/api/mesh/nodes` lists known peers
- [ ] **Auto-discovery** — `/api/mesh/discovery/status` shows active discovery
- [ ] **CRDT sync queues** drain to zero after initial sync
- [ ] **Offline capabilities** — `/api/mesh/offline/capabilities` returns expected features
- [ ] **Air-gap** engage/disengage cycle completes without error

---

## 5. Frontend Runtime

- [ ] **Browser console** — no uncaught errors on any route
- [ ] **WebSocket** — `/ws/chat` connects and receives messages
- [ ] **Proxy** — `:3000 → :8000` proxy stable (no ECONNREFUSED)
- [ ] **LocalStorage** — no stale `token`/`user` keys (only `asim_token`/`asim_user`)
- [ ] **Service Worker** — PWA caches static assets correctly

---

## 6. Backend Stability

- [ ] **Model loaded** — `/health/status` reports Qwen3 GGUF model ready
- [ ] **Database** — SQLite query times < 50ms on indexed queries
- [ ] **Memory usage** — backend process < 8GB RSS (model loaded)
- [ ] **CPU** — idle CPU < 5% (no runaway loops)
- [ ] **No crash loops** — uvicorn process stable for 30+ minutes

---

## Anomaly Log

| Time (UTC) | Component | Severity | Description | Action Taken |
|------------|-----------|----------|-------------|--------------|
| — | — | — | — | — |

---

## Sign-Off

Once all checks pass, record below:

| Role | Name | Date | Signature |
|------|------|------|-----------|
| DevOps | — | — | — |
| QA | — | — | — |

---

*See [RELEASE_NOTES_RC2.md](RELEASE_NOTES_RC2.md) for full release notes and rollback instructions.*
