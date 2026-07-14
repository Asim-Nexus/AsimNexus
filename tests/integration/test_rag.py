"""
tests/test_rag.py
Tests for the AsimNexus RAG (Retrieval-Augmented Generation) engine.
"""

import pytest
import tempfile
from core.knowledge.rag_engine import RAGEngine

@pytest.fixture
def rag():
    tmpdir = tempfile.mkdtemp(prefix="rag_test_")
    return RAGEngine(persist_dir=tmpdir)

def test_rag_engine_instantiates(rag):
    assert rag is not None

@pytest.mark.asyncio
async def test_rag_query_returns_result(rag):
    """retrieve() returns a list of matching dicts (may be empty for no data)."""
    result = rag.retrieve("What is the tax rate in Nepal?")
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_rag_query_empty_string(rag):
    """Empty query should return a list (possibly empty) without crashing."""
    result = rag.retrieve("")
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_rag_ingest_text(rag):
    """Ingest via add_text — the engine's public API."""
    doc_id = rag.add_text(
        "Nepal Rastra Bank regulates all banking in Nepal.",
        metadata={"source": "nrb_act"},
    )
    assert doc_id  # should return a non-empty chunk id

@pytest.mark.asyncio
async def test_rag_query_after_ingest(rag):
    """After ingestion, a related query should return matching results."""
    rag.add_text(
        "Nepal Rastra Bank regulates all banking in Nepal.",
        metadata={"source": "nrb_act"},
    )
    result = rag.retrieve("Which bank regulates Nepal?")
    assert isinstance(result, list)
    # We expect at least one match since we inserted a relevant doc
    assert len(result) >= 1
    assert "text" in result[0]
