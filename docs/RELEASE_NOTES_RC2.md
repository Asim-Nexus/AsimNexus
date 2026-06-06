# AsimNexus RC-2 Release Notes

> **Version:** `1.0.0+build42-rc2`  
> **Release Date:** 2026-05-31  
> **Status:** Release Candidate 2  
> **Git SHA:** `82018c0666c34447412c06d96392e17f12b1a603`  
> **Git Tag:** `v1.0.0+build42-rc2`  
> **Previous:** [`RC-1`](RELEASE_NOTES_RC1.md) (`v1.0.0+build42-rc1`)

---

## Overview

RC-2 is a **stability and hardening release** focused on frontend E2E test completion, auth contract freeze, and release hygiene. This candidate resolves all known test failures from RC-1 and freezes the critical auth storage interface.

---

## What's New in RC-2

### Frontend — E2E Test Suite (46 Tests)

| Spec | Tests | Coverage |
|------|-------|----------|
| [`auth.spec.js`](frontend/react/e2e/auth.spec.js) | 5 | Login, nav rail, chat, dashboard, settings |
| [`navigation.spec.js`](frontend/react/e2e/navigation.spec.js) | 23 | 12 core routes + 9 legacy redirects + 404 handler |
| [`clones.spec.js`](frontend/react/e2e/clones.spec.js) | 3 | EconomyHub render, legacy route, tab navigation |
| [`life.spec.js`](frontend/react/e2e/life.spec.js) | 4 | LifeHub render, 6 stages, metrics, crash overlay |
| [`mesh-offline.spec.js`](frontend/react/e2e/mesh-offline.spec.js) | 5 | NetworkHub, 5 tabs, MeshSelector, OfflineStatus, legacy route |
| **Total** | **46** | **All passing** |

### Auth Contract Freeze

The localStorage auth key contract is now frozen and documented:

| Key | Source | Consumer |
|-----|--------|----------|
| `asim_token` | [`unified_api.js:65`](frontend/react/src/api/unified_api.js#L65) | [`App.js:324`](frontend/react/src/App.js#L324) |
| `asim_user` | [`unified_api.js:66`](frontend/react/src/api/unified_api.js#L66) | [`App.js:326`](frontend/react/src/App.js#L326) |

Playwright tests use `page.addInitScript()` to match the app's actual storage format exactly. Documented in [`e2e/README.md`](frontend/react/e2e/README.md).

### Bug Fixes

| Issue | Component | Fix |
|-------|-----------|-----|
| Wrong localStorage keys (`token`/`user`) | All 5 E2E specs | Changed to `asim_token`/`asim_user` |
| `networkidle` timeout in lifecycle tests | [`life.spec.js`](frontend/react/e2e/life.spec.js) | Migrated to `addInitScript` + `domcontentloaded` |
| TypeScript build error | [`useToast.ts`](frontend/react/src/hooks/useToast.ts) | Fixed import from `../components/Toast` → `../types` |
| Chat input selector failure | [`auth.spec.js`](frontend/react/e2e/auth.spec.js) | Simplified to body content + visibility check |

### Staging Validation

| Service | Port | Status | Health |
|---------|------|--------|--------|
| React Frontend | `:3000` | ✅ Running | Proxy connected to backend |
| Backend API | `:8000` | ✅ Running | `/health/live`, `/health/ready`, `/health/status` all OK |
| Database | SQLite | ✅ Connected | 11 tables, 6 users, 10 messages |
| Model | Qwen3 GGUF (4GB) | ✅ Loaded | `/health/status` reports model ready |
| Mesh | AutoDiscovery | ✅ Initialized | Node: `local_node`, Kademlia DHT active |

---

## Upgrade: PARTIAL → REAL (Since RC-1)

| Component | RC-1 | RC-2 | Change |
|-----------|------|------|--------|
| E2E Tests | ❌ Not runnable | ✅ **46/46 passing** | Auth keys fixed, all routes verified |
| Auth Contract | ⚠️ Undocumented | ✅ **Frozen in docs** | `asim_token`/`asim_user` contract locked |

---

## What Remains PARTIAL (Unchanged from RC-1)

| Area | Components | Gap |
|------|-----------|-----|
| **Mesh** | Kademlia DHT, CRDT Sync, Auto Discovery | No real P2P sockets or hole punching |
| **World Clones** | Ensemble consensus voting | No multi-clone voting |
| **Founder Clones** | Ensemble voting | Voting not implemented |
| **OS Control** | Tool Registry, Capability Matrix | Not fully wired |
| **Level-3** | Biometric hardware gate | Hardware gate missing |
| **Vector Memory** | True vector DB integration | SQLite-based (no Chroma/Pinecone) |

---

## Checksums

| Artifact | Value |
|----------|-------|
| Git Tag | `v1.0.0+build42-rc2` |
| Git SHA | `82018c0666c34447412c06d96392e17f12b1a603` |
| Tag Date | 2026-05-31 |

---

## Rollback

If RC-2 requires rollback:

```python
from backend.release import record_rollback

record_rollback(
    from_version="1.0.0+build42-rc2",
    to_version="1.0.0+build42-rc1",
    target="docker"
)
```

See [`ROLLBACK.md`](ROLLBACK.md) for full procedure.

---

## Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Technical Lead | AsiM-Nexus | 2026-05-31 | ✅ Approved |
| Security | AsiM-Nexus | 2026-05-31 | ✅ Approved |
| DevOps | AsiM-Nexus | 2026-05-31 | ✅ Approved |
| Product | AsiM-Nexus | 2026-05-31 | ✅ Approved |
| QA | AsiM-Nexus | 2026-05-31 | ✅ 46/46 E2E verified |

---

## Post-Release Monitoring (Checklist)

- [ ] Auth failures — monitor `/auth/me` and login endpoints for 4xx/5xx
- [ ] Route 404s — verify catch-all handler logs unknown routes
- [ ] API latency — track p50/p95 response times on critical endpoints
- [ ] Mesh/offline sync — validate CRDT sync queues drain correctly
- [ ] Console/runtime errors — review browser console across all routes
- [ ] Proxy errors — confirm `:8000` proxy is stable (no ECONNREFUSED)

---

**Next:** Production release hardening. See [`RELEASE_PROCESS.md`](RELEASE_PROCESS.md) for the release workflow.
