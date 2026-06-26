# AsimNexus Unified Structure - FINAL

## ✅ Active Directories (With Code)

### `core/` (54 py files) - CORE ENGINE
- consensus_engine.py - 15 Founder Clones consensus
- compliance_engine.py - 51/49 Power Balance
- entity_bridge.py - Entity bridge
- dharma_chakra/ - Ethics/Governance
- life_journey.py - Digital Twin lifecycle

### `connectors/` (63 py files) - DATA CONNECTORS
- nepal_connectors.py - Gov + Companies + Education
- health_connectors.py - Hospitals
- palika_connectors.py - 753 Palikas
- tourism_connectors.py - Hotels

### `mesh/` (26 py files) - OFFLINE SYNC
- offline_sync_engine.py - CRDT + sync

### `security/` (50 py files) - SECURITY
- zkp_privacy.py - ZKP proofs
- power_balance_constitution.py - 51/49 system
- security_layer.py - HSM + ZKP

### `economy/` (7 py files) - ECONOMY SYSTEM
- wallet.py, tokens.py, escrow.py, marketplace.py, staking.py

### `os_control/` (47 tools) - OS TOOLS
- tool_registry.py - Tool registry
- openclaw_like_tools/ - File/Process/System tools

### `tools/` (3 py files) - TOOLS BARREL
- all_tools.py - Unified tools export

### `database/` - DATABASE INTEGRATION
- Supabase integration

### `docker/` - DEPLOYMENT
- Docker configurations

### `DigitalNepal-backend/` - ORIGINAL BACKEND
- Kept for core modules

## 🗃️ Archived/Removed
- `evolution/`, `founders/`, `.plans/` - Removed (no active code)
- `ui/`, `web/` - Removed (duplicates)
- `desktop/`, `mobile/` - Archived

## 🚀 Run
```bash
# Backend
cd AsimNexus
uvicorn app:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm start
```

## 📊 Entity Counts
- Ministries: 18
- Provinces: 7
- Districts: 77
- Banks: 30
- ISPs: 20
- Universities: 12
- Schools: 7
- Hospitals: 12
- Hotels: 20
- Palikas: 753
- OS Tools: 47
- React Components: 52