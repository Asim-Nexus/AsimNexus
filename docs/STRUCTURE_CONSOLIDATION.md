# AsimNexus Unified Structure Plan

## Current State - Fragmented
```
DigitalNepal-backend/app.py          ← Main backend
backend/                              ← Alternative backend
DigitalNepal-backend/tools/            ← Tools
os_control/                           ← OS Control tools
core/                                 ← Core modules
packages/core/                        ← Alternative core
frontend/                             ← React frontend
```

## Target State - Unified
```
AsimNexus/
├── app.py                    # FastAPI main entry
├── nexus_core.py            # Unified core module
├── connectors/              # All connectors (Nepal + edu + health + tour)
├── tools/                   # All tools (OS Control + Core Tools)
├── security/                # ZKP + HSMs + Veto
├── mesh/                    # Offline sync + CRDT
├── knowledge/               # Knowledge foundations
├── database/                # DB integration
├── frontend/                # React app
└── docs/                    # Documentation
```

## Consolidation Mappings

### Tools
- `os_control/tool_registry.py` → `tools/`
- `core/tools/*.py` → `tools/`
- Merge into single `tools/all_tools.py`

### Backend
- `DigitalNepal-backend/app.py` → root `app.py`
- Import paths from `DigitalNepal-backend/` → root paths

### Core Modules
- `core/*.py` + `DigitalNepal-backend/core/*.py` → unified `core/`

### Remove Duplicates
- Remove `backend/`, `apps/backend/`, duplicate `__init__.py` files
- Consolidate `packages/core/*` into root `core/`