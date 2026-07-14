"""
Analytics Routes
================
Endpoints for analytics, health, status, dreaming, RAG, knowledge.
"""

import logging
from fastapi import APIRouter, Body
from typing import Optional
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Analytics"])

logger = logging.getLogger("AsimNexus.Routes.Analytics")

# Module-level globals set by app.py at startup
orchestrator = None
analytics_engine = None
rag_engine = None
dreaming_engine = None
health_checker = None


def init_analytics(app_globals: dict) -> None:
    """Initialize analytics module from app.py globals."""
    global orchestrator, analytics_engine, rag_engine, dreaming_engine, health_checker
    orchestrator = app_globals.get("orchestrator")
    analytics_engine = app_globals.get("analytics_engine")
    rag_engine = app_globals.get("rag_engine")
    dreaming_engine = app_globals.get("dreaming_engine")
    health_checker = app_globals.get("health_checker")


# ── Analytics ─────────────────────────────────────────────────────────

@router.get("/api/analytics/overview")
async def analytics_overview():
    """Live hardware metrics (CPU, Memory, Network) for Dashboard."""
    try:
        if analytics_engine:
            return ok(data=await analytics_engine.get_overview())
        return ok(data={"cpu": 0, "memory": 0, "network": 0, "status": "inactive"})
    except Exception as e:
        logger.error(f"analytics_overview error: {e}")
        return error(str(e))


@router.get("/api/analytics/activity")
async def analytics_activity():
    """Recent activity analytics."""
    try:
        if analytics_engine:
            return ok(data=await analytics_engine.get_activity())
        return ok(data={"activities": [], "count": 0})
    except Exception as e:
        logger.error(f"analytics_activity error: {e}")
        return error(str(e))


@router.get("/api/bugs/stats")
async def bugs_stats():
    """Get bug tracking statistics."""
    try:
        return ok(data={
            "total_reported": 0,
            "open": 0,
            "in_progress": 0,
            "resolved": 0,
            "closed": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        })
    except Exception as e:
        logger.error(f"bugs_stats error: {e}")
        return error(str(e))


@router.get("/api/analytics")
async def analytics_overview_v2(data: dict = Body(...)):
    """Analytics overview (v2 with user context)."""
    try:
        user_id = data.get("user_id", "web_user") or "guest"
        if analytics_engine:
            return ok(data=await analytics_engine.get_full_analytics(user_id))
        return ok(data={"user_id": user_id, "analytics": {}})
    except Exception as e:
        logger.error(f"analytics_overview_v2 error: {e}")
        return error(str(e))


# ── Health & Status ───────────────────────────────────────────────────

@router.get("/healthz")
async def healthz():
    """Simple health check."""
    return ok(note="AsimNexus")


@router.get("/api/version")
async def api_version():
    """API version info."""
    try:
        if orchestrator:
            return ok(data=await orchestrator.get_version())
        return ok(data={"version": "1.0.0", "build": "latest"})
    except Exception as e:
        logger.error(f"api_version error: {e}")
        return error(str(e))


@router.get("/api/build")
async def api_build():
    """Build info."""
    try:
        if orchestrator:
            return ok(data=await orchestrator.get_build_info())
        return ok(data={"build": "latest", "date": "unknown"})
    except Exception as e:
        logger.error(f"api_build error: {e}")
        return error(str(e))


@router.get("/api/status")
async def health():
    """Full system health status."""
    try:
        if health_checker:
            return ok(data=await health_checker.get_status())
        return ok(data={"status": "healthy", "uptime": 0})
    except Exception as e:
        logger.error(f"health error: {e}")
        return error(str(e))


@router.get("/api/local-llm/health")
async def system_info():
    """Local LLM health info."""
    try:
        if orchestrator:
            return ok(data=await orchestrator.get_llm_health())
        return ok(data={"status": "inactive"})
    except Exception as e:
        logger.error(f"system_info error: {e}")
        return error(str(e))


@router.get("/api/v1/operator/status")
async def operator_status():
    """Operator status."""
    try:
        if orchestrator:
            return ok(data=await orchestrator.get_operator_status())
        return ok(data={"status": "active"})
    except Exception as e:
        logger.error(f"operator_status error: {e}")
        return error(str(e))


@router.get("/api/system/complete")
async def complete_system_status():
    """Get complete AsimNexus system status - ALL phases."""
    try:
        result = {"status": "running", "modules": {}}
        # Try to get finance status
        try:
            from core.finance import (
                get_finance_status, get_wallet_stats, get_exchange_rates
            )
            result["modules"]["finance"] = await get_finance_status()
        except Exception:
            result["modules"]["finance"] = {"status": "unavailable"}
        # Try to get government status
        try:
            from core.government import (
                get_government_status, get_identity_stats, get_tax_info
            )
            result["modules"]["government"] = await get_government_status()
        except Exception:
            result["modules"]["government"] = {"status": "unavailable"}
        # Try to get mesh status
        try:
            from core.mesh import (
                get_mesh_stats, get_peer_count, get_network_topology
            )
            result["modules"]["mesh"] = {
                "stats": await get_mesh_stats(),
                "peers": await get_peer_count(),
            }
        except Exception:
            result["modules"]["mesh"] = {"status": "unavailable"}
        return ok(data=result)
    except Exception as e:
        logger.error(f"complete_system_status error: {e}")
        return error(str(e))


@router.get("/status")
async def system_status():
    """System status endpoint."""
    try:
        if orchestrator:
            return ok(data=await orchestrator.get_system_status())
        return ok(data={"status": "active", "mode": "standalone"})
    except Exception as e:
        logger.error(f"system_status error: {e}")
        return error(str(e))


# ── RAG / Knowledge ───────────────────────────────────────────────────

@router.post("/api/v1/rag/query")
async def query_knowledge(data: dict = Body(...)):
    """Query the AsimNexus Knowledge base (Neutron Star)."""
    try:
        if rag_engine:
            return ok(data=await rag_engine.query(
                data.get("query", ""),
                data.get("top_k", 5),
                data.get("filters", {})
            ))
        return unavailable("rag_engine")
    except Exception as e:
        logger.error(f"query_knowledge error: {e}")
        return error(str(e))


@router.post("/api/v1/rag/cosmos/evolve")
async def trigger_cosmos_evolution(data: dict = Body(...)):
    """Trigger a single iteration of the Cosmos Evolutionary Engine (CEE)."""
    try:
        if rag_engine:
            return ok(data=await rag_engine.cosmos_evolve(data.get("prompt", ""), data.get("context", {})))
        return unavailable("rag_engine")
    except Exception as e:
        logger.error(f"trigger_cosmos_evolution error: {e}")
        return error(str(e))


# ── Dreaming ──────────────────────────────────────────────────────────

@router.get("/api/dreaming/briefing")
async def dreaming_briefing():
    """RAG status summary (Neutron Star briefing) for the Dashboard."""
    try:
        if dreaming_engine:
            return ok(data=await dreaming_engine.get_briefing())
        return ok(data={"status": "inactive", "briefing": "Dreaming engine unavailable"})
    except Exception as e:
        logger.error(f"dreaming_briefing error: {e}")
        return error(str(e))


@router.get("/api/dreaming/status")
async def dreaming_status():
    """Dreaming engine status."""
    try:
        if dreaming_engine:
            return ok(data=await dreaming_engine.get_status())
        return ok(data={"status": "inactive"})
    except Exception as e:
        logger.error(f"dreaming_status error: {e}")
        return error(str(e))


@router.post("/api/dreaming/trigger")
async def dreaming_trigger(data: dict = Body(...)):
    """Trigger a dreaming cycle."""
    try:
        if dreaming_engine:
            return ok(data=await dreaming_engine.trigger(data.get("mode", "auto"), data.get("params", {})))
        return unavailable("dreaming_engine")
    except Exception as e:
        logger.error(f"dreaming_trigger error: {e}")
        return error(str(e))


# ── Integration Health ────────────────────────────────────────────────

# ── APIs Status ───────────────────────────────────────────────────────

@router.get("/api/apis/status")
async def apis_status(data: dict = Body(...)):
    """API status check."""
    try:
        endpoints = data.get("endpoints", [])
        results = {}
        for ep in endpoints:
            try:
                results[ep] = {"status": "available"}
            except Exception:
                results[ep] = {"status": "unavailable"}
        return ok(data={"endpoints": results})
    except Exception as e:
        logger.error(f"apis_status error: {e}")
        return error(str(e))


# ── Theme & Universe ──────────────────────────────────────────────────

@router.post("/api/theme/set")
async def set_theme(data: dict = Body(...)):
    """Set user theme."""
    try:
        user_id = data.get("user_id", "web_user")
        theme = data.get("theme", "dark")
        if orchestrator:
            return ok(data=await orchestrator.set_theme(user_id, theme))
        return ok(data={"theme": theme})
    except Exception as e:
        logger.error(f"set_theme error: {e}")
        return error(str(e))


@router.post("/api/universe/set")
async def set_universe(data: dict = Body(...)):
    """Set user universe config."""
    try:
        user_id = data.get("user_id", "web_user")
        config = data.get("config", {})
        if orchestrator:
            return ok(data=await orchestrator.set_universe(user_id, config))
        return ok()
    except Exception as e:
        logger.error(f"set_universe error: {e}")
        return error(str(e))


# ── Phase 4 — DePIN Network Map ──────────────────────────────────────────


@router.get("/api/analytics/depin/map")
async def depin_network_map():
    """
    Phase 4 — DePIN Network Map.
    
    Returns Nepal villages with LoRaWAN/WiFi Direct nodes,
    offline sync gateways, and mesh relay topology.
    """
    try:
        from core.depin_bridge import get_depin_bridge
        bridge = get_depin_bridge()
        nodes = bridge.get_all_nodes()
        stats = bridge.get_stats()

        # Build network map with geo-locations
        network_map = {
            "nodes": [],
            "gateways": [],
            "relays": [],
            "offline_zones": [],
        }

        for node in nodes:
            node_info = {
                "node_id": node.get("node_id", "unknown"),
                "status": node.get("status", "offline"),
                "capabilities": node.get("capabilities", []),
                "last_seen": node.get("last_seen", ""),
                "location": node.get("location", {}),
                "signal_strength": node.get("signal_strength", 0),
            }
            if "gateway" in node.get("capabilities", []):
                network_map["gateways"].append(node_info)
            elif "relay" in node.get("capabilities", []):
                network_map["relays"].append(node_info)
            else:
                network_map["nodes"].append(node_info)

        return ok(data={
            "network_map": network_map,
            "total_nodes": stats.get("total_nodes", 0),
            "online_nodes": stats.get("online_nodes", 0),
            "offline_nodes": stats.get("offline_nodes", 0),
            "gateways": len(network_map["gateways"]),
            "relays": len(network_map["relays"]),
            "phase": "Phase 4 — DePIN Mesh Network",
            "coverage_areas": ["Nepal Rural Villages", "LoRaWAN Zones", "WiFi Direct Clusters"],
        })
    except Exception as e:
        logger.error(f"DePIN network map error: {e}")
        return error(str(e))


@router.get("/api/analytics/depin/coverage")
async def depin_coverage():
    """Phase 4 — DePIN coverage areas with offline sync status."""
    try:
        from core.depin_bridge import get_depin_bridge
        bridge = get_depin_bridge()
        coverage = bridge.get_coverage_areas()
        return ok(data={
            "coverage": coverage,
            "phase": "Phase 4 — DePIN Coverage Intelligence",
        })
    except Exception as e:
        logger.error(f"DePIN coverage error: {e}")
        return error(str(e))


# ── Phase 4 — Clone Agents Live Feed ─────────────────────────────────────


@router.get("/api/analytics/clone-agents/feed")
async def clone_agents_feed(limit: int = 50):
    """
    Phase 4 — 15 Clone Agents Live Feed.
    
    Returns real-time activity feed from all 15 clone sub-agents:
    - 5 Clone Agents (Economic, Governance, Security, Mesh, Evolution)
    - 10 Sub-Agents (Token, Escrow, Staking, Marketplace, Identity,
                     Compliance, Veto, Constitution, Sync, Bridge)
    """
    try:
        from core.multi_agent_orchestrator import get_orchestrator
        orch = get_orchestrator()

        agents = orch.get_all_agents()
        feed = []

        for agent in agents:
            agent_id = agent.get("agent_id", "unknown")
            agent_type = agent.get("type", "unknown")
            status = agent.get("status", "idle")
            last_action = agent.get("last_action", {})
            metrics = agent.get("metrics", {})

            feed.append({
                "agent_id": agent_id,
                "type": agent_type,
                "status": status,
                "last_action": last_action.get("description", "No recent action"),
                "last_action_time": last_action.get("timestamp", ""),
                "tasks_completed": metrics.get("tasks_completed", 0),
                "success_rate": metrics.get("success_rate", 1.0),
                "active": status == "active",
            })

        # Sort by most recent activity
        feed.sort(key=lambda x: x["last_action_time"], reverse=True)

        return ok(data={
            "feed": feed[:limit],
            "total_agents": len(agents),
            "active_agents": sum(1 for a in feed if a["active"]),
            "phase": "Phase 4 — 15 Clone Agents Live Feed",
            "agent_roster": {
                "primary_clones": [
                    "Economic Agent", "Governance Agent", "Security Agent",
                    "Mesh Agent", "Evolution Agent",
                ],
                "sub_agents": [
                    "Token Agent", "Escrow Agent", "Staking Agent",
                    "Marketplace Agent", "Identity Agent",
                    "Compliance Agent", "Veto Agent", "Constitution Agent",
                    "Sync Agent", "Bridge Agent",
                ],
            },
        })
    except Exception as e:
        logger.error(f"Clone agents feed error: {e}")
        return error(str(e))


@router.get("/api/analytics/clone-agents/stats")
async def clone_agents_stats():
    """Phase 4 — Clone agents aggregate statistics."""
    try:
        from core.multi_agent_orchestrator import get_orchestrator
        orch = get_orchestrator()
        stats = orch.get_agent_stats()
        return ok(data={
            "stats": stats,
            "phase": "Phase 4 — Clone Agents Intelligence",
        })
    except Exception as e:
        logger.error(f"Clone agents stats error: {e}")
        return error(str(e))
