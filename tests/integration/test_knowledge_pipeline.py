"""
AsimNexus — Knowledge Pipeline Integration Tests
=================================================
Tests the complete RAG pipeline: chunk → embed → store → retrieve → filter.

Run: pytest tests/integration/test_knowledge_pipeline.py -v
"""

import os
import pytest
import tempfile
import shutil
from typing import Generator

from core.knowledge.rag_engine import RAGEngine
from core.knowledge.vector_store import VectorStore
from core.knowledge.chunker import RecursiveCharacterTextSplitter
from core.knowledge.embeddings import EmbeddingsService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_persist_dir() -> Generator[str, None, None]:
    """Provide a temporary directory for ChromaDB persistence."""
    tmpdir = tempfile.mkdtemp(prefix="asim_knowledge_test_")
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)

@pytest.fixture
def rag(temp_persist_dir: str) -> Generator[RAGEngine, None, None]:
    """Fresh RAGEngine backed by a temporary ChromaDB store."""
    engine = RAGEngine(persist_dir=temp_persist_dir)
    yield engine
    try:
        engine.reset()
    except Exception:
        pass

@pytest.fixture
def vector_store(temp_persist_dir: str) -> Generator[VectorStore, None, None]:
    """Fresh VectorStore backed by a temporary ChromaDB store."""
    store = VectorStore(persist_dir=temp_persist_dir)
    yield store
    try:
        store.reset()
    except Exception:
        pass

# ---------------------------------------------------------------------------
# VectorStore Tests
# ---------------------------------------------------------------------------

class TestVectorStore:
    """Tests for the ChromaDB-backed VectorStore."""

    def test_initialization(self, vector_store: VectorStore):
        """Test store initialises with correct defaults."""
        assert vector_store.collection_name == "nepal_knowledge"
        assert vector_store.embed_model == "all-MiniLM-L6-v2"
        assert vector_store.count() == 0

    def test_add_and_count(self, vector_store: VectorStore):
        """Test adding documents and counting."""
        vector_store.add(
            ids=["doc1", "doc2"],
            texts=["Nepal is in South Asia.", "Mount Everest is the tallest peak."],
            metadatas=[{"source": "geo"}, {"source": "geo"}],
        )
        assert vector_store.count() == 2

    def test_add_empty_ids(self, vector_store: VectorStore):
        """Test adding with empty ids does not crash."""
        vector_store.add(ids=[], texts=[], metadatas=[])
        assert vector_store.count() == 0

    def test_query_returns_results(self, vector_store: VectorStore):
        """Test query returns relevant documents."""
        vector_store.add(
            ids=["d1", "d2", "d3"],
            texts=[
                "Nepal is a beautiful country in South Asia.",
                "Mount Everest is located in Nepal.",
                "Python is a programming language.",
            ],
            metadatas=[{"cat": "geo"}, {"cat": "geo"}, {"cat": "tech"}],
        )
        results = vector_store.query("Nepal mountains", top_k=2)
        assert "documents" in results
        assert len(results["documents"][0]) == 2

    def test_query_with_metadata_filter(self, vector_store: VectorStore):
        """Test query filtered by metadata."""
        vector_store.add(
            ids=["d1", "d2"],
            texts=["Nepal geography", "Python programming"],
            metadatas=[{"cat": "geo"}, {"cat": "tech"}],
        )
        results = vector_store.query("programming", top_k=5, where={"cat": "tech"})
        assert len(results["documents"][0]) >= 1
        assert "programming" in results["documents"][0][0].lower()

    def test_update_document(self, vector_store: VectorStore):
        """Test updating an existing document."""
        vector_store.add(
            ids=["doc1"],
            texts=["Original text"],
            metadatas=[{"version": 1}],
        )
        vector_store.update(
            ids=["doc1"],
            texts=["Updated text"],
            metadatas=[{"version": 2}],
        )
        results = vector_store.query("Updated", top_k=1)
        assert len(results["documents"][0]) == 1
        assert "updated" in results["documents"][0][0].lower()

    def test_delete_document(self, vector_store: VectorStore):
        """Test deleting a document."""
        vector_store.add(
            ids=["doc1", "doc2"],
            texts=["Keep me", "Delete me"],
            metadatas=[{"tag": "keep"}, {"tag": "delete"}],
        )
        assert vector_store.count() == 2
        vector_store.delete(ids=["doc2"])
        assert vector_store.count() == 1

    def test_peek(self, vector_store: VectorStore):
        """Test peek returns sample documents."""
        vector_store.add(
            ids=["a", "b", "c"],
            texts=["Text A", "Text B", "Text C"],
            metadatas=[{"tag": "a"}, {"tag": "b"}, {"tag": "c"}],
        )
        sample = vector_store.peek(limit=2)
        assert "documents" in sample
        assert len(sample["documents"]) >= 1

    def test_reset(self, vector_store: VectorStore):
        """Test reset clears all documents."""
        vector_store.add(ids=["x"], texts=["Something"], metadatas=[{"tag": "x"}])
        assert vector_store.count() > 0
        vector_store.reset()
        assert vector_store.count() == 0

# ---------------------------------------------------------------------------
# RAGEngine Tests
# ---------------------------------------------------------------------------

class TestRAGEngine:
    """Tests for the complete RAG pipeline."""

    def test_initialization(self, rag: RAGEngine):
        """Test engine initialises with correct defaults."""
        assert rag.count() == 0
        assert rag.splitter is not None

    def test_chunk_document(self, rag: RAGEngine):
        """Test document chunking produces expected output."""
        text = "Nepal. India. China. Bhutan. All are in Asia."
        chunks = rag.chunk_document(text, metadata={"source": "test"})
        assert len(chunks) > 0
        for chunk in chunks:
            assert "id" in chunk
            assert "text" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["source"] == "test"

    def test_add_text(self, rag: RAGEngine):
        """Test add_text convenience method."""
        doc_id = rag.add_text(
            "Nepal is known for its diverse geography.",
            metadata={"source": "geo"},
        )
        assert isinstance(doc_id, str)
        assert doc_id.startswith("chunk_")
        assert rag.count() > 0

    def test_add_documents(self, rag: RAGEngine):
        """Test add_documents with pre-chunked docs."""
        docs = [
            {"id": "manual_1", "text": "Everest is 8848m tall.", "metadata": {"peak": "everest"}},
            {"id": "manual_2", "text": "Annapurna is 8091m tall.", "metadata": {"peak": "annapurna"}},
        ]
        rag.add_documents(docs)
        assert rag.count() == 2

    def test_retrieve_returns_relevant_results(self, rag: RAGEngine):
        """Test retrieve returns semantically relevant chunks."""
        rag.add_text("Nepal is a beautiful country in South Asia.", metadata={"topic": "geo"})
        rag.add_text("Python is a programming language.", metadata={"topic": "tech"})
        rag.add_text("Mount Everest is the world's tallest mountain.", metadata={"topic": "geo"})

        results = rag.retrieve("Nepal mountains", top_k=3)
        assert len(results) >= 1  # At least the most relevant result
        for r in results:
            assert "text" in r
            assert "metadata" in r
            assert "score" in r
            assert 0 <= r["score"] <= 1.0
        # The top result should be about Nepal or mountains
        top_text = results[0]["text"].lower()
        assert any(kw in top_text for kw in ["nepal", "everest", "mountain"])

    def test_retrieve_by_metadata(self, rag: RAGEngine):
        """Test retrieve filtered by metadata."""
        rag.add_text("Nepal geography", metadata={"cat": "geo"})
        rag.add_text("Python coding", metadata={"cat": "tech"})

        # ChromaDB where filter uses $eq operator
        results = rag.retrieve_by_metadata("coding", where={"cat": {"$eq": "tech"}}, top_k=5)
        assert len(results) >= 1
        assert all(r["metadata"].get("cat") == "tech" for r in results)

    def test_retrieve_empty_store(self, rag: RAGEngine):
        """Test retrieve on empty store returns empty list."""
        results = rag.retrieve("anything", top_k=5)
        assert results == []

    def test_black_hole_filter(self, rag: RAGEngine):
        """Test black_hole_filter re-ranks by relevance threshold."""
        rag.add_text("Nepal is in South Asia.", metadata={"id": "a"})
        rag.add_text("Python is a language.", metadata={"id": "b"})

        chunks = rag.retrieve("Nepal", top_k=5)
        assert len(chunks) >= 1

        filtered = rag.black_hole_filter("Nepal", chunks, threshold=0.3)
        assert len(filtered) >= 1
        for r in filtered:
            assert r.get("score", 0) >= 0.3

    def test_black_hole_filter_empty_input(self, rag: RAGEngine):
        """Test black_hole_filter with empty input returns empty."""
        assert rag.black_hole_filter("query", []) == []

    def test_supernova_rechunk(self, rag: RAGEngine):
        """Test supernova_rechunk merges and re-chunks."""
        old = [
            {"text": "Part one of the document."},
            {"text": "Part two of the document."},
        ]
        new_chunks = rag.supernova_rechunk(old)
        assert len(new_chunks) > 0
        for c in new_chunks:
            assert c["metadata"].get("generation") == "supernova"

    def test_supernova_rechunk_empty(self, rag: RAGEngine):
        """Test supernova_rechunk with empty input."""
        assert rag.supernova_rechunk([]) == []

    def test_reset(self, rag: RAGEngine):
        """Test reset wipes the store."""
        rag.add_text("Something to store.")
        assert rag.count() > 0
        rag.reset()
        assert rag.count() == 0

    def test_full_pipeline(self, rag: RAGEngine):
        """End-to-end: chunk → add → retrieve → filter → rechunk."""
        # 1. Chunk a long document
        text = (
            "Nepal is a landlocked country in South Asia. "
            "It is located mainly in the Himalayas. "
            "The country has a diverse geography including fertile plains, "
            "forested hills, and eight of the world's ten tallest mountains. "
            "Mount Everest, the highest point on Earth, is on the Nepal-China border. "
            "The capital city is Kathmandu. "
            "Nepal has a population of approximately 30 million people."
        )
        chunks = rag.chunk_document(text, metadata={"source": "nepal_facts"})
        assert len(chunks) > 0

        # 2. Add to store
        rag.add_documents(chunks)
        assert rag.count() == len(chunks)

        # 3. Retrieve
        results = rag.retrieve("What is the capital of Nepal?", top_k=3)
        assert len(results) > 0
        assert any("kathmandu" in r["text"].lower() for r in results)

        # 4. Filter — black_hole_filter re-queries Chroma, so results may differ
        # from the original retrieve. Just verify it doesn't crash and returns a list.
        filtered = rag.black_hole_filter("capital city", results, threshold=0.1)
        assert isinstance(filtered, list)

        # 5. Rechunk
        rechunked = rag.supernova_rechunk(filtered)
        assert len(rechunked) > 0

# ---------------------------------------------------------------------------
# Chunker Tests
# ---------------------------------------------------------------------------

class TestChunker:
    """Tests for the RecursiveCharacterTextSplitter."""

    def test_split_simple(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
        chunks = splitter.split_text("Hello. World. Test.")
        assert len(chunks) > 0
        assert all(len(c) <= 100 for c in chunks)

    def test_split_nepali_punctuation(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
        text = "नेपाल दक्षिण एसियामा अवस्थित छ। यो हिमालय क्षेत्रमा पर्दछ।"
        chunks = splitter.split_text(text)
        assert len(chunks) > 0

    def test_split_no_separator(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0)
        chunks = splitter.split_text("A" * 200)
        # Should still produce chunks even without separators
        assert len(chunks) > 0

    def test_chunk_size_respected(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=2)
        chunks = splitter.split_text("word1 word2 word3 word4 word5")
        for c in chunks:
            assert len(c) <= 10

# ---------------------------------------------------------------------------
# EmbeddingsService Tests
# ---------------------------------------------------------------------------

class TestEmbeddingsService:
    """Tests for the EmbeddingsService."""

    def test_get_embedding(self):
        service = EmbeddingsService()
        vec = service.get_embedding("Nepal")
        assert isinstance(vec, list)
        assert len(vec) > 0
        assert all(isinstance(v, float) for v in vec)

    def test_embedding_deterministic(self):
        service = EmbeddingsService()
        v1 = service.get_embedding("Same text")
        v2 = service.get_embedding("Same text")
        assert v1 == v2

    def test_embedding_different_texts(self):
        service = EmbeddingsService()
        v1 = service.get_embedding("Nepal")
        v2 = service.get_embedding("Python")
        # Different texts should produce different vectors
        assert v1 != v2
