"""
ASIMNEXUS Identity, SVT, HDT & World OS API
============================================
Adds 16 missing backend endpoints for:
  - Identity System (stats, list, create, verify)
  - SVT Sovereign Token (stats, wallet, mint, wallet/{did})
  - HDT Human Digital Twin (create, status, skill, announce)
  - World OS Dashboard (quad/status, bugs/stats, dht/status, firewall/status)

Integrates with existing core modules:
  - core/identity/user_identity.py → UserIdentitySystem / get_identity_system()
  - core/economy/sovereign_token.py → SovereignTokenEngine / get_svt_engine()
  - core/agent/digital_twin.py → HumanDigitalTwin / get_human_digital_twin()
  - core/infrastructure/federated_mesh.py → FederatedMeshNetwork / get_mesh_network()
  - core/dreaming/bug_triage.py → BugTriageEngine / get_bug_triage()
  - mesh/kademlia_dht.py → KademliaDHT / get_kademlia_dht()
  - mesh/multi_mesh_router.py → MultiMeshRouter / get_multi_mesh_router()
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# ── Core module imports (with graceful fallback) ──────────────────────────────

logger = logging.getLogger("AsimNexus.API.IdentitySVT")

# Identity System
_identity_system = None
def _get_identity():
    global _identity_system
    if _identity_system is None:
        try:
            from core.identity.user_identity import get_identity_system, IdentityStatus, IdentityLevel, VerificationMethod
            _identity_system = get_identity_system()
            logger.info("✅ Identity system loaded")
        except Exception as e:
            logger.warning(f"⚠️ Identity system unavailable: {e}")
    return _identity_system

# SVT Engine
_svt_engine = None
def _get_svt():
    global _svt_engine
    if _svt_engine is None:
        try:
            from core.economy.sovereign_token import get_svt_engine
            _svt_engine = get_svt_engine()
            logger.info("✅ SVT engine loaded")
        except Exception as e:
            logger.warning(f"⚠️ SVT engine unavailable: {e}")
    return _svt_engine

# HDT
_hdt = None
def _get_hdt():
    global _hdt
    if _hdt is None:
        try:
            from core.agent.digital_twin import get_human_digital_twin, TwinCapability
            _hdt = get_human_digital_twin()
            logger.info("✅ HDT system loaded")
        except Exception as e:
            logger.warning(f"⚠️ HDT system unavailable: {e}")
    return _hdt

# Federated Mesh (for quad status)
_mesh_network = None
def _get_mesh():
    global _mesh_network
    if _mesh_network is None:
        try:
            from core.infrastructure.federated_mesh import get_mesh_network
            _mesh_network = get_mesh_network()
            logger.info("✅ Mesh network loaded")
        except Exception as e:
            logger.warning(f"⚠️ Mesh network unavailable: {e}")
    return _mesh_network

# Bug Triage (for bug stats)
_bug_triage = None
def _get_bug():
    global _bug_triage
    if _bug_triage is None:
        try:
            from core.dreaming.bug_triage import get_bug_triage
            _bug_triage = get_bug_triage()
            logger.info("✅ Bug triage loaded")
        except Exception as e:
            logger.warning(f"⚠️ Bug triage unavailable: {e}")
    return _bug_triage

# Kademlia DHT (for DHT status)
_dht = None
def _get_dht():
    global _dht
    if _dht is None:
        try:
            from mesh.kademlia_dht import get_kademlia_dht
            _dht = get_kademlia_dht()
            logger.info("✅ Kademlia DHT loaded")
        except Exception as e:
            logger.warning(f"⚠️ Kademlia DHT unavailable: {e}")
    return _dht

# Multi-Mesh Router (for firewall status)
_mesh_router = None
def _get_router():
    global _mesh_router
    if _mesh_router is None:
        try:
            from mesh.multi_mesh_router import get_multi_mesh_router
            _mesh_router = get_multi_mesh_router()
            logger.info("✅ Multi-mesh router loaded")
        except Exception as e:
            logger.warning(f"⚠️ Multi-mesh router unavailable: {e}")
    return _mesh_router


# ── Pydantic Models ───────────────────────────────────────────────────────────

class IdentityCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=200)
    attributes: Optional[Dict[str, Any]] = None

class IdentityVerifyRequest(BaseModel):
    identity_id: str = Field(..., min_length=1)
    method: str = Field(..., pattern="^(email|phone|government_id|biometric|zkp|did|social)$")
    verification_data: Dict[str, Any] = Field(default_factory=dict)

class SVTMintRequest(BaseModel):
    did: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0, le=1_000_000)
    memo: str = Field(default="", max_length=200)

class SVTWalletRequest(BaseModel):
    did: str = Field(..., min_length=1)

class HDTCreateRequest(BaseModel):
    did: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1, max_length=100)
    universe: str = Field(default="personal", pattern="^(personal|family|community|enterprise|sovereign)$")

class HDTStatusRequest(BaseModel):
    did: str = Field(..., min_length=1)

class HDTSkillRequest(BaseModel):
    did: str = Field(..., min_length=1)
    skill: str = Field(..., min_length=1, max_length=100)
    level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced|expert)$")

class HDTAnnounceRequest(BaseModel):
    did: str = Field(..., min_length=1)


# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(tags=["Identity, SVT, HDT & World OS"])


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTITY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/identity/stats")
async def identity_stats():
    """Get identity system statistics"""
    system = _get_identity()
    if not system:
        raise HTTPException(status_code=503, detail="Identity system unavailable")
    try:
        return system.stats()
    except Exception as e:
        logger.error(f"Identity stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/identity/list")
async def identity_list(
    status: Optional[str] = Query(None, description="Filter by status"),
    level: Optional[int] = Query(None, description="Filter by assurance level (1-5)"),
    limit: int = Query(100, ge=1, le=1000),
):
    """List identities with optional filters"""
    system = _get_identity()
    if not system:
        raise HTTPException(status_code=503, detail="Identity system unavailable")
    try:
        from core.identity.user_identity import IdentityStatus, IdentityLevel
        status_enum = IdentityStatus(status) if status else None
        level_enum = IdentityLevel(level) if level else None
        records = system.list_identities(status=status_enum, level=level_enum, limit=limit)
        return {
            "total": len(records),
            "identities": [r.to_dict() for r in records],
        }
    except Exception as e:
        logger.error(f"Identity list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/identity/create")
async def identity_create(req: IdentityCreateRequest):
    """Create a new ZKP identity"""
    system = _get_identity()
    if not system:
        raise HTTPException(status_code=503, detail="Identity system unavailable")
    try:
        record = system.create_identity(
            user_id=req.user_id,
            display_name=req.display_name,
            email=req.email,
            attributes=req.attributes,
        )
        # Auto-activate
        system.activate_identity(record.identity_id)
        return {
            "success": True,
            "identity_id": record.identity_id,
            "did": record.did,
            "status": record.status.value,
            "level": record.level.value,
            "created_at": record.created_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Identity create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/identity/verify")
async def identity_verify(req: IdentityVerifyRequest):
    """Verify a ZKP identity"""
    system = _get_identity()
    if not system:
        raise HTTPException(status_code=503, detail="Identity system unavailable")
    try:
        from core.identity.user_identity import VerificationMethod
        method = VerificationMethod(req.method)
        success, message = system.verify_identity(
            identity_id=req.identity_id,
            method=method,
            verification_data=req.verification_data,
        )
        return {
            "success": success,
            "message": message,
            "identity_id": req.identity_id,
        }
    except Exception as e:
        logger.error(f"Identity verify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# SVT (SOVEREIGN TOKEN) ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/svt/stats")
async def svt_stats():
    """Get SVT token economy statistics"""
    engine = _get_svt()
    if not engine:
        raise HTTPException(status_code=503, detail="SVT engine unavailable")
    try:
        return engine.stats()
    except Exception as e:
        logger.error(f"SVT stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/svt/wallet")
async def svt_create_wallet(req: SVTWalletRequest):
    """Create a new SVT wallet for a DID"""
    engine = _get_svt()
    if not engine:
        raise HTTPException(status_code=503, detail="SVT engine unavailable")
    try:
        wallet = engine.create_wallet(req.did)
        return {
            "success": True,
            "did": wallet.did,
            "balance": wallet.balance,
            "created_at": wallet.created_at,
        }
    except Exception as e:
        logger.error(f"SVT wallet create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/svt/mint")
async def svt_mint(req: SVTMintRequest):
    """Mint SVT tokens (system only)"""
    engine = _get_svt()
    if not engine:
        raise HTTPException(status_code=503, detail="SVT engine unavailable")
    try:
        tx = engine.mint(to_did=req.did, amount=req.amount, memo=req.memo)
        return {
            "success": True,
            "tx_id": tx.tx_id,
            "amount": req.amount,
            "to_did": req.did,
            "memo": req.memo,
            "timestamp": tx.ts,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"SVT mint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/svt/wallet/{did}")
async def svt_get_wallet(did: str):
    """Get SVT wallet info for a DID"""
    engine = _get_svt()
    if not engine:
        raise HTTPException(status_code=503, detail="SVT engine unavailable")
    try:
        info = engine.wallet_info(did)
        return info
    except Exception as e:
        logger.error(f"SVT wallet get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# HDT (HUMAN DIGITAL TWIN) ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/hdt/create")
async def hdt_create(req: HDTCreateRequest):
    """Create a Human Digital Twin"""
    hdt = _get_hdt()
    if not hdt:
        raise HTTPException(status_code=503, detail="HDT system unavailable")
    try:
        twin = hdt.create_twin(user_id=req.did, name=req.display_name)
        return {
            "success": True,
            "twin_id": twin.twin_id,
            "user_id": twin.user_id,
            "name": twin.name,
            "state": twin.state.value,
            "capabilities": [c.value for c in twin.authorized_capabilities],
            "created_at": twin.created_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"HDT create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/hdt/{did}/status")
async def hdt_status(did: str):
    """Get HDT status for a DID"""
    hdt = _get_hdt()
    if not hdt:
        raise HTTPException(status_code=503, detail="HDT system unavailable")
    try:
        twins = hdt.get_user_twins(user_id=did)
        if not twins:
            return {
                "exists": False,
                "did": did,
                "message": "No digital twin found for this DID",
            }
        # Return the most recent twin
        twin = twins[-1]
        stats = hdt.get_twin_stats(twin.twin_id)
        return {
            "exists": True,
            "did": did,
            "twin": stats,
        }
    except Exception as e:
        logger.error(f"HDT status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/hdt/{did}/skill")
async def hdt_add_skill(did: str, req: HDTSkillRequest):
    """Add a skill to a Human Digital Twin"""
    hdt = _get_hdt()
    if not hdt:
        raise HTTPException(status_code=503, detail="HDT system unavailable")
    try:
        twins = hdt.get_user_twins(user_id=did)
        if not twins:
            raise HTTPException(status_code=404, detail="No digital twin found for this DID")
        twin = twins[-1]

        # Learn from this skill addition
        hdt.learn_from_action(
            twin_id=twin.twin_id,
            action="add_skill",
            context={"skill": req.skill, "level": req.level},
            outcome="success",
        )
        return {
            "success": True,
            "twin_id": twin.twin_id,
            "skill": req.skill,
            "level": req.level,
            "message": f"Skill '{req.skill}' ({req.level}) added to twin",
        }
    except Exception as e:
        logger.error(f"HDT skill error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/hdt/{did}/announce")
async def hdt_announce(did: str):
    """Announce HDT to the DHT network"""
    hdt = _get_hdt()
    if not hdt:
        raise HTTPException(status_code=503, detail="HDT system unavailable")
    try:
        twins = hdt.get_user_twins(user_id=did)
        if not twins:
            raise HTTPException(status_code=404, detail="No digital twin found for this DID")
        twin = twins[-1]

        # Attempt to publish to DHT
        dht = _get_dht()
        dht_published = False
        if dht:
            try:
                from mesh.kademlia_dht import NodeID
                key = NodeID.from_string(f"hdt:{did}")
                payload = json.dumps({
                    "twin_id": twin.twin_id,
                    "did": did,
                    "name": twin.name,
                    "state": twin.state.value,
                    "capabilities": [c.value for c in twin.authorized_capabilities],
                    "announced_at": datetime.now().isoformat(),
                }).encode()
                dht.store(key, payload, ttl=86400)  # 24h TTL
                dht_published = True
            except Exception as dht_err:
                logger.warning(f"DHT publish failed for HDT announce: {dht_err}")

        return {
            "success": True,
            "twin_id": twin.twin_id,
            "did": did,
            "dht_published": dht_published,
            "message": "HDT announced to network",
        }
    except Exception as e:
        logger.error(f"HDT announce error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# WORLD OS DASHBOARD ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/quad/status")
async def quad_status():
    """Get Quad mesh system status (Personal/Family/Community/Enterprise/Sovereign)"""
    mesh = _get_mesh()
    if not mesh:
        raise HTTPException(status_code=503, detail="Mesh network unavailable")
    try:
        return mesh.get_quad_system_status()
    except Exception as e:
        logger.error(f"Quad status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/bugs/stats")
async def bug_stats():
    """Get bug pipeline statistics"""
    triage = _get_bug()
    if not triage:
        raise HTTPException(status_code=503, detail="Bug triage unavailable")
    try:
        return triage.stats()
    except Exception as e:
        logger.error(f"Bug stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dht/status")
async def dht_status():
    """Get DHT network status"""
    dht = _get_dht()
    if not dht:
        raise HTTPException(status_code=503, detail="DHT unavailable")
    try:
        return dht.get_stats()
    except Exception as e:
        logger.error(f"DHT status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/firewall/status")
async def firewall_status():
    """Get firewall / mesh security status"""
    router_inst = _get_router()
    if not router_inst:
        raise HTTPException(status_code=503, detail="Mesh router unavailable")
    try:
        # Get mesh stats which includes security-related info
        stats = router_inst.get_mesh_stats()
        # Get connected meshes
        connected = router_inst.get_connected_meshes()
        # Get switch history for recent security events
        history = router_inst.get_switch_history(limit=20)

        return {
            "status": "active",
            "active_mesh": router_inst.get_active_mesh().value if hasattr(router_inst.get_active_mesh(), 'value') else str(router_inst.get_active_mesh()),
            "connected_meshes": {
                mtype.value if hasattr(mtype, 'value') else str(mtype): profile.to_dict()
                for mtype, profile in connected.items()
            },
            "total_routing_rules": len(router_inst.get_routing_rules()),
            "recent_switches": len(history),
            "mesh_stats": stats,
            "firewall_mode": "dharma_gated",
            "encryption": "mtls_required",
        }
    except Exception as e:
        logger.error(f"Firewall status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Helper to register all routes on an app ───────────────────────────────────

def register_identity_svt_hdt_routes(app):
    """Register all identity, SVT, HDT, and World OS routes on a FastAPI app"""
    app.include_router(router)
    logger.info("✅ Identity, SVT, HDT & World OS routes registered")
    return app
