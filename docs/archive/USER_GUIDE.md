# ASIMNEXUS World OS - User Guide

## Getting Started

ASIMNEXUS is a super-intelligent World OS that automates all digital and technology tasks. This guide shows you how to use it.

---

## Basic Usage

### 1. Initialize ASIMNEXUS

```python
from asim import ASIMNEXUS

# Create ASIMNEXUS instance
asim = ASIMNEXUS("your_user_id")
```

### 2. Use AI Capabilities

```python
# Generate text with AI
response = asim.universal_gateway.generate(
    "Write a Python function to sort a list"
)
print(response)

# Use specific model
response = asim.universal_gateway.generate(
    "Explain quantum computing",
    model="gpt-4"
)
```

### 3. Use Memory System

```python
# Add memory
memory_id = asim.vector_memory.add_memory(
    "I prefer morning meetings",
    metadata={"category": "preference"}
)

# Search memory
results = asim.vector_memory.search_memories("meetings")
for result in results:
    print(f"{result['text']} (score: {result['score']})")
```

### 4. Use RAG System

```python
# Add knowledge
asim.rag.add_knowledge(
    "ASIMNEXUS can automate 15 global systems",
    namespace="capabilities"
)

# Query with RAG
response = asim.rag.query_with_rag(
    "What can ASIMNEXUS automate?",
    namespace="capabilities"
)
print(response)
```

### 5. Use Founder Clones

```python
# Get all founders status
status = asim.founder_clones.get_all_founders_status()
print(status)

# Assign task to specific founder
await asim.founder_clones.assign_task_to_founder(
    FounderRole.CTO,
    "Review system architecture"
)

# Auto-assign task
await asim.founder_clones.auto_assign_task(
    "Create marketing strategy",
    "marketing"
)
```

### 6. Use Global Systems

```python
# Healthcare
health_status = asim.healthcare_system.get_patient_status("patient_id")

# Education
courses = asim.education_system.get_courses("student_id")

# Financial
balance = asim.financial_system.get_balance("account_id")
```

### 7. Use Life Dimensions

```python
# Get life balance report
report = await asim.life_dimensions.get_life_balance_report()
print(report)

# Update dimension
await asim.life_dimensions.update_dimension(
    LifeDimension.PHYSICAL_HEALTH,
    0.8
)
```

---

## Advanced Usage

### 1. Custom CrewAI Agents

```python
from core.crewai_integration import ASIMCrewAIOrchestrator

# Create orchestrator
orchestrator = ASIMCrewAIOrchestrator()

# Create custom agent
agent = orchestrator.create_agent(
    agent_id="custom_agent",
    role="Data Analyst",
    goal="Analyze data and provide insights",
    backstory="Expert in data analysis and visualization"
)

# Create crew
crew = orchestrator.create_sequential_crew(
    crew_id="data_analysis",
    agents=[agent],
    tasks=[...]
)

# Execute crew
result = orchestrator.execute_crew("data_analysis", inputs={...})
```

### 2. Custom MCP Tools

```python
from connectors.mcp_connector import ASIMMCPConnector

# Create connector
mcp = ASIMMCPConnector()

# Register custom tool
def custom_tool(params):
    return f"Custom tool executed with {params}"

mcp.register_tool(
    name="my_tool",
    description="My custom tool",
    tool_type=MCPToolType.TOOL,
    handler=custom_tool,
    parameters={"input": "string"}
)

# Invoke tool
result = mcp.invoke_tool("my_tool", {"input": "test"})
```

### 3. Observability

```python
from core.observability import ASIMObservability

# Create observability
obs = ASIMObservability(
    public_key="your_key",
    secret_key="your_secret"
)

# Start trace
trace_id = obs.start_trace("my_trace", "Operation name")

# Log events
obs.log_event(trace_id, "step1", {"data": "value"})

# End trace
obs.end_trace(trace_id, status="completed")

# Export traces
obs.export_traces("traces.json")
```

### 4. Human Oversight

```python
from core.human_oversight import ASIMHumanOversight, ActionRisk

# Create oversight
oversight = ASIMHumanOversight(auto_approve_threshold=ActionRisk.LOW)

# Request approval
request_id = oversight.request_approval(
    action_type="delete_file",
    description="Delete important file",
    proposed_action={"file": "data.txt"},
    requester="system",
    risk_level=ActionRisk.HIGH
)

# Approve request
oversight.approve_request(request_id, human_response="Approved")
```

### 5. Guardrails

```python
from core.guardrails import ASIMGuardrails

# Create guardrails
guardrails = ASIMGuardrails()

# Check content
result = guardrails.check_content("This is safe content")
if result.triggered:
    print(f"Blocked: {result.message}")

# Check PII
result = guardrails.check_pii("My email is test@example.com")
if result.triggered:
    print(f"Redacted: {result.modified_content}")

# Run all checks
results = guardrails.run_all_checks(content, user_id="user")
```

---

## Configuration

### Environment Variables

Set in `.env` file:

```bash
# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# Vector Database
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1

# Observability
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...

# Cloud
AWS_ACCESS_KEY=AKIA...
AWS_SECRET_KEY=...
```

### User Configuration

Edit `config/profiles/user_asim.json`:

```json
{
  "user_id": "your_id",
  "enabled_services": {
    "openai": true,
    "anthropic": true,
    "google": true
  },
  "preferences": {
    "default_model": "gpt-4",
    "max_tokens": 4096,
    "temperature": 0.7
  }
}
```

---

## Common Tasks

### Task 1: Automate Document Analysis

```python
# Use RAG to analyze documents
asim.rag.add_knowledge(document_text, namespace="docs")
analysis = asim.rag.query_with_rag("Summarize this document", namespace="docs")
```

### Task 2: Automate Data Processing

```python
# Use Data founder clone
await asim.founder_clones.auto_assign_task(
    "Process sales data and generate report",
    "data"
)
```

### Task 3: Automate Communication

```python
# Use Communication system
asim.communication_system.send_email(
    to="user@example.com",
    subject="Automated Report",
    body=report_text
)
```

### Task 4: Automate Monitoring

```python
# Use observability to monitor operations
obs.start_trace("monitoring", "System health")
# ... operations ...
obs.end_trace("monitoring", status="completed")
```

---

## Best Practices

1. **Always use logging instead of print**
2. **Use guardrails for user inputs**
3. **Use human oversight for critical actions**
4. **Monitor with observability**
5. **Use rate limiting for API calls**
6. **Use retry handler for resilient operations**
7. **Use context management for long conversations**
8. **Use state persistence for durability**

---

## Troubleshooting

### Issue: Slow response times
**Solution:** Use context management to reduce token usage

### Issue: High API costs
**Solution:** Use rate limiting and spot instances

### Issue: Memory not found
**Solution:** Check Pinecone API key and namespace

### Issue: Founder clone not responding
**Solution:** Check founder status and reassign task

---

## Support

- Documentation: https://docs.asimnexus.ai
- Community: https://community.asimnexus.ai
- Issues: https://github.com/your-repo/AsimNexus/issues
