# AsimNexus Developer Setup Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git
- Docker (optional)

### 1. Clone Repository
```bash
git clone https://github.com/asimnexus/asimnexus.git
cd asimnexus
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend
python simple_backend.py
```

Backend will start at: `http://127.0.0.1:8000`

### 3. Frontend Setup
```bash
cd frontend/react

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will start at: `http://localhost:3000`

### 4. Verify Installation
```bash
# Run integration tests
cd tests/integration
python test_all_endpoints.py
```

---

## 🐳 Docker Setup (Alternative)

### Full Stack with Docker Compose
```bash
# Start all services
docker-compose --profile frontend up -d

# Access:
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### Individual Services
```bash
# Backend only
docker-compose up -d asimnexus

# With database
docker-compose --profile database up -d

# With Redis cache
docker-compose --profile cache up -d
```

---

## 📁 Project Structure

```
asimnexus/
├── simple_backend.py           # Main backend (4,200+ lines)
├── core/                       # Core modules
│   ├── universal/             # Phase 1: 182 currencies
│   ├── infrastructure/          # Phase 2: CDN, nodes
│   ├── platform/               # Phase 3: PWA, mobile
│   ├── finance/                # Phase 4: Wallet, banks
│   ├── government/             # Phase 5: e-ID, tax
│   ├── accessibility/          # Phase 6: WCAG 2.1
│   ├── performance/            # Phase 7: 2G/3G
│   ├── security/               # Phase 8: ZKP, crypto
│   ├── mesh/                   # Mesh Network
│   ├── sovereignty/            # Air-gap
│   └── universe/               # Personal universe
├── frontend/
│   └── react/
│       ├── src/
│       │   ├── components/     # UI components
│       │   │   ├── UniversalChat.jsx
│       │   │   ├── PersonalOS.jsx
│       │   │   └── ...
│       │   ├── services/
│       │   │   └── api.js      # Backend API
│       │   └── App.js
│       └── package.json
├── tests/
│   └── integration/
│       └── test_all_endpoints.py
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🔧 Backend Development

### API Endpoints (75+ available)

#### Core Endpoints
```
GET  /api/system/complete          # Full system status
GET  /api/system/info              # System info
GET  /api/health                   # Health check
```

#### Dharma / ΔT Engine
```
GET  /api/dharma/status            # Production ΔT
GET  /api/dharma/production/status
POST /api/dharma/veto              # Ethical veto
```

#### Personal OS
```
GET  /api/personal/status
GET  /api/personal/universe
GET  /api/personal/contracts
```

#### Agent Mode
```
POST /api/agent/mode/on            # Activate clone
POST /api/agent/mode/off           # Deactivate
GET  /api/agent/status
```

#### Financial
```
GET  /api/finance/status
GET  /api/finance/currencies
POST /api/finance/wallet/create
```

#### Mesh Network
```
GET  /api/mesh/status
POST /api/mesh/node/init
POST /api/mesh/clone/sync
```

#### Sovereignty
```
GET  /api/sovereignty/airgap/status
POST /api/sovereignty/airgap/activate
POST /api/sovereignty/airgap/restore
```

### Adding New Endpoints

Edit `simple_backend.py`:
```python
@app.get("/api/myfeature/status")
async def my_feature_status():
    try:
        from core.myfeature import get_manager
        return JSONResponse(get_manager().get_status())
    except Exception as e:
        return JSONResponse({"error": str(e)})
```

---

## 🎨 Frontend Development

### Component Structure
```javascript
// services/api.js - All API calls
import { api } from '../services/api';

// Use in components
const status = await api.getDharmaStatus();
const mesh = await api.getMeshStatus();
```

### Key Components
- `UniversalChat.jsx` - AI chat interface
- `PersonalOS.jsx` - Personal dashboard
- `ClonesPanel.jsx` - Clone management
- `AgentMarketplacePanel.jsx` - Job marketplace
- `Wallet.jsx` - Financial wallet

### Adding New Components
```javascript
// src/components/MyFeature.jsx
import React from 'react';
import { api } from '../services/api';

export function MyFeature() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    api.getMyFeature().then(setData);
  }, []);
  
  return <div>{data && JSON.stringify(data)}</div>;
}
```

---

## 🧪 Testing

### Integration Tests
```bash
# Run all endpoint tests
cd tests/integration
python test_all_endpoints.py

# Results saved to: test_results_*.json
```

### Manual Testing
```bash
# Test specific endpoint
curl http://127.0.0.1:8000/api/dharma/status

# Test with POST
curl -X POST http://127.0.0.1:8000/api/mesh/node/init \
  -H "Content-Type: application/json" \
  -d '{"node_type": "personal", "name": "Test", "country": "NP"}'
```

---

## 🐛 Common Issues

### Backend won't start
```bash
# Check port 8000 is free
lsof -i :8000

# Check dependencies
pip install -r requirements.txt --upgrade

# Check Python version
python --version  # Should be 3.8+
```

### Frontend won't connect
```bash
# Check backend is running
curl http://127.0.0.1:8000/api/system/info

# Check CORS in .env
REACT_APP_API_URL=http://127.0.0.1:8000
```

### Module not found
```bash
# Ensure running from correct directory
cd asimnexus
python simple_backend.py

# Or use absolute imports
python -m asimnexus.simple_backend
```

---

## 📝 Environment Variables

### Backend (.env)
```env
ASIM_JWT_SECRET=your-secret-key-here
ASIM_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ASIM_DATA_DIR=/app/data
LOG_LEVEL=INFO
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_VERSION=0.8.0
```

---

## 🚀 Deployment

### Production Deployment
```bash
# Build frontend
cd frontend/react
npm run build

# Deploy backend
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker simple_backend:app

# Or use Docker
docker-compose --profile proxy up -d
```

### Environment-specific configs
- `config/production.yaml`
- `config/staging.yaml`
- `config/development.yaml`

---

## 📊 Monitoring

### Health Check
```bash
# System health
curl http://127.0.0.1:8000/api/system/info

# Complete status
curl http://127.0.0.1:8000/api/system/complete
```

### Logs
```bash
# Backend logs
tail -f logs/asimnexus.log

# Docker logs
docker-compose logs -f asimnexus
```

---

## 🤝 Contributing

### Code Style
- Python: PEP 8, type hints
- JavaScript: ESLint, Prettier
- Git: Conventional commits

### Pull Request Process
1. Fork repository
2. Create feature branch
3. Add tests
4. Update documentation
5. Submit PR

### Testing Required
- Integration tests pass
- Manual testing completed
- Documentation updated

---

## 📚 Resources

- **API Documentation**: See Bible.md
- **Architecture**: See docs/ARCHITECTURE.md
- **Contributing**: See CONTRIBUTING.md
- **License**: Dual License (AGPL Core + Commercial Advanced)

---

## 💬 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Discord**: discord.gg/asimnexus
- **Email**: dev@asimnexus.org

---

## 🎯 Quick Commands Cheat Sheet

```bash
# Start everything
python simple_backend.py &
cd frontend/react && npm start

# Test everything
python tests/integration/test_all_endpoints.py

# Docker everything
docker-compose --profile frontend up -d

# Stop everything
docker-compose down
pkill -f "python simple_backend"
```

---

**Version**: 0.8.0 | **Updated**: 2025-01-25 | **Status**: 80-85% Complete
