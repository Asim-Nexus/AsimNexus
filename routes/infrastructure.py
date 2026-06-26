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


# ─── Infrastructure Status ───────────────────────────────────────────────────


@router.get("/api/infrastructure/status")
async def infrastructure_status():
    """Global infrastructure status (CDN + Mesh)"""
    try:
        from core.cdn import get_cdn_manager
        from core.mesh import get_mesh_network

        cdn = get_cdn_manager()
        mesh = get_mesh_network()

        return ok(data={
            "cdn": {
                "locations": len(cdn.get_locations()),
                "active_nodes": cdn.get_active_count(),
                "status": "operational" if cdn.is_healthy() else "degraded"
            },
            "mesh": {
                "nodes": len(mesh.get_all_nodes()),
                "federation_status": mesh.get_federation_status(),
                "status": "operational" if mesh.is_healthy() else "degraded"
            },
            "overall": "operational"
        })
    except Exception as e:
        logger.error(f"Infrastructure status error: {e}")
        return error(str(e))


# ─── CDN ─────────────────────────────────────────────────────────────────────


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


# ─── Mesh Infrastructure ─────────────────────────────────────────────────────


@router.get("/api/infrastructure/mesh/status")
async def mesh_status():
    """Federated mesh network status"""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        return ok(data={
            "status": mesh.get_status(),
            "nodes": len(mesh.get_all_nodes()),
            "federation": mesh.get_federation_status(),
            "healthy": mesh.is_healthy()
        })
    except Exception as e:
        logger.error(f"Mesh status error: {e}")
        return error(str(e))


@router.get("/api/infrastructure/mesh/nodes")
async def mesh_nodes():
    """Get all mesh nodes"""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        nodes = mesh.get_all_nodes()
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
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        node = mesh.get_node(node_id)
        if not node:
            return error(f"Node {node_id} not found")
        return ok(data=node)
    except Exception as e:
        logger.error(f"Mesh node detail error: {e}")
        return error(str(e))


@router.post("/api/infrastructure/mesh/join")
async def mesh_join(data: dict = Body(...)):
    """Join the federated mesh network"""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        result = mesh.join_federation(
            node_id=data.get("node_id"),
            capabilities=data.get("capabilities", []),
            location=data.get("location", {})
        )
        return ok(data=result)
    except Exception as e:
        logger.error(f"Mesh join error: {e}")
        return error(str(e))


@router.get("/api/infrastructure/mesh/sovereign-nodes")
async def mesh_sovereign_nodes():
    """Get all sovereign/government nodes"""
    try:
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        nodes = mesh.get_sovereign_nodes()
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
        from core.mesh import get_mesh_network
        mesh = get_mesh_network()
        result = mesh.trigger_sync(
            node_id=data.get("node_id"),
            full_sync=data.get("full_sync", False)
        )
        return ok(data=result)
    except Exception as e:
        logger.error(f"Mesh sync error: {e}")
        return error(str(e))


# ─── Platform ────────────────────────────────────────────────────────────────


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


# ─── Microkernel ───────────────────────────────────────────────────────────────

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


# ─── Language Support ────────────────────────────────────────────────────────────

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
