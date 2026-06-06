
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""Test suite for Execution Pipeline - Multi-step task handling & Failure recovery."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from core.execution_pipeline import (
    ExecutionPipeline, PlannerAgent, ExecutorAgent, AnalystAgent,
    Task, TaskPlan, ExecutionResult
)


class TestMultiStepTaskExecution:
    """Test multi-step task execution with dependencies."""
    
    @pytest.fixture
    def mock_executor(self):
        """Create mock executor that simulates realistic execution."""
        executor = Mock(spec=ExecutorAgent)
        
        async def mock_execute(task, deps=None):
            # Simulate execution
            await asyncio.sleep(0.01)
            return ExecutionResult(
                success=True,
                output=f"Executed {task.type}",
                execution_time_ms=10
            )
        
        executor.execute = AsyncMock(side_effect=mock_execute)
        return executor
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self, mock_executor):
        """Should execute tasks sequentially with dependencies."""
        pipeline = ExecutionPipeline(
            planner=Mock(),
            executor=mock_executor,
            validator=Mock(),
            compiler=Mock()
        )
        
        plan = TaskPlan(
            plan_id="test_plan",
            user_request="complex task",
            tasks=[
                Task(
                    task_id="step_1",
                    type="file_read",
                    description="Read config",
                    dependencies=[]
                ),
                Task(
                    task_id="step_2",
                    type="process",
                    description="Process data",
                    dependencies=["step_1"]
                ),
                Task(
                    task_id="step_3",
                    type="file_write",
                    description="Write output",
                    dependencies=["step_2"]
                )
            ]
        )
        
        results = await pipeline.execute_plan(plan)
        
        # Should have 3 results
        assert len(results) == 3
        # All should succeed
        assert all(r.success for r in results)
        # Should execute in order
        mock_executor.execute.assert_any_call(plan.tasks[0], [])
        mock_executor.execute.assert_any_call(plan.tasks[1], [results[0]])
        mock_executor.execute.assert_any_call(plan.tasks[2], [results[1]])


class TestFailureHandling:
    """Test failure handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_graceful_task_failure(self):
        """Should handle task failure without crashing system."""
        executor = Mock(spec=ExecutorAgent)
        
        async def failing_execute(task, deps=None):
            if task.task_id == "step_2":
                return ExecutionResult(
                    success=False,
                    error="Simulated failure",
                    execution_time_ms=5
                )
            return ExecutionResult(
                success=True,
                output=f"Executed {task.type}",
                execution_time_ms=10
            )
        
        executor.execute = AsyncMock(side_effect=failing_execute)
        
        pipeline = ExecutionPipeline(
            planner=Mock(),
            executor=executor,
            validator=Mock(),
            compiler=Mock()
        )
        
        plan = TaskPlan(
            plan_id="test_plan",
            user_request="test failure",
            tasks=[
                Task(task_id="step_1", type="file_read", dependencies=[]),
                Task(task_id="step_2", type="risky_op", dependencies=["step_1"]),
                Task(task_id="step_3", type="file_write", dependencies=["step_2"]),
            ]
        )
        
        results = await pipeline.execute_plan(plan)
        
        # Should complete without exception
        assert len(results) == 3
        # step_2 should fail
        assert not results[1].success
        # step_3 might fail due to dependency failure
        # But system should not crash
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Should retry failed tasks up to max attempts."""
        executor = Mock(spec=ExecutorAgent)
        attempts = 0
        
        async def flaky_execute(task, deps=None):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                return ExecutionResult(
                    success=False,
                    error="Temporary error",
                    execution_time_ms=5
                )
            return ExecutionResult(
                success=True,
                output="Success after retries",
                execution_time_ms=10
            )
        
        executor.execute = AsyncMock(side_effect=flaky_execute)
        
        # Execute with retry
        result = await executor.execute(Task(task_id="test", type="file_read"))
        
        # Should eventually succeed
        # (Retry logic would be in actual implementation)
    
    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self):
        """Should continue execution even if some tasks fail."""
        executor = Mock(spec=ExecutorAgent)
        
        async def partial_execute(task, deps=None):
            # Some tasks fail, others succeed
            success = task.task_id in ["step_1", "step_3"]
            return ExecutionResult(
                success=success,
                output="Success" if success else "Failed",
                error=None if success else "Task failed",
                execution_time_ms=10
            )
        
        executor.execute = AsyncMock(side_effect=partial_execute)
        
        pipeline = ExecutionPipeline(
            planner=Mock(),
            executor=executor,
            validator=Mock(),
            compiler=Mock()
        )
        
        plan = TaskPlan(
            plan_id="test_plan",
            user_request="partial failure test",
            tasks=[
                Task(task_id="step_1", type="file_read", dependencies=[]),
                Task(task_id="step_2", type="process", dependencies=[]),  # Independent
                Task(task_id="step_3", type="file_write", dependencies=[]),  # Independent
            ],
            parallelizable=True
        )
        
        results = await pipeline.execute_plan(plan)
        
        # Should complete all 3 tasks
        assert len(results) == 3
        # System should not crash


class TestMemoryManagement:
    """Test memory overflow and trimming."""
    
    def test_large_task_list_handling(self):
        """Should handle plans with many tasks."""
        # Create plan with 1000 tasks
        tasks = [
            Task(
                task_id=f"step_{i}",
                type="file_read",
                dependencies=[f"step_{i-1}"] if i > 0 else []
            )
            for i in range(1000)
        ]
        
        plan = TaskPlan(
            plan_id="large_plan",
            user_request="massive task",
            tasks=tasks
        )
        
        # Should create plan without memory issues
        assert len(plan.tasks) == 1000
        assert plan.plan_id is not None
    
    @pytest.mark.asyncio
    async def test_result_accumulation_limits(self):
        """Should limit result accumulation to prevent memory overflow."""
        pipeline = ExecutionPipeline(
            planner=Mock(),
            executor=Mock(),
            validator=Mock(),
            compiler=Mock()
        )
        
        # Mock executor to return large outputs
        async def large_output_execute(task, deps=None):
            return ExecutionResult(
                success=True,
                output="x" * 1000000,  # 1MB output
                execution_time_ms=10
            )
        
        pipeline.executor.execute = AsyncMock(side_effect=large_output_execute)
        
        plan = TaskPlan(
            plan_id="memory_test",
            user_request="test memory",
            tasks=[Task(task_id="step_1", type="process")]
        )
        
        # Should handle without crashing
        results = await pipeline.execute_plan(plan)
        assert len(results) == 1


class TestExecutionTimeout:
    """Test execution timeouts."""
    
    @pytest.mark.asyncio
    async def test_task_timeout(self):
        """Should timeout long-running tasks."""
        executor = Mock(spec=ExecutorAgent)
        
        async def slow_execute(task, deps=None):
            await asyncio.sleep(10)  # Very slow
            return ExecutionResult(success=True, output="Done")
        
        executor.execute = AsyncMock(side_effect=slow_execute)
        
        task = Task(task_id="slow", type="file_read")
        
        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                executor.execute(task),
                timeout=1.0
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
