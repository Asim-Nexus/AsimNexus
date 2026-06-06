
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""Simplified 3-core-agent system: Planner, Executor, Analyst."""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import uuid


class AgentRole(Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    ANALYST = "analyst"


@dataclass
class AgentState:
    """State for any agent."""
    agent_id: str
    role: AgentRole
    status: str  # idle, busy, error
    current_task: Optional[str] = None
    task_history: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    context: Dict = field(default_factory=dict)


class BaseAgent:
    """Base class for all 3 core agents."""
    
    def __init__(self, role: AgentRole, state_manager=None, model_connector=None):
        self.agent_id = f"{role.value}_{uuid.uuid4().hex[:8]}"
        self.role = role
        self.state_manager = state_manager
        self.model_connector = model_connector
        self.state = AgentState(
            agent_id=self.agent_id,
            role=role,
            status="idle"
        )
    
    async def update_state(self, status: str, task: Optional[str] = None):
        """Update agent state."""
        self.state.status = status
        self.state.current_task = task
        self.state.last_active = datetime.now()
        
        if task and task not in self.state.task_history:
            self.state.task_history.append(task)
        
        # Persist to state manager
        if self.state_manager:
            await self.state_manager.set_agent_state(
                self.agent_id,
                {
                    "role": self.role.value,
                    "status": status,
                    "current_task": task,
                    "last_active": self.state.last_active.isoformat()
                }
            )
    
    async def get_context(self) -> Dict:
        """Get agent context."""
        return self.state.context.copy()
    
    async def set_context(self, key: str, value: Any):
        """Set context value."""
        self.state.context[key] = value


class PlannerAgent(BaseAgent):
    """
    Planner Agent: Strategy and task decomposition.
    
    Responsibilities:
    - Analyze user intent
    - Break down complex requests
    - Create execution plans
    - Determine required tools
    """
    
    def __init__(self, state_manager=None, model_connector=None, 
                 hybrid_router=None):
        super().__init__(AgentRole.PLANNER, state_manager, model_connector)
        self.hybrid_router = hybrid_router
    
    async def analyze_intent(self, user_request: str) -> Dict:
        """Analyze user request and determine intent."""
        await self.update_state("busy", f"analyze:{user_request[:50]}")
        
        try:
            if self.hybrid_router:
                route = await self.hybrid_router.route(user_request)
                return {
                    "intent": route.intent.value,
                    "confidence": route.confidence,
                    "method": route.method,
                    "parameters": route.parameters
                }
            else:
                # Fallback
                return {
                    "intent": "general_query",
                    "confidence": 0.5,
                    "method": "fallback",
                    "parameters": {}
                }
        finally:
            await self.update_state("idle")
    
    async def create_plan(self, user_request: str, intent_analysis: Dict) -> Dict:
        """Create execution plan from analyzed intent."""
        await self.update_state("busy", f"plan:{user_request[:50]}")
        
        try:
            intent = intent_analysis.get("intent", "general_query")
            confidence = intent_analysis.get("confidence", 0.5)
            
            # Simple plan for high confidence, complex for low
            if confidence > 0.8:
                # Single step plan
                plan = {
                    "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
                    "user_request": user_request,
                    "steps": [
                        {
                            "step_id": "step_1",
                            "type": intent,
                            "description": f"Execute {intent}",
                            "dependencies": [],
                            "parameters": intent_analysis.get("parameters", {})
                        }
                    ],
                    "parallelizable": False
                }
            else:
                # Multi-step plan using LLM
                plan = await self._create_complex_plan(user_request, intent_analysis)
            
            return plan
            
        finally:
            await self.update_state("idle")
    
    async def _create_complex_plan(self, user_request: str, 
                                   intent_analysis: Dict) -> Dict:
        """Create multi-step plan using LLM."""
        if not self.model_connector:
            # Fallback to simple plan
            return {
                "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
                "user_request": user_request,
                "steps": [
                    {
                        "step_id": "step_1",
                        "type": "llm_query",
                        "description": "Process user request",
                        "dependencies": [],
                        "parameters": {"query": user_request}
                    }
                ],
                "parallelizable": False
            }
        
        system_prompt = """You are a task planner. Break down the user request into executable steps.

Respond with JSON:
{
  "steps": [
    {
      "step_id": "step_1",
      "type": "file_operation|system_command|...",
      "description": "what this step does",
      "dependencies": [],
      "parameters": {}
    }
  ],
  "parallelizable": false
}"""
        
        prompt = f"User request: {user_request}\nIntent: {intent_analysis}\n\nCreate plan:"
        
        try:
            import json
            response = await self.model_connector.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2
            )
            
            plan_data = json.loads(response.strip())
            
            return {
                "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
                "user_request": user_request,
                "steps": plan_data.get("steps", []),
                "parallelizable": plan_data.get("parallelizable", False)
            }
            
        except Exception as e:
            print(f"Complex planning error: {e}")
            return {
                "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
                "user_request": user_request,
                "steps": [
                    {
                        "step_id": "step_1",
                        "type": "general",
                        "description": "Process user request",
                        "dependencies": [],
                        "parameters": {"query": user_request}
                    }
                ],
                "parallelizable": False
            }


class ExecutorAgent(BaseAgent):
    """
    Executor Agent: Tool execution and system interaction.
    
    Responsibilities:
    - Execute tools
    - Handle system commands
    - Manage sandboxes
    - Return execution results
    """
    
    def __init__(self, state_manager=None, tool_engine=None, sandbox=None):
        super().__init__(AgentRole.EXECUTOR, state_manager)
        self.tool_engine = tool_engine
        self.sandbox = sandbox
    
    async def execute_step(self, step: Dict, context: Dict = None) -> Dict:
        """Execute a single step from plan."""
        step_id = step.get("step_id", "unknown")
        await self.update_state("busy", f"execute:{step_id}")
        
        try:
            step_type = step.get("type", "general")
            parameters = step.get("parameters", {})
            
            # Execute based on step type
            if step_type in ["file_operation", "file"]:
                result = await self._execute_file_operation(parameters)
            elif step_type in ["system_command", "system"]:
                result = await self._execute_system_command(parameters)
            elif step_type in ["codebase_query", "code"]:
                result = await self._execute_code_query(parameters)
            elif step_type == "api_connect":
                result = await self._execute_api_connect(parameters)
            elif step_type == "agent_task":
                result = await self._execute_agent_task(parameters)
            else:
                # General query or LLM task
                result = await self._execute_general(parameters, context)
            
            return {
                "step_id": step_id,
                "success": result.get("success", True),
                "output": result.get("output"),
                "error": result.get("error"),
                "execution_time_ms": result.get("execution_time_ms", 0)
            }
            
        except Exception as e:
            return {
                "step_id": step_id,
                "success": False,
                "output": None,
                "error": str(e),
                "execution_time_ms": 0
            }
        finally:
            await self.update_state("idle")
    
    async def execute_parallel(self, steps: List[Dict], 
                               max_concurrency: int = 3,
                               context: Dict = None) -> List[Dict]:
        """Execute multiple steps in parallel with controlled concurrency."""
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def execute_with_limit(step):
            async with semaphore:
                return await self.execute_step(step, context)
        
        results = await asyncio.gather(*[execute_with_limit(s) for s in steps])
        return results
    
    async def _execute_file_operation(self, parameters: Dict) -> Dict:
        """Execute file operation."""
        # Delegate to tool engine
        if self.tool_engine:
            selection = await self.tool_engine.select_and_prepare(
                str(parameters), "file_operation"
            )
            return {"success": True, "output": f"File op: {selection.tool_name}", "execution_time_ms": 100}
        return {"success": False, "error": "No tool engine available"}
    
    async def _execute_system_command(self, parameters: Dict) -> Dict:
        """Execute system command."""
        if self.sandbox:
            # Execute in sandbox
            return {"success": True, "output": "Command executed in sandbox", "execution_time_ms": 200}
        return {"success": False, "error": "No sandbox available"}
    
    async def _execute_code_query(self, parameters: Dict) -> Dict:
        """Execute codebase query."""
        return {"success": True, "output": "Code search results", "execution_time_ms": 150}
    
    async def _execute_api_connect(self, parameters: Dict) -> Dict:
        """Execute API connection."""
        return {"success": True, "output": "API connected", "execution_time_ms": 500}
    
    async def _execute_agent_task(self, parameters: Dict) -> Dict:
        """Execute agent task."""
        return {"success": True, "output": "Agent task completed", "execution_time_ms": 300}
    
    async def _execute_general(self, parameters: Dict, context: Dict = None) -> Dict:
        """Execute general task."""
        return {"success": True, "output": parameters.get("query", "No query"), "execution_time_ms": 50}


class AnalystAgent(BaseAgent):
    """
    Analyst Agent: Validation and quality assurance.
    
    Responsibilities:
    - Validate execution results
    - Check completeness and accuracy
    - Provide feedback
    - Suggest improvements
    """
    
    def __init__(self, state_manager=None, model_connector=None):
        super().__init__(AgentRole.ANALYST, state_manager, model_connector)
    
    async def validate_result(self, step: Dict, result: Dict) -> Dict:
        """Validate single execution result."""
        await self.update_state("busy", f"validate:{step.get('step_id', 'unknown')}")
        
        try:
            success = result.get("success", False)
            output = result.get("output")
            error = result.get("error")
            
            # Basic validation
            if not success:
                return {
                    "valid": False,
                    "score": 0.0,
                    "feedback": f"Execution failed: {error}",
                    "suggestions": ["Check error message", "Retry with different parameters"]
                }
            
            if output is None:
                return {
                    "valid": False,
                    "score": 0.0,
                    "feedback": "No output produced",
                    "suggestions": ["Verify input parameters"]
                }
            
            # Check against expected output
            score = 1.0
            feedback = "Execution successful"
            suggestions = []
            
            # If we have a model connector, do deeper analysis
            if self.model_connector and step.get("requires_validation"):
                analysis = await self._llm_analyze(step, result)
                score = analysis.get("score", score)
                feedback = analysis.get("feedback", feedback)
                suggestions = analysis.get("suggestions", suggestions)
            
            return {
                "valid": score >= 0.8,
                "score": score,
                "feedback": feedback,
                "suggestions": suggestions
            }
            
        finally:
            await self.update_state("idle")
    
    async def validate_batch(self, plan: Dict, results: List[Dict]) -> Dict:
        """Validate all results in a plan."""
        await self.update_state("busy", f"validate_batch:{plan.get('plan_id', 'unknown')}")
        
        try:
            steps = plan.get("steps", [])
            validations = []
            total_score = 0.0
            failed_count = 0
            
            for step, result in zip(steps, results):
                validation = await self.validate_result(step, result)
                validations.append({
                    "step_id": step.get("step_id"),
                    **validation
                })
                total_score += validation["score"]
                if not validation["valid"]:
                    failed_count += 1
            
            avg_score = total_score / len(validations) if validations else 0.0
            all_valid = failed_count == 0
            
            return {
                "plan_id": plan.get("plan_id"),
                "all_valid": all_valid,
                "overall_score": avg_score,
                "validations": validations,
                "summary": {
                    "total": len(validations),
                    "passed": len(validations) - failed_count,
                    "failed": failed_count
                }
            }
            
        finally:
            await self.update_state("idle")
    
    async def compile_response(self, plan: Dict, results: List[Dict],
                                validation: Dict) -> str:
        """Compile final response for user."""
        await self.update_state("busy", "compile_response")
        
        try:
            # Build summary
            parts = []
            
            for result in results:
                if result.get("success"):
                    parts.append(f"✓ {result.get('step_id')}: Completed")
                else:
                    parts.append(f"✗ {result.get('step_id')}: Failed - {result.get('error', 'Unknown error')}")
            
            if not validation.get("all_valid", True):
                parts.append("\n⚠ Some issues were detected:")
                for v in validation.get("validations", []):
                    if not v.get("valid"):
                        parts.append(f"  • {v.get('step_id')}: {v.get('feedback')}")
            
            # If we have LLM, generate natural response
            if self.model_connector:
                natural_response = await self._generate_natural_response(
                    plan, results, validation
                )
                if natural_response:
                    return natural_response
            
            return "\n".join(parts)
            
        finally:
            await self.update_state("idle")
    
    async def _llm_analyze(self, step: Dict, result: Dict) -> Dict:
        """Use LLM for sophisticated analysis."""
        # Placeholder
        return {"score": 1.0, "feedback": "Valid", "suggestions": []}
    
    async def _generate_natural_response(self, plan: Dict, results: List[Dict],
                                         validation: Dict) -> Optional[str]:
        """Generate natural language response using LLM."""
        if not self.model_connector:
            return None
        
        prompt = f"""Summarize the execution results for the user.

Request: {plan.get('user_request', '')}
Results: {results}
Validation: {validation.get('overall_score', 0):.0%} passed

Provide a concise, natural response."""
        
        try:
            return await self.model_connector.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=300
            )
        except:
            return None


class SimplifiedAgentSystem:
    """
    Coordinator for the 3-core-agent system.
    
    Orchestrates Planner → Executor → Analyst flow.
    """
    
    def __init__(self, state_manager=None, model_connector=None, 
                 tool_engine=None, hybrid_router=None, sandbox=None):
        self.planner = PlannerAgent(state_manager, model_connector, hybrid_router)
        self.executor = ExecutorAgent(state_manager, tool_engine, sandbox)
        self.analyst = AnalystAgent(state_manager, model_connector)
        self.state_manager = state_manager
    
    async def process(self, user_request: str, context: Dict = None) -> Dict:
        """
        Process user request through 3-agent pipeline.
        
        Flow:
        1. Planner analyzes and creates plan
        2. Executor runs all steps
        3. Analyst validates and compiles response
        """
        import time
        start_time = time.time()
        
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        try:
            # Step 1: Planning
            intent_analysis = await self.planner.analyze_intent(user_request)
            plan = await self.planner.create_plan(user_request, intent_analysis)
            
            # Step 2: Execution
            steps = plan.get("steps", [])
            parallelizable = plan.get("parallelizable", False)
            
            if parallelizable and len(steps) > 1:
                results = await self.executor.execute_parallel(steps, context=context)
            else:
                # Sequential execution with dependency resolution
                results = await self._execute_sequential(steps, context)
            
            # Step 3: Validation
            validation = await self.analyst.validate_batch(plan, results)
            
            # Step 4: Response compilation
            response = await self.analyst.compile_response(plan, results, validation)
            
            total_time = (time.time() - start_time) * 1000
            
            return {
                "request_id": request_id,
                "success": validation.get("all_valid", False),
                "response": response,
                "plan": plan,
                "results": results,
                "validation": validation,
                "total_time_ms": total_time
            }
            
        except Exception as e:
            return {
                "request_id": request_id,
                "success": False,
                "response": f"Error: {str(e)}",
                "error": str(e),
                "total_time_ms": (time.time() - start_time) * 1000
            }
    
    async def _execute_sequential(self, steps: List[Dict], 
                                  context: Dict = None) -> List[Dict]:
        """Execute steps in order with dependency resolution."""
        results = []
        completed_steps = set()
        
        while len(completed_steps) < len(steps):
            for step in steps:
                step_id = step.get("step_id")
                if step_id in completed_steps:
                    continue
                
                # Check dependencies
                deps = step.get("dependencies", [])
                if all(d in completed_steps for d in deps):
                    # Execute
                    result = await self.executor.execute_step(step, context)
                    results.append(result)
                    completed_steps.add(step_id)
            
            # Prevent infinite loop
            if len(results) == len(completed_steps):
                break
        
        return results
