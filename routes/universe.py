"""
Personal Universe Routes
========================
REST API for the Personal Universe Manager — user lifecycle management across
5 layers (Personal, Family, Community, Enterprise, Sovereign), universe CRUD,
layer activation, and lifecycle state transitions.

Reference:
  - core/universe/personal_universe.py — Core PersonalUniverseManager implementation
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query

from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Universe")

router = APIRouter(tags=["Universe"])

# Module-level globals (set via init_universe)
orchestrator = None


def init_universe(app_globals: dict) -> None:
    """Initialize universe module with shared app state."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ─── Universe CRUD ───────────────────────────────────────────────────────────


@router.post("/api/universe/create")
async def universe_create(data: dict = Body(...)):
    """Create a new personal universe for a user.

    Request body:
      - user_id (str, required): Unique user identifier
      - email (str, required): User email address
      - display_name (str, required): User's display name

    Returns:
      - universe: The created PersonalUniverse
    """
    try:
        from core.universe import get_universe_manager

        manager = get_universe_manager()
        user_id = data.get("user_id")
        email = data.get("email")
        display_name = data.get("display_name")

        if not user_id or not email or not display_name:
            return error("user_id, email, and display_name are required")

        universe = manager.create_universe(
            user_id=user_id,
            email=email,
            display_name=display_name,
        )

        return ok(data={
            "user_id": universe.user_id,
            "email": universe.email,
            "display_name": universe.display_name,
            "state": universe.state.value,
            "created_at": universe.created_at.isoformat() if hasattr(universe.created_at, 'isoformat') else str(universe.created_at),
        })
    except Exception as e:
        logger.exception("Failed to create universe")
        return error(str(e))


@router.get("/api/universe/status")
async def universe_status(
    user_id: str = Query(..., description="User ID"),
):
    """Get the status of a user's personal universe.

    Query params:
      - user_id (str, required): The user ID

    Returns:
      - status: Universe status with layers, state, and metrics
    """
    try:
        from core.universe import get_universe_manager

        manager = get_universe_manager()
        status = manager.get_universe_status(user_id)

        if "error" in status:
            return error(status["error"])

        return ok(data=status)
    except Exception as e:
        logger.exception("Failed to get universe status")
        return error(str(e))


@router.get("/api/universe/lifecycle")
async def universe_lifecycle(
    user_id: str = Query(..., description="User ID"),
):
    """Get the lifecycle summary for a user's universe.

    Query params:
      - user_id (str, required): The user ID

    Returns:
      - lifecycle: Lifecycle summary with state transitions and timeline
    """
    try:
        from core.universe import get_universe_manager

        manager = get_universe_manager()
        summary = manager.get_lifecycle_summary(user_id)

        if "error" in summary:
            return error(summary["error"])

        return ok(data=summary)
    except Exception as e:
        logger.exception("Failed to get lifecycle summary")
        return error(str(e))


# ─── Layer Management ────────────────────────────────────────────────────────


@router.post("/api/universe/layer/activate")
async def universe_activate_layer(data: dict = Body(...)):
    """Activate a new layer in a user's universe.

    Request body:
      - user_id (str, required): The user ID
      - layer (int, required): Layer number (1-5: PERSONAL=1, FAMILY=2, COMMUNITY=3, ENTERPRISE=4, SOVEREIGN=5)
      - metadata (dict, optional): Layer activation metadata

    Returns:
      - result: Layer activation result
    """
    try:
        from core.universe import get_universe_manager, UniverseLayer

        manager = get_universe_manager()
        user_id = data.get("user_id")
        layer_value = data.get("layer")
        metadata = data.get("metadata", {})

        if not user_id or layer_value is None:
            return error("user_id and layer are required")

        try:
            layer = UniverseLayer(layer_value)
        except ValueError:
            valid_layers = [l.value for l in UniverseLayer]
            return error(f"Invalid layer. Valid: {valid_layers}")

        result = manager.activate_layer(user_id, layer, metadata)

        if "error" in result:
            return error(result["error"])

        return ok(data=result)
    except Exception as e:
        logger.exception("Failed to activate layer")
        return error(str(e))


# ─── State Management ────────────────────────────────────────────────────────


@router.post("/api/universe/state/update")
async def universe_update_state(data: dict = Body(...)):
    """Update the state of a user's universe.

    Request body:
      - user_id (str, required): The user ID
      - new_state (str, required): New state (ONBOARDING/ACTIVE/SUSPENDED/ARCHIVED/LOCKED/TERMINATED)

    Returns:
      - result: State update result
    """
    try:
        from core.universe import get_universe_manager, UserState

        manager = get_universe_manager()
        user_id = data.get("user_id")
        state_str = data.get("new_state")

        if not user_id or not state_str:
            return error("user_id and new_state are required")

        try:
            new_state = UserState(state_str)
        except ValueError:
            valid_states = [s.value for s in UserState]
            return error(f"Invalid new_state. Valid: {valid_states}")

        success = manager.update_state(user_id, new_state)

        if not success:
            return error("Failed to update state. User may not exist or transition is invalid.")

        return ok(data={
            "user_id": user_id,
            "new_state": new_state.value,
            "message": f"State updated to {new_state.value}",
        })
    except Exception as e:
        logger.exception("Failed to update state")
        return error(str(e))


# ─── Activity & Connections ──────────────────────────────────────────────────


@router.post("/api/universe/activity/record")
async def universe_record_activity(data: dict = Body(...)):
    """Record an activity in a user's universe.

    Request body:
      - user_id (str, required): The user ID
      - activity_type (str, required): Type of activity
      - details (dict, optional): Activity details

    Returns:
      - result: Activity recording result
    """
    try:
        from core.universe import get_universe_manager

        manager = get_universe_manager()
        user_id = data.get("user_id")
        activity_type = data.get("activity_type")
        details = data.get("details", {})

        if not user_id or not activity_type:
            return error("user_id and activity_type are required")

        result = manager.record_activity(user_id, activity_type, details)

        return ok(data=result)
    except Exception as e:
        logger.exception("Failed to record activity")
        return error(str(e))


@router.post("/api/universe/connection/add")
async def universe_add_connection(data: dict = Body(...)):
    """Add a connection to a user's universe.

    Request body:
      - user_id (str, required): The user ID
      - connection_type (str, required): Type of connection
      - connection_data (dict, required): Connection details

    Returns:
      - result: Connection addition result
    """
    try:
        from core.universe import get_universe_manager

        manager = get_universe_manager()
        user_id = data.get("user_id")
        connection_type = data.get("connection_type")
        connection_data = data.get("connection_data", {})

        if not user_id or not connection_type:
            return error("user_id and connection_type are required")

        result = manager.add_connection(user_id, connection_type, connection_data)

        return ok(data=result)
    except Exception as e:
        logger.exception("Failed to add connection")
        return error(str(e))


# ─── Migration & Archival ────────────────────────────────────────────────────


@router.post("/api/universe/migrate")
async def universe_migrate(data: dict = Body(...)):
    """Migrate a user's universe to a new node.

    Request body:
      - user_id (str, required): The user ID
      - new_node (str, required): Target node identifier

    Returns:
      - result: Migration result
    """
    try:
        from core.universe import get_universe_manager

        manager = get_universe_manager()
        user_id = data.get("user_id")
        new_node = data.get("new_node")

        if not user_id or not new_node:
            return error("user_id and new_node are required")

        success = manager.migrate_universe(user_id, new_node)

        if not success:
            return error("Migration failed")

        return ok(data={
            "user_id": user_id,
            "new_node": new_node,
            "message": "Universe migrated successfully",
        })
    except Exception as e:
        logger.exception("Failed to migrate universe")
        return error(str(e))


@router.post("/api/universe/archive")
async def universe_archive(data: dict = Body(...)):
    """Archive a user's universe.

    Request body:
      - user_id (str, required): The user ID
      - reason (str, optional): Reason for archiving

    Returns:
      - result: Archival result
    """
    try:
        from core.universe import get_universe_manager

        manager = get_universe_manager()
        user_id = data.get("user_id")
        reason = data.get("reason", "User request")

        if not user_id:
            return error("user_id is required")

        success = manager.archive_universe(user_id, reason)

        if not success:
            return error("Archival failed")

        return ok(data={
            "user_id": user_id,
            "message": f"Universe archived: {reason}",
        })
    except Exception as e:
        logger.exception("Failed to archive universe")
        return error(str(e))


@router.post("/api/universe/reactivate")
async def universe_reactivate(data: dict = Body(...)):
    """Reactivate an archived universe.

    Request body:
      - user_id (str, required): The user ID

    Returns:
      - result: Reactivation result
    """
    try:
        from core.universe import get_universe_manager

        manager = get_universe_manager()
        user_id = data.get("user_id")

        if not user_id:
            return error("user_id is required")

        success = manager.reactivate_universe(user_id)

        if not success:
            return error("Reactivation failed")

        return ok(data={
            "user_id": user_id,
            "message": "Universe reactivated",
        })
    except Exception as e:
        logger.exception("Failed to reactivate universe")
        return error(str(e))


# ─── Statistics ──────────────────────────────────────────────────────────────


@router.get("/api/universe/stats")
async def universe_stats():
    """Get universe manager statistics.

    Returns:
      - stats: Universe statistics with counts and metrics
    """
    try:
        from core.universe import get_universe_manager

        manager = get_universe_manager()
        stats = manager.get_stats()

        return ok(data=stats.to_dict() if hasattr(stats, "to_dict") else stats)
    except Exception as e:
        logger.exception("Failed to get universe stats")
        return error(str(e))


@router.get("/api/universe/privacy-score")
async def universe_privacy_score(
    user_id: str = Query(..., description="User ID"),
):
    """Calculate privacy score for a user's universe.

    Query params:
      - user_id (str, required): The user ID

    Returns:
      - privacy_score: Calculated privacy score
    """
    try:
        from core.universe import get_universe_manager

        manager = get_universe_manager()
        score = manager.calculate_privacy_score(user_id)

        return ok(data={
            "user_id": user_id,
            "privacy_score": score,
        })
    except Exception as e:
        logger.exception("Failed to calculate privacy score")
        return error(str(e))
