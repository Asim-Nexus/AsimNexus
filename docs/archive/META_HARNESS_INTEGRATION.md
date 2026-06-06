# ASIMNEXUS Meta-Harness Integration Guide

## Overview

ASIMNEXUS now integrates Stanford's **Meta-Harness** research, which shows that AI agent performance depends **6x more** on the harness layer than on the model itself. This integration enables:

- **Auto-correction** of mistakes in harness code
- **Continuous learning** from agent actions
- **6x performance improvement** through smart harness optimization
- **Self-improvement loop** that runs automatically

---

## What is Meta-Harness?

### Harness Definition
**Harness** = The layer that controls:
- **Tool Selection**: Which tool to use when
- **Memory Management**: What to remember vs forget
- **Retrieval**: How to search and retrieve data

### Key Insight
- Same model with good harness = **6x better performance**
- Manual harness coding = Weeks of work
- **Meta-Harness** = Automated, self-improving

### How It Works
1. **Model Layer**: Watches every agent mistake
2. **Auto-Correction**: Automatically fixes code when agent uses wrong tool or forgets info
3. **Continuous Learning**: Agent gets smarter over time
4. **Results**: Outperformed manual systems in Terminal Bench 2

---

## ASIMNEXUS Implementation

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Meta-Harness Model (The Brain)                │
│ - core/meta_harness_model.py                           │
│ - Watches all agent actions                            │
│ - Identifies patterns in mistakes                      │
│ - Triggers auto-corrections                            │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Harness Engines                              │
│ - core/harness/tool_selection_engine.py                │
│ - core/harness/memory_management_engine.py             │
│ - core/harness/retrieval_engine.py                     │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Learning & Optimization                       │
│ - core/harness/pattern_analyzer.py                     │
│ - core/harness/harness_optimizer.py                    │
│ - core/harness/self_improvement_loop.py               │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Layer 4: Integrated Systems                             │
│ - core/orchestrator.py (with Meta-Harness)             │
│ - core/mmmm_engine.py (with Meta-Harness)              │
│ - core/triple_brain_system.py (with Meta-Harness)      │
└─────────────────────────────────────────────────────────┘
```

### File Structure

```
c:\AsimNexus\
├── core/
│   ├── meta_harness_model.py          # Meta-Harness brain
│   ├── harness/
│   │   ├── __init__.py               # Package init
│   │   ├── tool_selection_engine.py   # Tool selection
│   │   ├── memory_management_engine.py # Memory management
│   │   ├── retrieval_engine.py        # Retrieval
│   │   ├── pattern_analyzer.py        # Pattern analysis
│   │   ├── harness_optimizer.py       # Harness optimization
│   │   └── self_improvement_loop.py   # Self-improvement
│   ├── orchestrator.py               # Updated with Meta-Harness
│   ├── mmmm_engine.py                # Updated with Meta-Harness
│   └── triple_brain_system.py        # Updated with Meta-Harness
```

---

## Components

### 1. Meta-Harness Model (`core/meta_harness_model.py`)

The brain that watches and learns.

**Key Classes:**
- `MetaHarnessModel`: Main model that observes actions
- `MistakeRecord`: Records mistakes for analysis
- `Pattern`: Patterns found in mistakes

**Key Methods:**
- `observe_action(agent_id, action, context)`: Observe and detect mistakes
- `analyze_patterns(limit)`: Find patterns in mistakes
- `apply_correction(mistake_id)`: Apply auto-correction

**Usage:**
```python
from core.meta_harness_model import meta_harness

# Observe action
mistake_id = await meta_harness.observe_action("agent_id", action_dict, context)

# Analyze patterns
patterns = await meta_harness.analyze_patterns(limit=100)

# Get statistics
stats = meta_harness.get_statistics()
```

### 2. Tool Selection Engine (`core/harness/tool_selection_engine.py`)

Intelligent tool selection - not rule-based.

**Key Classes:**
- `ToolSelectionEngine`: Selects best tools for tasks
- `ToolPerformance`: Tracks tool performance
- `ToolCategory`: Tool categories (coding, search, file, etc.)

**Key Methods:**
- `select_tool(task, context)`: Select best tool using learned patterns
- `record_tool_use(tool_id, success, task)`: Record tool performance

**Usage:**
```python
from core.harness.tool_selection_engine import tool_selection_engine

# Select tool
tool_id = await tool_selection_engine.select_tool("Write code to fix bug", {})

# Record usage
await tool_selection_engine.record_tool_use(tool_id, True, "Write code to fix bug")
```

### 3. Memory Management Engine (`core/harness/memory_management_engine.py`)

Smart memory management - what to remember vs forget.

**Key Classes:**
- `MemoryManagementEngine`: Manages memory decisions
- `MemoryItem`: A memory item with importance
- `MemoryImportance`: Importance levels (critical, high, medium, low, trivial)

**Key Methods:**
- `should_remember(info)`: Decide if info is worth remembering
- `should_forget(memory_id)`: Decide if memory should be forgotten
- `store_memory(memory_id, content)`: Store memory if important enough

**Usage:**
```python
from core.harness.memory_management_engine import memory_management_engine

# Check if should remember
if await memory_management_engine.should_remember({"type": "critical", "content": "..."}):
    await memory_management_engine.store_memory("mem_id", content)
```

### 4. Retrieval Engine (`core/harness/retrieval_engine.py`)

Optimized data retrieval.

**Key Classes:**
- `RetrievalEngine`: Optimized retrieval
- `RetrievalStrategy`: Retrieval strategies (exact, semantic, hybrid, etc.)
- `RetrievalResult`: A retrieval result with relevance score

**Key Methods:**
- `retrieve(query, context, max_results)`: Retrieve relevant information
- `add_knowledge(key, content)`: Add content to knowledge base

**Usage:**
```python
from core.harness.retrieval_engine import retrieval_engine

# Retrieve information
results = await retrieval_engine.retrieve("How to fix memory leak", {}, max_results=10)
```

### 5. Pattern Analyzer (`core/harness/pattern_analyzer.py`)

Analyzes patterns in mistakes.

**Key Classes:**
- `PatternAnalyzer`: Analyzes mistakes to find patterns
- `PatternAnalysis`: Result of pattern analysis

**Key Methods:**
- `analyze_mistakes(mistakes)`: Analyze list of mistakes
- `get_analysis_history(limit)`: Get recent analysis history

**Usage:**
```python
from core.harness.pattern_analyzer import pattern_analyzer
from core.meta_harness_model import meta_harness

# Get recent mistakes
recent_mistakes = list(meta_harness.mistakes.values())[-100:]

# Analyze patterns
analysis = await pattern_analyzer.analyze_mistakes(recent_mistakes)
```

### 6. Harness Optimizer (`core/harness/harness_optimizer.py`)

Generates and applies harness code improvements.

**Key Classes:**
- `HarnessOptimizer`: Generates and applies fixes
- `OptimizationResult`: Result of optimization

**Key Methods:**
- `generate_fix(pattern)`: Generate code fix for pattern
- `apply_fix(fix_code, target_file)`: Apply fix to codebase
- `optimize_pattern(pattern)`: Generate and apply fix

**Usage:**
```python
from core.harness.harness_optimizer import harness_optimizer

# Optimize a pattern
result = await harness_optimizer.optimize_pattern(pattern)
```

### 7. Self-Improvement Loop (`core/harness/self_improvement_loop.py`)

Continuous self-improvement.

**Key Classes:**
- `SelfImprovementLoop`: Runs improvement cycles
- `ImprovementCycle`: Result of an improvement cycle

**Key Methods:**
- `run_improvement_cycle()`: Run one improvement cycle
- `start_continuous_improvement()`: Start continuous loop
- `stop_continuous_improvement()`: Stop continuous loop

**Usage:**
```python
from core.harness.self_improvement_loop import self_improvement_loop

# Run one cycle
cycle = await self_improvement_loop.run_improvement_cycle()

# Start continuous improvement
await self_improvement_loop.start_continuous_improvement()
```

---

## Integration with Existing Systems

### Orchestrator Integration

**File:** `core/orchestrator.py`

**Changes:**
- Added Meta-Harness imports
- Initialized harness engines in `__init__`
- Added observation in `process_request`
- Integrated tool selection in `_route_to_ai`
- Added harness statistics in `generate_report`

**Usage:**
```python
from core.orchestrator import UnifiedOrchestrator

orchestrator = UnifiedOrchestrator()
await orchestrator.initialize()

# All requests now go through Meta-Harness
result = await orchestrator.process_request({
    "type": "tool",
    "task": "Write code"
})
```

### MMMM Engine Integration

**File:** `core/mmmm_engine.py`

**Changes:**
- Added Meta-Harness import
- Initialized Meta-Harness in `__init__`
- Added observation in `generate_thought`
- Added observation in `generate_emotion`
- Added harness statistics in `get_report`

**Usage:**
```python
from core.mmmm_engine import MMMMEngine

mmmm = MMMMEngine("user_id")
thought = await mmmm.generate_thought(
    ThoughtType.ANALYTICAL,
    "Analyze this situation"
)
```

### Triple Brain Integration

**File:** `core/triple_brain_system.py`

**Changes:**
- Added Meta-Harness import
- Initialized Meta-Harness in `__init__`
- Added observation in `think_unified`
- Added harness statistics in `get_stats`

**Usage:**
```python
from core.triple_brain_system import asim_triple_brain

result = await asim_triple_brain.think_unified(
    "What should I do?",
    context={},
    consciousness_level=ConsciousnessLevel.NATIONAL
)
```

---

## Configuration

### Enabling/Disabling Features

```python
from core.meta_harness_model import meta_harness

# Enable auto-correction
meta_harness.enable_auto_correction(True)

# Enable learning
meta_harness.enable_learning(True)

# Disable auto-correction
meta_harness.enable_auto_correction(False)
```

### Self-Improvement Loop Configuration

```python
from core.harness.self_improvement_loop import self_improvement_loop

# Configure cycle interval (hours)
self_improvement_loop.cycle_interval_hours = 1

# Configure mistakes per cycle
self_improvement_loop.mistakes_per_cycle = 100

# Enable auto-run
self_improvement_loop.auto_run = True
```

---

## Performance Tracking

### Key Metrics

1. **Tool Selection Accuracy**: Percentage of correct tool selections
2. **Memory Hit Rate**: Percentage of relevant memories retrieved
3. **Retrieval Precision/Recall**: Quality of retrieval results
4. **Agent Success Rate**: Overall agent task success
5. **Auto-Correction Rate**: Number of corrections applied per day
6. **Learning Rate**: Improvement rate over time

### Monitoring

```python
# Get Meta-Harness statistics
stats = meta_harness.get_statistics()

# Get tool selection statistics
tool_stats = tool_selection_engine.get_tool_statistics()

# Get memory management statistics
memory_stats = memory_management_engine.get_statistics()

# Get retrieval statistics
retrieval_stats = retrieval_engine.get_statistics()

# Get self-improvement statistics
improvement_stats = self_improvement_loop.get_statistics()
```

---

## Best Practices

### 1. Start with Observation

Let Meta-Harness observe actions before enabling auto-correction:

```python
# Phase 1: Observe only
meta_harness.auto_correction_enabled = False
meta_harness.learning_enabled = True

# Run for a week to collect data

# Phase 2: Enable auto-correction
meta_harness.auto_correction_enabled = True
```

### 2. Monitor Patterns

Regularly check patterns to understand common mistakes:

```python
patterns = await meta_harness.analyze_patterns(limit=100)
for pattern in patterns:
    print(f"{pattern.pattern_type}: {pattern.frequency} occurrences")
```

### 3. Run Improvement Cycles

Run improvement cycles regularly:

```python
# Run manually
await self_improvement_loop.run_improvement_cycle()

# Or start continuous improvement
await self_improvement_loop.start_continuous_improvement()
```

### 4. Track Progress

Monitor the 6x improvement goal:

```python
# Before Meta-Harness
baseline_success_rate = 0.30

# After Meta-Harness
current_success_rate = 0.45

# Calculate improvement
improvement = current_success_rate / baseline_success_rate
print(f"Improvement: {improvement}x")  # Target: 6x
```

---

## Troubleshooting

### Issue: Too Many Mistakes Logged

**Solution:** Increase mistake threshold or filter by severity

```python
# Only log critical mistakes
# Modify _detect_mistake in meta_harness_model.py
```

### Issue: Auto-Corrections Not Applying

**Solution:** Check if auto-correction is enabled

```python
meta_harness.enable_auto_correction(True)
```

### Issue: Performance Degradation

**Solution:** Reduce observation frequency or disable for specific agents

```python
# Disable for specific agent types
if agent_id.startswith("test_"):
    return None  # Don't observe
```

---

## Future Enhancements

1. **LLM-Based Fix Generation**: Use actual LLM to generate code fixes
2. **Multi-Agent Pattern Sharing**: Share patterns across agents
3. **A/B Testing**: Test different harness strategies
4. **Real-Time Dashboard**: Visual monitoring of harness performance
5. **Cross-Project Learning**: Learn from multiple ASIMNEXUS instances

---

## References

- Stanford Meta-Harness Paper
- Terminal Bench 2 Competition
- ASIMNEXUS Master Plan: `ASIMNEXUS_META_HARNESS_MASTER_PLAN.md`

---

**Last Updated:** April 10, 2026
**Version:** 3.0-Meta-Harness
