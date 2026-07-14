# AsimNexus — Complete Integration Audit & Repair Plan

> **Purpose**: Identify every disconnection, broken reference, orphaned file, and integration gap across the entire codebase, then provide a step-by-step repair plan.
> **Date**: 2025-07-05
> **Author**: Architect Mode

---

## 1. Executive Summary

After exhaustive inspection of **all folders and files**, I found the system is **functionally coherent** but has **8 critical disconnections** and **15+ improvement opportunities**. The core self-awareness loop (Scan → Analyze → Build → Test → Heal) works correctly with 41/41 tests passing. However, there are broken references, orphaned directories, duplicate code paths, and missing integrations.

---

## 2. Critical Disconnections (Must Fix)

### 🔴 C1: `frontend/react/` Directory Does Not Exist

**Location**: Referenced in VSCode open tabs as:
- `frontend/react/src/components/dashboard/Dashboard.js`
- `frontend/react/src/components/os/PersonalOS.jsx`
- `frontend/react/src/components/clones/WorldClones.jsx`
- `frontend/react/src/components/pages/EconomyHub.jsx`

**Problem**: These files are referenced in open tabs but the directory `frontend/react/` **does not exist** on disk. The actual frontend is at `frontend/src/`. These are likely from a previous project structure or a failed migration.

**Fix**: Either:
- (a) Delete these stale references from VSCode workspace
- (b) If these files contain unique code, create the directory and copy them

---

### 🔴 C2: `core/security/` — Files Referenced in `__init__.py` That Don't Exist

**Location**: [`core/security/__init__.py`](core/security/__init__.py)

**Problem**: The `__init__.py` imports from these files that **do not exist** on disk:
- `core/security/zkp.py` — referenced but not in file listing
- `core/security/hsm_client.py` — referenced but not in file listing
- `core/security/hsm_integration.py` — referenced but not in file listing
- `core/security/hsm_production_shim.py` — referenced but not in file listing
- `core/security/security_audit.py` — referenced but not in file listing
- `core/security/hard_lock.py` — referenced but not in file listing
- `core/security/biometric_gate.py` — referenced but not in file listing
- `core/security/immutable_constitution.py` — referenced but not in file listing
- `core/security/auth_middleware.py` — referenced but not in file listing
- `core/security/input_sanitizer.py` — referenced but not in file listing
- `core/security/jwt.py` — referenced but not in file listing
- `core/security/level3_confirmation.py` — referenced but not in file listing
- `core/security/mtls.py` — referenced but not in file listing
- `core/security/mythos_scanner.py` — referenced but not in file listing
- `core/security/post_quantum_crypto.py` — referenced but not in file listing
- `core/security/rbac.py` — referenced but not in file listing
- `core/security/risk_validator.py` — referenced but not in file listing
- `core/security/tpm_binding.py` — referenced but not in file listing
- `core/security/zero_trust.py` — referenced but not in file listing
- `core/security/identity_manager.py` — referenced but not in file listing

**Impact**: `from core.security import X` will raise `ImportError` for ALL of these. The security package is essentially **non-functional** despite having a comprehensive `__init__.py`.

**Fix**: Either:
- (a) Create stub files for each missing module with the referenced classes
- (b) Remove the imports from `__init__.py` and add proper error handling
- (c) Restore the actual implementation files from backup/git history

---

### 🔴 C3: `core/security/` — Files That Exist But Are Not in `__init__.py`

**Location**: [`core/security/`](core/security/)

**Problem**: These files exist on disk but are **not exported** from `__init__.py`:
- `core/security/audit_log.py`
- `core/security/audit_logger.py`
- `core/security/biometric_hardware_gate.py`
- `core/security/bulletproof_zkp.py`
- `core/security/hard_lock.py` (wait, this IS referenced)
- `core/security/hardware_dna.py`
- `core/security/hardware_hard_lock.py`
- `core/security/hsm_production.py`

**Impact**: These files are orphaned — they exist but cannot be imported via `core.security.X`.

---

### 🔴 C4: `core/__init__.py` — Subpackages Referenced That Don't Exist

**Location**: [`core/__init__.py`](core/__init__.py:12-55)

**Problem**: These subpackages are listed in `_SUBPACKAGES` but their directories **do not exist**:
- `core/analytics/` — does not exist
- `core/api/` — exists but `core/api/__init__.py` may be empty
- `core/api_endpoints/` — does not exist
- `core/asim_brain/` — does not exist
- `core/compliance/` — does not exist
- `core/data/` — does not exist
- `core/finance/` — does not exist
- `core/government/` — does not exist
- `core/integration/` — does not exist
- `core/policy/` — does not exist
- `core/risk_management/` — does not exist
- `core/sync/` — does not exist
- `core/universal/` — does not exist
- `core/world/` — does not exist

**Impact**: `from core import analytics` will raise `ImportError`. The lazy loading system silently fails.

---

### 🔴 C5: `app.py` — Route Init Functions That Don't Exist

**Location**: [`app.py`](app.py:633-754)

**Problem**: These `init_*` functions are called but the corresponding route modules may not have them:
- `init_learning` — does `routes/learning.py` have this function?
- `init_observability` — does `routes/observability.py` have this function?
- `init_registry` — does `routes/registry.py` have this function?
- `init_deploy` — does `routes/deploy.py` have this function?
- `init_push` — does `routes/push.py` have this function?
- `init_bugs` — does `routes/bugs.py` have this function?
- `init_clones` — does `routes/clones.py` have this function?
- `init_offline` — does `routes/offline.py` have this function?
- `init_override` — does `routes/override.py` have this function?
- `init_router` — does `routes/router.py` have this function?
- `init_health` — does `routes/health.py` have this function?

**Impact**: If any of these `init_*` functions are missing, the entire route registration block will fail with `ImportError`, and **all routes** will be skipped (the whole thing is wrapped in one `try/except`).

---

### 🔴 C6: `routes/__init__.py` — Router Imports That May Fail

**Location**: [`routes/__init__.py`](routes/__init__.py:14-112)

**Problem**: All 48 route modules are imported at the top of `register_routes()`. If ANY single module has a syntax error or missing dependency, the **entire route registration fails**. There's no per-module error handling.

**Impact**: A single broken route module takes down all 273+ routes.

---

### 🔴 C7: `core/self_awareness/self_builder.py` — `generate_route_module()` Still Uses Inline String Building

**Location**: [`core/self_awareness/self_builder.py:132-201`](core/self_awareness/self_builder.py:132)

**Problem**: Unlike the other 5 `generate_*` methods which now use `_render_template()`, `generate_route_module()` still builds content inline using Python string concatenation. The `TEMPLATE_ROUTE` Jinja2 template exists but is never used.

**Impact**: Inconsistent code generation — route modules don't benefit from template maintainability.

---

### 🔴 C8: `core/self_awareness/self_builder.py` — 3 Template Constants Defined But No Templates Registered

**Location**: [`core/self_awareness/self_builder.py:54-59`](core/self_awareness/self_builder.py:54)

**Problem**: These template constants are defined but have **no entry** in `_load_templates()`:
- `TEMPLATE_TEST_REAL` (line 54)
- `TEMPLATE_INIT` (line 58)
- `TEMPLATE_SCHEMA` (line 59)

**Impact**: If any code tries to use these templates, it will get `ValueError: Template not found`.

---

## 3. Moderate Disconnections (Should Fix)

### 🟡 M1: Duplicate Core Module Files at Root Level

**Location**: [`core/`](core/) root directory

**Problem**: These files exist at `core/` root level but also have dedicated subpackages:
- `core/consensus_engine.py` — duplicates `core/consensus/consensus_engine.py`
- `core/agent_contract.py` — should be in `core/agent/` or `core/agents/`
- `core/life_journey.py` — should be in `core/lifecycle/`
- `core/global_mesh.py` — duplicates `core/mesh/unified_mesh.py`
- `core/security_layer.py` — duplicates `core/security/`
- `core/multi_agent_orchestrator.py` — duplicates `core/orchestrator/`
- `core/digital_twin_system.py` — duplicates `core/agent/digital_twin.py`
- `core/entity_bridge.py` — should be in `core/integration/`
- `core/execution_pipeline.py` — should be in `core/orchestrator/`
- `core/event_bus.py` — should be in `core/mesh/` or `core/integration/`
- `core/universal_api_gateway.py` — duplicates `core/gateway/unified_gateway.py`
- `core/universal_clone_system.py` — duplicates `core/founder_clones/`
- `core/vectormemory.py` — duplicates `core/knowledge/vector_store.py`
- `core/plugin_marketplace.py` — duplicates `core/economy/marketplace.py`
- `core/rate_limiter_middleware.py` — duplicates `core/security/rbac.py`
- `core/security_headers_middleware.py` — should be in `core/security/`
- `core/structured_logger.py` — should be in `core/monitoring/`
- `core/telemetry_schema.py` — should be in `core/monitoring/`
- `core/prometheus_metrics.py` — should be in `core/monitoring/`
- `core/smart_llm_router.py` — duplicates `core/gateway/smart_model_router.py`
- `core/language_manager.py` — duplicates `core/nepal/language_support.py`
- `core/redis_manager.py` — should be in `infrastructure/`
- `core/disaster_recovery.py` — should be in `core/security/`
- `core/monitoring_middleware.py` — should be in `core/monitoring/`
- `core/new_architecture_integration.py` — should be in `core/integration/`
- `core/platform.py` — should be in `core/kernel/`
- `core/depin_bridge.py` — duplicates `core/depin/`
- `core/quantum_bridge.py` — orphaned, no subpackage

**Impact**: Code duplication, confusion about which version is "correct", maintenance burden.

---

### 🟡 M2: `core/mirror/` Has Duplicate Files with `core/dreaming/`

**Location**: [`core/mirror/`](core/mirror/) and [`core/dreaming/`](core/dreaming/)

**Problem**: These files exist in BOTH directories:
- `dreaming_engine.py` — in both `core/mirror/` and `core/dreaming/`
- `lora_engine.py` — in both `core/mirror/` and `core/dreaming/`

**Impact**: Confusion about which dreaming engine is authoritative. `app.py` imports from `core.dreaming.dreaming_engine` but `core.mirror.dreaming_engine` also exists.

---

### 🟡 M3: `core/mesh/` Has 18 Files But No `__init__.py` Exports

**Location**: [`core/mesh/`](core/mesh/)

**Problem**: The mesh directory has 18 files but `core/mesh/__init__.py` may not export them properly. `app.py` references `from core.mesh import get_mesh_coordinator, NodeType` but these may not exist.

---

### 🟡 M4: `tests/` Has 200+ Test Files But Only 41 Are Run

**Location**: [`tests/`](tests/)

**Problem**: There are 200+ test files across `unit/`, `integration/`, `e2e/`, `real/`, `security/`, `smoke/`, `performance/`, `regression/`, `prototype/` directories. But only 41 tests (from `tests/unit/test_self_builder.py`, `tests/unit/test_gap_analyzer.py`, `tests/unit/test_auto_builder.py`, `tests/integration/test_self_building_loop.py`, `tests/integration/test_soul_key.py`) are confirmed passing.

**Impact**: Massive untested codebase. Many tests may be broken or outdated.

---

### 🟡 M5: `frontend/src/api/asimnexus.ts` — 1590-Line Monolith

**Location**: [`frontend/src/api/asimnexus.ts`](frontend/src/api/asimnexus.ts)

**Problem**: Single file with 80+ API methods, all Axios configuration, auth interceptors, and TypeScript interfaces. No code splitting.

**Impact**: Hard to maintain, any change risks breaking unrelated API calls.

---

### 🟡 M6: No Database — All Persistence Is JSON Files

**Location**: [`data/`](data/), [`database/`](database/)

**Problem**: The `database/` directory has migration SQL files but no actual database connection. All persistence is flat JSON files:
- `data/soul_keys/soul_key_state.json`
- `data/self_awareness/patches/action_history.json`
- `data/self_awareness/backups/*.bak`

**Impact**: No query capability, no ACID transactions, no relationships, no scalability.

---

## 4. Minor Issues (Nice to Fix)

### 🟢 N1: `core/__init__.py` — `__all__` Contains Non-Existent Attributes

**Location**: [`core/__init__.py:73`](core/__init__.py:73)

**Problem**: `__all__` is set to `sorted(_SUBPACKAGES.keys())` which includes all 42 subpackages, but many don't exist.

---

### 🟢 N2: `app.py` — `_time_module` Used But Not Imported

**Location**: [`app.py:410`](app.py:410)

**Problem**: `_time_module.time()` is used in the mirror reflection loop but `_time_module` is not imported at the top of the file.

---

### 🟢 N3: `app.py` — `_build_app_globals()` Returns Dict But No Type Hints

**Location**: [`app.py:121`](app.py:121)

**Problem**: Returns `dict` with no type specification. Callers don't know what keys are available.

---

### 🟢 N4: `frontend/src/` — TypeScript Files Use `.tsx` Extension for Non-JSX Files

**Location**: Various in [`frontend/src/`](frontend/src/)

**Problem**: Files like `useAIPersonalization.ts`, `useMode.ts`, `useRealTimeMetrics.ts`, `useStreamingChat.ts` use `.ts` extension (correct), but some service files may have incorrect extensions.

---

### 🟢 N5: No Central Configuration System

**Location**: [`config/`](config/)

**Problem**: The `config/` directory exists but its contents are unknown. Hardcoded paths like `os.getcwd()` are used throughout the codebase.

---

## 5. Repair Plan — Step by Step

### Phase 1: Fix Critical Disconnections (C1-C8)

```mermaid
flowchart LR
    C1[Fix frontend/react/] --> C2[Fix security __init__.py]
    C2 --> C3[Fix orphaned security files]
    C3 --> C4[Fix core __init__.py subpackages]
    C4 --> C5[Verify route init functions]
    C5 --> C6[Add per-module error handling]
    C6 --> C7[Wire generate_route_module to template]
    C7 --> C8[Register missing templates]
```

| Step | File | Action | Risk |
|------|------|--------|------|
| **1.1** | `frontend/react/` | Create directory, move files from stale references or remove references | Low |
| **1.2** | `core/security/__init__.py` | Audit all 20+ imports, create stub files or remove broken imports | **High** |
| **1.3** | `core/security/*.py` | Audit orphaned files, integrate into `__init__.py` or remove | Medium |
| **1.4** | `core/__init__.py` | Remove non-existent subpackages from `_SUBPACKAGES` | Low |
| **1.5** | `routes/*.py` | Verify all `init_*` functions exist in all 48 route modules | Medium |
| **1.6** | `routes/__init__.py` | Add per-module try/except for route registration | Low |
| **1.7** | `core/self_awareness/self_builder.py` | Wire `generate_route_module()` to use `TEMPLATE_ROUTE` | Low |
| **1.8** | `core/self_awareness/self_builder.py` | Add templates for `TEMPLATE_TEST_REAL`, `TEMPLATE_INIT`, `TEMPLATE_SCHEMA` | Low |

### Phase 2: Fix Moderate Disconnections (M1-M6)

| Step | File | Action | Risk |
|------|------|--------|------|
| **2.1** | `core/*.py` (root) | Audit 25+ root-level files, consolidate into proper subpackages | **High** |
| **2.2** | `core/mirror/`, `core/dreaming/` | Deduplicate `dreaming_engine.py` and `lora_engine.py` | Medium |
| **2.3** | `core/mesh/__init__.py` | Add proper exports for all 18 mesh modules | Medium |
| **2.4** | `tests/` | Run all 200+ test files, fix broken ones, establish baseline | **High** |
| **2.5** | `frontend/src/api/asimnexus.ts` | Split into domain-specific API modules | Medium |
| **2.6** | `database/` | Integrate actual database (SQLite for dev, PostgreSQL for prod) | **High** |

### Phase 3: Fix Minor Issues (N1-N5)

| Step | File | Action | Risk |
|------|------|--------|------|
| **3.1** | `core/__init__.py` | Fix `__all__` to only include existing subpackages | Low |
| **3.2** | `app.py` | Add `import time as _time_module` | Low |
| **3.3** | `app.py` | Add TypedDict for `_app_globals` | Low |
| **3.4** | `frontend/src/` | Fix file extensions where needed | Low |
| **3.5** | `config/` | Implement central configuration with env vars | Medium |

---

## 6. Detailed File-by-File Audit

### 6.1 `core/` Root Level — 30 Files

| File | Status | Destination |
|------|--------|-------------|
| `agent_contract.py` | 🟡 Orphaned | Should be in `core/agent/` or `core/agents/` |
| `consensus_engine.py` | 🟡 Duplicate | `core/consensus/consensus_engine.py` exists |
| `context_router.py` | 🟡 Orphaned | Should be in `core/routing/` |
| `depin_bridge.py` | 🟡 Duplicate | `core/depin/` exists |
| `digital_twin_system.py` | 🟡 Duplicate | `core/agent/digital_twin.py` exists |
| `disaster_recovery.py` | 🟡 Orphaned | Should be in `core/security/` |
| `entity_bridge.py` | 🟡 Orphaned | Should be in `core/integration/` |
| `event_bus.py` | 🟡 Orphaned | Should be in `core/mesh/` |
| `execution_pipeline.py` | 🟡 Orphaned | Should be in `core/orchestrator/` |
| `global_mesh.py` | 🟡 Duplicate | `core/mesh/unified_mesh.py` exists |
| `language_manager.py` | 🟡 Duplicate | `core/nepal/language_support.py` exists |
| `lazy_loader.py` | ✅ Core | Used by `app.py` |
| `life_journey.py` | 🟡 Orphaned | Should be in `core/lifecycle/` |
| `life_protocol_automation.py` | 🟡 Orphaned | Unknown purpose |
| `monitoring_middleware.py` | 🟡 Orphaned | Should be in `core/monitoring/` |
| `multi_agent_orchestrator.py` | 🟡 Duplicate | `core/orchestrator/` exists |
| `new_architecture_integration.py` | 🟡 Orphaned | Should be in `core/integration/` |
| `platform.py` | 🟡 Orphaned | Should be in `core/kernel/` |
| `plugin_marketplace.py` | 🟡 Duplicate | `core/economy/marketplace.py` exists |
| `prometheus_metrics.py` | 🟡 Orphaned | Should be in `core/monitoring/` |
| `quantum_bridge.py` | 🔴 Broken | Has pre-existing parse errors |
| `rate_limiter_middleware.py` | 🟡 Duplicate | `core/security/rbac.py` has rate limiter |
| `redis_manager.py` | 🟡 Orphaned | Should be in `infrastructure/` |
| `security_headers_middleware.py` | 🟡 Orphaned | Should be in `core/security/` |
| `security_layer.py` | 🟡 Duplicate | `core/security/` exists |
| `smart_llm_router.py` | 🟡 Duplicate | `core/gateway/smart_model_router.py` exists |
| `structured_logger.py` | 🟡 Orphaned | Should be in `core/monitoring/` |
| `telemetry_schema.py` | 🟡 Orphaned | Should be in `core/monitoring/` |
| `universal_api_gateway.py` | 🟡 Duplicate | `core/gateway/unified_gateway.py` exists |
| `universal_clone_system.py` | 🟡 Duplicate | `core/founder_clones/` exists |
| `vectormemory.py` | 🟡 Duplicate | `core/knowledge/vector_store.py` exists |

### 6.2 `routes/` — 48 Route Modules

| File | Router | `init_*` Function | Status |
|------|--------|-------------------|--------|
| `analytics.py` | ✅ | `init_analytics` | ✅ |
| `arvr.py` | ✅ | `init_arvr` | ✅ |
| `auth.py` | ✅ | `init_auth` | ✅ |
| `blockchain_identity.py` | ✅ | `init_blockchain_identity` | ✅ |
| `bugs.py` | ✅ | `init_bugs` | ❓ Need to verify |
| `chat.py` | ✅ | `init_chat` | ✅ |
| `clones.py` | ✅ | `init_clones` | ❓ Need to verify |
| `consensus.py` | ✅ | `init_consensus` | ✅ |
| `depin.py` | ✅ | `init_depin` | ✅ |
| `deploy.py` | ✅ | `init_deploy` | ❓ Need to verify |
| `dharma.py` | ✅ | `init_dharma` | ✅ |
| `dreaming.py` | ✅ | `init_dreaming` | ✅ |
| `enterprise.py` | ✅ | `init_enterprise` | ✅ |
| `evolution.py` | ✅ | `init_evolution` | ✅ |
| `finance.py` | ✅ | `init_finance` | ✅ |
| `founder_clones.py` | ✅ | `init_founder_clones` | ✅ |
| `governance.py` | ✅ | `init_governance` | ✅ |
| `government.py` | ✅ | `init_government` | ✅ |
| `healing.py` | ✅ | `init_healing` | ✅ |
| `health.py` | ✅ | `init_health` | ❓ Need to verify |
| `identity.py` | ✅ | `init_identity` | ✅ |
| `infrastructure.py` | ✅ | `init_infrastructure` | ✅ |
| `jobs.py` | ✅ | `init_jobs` | ✅ |
| `learning.py` | ✅ | `init_learning` | ❓ Need to verify |
| `marketplace.py` | ✅ | `init_marketplace` | ✅ |
| `mcp.py` | ✅ | `init_mcp` | ✅ |
| `memory.py` | ✅ | `init_memory` | ✅ |
| `mesh.py` | ✅ | `init_mesh` | ✅ |
| `mirror.py` | ✅ | `init_mirror` | ✅ |
| `nepal.py` | ✅ | `init_nepal_data` | ✅ |
| `observability.py` | ✅ | `init_observability` | ❓ Need to verify |
| `offline.py` | ✅ | `init_offline` | ❓ Need to verify |
| `os_control.py` | ✅ | `init_os_control` | ✅ |
| `override.py` | ✅ | `init_override` | ❓ Need to verify |
| `push.py` | ✅ | `init_push` | ❓ Need to verify |
| `pwa.py` | ✅ | `init_pwa` | ✅ |
| `rbe.py` | ✅ | `init_rbe` | ✅ |
| `registry.py` | ✅ | `init_registry` | ❓ Need to verify |
| `release.py` | ✅ | `init_release` | ✅ |
| `response.py` | ✅ | (not in app.py) | ❓ |
| `router.py` | ✅ | `init_router` | ❓ Need to verify |
| `security.py` | ✅ | `init_security` | ✅ |
| `self_awareness.py` | ✅ | `init_self_awareness` | ✅ |
| `soul_key.py` | ✅ | `init_soul_key` | ✅ |
| `sovereignty.py` | ✅ | `init_sovereignty` | ✅ |
| `stakeholder.py` | ✅ | `init_stakeholder` | ✅ |
| `universal.py` | ✅ | `init_universal` | ✅ |
| `universe.py` | ✅ | `init_universe` | ✅ |

### 6.3 `frontend/src/` — Component Inventory

| Component | Lines | Status |
|-----------|-------|--------|
| `App.tsx` | 556 | ✅ Main app shell |
| `api/asimnexus.ts` | 1700+ | 🟡 Monolithic, needs splitting |
| `api/index.ts` | — | ✅ Barrel export |
| `api/odysseus.ts` | — | ✅ Agent API |
| `components/shared/SmartHub.tsx` | — | ✅ Tab container |
| `components/shared/UnifiedChat.tsx` | — | ✅ Chat component |
| `components/pages/AIHub.tsx` | 55 | ✅ |
| `components/pages/LifeHub.tsx` | 43 | ✅ |
| `components/pages/IdentityHub.tsx` | 45 | ✅ |
| `components/pages/NetworkHub.tsx` | 154 | ✅ |
| `components/pages/GovernanceHub.tsx` | 98 | ✅ |
| `components/pages/EconomyHub.tsx` | — | ✅ |
| `components/pages/NepalHub.tsx` | — | ✅ |
| `components/pages/OSHub.tsx` | — | ✅ |
| `components/identity/SoulKeyDashboard.tsx` | 995 | ✅ |
| `components/mirror/MirrorEvolutionHub.tsx` | 1221 | ✅ |
| `components/universe/PersonalUniverseDashboard.tsx` | 939 | ✅ |
| `components/self-awareness/SelfAwarenessHub.tsx` | — | ✅ |

---

## 7. Integration Test Results Summary

| Test Suite | Tests | Status |
|------------|-------|--------|
| `tests/unit/test_self_builder.py` | 6 | ✅ PASS |
| `tests/unit/test_gap_analyzer.py` | 3 | ✅ PASS |
| `tests/unit/test_auto_builder.py` | 3 | ✅ PASS |
| `tests/integration/test_self_building_loop.py` | 17 | ✅ PASS |
| `tests/integration/test_soul_key.py` | 12 | ✅ PASS |
| **Total Verified** | **41** | **✅ ALL PASS** |
| **Total Test Files** | **200+** | **❓ UNKNOWN** |

---

## 8. Recommended Execution Order

```mermaid
flowchart TD
    A[Phase 1: Fix Critical] --> B[Phase 2: Fix Moderate]
    B --> C[Phase 3: Fix Minor]
    C --> D[Phase 4: Run Full Test Suite]
    D --> E[Phase 5: Verify Startup]
    E --> F[Phase 6: Document Results]
    
    subgraph Phase1[Phase 1: Critical Fixes]
        P1C1[Fix security __init__.py imports]
        P1C2[Fix core __init__.py subpackages]
        P1C3[Verify all route init functions]
        P1C4[Add per-module error handling in routes]
        P1C5[Wire generate_route_module to template]
        P1C6[Register missing templates]
    end
    
    subgraph Phase2[Phase 2: Moderate Fixes]
        P2M1[Consolidate root-level core files]
        P2M2[Deduplicate mirror/dreaming]
        P2M3[Fix mesh __init__.py exports]
        P2M4[Run and fix all 200+ tests]
        P2M5[Split monolithic API client]
    end
    
    Phase1 --> Phase2
```

---

## 9. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| `core/security/__init__.py` broken imports | **CRITICAL** | Create stub files first, then restore implementations |
| Route init functions missing | **HIGH** | Add try/except per-module, verify each function exists |
| Database integration | **HIGH** | Start with SQLite, migrate to PostgreSQL later |
| 200+ untested tests | **HIGH** | Run in batches, fix incrementally |
| Root-level file consolidation | **MEDIUM** | Create deprecation wrappers, migrate gradually |
| Frontend API client split | **MEDIUM** | Create domain modules, keep backward compatibility |
| Template wiring | **LOW** | Straightforward refactoring, already done for 5/6 methods |
| Missing template registration | **LOW** | Add Jinja2 templates for the 3 missing constants |
