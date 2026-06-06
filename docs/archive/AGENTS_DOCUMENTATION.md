# ASIMNEXUS Multi-Agent System Documentation

## 📚 Complete Agent Reference Guide

---

## Overview

ASIMNEXUS features a comprehensive Multi-Agent Autonomous Company System with 5 core company agents and 4 Agentic AI features.

---

## 🤖 Company Agents

### 1. CEO Agent
**Location:** `agents/company/ceo_agent.py`

**Purpose:** Autonomous decision-making for company operations

**Capabilities:**
- Makes decisions on hiring, purchasing, projects, and strategy
- Auto-approves routine decisions (< $100)
- Generates 3 options for major decisions
- Handles approval workflows
- Manages daily budget ($1000/day)

**Key Methods:**
- `make_decision(decision_request)` - Main decision entry point
- `_classify_decision(req_type, amount, urgency)` - Categorizes decisions
- `_generate_options(request)` - Creates decision options
- `_auto_approve(decision)` - Auto-approves routine decisions

**Decision Types:**
- ROUTINE: Auto-approve (< $100)
- MODERATE: Inform but auto-approve (< $1000)
- MAJOR: Require human approval (>= $1000)
- CRITICAL: Explicit confirmation (hiring, contracts)

---

### 2. Architect Agent
**Location:** `agents/company/architect_agent.py`

**Purpose:** System design and technical architecture

**Capabilities:**
- Designs system architecture (microservices, serverless, etc.)
- Creates API specifications
- Plans integrations
- Estimates complexity
- Reviews designs
- Makes technical decisions

**Key Methods:**
- `design_system(requirements)` - Creates architecture design
- `_design_components(requirements, pattern)` - Designs components
- `_design_apis(requirements, components)` - Designs API endpoints
- `make_technical_decision(decision_request)` - Technical choices
- `review_design(design_id)` - Reviews architecture

**Architecture Patterns:**
- Microservices
- Event-Driven
- Layered
- Serverless
- Hexagonal
- Clean Architecture

---

### 3. DevOps Agent
**Location:** `agents/company/devops_agent.py`

**Purpose:** Deployment and infrastructure management

**Capabilities:**
- Creates CI/CD pipelines
- Manages deployments
- Provisions infrastructure
- Monitors services
- Scales resources
- Handles rollback

**Key Methods:**
- `create_pipeline(config)` - Creates CI/CD pipeline
- `deploy(pipeline_id, config)` - Executes deployment
- `provision_infrastructure(specs)` - Provisions cloud resources
- `monitor_service(service_name, metrics)` - Monitors health
- `scale_service(service_name, instances)` - Scales horizontally

**Pipeline Templates:**
- python_api
- node_webapp
- static_site

---

### 4. Marketing Agent
**Location:** `agents/company/marketing_agent.py`

**Purpose:** Content creation and promotion

**Capabilities:**
- Creates various content types (blogs, social, emails)
- Manages marketing campaigns
- Analyzes competitors
- Generates market insights
- Manages brand voice
- Tracks content calendar

**Key Methods:**
- `create_content(request)` - Creates marketing content
- `create_campaign(campaign_config)` - Creates campaigns
- `analyze_competitor(name, data)` - Competitor analysis
- `generate_market_insight(category, data)` - Market research
- `get_content_calendar(days)` - Content planning

**Content Types:**
- Blog posts
- Social media posts
- Email newsletters
- Video scripts
- Whitepapers
- Landing pages
- Press releases

---

### 5. Software Agency
**Location:** `agents/company/software_agency.py`

**Purpose:** Full software development lifecycle automation

**Capabilities:**
- Manages complete SDLC
- Coordinates all other agents
- Automates project stages
- Tracks quality metrics
- Generates code
- Runs tests

**SDLC Stages:**
1. Discovery - Requirements gathering
2. Design - Architecture planning
3. Implementation - Coding
4. Testing - QA and validation
5. Deployment - Production release
6. Maintenance - Ongoing support

**Key Methods:**
- `create_project(project_spec)` - Starts new project
- `_stage_discovery(project)` - Requirements phase
- `_stage_design(project)` - Architecture phase
- `_stage_implementation(project)` - Coding phase
- `_stage_testing(project)` - Testing phase
- `_stage_deployment(project)` - Release phase

---

## 🧠 Agentic AI Features

### 1. Self-Planning System
**Location:** `core/self_planning.py`

**Purpose:** Agents create their own task plans

**Features:**
- Automatic goal decomposition
- Task dependency management
- Strategy selection (sequential, parallel, adaptive, hierarchical)
- Progress tracking
- Dynamic replanning

**Planning Strategies:**
- SEQUENTIAL: Execute tasks one after another
- PARALLEL: Run independent tasks simultaneously
- ADAPTIVE: Adjust based on feedback
- HIERARCHICAL: Master task with subtasks

**Key Methods:**
- `create_plan(agent_id, goal, context)` - Creates task plan
- `execute_plan(plan_id, executor)` - Executes plan
- `replan(plan_id, new_goal)` - Adjusts existing plan

---

### 2. Tool Use System
**Location:** `core/tool_use.py`

**Purpose:** Agents dynamically use tools

**Features:**
- Tool registry with 10+ built-in tools
- Dynamic tool selection
- Automatic parameter inference
- Permission-based access
- Execution history tracking

**Built-in Tools:**
- web_search - Internet search
- http_request - API calls
- read_file - File reading
- write_file - File writing
- parse_json - JSON parsing
- format_data - Data formatting
- execute_python - Code execution
- send_message - Messaging
- search_knowledge - Knowledge search
- get_system_info - System metrics
- call_llm - LLM invocation

**Key Methods:**
- `register_tool(tool)` - Add new tool
- `execute_tool(tool_id, parameters)` - Execute tool
- `search_tools(query)` - Find relevant tools

---

### 3. Self-Correction System
**Location:** `core/self_correction.py`

**Purpose:** Agents detect and fix their own errors

**Features:**
- Error classification (syntax, logic, runtime, etc.)
- Automatic error detection
- Correction strategies
- Retry with backoff
- Performance tracking

**Correction Strategies:**
- Retry - Simple retry with exponential backoff
- Reparse - Adjust parsing settings
- Fallback - Use alternative approach
- Decompose - Break complex task
- Validate Input - Add validation

**Key Methods:**
- `monitor_execution(agent_id, task_func)` - Monitors with auto-correction
- `_attempt_correction(agent_id, error, task)` - Applies correction
- `analyze_error_patterns()` - Error insights

---

### 4. Collaboration System
**Location:** `core/agent_collaboration.py`

**Purpose:** Agents communicate and work together

**Features:**
- Inter-agent messaging
- Collaboration sessions
- Shared tasks
- Assistance requests
- Task delegation
- Progress updates

**Message Types:**
- TASK_REQUEST - Request to perform task
- TASK_RESPONSE - Response to request
- INFORMATION - Share info
- QUERY - Ask for info
- UPDATE - Status update
- ALERT - Urgent notification
- COORDINATION - Coordination
- DELEGATION - Task delegation
- APPROVAL - Request/grant approval

**Key Methods:**
- `send_message(sender, recipient, type, content)` - Send message
- `create_collaboration_session(name, mode, coordinator, participants)` - Create session
- `create_shared_task(session_id, title, subtasks)` - Share task
- `request_assistance(requester, task, capabilities)` - Ask for help

---

## 📚 Knowledge System

**Location:** `core/knowledge_system.py`

**Purpose:** Wikipedia-style personal knowledge base (Karpathy-style)

**Features:**
- Knowledge nodes (concepts, notes, projects, papers)
- Bidirectional linking
- Daily logs
- Reading queue
- Tag-based organization
- Graph visualization

**Node Types:**
- CONCEPT - Core concepts
- NOTE - Quick thoughts
- PROJECT - Documentation
- PAPER - Research articles
- BOOK - Reading notes
- TALK - Presentations
- CODE - Code snippets
- PERSON - Contacts
- TOOL - Software
- EVENT - Conferences

**Key Methods:**
- `create_node(title, type, content)` - Create knowledge node
- `link_nodes(from_id, to_id, type)` - Link nodes
- `search(query)` - Search knowledge
- `export_graph()` - Export for visualization

---

## 📊 Supporting Systems

### Company Integration
**Location:** `agents/company/company_integration.py`

Integrates all agents under CEO hierarchy with Agentic AI features.

### Communication Protocol
**Location:** `core/agent_protocol.py`

Standardized messaging with multiple protocols and delivery guarantees.

### Task Delegation
**Location:** `core/delegation_system.py`

CEO task delegation with smart agent matching and workload balancing.

### Performance Monitoring
**Location:** `core/agent_monitoring.py`

Agent performance tracking with alerts and optimization recommendations.

### Collaboration Dashboard
**Location:** `ui/collab_dashboard.py`

Real-time web dashboard for monitoring agent activity.

---

## 🚀 Quick Start

### Initialize All Components
```python
import asyncio

# Initialize all systems
async def initialize_all():
    # Company agents
    from agents.company.company_integration import initialize_company_integration
    company = await initialize_company_integration()
    
    # Knowledge system
    from core.knowledge_system import initialize_knowledge_system
    knowledge = await initialize_knowledge_system("user_id")
    
    # Dashboard
    from ui.collab_dashboard import initialize_dashboard
    dashboard = await initialize_dashboard(port=8080)
    
    return company, knowledge, dashboard

# Run
asyncio.run(initialize_all())
```

### Create a Project
```python
# Submit project request
result = await company.submit_request({
    "type": "project",
    "title": "E-commerce API",
    "description": "REST API for online store",
    "requester": "product_manager",
    "budget": 50000,
    "priority": "high",
    "data": {
        "requirements": {...},
        "tech_stack": {...}
    }
})
```

### Create Knowledge
```python
# Add knowledge node
node = await knowledge.create_node(
    title="Machine Learning Basics",
    node_type="concept",
    content="# ML Basics\n\nMachine learning is...",
    tags=["ai", "ml"],
    importance=4
)
```

---

## 📈 Architecture

```
ASIMNEXUS Multi-Agent System
│
├── 🤖 Company Agents (5)
│   ├── CEO Agent (Decision Maker)
│   ├── Architect Agent (Designer)
│   ├── DevOps Agent (Deployer)
│   ├── Marketing Agent (Promoter)
│   └── Software Agency (SDLC)
│
├── 🧠 Agentic AI (4)
│   ├── Self-Planning (Task planning)
│   ├── Tool Use (Dynamic tools)
│   ├── Self-Correction (Error fix)
│   └── Collaboration (Communication)
│
├── 📚 Knowledge System
│   ├── Knowledge Nodes
│   ├── Daily Logs
│   ├── Reading Queue
│   └── Graph Visualization
│
└── 📊 Infrastructure
    ├── Communication Protocol
    ├── Task Delegation
    ├── Performance Monitoring
    └── Collaboration Dashboard
```

---

## 🔧 Configuration

### Environment Variables
```bash
ASIM_DEBUG=true
ASIM_LOG_LEVEL=INFO
ASIM_DASHBOARD_PORT=8080
ASIM_MAX_AGENTS=20
ASIM_DEFAULT_TIMEOUT=30
```

### Agent Settings
```python
# In asim_config.py or environment
AGENT_SETTINGS = {
    "ceo": {
        "daily_budget": 1000,
        "auto_approve_threshold": 100
    },
    "architect": {
        "default_pattern": "microservices"
    },
    "devops": {
        "default_provider": "aws"
    }
}
```

---

## 📊 Metrics & Monitoring

### Agent Performance
- Task completion rate
- Response time
- Error rate
- Throughput
- Quality score
- Availability

### System Health
- Active agents
- Messages per second
- Task queue depth
- Memory usage
- Error counts

---

## 🛠️ Troubleshooting

### Common Issues

**Issue:** Agent not responding
**Solution:** Check agent health status in monitoring dashboard

**Issue:** High error rate
**Solution:** Review self-correction logs, may need manual intervention

**Issue:** Slow task completion
**Solution:** Check agent workload, may need task redistribution

---

## 📝 Version History

- v1.0.0 - Initial Multi-Agent System
- v1.1.0 - Added Agentic AI features
- v1.2.0 - Added Knowledge System
- v1.3.0 - Added Collaboration Dashboard

---

## 📞 Support

For issues and feature requests:
- Check documentation
- Review test suite: `tests/test_multi_agent.py`
- Monitor dashboard: `http://localhost:8080`

---

**Last Updated:** 2024
**Version:** 1.3.0
**Total Agents:** 5 (+ 50+ system agents)
**Total Features:** 17 major components
