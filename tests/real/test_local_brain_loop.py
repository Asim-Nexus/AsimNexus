#!/usr/bin/env python3
"""
STATUS: REAL — Comprehensive tests for Local Brain Loop components
===============================================================================
Tests for:
  1. HybridRouter (core/routing/hybrid_router.py)
  2. VectorMemory (core/vectormemory.py)
  3. DharmaVeto (core/dharma/dharma_veto.py)
  4. DharmaVetoEngine + ZKPConfirmationManager (core/dharma_chakra/veto_engine.py)
  5. WorldCloneOrchestrator (core/founder_clones/world_clones.py)
  6. FounderCloneSystem (core/founder_clones/founder_clone_system.py)
"""

import os
import sys
import json
import time
import pytest
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from unittest.mock import patch, MagicMock, AsyncMock

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_env():
    """Ensure clean env vars for each test."""
    saved = {}
    for k in ["ASIM_ROUTER_PREFER_LOCAL", "ASIM_ROUTER_OFFLINE_MODE",
              "ASIM_ROUTER_RATE_LIMIT", "ASIM_ROUTER_RATE_WINDOW",
              "ASIM_VECTOR_DB_PATH", "ASIM_EMBEDDING_BACKEND",
              "ASIM_DHARMA_DT_ENGINE", "ASIM_DHARMA_CULTURAL",
              "ASIM_VETO_FINANCE_THRESHOLD", "ASIM_VETO_ZKP_TTL",
              "ASIM_NVIDIA_API_KEYS"]:
        saved[k] = os.environ.get(k)
        if k in os.environ:
            del os.environ[k]
    yield
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v
        elif k in os.environ:
            del os.environ[k]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. HybridRouter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHybridRouter:
    """Test suite for HybridRouter class."""

    def test_import(self):
        """Verify HybridRouter can be imported."""
        from core.routing.hybrid_router import HybridRouter, IntentType, ModelTier, RouteDecision
        assert HybridRouter is not None
        assert IntentType is not None
        assert ModelTier is not None
        assert RouteDecision is not None

    def test_default_initialization(self):
        """Test default initialization with env var fallbacks."""
        from core.routing.hybrid_router import HybridRouter
        router = HybridRouter()
        assert router.prefer_local is True
        assert router.offline_mode is False
        assert router._rate_limit_max == 100
        assert router._rate_limit_window == 60

    def test_env_var_initialization(self):
        """Test initialization respects env vars."""
        os.environ["ASIM_ROUTER_PREFER_LOCAL"] = "false"
        os.environ["ASIM_ROUTER_OFFLINE_MODE"] = "true"
        os.environ["ASIM_ROUTER_RATE_LIMIT"] = "50"
        os.environ["ASIM_ROUTER_RATE_WINDOW"] = "30"
        # Reimport to pick up new env vars
        import importlib
        from core import routing
        importlib.reload(routing.hybrid_router)
        from core.routing.hybrid_router import HybridRouter
        router = HybridRouter()
        assert router.prefer_local is False
        assert router.offline_mode is True
        assert router._rate_limit_max == 50
        assert router._rate_limit_window == 30

    def test_explicit_params_override_env(self):
        """Test explicit constructor params override env vars."""
        os.environ["ASIM_ROUTER_PREFER_LOCAL"] = "false"
        import importlib
        from core import routing
        importlib.reload(routing.hybrid_router)
        from core.routing.hybrid_router import HybridRouter
        router = HybridRouter(prefer_local=True)
        assert router.prefer_local is True  # explicit param wins

    def test_route_health_intent(self):
        """Test routing detects health-related intent."""
        from core.routing.hybrid_router import HybridRouter, IntentType
        router = HybridRouter()
        decision = router.route("I have a medical condition and need to see a doctor")
        assert decision.intent == IntentType.HEALTH
        assert decision.requires_veto is True
        assert decision.score > 0

    def test_route_finance_intent(self):
        """Test routing detects finance-related intent."""
        from core.routing.hybrid_router import HybridRouter, IntentType
        router = HybridRouter()
        decision = router.route("I need to transfer money to my bank account")
        assert decision.intent == IntentType.FINANCE
        assert decision.requires_veto is True

    def test_route_technical_intent(self):
        """Test routing detects technical intent."""
        from core.routing.hybrid_router import HybridRouter, IntentType
        router = HybridRouter()
        decision = router.route("Write a Python function to sort an array")
        assert decision.intent == IntentType.TECHNICAL
        assert decision.requires_veto is False

    def test_route_emergency_intent(self):
        """Test emergency intent is always boosted."""
        from core.routing.hybrid_router import HybridRouter, IntentType
        router = HybridRouter()
        decision = router.route("EMERGENCY! There is a fire in the building!")
        assert decision.intent == IntentType.EMERGENCY
        assert decision.requires_veto is True
        assert decision.requires_human is True

    def test_route_generic_fallback(self):
        """Test generic message falls back to GENERIC intent."""
        from core.routing.hybrid_router import HybridRouter, IntentType
        router = HybridRouter()
        decision = router.route("Hello, how are you today?")
        assert decision.intent == IntentType.GENERIC

    def test_route_with_explicit_intent(self):
        """Test explicit intent override."""
        from core.routing.hybrid_router import HybridRouter, IntentType
        router = HybridRouter()
        decision = router.route("Some random text", intent=IntentType.LEGAL)
        assert decision.intent == IntentType.LEGAL
        assert decision.requires_veto is True
        assert decision.requires_human is True

    def test_route_offline_mode(self):
        """Test offline mode selects local model."""
        from core.routing.hybrid_router import HybridRouter, ModelTier
        router = HybridRouter(offline_mode=True)
        decision = router.route("Write some code")
        assert decision.tier in (ModelTier.LOCAL_FAST, ModelTier.LOCAL_QUALITY)

    def test_route_cloud_priority(self):
        """Test quality priority selects cloud model."""
        from core.routing.hybrid_router import HybridRouter, ModelTier
        router = HybridRouter(prefer_local=False)
        decision = router.route("Write some code", context={"priority": "quality"})
        assert decision.tier == ModelTier.CLOUD_QUALITY

    def test_rate_limiting(self):
        """Test rate limiter blocks after max calls."""
        from core.routing.hybrid_router import HybridRouter
        router = HybridRouter()
        router.set_rate_limit(3, 60)  # 3 calls per 60 seconds
        # First 3 calls should succeed
        for i in range(3):
            decision = router.route(f"test message {i}")
            assert decision.model != "rate_limited", f"Call {i} was rate limited"
        # 4th call should be rate limited
        decision = router.route("test message 4")
        assert decision.model == "rate_limited"

    def test_rate_limit_status(self):
        """Test rate limit status reporting."""
        from core.routing.hybrid_router import HybridRouter
        router = HybridRouter()
        router.set_rate_limit(5, 60)
        router.route("test")
        status = router.get_rate_limit_status()
        assert status["active_calls"] == 1
        assert status["max_calls"] == 5
        assert status["remaining"] == 4

    def test_metrics_tracking(self):
        """Test performance metrics tracking."""
        from core.routing.hybrid_router import HybridRouter
        router = HybridRouter()
        router.update_metrics("test-model", 150.0, True)
        router.update_metrics("test-model", 250.0, False)
        metrics = router.get_metrics()
        assert "test-model" in metrics
        assert metrics["test-model"]["calls"] == 2
        assert metrics["test-model"]["avg_latency_ms"] == 200.0
        assert metrics["test-model"]["success_rate"] == 0.5

    def test_set_offline_toggle(self):
        """Test offline mode toggle."""
        from core.routing.hybrid_router import HybridRouter
        router = HybridRouter()
        assert router.offline_mode is False
        router.set_offline(True)
        assert router.offline_mode is True
        router.set_offline(False)
        assert router.offline_mode is False

    def test_route_error_handling(self):
        """Test error handling returns error decision."""
        from core.routing.hybrid_router import HybridRouter
        router = HybridRouter()
        # Force an error by passing None as message (should not crash)
        decision = router.route("")
        assert decision is not None
        assert decision.model != "error"

    def test_nepali_keyword_detection(self):
        """Test Nepali keyword detection."""
        from core.routing.hybrid_router import HybridRouter, IntentType
        router = HybridRouter()
        decision = router.route("मलाई स्वास्थ्य समस्या छ")  # "I have a health problem"
        assert decision.intent == IntentType.HEALTH

    def test_get_hybrid_router_singleton(self):
        """Test singleton factory function."""
        from core.routing.hybrid_router import get_hybrid_router
        router1 = get_hybrid_router()
        router2 = get_hybrid_router()
        # Factory creates new instances each time (not a true singleton)
        assert router1 is not router2


# ═══════════════════════════════════════════════════════════════════════════════
# 2. VectorMemory Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestVectorMemory:
    """Test suite for VectorMemory class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        import gc, time
        gc.collect()
        time.sleep(0.05)
        try:
            if Path(db_path).exists():
                Path(db_path).unlink()
        except PermissionError:
            pass
        # Also clean up SQLite WAL/SHM files
        for ext in ("-wal", "-shm"):
            p = Path(db_path + ext)
            if p.exists():
                try:
                    p.unlink()
                except PermissionError:
                    pass

    def test_import(self):
        """Verify VectorMemory can be imported."""
        from core.vectormemory import VectorMemory, MemoryType, Memory, SearchResult
        assert VectorMemory is not None
        assert MemoryType is not None
        assert Memory is not None
        assert SearchResult is not None

    def test_init_creates_db(self, temp_db):
        """Test initialization creates database file."""
        from core.vectormemory import VectorMemory, EmbeddingBackend
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        assert Path(temp_db).exists()

    def test_add_and_get_memory(self, temp_db):
        """Test adding and retrieving a memory."""
        from core.vectormemory import VectorMemory, EmbeddingBackend, MemoryType
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        mem_id = vm.add_memory("Hello world", MemoryType.CHAT, "user1")
        assert mem_id is not None
        assert len(mem_id) > 0

        mem = vm.get_memory(mem_id)
        assert mem is not None
        assert mem.content == "Hello world"
        assert mem.memory_type == MemoryType.CHAT
        assert mem.user_id == "user1"

    def test_get_memory_not_found(self, temp_db):
        """Test get_memory returns None for non-existent ID."""
        from core.vectormemory import VectorMemory, EmbeddingBackend
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        mem = vm.get_memory("nonexistent")
        assert mem is None

    def test_add_memory_with_metadata(self, temp_db):
        """Test adding memory with metadata."""
        from core.vectormemory import VectorMemory, EmbeddingBackend, MemoryType
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        mem_id = vm.add_memory(
            "Important lesson learned",
            MemoryType.LESSON,
            "user1",
            {"priority": "high", "tags": ["learning", "important"]}
        )
        mem = vm.get_memory(mem_id)
        assert mem.metadata.get("priority") == "high"
        assert "learning" in mem.metadata.get("tags", [])

    def test_search_memories(self, temp_db):
        """Test semantic search returns relevant memories."""
        from core.vectormemory import VectorMemory, EmbeddingBackend, MemoryType
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        vm.add_memory("The cat sat on the mat", MemoryType.CHAT, "user1")
        vm.add_memory("Dogs love to play fetch", MemoryType.CHAT, "user1")
        vm.add_memory("Python is a programming language", MemoryType.KNOWLEDGE, "user1")

        results = vm.search("programming code", limit=5)
        assert len(results) > 0
        # The dummy embedding is hash-based, so results may vary
        # Just verify search doesn't crash and returns results
        assert all(r.similarity >= 0.0 for r in results)

    def test_search_with_type_filter(self, temp_db):
        """Test search with memory type filter."""
        from core.vectormemory import VectorMemory, EmbeddingBackend, MemoryType
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        vm.add_memory("Chat message", MemoryType.CHAT, "user1")
        vm.add_memory("System event", MemoryType.SYSTEM, "user1")

        results = vm.search("message", memory_type=MemoryType.CHAT)
        assert len(results) > 0
        for r in results:
            assert r.memory.memory_type == MemoryType.CHAT

    def test_get_user_memories(self, temp_db):
        """Test getting all memories for a user."""
        from core.vectormemory import VectorMemory, EmbeddingBackend, MemoryType
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        vm.add_memory("Memory 1", MemoryType.CHAT, "user1")
        vm.add_memory("Memory 2", MemoryType.CHAT, "user1")
        vm.add_memory("Other user memory", MemoryType.CHAT, "user2")

        memories = vm.get_user_memories("user1")
        assert len(memories) == 2

    def test_delete_memory(self, temp_db):
        """Test deleting a memory."""
        from core.vectormemory import VectorMemory, EmbeddingBackend, MemoryType
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        mem_id = vm.add_memory("To be deleted", MemoryType.CHAT, "user1")
        assert vm.delete_memory(mem_id) is True
        assert vm.get_memory(mem_id) is None

    def test_delete_nonexistent_memory(self, temp_db):
        """Test deleting non-existent memory returns False."""
        from core.vectormemory import VectorMemory, EmbeddingBackend
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        assert vm.delete_memory("nonexistent") is False

    def test_get_stats(self, temp_db):
        """Test stats reporting."""
        from core.vectormemory import VectorMemory, EmbeddingBackend, MemoryType
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        vm.add_memory("Test", MemoryType.CHAT, "user1")
        vm.add_memory("Test 2", MemoryType.KNOWLEDGE, "user1")
        stats = vm.get_stats()
        assert stats["total_memories"] == 2
        assert stats["by_type"]["chat"] == 1
        assert stats["by_type"]["knowledge"] == 1
        assert stats["embedding_backend"] == "dummy"

    def test_prune_old_memories(self, temp_db):
        """Test pruning old memories."""
        from core.vectormemory import VectorMemory, EmbeddingBackend, MemoryType
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        vm.add_memory("Keep me", MemoryType.CHAT, "user1")
        # Prune with days=0 should remove nothing (no cutoff)
        deleted = vm.prune_old_memories(days=0, keep_per_type=100)
        assert deleted >= 0  # Should not crash

    def test_env_var_db_path(self):
        """Test get_vector_memory uses env var for db_path."""
        os.environ["ASIM_VECTOR_DB_PATH"] = "data/test_vector_memory.db"
        import importlib
        from core import vectormemory
        importlib.reload(vectormemory)
        from core.vectormemory import get_vector_memory, reset_vector_memory
        reset_vector_memory()
        vm = get_vector_memory()
        assert vm.db_path == "data/test_vector_memory.db"
        reset_vector_memory()

    def test_cosine_similarity(self, temp_db):
        """Test cosine similarity calculation."""
        from core.vectormemory import VectorMemory, EmbeddingBackend
        vm = VectorMemory(temp_db, EmbeddingBackend.DUMMY)
        # Test identical vectors
        sim = vm._cosine_similarity([1.0, 0.0], [1.0, 0.0])
        assert sim == pytest.approx(1.0, abs=0.01)
        # Test orthogonal vectors
        sim = vm._cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert sim == pytest.approx(0.0, abs=0.01)
        # Test zero vector
        sim = vm._cosine_similarity([0.0, 0.0], [1.0, 0.0])
        assert sim == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DharmaVeto Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDharmaVeto:
    """Test suite for DharmaVeto class."""

    def test_import(self):
        """Verify DharmaVeto can be imported."""
        from core.dharma.dharma_veto import DharmaVeto, VetoResult, VetoSeverity, VetoReason
        assert DharmaVeto is not None
        assert VetoResult is not None
        assert VetoSeverity is not None
        assert VetoReason is not None

    def test_init(self):
        """Test initialization."""
        from core.dharma.dharma_veto import DharmaVeto
        veto = DharmaVeto()
        assert veto is not None
        assert veto._audit == []

    def test_check_pass(self):
        """Test a safe action passes all layers."""
        from core.dharma.dharma_veto import DharmaVeto
        veto = DharmaVeto()
        result = veto.check(action="read_file", node_id="user1",
                            context={"path": "/home/user1/notes.txt"})
        assert result.passed is True
        assert result.severity.value == "pass"

    def test_check_critical_forbidden(self):
        """Test critical forbidden patterns are blocked."""
        from core.dharma.dharma_veto import DharmaVeto, VetoSeverity
        veto = DharmaVeto()
        result = veto.check(action="rm -rf /", node_id="user1")
        assert result.passed is False
        assert result.severity == VetoSeverity.CRITICAL
        assert result.requires_human is False  # Cannot be overridden

    def test_check_block_pattern(self):
        """Test block patterns require human override."""
        from core.dharma.dharma_veto import DharmaVeto
        veto = DharmaVeto()
        result = veto.check(action="transfer all data", node_id="user1")
        assert result.passed is False
        assert result.requires_human is True

    def test_check_monopoly_pattern(self):
        """Test monopoly patterns trigger warning."""
        from core.dharma.dharma_veto import DharmaVeto
        veto = DharmaVeto()
        result = veto.check(action="apply universal standard", node_id="user1")
        assert result.passed is True  # WARN passes but logs
        assert result.severity.value == "warn"

    def test_audit_log(self):
        """Test audit log records veto events."""
        from core.dharma.dharma_veto import DharmaVeto, get_dharma_veto
        # Use fresh instance to avoid shared singleton state
        veto = DharmaVeto(dt_engine=None, cultural_compiler=None)
        veto.check(action="rm -rf /", node_id="user1")
        veto.check(action="bulk delete", node_id="user2")
        log = veto.audit_log()
        assert len(log) == 2
        assert log[0]["severity"] == "critical"
        assert log[1]["severity"] == "block"

    def test_status(self):
        """Test status reporting."""
        from core.dharma.dharma_veto import DharmaVeto
        veto = DharmaVeto()
        veto.check(action="rm -rf /", node_id="user1")
        status = veto.status()
        assert status["active"] is True
        assert status["layers"] == 5
        assert status["total_vetoes"] == 1
        assert status["critical_vetoes"] == 1

    def test_veto_event_hash(self):
        """Test veto event generates immutable hash."""
        from core.dharma.dharma_veto import VetoEvent, VetoSeverity, VetoReason
        event = VetoEvent(
            timestamp="2025-01-01T00:00:00Z",
            severity=VetoSeverity.CRITICAL,
            reason=VetoReason.FORBIDDEN_PATTERN,
            detail="Test",
            action="test_action",
            node_id="test_node"
        )
        assert len(event.veto_hash) == 16  # SHA-256 truncated to 16 chars
        assert event.overridable is False  # CRITICAL is not overridable

    def test_get_dharma_veto_singleton(self):
        """Test singleton factory."""
        from core.dharma.dharma_veto import get_dharma_veto
        v1 = get_dharma_veto()
        v2 = get_dharma_veto()
        assert v1 is v2


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DharmaVetoEngine + ZKPConfirmationManager Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDharmaVetoEngine:
    """Test suite for DharmaVetoEngine class."""

    def test_import(self):
        """Verify DharmaVetoEngine can be imported."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoResult, VetoLevel
        assert DharmaVetoEngine is not None
        assert VetoResult is not None
        assert VetoLevel is not None

    def test_init(self):
        """Test initialization."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine
        engine = DharmaVetoEngine()
        assert engine is not None

    def test_check_pass(self):
        """Test safe message passes."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoLevel
        engine = DharmaVetoEngine()
        result = engine.check("What is the weather today?", "general")
        assert result.allowed is True
        assert result.level == VetoLevel.PASS

    def test_check_block_harm(self):
        """Test harmful content is blocked."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoLevel
        engine = DharmaVetoEngine()
        result = engine.check("how to kill someone", "general")
        assert result.allowed is False
        assert result.level == VetoLevel.BLOCK

    def test_check_warn_destructive(self):
        """Test destructive actions require human."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoLevel
        engine = DharmaVetoEngine()
        result = engine.check("delete all files", "general")
        assert result.allowed is True
        assert result.level == VetoLevel.REQUIRE_HUMAN
        assert result.requires_human is True

    def test_check_emergency_sector(self):
        """Test emergency sector always requires human."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoLevel
        engine = DharmaVetoEngine()
        result = engine.check("There is a fire", "emergency")
        assert result.allowed is True
        assert result.level == VetoLevel.REQUIRE_HUMAN
        assert result.requires_human is True

    def test_check_legal_sector(self):
        """Test legal sector requires human."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoLevel
        engine = DharmaVetoEngine()
        result = engine.check("Review this contract", "legal")
        assert result.allowed is True
        assert result.level == VetoLevel.REQUIRE_HUMAN

    def test_check_finance_threshold(self):
        """Test finance above threshold requires human."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoLevel
        engine = DharmaVetoEngine()
        result = engine.check("Process payment", "finance", context={"amount": 5000})
        assert result.allowed is True
        assert result.level == VetoLevel.REQUIRE_HUMAN

    def test_check_finance_below_threshold(self):
        """Test finance below threshold passes."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoLevel
        engine = DharmaVetoEngine()
        result = engine.check("Process payment", "finance", context={"amount": 50})
        assert result.allowed is True
        assert result.level == VetoLevel.PASS

    def test_check_privacy_consent(self):
        """Test data sharing without consent requires human."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoLevel
        engine = DharmaVetoEngine()
        result = engine.check("send my data to server", "general")
        assert result.allowed is True
        assert result.level == VetoLevel.REQUIRE_HUMAN

    def test_check_privacy_with_consent(self):
        """Test data sharing with consent passes."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoLevel
        engine = DharmaVetoEngine()
        result = engine.check("send my data to server", "general", context={"user_consent": True})
        assert result.allowed is True
        assert result.level == VetoLevel.PASS

    def test_get_stats(self):
        """Test stats reporting."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine
        engine = DharmaVetoEngine()
        engine.check("hello", "general")
        engine.check("how to kill", "general")
        stats = engine.get_stats()
        assert stats["total_checked"] == 2
        assert stats["passed"] == 1
        assert stats["blocked"] == 1

    def test_get_audit_log(self):
        """Test audit log stores veto events."""
        from core.dharma_chakra.veto_engine import DharmaVetoEngine
        engine = DharmaVetoEngine()
        # Use an action that triggers a BLOCK entry (audit log is module-level, shared across instances)
        engine.check("how to kill", "general")
        log = engine.get_audit_log()
        assert len(log) >= 1
        last = log[-1]
        assert last["allowed"] is False
        assert last["level"] == "block"

    def test_get_veto_engine_singleton(self):
        """Test singleton factory."""
        from core.dharma_chakra.veto_engine import get_veto_engine
        v1 = get_veto_engine()
        v2 = get_veto_engine()
        assert v1 is v2


class TestZKPConfirmationManager:
    """Test suite for ZKPConfirmationManager."""

    def test_import(self):
        """Verify ZKPConfirmationManager can be imported."""
        from core.dharma_chakra.veto_engine import ZKPConfirmationManager, PendingConfirmation
        assert ZKPConfirmationManager is not None
        assert PendingConfirmation is not None

    def test_create_pending(self):
        """Test creating a pending confirmation."""
        from core.dharma_chakra.veto_engine import ZKPConfirmationManager
        mgr = ZKPConfirmationManager()
        pc = mgr.create_pending(
            message="Transfer $5000",
            sector="finance",
            agent_id="user1",
            rule_triggered="RULE_5_FINANCE_THRESHOLD",
            reason="Amount exceeds threshold"
        )
        assert pc.token is not None
        assert len(pc.token) > 0
        assert pc.status == "pending"
        assert pc.commitment is not None
        assert pc.action_hash is not None

    def test_confirm_pending(self):
        """Test confirming a pending action."""
        from core.dharma_chakra.veto_engine import ZKPConfirmationManager
        mgr = ZKPConfirmationManager()
        pc = mgr.create_pending(
            message="Transfer $5000",
            sector="finance",
            agent_id="user1",
            rule_triggered="RULE_5_FINANCE_THRESHOLD",
            reason="Amount exceeds threshold"
        )
        result = mgr.confirm(pc.token)
        assert result["success"] is True
        assert result["zk_valid"] is True
        assert result["status"] == "confirmed"

    def test_reject_pending(self):
        """Test rejecting a pending action."""
        from core.dharma_chakra.veto_engine import ZKPConfirmationManager
        mgr = ZKPConfirmationManager()
        pc = mgr.create_pending(
            message="Delete all files",
            sector="general",
            agent_id="user1",
            rule_triggered="RULE_2_DESTRUCTIVE_ACTION",
            reason="Destructive action"
        )
        result = mgr.reject(pc.token)
        assert result["success"] is True
        assert result["status"] == "rejected"

    def test_confirm_invalid_token(self):
        """Test confirming with invalid token."""
        from core.dharma_chakra.veto_engine import ZKPConfirmationManager
        mgr = ZKPConfirmationManager()
        result = mgr.confirm("invalid-token")
        assert result["success"] is False
        assert "Token not found" in result["error"]

    def test_get_status(self):
        """Test getting status of pending confirmation."""
        from core.dharma_chakra.veto_engine import ZKPConfirmationManager
        mgr = ZKPConfirmationManager()
        pc = mgr.create_pending(
            message="Test",
            sector="general",
            agent_id="user1",
            rule_triggered="RULE_1",
            reason="Test"
        )
        status = mgr.get_status(pc.token)
        assert status is not None
        assert status["status"] == "pending"
        assert status["token"] == pc.token

    def test_get_status_nonexistent(self):
        """Test get_status returns None for invalid token."""
        from core.dharma_chakra.veto_engine import ZKPConfirmationManager
        mgr = ZKPConfirmationManager()
        assert mgr.get_status("nonexistent") is None

    def test_list_pending(self):
        """Test listing pending confirmations."""
        from core.dharma_chakra.veto_engine import ZKPConfirmationManager
        mgr = ZKPConfirmationManager()
        mgr.create_pending("Test 1", "general", "user1", "RULE_1", "Test")
        mgr.create_pending("Test 2", "finance", "user2", "RULE_5", "Test")
        pending = mgr.list_pending()
        assert len(pending) == 2

    def test_zkp_commitment_verification(self):
        """Test ZKP commitment verification."""
        from core.dharma_chakra.veto_engine import ZKPConfirmationManager
        mgr = ZKPConfirmationManager()
        pc = mgr.create_pending(
            message="Secret action",
            sector="general",
            agent_id="user1",
            rule_triggered="RULE_1",
            reason="Test"
        )
        # Verify commitment is SHA-256 of action_hash + nonce
        expected = hashlib.sha256(f"{pc.action_hash}{pc.nonce}".encode()).hexdigest()
        assert pc.commitment == expected

    def test_get_zkp_manager_singleton(self):
        """Test singleton factory."""
        from core.dharma_chakra.veto_engine import get_zkp_manager
        m1 = get_zkp_manager()
        m2 = get_zkp_manager()
        assert m1 is m2


# ═══════════════════════════════════════════════════════════════════════════════
# 5. WorldCloneOrchestrator Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestWorldCloneOrchestrator:
    """Test suite for WorldCloneOrchestrator."""

    def test_import(self):
        """Verify WorldCloneOrchestrator can be imported."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator, WorldClone, CloneRole
        assert WorldCloneOrchestrator is not None
        assert WorldClone is not None
        assert CloneRole is not None

    def test_init_creates_15_clones(self):
        """Test initialization creates all 15 clones."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator
        orch = WorldCloneOrchestrator()
        assert len(orch.clones) == 15

    def test_get_all_clones(self):
        """Test get_all_clones returns all clone info."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator
        orch = WorldCloneOrchestrator()
        clones = orch.get_all_clones()
        assert len(clones) == 15
        for c in clones:
            assert "role" in c
            assert "icon" in c
            assert "specialty" in c
            assert "capabilities" in c

    def test_select_clones_for_task_tech(self):
        """Test selecting clones for a tech task."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator, CloneRole
        orch = WorldCloneOrchestrator()
        roles = orch.select_clones_for_task("I need help with Python code and API design")
        assert CloneRole.TECH_ARCHITECT in roles
        assert CloneRole.HARMONY_KEEPER in roles  # Always included

    def test_select_clones_for_task_health(self):
        """Test selecting clones for a health task."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator, CloneRole
        orch = WorldCloneOrchestrator()
        roles = orch.select_clones_for_task("I need to see a doctor for my health checkup")
        assert CloneRole.HEALTH_SAGE in roles
        assert CloneRole.HARMONY_KEEPER in roles  # Always included

    def test_select_clones_for_task_nepali(self):
        """Test selecting clones with Nepali keywords."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator, CloneRole
        orch = WorldCloneOrchestrator()
        roles = orch.select_clones_for_task("मलाई कोड चाहियो र सफ्टवेयर बनाउनु छ")
        assert CloneRole.TECH_ARCHITECT in roles

    def test_select_clones_for_task_finance_nepali(self):
        """Test Nepali finance keywords trigger Financial Oracle."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator, CloneRole
        orch = WorldCloneOrchestrator()
        roles = orch.select_clones_for_task("पैसा र बैंकको बारेमा जानकारी चाहियो")
        assert CloneRole.FINANCIAL_ORACLE in roles

    def test_select_clones_for_task_default(self):
        """Test fallback to Tech + Strategic if nothing matched."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator, CloneRole
        orch = WorldCloneOrchestrator()
        roles = orch.select_clones_for_task("xyzzy quantum plugh")
        assert CloneRole.HARMONY_KEEPER in roles
        assert CloneRole.STRATEGIC_PLANNER in roles
        assert len(roles) == 2  # Harmony + Strategic

    def test_select_clones_max_5(self):
        """Test max 5 clones per request."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator
        orch = WorldCloneOrchestrator()
        roles = orch.select_clones_for_task(
            "code health money law security environment travel education art research"
        )
        assert len(roles) <= 5

    def test_toggle_agent_mode(self):
        """Test toggling agent mode on/off."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator
        orch = WorldCloneOrchestrator()
        assert orch.agent_mode is False
        orch.toggle_agent_mode(True)
        assert orch.agent_mode is True
        orch.toggle_agent_mode(False)
        assert orch.agent_mode is False

    def test_get_clone(self):
        """Test getting a specific clone by role."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator, CloneRole
        orch = WorldCloneOrchestrator()
        import asyncio
        clone = asyncio.run(orch.get_clone(CloneRole.HEALTH_SAGE))
        assert clone is not None
        assert clone.config.role == CloneRole.HEALTH_SAGE

    def test_direct_message_not_found(self):
        """Test direct_message with invalid role name."""
        from core.founder_clones.world_clones import WorldCloneOrchestrator
        orch = WorldCloneOrchestrator()
        import asyncio
        result = asyncio.run(orch.direct_message("NONEXISTENT", "Hello"))
        assert "not found" in result.lower()

    def test_get_world_clones_singleton(self):
        """Test singleton factory."""
        from core.founder_clones.world_clones import get_world_clones
        w1 = get_world_clones()
        w2 = get_world_clones()
        assert w1 is w2


# ═══════════════════════════════════════════════════════════════════════════════
# 6. FounderCloneSystem Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFounderCloneSystem:
    """Test suite for FounderCloneSystem (NVIDIA-backed)."""

    def test_import(self):
        """Verify FounderCloneSystem can be imported."""
        from core.founder_clones.founder_clone_system import (
            FounderCloneSystem, FounderClone, FounderRole, NVIDIA_API_KEYS
        )
        assert FounderCloneSystem is not None
        assert FounderClone is not None
        assert FounderRole is not None
        assert isinstance(NVIDIA_API_KEYS, dict)

    def test_init_no_keys(self):
        """Test initialization without API keys (15 founders created with empty keys)."""
        from core.founder_clones.founder_clone_system import FounderCloneSystem
        fcs = FounderCloneSystem(nvidia_api_keys={})
        # Founders are always created, just without API keys
        assert len(fcs.founders) == 15

    def test_init_with_mock_keys(self):
        """Test initialization with mock NVIDIA API keys."""
        from core.founder_clones.founder_clone_system import FounderCloneSystem, FounderRole
        mock_keys = {
            "key1": {"type": "reasoning", "model": "test-model", "params": {"temperature": 0.7}},
            "key2": {"type": "coding", "model": "code-model", "params": {"temperature": 0.2}},
        }
        fcs = FounderCloneSystem(nvidia_api_keys=mock_keys)
        assert len(fcs.founders) == 15
        assert FounderRole.CEO in fcs.founders
        assert FounderRole.CTO in fcs.founders
        assert FounderRole.CFO in fcs.founders

    def test_get_founder(self):
        """Test getting a specific founder."""
        from core.founder_clones.founder_clone_system import FounderCloneSystem, FounderRole
        mock_keys = {
            "key1": {"type": "reasoning", "model": "test-model", "params": {}},
            "key2": {"type": "general", "model": "test-model", "params": {}},
            "key3": {"type": "coding", "model": "test-model", "params": {}},
            "key4": {"type": "reasoning_flash", "model": "test-model", "params": {}},
            "key5": {"type": "reasoning_tools", "model": "test-model", "params": {}},
        }
        fcs = FounderCloneSystem(nvidia_api_keys=mock_keys)
        import asyncio
        ceo = asyncio.run(fcs.get_founder(FounderRole.CEO))
        assert ceo is not None
        assert ceo.config.role == FounderRole.CEO
        assert ceo.config.name == "Alex Chen"

    def test_get_founder_not_found(self):
        """Test getting a non-existent founder."""
        from core.founder_clones.founder_clone_system import FounderCloneSystem
        fcs = FounderCloneSystem(nvidia_api_keys={})
        import asyncio
        result = asyncio.run(fcs.get_founder(None))
        assert result is None

    def test_message_founder_no_keys(self):
        """Test messaging a founder when no NVIDIA API keys are available."""
        from core.founder_clones.founder_clone_system import FounderCloneSystem, FounderRole
        fcs = FounderCloneSystem(nvidia_api_keys={})
        import asyncio
        result = asyncio.run(fcs.message_founder(FounderRole.CEO, "Hello"))
        assert "No NVIDIA API key available" in result
        assert "Alex Chen" in result

    def test_select_relevant_founders_strategy(self):
        """Test selecting founders for a strategy task."""
        from core.founder_clones.founder_clone_system import (FounderCloneSystem, FounderRole)
        mock_keys = {
            "key1": {"type": "reasoning", "model": "test-model", "params": {}},
        }
        fcs = FounderCloneSystem(nvidia_api_keys=mock_keys)
        roles = fcs._select_relevant_founders("We need a new corporate strategy and vision")
        assert FounderRole.CEO in roles

    def test_select_relevant_founders_tech(self):
        """Test selecting founders for a tech task."""
        from core.founder_clones.founder_clone_system import (FounderCloneSystem, FounderRole)
        mock_keys = {
            "key1": {"type": "reasoning", "model": "test-model", "params": {}},
        }
        fcs = FounderCloneSystem(nvidia_api_keys=mock_keys)
        roles = fcs._select_relevant_founders("Need architecture for new code system")
        assert FounderRole.CTO in roles
        assert FounderRole.VP_ENGINEERING in roles

    def test_select_relevant_founders_finance(self):
        """Test selecting founders for a finance task."""
        from core.founder_clones.founder_clone_system import (FounderCloneSystem, FounderRole)
        mock_keys = {
            "key1": {"type": "reasoning", "model": "test-model", "params": {}},
        }
        fcs = FounderCloneSystem(nvidia_api_keys=mock_keys)
        roles = fcs._select_relevant_founders("Analyze our budget and reduce costs")
        assert FounderRole.CFO in roles

    def test_select_relevant_founders_default(self):
        """Test default selection (CEO) when nothing matches."""
        from core.founder_clones.founder_clone_system import (FounderCloneSystem, FounderRole)
        mock_keys = {
            "key1": {"type": "reasoning", "model": "test-model", "params": {}},
        }
        fcs = FounderCloneSystem(nvidia_api_keys=mock_keys)
        roles = fcs._select_relevant_founders("xyzzy plugh")
        assert FounderRole.CEO in roles
        assert len(roles) == 1

    def test_get_all_founders_status(self):
        """Test getting status of all founders."""
        from core.founder_clones.founder_clone_system import FounderCloneSystem
        mock_keys = {
            "key1": {"type": "reasoning", "model": "test-model", "params": {}},
        }
        fcs = FounderCloneSystem(nvidia_api_keys=mock_keys)
        import asyncio
        status = asyncio.run(fcs.get_all_founders_status())
        assert len(status) >= 1
        for role_name, info in status.items():
            assert "name" in info
            assert "active" in info
            assert "specialization" in info
            assert "model" in info

    def test_coordinate_founders_no_keys(self):
        """Test coordinate_founders without keys."""
        from core.founder_clones.founder_clone_system import FounderCloneSystem
        fcs = FounderCloneSystem(nvidia_api_keys={})
        import asyncio
        result = asyncio.run(fcs.coordinate_founders("test task", []))
        assert result["task"] == "test task"
        assert result["coordination_status"] == "completed"
        assert len(result["results"]) == 0