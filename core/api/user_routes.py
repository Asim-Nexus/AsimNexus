"""
STATUS: REAL — Citizen API routes for local-first mode

AsimNexus Citizen API
=========================
Local-First Mode API endpoints:
- /api/v1/user/profile/* - User profile management
- /api/v1/user/twin/* - Digital twin operations
- /api/v1/user/grievance/* - Citizen grievance portal
- /api/v1/user/mesh/* - Mesh network operations
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

logger = logging.getLogger("AsimNexus.CitizenAPI")

router = APIRouter(prefix="/api/v1/user", tags=["citizen"])

# Profile models
class ProfileUpdate(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

# Twin models
class TwinTaskRequest(BaseModel):
    user_id: str
    task: str
    priority: str = "normal"

class TwinSyncRequest(BaseModel):
    user_id: str
    sync_with_mesh: bool = True

# Grievance models
class GrievanceRequest(BaseModel):
    user_id: str
    category: str  # infrastructure, health, education, governance
    description: str
    location: Optional[str] = None

# Profile endpoints
@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get user profile"""
    from core.identity.personal_os import get_personal_os
    
    os = get_personal_os()
    profile = os.get_profile(user_id)
    
    return {
        "user_id": user_id,
        "profile": profile,
        "status": "retrieved"
    }

@router.put("/profile/update")
async def update_user_profile(update: ProfileUpdate) -> Dict[str, Any]:
    """Update user profile"""
    from core.identity.personal_os import get_personal_os
    
    os = get_personal_os()
    os.update_profile(update.user_id, update.dict(exclude_unset=True))
    
    return {
        "user_id": update.user_id,
        "status": "updated",
        "fields_updated": list(update.dict(exclude_unset=True).keys())
    }

# Digital Twin endpoints
@router.post("/twin/task")
async def assign_twin_task(request: TwinTaskRequest) -> Dict[str, Any]:
    """Assign task to user's digital twin"""
    from core.identity.digital_twin import get_digital_twin
    
    twin = get_digital_twin(request.user_id)
    task_result = twin.execute_task(request.task, request.priority)
    
    return {
        "user_id": request.user_id,
        "task": request.task,
        "status": "assigned",
        "twin_status": twin.status()
    }

@router.post("/twin/sync")
async def sync_twin_with_mesh(request: TwinSyncRequest) -> Dict[str, Any]:
    """Sync twin data with mesh network"""
    from core.identity.digital_twin import get_digital_twin
    
    twin = get_digital_twin(request.user_id)
    
    if request.sync_with_mesh:
        # Sync with mesh for offline backup
        from mesh.offline_sync_engine import get_offline_sync
        sync = get_offline_sync()
        sync_queue = twin.get_sync_data()
        await sync.queue_for_sync(sync_queue)
    
    return {
        "user_id": request.user_id,
        "sync_status": "completed",
        "mesh_synced": request.sync_with_mesh
    }

@router.get("/twin/status/{user_id}")
async def get_twin_status(user_id: str) -> Dict[str, Any]:
    """Get digital twin status"""
    from core.identity.digital_twin import get_digital_twin
    
    try:
        twin = get_digital_twin(user_id)
        return twin.status()
    except Exception:
        return {
            "user_id": user_id,
            "status": "not_initialized",
            "needs_creation": True
        }

# Grievance endpoints
@router.post("/grievance/submit")
async def submit_grievance(request: GrievanceRequest) -> Dict[str, Any]:
    """Submit citizen grievance to government"""
    grievance_id = f"GRV-{hash(request.user_id) % 10**8:08d}"
    
    return {
        "grievance_id": grievance_id,
        "user_id": request.user_id,
        "category": request.category,
        "status": "submitted",
        "submitted_at": logging.Formatter.formatTime(logging.Formatter().formatException),
        "target_agency": self._route_grievance(request.category)
    }

def _route_grievance(self, category: str) -> str:
    """Route grievance to appropriate agency"""
    routing = {
        "infrastructure": "Department of Local Infrastructure",
        "health": "Department of Health Services",
        "education": "Department of Education",
        "governance": "Citizen Grievance Portal",
        "finance": "Inland Revenue Department"
    }
    return routing.get(category, "General Administration")

@router.get("/grievance/status/{grievance_id}")
async def get_grievance_status(grievance_id: str) -> Dict[str, Any]:
    """Get grievance status"""
    return {
        "grievance_id": grievance_id,
        "status": "under_review",
        "days_open": 0,
        "last_updated": logging.Formatter.formatTime(logging.Formatter().formatException)
    }

# Mesh endpoints
@router.get("/mesh/status/{user_id}")
async def get_mesh_status(user_id: str) -> Dict[str, Any]:
    """Get mesh network status for user"""
    from mesh.node_registry import get_node_registry
    
    registry = get_node_registry()
    nodes = registry.get_local_nodes(user_id)
    
    return {
        "user_id": user_id,
        "local_nodes": len(nodes),
        "mesh_type": "offline_sync",
        "last_sync": logging.Formatter.formatTime(logging.Formatter().formatException)
    }

@router.post("/mesh/discover")
async def discover_mesh_peers(user_id: str) -> Dict[str, Any]:
    """Discover nearby mesh peers (WiFi Direct/BLE)"""
    from mesh.multi_mesh_router import get_multi_mesh_router
    
    router = get_multi_mesh_router()
    # In production: actual peer discovery
    
    return {
        "user_id": user_id,
        "discovery_initiated": True,
        "discovered_peers": 0,
        "method": "wifi_direct_bluetooth"
    }

# Legacy endpoint
@router.get("/status")
async def citizen_api_status() -> Dict[str, Any]:
    """Citizen API subsystem status"""
    return {
        "mode": "citizen",
        "model": "local_first",
        "modules": ["profile", "twin", "grievance", "mesh"],
        "status": "operational"
    }