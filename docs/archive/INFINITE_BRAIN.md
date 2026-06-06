# ASIMNEXUS Infinite Brain Documentation

## Overview

ASIMNEXUS Infinite Brain is a Personal Super-Clone + Nexus Brain + RAG System that enables intelligent knowledge management, contextual retrieval, and personalized AI interactions.

## Architecture

### Core Components

1. **Atomic Notes** - Small, focused notes (50-300 words) in Markdown/JSON format
2. **16 Node Types** - Fact, Decision, Hypothesis, Question, Playbook, Concept, Source, Goal, Risk, Lesson, Principle, Memory, Project, Area, Resource, Archive
3. **13 Edge Types** - Supports, Contradicts, Depends_On, Derived_From, Precedes, Follows, Enables, Blocks, Exemplifies, Generalizes, Parent_Of, Child_Of, Related_To
4. **AI-Led Maintenance** - Automatic splitting, tagging, edge creation, cleanup, and linking

### Technical Stack

- **Graph Database**: Neo4j (recommended) or NetworkX
- **Vector DB**: ChromaDB or Pinecone (for semantic search)
- **Hybrid Retrieval**: Vector + Graph (GraphRAG)
- **Storage**: Encrypted vault (Supabase + IPFS option)

## Module Structure

```
core/infinite_brain/
├── __init__.py              # Package initialization
├── node_types.py            # Node and edge type definitions
├── node_classifier.py       # LLM-based node classification
├── edge_builder.py          # Relationship detection
├── graph_maintainer.py      # AI-led graph maintenance
├── scoped_retriever.py      # GraphRAG retrieval
├── personal_clone.py        # Digital twin implementation
└── chat_integration.py      # Chat engine integration
```

## Usage

### 1. Creating Atomic Notes

```python
from core.infinite_brain import get_node_classifier

classifier = get_node_classifier()

# Create atomic notes from raw text
raw_text = "Your long text here..."
atomic_notes = classifier.create_atomic_notes(raw_text)

for note in atomic_notes:
    print(f"Note: {note.content}")
    print(f"Type: {note.node_type.value}")
    print(f"Tags: {note.tags}")
```

### 2. Building Knowledge Graph

```python
from core.infinite_brain import get_edge_builder, get_graph_maintainer

edge_builder = get_edge_builder()
maintainer = get_graph_maintainer()

# Add notes to graph
for note in atomic_notes:
    maintainer.add_note(note)

# Build edges between notes
edges = edge_builder.build_edges_for_notes(atomic_notes)

for edge in edges:
    maintainer.add_edge(edge)
```

### 3. AI-Led Maintenance

```python
# Run full maintenance cycle
results = maintainer.run_maintenance()

print(f"Duplicate notes removed: {results['duplicate_notes_removed']}")
print(f"Weak edges removed: {results['weak_edges_removed']}")
print(f"New links created: {results['new_links_created']}")
```

### 4. Graph Retrieval

```python
from core.infinite_brain import get_scoped_retriever

retriever = get_scoped_retriever()
retriever.load_graph(maintainer.notes, maintainer.edges)

# Retrieve by node type
decisions = retriever.retrieve_by_node_type(NodeType.DECISION)

# Hop through graph
related_notes = retriever.hop_from_note(note_id, max_hops=2)

# Retrieve supporting notes
supporting = retriever.retrieve_supporting_notes(note_id)
```

### 5. Personal Clone

```python
from core.infinite_brain import get_personal_clone

clone = get_personal_clone(user_id="user123")

# Create personality profile
clone.create_personality_profile(
    traits={"openness": 0.8, "conscientiousness": 0.9},
    communication_style="formal",
    decision_making_style="analytical",
    values=["innovation", "quality", "efficiency"],
    preferences={"language": "english"}
)

# Add memory note
clone.add_memory_note("Important insight from meeting", ["meeting", "insight"])
```

### 6. Chat Integration

```python
from core.infinite_brain import get_chat_integration

chat = get_chat_integration()

# Process query with Infinite Brain context
result = chat.process_query(
    query="Analyze my last year's pricing decisions",
    user_id="user123"
)

print(f"Response: {result['response']}")
print(f"Query type: {result['query_type']}")
print(f"Relevant notes: {result['relevant_notes_count']}")
```

## Query Types

The chat integration automatically classifies queries into types:

1. **decision_analysis** - Analyze decision history
2. **contradiction_check** - Check for contradictions in notes
3. **playbook_request** - Retrieve relevant playbooks
4. **goal_support** - Find notes supporting goals
5. **risk_assessment** - Identify risks
6. **lesson_retrieval** - Retrieve lessons learned
7. **general** - General knowledge retrieval

## Example Chat Queries

```
"Analyze my last year's pricing decisions"
"Does this new business idea contradict my previous principles?"
"Show me playbooks that support my health goal"
"What are the risks I've identified for this project?"
"What lessons have I learned about leadership?"
```

## Graph Operations

### Hopping Through Graph

```python
# Hop from a note with specific edge type
related = retriever.hop_from_note(
    note_id="note_abc123",
    edge_type=EdgeType.SUPPORTS,
    max_hops=2
)
```

### Finding Paths

```python
# Find shortest path between notes
path = retriever.retrieve_by_path(
    start_note_id="note_abc123",
    end_note_id="note_def456",
    max_depth=5
)
```

### Contextual Retrieval

```python
# Retrieve with context from specific notes
results = retriever.retrieve_contextual(
    query="pricing strategy",
    context_note_ids=["note_abc123", "note_def456"],
    max_hops=2
)
```

## Maintenance Operations

### Automatic Cleanup

- **Duplicate Removal**: Removes notes with >90% similarity
- **Weak Edge Removal**: Removes edges with strength <0.3
- **Orphan Note Removal**: Removes notes with no edges
- **Auto-Linking**: Creates edges between related notes
- **Consolidation**: Merges similar notes (>80% similarity)

### Manual Operations

```python
# Remove specific note
maintainer.remove_note(note_id)

# Remove specific edge
maintainer.remove_edge(edge_id)

# Cleanup duplicates
count = maintainer.cleanup_duplicate_notes()

# Cleanup weak edges
count = maintainer.cleanup_weak_edges(threshold=0.3)
```

## Personal Clone Features

### Personality Profile

Tracks user traits, communication style, decision-making style, values, and preferences for personalized responses.

### Knowledge Profile

Tracks expertise areas, learning goals, known concepts, and unknown concepts for adaptive learning.

### Interaction History

Records all interactions with satisfaction scores for continuous improvement.

### Response Adaptation

Adapts AI responses based on user's communication style (formal/casual).

## Integration with Chat Engine

The chat integration provides:

1. **Query Classification** - Automatic detection of query intent
2. **Graph-Based Context** - Retrieves relevant notes from knowledge graph
3. **Personalized Responses** - Adapts responses based on user profile
4. **Interaction Recording** - Tracks all interactions for learning
5. **Note Addition** - Allows adding notes directly from chat

## Best Practices

1. **Keep Notes Atomic** - Each note should be 50-300 words focused on a single idea
2. **Use Consistent Tagging** - Use meaningful tags for better retrieval
3. **Regular Maintenance** - Run maintenance cycles weekly
4. **Review Relationships** - Periodically review auto-generated edges
5. **Update Profiles** - Keep personality and knowledge profiles current

## Performance Considerations

- Graph size impacts retrieval speed
- Consider using Neo4j for large graphs (>10,000 notes)
- Use vector search for semantic similarity
- Cache frequently accessed notes
- Limit hop depth for complex queries

## Security

- All notes are stored in encrypted vault
- Personal clone data is isolated per user
- No cross-user data sharing
- Secure authentication required

## Future Enhancements

- Real-time collaboration
- Multi-modal notes (images, audio, video)
- Advanced NLP for better classification
- Machine learning for edge strength prediction
- Export/import functionality
- Visualization tools for graph exploration

## API Reference

See individual module files for detailed API documentation:
- `node_types.py` - Node and edge type definitions
- `node_classifier.py` - Classification API
- `edge_builder.py` - Relationship detection API
- `graph_maintainer.py` - Maintenance operations API
- `scoped_retriever.py` - Retrieval API
- `personal_clone.py` - Personal clone API
- `chat_integration.py` - Chat integration API

## Support

For issues or questions:
- GitHub: https://github.com/asimnexus/asimnexus
- Documentation: https://docs.asimnexus.ai
- Email: support@asimnexus.ai
