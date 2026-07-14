"""
Nexus Connector API Routes — Unified Bridge for Government (51%), Companies (49%), Citizens (Local-First)
=========================================================================================================

Provides REST API endpoints for:
  - Session management (create, switch mode, end)
  - Action processing (all stakeholder modes)
  - Cross-consent management
  - Mode switching
  - Status and statistics

All endpoints integrate with the Nexus Connector, Enhanced Federated Identity,
and the existing governance layers.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── Lazy Imports ────────────────────────────────────────────────────────────
# These are imported at module level for type hints, but the actual instances
# are loaded lazily in init_nexus().

try:
    from core.nexus_connector import NexusMode, NexusAction, MODE_PERMISSION_MATRIX
    _NEXUS_AVAILABLE = True
except ImportError:
    NexusMode = None
    NexusAction = None
    MODE_PERMISSION_MATRIX = {}
    _NEXUS_AVAILABLE = False

try:
    from core.identity.enhanced_federated_identity import IdentityMode
    _IDENTITY_AVAILABLE = True
except ImportError:
    IdentityMode = None
    _IDENTITY_AVAILABLE = False

# ─── Singleton References (lazy-loaded) ──────────────────────────────────────
_nexus = None
_identity = None


def init_nexus(app_globals: dict) -> None:
    """Initialize nexus routes with app globals."""
    global _nexus, _identity
    try:
        from core.nexus_connector import get_nexus_connector
        _nexus = get_nexus_connector()
        logger.info("Nexus Connector loaded for API routes")
    except Exception as e:
        logger.warning(f"Nexus Connector not available: {e}")
    
    try:
        from core.identity.enhanced_federated_identity import get_enhanced_identity
        _identity = get_enhanced_identity()
        logger.info("Enhanced Federated Identity loaded for API routes")
    except Exception as e:
        logger.warning(f"Enhanced Federated Identity not available: {e}")


# ─── Request/Response Models ─────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    user_id: str
    mode: str = "citizen"
    context: Optional[Dict[str, Any]] = None


class SwitchModeRequest(BaseModel):
    session_id: str
    new_mode: str
    context: Optional[Dict[str, Any]] = None


class ProcessActionRequest(BaseModel):
    user_id: str
    action: str
    payload: Dict[str, Any]
    source_mode: Optional[str] = None
    session_id: Optional[str] = None


class ConsentResponse(BaseModel):
    request_id: str
    approved: bool
    response: Optional[str] = None


class RegisterUserRequest(BaseModel):
    user_id: str
    display_name: str


class SwitchIdentityModeRequest(BaseModel):
    user_id: str
    to_mode: str
    reason: str = "user_request"
    require_approval: bool = False


# ─── Session Endpoints ───────────────────────────────────────────────────────

@router.post("/api/nexus/session/create")
async def create_session(req: CreateSessionRequest):
    """Create a new session for a user in a specific mode."""
    if not _nexus or NexusMode is None:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    try:
        mode = NexusMode(req.mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {req.mode}")
    
    session = _nexus.create_session(
        user_id=req.user_id,
        mode=mode,
        context=req.context,
    )
    return {"status": "ok", "session": session.to_dict()}


@router.post("/api/nexus/session/switch-mode")
async def switch_mode(req: SwitchModeRequest):
    """Switch a session to a different mode."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    try:
        new_mode = NexusMode(req.new_mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {req.new_mode}")
    
    session = _nexus.switch_mode(
        session_id=req.session_id,
        new_mode=new_mode,
        context=req.context,
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "ok", "session": session.to_dict()}


@router.get("/api/nexus/session/{session_id}")
async def get_session(session_id: str):
    """Get session details."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    session = _nexus.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "ok", "session": session.to_dict()}


@router.get("/api/nexus/user/{user_id}/sessions")
async def get_user_sessions(user_id: str):
    """Get all sessions for a user."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    sessions = _nexus.get_user_sessions(user_id)
    return {
        "status": "ok",
        "user_id": user_id,
        "sessions": [s.to_dict() for s in sessions],
        "active_mode": _nexus.get_user_active_mode(user_id).value if _nexus.get_user_active_mode(user_id) else None,
    }


@router.post("/api/nexus/session/{session_id}/end")
async def end_session(session_id: str):
    """End a session."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    result = _nexus.end_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "ok", "message": "Session ended"}


# ─── Action Endpoints ────────────────────────────────────────────────────────

@router.post("/api/nexus/action")
async def process_action(req: ProcessActionRequest):
    """Process an action through the Nexus Connector."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    try:
        action = NexusAction(req.action)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid action: {req.action}")
    
    source_mode = None
    if req.source_mode:
        try:
            source_mode = NexusMode(req.source_mode)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid source mode: {req.source_mode}")
    
    record = await _nexus.process_action(
        user_id=req.user_id,
        action=action,
        payload=req.payload,
        source_mode=source_mode,
        session_id=req.session_id,
    )
    return {"status": "ok", "action": record.to_dict()}


@router.get("/api/nexus/action/{action_id}")
async def get_action(action_id: str):
    """Get action details."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    action = _nexus._actions.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    return {"status": "ok", "action": action.to_dict()}


# ─── Consent Endpoints ───────────────────────────────────────────────────────

@router.post("/api/nexus/consent/respond")
async def respond_consent(req: ConsentResponse):
    """Respond to a cross-consent request."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    result = _nexus.respond_to_consent(
        request_id=req.request_id,
        approved=req.approved,
        response=req.response,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Consent request not found")
    
    return {"status": "ok", "message": "Consent response recorded"}


@router.get("/api/nexus/consent/pending")
async def get_pending_consents(
    user_id: str = Query(...),
    mode: Optional[str] = Query(None),
):
    """Get all pending consent requests for a user."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    target_mode = None
    if mode:
        try:
            target_mode = NexusMode(mode)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")
    
    requests = _nexus.get_pending_consents(user_id, target_mode)
    return {
        "status": "ok",
        "user_id": user_id,
        "pending_consents": [r.to_dict() for r in requests],
    }


# ─── Identity Endpoints ──────────────────────────────────────────────────────

@router.post("/api/nexus/identity/register")
async def register_user(req: RegisterUserRequest):
    """Register a new user with all mode-specific Digital Twins."""
    if not _identity:
        raise HTTPException(status_code=503, detail="Enhanced Federated Identity not available")
    
    twins = _identity.register_user(
        user_id=req.user_id,
        display_name=req.display_name,
    )
    return {
        "status": "ok",
        "user_id": req.user_id,
        "twins": {k: v.to_dict() for k, v in twins.items()},
    }


@router.post("/api/nexus/identity/switch-mode")
async def switch_identity_mode(req: SwitchIdentityModeRequest):
    """Switch a user's active identity mode."""
    if not _identity:
        raise HTTPException(status_code=503, detail="Enhanced Federated Identity not available")
    
    try:
        from core.identity.enhanced_federated_identity import IdentityMode
        to_mode = IdentityMode(req.to_mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {req.to_mode}")
    
    success, error, switch = _identity.switch_mode(
        user_id=req.user_id,
        to_mode=to_mode,
        reason=req.reason,
        require_approval=req.require_approval,
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "status": "ok",
        "switch": switch.to_dict() if switch else None,
    }


@router.get("/api/nexus/identity/{user_id}/twins")
async def get_user_twins(user_id: str):
    """Get all Digital Twins for a user."""
    if not _identity:
        raise HTTPException(status_code=503, detail="Enhanced Federated Identity not available")
    
    twins = _identity.get_all_twins(user_id)
    return {
        "status": "ok",
        "user_id": user_id,
        "twins": {k: v.to_dict() for k, v in twins.items()},
        "active_mode": _identity.get_active_mode(user_id),
    }


@router.get("/api/nexus/identity/{user_id}/switch-history")
async def get_switch_history(user_id: str, limit: int = Query(50, ge=1, le=200)):
    """Get mode switch history for a user."""
    if not _identity:
        raise HTTPException(status_code=503, detail="Enhanced Federated Identity not available")
    
    history = _identity.get_mode_switch_history(user_id, limit)
    return {
        "status": "ok",
        "user_id": user_id,
        "switches": [r.to_dict() for r in history],
    }


# ─── Status Endpoints ────────────────────────────────────────────────────────

@router.get("/api/nexus/status")
async def nexus_status():
    """Get Nexus Connector system status."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    return {"status": "ok", "data": _nexus.get_status()}


@router.get("/api/nexus/stats")
async def nexus_stats():
    """Get Nexus Connector comprehensive statistics."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    nexus_stats_data = _nexus.get_stats()
    identity_stats = {}
    if _identity:
        identity_stats = _identity.get_stats()
    
    return {
        "status": "ok",
        "nexus": nexus_stats_data,
        "identity": identity_stats,
    }


@router.get("/api/nexus/modes")
async def list_modes():
    """List all available operational modes."""
    if not _nexus:
        raise HTTPException(status_code=503, detail="Nexus Connector not available")
    
    from core.nexus_connector import NexusMode, NexusAction
    
    modes = []
    for mode in NexusMode:
        permissions = {}
        for action in NexusAction:
            from core.nexus_connector import MODE_PERMISSION_MATRIX
            consent = MODE_PERMISSION_MATRIX.get(mode, {}).get(action)
            if consent:
                permissions[action.value] = consent.value
        modes.append({
            "mode": mode.value,
            "permissions": permissions,
        })
    
    return {"status": "ok", "modes": modes}
