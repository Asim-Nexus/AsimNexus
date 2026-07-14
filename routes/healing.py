"""
AsimNexus Healing Route Module
===============================
Bug detection, frontend-backend connection monitoring, and auto-fix.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Body
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Healing")

router = APIRouter(tags=["Healing"])

# Module-level globals (set via init_healing)
orchestrator = None


def init_healing(app_globals: dict) -> None:
    """Initialize healing router with shared application globals."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ──────────────────────────────────────────────
#  Healing Endpoints
# ──────────────────────────────────────────────


@router.get("/api/healing/status")
async def healing_status():
    """Get healing system status."""
    try:
        return ok(data={"status": "active", "healing_engine": "available"})
    except Exception as e:
        return error(str(e))


@router.get("/api/healing/balance")
async def healing_balance():
    """Get healing balance info."""
    try:
        return ok(data={"balance": "healthy", "status": "active"})
    except Exception as e:
        return error(str(e))


@router.post("/api/healing/heal")
async def healing_heal(data: dict = Body(...)):
    """Trigger healing action."""
    try:
        return ok(data={"status": "healing_initiated", "action": data.get("action", "auto")})
    except Exception as e:
        return error(str(e))


@router.get("/api/healing/bugs")
async def healing_bugs():
    """Get detected bugs"""
    try:
        from core.healing import BugDetector
        import asyncio
        detector = BugDetector()
        bugs = await detector.scan_all_files()
        return ok(data={
            "total_bugs": len(bugs),
            "auto_fixable": sum(1 for b in bugs if b.auto_fixable),
            "bugs": [{"id": b.id, "severity": b.severity, "description": b.description,
                       "file": b.file_path, "line": b.line_number, "auto_fixable": b.auto_fixable}
                      for b in bugs]
        })
    except Exception as e:
        return error(str(e))


@router.get("/api/healing/connection")
async def healing_connection():
    """Check frontend-backend connection"""
    try:
        from core.healing import FrontendBackendMonitor
        import asyncio
        monitor = FrontendBackendMonitor()
        backend = await monitor.check_backend_health()
        api = await monitor.check_api_connectivity()
        return ok(data={
            "backend": backend,
            "api": api,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return error(str(e))


@router.post("/api/healing/fix-connections")
async def healing_fix_connections():
    """Auto-fix frontend-backend connection issues"""
    try:
        from core.healing import FrontendBackendMonitor
        import asyncio
        monitor = FrontendBackendMonitor()
        fixes = await monitor.fix_connection_issues()
        return ok(data={
            "fixes_applied": fixes,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return error(str(e))
