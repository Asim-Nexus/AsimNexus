# Phase: Next Integration — Connect Remaining Disconnected Components

## Summary
After completing the 16-step Deep Integration phase, the following disconnections remain. This plan addresses them in 3 logical phases.

---

## Phase A: Core Package Wiring (4 steps)

### A1. Add missing subpackages to `core/__init__.py` `_SUBPACKAGES` dict
**Files to modify:** [`core/__init__.py`](core/__init__.py)
- Add 7 missing subpackages: `api`, `api_endpoints`, `asim_brain`, `data`, `dharma`, `founder_clones`, `integration`
- Each maps to `"core.<name>"` for lazy loading
- Update `__all__` and `__dir__()` accordingly

### A2. Fill `core/api/__init__.py` with proper exports
**Files to modify:** [`core/api/__init__.py`](core/api/__init__.py)
- Currently just docstring `"""AsimNexus Api module."""`
- Export: `CoreKernelAPI`, `GovRoutes`, `RealTimeAPI`, `WSRoutes` (or whatever the classes are)
- Add `__all__`

### A3. Fill `core/founder_clones/__init__.py` with proper exports
**Files to modify:** [`core/founder_clones/__init__.py`](core/founder_clones/__init__.py)
- Currently just docstring
- Export: `FounderCloneSystem`, `WorldClones` (or whatever the classes are)
- Add `__all__`

### A4. Fill `core/data/__init__.py` with proper exports
**Files to modify:** [`core/data/__init__.py`](core/data/__init__.py)
- Currently just docstring
- Check what modules exist in `core/data/` and export them
- Add `__all__`

---

## Phase B: Frontend Hub Wiring (5 steps)

### B1. Add SoulKeyDashboard tab to IdentityHub
**Files to modify:** [`frontend/src/components/pages/IdentityHub.tsx`](frontend/src/components/pages/IdentityHub.tsx)
- Import `SoulKeyDashboard` from `'../identity/SoulKeyDashboard'`
- Add tab: `{ id: 'soul-key', label: 'Soul Key', icon: '🔑', desc: 'Soul Key Protocol' }`
- Add case `'soul-key'` → `<SoulKeyDashboard />`

### B2. Add SelfAwarenessHub + MirrorEvolutionHub tabs to AIHub
**Files to modify:** [`frontend/src/components/pages/AIHub.tsx`](frontend/src/components/pages/AIHub.tsx)
- Import `SelfAwarenessHub` from `'../self-awareness/SelfAwarenessHub'`
- Import `MirrorEvolutionHub` from `'../mirror/MirrorEvolutionHub'`
- Add tabs: `self-awareness` and `mirror`
- Add cases for both

### B3. Add PersonalUniverse + MirrorEvolutionHub tabs to LifeHub
**Files to modify:** [`frontend/src/components/pages/LifeHub.tsx`](frontend/src/components/pages/LifeHub.tsx)
- Currently only has 1 tab (journey) — very sparse
- Import `MirrorEvolutionHub` from `'../mirror/MirrorEvolutionHub'`
- Add tabs: `universe` (PersonalUniverse), `mirror` (MirrorEvolutionHub)
- Need to create a `PersonalUniverseDashboard` component or use the existing Universe API routes

### B4. Add Dharma/Veto tab to GovernanceHub
**Files to modify:** [`frontend/src/components/pages/GovernanceHub.tsx`](frontend/src/components/pages/GovernanceHub.tsx)
- Add tab for Dharma/Veto constitutional oversight
- Create or import a `DharmaVetoPanel` component
- Wire to `/api/dharma/*` routes (need to create these routes first — see C1)

### B5. Add Universe tab to NetworkHub
**Files to modify:** [`frontend/src/components/pages/NetworkHub.tsx`](frontend/src/components/pages/NetworkHub.tsx)
- Add tab for PersonalUniverse
- Import or create a `PersonalUniversePanel` component
- Wire to `/api/universe/*` routes (already exist from Step 5)

---

## Phase C: New REST API Routes (2 steps)

### C1. Create Dharma/Veto REST API routes
**Files to create:** [`routes/dharma.py`](routes/dharma.py)
- `GET /api/dharma/status` — Dharma system health
- `POST /api/dharma/veto/evaluate` — Evaluate a veto action
- `GET /api/dharma/veto/history` — Veto history
- `GET /api/dharma/cultural/profile` — Cultural profile
- `POST /api/dharma/cultural/compile` — Compile cultural rules
- `GET /api/dharma/delta-t/status` — Delta-T engine status
- `POST /api/dharma/delta-t/simulate` — Run PoS simulator
**Files to modify:** [`routes/__init__.py`](routes/__init__.py)
- Register `dharma_router`

### C2. Create FounderClones REST API routes
**Files to create:** [`routes/founder_clones.py`](routes/founder_clones.py)
- `GET /api/founder-clones/list` — List all clones
- `POST /api/founder-clones/spawn` — Spawn a new clone
- `POST /api/founder-clones/{clone_id}/assign-task` — Assign task to clone
- `GET /api/founder-clones/{clone_id}/status` — Clone status
- `POST /api/founder-clones/{clone_id}/terminate` — Terminate clone
**Files to modify:** [`routes/__init__.py`](routes/__init__.py)
- Register `founder_clones_router`

---

## Phase D: Frontend Components (2 steps)

### D1. Create PersonalUniverseDashboard frontend component
**Files to create:** [`frontend/src/components/universe/PersonalUniverseDashboard.tsx`](frontend/src/components/universe/PersonalUniverseDashboard.tsx)
- Fetches from `/api/universe/status`, `/api/universe/lifecycle`, `/api/universe/stats`
- Shows: current layer, user state, lifecycle stage, privacy score
- Actions: activate layer, update state, record activity, add connection, migrate, archive

### D2. Create DharmaVetoPanel frontend component
**Files to create:** [`frontend/src/components/governance/DharmaVetoPanel.tsx`](frontend/src/components/governance/DharmaVetoPanel.tsx)
- Fetches from `/api/dharma/status`, `/api/dharma/veto/history`
- Shows: veto history, cultural profile, Delta-T status
- Actions: evaluate veto, compile cultural rules, run PoS simulator

---

## Execution Order

```
Phase A (Core) → Phase C (Routes) → Phase D (Components) → Phase B (Hub Wiring)
```

**Rationale:** Core must be wired first so routes can import from it. Routes must exist before frontend components can call them. Components must exist before hubs can wire them.

---

## Files Summary

| # | Action | File | Type |
|---|--------|------|------|
| A1 | Modify | `core/__init__.py` | Add 7 missing subpackages |
| A2 | Modify | `core/api/__init__.py` | Add proper exports |
| A3 | Modify | `core/founder_clones/__init__.py` | Add proper exports |
| A4 | Modify | `core/data/__init__.py` | Add proper exports |
| C1 | Create | `routes/dharma.py` | 7 Dharma/Veto routes |
| C1 | Modify | `routes/__init__.py` | Register dharma router |
| C2 | Create | `routes/founder_clones.py` | 5 FounderClone routes |
| C2 | Modify | `routes/__init__.py` | Register founder_clones router |
| D1 | Create | `frontend/src/components/universe/PersonalUniverseDashboard.tsx` | Universe UI |
| D2 | Create | `frontend/src/components/governance/DharmaVetoPanel.tsx` | Dharma/Veto UI |
| B1 | Modify | `frontend/src/components/pages/IdentityHub.tsx` | Add SoulKey tab |
| B2 | Modify | `frontend/src/components/pages/AIHub.tsx` | Add SelfAwareness + Mirror tabs |
| B3 | Modify | `frontend/src/components/pages/LifeHub.tsx` | Add Universe + Mirror tabs |
| B4 | Modify | `frontend/src/components/pages/GovernanceHub.tsx` | Add Dharma/Veto tab |
| B5 | Modify | `frontend/src/components/pages/NetworkHub.tsx` | Add Universe tab |

**Total: 15 files (8 modified, 4 created, 3 filled)**
