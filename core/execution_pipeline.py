
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

import logging
logger = logging.getLogger(__name__)
"""Standardized Execution Pipeline: Planner → Executor → Validator."""
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ValidationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class Task:
    """Single executable task."""
    id: str
    type: str
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    execution_time_ms: float = 0.0


@dataclass
class TaskPlan:
    """Plan containing multiple tasks."""
    id: str
    user_request: str
    tasks: List[Task]
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_execution_order(self) -> List[Task]:
        """Get tasks in dependency-resolved order."""
        # Simple topological sort
        completed = set()
        order = []
        
        while len(order) < len(self.tasks):
            for task in self.tasks:
                if task.id in completed:
                    continue
                
                # Check if all dependencies are completed
                if all(dep in completed for dep in task.dependencies):
                    order.append(task)
                    completed.add(task.id)
        
        return order


@dataclass
class ExecutionResult:
    """Result of task execution."""
    task_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Validation:
    """Validation result for execution output."""
    task_id: str
    status: ValidationStatus
    score: float  # 0.0 - 1.0
    feedback: str
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation report for all tasks."""
    plan_id: str
    validations: List[Validation]
    all_passed: bool
    overall_score: float
    failed_tasks: List[str] = field(default_factory=list)


@dataclass
class FinalResponse:
    """Final compiled response to user."""
    request_id: str
    user_request: str
    response: str
    success: bool
    execution_summary: Dict[str, Any]
    tasks_completed: int
    tasks_failed: int
    total_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)


class PlannerAgent:
    """Plans task decomposition and execution strategy."""
    
    def __init__(self, model_connector=None, hybrid_router=None):
        self.model_connector = model_connector
        self.hybrid_router = hybrid_router
    
    async def plan(self, user_request: str, context: Dict = None) -> TaskPlan:
        """Create execution plan from user request."""
        plan_id = str(uuid.uuid4())
        
        # Use hybrid router for intent classification
        route_decision = await self.hybrid_router.route(user_request)
        
        # Simple planning logic
        if route_decision.confidence > 0.8:
            # Single task plan
            task = Task(
                id=f"task_{uuid.uuid4().hex[:8]}",
                type=route_decision.intent.value,
                parameters=route_decision.parameters
            )
            return TaskPlan(
                id=plan_id,
                user_request=user_request,
                tasks=[task]
            )
        else:
            # Multi-step plan using LLM
            return await self._create_multi_step_plan(plan_id, user_request, context)
    
    async def _create_multi_step_plan(self, plan_id: str, user_request: str, 
                                       context: Dict) -> TaskPlan:
        """Create multi-step plan using LLM."""
        if not self.model_connector:
            # Fallback to single task
            task = Task(
                id=f"task_{uuid.uuid4().hex[:8]}",
                type="llm_query",
                parameters={"query": user_request}
            )
            return TaskPlan(id=plan_id, user_request=user_request, tasks=[task])
        
        system_prompt = """You are a task planner. Break down the user request into executable steps.
Respond with JSON format:
{
  "steps": [
    {
      "id": "step_1",
      "type": "file_operation|system_command|codebase_query|...",
      "tool": "tool_name (optional)",
      "parameters": {...},
      "dependencies": ["step_ids"]
    }
  ]
}"""
        
        prompt = f"Request: {user_request}\n\nCreate a step-by-step plan:"
        
        try:
            import json
            response = await self.model_connector.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2
            )
            
            plan_data = json.loads(response.strip())
            
            tasks = []
            for step in plan_data.get('steps', []):
                task = Task(
                    id=step.get('id', f"task_{uuid.uuid4().hex[:8]}"),
                    type=step.get('type', 'general'),
                    tool_name=step.get('tool'),
                    parameters=step.get('parameters', {}),
                    dependencies=step.get('dependencies', [])
                )
                tasks.append(task)
            
            return TaskPlan(id=plan_id, user_request=user_request, tasks=tasks)
            
        except Exception as e:
            print(f"Multi-step planning error: {e}")
            # Fallback
            task = Task(
                id=f"task_{uuid.uuid4().hex[:8]}",
                type="general",
                parameters={"query": user_request}
            )
            return TaskPlan(id=plan_id, user_request=user_request, tasks=[task])


class ExecutorAgent:
    """Executes tasks using tools and sandboxes."""
    
    def __init__(self, tool_registry=None, sandbox=None, state_manager=None):
        self.tool_registry = tool_registry
        self.sandbox = sandbox
        self.state_manager = state_manager
    
    async def execute(self, task: Task, context: Dict = None) -> ExecutionResult:
        """Execute a single task."""
        import time
        start_time = time.time()
        
        task.status = TaskStatus.RUNNING
        
        try:
            # Update state
            if self.state_manager:
                await self.state_manager.update_task_status(
                    task.id, 
                    "running",
                    {"started_at": datetime.now().isoformat()}
                )
            
            # Execute based on task type
            if task.tool_name and self.tool_registry:
                result = await self._execute_tool(task)
            else:
                result = await self._execute_direct(task, context)
            
            execution_time = (time.time() - start_time) * 1000
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.execution_time_ms = execution_time
            
            # Update state
            if self.state_manager:
                await self.state_manager.update_task_status(
                    task.id,
                    "completed",
                    {"result": result, "execution_time_ms": execution_time}
                )
            
            return ExecutionResult(
                task_id=task.id,
                success=True,
                output=result,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.execution_time_ms = execution_time
            
            return ExecutionResult(
                task_id=task.id,
                success=False,
                output=None,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    async def _execute_tool(self, task: Task) -> Any:
        """Execute using tool registry."""
        # Tool execution logic here
        return {"tool": task.tool_name, "parameters": task.parameters, "status": "executed"}
    
    async def _execute_direct(self, task: Task, context: Dict) -> Any:
        """Direct execution without tool."""
        # Direct execution logic here
        return {"type": task.type, "parameters": task.parameters, "status": "completed"}
    
    async def execute_parallel(self, tasks: List[Task], 
                               max_concurrency: int = 5) -> List[ExecutionResult]:
        """Execute multiple tasks with controlled concurrency."""
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def execute_with_limit(task):
            async with semaphore:
                return await self.execute(task)
        
        results = await asyncio.gather(*[execute_with_limit(t) for t in tasks])
        return results


class AnalystAgent:
    """Validates execution results and provides feedback."""
    
    def __init__(self, model_connector=None):
        self.model_connector = model_connector
    
    async def validate(self, task: Task, result: ExecutionResult, 
                       expectation: Dict = None) -> Validation:
        """Validate a single execution result."""
        
        # Check if execution succeeded
        if not result.success:
            return Validation(
                task_id=task.id,
                status=ValidationStatus.FAILED,
                score=0.0,
                feedback=f"Execution failed: {result.error}",
                suggestions=["Check error message", "Retry with modified parameters"]
            )
        
        # Check completeness
        score = 1.0
        feedback = "Execution completed successfully"
        suggestions = []
        
        # Validate against expectation if provided
        if expectation and result.output:
            required_keys = expectation.get('required_output_keys', [])
            missing_keys = [k for k in required_keys 
                          if k not in (result.output if isinstance(result.output, dict) else {})]
            
            if missing_keys:
                score = 0.5
                feedback = f"Partial result: missing keys {missing_keys}"
                suggestions.append(f"Ensure output contains: {missing_keys}")
        
        # LLM validation for complex outputs
        if self.model_connector and score > 0.5:
            llm_validation = await self._llm_validate(task, result)
            if llm_validation['score'] < score:
                score = llm_validation['score']
                feedback = llm_validation['feedback']
                suggestions.extend(llm_validation.get('suggestions', []))
        
        status = ValidationStatus.PASSED if score >= 0.8 else (
            ValidationStatus.PARTIAL if score >= 0.5 else ValidationStatus.FAILED
        )
        
        return Validation(
            task_id=task.id,
            status=status,
            score=score,
            feedback=feedback,
            suggestions=suggestions
        )
    
    async def validate_batch(self, plan: TaskPlan, 
                             results: List[ExecutionResult]) -> ValidationReport:
        """Validate all results in a plan."""
        validations = []
        failed_tasks = []
        total_score = 0.0
        
        for task, result in zip(plan.tasks, results):
            validation = await self.validate(task, result)
            validations.append(validation)
            total_score += validation.score
            
            if validation.status == ValidationStatus.FAILED:
                failed_tasks.append(task.id)
        
        overall_score = total_score / len(validations) if validations else 0.0
        all_passed = len(failed_tasks) == 0
        
        return ValidationReport(
            plan_id=plan.id,
            validations=validations,
            all_passed=all_passed,
            overall_score=overall_score,
            failed_tasks=failed_tasks
        )
    
    async def _llm_validate(self, task: Task, result: ExecutionResult) -> Dict:
        """Use LLM for sophisticated validation."""
        # Placeholder for LLM validation
        return {"score": 1.0, "feedback": "Valid", "suggestions": []}


class ResponseCompiler:
    """Compiles execution results into final user response."""
    
    def __init__(self, model_connector=None):
        self.model_connector = model_connector
    
    async def compile(self, plan: TaskPlan, results: List[ExecutionResult],
                      validation: ValidationReport) -> str:
        """Compile final response from execution results."""
        
        # Build execution summary
        summary_parts = []
        
        for task, result in zip(plan.tasks, results):
            if result.success:
                summary_parts.append(f"✓ {task.type}: Completed ({result.execution_time_ms:.0f}ms)")
            else:
                summary_parts.append(f"✗ {task.type}: Failed - {result.error}")
        
        # If validation failed, include feedback
        if not validation.all_passed:
            summary_parts.append("\n⚠ Some tasks require attention:")
            for val in validation.validations:
                if val.status != ValidationStatus.PASSED:
                    summary_parts.append(f"  • Task {val.task_id}: {val.feedback}")
        
        # If we have a model connector, use it to generate natural response
        if self.model_connector and results:
            successful_outputs = [r.output for r in results if r.success]
            if successful_outputs:
                return await self._generate_natural_response(
                    plan.user_request, successful_outputs, validation
                )
        
        return "\n".join(summary_parts)
    
    async def _generate_natural_response(self, user_request: str, 
                                         outputs: List[Any],
                                         validation: ValidationReport) -> str:
        """Generate natural language response using LLM."""
        if not self.model_connector:
            return str(outputs)
        
        prompt = f"""User request: {user_request}

Execution results: {outputs}

Validation: {validation.overall_score:.0%} passed

Provide a natural response to the user summarizing the results."""
        
        return await self.model_connector.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=500
        )


class ExecutionPipeline:
    """
    Standardized execution pipeline: Planner → Executor → Validator.
    """
    
    def __init__(self, 
                 planner: PlannerAgent = None,
                 executor: ExecutorAgent = None,
                 validator: AnalystAgent = None,
                 compiler: ResponseCompiler = None,
                 state_manager = None):
        
        self.planner = planner
        self.executor = executor
        self.validator = validator
        self.compiler = compiler
        self.state_manager = state_manager
    
    async def execute(self, user_request: str, context: Dict = None) -> FinalResponse:
        """
        Execute user request through standardized pipeline.
        
        Flow:
        1. Plan: Decompose request into tasks
        2. Execute: Run all tasks
        3. Validate: Check all results
        4. Compile: Generate final response
        """
        import time
        start_time = time.time()
        
        request_id = str(uuid.uuid4())
        
        try:
            # Stage 1: Planning
            plan = await self.planner.plan(user_request, context)
            
            # Stage 2: Execution
            execution_order = plan.get_execution_order()
            results = []
            
            # Execute with dependency resolution
            for task in execution_order:
                # Wait for dependencies
                while any(dep not in [r.task_id for r in results] 
                         for dep in task.dependencies):
                    await asyncio.sleep(0.1)
                
                result = await self.executor.execute(task, context)
                results.append(result)
                
                # Update task in plan
                for t in plan.tasks:
                    if t.id == task.id:
                        t.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                        t.result = result.output
            
            # Stage 3: Validation
            validation = await self.validator.validate_batch(plan, results)
            
            # Stage 4: Response Compilation
            response_text = await self.compiler.compile(plan, results, validation)
            
            total_time = (time.time() - start_time) * 1000
            
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            return FinalResponse(
                request_id=request_id,
                user_request=user_request,
                response=response_text,
                success=validation.all_passed,
                execution_summary={
                    "plan_id": plan.id,
                    "total_tasks": len(plan.tasks),
                    "validation_score": validation.overall_score,
                    "validation_feedback": [
                        v.feedback for v in validation.validations 
                        if v.status != ValidationStatus.PASSED
                    ]
                },
                tasks_completed=successful,
                tasks_failed=failed,
                total_time_ms=total_time
            )
            
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            
            return FinalResponse(
                request_id=request_id,
                user_request=user_request,
                response=f"Pipeline error: {str(e)}",
                success=False,
                execution_summary={"error": str(e)},
                tasks_completed=0,
                tasks_failed=0,
                total_time_ms=total_time
            )
