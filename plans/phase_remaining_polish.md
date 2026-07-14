# Phase: Remaining Polish — Final Cleanup & Hardening

## Objective
After completing Phase Final Unification (all 11 steps), this plan addresses the remaining gaps that were identified in earlier plans but not yet implemented. These are small, focused tasks to harden the system.

---

## Step 1: Fill `core/data/__init__.py` with Proper Exports

**File**: [`core/data/__init__.py`](core/data/__init__.py)

**Current state**: Only `__all__ = []` — completely empty.

**Action**: Check what modules exist in `core/data/` and add proper re-exports. The directory currently only has `__init__.py` itself, so this may need a module to be created or the file can be left as-is if no data modules exist yet.

**Status**: ⬜ Pending — needs investigation of what data modules exist.

---

## Step 2: Add Missing Gap Detectors to `GapAnalyzer`

**File**: [`core/self_awareness/gap_analyzer.py`](core/self_awareness/gap_analyzer.py)

**Current state**: Has basic gap detection but missing:
- `_detect_missing_init_exports()` — checks if subpackages have proper `__all__`
- `_detect_missing_api_routes()` — checks if core modules have corresponding route files
- `_detect_missing_frontend_components()` — checks if backend modules have frontend equivalents

**Action**: Add these 3 gap detector methods to make the self-awareness system more comprehensive.

**Status**: ⬜ Pending

---

## Step 3: Create Integration Tests for Self-Building Loop

**File**: [`tests/integration/test_self_building_loop.py`](tests/integration/test_self_building_loop.py)

**Action**: Create integration tests that verify:
1. Full scan → analyze → plan → build → test → verify cycle
2. Self-healing on test regression
3. EvolutionBridge wiring (EvolutionEngine → SelfBuilder)
4. MirrorModule → EvolutionBridge → SelfKnowledge flow
5. DreamingEngine → EvolutionBridge → SelfKnowledge flow
6. GapAnalyzer gap detection accuracy

**Status**: ⬜ Pending

---

## Step 4: Create Integration Tests for Soul Key Protocol

**File**: [`tests/integration/test_soul_key.py`](tests/integration/test_soul_key.py)

**Action**: Create integration tests that verify:
1. Create Soul Key with citizen data
2. Add life events (all 12 types)
3. Verify Soul Key integrity (Merkle root)
4. Hardware attestation (trusted vs untrusted)
5. Trigger lockout (all 3 stages)
6. Resolve lockout
7. Get stats
8. Persistence (save/load)

**Status**: ⬜ Pending

---

## Step 5: Wire DreamingEngine → AutoBuilder Directly

**File**: [`app.py`](app.py) — lifespan section

**Action**: After DreamingEngine bridge wiring in lifespan, also feed dream lessons as AutoBuilder actions:
```python
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

**Status**: ⬜ Pending

---

## Step 6: Wire MirrorModule Contradictions → AutoBuilder Directly

**File**: [`app.py`](app.py) — lifespan section

**Action**: After MirrorModule bridge wiring in lifespan, feed contradictions as AutoBuilder `resolve_todos` actions.

**Status**: ⬜ Pending

---

## Step 7: Run Full Test Suite and Verify

**Action**:
1. Run `python -m pytest tests/unit/ -q --tb=short` — all unit tests must pass
2. Run `python -m pytest tests/integration/ -q --tb=short` — all integration tests must pass
3. Run `python -m pytest tests/smoke/ -q --tb=short` — smoke tests must pass
4. Verify `python -c "from core import self_awareness, mesh, evolution, dreaming, mirror"` works
5. Verify `python -c "from core.security import SoulKeyProtocol, get_soul_key_protocol"` works

**Status**: ⬜ Pending

---

## Execution Order

```
Step 1 (data/__init__.py) → Step 2 (gap detectors) → Step 5+6 (AutoBuilder wiring) → Step 3+4 (tests) → Step 7 (verify)
```

## Files Summary

| # | Action | File | Description |
|---|--------|------|-------------|
| 1 | Modify | `core/data/__init__.py` | Add proper exports |
| 2 | Modify | `core/self_awareness/gap_analyzer.py` | Add 3 new gap detectors |
| 3 | Create | `tests/integration/test_self_building_loop.py` | Self-building integration tests |
| 4 | Create | `tests/integration/test_soul_key.py` | Soul Key integration tests |
| 5 | Modify | `app.py` | Wire DreamingEngine → AutoBuilder |
| 6 | Modify | `app.py` | Wire MirrorModule → AutoBuilder |
| 7 | Run | Full test suite | Verify all changes |
