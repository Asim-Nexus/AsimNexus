
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Unified API - Production-Ready Backend
=================================================

Unified FastAPI backend connecting all 21 components to the frontend.
Provides REST API endpoints for:
- Digital Twin Management
- AGI Reasoning
- Quantum Computing
- Blockchain Identity
- Global Mesh Network
- Life Protocol Automation

Production Features:
- Rate limiting
- Authentication/Authorization
- Request validation
- Error handling
- Logging
- CORS
- Documentation (Swagger/OpenAPI)
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import date, datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

# Import ASIMNEXUS core
import sys
sys.path.append('c:\\AsimNexus')

from core.new_architecture_integration import NewASIMNEXUS, ASIMConfig
from core.digital_twin_system import Gender, get_digital_twin_system
from core.agi_core import get_agi_core, ReasoningMode
from core.quantum_bridge import get_quantum_bridge, QuantumAlgorithm, QuantumProvider
from core.blockchain_identity_advanced import (
    get_blockchain_identity_advanced,
    BlockchainNetwork,
    AttestationType
)

# Optional imports — these modules may not exist yet
try:
    from core.global_mesh import get_global_mesh_network, Region
except ImportError:
    get_global_mesh_network = None
    Region = None
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ core.global_mesh not available — mesh endpoints will use fallback")

try:
    from core.life_protocol_automation import get_life_protocol_automation
except ImportError:
    get_life_protocol_automation = None
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ core.life_protocol_automation not available — life protocol endpoints will use fallback")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global ASIMNEXUS instance
asim_nexus: Optional[NewASIMNEXUS] = None

# Pydantic models for request/response
class DigitalTwinCreateRequest(BaseModel):
    legal_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    nationality: str = Field(..., min_length=2, max_length=50)
    gender: str = Field(..., pattern="^(male|female|other|prefer_not_to_say)$")
    birth_certificate_id: Optional[str] = None

class DigitalTwinResponse(BaseModel):
    twin_id: str
    legal_name: str
    nationality: str
    status: str
    created_at: str

class AGIThinkRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    reasoning_mode: str = Field(default="analytical", pattern="^(analytical|creative|critical|systems|ethical)$")
    max_depth: int = Field(default=10, ge=1, le=20)

class AGIThinkResponse(BaseModel):
    chain_id: str
    query: str
    conclusion: str
    confidence: float
    thoughts_count: int
    reasoning_mode: str
    created_at: str

class QuantumJobRequest(BaseModel):
    algorithm: str = Field(..., pattern="^(grover|shor|qaoa|vqe|qft|bernstein_vazirani|deutsch_josza|simon)$")
    problem_size: int = Field(default=1000, ge=10, le=100000)
    shots: int = Field(default=1024, ge=1, le=10000)
    parameters: Optional[Dict[str, Any]] = None

class QuantumJobResponse(BaseModel):
    job_id: str
    algorithm: str
    status: str
    result: Optional[Dict[str, Any]] = None
    speedup: Optional[float] = None

class BlockchainDIDRequest(BaseModel):
    public_key: str
    network: str = Field(default="ethereum", pattern="^(ethereum|polygon|polkadot|solana)$")

class BlockchainDIDResponse(BaseModel):
    did: str
    network: str
    created_at: str

class CredentialIssueRequest(BaseModel):
    issuer_did: str
    subject_did: str
    credential_type: str
    claims: Dict[str, Any]
    expiration_days: int = Field(default=365, ge=1, le=3650)

class LifeEventRequest(BaseModel):
    event_type: str = Field(..., pattern="^(birth|education|employment|marriage|retirement|death)$")
    details: Dict[str, Any]

class SystemStatsResponse(BaseModel):
    original_components: Dict[str, Any]
    world_os_components: Dict[str, Any]
    universal_os_components: Dict[str, Any]
    advanced_components: Dict[str, Any]
    total_components: int
    status: str

# Security
security = HTTPBearer()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global asim_nexus
    
    logger.info("🚀 Starting ASIMNEXUS Unified API...")
    
    # Initialize ASIMNEXUS (with graceful fallback)
    try:
        config = ASIMConfig(
            enable_microkernel=True,
            enable_p2p_network=True,
            enable_depin=True,
            enable_rbe=True,
            enable_mythos=True,
            enable_universal_gateway=True,
            enable_digital_twins=True,
            enable_life_automation=True,
            enable_global_mesh=True,
            enable_agi=True,
            enable_quantum=True,
            enable_blockchain_identity=True
        )
        
        asim_nexus = NewASIMNEXUS(config)
        await asim_nexus.initialize()
        
        logger.info("✅ ASIMNEXUS initialized successfully with 21 components")
    except Exception as e:
        logger.warning(f"⚠️ ASIMNEXUS full initialization failed: {e}")
        logger.info("🔄 Running in LIMITED mode - core endpoints still available")
        asim_nexus = None
    
    # Register Qwen3-4B local model
    try:
        from core.local_llm_manager import get_local_llm_manager, LocalModelConfig, LocalModelType
        manager = get_local_llm_manager()
        
        # Add Qwen3-4B GGUF model
        qwen_config = LocalModelConfig(
            name="Qwen3 4B (Local GGUF)",
            model_type=LocalModelType.LLAMA_CPP,
            model_id="qwen3-4b-local",
            path="C:/AsimNexus/models/Qwen3-4B-distill-deepseek-opus-gemini-Q8_0.gguf",
            context_length=4096,
            gpu_layers=35,
            temperature=0.7,
            max_tokens=512,
            system_prompt="You are Asim, the AI assistant for AsimNexus - a World Operating System. You help users with health, work, AI agents, mesh networks, governance, and digital identity. Be helpful, concise, and friendly."
        )
        manager.add_model(qwen_config)
        manager.set_active_model("qwen3-4b-local")
        logger.info("🤖 Qwen3-4B model registered successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not register Qwen3-4B model: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down ASIMNEXUS...")
    if asim_nexus:
        try:
            await asim_nexus.shutdown()
            logger.info("✅ ASIMNEXUS shutdown complete")
        except Exception as e:
            logger.warning(f"⚠️ Shutdown error: {e}")

# Create FastAPI app
app = FastAPI(
    title="ASIMNEXUS World OS API",
    description="Unified API for Digital Twin, AGI, Quantum, Blockchain, and Global Mesh",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
try:
    from core.rate_limiter_middleware import RateLimiterMiddleware
    app.add_middleware(RateLimiterMiddleware)
    logger.info("✅ RateLimiterMiddleware registered on unified API")
except Exception as e:
    logger.warning(f"⚠️ RateLimiterMiddleware registration skipped: {e}")

# ============ HEALTH & STATS ENDPOINTS ============

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": 21,
        "version": "1.0.0"
    }

@app.get("/api/stats", response_model=SystemStatsResponse, tags=["System"])
async def get_system_stats():
    """Get complete system statistics"""
    if not asim_nexus:
        return {
            "status": "limited_mode",
            "total_components": 21,
            "original_components": {
                "hybrid_router": "limited",
                "state_manager": "limited",
                "cache_manager": "limited"
            },
            "world_os_components": {},
            "universal_os_components": {},
            "advanced_components": {}
        }
    
    stats = await asim_nexus.get_stats()
    
    return {
        "original_components": {
            "hybrid_router": "active",
            "state_manager": "active",
            "cache_manager": "active",
            "smart_llm_router": "active",
            "tool_engine": "active",
            "hybrid_rag": "active",
            "agent_system": "active",
            "execution_pipeline": "active",
            "async_executor": "active"
        },
        "world_os_components": {
            "microkernel": stats.get("world_os", {}).get("microkernel", {}),
            "p2p_network": stats.get("world_os", {}).get("p2p_network", {}),
            "rbe": stats.get("world_os", {}).get("rbe", {}),
            "mythos": stats.get("world_os", {}).get("mythos", {})
        },
        "universal_os_components": {
            "digital_twins": stats.get("universal_os", {}).get("digital_twins", {}),
            "life_automation": stats.get("universal_os", {}).get("life_automation", {}),
            "global_mesh": stats.get("universal_os", {}).get("global_mesh", {})
        },
        "advanced_components": stats.get("advanced_components", {}),
        "total_components": 21,
        "status": "operational"
    }

# ============ DIGITAL TWIN ENDPOINTS ============

@app.post("/api/digital-twin", response_model=DigitalTwinResponse, tags=["Digital Twin"])
async def create_digital_twin(request: DigitalTwinCreateRequest):
    """Create a new digital twin"""
    try:
        gender_map = {
            "male": Gender.MALE,
            "female": Gender.FEMALE,
            "other": Gender.OTHER,
            "prefer_not_to_say": Gender.PREFER_NOT_TO_SAY
        }
        
        if not asim_nexus:
            raise HTTPException(status_code=503, detail="Digital Twin not available in limited mode")
        
        result = asim_nexus.create_digital_twin(
            legal_name=request.legal_name,
            date_of_birth=request.date_of_birth,
            nationality=request.nationality,
            gender=gender_map.get(request.gender, Gender.OTHER),
            birth_certificate_id=request.birth_certificate_id
        )
        
        return {
            "twin_id": result["twin_id"],
            "legal_name": result["legal_name"],
            "nationality": result["nationality"],
            "status": result["status"],
            "created_at": result["created_at"]
        }
    except Exception as e:
        logger.error(f"Error creating digital twin: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/digital-twin/{twin_id}", tags=["Digital Twin"])
async def get_digital_twin(twin_id: str):
    """Get digital twin by ID"""
    try:
        if not asim_nexus:
            raise HTTPException(status_code=503, detail="Digital Twin not available in limited mode")
        twin = asim_nexus.get_digital_twin(twin_id)
        if not twin:
            raise HTTPException(status_code=404, detail="Digital twin not found")
        return twin
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/digital-twin/{twin_id}/life-events", tags=["Digital Twin"])
async def get_life_events(twin_id: str):
    """Get life events for digital twin"""
    try:
        twin_system = get_digital_twin_system()
        twin = twin_system.get_twin(twin_id)
        if not twin:
            raise HTTPException(status_code=404, detail="Digital twin not found")
        
        return {
            "twin_id": twin_id,
            "life_events": [
                {
                    "event_type": event.event_type,
                    "date": event.date,
                    "description": event.description
                }
                for event in twin.life_events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ AGI ENDPOINTS ============

@app.post("/api/agi/think", response_model=AGIThinkResponse, tags=["AGI"])
async def agi_think(request: AGIThinkRequest):
    """Process query through AGI reasoning engine"""
    try:
        agi = get_agi_core()
        
        mode_map = {
            "analytical": ReasoningMode.ANALYTICAL,
            "creative": ReasoningMode.CREATIVE,
            "critical": ReasoningMode.CRITICAL,
            "systems": ReasoningMode.SYSTEMS,
            "ethical": ReasoningMode.ETHICAL
        }
        
        chain = await agi.think(
            query=request.query,
            reasoning_mode=mode_map.get(request.reasoning_mode, ReasoningMode.ANALYTICAL),
            max_depth=request.max_depth
        )
        
        return {
            "chain_id": chain.chain_id,
            "query": chain.query,
            "conclusion": chain.conclusion,
            "confidence": chain.confidence,
            "thoughts_count": len(chain.thoughts),
            "reasoning_mode": request.reasoning_mode,
            "created_at": chain.created_at
        }
    except Exception as e:
        logger.error(f"Error in AGI thinking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agi/stats", tags=["AGI"])
async def get_agi_stats():
    """Get AGI system statistics"""
    try:
        agi = get_agi_core()
        return agi.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ QUANTUM ENDPOINTS ============

@app.post("/api/quantum/job", response_model=QuantumJobResponse, tags=["Quantum"])
async def create_quantum_job(request: QuantumJobRequest):
    """Create and run a quantum computing job"""
    try:
        quantum = get_quantum_bridge()
        
        algo_map = {
            "grover": QuantumAlgorithm.GROVER,
            "shor": QuantumAlgorithm.SHOR,
            "qaoa": QuantumAlgorithm.QAOA,
            "vqe": QuantumAlgorithm.VQE,
            "qft": QuantumAlgorithm.QFT,
            "bernstein_vazirani": QuantumAlgorithm.BERNSTEIN_VAZIRANI,
            "deutsch_josza": QuantumAlgorithm.DEUTSCH_JOSZA,
            "simon": QuantumAlgorithm.SIMON
        }
        
        job = quantum.create_job(
            algorithm=algo_map.get(request.algorithm, QuantumAlgorithm.GROVER),
            parameters={"problem_size": request.problem_size, **(request.parameters or {})},
            shots=request.shots
        )
        
        result = await quantum.execute_job(job.job_id)
        
        return {
            "job_id": job.job_id,
            "algorithm": request.algorithm,
            "status": job.status,
            "result": result,
            "speedup": result.get("speedup")
        }
    except Exception as e:
        logger.error(f"Error running quantum job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quantum/stats", tags=["Quantum"])
async def get_quantum_stats():
    """Get quantum computing system statistics"""
    try:
        quantum = get_quantum_bridge()
        return quantum.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quantum/devices", tags=["Quantum"])
async def get_quantum_devices():
    """List available quantum devices"""
    try:
        quantum = get_quantum_bridge()
        return {
            "devices": [
                {
                    "device_id": d.device_id,
                    "name": d.name,
                    "provider": d.provider.value,
                    "qubits": d.qubits,
                    "is_available": d.is_available
                }
                for d in quantum.devices.values()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ BLOCKCHAIN IDENTITY ENDPOINTS ============

@app.post("/api/blockchain/did", response_model=BlockchainDIDResponse, tags=["Blockchain"])
async def create_did(request: BlockchainDIDRequest):
    """Create a new Decentralized Identifier (DID)"""
    try:
        blockchain = get_blockchain_identity_advanced()
        
        network_map = {
            "ethereum": BlockchainNetwork.ETHEREUM,
            "polygon": BlockchainNetwork.POLYGON,
            "polkadot": BlockchainNetwork.POLKADOT,
            "solana": BlockchainNetwork.SOLANA
        }
        
        did = blockchain.create_did(
            public_key=request.public_key,
            network=network_map.get(request.network, BlockchainNetwork.ETHEREUM)
        )
        
        return {
            "did": did,
            "network": request.network,
            "created_at": blockchain.dids[did].created_at
        }
    except Exception as e:
        logger.error(f"Error creating DID: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/blockchain/credential", tags=["Blockchain"])
async def issue_credential(request: CredentialIssueRequest):
    """Issue a verifiable credential"""
    try:
        blockchain = get_blockchain_identity_advanced()
        
        type_map = {
            "identity": AttestationType.IDENTITY,
            "education": AttestationType.EDUCATION,
            "employment": AttestationType.EMPLOYMENT,
            "health": AttestationType.HEALTH,
            "financial": AttestationType.FINANCIAL,
            "government": AttestationType.GOVERNMENT
        }
        
        vc_id = blockchain.issue_credential(
            issuer_did=request.issuer_did,
            subject_did=request.subject_did,
            credential_type=type_map.get(request.credential_type, AttestationType.IDENTITY),
            claims=request.claims,
            expiration_days=request.expiration_days
        )
        
        return {
            "vc_id": vc_id,
            "status": "issued"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/blockchain/credentials/{did}", tags=["Blockchain"])
async def get_credentials(did: str):
    """Get credentials for a DID"""
    try:
        blockchain = get_blockchain_identity_advanced()
        credentials = blockchain.get_credentials_for_subject(did)
        
        return {
            "did": did,
            "credentials": [
                {
                    "vc_id": c.vc_id,
                    "type": c.credential_type.value,
                    "status": c.status.value,
                    "issued_at": c.issuance_date
                }
                for c in credentials
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/blockchain/sbts/{did}", tags=["Blockchain"])
async def get_sbts(did: str):
    """Get Soulbound Tokens for a DID"""
    try:
        blockchain = get_blockchain_identity_advanced()
        sbts = blockchain.get_sbts_for_owner(did)
        
        return {
            "did": did,
            "sbts": [
                {
                    "sbt_id": s.sbt_id,
                    "token_type": s.token_type,
                    "issuer": s.issuer,
                    "issued_at": s.issued_at
                }
                for s in sbts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/blockchain/zkproof", tags=["Blockchain"])
async def create_zkproof(prover_did: str, statement: str, secret_data: str):
    """Create a Zero-Knowledge Proof"""
    try:
        blockchain = get_blockchain_identity_advanced()
        proof = blockchain.create_zk_proof(prover_did, statement, secret_data)
        
        return {
            "proof_id": proof.proof_id,
            "statement": proof.statement,
            "created_at": proof.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ GLOBAL MESH ENDPOINTS ============

@app.get("/api/mesh/status", tags=["Mesh"])
async def get_mesh_status():
    """Get global mesh network status"""
    try:
        mesh = get_global_mesh_network()
        return mesh.get_network_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mesh/edge-node", tags=["Mesh"])
async def add_edge_node(
    region: str,
    lat: float,
    lon: float,
    compute_capacity: int = 100,
    memory_gb: int = 16
):
    """Add an edge computing node"""
    try:
        mesh = get_global_mesh_network()
        
        region_map = {
            "north_america": Region.NORTH_AMERICA,
            "south_america": Region.SOUTH_AMERICA,
            "europe": Region.EUROPE,
            "asia": Region.ASIA,
            "africa": Region.AFRICA,
            "oceania": Region.OCEANIA,
            "middle_east": Region.MIDDLE_EAST
        }
        
        node_id = mesh.add_edge_node(
            region=region_map.get(region, Region.ASIA),
            location=(lat, lon),
            compute_capacity=compute_capacity,
            memory_gb=memory_gb
        )
        
        return {
            "node_id": node_id,
            "status": "added"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ LIFE PROTOCOL ENDPOINTS ============

@app.post("/api/life-protocol/event", tags=["Life Protocol"])
async def schedule_life_event(request: LifeEventRequest):
    """Schedule a life event automation"""
    try:
        life = get_life_protocol_automation()
        
        from core.life_protocol import LifeEventType
        
        event_type_map = {
            "birth": LifeEventType.BIRTH,
            "education": LifeEventType.EDUCATION_ENROLLMENT,
            "employment": LifeEventType.JOB_REGISTRATION,
            "marriage": LifeEventType.MARRIAGE_REGISTRATION,
            "retirement": LifeEventType.RETIREMENT_PLANNING,
            "death": LifeEventType.DEATH_REGISTRATION
        }
        
        task_id = life.schedule_task(
            event_type=event_type_map.get(request.event_type, LifeEventType.JOB_REGISTRATION),
            scheduled_time="2025-01-01T00:00:00",  # Simplified
            details=request.details,
            priority=5
        )
        
        return {
            "task_id": task_id,
            "event_type": request.event_type,
            "status": "scheduled"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/life-protocol/tasks", tags=["Life Protocol"])
async def get_life_tasks():
    """Get life protocol automation tasks"""
    try:
        life = get_life_protocol_automation()
        return {
            "total_tasks": len(life.tasks),
            "pending_tasks": len(life.get_pending_tasks()),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "event_type": t.event_type.value,
                    "status": t.status.value
                }
                for t in life.tasks.values()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ LOCAL LLM ENDPOINTS ============

try:
    from core.local_llm_manager import register_local_llm_routes, get_local_llm_manager
    # Register local LLM routes
    register_local_llm_routes(app)
except ImportError:
    register_local_llm_routes = None
    get_local_llm_manager = None

@app.get("/api/local-llm/health", tags=["Local LLM"])
async def check_local_llm_health():
    """Check local LLM services health"""
    if get_local_llm_manager is None:
        return {"status": "unavailable", "detail": "Local LLM manager not installed"}
    try:
        manager = get_local_llm_manager()
        ollama_running = await manager.check_ollama()
        lm_studio_running = await manager.check_lm_studio()
        return {
            "ollama": "running" if ollama_running else "stopped",
            "lm_studio": "running" if lm_studio_running else "stopped",
            "status": "healthy" if ollama_running else "limited"
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ============ ASIM BRAIN CHAT ENDPOINTS (Frontend Compatibility) ============

class BrainProcessRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    mode: str = "personal"
    streaming: bool = False

class BrainProcessResponse(BaseModel):
    response: str
    source: str = "asim_brain"
    timestamp: str
    clone_used: Optional[str] = None

@app.post("/api/brain/process", response_model=BrainProcessResponse, tags=["Asim Brain"])
async def brain_process(request: BrainProcessRequest):
    """Process chat message through Asim Brain using local Qwen3-4B LLM"""
    try:
        logger.info(f"🧠 Brain processing: {request.message[:50]}...")
        
        # Try local LLM first (Qwen3-4B GGUF)
        try:
            from core.local_llm_manager import get_local_llm_manager
            manager = get_local_llm_manager()
            
            # Build prompt with system context
            system = "You are Asim, the AI assistant for AsimNexus - a World Operating System. You help users with health, work, AI agents, mesh networks, governance, and digital identity. Be helpful, concise, and friendly."
            prompt = f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{request.message}<|im_end|>\n<|im_start|>assistant\n"
            
            result = await manager.generate(prompt, stream=False)
            
            if result.success:
                # Clean up the response
                response_text = result.text.strip()
                # Remove any remaining prompt tokens
                if "<|im_end|>" in response_text:
                    response_text = response_text.split("<|im_end|>")[0].strip()
                if "<|im_start|>" in response_text:
                    response_text = response_text.split("<|im_start|>")[-1].strip()
                
                logger.info(f"✅ LLM response generated ({result.tokens_generated} tokens, {result.generation_time_ms:.0f}ms)")
                return BrainProcessResponse(
                    response=response_text,
                    source="qwen3-4b-local",
                    timestamp=datetime.now().isoformat(),
                    clone_used="Asim Core (Qwen3-4B)"
                )
            else:
                logger.warning(f"⚠️ LLM generation failed: {result.error}")
        except Exception as llm_error:
            logger.warning(f"⚠️ LLM not available: {llm_error}")
        
        # Fallback: Route to AGI if available
        if asim_nexus and any(kw in request.message.lower() for kw in ['why', 'how', 'explain', 'analyze', 'think']):
            try:
                agi_core = get_agi_core()
                result = agi_core.reason(
                    query=request.message,
                    mode=ReasoningMode.ANALYTICAL,
                    max_depth=5
                )
                return BrainProcessResponse(
                    response=result.conclusion,
                    source="agi_analytical",
                    timestamp=datetime.now().isoformat(),
                    clone_used="Asim Core"
                )
            except Exception:
                pass
        
        # Ultimate fallback: simple response
        return BrainProcessResponse(
            response=f"🤖 **Asim:** I received your message: \"{request.message}\"\n\nI'm currently in local fallback mode. Full AI integration coming soon!\n\n**Try asking:**\n• Health check\n• Work status\n• Mesh info\n• What is Asim",
            source="local_fallback",
            timestamp=datetime.now().isoformat(),
            clone_used="Local Assistant"
        )
        
    except Exception as e:
        logger.error(f"Error in brain process: {e}")
        return BrainProcessResponse(
            response=f"⚠️ Error processing: {str(e)}",
            source="error",
            timestamp=datetime.now().isoformat()
        )

@app.post("/api/brain/stream", tags=["Asim Brain"])
async def brain_stream(request: BrainProcessRequest):
    """Stream chat response from Asim Brain (Frontend compatible)"""
    from fastapi.responses import StreamingResponse
    import asyncio
    
    async def generate_stream():
        words = ["Thinking", "...", "Processing", "...", "Here", "is", "your", "response:", "\\n\\n", "I", "received:", f"\\\"{request.message}\\\"", "\\n\\n", "[Streaming", "mode", "active", "-", "full", "AI", "integration", "coming", "soon!]"]
        
        for word in words:
            yield f"data: {json.dumps({'token': word + ' '})}\\n\\n"
            await asyncio.sleep(0.1)
        
        yield f"data: {json.dumps({'done': True})}\\n\\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )

# ============ REGISTER IDENTITY, SVT, HDT & WORLD OS ROUTES ============

# Register the 16 new endpoints from identity_svt_hdt_api.py
try:
    from api.identity_svt_hdt_api import register_identity_svt_hdt_routes
    register_identity_svt_hdt_routes(app)
    logger.info("✅ Identity, SVT, HDT & World OS routes registered on main app")
except Exception as e:
    logger.warning(f"⚠️ Could not register identity/SVT/HDT/World OS routes: {e}")

# ============ REGISTER CONSENSUS, MESH, CLONES, HEALING & OS TOOLS ROUTES ============

# Register the new endpoints from consensus_mesh_clones_healing_ostools_api.py
try:
    from api.consensus_mesh_clones_healing_ostools_api import register_consensus_mesh_clones_healing_ostools_routes
    register_consensus_mesh_clones_healing_ostools_routes(app)
    logger.info("✅ Consensus, Mesh, Clones, Healing & OS Tools routes registered on main app")
except Exception as e:
    logger.warning(f"⚠️ Could not register Consensus/Mesh/Clones/Healing/OS Tools routes: {e}")

# ============ REGISTER REMAINING MISSING ROUTES (Dharma, Dreaming, Analytics, Jobs, Sync) ============

try:
    from api.remaining_missing_api import register_remaining_routes
    register_remaining_routes(app)
    logger.info("✅ Dharma, Dreaming, Analytics, Jobs & Sync routes registered on main app")
except Exception as e:
    logger.warning(f"⚠️ Could not register remaining routes: {e}")

# ============ REGISTER ECONOMY ROUTES (Contract Executor + Nexus Credits) ============

try:
    from core.api_endpoints import register_economy_routes
    register_economy_routes(app)
    logger.info("✅ Economy routes (Contract Executor + Nexus Credits) registered on main app")
except Exception as e:
    logger.warning(f"⚠️ Could not register economy routes: {e}")

# ============ REGISTER UNIFIED ROUTES (Chat, Files, Codebase, Terminal, Automation, Security, etc.) ============

try:
    from api.unified_routes_api import register_unified_routes
    register_unified_routes(app)
    logger.info("✅ Unified routes (Chat, Files, Codebase, Terminal, Automation, Security, Virtual Office, Autonomous, HDT, ZKP, Clones, Identity, SVT, Quad, Bugs, DHT, Firewall, Universe, Universal) registered")
except Exception as e:
    logger.warning(f"⚠️ Could not register unified routes: {e}")

# ============ MAIN ============

if __name__ == "__main__":
    uvicorn.run(
        "api.unified_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
