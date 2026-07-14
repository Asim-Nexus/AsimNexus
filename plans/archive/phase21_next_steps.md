# Phase 21: Next Steps — What Remains After v1.0.0

> **Current State:** All Phases 1-20 complete. v1.0.0 production release ready.
> **Tests:** 491 passed, 5 skipped, 0 failures
> **API Routes:** 43 modules, 636+ routes
> **Frontend:** 70+ components, 9 Hub pages, 9 mobile screens

---

## What's Still Remaining

After completing all 20 phases, here's what's left — organized by priority:

### P0 — Cleanup Stale Artifacts (Must Do)

| # | Item | Path | Action |
|---|------|------|--------|
| 1 | Forensic reports | `forensic_report_*.json` (9 files at root) | Delete — runtime artifacts from biometric gate testing |
| 2 | Stale audit scripts | `scripts/audit/_*.py` (8 files) | Delete — development/debug scripts, not needed in production |
| 3 | Stale archive files | `.kilo/archive/` (50+ files) | Review and clean — old plans, test outputs, forensic reports |
| 4 | Stale root scripts | `_migrate_tokens.py`, `_monitor_staging.py`, `_rollback_rehearsal.py`, `_test_get_stats.py`, `staging_verify.py` | Delete — development scripts at root level |
| 5 | Empty config | `config/__init__.py` (empty), `config/mvp_definition.py` (stale) | Review and clean |

### P1 — Production Hardening

| # | Item | Details |
|---|------|---------|
| 6 | Fix `frontend/react/` references | Open tabs show `frontend/react/src/...` files — these are stale references; the real frontend is in `frontend/src/` |
| 7 | Add `.gitignore` entries | Add `forensic_report_*.json`, `scripts/audit/`, `.kilo/archive/` to `.gitignore` |
| 8 | Fix CI/CD workflow | Check `ci-cd.yml` references — may point to stale paths |
| 9 | Add health check endpoints | Verify `/health/live`, `/health/ready`, `/health/status` work correctly |
| 10 | Add Prometheus metrics | Verify `/metrics` endpoint exposes all required metrics |

### P2 — Feature Completion

| # | Item | Details |
|---|------|---------|
| 11 | Plugin Marketplace Frontend | Build UI for `core/plugin_marketplace.py` — browse, install, enable/disable plugins |
| 12 | AR/VR Frontend | Connect WebXR to `routes/arvr.py` — immersive dashboard mode |
| 13 | Real Mesh Networking (socket) | Enable actual UDP/TCP sockets in `core/mesh/` — currently production-grade code but not socket-bound |
| 14 | Real Biometric Hardware | Connect libfprint/OpenCV to `core/security/biometric_hardware_gate.py` |
| 15 | Performance Load Tests | Create real load tests with 100+ concurrent users |
| 16 | E2E Tests for Governance | Add E2E tests for governance chat, enterprise dashboard, stakeholder workflow |

### P3 — Nepal-Specific Features

| # | Item | Details |
|---|------|---------|
| 17 | Nepal Payment Gateway | Integrate Nepal's banking APIs (connectIPS, eSewa, Khalti) |
| 18 | Nepal Digital Identity | Connect to Nepal's national digital identity system |
| 19 | Nepal Language Full Support | Complete Nepali language UI across all components |
| 20 | Nepal Government API | Connect to Nepal government's open data APIs |

### P4 — Advanced Features

| # | Item | Details |
|---|------|---------|
| 21 | Multi-language Support | Add i18n for Nepali, English, Hindi, etc. |
| 22 | Offline-First Sync | Complete offline support with CRDT sync |
| 23 | Mobile App Polish | Complete React Native app with all features |
| 24 | Desktop App Polish | Complete Electron app with system tray, notifications |
| 25 | PWA Enhancements | Add push notifications, background sync |

---

## Recommended Execution Order

```
Phase 21.1 → 21.2 → 21.3  (P0 — cleanup stale artifacts)
     ↓
Phase 21.4 → 21.5 → 21.6  (P1 — production hardening)
     ↓
Phase 21.7 → 21.8 → 21.9  (P2 — feature completion)
     ↓
Phase 21.10 → 21.11       (P3 — Nepal features)
     ↓
Phase 21.12 → 21.13       (P4 — advanced features)
```

---

## Detailed Todo Checklist

### Phase 21.1: Delete Forensic Reports
- [ ] Delete `forensic_report_20260703_190923.json`
- [ ] Delete `forensic_report_20260703_191125.json`
- [ ] Delete `forensic_report_20260703_191914.json`
- [ ] Delete `forensic_report_20260703_192021.json`
- [ ] Delete `forensic_report_20260703_192130.json`
- [ ] Delete `forensic_report_20260703_192234.json`
- [ ] Delete `forensic_report_20260703_192432.json`
- [ ] Delete `forensic_report_20260703_192556.json`
- [ ] Delete `forensic_report_20260703_192750.json`

### Phase 21.2: Delete Stale Audit Scripts
- [ ] Delete `scripts/audit/_audit_routes.py`
- [ ] Delete `scripts/audit/_audit2.py`
- [ ] Delete `scripts/audit/_debug_zkp.py`
- [ ] Delete `scripts/audit/_deep_audit.py`
- [ ] Delete `scripts/audit/_extract_all_routes.py`
- [ ] Delete `scripts/audit/_extract_routes.py`
- [ ] Delete `scripts/audit/_test_chat_hang.py`
- [ ] Delete `scripts/audit/_verify_imports.py`

### Phase 21.3: Delete Stale Root Scripts
- [ ] Delete `_migrate_tokens.py`
- [ ] Delete `_monitor_staging.py`
- [ ] Delete `_rollback_rehearsal.py`
- [ ] Delete `_test_get_stats.py`
- [ ] Delete `staging_verify.py`

### Phase 21.4: Update .gitignore
- [ ] Add `forensic_report_*.json` to `.gitignore`
- [ ] Add `scripts/audit/` to `.gitignore`
- [ ] Add `.kilo/archive/` to `.gitignore`
- [ ] Add `_*.py` (root-level underscore scripts) to `.gitignore`

### Phase 21.5: Fix CI/CD & Production Config
- [ ] Verify `ci-cd.yml` references are correct
- [ ] Verify `docker-publish.yml` references are correct
- [ ] Verify `security-scan.yml` references are correct
- [ ] Check `Dockerfile.backend` for stale path references
- [ ] Check `docker-compose.prod.yml` for stale path references

### Phase 21.6: Verify Health & Metrics Endpoints
- [ ] Test `/health/live` returns 200
- [ ] Test `/health/ready` returns 200
- [ ] Test `/health/status` returns all components
- [ ] Test `/metrics` returns Prometheus metrics

### Phase 21.7: Plugin Marketplace Frontend
- [ ] Create `frontend/src/components/marketplace/PluginMarketplace.tsx`
- [ ] Create `frontend/src/components/marketplace/PluginCard.tsx`
- [ ] Create `frontend/src/components/marketplace/PluginDetail.tsx`
- [ ] Add plugin API methods to `frontend/src/api/asimnexus.ts`
- [ ] Add route in `frontend/src/App.tsx`

### Phase 21.8: AR/VR Frontend
- [ ] Create `frontend/src/components/arvr/ARVRViewport.tsx`
- [ ] Create `frontend/src/components/arvr/SpatialMenu.tsx`
- [ ] Add AR/VR API methods to `frontend/src/api/asimnexus.ts`
- [ ] Add route in `frontend/src/App.tsx`

### Phase 21.9: Real Mesh Networking (Socket)
- [ ] Enable UDP sockets in `core/mesh/kademlia_dht.py`
- [ ] Enable WebSocket sync in `core/mesh/crdt_sync.py`
- [ ] Enable UDP hole punching in `core/mesh/hole_punching.py`
- [ ] Enable STUN/TURN in `core/mesh/stun_turn.py`
- [ ] Enable mDNS broadcast in `core/mesh/autodiscovery.py`
- [ ] Write mesh integration tests (2-node, 3-node, 10-node)

### Phase 21.10: Nepal Payment Gateway
- [ ] Integrate connectIPS API
- [ ] Integrate eSewa API
- [ ] Integrate Khalti API
- [ ] Create payment UI components
- [ ] Add payment routes

### Phase 21.11: Nepal Digital Identity
- [ ] Connect to Nepal national digital identity API
- [ ] Create identity verification flow
- [ ] Add e-Residency full integration

### Phase 21.12: Multi-language Support
- [ ] Set up i18n framework
- [ ] Create Nepali translations
- [ ] Create English translations
- [ ] Create Hindi translations
- [ ] Add language selector to all pages

### Phase 21.13: Mobile & Desktop Polish
- [ ] Complete all React Native screens
- [ ] Add push notifications to mobile
- [ ] Add system tray to Electron
- [ ] Add desktop notifications
- [ ] Add PWA background sync

---

## Summary

| Phase | Focus | Items | Priority |
|-------|-------|:-----:|:--------:|
| 21.1 | Delete forensic reports | 9 files | P0 |
| 21.2 | Delete stale audit scripts | 8 files | P0 |
| 21.3 | Delete stale root scripts | 5 files | P0 |
| 21.4 | Update .gitignore | 4 entries | P0 |
| 21.5 | Fix CI/CD & production config | 5 checks | P1 |
| 21.6 | Verify health & metrics | 4 endpoints | P1 |
| 21.7 | Plugin Marketplace Frontend | 5 components | P2 |
| 21.8 | AR/VR Frontend | 3 components | P2 |
| 21.9 | Real Mesh Networking (socket) | 6 modules | P2 |
| 21.10 | Nepal Payment Gateway | 5 integrations | P3 |
| 21.11 | Nepal Digital Identity | 3 integrations | P3 |
| 21.12 | Multi-language Support | 5 tasks | P4 |
| 21.13 | Mobile & Desktop Polish | 5 tasks | P4 |
