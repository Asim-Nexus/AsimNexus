# ASIMNEXUS Complete Architecture Documentation
## Line-by-Line Understanding

---

## 1. WHAT IS ASIMNEXUS?

ASIMNEXUS is a **World Operating System** - an autonomous AI system that can:
- Connect to any API in the world through chat
- Automate tasks across life, computer, devices, business
- Run a digital company with 15 founder clones
- Integrate with government systems (Nepal, India, Bangladesh, etc.)
- Control system hardware and software
- Create and manage digital clones

---

## 2. MAIN ENTRY POINT: main.py

### File Structure:
```
main.py (117,217 bytes)
├── Configuration Loading (lines 39-51)
├── Backend Startup (lines 53-145)
│   ├── Unified Orchestrator init
│   ├── Automation OS init
│   ├── Hardware-aware processor init
│   └── Gemma-2 2B LLM loading (lines 100-114)
├── GemmaASIM Class (lines 147-165)
│   ├── __init__: Sets up LLM, integrator, memory
│   └── chat(): Main chat processing (lines 166-400+)
├── MinimalASIM Fallback (lines 1576-1690)
└── HTTP Server Setup (lines 1750-1800)
```

### Current Chat Flow (main.py lines 166-400):
```python
async def chat(self, message):
    1. Add to conversation_memory (line 169-170)
    2. Check Nepali language (lines 173-182)
    3. Initialize tool_manager (lines 185-191)
    4. DIRECT INTENT DETECTION (lines 194-400)
       - Pattern matching for greetings
       - Pattern matching for API keys
       - Pattern matching for automation
       - Pattern matching for system scan
       - Pattern matching for file operations
       - If no match → LLM fallback
```

---

## 3. CORE MODULES (194 files in core/)

### Key Directories:
```
core/
├── agents/ (17 items) - 15 Founder Clones
├── universal_auto_api/ (4 items) - API & Automation
├── external_apis/ (4 items) - NVIDIA NIM, AI Tools
├── api_gateway/ (4 items) - API routing
├── circuit_breaker/ (3 items) - Error handling
├── cqrs/ (3 items) - Command Query Separation
├── evaluation/ (5 items) - System evaluation
├── leaderboard/ (2 items) - Performance tracking
├── memory/ (1 item) - Vector memory
├── nepal/ (5 items) - Nepal-specific integrations
├── participants/ (2 items) - User management
├── saga/ (2 items) - Long-running transactions
├── service_discovery/ (4 items) - Service registry
├── skills/ (1 item) - Agent skills
├── submissions/ (2 items) - Task submissions
├── workflow/ (2 items) - Workflow engine
└── world_knowledge/ (7 items) - Knowledge base
```

### Critical Core Files:

#### A. orchestrator.py (lines 1-318)
**ASIMUnifiedOrchestrator** - The Master Controller
- Integrates: Cloud Brain, Clone Kernel, Life Protocol, Security, WAMP, 15-Founder Company
- Methods:
  - `initialize()`: Starts all 7 components (lines 54-134)
  - `process_request()`: Routes requests through security layers (lines 156-203)
  - `get_system_status()`: Returns complete system state (lines 271-294)

#### B. unified_orchestrator.py (lines 38-185)
**Alternative Orchestrator** with task analysis
- `analyze_request()`: Uses LLM intent detector (lines 84-136)
- Intent mapping: file_create, file_read, system_command, automation, etc.
- Fallback to keyword-based analysis (lines 138-185)

#### C. world_os_architecture.py (lines 1-278)
**5-Layer Architecture Definition**:
```
Layer 1: FOUNDATION
- core_engines
- core_storage

Layer 2: ORCHESTRATION
- orchestrator
- agent_collaboration

Layer 3: EXECUTION
- agent_system
- tool_registry

Layer 4: INTERFACE
- api_endpoints
- websocket_server

Layer 5: APPLICATION
- (User-facing apps)
```

---

## 4. 15 FOUNDER CLONES SYSTEM

### File: core/company_structure.py (lines 51-102)

**FounderClone Class** with 15 autonomous founders:

| Role | Name | Capabilities |
|------|------|-------------|
| CEO | CEO Clone | vision, strategy, fundraising, leadership |
| CTO | CTO Clone | technology, architecture, innovation, research |
| CFO | CFO Clone | finance, planning, compliance, investment |
| COO | COO Clone | operations, scaling, efficiency, logistics |
| CPO | CPO Clone | product, ux, design, roadmap |
| CHRO | CHRO Clone | hr, hiring, culture, team |
| CMO | CMO Clone | marketing, brand, growth, pr |
| CLO | CLO Clone | legal, contracts, ip, compliance |
| CSO | CSO Clone | security, risk, audit, compliance |
| CDO | CDO Clone | data, analytics, ml, insights |
| CIO | CIO Clone | infrastructure, cloud, devops, reliability |
| VP_Engineering | VP Engineering Clone | engineering, code_quality, delivery |
| VP_Product | VP Product Clone | product_delivery, features, user_feedback |
| VP_Sales | VP Sales Clone | sales, partnerships, revenue, growth |
| VP_Operations | VP Operations Clone | operations, support, efficiency, nepal_region |

### Base Agent Class: core/agents/base_agent.py (lines 15-50)
```python
class BaseAgent(ABC):
    - agent_id: str
    - role: str
    - goal: str
    - backstory: str
    - tools: List[str]
    - skills: List[str]
    - llm_provider: str = "gemma-4"
    - task_queue: List
    - completed_tasks: List
```

---

## 5. UNIVERSAL API CONNECTOR

### File: core/universal_auto_api/universal_api_connector.py

**Purpose**: Connect ANY API from chat

**Key Methods**:
- `auto_connect(message)` - Main entry point
- `parse_api_from_chat(message)` - Extract API info from natural language
- `_detect_service_from_key(key)` - Auto-detect from key patterns
- `_detect_base_url(service)` - Get correct base URL

**Supported Services**:
```python
API_PATTERNS = {
    'AIza': 'google_gemini',      # Google AI
    'nvapi-': 'nvidia_nim',        # NVIDIA NIM
    'sk-': 'openai',               # OpenAI
    'sk-ant-': 'anthropic',        # Anthropic
    'gsk_': 'groq',                 # Groq
}

BASE_URLS = {
    'nvidia_nim': 'https://integrate.api.nvidia.com/v1',
    'openai': 'https://api.openai.com/v1',
    'anthropic': 'https://api.anthropic.com',
    'google_gemini': 'https://generativelanguage.googleapis.com',
    'groq': 'https://api.groq.com/openai/v1'
}
```

---

## 6. AUTO-AUTOMATION ENGINE

### File: core/universal_auto_api/auto_automation_engine.py

**Purpose**: Natural language → Automation rules

**Trigger Types**:
1. **Time-based**: "every morning at 8am check email"
2. **Condition-based**: "when cpu > 90% kill heavy processes"
3. **Event-based**: "on shutdown backup files"

**Key Methods**:
- `create_automation(message)` - Main entry
- `parse_automation_from_chat(message)` - Parse natural language
- `parse_time_based(message)` - Extract schedule
- `parse_condition_based(message)` - Extract condition
- `parse_event_based(message)` - Extract event trigger

**Rule Storage**: `./data/automation_rules.json`

---

## 7. NVIDIA NIM INTEGRATION

### File: core/external_apis/nvidia_nim_connector.py

**Purpose**: Access 90+ AI models

**Key Methods**:
- `list_available_models()` - Returns 90+ models
- `call_model(model_id, prompt)` - Call specific model
- `get_model_details(model_id)` - Get model info

**Available Providers**:
- Meta (Llama, CodeLlama)
- Google (Gemma)
- Microsoft (Phi-3)
- Mistral (Mistral, Mixtral)
- DeepSeek (DeepSeek R1)
- And more...

---

## 8. AI TOOLS DISCOVERY

### File: core/external_apis/ai_tools_discovery.py

**Purpose**: 2000+ AI tools database

**Key Methods**:
- `search_tools(query)` - Search by keyword
- `recommend_tools(task)` - Get recommendations
- `get_popular_tools()` - Top 10 list
- `filter_by_category(category)` - Category filter
- `filter_by_price(price_type)` - Price filter

---

## 9. CURRENT CHAT ARCHITECTURE PROBLEM

### Current Flow (DIRECT PATTERN MATCHING):
```
User Input
    ↓
ASIM chat()
    ↓
Pattern Match (if/elif chain)
    - "hey" → Greeting
    - "api key" → API Connect
    - "every" → Automation
    - "scan" → System Scan
    ↓
Direct Response (NO LLM)
    OR
LLM Fallback (if no match)
```

### Problems:
1. **Rigid**: Can only handle pre-defined patterns
2. **No Learning**: Doesn't adapt to user preferences
3. **Limited Understanding**: Can't handle complex/combined requests
4. **Hardcoded**: Adding new patterns requires code changes

---

## 10. NEW INTEGRATED ARCHITECTURE (Created)

### Files Created:
```
core/llm_interpreter/
├── __init__.py (18 bytes)
├── llm_interpreter.py (424 lines)
└── asim_system_prompt.txt (168 lines)
```

### New Flow (LLM AS BRAIN):
```
User Input
    ↓
ASIM chat()
    ↓
LLM Interpreter (with System Prompt)
    - LLM reads ASIM capabilities
    - Interprets user intent
    - Returns JSON command
    ↓
ASIM Execute Command
    - API Connect
    - Automation
    - System Control
    ↓
User Response
    ↓
Learning (Store pattern)
```

### System Prompt Structure:
```
1. ASIMNEXUS Architecture Overview
2. Universal API Connector rules
3. Auto-Automation Engine rules
4. System Control capabilities
5. AI Tools Discovery
6. NVIDIA NIM Integration
7. 15 Founder Clones
8. JSON Response Format
9. Learning Rules
10. Examples
```

---

## 11. STEP-BY-STEP INTEGRATION PLAN

### Phase 1: Update main.py (HIGH PRIORITY)
```
1. Import LLM Interpreter
   from core.llm_interpreter import get_llm_interpreter

2. Modify GemmaASIM.chat() method
   - Add interpreter initialization
   - Send message to interpreter instead of pattern matching
   - Execute interpreted command
   - Return result

3. Remove/Move direct pattern matching
   - Keep as fallback only
   - Let LLM handle primary interpretation
```

### Phase 2: Enhance LLM Interpreter
```
1. Add more capability handlers
   - Founder clone delegation
   - Multi-step task planning
   - Complex query handling

2. Improve learning system
   - Store user preferences
   - Adapt responses
   - Pattern recognition

3. Add caching
   - Cache common interpretations
   - Speed up responses
```

### Phase 3: Test & Validate
```
1. Test all 10 use cases
2. Validate learning system
3. Check error handling
4. Performance testing
```

### Phase 4: Documentation
```
1. Update architecture docs
2. Create user guide
3. Add examples
4. Document API changes
```

---

## 12. KEY FILES TO MODIFY

| File | Lines | Purpose | Changes Needed |
|------|-------|---------|----------------|
| main.py | 1922 | Entry point | Integrate LLM Interpreter |
| core/chat.py | 376 | Chat interface | Use interpreter |
| core/api_endpoints.py | 1167 | API routes | Update chat endpoint |
| core/unified_orchestrator.py | 464 | Orchestrator | Use interpreter |

---

## 13. INTEGRATION CHECKLIST

- [ ] Update main.py GemmaASIM.chat()
- [ ] Remove hardcoded pattern matching
- [ ] Add LLM Interpreter integration
- [ ] Test API connection flow
- [ ] Test automation flow
- [ ] Test system control flow
- [ ] Test learning system
- [ ] Update documentation
- [ ] Create test cases
- [ ] Validate error handling

---

**Next Action**: Update main.py to use LLM Interpreter
