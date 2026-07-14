# Phase: Deep Integration — Make AsimNexus One Unified System

## Goal
Connect every disconnected component, fill every `__init__.py` gap, add missing REST APIs, add missing frontend UIs, and make the entire system self-aware, self-building, and self-healing from every angle.

---

## Step 1: Fix `core/__init__.py` — Add Lazy Loading for All Subpackages

**Problem**: `core/__init__.py` only exports `orchestrator` and `security`. 20+ subpackages must be imported directly.

**Action**: Add `__getattr__` entries for all major subpackages:
- `self_awareness`, `mesh`, `evolution`, `dreaming`, `mirror`, `dharma_chakra`
- `federation`, `governance`, `economy`, `finance`, `agents`, `identity`
- `knowledge`, `mcp`, `policy`, `risk_management`, `routing`, `sandbox`
- `sync`, `universal`, `universe`, `world`, `depin`, `nepal`, `compliance`
- `consensus`, `analytics`, `gateway`, `kernel`, `lifecycle`, `network`

**File**: [`core/__init__.py`](core/__init__.py)

---

## Step 2: Fill Empty `__init__.py` Files with Proper Exports

**Problem**: Several subpackages have empty `__init__.py` files (only docstrings):
- [`core/mirror/__init__.py`](core/mirror/__init__.py) — empty
- [`core/dreaming/__init__.py`](core/dreaming/__init__.py) — empty
- [`core/evolution/__init__.py`](core/evolution/__init__.py) — empty
- [`core/universe/__init__.py`](core/universe/__init__.py) — empty
- [`core/mcp/__init__.py`](core/mcp/__init__.py) — empty

**Action**: Add proper re-exports with `__all__` and singleton getters for each.

**Example for `core/mirror/__init__.py`**:
```python
from .mirror_module import MirrorModule, MirrorReflection, get_mirror_module
from .consciousness import ConsciousnessLayer, Thought, ThoughtType
from .lora_engine import MirrorLoRA
from .dreaming_engine import DreamingEngine, Dream, DreamType

__all__ = [
    "MirrorModule", "MirrorReflection", "get_mirror_module",
    "ConsciousnessLayer", "Thought", "ThoughtType",
    "MirrorLoRA", "DreamingEngine", "Dream", "DreamType",
]
```

---

## Step 3: Add `get_gap_analyzer()` Singleton to Self-Awareness

**Problem**: [`core/self_awareness/__init__.py`](core/self_awareness/__init__.py) exports `GapAnalyzer` class but has no `get_gap_analyzer()` singleton getter.

**Action**: Add `get_gap_analyzer()` function that creates/returns a singleton `GapAnalyzer` instance.

---

## Step 4: Enhance GapAnalyzer — Add Missing Detection Rules

**Problem**: [`core/self_awareness/gap_analyzer.py`](core/self_awareness/gap_analyzer.py) doesn't detect:
- Missing `__init__.py` exports
- Missing REST API routes for core modules
- Missing frontend components
- Disconnected subpackages (not in `core/__init__.py`)

**Action**: Add 3 new gap detectors:
1. `_detect_missing_init_exports()` — checks if subpackages have proper `__all__`
2. `_detect_missing_api_routes()` — checks if core modules have corresponding route files
3. `_detect_missing_frontend_components()` — checks if backend modules have frontend equivalents

---

## Step 5: Add REST API Routes for Missing Core Modules

**Problem**: No REST API endpoints exist for:
- MirrorModule (reflections, consciousness)
- DreamingEngine (dream cycles, lessons)
- EvolutionEngine (suggestions, evolution history)
- PersonalUniverse (user universes, layers)

**Action**: Create route files:
- [`routes/mirror.py`](routes/mirror.py) — Mirror reflection CRUD, consciousness state
- [`routes/dreaming.py`](routes/dreaming.py) — Dream cycle status, lessons, patterns
- [`routes/evolution.py`](routes/evolution.py) — Evolution suggestions, history, stats
- [`routes/universe.py`](routes/universe.py) — Personal universe CRUD, layer management

**Register** all 4 in [`routes/__init__.py`](routes/__init__.py).

---

## Step 6: Add Self-Awareness Health Endpoint

**Problem**: No dedicated health check for the self-awareness system.

**Action**: Add `GET /api/self/health` endpoint in [`routes/self_awareness.py`](routes/self_awareness.py) that returns:
- Scanner status (last scan time, modules scanned)
- Knowledge status (total modules, routes, issues)
- Builder status (total actions, success rate)
- AutoBuilder status (last cycle, current state)
- Bridge status (total actions by source)
- GapAnalyzer status (last analysis)

---

## Step 7: Add Integration Tests for Self-Building Loop

**Problem**: No integration tests verify the complete self-building cycle.

**Action**: Create [`tests/integration/test_self_building_loop.py`](tests/integration/test_self_building_loop.py) with tests for:
1. Full scan → analyze → plan → build → test → verify cycle
2. Self-healing on test regression
3. Auto-deploy to staging
4. EvolutionBridge wiring (EvolutionEngine → SelfBuilder)
5. MirrorModule → EvolutionBridge → SelfKnowledge flow
6. DreamingEngine → EvolutionBridge → SelfKnowledge flow
7. GapAnalyzer gap detection accuracy
8. Soul Key protocol CRUD operations
9. Soul Key hardware attestation + lockout

---

## Step 8: Add Integration Tests for Soul Key Protocol

**Problem**: No integration tests for Soul Key.

**Action**: Create [`tests/integration/test_soul_key.py`](tests/integration/test_soul_key.py) with tests for:
1. Create Soul Key with citizen data
2. Add life events (all 12 types)
3. Verify Soul Key integrity (Merkle root)
4. Hardware attestation (trusted vs untrusted)
5. Trigger lockout (all 3 stages)
6. Resolve lockout
7. Get stats
8. Persistence (save/load)

---

## Step 9: Add Frontend UI for Self-Awareness Dashboard

**Problem**: No frontend UI for the self-awareness system.

**Action**: Create React components:
- [`frontend/src/components/self-awareness/SelfAwarenessDashboard.tsx`](frontend/src/components/self-awareness/SelfAwarenessDashboard.tsx) — Main dashboard
- [`frontend/src/components/self-awareness/ScannerStatus.tsx`](frontend/src/components/self-awareness/ScannerStatus.tsx) — Scanner status card
- [`frontend/src/components/self-awareness/KnowledgeGraph.tsx`](frontend/src/components/self-awareness/KnowledgeGraph.tsx) — Module dependency graph
- [`frontend/src/components/self-awareness/BuildHistory.tsx`](frontend/src/components/self-awareness/BuildHistory.tsx) — AutoBuilder cycle history
- [`frontend/src/components/self-awareness/GapAnalysis.tsx`](frontend/src/components/self-awareness/GapAnalysis.tsx) — Gap analysis results
- [`frontend/src/components/self-awareness/EvolutionBridge.tsx`](frontend/src/components/self-awareness/EvolutionBridge.tsx) — Bridge action log
- [`frontend/src/components/self-awareness/DeployStatus.tsx`](frontend/src/components/self-awareness/DeployStatus.tsx) — Deployment status

**Add tab** to [`NepalHub.tsx`](frontend/src/components/pages/NepalHub.tsx) or create new page.

---

## Step 10: Add Frontend UI for Soul Key Protocol

**Problem**: No frontend UI for Soul Key.

**Action**: Create React components:
- [`frontend/src/components/security/SoulKeyDashboard.tsx`](frontend/src/components/security/SoulKeyDashboard.tsx) — Main Soul Key dashboard
- [`frontend/src/components/security/SoulKeyCreate.tsx`](frontend/src/components/security/SoulKeyCreate.tsx) — Create Soul Key form
- [`frontend/src/components/security/SoulKeyEvents.tsx`](frontend/src/components/security/SoulKeyEvents.tsx) — Life events list
- [`frontend/src/components/security/SoulKeyAttestation.tsx`](frontend/src/components/security/SoulKeyAttestation.tsx) — Device attestation UI
- [`frontend/src/components/security/SoulKeyLockout.tsx`](frontend/src/components/security/SoulKeyLockout.tsx) — Lockout history

---

## Step 11: Add Frontend UI for Mirror/Dreaming/Evolution

**Problem**: No frontend UI for Mirror, Dreaming, or Evolution systems.

**Action**: Create React components:
- [`frontend/src/components/mirror/MirrorDashboard.tsx`](frontend/src/components/mirror/MirrorDashboard.tsx) — Mirror reflections, consciousness
- [`frontend/src/components/dreaming/DreamingDashboard.tsx`](frontend/src/components/dreaming/DreamingDashboard.tsx) — Dream cycles, lessons, patterns
- [`frontend/src/components/evolution/EvolutionDashboard.tsx`](frontend/src/components/evolution/EvolutionDashboard.tsx) — Evolution suggestions, history

---

## Step 12: Wire DreamingEngine → AutoBuilder Directly

**Problem**: DreamingEngine lessons go to EvolutionBridge → SelfKnowledge, but not to AutoBuilder for action.

**Action**: In [`app.py`](app.py) lifespan, after DreamingEngine bridge wiring, also feed dream lessons as AutoBuilder actions:
```python
# After bridge wiring, also feed to AutoBuilder
from core.self_awareness import get_auto_builder
auto_builder = get_auto_builder()
for lesson in lessons:
    topic = lesson.get("topic", "")
    if topic in ["code_improvement", "architecture", "refactoring"]:
        auto_builder._pending_bridge_actions.append({
            "type": "generate_test",
            "module": lesson.get("target_module", "core"),
            "source": "dream_lesson",
        })
```

---

## Step 13: Wire MirrorModule Contradictions → AutoBuilder Directly

**Problem**: Mirror contradictions go to EvolutionBridge → SelfKnowledge issues, but not to AutoBuilder for resolution.

**Action**: In [`app.py`](app.py) lifespan, after MirrorModule bridge wiring, feed contradictions as AutoBuilder `resolve_todos` actions.

---

## Step 14: Add Scheduled Mirror Reflection Processing

**Problem**: MirrorModule reflections are only processed once at startup.

**Action**: Add a background task in [`app.py`](app.py) lifespan that periodically:
1. Queries MirrorModule for new reflections
2. Feeds them through EvolutionBridge
3. Feeds contradictions to AutoBuilder

---

## Step 15: Add Scheduled EvolutionEngine Suggestion Processing

**Problem**: EvolutionEngine suggestions are only processed once at startup.

**Action**: Add a background task in [`app.py`](app.py) lifespan that periodically:
1. Queries EvolutionEngine for new approved suggestions
2. Feeds them through EvolutionBridge
3. Feeds code_improvement suggestions to AutoBuilder

---

## Step 16: Run Full Test Suite and Verify

**Problem**: Need to verify all changes don't break existing functionality.

**Action**:
1. Run `python -m pytest tests/unit/ -q --tb=short` — all unit tests must pass
2. Run `python -m pytest tests/integration/ -q --tb=short` — all integration tests must pass
3. Run `python -m pytest tests/real/test_self_awareness.py -q --tb=short` — self-awareness tests must pass
4. Run `python -m pytest tests/smoke/ -q --tb=short` — smoke tests must pass (except 401 auth errors)
5. Verify `python -c "from core import self_awareness, mesh, evolution, dreaming, mirror"` works
6. Verify `python -c "from core.security import SoulKeyProtocol, get_soul_key_protocol"` works

---

## Summary of Files to Create/Modify

| # | File | Action | Description |
|---|------|--------|-------------|
| 1 | `core/__init__.py` | **Modify** | Add lazy loading for all subpackages |
| 2 | `core/mirror/__init__.py` | **Modify** | Add proper exports |
| 3 | `core/dreaming/__init__.py` | **Modify** | Add proper exports |
| 4 | `core/evolution/__init__.py` | **Modify** | Add proper exports |
| 5 | `core/universe/__init__.py` | **Modify** | Add proper exports |
| 6 | `core/mcp/__init__.py` | **Modify** | Add proper exports |
| 7 | `core/self_awareness/__init__.py` | **Modify** | Add `get_gap_analyzer()` |
| 8 | `core/self_awareness/gap_analyzer.py` | **Modify** | Add 3 new gap detectors |
| 9 | `routes/mirror.py` | **Create** | Mirror REST API |
| 10 | `routes/dreaming.py` | **Create** | Dreaming REST API |
| 11 | `routes/evolution.py` | **Create** | Evolution REST API |
| 12 | `routes/universe.py` | **Create** | Universe REST API |
| 13 | `routes/__init__.py` | **Modify** | Register 4 new route modules |
| 14 | `routes/self_awareness.py` | **Modify** | Add health endpoint |
| 15 | `tests/integration/test_self_building_loop.py` | **Create** | Self-building integration tests |
| 16 | `tests/integration/test_soul_key.py` | **Create** | Soul Key integration tests |
| 17 | `frontend/src/components/self-awareness/*.tsx` | **Create** | 7 self-awareness UI components |
| 18 | `frontend/src/components/security/SoulKey*.tsx` | **Create** | 5 Soul Key UI components |
| 19 | `frontend/src/components/mirror/MirrorDashboard.tsx` | **Create** | Mirror UI |
| 20 | `frontend/src/components/dreaming/DreamingDashboard.tsx` | **Create** | Dreaming UI |
| 21 | `frontend/src/components/evolution/EvolutionDashboard.tsx` | **Create** | Evolution UI |
| 22 | `app.py` | **Modify** | Add 3 background tasks + direct AutoBuilder wiring |
