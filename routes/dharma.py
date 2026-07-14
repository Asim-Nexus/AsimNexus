"""
Dharma Routes
=============
REST API endpoints for the Nepal Digital Dharma Framework:
- Dharma Veto (constitutional veto system)
- Cultural Compiler (locale-aware cultural rule compilation)
- Cultural Sovereignty (country-specific cultural rule enforcement)
- Delta-T Engine (Proof of Symmetry — network balance)
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Body

from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Dharma")

router = APIRouter(prefix="/api/dharma", tags=["Dharma"])

_app_globals: dict = {}


def init_dharma(app_globals: dict) -> None:
    """Store app globals for lazy initialization."""
    global _app_globals
    _app_globals = app_globals


@router.get("/status")
async def dharma_status():
    """Get the overall status of the Dharma framework."""
    try:
        from core.dharma import get_nepal_dharma
        dharma = get_nepal_dharma()
        return ok(data={
            "framework": "Nepal Digital Dharma",
            "version": "1.0.0",
            "subsystems": {
                "cultural_compiler": "active",
                "cultural_sovereignty": "active",
                "delta_t_engine": "active",
                "dharma_veto": "active",
            },
        })
    except Exception as e:
        logger.warning(f"Dharma status error: {e}")
        return error(str(e), status_code=503)


@router.post("/veto/evaluate")
async def dharma_veto_evaluate(data: dict = Body(...)):
    """Evaluate an action through the Dharma Veto system."""
    try:
        from core.dharma import get_nepal_dharma
        dharma = get_nepal_dharma()
        action = data.get("action", "")
        params = data.get("params", {})
        result = dharma.check_action(action, params)
        return ok(data=result)
    except Exception as e:
        logger.warning(f"Dharma veto evaluate error: {e}")
        return error(str(e), status_code=500)


@router.get("/veto/history")
async def dharma_veto_history(limit: int = 50):
    """Get veto history."""
    try:
        from core.dharma import get_dharma_veto
        veto = get_dharma_veto()
        history = veto.get_history(limit=limit) if hasattr(veto, 'get_history') else []
        return ok(data={"history": history, "total": len(history)})
    except Exception as e:
        logger.warning(f"Dharma veto history error: {e}")
        return error(str(e), status_code=500)


@router.get("/cultural/profile")
async def dharma_cultural_profile(country_code: str = "NP"):
    """Get the cultural profile for a country."""
    try:
        from core.dharma import get_cultural_sovereignty_engine
        engine = get_cultural_sovereignty_engine()
        profile = engine.get_profile(country_code) if hasattr(engine, 'get_profile') else {}
        return ok(data={"country_code": country_code, "profile": profile})
    except Exception as e:
        logger.warning(f"Dharma cultural profile error: {e}")
        return error(str(e), status_code=500)


@router.post("/cultural/compile")
async def dharma_cultural_compile(data: dict = Body(...)):
    """Compile cultural rules for a given context."""
    try:
        from core.dharma import get_cultural_compiler
        compiler = get_cultural_compiler(data.get("locale", "ne_NP"))
        rules = compiler.compile(data.get("context", {})) if hasattr(compiler, 'compile') else []
        return ok(data={"locale": data.get("locale", "ne_NP"), "rules": rules})
    except Exception as e:
        logger.warning(f"Dharma cultural compile error: {e}")
        return error(str(e), status_code=500)


@router.get("/delta-t/status")
async def dharma_delta_t_status():
    """Get Delta-T Engine status."""
    try:
        from core.dharma import DeltaTEngine
        engine = DeltaTEngine()
        status = engine.get_status() if hasattr(engine, 'get_status') else {"status": "active"}
        return ok(data=status)
    except Exception as e:
        logger.warning(f"Delta-T status error: {e}")
        return error(str(e), status_code=500)


@router.post("/delta-t/simulate")
async def dharma_delta_t_simulate(data: dict = Body(...)):
    """Run a Proof of Symmetry simulation."""
    try:
        from core.dharma import run_pos_simulator
        nodes = data.get("nodes", [])
        result = run_pos_simulator(nodes)
        return ok(data=result)
    except Exception as e:
        logger.warning(f"Delta-T simulate error: {e}")
        return error(str(e), status_code=500)
