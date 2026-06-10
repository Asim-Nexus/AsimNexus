
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Multi-Agent Orchestrator - OPTIMIZED
===============================================
Optimized for parallel processing using Essential Clones only
Replaces sequential loops with async parallel execution
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("ASIM_Orchestrator")

# Import tool safety and other core systems
from core.tool_safety import get_tool_safety_validator, PermissionLevel
from core.execution_timeout import get_execution_timeout
from core.state_manager import get_state_manager
from core.execution_tracer import get_execution_tracer, ComponentType


class CloneRole(Enum):
    """Essential Clones Only - 6 Core Roles"""
    CEO = "ceo"                    # Chief Executive Officer
    CTO = "cto"                    # Chief Technology Officer
    CFO = "cfo"                    # Chief Financial Officer
    CMO = "cmo"                    # Chief Marketing Officer
    COO = "coo"                    # Chief Operations Officer
    CHRO = "chro"                  # Chief Human Resources Officer


@dataclass
class CloneConfig:
    """Configuration for each clone"""
    role: CloneRole
    name: str
    personality: str
    expertise: List[str]
    model_preference: str
    system_prompt: str
    is_active: bool = True
    last_active: Optional[str] = None


@dataclass
class Task:
    """Task for clones to execute"""
    task_id: str
    task_type: str
    description: str
    assigned_clone: CloneRole
    priority: str  # 'low', 'medium', 'high', 'critical'
    status: str = 'pending'  # 'pending', 'in_progress', 'completed', 'failed'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    result: Any = None
    context: Dict = field(default_factory=dict)


class MultiAgentOrchestrator:
    """
    Orchestrates 6 Essential Clones with safety enforcement
    Routes tasks, manages conversations, coordinates responses
    All tool executions go through safety validation
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ASIM_Orchestrator")
        
        # Initialize 6 Essential Clones
        self.clones: Dict[CloneRole, CloneConfig] = self._initialize_clones()
        
        # Task queue
        self.tasks: List[Task] = []
        
        # Conversation memory per user
        self.conversations: Dict[str, List[Dict]] = {}
        
        # Smart Router for model selection
        self.model_router = None
        
        # Unified LLM Gateway
        self.llm_gateway = None
        
        # Core systems for safety and state management
        self.tool_safety = get_tool_safety_validator()
        self.execution_timeout = get_execution_timeout()
        self.state_manager = get_state_manager()
        self.execution_tracer = get_execution_tracer()
        
        # Clone permission levels
        self.clone_permissions = {
            CloneRole.CEO: PermissionLevel.SYSTEM,      # Full access
            CloneRole.CTO: PermissionLevel.ADMIN,       # Technical admin
            CloneRole.CFO: PermissionLevel.ADMIN,       # Financial admin
            CloneRole.CMO: PermissionLevel.USER,         # Marketing user
            CloneRole.COO: PermissionLevel.ADMIN,       # Operations admin
            CloneRole.CHRO: PermissionLevel.USER         # HR user
        }
        
        self._initialized = False
        
    async def initialize(self):
        """Initialize orchestrator and its components"""
        if self._initialized:
            return
            
        # Initialize Smart Router
        try:
            from connectors.smart_model_router import SmartModelRouter
            self.model_router = SmartModelRouter()
        except Exception as e:
            self.logger.warning(f"SmartModelRouter initialization failed: {e}")
        
        # Initialize LLM Gateway
        try:
            from connectors.unified_llm_gateway import UnifiedLLMGateway
            self.llm_gateway = UnifiedLLMGateway()
            await self.llm_gateway.initialize()
        except Exception as e:
            self.logger.warning(f"UnifiedLLMGateway initialization failed: {e}")
        
        self._initialized = True
        self.logger.info("✅ Multi-Agent Orchestrator initialized with 6 Essential Clones")
    
    def _initialize_clones(self) -> Dict[CloneRole, CloneConfig]:
        """Initialize Essential Clones Only - 6 Core Roles"""
        clones = {
            CloneRole.CEO: CloneConfig(
                role=CloneRole.CEO,
                name="ASIM-CEO",
                personality="Visionary, decisive, strategic",
                expertise=["leadership", "strategy", "business", "innovation", "decision_making"],
                model_preference="reasoning",
                system_prompt="You are ASIM-CEO, the Chief Executive Officer. You provide strategic leadership and make high-level decisions. Always think about the big picture and long-term vision."
            ),
            
            CloneRole.CTO: CloneConfig(
                role=CloneRole.CTO,
                name="ASIM-CTO",
                personality="Technical, precise, innovative",
                expertise=["technology", "architecture", "development", "innovation", "systems"],
                model_preference="coding",
                system_prompt="You are ASIM-CTO, the Chief Technology Officer. You handle all technical matters, architecture, and development. Always provide precise and innovative solutions."
            ),
            
            CloneRole.CFO: CloneConfig(
                role=CloneRole.CFO,
                name="ASIM-CFO",
                personality="Analytical, strategic, detail-oriented",
                expertise=["finance", "strategy", "risk_management", "investment", "budgeting"],
                model_preference="reasoning",
                system_prompt="You are ASIM-CFO, the Chief Financial Officer. You handle all financial matters, budgeting, and investments. Always be analytical and risk-aware."
            ),
            
            CloneRole.CMO: CloneConfig(
                role=CloneRole.CMO,
                name="ASIM-CMO",
                personality="Creative, strategic, customer-focused",
                expertise=["marketing", "branding", "customer_experience", "growth", "promotion"],
                model_preference="chat",
                system_prompt="You are ASIM-CMO, the Chief Marketing Officer. You handle marketing, branding, and customer experience. Always be creative and customer-focused."
            ),
            
            CloneRole.COO: CloneConfig(
                role=CloneRole.COO,
                name="ASIM-COO",
                personality="Efficient, systematic, process-oriented",
                expertise=["operations", "process_optimization", "efficiency", "workflow", "management"],
                model_preference="chat",
                system_prompt="You are ASIM-COO, the Chief Operations Officer. You handle operations, processes, and efficiency. Always optimize for performance and scalability."
            ),
            
            CloneRole.CHRO: CloneConfig(
                role=CloneRole.CHRO,
                name="ASIM-CHRO",
                personality="People-focused, empathetic, strategic",
                expertise=["hr", "people", "talent", "team", "culture"],
                model_preference="chat",
                system_prompt="You are ASIM-CHRO, the Chief Human Resources Officer. You handle people, talent, and culture. Always be empathetic and strategic."
            )
        }
        
        return clones
    
    def detect_intent(self, message: str) -> Dict[str, Any]:
        """
        Detect user intent and determine which clones should respond
        """
        message_lower = message.lower()
        
        # Intent detection patterns
        intents = {
            'technical': ['code', 'program', 'error', 'bug', 'system', 'architecture', 'api', 'database'],
            'financial': ['budget', 'cost', 'money', 'invest', 'finance', 'revenue', 'profit', 'price'],
            'marketing': ['market', 'brand', 'social', 'content', 'ad', 'campaign', 'promote'],
            'legal': ['legal', 'contract', 'law', 'compliance', 'regulation', 'terms'],
            'security': ['security', 'hack', 'protect', 'privacy', 'encrypt', 'threat'],
            'creative': ['design', 'logo', 'creative', 'art', 'image', 'style', 'look'],
            'health': ['health', 'medical', 'doctor', 'medicine', 'wellness', 'fitness'],
            'education': ['teach', 'learn', 'course', 'education', 'training', 'tutorial'],
            'strategy': ['strategy', 'plan', 'vision', 'future', 'direction', 'goal']
        }
        
        detected_intents = []
        for intent, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # Map intents to clones (6 essential roles only)
        clone_mapping = {
            'technical': [CloneRole.CTO],  # Fixed: removed undefined CSEO
            'financial': [CloneRole.CFO],
            'marketing': [CloneRole.CMO],  # Fixed: removed undefined CCO
            'legal': [CloneRole.CEO],  # Fixed: mapped CLO → CEO (strategy/oversight)
            'security': [CloneRole.CTO],  # Fixed: mapped CSO → CTO (technical security)
            'creative': [CloneRole.CMO],  # Fixed: removed undefined CCO, map to CMO
            'health': [CloneRole.CHRO],  # Fixed: mapped CHMO → CHRO (people/wellness)
            'education': [CloneRole.CHRO],  # Fixed: mapped CEdO → CHRO (training/talent)
            'strategy': [CloneRole.CEO],  # Fixed: removed undefined CINO, keep CEO
            'general': [CloneRole.CEO, CloneRole.CTO]
        }
        
        # Determine primary clones to involve
        if detected_intents:
            primary_clones = []
            for intent in detected_intents:
                primary_clones.extend(clone_mapping.get(intent, []))
            
            # Remove duplicates while preserving order
            seen = set()
            primary_clones = [c for c in primary_clones if not (c in seen or seen.add(c))]
        else:
            primary_clones = [CloneRole.CEO, CloneRole.CTO]  # Default
        
        return {
            'intents': detected_intents,
            'primary_clones': primary_clones,
            'confidence': len(detected_intents) / len(intents) if intents else 0
        }
    
    async def process_user_message(
        self,
        user_id: str,
        message: str,
        platform: str = 'web',
        message_type: str = 'text',
        processing_mode: str = 'auto',
        context: Dict = None
    ) -> str:
        """
        Main entry point: Process any user message through the AI system
        """
        if not self._initialized:
            await self.initialize()
        
        self.logger.info(f"🧠 Processing message from {user_id} on {platform}")
        
        # Step 1: Detect intent
        intent_analysis = self.detect_intent(message)
        primary_clones = intent_analysis['primary_clones']
        
        self.logger.info(f"   Detected intents: {intent_analysis['intents']}")
        self.logger.info(f"   Primary clones: {[c.value for c in primary_clones]}")
        
        # Step 2: Build conversation context
        conversation_context = self._build_context(user_id, message, context)
        
        # Step 3: Get responses from primary clones
        clone_responses = await self._get_clone_responses(
            primary_clones,
            message,
            conversation_context,
            processing_mode
        )
        
        # Step 4: Synthesize final response
        final_response = await self._synthesize_response(
            clone_responses,
            message,
            intent_analysis
        )
        
        # Step 5: Store conversation
        self._store_conversation(user_id, message, final_response)
    
def detect_intent(self, message: str) -> Dict[str, Any]:
    """
    Detect user intent and determine which clones should respond
    """
    message_lower = message.lower()
        
    # Intent detection patterns
    intents = {
        'technical': ['code', 'program', 'error', 'bug', 'system', 'architecture', 'api', 'database'],
        'financial': ['budget', 'cost', 'money', 'invest', 'finance', 'revenue', 'profit', 'price'],
        'marketing': ['market', 'brand', 'social', 'content', 'ad', 'campaign', 'promote'],
        'legal': ['legal', 'contract', 'law', 'compliance', 'regulation', 'terms'],
        'security': ['security', 'hack', 'protect', 'privacy', 'encrypt', 'threat'],
        'creative': ['design', 'logo', 'creative', 'art', 'image', 'style', 'look'],
        'health': ['health', 'medical', 'doctor', 'medicine', 'wellness', 'fitness'],
        'education': ['teach', 'learn', 'course', 'education', 'training', 'tutorial'],
        'strategy': ['strategy', 'plan', 'vision', 'future', 'direction', 'goal']
    }
        
    detected_intents = []
    for intent, keywords in intents.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_intents.append(intent)
        
    # Map intents to clones
    clone_mapping = {
        'technical': [CloneRole.CTO, CloneRole.CSEO],
        'financial': [CloneRole.CFO],
        'marketing': [CloneRole.CMO, CloneRole.CCO],
        'legal': [CloneRole.CLO],
        'security': [CloneRole.CSO],
        'creative': [CloneRole.CCO, CloneRole.CMO],
        'health': [CloneRole.CHMO],
        'education': [CloneRole.CEdO],
        'strategy': [CloneRole.CEO, CloneRole.CINO],
        'general': [CloneRole.CEO, CloneRole.CTO]
    }
        
    # Determine primary clones to involve
    if detected_intents:
        primary_clones = []
        for intent in detected_intents:
            primary_clones.extend(clone_mapping.get(intent, []))
            
        # Remove duplicates while preserving order
        seen = set()
        primary_clones = [c for c in primary_clones if not (c in seen or seen.add(c))]
    else:
        primary_clones = [CloneRole.CEO, CloneRole.CTO]  # Default
        
    return {
        'intents': detected_intents,
        'primary_clones': primary_clones,
        'confidence': len(detected_intents) / len(intents) if intents else 0
    }
    
async def process_user_message(
    self,
    user_id: str,
    message: str,
    platform: str = 'web',
    message_type: str = 'text',
    processing_mode: str = 'auto',
    context: Dict = None
) -> str:
    """
    Main entry point: Process any user message through the AI system
    """
    if not self._initialized:
        await self.initialize()
        
    self.logger.info(f"🧠 Processing message from {user_id} on {platform}")
        
    # Step 1: Detect intent
    intent_analysis = self.detect_intent(message)
    primary_clones = intent_analysis['primary_clones']
        
    self.logger.info(f"   Detected intents: {intent_analysis['intents']}")
    self.logger.info(f"   Primary clones: {[c.value for c in primary_clones]}")
        
    # Step 2: Build conversation context
    conversation_context = self._build_context(user_id, message, context)
        
    # Step 3: Get responses from primary clones
    clone_responses = await self._get_clone_responses(
        primary_clones,
        message,
        conversation_context,
        processing_mode
    )
        
    # Step 4: Synthesize final response
    final_response = await self._synthesize_response(
        clone_responses,
        message,
        intent_analysis
    )
        
    # Step 5: Store conversation
    self._store_conversation(user_id, message, final_response)
        
    return final_response
    
def _build_context(self, user_id: str, current_message: str, extra_context: Dict = None) -> Dict:
    """Build conversation context including history"""
    history = self.conversations.get(user_id, [])[-5:]  # Last 5 messages
        
    context = {
        'user_id': user_id,
        'current_message': current_message,
        'conversation_history': history,
        'timestamp': datetime.now().isoformat(),
        'extra_context': extra_context or {}
    }
        
    return context
    
async def _get_clone_responses(
    self,
    clones: List[CloneRole],
    message: str,
    context: Dict,
    processing_mode: str = 'auto'
) -> Dict[CloneRole, str]:
    """Get responses from selected clones"""
    responses = {}
        
    # Create tasks for all clones
    tasks = []
    for clone_role in clones:
        task = self._get_single_clone_response(clone_role, message, context, processing_mode)
        tasks.append(task)
        
    # Execute all in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
        
    for clone_role, result in zip(clones, results):
        if isinstance(result, Exception):
            self.logger.error(f"   ❌ {clone_role.value} failed: {result}")
            responses[clone_role] = f"[{clone_role.value} unavailable]"
        else:
            responses[clone_role] = result
    
    async def _get_single_clone_response(
        self,
        clone_role: CloneRole,
        message: str,
        context: Dict,
        processing_mode: str = 'auto'
    ) -> str:
        """Get response from a single clone with safety enforcement"""
        clone = self.clones[clone_role]
        clone_id = f"{clone_role.value}_clone"
        
        # Get clone permission level
        clone_permission = self.clone_permissions[clone_role]
        
        # Create session for this clone
        session_id = await self.state_manager.create_session(
            user_id=context.get('user_id', 'system'),
            agent_id=clone_id,
            metadata={"clone_role": clone_role.value, "message": message[:100]}
        )
        
        # Update clone state to ACTIVE
        try:
            await self.state_manager.update_state(
                namespace="agent",
                key=f"{clone_id}_state",
                data={"state": "active", "processing_mode": processing_mode}
            )
        except Exception as e:
            logger.warning(f"State update failed: {e}")
        
        # Trace execution start
        self.execution_tracer.trace_event(
            component=ComponentType.AGENT,
            component_id=clone_id,
            action="response_start",
            message=f"Starting response generation for {clone.name}",
            data={"permission": clone_permission.value, "message_length": len(message)}
        )
        
        try:
            # Use Smart Model Router to select best model based on processing_mode
            if self.model_router:
                # Override model preference based on processing_mode
                if processing_mode == 'local':
                    model_selection = {
                        'provider': 'local',
                        'model': 'gemma-2-2b-it',
                        'api_key': None
                    }
                elif processing_mode == 'cloud':
                    model_selection = {
                        'provider': 'nvidia_nim',
                        'model': 'nvidia/nemotron-3-super-120b-a12b',
                        'api_key': None
                    }
                else:  # auto mode
                    model_selection = self.model_router.select_model(
                        message,
                        clone.model_preference
                    )
            else:
                model_selection = {
                    'provider': 'local',
                    'model': 'gemma-2-2b-it',
                    'api_key': None
                }
            
            # Generate response using selected model with timeout and safety
            async def generate_response():
                # For local provider, use direct API call
                if model_selection.get('provider') == 'local':
                    import aiohttp
                    
                    # Build prompt for local LLM
                    prompt = f"{clone.system_prompt}\n\nUser: {message}\n\n{clone.name}:"
                    
                    data = {
                        "prompt": prompt,
                        "model_id": model_selection.get('model', 'gemma-2-2b-it'),
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                    
                    # Validate tool usage if any
                    if "file" in message.lower() or "execute" in message.lower():
                        validation = await self.tool_safety.validate_tool_execution(
                            tool_name="llm_call",
                            parameters={"prompt": prompt, "model": model_selection.get('model')},
                            agent_id=clone_id,
                            agent_permission=clone_permission
                        )
                        
                        if not validation.is_valid:
                            return f"🤖 {clone.name}\n⚠️ {validation.errors[0] if validation.errors else 'Operation not permitted'}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            "http://localhost:8000/api/local-llm/generate",
                            json=data
                        ) as response:
                            result = await response.json()
                            content = result.get("text", f"I'm {clone.name} and I understand you're asking about '{message[:30]}...'")
                    
                    return content
                
                # For cloud providers, use LLM Gateway
                elif self.llm_gateway:
                    from connectors.unified_llm_gateway import UnifiedCompletionRequest, LLMProvider
                    
                    # Convert provider string to enum
                    provider_map = {
                        'openai': LLMProvider.OPENAI,
                        'anthropic': LLMProvider.ANTHROPIC,
                        'gemini': LLMProvider.GEMINI,
                        'nvidia_nim': LLMProvider.NVIDIA_NIM,
                        'local': LLMProvider.LOCAL
                    }
                    
                    provider = provider_map.get(
                        model_selection.get('provider', 'local'),
                        LLMProvider.LOCAL
                    )
                    
                    # Validate LLM call
                    validation = await self.tool_safety.validate_tool_execution(
                        tool_name="llm_call",
                        parameters={"provider": provider.value, "model": model_selection.get('model')},
                        agent_id=clone_id,
                        agent_permission=clone_permission
                    )
                    
                    if not validation.is_valid:
                        return f"🤖 {clone.name}\n⚠️ {validation.errors[0] if validation.errors else 'LLM call not permitted'}"
                    
                    request = UnifiedCompletionRequest(
                        messages=[
                            {"role": "system", "content": clone.system_prompt},
                            {"role": "user", "content": message}
                        ],
                        model=model_selection.get('model'),
                        provider=provider,
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    response = await self.llm_gateway.complete(request)
                    content = response.choices[0].message.content
                    
                    return content
                
                else:
                    # Fallback response
                    return f"I'm {clone.name} and I understand you're asking about '{message[:30]}...'"
            
            # Execute with timeout and circuit breaker
            result = await self.execution_timeout.execute_with_timeout(
                func=generate_response,
                timeout=30,
                circuit_name=f"clone_{clone_role.value}",
                fallback_func=lambda: f"🤖 {clone.name}\n⚠️ Response generation temporarily unavailable"
            )
            
            if result.success:
                content = result.result
            else:
                content = f"🤖 {clone.name}\n⚠️ {result.error}"
            
            # Format response with clone identity
            formatted_response = f"🤖 {clone.name}\n{datetime.now().strftime('%I:%M:%S %p')}\n{content}"
            
            # Trace successful execution
            self.execution_tracer.trace_event(
                component=ComponentType.AGENT,
                component_id=clone_id,
                action="response_complete",
                message=f"Response generated successfully",
                data={"response_length": len(content), "timeout_occurred": result.timeout_occurred}
            )
            
            return formatted_response
                
        except Exception as e:
            # Update clone state to ERROR
            try:
                await self.state_manager.update_state(
                    namespace="agent",
                    key=f"{clone_id}_state",
                    data={"state": "error", "error": str(e)}
                )
            except Exception as state_error:
                logger.warning(f"Error state update failed: {state_error}")
            
            # Trace error
            self.execution_tracer.trace_event(
                component=ComponentType.AGENT,
                component_id=clone_id,
                action="response_error",
                message=f"Error generating response: {str(e)}",
                level="error"
            )
            
            self.logger.error(f"Error getting response from {clone_role.value}: {e}")
            return f"🤖 {clone.name}\n{datetime.now().strftime('%I:%M:%S %p')}\n[Error: Unable to process request]"
        
        finally:
            # Update clone state back to IDLE
            try:
                await self.state_manager.update_state(
                    namespace="agent",
                    key=f"{clone_id}_state",
                    data={"state": "idle"}
                )
            except Exception as e:
                logger.warning(f"Idle state update failed: {e}")
    
    async def _synthesize_response(
        self,
        clone_responses: Dict[CloneRole, str],
        original_message: str,
        intent_analysis: Dict
    ) -> str:
        """
        Synthesize responses from multiple clones into one coherent response
        """
        if len(clone_responses) == 1:
            # Single clone - return directly
            return list(clone_responses.values())[0]
        
        # Multiple clones - need to synthesize
        if self.llm_gateway:
            try:
                from connectors.unified_llm_gateway import UnifiedCompletionRequest, LLMProvider
                
                synthesis_prompt = f"""You are ASIM, the unified intelligence of ASIMNEXUS.
Your 15 Founder Clones have provided their expert perspectives.
Synthesize their responses into one coherent, helpful response.

Original user message: {original_message}

Clone responses:
"""
                
                for clone_role, response in clone_responses.items():
                    synthesis_prompt += f"\n[{clone_role.value.upper()}]: {response}\n"
                
                synthesis_prompt += """

Create a unified response that:
1. Addresses the user's needs
2. Incorporates relevant expertise from all clones
3. Is conversational and natural
4. Identifies as ASIM (not individual clones)
5. Is concise but comprehensive"""
                
                request = UnifiedCompletionRequest(
                    messages=[
                        {"role": "system", "content": "You are ASIM, the unified intelligence of ASIMNEXUS."},
                        {"role": "user", "content": synthesis_prompt}
                    ],
                    provider=LLMProvider.NVIDIA_NIM,
                    model="nvidia/llama-3.1-nemotron-70b-instruct",
                    temperature=0.7,
                    max_tokens=1500
                )
                
                response = await self.llm_gateway.complete(request)
                
                # Format synthesis response with ASIM identity
                formatted_response = f"🤖 ASIM\n{datetime.now().strftime('%I:%M:%S %p')}\n{response.content}"
                return formatted_response
                
            except Exception as e:
                self.logger.error(f"Synthesis failed: {e}")
        
        # Fallback: concatenate responses with proper formatting
        formatted_responses = []
        for role, resp in clone_responses.items():
            clone_name = self.clones[role].name
            formatted_responses.append(f"🤖 {clone_name}\n{datetime.now().strftime('%I:%M:%S %p')}\n{resp}")
        
        return "\n\n".join(formatted_responses)
    
    def _store_conversation(self, user_id: str, user_message: str, ai_response: str):
        """Store conversation in memory"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response
        })
        
        # Keep only last 50 messages
        self.conversations[user_id] = self.conversations[user_id][-50:]
    
    async def create_task(
        self,
        task_type: str,
        description: str,
        assigned_clone: CloneRole,
        priority: str = 'medium',
        context: Dict = None
    ) -> Task:
        """Create and execute a task"""
        task_id = f"task_{datetime.now().timestamp()}"
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            assigned_clone=assigned_clone,
            priority=priority,
            context=context or {}
        )
        
        self.tasks.append(task)
        
        # Execute task
        await self._execute_task(task)
        
        return task
    
    async def _execute_task(self, task: Task):
        """Execute a single task"""
        task.status = 'in_progress'
        
        try:
            clone = self.clones[task.assigned_clone]
            
            # Get model for this clone
            if self.model_router:
                model_selection = self.model_router.select_model(
                    task.description,
                    clone.model_preference
                )
            else:
                model_selection = {'provider': 'local', 'model': 'gemma-2-2b-it'}
            
            # Execute with LLM
            if self.llm_gateway:
                from connectors.unified_llm_gateway import UnifiedCompletionRequest
                
                request = UnifiedCompletionRequest(
                    messages=[
                        {"role": "system", "content": clone.system_prompt},
                        {"role": "user", "content": f"Task: {task.description}\n\nExecute this task."}
                    ],
                    provider=model_selection.get('provider', 'local'),
                    model=model_selection.get('model')
                )
                
                response = await self.llm_gateway.complete(request)
                
                task.result = response.content
                task.status = 'completed'
            else:
                task.result = "LLM Gateway not available"
                task.status = 'failed'
            
        except Exception as e:
            task.status = 'failed'
            task.result = str(e)
        
        task.completed_at = datetime.now().isoformat()
    
    def get_clone_status(self) -> Dict[str, Any]:
        """Get status of all clones"""
        return {
            'total_clones': len(self.clones),
            'active_clones': sum(1 for c in self.clones.values() if c.is_active),
            'clones': [
                {
                    'role': c.role.value,
                    'name': c.name,
                    'active': c.is_active,
                    'expertise': c.expertise,
                    'model_preference': c.model_preference
                }
                for c in self.clones.values()
            ]
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'initialized': self._initialized,
            'clones': self.get_clone_status(),
            'pending_tasks': len([t for t in self.tasks if t.status == 'pending']),
            'completed_tasks': len([t for t in self.tasks if t.status == 'completed']),
            'total_conversations': len(self.conversations),
            'model_router_available': self.model_router is not None,
            'llm_gateway_available': self.llm_gateway is not None
        }


# Singleton instance
orchestrator = MultiAgentOrchestrator()
