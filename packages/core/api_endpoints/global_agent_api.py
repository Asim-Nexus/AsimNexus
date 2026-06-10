#!/usr/bin/env python3
"""
ASIMNEXUS Global Agent Mode API
================================
Global agent orchestration for worldwide ASIMNEXUS deployment.

This module enables:
- Global agent coordination across mesh networks
- Multi-region deployment management
- Worldwide node discovery and synchronization
- Cross-border governance compliance
- 100% Personal OS operation from anywhere in the world
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Body

logger = logging.getLogger("AsimNexus.API.GlobalAgent")

router = APIRouter()


class GlobalAgentMode:
    """
    Global Agent Mode orchestrator.
    Manages worldwide ASIMNEXUS node coordination.
    """

    def __init__(self):
        self.mode_active = False
        self.deployed_regions: Dict[str, Dict[str, Any]] = {}
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.global_config: Dict[str, Any] = self._default_config()
        self._audit_log: List[Dict[str, Any]] = []
        logger.info("🌍 Global Agent Mode initialized")

    def _default_config(self) -> Dict[str, Any]:
        return {
            "mode": "personal_os",
            "government_share": 0.51,
            "private_share": 0.49,
            "personal_os_enabled": True,
            "global_discovery": True,
            "cross_border_sync": True,
            "mesh_routing": "auto",
            "audit_level": "full",
            "regions": ["global"],
            "max_agents": 1000,
            "heartbeat_interval": 30,
        }

    def activate(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Activate global agent mode."""
        if config:
            self.global_config.update(config)
        self.mode_active = True
        self._audit("global_mode_activated")
        return {
            "status": "activated",
            "mode": self.global_config["mode"],
            "government_share": self.global_config["government_share"],
            "private_share": self.global_config["private_share"],
            "personal_os": self.global_config["personal_os_enabled"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    def deactivate(self) -> Dict[str, Any]:
        """Deactivate global agent mode."""
        self.mode_active = False
        self._audit("global_mode_deactivated")
        return {"status": "deactivated", "timestamp": datetime.utcnow().isoformat()}

    def register_region(self, region_id: str, name: str, endpoint: str,
                        region_type: str = "auto") -> Dict[str, Any]:
        """Register a deployment region."""
        if region_id in self.deployed_regions:
            return {"error": "Region already registered", "region_id": region_id}

        self.deployed_regions[region_id] = {
            "region_id": region_id,
            "name": name,
            "endpoint": endpoint,
            "region_type": region_type,
            "status": "active",
            "agent_count": 0,
            "registered_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat(),
        }
        self._audit("region_registered", region_id)
        return {"status": "registered", "region_id": region_id, "name": name}

    def register_agent(self, agent_id: str, agent_type: str, region_id: str,
                       capabilities: Optional[List[str]] = None) -> Dict[str, Any]:
        """Register a global agent."""
        if agent_id in self.active_agents:
            return {"error": "Agent already registered", "agent_id": agent_id}
        if region_id not in self.deployed_regions:
            return {"error": "Region not found", "region_id": region_id}

        self.active_agents[agent_id] = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "region_id": region_id,
            "capabilities": capabilities or [],
            "status": "active",
            "tasks_completed": 0,
            "registered_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat(),
        }
        self.deployed_regions[region_id]["agent_count"] += 1
        self._audit("agent_registered", agent_id, {"region_id": region_id})
        return {"status": "registered", "agent_id": agent_id, "region": region_id}

    def deploy_to_region(self, region_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy ASIMNEXUS to a region."""
        if region_id not in self.deployed_regions:
            return {"error": "Region not registered", "region_id": region_id}

        self.deployed_regions[region_id].update({
            "deployed": True,
            "deployed_at": datetime.utcnow().isoformat(),
            "deploy_config": config,
        })
        self._audit("region_deployed", region_id)
        return {"status": "deployed", "region_id": region_id}

    def get_status(self) -> Dict[str, Any]:
        """Get global agent mode status."""
        return {
            "mode_active": self.mode_active,
            "mode": self.global_config["mode"],
            "regions": len(self.deployed_regions),
            "active_agents": len(self.active_agents),
            "government_share": self.global_config["government_share"],
            "private_share": self.global_config["private_share"],
            "personal_os": self.global_config["personal_os_enabled"],
            "config": self.global_config,
            "regions_detail": {
                rid: {"name": r["name"], "status": r["status"], "agent_count": r["agent_count"]}
                for rid, r in self.deployed_regions.items()
            },
        }

    def get_global_overview(self) -> Dict[str, Any]:
        """Get full global deployment overview."""
        return {
            "global_mode": self.mode_active,
            "total_regions": len(self.deployed_regions),
            "total_agents": len(self.active_agents),
            "regions": list(self.deployed_regions.values()),
            "agents": list(self.active_agents.values()),
            "config": self.global_config,
            "audit_entries": len(self._audit_log),
        }

    def _audit(self, action: str, resource_id: str = "", details: Optional[Dict] = None) -> None:
        self._audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "resource_id": resource_id,
            "details": details or {},
        })

    def reset(self) -> None:
        """Reset global agent mode (for testing)."""
        self.mode_active = False
        self.deployed_regions.clear()
        self.active_agents.clear()
        self.global_config = self._default_config()
        self._audit_log.clear()


# ─── SINGLETON ────────────────────────────────────────────────────────────

_global_agent_instance = None
_global_agent_lock = asyncio.Lock()


async def get_global_agent() -> GlobalAgentMode:
    global _global_agent_instance
    if _global_agent_instance is None:
        async with _global_agent_lock:
            if _global_agent_instance is None:
                _global_agent_instance = GlobalAgentMode()
    return _global_agent_instance


def reset_global_agent() -> None:
    global _global_agent_instance
    if _global_agent_instance:
        _global_agent_instance.reset()
    _global_agent_instance = None


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL AGENT API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/api/global/activate", tags=["Global Agent"])
async def activate_global_mode(req: dict = Body({})):
    """Activate global agent mode for worldwide deployment."""
    engine = await get_global_agent()
    return engine.activate(req.get("config"))

@router.post("/api/global/deactivate", tags=["Global Agent"])
async def deactivate_global_mode():
    """Deactivate global agent mode."""
    engine = await get_global_agent()
    return engine.deactivate()

@router.post("/api/global/regions", tags=["Global Agent"])
async def register_region(req: dict = Body(...)):
    """Register a deployment region."""
    engine = await get_global_agent()
    return engine.register_region(
        region_id=req.get("region_id"),
        name=req.get("name"),
        endpoint=req.get("endpoint"),
        region_type=req.get("region_type", "auto"),
    )

@router.post("/api/global/regions/{region_id}/deploy", tags=["Global Agent"])
async def deploy_region(region_id: str, req: dict = Body({})):
    """Deploy to a registered region."""
    engine = await get_global_agent()
    return engine.deploy_to_region(region_id, req.get("config", {}))

@router.post("/api/global/agents", tags=["Global Agent"])
async def register_agent(req: dict = Body(...)):
    """Register a global agent."""
    engine = await get_global_agent()
    return engine.register_agent(
        agent_id=req.get("agent_id"),
        agent_type=req.get("agent_type"),
        region_id=req.get("region_id"),
        capabilities=req.get("capabilities"),
    )

@router.get("/api/global/status", tags=["Global Agent"])
async def global_status():
    """Get global agent mode status."""
    engine = await get_global_agent()
    return engine.get_status()

@router.get("/api/global/overview", tags=["Global Agent"])
async def global_overview():
    """Get full global deployment overview."""
    engine = await get_global_agent()
    return engine.get_global_overview()
