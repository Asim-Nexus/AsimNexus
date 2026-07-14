# Phase Final Unification: Complete AsimNexus Integration

## Objective
Fix all remaining disconnections across backend and frontend to make AsimNexus a fully unified system where every component is properly wired, every route has its `init_*()` call, every frontend component uses the unified API layer, and all exports are complete.

---

## Step 1: Fix `app.py` — Add 17 Missing `init_*()` Calls

**File**: [`app.py:633-720`](app.py:633)

**Action**: Add the following 17 `init_*()` calls to `_lazy_register_routes()`:

```python
from routes.universe import init_universe
from routes.mirror import init_mirror
from routes.dreaming import init_dreaming
from routes.evolution import init_evolution
from routes.dharma import init_dharma
from routes.founder_clones import init_founder_clones
from routes.learning import init_learning
from routes.observability import init_observability
from routes.registry import init_registry
from routes.deploy import init_deploy
from routes.push import init_push
from routes.bugs import init_bugs
from routes.clones import init_clones
from routes.offline import init_offline
from routes.override import init_override
from routes.router import init_router
from routes.health import init_health

init_universe(_app_globals)
init_mirror(_app_globals)
init_dreaming(_app_globals)
init_evolution(_app_globals)
init_dharma(_app_globals)
init_founder_clones(_app_globals)
init_learning(_app_globals)
init_observability(_app_globals)
init_registry(_app_globals)
init_deploy(_app_globals)
init_push(_app_globals)
init_bugs(_app_globals)
init_clones(_app_globals)
init_offline(_app_globals)
init_override(_app_globals)
init_router(_app_globals)
init_health(_app_globals)
```

**Verification**: Run `python -c "from app import _lazy_register_routes; print('OK')"` — no import errors.

---

## Step 2: Create `soulKeyAPI` in Frontend API Layer

**File**: [`frontend/src/api/asimnexus.ts`](frontend/src/api/asimnexus.ts)

**Action**: Add a `soulKeyAPI` object with 8 endpoints matching [`routes/soul_key.py`](routes/soul_key.py):

| Endpoint | Method | Function |
|---|---|---|
| `/api/soul-key/create` | POST | `create(data)` |
| `/api/soul-key/{citizen_id}` | GET | `getSoulKey(citizenId)` |
| `/api/soul-key/{citizen_id}/verify` | POST | `verify(citizenId, data)` |
| `/api/soul-key/{citizen_id}/attest` | POST | `attest(citizenId, data)` |
| `/api/soul-key/{citizen_id}/event` | POST | `addEvent(citizenId, data)` |
| `/api/soul-key/{citizen_id}/lockout` | POST | `triggerLockout(citizenId, data)` |
| `/api/soul-key/{citizen_id}/lockout/{record_id}/resolve` | POST | `resolveLockout(citizenId, recordId)` |
| `/api/soul-key/stats` | GET | `getStats()` |

---

## Step 3: Create `founderClonesAPI` in Frontend API Layer

**File**: [`frontend/src/api/asimnexus.ts`](frontend/src/api/asimnexus.ts)

**Action**: Add a `founderClonesAPI` object with 5 endpoints matching [`routes/founder_clones.py`](routes/founder_clones.py):

| Endpoint | Method | Function |
|---|---|---|
| `/api/founder-clones/status` | GET | `getStatus()` |
| `/api/founder-clones/message` | POST | `sendMessage(data)` |
| `/api/founder-clones/consensus/propose` | POST | `proposeConsensus(data)` |
| `/api/founder-clones/consensus/vote` | POST | `castVote(data)` |
| `/api/founder-clones/consensus/history` | GET | `getConsensusHistory()` |

---

## Step 4: Create `universeAPI` in Frontend API Layer

**File**: [`frontend/src/api/asimnexus.ts`](frontend/src/api/asimnexus.ts)

**Action**: Add a `universeAPI` object with 12 endpoints matching [`routes/universe.py`](routes/universe.py):

| Endpoint | Method | Function |
|---|---|---|
| `/api/universe/create` | POST | `create(data)` |
| `/api/universe/status` | GET | `getStatus(userId)` |
| `/api/universe/lifecycle` | GET | `getLifecycle(userId)` |
| `/api/universe/layer/activate` | POST | `activateLayer(data)` |
| `/api/universe/state/update` | POST | `updateState(data)` |
| `/api/universe/activity/record` | POST | `recordActivity(data)` |
| `/api/universe/connection/add` | POST | `addConnection(data)` |
| `/api/universe/migrate` | POST | `migrate(data)` |
| `/api/universe/archive` | POST | `archive(data)` |
| `/api/universe/reactivate` | POST | `reactivate(data)` |
| `/api/universe/stats` | GET | `getStats()` |
| `/api/universe/privacy-score` | GET | `getPrivacyScore(userId)` |

---

## Step 5: Expand `dharmaAPI` — Add 6 Missing Endpoints

**File**: [`frontend/src/api/asimnexus.ts:672`](frontend/src/api/asimnexus.ts:672)

**Action**: Add 6 missing endpoints to existing `dharmaAPI`:

| Endpoint | Method | Function |
|---|---|---|
| `/api/dharma/veto/evaluate` | POST | `evaluateVeto(data)` |
| `/api/dharma/veto/history` | GET | `getVetoHistory()` |
| `/api/dharma/cultural/profile` | GET | `getCulturalProfile(userId)` |
| `/api/dharma/cultural/compile` | POST | `compileCultural(data)` |
| `/api/dharma/delta-t/status` | GET | `getDeltaTStatus()` |
| `/api/dharma/delta-t/simulate` | POST | `simulateDeltaT(data)` |

---

## Step 6: Fix `lifecycleAPI` Paths

**File**: [`frontend/src/api/asimnexus.ts:596`](frontend/src/api/asimnexus.ts:596)

**Action**: Change `lifecycleAPI` endpoint paths from `/api/universe/{userId}/...` to `/api/universe/...` with query parameters, matching [`routes/universe.py`](routes/universe.py).

Current (wrong):
```typescript
getLifecycle: (userId: string) => api.get(`/api/universe/${userId}/lifecycle`),
getStatus: (userId: string) => api.get(`/api/universe/${userId}/status`),
```

Fixed:
```typescript
getLifecycle: (userId: string) => api.get('/api/universe/lifecycle', { params: { user_id: userId } }),
getStatus: (userId: string) => api.get('/api/universe/status', { params: { user_id: userId } }),
```

---

## Step 7: Add Missing Barrel Exports

**File**: [`frontend/src/api/index.ts`](frontend/src/api/index.ts)

**Action**: Add exports for:
- `evolutionAPI` — already exists in asimnexus.ts, just needs barrel export
- `soulKeyAPI` — created in Step 2
- `founderClonesAPI` — created in Step 3
- `universeAPI` — created in Step 4

---

## Step 8: Refactor SoulKeyDashboard to Use Unified API

**File**: [`frontend/src/components/identity/SoulKeyDashboard.tsx`](frontend/src/components/identity/SoulKeyDashboard.tsx)

**Action**: Replace all raw `fetchJSON<T>()`/`postJSON<T>()` calls with `soulKeyAPI` calls from the unified API layer.

---

## Step 9: Refactor PersonalUniverseDashboard to Use Unified API

**File**: [`frontend/src/components/universe/PersonalUniverseDashboard.tsx`](frontend/src/components/universe/PersonalUniverseDashboard.tsx)

**Action**: Replace all raw `fetchJSON<T>()`/`postJSON<T>()` calls with `universeAPI` calls from the unified API layer.

---

## Step 10: Fix NetworkHub Tab Pattern for Consistency

**File**: [`frontend/src/components/pages/NetworkHub.tsx:141`](frontend/src/components/pages/NetworkHub.tsx:141)

**Action**: Change from `idx`-based matching `(_tab, idx)` to `switch(tab.id)` pattern, consistent with all other 7 hubs.

---

## Step 11: Run Integration Tests

**Action**: Run the full test suite to verify all changes work correctly:
```bash
cd c:/AsimNexus && python -m pytest tests/integration/ -v --timeout=300 2>&1
```

---

## Summary

| Step | Description | Files Changed | Risk |
|---|---|---|---|
| 1 | Add 17 missing `init_*()` calls in `app.py` | 1 | Medium — imports must exist |
| 2 | Create `soulKeyAPI` | 1 | Low — new code |
| 3 | Create `founderClonesAPI` | 1 | Low — new code |
| 4 | Create `universeAPI` | 1 | Low — new code |
| 5 | Expand `dharmaAPI` | 1 | Low — adding to existing |
| 6 | Fix `lifecycleAPI` paths | 1 | Medium — changes existing paths |
| 7 | Add barrel exports | 1 | Low — adding exports |
| 8 | Refactor SoulKeyDashboard | 1 | Medium — rewrites API calls |
| 9 | Refactor PersonalUniverseDashboard | 1 | Medium — rewrites API calls |
| 10 | Fix NetworkHub tab pattern | 1 | Low — cosmetic consistency |
| 11 | Run integration tests | 0 | Verification only |

**Total: 10 files modified, 1 verification step**
