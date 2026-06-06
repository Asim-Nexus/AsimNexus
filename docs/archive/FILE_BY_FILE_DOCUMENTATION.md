# ASIMNEXUS - File by File Documentation

## Overview
ASIMNEXUS has 200+ Python files organized into modules. This document explains what each file does and how they connect.

---

## Root Level Files

### main.py (1,888 lines)
**Purpose**: Main entry point for ASIMNEXUS
**Key Components**:
- Configuration loading
- Backend startup (Unified Orchestrator, Automation OS)
- Gemma-2 2B LLM loading
- GemmaASIM class with chat() method
- HTTP server setup
- API endpoints

**Connections**:
- Imports from: core/, runtime/, connectors/
- Used by: Docker, deployment scripts

**Recent Changes**: Added LLM Interpreter integration (lines 193-209)

---

### asim.py (1,085 lines)
**Purpose**: Alternative CLI interface for ASIMNEXUS
**Key Components**:
- Interactive shell
- Command processing
- Agent system integration

**Connections**:
- Imports from: core/, agents/
- Used by: CLI users

---

### asim_config.py (98 lines)
**Purpose**: Configuration management
**Key Components**:
- Config loading from environment
- Default settings

**Connections**:
- Used by: main.py, asim.py

---

## core/ Directory (194 files)

### Core Orchestrators

#### orchestrator.py (307 lines)
**Purpose**: Main orchestrator for ASIM components
**Key Components**:
- ASIMUnifiedOrchestrator class
- Integrates: Cloud Brain, Clone Kernel, Life Protocol, Security, WAMP, 15-Founder Company
- Request processing with security layers

**Connections**:
- Imports from: cloud/, core/, security/
- Used by: main.py

---

#### unified_orchestrator.py (453 lines)
**Purpose**: Alternative orchestrator with task analysis
**Key Components**:
- Task type analysis
- Intent detection
- Task routing

**Connections**:
- Imports from: core/llm_intent_detector, core/codebase_indexer
- Used by: main.py

---

### LLM Integration

#### llm_interpreter/llm_interpreter.py (413 lines)
**Purpose**: LLM Interpreter - Brain of ASIMNEXUS
**Key Components**:
- LLMInterpreter class
- interpret() - Send user message to LLM with system prompt
- execute() - Run interpreted command
- process_chat() - End-to-end processing
- Learning system (teacher-student model)

**Connections**:
- Imports from: core/universal_auto_api, core/external_apis
- Used by: main.py (NEW integration)

---

#### llm_interpreter/asim_system_prompt.txt (168 lines)
**Purpose**: System prompt for LLM
**Contents**:
- ASIMNEXUS architecture overview
- 15 Founder Clones description
- Universal API Connector rules
- Auto-Automation Engine rules
- JSON response format
- Learning rules

**Connections**:
- Used by: llm_interpreter.py

---

#### asim_gemma_integration.py (240 lines)
**Purpose**: Gemma-2 LLM integration
**Key Components**:
- ASIMGemmaIntegration class
- Model loading
- Chat completion

**Connections**:
- Used by: main.py

---

### Universal API & Automation

#### universal_auto_api/universal_api_connector.py (439 lines)
**Purpose**: Connect ANY API from chat
**Key Components**:
- UniversalAutoAPIConnector class
- auto_connect() - Main entry
- parse_api_from_chat() - Extract API info
- _detect_service_from_key() - Auto-detect from key patterns
- Supports: OpenAI, Anthropic, Google, NVIDIA NIM, Groq

**Connections**:
- Used by: llm_interpreter.py, main.py

---

#### universal_auto_api/auto_automation_engine.py (530 lines)
**Purpose**: Natural language → Automation rules
**Key Components**:
- AutoAutomationEngine class
- create_automation() - Main entry
- parse_time_based() - Extract schedule
- parse_condition_based() - Extract condition
- parse_event_based() - Extract event trigger

**Connections**:
- Used by: llm_interpreter.py, main.py

---

#### universal_auto_api/api_intelligence.py (284 lines)
**Purpose**: API intelligence and analysis
**Key Components**:
- API schema analysis
- API discovery
- API documentation generation

**Connections**:
- Used by: universal_api_connector.py

---

### External APIs

#### external_apis/nvidia_nim_connector.py (265 lines)
**Purpose**: NVIDIA NIM integration (90+ models)
**Key Components**:
- list_available_models() - Returns 90+ models
- call_model() - Call specific model
- get_model_details() - Get model info

**Connections**:
- Used by: llm_interpreter.py, main.py

---

#### external_apis/ai_tools_discovery.py (682 lines)
**Purpose**: 2000+ AI tools database
**Key Components**:
- search_tools() - Search by keyword
- recommend_tools() - Get recommendations
- get_popular_tools() - Top 10 list
- filter_by_category() - Category filter

**Connections**:
- Used by: llm_interpreter.py, main.py

---

#### external_apis/unified_api_manager.py (343 lines)
**Purpose**: Unified API management
**Key Components**:
- API connection management
- API health monitoring
- API load balancing

**Connections**:
- Used by: external_apis modules

---

### Agent System

#### agents/base_agent.py (292 lines)
**Purpose**: Base class for all agents
**Key Components**:
- BaseAgent abstract class
- agent_id, role, goal, backstory
- tools, skills, llm_provider
- task_queue, completed_tasks

**Connections**:
- Used by: All agent clones

---

#### agents/clones/ (15 files)
**Purpose**: 15 Founder Clones
**Files**:
- ceo_clone.py (190 lines) - CEO Clone
- cto_clone.py (221 lines) - CTO Clone
- cfo_clone.py (216 lines) - CFO Clone
- coo_clone.py (253 lines) - COO Clone
- cmo_clone.py (318 lines) - CMO Clone
- devops_clone.py (315 lines) - DevOps Clone
- security_clone.py (330 lines) - Security Clone
- ai_ml_clone.py (302 lines) - AI/ML Clone
- data_clone.py (281 lines) - Data Clone
- frontend_clone.py (282 lines) - Frontend Clone
- nepal_clone.py (262 lines) - Nepal Clone
- support_clone.py (270 lines) - Support Clone
- legal_clone.py (274 lines) - Legal Clone
- hr_clone.py (287 lines) - HR Clone
- innovation_clone.py (275 lines) - Innovation Clone

**Connections**:
- Inherit from: base_agent.py
- Used by: company_structure.py

---

#### agents/multi_agent_orchestrator.py (318 lines)
**Purpose**: Multi-agent coordination
**Key Components**:
- Agent task delegation
- Agent collaboration
- Agent performance tracking

**Connections**:
- Used by: unified_orchestrator.py

---

### World Systems (40+ files)

#### healthcare_system.py (320 lines)
**Purpose**: Healthcare automation
**Key Components**:
- Patient management
- Appointment scheduling
- Medical records

**Connections**:
- Used by: orchestrator.py

---

#### financial_system.py (294 lines)
**Purpose**: Financial automation
**Key Components**:
- Transaction processing
- Budget management
- Financial reporting

**Connections**:
- Used by: orchestrator.py

---

#### education_system.py (333 lines)
**Purpose**: Education automation
**Key Components**:
- Student management
- Course scheduling
- Grade tracking

**Connections**:
- Used by: orchestrator.py

---

#### government_system.py (350 lines)
**Purpose**: Government integration
**Key Components**:
- Government services
- Citizen management
- Policy automation

**Connections**:
- Used by: orchestrator.py

---

### Other Core Modules

#### asim_tools.py (1,422 lines)
**Purpose**: Tool registry and management
**Key Components**:
- Tool registration
- Tool execution
- Tool validation

**Connections**:
- Used by: main.py, agents

---

#### engines.py (1,147 lines)
**Purpose**: Core engines
**Key Components**:
- LLM engine
- Automation engine
- Orchestration engine

**Connections**:
- Used by: main.py

---

#### api_endpoints.py (1,084 lines)
**Purpose**: FastAPI endpoints
**Key Components**:
- /llm/chat endpoint
- /status endpoint
- /queue endpoint

**Connections**:
- Used by: main.py

---

#### conversation_memory.py (225 lines)
**Purpose**: Conversation memory management
**Key Components**:
- Session management
- Message storage
- Context tracking

**Connections**:
- Used by: main.py, chat.py

---

#### system_scanner.py (466 lines)
**Purpose**: System scanning
**Key Components**:
- Hardware scan
- Software scan
- Process scan

**Connections**:
- Used by: main.py

---

## connectors/ Directory (18 files)

### LLM Connectors

#### openai_connector.py (233 lines)
**Purpose**: OpenAI API connector
**Key Components**:
- Chat completion
- Streaming support
- Error handling

**Connections**:
- Used by: unified_llm_gateway.py

---

#### anthropic_connector.py (225 lines)
**Purpose**: Anthropic Claude connector
**Key Components**:
- Chat completion
- Streaming support
- Error handling

**Connections**:
- Used by: unified_llm_gateway.py

---

#### gemini_connector.py (248 lines)
**Purpose**: Google Gemini connector
**Key Components**:
- Chat completion
- Streaming support
- Error handling

**Connections**:
- Used by: unified_llm_gateway.py

---

#### unified_llm_gateway.py (656 lines)
**Purpose**: Unified LLM gateway
**Key Components**:
- Multi-LLM routing
- Load balancing
- Fallback handling

**Connections**:
- Used by: main.py, core/

---

### Other Connectors

#### nepal_banking.py (453 lines)
**Purpose**: Nepal banking integration
**Key Components**:
- Bank API connections
- Transaction processing
- Account management

**Connections**:
- Used by: core/nepal/

---

#### world_integrations.py (209 lines)
**Purpose**: World service integrations
**Key Components**:
- Global API connections
- International services

**Connections**:
- Used by: core/

---

## security/ Directory (10 files)

### security_framework.py (687 lines)
**Purpose**: Main security framework
**Key Components**:
- 3-layer security
- Authentication
- Authorization
- Audit logging

**Connections**:
- Used by: orchestrator.py

---

### security_vault.py (684 lines)
**Purpose**: Secret management
**Key Components**:
- API key storage
- Encryption
- Access control

**Connections**:
- Used by: all connectors

---

### security_audit.py (310 lines)
**Purpose**: Security auditing
**Key Components**:
- Audit log
- Compliance checking
- Security reporting

**Connections**:
- Used by: security_framework.py

---

## deployment/ Directory (24 files)

### multicloud.py (706 lines)
**Purpose**: Multi-cloud deployment
**Key Components**:
- AWS deployment
- GCP deployment
- Azure deployment

**Connections**:
- Used by: deployment scripts

---

### load_balancer.py (223 lines)
**Purpose**: Load balancing
**Key Components**:
- Round-robin
- Least connections
- Health checks

**Connections**:
- Used by: multicloud.py

---

## tests/ Directory (15 files)

### integration_test_suite.py (587 lines)
**Purpose**: Integration tests
**Key Components**:
- API tests
- Agent tests
- System tests

**Connections**:
- Used by: CI/CD

---

### load_test.py (433 lines)
**Purpose**: Load testing
**Key Components**:
- Performance tests
- Stress tests
- Scalability tests

**Connections**:
- Used by: CI/CD

---

## Summary

### File Count by Category
- **Core**: 194 files
- **Connectors**: 18 files
- **Security**: 10 files
- **Deployment**: 24 files
- **Tests**: 15 files
- **Other**: ~50 files
- **Total**: ~311 files

### Lines of Code by Category
- **main.py**: 1,888 lines
- **core/**: ~100,000 lines
- **connectors/**: ~5,000 lines
- **security/**: ~4,000 lines
- **deployment/**: ~2,000 lines
- **tests/**: ~3,000 lines
- **Total**: ~150,000+ lines

### Key Connections
```
main.py
    ↓
core/orchestrator.py
    ↓
core/llm_interpreter/llm_interpreter.py
    ↓
core/universal_auto_api/
core/external_apis/
core/agents/
    ↓
connectors/unified_llm_gateway.py
    ↓
connectors/openai_connector.py
connectors/anthropic_connector.py
connectors/gemini_connector.py
```

---

**Next Step**: Implement Phase 1 improvements from WORLD_CLASS_ANALYSIS.md
