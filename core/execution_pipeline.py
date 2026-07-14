"""
AsimNexus — Execution Pipeline
==============================
Multi-step task execution with dependency resolution, failure handling, and retry logic.
"""

import asyncio
import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Awaitable


@dataclass
class Task:
    """A single unit of work within a plan."""
    id: str
    type: str = "generic"
    dependencies: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    timeout: float = 30.0


@dataclass
class TaskPlan:
    """A collection of tasks to be executed, possibly with dependencies."""
    id: str
    user_request: str
    tasks: List[Task] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of executing a single task."""
    task_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    retries: int = 0


class PlannerAgent:
    """Responsible for decomposing user requests into task plans."""

    async def create_plan(self, user_request: str) -> TaskPlan:
        """Create a plan from a user request."""
        plan_id = str(uuid.uuid4())
        return TaskPlan(
            id=plan_id,
            user_request=user_request,
            tasks=[]
        )


class ExecutorAgent:
    """Responsible for executing individual tasks."""

    async def execute(self, task: Task, deps: Optional[Dict[str, ExecutionResult]] = None) -> ExecutionResult:
        """Execute a single task."""
        start = time.time()
        try:
            # Simulate execution
            await asyncio.sleep(0.01)
            elapsed = (time.time() - start) * 1000
            return ExecutionResult(
                task_id=task.id,
                success=True,
                output=f"Executed {task.type}",
                execution_time_ms=elapsed
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ExecutionResult(
                task_id=task.id,
                success=False,
                error=str(e),
                execution_time_ms=elapsed
            )


class AnalystAgent:
    """Responsible for analyzing execution results and providing insights."""

    async def analyze(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """Analyze execution results."""
        total = len(results)
        succeeded = sum(1 for r in results if r.success)
        failed = total - succeeded
        return {
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "success_rate": (succeeded / total * 100) if total > 0 else 0.0
        }


class ExecutionPipeline:
    """Orchestrates multi-step task execution with dependency resolution."""

    def __init__(
        self,
        planner: Any = None,
        executor: Any = None,
        validator: Any = None,
        compiler: Any = None
    ):
        self.planner = planner or PlannerAgent()
        self.executor = executor or ExecutorAgent()
        self.validator = validator
        self.compiler = compiler
        self._results: Dict[str, ExecutionResult] = {}

    async def execute_plan(self, plan: TaskPlan) -> List[ExecutionResult]:
        """Execute all tasks in a plan, respecting dependencies."""
        results: List[ExecutionResult] = []
        completed: Dict[str, ExecutionResult] = {}

        # Build dependency graph
        task_map = {task.id: task for task in plan.tasks}
        remaining = set(task.id for task in plan.tasks)

        while remaining:
            # Find tasks whose dependencies are all met
            ready = [
                tid for tid in remaining
                if all(dep in completed for dep in task_map[tid].dependencies)
            ]

            if not ready:
                # Circular dependency or missing dependency - fail remaining
                for tid in remaining:
                    results.append(ExecutionResult(
                        task_id=tid,
                        success=False,
                        error="Dependency not met or circular dependency",
                        execution_time_ms=0
                    ))
                break

            # Execute ready tasks
            for tid in ready:
                task = task_map[tid]
                deps = {dep: completed[dep] for dep in task.dependencies if dep in completed}

                # Retry logic
                result = None
                for attempt in range(task.max_retries):
                    try:
                        result = await asyncio.wait_for(
                            self.executor.execute(task, deps),
                            timeout=task.timeout
                        )
                        result.retries = attempt
                        if result.success:
                            break
                    except asyncio.TimeoutError:
                        result = ExecutionResult(
                            task_id=tid,
                            success=False,
                            error="Timeout",
                            execution_time_ms=task.timeout * 1000,
                            retries=attempt
                        )
                    except Exception as e:
                        result = ExecutionResult(
                            task_id=tid,
                            success=False,
                            error=str(e),
                            execution_time_ms=0,
                            retries=attempt
                        )
                    if attempt < task.max_retries - 1:
                        await asyncio.sleep(0.1 * (attempt + 1))

                if result is None:
                    result = ExecutionResult(
                        task_id=tid,
                        success=False,
                        error="Failed to execute",
                        execution_time_ms=0
                    )

                completed[tid] = result
                results.append(result)
                remaining.remove(tid)

        self._results = {r.task_id: r for r in results}
        return results

    def get_result(self, task_id: str) -> Optional[ExecutionResult]:
        """Get the result for a specific task."""
        return self._results.get(task_id)
