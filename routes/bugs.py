"""
Bug Tracking Routes
===================
Endpoints for bug reporting, triage, listing, and approval.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Bug Tracking"])

logger = logging.getLogger("AsimNexus.Routes.Bugs")

bug_tracker = None

def init_bugs(app_globals: dict) -> None:
    global bug_tracker
    bug_tracker = app_globals.get("bug_tracker")

@router.post("/api/bugs/report")
async def bugs_report(data: dict = Body(...)):
    """Report a new bug."""
    try:
        if bug_tracker:
            result = await bug_tracker.report(data)
            return ok(data=result)
        return ok(data={"status": "reported", "bug_id": "mock_bug", "title": data.get("title", "")})
    except Exception as e:
        logger.error(f"bugs_report error: {e}")
        return error(str(e))

@router.get("/api/bugs/list")
async def bugs_list(status: str = "", severity: str = ""):
    """List bugs with optional filters."""
    try:
        if bug_tracker:
            data = await bug_tracker.list_bugs(status=status, severity=severity)
            return ok(data=data)
        return ok(data={"bugs": [], "count": 0})
    except Exception as e:
        logger.error(f"bugs_list error: {e}")
        return error(str(e))

@router.get("/api/bugs/pending")
async def bugs_pending():
    """List pending bugs awaiting triage."""
    try:
        if bug_tracker:
            data = await bug_tracker.get_pending()
            return ok(data=data)
        return ok(data={"bugs": [], "count": 0})
    except Exception as e:
        logger.error(f"bugs_pending error: {e}")
        return error(str(e))

@router.post("/api/bugs/batch-triage")
async def bugs_batch_triage(data: dict = Body(...)):
    """Batch triage multiple bugs."""
    try:
        if bug_tracker:
            result = await bug_tracker.batch_triage(data)
            return ok(data=result)
        return ok(data={"status": "triaged", "count": len(data.get("bug_ids", []))})
    except Exception as e:
        logger.error(f"bugs_batch_triage error: {e}")
        return error(str(e))

@router.post("/api/bugs/{bug_id}/approve")
async def bugs_approve(bug_id: str, data: dict = Body(...)):
    """Approve a bug for fixing."""
    try:
        if bug_tracker:
            result = await bug_tracker.approve(bug_id, data)
            return ok(data=result)
        return ok(data={"status": "approved", "bug_id": bug_id})
    except Exception as e:
        logger.error(f"bugs_approve error: {e}")
        return error(str(e))
