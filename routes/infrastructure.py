"""
AsimNexus Infrastructure Route Module
======================================
Infrastructure, CDN, platform, PWA, push notifications, and offline sync endpoints.
"""

import logging
from fastapi import APIRouter, Body
from typing import Optional
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Infrastructure")

router = APIRouter(tags=["Infrastructure"])

# Module-level globals (set via init_infrastructure)
orchestrator = None


def init_infrastructure(app_globals: dict) -> None:
    """Initialize infrastructure module with shared app state."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# â”€â”€â”€ Infrastructure Status â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.get("/api/infrastructure/status")
async def infrastructure_status():
    """Global infrastructure status (CDN + Mesh)"""
    try:
        from core.cdn import get_cdn_manager
        from core.mesh import get_mesh_coordinator

        cdn = get_cdn_manager()
        mesh = get_mesh_coordinator()
        mesh_stats = mesh.get_mesh_stats()

        return ok(data={
            "cdn": {
                "locations": len(cdn.get_locations()),
                "active_nodes": cdn.get_active_count(),
                "status": "operational" if cdn.is_healthy() else "degraded"
            },
            "mesh": {
                "nodes": mesh_stats.get("total_nodes", 0),
                "federation_status": "active",
                "status": "operational" if mesh_stats.get("total_nodes", 0) > 0 else "degraded"
            },
            "overall": "operational"
        })
    except Exception as e:
        logger.error(f"Infrastructure status error: {e}")
        return error(str(e))


# â”€â”€â”€ CDN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.get("/api/infrastructure/cdn/locations")
async def cdn_locations():
    """Get all CDN edge locations"""
    try:
        from core.cdn import get_cdn_manager
        cdn = get_cdn_manager()
        return ok(data={
            "locations": cdn.get_locations(),
            "count": len(cdn.get_locations())
        })
    except Exception as e:
        logger.error(f"CDN locations error: {e}")
        return error(str(e))


@router.get("/api/infrastructure/cdn/routing/{country_code}")
async def cdn_routing(country_code: str, lat: Optional[float] = None, lon: Optional[float] = None):
    """Get optimal CDN routing for a location"""
    try:
        from core.cdn import get_cdn_manager
        cdn = get_cdn_manager()
        route = cdn.get_optimal_route(country_code, lat, lon)
        return ok(data=route)
    except Exception as e:
        logger.error(f"CDN routing error: {e}")
        return error(str(e))


@router.get("/api/infrastructure/cdn/nearest")
async def cdn_nearest(lat: float, lon: float):
    """Find nearest CDN edge location"""
    try:
        from core.cdn import get_cdn_manager
        cdn = get_cdn_manager()
        nearest = cdn.get_nearest_node(lat, lon)
        return ok(data=nearest)
    except Exception as e:
        logger.error(f"CDN nearest error: {e}")
        return error(str(e))


# â”€â”€â”€ Mesh Infrastructure â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.get("/api/infrastructure/mesh/status")
async def mesh_status():
    """Federated mesh network status"""
    try:
        from core.mesh import get_mesh_coordinator
        mesh = get_mesh_coordinator()
        stats = mesh.get_mesh_stats()
        return ok(data={
            "status": "operational" if stats.get("total_nodes", 0) > 0 else "initializing",
            "nodes": stats.get("total_nodes", 0),
            "federation": "active",
            "healthy": stats.get("total_nodes", 0) > 0
        })
    except Exception as e:
        logger.error(f"Mesh status error: {e}")
        return error(str(e))


@router.get("/api/infrastructure/mesh/nodes")
async def mesh_nodes():
    """Get all mesh nodes"""
    try:
        from core.mesh import get_mesh_coordinator
        mesh = get_mesh_coordinator()
        nodes = [n.to_dict() for n in mesh.nodes.values()]
        return ok(data={
            "nodes": nodes,
            "count": len(nodes)
        })
    except Exception as e:
        logger.error(f"Mesh nodes error: {e}")
        return error(str(e))


@router.get("/api/infrastructure/mesh/nodes/{node_id}")
async def mesh_node_detail(node_id: str):
    """Get specific node details"""
    try:
        from core.mesh import get_mesh_coordinator
        mesh = get_mesh_coordinator()
        node = mesh.nodes.get(node_id)
        if not node:
            return error(f"Node {node_id} not found")
        return ok(data=node.to_dict())
    except Exception as e:
        logger.error(f"Mesh node detail error: {e}")
        return error(str(e))


@router.post("/api/infrastructure/mesh/join")
async def mesh_join(data: dict = Body(...)):
    """Join the federated mesh network"""
    try:
        from core.mesh import get_mesh_coordinator, NodeType
        mesh = get_mesh_coordinator()
        node_type_str = data.get("node_type", "personal")
        node_type = NodeType.PERSONAL
        for nt in NodeType:
            if nt.value == node_type_str:
                node_type = nt
                break
        result = mesh.initialize_local_node(
            node_type=node_type,
            name=data.get("name", "Anonymous Node"),
            country=data.get("country", "NP")
        )
        return ok(data=result.to_dict() if result else {"status": "joined"})
    except Exception as e:
        logger.error(f"Mesh join error: {e}")
        return error(str(e))


@router.get("/api/infrastructure/mesh/sovereign-nodes")
async def mesh_sovereign_nodes():
    """Get all sovereign/government nodes"""
    try:
        from core.mesh import get_mesh_coordinator, NodeType
        mesh = get_mesh_coordinator()
        nodes = [n.to_dict() for n in mesh.nodes.values() if n.node_type == NodeType.SOVEREIGN]
        return ok(data={
            "nodes": nodes,
            "count": len(nodes)
        })
    except Exception as e:
        logger.error(f"Sovereign nodes error: {e}")
        return error(str(e))


@router.post("/api/infrastructure/mesh/sync")
async def mesh_sync(data: dict = Body(...)):
    """Trigger mesh sync for a node"""
    try:
        from core.mesh import get_mesh_coordinator
        mesh = get_mesh_coordinator()
        stats = mesh.get_mesh_stats()
        return ok(data={
            "status": "synced",
            "node_id": data.get("node_id"),
            "full_sync": data.get("full_sync", False),
            "total_nodes": stats.get("total_nodes", 0)
        })
    except Exception as e:
        logger.error(f"Mesh sync error: {e}")
        return error(str(e))


# â”€â”€â”€ Platform â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.get("/api/platform/status")
async def platform_status():
    """Get platform support status"""
    try:
        from core.platform import get_platform_manager
        pm = get_platform_manager()
        return ok(data=pm.get_status())
    except Exception as e:
        logger.error(f"Platform status error: {e}")
        return error(str(e))


@router.post("/api/platform/register")
async def platform_register(data: dict = Body(...)):
    """Register a device/platform session"""
    try:
        from core.platform import get_platform_manager
        pm = get_platform_manager()
        result = pm.register_session(
            platform=data.get("platform", "web"),
            device_id=data.get("device_id"),
            user_agent=data.get("user_agent", ""),
            user_id=data.get("user_id", "anonymous")
        )
        return ok(data=result)
    except Exception as e:
        logger.error(f"Platform register error: {e}")
        return error(str(e))


@router.get("/api/platform/downloads")
async def platform_downloads():
    """Get download links for all platforms"""
    try:
        from core.platform import get_platform_manager
        pm = get_platform_manager()
        return ok(data=pm.get_downloads())
    except Exception as e:
        logger.error(f"Platform downloads error: {e}")
        return error(str(e))


# â”€â”€â”€ Microkernel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/api/microkernel/status")
async def microkernel_status():
    """Get microkernel status."""
    try:
        from core.kernel.microkernel import ASIMMicrokernel
        kernel = ASIMMicrokernel()
        return ok(data=kernel.get_status())
    except Exception as e:
        logger.error(f"Microkernel status error: {e}")
        return error(str(e))


@router.post("/api/microkernel/plugin/load")
async def microkernel_load_plugin(plugin_id: str = Body(..., embed=True),
                                 plugin_module: str = Body(..., embed=True)):
    """Load a plugin."""
    try:
        from core.kernel.microkernel import ASIMMicrokernel
        kernel = ASIMMicrokernel()
        result = kernel.load_plugin(plugin_id, plugin_module)
        return ok(data=result)
    except Exception as e:
        logger.error(f"Plugin load error: {e}")
        return error(str(e))


@router.post("/api/microkernel/plugin/unload")
async def microkernel_unload_plugin(plugin_id: str = Body(..., embed=True)):
    """Unload a plugin."""
    try:
        from core.kernel.microkernel import ASIMMicrokernel
        kernel = ASIMMicrokernel()
        result = kernel.unload_plugin(plugin_id)
        return ok(data=result)
    except Exception as e:
        logger.error(f"Plugin unload error: {e}")
        return error(str(e))


# â”€â”€â”€ Language Support â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/api/language/status")
async def language_status():
    """Get current language status."""
    try:
        from core.language_manager import get_language_manager
        lm = get_language_manager()
        return ok(data=lm.get_status())
    except Exception as e:
        logger.error(f"Language status error: {e}")
        return error(str(e))


@router.post("/api/language/set")
async def language_set(lang_code: str = Body(..., embed=True)):
    """Set current language."""
    try:
        from core.language_manager import get_language_manager
        lm = get_language_manager()
        result = lm.set_language(lang_code)
        return ok(data=result)
    except Exception as e:
        logger.error(f"Language set error: {e}")
        return error(str(e))


@router.post("/api/federation/peer/add")
async def federation_add_peer(did: str = Body(..., embed=True),
                             endpoint: str = Body(..., embed=True)):
    """Add a federation peer."""
    try:
        from core.federation.global_federation import get_federation
        fed = get_federation()
        peer = fed.add_peer(did, endpoint)
        return ok(data=peer)
    except Exception as e:
        logger.error(f"Add peer error: {e}")
        return error(str(e))


@router.post("/api/federation/peer/consent")
async def federation_consent_peer(peer_id: str = Body(..., embed=True)):
    """Consent to sync with a peer."""
    try:
        from core.federation.global_federation import get_federation
        fed = get_federation()
        fed.consent_peer(peer_id)
        return ok(data={"status": "consented", "peer_id": peer_id})
    except Exception as e:
        logger.error(f"Consent error: {e}")
        return error(str(e))


# â”€â”€â”€ Plugin Marketplace â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/api/marketplace/apps")
async def marketplace_list(category: Optional[str] = None):
    """List apps in marketplace."""
    try:
        from core.plugin_marketplace import get_marketplace
        mp = get_marketplace()
        return ok(data=mp.list_apps(category))
    except Exception as e:
        logger.error(f"Marketplace list error: {e}")
        return error(str(e))


@router.get("/api/marketplace/apps/{app_id}")
async def marketplace_get(app_id: str):
    """Get specific app details."""
    try:
        from core.plugin_marketplace import get_marketplace
        mp = get_marketplace()
        app = mp.get_app(app_id)
        if not app:
            return error("App not found")
        return ok(data=app)
    except Exception as e:
        logger.error(f"Marketplace get error: {e}")
        return error(str(e))

# â”€â”€â”€ AI Improvements â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/api/ai/status")
async def ai_status():
    """Get AI improvements status."""
    try:
        from core.ai_improvements import get_nepali_fine_tuner, get_multimodal_processor
        tuner = get_nepali_fine_tuner()
        mm = get_multimodal_processor()
        return ok(data={
            "nepali_finetuning": tuner.get_status(),
            "multimodal": {"capabilities": mm.get_capabilities()}
        })
    except Exception as e:
        logger.error(f"AI status error: {e}")
        return error(str(e))


@router.post("/api/ai/finetune/nepali")
async def ai_finetune_nepali(model: str = Body(..., embed=True)):
    """Fine-tune model on Nepali language."""
    try:
        from core.ai_improvements import get_nepali_fine_tuner
        tuner = get_nepali_fine_tuner()
        result = tuner.fine_tune(model)
        return ok(data=result)
    except Exception as e:
        logger.error(f"Finetune error: {e}")
        return error(str(e))

# â”€â”€â”€ Nepal Government Layer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/api/nepal/ministries")
async def nepal_ministries():
    """Get all Nepal ministries."""
    try:
        from core.gateway.nepal.government import MINISTRIES
        return ok(data=list(MINISTRIES.values()))
    except Exception as e:
        logger.error(f"Nepal ministries error: {e}")
        return error(str(e))


@router.get("/api/nepal/provinces")
async def nepal_provinces():
    """Get all Nepal provinces."""
    try:
        from core.gateway.nepal.government import PROVINCES
        return ok(data=list(PROVINCES.values()))
    except Exception as e:
        logger.error(f"Nepal provinces error: {e}")
        return error(str(e))


@router.get("/api/nepal/districts")
async def nepal_districts(province: Optional[str] = None):
    """Get Nepal districts, optionally filtered by province."""
    try:
        from core.gateway.nepal.government import DISTRICTS
        if province:
            filtered = [d for d in DISTRICTS.values() if d["province"] == province]
            return ok(data=filtered)
        return ok(data=list(DISTRICTS.values()))
    except Exception as e:
        logger.error(f"Nepal districts error: {e}")
        return error(str(e))


@router.get("/api/nepal/gov-layer/status")
async def nepal_gov_layer_status():
    """Get Nepal government layer status."""
    try:
        from core.governance.national_gov_layer import get_national_gov_layer
        layer = get_national_gov_layer()
        return ok(data=layer.get_stats())
    except Exception as e:
        logger.error(f"Gov layer status error: {e}")
        return error(str(e))


@router.post("/api/nepal/gov-layer/submit")
async def nepal_gov_layer_submit(
    action_type: str = Body(..., embed=True),
    entity: str = Body(..., embed=True),
    jurisdiction: str = Body(..., embed=True),
    description: str = Body(..., embed=True)
):
    """Submit government action for Nepal."""
    try:
        from core.governance.national_gov_layer import (
            get_national_gov_layer, GovernmentActionType, OversightSector
        )
        layer = get_national_gov_layer()
        action_type_enum = GovernmentActionType(action_type) if action_type in [a.value for a in GovernmentActionType] else GovernmentActionType.DATA_REQUEST
        sector = OversightSector.INFRASTRUCTURE if action_type == "infrastructure" else None
        result = layer.submit_action(
            action_type=action_type_enum,
            government_entity=entity,
            jurisdiction=jurisdiction,
            description=description,
            sector=sector
        )
        return ok(data={"action_id": result})
    except Exception as e:
        logger.error(f"Gov layer submit error: {e}")
        return error(str(e))

@router.get("/api/consensus/status")
async def consensus_status():
    """Get consensus engine status."""
    try:
        from core.consensus.clone_consensus_voting import get_consensus_engine
        engine = get_consensus_engine()
        return ok(data=engine.get_stats())
    except Exception as e:
        logger.error(f"Consensus status error: {e}")
        return error(str(e))



