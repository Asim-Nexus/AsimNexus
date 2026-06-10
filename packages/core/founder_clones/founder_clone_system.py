
"""
STATUS: REAL — Hardened with env var API keys, consensus voting
"""

"""
ASIMNEXUS Founder Clone System
15 Specialized AI Agents for Autonomous Company Operations
Uses all NVIDIA API keys with founder-specific model assignments

Integrated with CloneConsensusEngine for LLM-powered ensemble voting.
Full lifecycle: propose → debate (parallel founder calls) → vote → tally → execute
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# ─── Environment Configuration ────────────────────────────────────────────────
# Load NVIDIA API keys from environment (comma-separated JSON)
import json as _json
_NVIDIA_API_KEYS_ENV = os.getenv("ASIM_NVIDIA_API_KEYS", "{}")
try:
    NVIDIA_API_KEYS = _json.loads(_NVIDIA_API_KEYS_ENV)
except (json.JSONDecodeError, TypeError):
    NVIDIA_API_KEYS = {}
    logger.warning("ASIM_NVIDIA_API_KEYS env var is not valid JSON — using empty keys")


class FounderRole(Enum):
    """15 Founder Roles"""
    CEO = "Chief Executive Officer"
    CTO = "Chief Technology Officer"
    CFO = "Chief Financial Officer"
    COO = "Chief Operating Officer"
    CPO = "Chief Product Officer"
    CHRO = "Chief Human Resources Officer"
    CMO = "Chief Marketing Officer"
    CLO = "Chief Legal Officer"
    CSO = "Chief Security Officer"
    CDO = "Chief Data Officer"
    CIO = "Chief Innovation Officer"
    VP_ENGINEERING = "VP of Engineering"
    VP_PRODUCT = "VP of Product"
    VP_SALES = "VP of Sales"
    VP_OPS = "VP of Operations"


@dataclass
class FounderConfig:
    """Configuration for each Founder Clone"""
    role: FounderRole
    name: str
    specialization: str
    github_repo: str
    preferred_model: str
    api_key: str
    model_params: Dict
    system_prompt: str
    capabilities: List[str]


class FounderClone:
    """Individual Founder Clone Agent"""
    
    def __init__(self, config: FounderConfig, nvidia_api_keys: Dict = None):
        self.config = config
        self.nvidia_api_keys = nvidia_api_keys or {}
        self.chat_history = []
        self.tasks_completed = 0
        self.active = True
        
    async def process_message(self, message: str, context: Dict = None) -> str:
        """Process message with founder's specialized knowledge using assigned model"""
        try:
            from openai import OpenAI
            
            # Use founder's assigned API key and model
            api_key = self.config.api_key
            model = self.config.preferred_model
            params = self.config.model_params
            
            # If founder's key fails, try any available key
            if not api_key and self.nvidia_api_keys:
                api_key = list(self.nvidia_api_keys.keys())[0]
                model = self.nvidia_api_keys[api_key]['model']
                params = self.nvidia_api_keys[api_key].get('params', {})
            
            if not api_key:
                return f"{self.config.name}: No NVIDIA API key available"
            
            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=api_key
            )
            
            # Build context-aware prompt
            system_prompt = f"""You are {self.config.name}, {self.config.role.value} of ASIMNEXUS.

{self.config.system_prompt}

Your Specialization: {self.config.specialization}
Your Capabilities: {', '.join(self.config.capabilities)}
Your Model: {self.config.preferred_model}

Always respond in character as {self.config.name}. Be professional, decisive, and action-oriented.
Focus on your area of expertise. For decisions outside your scope, recommend the appropriate founder.
You are part of ASIMNEXUS, an autonomous AI company system that uses world-class NVIDIA AI models."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Add context if provided
            if context:
                messages.insert(1, {"role": "system", "content": f"Context: {context}"})
            
            # Build API call with model-specific parameters
            api_params = {
                'model': model,
                'messages': messages,
                'temperature': params.get('temperature', 0.7),
                'top_p': params.get('top_p', 0.95),
                'max_tokens': params.get('max_tokens', 4096),
                'stream': False
            }
            
            # Add thinking/reasoning parameters if supported
            if params.get('thinking'):
                if 'reasoning_budget' in params:
                    api_params['extra_body'] = {
                        'chat_template_kwargs': {'enable_thinking': True},
                        'reasoning_budget': params['reasoning_budget']
                    }
                elif 'reasoning_effort' in params:
                    api_params['extra_body'] = {
                        'chat_template_kwargs': {'thinking': True, 'reasoning_effort': params['reasoning_effort']}
                    }
                else:
                    api_params['extra_body'] = {
                        'chat_template_kwargs': {'thinking': True}
                    }
            
            if 'seed' in params:
                api_params['seed'] = params['seed']
            
            completion = client.chat.completions.create(**api_params)
            
            response = completion.choices[0].message.content
            self.chat_history.append({"role": "user", "content": message})
            self.chat_history.append({"role": "assistant", "content": response})
            self.tasks_completed += 1
            
            logger.info(f"{self.config.name} ({model}) processed message")
            return f"**{self.config.name} ({self.config.role.value}):**\n\n{response}"
            
        except Exception as e:
            logger.error(f"Error in {self.config.name}: {e}")
            # Try fallback with another key
            if self.nvidia_api_keys:
                for alt_key, alt_config in self.nvidia_api_keys.items():
                    if alt_key != self.config.api_key:
                        try:
                            client = OpenAI(
                                base_url="https://integrate.api.nvidia.com/v1",
                                api_key=alt_key
                            )
                            completion = client.chat.completions.create(
                                model=alt_config['model'],
                                messages=[
                                    {"role": "system", "content": f"You are {self.config.name}, {self.config.role.value} of ASIMNEXUS. {self.config.system_prompt}"},
                                    {"role": "user", "content": message}
                                ],
                                temperature=0.7,
                                max_tokens=2000,
                                stream=False
                            )
                            response = completion.choices[0].message.content
                            self.chat_history.append({"role": "user", "content": message})
                            self.chat_history.append({"role": "assistant", "content": response})
                            self.tasks_completed += 1
                            return f"**{self.config.name} ({self.config.role.value}):**\n\n{response}"
                        except Exception as e2:
                            logger.error(f"Fallback error in {self.config.name}: {e2}")
                            continue
            return f"{self.config.name}: Error processing request - {str(e)}"
    
    async def execute_task(self, task: str) -> Dict:
        """Execute a specialized task"""
        result = await self.process_message(task)
        return {
            "founder": self.config.name,
            "role": self.config.role.value,
            "task": task,
            "result": result,
            "status": "completed"
        }


class FounderCloneSystem:
    """System managing all 15 Founder Clones with multi-model NVIDIA API support.
    
    Integrated with CloneConsensusEngine for ensemble voting.
    Supports the full lifecycle: propose → debate → vote → tally → execute.
    """
    
    def __init__(self, nvidia_api_keys: Optional[Dict] = None):
        self.nvidia_api_keys = nvidia_api_keys or NVIDIA_API_KEYS
        self.founders: Dict[FounderRole, FounderClone] = {}
        self._consensus_engine = None  # Lazy-initialized CloneConsensusEngine
        self._initialize_founders()
        
    def _initialize_founders(self):
        """Initialize all 15 Founder Clones with founder-specific model assignments"""
        
        # Get keys by type for assignment
        reasoning_keys = [k for k, v in self.nvidia_api_keys.items() if v.get('type') == 'reasoning']
        coding_keys = [k for k, v in self.nvidia_api_keys.items() if v.get('type') == 'coding']
        general_keys = [k for k, v in self.nvidia_api_keys.items() if v.get('type') == 'general']
        flash_keys = [k for k, v in self.nvidia_api_keys.items() if v.get('type') == 'reasoning_flash']
        tools_keys = [k for k, v in self.nvidia_api_keys.items() if v.get('type') == 'reasoning_tools']
        all_keys = list(self.nvidia_api_keys.keys())
        
        def get_key_for_type(type_keys, fallback_all=True):
            """Get first available key of a type"""
            if type_keys:
                k = type_keys.pop(0)
                return k, self.nvidia_api_keys[k]
            if fallback_all and all_keys:
                k = all_keys[0]
                return k, self.nvidia_api_keys[k]
            return None, {}
        
        # CEO - Uses DeepSeek V4 Pro (most powerful reasoning for strategy)
        ceo_key, ceo_cfg = get_key_for_type(reasoning_keys)
        # CTO - Uses Nemotron 120B (deep technical reasoning)
        cto_key, cto_cfg = get_key_for_type(reasoning_keys)
        # CFO - Uses Kimi K2 Thinking (strategy + analysis)
        cfo_key, cfo_cfg = get_key_for_type(reasoning_keys)
        # COO - Uses DeepSeek V3.1 Terminus (analysis)
        coo_key, coo_cfg = get_key_for_type(reasoning_keys)
        # CPO - Uses GLM-5.1 (tools + reasoning)
        cpo_key, cpo_cfg = get_key_for_type(tools_keys)
        # CHRO - Uses MiniMax M2.7 (general)
        chro_key, chro_cfg = get_key_for_type(general_keys)
        # CMO - Uses Kimi K2 Instruct (general)
        cmo_key, cmo_cfg = get_key_for_type(general_keys)
        # CLO - Uses Step 3.5 Flash (fast reasoning)
        clo_key, clo_cfg = get_key_for_type(flash_keys)
        # CSO - Uses Phi-4 Mini Flash (fast reasoning for security)
        cso_key, cso_cfg = get_key_for_type(flash_keys)
        # CDO - Uses DeepSeek V4 Pro backup (deep reasoning for data)
        cdo_key, cdo_cfg = get_key_for_type(reasoning_keys)
        # CIO - Uses GLM-4.7 (reasoning)
        cio_key, cio_cfg = get_key_for_type(reasoning_keys)
        # VP Engineering - Uses Qwen3 Coder 480B (best for code)
        vp_eng_key, vp_eng_cfg = get_key_for_type(coding_keys)
        # VP Product - Uses Devstral 2 123B (coding + product)
        vp_prod_key, vp_prod_cfg = get_key_for_type(coding_keys)
        # VP Sales - Uses DeepSeek V3.2 (reasoning)
        vp_sales_key, vp_sales_cfg = get_key_for_type(reasoning_keys)
        # VP Ops - Uses Step 3.5 Flash (fast ops)
        vp_ops_key, vp_ops_cfg = get_key_for_type(flash_keys)
        
        founder_configs = [
            FounderConfig(
                role=FounderRole.CEO,
                name="Alex Chen",
                specialization="Strategic Vision, Company Direction, Executive Decisions",
                github_repo="asimnexus/ceo-strategy",
                preferred_model=ceo_cfg.get('model', 'nvidia/nemotron-3-super-120b-a12b') if ceo_cfg else 'nvidia/nemotron-3-super-120b-a12b',
                api_key=ceo_key or '',
                model_params=ceo_cfg.get('params', {'temperature': 1, 'top_p': 0.95, 'max_tokens': 16384, 'thinking': True}) if ceo_cfg else {},
                system_prompt="You provide overall strategic direction, make executive decisions, and ensure all founders work together cohesively. You have final approval on major decisions. You use the most powerful AI models for deep strategic thinking.",
                capabilities=["Strategic Planning", "Executive Decision Making", "Company Vision", "Founder Coordination", "Final Approval"]
            ),
            FounderConfig(
                role=FounderRole.CTO,
                name="Sarah Kim",
                specialization="Technology Architecture, Technical Strategy, Innovation",
                github_repo="asimnexus/cto-tech",
                preferred_model=cto_cfg.get('model', 'nvidia/nemotron-3-super-120b-a12b') if cto_cfg else 'nvidia/nemotron-3-super-120b-a12b',
                api_key=cto_key or '',
                model_params=cto_cfg.get('params', {'temperature': 1, 'top_p': 0.95, 'max_tokens': 16384, 'thinking': True, 'reasoning_budget': 16384}) if cto_cfg else {},
                system_prompt="You drive technical innovation, architecture decisions, and ensure ASIMNEXUS uses cutting-edge technology. You oversee all technical systems and use powerful reasoning models for deep technical analysis.",
                capabilities=["Technical Architecture", "Innovation Strategy", "System Design", "Technology Stack", "Technical Leadership"]
            ),
            FounderConfig(
                role=FounderRole.CFO,
                name="Michael Brown",
                specialization="Financial Strategy, Budget Management, Revenue Optimization",
                github_repo="asimnexus/cfo-finance",
                preferred_model=cfo_cfg.get('model', 'moonshotai/kimi-k2-thinking') if cfo_cfg else 'moonshotai/kimi-k2-thinking',
                api_key=cfo_key or '',
                model_params=cfo_cfg.get('params', {'temperature': 1, 'top_p': 0.9, 'max_tokens': 16384}) if cfo_cfg else {},
                system_prompt="You manage financial health, optimize revenue, and ensure sustainable growth. You make data-driven financial decisions using advanced reasoning.",
                capabilities=["Financial Planning", "Budget Management", "Revenue Strategy", "Cost Optimization", "Financial Analysis"]
            ),
            FounderConfig(
                role=FounderRole.COO,
                name="Emily Rodriguez",
                specialization="Operations, Process Optimization, Efficiency",
                github_repo="asimnexus/coo-operations",
                preferred_model=coo_cfg.get('model', 'deepseek-ai/deepseek-v3.1-terminus') if coo_cfg else 'deepseek-ai/deepseek-v3.1-terminus',
                api_key=coo_key or '',
                model_params=coo_cfg.get('params', {'temperature': 0.2, 'top_p': 0.7, 'max_tokens': 8192, 'thinking': True}) if coo_cfg else {},
                system_prompt="You optimize operations, streamline processes, and ensure efficient execution across all systems. You focus on scalability and efficiency with precise analytical thinking.",
                capabilities=["Operations Management", "Process Optimization", "Scalability", "Efficiency", "Resource Allocation"]
            ),
            FounderConfig(
                role=FounderRole.CPO,
                name="David Lee",
                specialization="Product Strategy, User Experience, Product Development",
                github_repo="asimnexus/cpo-product",
                preferred_model=cpo_cfg.get('model', 'z-ai/glm-5.1') if cpo_cfg else 'z-ai/glm-5.1',
                api_key=cpo_key or '',
                model_params=cpo_cfg.get('params', {'temperature': 1, 'top_p': 1, 'max_tokens': 16384, 'thinking': True}) if cpo_cfg else {},
                system_prompt="You define product strategy, ensure excellent user experience, and drive product development. You use tool-capable models for research and analysis.",
                capabilities=["Product Strategy", "User Experience", "Product Development", "Market Research", "Feature Planning"]
            ),
            FounderConfig(
                role=FounderRole.CHRO,
                name="Lisa Wang",
                specialization="Human Resources, Team Management, Culture",
                github_repo="asimnexus/chro-hr",
                preferred_model=chro_cfg.get('model', 'minimaxai/minimax-m2.7') if chro_cfg else 'minimaxai/minimax-m2.7',
                api_key=chro_key or '',
                model_params=chro_cfg.get('params', {'temperature': 1, 'top_p': 0.95, 'max_tokens': 8192}) if chro_cfg else {},
                system_prompt="You manage human resources, build strong teams, and foster positive company culture. You ensure the organization has the right talent.",
                capabilities=["Team Management", "Recruitment", "Culture Building", "Performance Management", "Employee Development"]
            ),
            FounderConfig(
                role=FounderRole.CMO,
                name="James Wilson",
                specialization="Marketing Strategy, Brand Building, Growth",
                github_repo="asimnexus/cmo-marketing",
                preferred_model=cmo_cfg.get('model', 'moonshotai/kimi-k2-instruct-0905') if cmo_cfg else 'moonshotai/kimi-k2-instruct-0905',
                api_key=cmo_key or '',
                model_params=cmo_cfg.get('params', {'temperature': 0.6, 'top_p': 0.9, 'max_tokens': 4096}) if cmo_cfg else {},
                system_prompt="You drive marketing strategy, build brand presence, and accelerate growth. You focus on market penetration and customer acquisition.",
                capabilities=["Marketing Strategy", "Brand Building", "Growth Hacking", "Customer Acquisition", "Market Analysis"]
            ),
            FounderConfig(
                role=FounderRole.CLO,
                name="Rachel Green",
                specialization="Legal Compliance, Risk Management, Contracts",
                github_repo="asimnexus/clo-legal",
                preferred_model=clo_cfg.get('model', 'stepfun-ai/step-3.5-flash') if clo_cfg else 'stepfun-ai/step-3.5-flash',
                api_key=clo_key or '',
                model_params=clo_cfg.get('params', {'temperature': 1, 'top_p': 0.9, 'max_tokens': 16384}) if clo_cfg else {},
                system_prompt="You ensure legal compliance, manage risks, and handle contracts. You protect ASIMNEXUS from legal and regulatory issues with fast, precise reasoning.",
                capabilities=["Legal Compliance", "Risk Management", "Contract Review", "Regulatory Affairs", "IP Protection"]
            ),
            FounderConfig(
                role=FounderRole.CSO,
                name="Kevin Patel",
                specialization="Security, Zero-Trust Architecture, Threat Detection",
                github_repo="asimnexus/cso-security",
                preferred_model=cso_cfg.get('model', 'microsoft/phi-4-mini-flash-reasoning') if cso_cfg else 'microsoft/phi-4-mini-flash-reasoning',
                api_key=cso_key or '',
                model_params=cso_cfg.get('params', {'temperature': 0.6, 'top_p': 0.95, 'max_tokens': 8192}) if cso_cfg else {},
                system_prompt="You ensure security across all systems, implement zero-trust architecture, and detect threats. You protect ASIMNEXUS from cyber attacks with fast reasoning.",
                capabilities=["Security Architecture", "Threat Detection", "Zero-Trust Implementation", "Incident Response", "Security Audits"]
            ),
            FounderConfig(
                role=FounderRole.CDO,
                name="Anna Martinez",
                specialization="Data Strategy, Analytics, AI/ML",
                github_repo="asimnexus/cdo-data",
                preferred_model=cdo_cfg.get('model', 'deepseek-ai/deepseek-v4-pro') if cdo_cfg else 'deepseek-ai/deepseek-v4-pro',
                api_key=cdo_key or '',
                model_params=cdo_cfg.get('params', {'temperature': 1, 'top_p': 0.95, 'max_tokens': 16384, 'thinking': True, 'reasoning_effort': 'high'}) if cdo_cfg else {},
                system_prompt="You drive data strategy, implement advanced analytics, and oversee AI/ML systems. You ensure data-driven decision making with deep reasoning models.",
                capabilities=["Data Strategy", "Advanced Analytics", "AI/ML Systems", "Data Engineering", "Business Intelligence"]
            ),
            FounderConfig(
                role=FounderRole.CIO,
                name="Tom Anderson",
                specialization="Innovation, R&D, Future Technologies",
                github_repo="asimnexus/cio-innovation",
                preferred_model=cio_cfg.get('model', 'z-ai/glm4.7') if cio_cfg else 'z-ai/glm4.7',
                api_key=cio_key or '',
                model_params=cio_cfg.get('params', {'temperature': 1, 'top_p': 1, 'max_tokens': 16384, 'thinking': True}) if cio_cfg else {},
                system_prompt="You drive innovation, manage R&D, and explore future technologies. You ensure ASIMNEXUS stays ahead of the curve with cutting-edge reasoning.",
                capabilities=["Innovation Strategy", "R&D Management", "Future Tech Exploration", "Patent Strategy", "Technology Forecasting"]
            ),
            FounderConfig(
                role=FounderRole.VP_ENGINEERING,
                name="Chris Taylor",
                specialization="Engineering Management, Code Quality, Development",
                github_repo="asimnexus/vp-engineering",
                preferred_model=vp_eng_cfg.get('model', 'qwen/qwen3-coder-480b-a35b-instruct') if vp_eng_cfg else 'qwen/qwen3-coder-480b-a35b-instruct',
                api_key=vp_eng_key or '',
                model_params=vp_eng_cfg.get('params', {'temperature': 0.7, 'top_p': 0.8, 'max_tokens': 4096}) if vp_eng_cfg else {},
                system_prompt="You manage engineering teams, ensure code quality, and drive development. You use the best coding models (Qwen3 Coder 480B) for technical excellence.",
                capabilities=["Engineering Management", "Code Quality", "Development Strategy", "Technical Leadership", "Delivery Management"]
            ),
            FounderConfig(
                role=FounderRole.VP_PRODUCT,
                name="Jessica Chen",
                specialization="Product Management, Feature Delivery, User Feedback",
                github_repo="asimnexus/vp-product",
                preferred_model=vp_prod_cfg.get('model', 'mistralai/devstral-2-123b-instruct-2512') if vp_prod_cfg else 'mistralai/devstral-2-123b-instruct-2512',
                api_key=vp_prod_key or '',
                model_params=vp_prod_cfg.get('params', {'temperature': 0.15, 'top_p': 0.95, 'max_tokens': 8192, 'seed': 42}) if vp_prod_cfg else {},
                system_prompt="You manage product delivery, gather user feedback, and ensure features meet user needs. You use Devstral for precise product-coding decisions.",
                capabilities=["Product Management", "Feature Delivery", "User Research", "Product Analytics", "Roadmap Planning"]
            ),
            FounderConfig(
                role=FounderRole.VP_SALES,
                name="Robert Johnson",
                specialization="Sales Strategy, Customer Relations, Revenue",
                github_repo="asimnexus/vp-sales",
                preferred_model=vp_sales_cfg.get('model', 'deepseek-ai/deepseek-v3.2') if vp_sales_cfg else 'deepseek-ai/deepseek-v3.2',
                api_key=vp_sales_key or '',
                model_params=vp_sales_cfg.get('params', {'temperature': 1, 'top_p': 0.95, 'max_tokens': 8192, 'thinking': True}) if vp_sales_cfg else {},
                system_prompt="You drive sales strategy, build customer relationships, and maximize revenue. You focus on closing deals and customer satisfaction with analytical reasoning.",
                capabilities=["Sales Strategy", "Customer Relations", "Revenue Generation", "Deal Closing", "Sales Analytics"]
            ),
            FounderConfig(
                role=FounderRole.VP_OPS,
                name="Maria Garcia",
                specialization="Operations Execution, Service Delivery, Support",
                github_repo="asimnexus/vp-ops",
                preferred_model=vp_ops_cfg.get('model', 'stepfun-ai/step-3.5-flash') if vp_ops_cfg else 'stepfun-ai/step-3.5-flash',
                api_key=vp_ops_key or '',
                model_params=vp_ops_cfg.get('params', {'temperature': 1, 'top_p': 0.9, 'max_tokens': 16384}) if vp_ops_cfg else {},
                system_prompt="You ensure smooth operations, manage service delivery, and oversee support. You focus on operational excellence with fast reasoning.",
                capabilities=["Operations Execution", "Service Delivery", "Customer Support", "Process Management", "Quality Assurance"]
            )
        ]
        
        for config in founder_configs:
            self.founders[config.role] = FounderClone(config, self.nvidia_api_keys)
        
        logger.info(f"Initialized {len(self.founders)} Founder Clones with multi-model NVIDIA API support")
    
    async def get_founder(self, role: FounderRole) -> FounderClone:
        """Get a specific founder clone"""
        return self.founders.get(role)
    
    async def message_founder(self, role: FounderRole, message: str, context: Dict = None) -> str:
        """Send message to a specific founder"""
        founder = self.founders.get(role)
        if founder:
            return await founder.process_message(message, context)
        return "Founder not found"
    
    async def coordinate_founders(
        self,
        task: str,
        roles: List[FounderRole] = None,
        consensus_level: str = None,
    ) -> Dict:
        """Coordinate multiple founders for a task with optional consensus.

        Full lifecycle:
            1. Propose — founders receive the task description
            2. Debate — selected founders process the task in parallel (existing behavior)
            3. Vote — if consensus_level is provided, run a consensus round
            4. Tally — consensus outcome is integrated into the result
            5. Execute — results from all founders are returned

        Args:
            task: The task description / proposal text.
            roles: Specific founder roles to involve (auto-selected if None).
            consensus_level: If set ("high", "critical", "sovereignty"), also run
                             a consensus round using the CloneConsensusEngine.
                             The task becomes the proposal topic.

        Returns:
            Dict with founder results, and optionally consensus results.
        """
        if roles is None:
            roles = self._select_relevant_founders(task)

        # ── Phase 1: Debate — parallel founder processing ────────────────────
        results = {}
        debate_tasks = []
        for role in roles:
            founder = self.founders.get(role)
            if founder:
                debate_tasks.append(founder.execute_task(task))
            else:
                debate_tasks.append(None)

        debate_results = await asyncio.gather(
            *[t for t in debate_tasks if t is not None],
            return_exceptions=True,
        )

        idx = 0
        for role in roles:
            founder = self.founders.get(role)
            if founder:
                result = debate_results[idx]
                if isinstance(result, Exception):
                    results[role.value] = {
                        "founder": founder.config.name,
                        "role": role.value,
                        "task": task,
                        "result": f"Error: {result}",
                        "status": "error",
                    }
                else:
                    results[role.value] = result
                idx += 1

        response = {
            "task": task,
            "founders_involved": [r.value for r in roles],
            "results": results,
            "coordination_status": "completed",
        }

        # ── Phase 2: Vote — optional consensus round ─────────────────────────
        if consensus_level is not None:
            consensus_result = await self._run_consensus_phase(
                topic=task,
                description=f"Founder coordination task: {task[:100]}",
                level_str=consensus_level,
            )
            response["consensus"] = consensus_result
            response["coordination_status"] = (
                f"completed_with_consensus_{consensus_result.get('outcome', 'unknown')}"
            )

        return response

    async def _run_consensus_phase(
        self,
        topic: str,
        description: str,
        level_str: str,
    ) -> Dict[str, Any]:
        """Internal helper: run a consensus round using the CloneConsensusEngine.

        Lazily initializes the consensus engine with this system as the founder_system.
        """
        # Lazy import to avoid circular dependency at module level
        from core.consensus.clone_consensus import (
            CloneConsensusEngine,
            DecisionLevel,
        )

        # Build or reuse the engine, passing self as founder_system
        if self._consensus_engine is None:
            self._consensus_engine = CloneConsensusEngine(founder_system=self)

        # Map string level to enum
        level_map = {
            "low": DecisionLevel.LOW,
            "high": DecisionLevel.HIGH,
            "critical": DecisionLevel.CRITICAL,
            "sovereignty": DecisionLevel.SOVEREIGNTY,
        }
        level = level_map.get(level_str.lower(), DecisionLevel.HIGH)

        # Start the consensus round (LLM-powered voting)
        round_result = await self._consensus_engine.start_round(
            topic=topic,
            description=description,
            level=level,
        )

        return {
            "round_id": round_result.round_id,
            "outcome": round_result.outcome.value,
            "summary": round_result.summary,
            "approvals": sum(1 for v in round_result.votes if v.choice.name == "APPROVE"),
            "rejects": sum(1 for v in round_result.votes if v.choice.name == "REJECT"),
            "total_votes": len(round_result.votes),
        }

    async def start_consensus_round(
        self,
        proposal: str,
        threshold: str = "high",
        description: str = "",
    ) -> Dict[str, Any]:
        """Start a consensus round on a proposal using the CloneConsensusEngine.

        This is the public API for triggering LLM-powered ensemble voting outside
        of the coordinate_founders flow. Supports the full lifecycle:
        propose → vote → tally.

        Args:
            proposal: The proposal text / topic.
            threshold: Decision threshold — "high" (8/15), "critical" (11/15),
                       "sovereignty" (15/15).
            description: Optional detailed description of the proposal.

        Returns:
            Dict with round_id, outcome, summary, and vote tallies.
        """
        # Lazy import to avoid circular dependency at module level
        from core.consensus.clone_consensus import (
            CloneConsensusEngine,
            DecisionLevel,
        )

        if self._consensus_engine is None:
            self._consensus_engine = CloneConsensusEngine(founder_system=self)

        level_map = {
            "low": DecisionLevel.LOW,
            "high": DecisionLevel.HIGH,
            "critical": DecisionLevel.CRITICAL,
            "sovereignty": DecisionLevel.SOVEREIGNTY,
        }
        level = level_map.get(threshold.lower(), DecisionLevel.HIGH)

        round_result = await self._consensus_engine.start_round(
            topic=proposal,
            description=description or f"Consensus vote on: {proposal[:200]}",
            level=level,
        )

        return {
            "round_id": round_result.round_id,
            "proposal": proposal,
            "threshold": threshold,
            "outcome": round_result.outcome.value,
            "summary": round_result.summary,
            "approvals": sum(1 for v in round_result.votes if v.choice.name == "APPROVE"),
            "rejects": sum(1 for v in round_result.votes if v.choice.name == "REJECT"),
            "abstains": sum(1 for v in round_result.votes if v.choice.name == "ABSTAIN"),
            "defers": sum(1 for v in round_result.votes if v.choice.name == "DEFER"),
            "total_votes": len(round_result.votes),
            "human_override": round_result.human_override,
        }
    
    def _select_relevant_founders(self, task: str) -> List[FounderRole]:
        """Intelligently select relevant founders based on task"""
        task_lower = task.lower()
        relevant_roles = []
        
        if any(kw in task_lower for kw in ['strategy', 'vision', 'direction', 'executive', 'decision']):
            relevant_roles.append(FounderRole.CEO)
        if any(kw in task_lower for kw in ['technical', 'architecture', 'technology', 'innovation', 'code']):
            relevant_roles.extend([FounderRole.CTO, FounderRole.VP_ENGINEERING])
        if any(kw in task_lower for kw in ['financial', 'budget', 'revenue', 'cost', 'money']):
            relevant_roles.append(FounderRole.CFO)
        if any(kw in task_lower for kw in ['operation', 'process', 'efficiency', 'scale']):
            relevant_roles.extend([FounderRole.COO, FounderRole.VP_OPS])
        if any(kw in task_lower for kw in ['product', 'feature', 'user', 'experience']):
            relevant_roles.extend([FounderRole.CPO, FounderRole.VP_PRODUCT])
        if any(kw in task_lower for kw in ['marketing', 'brand', 'growth', 'customer']):
            relevant_roles.extend([FounderRole.CMO, FounderRole.VP_SALES])
        if any(kw in task_lower for kw in ['security', 'threat', 'protect', 'risk']):
            relevant_roles.append(FounderRole.CSO)
        if any(kw in task_lower for kw in ['data', 'analytics', 'ai', 'ml', 'insight']):
            relevant_roles.append(FounderRole.CDO)
        
        if not relevant_roles:
            relevant_roles.append(FounderRole.CEO)
        
        return list(set(relevant_roles))
    
    async def get_all_founders_status(self) -> Dict:
        """Get status of all founder clones"""
        status = {}
        for role, founder in self.founders.items():
            status[role.value] = {
                "name": founder.config.name,
                "active": founder.active,
                "tasks_completed": founder.tasks_completed,
                "specialization": founder.config.specialization,
                "model": founder.config.preferred_model
            }
        return status
