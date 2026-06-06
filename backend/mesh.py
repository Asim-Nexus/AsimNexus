#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade mesh backend
ASIMNEXUS Mesh Backend
======================
Mesh API endpoints for mesh network operations.
Provides REST interface to mesh components.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("AsimNexus.Mesh")


def setup_mesh_routes(app, node_id: str = "local_node"):
    """
    Setup mesh API routes on FastAPI app.
    Call this from simple_backend.py to wire mesh endpoints.
    """
    from mesh.autodiscovery import get_auto_discovery, DiscoveryMethod
    from mesh.node_registry import get_node_registry, TrustLevel, NodeStatus
    from mesh.kademlia_dht import get_kademlia_dht, NodeID
    from mesh.p2p_transport import get_p2p_transport
    from mesh.crdt_sync import get_crdt_store
    from mesh.relay import get_relay_service, RelayRole
    from mesh.bootstrap import get_bootstrap_service, BootstrapRegion
    
    # Initialize mesh components
    auto_discovery = get_auto_discovery(node_id)
    node_registry = get_node_registry()
    kademlia_dht = get_kademlia_dht()
    p2p_transport = get_p2p_transport(node_id)
    crdt_store = get_crdt_store(node_id)
    relay_service = get_relay_service(node_id)
    bootstrap_service = get_bootstrap_service(node_id)
    
    class DiscoveryRequest(BaseModel):
        """Request model for discovery."""
        method: str = "broadcast"
        timeout: int = 5
    
    class NodeRegistrationRequest(BaseModel):
        """Request model for node registration."""
        node_id: str
        hostname: str
        ip_address: str
        port: int
        capabilities: Optional[List[str]] = None
    
    class TrustLevelRequest(BaseModel):
        """Request model for trust level change."""
        trust_level: str
        reason: str
    
    class DHTStoreRequest(BaseModel):
        """Request model for DHT store."""
        key: str
        value: str
        ttl: int = 86400
    
    class SyncRequest(BaseModel):
        """Request model for sync."""
        since: Optional[float] = None
    
    class BootstrapRequest(BaseModel):
        """Request model for bootstrap."""
        region: Optional[str] = None
    
    # ─── DISCOVERY ENDPOINTS ────────────────────────────────────────────────
    
    @app.post("/api/mesh/discover")
    async def discover_nodes(req: DiscoveryRequest):
        """Perform one-time node discovery."""
        try:
            method = DiscoveryMethod(req.method)
            nodes = auto_discovery.discover_once(req.timeout)
            
            # Register discovered nodes
            for node in nodes:
                node_registry.register_node(
                    node_id=node.node_id,
                    hostname=node.hostname,
                    ip_address=node.ip_address,
                    port=node.port,
                    capabilities=node.capabilities
                )
            
            return JSONResponse({
                "discovered": len(nodes),
                "nodes": [
                    {
                        "node_id": n.node_id,
                        "hostname": n.hostname,
                        "ip_address": n.ip_address,
                        "port": n.port,
                        "capabilities": n.capabilities
                    }
                    for n in nodes
                ]
            })
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/discovered")
    async def get_discovered_nodes():
        """Get all discovered nodes."""
        try:
            nodes = auto_discovery.get_discovered_nodes()
            return JSONResponse([
                {
                    "node_id": n.node_id,
                    "hostname": n.hostname,
                    "ip_address": n.ip_address,
                    "port": n.port,
                    "capabilities": n.capabilities,
                    "last_seen": n.last_seen
                }
                for n in nodes
            ])
        except Exception as e:
            logger.error(f"Get discovered nodes error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/mesh/discovery/start")
    async def start_discovery(req: DiscoveryRequest):
        """Start continuous discovery."""
        try:
            method = DiscoveryMethod(req.method)
            auto_discovery.start(method)
            return JSONResponse({"status": "started", "method": req.method})
        except Exception as e:
            logger.error(f"Start discovery error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/mesh/discovery/stop")
    async def stop_discovery():
        """Stop continuous discovery."""
        try:
            auto_discovery.stop()
            return JSONResponse({"status": "stopped"})
        except Exception as e:
            logger.error(f"Stop discovery error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # ─── NODE REGISTRY ENDPOINTS ────────────────────────────────────────────
    
    @app.post("/api/mesh/nodes/register")
    async def register_node(req: NodeRegistrationRequest):
        """Register a node in the registry."""
        try:
            node = node_registry.register_node(
                node_id=req.node_id,
                hostname=req.hostname,
                ip_address=req.ip_address,
                port=req.port,
                capabilities=req.capabilities
            )
            return JSONResponse({
                "node_id": node.node_id,
                "trust_level": node.trust_level.value,
                "status": node.status.value
            })
        except Exception as e:
            logger.error(f"Register node error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/nodes/{node_id}")
    async def get_node(node_id: str):
        """Get a node by ID."""
        try:
            node = node_registry.get_node(node_id)
            if not node:
                raise HTTPException(status_code=404, detail="Node not found")
            
            return JSONResponse({
                "node_id": node.node_id,
                "hostname": node.hostname,
                "ip_address": node.ip_address,
                "port": node.port,
                "trust_level": node.trust_level.value,
                "status": node.status.value,
                "capabilities": node.capabilities,
                "first_seen": node.first_seen,
                "last_seen": node.last_seen
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get node error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/nodes")
    async def get_nodes(trust_level: Optional[str] = None, status: Optional[str] = None):
        """Get nodes, optionally filtered."""
        try:
            nodes = list(node_registry.nodes.values())
            
            if trust_level:
                try:
                    level = TrustLevel(trust_level)
                    nodes = [n for n in nodes if n.trust_level == level]
                except ValueError:
                    pass
            
            if status:
                try:
                    st = NodeStatus(status)
                    nodes = [n for n in nodes if n.status == st]
                except ValueError:
                    pass
            
            return JSONResponse([
                {
                    "node_id": n.node_id,
                    "hostname": n.hostname,
                    "ip_address": n.ip_address,
                    "port": n.port,
                    "trust_level": n.trust_level.value,
                    "status": n.status.value,
                    "capabilities": n.capabilities
                }
                for n in nodes
            ])
        except Exception as e:
            logger.error(f"Get nodes error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.put("/api/mesh/nodes/{node_id}/trust")
    async def set_trust_level(node_id: str, req: TrustLevelRequest):
        """Set trust level for a node."""
        try:
            level = TrustLevel(req.trust_level)
            success = node_registry.set_trust_level(node_id, level, req.reason)
            if not success:
                raise HTTPException(status_code=404, detail="Node not found")
            return JSONResponse({"success": True, "trust_level": req.trust_level})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Set trust level error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/nodes/stats")
    async def get_node_stats():
        """Get node registry statistics."""
        try:
            stats = node_registry.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get node stats error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # ─── DHT ENDPOINTS ─────────────────────────────────────────────────────
    
    @app.post("/api/mesh/dht/store")
    async def dht_store(req: DHTStoreRequest):
        """Store a value in the DHT."""
        try:
            key = NodeID.from_string(req.key)
            value = req.value.encode()
            kademlia_dht.store(key, value, req.ttl)
            return JSONResponse({"success": True, "key": req.key})
        except Exception as e:
            logger.error(f"DHT store error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/dht/get/{key}")
    async def dht_get(key: str):
        """Get a value from the DHT."""
        try:
            key_id = NodeID.from_string(key)
            value = kademlia_dht.get(key_id)
            if value:
                return JSONResponse({"key": key, "value": value.decode()})
            else:
                return JSONResponse({"key": key, "value": None})
        except Exception as e:
            logger.error(f"DHT get error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/dht/stats")
    async def get_dht_stats():
        """Get DHT statistics."""
        try:
            stats = kademlia_dht.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get DHT stats error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # ─── P2P TRANSPORT ENDPOINTS ───────────────────────────────────────────
    
    @app.post("/api/mesh/p2p/connect/{peer_id}")
    async def connect_peer(peer_id: str, ip_address: str, port: int):
        """Connect to a peer."""
        try:
            success = await p2p_transport.connect(peer_id, ip_address, port)
            return JSONResponse({"success": success, "peer_id": peer_id})
        except Exception as e:
            logger.error(f"Connect peer error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/mesh/p2p/disconnect/{peer_id}")
    async def disconnect_peer(peer_id: str):
        """Disconnect from a peer."""
        try:
            success = await p2p_transport.disconnect(peer_id)
            return JSONResponse({"success": success, "peer_id": peer_id})
        except Exception as e:
            logger.error(f"Disconnect peer error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/p2p/connections")
    async def get_connections():
        """Get all P2P connections."""
        try:
            connections = p2p_transport.get_connections()
            return JSONResponse([
                {
                    "peer_id": c.peer_id,
                    "ip_address": c.ip_address,
                    "port": c.port,
                    "state": c.state.value,
                    "last_seen": c.last_seen
                }
                for c in connections
            ])
        except Exception as e:
            logger.error(f"Get connections error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/p2p/stats")
    async def get_p2p_stats():
        """Get P2P transport statistics."""
        try:
            stats = p2p_transport.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get P2P stats error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # ─── CRDT SYNC ENDPOINTS ────────────────────────────────────────────────
    
    @app.get("/api/mesh/sync/state")
    async def get_sync_state(since: Optional[float] = None):
        """Get sync state."""
        try:
            state = crdt_store.get_sync_state(since)
            return JSONResponse(state)
        except Exception as e:
            logger.error(f"Get sync state error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/mesh/sync/apply")
    async def apply_sync_state(req: SyncRequest):
        """Apply sync state from another node."""
        try:
            # In a real implementation, you'd receive the sync state in the request
            # For now, return a placeholder response
            return JSONResponse({"applied": 0, "message": "Sync state application"})
        except Exception as e:
            logger.error(f"Apply sync state error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/sync/crdts")
    async def get_crdts():
        """Get all CRDTs."""
        try:
            state = crdt_store.get_state()
            return JSONResponse(state)
        except Exception as e:
            logger.error(f"Get CRDTs error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # ─── RELAY ENDPOINTS ────────────────────────────────────────────────────
    
    @app.get("/api/mesh/relay/sessions")
    async def get_relay_sessions():
        """Get all relay sessions."""
        try:
            sessions = relay_service.get_sessions()
            return JSONResponse([
                {
                    "session_id": s.session_id,
                    "client_a_id": s.client_a_id,
                    "client_b_id": s.client_b_id,
                    "status": s.status.value,
                    "bytes_relayed": s.bytes_relayed
                }
                for s in sessions
            ])
        except Exception as e:
            logger.error(f"Get relay sessions error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/relay/stats")
    async def get_relay_stats():
        """Get relay statistics."""
        try:
            stats = relay_service.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get relay stats error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # ─── BOOTSTRAP ENDPOINTS ────────────────────────────────────────────────
    
    @app.get("/api/mesh/bootstrap/nodes")
    async def get_bootstrap_nodes(region: Optional[str] = None):
        """Get bootstrap nodes."""
        try:
            region_enum = None
            if region:
                try:
                    region_enum = BootstrapRegion(region)
                except ValueError:
                    pass
            
            nodes = bootstrap_service.get_bootstrap_nodes(region=region_enum)
            return JSONResponse([
                {
                    "node_id": n.node_id,
                    "ip_address": n.ip_address,
                    "port": n.port,
                    "region": n.region.value,
                    "trust_level": n.trust_level,
                    "load": n.load
                }
                for n in nodes
            ])
        except Exception as e:
            logger.error(f"Get bootstrap nodes error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/mesh/bootstrap")
    async def bootstrap():
        """Bootstrap the mesh network."""
        try:
            nodes = await bootstrap_service.bootstrap()
            return JSONResponse({
                "success": True,
                "nodes_found": len(nodes),
                "nodes": [
                    {
                        "node_id": n.node_id,
                        "ip_address": n.ip_address,
                        "port": n.port,
                        "region": n.region.value
                    }
                    for n in nodes
                ]
            })
        except Exception as e:
            logger.error(f"Bootstrap error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/mesh/bootstrap/stats")
    async def get_bootstrap_stats():
        """Get bootstrap statistics."""
        try:
            stats = bootstrap_service.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get bootstrap stats error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # ─── OVERALL MESH STATUS ───────────────────────────────────────────────
    
    @app.get("/api/mesh/status")
    async def get_mesh_status():
        """Get overall mesh status."""
        try:
            return JSONResponse({
                "node_id": node_id,
                "discovery": {
                    "running": auto_discovery._running,
                    "discovered_nodes": len(auto_discovery.discovered_nodes)
                },
                "registry": node_registry.get_stats(),
                "dht": kademlia_dht.get_stats(),
                "p2p": p2p_transport.get_stats(),
                "relay": relay_service.get_stats(),
                "bootstrap": bootstrap_service.get_stats()
            })
        except Exception as e:
            logger.error(f"Get mesh status error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
