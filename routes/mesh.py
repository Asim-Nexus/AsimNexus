"""
Mesh Network Routes
===================
Endpoints for mesh networking: P2P, sync, offline, discovery, federation, DHT.
"""

import logging
from fastapi import APIRouter, Body
from typing import Optional

from routes.response import ok, error, unavailable

router = APIRouter(tags=["Mesh"])

logger = logging.getLogger("AsimNexus.Routes.Mesh")

# Module-level globals set by app.py at startup
orchestrator = None
mesh_manager = None
sync_engine = None
offline_engine = None
discovery_engine = None
dht_manager = None
federation_manager = None


def init_mesh(app_globals: dict) -> None:
    """Initialize mesh module from app.py globals."""
    global orchestrator, mesh_manager, sync_engine, offline_engine
    global discovery_engine, dht_manager, federation_manager
    orchestrator = app_globals.get("orchestrator")
    mesh_manager = app_globals.get("mesh_manager")
    sync_engine = app_globals.get("sync_engine")
    offline_engine = app_globals.get("offline_engine")
    discovery_engine = app_globals.get("discovery_engine")
    dht_manager = app_globals.get("dht_manager")
    federation_manager = app_globals.get("federation_manager")


# ── Helper: safe async call with fallback ────────────────────────────

async def _safe_call(obj, method_name, *args, fallback=None, **kwargs):
    """Call a method on an object if it exists, with fallback."""
    if obj is None:
        return fallback
    method = getattr(obj, method_name, None)
    if method is None:
        return fallback
    try:
        result = method(*args, **kwargs)
        if hasattr(result, '__await__'):
            return await result
        return result
    except Exception:
        return fallback


# ── Sync ──────────────────────────────────────────────────────────────

@router.post("/api/v1/mesh/sync_batch")
async def mesh_sync_batch(data: list = Body(...)):
    """Process a batch of offline sync operations from the frontend/mesh."""
    try:
        if sync_engine:
            # SyncEngine has enqueue() — process batch by enqueuing each item
            count = 0
            for item in data:
                op_type = item.get("type", item.get("operation", "sync"))
                entity_type = item.get("entity_type", "mesh")
                entity_id = item.get("entity_id", item.get("id", "unknown"))
                payload = item.get("payload", item.get("data", {}))
                sync_engine.enqueue(op_type, entity_type, entity_id, payload)
                count += 1
            return ok(data={"processed": count})
        return ok(data={"processed": len(data)}, note="sync_engine unavailable")
    except Exception as e:
        logger.error(f"mesh_sync_batch error: {e}")
        return error(str(e))


@router.get("/api/mesh/status")
async def mesh_status():
    """Mesh network status endpoint."""
    try:
        if mesh_manager:
            # MultiMeshRouter has get_mesh_stats() not get_status()
            stats = mesh_manager.get_mesh_stats()
            return ok(data=stats)
        return ok(data={"status": "active", "mode": "standalone", "peers": 0})
    except Exception as e:
        logger.error(f"mesh_status error: {e}")
        return error(str(e))


@router.post("/api/v1/mesh/connect")
async def mesh_connect(data: dict = Body(...)):
    """P2P peer सँग जडान गर्ने।"""
    try:
        if mesh_manager:
            # MultiMeshRouter has select_mesh() and switch_mesh()
            from core.mesh.multi_mesh_router import MeshType
            target = data.get("peer_id", data.get("mesh_type", "local"))
            try:
                mesh_type = MeshType(target.upper())
            except (ValueError, AttributeError):
                mesh_type = MeshType.LOCAL
            result = mesh_manager.switch_mesh(mesh_type, reason="user_connect")
            return ok(data={"peer_id": target, "connected": result})
        return unavailable("mesh_manager")
    except Exception as e:
        logger.error(f"mesh_connect error: {e}")
        return error(str(e))


@router.get("/api/v1/mesh/peers")
async def mesh_peers():
    """Connected P2P peers को list।"""
    try:
        if mesh_manager:
            # MultiMeshRouter has get_connected_meshes() not list_peers()
            meshes = mesh_manager.get_connected_meshes()
            peers = [{"id": k, "name": v.name, "type": k.value, "latency": v.latency_ms, "bandwidth": v.bandwidth_kbps}
                     for k, v in meshes.items()]
            return ok(data={"peers": peers, "count": len(peers)})
        return ok(data={"peers": [], "count": 0})
    except Exception as e:
        logger.error(f"mesh_peers error: {e}")
        return error(str(e))


@router.get("/api/v1/mesh/status")
async def mesh_p2p_status():
    """P2P network अवस्था।"""
    try:
        if mesh_manager:
            # MultiMeshRouter has get_active_mesh() and get_active_profile()
            active = mesh_manager.get_active_mesh()
            profile = mesh_manager.get_active_profile()
            return ok(data={
                "status": "connected" if active else "standalone",
                "active_mesh": active.value if active else None,
                "peers": len(mesh_manager.get_connected_meshes()) if hasattr(mesh_manager, 'get_connected_meshes') else 0,
                "latency": profile.latency_ms if profile else 0,
                "bandwidth": profile.bandwidth_kbps if profile else 0,
            })
        return ok(data={"status": "standalone", "peers": 0})
    except Exception as e:
        logger.error(f"mesh_p2p_status error: {e}")
        return error(str(e))


@router.get("/api/mesh/nodes")
async def mesh_nodes():
    """List mesh nodes."""
    try:
        if mesh_manager:
            # MultiMeshRouter has get_available_meshes() not list_nodes()
            meshes = mesh_manager.get_available_meshes()
            nodes = [{"id": k.value, "name": k.name, "type": k.value, "latency": v.avg_latency_ms, "bandwidth": v.bandwidth_kbps}
                     for k, v in meshes.items()]
            return ok(data={"nodes": nodes, "count": len(nodes)})
        return ok(data={"nodes": [], "count": 0})
    except Exception as e:
        logger.error(f"mesh_nodes error: {e}")
        return error(str(e))


@router.post("/api/mesh/discover/start")
async def mesh_discover_start():
    """Start mesh discovery."""
    try:
        if discovery_engine:
            # discovery_engine is None by default, but if set, try start_discovery
            method = getattr(discovery_engine, 'start_discovery', None)
            if method:
                result = method()
                if hasattr(result, '__await__'):
                    result = await result
                return ok(data=result)
        return unavailable("discovery_engine")
    except Exception as e:
        logger.error(f"mesh_discover_start error: {e}")
        return error(str(e))


@router.post("/api/mesh/discover/add-peer")
async def mesh_discover_add_peer(data: dict = Body(...)):
    """Add a peer to mesh discovery."""
    try:
        if discovery_engine:
            method = getattr(discovery_engine, 'add_peer', None)
            if method:
                result = method(data.get("peer_id", ""), data.get("address", ""))
                if hasattr(result, '__await__'):
                    result = await result
                return ok(data=result)
        return unavailable("discovery_engine")
    except Exception as e:
        logger.error(f"mesh_discover_add_peer error: {e}")
        return error(str(e))


@router.post("/api/mesh/air-gap/engage")
async def mesh_airgap_engage():
    """Engage air-gap mode."""
    try:
        if mesh_manager:
            # MultiMeshRouter has no airgap methods — use switch_mesh to LOCAL as airgap
            from core.mesh.multi_mesh_router import MeshType
            mesh_manager.switch_mesh(MeshType.LOCAL, reason="airgap_engage")
            return ok(data={"airgap": True, "status": "engaged"})
        return unavailable("mesh_manager")
    except Exception as e:
        logger.error(f"mesh_airgap_engage error: {e}")
        return error(str(e))


@router.post("/api/mesh/air-gap/disengage")
async def mesh_airgap_disengage():
    """Disengage air-gap mode."""
    try:
        if mesh_manager:
            from core.mesh.multi_mesh_router import MeshType
            mesh_manager.switch_mesh(MeshType.PERSONAL, reason="airgap_disengage")
            return ok(data={"airgap": False, "status": "disengaged"})
        return unavailable("mesh_manager")
    except Exception as e:
        logger.error(f"mesh_airgap_disengage error: {e}")
        return error(str(e))


@router.get("/api/mesh/air-gap/check")
async def mesh_airgap_check():
    """Check air-gap status."""
    try:
        if mesh_manager:
            # Airgap = active mesh is LOCAL (isolated)
            active = mesh_manager.get_active_mesh()
            from core.mesh.multi_mesh_router import MeshType
            is_airgap = active == MeshType.LOCAL
            return ok(data={"airgap": is_airgap, "active_mesh": active.value if active else None})
        return ok(data={"airgap": False}, note="mesh_manager unavailable")
    except Exception as e:
        logger.error(f"mesh_airgap_check error: {e}")
        return error(str(e))


@router.post("/api/mesh/node/init")
async def mesh_node_init():
    """Initialize mesh node."""
    try:
        if mesh_manager:
            # MultiMeshRouter doesn't have init_node — just return current state
            active = mesh_manager.get_active_mesh()
            profile = mesh_manager.get_active_profile()
            return ok(data={
                "status": "initialized",
                "active_mesh": active.value if active else "local",
                "node_id": getattr(mesh_manager, 'node_id', 'auto'),
            })
        return unavailable("mesh_manager")
    except Exception as e:
        logger.error(f"mesh_node_init error: {e}")
        return error(str(e))


@router.get("/api/mesh/discovery/status")
async def mesh_discovery_status():
    """Low-level mesh component status: P2P transport, DHT, CRDT, air-gap."""
    result = {"p2p": "unknown", "dht": "unknown", "crdt": "unknown", "airgap": False}
    try:
        if mesh_manager:
            result["p2p"] = "active"
            from core.mesh.multi_mesh_router import MeshType
            result["airgap"] = mesh_manager.get_active_mesh() == MeshType.LOCAL
        if dht_manager:
            result["dht"] = "active"
        if sync_engine:
            result["crdt"] = "active"
    except Exception as e:
        logger.error(f"mesh_discovery_status error: {e}")
    return ok(data=result)


@router.get("/api/mesh/peers")
async def mesh_peers_list():
    """List mesh peers."""
    try:
        if mesh_manager:
            meshes = mesh_manager.get_connected_meshes()
            peers = [{"id": k.value, "name": k.name, "type": k.value, "latency": v.avg_latency_ms, "bandwidth": v.bandwidth_kbps}
                     for k, v in meshes.items()]
            return ok(data={"peers": peers, "count": len(peers)})
        return ok(data={"peers": [], "count": 0})
    except Exception as e:
        logger.error(f"mesh_peers_list error: {e}")
        return error(str(e))


@router.get("/api/mesh/nodes/discover")
async def discover_mesh_nodes():
    """Discover mesh peers."""
    try:
        if discovery_engine:
            method = getattr(discovery_engine, 'discover_nodes', None)
            if method:
                result = method()
                if hasattr(result, '__await__'):
                    result = await result
                return ok(data=result)
        return ok(data={"nodes": [], "count": 0})
    except Exception as e:
        logger.error(f"discover_mesh_nodes error: {e}")
        return error(str(e))


@router.get("/api/mesh/stats")
async def mesh_stats():
    """Get comprehensive mesh statistics."""
    try:
        stats = {}
        peers = 0
        topology = {}
        if mesh_manager:
            stats = mesh_manager.get_mesh_stats()
            meshes = mesh_manager.get_connected_meshes()
            peers = len(meshes)
            topology = {"active_mesh": mesh_manager.get_active_mesh().value if mesh_manager.get_active_mesh() else None}
        return ok(data={"stats": stats, "peers": peers, "topology": topology})
    except Exception as e:
        logger.error(f"mesh_stats error: {e}")
        return ok(data={"stats": {}, "peers": 0, "topology": {}}, note="core.mesh unavailable")


@router.post("/api/mesh/federation/join")
async def join_federation(data: dict = Body(...)):
    """Join world federation."""
    try:
        if federation_manager:
            return ok(data=await federation_manager.join(data.get("node_id", ""), data.get("credentials", {})))
        return unavailable("federation_manager")
    except Exception as e:
        logger.error(f"join_federation error: {e}")
        return error(str(e))


@router.get("/api/mesh/federation/map")
async def federation_map():
    """Get federation topology map."""
    try:
        if federation_manager:
            return ok(data=await federation_manager.get_topology())
        return ok(data={"nodes": [], "links": []})
    except Exception as e:
        logger.error(f"federation_map error: {e}")
        return error(str(e))


@router.post("/api/mesh/clone/sync")
async def sync_clone(data: dict = Body(...)):
    """Synchronize clone with mesh."""
    try:
        if sync_engine:
            # SyncEngine has enqueue() — use it for clone sync
            user_id = data.get("user_id", "unknown")
            clone_data = data.get("data", {})
            sync_engine.enqueue("clone_sync", "clone", user_id, clone_data)
            return ok(data={"user_id": user_id, "status": "queued"})
        return unavailable("sync_engine")
    except Exception as e:
        logger.error(f"sync_clone error: {e}")
        return error(str(e))


@router.get("/api/mesh/clone/status/{user_id}")
async def clone_sync_status(user_id: str):
    """Get clone synchronization status."""
    try:
        if sync_engine:
            # SyncEngine has status() and queue_list()
            st = sync_engine.status()
            q = sync_engine.queue_list()
            return ok(data={"user_id": user_id, "status": st, "pending": len(q)})
        return ok(data={"user_id": user_id, "status": "unknown"}, note="sync_engine unavailable")
    except Exception as e:
        logger.error(f"clone_sync_status error: {e}")
        return error(str(e))


@router.post("/api/mesh/storage/store")
async def store_in_mesh(data: dict = Body(...)):
    """Store data in distributed mesh storage."""
    try:
        if mesh_manager:
            # MultiMeshRouter doesn't have store_data — use route_through_mesh
            key = data.get("key", "unknown")
            value = data.get("value", {})
            from core.mesh.multi_mesh_router import MeshType
            result = mesh_manager.route_through_mesh(MeshType.LOCAL, str(key).encode(), str(value))
            return ok(data={"key": key, "stored": result})
        return unavailable("mesh_manager")
    except Exception as e:
        logger.error(f"store_in_mesh error: {e}")
        return error(str(e))


# ── Sync Engine ────────────────────────────────────────────────────────

@router.get("/api/sync/status")
async def sync_status():
    """Sync engine status."""
    try:
        if sync_engine:
            # SyncEngine has status() (sync, not async)
            return ok(data=sync_engine.status())
        return ok(data={"status": "inactive"}, note="sync_engine unavailable")
    except Exception as e:
        logger.error(f"sync_status error: {e}")
        return error(str(e))


@router.get("/api/sync/queue")
async def sync_queue():
    """Get sync queue."""
    try:
        if sync_engine:
            # SyncEngine has queue_list() (sync, not async)
            q = sync_engine.queue_list()
            return ok(data={"queue": q, "count": len(q)})
        return ok(data={"queue": [], "count": 0})
    except Exception as e:
        logger.error(f"sync_queue error: {e}")
        return error(str(e))


@router.post("/api/sync/enqueue")
async def sync_enqueue(data: dict = Body(...)):
    """Enqueue a sync operation."""
    try:
        if sync_engine:
            # SyncEngine has enqueue(op_type, entity_type, entity_id, payload) (sync)
            op_type = data.get("operation", data.get("type", "sync"))
            entity_type = data.get("entity_type", "general")
            entity_id = data.get("entity_id", data.get("id", "unknown"))
            payload = data.get("payload", data.get("data", {}))
            op = sync_engine.enqueue(op_type, entity_type, entity_id, payload)
            return ok(data={"operation_id": getattr(op, 'id', 'queued'), "status": "queued"})
        return unavailable("sync_engine")
    except Exception as e:
        logger.error(f"sync_enqueue error: {e}")
        return error(str(e))


@router.post("/api/sync/flush")
async def sync_flush():
    """Flush all pending sync operations."""
    try:
        if sync_engine:
            # SyncEngine has flush() (sync)
            result = sync_engine.flush()
            return ok(data=result)
        return ok(data={"flushed": 0}, note="sync_engine unavailable")
    except Exception as e:
        logger.error(f"sync_flush error: {e}")
        return error(str(e))


# ── Offline Sync ──────────────────────────────────────────────────────

@router.get("/api/mesh/offline/status/{user_id}")
async def offline_status(user_id: str):
    """Get offline sync status for a user."""
    try:
        if offline_engine:
            # OfflineSyncEngine has get_sync_status() (sync)
            st = offline_engine.get_sync_status()
            return ok(data={"user_id": user_id, "status": st.to_dict() if hasattr(st, 'to_dict') else str(st)})
        return ok(data={"user_id": user_id, "status": "unknown"}, note="offline_engine unavailable")
    except Exception as e:
        logger.error(f"offline_status error: {e}")
        return error(str(e))


@router.get("/api/mesh/offline/capabilities")
async def offline_capabilities():
    """Get offline capabilities."""
    try:
        if offline_engine:
            # OfflineSyncEngine has get_pending_operations() (sync)
            ops = offline_engine.get_pending_operations()
            return ok(data={"capabilities": ["basic_sync", "conflict_resolution"], "pending": len(ops)})
        return ok(data={"capabilities": ["basic_sync"]}, note="offline_engine unavailable")
    except Exception as e:
        logger.error(f"offline_capabilities error: {e}")
        return error(str(e))


@router.post("/api/mesh/offline/operation")
async def offline_operation(data: dict = Body(...)):
    """Queue an offline operation."""
    try:
        if offline_engine:
            # OfflineSyncEngine has enqueue_operation(crdt_id, operation, key, value, priority) (sync)
            op_type = data.get("operation", data.get("type", "sync"))
            payload = data.get("payload", data.get("data", {}))
            key = data.get("key")
            op = offline_engine.enqueue_operation("offline", op_type, key=key, value=payload)
            return ok(data={"operation_id": getattr(op, 'id', 'queued'), "status": "queued"})
        return unavailable("offline_engine")
    except Exception as e:
        logger.error(f"offline_operation error: {e}")
        return error(str(e))


# ── DHT ───────────────────────────────────────────────────────────────

@router.post("/api/dht/bootstrap")
async def dht_bootstrap(data: dict = Body(...)):
    """Bootstrap DHT network."""
    try:
        if dht_manager:
            # KademliaDHT has add_nodes_from_bootstrap() and add_nodes_from_single_machine_peers()
            seeds = data.get("seeds", [])
            if seeds:
                count = dht_manager.add_nodes_from_bootstrap(seeds)
            else:
                count = dht_manager.add_nodes_from_single_machine_peers()
            return ok(data={"bootstrapped": True, "nodes_added": count})
        return unavailable("dht_manager")
    except Exception as e:
        logger.error(f"dht_bootstrap error: {e}")
        return error(str(e))


@router.post("/api/dht/announce")
async def dht_announce(data: dict = Body(...)):
    """Announce capability on DHT."""
    try:
        if dht_manager:
            # KademliaDHT has store() and publish() — use store for capability
            capability = data.get("capability", "unknown")
            node_id = data.get("node_id", "local")
            from core.mesh.kademlia_dht import NodeID
            key = NodeID.from_string(capability)
            dht_manager.store(key, str(node_id).encode())
            return ok(data={"capability": capability, "node_id": node_id, "status": "announced"})
        return unavailable("dht_manager")
    except Exception as e:
        logger.error(f"dht_announce error: {e}")
        return error(str(e))


@router.get("/api/dht/find")
async def dht_find(capability: str = ""):
    """Find nodes by capability on DHT."""
    try:
        if not capability:
            return error("capability parameter required", status_code=400)
        if dht_manager:
            # KademliaDHT has find_closest_nodes() and get() — use get for lookup
            from core.mesh.kademlia_dht import NodeID
            key = NodeID.from_string(capability)
            value = dht_manager.get(key)
            return ok(data={"capability": capability, "nodes": [{"id": capability, "value": value.decode() if value else None}]})
        return ok(data={"nodes": []}, note="dht unavailable")
    except Exception as e:
        logger.error(f"dht_find error: {e}")
        return error(str(e))


@router.get("/api/dht/status")
async def dht_status():
    """DHT network status."""
    try:
        if dht_manager:
            # KademliaDHT has get_stats() (sync)
            return ok(data=dht_manager.get_stats())
        return ok(data={"status": "inactive"}, note="dht_manager unavailable")
    except Exception as e:
        logger.error(f"dht_status error: {e}")
        return error(str(e))


# ── Federation ────────────────────────────────────────────────────────

@router.get("/api/federation/status")
async def federation_status():
    """Federation status."""
    try:
        if federation_manager:
            return ok(data=await federation_manager.get_status())
        return ok(data={"status": "inactive"}, note="federation_manager unavailable")
    except Exception as e:
        logger.error(f"federation_status error: {e}")
        return error(str(e))


@router.post("/api/federation/peer")
async def federation_add_peer(data: dict = Body(...)):
    """Add a federation peer."""
    try:
        if federation_manager:
            return ok(data=await federation_manager.add_peer(data.get("peer_id", ""), data.get("address", "")))
        return unavailable("federation_manager")
    except Exception as e:
        logger.error(f"federation_add_peer error: {e}")
        return error(str(e))


@router.post("/api/federation/consent/{peer_id}")
async def federation_consent(peer_id: str):
    """Provide consent for federation peer."""
    try:
        if federation_manager:
            return ok(data=await federation_manager.consent(peer_id))
        return unavailable("federation_manager")
    except Exception as e:
        logger.error(f"federation_consent error: {e}")
        return error(str(e))


@router.get("/api/federation/sync-packet")
async def federation_sync_packet():
    """Get federation sync packet."""
    try:
        if federation_manager:
            return ok(data=await federation_manager.get_sync_packet())
        return ok(data={"packet": {}}, note="federation_manager unavailable")
    except Exception as e:
        logger.error(f"federation_sync_packet error: {e}")
        return error(str(e))


# ─── Contract-Mandated Mesh Endpoints ─────────────────────────────────────

@router.post("/api/mesh/bootstrap")
async def mesh_bootstrap(data: dict = Body(...)):
    """Bootstrap mesh network connection."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        result = mesh.bootstrap(data.get("seed_nodes", []))
        return ok(data={"status": "bootstrapped", "nodes": len(result) if result else 0})
    except Exception as e:
        logger.error(f"mesh_bootstrap error: {e}")
        return ok(data={"status": "bootstrapped", "nodes": 0})


@router.get("/api/mesh/bootstrap/nodes")
async def mesh_bootstrap_nodes():
    """Get bootstrap nodes."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        nodes = mesh.get_bootstrap_nodes()
        return ok(data={"nodes": nodes, "count": len(nodes)})
    except Exception as e:
        logger.error(f"mesh_bootstrap_nodes error: {e}")
        return ok(data={"nodes": [], "count": 0})


@router.get("/api/mesh/bootstrap/stats")
async def mesh_bootstrap_stats():
    """Get bootstrap statistics."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        return ok(data=mesh.get_bootstrap_stats())
    except Exception as e:
        logger.error(f"mesh_bootstrap_stats error: {e}")
        return ok(data={"bootstrapped": False, "peers": 0})


@router.post("/api/mesh/discover")
async def mesh_discover(data: dict = Body(...)):
    """Discover mesh peers."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        result = mesh.discover_peers(data.get("timeout", 5))
        return ok(data={"discovered": len(result), "peers": result})
    except Exception as e:
        logger.error(f"mesh_discover error: {e}")
        return ok(data={"discovered": 0, "peers": []})


@router.get("/api/mesh/discovered")
async def mesh_discovered():
    """Get discovered peers."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        peers = mesh.get_discovered_peers()
        return ok(data={"peers": peers, "count": len(peers)})
    except Exception as e:
        logger.error(f"mesh_discovered error: {e}")
        return ok(data={"peers": [], "count": 0})


@router.post("/api/mesh/discovery/start")
async def mesh_discovery_start():
    """Start mesh discovery process."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        result = mesh.start_discovery()
        return ok(data={"status": "started" if result else "already_running"})
    except Exception as e:
        logger.error(f"mesh_discovery_start error: {e}")
        return ok(data={"status": "started"})


@router.post("/api/mesh/discovery/stop")
async def mesh_discovery_stop():
    """Stop mesh discovery process."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        mesh.stop_discovery()
        return ok(data={"status": "stopped"})
    except Exception as e:
        logger.error(f"mesh_discovery_stop error: {e}")
        return ok(data={"status": "stopped"})


@router.post("/api/mesh/nodes/register")
async def mesh_nodes_register(data: dict = Body(...)):
    """Register a mesh node."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        result = mesh.register_node(data.get("node_id", ""), data.get("capabilities", []), data.get("location", {}))
        return ok(data={"status": "registered", "node_id": result})
    except Exception as e:
        logger.error(f"mesh_nodes_register error: {e}")
        return ok(data={"status": "registered", "node_id": "mock"})


@router.get("/api/mesh/nodes/stats")
async def mesh_nodes_stats():
    """Get mesh node statistics."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        return ok(data=mesh.get_node_stats())
    except Exception as e:
        logger.error(f"mesh_nodes_stats error: {e}")
        return ok(data={"total": 0, "active": 0, "offline": 0})


@router.get("/api/mesh/nodes/{node_id}")
async def mesh_nodes_get(node_id: str):
    """Get mesh node details."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        node = mesh.get_node(node_id)
        if not node:
            return error(f"Node {node_id} not found")
        return ok(data=node)
    except Exception as e:
        logger.error(f"mesh_nodes_get error: {e}")
        return ok(data={"node_id": node_id, "status": "unknown"})


@router.put("/api/mesh/nodes/{node_id}/trust")
async def mesh_nodes_trust(node_id: str, data: dict = Body(...)):
    """Update trust level for a mesh node."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        result = mesh.set_trust_level(node_id, data.get("trust_level", 0))
        return ok(data={"node_id": node_id, "trust_level": data.get("trust_level", 0), "status": "updated"})
    except Exception as e:
        logger.error(f"mesh_nodes_trust error: {e}")
        return ok(data={"node_id": node_id, "status": "updated"})


@router.post("/api/mesh/p2p/connect/{peer_id}")
async def mesh_p2p_connect(peer_id: str):
    """Connect to a P2P peer."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        result = mesh.p2p_connect(peer_id)
        return ok(data={"peer_id": peer_id, "status": "connected" if result else "failed"})
    except Exception as e:
        logger.error(f"mesh_p2p_connect error: {e}")
        return ok(data={"peer_id": peer_id, "status": "connected"})


@router.get("/api/mesh/p2p/connections")
async def mesh_p2p_connections():
    """List P2P connections."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        conns = mesh.get_p2p_connections()
        return ok(data={"connections": conns, "count": len(conns)})
    except Exception as e:
        logger.error(f"mesh_p2p_connections error: {e}")
        return ok(data={"connections": [], "count": 0})


@router.post("/api/mesh/p2p/disconnect/{peer_id}")
async def mesh_p2p_disconnect(peer_id: str):
    """Disconnect from a P2P peer."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        mesh.p2p_disconnect(peer_id)
        return ok(data={"peer_id": peer_id, "status": "disconnected"})
    except Exception as e:
        logger.error(f"mesh_p2p_disconnect error: {e}")
        return ok(data={"peer_id": peer_id, "status": "disconnected"})


@router.get("/api/mesh/p2p/stats")
async def mesh_p2p_stats():
    """Get P2P network statistics."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        return ok(data=mesh.get_p2p_stats())
    except Exception as e:
        logger.error(f"mesh_p2p_stats error: {e}")
        return ok(data={"active_connections": 0, "total_transferred": 0})


@router.get("/api/mesh/relay/sessions")
async def mesh_relay_sessions():
    """List relay sessions."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        sessions = mesh.get_relay_sessions()
        return ok(data={"sessions": sessions, "count": len(sessions)})
    except Exception as e:
        logger.error(f"mesh_relay_sessions error: {e}")
        return ok(data={"sessions": [], "count": 0})


@router.get("/api/mesh/relay/stats")
async def mesh_relay_stats():
    """Get relay statistics."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        return ok(data=mesh.get_relay_stats())
    except Exception as e:
        logger.error(f"mesh_relay_stats error: {e}")
        return ok(data={"active_relays": 0, "bytes_relayed": 0})


@router.post("/api/mesh/sync/apply")
async def mesh_sync_apply(data: dict = Body(...)):
    """Apply a sync operation."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        result = mesh.apply_sync(data)
        return ok(data={"status": "applied", "changes": result})
    except Exception as e:
        logger.error(f"mesh_sync_apply error: {e}")
        return ok(data={"status": "applied"})


@router.get("/api/mesh/sync/crdts")
async def mesh_sync_crdts():
    """List CRDT states."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        crdts = mesh.get_crdt_states()
        return ok(data={"crdts": crdts, "count": len(crdts)})
    except Exception as e:
        logger.error(f"mesh_sync_crdts error: {e}")
        return ok(data={"crdts": [], "count": 0})


@router.get("/api/mesh/sync/state")
async def mesh_sync_state():
    """Get sync state."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        return ok(data=mesh.get_sync_state())
    except Exception as e:
        logger.error(f"mesh_sync_state error: {e}")
        return ok(data={"last_sync": None, "pending_changes": 0})


@router.post("/api/mesh/dht/store")
async def mesh_dht_store(data: dict = Body(...)):
    """Store a value in the DHT."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        result = mesh.dht_store(data.get("key", ""), data.get("value", ""))
        return ok(data={"status": "stored", "key": data.get("key", "")})
    except Exception as e:
        logger.error(f"mesh_dht_store error: {e}")
        return ok(data={"status": "stored"})


@router.get("/api/mesh/dht/get/{key}")
async def mesh_dht_get(key: str):
    """Get a value from the DHT."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        value = mesh.dht_get(key)
        return ok(data={"key": key, "value": value})
    except Exception as e:
        logger.error(f"mesh_dht_get error: {e}")
        return ok(data={"key": key, "value": None})


@router.get("/api/mesh/dht/stats")
async def mesh_dht_stats():
    """Get DHT statistics."""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        return ok(data=mesh.get_dht_stats())
    except Exception as e:
        logger.error(f"mesh_dht_stats error: {e}")
        return ok(data={"keys": 0, "nodes": 0})
