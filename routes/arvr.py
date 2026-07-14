"""
AsimNexus AR/VR Interface Routes
=================================
Exposes the AR/VR immersive interface via REST API.
Allows creating spatial elements, registering gestures,
triggering haptic feedback, and querying interface state.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

logger = logging.getLogger("AsimNexus.Routes.ARVR")

router = APIRouter()

# Global reference — set by init_arvr()
_arvr_interface = None


def init_arvr(app_globals: dict) -> None:
    """Initialize AR/VR interface singleton."""
    global _arvr_interface
    try:
        from frontend.arvr.interface import get_arvr_interface
        _arvr_interface = get_arvr_interface()
        logger.info("✅ AR/VR Interface initialized")
    except Exception as e:
        logger.warning(f"⚠️ AR/VR Interface not available: {e}")
        _arvr_interface = None


def _get_arvr():
    """Get AR/VR interface singleton."""
    global _arvr_interface
    if _arvr_interface is None:
        try:
            from frontend.arvr.interface import get_arvr_interface
            _arvr_interface = get_arvr_interface()
        except Exception as e:
            logger.warning(f"⚠️ AR/VR Interface unavailable: {e}")
    return _arvr_interface


@router.get("/api/arvr/status")
async def arvr_status():
    """Get AR/VR interface status."""
    arvr = _get_arvr()
    if arvr is None:
        return unavailable("AR/VR interface")
    try:
        stats = arvr.get_interface_stats()
        return ok(data=stats)
    except Exception as e:
        logger.error(f"AR/VR status error: {e}")
        return error(str(e))


@router.get("/api/arvr/scene")
async def arvr_scene():
    """Get current spatial scene."""
    arvr = _get_arvr()
    if arvr is None:
        return unavailable("AR/VR interface")
    try:
        scene = arvr.get_spatial_scene()
        return ok(data=scene)
    except Exception as e:
        logger.error(f"AR/VR scene error: {e}")
        return error(str(e))


@router.post("/api/arvr/mode")
async def arvr_set_mode(data: dict = Body(...)):
    """Set AR/VR interface mode (ar/vr/mr)."""
    arvr = _get_arvr()
    if arvr is None:
        return unavailable("AR/VR interface")
    try:
        from frontend.arvr.interface import InterfaceMode
        mode_str = data.get("mode", "vr").lower()
        mode = InterfaceMode(mode_str)
        arvr.set_mode(mode)
        return ok(data={"mode": mode.value})
    except ValueError:
        return error("Invalid mode. Use: ar, vr, mr", status_code=400)
    except Exception as e:
        logger.error(f"AR/VR set mode error: {e}")
        return error(str(e))


@router.post("/api/arvr/element")
async def arvr_create_element(data: dict = Body(...)):
    """Create a spatial element in AR/VR space."""
    arvr = _get_arvr()
    if arvr is None:
        return unavailable("AR/VR interface")
    try:
        position = data.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})
        content = data.get("content", "")
        rotation = data.get("rotation")
        scale = data.get("scale")
        interactive = data.get("interactive", True)

        element = arvr.create_spatial_element(
            position=position,
            content=content,
            rotation=rotation,
            scale=scale,
            interactive=interactive
        )
        return ok(data={
            "element": {
                "id": element.element_id,
                "position": element.position,
                "content": element.content,
                "interactive": element.interactive,
            }
        })
    except Exception as e:
        logger.error(f"AR/VR create element error: {e}")
        return error(str(e))


@router.post("/api/arvr/element/{element_id}/position")
async def arvr_update_position(element_id: str, data: dict = Body(...)):
    """Update a spatial element's position."""
    arvr = _get_arvr()
    if arvr is None:
        return unavailable("AR/VR interface")
    try:
        position = data.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})
        success = arvr.update_element_position(element_id, position)
        if success:
            return ok(data={"element_id": element_id})
        return error(f"Element {element_id} not found", status_code=404)
    except Exception as e:
        logger.error(f"AR/VR update position error: {e}")
        return error(str(e))


@router.delete("/api/arvr/element/{element_id}")
async def arvr_remove_element(element_id: str):
    """Remove a spatial element."""
    arvr = _get_arvr()
    if arvr is None:
        return unavailable("AR/VR interface")
    try:
        success = arvr.remove_element(element_id)
        if success:
            return ok(data={"element_id": element_id})
        return error(f"Element {element_id} not found", status_code=404)
    except Exception as e:
        logger.error(f"AR/VR remove element error: {e}")
        return error(str(e))


@router.post("/api/arvr/gesture")
async def arvr_register_gesture(data: dict = Body(...)):
    """Register a gesture command."""
    arvr = _get_arvr()
    if arvr is None:
        return unavailable("AR/VR interface")
    try:
        from frontend.arvr.interface import GestureType
        gesture_type_str = data.get("gesture_type", "tap").lower()
        gesture_type = GestureType(gesture_type_str)
        target = data.get("target_element")
        parameters = data.get("parameters", {})

        gesture = arvr.register_gesture(gesture_type, target, parameters)
        return ok(data={
            "gesture": {
                "id": gesture.command_id,
                "type": gesture.gesture_type.value,
                "target": gesture.target_element,
            }
        })
    except ValueError:
        return error("Invalid gesture type. Use: tap, swipe, pinch, grab, point, voice", status_code=400)
    except Exception as e:
        logger.error(f"AR/VR register gesture error: {e}")
        return error(str(e))


@router.post("/api/arvr/haptic")
async def arvr_trigger_haptic(data: dict = Body(...)):
    """Trigger haptic feedback."""
    arvr = _get_arvr()
    if arvr is None:
        return unavailable("AR/VR interface")
    try:
        intensity = data.get("intensity", 0.5)
        duration_ms = data.get("duration_ms", 100)
        pattern = data.get("pattern", "pulse")

        feedback = arvr.trigger_haptic(intensity, duration_ms, pattern)
        return ok(data={
            "feedback": {
                "id": feedback.feedback_id,
                "intensity": feedback.intensity,
                "duration_ms": feedback.duration_ms,
                "pattern": feedback.pattern,
            }
        })
    except Exception as e:
        logger.error(f"AR/VR haptic error: {e}")
        return error(str(e))


@router.get("/api/arvr/gestures")
async def arvr_gesture_history(limit: int = 10):
    """Get recent gesture history."""
    arvr = _get_arvr()
    if arvr is None:
        return unavailable("AR/VR interface")
    try:
        gesture_list = arvr.get_gesture_history(limit=limit)
        result = []
        for g in gesture_list:
            ts = g.timestamp.isoformat() if hasattr(g.timestamp, 'isoformat') else str(g.timestamp)
            result.append({
                "id": g.command_id,
                "type": g.gesture_type.value,
                "target": g.target_element,
                "parameters": g.parameters,
                "timestamp": ts,
            })
        return ok(data={"gestures": result})
    except Exception as e:
        logger.error(f"AR/VR gesture history error: {e}")
        return error(str(e))
