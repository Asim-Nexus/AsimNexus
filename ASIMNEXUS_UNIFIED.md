# AsimNexus Unified Architecture

## 🏛️ Core Philosophy
AsimNexus = World OS — Digital Entity Control Dashboard

## 📁 Unified Structure

### Backend: `DigitalNepal-backend/`
```
app.py                    # FastAPI server (localhost:8000)
nexus_core.py            # Unified Core Interface
connectors/
  ├── nepal_connectors.py  # All connectors (gov + companies + edu)
  ├── health_connectors.py
  ├── palika_connectors.py
  └── tourism_connectors.py
core/
  ├── consensus_engine.py   # 15 Founder Clones
  ├── compliance_engine.py    # 51/49 Power Balance
  ├── security_layer.py       # ZKP + HSMs
  └── entity_bridge.py
security/
  └── zkp_privacy.py          # Pedersen + Schnorr + ECC
mesh/
  └── offline_sync_engine.py  # CRDT + Sync
knowledge/
  └── __init__.py             # 9 Knowledge Foundations
database/
  └── __init__.py             # Firebase Integration
```

### Frontend: `frontend/`
```
src/
  ├── App.js                 # Main router + layout
  ├── index.js               # React entry
  ├── components/
  │   ├── chat/
  │   │   ├── UniversalChat.jsx    # Full-page chat
  │   │   └── UnifiedChat.jsx      # Shared component (floating + full)
  │   ├── odysseus/
  │   │   ├── ToolConfirmationDialog.jsx
  │   │   └── MCPServiceBrowser.jsx
  │   ├── pages/
  │   │   ├── OSHub.jsx      # OS dashboard
  │   │   ├── EconomyHub.jsx  # Marketplace
  │   │   ├── AIHub.jsx       # Memory + LLM
  │   │   ├── IdentityHub.jsx   # ZKP identity
  │   │   ├── LifeHub.jsx       # Life journey
  │   │   └── NetworkHub.jsx    # Mesh network
  │   └── shared/
  │       └── AsimOrbMaster.jsx   # Floating chat
  └── api/
      ├── asimnexus.js        # Main API client
      ├── unified_api.js      # Unified API exports
      ├── odysseus.js         # Agent/MCP/Tools
      └── index.js            # Barrel export
```

## 🔗 API Contract (Backend Routes)

| Frontend Endpoint | Backend Route | Component |
|------------------|---------------|-----------|
| `/api/v1/np/*` | `app.py` endpoints | Nepal connectors |
| `/api/chat` | `chatAPI.sendMessage` | UniversalChat |
| `/personal/status` | `personalAPI.getStatus` | OSHub |
| `/api/mesh/*` | `meshAPI.*` | NetworkHub |
| `/api/os/*` | `osToolsAPI.*` | OSControlPanel |
| `/health` | `healthAPI.check` | All pages |

## 🚀 Run Commands

```bash
# Terminal 1: Backend
cd DigitalNepal-backend
uvicorn app:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm start

# Both connect at: http://localhost:8000
```