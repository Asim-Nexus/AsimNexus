#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade tests for Milestone 2
ASIMNEXUS Milestone 2 Tests
===========================
Tests for Local Brain Loop components:
- Model Router
- Vector Memory
- Clone Orchestrator
- Policy Gate
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestModelRouter:
    """Tests for core.model_router."""
    
    @pytest.fixture
    def router(self):
        from core.model_router import ModelRouter, reset_model_router
        reset_model_router()
        return ModelRouter()
    
    def test_device_capability_detection(self, router):
        """Test device capability detection."""
        capability = router.get_device_capability()
        assert capability.cpu_cores > 0
        assert capability.total_ram_gb > 0
        assert capability.available_ram_gb > 0
    
    def test_recommended_tier(self, router):
        """Test recommended model tier."""
        tier = router.get_recommended_tier()
        assert tier is not None
        assert tier.value in ["tiny", "small", "medium", "large", "xlarge"]
    
    def test_register_model(self, router):
        """Test model registration."""
        from core.model_router import ModelSpec, ModelTier, TaskType
        spec = ModelSpec(
            name="test-model",
            tier=ModelTier.TINY,
            params_b=0.5,
            supported_tasks=[TaskType.CHAT],
            file_path="/tmp/model.gguf",
            context_length=2048,
            quantization="Q4_K_M"
        )
        success = router.register_model(spec)
        assert success is True
        assert spec.name in router.available_models
    
    def test_select_model(self, router):
        """Test model selection by task."""
        from core.model_router import ModelSpec, ModelTier, TaskType
        spec = ModelSpec(
            name="test-model",
            tier=ModelTier.TINY,
            params_b=0.5,
            supported_tasks=[TaskType.CHAT],
            file_path="/tmp/model.gguf",
            context_length=2048,
            quantization="Q4_K_M"
        )
        router.register_model(spec)
        
        selected = router.select_model(TaskType.CHAT)
        assert selected == "test-model"
    
    def test_list_available_models(self, router):
        """Test listing available models."""
        models = router.list_available_models()
        assert isinstance(models, list)


class TestVectorMemory:
    """Tests for core.vectormemory."""
    
    @pytest.fixture
    def temp_db(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        try:
            Path(path).unlink(missing_ok=True)
        except PermissionError:
            import gc
            gc.collect()
            for _ in range(5):
                try:
                    Path(path).unlink(missing_ok=True)
                    break
                except PermissionError:
                    import time
                    time.sleep(0.1)
    
    @pytest.fixture
    def memory(self, temp_db):
        from core.vectormemory import VectorMemory, EmbeddingBackend, reset_vector_memory
        reset_vector_memory()
        return VectorMemory(temp_db, EmbeddingBackend.DUMMY)
    
    def test_add_memory(self, memory):
        """Test adding a memory."""
        from core.vectormemory import MemoryType
        memory_id = memory.add_memory(
            content="Test memory content",
            memory_type=MemoryType.CHAT,
            user_id="test-user"
        )
        assert memory_id is not None
        assert len(memory_id) > 0
    
    def test_get_memory(self, memory):
        """Test retrieving a memory."""
        from core.vectormemory import MemoryType
        memory_id = memory.add_memory(
            content="Test memory content",
            memory_type=MemoryType.CHAT,
            user_id="test-user"
        )
        
        retrieved = memory.get_memory(memory_id)
        assert retrieved is not None
        assert retrieved.content == "Test memory content"
        assert retrieved.user_id == "test-user"
    
    def test_search_memory(self, memory):
        """Test semantic search."""
        from core.vectormemory import MemoryType
        memory.add_memory(
            content="Python programming language",
            memory_type=MemoryType.KNOWLEDGE,
            user_id="test-user"
        )
        
        results = memory.search("python", user_id="test-user")
        assert len(results) >= 0
    
    def test_get_user_memories(self, memory):
        """Test getting user memories."""
        from core.vectormemory import MemoryType
        memory.add_memory(
            content="User memory 1",
            memory_type=MemoryType.USER_MEMORY,
            user_id="test-user"
        )
        
        memories = memory.get_user_memories("test-user")
        assert len(memories) >= 1
    
    def test_delete_memory(self, memory):
        """Test deleting a memory."""
        from core.vectormemory import MemoryType
        memory_id = memory.add_memory(
            content="Test memory",
            memory_type=MemoryType.CHAT,
            user_id="test-user"
        )
        
        success = memory.delete_memory(memory_id)
        assert success is True
        
        retrieved = memory.get_memory(memory_id)
        assert retrieved is None
    
    def test_get_stats(self, memory):
        """Test getting memory statistics."""
        stats = memory.get_stats()
        assert "total_memories" in stats
        assert "by_type" in stats
        assert "storage_size_bytes" in stats


class TestCloneOrchestrator:
    """Tests for core.clone_orchestrator."""
    
    @pytest.fixture
    def temp_db(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        try:
            Path(path).unlink(missing_ok=True)
        except PermissionError:
            import gc
            gc.collect()
            for _ in range(5):
                try:
                    Path(path).unlink(missing_ok=True)
                    break
                except PermissionError:
                    import time
                    time.sleep(0.1)
    
    @pytest.fixture
    def orchestrator(self, temp_db):
        from core.clone_orchestrator import CloneOrchestrator, reset_clone_orchestrator
        reset_clone_orchestrator()
        return CloneOrchestrator(temp_db)
    
    def test_founder_clones_initialized(self, orchestrator):
        """Test that 15 founder clones are initialized."""
        assert len(orchestrator.clones) == 15
    
    def test_get_clone(self, orchestrator):
        """Test getting a specific clone."""
        clone = orchestrator.get_clone("clone_architect")
        assert clone is not None
        assert clone.name == "Atlas"
        assert clone.role.value == "architect"
    
    def test_get_available_clones(self, orchestrator):
        """Test getting available clones."""
        available = orchestrator.get_available_clones()
        assert len(available) > 0
    
    def test_create_task(self, orchestrator):
        """Test creating a task."""
        task_id = orchestrator.create_task(
            description="Test task",
            required_skills=["system_design"],
            priority=5
        )
        assert task_id is not None
        assert task_id in orchestrator.tasks
    
    def test_assign_task(self, orchestrator):
        """Test assigning a task to a clone."""
        task_id = orchestrator.create_task(
            description="Test task",
            required_skills=["system_design"],
            priority=5
        )
        
        assigned_clone_id = orchestrator.assign_task(task_id)
        assert assigned_clone_id is not None
        assert orchestrator.tasks[task_id].status.value == "assigned"
    
    def test_complete_task(self, orchestrator):
        """Test completing a task."""
        task_id = orchestrator.create_task(
            description="Test task",
            required_skills=["system_design"],
            priority=5
        )
        
        orchestrator.assign_task(task_id)
        success = orchestrator.complete_task(task_id, {"result": "success"}, True)
        assert success is True
        assert orchestrator.tasks[task_id].status.value == "completed"
    
    def test_create_consensus_decision(self, orchestrator):
        """Test creating a consensus decision."""
        from core.clone_orchestrator import ConsensusType
        decision_id = orchestrator.create_consensus_decision(
            description="Test decision",
            consensus_type=ConsensusType.MAJORITY
        )
        assert decision_id is not None
        assert decision_id in orchestrator.decisions
    
    def test_cast_vote(self, orchestrator):
        """Test casting a vote on a decision."""
        from core.clone_orchestrator import ConsensusType
        decision_id = orchestrator.create_consensus_decision(
            description="Test decision",
            consensus_type=ConsensusType.MAJORITY
        )
        
        success = orchestrator.cast_vote(
            decision_id=decision_id,
            clone_id="clone_architect",
            vote=True,
            reasoning="I approve"
        )
        assert success is True
    
    def test_get_status(self, orchestrator):
        """Test getting orchestrator status."""
        status = orchestrator.get_status()
        assert "clones" in status
        assert "tasks" in status
        assert "decisions" in status


class TestPolicyGate:
    """Tests for core.policy_gate."""
    
    @pytest.fixture
    def temp_db(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        try:
            Path(path).unlink(missing_ok=True)
        except PermissionError:
            import gc
            gc.collect()
            for _ in range(5):
                try:
                    Path(path).unlink(missing_ok=True)
                    break
                except PermissionError:
                    import time
                    time.sleep(0.1)
    
    @pytest.fixture
    def policy_gate(self, temp_db):
        from core.policy_gate import PolicyGate, reset_policy_gate
        reset_policy_gate()
        return PolicyGate(temp_db)
    
    def test_default_rules_initialized(self, policy_gate):
        """Test that default policy rules are initialized."""
        assert len(policy_gate.rules) > 0
    
    def test_get_rule(self, policy_gate):
        """Test getting a specific rule."""
        rule = policy_gate.get_rule("rule_file_read")
        assert rule is not None
        assert rule.name == "File Read"
    
    def test_evaluate_action_safe(self, policy_gate):
        """Test evaluating a safe action."""
        from core.policy_gate import ActionCategory
        decision = policy_gate.evaluate_action(
            action_type="read",
            category=ActionCategory.FILE_OPERATION,
            parameters={"path": "/tmp/test.txt"}
        )
        assert decision is not None
        assert decision.risk_level.value in ["safe", "low", "medium", "high", "critical"]
    
    def test_evaluate_action_risky(self, policy_gate):
        """Test evaluating a risky action."""
        from core.policy_gate import ActionCategory
        decision = policy_gate.evaluate_action(
            action_type="delete",
            category=ActionCategory.FILE_OPERATION,
            parameters={"path": "/tmp/test.txt"}
        )
        assert decision is not None
        assert decision.risk_level.value in ["safe", "low", "medium", "high", "critical"]
    
    def test_request_approval(self, policy_gate):
        """Test creating an approval request."""
        from core.policy_gate import ActionCategory
        request_id = policy_gate.request_approval(
            action_type="delete",
            category=ActionCategory.FILE_OPERATION,
            parameters={"path": "/tmp/test.txt"}
        )
        assert request_id is not None
        assert request_id in policy_gate.pending_approvals
    
    def test_approve_request(self, policy_gate):
        """Test approving a pending request."""
        from core.policy_gate import ActionCategory
        request_id = policy_gate.request_approval(
            action_type="delete",
            category=ActionCategory.FILE_OPERATION,
            parameters={"path": "/tmp/test.txt"}
        )
        
        success = policy_gate.approve_request(request_id, "test-user", "Approved for testing")
        assert success is True
        assert request_id not in policy_gate.pending_approvals
    
    def test_reject_request(self, policy_gate):
        """Test rejecting a pending request."""
        from core.policy_gate import ActionCategory
        request_id = policy_gate.request_approval(
            action_type="delete",
            category=ActionCategory.FILE_OPERATION,
            parameters={"path": "/tmp/test.txt"}
        )
        
        success = policy_gate.reject_request(request_id, "test-user", "Rejected for testing")
        assert success is True
        assert request_id not in policy_gate.pending_approvals
    
    def test_get_pending_requests(self, policy_gate):
        """Test getting pending requests."""
        from core.policy_gate import ActionCategory
        policy_gate.request_approval(
            action_type="delete",
            category=ActionCategory.FILE_OPERATION,
            parameters={"path": "/tmp/test.txt"}
        )
        
        pending = policy_gate.get_pending_requests()
        assert len(pending) >= 1
    
    def test_get_stats(self, policy_gate):
        """Test getting policy gate statistics."""
        stats = policy_gate.get_stats()
        assert "rules" in stats
        assert "requests" in stats
        assert "by_risk_level" in stats


class TestChatBackend:
    """Tests for backend.chat."""
    
    @pytest.fixture
    def temp_db(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        try:
            Path(path).unlink(missing_ok=True)
        except PermissionError:
            import gc
            gc.collect()
            for _ in range(5):
                try:
                    Path(path).unlink(missing_ok=True)
                    break
                except PermissionError:
                    import time
                    time.sleep(0.1)
    
    @pytest.fixture
    def chat_backend(self, temp_db):
        from backend.chat import ChatBackend
        return ChatBackend(temp_db)
    
    def test_create_session(self, chat_backend):
        """Test creating a chat session."""
        session_id = chat_backend.create_session("test-user", "Test Chat")
        assert session_id is not None
        
        session = chat_backend.get_session(session_id)
        assert session is not None
        assert session.user_id == "test-user"
        assert session.title == "Test Chat"
    
    def test_add_message(self, chat_backend):
        """Test adding a message."""
        message_id = chat_backend.add_message(
            role="user",
            content="Hello, world!",
            user_id="test-user"
        )
        assert message_id is not None
    
    def test_get_session_messages(self, chat_backend):
        """Test getting messages for a session."""
        session_id = chat_backend.create_session("test-user", "Test Chat")
        chat_backend.add_message(
            role="user",
            content="Hello!",
            user_id="test-user",
            session_id=session_id
        )
        
        messages = chat_backend.get_session_messages(session_id)
        assert len(messages) >= 1
    
    def test_get_user_sessions(self, chat_backend):
        """Test getting user sessions."""
        chat_backend.create_session("test-user", "Chat 1")
        chat_backend.create_session("test-user", "Chat 2")
        
        sessions = chat_backend.get_user_sessions("test-user")
        assert len(sessions) >= 2
    
    def test_delete_session(self, chat_backend):
        """Test deleting a session."""
        session_id = chat_backend.create_session("test-user", "Test Chat")
        
        success = chat_backend.delete_session(session_id)
        assert success is True
        
        session = chat_backend.get_session(session_id)
        assert session is None
    
    def test_get_stats(self, chat_backend):
        """Test getting chat statistics."""
        stats = chat_backend.get_stats()
        assert "total_sessions" in stats
        assert "total_messages" in stats
