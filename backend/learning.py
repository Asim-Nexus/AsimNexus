#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade learning backend
ASIMNEXUS Learning Backend
==========================
Learning API endpoints for training pipeline.
Provides REST interface to dataset builder, training trigger, evaluator, and adapter registry.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("AsimNexus.Learning")


def setup_learning_routes(app, db_path: str = "data"):
    """
    Setup learning API routes on FastAPI app.
    Call this from simple_backend.py to wire learning endpoints.
    """
    from core.dataset_builder import get_dataset_builder, DatasetType, LabelType
    from core.training_trigger import get_training_trigger, TrainingStatus
    from core.evaluator import get_evaluator, EvaluationStatus
    from core.adapter_registry import get_adapter_registry, AdapterStatus, PromotionStage
    from core.hot_swap_router import get_hot_swap_router
    
    # Initialize learning components
    dataset_builder = get_dataset_builder(f"{db_path}/dataset_builder.db")
    training_trigger = get_training_trigger(f"{db_path}/training_trigger.db")
    evaluator = get_evaluator(f"{db_path}/evaluator.db")
    adapter_registry = get_adapter_registry(f"{db_path}/adapter_registry.db")
    hot_swap_router = get_hot_swap_router()
    
    class CaptureSampleRequest(BaseModel):
        """Request model for capturing samples."""
        input_text: str
        output_text: Optional[str] = None
        source: str = "manual"
        metadata: Optional[Dict[str, Any]] = None
    
    class LabelSampleRequest(BaseModel):
        """Request model for labeling samples."""
        label_type: str
        value: Any
    
    class CreateSnapshotRequest(BaseModel):
        """Request model for creating snapshots."""
        dataset_type: str
        parent_snapshot_id: Optional[str] = None
        metadata: Optional[Dict[str, Any]] = None
    
    class TrainingConfigRequest(BaseModel):
        """Request model for training configuration."""
        method: str = "qlora"
        learning_rate: float = 2e-4
        batch_size: int = 4
        epochs: int = 3
        lora_r: int = 8
        lora_alpha: int = 16
    
    class CreateTrainingJobRequest(BaseModel):
        """Request model for creating training jobs."""
        base_model_id: str
        dataset_snapshot_id: str
        config: Optional[TrainingConfigRequest] = None
        metadata: Optional[Dict[str, Any]] = None
    
    class EvaluationThresholdRequest(BaseModel):
        """Request model for evaluation thresholds."""
        metric_name: str
        min_value: float
        max_value: Optional[float] = None
        required: bool = True
    
    class CreateGoldenDatasetRequest(BaseModel):
        """Request model for creating golden datasets."""
        name: str
        dataset_type: str
        samples: List[Dict[str, Any]]
        thresholds: Optional[List[EvaluationThresholdRequest]] = None
        metadata: Optional[Dict[str, Any]] = None
    
    class CreateEvaluationRequest(BaseModel):
        """Request model for creating evaluations."""
        adapter_id: str
        golden_dataset_id: str
        metadata: Optional[Dict[str, Any]] = None
    
    class PromoteAdapterRequest(BaseModel):
        """Request model for promoting adapters."""
        stage: str
        evaluation_ids: Optional[List[str]] = None
    
    # ─── DATASET BUILDER ENDPOINTS ────────────────────────────────────────────
    
    @app.post("/api/learning/dataset/capture")
    async def capture_sample(req: CaptureSampleRequest):
        """Capture a data sample."""
        try:
            sample = dataset_builder.capture_sample(
                input_text=req.input_text,
                output_text=req.output_text,
                source=req.source,
                metadata=req.metadata
            )
            return JSONResponse({"sample_id": sample.id, "status": "captured"})
        except Exception as e:
            logger.error(f"Capture sample error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/learning/dataset/label/{sample_id}")
    async def label_sample(sample_id: str, req: LabelSampleRequest):
        """Label a data sample."""
        try:
            # Find sample in current samples
            sample = next((s for s in dataset_builder.current_samples if s.id == sample_id), None)
            if not sample:
                raise HTTPException(status_code=404, detail="Sample not found")
            
            label_type = LabelType(req.label_type)
            labeled = dataset_builder.label_sample(sample, label_type, req.value)
            return JSONResponse({"sample_id": sample_id, "status": "labeled"})
        except Exception as e:
            logger.error(f"Label sample error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/learning/dataset/snapshot")
    async def create_snapshot(req: CreateSnapshotRequest):
        """Create a dataset snapshot."""
        try:
            dtype = DatasetType(req.dataset_type)
            snapshot = dataset_builder.create_snapshot(
                dataset_type=dtype,
                parent_snapshot_id=req.parent_snapshot_id,
                metadata=req.metadata
            )
            return JSONResponse({
                "snapshot_id": snapshot.snapshot_id,
                "version": snapshot.version,
                "sample_count": len(snapshot.samples),
                "stats": snapshot.stats
            })
        except Exception as e:
            logger.error(f"Create snapshot error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/learning/dataset/snapshots")
    async def get_snapshots(dataset_type: Optional[str] = None):
        """Get all dataset snapshots."""
        try:
            dtype = DatasetType(dataset_type) if dataset_type else None
            snapshots = dataset_builder.get_snapshots(dtype)
            return JSONResponse([
                {
                    "snapshot_id": s.snapshot_id,
                    "dataset_type": s.dataset_type.value,
                    "version": s.version,
                    "sample_count": len(s.samples),
                    "created_at": s.created_at,
                    "stats": s.stats
                }
                for s in snapshots
            ])
        except Exception as e:
            logger.error(f"Get snapshots error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/learning/dataset/snapshot/{snapshot_id}")
    async def get_snapshot(snapshot_id: str):
        """Get a specific snapshot."""
        try:
            snapshot = dataset_builder.get_snapshot(snapshot_id)
            if not snapshot:
                raise HTTPException(status_code=404, detail="Snapshot not found")
            return JSONResponse(snapshot.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get snapshot error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/learning/dataset/stats")
    async def get_dataset_stats():
        """Get dataset builder statistics."""
        try:
            stats = dataset_builder.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get dataset stats error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # ─── TRAINING TRIGGER ENDPOINTS ────────────────────────────────────────────
    
    @app.post("/api/learning/training/job")
    async def create_training_job(req: CreateTrainingJobRequest):
        """Create a training job."""
        try:
            from core.training_trigger import TrainingConfig
            config = TrainingConfig.from_dict(req.config.dict()) if req.config else TrainingConfig()
            
            job = training_trigger.create_training_job(
                base_model_id=req.base_model_id,
                dataset_snapshot_id=req.dataset_snapshot_id,
                config=config,
                metadata=req.metadata
            )
            return JSONResponse({
                "job_id": job.job_id,
                "status": job.status.value,
                "created_at": job.created_at
            })
        except Exception as e:
            logger.error(f"Create training job error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/learning/training/job/{job_id}/start")
    async def start_training(job_id: str):
        """Start a training job."""
        try:
            success = training_trigger.start_training(job_id)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to start training")
            return JSONResponse({"job_id": job_id, "status": "running"})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Start training error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/learning/training/job/{job_id}/complete")
    async def complete_training(job_id: str, adapter_path: str, metrics: Dict[str, Any]):
        """Mark a training job as completed."""
        try:
            success = training_trigger.complete_training(job_id, adapter_path, metrics)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to complete training")
            return JSONResponse({"job_id": job_id, "status": "completed"})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Complete training error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/learning/training/job/{job_id}/cancel")
    async def cancel_training(job_id: str):
        """Cancel a training job."""
        try:
            success = training_trigger.cancel_training(job_id)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to cancel training")
            return JSONResponse({"job_id": job_id, "status": "cancelled"})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Cancel training error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/training/jobs")
    async def get_training_jobs(status: Optional[str] = None):
        """Get all training jobs."""
        try:
            tstatus = TrainingStatus(status) if status else None
            jobs = training_trigger.get_jobs(tstatus)
            return JSONResponse([
                {
                    "job_id": j.job_id,
                    "base_model_id": j.base_model_id,
                    "dataset_snapshot_id": j.dataset_snapshot_id,
                    "status": j.status.value,
                    "created_at": j.created_at,
                    "started_at": j.started_at,
                    "completed_at": j.completed_at,
                    "adapter_path": j.adapter_path,
                    "metrics": j.metrics
                }
                for j in jobs
            ])
        except Exception as e:
            logger.error(f"Get training jobs error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/training/job/{job_id}")
    async def get_training_job(job_id: str):
        """Get a specific training job."""
        try:
            job = training_trigger.get_job(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            return JSONResponse(job.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get training job error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/training/stats")
    async def get_training_stats():
        """Get training trigger statistics."""
        try:
            stats = training_trigger.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get training stats error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    # ─── EVALUATOR ENDPOINTS ──────────────────────────────────────────────────
    
    @app.post("/api/learning/evaluator/golden-dataset")
    async def create_golden_dataset(req: CreateGoldenDatasetRequest):
        """Create a golden dataset for evaluation."""
        try:
            from core.evaluator import EvaluationThreshold
            thresholds = []
            if req.thresholds:
                thresholds = [
                    EvaluationThreshold(
                        metric_name=t.metric_name,
                        min_value=t.min_value,
                        max_value=t.max_value,
                        required=t.required
                    )
                    for t in req.thresholds
                ]
            
            dataset = evaluator.create_golden_dataset(
                name=req.name,
                dataset_type=req.dataset_type,
                samples=req.samples,
                thresholds=thresholds,
                metadata=req.metadata
            )
            return JSONResponse({
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "sample_count": len(dataset.samples)
            })
        except Exception as e:
            logger.error(f"Create golden dataset error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/evaluator/golden-datasets")
    async def get_golden_datasets(dataset_type: Optional[str] = None):
        """Get all golden datasets."""
        try:
            datasets = evaluator.get_golden_datasets(dataset_type)
            return JSONResponse([
                {
                    "dataset_id": d.dataset_id,
                    "name": d.name,
                    "dataset_type": d.dataset_type,
                    "sample_count": len(d.samples),
                    "created_at": d.created_at
                }
                for d in datasets
            ])
        except Exception as e:
            logger.error(f"Get golden datasets error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.post("/api/learning/evaluator/evaluation")
    async def create_evaluation(req: CreateEvaluationRequest):
        """Create an evaluation."""
        try:
            evaluation = evaluator.create_evaluation(
                adapter_id=req.adapter_id,
                golden_dataset_id=req.golden_dataset_id,
                metadata=req.metadata
            )
            return JSONResponse({
                "evaluation_id": evaluation.evaluation_id,
                "status": evaluation.status.value,
                "created_at": evaluation.created_at
            })
        except Exception as e:
            logger.error(f"Create evaluation error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.post("/api/learning/evaluator/evaluation/{evaluation_id}/start")
    async def start_evaluation(evaluation_id: str):
        """Start an evaluation."""
        try:
            success = evaluator.start_evaluation(evaluation_id)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to start evaluation")
            return JSONResponse({"evaluation_id": evaluation_id, "status": "running"})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Start evaluation error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.post("/api/learning/evaluator/evaluation/{evaluation_id}/complete")
    async def complete_evaluation(evaluation_id: str, metrics: Dict[str, float]):
        """Complete an evaluation with metrics."""
        try:
            success = evaluator.complete_evaluation(evaluation_id, metrics)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to complete evaluation")
            return JSONResponse({"evaluation_id": evaluation_id, "status": "completed"})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Complete evaluation error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/evaluator/evaluations")
    async def get_evaluations(adapter_id: Optional[str] = None, status: Optional[str] = None):
        """Get all evaluations."""
        try:
            estatus = EvaluationStatus(status) if status else None
            evaluations = evaluator.get_evaluations(adapter_id, estatus)
            return JSONResponse([
                {
                    "evaluation_id": e.evaluation_id,
                    "adapter_id": e.adapter_id,
                    "golden_dataset_id": e.golden_dataset_id,
                    "status": e.status.value,
                    "passed": e.passed,
                    "metrics": e.metrics,
                    "created_at": e.created_at,
                    "completed_at": e.completed_at
                }
                for e in evaluations
            ])
        except Exception as e:
            logger.error(f"Get evaluations error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/evaluator/can-promote/{adapter_id}")
    async def can_promote(adapter_id: str):
        """Check if an adapter can be promoted."""
        try:
            can_promote = evaluator.can_promote(adapter_id)
            return JSONResponse({"adapter_id": adapter_id, "can_promote": can_promote})
        except Exception as e:
            logger.error(f"Can promote error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/evaluator/stats")
    async def get_evaluator_stats():
        """Get evaluator statistics."""
        try:
            stats = evaluator.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get evaluator stats error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    # ─── ADAPTER REGISTRY ENDPOINTS ────────────────────────────────────────────
    
    @app.post("/api/learning/adapter/register")
    async def register_adapter(base_model_id: str, training_job_id: str, 
                             adapter_path: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None):
        """Register a new adapter."""
        try:
            adapter = adapter_registry.register_adapter(
                base_model_id=base_model_id,
                training_job_id=training_job_id,
                adapter_path=adapter_path,
                metadata=metadata
            )
            return JSONResponse({
                "adapter_id": adapter.adapter_id,
                "version": adapter.version,
                "status": adapter.status.value
            })
        except Exception as e:
            logger.error(f"Register adapter error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.put("/api/learning/adapter/{adapter_id}/version/{version}/status")
    async def update_adapter_status(adapter_id: str, version: int, status: str):
        """Update adapter status."""
        try:
            astatus = AdapterStatus(status)
            success = adapter_registry.update_adapter_status(adapter_id, version, astatus)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to update status")
            return JSONResponse({"adapter_id": adapter_id, "version": version, "status": status})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update adapter status error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.post("/api/learning/adapter/{adapter_id}/version/{version}/promote")
    async def promote_adapter(adapter_id: str, version: int, req: PromoteAdapterRequest):
        """Promote an adapter to a stage."""
        try:
            stage = PromotionStage(req.stage)
            success = adapter_registry.promote_adapter(
                adapter_id, version, stage, req.evaluation_ids
            )
            if not success:
                raise HTTPException(status_code=400, detail="Failed to promote adapter")
            return JSONResponse({"adapter_id": adapter_id, "version": version, "stage": req.stage})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Promote adapter error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.post("/api/learning/adapter/{adapter_id}/rollback")
    async def rollback_adapter(adapter_id: str, from_version: int, to_version: int, reason: str):
        """Rollback an adapter to a previous version."""
        try:
            success = adapter_registry.rollback_adapter(adapter_id, from_version, to_version, reason)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to rollback adapter")
            return JSONResponse({"adapter_id": adapter_id, "from_version": from_version, "to_version": to_version})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rollback adapter error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/adapters")
    async def get_adapters(status: Optional[str] = None, promotion_stage: Optional[str] = None):
        """Get all adapters."""
        try:
            astatus = AdapterStatus(status) if status else None
            pstage = PromotionStage(promotion_stage) if promotion_stage else None
            adapters = adapter_registry.get_adapters(astatus, pstage)
            return JSONResponse([
                {
                    "adapter_id": a.adapter_id,
                    "version": a.version,
                    "base_model_id": a.base_model_id,
                    "status": a.status.value,
                    "promotion_stage": a.promotion_stage.value if a.promotion_stage else None,
                    "created_at": a.created_at,
                    "promoted_at": a.promoted_at,
                    "metrics": a.metrics
                }
                for a in adapters
            ])
        except Exception as e:
            logger.error(f"Get adapters error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/adapter/{adapter_id}")
    async def get_adapter(adapter_id: str, version: Optional[int] = None):
        """Get an adapter by ID."""
        try:
            adapter = adapter_registry.get_adapter(adapter_id, version)
            if not adapter:
                raise HTTPException(status_code=404, detail="Adapter not found")
            return JSONResponse(adapter.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get adapter error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/adapter/{adapter_id}/versions")
    async def get_adapter_versions(adapter_id: str):
        """Get all versions of an adapter."""
        try:
            versions = adapter_registry.get_adapter_versions(adapter_id)
            return JSONResponse([v.to_dict() for v in versions])
        except Exception as e:
            logger.error(f"Get adapter versions error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/adapter/{adapter_id}/production")
    async def get_production_adapter(adapter_id: str):
        """Get the production adapter."""
        try:
            adapter = adapter_registry.get_production_adapter(adapter_id)
            if not adapter:
                raise HTTPException(status_code=404, detail="Production adapter not found")
            return JSONResponse(adapter.to_dict())
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get production adapter error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/adapter/rollback-history")
    async def get_rollback_history(adapter_id: Optional[str] = None):
        """Get rollback history."""
        try:
            history = adapter_registry.get_rollback_history(adapter_id)
            return JSONResponse([
                {
                    "event_id": e.event_id,
                    "adapter_id": e.adapter_id,
                    "from_version": e.from_version,
                    "to_version": e.to_version,
                    "reason": e.reason,
                    "timestamp": e.timestamp
                }
                for e in history
            ])
        except Exception as e:
            logger.error(f"Get rollback history error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/adapter/stats")
    async def get_adapter_stats():
        """Get adapter registry statistics."""
        try:
            stats = adapter_registry.get_stats()
            return JSONResponse(stats)
        except Exception as e:
            logger.error(f"Get adapter stats error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    # ─── HOT SWAP ROUTER ENDPOINTS ────────────────────────────────────────────
    
    @app.post("/api/learning/router/load")
    async def load_adapter(adapter_id: str, version: int, base_model_id: str, adapter_path: str,
                         metadata: Optional[Dict[str, Any]] = None):
        """Load an adapter into the router."""
        try:
            adapter = hot_swap_router.load_adapter(
                adapter_id=adapter_id,
                version=version,
                base_model_id=base_model_id,
                adapter_path=adapter_path,
                metadata=metadata
            )
            return JSONResponse({
                "adapter_id": adapter.adapter_id,
                "version": adapter.version,
                "status": "loaded"
            })
        except Exception as e:
            logger.error(f"Load adapter error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.post("/api/learning/router/swap")
    async def swap_adapter(new_adapter_id: str, force: bool = False):
        """Swap to a different adapter."""
        try:
            success = hot_swap_router.swap_adapter(new_adapter_id, force)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to swap adapter")
            return JSONResponse({
                "active_adapter_id": new_adapter_id,
                "status": "swapped"
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Swap adapter error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/router/status")
    async def get_router_status():
        """Get router status."""
        try:
            status = hot_swap_router.get_status()
            return JSONResponse(status)
        except Exception as e:
            logger.error(f"Get router status error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/router/loaded-adapters")
    async def get_loaded_adapters():
        """Get all loaded adapters."""
        try:
            adapters = hot_swap_router.get_loaded_adapters()
            return JSONResponse([a.to_dict() for a in adapters])
        except Exception as e:
            logger.error(f"Get loaded adapters error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    @app.get("/api/learning/router/swap-history")
    async def get_swap_history(limit: int = 100):
        """Get swap history."""
        try:
            history = hot_swap_router.get_swap_history(limit)
            return JSONResponse(history)
        except Exception as e:
            logger.error(f"Get swap history error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
    
    # ─── OVERALL LEARNING STATUS ───────────────────────────────────────────────
    
    @app.get("/api/learning/status")
    async def get_learning_status():
        """Get overall learning status."""
        try:
            return JSONResponse({
                "dataset_builder": dataset_builder.get_stats(),
                "training_trigger": training_trigger.get_stats(),
                "evaluator": evaluator.get_stats(),
                "adapter_registry": adapter_registry.get_stats(),
                "hot_swap_router": hot_swap_router.get_status()
            })
        except Exception as e:
            logger.error(f"Get learning status error: {e}")
            raise HTTPException(status_code=400, detail(str(e))
