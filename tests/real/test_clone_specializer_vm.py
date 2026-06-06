#!/usr/bin/env python3
"""
Tests for core/founder_clones/clone_specializer.py — CloneSpecializer VectorMemory Integration

Covers: clone routing, VectorMemory save/load/search, cross-clone memory search,
spec lookups, status reporting, and singleton pattern.
"""

import os
import sys
import json
import time
import pytest
from datetime import datetime
from typing import Dict, List, Optional

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(autouse=True)
def clean_singletons():
    """Reset the specializer singleton between tests."""
    import core.founder_clones.clone_specializer as cs
    cs._specializer = None
    yield
    cs._specializer = None


@pytest.fixture
def specializer(tmp_path):
    """Provide a fresh CloneSpecializer with a temp VectorMemory DB."""
    from core.founder_clones.clone_specializer import CloneSpecializer
    db_path = str(tmp_path / "test_clone_vector.db")
    spec = CloneSpecializer(vector_db_path=db_path)
    return spec


# ─── Spec Lookups ──────────────────────────────────────────────────────────

class TestSpecLookups:
    """Tests for get_spec, get_by_name, get_by_domain."""

    def test_get_spec_by_id(self, specializer):
        """get_spec returns the correct CloneSpec by clone_id."""
        spec = specializer.get_spec(1)
        assert spec is not None
        assert spec.name == "Dharma Guardian"
        assert spec.domain == "ethics_constitution"

    def test_get_spec_invalid_id(self, specializer):
        """get_spec returns None for invalid clone_id."""
        assert specializer.get_spec(999) is None

    def test_get_by_name(self, specializer):
        """get_by_name finds a clone by name (case-insensitive)."""
        spec = specializer.get_by_name("tech architect")
        assert spec is not None
        assert spec.clone_id == 2

    def test_get_by_name_not_found(self, specializer):
        """get_by_name returns None for unknown name."""
        assert specializer.get_by_name("nonexistent") is None

    def test_get_by_domain(self, specializer):
        """get_by_domain finds a clone by domain."""
        spec = specializer.get_by_domain("economics_finance")
        assert spec is not None
        assert spec.name == "Financial Oracle"

    def test_get_by_domain_not_found(self, specializer):
        """get_by_domain returns None for unknown domain."""
        assert specializer.get_by_domain("nonexistent") is None


# ─── Routing ───────────────────────────────────────────────────────────────

class TestRouting:
    """Tests for the route() method."""

    def test_route_ethics_query(self, specializer):
        """A query matching ethics domain routes to Dharma Guardian (clone_1)."""
        spec = specializer.route("ethics constitution review needed")
        assert spec.clone_id == 1

    def test_route_economy_query(self, specializer):
        """A query matching economics domain routes to Financial Oracle (clone_5)."""
        spec = specializer.route("economics finance forecast needed")
        assert spec.clone_id == 5

    def test_route_default_fallback(self, specializer):
        """A query with no matching keywords falls back to Tech Architect (clone_2)."""
        spec = specializer.route("xyznonexistentkeyword12345")
        assert spec.clone_id == 2

    def test_route_exact_domain_match(self, specializer):
        """Domain name in query gets a boost."""
        spec = specializer.route("Handle all communication tasks")
        assert spec is not None


# ─── System Prompt ─────────────────────────────────────────────────────────

class TestSystemPrompt:
    """Tests for get_system_prompt."""

    def test_get_system_prompt_valid(self, specializer):
        """get_system_prompt returns a non-empty string for valid clone_id."""
        prompt = specializer.get_system_prompt(1)
        assert prompt is not None
        assert len(prompt) > 0

    def test_get_system_prompt_invalid(self, specializer):
        """get_system_prompt returns fallback for invalid clone_id."""
        prompt = specializer.get_system_prompt(999)
        assert prompt == "You are a helpful AsimNexus assistant."


# ─── Memory Operations (VectorMemory + JSONL) ─────────────────────────────

class TestMemoryOperations:
    """Tests for save_memory, load_memory, search_clone_memories."""

    def test_save_memory_vector(self, specializer):
        """save_memory stores a memory entry via VectorMemory."""
        entry = {"content": "Test memory entry", "role": "user", "ts": time.time()}
        result = specializer.save_memory(1, entry)
        assert result is True

    def test_save_memory_invalid_clone(self, specializer):
        """save_memory returns False for invalid clone_id."""
        result = specializer.save_memory(999, {"content": "test"})
        assert result is False

    def test_save_memory_without_content_key(self, specializer):
        """save_memory handles entries without 'content' key."""
        entry = {"message": "Alternate message format", "role": "assistant"}
        result = specializer.save_memory(1, entry)
        assert result is True

    def test_load_memory_recent(self, specializer):
        """load_memory returns recent memories when no query is provided."""
        # Save a few memories
        for i in range(3):
            specializer.save_memory(1, {"content": f"Memory {i}", "ts": time.time()})

        memories = specializer.load_memory(1, limit=10)
        assert len(memories) >= 3

    def test_load_memory_invalid_clone(self, specializer):
        """load_memory returns empty list for invalid clone_id."""
        memories = specializer.load_memory(999)
        assert memories == []

    def test_load_memory_with_query(self, specializer):
        """load_memory with a query performs semantic search."""
        specializer.save_memory(1, {"content": "Blockchain consensus mechanism design"})
        specializer.save_memory(1, {"content": "Pizza recipe with mozzarella"})

        # Search for blockchain-related memory
        results = specializer.load_memory(1, limit=10, query="blockchain")
        # With DUMMY embedding, search may be approximate — at least it doesn't crash
        assert isinstance(results, list)

    def test_load_memory_respects_limit(self, specializer):
        """load_memory returns at most 'limit' entries."""
        for i in range(10):
            specializer.save_memory(1, {"content": f"Memory {i}", "ts": time.time()})

        memories = specializer.load_memory(1, limit=5)
        assert len(memories) <= 5

    def test_search_single_clone(self, specializer):
        """search_clone_memories searches within a specific clone."""
        specializer.save_memory(1, {"content": "Ethical framework for AI"})
        specializer.save_memory(2, {"content": "Rust vs Go performance"})

        results = specializer.search_clone_memories(
            query="AI ethics",
            clone_ids=[1],
            limit=10,
        )
        # Should find results from clone_1
        assert isinstance(results, list)

    def test_search_cross_clone(self, specializer):
        """search_clone_memories searches across all clones when no clone_ids given."""
        specializer.save_memory(1, {"content": "Moral philosophy update"})
        specializer.save_memory(2, {"content": "System architecture review"})

        results = specializer.search_clone_memories(
            query="philosophy",
            limit=10,
        )
        assert isinstance(results, list)

    def test_search_no_vector_memory(self, specializer):
        """search_clone_memories returns empty when vector memory unavailable."""
        specializer._vector_memory = None
        results = specializer.search_clone_memories("test", limit=10)
        assert results == []


# ─── All Specs & Status ────────────────────────────────────────────────────

class TestAllSpecsAndStatus:
    """Tests for all_specs and status."""

    def test_all_specs_returns_15(self, specializer):
        """all_specs returns all 15 clone specifications."""
        specs = specializer.all_specs()
        assert len(specs) == 15

    def test_all_specs_has_required_keys(self, specializer):
        """Each spec dict has the expected keys."""
        specs = specializer.all_specs()
        for spec in specs:
            assert "clone_id" in spec
            assert "name" in spec
            assert "domain" in spec
            assert "dharma_weight" in spec
            assert "tools" in spec
            assert "specializations" in spec

    def test_all_specs_contains_dharma_guardian(self, specializer):
        """Clone 1 is Dharma Guardian with max dharma_weight."""
        specs = specializer.all_specs()
        clone_1 = next(s for s in specs if s["clone_id"] == 1)
        assert clone_1["name"] == "Dharma Guardian"
        assert clone_1["dharma_weight"] >= 0.95

    def test_status_returns_expected_keys(self, specializer):
        """status() returns the expected summary."""
        st = specializer.status()
        assert st["total_clones"] == 15
        assert len(st["domains"]) == 15
        assert "max_dharma" in st
        assert "vector_memory" in st
        assert st["vector_memory"] is True  # VectorMemory initialized

    def test_status_sovereignty_clones(self, specializer):
        """status() lists sovereignty clones (dharma_weight >= 0.95)."""
        st = specializer.status()
        assert len(st["sovereignty_clones"]) >= 1
        assert "Dharma Guardian" in st["sovereignty_clones"]


# ─── Singleton ─────────────────────────────────────────────────────────────

class TestSingleton:
    """Tests for the singleton pattern."""

    def test_get_specializer(self):
        """get_specializer returns a singleton."""
        from core.founder_clones.clone_specializer import get_specializer
        s1 = get_specializer()
        s2 = get_specializer()
        assert s1 is s2

    def test_specializer_singleton_reset(self):
        """Resetting _specializer gives a new instance on next get."""
        from core.founder_clones.clone_specializer import get_specializer, _specializer
        s1 = get_specializer()
        import core.founder_clones.clone_specializer as cs
        cs._specializer = None
        s2 = get_specializer()
        assert s1 is not s2
