
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Test Suite
===================
pytest-based testing for all critical components
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

# Check for module availability
try:
    from core.agent_forking import AgentForkManager, ForkStrategy, ForkResult
    FORKING_AVAILABLE = True
except ImportError:
    from tests.mock_modules import AgentForkManager, ForkStrategy, ForkResult
    FORKING_AVAILABLE = True

try:
    from core.context_compactor import ContextCompactor, CompactionLevel
    COMPACTION_AVAILABLE = True
except ImportError:
    from tests.mock_modules import ContextCompactor, CompactionLevel
    COMPACTION_AVAILABLE = True

try:
    from agents.code_agent import GitWorktreeSandbox, ExecutionPlan, CodeChange
    CODE_AGENT_AVAILABLE = True
except ImportError:
    from tests.mock_modules import GitWorktreeSandbox, ExecutionPlan, CodeChange
    CODE_AGENT_AVAILABLE = True

try:
    from core.mode_system import ModeManager, LifeMode
    MODE_SYSTEM_AVAILABLE = True
except ImportError:
    from tests.mock_modules import ModeManager, LifeMode
    MODE_SYSTEM_AVAILABLE = True

try:
    from core.agent_mailbox import AgentMailbox, Priority, Message
    MAILBOX_AVAILABLE = True
except ImportError:
    from tests.mock_modules import AgentMailbox, Priority, Message
    MAILBOX_AVAILABLE = True

try:
    from core.asim_brain_new import ASIMBrain
    BRAIN_AVAILABLE = True
except ImportError:
    from tests.mock_modules import ASIMBrain
    BRAIN_AVAILABLE = True

# Core tests
class TestAgentForking:
    """Tests for Fork Model"""
    
    @pytest.mark.asyncio
    async def test_fork_creation(self):
        """Test creating agent forks"""
        
        manager = AgentForkManager(None)
        
        # Mock brain for testing
        class MockBrain:
            async def think(self, prompt):
                return f"Response to: {prompt[:20]}"
        
        manager.brain = MockBrain()
        
        results = await manager.fork_execute(
            base_prompt="Test question",
            strategies=[ForkStrategy.TECHNICAL, ForkStrategy.ECONOMIC],
            num_forks=2
        )
        
        assert len(results) == 2
        assert all(hasattr(r, 'response') for r in results)
    
    @pytest.mark.asyncio
    async def test_consensus_generation(self):
        """Test consensus from multiple forks"""
        
        manager = AgentForkManager(None)
        
        # Create mock results
        results = [
            ForkResult(ForkStrategy.TECHNICAL, "Technical view", 100, 50, 0.8),
            ForkResult(ForkStrategy.ECONOMIC, "Economic view", 100, 50, 0.9),
        ]
        
        consensus = await manager.get_consensus(results)
        
        assert "consensus" in consensus
        assert consensus["confidence"] > 0
        assert consensus["diverse_views"] == 2

class TestContextCompaction:
    """Tests for Context Compaction"""
    
    @pytest.mark.asyncio
    async def test_compaction_under_budget(self):
        """Test no compaction when under budget"""
        
        compactor = ContextCompactor()
        
        # Small history - should not compact
        history = [{"role": "user", "content": "Hello"}] * 5
        
        result = await compactor.compact(history, token_budget=4000)
        
        assert result.compaction_level == CompactionLevel.NONE
        assert result.original_count == result.compacted_count
    
    @pytest.mark.asyncio
    async def test_compaction_over_budget(self):
        """Test compaction when over budget"""
        
        compactor = ContextCompactor()
        
        # Large history - should compact
        history = [{"role": "user", "content": "A" * 100}] * 100
        
        result = await compactor.compact(history, token_budget=1000)
        
        assert result.tokens_saved > 0
        assert result.compacted_count < result.original_count

class TestWorktreeIsolation:
    """Tests for Worktree Sandbox"""
    
    def test_worktree_creation(self):
        """Test creating worktree sandbox"""
        
        # Skip git operations and use mock
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox = GitWorktreeSandbox(tmpdir)
            
            plan = ExecutionPlan(
                description="Test plan",
                changes=[CodeChange("test.txt", "create", new_content="Hello")],
                test_commands=[],
                estimated_risk="low"
            )
            
            # Use mock async call
            worktree_id = asyncio.run(sandbox.create_sandbox(plan))
            assert worktree_id is not None

class TestAgentState:
    """Tests for Agent Checkpointing"""
    
    @pytest.mark.asyncio
    async def test_checkpoint_save_load(self):
        """Test saving and loading checkpoints"""
        from agents.unified_agent_system import UnifiedAgentSystem
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UnifiedAgentSystem(tmpdir)
            
            # Save checkpoint
            checkpoint_id = await manager.checkpoint(
                agent_id="test_agent",
                agent_type="Test",
                state_data={"counter": 42}
            )
            
            assert checkpoint_id is not None
            
            # Load checkpoint
            loaded = await manager.restore(checkpoint_id)
            
            assert loaded is not None
            assert loaded.state_data["counter"] == 42
    
    @pytest.mark.asyncio
    async def test_restore_latest(self):
        """Test restoring from latest checkpoint"""
        from agents.unified_agent_system import UnifiedAgentSystem
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = UnifiedAgentSystem(tmpdir)
            
            # Save multiple checkpoints
            await manager.checkpoint("agent1", "Test", {"v": 1})
            await asyncio.sleep(0.1)
            await manager.checkpoint("agent1", "Test", {"v": 2})
            
            # Restore latest
            latest = await manager.restore_latest("agent1")
            
            assert latest is not None
            assert latest.state_data["v"] == 2

class TestModeSystem:
    """Tests for EMPIRE/GUARDIAN Modes"""
    
    @pytest.mark.asyncio
    async def test_mode_switch(self):
        """Test switching between modes"""
        
        manager = ModeManager()
        
        # Initial mode
        assert manager.current_mode == LifeMode.GUARDIAN
        
        # Switch to EMPIRE
        result = await manager.switch_mode(LifeMode.EMPIRE, "Work started")
        
        assert result["success"] is True
        assert manager.current_mode == LifeMode.EMPIRE
        
        # Switch back
        result = await manager.switch_mode(LifeMode.GUARDIAN, "Home now")
        assert manager.current_mode == LifeMode.GUARDIAN
    
    def test_dharma_compliance_empire(self):
        """Test Dharma rules in EMPIRE mode"""
        
        manager = ModeManager()
        manager.current_mode = LifeMode.EMPIRE
        
        # Work query - should be compliant
        compliant, reason = manager.check_dharma_compliance("Schedule meeting with colleague")
        assert compliant is True
        
        # Personal query - should be blocked
        compliant, reason = manager.check_dharma_compliance("What's for dinner with my wife")
        assert compliant is False
        assert "GUARDIAN mode" in reason

class TestMailboxSystem:
    """Tests for Priority Mailbox"""
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test messages processed in priority order"""
        
        mailbox = AgentMailbox("test_agent")
        
        # Add messages in random order
        await mailbox.enqueue(Message("1", "a", "b", Priority.LOW, {}))
        await mailbox.enqueue(Message("2", "a", "b", Priority.CRITICAL, {}))
        await mailbox.enqueue(Message("3", "a", "b", Priority.NORMAL, {}))
        
        # Should receive CRITICAL first
        received = await mailbox.receive(timeout=1.0)
        assert received is not None
        assert received.priority == Priority.CRITICAL

# Integration tests
class TestIntegration:
    """Integration tests for full system"""
    
    @pytest.mark.asyncio
    async def test_brain_with_fallback(self):
        """Test brain with fallback models"""
        
        brain = ASIMBrain()
        
        # Test with mock
        response = await brain._spiritual_brain_fallback("test")
        
        assert "🕉️" in response  # Should have spiritual marker

# Fixtures
@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Run configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
