# AsimNexus Unified Structure - FINAL

## Current Directories (To Clean)
```
tests/           ~50 test files (duplicate coverage)
api/             alt API layer
apps/backend/    duplicate backend
kernel/          alt core
agents/          agent system
cloud/           cloud services
training/        model training
config/          config tests
training/        training scripts
```

## Target Structure
```
AsimNexus/
├── app.py                    # FastAPI unified entry
├── nexus_core.py            # Core interface
├── connectors/              # All connectors unified
│   ├── nepal_connectors.py  # Gov + Companies + Education
│   ├── health_connectors.py
│   ├── palika_connectors.py
│   └── tourism_connectors.py
├── tools/                   # All tools
│   ├── all_tools.py         # OS Control + Core tools
│   └── __init__.py
├── security/                # ZKP + Security
│   ├── zkp_privacy.py
│   ├── power_balance_constitution.py
│   └── __init__.py
├── mesh/                    # Offline sync + CRDT
├── core/                    # Core modules
│   ├── consensus_engine.py
│   ├── compliance_engine.py
│   └── entity_bridge.py
├── knowledge/               # Knowledge foundations
├── database/                # Database integration
├── frontend/                # React frontend
├── tests/                   # Keep only essential tests
└── docs/
```

## Files to Move/Consolidate

### Tests → Single test file
- All test files → `tests/integration_complete.py`

### API Layers → Single app.py
- `api/`, `apps/backend/api/` → root `app.py`

### Config → Single config
- `config/`, `.kilo/`, `AGENTS.md` → single `config/`