# ASIMNEXUS Folder Structure Refactor Guide

## Current State Analysis

The current ASIMNEXUS structure has many files scattered at the root level, making it difficult to navigate and maintain. This guide outlines the recommended clean structure.

## Recommended Folder Structure

```
asim_nexus/                          # Root directory
├── core/                            # Core systems
│   ├── microkernel/                 # Kernel, Bus, Brain
│   │   ├── nexus_bus.py            # Intelligence Bus
│   │   └── nexus_brain.py          # ML Core Architecture
│   ├── security/                   # Security components
│   │   ├── post_quantum.py         # Quantum-Resistant Crypto
│   │   ├── zk_proofs.py            # Zero-Knowledge Proofs
│   │   └── hardware_root.py        # Biometric + Hardware Root of Trust
│   ├── identity/                   # Identity components
│   │   ├── did_system.py           # DID + Verifiable Credentials
│   │   └── context_aware.py        # Context-Aware Engine
│   └── world/                      # World system integrations
│       ├── nexus_world_bridge.py   # World Systems Bridge
│       ├── digital_twin.py         # Digital Twin Engine
│       ├── physical_transport.py   # Physical/Transportation
│       ├── financial_systems.py    # Global Financial Systems
│       ├── security_intel.py      # Security/Military Intelligence
│       ├── media_flow.py           # Media/Information Flow
│       ├── education_research.py   # Education/Research
│       ├── legal_compliance.py     # Legal/Regulatory Compliance
│       ├── environment_monitor.py  # Environment/Climate
│       ├── human_social.py         # Human/Social Systems
│       └── emerging_tech.py        # Emerging Tech Integration
│
├── agents/                          # Agent orchestration
│   ├── swarm.py                    # Autonomous Agent Swarm
│   ├── hybrid_economy.py           # Human-Agent Hybrid Economy
│   └── crewai_integration.py       # CrewAI orchestration
│
├── economy/                         # Economy components
│   ├── task_bus.py                 # Decentralized Task Bus
│   ├── nexus_credits.py            # Nexus Credits Token System
│   ├── reputation_system.py        # Reputation System with Staking
│   └── token_bridge.py            # Cross-Chain Token Bridge
│
├── ml/                              # ML components
│   ├── intent_recognition.py       # Intent Recognition Engine
│   ├── resource_optimization.py   # Resource Optimization ML
│   ├── predictive_security.py      # Predictive Security ML
│   ├── local_data_collection.py    # Local-First Data Collection
│   ├── self_tuning_training.py     # Self-Tuning Training System
│   ├── rag_system.py               # RAG System
│   ├── llm_finetuning.py          # LLM Fine-Tuning Pipeline
│   ├── audio_processing.py        # Audio Processing Module
│   ├── personal_ml.py             # Personal ML per User/Clone/Founder
│   └── ml_config.py               # ASIM ML Configuration
│
├── integrations/                    # External integrations
│   ├── apis/                       # API integrations
│   │   ├── nvidia_nim/            # NVIDIA NIM connectors
│   │   ├── gemini/                # Gemini API
│   │   ├── deepseek/              # DeepSeek API
│   │   └── grok/                  # Grok API
│   ├── mcps/                       # MCP connectors
│   │   ├── supabase_mcp.py        # Supabase MCP
│   │   ├── github_mcp.py          # GitHub MCP
│   │   ├── google_drive_mcp.py    # Google Drive MCP
│   │   ├── calendar_mcp.py        # Calendar MCP
│   │   └── email_mcp.py           # Email MCP
│   └── services/                   # Service APIs
│       ├── news_api.py            # News API
│       ├── crypto_api.py          # Crypto API
│       ├── cloudinary_api.py      # Cloudinary API
│       └── pollinations_api.py    # Pollinations API
│
├── frontend/                        # Frontend interfaces
│   ├── dashboard/                  # Dashboard
│   │   └── dashboard.py           # Dashboard module
│   ├── arvr/                       # AR/VR Interface
│   │   └── interface.py           # AR/VR module
│   └── mobile/                     # Mobile App
│       └── app.py                  # React Native backend
│
├── governance/                      # Governance components
│   └── consensus.py                # Governance & Consensus Engine
│
├── audit/                           # Audit components
│   └── ledger.py                   # Audit & Provenance Logger
│
├── input/                           # Input components
│   └── multimodal.py               # Multimodal Input (Voice, Vision, AR)
│
├── world_bridge/                    # World bridge (legacy)
│   └── simulator.py                # Simulation Sandbox
│
├── tests/                           # Testing suite
│   └── test_suite.py              # Comprehensive Testing Suite
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md            # Architecture documentation
│   └── FOLDER_STRUCTURE_REFACTOR.md # This file
│
├── config/                          # Configuration
│   └── .env.example               # Environment variables template
│
├── scripts/                         # Utility scripts
│   └── setup_nexus.ps1            # Setup script
│
├── deployment/                      # Deployment configs
│   ├── docker/                    # Docker configurations
│   ├── k8s/                       # Kubernetes configurations
│   └── github_actions/            # CI/CD workflows
│
├── monitoring/                      # Monitoring & Observability
│   ├── prometheus/                # Prometheus configs
│   ├── grafana/                   # Grafana dashboards
│   └── opentelemetry/             # OpenTelemetry configs
│
├── asim.py                          # Main entry point
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker configuration
├── docker-compose.yml               # Docker Compose configuration
└── README.md                        # Project documentation
```

## Migration Steps

### Phase 1: Create New Directory Structure
```bash
# Create new directories
mkdir -p core/microkernel
mkdir -p core/security
mkdir -p core/identity
mkdir -p core/world
mkdir -p agents
mkdir -p economy
mkdir -p ml
mkdir -p integrations/apis/nvidia_nim
mkdir -p integrations/apis/gemini
mkdir -p integrations/apis/deepseek
mkdir -p integrations/apis/grok
mkdir -p integrations/mcps
mkdir -p integrations/services
mkdir -p frontend/dashboard
mkdir -p frontend/arvr
mkdir -p frontend/mobile
mkdir -p governance
mkdir -p audit
mkdir -p input
mkdir -p world_bridge
mkdir -p tests
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana
mkdir -p monitoring/opentelemetry
```

### Phase 2: Move Core Files
```bash
# Move core files
mv core/nexus_brain.py core/microkernel/
mv core/security/post_quantum.py core/security/
mv core/security/zk_proofs.py core/security/
mv core/identity/did_system.py core/identity/
mv core/identity/context_aware.py core/identity/
mv core/world/*.py core/world/
```

### Phase 3: Move Agent Files
```bash
# Move agent files
mv core/agents/swarm.py agents/
mv core/economy/hybrid_economy.py agents/
```

### Phase 4: Move Economy Files
```bash
# Move economy files
mv core/economy/task_bus.py economy/
mv core/economy/nexus_credits.py economy/
mv core/economy/reputation_system.py economy/
```

### Phase 5: Move ML Files
```bash
# Move ML files to ml/ directory
# (Move all ML core components)
```

### Phase 6: Move Integration Files
```bash
# Move API integrations
mv runtime/mcp_connectors/*.py integrations/mcps/
# Move service APIs
```

### Phase 7: Move Frontend Files
```bash
# Move frontend files
mv frontend/dashboard/dashboard.py frontend/dashboard/
mv frontend/arvr/interface.py frontend/arvr/
mv frontend/mobile/app.py frontend/mobile/
```

### Phase 8: Move Test Files
```bash
# Move test files
mv tests/test_suite.py tests/
```

### Phase 9: Clean Root Directory
```bash
# Move documentation to docs/
# Move configuration to config/
# Move scripts to scripts/
# Move deployment configs to deployment/
```

### Phase 10: Update Import Paths
After moving files, update all import statements throughout the codebase:
- `from core.nexus_brain import` → `from core.microkernel.nexus_brain import`
- `from core.security.post_quantum import` → `from core.security.post_quantum import`
- etc.

## Benefits of This Structure

1. **Clear Separation of Concerns**: Each module has its own dedicated directory
2. **Easier Navigation**: Logical grouping of related components
3. **Better Scalability**: Easy to add new modules without clutter
4. **Improved Maintainability**: Clear structure makes debugging easier
5. **Professional Organization**: Follows industry best practices

## Notes

- This is a major refactor that requires careful testing after each phase
- Consider using version control to track changes
- Update all documentation to reflect new structure
- Update CI/CD pipelines to use new paths
- Test all imports after migration
