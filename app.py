#!/usr/bin/env python3
"""
AsimNexus = World OS - Unified Backend
======================================
Single entry point for all AsimNexus functionality.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("AsimNexus")

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Config
try:
    from asim_config import get_config
    config = get_config()
except ImportError:
    config = None

# Core module imports
try:
    from core.consensus_engine import ConsensusEngine
except ImportError:
    class ConsensusEngine:
        def get_stats(self): return {"total_rounds": 0}
        def start_round(self, **kwargs): return None

try:
    from core.compliance_engine import ComplianceEngine
except ImportError:
    class ComplianceEngine:
        def check_decision(self, sector, is_public_decision=False): 
            class R: verdict = type('V', (), {'value': 'allow'})()
            return R()
        def get_stats(self): return {"total_sectors": 8}

try:
    from core.entity_bridge import EntityBridge
except ImportError:
    EntityBridge = None

try:
    from core.security_layer import ZKPProof, HSMService
except ImportError:
    ZKPProof = HSMService = None

# Import LLM gateway
try:
    from connectors.unified_llm_gateway import unified_llm_gateway, LLMProvider, UnifiedCompletionRequest
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Import World Clones for system prompts
try:
    from core.founder_clones.world_clones import WORLD_CLONE_CONFIGS, CloneRole
    CLONES_AVAILABLE = True
except ImportError:
    CLONES_AVAILABLE = False
    WORLD_CLONE_CONFIGS = []

# Import connectors (unified location)
try:
    from connectors.nepal.government import (
        MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS,
        UNIVERSITIES, SCHOOLS
    )
    from connectors.health.hospitals import HOSPITALS
    from connectors.local.palikas import PALIKAS
    from connectors.tourism.hotels import HOTELS
    CONNECTORS_AVAILABLE = True
except ImportError:
    CONNECTORS_AVAILABLE = False
    MINISTRIES = PROVINCES = DISTRICTS = BANKS = ISPS = UNIVERSITIES = SCHOOLS = {}
    HOSPITALS = PALIKAS = HOTELS = {}

# Initialize Orchestrator
try:
    from core.orchestrator.orchestrator import Orchestrator
    orchestrator = Orchestrator()
except Exception as e:
    print(f"Failed to load Orchestrator: {e}")
    orchestrator = None

# Create FastAPI app
app = FastAPI(
    title="AsimNexus World OS",
    version="1.0.0",
    description="Nepal National Digital Operating System - Citizen/Company/Government API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# Register JWT/HSM Auth Middleware
from core.security.auth_middleware import AuthMiddleware
app.add_middleware(AuthMiddleware)

# Register Monitoring & Security Middlewares (Phase 3)
from core.monitoring_middleware import PrometheusMonitoringMiddleware
from core.security_headers_middleware import SecurityHeadersMiddleware
app.add_middleware(PrometheusMonitoringMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


# Initialize LLM gateway on startup
# Initialize LLM gateway on startup
llm_gateway = None
local_llm = None
redis_mgr = None

@app.on_event("startup")
async def init_llm():
    global llm_gateway, local_llm, redis_mgr
    if LLM_AVAILABLE:
        llm_gateway = unified_llm_gateway
        await llm_gateway.initialize()
    
    # Register monitoring middleware singleton
    from core.monitoring_middleware import set_monitoring, PrometheusMonitoringMiddleware
    # Find and register the monitoring middleware instance
    for m in app.user_middleware:
        if isinstance(m, PrometheusMonitoringMiddleware):
            await set_monitoring(m)
    
    # Initialize Redis if available
    try:
        from core.redis_manager import AsimRedisManager
        redis_mgr = AsimRedisManager.get_instance()
        redis_mgr.redis.ping()
    except Exception as e:
        print(f"Redis not available: {e}")
    
    # Initialize local LLM if model exists
    try:
        from connectors.local_llm_connector import LocalLLM
        from pathlib import Path
        model_path = Path("models/Qwen3-4B-distill-deepseek-opus-gemini-Q8_0.gguf")
        if model_path.exists():
            local_llm = await LocalLLM.get_instance()
    except Exception as e:
        print(f"Local LLM init skipped: {e}")
        
    # Auto-ingest RAG data on startup
    try:
        from knowledge.rag_engine import RAGEngine
        from pathlib import Path
        rag = RAGEngine()
        data_dir = Path("data")
        if data_dir.exists():
            print("Starting Auto-Ingest for RAG...")
            for file_path in data_dir.glob("*.txt"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                        chunks = rag.chunk_document(text, {"source": file_path.name})
                        rag.add_documents(chunks)
                        print(f"Ingested {file_path.name} into Neutron Star")
                except Exception as e:
                    print(f"Failed to ingest {file_path.name}: {e}")
    except Exception as e:
        print(f"RAG init skipped: {e}")

@app.on_event("shutdown")
async def close_llm():
    global llm_gateway
    if llm_gateway:
        await llm_gateway.close()

# â”€â”€â”€ WebSocket Endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

from core.api.ws_routes import router as ws_router
app.include_router(ws_router)

# â”€â”€â”€ Route Modules â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Import and register all domain-specific route modules.
# Each module has an init_*(app_globals) function that receives shared state.

from routes import register_routes

# Build shared state dict for route modules
_app_globals = {
    "orchestrator": orchestrator,
    "llm_gateway": llm_gateway,
    "local_llm": local_llm,
    "redis_mgr": redis_mgr,
    "LLM_AVAILABLE": LLM_AVAILABLE,
    "CLONES_AVAILABLE": CLONES_AVAILABLE,
    "WORLD_CLONE_CONFIGS": WORLD_CLONE_CONFIGS,
    "MINISTRIES": MINISTRIES,
    "PROVINCES": PROVINCES,
    "DISTRICTS": DISTRICTS,
    "BANKS": BANKS,
    "ISPS": ISPS,
    "UNIVERSITIES": UNIVERSITIES,
    "SCHOOLS": SCHOOLS,
    "HOSPITALS": HOSPITALS,
    "PALIKAS": PALIKAS,
    "HOTELS": HOTELS,
    "ConsensusEngine": ConsensusEngine,
    "ComplianceEngine": ComplianceEngine,
    "EntityBridge": EntityBridge,
    "ZKPProof": ZKPProof,
    "HSMService": HSMService,
}

# Initialize all route modules with shared state
from routes.nepal import init_nepal_data
from routes.chat import init_chat
from routes.auth import init_auth
from routes.marketplace import init_marketplace
from routes.mesh import init_mesh
from routes.os_control import init_os_control
from routes.identity import init_identity
from routes.consensus import init_consensus
from routes.analytics import init_analytics
from routes.memory import init_memory
from routes.mcp import init_mcp
from routes.healing import init_healing
from routes.universal import init_universal
from routes.sovereignty import init_sovereignty
from routes.infrastructure import init_infrastructure
from routes.finance import init_finance
from routes.government import init_government
from routes.security import init_security

init_nepal_data(_app_globals)
init_chat(_app_globals)
init_auth(_app_globals)
init_marketplace(_app_globals)
init_mesh(_app_globals)
init_os_control(_app_globals)
init_identity(_app_globals)
init_consensus(_app_globals)
init_analytics(_app_globals)
init_memory(_app_globals)
init_mcp(_app_globals)
init_healing(_app_globals)
init_universal(_app_globals)
init_sovereignty(_app_globals)
init_infrastructure(_app_globals)
init_finance(_app_globals)
init_government(_app_globals)
init_security(_app_globals)

# Register all route routers with the app
register_routes(app)

logger.info(f"âœ… All route modules initialized and registered ({len(app.routes)} total routes)")

# â”€â”€â”€ Root Endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.get("/")
async def root():
    return {"message": "AsimNexus World OS", "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/system/info")
async def system_info():
    return {"os": "Windows", "python": "3.11", "llm": "Qwen3-4B"}


# Phase 3: Monitoring & Metrics Endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    from core.monitoring_middleware import monitoring_instance
    if monitoring_instance:
        m = monitoring_instance.get_metrics()
        return {"status": "ok", "data": m}
    return {"status": "ok", "data": {"request_count": {}, "error_count": {}, "latency_avg": {}, "active_users": 0}}

# Shared brain processing logic (used by both /api/brain/process and /api/agent/run)
async def _process_brain_message(message: str, clone: str = "auto", mode: str = "personal"):
    """Shared logic for processing brain messages."""
    import json
    import re
    
    # Check for tool command pattern: "tool.name: {params}"
    tool_match = re.match(r'^(\w+(?:\.\w+)+)\s*:\s*(\{.*\})?', message.strip())
    if tool_match:
        tool_id = tool_match.group(1)
        params_str = tool_match.group(2) or "{}"
        try:
            from os_control.os_tool_executor import get_os_tool_executor
            executor = get_os_tool_executor()
            params = json.loads(params_str)
            result = await executor.execute(tool_id, params, "AutoModeAgent", "chat_user")
            return {
                "response": f"ðŸŒŒ **Asim**\n\n**Tool Result for `{tool_id}`:**\n```\n{json.dumps(result, indent=2)}\n```",
                "source": "asim_nexus",
                "clone_used": clone
            }
        except Exception as e:
            return {
                "response": f"ðŸŒŒ **Asim**\n\nError executing tool `{tool_id}`: {str(e)}",
                "source": "asim_nexus",
                "clone_used": clone
            }
    
    # Get clone system prompt
    system_prompt = None
    if CLONES_AVAILABLE and clone != "auto" and clone != "general":
        for cc in WORLD_CLONE_CONFIGS:
            clone_id = clone.lower().replace(" ", "_").replace("-", "_")
            role_id = cc.role.value.lower().replace(" ", "_").replace("-", "_")
            if clone_id == role_id or cc.role.value.lower() == clone.lower():
                system_prompt = cc.system_prompt
                break
                
    # Fetch RAG context
    rag_context = ""
    try:
        from knowledge.rag_engine import RAGEngine
        from knowledge.cosmos.black_hole import BlackHole
        rag = RAGEngine()
        black_hole = BlackHole()
        retrieved = rag.retrieve(message, top_k=3)
        filtered = black_hole.filter(message, retrieved, threshold=0.2)
        if filtered:
            context_texts = [f"- {c.get('text', '')}" for c in filtered]
            rag_context = "\n".join(context_texts)
    except Exception as e:
        pass
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if rag_context:
        messages.append({"role": "system", "content": f"Relevant AsimNexus Knowledge (Nepal Context):\n{rag_context}\nUse this if relevant to the user query."})
    messages.append({"role": "user", "content": message})
    
    # Priority 1: Local llama-cpp LLM (offline-first)
    if local_llm and local_llm.llm:
        try:
            response = await local_llm.generate(messages, max_tokens=500, temperature=0.7)
            if response:
                # Always identify as Asim, not the model name
                return {
                    "response": f"ðŸŒŒ **Asim**\n\n{response}",
                    "source": "asim_nexus",
                    "clone_used": clone
                }
        except Exception as e:
            pass
    
    # Priority 2: LLM gateway (online providers)
    use_llm = False
    if llm_gateway and llm_gateway.providers:
        for provider, cfg in llm_gateway.providers.items():
            if provider != LLMProvider.LOCAL and cfg.api_key:
                use_llm = True
                break
    
    if use_llm and llm_gateway:
        try:
            request = UnifiedCompletionRequest(
                messages=messages,
                provider=LLMProvider.LOCAL,
                max_tokens=500,
                temperature=0.7
            )
            response = await llm_gateway.complete(request)
            if response and response.content:
                # Always identify as Asim
                return {
                    "response": f"ðŸŒŒ **Asim**\n\n{response.content}",
                    "source": "asim_nexus",
                    "clone_used": clone
                }
        except Exception as e:
            pass
    
    # Priority 3: Smart fallback
    return _smart_response(message, clone, system_prompt, rag_context)



# â”€â”€â”€ Fallback Auth Manager (used when orchestrator is unavailable) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class _FallbackAuthManager:
    """Minimal auth manager that handles basic login/refresh without DB."""
    def login(self, username: str, password: str) -> dict:
        if username and password:
            return {"success": True, "token": "fallback_token", "user": {"id": username, "email": f"{username}@local"}}
        raise HTTPException(status_code=401, detail="Invalid credentials")
    def refresh_token(self, token: str) -> dict:
        return {"success": True, "token": "refreshed_fallback_token"}

auth_manager = _FallbackAuthManager()



def _smart_response(message: str, clone: str, system_prompt: str = None, rag_context: str = None):
    """Fallback smart responses without LLM - Asim Nexus AI Assistant"""
    lower_msg = message.lower().strip()
    
    if system_prompt and "tech architect" in system_prompt.lower():
        response = f"ðŸŒŒ **Asim**\n\n{message}\n\nà¤® à¤¤à¤ªà¤¾à¤ˆà¤‚à¤•à¥‹ Asim à¤¹à¥à¤ â€” à¤¤à¤•à¤¨à¥€à¤•à¥€ à¤¸à¤²à¥à¤²à¤¾à¤¹à¤•à¤¾à¤°à¥€à¥¤ à¤•à¥‡ à¤® à¤¤à¤ªà¤¾à¤ˆà¤‚à¤²à¤¾à¤ˆ à¤•à¤¸à¤°à¥€ à¤®à¤¦à¥à¤¦à¤¤ à¤—à¤°à¥à¤¨ à¤¸à¤•à¥à¤›à¥?"
    elif system_prompt and "health" in system_prompt.lower():
        response = f"ðŸŒŒ **Asim**\n\n{message}\n\nà¤¸à¥à¤µà¤¾à¤¸à¥à¤¥à¥à¤¯ à¤¸à¤®à¥à¤¬à¤¨à¥à¤§à¥€ à¤•à¥à¤°à¤¾ à¤¤à¤¥à¥à¤¯à¤¾à¤™à¥à¤•à¤¹à¤°à¥‚ à¤µà¤¾ à¤ªà¥à¤°à¤¶à¥à¤¨à¤¹à¤°à¥‚ à¤¬à¤¤à¤¾à¤‰à¤¨à¥à¤¹à¥‹à¤¸à¥à¥¤"
    elif system_prompt and "finance" in system_prompt.lower():
        response = f"ðŸŒŒ **Asim**\n\n{message}\n\nà¤® à¤¤à¤ªà¤¾à¤ˆà¤‚à¤•à¥‹ à¤µà¤¿à¤¤à¥à¤¤à¥€à¤¯ à¤¸à¤²à¥à¤²à¤¾à¤¹à¤•à¤¾à¤°à¥€ à¤¹à¥à¤à¥¤ à¤µà¤¿à¤¤à¥à¤¤à¥€à¤¯ à¤¸à¤²à¥à¤²à¤¾à¤¹à¤•à¤¾ à¤²à¤¾à¤—à¤¿à¥¤"
    elif "hey" in lower_msg or "hello" in lower_msg or "hi" in lower_msg or "à¤¨à¤®à¤¸à¥à¤¤à¥‡" in lower_msg:
        response = "ðŸŒŒ **Asim**\n\nNamaste! à¤® à¤¤à¤ªà¤¾à¤ˆà¤‚à¤•à¥‹ Asim à¤¹à¥à¤ â€” à¤¤à¤ªà¤¾à¤ˆà¤‚à¤•à¥‹ à¤µà¤¿à¤¶à¥à¤µ OS à¤¸à¤¹à¤¯à¥‹à¤—à¥€à¥¤\n\nà¤•à¤¸à¤°à¥€ à¤®à¤¦à¥à¤¦à¤¤ à¤—à¤°à¥à¤¨ à¤¸à¤•à¥à¤›à¥? ðŸ¥ Health Â· ðŸ’¼ Work Â· ðŸ¤– Agents Â· ðŸŒ Mesh Â· âš–ï¸ Governance Â· ðŸ’° Wallet"
    elif "health" in lower_msg or "swasthya" in lower_msg or "à¤¸à¥à¤µà¤¾à¤¸à¥à¤¥à¥à¤¯" in lower_msg:
        response = "ðŸŒŒ **Asim**\n\n**à¤¸à¥à¤µà¤¾à¤¸à¥à¤¥à¥à¤¯ à¤¡à¥à¤¯à¤¾à¤¸à¤¬à¥‹à¤°à¥à¤¡**\n\nâ€¢ à¤°à¤•à¤¤à¤šà¤¾à¤ª: 120/80 mmHg (à¤¸à¤¾à¤§à¤¾à¤°à¤£)\nâ€¢ à¤¹à¥ƒà¤¦à¤¯à¤—à¤¤à¤¿: 72 bpm (à¤µà¤¿à¤¶à¥à¤°à¤¾à¤®)\nâ€¢ à¤¨à¤¿à¤¦à¥à¤°à¤¾: 7.5 à¤˜à¤£à¥à¤Ÿà¤¾\nâ€¢ à¤†à¤œà¤•à¥‹ à¤šà¤°à¤£: 8,432\n\nà¤¸à¤¿à¤«à¤¾à¤°à¤¿à¤¸à¤¹à¤°à¥‚: 2L à¤ªà¤¾à¤¨à¥€, 30 à¤®à¤¿à¤¨à¥‡à¤Ÿ à¤®à¥‡à¤¡à¤¿à¤Ÿà¥‡à¤¸à¤¨"
    elif "work" in lower_msg or "à¤•à¤¾à¤®" in lower_msg or "à¤•à¤¾à¤®" in lower_msg:
        response = "ðŸŒŒ **Asim**\n\n**à¤•à¤¾à¤® à¤®à¥‹à¤¡**\n\nâ€¢ à¤…à¤¨à¥à¤¬à¤¨à¥à¤§à¤¹à¤°à¥‚: à¥© à¤¸à¤•à¥à¤°à¤¿à¤¯\nâ€¢ à¤®à¤¾à¤‡à¤²à¥‹: à¥¨/à¥« à¤ªà¥‚à¤°à¤¾\nâ€¢ à¤†à¤®à¤¦à¤¨à¥€: $20,800 à¤¯à¤¸ à¤®à¤¹à¤¿à¤¨à¤¾\nâ€¢ à¤à¤œà¥‡à¤¨à¥à¤Ÿà¤¹à¤°à¥‚ à¤•à¤¾à¤® à¤—à¤°à¤¿à¤°à¤¹à¥‡à¤•à¤¾ à¤›à¤¨à¥"
    elif "mesh" in lower_msg or "à¤œà¤¾à¤²à¥‹" in lower_msg or "à¤œà¤¾à¤²" in lower_msg:
        response = "ðŸŒŒ **Asim**\n\n**à¤®à¥‡à¤· à¤œà¤¾à¤² à¤œà¤¾à¤¨à¤•à¤¾à¤°à¥€**\n\nâ€¢ à¤¨à¥‹à¤¡à¤¹à¤°à¥‚: à¥© à¤œà¤¡à¤¾à¤¨ à¤­à¤à¤•à¤¾\nâ€¢ à¤†à¤œ: à¥ªà¥« MB à¤…à¤ªà¤²à¥‹à¤¡, à¥§à¥¨à¥® MB à¤¡à¤¾à¤‰à¤¨à¤²à¥‹à¤¡\nâ€¢ à¤¸à¥à¤¥à¤¿à¤¤à¤¿: à¤…à¤¨à¤²à¤¾à¤‡à¤¨ à¤° à¤¸à¤¿à¤™à¥à¤• à¤­à¤à¤•à¥‹"
    elif "agent" in lower_msg or "à¤•à¥à¤²à¥‹à¤¨" in lower_msg or "hire" in lower_msg or "à¤à¤œà¥‡à¤¨à¥à¤Ÿ" in lower_msg:
        response = "ðŸŒŒ **Asim**\n\n**AI à¤à¤œà¥‡à¤¨à¥à¤Ÿà¤¹à¤°à¥‚**\n\nà¤‰à¤ªà¤²à¤¬à¥à¤§: Tech Architect, Data Engineer, Security Sentinel, Health Sage\nà¤•à¤®à¤¾à¤£à¥à¤¡à¤¹à¤°à¥‚: /hire Â· /pause Â· /budget"
    elif rag_context:
        # Provide knowledge from RAG if available!
        response = f"ðŸŒŒ **Asim**\n\nà¤¤à¤ªà¤¾à¤ˆà¤‚à¤•à¥‹ à¤ªà¥à¤°à¤¶à¥à¤¨à¤•à¥‹ à¤²à¤¾à¤—à¤¿ à¤®à¥ˆà¤²à¥‡ AsimNexus Knowledge Base (Neutron Star) à¤¬à¤¾à¤Ÿ à¤¯à¥€ à¤œà¤¾à¤¨à¤•à¤¾à¤°à¥€à¤¹à¤°à¥‚ à¤«à¥‡à¤²à¤¾ à¤ªà¤¾à¤°à¥‡à¤•à¥‹ à¤›à¥:\n\n{rag_context}"
    elif message.strip():
        response = f"ðŸŒŒ **Asim**\n\nReceived: {message}\n\nà¤® à¤¤à¤ªà¤¾à¤ˆà¤‚à¤²à¤¾à¤ˆ à¤•à¤¸à¤°à¥€ à¤®à¤¦à¥à¤¦à¤¤ à¤—à¤°à¥à¤¨ à¤¸à¤•à¥à¤›à¥? ðŸ¥ à¤¸à¥à¤µà¤¾à¤¸à¥à¤¥à¥à¤¯ Â· ðŸ’¼ à¤•à¤¾à¤® Â· ðŸŒ à¤®à¥‡à¤· Â· ðŸ¤– à¤à¤œà¥‡à¤¨à¥à¤Ÿà¤¹à¤°à¥‚ Â· ðŸ’° à¤µà¤¾à¤²à¥‡à¤Ÿ"
    else:
        response = "ðŸŒŒ **Asim**\n\nNamaste! à¤® à¤¤à¤ªà¤¾à¤ˆà¤‚à¤•à¥‹ Asim à¤¹à¥à¤à¥¤ à¤•à¥‡ à¤¬à¤¤à¤¾à¤‰à¤¨ à¤šà¤¾à¤¹à¤¨à¥à¤¹à¥à¤¨à¥à¤›?"
    
    return {
        "response": response,
        "source": "asim_nexus",
        "clone_used": clone
    }

# All route handlers have been moved to routes/ modules.
# See routes/__init__.py for registration and individual modules for implementations.
# TODO: Replace archived refs (_memory) with app.py equivalents
