"""Knowledge management package — vector stores, cosmos engine, and RAG."""

from core.knowledge.chunker import RecursiveCharacterTextSplitter
from core.knowledge.embeddings import EmbeddingsService
from core.knowledge.rag_engine import RAGEngine
from core.knowledge.vector_store import VectorStore

# Backward-compatible alias
Chunker = RecursiveCharacterTextSplitter


# Re-export from root-level module: language_manager.py
from core.language_manager import (
    LanguageManager,
    get_language_manager,
)



# Re-export from root-level module: vectormemory.py
from core.vectormemory import (
    EmbeddingBackend,
    Memory,
    MemoryType,
    SearchResult,
    VectorMemory,
    get_vector_memory,
    reset_vector_memory,
)


__all__ = [
    "RecursiveCharacterTextSplitter",
    "Chunker",
    "EmbeddingsService",
    "RAGEngine",
    "VectorStore",
]
