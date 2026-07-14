"""
Learning & Adaptation Routes
============================
Endpoints for adapter management, dataset capture, evaluation,
model routing, and training job lifecycle.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Learning"])

logger = logging.getLogger("AsimNexus.Routes.Learning")

# Module-level globals set by app.py at startup
learning_manager = None


def init_learning(app_globals: dict) -> None:
    """Initialize learning module from app.py globals."""
    global learning_manager
    learning_manager = app_globals.get("learning_manager")


# ── Status ────────────────────────────────────────────────────────────

@router.get("/api/learning/status")
async def learning_status():
    """Get learning system status."""
    try:
        if learning_manager:
            data = await learning_manager.get_status()
            return ok(data=data)
        return ok(data={"status": "active", "mode": "learning"})
    except Exception as e:
        logger.error(f"learning_status error: {e}")
        return error(str(e))


# ── Adapter Management ────────────────────────────────────────────────

@router.post("/api/learning/adapter/register")
async def learning_adapter_register(data: dict = Body(...)):
    """Register a new adapter."""
    try:
        if learning_manager:
            result = await learning_manager.register_adapter(data)
            return ok(data=result)
        return ok(data={"status": "registered", "adapter_id": "mock"})
    except Exception as e:
        logger.error(f"learning_adapter_register error: {e}")
        return error(str(e))


@router.get("/api/learning/adapters")
async def learning_adapters():
    """List all registered adapters."""
    try:
        if learning_manager:
            data = await learning_manager.list_adapters()
            return ok(data=data)
        return ok(data={"adapters": [], "count": 0})
    except Exception as e:
        logger.error(f"learning_adapters error: {e}")
        return error(str(e))


@router.get("/api/learning/adapter/{adapter_id}")
async def learning_adapter_get(adapter_id: str):
    """Get adapter details by ID."""
    try:
        if learning_manager:
            data = await learning_manager.get_adapter(adapter_id)
            return ok(data=data)
        return ok(data={"adapter_id": adapter_id, "status": "unknown"})
    except Exception as e:
        logger.error(f"learning_adapter_get error: {e}")
        return error(str(e))


@router.get("/api/learning/adapter/{adapter_id}/versions")
async def learning_adapter_versions(adapter_id: str):
    """List all versions of an adapter."""
    try:
        if learning_manager:
            data = await learning_manager.get_adapter_versions(adapter_id)
            return ok(data=data)
        return ok(data={"adapter_id": adapter_id, "versions": []})
    except Exception as e:
        logger.error(f"learning_adapter_versions error: {e}")
        return error(str(e))


@router.get("/api/learning/adapter/{adapter_id}/production")
async def learning_adapter_production(adapter_id: str):
    """Get production version of an adapter."""
    try:
        if learning_manager:
            data = await learning_manager.get_production_version(adapter_id)
            return ok(data=data)
        return ok(data={"adapter_id": adapter_id, "production_version": None})
    except Exception as e:
        logger.error(f"learning_adapter_production error: {e}")
        return error(str(e))


@router.post("/api/learning/adapter/{adapter_id}/rollback")
async def learning_adapter_rollback(adapter_id: str, data: dict = Body(...)):
    """Rollback adapter to a previous version."""
    try:
        if learning_manager:
            result = await learning_manager.rollback_adapter(adapter_id, data.get("version", ""))
            return ok(data=result)
        return ok(data={"status": "rolled_back", "adapter_id": adapter_id})
    except Exception as e:
        logger.error(f"learning_adapter_rollback error: {e}")
        return error(str(e))


@router.post("/api/learning/adapter/{adapter_id}/version/{version}/promote")
async def learning_adapter_promote(adapter_id: str, version: str):
    """Promote a version to production."""
    try:
        if learning_manager:
            result = await learning_manager.promote_version(adapter_id, version)
            return ok(data=result)
        return ok(data={"status": "promoted", "adapter_id": adapter_id, "version": version})
    except Exception as e:
        logger.error(f"learning_adapter_promote error: {e}")
        return error(str(e))


@router.put("/api/learning/adapter/{adapter_id}/version/{version}/status")
async def learning_adapter_version_status(adapter_id: str, version: str, data: dict = Body(...)):
    """Update version status."""
    try:
        if learning_manager:
            result = await learning_manager.set_version_status(adapter_id, version, data.get("status", ""))
            return ok(data=result)
        return ok(data={"status": "updated"})
    except Exception as e:
        logger.error(f"learning_adapter_version_status error: {e}")
        return error(str(e))


@router.get("/api/learning/adapter/rollback-history")
async def learning_adapter_rollback_history():
    """Get rollback history across all adapters."""
    try:
        if learning_manager:
            data = await learning_manager.get_rollback_history()
            return ok(data=data)
        return ok(data={"rollbacks": [], "count": 0})
    except Exception as e:
        logger.error(f"learning_adapter_rollback_history error: {e}")
        return error(str(e))


@router.get("/api/learning/adapter/stats")
async def learning_adapter_stats():
    """Get adapter statistics."""
    try:
        if learning_manager:
            data = await learning_manager.get_adapter_stats()
            return ok(data=data)
        return ok(data={"total_adapters": 0, "total_versions": 0})
    except Exception as e:
        logger.error(f"learning_adapter_stats error: {e}")
        return error(str(e))


# ── Dataset Management ────────────────────────────────────────────────

@router.post("/api/learning/dataset/capture")
async def learning_dataset_capture(data: dict = Body(...)):
    """Capture a new dataset sample."""
    try:
        if learning_manager:
            result = await learning_manager.capture_dataset(data)
            return ok(data=result)
        return ok(data={"status": "captured", "sample_id": "mock"})
    except Exception as e:
        logger.error(f"learning_dataset_capture error: {e}")
        return error(str(e))


@router.post("/api/learning/dataset/label/{sample_id}")
async def learning_dataset_label(sample_id: str, data: dict = Body(...)):
    """Label a dataset sample."""
    try:
        if learning_manager:
            result = await learning_manager.label_sample(sample_id, data.get("label", ""))
            return ok(data=result)
        return ok(data={"status": "labeled", "sample_id": sample_id})
    except Exception as e:
        logger.error(f"learning_dataset_label error: {e}")
        return error(str(e))


@router.post("/api/learning/dataset/snapshot")
async def learning_dataset_snapshot(data: dict = Body(...)):
    """Create a dataset snapshot."""
    try:
        if learning_manager:
            result = await learning_manager.create_snapshot(data)
            return ok(data=result)
        return ok(data={"status": "snapshot_created", "snapshot_id": "mock"})
    except Exception as e:
        logger.error(f"learning_dataset_snapshot error: {e}")
        return error(str(e))


@router.get("/api/learning/dataset/snapshot/{snapshot_id}")
async def learning_dataset_snapshot_get(snapshot_id: str):
    """Get dataset snapshot details."""
    try:
        if learning_manager:
            data = await learning_manager.get_snapshot(snapshot_id)
            return ok(data=data)
        return ok(data={"snapshot_id": snapshot_id, "status": "unknown"})
    except Exception as e:
        logger.error(f"learning_dataset_snapshot_get error: {e}")
        return error(str(e))


@router.get("/api/learning/dataset/snapshots")
async def learning_dataset_snapshots():
    """List all dataset snapshots."""
    try:
        if learning_manager:
            data = await learning_manager.list_snapshots()
            return ok(data=data)
        return ok(data={"snapshots": [], "count": 0})
    except Exception as e:
        logger.error(f"learning_dataset_snapshots error: {e}")
        return error(str(e))


@router.get("/api/learning/dataset/stats")
async def learning_dataset_stats():
    """Get dataset statistics."""
    try:
        if learning_manager:
            data = await learning_manager.get_dataset_stats()
            return ok(data=data)
        return ok(data={"total_samples": 0, "labeled": 0, "unlabeled": 0})
    except Exception as e:
        logger.error(f"learning_dataset_stats error: {e}")
        return error(str(e))


# ── Evaluation ────────────────────────────────────────────────────────

@router.post("/api/learning/evaluator/evaluation")
async def learning_evaluator_evaluation(data: dict = Body(...)):
    """Create a new evaluation."""
    try:
        if learning_manager:
            result = await learning_manager.create_evaluation(data)
            return ok(data=result)
        return ok(data={"status": "created", "evaluation_id": "mock"})
    except Exception as e:
        logger.error(f"learning_evaluator_evaluation error: {e}")
        return error(str(e))


@router.post("/api/learning/evaluator/evaluation/{evaluation_id}/start")
async def learning_evaluator_evaluation_start(evaluation_id: str):
    """Start an evaluation."""
    try:
        if learning_manager:
            result = await learning_manager.start_evaluation(evaluation_id)
            return ok(data=result)
        return ok(data={"status": "started", "evaluation_id": evaluation_id})
    except Exception as e:
        logger.error(f"learning_evaluator_evaluation_start error: {e}")
        return error(str(e))


@router.post("/api/learning/evaluator/evaluation/{evaluation_id}/complete")
async def learning_evaluator_evaluation_complete(evaluation_id: str, data: dict = Body(...)):
    """Complete an evaluation."""
    try:
        if learning_manager:
            result = await learning_manager.complete_evaluation(evaluation_id, data)
            return ok(data=result)
        return ok(data={"status": "completed", "evaluation_id": evaluation_id})
    except Exception as e:
        logger.error(f"learning_evaluator_evaluation_complete error: {e}")
        return error(str(e))


@router.get("/api/learning/evaluator/evaluations")
async def learning_evaluator_evaluations():
    """List all evaluations."""
    try:
        if learning_manager:
            data = await learning_manager.list_evaluations()
            return ok(data=data)
        return ok(data={"evaluations": [], "count": 0})
    except Exception as e:
        logger.error(f"learning_evaluator_evaluations error: {e}")
        return error(str(e))


@router.post("/api/learning/evaluator/golden-dataset")
async def learning_evaluator_golden_dataset(data: dict = Body(...)):
    """Create a golden dataset for evaluation."""
    try:
        if learning_manager:
            result = await learning_manager.create_golden_dataset(data)
            return ok(data=result)
        return ok(data={"status": "created", "golden_id": "mock"})
    except Exception as e:
        logger.error(f"learning_evaluator_golden_dataset error: {e}")
        return error(str(e))


@router.get("/api/learning/evaluator/golden-datasets")
async def learning_evaluator_golden_datasets():
    """List all golden datasets."""
    try:
        if learning_manager:
            data = await learning_manager.list_golden_datasets()
            return ok(data=data)
        return ok(data={"golden_datasets": [], "count": 0})
    except Exception as e:
        logger.error(f"learning_evaluator_golden_datasets error: {e}")
        return error(str(e))


@router.get("/api/learning/evaluator/stats")
async def learning_evaluator_stats():
    """Get evaluator statistics."""
    try:
        if learning_manager:
            data = await learning_manager.get_evaluator_stats()
            return ok(data=data)
        return ok(data={"total_evaluations": 0, "pass_rate": 0.0})
    except Exception as e:
        logger.error(f"learning_evaluator_stats error: {e}")
        return error(str(e))


@router.get("/api/learning/evaluator/can-promote/{adapter_id}")
async def learning_evaluator_can_promote(adapter_id: str):
    """Check if an adapter can be promoted to production."""
    try:
        if learning_manager:
            data = await learning_manager.can_promote(adapter_id)
            return ok(data=data)
        return ok(data={"can_promote": True, "adapter_id": adapter_id})
    except Exception as e:
        logger.error(f"learning_evaluator_can_promote error: {e}")
        return error(str(e))


# ── Model Router ──────────────────────────────────────────────────────

@router.post("/api/learning/router/load")
async def learning_router_load(data: dict = Body(...)):
    """Load an adapter into the router."""
    try:
        if learning_manager:
            result = await learning_manager.load_adapter(data.get("adapter_id", ""))
            return ok(data=result)
        return ok(data={"status": "loaded"})
    except Exception as e:
        logger.error(f"learning_router_load error: {e}")
        return error(str(e))


@router.get("/api/learning/router/loaded-adapters")
async def learning_router_loaded_adapters():
    """List currently loaded adapters."""
    try:
        if learning_manager:
            data = await learning_manager.get_loaded_adapters()
            return ok(data=data)
        return ok(data={"loaded_adapters": [], "count": 0})
    except Exception as e:
        logger.error(f"learning_router_loaded_adapters error: {e}")
        return error(str(e))


@router.get("/api/learning/router/status")
async def learning_router_status():
    """Get router status."""
    try:
        if learning_manager:
            data = await learning_manager.get_router_status()
            return ok(data=data)
        return ok(data={"status": "active", "loaded_adapters": 0})
    except Exception as e:
        logger.error(f"learning_router_status error: {e}")
        return error(str(e))


@router.post("/api/learning/router/swap")
async def learning_router_swap(data: dict = Body(...)):
    """Swap active adapter in the router."""
    try:
        if learning_manager:
            result = await learning_manager.swap_adapter(data.get("adapter_id", ""))
            return ok(data=result)
        return ok(data={"status": "swapped"})
    except Exception as e:
        logger.error(f"learning_router_swap error: {e}")
        return error(str(e))


@router.get("/api/learning/router/swap-history")
async def learning_router_swap_history():
    """Get adapter swap history."""
    try:
        if learning_manager:
            data = await learning_manager.get_swap_history()
            return ok(data=data)
        return ok(data={"swaps": [], "count": 0})
    except Exception as e:
        logger.error(f"learning_router_swap_history error: {e}")
        return error(str(e))


# ── Training Jobs ─────────────────────────────────────────────────────

@router.post("/api/learning/training/job")
async def learning_training_job(data: dict = Body(...)):
    """Create a new training job."""
    try:
        if learning_manager:
            result = await learning_manager.create_training_job(data)
            return ok(data=result)
        return ok(data={"status": "created", "job_id": "mock"})
    except Exception as e:
        logger.error(f"learning_training_job error: {e}")
        return error(str(e))


@router.get("/api/learning/training/jobs")
async def learning_training_jobs():
    """List all training jobs."""
    try:
        if learning_manager:
            data = await learning_manager.list_training_jobs()
            return ok(data=data)
        return ok(data={"jobs": [], "count": 0})
    except Exception as e:
        logger.error(f"learning_training_jobs error: {e}")
        return error(str(e))


@router.get("/api/learning/training/job/{job_id}")
async def learning_training_job_get(job_id: str):
    """Get training job details."""
    try:
        if learning_manager:
            data = await learning_manager.get_training_job(job_id)
            return ok(data=data)
        return ok(data={"job_id": job_id, "status": "unknown"})
    except Exception as e:
        logger.error(f"learning_training_job_get error: {e}")
        return error(str(e))


@router.post("/api/learning/training/job/{job_id}/start")
async def learning_training_job_start(job_id: str):
    """Start a training job."""
    try:
        if learning_manager:
            result = await learning_manager.start_training_job(job_id)
            return ok(data=result)
        return ok(data={"status": "started", "job_id": job_id})
    except Exception as e:
        logger.error(f"learning_training_job_start error: {e}")
        return error(str(e))


@router.post("/api/learning/training/job/{job_id}/cancel")
async def learning_training_job_cancel(job_id: str):
    """Cancel a training job."""
    try:
        if learning_manager:
            result = await learning_manager.cancel_training_job(job_id)
            return ok(data=result)
        return ok(data={"status": "cancelled", "job_id": job_id})
    except Exception as e:
        logger.error(f"learning_training_job_cancel error: {e}")
        return error(str(e))


@router.post("/api/learning/training/job/{job_id}/complete")
async def learning_training_job_complete(job_id: str, data: dict = Body(...)):
    """Complete a training job."""
    try:
        if learning_manager:
            result = await learning_manager.complete_training_job(job_id, data)
            return ok(data=result)
        return ok(data={"status": "completed", "job_id": job_id})
    except Exception as e:
        logger.error(f"learning_training_job_complete error: {e}")
        return error(str(e))


@router.get("/api/learning/training/stats")
async def learning_training_stats():
    """Get training statistics."""
    try:
        if learning_manager:
            data = await learning_manager.get_training_stats()
            return ok(data=data)
        return ok(data={"total_jobs": 0, "active": 0, "completed": 0})
    except Exception as e:
        logger.error(f"learning_training_stats error: {e}")
        return error(str(e))
