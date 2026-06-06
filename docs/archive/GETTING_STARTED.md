# AsimNexus — Getting Started Guide

## 🚀 Quick Start (5 minutes)

### One-Line Install
```bash
curl -fsSL install.asimnexus.org | bash
```

### Start AsimNexus
```bash
asimnexus        # Normal mode
asimnexus dev    # Development mode
asimnexus offline # Offline mode (local AI only)
```

### Access
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📋 Installation Methods

### Method 1: Automatic (Recommended)
```bash
curl -fsSL install.asimnexus.org | bash
```

### Method 2: Manual Clone
```bash
git clone https://github.com/asimnexus/asimnexus.git
cd asimnexus
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Method 3: Docker
```bash
docker-compose up
```

### Method 4: Windows (PowerShell)
```powershell
# Download and run installer
Invoke-WebRequest -Uri "https://install.asimnexus.org/windows" -OutFile "install.ps1"
.\install.ps1
```

---

## 🔧 Post-Installation Setup

### 1. Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your settings
```

Required:
- `ASIM_JWT_SECRET` — Random 64-character string
- `ASIM_DATA_DIR` — Where to store user data
- `ASIM_ALLOWED_ORIGINS` — Frontend URLs (comma-separated)

Optional (for external APIs):
- `OPENAI_API_KEY` — For GPT-4 access
- `GOOGLE_API_KEY` — For Gemini access
- `ANTHROPIC_API_KEY` — For Claude access
- `TESLA_API_TOKEN` — For Tesla vehicle control

### 2. Create Admin Account
```bash
python scripts/create_admin.py --email admin@example.com --password secure123
```

### 3. Download Local LLM (Optional, for offline mode)
```bash
# Download a GGUF model
python -c "from core.llm.local_llm import get_local_llm; \
  llm = get_local_llm(); \
  llm.download_model('https://huggingface.co/TheBloke/Llama-2-7B-GGUF/resolve/main/llama-2-7b.Q4_K_M.gguf', 'llama-2-7b')"
```

---

## 🌐 Using AsimNexus

### Web Interface
1. Open http://localhost:3000
2. Register or login
3. Access your **Personal Universe**
4. Chat with **15 Founder Clones**
5. Manage your **Human Digital Twin (HDT)**

### API Examples

#### Register
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Ram Bahadur",
    "email": "ram@example.com",
    "password": "secure123",
    "country_code": "NP"
  }'
```

#### Chat
```bash
curl -X POST http://localhost:8000/llm/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "नेपालको इतिहास बताउनुहोस्"}'
```

#### List Clones
```bash
curl http://localhost:8000/clones/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get HDT
```bash
curl http://localhost:8000/hdt/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  ⑤ OMNI-OPERATOR INTERFACE (React Frontend)                  │
├─────────────────────────────────────────────────────────────┤
│  ④ AGENTIC MATRIX (15 Founder Clones + Universal Bridge)     │
├─────────────────────────────────────────────────────────────┤
│  ③ DHARMA-CHAKRA (Constitutional Guard + Real ZKP)           │
├─────────────────────────────────────────────────────────────┤
│  ② UNIVERSAL MCP (OS Abstraction + Auto Discovery)           │
├─────────────────────────────────────────────────────────────┤
│  ① PURE KERNEL (FastAPI + Local LLM + Mesh Network)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 Security Features

- **JWT Authentication** — Stateless, secure tokens
- **Zero-Knowledge Proofs** — Privacy-preserving verification
- **Dharma-Chakra VETO** — Constitutional AI guard
- **Level-3 Confirmation** — Human-in-the-loop for critical actions
- **Local-First** — Your data stays on your device

---

## 🌟 Key Features

### For Individuals
- **Personal Universe** — Your own digital world
- **Human Digital Twin** — AI that learns your preferences
- **Offline AI** — Works without internet
- **15 Founder Clones** — Expert AI agents for every domain

### For Companies
- **Enterprise Universe** — Secure team workspaces
- **Universal API Bridge** — Connect any external service
- **Auto Discovery** — Zero-config device joining
- **Hierarchical Access** — Role-based permissions

### For Governments
- **National Universe** — Sovereign data control
- **Legal Compliance** — Automatic regulation adherence
- **Citizen Services** — Digital identity and access
- **Transparent Governance** — Audit trails and accountability

---

## 📚 Next Steps

1. **Explore API**: http://localhost:8000/docs
2. **Read Architecture**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
3. **Deploy Production**: [docs/DEPLOYMENT.md](DEPLOYMENT.md)
4. **Contribute**: [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 🆘 Troubleshooting

### Port already in use
```bash
# Find and kill process
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Or use different port
python main.py --port 8080
```

### Permission denied
```bash
# Fix permissions
chmod +x install.sh
chmod -R 755 data/
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend won't start
```bash
cd frontend/react
rm -rf node_modules
npm install
npm start
```

---

## 💬 Support

- **GitHub Issues**: https://github.com/asimnexus/asimnexus/issues
- **Discord**: https://discord.gg/asimnexus
- **Email**: team@asimnexus.org

---

**Welcome to AsimNexus — One Kernel, Infinite Worlds! 🌐**
