"""
AsimNexus Sovereignty Route Module
===================================
Sovereignty, air-gap, cultural compliance, and Dharma influence endpoints.
"""

import logging
from fastapi import APIRouter, Body
from typing import Optional
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Sovereignty")

router = APIRouter(tags=["Sovereignty"])

# Module-level globals (set via init_sovereignty)
orchestrator = None


def init_sovereignty(app_globals: dict) -> None:
    """Initialize sovereignty module with shared app state."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ─── Air-Gap ────────────────────────────────────────────────────────────────


@router.get("/api/sovereignty/airgap/status")
async def airgap_status():
    """Get air-gap status"""
    try:
        from core.sovereignty import get_emergency_air_gap
        return ok(data=get_emergency_air_gap().get_status())
    except Exception as e:
        return error(str(e))


@router.post("/api/sovereignty/airgap/activate")
async def airgap_activate(data: dict = Body(...)):
    """Activate air-gap mode"""
    try:
        from core.sovereignty import get_emergency_air_gap, AirGapMode
        import asyncio

        mode = AirGapMode(data.get('mode', 'partial'))
        reason = data.get('reason', 'User requested')
        user_id = data.get('user_id', 'anonymous')

        result = asyncio.run(get_emergency_air_gap().activate_air_gap(
            mode, reason, user_id
        ))

        return ok(data=result)
    except Exception as e:
        return error(str(e))


@router.post("/api/sovereignty/airgap/restore")
async def airgap_restore(data: dict = Body(...)):
    """Restore connection from air-gap"""
    try:
        from core.sovereignty import get_emergency_air_gap
        import asyncio

        user_id = data.get('user_id', 'anonymous')
        verify = data.get('verify_integrity', True)

        result = asyncio.run(get_emergency_air_gap().restore_connection(
            user_id, verify
        ))

        return ok(data=result)
    except Exception as e:
        return error(str(e))


@router.get("/api/sovereignty/airgap/history")
async def airgap_history():
    """Get air-gap activation history"""
    try:
        from core.sovereignty import get_emergency_air_gap
        return ok(data={
            "history": get_emergency_air_gap().get_emergency_history()
        })
    except Exception as e:
        return error(str(e))


# ─── Cultural Sovereignty ────────────────────────────────────────────────────


@router.post("/api/sovereignty/check")
async def check_cultural_compliance(data: dict = Body(...)):
    """Check action against country cultural rules"""
    try:
        from core.dharma.cultural_sovereignty import get_cultural_sovereignty_engine

        engine = get_cultural_sovereignty_engine()

        result = engine.check_action(
            country_code=data.get("country_code", "NP"),
            action=data.get("action"),
            params=data.get("params", {})
        )

        return ok(data=result)
    except Exception as e:
        logger.error(f"Cultural check error: {e}")
        return error(str(e))


@router.get("/api/sovereignty/countries")
async def list_countries():
    """List all countries with cultural rules"""
    try:
        from core.dharma.cultural_sovereignty import get_cultural_sovereignty_engine

        engine = get_cultural_sovereignty_engine()
        countries = engine.list_countries()

        return ok(data={
            "countries": countries,
            "count": len(countries)
        })
    except Exception as e:
        logger.error(f"Country list error: {e}")
        return error(str(e))


@router.get("/api/sovereignty/country/{country_code}")
async def get_country_profile(country_code: str):
    """Get cultural profile for specific country"""
    try:
        from core.dharma.cultural_sovereignty import get_cultural_sovereignty_engine

        engine = get_cultural_sovereignty_engine()
        profile = engine.get_country_profile(country_code)

        if not profile:
            return error(f"Country {country_code} not found")

        return ok(data=profile)
    except Exception as e:
        logger.error(f"Country profile error: {e}")
        return error(str(e))


@router.get("/api/sovereignty/report")
async def get_sovereignty_report():
    """Get global cultural sovereignty compliance report"""
    try:
        from core.dharma.cultural_sovereignty import get_cultural_sovereignty_engine

        engine = get_cultural_sovereignty_engine()
        report = engine.get_global_compliance_report()

        return ok(data=report)
    except Exception as e:
        logger.error(f"Sovereignty report error: {e}")
        return error(str(e))


# ─── Dharma Influence ────────────────────────────────────────────────────────


@router.get("/api/dharma/influence/status")
async def influence_status():
    """Get real-time influence monitoring status"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration
        integration = await get_delta_t_integration()
        return ok(data=await integration.get_current_status())
    except Exception as e:
        return error(str(e))


@router.get("/api/dharma/influence/history")
async def influence_history(
    entity_id: str = None,
    since: str = None,
    limit: int = 100):
    """Get influence history"""
    return ok(data={"history": [], "entity_id": entity_id, "since": since, "limit": limit})


@router.post("/api/dharma/influence/record")
async def record_influence(data: dict = Body(...)):
    """Record influence event (called by system)"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration

        integration = await get_delta_t_integration()
        record = await integration.record_influence(
            entity_id=data.get("entity_id"),
            entity_type=data.get("entity_type"),
            action_type=data.get("action_type"),
            details=data.get("details", {})
        )

        return ok(data={
            "record_id": record.id,
            "influence_score": record.influence_score,
            "delta_t_score": record.delta_t_score,
            "veto_status": record.veto_status,
            "message": "Influence recorded successfully"
        })
    except Exception as e:
        return error(str(e))


@router.post("/api/dharma/veto/manual")
async def manual_veto(data: dict = Body(...)):
    """Manual veto by human user"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration

        integration = await get_delta_t_integration()
        success = await integration.manual_veto(
            record_id=data.get("record_id"),
            reason=data.get("reason", "Manual veto by user"),
            user_id=data.get("user_id", "anonymous")
        )

        if success:
            return ok(data={
                "success": True,
                "message": "Veto applied successfully"
            })
        else:
            return error("Record not found")

    except Exception as e:
        return error(str(e))


@router.post("/api/dharma/monitoring/start")
async def start_monitoring(data: dict = Body(...)):
    """Start real-time influence monitoring"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration

        interval = data.get("interval_seconds", 30)

        integration = await get_delta_t_integration()
        await integration.start_monitoring(interval)

        return ok(data={
            "success": True,
            "monitoring_active": True,
            "interval_seconds": interval,
            "message": "Real-time monitoring started"
        })
    except Exception as e:
        return error(str(e))


@router.post("/api/dharma/monitoring/stop")
async def stop_monitoring():
    """Stop real-time influence monitoring"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration

        integration = await get_delta_t_integration()
        await integration.stop_monitoring()

        return ok(data={
            "success": True,
            "monitoring_active": False,
            "message": "Monitoring stopped"
        })
    except Exception as e:
        return error(str(e))


@router.get("/api/dharma/mesh/status")
async def delta_t_mesh_status():
    """Get mesh-wide ΔT status"""
    try:
        from core.dharma.delta_t_mesh import get_delta_t_mesh

        mesh_integration = await get_delta_t_mesh()
        return ok(data=mesh_integration.get_mesh_status())
    except Exception as e:
        return error(str(e))


# ─── Veto Configuration ──────────────────────────────────────────────────────


@router.get("/api/dharma/veto/config")
async def get_veto_config():
    """Get auto-veto configuration"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration

        integration = await get_delta_t_integration()

        return ok(data={
            "auto_veto_enabled": integration.auto_veto_enabled,
            "influence_threshold": integration.influence_threshold,
            "threshold_percent": f"{integration.influence_threshold * 100:.1f}%",
            "monitoring_active": integration.monitoring_active,
            "sync_interval_seconds": integration.sync_interval if hasattr(integration, 'sync_interval') else 60,
            "description": "Auto-veto triggers when Gini coefficient exceeds threshold"
        })
    except Exception as e:
        logger.error(f"Veto config error: {e}")
        return error(str(e))


@router.post("/api/dharma/veto/config")
async def update_veto_config(data: dict = Body(...)):
    """Update auto-veto configuration"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration

        integration = await get_delta_t_integration()

        # Update settings
        if 'auto_veto_enabled' in data:
            integration.auto_veto_enabled = data['auto_veto_enabled']

        if 'influence_threshold' in data:
            threshold = float(data['influence_threshold'])
            if 0 < threshold <= 1:
                integration.influence_threshold = threshold
            else:
                return error("Threshold must be between 0 and 1")

        return ok(data={
            "success": True,
            "message": "Auto-veto configuration updated",
            "config": {
                "auto_veto_enabled": integration.auto_veto_enabled,
                "influence_threshold": integration.influence_threshold
            }
        })
    except Exception as e:
        logger.error(f"Veto config update error: {e}")
        return error(str(e))


@router.get("/api/dharma/veto/pending")
async def get_pending_vetos():
    """Get all pending veto events"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration

        integration = await get_delta_t_integration()

        # Get recent calculations with pending veto status
        pending = [
            {
                "record_id": calc.get('record_id'),
                "entity_id": calc.get('entity_id'),
                "influence_score": calc.get('influence'),
                "delta_t_score": calc.get('delta_t'),
                "timestamp": calc.get('timestamp'),
                "veto_status": calc.get('veto_status')
            }
            for calc in integration.recent_calculations
            if calc.get('veto_status') == 'pending'
        ]

        return ok(data={
            "pending_count": len(pending),
            "pending_vetos": pending,
            "auto_veto_enabled": integration.auto_veto_enabled
        })
    except Exception as e:
        logger.error(f"Pending vetos error: {e}")
        return error(str(e))


@router.get("/api/dharma/veto/history")
async def get_veto_history(limit: int = 100):
    """Get veto history from database"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration

        integration = await get_delta_t_integration()

        # Get vetoed records
        records = await integration.get_influence_history(
            since=None,
            limit=limit
        )

        vetoed = [
            {
                "record_id": r.id,
                "entity_id": r.entity_id,
                "entity_type": r.entity_type,
                "influence_score": r.influence_score,
                "veto_status": r.veto_status,
                "timestamp": r.timestamp.isoformat(),
                "action_type": r.action_type
            }
            for r in records
            if r.veto_status in ['vetoed', 'pending']
        ]

        return ok(data={
            "total_vetos": len(vetoed),
            "vetos": vetoed
        })
    except Exception as e:
        logger.error(f"Veto history error: {e}")
        return error(str(e))


@router.post("/api/dharma/veto/release/{record_id}")
async def release_veto(record_id: str, data: dict = Body(...)):
    """Release/approve a vetoed action (human override)"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration
        import json
        from datetime import datetime

        reason = data.get("reason", "Manual override by admin")
        user_id = data.get("user_id", "admin")

        integration = await get_delta_t_integration()

        # Update record to approved
        if integration.local_db:
            integration.local_db.update('influence_records', record_id, {
                'veto_status': 'approved',
                'details': json.dumps({
                    'release_reason': reason,
                    'released_by': user_id,
                    'released_at': datetime.now().isoformat()
                })
            })

        return ok(data={
            "success": True,
            "record_id": record_id,
            "new_status": "approved",
            "released_by": user_id,
            "reason": reason
        })
    except Exception as e:
        logger.error(f"Veto release error: {e}")
        return error(str(e))


@router.get("/api/dharma/enforcement/status")
async def get_enforcement_status():
    """Get overall Dharma enforcement status"""
    try:
        from core.dharma.delta_t_integration import get_delta_t_integration

        integration = await get_delta_t_integration()

        # Get current ΔT status
        delta_t_status = await integration.get_current_status()

        return ok(data={
            "delta_t": delta_t_status['delta_t'],
            "auto_veto": {
                "enabled": delta_t_status['auto_veto_enabled'],
                "threshold": delta_t_status['threshold']
            },
            "monitoring": {
                "active": delta_t_status['monitoring_active'],
                "recent_high_influence": delta_t_status['recent_high_influence_events']
            },
            "database_stats": delta_t_status['database_stats'],
            "system_health": "healthy" if delta_t_status['delta_t']['gini_coefficient'] < 0.1 else "warning"
        })
    except Exception as e:
        logger.error(f"Enforcement status error: {e}")
        return error(str(e))
