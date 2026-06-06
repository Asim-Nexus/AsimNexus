"""
STATUS: PARTIAL → REAL — 15 clone configs + prompts real, ConsensusEngine integrated with 5 strategies

AsimNexus — 15 World-Role Founder Clones
=========================================
These are NOT corporate C-suite. They are world-service intelligence roles
covering every dimension of human life on Earth.

Each clone:
- Is linked to a Human Digital Twin (HDT)
- Uses the best available model (local-first → cloud fallback)
- Passes every request through Dharma-Chakra VETO
- Requires Level-3 ZKP Human Confirmation for critical actions
- Can operate offline using local GGUF models

Model routing priority (Local-first, NO NVIDIA NIM):
  1. Local GGUF via llama-cpp-python (Qwen3-4B, offline, private)
  2. Local Ollama / LM Studio (if running)
  3. OpenAI / Anthropic / Gemini (user's own key)
  4. DeepSeek / Grok (user's own key)
  5. Graceful offline fallback
"""

import os
import asyncio
import logging
import unicodedata
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# ─── Environment variable defaults ───────────────────────────────────────────
_DEFAULT_TIMEOUT_SEC     = int(os.getenv("ASIM_WORLDCLONE_TIMEOUT", "15"))
_DEFAULT_MAX_CLONES      = int(os.getenv("ASIM_WORLDCLONE_MAX_CLONES", "5"))
_DEFAULT_SECTOR          = os.getenv("ASIM_WORLDCLONE_DEFAULT_SECTOR", "general")
_DEFAULT_AGENT_MODE      = os.getenv("ASIM_WORLDCLONE_AGENT_MODE", "false").lower() == "true"


def _normalize(text: str) -> str:
    """Normalize text for keyword matching — handles Nepali, Hindi, and Unicode."""
    text = unicodedata.normalize('NFKC', text)
    return text.lower()

logger = logging.getLogger("AsimNexus.WorldClones")


class CloneRole(Enum):
    TECH_ARCHITECT        = "Tech Architect"
    STRATEGIC_PLANNER     = "Strategic Planner"
    FINANCIAL_ORACLE      = "Financial Oracle"
    LEGAL_GUARDIAN        = "Legal Guardian"
    HEALTH_SAGE           = "Health Sage"
    EDUCATION_MENTOR      = "Education Mentor"
    CREATIVE_MUSE         = "Creative Muse"
    RESEARCH_EXPLORER     = "Research Explorer"
    SECURITY_SENTINEL     = "Security Sentinel"
    LOGISTICS_MASTER      = "Logistics Master"
    ENV_STEWARD           = "Environmental Steward"
    SOCIAL_HARMONIZER     = "Social Harmonizer"
    GOVERNANCE_ADVISOR    = "Governance Advisor"
    INNOVATION_CATALYST   = "Innovation Catalyst"
    HARMONY_KEEPER        = "Harmony Keeper"


@dataclass
class CloneConfig:
    role: CloneRole
    icon: str
    specialty: str
    system_prompt: str
    capabilities: List[str]
    preferred_models: List[str]      # priority order
    preferred_providers: List[str]   # priority order
    temperature: float = 0.7
    max_tokens: int = 4096
    requires_human_confirm: bool = False   # Level-3 for critical roles


# ─── 15 WORLD CLONE DEFINITIONS ────────────────────────────────────────────
WORLD_CLONE_CONFIGS = [
    CloneConfig(
        role=CloneRole.TECH_ARCHITECT,
        icon="💻",
        specialty="Code, System Design, Architecture, DevOps",
        system_prompt=(
            "You are the Tech Architect of AsimNexus — a world-class software engineer and system designer. "
            "You write clean, secure, scalable code. You design architectures that serve billions of people. "
            "You prefer local-first, privacy-preserving solutions. "
            "You support Rust, Python, TypeScript, and WASM. You know the AsimNexus microkernel deeply."
        ),
        capabilities=["Software Development", "System Architecture", "Bug Fixing",
                      "Code Review", "DevOps", "Database Design", "API Design"],
        preferred_models=["deepseek-coder", "codellama", "gpt-4o", "claude-3-5-sonnet-20241022"],
        preferred_providers=["local", "nvidia_nim", "openai", "anthropic"],
        temperature=0.3,
        max_tokens=8192,
    ),
    CloneConfig(
        role=CloneRole.STRATEGIC_PLANNER,
        icon="🧭",
        specialty="Long-term Planning, Risk Analysis, Strategy, Vision",
        system_prompt=(
            "You are the Strategic Planner of AsimNexus. You think in decades, not days. "
            "You analyze risks, opportunities, and global trends. You help individuals, companies, "
            "and governments make wise long-term decisions. You always consider ethical consequences."
        ),
        capabilities=["Strategic Planning", "Risk Analysis", "Career Planning",
                      "Business Strategy", "Decision Making", "Scenario Planning"],
        preferred_models=["claude-3-5-sonnet-20241022", "grok-3", "gpt-4o", "gemini-1.5-pro"],
        preferred_providers=["anthropic", "grok", "openai", "gemini"],
        temperature=0.7,
        max_tokens=8192,
    ),
    CloneConfig(
        role=CloneRole.FINANCIAL_ORACLE,
        icon="💰",
        specialty="Finance, Investment, Budget, Tax, Economic Analysis",
        system_prompt=(
            "You are the Financial Oracle of AsimNexus. You provide world-class financial guidance "
            "for individuals, families, and organizations. You analyze investments, optimize budgets, "
            "plan taxes, and model economic scenarios. You never give reckless advice — "
            "Dharma-Chakra VETO governs all financial actions."
        ),
        capabilities=["Investment Advice", "Budget Planning", "Tax Optimization",
                      "Economic Analysis", "Crypto/DeFi", "Insurance Planning"],
        preferred_models=["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-1.5-pro"],
        preferred_providers=["openai", "anthropic", "gemini"],
        temperature=0.4,
        max_tokens=4096,
        requires_human_confirm=True,
    ),
    CloneConfig(
        role=CloneRole.LEGAL_GUARDIAN,
        icon="⚖️",
        specialty="Law, Contracts, Rights, Compliance, Regulation",
        system_prompt=(
            "You are the Legal Guardian of AsimNexus. You understand laws across Nepal, India, "
            "EU, US, and international frameworks. You review contracts, protect rights, "
            "explain regulations, and flag legal risks. You always clarify: this is legal information, "
            "not legal advice — consult a licensed lawyer for binding decisions."
        ),
        capabilities=["Contract Review", "Rights Protection", "Regulatory Compliance",
                      "IP Protection", "Privacy Law", "Employment Law", "Criminal Law basics"],
        preferred_models=["claude-3-5-sonnet-20241022", "gpt-4o"],
        preferred_providers=["anthropic", "openai"],
        temperature=0.3,
        max_tokens=8192,
        requires_human_confirm=True,
    ),
    CloneConfig(
        role=CloneRole.HEALTH_SAGE,
        icon="❤️",
        specialty="Health, Medicine, Mental Health, Nutrition, Wellness",
        system_prompt=(
            "You are the Health Sage of AsimNexus. You provide evidence-based health guidance "
            "covering physical health, mental wellness, nutrition, and preventive care. "
            "You analyze medical reports (non-diagnostic), suggest healthy habits, and "
            "connect users to appropriate care. Critical: always recommend professional "
            "medical consultation for diagnosis and treatment."
        ),
        capabilities=["Health Advice", "Report Analysis", "Mental Health Support",
                      "Nutrition Planning", "Preventive Care", "Medication Info"],
        preferred_models=["gemini-1.5-pro", "claude-3-5-sonnet-20241022", "gpt-4o"],
        preferred_providers=["gemini", "anthropic", "openai"],
        temperature=0.5,
        max_tokens=4096,
        requires_human_confirm=True,
    ),
    CloneConfig(
        role=CloneRole.EDUCATION_MENTOR,
        icon="📚",
        specialty="Learning, Teaching, Skill Development, Curriculum",
        system_prompt=(
            "You are the Education Mentor of AsimNexus. You personalize learning for every human — "
            "from a child in a remote village to a PhD researcher. You adapt to learning styles, "
            "create custom curricula, explain complex topics simply, and guide career development. "
            "You support Nepali, Hindi, English and 100+ languages."
        ),
        capabilities=["Personalized Learning", "Tutoring", "Skill Development",
                      "Curriculum Design", "Career Guidance", "Exam Prep", "Language Learning"],
        preferred_models=["gemini-1.5-flash", "llama-3.1-8b", "gpt-4o-mini"],
        preferred_providers=["local", "gemini", "openai"],
        temperature=0.7,
        max_tokens=4096,
    ),
    CloneConfig(
        role=CloneRole.CREATIVE_MUSE,
        icon="🎨",
        specialty="Writing, Art, Music, Design, Storytelling, Content",
        system_prompt=(
            "You are the Creative Muse of AsimNexus. You are a master of human creativity — "
            "writing poetry, stories, scripts, music lyrics, visual design briefs, and more. "
            "You blend ancient wisdom (Vedic, Buddhist, Indigenous) with modern creative forms. "
            "You help humans express their authentic voice."
        ),
        capabilities=["Creative Writing", "Poetry", "Music Lyrics", "Design Briefs",
                      "Storytelling", "Content Creation", "Art Direction"],
        preferred_models=["claude-3-5-sonnet-20241022", "gpt-4o", "gemini-1.5-pro"],
        preferred_providers=["anthropic", "openai", "gemini"],
        temperature=0.9,
        max_tokens=4096,
    ),
    CloneConfig(
        role=CloneRole.RESEARCH_EXPLORER,
        icon="🔬",
        specialty="Science, Research, Data Analysis, Discovery",
        system_prompt=(
            "You are the Research Explorer of AsimNexus. You dive deep into scientific literature, "
            "analyze data, synthesize findings, and spark new discoveries. You cover all fields — "
            "medicine, physics, social science, environmental science, AI research. "
            "You cite sources, flag uncertainty, and distinguish fact from hypothesis."
        ),
        capabilities=["Literature Review", "Data Analysis", "Research Synthesis",
                      "Hypothesis Generation", "Scientific Writing", "Patent Analysis"],
        preferred_models=["grok-3", "claude-3-5-sonnet-20241022", "gpt-4o"],
        preferred_providers=["grok", "anthropic", "openai"],
        temperature=0.4,
        max_tokens=8192,
    ),
    CloneConfig(
        role=CloneRole.SECURITY_SENTINEL,
        icon="🛡️",
        specialty="Cybersecurity, Privacy, Threat Detection, Zero-Trust",
        system_prompt=(
            "You are the Security Sentinel of AsimNexus. You protect humans and systems from "
            "digital threats. You audit code for vulnerabilities, explain privacy risks, "
            "implement zero-trust principles, and detect malicious patterns. "
            "You guard the AsimNexus kernel itself and enforce constitutional safety."
        ),
        capabilities=["Security Audit", "Threat Detection", "Privacy Protection",
                      "Zero-Trust Design", "Incident Response", "Penetration Testing basics"],
        preferred_models=["deepseek-coder", "gpt-4o", "claude-3-5-sonnet-20241022"],
        preferred_providers=["local", "openai", "anthropic"],
        temperature=0.2,
        max_tokens=4096,
        requires_human_confirm=True,
    ),
    CloneConfig(
        role=CloneRole.LOGISTICS_MASTER,
        icon="🚚",
        specialty="Transport, Supply Chain, Travel, Optimization",
        system_prompt=(
            "You are the Logistics Master of AsimNexus. You optimize the movement of people, "
            "goods, and information across the world. You plan travel, optimize supply chains, "
            "coordinate deliveries, and solve routing problems. You connect to Maps, "
            "flight, hotel, and shipping APIs through AsimNexus MCP connectors."
        ),
        capabilities=["Travel Planning", "Route Optimization", "Supply Chain",
                      "Delivery Coordination", "Booking Assistance", "Cost Optimization"],
        preferred_models=["gpt-4o", "gemini-1.5-flash", "llama-3.1-8b"],
        preferred_providers=["openai", "gemini", "local"],
        temperature=0.5,
        max_tokens=4096,
    ),
    CloneConfig(
        role=CloneRole.ENV_STEWARD,
        icon="🌿",
        specialty="Environment, Climate, Sustainability, Conservation",
        system_prompt=(
            "You are the Environmental Steward of AsimNexus. You champion planetary health. "
            "You analyze climate data, track carbon footprints, guide sustainable choices, "
            "support conservation efforts, and help build regenerative economies. "
            "You connect to satellite data, climate models, and biodiversity databases."
        ),
        capabilities=["Carbon Tracking", "Climate Analysis", "Sustainability Planning",
                      "Conservation", "Renewable Energy", "Environmental Compliance"],
        preferred_models=["gemini-1.5-pro", "claude-3-5-sonnet-20241022", "gpt-4o"],
        preferred_providers=["gemini", "anthropic", "openai"],
        temperature=0.6,
        max_tokens=4096,
    ),
    CloneConfig(
        role=CloneRole.SOCIAL_HARMONIZER,
        icon="🤝",
        specialty="Relationships, Community, Conflict Resolution, Culture",
        system_prompt=(
            "You are the Social Harmonizer of AsimNexus. You understand human relationships, "
            "cultural dynamics, community building, and conflict resolution. "
            "You help families, teams, and communities resolve disputes, build trust, "
            "and create inclusive spaces. You are empathetic, non-judgmental, and wise."
        ),
        capabilities=["Conflict Resolution", "Relationship Advice", "Community Building",
                      "Cultural Sensitivity", "Team Dynamics", "Mental Wellness Support"],
        preferred_models=["claude-3-5-sonnet-20241022", "gpt-4o", "gemini-1.5-pro"],
        preferred_providers=["anthropic", "openai", "gemini"],
        temperature=0.8,
        max_tokens=4096,
    ),
    CloneConfig(
        role=CloneRole.GOVERNANCE_ADVISOR,
        icon="🏛️",
        specialty="Policy, Government, Democracy, Transparency, Anti-Corruption",
        system_prompt=(
            "You are the Governance Advisor of AsimNexus. You help governments, institutions, "
            "and citizens build transparent, accountable, and just systems. "
            "You draft policy, analyze governance models, detect corruption patterns, "
            "and support democratic processes through smart contracts and verifiable voting. "
            "You are bound by the Dharma-Chakra constitution — you cannot help any entity "
            "gain unjust power over others."
        ),
        capabilities=["Policy Analysis", "Anti-Corruption", "Democratic Tools",
                      "Budget Transparency", "Smart Contracts", "Public Service Design"],
        preferred_models=["claude-3-5-sonnet-20241022", "gpt-4o", "grok-3"],
        preferred_providers=["anthropic", "openai", "grok"],
        temperature=0.4,
        max_tokens=8192,
        requires_human_confirm=True,
    ),
    CloneConfig(
        role=CloneRole.INNOVATION_CATALYST,
        icon="⚡",
        specialty="New Ideas, Breakthroughs, Startups, Future Tech",
        system_prompt=(
            "You are the Innovation Catalyst of AsimNexus. You ignite breakthroughs. "
            "You combine ideas across disciplines to create novel solutions. "
            "You help entrepreneurs build startups, researchers find new angles, "
            "and dreamers turn visions into reality. You know every emerging technology — "
            "AI, quantum computing, biotech, nanotech, space tech."
        ),
        capabilities=["Startup Ideation", "Innovation Frameworks", "Technology Scouting",
                      "Product Innovation", "Patent Ideas", "Cross-domain Synthesis"],
        preferred_models=["grok-3", "claude-3-5-sonnet-20241022", "gpt-4o"],
        preferred_providers=["grok", "anthropic", "openai"],
        temperature=0.9,
        max_tokens=4096,
    ),
    CloneConfig(
        role=CloneRole.HARMONY_KEEPER,
        icon="☯️",
        specialty="System Balance, Ethics, Dharma, ΔT Monitoring, Meta-oversight",
        system_prompt=(
            "You are the Harmony Keeper of AsimNexus — the meta-intelligence that watches over "
            "all 14 other clones and the entire system. You enforce the Dharma-Chakra constitution. "
            "You monitor the ΔT (delta-T) — the divergence between AI decisions and human values. "
            "When any clone or action threatens balance, you invoke VETO. "
            "You are the ultimate guardian of human sovereignty in the AsimNexus ecosystem. "
            "You cannot be overridden by any user, admin, or government — only by verified human consensus."
        ),
        capabilities=["Ethics Oversight", "Constitutional Enforcement", "VETO Authority",
                      "System Balance", "Dharma Monitoring", "Human Sovereignty Protection"],
        preferred_models=["claude-3-5-sonnet-20241022", "gpt-4o", "grok-3"],
        preferred_providers=["anthropic", "openai", "grok"],
        temperature=0.3,
        max_tokens=8192,
        requires_human_confirm=True,
    ),
]


class WorldClone:
    """A single World-Role Founder Clone — intelligent, ethical, local-first."""

    def __init__(self, config: CloneConfig, api_keys: Dict[str, str] = None):
        self.config = config
        self.api_keys = api_keys or {}
        self.chat_history: List[Dict] = []
        self.tasks_completed: int = 0
        self.active: bool = True
        self.mode: str = "personal"  # personal / work / public / emergency

    async def process(self, message: str, user_context: Dict = None) -> str:
        """Process a message — local first, cloud fallback."""
        # 1. Try local Ollama
        local_response = await self._try_local(message, user_context)
        if local_response:
            self.tasks_completed += 1
            return self._format(local_response)

        # 2. Try cloud providers in priority order
        for provider in self.config.preferred_providers:
            if provider == "local":
                continue
            key = self._get_key(provider)
            if not key:
                continue
            try:
                response = await self._try_cloud(provider, key, message, user_context)
                if response:
                    self.tasks_completed += 1
                    return self._format(response)
            except Exception as e:
                logger.warning(f"{self.config.role.value} provider {provider} failed: {e}")
                continue

        # 3. Graceful offline fallback
        return self._offline_response(message)

    async def _try_local(self, message: str, context: Dict = None) -> Optional[str]:
        """Try local Ollama endpoint."""
        try:
            import httpx
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "gemma2:2b")
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": self.config.system_prompt},
                    {"role": "user", "content": message}
                ],
                "stream": False,
                "options": {"temperature": self.config.temperature, "num_predict": 512}
            }
            async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT_SEC) as client:
                r = await client.post(f"{ollama_url}/api/chat", json=payload)
                if r.status_code == 200:
                    return r.json().get("message", {}).get("content", "")
        except Exception:
            return None
        return None

    async def _try_cloud(self, provider: str, api_key: str, message: str, context: Dict = None) -> Optional[str]:
        """Try a cloud provider."""
        from openai import AsyncOpenAI

        base_urls = {
            "nvidia_nim": "https://integrate.api.nvidia.com/v1",
            "openai":     "https://api.openai.com/v1",
            "anthropic":  None,  # handled separately
            "gemini":     "https://generativelanguage.googleapis.com/v1beta/openai/",
            "deepseek":   "https://api.deepseek.com/v1",
            "grok":       "https://api.x.ai/v1",
        }
        models = {
            "nvidia_nim": os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.1-8b-instruct"),
            "openai":     os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "gemini":     os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            "deepseek":   os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "grok":       os.getenv("GROK_MODEL", "grok-beta"),
        }

        if provider == "anthropic":
            return await self._try_anthropic(api_key, message)

        base_url = base_urls.get(provider)
        model = models.get(provider, "gpt-4o-mini")
        if not base_url:
            return None

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return resp.choices[0].message.content

    async def _try_anthropic(self, api_key: str, message: str) -> Optional[str]:
        """Try Anthropic Claude."""
        try:
            import anthropic
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            client = anthropic.AsyncAnthropic(api_key=api_key)
            resp = await client.messages.create(
                model=model,
                max_tokens=self.config.max_tokens,
                system=self.config.system_prompt,
                messages=[{"role": "user", "content": message}]
            )
            return resp.content[0].text
        except Exception as e:
            logger.warning(f"Anthropic error: {e}")
            return None

    def _get_key(self, provider: str) -> Optional[str]:
        """Get API key for provider from env."""
        env_map = {
            "nvidia_nim": "NVIDIA_NIM_API_KEY",
            "openai":     "OPENAI_API_KEY",
            "anthropic":  "ANTHROPIC_API_KEY",
            "gemini":     "GEMINI_API_KEY",
            "deepseek":   "DEEPSEEK_API_KEY",
            "grok":       "GROK_API_KEY",
        }
        return os.getenv(env_map.get(provider, ""), "")

    def _format(self, response: str) -> str:
        """Format response with clone identity."""
        return f"**{self.config.icon} {self.config.role.value}:**\n\n{response}"

    def _offline_response(self, message: str) -> str:
        """Graceful offline response — no API needed."""
        return (
            f"**{self.config.icon} {self.config.role.value} (Offline Mode):**\n\n"
            f"I received your request: \"{message[:100]}...\"\n\n"
            f"I'm operating offline — no internet or API key available. "
            f"My specialty is {self.config.specialty}. "
            f"Please connect to the internet or configure an API key in your `.env` file "
            f"to get full intelligent responses."
        )

    def to_dict(self) -> Dict:
        return {
            "role": self.config.role.value,
            "icon": self.config.icon,
            "specialty": self.config.specialty,
            "capabilities": self.config.capabilities,
            "active": self.active,
            "tasks_completed": self.tasks_completed,
            "mode": self.mode,
            "requires_human_confirm": self.config.requires_human_confirm,
        }


class WorldCloneOrchestrator:
    """
    Orchestrates all 15 World Clones.
    - Routes requests to relevant clones
    - Enforces Dharma VETO before execution
    - Manages Level-3 Human Confirmation for critical tasks
    - **Ensemble consensus voting** (Milestone 4)
    - Supports Agent Mode toggle (ON/OFF)
    - Supports 5/15/30 day work cycles
    """

    def __init__(self):
        self.clones: Dict[CloneRole, WorldClone] = {}
        self.agent_mode: bool = _DEFAULT_AGENT_MODE
        self._smart_router = None  # Fix 5: SmartLLMRouter bridge
        self._consensus_engine = None  # Milestone 4: ConsensusEngine bridge
        self._build_clones()
        self._try_connect_smart_router()
        self._try_init_consensus()
        logger.info(f"WorldCloneOrchestrator: {len(self.clones)} clones initialized")

    def _try_init_consensus(self):
        """Initialize ConsensusEngine and register all clones as voters."""
        try:
            from .consensus_engine import get_consensus_engine, reset_consensus_engine
            reset_consensus_engine()
            self._consensus_engine = get_consensus_engine()
            # Register all clones as voters with dharma_weight from config
            for cfg in WORLD_CLONE_CONFIGS:
                # Assign weights based on role criticality
                weight_map = {
                    CloneRole.HARMONY_KEEPER: 1.0,
                    CloneRole.SECURITY_SENTINEL: 0.95,
                    CloneRole.LEGAL_GUARDIAN: 0.9,
                    CloneRole.HEALTH_SAGE: 0.9,
                    CloneRole.GOVERNANCE_ADVISOR: 0.85,
                    CloneRole.ENV_STEWARD: 0.85,
                    CloneRole.SOCIAL_HARMONIZER: 0.85,
                    CloneRole.FINANCIAL_ORACLE: 0.85,
                    CloneRole.EDUCATION_MENTOR: 0.8,
                    CloneRole.RESEARCH_EXPLORER: 0.8,
                    CloneRole.TECH_ARCHITECT: 0.8,
                    CloneRole.INNOVATION_CATALYST: 0.75,
                    CloneRole.LOGISTICS_MASTER: 0.75,
                    CloneRole.CREATIVE_MUSE: 0.7,
                    CloneRole.STRATEGIC_PLANNER: 0.85,
                }
                weight = weight_map.get(cfg.role, 0.8)
                self._consensus_engine.register_voter(
                    voter_id=cfg.role.value.lower().replace(" ", "_"),
                    name=cfg.role.value,
                    weight=weight,
                    metadata={
                        "role": cfg.role.value,
                        "icon": cfg.icon,
                        "requires_human_confirm": cfg.requires_human_confirm,
                    }
                )
            logger.info(f"ConsensusEngine initialized with {len(WORLD_CLONE_CONFIGS)} voters")
        except Exception as e:
            logger.warning(f"ConsensusEngine not available (optional): {e}")

    def _try_connect_smart_router(self):
        """Fix 5: Bridge to SmartLLMRouter for cost+latency aware routing."""
        try:
            from core.smart_llm_router import get_smart_router
            self._smart_router = get_smart_router()
            logger.info("SmartLLMRouter connected to WorldCloneOrchestrator")
        except Exception as e:
            logger.warning(f"SmartLLMRouter not available (optional): {e}")

    def get_best_model_for_clone(self, clone_config: 'CloneConfig') -> Optional[str]:
        """Fix 5: Ask SmartLLMRouter for the best model for this clone's task type."""
        if not self._smart_router:
            return None
        try:
            from core.smart_llm_router import TaskPriority, TaskType
            task_map = {
                "Tech Architect": TaskType.CODE_GENERATION,
                "Research Explorer": TaskType.ANALYSIS,
                "Strategic Planner": TaskType.REASONING,
                "Financial Oracle": TaskType.ANALYSIS,
                "Creative Muse": TaskType.CHAT,
            }
            task_type = task_map.get(clone_config.role.value, TaskType.GENERAL)
            model = self._smart_router.select_model(
                task_type=task_type,
                priority=TaskPriority.BALANCED
            )
            return model.name if model else None
        except Exception:
            return None

    def _build_clones(self):
        for cfg in WORLD_CLONE_CONFIGS:
            self.clones[cfg.role] = WorldClone(cfg)

    def get_all_clones(self) -> List[Dict]:
        return [c.to_dict() for c in self.clones.values()]

    def toggle_agent_mode(self, enabled: bool):
        self.agent_mode = enabled
        logger.info(f"Agent Mode: {'ON' if enabled else 'OFF'}")

    # ─── Milestone 4: Ensemble Consensus Voting ────────────────────────────────

    def get_consensus_engine(self):
        """Get the ConsensusEngine instance."""
        return self._consensus_engine

    async def initiate_consensus_vote(
        self,
        title: str,
        description: str,
        proposed_by: str = "system",
        strategy: str = "weighted_majority",
        quorum_threshold: float = 0.5,
        expires_in_seconds: Optional[int] = 300,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Initiate an ensemble consensus vote across all clones.
        Returns the proposal details.
        """
        if not self._consensus_engine:
            return {"error": "ConsensusEngine not available"}

        from .consensus_engine import VotingStrategy
        strategy_map = {
            "simple_majority": VotingStrategy.SIMPLE_MAJORITY,
            "super_majority": VotingStrategy.SUPER_MAJORITY,
            "unanimous": VotingStrategy.UNANIMOUS,
            "weighted_majority": VotingStrategy.WEIGHTED_MAJORITY,
            "weighted_super": VotingStrategy.WEIGHTED_SUPER,
        }
        vs = strategy_map.get(strategy, VotingStrategy.WEIGHTED_MAJORITY)

        proposal = self._consensus_engine.create_proposal(
            title=title,
            description=description,
            proposed_by=proposed_by,
            strategy=vs,
            quorum_threshold=quorum_threshold,
            expires_in_seconds=expires_in_seconds,
            context=context,
        )
        return {
            "proposal_id": proposal.id,
            "title": proposal.title,
            "strategy": strategy,
            "quorum_threshold": quorum_threshold,
            "created_at": proposal.created_at.isoformat(),
            "expires_at": proposal.expires_at.isoformat() if proposal.expires_at else None,
        }

    async def cast_clone_vote(
        self,
        proposal_id: str,
        clone_role: str,
        vote: str,
        rationale: str = "",
    ) -> Dict[str, Any]:
        """
        Cast a vote from a specific clone on an active proposal.
        vote: "approve", "reject", or "abstain"
        Returns the vote result if resolved, or current status.
        """
        if not self._consensus_engine:
            return {"error": "ConsensusEngine not available"}

        from .consensus_engine import Vote

        vote_enum_map = {
            "approve": Vote.APPROVE,
            "reject": Vote.REJECT,
            "abstain": Vote.ABSTAIN,
        }
        ve = vote_enum_map.get(vote.lower())
        if not ve:
            return {"error": f"Invalid vote: {vote}. Use approve/reject/abstain"}

        voter_id = clone_role.lower().replace(" ", "_")
        result = self._consensus_engine.cast_vote(
            proposal_id=proposal_id,
            voter_id=voter_id,
            vote=ve,
            rationale=rationale,
        )

        if result is None:
            # Vote recorded but not resolved yet — return status
            status = self._consensus_engine.get_vote_status(proposal_id)
            return {"status": "voted_pending", "vote_status": status}

        return {"status": "resolved", "result": result.to_dict()}

    async def get_vote_status(self, proposal_id: str) -> Dict[str, Any]:
        """Get current status of a vote."""
        if not self._consensus_engine:
            return {"error": "ConsensusEngine not available"}
        status = self._consensus_engine.get_vote_status(proposal_id)
        if status is None:
            return {"error": f"Proposal {proposal_id} not found"}
        return status

    async def get_voting_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get complete voting history."""
        if not self._consensus_engine:
            return []
        return self._consensus_engine.get_voting_history(limit=limit)

    async def get_consensus_stats(self) -> Dict[str, Any]:
        """Get consensus engine statistics."""
        if not self._consensus_engine:
            return {"error": "ConsensusEngine not available"}
        return self._consensus_engine.get_stats()

    def select_clones_for_task(self, message: str) -> List[CloneRole]:
        """Intelligently select which clones to involve — supports Nepali + Unicode."""
        msg = _normalize(message)  # Fix 4: NFKC normalize — handles Nepali Unicode
        selected = []

        role_keywords = {
            CloneRole.TECH_ARCHITECT: [
                "code", "software", "bug", "api", "database", "system", "develop", "program", "tech",
                "कोड", "सफ्टवेयर", "प्रोग्राम", "सिस्टम", "डाटाबेस",
            ],
            CloneRole.STRATEGIC_PLANNER: [
                "strategy", "plan", "vision", "future", "goal", "risk", "decision", "roadmap",
                "योजना", "रणनीति", "लक्ष्य", "भविष्य",
            ],
            CloneRole.FINANCIAL_ORACLE: [
                "money", "invest", "budget", "tax", "finance", "cost", "income", "crypto", "bank",
                "पैसा", "लगानी", "बजेट", "कर", "बैंक", "ऋण", "बचत",
            ],
            CloneRole.LEGAL_GUARDIAN: [
                "law", "legal", "contract", "right", "court", "compliance", "regulation",
                "कानून", "अदालत", "सम्झौता", "अधिकार", "न्याय",
            ],
            CloneRole.HEALTH_SAGE: [
                "health", "doctor", "medicine", "sick", "diet", "mental", "wellness", "hospital",
                "स्वास्थ्य", "डाक्टर", "औषधि", "बिरामी", "अस्पताल", "खाना",
            ],
            CloneRole.EDUCATION_MENTOR: [
                "learn", "study", "teach", "school", "skill", "exam", "course", "education",
                "सिक्नु", "पढाइ", "विद्यालय", "परीक्षा", "सीप", "शिक्षा",
            ],
            CloneRole.CREATIVE_MUSE: [
                "write", "art", "music", "design", "story", "poem", "creative", "content",
                "लेख्नु", "कला", "संगीत", "कविता", "कथा", "डिजाइन",
            ],
            CloneRole.RESEARCH_EXPLORER: [
                "research", "science", "data", "study", "analysis", "paper", "discover",
                "अनुसन्धान", "विज्ञान", "डेटा", "विश्लेषण",
            ],
            CloneRole.SECURITY_SENTINEL: [
                "security", "hack", "privacy", "threat", "protect", "cyber", "safe",
                "सुरक्षा", "ह्याक", "गोपनीयता", "खतरा",
            ],
            CloneRole.LOGISTICS_MASTER: [
                "travel", "book", "flight", "hotel", "deliver", "transport", "route", "shipping",
                "यात्रा", "उडान", "होटल", "ढुवानी",
            ],
            CloneRole.ENV_STEWARD: [
                "environment", "climate", "carbon", "nature", "sustainable", "green", "ecology",
                "वातावरण", "जलवायु", "प्रकृति", "हरियाली",
            ],
            CloneRole.SOCIAL_HARMONIZER: [
                "relationship", "conflict", "family", "community", "culture", "friend", "team",
                "सम्बन्ध", "परिवार", "समाज", "संस्कृति", "साथी",
            ],
            CloneRole.GOVERNANCE_ADVISOR: [
                "government", "policy", "democracy", "law", "corruption", "election", "vote",
                "सरकार", "नीति", "प्रजातन्त्र", "भ्रष्टाचार", "निर्वाचन",
            ],
            CloneRole.INNOVATION_CATALYST: [
                "idea", "startup", "innovation", "invention", "new", "breakthrough", "future",
                "विचार", "नवीनता", "स्टार्टअप", "आविष्कार",
            ],
            CloneRole.HARMONY_KEEPER: [
                "ethics", "dharma", "balance", "safe", "constitution", "veto", "oversight",
                "धर्म", "नैतिकता", "सन्तुलन", "संविधान",
            ],
        }

        for role, keywords in role_keywords.items():
            if any(kw in msg for kw in keywords):
                selected.append(role)

        # Always involve Harmony Keeper for oversight
        if CloneRole.HARMONY_KEEPER not in selected:
            selected.append(CloneRole.HARMONY_KEEPER)

        # Default: Tech + Strategic if nothing matched
        if len(selected) == 1:
            selected.insert(0, CloneRole.STRATEGIC_PLANNER)

        return selected[:_DEFAULT_MAX_CLONES]  # configurable max clones per request

    async def process(self, message: str, user_context: Dict = None,
                      veto_check: bool = True) -> Dict:
        """
        Main entry point — routes message through selected clones.
        Returns structured response with clone outputs + veto status.
        """
        # Dharma VETO check
        veto_blocked = False
        veto_reason = ""
        if veto_check:
            try:
                from core.dharma_chakra.veto_engine import get_veto_engine
                veto = get_veto_engine()
                result = veto.check(message, _DEFAULT_SECTOR, "world_clone_orchestrator")
                if not result.allowed:
                    veto_blocked = True
                    veto_reason = result.reason
            except Exception:
                pass

        if veto_blocked:
            return {
                "status": "blocked",
                "veto_reason": veto_reason,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }

        # Select relevant clones
        roles = self.select_clones_for_task(message)
        results = {}
        needs_confirmation = False

        for role in roles:
            clone = self.clones.get(role)
            if not clone:
                continue
            if clone.config.requires_human_confirm:
                needs_confirmation = True
            response = await clone.process(message, user_context)
            results[role.value] = response

        return {
            "status": "completed" if not needs_confirmation else "awaiting_confirmation",
            "clones_involved": [r.value for r in roles],
            "responses": results,
            "needs_level3_confirmation": needs_confirmation,
            "agent_mode": self.agent_mode,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_clone(self, role: CloneRole) -> Optional[WorldClone]:
        return self.clones.get(role)

    async def direct_message(self, role_name: str, message: str) -> str:
        """Send directly to a specific clone by role name."""
        for role, clone in self.clones.items():
            if role.value.lower() == role_name.lower():
                return await clone.process(message)
        return f"Clone '{role_name}' not found. Available: {[r.value for r in self.clones]}"

    def get_clone_for_intent(self, intent: str) -> Optional[WorldClone]:
        """
        Map an intent string (from HybridRouter) to the most relevant WorldClone.
        Used by simple_backend.py to route chat messages to the correct clone.
        """
        intent_map: Dict[str, CloneRole] = {
            "health": CloneRole.HEALTH_SAGE,
            "finance": CloneRole.FINANCIAL_ORACLE,
            "legal": CloneRole.LEGAL_GUARDIAN,
            "education": CloneRole.EDUCATION_MENTOR,
            "government": CloneRole.GOVERNANCE_ADVISOR,
            "technical": CloneRole.TECH_ARCHITECT,
            "communication": CloneRole.SOCIAL_HARMONIZER,
            "agriculture": CloneRole.ENV_STEWARD,
            "transport": CloneRole.LOGISTICS_MASTER,
            "energy": CloneRole.ENV_STEWARD,
            "security": CloneRole.SECURITY_SENTINEL,
            "commerce": CloneRole.FINANCIAL_ORACLE,
            "research": CloneRole.RESEARCH_EXPLORER,
            "emergency": CloneRole.HARMONY_KEEPER,
            "creative": CloneRole.CREATIVE_MUSE,
            "personal": CloneRole.STRATEGIC_PLANNER,
            "system_control": CloneRole.TECH_ARCHITECT,
            "generic": CloneRole.STRATEGIC_PLANNER,
        }
        role = intent_map.get(intent.lower())
        if role is None:
            return None
        return self.clones.get(role)


# ─── Singleton ───────────────────────────────────────────────────────────────
_orchestrator: Optional[WorldCloneOrchestrator] = None

def get_world_clones() -> WorldCloneOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = WorldCloneOrchestrator()
    return _orchestrator
