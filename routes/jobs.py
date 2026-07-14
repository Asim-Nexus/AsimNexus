"""
Jobs Routes
===========
Endpoints for job management and status tracking.
"""

import logging
from fastapi import APIRouter
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Jobs"])

logger = logging.getLogger("AsimNexus.Routes.Jobs")

job_manager = None


def init_jobs(app_globals: dict) -> None:
    global job_manager
    job_manager = app_globals.get("job_manager")


@router.get("/api/jobs/{job_id}")
async def jobs_get(job_id: str):
    """Get job details by ID."""
    try:
        if job_manager:
            data = await job_manager.get_job(job_id)
            return ok(data=data)
        return ok(data={"job_id": job_id, "status": "unknown"})
    except Exception as e:
        logger.error(f"jobs_get error: {e}")
        return error(str(e))
