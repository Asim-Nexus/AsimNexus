# AsimNexus Unified UI/UX Structure

## Step 1: Identify All UI Sources

| Folder | Type | Framework | Status |
|--------|------|-----------|--------|
| `frontend/` | Main | React 18 | ✅ Primary |
| `ui/` | Alternative | Flask + SocketIO | ⚠️ Duplicate |
| `web/` | Alternative | Flask | ⚠️ Duplicate |
| `desktop/` | Desktop | Electron? | ❓ Unknown |
| `mobile/` | Mobile | React Native? | ❓ Unknown |

## Step 2: Consolidation Plan

### Keep: `frontend/` (React 18)
- Modern component architecture
- UnifiedChat + AsimOrb
- All 15 Clones
- API integration

### Remove: `ui/` and `web/` (Flask duplicates)
- Move unique features to frontend
- Use FastAPI backend instead

### Action Items:
1. ✅ `app.py` - Unified FastAPI backend
2. ✅ `frontend/src/api/` - API client
3. ✅ `frontend/src/components/` - All React components
4. ❌ Remove `ui/` and `web/` duplicates
5. ❌ Move `desktop/`, `mobile/` to archive

## Step 3: Run Structure

```
AsimNexus/
├── app.py                    # Unified FastAPI backend
├── frontend/                 # React 18 frontend
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── index.js
│   └── package.json
├── connectors/               # All connectors
├── tools/                    # All tools
├── core/                     # Core modules
└── docs/
```