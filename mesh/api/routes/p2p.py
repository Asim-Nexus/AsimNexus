#!/usr/bin/env python3
"""
STATUS: NEW — P2P API Routes
P2P Mesh Network API Endpoints
=============================
Real P2P WebSocket connections का लागि API।
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

try:
    from mesh.p2p_transport import P2PTransport, p2p_transport
except ImportError:
    P2PTransport = None
    p2p_transport = None

router = APIRouter(prefix="/api/v1/mesh", tags=["mesh"])


class PeerConnectRequest(BaseModel):
    hostname: str
    port: int


@router.post("/connect")
async def mesh_connect(request: PeerConnectRequest):
    """P2P peer सँग जडान गर्ने।"""
    if not p2p_transport:
        return {"success": False, "error": "P2P transport not available"}

    result = await p2p_transport.connect_to_peer(
        request.hostname, request.port
    )
    return {"success": result}


@router.get("/peers")
async def mesh_peers():
    """Connected P2P peers को list।"""
    if not p2p_transport:
        return {"success": False, "peers": [], "error": "P2P transport not available"}

    return {"success": True, "peers": [p.__dict__ for p in p2p_transport.get_peers()]}


@router.get("/status")
async def mesh_status():
    """P2P network अवस्था।"""
    return {
        "node_id": p2p_transport.node_id if p2p_transport else "not_started",
        "running": p2p_transport._running if p2p_transport else False,
        "websockets_available": P2PTransport is not None,
    }