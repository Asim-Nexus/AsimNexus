# AsimNexus World OS v2.0

Nepal National Digital Operating System - Citizen/Company/Government API

## Features Added (World OS Integration)
- 16 AI Agents (Browser, Voice, Robotics, Enterprise, Orchestration)
- 15 Tools (Email, Money, Internet, Database, DALL-E, Perplexity, Quantum, IoT, NVIDIA Isaac)
- 5 Agent Frameworks (LangGraph, CrewAI, AutoGen, OpenAI Agents, PydanticAI)
- 6 Risk Management Modules (Guardrails, Bias Detection, Toxicity Filter, Compliance)
- 3 Monitoring Modules (LangSmith, Weights & Biases, Prometheus)

## Integration Status - ALL SYSTEMS ACTIVE
```
Mirror: active     - Digital Twin consciousness + reflection
Consensus: active  - 15 Founder Clones voting system
Sandbox: active    - Docker tool execution environment
Veto: active      - Dharma Veto Engine (ethical checks)
Life Journey: active - User stage progression system
Power Balance: active - 51/49 government/public constitutional balance
Mesh P2P: active   - WebSocket peer-to-peer networking
```

## Structure
```
AsimNexus/
+-- app.py               # FastAPI unified entry (25+ endpoints)
+-- app_unified.py       # Master integration application
+-- core/
¦   +-- mirror/          # Digital Twin system (consciousness, lora, dreaming)
¦   +-- consensus/       # 15 Founder Clone voting
¦   +-- sandbox/         # Docker tool execution
¦   +-- dharma_chakra/   # Veto engine
¦   +-- life_journey.py  # User stage progression
+-- mesh/
¦   +-- p2p_transport.py # P2P networking
+-- security/
¦   +-- power_balance_constitution.py  # 51/49 constitutional rule
+-- infra/
¦   +-- docker/          # Dockerfile.backend, Dockerfile.frontend, docker-compose.prod.yml
+-- .kilo/
¦   +-- k8s/           # K8s deployment manifests
+-- frontend/          # React 18 dashboard
+-- tests/             # Integration tests
```

## Quick Start
```bash
# Run unified integration test
python app_unified.py

# Backend
uvicorn app:app --host 0.0.0.0 --port 8000

# Frontend  
cd frontend && npm start

# Test all systems
pytest tests/real/test_complete_integration.py -v
```

## Usage - Chat Commands
- `tool.email.send: {"to": "test@test.com"}`
- `tool.framework.langgraph: {"workflow": []}`
- `model.gateway.generate: {"provider": "openai"}`
- `tool.physical.nvidia_isaac: {"scene": "warehouse"}`