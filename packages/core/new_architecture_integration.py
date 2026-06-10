
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS New Architecture Integration
========================================

This module integrates all 9 improvements + 5 World OS components into a cohesive system:

Original 9 improvements:
1. Hybrid Router (keyword + embedding + LLM)
2. Central State Manager (Redis + DB unified)
3. Refactored Orchestrator (planning only, separate execution)
4. Tool Engine (category-based filtering)
5. Simplified Agents (3 core roles: Planner, Executor, Analyst)
6. Upgraded RAG (hybrid search + re-ranking)
7. Smart LLM Routing (cost + latency aware)
8. Mandatory Validation Layer
9. Async Execution + Caching

New World OS components:
10. seL4-inspired Microkernel (capability-based security, process isolation)
11. P2P Network (Kademlia DHT, mesh routing)
12. DePIN Connectors (Uplink, Daylight, DIMO)
13. Resource-Based Economy (equilibrium distribution)
14. Mythos Security Scanner (AI-powered vulnerability detection)

Usage:
    from core.new_architecture_integration import NewASIMNEXUS
    
    asim = NewASIMNEXUS()
    await asim.initialize()
    
    result = await asim.process("Find and summarize the authentication code")
    logger.info(result['response'])
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("NewASIMNEXUS")

# ─── Safe Import Helper ───────────────────────────────────────────────────────
def _safe_import(module_path: str, names: list):
    """Import a module safely — never crash the whole system on a missing file."""
    try:
        mod = __import__(module_path, fromlist=names)
        return tuple(getattr(mod, n, None) for n in names)
    except Exception as e:
        logger.warning(f"⚠️  Optional module unavailable [{module_path}]: {e}")
        return tuple(None for _ in names)

# ─── Core components ─────────────────────────────────────────────────────────
(HybridRouter, RouteDecision, IntentType) = _safe_import(
    "core.routing.hybrid_router", ["HybridRouter", "RouteDecision", "IntentType"])

(CentralStateManager, StateNamespace, get_state_manager) = _safe_import(
    "core.state_manager", ["CentralStateManager", "StateNamespace", "get_state_manager"])

(ExecutionPipeline, PlannerAgent, ExecutorAgent, AnalystAgent, ResponseCompiler) = _safe_import(
    "core.execution_pipeline",
    ["ExecutionPipeline", "PlannerAgent", "ExecutorAgent", "AnalystAgent", "ResponseCompiler"])

(CategorizedToolRegistry, ToolCategory) = _safe_import(
    "core.tools.categorized_registry", ["CategorizedToolRegistry", "ToolCategory"])

(ToolFilter, ToolEngine) = _safe_import(
    "core.tools.tool_filter", ["ToolFilter", "ToolEngine"])

(SimplifiedAgentSystem, SimplePlanner, SimpleExecutor, SimpleAnalyst, BaseAgent, AgentRole) = _safe_import(
    "agents.simplified_agents",
    ["SimplifiedAgentSystem", "PlannerAgent", "ExecutorAgent", "AnalystAgent", "BaseAgent", "AgentRole"])

(HybridRAG,) = _safe_import("core.rag.hybrid_rag", ["HybridRAG"])

(SmartLLMRouter, TaskPriority, TaskType, ModelConfig, get_smart_router) = _safe_import(
    "core.smart_llm_router",
    ["SmartLLMRouter", "TaskPriority", "TaskType", "ModelConfig", "get_smart_router"])

(CacheManager, AsyncExecutor, cached, get_cache_manager, get_async_executor) = _safe_import(
    "core.cache_manager",
    ["CacheManager", "AsyncExecutor", "cached", "get_cache_manager", "get_async_executor"])

# ─── World OS components ──────────────────────────────────────────────────────
(ASIMMicrokernel, get_microkernel) = _safe_import(
    "core.kernel.microkernel", ["ASIMMicrokernel", "get_microkernel"])

(P2PNetwork, get_p2p_network) = _safe_import(
    "core.network.p2p_network", ["P2PNetwork", "get_p2p_network"])

(UplinkConnector, get_uplink_connector) = _safe_import(
    "core.depin.uplink_connector", ["UplinkConnector", "get_uplink_connector"])

(DaylightConnector, get_daylight_connector) = _safe_import(
    "core.depin.daylight_connector", ["DaylightConnector", "get_daylight_connector"])

(DIMOConnector, get_dimo_connector) = _safe_import(
    "core.depin.dimo_connector", ["DIMOConnector", "get_dimo_connector"])

(RBEAlgorithm, get_rbe_algorithm) = _safe_import(
    "core.world.economy.rbe_algorithm", ["RBEAlgorithm", "get_rbe_algorithm"])

(MythosScanner, get_mythos_scanner) = _safe_import(
    "core.security.mythos_scanner", ["MythosScanner", "get_mythos_scanner"])

# ─── Universal OS components ──────────────────────────────────────────────────
(APIGateway, GatewayConfig) = _safe_import(
    "core.universal_api_gateway", ["APIGateway", "GatewayConfig"])

(DigitalTwinSystem, get_digital_twin_system) = _safe_import(
    "core.digital_twin_system", ["DigitalTwinSystem", "get_digital_twin_system"])

(LifeProtocolAutomation, get_life_protocol_automation) = _safe_import(
    "core.life_protocol_automation", ["LifeProtocolAutomation", "get_life_protocol_automation"])

(GlobalMeshNetwork, get_global_mesh_network) = _safe_import(
    "core.global_mesh", ["GlobalMeshNetwork", "get_global_mesh_network"])

# ─── AGI + Quantum + Blockchain ───────────────────────────────────────────────
(AGICore, get_agi_core, ReasoningMode, AGICapability) = _safe_import(
    "core.agi_core", ["AGICore", "get_agi_core", "ReasoningMode", "AGICapability"])

(QuantumBridge, get_quantum_bridge, QuantumAlgorithm, QuantumProvider) = _safe_import(
    "core.quantum_bridge",
    ["QuantumBridge", "get_quantum_bridge", "QuantumAlgorithm", "QuantumProvider"])

(BlockchainIdentityAdvanced, get_blockchain_identity_advanced, BlockchainNetwork, AttestationType) = _safe_import(
    "core.blockchain_identity_advanced",
    ["BlockchainIdentityAdvanced", "get_blockchain_identity_advanced",
     "BlockchainNetwork", "AttestationType"])


@dataclass
class ASIMConfig:
    """Configuration for the new ASIMNEXUS architecture."""
    # Redis
    redis_host: str = 'localhost'
    redis_port: int = 6379
    
    # Caching
    cache_l1_size: int = 1000
    cache_l1_ttl: int = 300
    
    # Concurrency
    max_concurrency: int = 10
    
    # Models
    embedding_model: str = 'all-MiniLM-L6-v2'
    reranker_model: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
    
    # Cost limits
    daily_cost_limit: float = 10.0
    monthly_cost_limit: float = 100.0
    
    # API Keys
    api_keys: Dict[str, str] = None
    
    # World OS Configuration
    enable_microkernel: bool = True
    enable_p2p_network: bool = True
    enable_depin: bool = True
    enable_rbe: bool = True
    enable_mythos: bool = True
    
    # Universal OS Configuration
    enable_universal_gateway: bool = True
    enable_digital_twins: bool = True
    enable_life_automation: bool = True
    enable_global_mesh: bool = True
    
    # AGI Configuration
    enable_agi: bool = True
    agi_reasoning_depth: int = 10
    agi_self_improvement: bool = True
    agi_human_oversight: bool = True
    
    # Quantum Computing Configuration
    enable_quantum: bool = True
    quantum_provider: str = "simulator"
    quantum_hybrid_threshold: int = 1000
    
    # Blockchain Identity Configuration
    enable_blockchain_identity: bool = True
    blockchain_network: str = "ethereum"
    
    # P2P Network
    p2p_host: str = '0.0.0.0'
    p2p_port: int = 6881
    p2p_bootstrap_nodes: list = None
    
    # Universal API Gateway
    gateway_port: int = 8000
    gateway_host: str = '0.0.0.0'
    gateway_enable_rate_limiting: bool = True
    
    # DePIN API Keys
    uplink_api_key: str = None
    daylight_api_key: str = None
    dimo_api_key: str = None
    
    # API Keys for AGI, Quantum, Blockchain
    ibm_quantum_api_key: str = None
    amazon_braket_api_key: str = None
    ethereum_api_key: str = None


class NewASIMNEXUS:
    """
    ASIMNEXUS with all 9 architectural improvements + 5 World OS components + 3 Universal OS components integrated.
    
    This is the main entry point for the Universal World OS system.
    """
    
    def __init__(self, config: Optional[ASIMConfig] = None):
        self.config = config or ASIMConfig()
        
        # Original Components (initialized in initialize())
        self.state_manager: Optional[CentralStateManager] = None
        self.cache_manager: Optional[CacheManager] = None
        self.async_executor: Optional[AsyncExecutor] = None
        
        self.hybrid_router: Optional[HybridRouter] = None
        self.smart_llm_router: Optional[SmartLLMRouter] = None
        
        self.tool_engine: Optional[ToolEngine] = None
        self.hybrid_rag: Optional[HybridRAG] = None
        
        self.agent_system: Optional[SimplifiedAgentSystem] = None
        self.execution_pipeline: Optional[ExecutionPipeline] = None
        
        # World OS Components (initialized in initialize())
        self.microkernel: Optional[ASIMMicrokernel] = None
        self.p2p_network: Optional[P2PNetwork] = None
        self.uplink_connector: Optional[UplinkConnector] = None
        self.daylight_connector: Optional[DaylightConnector] = None
        self.dimo_connector: Optional[DIMOConnector] = None
        self.rbe_algorithm: Optional[RBEAlgorithm] = None
        self.mythos_scanner: Optional[MythosScanner] = None
        
        # Universal OS Components (initialized in initialize())
        self.api_gateway: Optional[APIGateway] = None
        self.digital_twin_system: Optional[DigitalTwinSystem] = None
        self.life_automation: Optional[LifeProtocolAutomation] = None
        self.global_mesh: Optional[GlobalMeshNetwork] = None
        
        # AGI, Quantum, and Blockchain Components
        self.agi_core: Optional[AGICore] = None
        self.quantum_bridge: Optional[QuantumBridge] = None
        self.blockchain_identity: Optional[BlockchainIdentityAdvanced] = None
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize all components."""
        if self._initialized:
            return
        
        logger.info("🔧 Initializing New ASIMNEXUS World OS Architecture...")
        
        # 1. Infrastructure Layer
        logger.info("  📦 Setting up infrastructure...")
        self.state_manager = CentralStateManager(
            redis_host=self.config.redis_host,
            redis_port=self.config.redis_port
        )
        self.cache_manager = CacheManager(
            l1_size=self.config.cache_l1_size,
            l1_ttl=self.config.cache_l1_ttl,
            redis_host=self.config.redis_host,
            redis_port=self.config.redis_port
        )
        self.async_executor = AsyncExecutor(
            max_concurrency=self.config.max_concurrency
        )
        
        # 2. Routing Layer
        logger.info("  🧭 Setting up routing...")
        if SmartLLMRouter:
            self.smart_llm_router = SmartLLMRouter()
            self.smart_llm_router.setup_default_models(self.config.api_keys or {})
        if HybridRouter:
            self.hybrid_router = HybridRouter(
                model_connector=self.smart_llm_router
            )

        # 3. Tool & Knowledge Layer
        logger.info("  🛠️ Setting up tools and knowledge...")
        if ToolEngine and self.smart_llm_router:
            self.tool_engine = ToolEngine(model_connector=self.smart_llm_router)
            try:
                self.tool_engine.registry.get_default_tools()
            except Exception as e:
                logger.warning(f"Tool registry load skipped: {e}")
        if HybridRAG:
            try:
                self.hybrid_rag = HybridRAG(
                    embedding_model=self.config.embedding_model,
                    reranker_model=self.config.reranker_model
                )
            except Exception as e:
                logger.warning(f"HybridRAG skipped: {e}")

        # 4. Agent Layer
        logger.info("  🤖 Setting up agents...")
        if SimplifiedAgentSystem and self.smart_llm_router:
            try:
                self.agent_system = SimplifiedAgentSystem(
                    state_manager=self.state_manager,
                    model_connector=self.smart_llm_router,
                    tool_engine=self.tool_engine,
                    hybrid_router=self.hybrid_router,
                    sandbox=None
                )
            except Exception as e:
                logger.warning(f"Agent system skipped: {e}")

        # 5. Execution Pipeline
        logger.info("  ⚙️ Setting up execution pipeline...")
        if ExecutionPipeline and self.smart_llm_router:
            try:
                self.execution_pipeline = ExecutionPipeline(
                    planner=PlannerAgent(
                        model_connector=self.smart_llm_router,
                        hybrid_router=self.hybrid_router
                    ),
                    executor=ExecutorAgent(
                        tool_registry=self.tool_engine,
                        state_manager=self.state_manager
                    ),
                    validator=AnalystAgent(
                        model_connector=self.smart_llm_router
                    ),
                    compiler=ResponseCompiler(
                        model_connector=self.smart_llm_router
                    ),
                    state_manager=self.state_manager
                )
            except Exception as e:
                logger.warning(f"Execution pipeline skipped: {e}")

        # 6. World OS Components
        logger.info("  🌍 Setting up World OS components...")

        # Microkernel
        if self.config.enable_microkernel and ASIMMicrokernel:
            try:
                logger.info("    🔐 Initializing seL4-inspired Microkernel...")
                self.microkernel = ASIMMicrokernel()
                self.microkernel.start()
            except Exception as e:
                logger.warning(f"Microkernel skipped: {e}")

        # P2P Network
        if self.config.enable_p2p_network and P2PNetwork:
            try:
                logger.info("    🔗 Initializing P2P Network...")
                self.p2p_network = P2PNetwork(
                    host=self.config.p2p_host,
                    port=self.config.p2p_port,
                    bootstrap_nodes=self.config.p2p_bootstrap_nodes or []
                )
                await self.p2p_network.start()
            except Exception as e:
                logger.warning(f"P2P Network skipped: {e}")
        
        # DePIN Connectors
        if self.config.enable_depin:
            logger.info("    📡 Initializing DePIN Connectors...")
            try:
                if UplinkConnector:
                    self.uplink_connector = UplinkConnector(api_key=self.config.uplink_api_key)
                    await self.uplink_connector.connect()
                if DaylightConnector:
                    self.daylight_connector = DaylightConnector(api_key=self.config.daylight_api_key)
                    await self.daylight_connector.connect()
                if DIMOConnector:
                    self.dimo_connector = DIMOConnector(api_key=self.config.dimo_api_key)
                    await self.dimo_connector.connect()
            except Exception as e:
                logger.warning(f"DePIN connectors skipped: {e}")

        # Resource-Based Economy
        if self.config.enable_rbe and RBEAlgorithm:
            try:
                logger.info("    💰 Initializing Resource-Based Economy...")
                self.rbe_algorithm = RBEAlgorithm()
            except Exception as e:
                logger.warning(f"RBE skipped: {e}")

        # Mythos Security Scanner
        if self.config.enable_mythos and MythosScanner:
            try:
                logger.info("    🛡️ Initializing Mythos Security Scanner...")
                self.mythos_scanner = MythosScanner()
            except Exception as e:
                logger.warning(f"Mythos scanner skipped: {e}")

        # 7. Universal OS Components
        logger.info("  🌐 Setting up Universal OS components...")

        if self.config.enable_universal_gateway and APIGateway and GatewayConfig:
            try:
                logger.info("    🚪 Initializing Universal API Gateway...")
                gateway_config = GatewayConfig(
                    port=self.config.gateway_port,
                    host=self.config.gateway_host,
                    enable_rate_limiting=self.config.gateway_enable_rate_limiting
                )
                self.api_gateway = APIGateway(gateway_config)
            except Exception as e:
                logger.warning(f"API Gateway skipped: {e}")

        if self.config.enable_digital_twins and get_digital_twin_system:
            try:
                logger.info("    👥 Initializing Digital Twin System...")
                self.digital_twin_system = get_digital_twin_system()
            except Exception as e:
                logger.warning(f"Digital Twin skipped: {e}")

        if self.config.enable_life_automation and get_life_protocol_automation:
            try:
                logger.info("    📋 Initializing Life Protocol Automation...")
                self.life_automation = get_life_protocol_automation()
            except Exception as e:
                logger.warning(f"Life Automation skipped: {e}")

        if self.config.enable_global_mesh and get_global_mesh_network:
            try:
                logger.info("    🌐 Initializing Global Mesh Network...")
                self.global_mesh = get_global_mesh_network()
            except Exception as e:
                logger.warning(f"Global Mesh skipped: {e}")

        # 8. AGI, Quantum, and Blockchain Components
        logger.info("  🧠 Setting up AGI, Quantum, and Blockchain components...")

        if self.config.enable_agi and get_agi_core:
            try:
                logger.info("    🧠 Initializing AGI Core...")
                self.agi_core = get_agi_core()
                self.agi_core.state.max_reasoning_depth = self.config.agi_reasoning_depth
                self.agi_core.state.self_improvement_enabled = self.config.agi_self_improvement
                self.agi_core.state.human_oversight_required = self.config.agi_human_oversight
            except Exception as e:
                logger.warning(f"AGI Core skipped: {e}")

        if self.config.enable_quantum and get_quantum_bridge:
            try:
                logger.info("    ⚛️  Initializing Quantum Bridge...")
                self.quantum_bridge = get_quantum_bridge()
                self.quantum_bridge.hybrid_threshold = self.config.quantum_hybrid_threshold
                if self.config.ibm_quantum_api_key and QuantumProvider:
                    self.quantum_bridge.configure_provider(
                        QuantumProvider.IBM, self.config.ibm_quantum_api_key)
                if self.config.amazon_braket_api_key and QuantumProvider:
                    self.quantum_bridge.configure_provider(
                        QuantumProvider.AMAZON_BRAKET, self.config.amazon_braket_api_key)
            except Exception as e:
                logger.warning(f"Quantum Bridge skipped: {e}")

        if self.config.enable_blockchain_identity and get_blockchain_identity_advanced:
            try:
                logger.info("    ⛓️  Initializing Blockchain Identity...")
                self.blockchain_identity = get_blockchain_identity_advanced()
                network_map = {
                    "ethereum": BlockchainNetwork.ETHEREUM if BlockchainNetwork else None,
                    "polygon":  BlockchainNetwork.POLYGON  if BlockchainNetwork else None,
                    "polkadot": BlockchainNetwork.POLKADOT if BlockchainNetwork else None,
                    "solana":   BlockchainNetwork.SOLANA   if BlockchainNetwork else None,
                }
                net = network_map.get(self.config.blockchain_network)
                if net and self.config.ethereum_api_key:
                    self.blockchain_identity.configure_network(net, self.config.ethereum_api_key)
            except Exception as e:
                logger.warning(f"Blockchain Identity skipped: {e}")
        
        self._initialized = True
        logger.info("✅ New ASIMNEXUS Universal World OS Architecture initialized successfully!")
        logger.info("   (18 components: 9 original + 5 World OS + 4 Universal OS + 3 Advanced)")
    
    async def process(self, user_request: str, 
                     context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process user request through the new architecture.
        
        Flow:
        1. Hybrid Router classifies intent
        2. Smart LLM Router selects appropriate model
        3. Simplified Agent System (3 agents) processes request
        4. Tool Engine selects tools with category filtering
        5. Hybrid RAG provides knowledge if needed
        6. Validation layer ensures output quality
        7. Result is cached for future use
        """
        if not self._initialized:
            await self.initialize()
        
        import time
        start_time = time.time()
        
        request_id = f"req_{hash(user_request) % 100000:05d}"
        
        try:
            # Step 1: Intent Classification (Hybrid Router)
            route_decision = await self.hybrid_router.route(user_request)
            
            # Step 2: Select LLM Model (Smart Router)
            complexity = self._estimate_complexity(user_request, route_decision)
            model = self.smart_llm_router.get_model_for_task(
                user_request, 
                complexity=complexity
            )
            
            # Step 3: Check Cache
            cache_key = f"{route_decision.intent.value}:{hash(user_request) % 1000000}"
            cached_result = await self.cache_manager.get('llm_response', cache_key)
            
            if cached_result:
                return {
                    "request_id": request_id,
                    "response": cached_result,
                    "source": "cache",
                    "intent": route_decision.intent.value,
                    "model": model.name if model else "cache",
                    "total_time_ms": (time.time() - start_time) * 1000
                }
            
            # Step 4: Process with Simplified Agent System
            agent_result = await self.agent_system.process(user_request, context)
            
            # Step 5: Store in Cache
            if agent_result.get('success'):
                await self.cache_manager.set(
                    'llm_response', 
                    cache_key, 
                    agent_result['response'],
                    ttl=600
                )
            
            # Step 6: Log stats
            total_time = (time.time() - start_time) * 1000
            
            return {
                "request_id": request_id,
                "response": agent_result['response'],
                "success": agent_result['success'],
                "source": "processed",
                "intent": route_decision.intent.value,
                "method": route_decision.method,
                "model": model.name if model else "unknown",
                "confidence": route_decision.confidence,
                "execution_details": {
                    "plan": agent_result.get('plan'),
                    "results": agent_result.get('results'),
                    "validation": agent_result.get('validation')
                },
                "total_time_ms": total_time,
                "cache_stats": self.cache_manager.get_stats()
            }
            
        except Exception as e:
            return {
                "request_id": request_id,
                "response": f"Error processing request: {str(e)}",
                "success": False,
                "error": str(e),
                "total_time_ms": (time.time() - start_time) * 1000
            }
    
    async def query_knowledge(self, query: str, top_k: int = 5) -> Dict:
        """Query knowledge base using Hybrid RAG."""
        if not self._initialized:
            await self.initialize()
        
        # Check cache
        cache_key = f"rag:{hash(query) % 1000000}"
        cached = await self.cache_manager.get('rag_search', cache_key)
        
        if cached:
            return cached
        
        # Perform hybrid search
        result = await self.hybrid_rag.query(query, top_k)
        
        # Cache result
        await self.cache_manager.set('rag_search', cache_key, result, ttl=600)
        
        return result
    
    async def select_tool(self, query: str, 
                         intent: Optional[str] = None) -> Dict:
        """Select best tool for query with category filtering."""
        if not self._initialized:
            await self.initialize()
        
        if not intent:
            # Infer intent from query
            route = await self.hybrid_router.route(query)
            intent = route.intent.value
        
        selection = await self.tool_engine.select_and_prepare(query, intent)
        
        return {
            "tool_name": selection.tool_name,
            "confidence": selection.confidence,
            "reasoning": selection.reasoning,
            "parameters": selection.parameters,
            "alternatives": selection.alternatives
        }
    
    async def get_stats(self) -> Dict:
        """Get comprehensive system statistics."""
        stats = {
            "cache": self.cache_manager.get_stats() if self.cache_manager else None,
            "llm_cost": self.smart_llm_router.cost_tracker.get_stats() if self.smart_llm_router else None,
            "state_manager": await self.state_manager.get_stats() if self.state_manager else None,
            "world_os": {}
        }
        
        # World OS stats
        if self.microkernel:
            stats["world_os"]["microkernel"] = {
                "processes": len(self.microkernel.process_manager.processes),
                "capabilities": len(self.microkernel.capability_manager.capabilities),
                "running": self.microkernel.running
            }
        
        if self.p2p_network:
            stats["world_os"]["p2p_network"] = self.p2p_network.get_status()
        
        if self.uplink_connector:
            stats["world_os"]["uplink"] = self.uplink_connector.get_network_stats()
        
        if self.daylight_connector:
            stats["world_os"]["daylight"] = self.daylight_connector.get_network_stats()
        
        if self.dimo_connector:
            stats["world_os"]["dimo"] = self.dimo_connector.get_network_stats()
        
        if self.rbe_algorithm:
            stats["world_os"]["rbe"] = {
                "resources": self.rbe_algorithm.get_resource_status(),
                "demands": self.rbe_algorithm.get_demand_status(),
                "equilibrium_score": self.rbe_algorithm.calculate_equilibrium_score()
            }
        
        if self.mythos_scanner:
            stats["world_os"]["mythos"] = self.mythos_scanner.get_scan_summary()
        
        # Universal OS stats
        stats["universal_os"] = {}
        
        if self.api_gateway:
            stats["universal_os"]["api_gateway"] = {
                "request_count": self.api_gateway.request_count,
                "error_count": self.api_gateway.error_count,
                "routes": len(self.api_gateway.routes),
                "services": len(self.api_gateway.services)
            }
        
        if self.digital_twin_system:
            stats["universal_os"]["digital_twins"] = {
                "total_twins": len(self.digital_twin_system.twins)
            }
        
        if self.life_automation:
            stats["universal_os"]["life_automation"] = {
                "total_tasks": len(self.life_automation.tasks),
                "pending_tasks": len(self.life_automation.get_pending_tasks())
            }
        
        if self.global_mesh:
            stats["universal_os"]["global_mesh"] = self.global_mesh.get_network_status()
        
        # AGI, Quantum, and Blockchain stats
        stats["advanced_components"] = {}
        
        if self.agi_core:
            stats["advanced_components"]["agi"] = self.agi_core.get_stats()
        
        if self.quantum_bridge:
            stats["advanced_components"]["quantum"] = self.quantum_bridge.get_stats()
        
        if self.blockchain_identity:
            stats["advanced_components"]["blockchain_identity"] = self.blockchain_identity.get_stats()
        
        return stats
    
    def _estimate_complexity(self, request: str, route: RouteDecision) -> str:
        """Estimate request complexity for model selection."""
        # Simple heuristics
        word_count = len(request.split())
        
        if word_count < 10 and route.confidence > 0.9:
            return "simple"
        elif word_count > 50 or route.intent in [IntentType.CODEBASE_QUERY, IntentType.AUTOMATION]:
            return "complex"
        else:
            return "medium"
    
    async def shutdown(self):
        """Shutdown all components gracefully."""
        logger.info("🛑 Shutting down ASIMNEXUS World OS...")
        
        # Shutdown World OS components
        if self.p2p_network:
            logger.info("  🔗 Shutting down P2P Network...")
            await self.p2p_network.stop()
        
        if self.microkernel:
            logger.info("  🔐 Shutting down Microkernel...")
            self.microkernel.stop()
        
        if self.uplink_connector:
            await self.uplink_connector.disconnect()
        
        if self.daylight_connector:
            await self.daylight_connector.disconnect()
        
        if self.dimo_connector:
            await self.dimo_connector.disconnect()
        
        self._initialized = False
        logger.info("✅ ASIMNEXUS World OS shutdown complete!")
    
    # World OS Helper Methods
    async def scan_security(self, directory: str) -> Dict:
        """Run Mythos security scanner on directory."""
        if not self.mythos_scanner:
            return {"error": "Mythos scanner not enabled"}
        
        return self.mythos_scanner.scan_directory(directory)
    
    async def auto_patch_security(self) -> Dict:
        """Auto-patch all detected vulnerabilities."""
        if not self.mythos_scanner:
            return {"error": "Mythos scanner not enabled"}
        
        return self.mythos_scanner.auto_patch_all()
    
    async def add_p2p_peer(self, peer_id: str, address: tuple) -> bool:
        """Add peer to P2P network."""
        if not self.p2p_network:
            return False
        
        return self.p2p_network.add_peer(peer_id, address)
    
    async def send_p2p_message(self, to_peer: str, message: str) -> bool:
        """Send message via P2P network."""
        if not self.p2p_network:
            return False
        
        from .network.p2p_network import NetworkMessage
        msg = NetworkMessage(
            from_peer=self.p2p_network.node_id,
            to_peer=to_peer,
            message_type="chat",
            payload={"message": message}
        )
        return await self.p2p_network.send_message(msg)
    
    # Universal OS Helper Methods
    def create_digital_twin(
        self,
        legal_name: str,
        date_of_birth,
        nationality: str,
        gender=None
    ):
        """Create a digital twin"""
        if not self.digital_twin_system:
            return {"error": "Digital twin system not enabled"}
        
        from .digital_twin_system import Gender
        if gender is None:
            gender = Gender.PREFER_NOT_TO_SAY
        
        twin = self.digital_twin_system.create_twin(
            legal_name=legal_name,
            date_of_birth=date_of_birth,
            nationality=nationality,
            gender=gender
        )
        
        # Auto-schedule life protocols
        if self.life_automation:
            self.life_automation.auto_schedule_for_twin(twin.identity.twin_id)
        
        return {
            "twin_id": twin.identity.twin_id,
            "legal_name": twin.identity.legal_name,
            "created_at": twin.created_at
        }
    
    def get_digital_twin(self, twin_id: str):
        """Get digital twin by ID"""
        if not self.digital_twin_system:
            return {"error": "Digital twin system not enabled"}
        
        twin = self.digital_twin_system.get_twin(twin_id)
        if not twin:
            return {"error": "Twin not found"}
        
        return self.digital_twin_system.get_twin_summary(twin_id)
    
    def register_api_route(self, path: str, method: str, handler, auth_required: bool = True):
        """Register an API route with the gateway"""
        if not self.api_gateway:
            return {"error": "API gateway not enabled"}
        
        from .universal_api_gateway import APIRoute
        route = APIRoute(
            path=path,
            method=method,
            handler=handler,
            auth_required=auth_required
        )
        
        self.api_gateway.register_route(route)
        return {"success": True, "route": path}


# Backwards compatibility wrapper
class ASIMNEXUSFacade:
    """
    Facade providing backwards-compatible interface to new architecture.
    
    Drop-in replacement for old ASIMNEXUS class.
    """
    
    def __init__(self, config: Optional[ASIMConfig] = None):
        self._new_system = NewASIMNEXUS(config)
        self._initialized = False
    
    async def initialize(self):
        """Initialize the system."""
        await self._new_system.initialize()
        self._initialized = True
    
    async def chat(self, message: str, session_id: Optional[str] = None) -> str:
        """
        Backwards-compatible chat interface.
        
        Returns just the response string (not full dict).
        """
        result = await self._new_system.process(message, {"session_id": session_id})
        return result.get('response', 'No response')
    
    async def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute a specific tool."""
        tool = self._new_system.tool_engine.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool {tool_name} not found"}
        
        # Execute via agent system
        return await self._new_system.agent_system.executor._execute_general(
            {"tool": tool_name, **parameters}
        )
    
    async def get_system_status(self) -> Dict:
        """Get system status."""
        return await self._new_system.get_stats()


# Convenience function for quick usage
async def quick_process(request: str, 
                       api_keys: Optional[Dict[str, str]] = None) -> str:
    """
    Quick one-liner to process a request.
    
    Usage:
        response = await quick_process("Summarize this code")
        logger.info(response)
    """
    config = ASIMConfig(api_keys=api_keys or {})
    asim = NewASIMNEXUS(config)
    await asim.initialize()
    
    result = await asim.process(request)
    return result.get('response', 'No response')


# Example usage
if __name__ == "__main__":
    async def demo():
        """Demonstrate the new architecture with World OS components."""
        logger.info("=" * 60)
        logger.info("ASIMNEXUS World OS Demo")
        logger.info("=" * 60)
        
        # Initialize
        config = ASIMConfig(
            enable_microkernel=True,
            enable_p2p_network=True,
            enable_depin=True,
            enable_rbe=True,
            enable_mythos=True
        )
        asim = NewASIMNEXUS(config)
        await asim.initialize()
        
        # Demo requests
        demo_requests = [
            "scan my computer",
            "read the file main.py",
            "find authentication code",
            "what is the weather today?",
        ]
        
        for request in demo_requests:
            logger.info(f"\n📝 Request: {request}")
            result = await asim.process(request)
            logger.info(f"🤖 Response: {result['response'][:100]}...")
            logger.info(f"📊 Intent: {result.get('intent')} (confidence: {result.get('confidence', 0):.2f})")
            logger.info(f"⏱️ Time: {result['total_time_ms']:.0f}ms")
            logger.info(f"💾 Source: {result.get('source', 'unknown')}")
        
        # Show World OS stats
        logger.info("\n" + "=" * 60)
        logger.info("World OS Statistics")
        logger.info("=" * 60)
        stats = await asim.get_stats()
        
        logger.info("\n🔐 Microkernel:")
        if stats['world_os'].get('microkernel'):
            mk = stats['world_os']['microkernel']
            logger.info(f"  Processes: {mk['processes']}")
            logger.info(f"  Capabilities: {mk['capabilities']}")
            logger.info(f"  Running: {mk['running']}")
        
        logger.info("\n🔗 P2P Network:")
        if stats['world_os'].get('p2p_network'):
            p2p = stats['world_os']['p2p_network']
            logger.info(f"  Node ID: {p2p['node_id'][:16]}...")
            logger.info(f"  Peers: {p2p['peers']}")
        
        logger.info("\n📡 DePIN Connectors:")
        if stats['world_os'].get('uplink'):
            logger.info(f"  Uplink: {stats['world_os']['uplink']['total_nodes']} nodes")
        if stats['world_os'].get('daylight'):
            logger.info(f"  Daylight: {stats['world_os']['daylight']['total_devices']} devices")
        if stats['world_os'].get('dimo'):
            logger.info(f"  DIMO: {stats['world_os']['dimo']['total_vehicles']} vehicles")
        
        logger.info("\n💰 Resource-Based Economy:")
        if stats['world_os'].get('rbe'):
            rbe = stats['world_os']['rbe']
            logger.info(f"  Equilibrium Score: {rbe['equilibrium_score']:.2f}")
        
        logger.info("\n🛡️ Mythos Scanner:")
        if stats['world_os'].get('mythos'):
            mythos = stats['world_os']['mythos']
            logger.info(f"  Total Vulnerabilities: {mythos['total_vulnerabilities']}")
            logger.info(f"  Patches Generated: {mythos['patches_generated']}")
        
        # Shutdown
        await asim.shutdown()
    
    # Run demo
    asyncio.run(demo())
