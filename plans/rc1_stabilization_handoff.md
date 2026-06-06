# RC-1 Stabilization — Implementation Handoff

## Overview

This document contains the complete implementation plan for executing the RC-1 Stabilization Phase. All Architect-mode prep work is complete. Code mode will execute the remaining steps.

**Files already created/frozen:**
- [`docs/STATUS.md`](docs/STATUS.md) — Frozen RC-1 snapshot with freeze banner, version reference, expanded component inventory
- [`docs/RELEASE_NOTES_RC1.md`](docs/RELEASE_NOTES_RC1.md) — Formal RC-1 release notes
- [`plans/comprehensive_analysis.md`](plans/comprehensive_analysis.md) — Full 13-section system analysis

**Current version:** `1.0.0+build42` in [`deploy/release/version.txt`](deploy/release/version.txt)

---

## Step 2b: Tag RC-1 in Release System

**Objective:** Formally record RC-1 via the existing [`backend/release.py`](backend/release.py) system.

### Actions:

1. **Publish RC-1 release:**
   ```python
   from backend.release import publish_release
   
   publish_release(
       version="1.0.0+build42",
       target="docker",
       checksum="<sha256_of_deploy_artifacts_or_placeholder>"
   )
   ```

2. **Set RC-1 as current:**
   ```python
   from backend.release import set_current_release
   
   set_current_release(version="1.0.0+build42", target="docker")
   ```

3. **Verify:**
   ```python
   from backend.release import current_release
   
   print(current_release(target="docker"))
   # Should return: {"version": "1.0.0+build42", "is_current": true, ...}
   ```

4. **If running from script,** use the CLI equivalent:
   ```bash
   python -c "from backend.release import publish_release; r = publish_release(version='1.0.0+build42', target='docker', checksum='rc-1-freeze'); print(r)"
   ```
   Then set current:
   ```bash
   python -c "from backend.release import set_current_release; set_current_release(version='1.0.0+build42', target='docker'); print('RC-1 set as current')"
   ```

**Expected result:** [`deploy/release/releases.json`](deploy/release/releases.json) gains a new entry with `version: "1.0.0+build42"`, `is_current: true`, `target: "docker"`.

---

## Step 3: Full Docs Pass

**Objective:** Create the remaining documentation files. All are `.md` files.

### 3a: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

Extract from [`plans/comprehensive_analysis.md`](plans/comprehensive_analysis.md) Sections 2-5 and 9. Include:

- **5-Layer Architecture diagram** (Mermaid):
  ```mermaid
  flowchart TD
      L1[Layer 1: Pure Kernel - ASIM Kernel + FastAPI]
      L2[Layer 2: Universal MCP - Model Routing + Privacy Tiers]
      L3[Layer 3: Dharma-Chakra - VETO + Constitution + Balance]
      L4[Layer 4: Agentic Matrix - Clones + Orchestrators]
      L5[Layer 5: Omni-Operator Interface - Frontend + API]
      L1 --> L2 --> L3 --> L4 --> L5
  ```
- Component dependency graph
- Data flow: Request → Router → VETO → Clone → Response
- Security boundary diagram (ZKP + Identity + Encryption)
- File structure overview (key directories)

### 3b: [`docs/INSTALL.md`](docs/INSTALL.md)

Update existing install guide. Must include:

- Prerequisites: Python 3.10+, Node.js 18+, Docker (optional)
- Quick start:
  ```bash
  git clone <repo>
  cd AsimNexus
  pip install -r requirements.txt
  cd frontend/react && npm install && cd ../..
  python main.py
  ```
- Docker setup: `docker-compose up`
- Configuration (`.env.example` reference)
- Troubleshooting section

### 3c: [`docs/ROLLBACK.md`](docs/ROLLBACK.md)

Document the rollback procedure using [`backend/release.py`](backend/release.py):

```python
from backend.release import record_rollback

# Record the rollback event
record_rollback(
    from_version="1.0.0+build42",
    to_version="<previous_stable_version>",
    target="docker"
)
```

Include:
- How to list available releases: `list_releases(target="docker")`
- How to check current release: `current_release(target="docker")`
- How to set a previous release as current: `set_current_release(version="<prev>", target="docker")`
- Git rollback instructions as safety net

### 3d: [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md)

Generate from [`core/api_endpoints.py`](core/api_endpoints.py) (100+ endpoints). Organize by prefix:

| Prefix | Endpoints | Auth Required |
|--------|-----------|---------------|
| `/auth/*` | register, login, me, users | Some |
| `/personal/*` | status, mode, clones, rule | Yes |
| `/health` | health_check | No |
| `/status` | get_status | No |
| `/llm/*` | chat, chat/stream | Yes |
| `/clones/*` | list, chat, direct, agent-mode | Some |
| `/dharma/*` | status, process, evaluate, countries, layers/* | Some |
| `/zkp/*` | pending, confirm, reject, status | Yes |
| `/hdt/*` | me, update, top-clones | Yes |
| `/mesh/*` | nodes, join | No |
| `/api/*` | agents, world_os, apis, analytics, security, bridge, discovery, local-llm | Some |
| `/files/*` | list, read, write, delete, create_directory, search | Some |
| `/tools/*` | execute, list, file/*, command, python, network | Some |
| `/system/*` | scan, summary | Admin |
| `/automation/*` | initialize, status, process, create, list, execute, delete | Some |

Each endpoint entry should include: method, path, description, request body (if POST), response format, auth requirement.

### 3e: [`docs/RELEASE_PROCESS.md`](docs/RELEASE_PROCESS.md)

Document how to create a new release:

1. Update version in `deploy/release/version.txt`
2. Run `publish_release(version="<new>", target="docker", checksum="<sha>")`
3. Run `set_current_release(version="<new>", target="docker")`
4. Verify with `current_release(target="docker")`
5. Write release notes
6. Update STATUS.md freeze (if applicable)

### 3f: [`docs/PWA_SETUP.md`](docs/PWA_SETUP.md)

PWA configuration notes:
- Manifest location: `frontend/react/public/manifest.json`
- Service worker: `frontend/react/public/service-worker.js`
- Verify: `npm run build` produces PWA-compatible output
- Lighthouse audit checklist

---

## Step 4: Deployment Verification

**Objective:** Verify all deployment paths. Requires running commands.

### Actions:

1. **Docker build:**
   ```bash
   docker-compose build
   docker-compose up -d
   curl http://localhost:8000/health
   ```
   Verify: health endpoint returns 200 with component statuses.

2. **K8s manifests:**
   ```bash
   kubectl apply --dry-run=client -f k8s/
   ```
   Verify: no validation errors. Check all YAML files in [`k8s/`](k8s/) directory.

3. **PWA manifest check:**
   - Verify `frontend/react/public/manifest.json` exists and has valid JSON
   - Verify `start_url`, `display: standalone`, icons array
   - Verify service worker registration in `src/index.js` or `App.js`

4. **Frontend build:**
   ```bash
   cd frontend/react && npm run build
   ```
   Verify: build completes without errors.

5. **Test suite:**
   ```bash
   python -m pytest tests/real/test_personal_os.py -v
   ```
   Verify: 121/121 tests passing.

---

## Step 5: Final Launch Checklist

**Objective:** Rewrite [`docs/LAUNCH_CHECKLIST.md`](docs/LAUNCH_CHECKLIST.md) from scratch. The current version (2024-01-XX, "Alpha 2.0.0-alpha") is obsolete.

### New structure:

```markdown
# AsimNexus RC-1 Launch Checklist

## 🎯 Goal
**Version:** 1.0.0+build42 (RC-1)
**Freeze:** 2026-05-31
**Status:** 🔒 FROZEN

## ✅ Pre-Launch (All Must Pass)

### Version & Release
- [x] Version locked: 1.0.0+build42 in deploy/release/version.txt
- [x] RC-1 published via backend/release.py:publish_release()
- [x] RC-1 set as current via backend/release.py:set_current_release()
- [x] Rollback path documented in docs/ROLLBACK.md
- [x] Release notes in docs/RELEASE_NOTES_RC1.md
- [x] STATUS.md frozen as RC-1 snapshot

### Testing
- [ ] Personal OS: 121/121 tests passing
- [ ] Security module tests: pytest security/test_*.py
- [ ] Auth tests: pytest tests/real/test_auth.py
- [ ] Backend API tests: pytest tests/real/test_backend_api.py
- [ ] Integration tests: pytest tests/integration/
- [ ] Frontend build: cd frontend/react && npm run build

### Security
- [ ] JWT secret configured in production
- [ ] ZKP system operational
- [ ] Immutable Constitution integrity verified
- [ ] Power Balance Constitution active
- [ ] Dharma VETO engine online
- [ ] Rate limiting enabled

### Documentation
- [x] STATUS.md frozen (docs/STATUS.md)
- [x] Release notes written (docs/RELEASE_NOTES_RC1.md)
- [ ] Architecture doc complete (docs/ARCHITECTURE.md)
- [ ] Install guide up to date (docs/INSTALL.md)
- [ ] Rollback procedure documented (docs/ROLLBACK.md)
- [ ] API reference generated (docs/API_REFERENCE.md)
- [ ] Release process documented (docs/RELEASE_PROCESS.md)

### Deployment
- [ ] Docker build: docker-compose build succeeds
- [ ] Docker run: docker-compose up -d, /health responds 200
- [ ] K8s manifests: kubectl apply --dry-run=client -f k8s/ passes
- [ ] PWA manifest valid
- [ ] Frontend production build succeeds

### Observability
- [ ] /health endpoint returns full component status
- [ ] /status endpoint returns system summary
- [ ] /api/analytics/* endpoints respond
- [ ] /metrics endpoint returns data

### No Critical Gaps
- [x] All CONCEPT items documented as future (not current features)
- [x] All PARTIAL items documented with clear upgrade path
- [ ] No critical bugs in REAL components
- [ ] Known limitations documented

## 🚀 Launch Day

### T-2 Hours
- [ ] Final STATUS.md integrity check
- [ ] Run full test suite
- [ ] Verify /health endpoint
- [ ] Prepare announcement

### T-0
- [ ] Deploy RC-1
- [ ] Verify all services healthy
- [ ] Post release announcement

### T+1 Hour
- [ ] Monitor error rates
- [ ] Check active connections
- [ ] Watch /health endpoint

## 📊 Success Metrics
| Metric | Target | Current |
|--------|--------|---------|
| API Uptime | 99.9% | N/A |
| Tests Passing | 100% | N/A |
| Critical Bugs | 0 | N/A |
```

---

## Implementation Order

Execute in this exact sequence:

1. **Step 2b:** Tag RC-1 via Python (run publish_release + set_current_release)
2. **Step 3a:** Create [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
3. **Step 3b:** Update [`docs/INSTALL.md`](docs/INSTALL.md)
4. **Step 3c:** Create [`docs/ROLLBACK.md`](docs/ROLLBACK.md)
5. **Step 3d:** Create [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md)
6. **Step 3e:** Create [`docs/RELEASE_PROCESS.md`](docs/RELEASE_PROCESS.md)
7. **Step 3f:** Create [`docs/PWA_SETUP.md`](docs/PWA_SETUP.md)
8. **Step 4:** Run deployment verification commands
9. **Step 5:** Rewrite [`docs/LAUNCH_CHECKLIST.md`](docs/LAUNCH_CHECKLIST.md)
10. **Final:** Run complete test suite, verify all checks pass

---

## Files to Create/Modify

| File | Action | Type |
|------|--------|------|
| `deploy/release/releases.json` | Append RC-1 entry | Data (via code) |
| `deploy/release/rollback_log.jsonl` | (empty, ready for rollbacks) | Data |
| `docs/ARCHITECTURE.md` | **Create** | Doc |
| `docs/INSTALL.md` | **Update** | Doc |
| `docs/ROLLBACK.md` | **Create** | Doc |
| `docs/API_REFERENCE.md` | **Create** | Doc |
| `docs/RELEASE_PROCESS.md` | **Create** | Doc |
| `docs/PWA_SETUP.md` | **Create** | Doc |
| `docs/LAUNCH_CHECKLIST.md` | **Rewrite** | Doc |
