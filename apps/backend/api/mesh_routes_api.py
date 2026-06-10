import logging, json, os, asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("AsimNexus.API.Mesh")
router = APIRouter(tags=["Mesh, DHT, Network & Infrastructure"])

# ── Lazy-loaded singletons (mirroring simple_backend.py globals) ──────────────

_local_llm = None
_nodes = None

def _get_nodes():
    global _nodes
    if _nodes is None:
        try:
            from core.network.node_registry import NodeRegistry
            _nodes = NodeRegistry()
            logger.info("✅ NodeRegistry loaded for mesh routes")
        except Exception as e:
            logger.warning(f"⚠️ NodeRegistry fallback: {e}")
    return _nodes

# ─── MESH NODES ───────────────────────────────────────────────────────────────

@router.get("/mesh/nodes")
@router.get("/api/mesh/nodes")
async def mesh_nodes():
    import socket
    hostname = socket.gethostname()
    nodes = [{"id": "local-node", "name": hostname, "type": "citizen",
              "status": "online", "host": "127.0.0.1", "port": 8000,
              "has_local_llm": _local_llm is not None}]
    reg = _get_nodes()
    if reg:
        try:
            registered = reg.get_all_nodes()
            for n in registered:
                nodes.append({"id": n.node_id, "name": n.display_name,
                              "type": n.node_type.value, "status": n.status.value})
        except Exception:
            pass
    return JSONResponse({"nodes": nodes, "total": len(nodes)})

# ─── MESH DISCOVERY ───────────────────────────────────────────────────────────

@router.get("/api/mesh/discovery/status")
async def mesh_discovery_status():
    out = {"p2p_transport": None, "dht": None, "crdt": None, "air_gap": None}
    try:
        from mesh.p2p_transport import get_p2p_transport
        t = get_p2p_transport()
        out["p2p_transport"] = {
            "node_id": t.node_id,
            "host": t.host,
            "port_udp": t.port_udp,
            "port_ws": t.port_ws,
            "running": t._running,
            "peers": len(t.peers),
            "online_peers": len(await t.get_online_peers()),
        }
    except Exception as e:
        out["p2p_transport"] = {"running": False, "error": str(e)}
    try:
        from mesh.kademlia_dht import get_kademlia_dht
        out["dht"] = get_kademlia_dht().get_stats()
    except Exception as e:
        out["dht"] = {"running": False, "error": str(e)}
    try:
        from mesh.crdt_sync import get_crdt_store
        crdt = get_crdt_store()
        out["crdt"] = {
            "crdt_count": len(crdt.crdts),
            "operation_count": len(crdt.operation_log),
            "node_id": crdt.node_id,
        }
    except Exception as e:
        out["crdt"] = {"running": False, "error": str(e)}
    try:
        from core.mesh.air_gap_controller import get_air_gap
        out["air_gap"] = get_air_gap().status()
    except Exception as e:
        out["air_gap"] = {"level": 0, "error": str(e)}
    return JSONResponse(out)

@router.post("/api/mesh/discover/start")
async def mesh_discover_start():
    try:
        from mesh.p2p_transport import get_p2p_transport
        t = get_p2p_transport()
        asyncio.create_task(t.start())
        return JSONResponse({
            "status": "started",
            "node_id": t.node_id,
            "host": t.host,
            "port_udp": t.port_udp,
            "port_ws": t.port_ws,
        })
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/api/mesh/discover/add-peer")
async def mesh_add_peer(request: Request):
    body = await request.json()
    node_id = body.get("node_id", body.get("id", ""))
    ip   = body.get("ip", body.get("host", ""))
    port_udp = int(body.get("port", body.get("port_udp", 7332)))
    port_ws  = int(body.get("port_ws", port_udp + 1))
    if not ip:
        raise HTTPException(400, "ip or host required")
    try:
        from mesh.p2p_transport import get_p2p_transport
        peer = get_p2p_transport().add_peer(node_id, ip, port_udp, port_ws)
        return JSONResponse({
            "node_id": peer.node_id,
            "host": peer.host,
            "port_udp": peer.port_udp,
            "port_ws": peer.port_ws,
            "is_connected": peer.is_connected,
        })
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/api/mesh/peers")
async def mesh_peers():
    try:
        from mesh.p2p_transport import get_p2p_transport
        from dataclasses import asdict
        t = get_p2p_transport()
        peers = [asdict(p) for p in await t.get_online_peers()]
        return JSONResponse({"peers": peers, "total": len(t.peers)})
    except Exception as e:
        return JSONResponse({"peers": [], "total": 0, "error": str(e)})

@router.post("/api/mesh/air-gap/engage")
async def air_gap_engage(request: Request):
    body  = await request.json()
    level = int(body.get("level", 3))
    reason = body.get("reason", "Human-initiated air-gap")
    try:
        from core.mesh.air_gap_controller import get_air_gap, AirGapLevel
        result = get_air_gap().engage(AirGapLevel(level), reason=reason, triggered_by="human")
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/api/mesh/air-gap/disengage")
async def air_gap_disengage():
    try:
        from core.mesh.air_gap_controller import get_air_gap
        result = get_air_gap().disengage(triggered_by="human")
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/api/mesh/air-gap/check")
async def air_gap_check(host: str = "8.8.8.8", port: int = 443):
    try:
        from core.mesh.air_gap_controller import get_air_gap
        return JSONResponse(get_air_gap().check_request(host, port))
    except Exception as e:
        raise HTTPException(500, str(e))

# ─── MESH NETWORK SYSTEM (infrastructure/mesh — from line 4629+) ──────────────

@router.get("/api/mesh/status")
async def mesh_status():
    try:
        from core.mesh import (
            get_mesh_coordinator, get_clone_synchronizer,
            get_federation, get_distributed_storage, get_offline_synchronizer,
            ConnectionState, NodeTier, NodeType
        )
        coordinator = get_mesh_coordinator()
        return JSONResponse({
            "status": "active",
            "topology": "star+mesh+tree+ring hybrid",
            "components": {
                "mesh_coordinator": "✅ Global mesh coordination",
                "clone_sync": "✅ Clone synchronization across mesh",
                "federation": "✅ World federation protocol",
                "distributed_storage": "✅ Sharded encrypted storage",
                "offline_sync": "✅ Offline-first CRDT sync"
            },
            "coverage": "All sectors, all countries, all people",
            "connection_states": [s.value for s in ConnectionState],
            "node_tiers": [t.value for t in NodeTier],
            "node_types": [t.value for t in NodeType]
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/mesh/node/init")
async def init_mesh_node(request: Request):
    try:
        from core.mesh import get_mesh_coordinator, NodeType, NodeTier
        body = await request.json()
        node_type = NodeType(body.get('node_type', 'personal'))
        name = body.get('name', 'MyNode')
        country = body.get('country', 'NP')
        coordinator = get_mesh_coordinator()
        node = asyncio.run(coordinator.initialize_local_node(node_type, name, country))
        return JSONResponse({
            "success": True,
            "node": node.to_dict(),
            "message": f"Node {node.node_id} initialized at tier {node.tier.value}"
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

# ─── KADEMLIA DHT ─────────────────────────────────────────────────────────────

@router.get("/api/dht/status")
async def dht_status():
    try:
        from mesh.kademlia_dht import get_kademlia_dht
        return JSONResponse(get_kademlia_dht().get_stats())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/dht/bootstrap")
async def dht_bootstrap(request: Request):
    body = await request.json()
    seeds = body.get("seeds", [])
    if not seeds:
        raise HTTPException(400, "seeds list required (e.g. [{'node_id':'...','host':'...','port':7332}])")
    try:
        from mesh.kademlia_dht import get_kademlia_dht, NodeID, DHTNode
        dht = get_kademlia_dht()
        added = 0
        for seed in seeds:
            nid = seed.get("node_id", "")
            host = seed.get("host", "")
            port = int(seed.get("port", 7332))
            if not host:
                continue
            node_id = NodeID.from_string(nid) if nid else NodeID.random()
            node = DHTNode(node_id=node_id, ip_address=host, port=port)
            if dht.add_node(node):
                added += 1
        return JSONResponse({"status": "bootstrapped", "seeds_provided": len(seeds), "nodes_added": added})
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/dht/announce")
async def dht_announce(request: Request):
    body = await request.json()
    capability = body.get("capability", "")
    details    = body.get("details", {})
    if not capability:
        raise HTTPException(400, "capability required")
    try:
        from mesh.kademlia_dht import get_kademlia_dht, NodeID
        dht = get_kademlia_dht()
        key = NodeID.from_string(capability)
        value_bytes = json.dumps(details, separators=(",", ":")).encode("utf-8")
        asyncio.create_task(dht.publish(key, value_bytes))
        return JSONResponse({"dht_key": str(key), "capability": capability, "status": "publishing"})
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/dht/find")
async def dht_find(capability: str = ""):
    if not capability:
        raise HTTPException(400, "capability query param required")
    try:
        from mesh.kademlia_dht import get_kademlia_dht, NodeID
        dht = get_kademlia_dht()
        key = NodeID.from_string(capability)
        local_value = dht.get(key)
        if local_value is not None:
            try:
                decoded = json.loads(local_value.decode("utf-8"))
            except Exception:
                decoded = local_value.decode("utf-8", errors="replace")
            return JSONResponse({"found": True, "value": decoded, "source": "local"})
        result_bytes = await dht.lookup(key)
        if result_bytes is not None:
            try:
                decoded = json.loads(result_bytes.decode("utf-8"))
            except Exception:
                decoded = result_bytes.decode("utf-8", errors="replace")
            return JSONResponse({"found": True, "value": decoded, "source": "remote"})
        return JSONResponse({"found": False, "value": None})
    except Exception as e:
        raise HTTPException(400, str(e))

# ─── QUAD MESH ────────────────────────────────────────────────────────────────

@router.get("/api/quad/status")
async def quad_status():
    try:
        from core.mesh.quad_mesh import get_quad_mesh
        return JSONResponse(get_quad_mesh().full_status())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/quad/join")
async def quad_join(request: Request):
    body = await request.json()
    did  = body.get("did","")
    layer= body.get("layer","citizen")
    if not did:
        raise HTTPException(400,"did required")
    try:
        from core.mesh.quad_mesh import get_quad_mesh, MeshLayer
        from dataclasses import asdict as _asdict
        peer = get_quad_mesh().join(did, MeshLayer(layer),
                                    body.get("ip",""), int(body.get("port",8765)))
        return JSONResponse(_asdict(peer))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/quad/{layer}/peers")
async def quad_peers(layer: str):
    try:
        from core.mesh.quad_mesh import get_quad_mesh, MeshLayer
        peers = get_quad_mesh().get_peers(MeshLayer(layer))
        return JSONResponse({"peers": peers, "count": len(peers)})
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/quad/send")
async def quad_send(request: Request):
    body = await request.json()
    try:
        from core.mesh.quad_mesh import get_quad_mesh, MeshLayer
        from dataclasses import asdict as _asdict
        msg = get_quad_mesh().send(
            body.get("from_did",""), MeshLayer(body.get("to_layer","citizen")),
            body.get("payload",{}), bool(body.get("require_consent",False)))
        return JSONResponse(_asdict(msg))
    except Exception as e:
        raise HTTPException(400, str(e))

# ─── ZERO TRUST RUNTIME ───────────────────────────────────────────────────────

@router.get("/api/runtime/status")
async def runtime_status():
    try:
        from core.runtime.zero_trust_runtime import get_runtime
        return JSONResponse(get_runtime().status())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/runtime/register")
async def runtime_register(request: Request):
    body = await request.json()
    try:
        from core.runtime.zero_trust_runtime import get_runtime
        from dataclasses import asdict as _asdict
        tok = get_runtime().register(
            body.get("principal",""), body.get("role","clone"),
            int(body.get("ttl",3600)), body.get("universe","personal"))
        return JSONResponse(tok.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/runtime/principals")
async def runtime_principals():
    try:
        from core.runtime.zero_trust_runtime import get_runtime
        return JSONResponse({"principals": get_runtime().list_principals()})
    except Exception as e:
        return JSONResponse({"principals": [], "error": str(e)})

@router.get("/api/runtime/violations")
async def runtime_violations():
    try:
        from core.runtime.zero_trust_runtime import get_runtime
        return JSONResponse({"violations": get_runtime().violations()})
    except Exception as e:
        return JSONResponse({"violations": [], "error": str(e)})

# ─── FEDERATION ───────────────────────────────────────────────────────────────

@router.get("/api/federation/status")
async def federation_status():
    try:
        from core.federation.global_federation import get_federation
        return JSONResponse(get_federation().status())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/federation/peer")
async def federation_add_peer(request: Request):
    body = await request.json()
    try:
        from core.federation.global_federation import get_federation
        from dataclasses import asdict as _asdict
        peer = get_federation().add_peer(
            body.get("did",""), body.get("endpoint",""), bool(body.get("trusted",False)))
        return JSONResponse(_asdict(peer))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/federation/consent/{peer_id}")
async def federation_consent(peer_id: str):
    try:
        from core.federation.global_federation import get_federation
        get_federation().consent_peer(peer_id)
        return JSONResponse({"ok": True, "peer_id": peer_id})
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/federation/sync-packet")
async def federation_sync_packet():
    try:
        from core.federation.global_federation import get_federation
        return JSONResponse(get_federation().get_sync_packet())
    except Exception as e:
        return JSONResponse({"error": str(e)})

# ─── EVENT BUS ────────────────────────────────────────────────────────────────

@router.get("/api/events/stats")
async def events_stats():
    try:
        from core.events.reactive_bus import get_bus
        return JSONResponse(get_bus().stats())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/events/publish")
async def events_publish(request: Request):
    body = await request.json()
    try:
        from core.events.reactive_bus import get_bus
        evt = get_bus().publish(
            body.get("topic",""), body.get("payload",{}),
            body.get("source","api"))
        return JSONResponse(evt.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/events/recent")
async def events_recent():
    try:
        from core.events.reactive_bus import get_bus
        return JSONResponse({"events": get_bus().recent_events(20)})
    except Exception as e:
        return JSONResponse({"events": [], "error": str(e)})

@router.get("/api/events/dlq")
async def events_dlq():
    try:
        from core.events.reactive_bus import get_bus
        return JSONResponse({"dlq": get_bus().dlq()})
    except Exception as e:
        return JSONResponse({"dlq": [], "error": str(e)})

# ─── INFRASTRUCTURE (CDN + Mesh from line 3703) ───────────────────────────────

@router.get("/api/infrastructure/status")
async def infrastructure_status():
    try:
        from core.infrastructure import get_cdn_system, get_mesh_network
        cdn_stats = get_cdn_system().get_stats()
        mesh_stats = get_mesh_network().get_mesh_stats()
        return JSONResponse({
            "infrastructure": {
                "cdn": cdn_stats,
                "mesh": mesh_stats
            },
            "status": "active",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get("/api/infrastructure/cdn/locations")
async def cdn_locations():
    try:
        from core.infrastructure import get_cdn_system
        cdn = get_cdn_system()
        locations = []
        for loc in cdn.get_all_locations():
            locations.append(loc.to_dict())
        return JSONResponse({
            "locations": locations,
            "stats": cdn.get_stats()
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get("/api/infrastructure/cdn/routing/{country_code}")
async def cdn_routing(country_code: str, lat: Optional[float] = None, lon: Optional[float] = None):
    try:
        from core.infrastructure import get_cdn_system
        cdn = get_cdn_system()
        routing = cdn.get_routing_table(country_code.upper(), lat, lon)
        return JSONResponse(routing)
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get("/api/infrastructure/cdn/nearest")
async def cdn_nearest(lat: float, lon: float):
    try:
        from core.infrastructure import get_cdn_system
        cdn = get_cdn_system()
        nearest = cdn.find_nearest_location(lat, lon)
        if nearest:
            return JSONResponse({
                "nearest": nearest.to_dict(),
                "distance_km": None
            })
        else:
            return JSONResponse({"error": "No location found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get("/api/infrastructure/mesh/status")
async def infra_mesh_status():
    try:
        from core.infrastructure import get_mesh_network
        mesh = get_mesh_network()
        return JSONResponse({
            "mesh": mesh.get_mesh_stats(),
            "quad_system": mesh.get_quad_system_status(),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get("/api/infrastructure/mesh/nodes")
async def infra_mesh_nodes():
    try:
        from core.infrastructure import get_mesh_network
        mesh = get_mesh_network()
        nodes = [n.to_dict() for n in mesh.nodes.values()]
        return JSONResponse({
            "nodes": nodes,
            "total": len(nodes),
            "my_node": mesh.my_node_id
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get("/api/infrastructure/mesh/nodes/{node_id}")
async def infra_mesh_node_detail(node_id: str):
    try:
        from core.infrastructure import get_mesh_network
        mesh = get_mesh_network()
        node = mesh.nodes.get(node_id)
        if not node:
            return JSONResponse({"error": f"Node {node_id} not found"}, status_code=404)
        peers = mesh.discover_peers(node_id, radius_km=500)
        return JSONResponse({
            "node": node.to_dict(),
            "peers": [p.to_dict() for p in peers[:10]],
            "peer_count": len(peers)
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/infrastructure/mesh/join")
async def infra_mesh_join(request: Request):
    try:
        from core.infrastructure import get_mesh_network, MeshNode, NodeType
        body = await request.json()
        user_id = body.get('user_id', 'anonymous')
        country = body.get('country', 'NP')
        lat = body.get('latitude', 27.7172)
        lon = body.get('longitude', 85.3240)
        mesh = get_mesh_network()
        node = mesh.create_personal_node(user_id, country, lat, lon)
        connected = mesh.connect_to_peers(node.node_id, max_peers=5)
        return JSONResponse({
            "success": True,
            "node_id": node.node_id,
            "name": node.name,
            "connections": connected,
            "dharma_score": node.dharma_score,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get("/api/infrastructure/mesh/sovereign-nodes")
async def infra_mesh_sovereign_nodes():
    try:
        from core.infrastructure import get_mesh_network, NodeType
        mesh = get_mesh_network()
        sovereign = [n.to_dict() for n in mesh.nodes.values()
                    if n.node_type == NodeType.SOVEREIGN]
        return JSONResponse({
            "sovereign_nodes": sovereign,
            "total": len(sovereign),
            "by_country": {}
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/infrastructure/mesh/sync")
async def infra_mesh_sync(request: Request):
    try:
        from core.infrastructure import get_mesh_network
        body = await request.json()
        node_id = body.get('node_id')
        mesh = get_mesh_network()
        result = mesh.sync_data(node_id)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)})


def register_mesh_routes(app):
    app.include_router(router)
    logger.info("✅ Mesh, DHT, Network & Infrastructure routes registered")
