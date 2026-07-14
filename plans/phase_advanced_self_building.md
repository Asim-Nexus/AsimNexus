# AsimNexus Advanced Self-Building Plan

## Vision: AsimNexus Builds AsimNexus

The goal is to make AsimNexus truly self-building — able to scan itself, understand itself, identify gaps, generate code, test it, deploy it, and monitor itself — all autonomously.

---

## Current State Assessment

| Area | Status | Gap |
|------|--------|-----|
| Self-Awareness Core | ✅ Created | Needs auto-scan on startup |
| Self-Builder | ✅ Created | Only 1 template (route), no model/test/service templates |
| Evolution Engine | ✅ Exists | Not wired to SelfBuilder automatically |
| Dreaming Engine | ✅ Exists | Not wired to SelfKnowledge |
| Mirror Module | ✅ Exists | Not wired to SelfKnowledge |
| CI/CD Pipeline | ⚠️ Exists | Outdated paths, no self-awareness tests |
| Docker Setup | ⚠️ Exists | No docker-compose for local dev |
| Frontend | ⚠️ Builds | No self-awareness UI, no auto-refresh |
| Monitoring | ⚠️ Basic | No real Prometheus metrics, no dashboards |
| API Documentation | ❌ Missing | No OpenAPI/Swagger docs page |
| Error Tracking | ❌ Missing | No centralized error aggregation |
| Performance Benchmarks | ❌ Missing | No baseline performance tracking |
| Security Audit | ❌ Missing | No automated security scanning |
| Database Migrations | ❌ Missing | No Alembic/schema migration system |
| Rate Limiting | ⚠️ Exists | Not configured/enabled |
| WebSocket Support | ⚠️ Exists | Not fully wired to frontend |
| Offline Mode | ⚠️ Exists | Not tested end-to-end |
| Multi-language Support | ❌ Missing | i18n not implemented in frontend |
| Theme System | ⚠️ Basic | No dark/light theme persistence |
| PWA Support | ⚠️ Exists | Service worker not verified |
| Mobile App | ❌ Missing | Only stub exists |
| Desktop App | ❌ Missing | No Electron/Tauri build |

---

## Phase A: Self-Awareness Auto-Pilot

### A1: Auto-Scan on Startup
- **File**: [`app.py`](app.py)
- **What**: Add `CodebaseScanner` auto-scan in the lifespan startup, populate `SelfKnowledge` automatically
- **Why**: So AsimNexus knows itself from the moment it starts

### A2: Scheduled Re-Scan
- **File**: [`core/self_awareness/self_knowledge.py`](core/self_awareness/self_knowledge.py)
- **What**: Add a background task that re-scans the codebase every N minutes/hours
- **Why**: So AsimNexus detects changes to its own codebase

### A3: Wire EvolutionEngine → SelfBuilder
- **File**: [`core/self_awareness/evolution_bridge.py`](core/self_awareness/evolution_bridge.py)
- **What**: Auto-process evolution suggestions as they're created (not just on-demand)
- **Why**: So AsimNexus can autonomously improve itself

### A4: Wire DreamingEngine → SelfKnowledge
- **File**: [`core/dreaming/dreaming_engine.py`](core/dreaming/dreaming_engine.py)
- **What**: Store dream lessons as knowledge entries
- **Why**: So AsimNexus learns from its own dreams

### A5: Wire MirrorModule → SelfKnowledge
- **File**: [`core/mirror/mirror_module.py`](core/mirror/mirror_module.py)
- **What**: Store mirror reflections as knowledge entries
- **Why**: So AsimNexus learns from self-reflection

---

## Phase B: Template Expansion

### B1: Model Template
- **File**: [`core/self_awareness/self_builder.py`](core/self_awareness/self_builder.py)
- **What**: Add `TEMPLATE_MODEL` — Pydantic model with fields, validators, serialization
- **Why**: So SelfBuilder can generate data models

### B2: Service Template
- **File**: [`core/self_awareness/self_builder.py`](core/self_awareness/self_builder.py)
- **What**: Add `TEMPLATE_SERVICE` — Business logic service class with CRUD
- **Why**: So SelfBuilder can generate service layers

### B3: Test Integration Template
- **File**: [`core/self_awareness/self_builder.py`](core/self_awareness/self_builder.py)
- **What**: Add `TEMPLATE_TEST_INTEGRATION` — Integration test with fixtures
- **Why**: So SelfBuilder can generate integration tests

### B4: API Client Template
- **File**: [`core/self_awareness/self_builder.py`](core/self_awareness/self_builder.py)
- **What**: Add `TEMPLATE_API_CLIENT` — Frontend API service module
- **Why**: So SelfBuilder can generate frontend API clients

### B5: React Component Template
- **File**: [`core/self_awareness/self_builder.py`](core/self_awareness/self_builder.py)
- **What**: Add `TEMPLATE_REACT_COMPONENT` — React component with hooks
- **Why**: So SelfBuilder can generate frontend components

---

## Phase C: Self-Healing & Auto-Fix

### C1: Auto-Fix Bare Excepts
- **File**: [`core/self_awareness/self_builder.py`](core/self_awareness/self_builder.py)
- **What**: New method `fix_bare_excepts()` — finds bare `except:` clauses and wraps them with `except Exception as e: logger.exception(...)`
- **Why**: 124 bare excepts found in audit — this is a major code quality issue

### C2: Auto-Fix Missing Docstrings
- **File**: [`core/self_awareness/self_builder.py`](core/self_awareness/self_builder.py)
- **What**: New method `add_missing_docstrings()` — adds docstrings to functions/classes missing them
- **Why**: Improves code documentation automatically

### C3: Auto-Fix Unused Imports
- **File**: [`core/self_awareness/self_builder.py`](core/self_awareness/self_builder.py)
- **What**: New method `remove_unused_imports()` — detects and removes unused imports
- **Why**: Cleaner code, faster imports

### C4: Auto-Fix TODO/FIXME Items
- **File**: [`core/self_awareness/self_builder.py`](core/self_awareness/self_builder.py)
- **What**: New method `resolve_todos()` — creates issues for TODO/FIXME items in SelfKnowledge
- **Why**: Track technical debt automatically

---

## Phase D: Production Infrastructure

### D1: Docker Compose for Local Dev
- **File**: [`infrastructure/docker/docker-compose.yml`](infrastructure/docker/docker-compose.yml)
- **What**: Full docker-compose with backend, frontend, Redis, ChromaDB, Prometheus, Grafana
- **Why**: One-command local development environment

### D2: Prometheus Metrics
- **File**: [`core/monitoring_middleware.py`](core/monitoring_middleware.py)
- **What**: Add real Prometheus metrics: request count, latency histogram, error rate, active connections
- **Why**: Production monitoring

### D3: Grafana Dashboard
- **File**: [`infrastructure/grafana/dashboard.json`](infrastructure/grafana/dashboard.json)
- **What**: Pre-built Grafana dashboard for AsimNexus metrics
- **Why**: Visual monitoring

### D4: Structured Logging
- **File**: [`core/structured_logger.py`](core/structured_logger.py)
- **What**: JSON-format logging with request IDs, correlation IDs, service name
- **Why**: Log aggregation (ELK/Loki)

### D5: Health Check Endpoints Enhancement
- **File**: [`routes/health.py`](routes/health.py)
- **What**: Add `/health/dependencies` — checks Redis, ChromaDB, model availability
- **Why**: Deep health monitoring

### D6: Rate Limiting Enablement
- **File**: [`core/rate_limiter_middleware.py`](core/rate_limiter_middleware.py)
- **What**: Enable rate limiting with configurable tiers (anonymous: 10/min, authenticated: 100/min, admin: 1000/min)
- **Why**: Production security

---

## Phase E: Frontend Self-Awareness UI

### E1: Self-Awareness Dashboard Page
- **File**: [`frontend/src/components/pages/SelfAwarenessHub.tsx`](frontend/src/components/pages/SelfAwarenessHub.tsx)
- **What**: New hub page showing:
  - Codebase overview (modules, classes, functions, routes)
  - Dependency graph visualization
  - Issue tracker (bare excepts, TODOs, FIXMEs)
  - Build history (actions applied, rolled back)
  - Scan status and trigger button
- **Why**: Visual self-awareness

### E2: Self-Awareness API Service
- **File**: [`frontend/src/api/self-awareness.ts`](frontend/src/api/self-awareness.ts)
- **What**: Frontend API client for all `/api/self/*` endpoints
- **Why**: Frontend-backend integration

### E3: Auto-Refresh Metrics
- **File**: [`frontend/src/hooks/useSelfAwareness.ts`](frontend/src/hooks/useSelfAwareness.ts)
- **What**: React hook that polls self-awareness endpoints every 30s
- **Why**: Live-updating dashboard

### E4: Add to Navigation
- **File**: [`frontend/src/components/layout/Sidebar.tsx`](frontend/src/components/layout/Sidebar.tsx)
- **What**: Add "Self-Awareness" link to sidebar navigation
- **Why**: User access

---

## Phase F: API Documentation & Developer Experience

### F1: OpenAPI/Swagger Docs Page
- **File**: [`routes/docs.py`](routes/docs.py)
- **What**: Custom Swagger UI page with:
  - API version info
  - Authentication instructions
  - Rate limiting info
  - Example requests/responses
  - WebSocket documentation
- **Why**: Developer onboarding

### F2: API Contract Validation
- **File**: [`tests/real/test_api_contract.py`](tests/real/test_api_contract.py)
- **What**: Test that all documented routes exist and return correct status codes
- **Why**: Contract-first development

### F3: Performance Benchmark Suite
- **File**: [`tests/benchmarks/test_performance.py`](tests/benchmarks/test_performance.py)
- **What**: Benchmark tests for:
  - Route response times (p50, p95, p99)
  - Concurrent request handling
  - Memory usage under load
  - Database query performance
- **Why**: Performance regression detection

---

## Phase G: Security Hardening

### G1: Automated Security Scan
- **File**: [`.github/workflows/security-scan.yml`](.github/workflows/security-scan.yml)
- **What**: Add Bandit, Safety, and Trivy scans to CI
- **Why**: Automated vulnerability detection

### G2: Input Sanitization Audit
- **File**: [`core/security/input_sanitizer.py`](core/security/input_sanitizer.py)
- **What**: Audit all route inputs for sanitization, add middleware for automatic sanitization
- **Why**: XSS/SQL injection prevention

### G3: CORS Configuration
- **File**: [`app.py`](app.py)
- **What**: Tighten CORS to allow only known origins in production
- **Why**: CSRF protection

### G4: Security Headers Audit
- **File**: [`core/security_headers_middleware.py`](core/security_headers_middleware.py)
- **What**: Add CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **Why**: Browser security

---

## Phase H: Database & Persistence

### H1: Alembic Migrations
- **File**: [`database/alembic/`](database/alembic/)
- **What**: Set up Alembic for schema migrations
- **Why**: Database schema versioning

### H2: Connection Pooling
- **File**: [`database/connection.py`](database/connection.py)
- **What**: Database connection pool with retry logic
- **Why**: Production database reliability

### H3: Backup System
- **File**: [`database/backup.py`](database/backup.py)
- **What**: Automated backup of knowledge base, federation state, user data
- **Why**: Disaster recovery

---

## Phase I: Multi-Platform Support

### I1: Electron Desktop App
- **File**: [`desktop/`](desktop/)
- **What**: Electron wrapper for AsimNexus frontend with:
  - System tray integration
  - Native notifications
  - Auto-update
  - Offline-first mode
- **Why**: Desktop presence

### I2: Mobile App Enhancement
- **File**: [`frontend/mobile/app.py`](frontend/mobile/app.py)
- **What**: Enhance mobile app with:
  - Push notifications
  - Biometric auth
  - Offline message queue
  - Camera/QR scanning
- **Why**: Mobile access

### I3: PWA Enhancement
- **File**: [`frontend/public/manifest.json`](frontend/public/manifest.json)
- **What**: Verify and enhance PWA manifest, service worker caching
- **Why**: Installable web app

---

## Phase J: Self-Building Loop Completion

### J1: Autonomous Gap Detection
- **File**: [`core/self_awareness/gap_analyzer.py`](core/self_awareness/gap_analyzer.py)
- **What**: New module that:
  - Compares current codebase against ideal architecture
  - Identifies missing modules, routes, tests
  - Creates EvolutionSuggestions for gaps
- **Why**: AsimNexus identifies what it's missing

### J2: Autonomous Code Generation
- **File**: [`core/self_awareness/auto_builder.py`](core/self_awareness/auto_builder.py)
- **What**: New module that:
  - Takes a gap analysis result
  - Generates the missing code using SelfBuilder
  - Runs tests to verify
  - Commits the change (if git available)
- **Why**: AsimNexus builds itself

### J3: Autonomous Test Generation
- **File**: [`core/self_awareness/auto_builder.py`](core/self_awareness/auto_builder.py)
- **What**: For any module without tests, auto-generate test stubs
- **Why**: 100% test coverage

### J4: Self-Verification Loop
- **File**: [`core/self_awareness/auto_builder.py`](core/self_awareness/auto_builder.py)
- **What**: After any self-modification:
  1. Run affected tests
  2. Run full test suite
  3. If tests fail, rollback
  4. Log the result
- **Why**: Safe autonomous modification

---

## Architecture Diagram

```mermaid
flowchart TD
    subgraph "Self-Awareness Core"
        CS[CodebaseScanner] --> SK[SelfKnowledge]
        SK --> SB[SelfBuilder]
        EB[EvolutionBridge] --> SB
    end

    subgraph "Existing Systems"
        EE[EvolutionEngine] --> EB
        DE[DreamingEngine] --> EB
        MM[MirrorModule] --> EB
    end

    subgraph "Auto-Pilot New"
        GA[GapAnalyzer] --> SK
        GA --> EE
        AB[AutoBuilder] --> SB
        AB --> TS{Test Suite}
        TS -->|Pass| DEPLOY[Deploy]
        TS -->|Fail| ROLLBACK[Rollback]
    end

    subgraph "Infrastructure"
        PROM[Prometheus] --> GRAF[Grafana]
        DOCKER[Docker Compose] --> APP[AsimNexus]
        ALB[Alembic] --> DB[(Database)]
    end

    subgraph "Frontend"
        SA_UI[SelfAwarenessHub] --> API[/api/self/*]
        DASH[Dashboard] --> API
    end

    CS -->|Auto-scan on startup| SK
    SK -->|Auto-detect gaps| GA
    SB -->|Generate code| AB
    AB -->|Create/Modify| FILES[Codebase Files]
    FILES --> CS
```

---

## Implementation Order

| Priority | Phase | Effort | Impact |
|----------|-------|--------|--------|
| 🔴 P0 | A1: Auto-Scan on Startup | Small | High |
| 🔴 P0 | A2: Scheduled Re-Scan | Small | High |
| 🔴 P0 | C1: Auto-Fix Bare Excepts | Medium | High |
| 🔴 P0 | D1: Docker Compose | Medium | High |
| 🟡 P1 | B1-B5: Template Expansion | Medium | High |
| 🟡 P1 | E1-E4: Self-Awareness UI | Large | High |
| 🟡 P1 | F1: OpenAPI Docs | Small | Medium |
| 🟡 P1 | D2-D3: Prometheus + Grafana | Medium | High |
| 🟢 P2 | A3-A5: Wire Engines | Medium | Medium |
| 🟢 P2 | C2-C4: More Auto-Fixes | Medium | Medium |
| 🟢 P2 | D4-D6: Logging, Health, Rate Limit | Medium | Medium |
| 🔵 P3 | G1-G4: Security Hardening | Large | High |
| 🔵 P3 | H1-H3: Database Infrastructure | Large | High |
| 🔵 P3 | I1-I3: Multi-Platform | Large | Medium |
| 💎 P4 | J1-J4: Self-Building Loop | Very Large | Transformative |

---

## Files to Create (New)

1. [`core/self_awareness/gap_analyzer.py`](core/self_awareness/gap_analyzer.py) — Autonomous gap detection
2. [`core/self_awareness/auto_builder.py`](core/self_awareness/auto_builder.py) — Autonomous code generation + test + verify loop
3. [`frontend/src/components/pages/SelfAwarenessHub.tsx`](frontend/src/components/pages/SelfAwarenessHub.tsx) — Self-awareness dashboard
4. [`frontend/src/api/self-awareness.ts`](frontend/src/api/self-awareness.ts) — API client
5. [`frontend/src/hooks/useSelfAwareness.ts`](frontend/src/hooks/useSelfAwareness.ts) — Auto-refresh hook
6. [`routes/docs.py`](routes/docs.py) — OpenAPI docs page
7. [`infrastructure/docker/docker-compose.yml`](infrastructure/docker/docker-compose.yml) — Local dev compose
8. [`infrastructure/grafana/dashboard.json`](infrastructure/grafana/dashboard.json) — Grafana dashboard
9. [`database/alembic/`](database/alembic/) — Migration setup
10. [`database/connection.py`](database/connection.py) — Connection pool
11. [`database/backup.py`](database/backup.py) — Backup system
12. [`tests/benchmarks/test_performance.py`](tests/benchmarks/test_performance.py) — Benchmarks
13. [`tests/real/test_api_contract.py`](tests/real/test_api_contract.py) — Contract validation

## Files to Modify (Existing)

1. [`app.py`](app.py) — Auto-scan on startup
2. [`core/self_awareness/self_knowledge.py`](core/self_awareness/self_knowledge.py) — Background re-scan task
3. [`core/self_awareness/self_builder.py`](core/self_awareness/self_builder.py) — Add templates + auto-fix methods
4. [`core/self_awareness/evolution_bridge.py`](core/self_awareness/evolution_bridge.py) — Auto-process suggestions
5. [`core/dreaming/dreaming_engine.py`](core/dreaming/dreaming_engine.py) — Wire to SelfKnowledge
6. [`core/mirror/mirror_module.py`](core/mirror/mirror_module.py) — Wire to SelfKnowledge
7. [`core/monitoring_middleware.py`](core/monitoring_middleware.py) — Real Prometheus metrics
8. [`core/rate_limiter_middleware.py`](core/rate_limiter_middleware.py) — Enable rate limiting
9. [`frontend/src/components/layout/Sidebar.tsx`](frontend/src/components/layout/Sidebar.tsx) — Add nav link
10. [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) — Update paths, add self-awareness tests
11. [`.github/workflows/security-scan.yml`](.github/workflows/security-scan.yml) — Add Bandit/Safety/Trivy
