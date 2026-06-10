#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade clones backend
ASIMNEXUS Clones Backend
========================
Clones API endpoints for clone orchestration.
Provides REST interface to core.clone_orchestrator.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("AsimNexus.Clones")


def setup_clones_routes(app, db_path: str = "data/clone_orchestrator.db"):
    """
    Setup clones API routes on FastAPI app.
    Call this from simple_backend.py to wire clones endpoints.
    """
    from core.clone_orchestrator import get_clone_orchestrator, CloneRole, ConsensusType
    
    # Initialize clone orchestrator
    clone_orchestrator = get_clone_orchestrator(db_path)
    
    class CreateTaskRequest(BaseModel):
        """Request model for creating a task."""
        description: str
        required_skills: List[str]
        priority: int = 5
        metadata: Optional[Dict[str, Any]] = None
    
    class AssignTaskRequest(BaseModel):
        """Request model for assigning a task."""
        clone_id: Optional[str] = None
    
    class CompleteTaskRequest(BaseModel):
        """Request model for completing a task."""
        result: Dict[str, Any]
        success: bool = True
    
    class VoteRequest(BaseModel):
        """Request model for casting a vote."""
        clone_id: str
        vote: bool
        reasoning: str
    
    class ConsensusRequest(BaseModel):
        """Request model for creating consensus decision."""
        description: str
        consensus_type: str = "majority"
        required_roles: Optional[List[str]] = None
    
    @app.get("/api/clones")
    async def get_clones():
        """Get all founder clones."""
        try:
            clones = clone_orchestrator.clones
            return JSONResponse([
                {
                    "id": c.id,
                    "name": c.name,
                    "role": c.role.value,
                    "skills": c.skills,
                    "availability": c.availability,
                    "current_task": c.current_task,
                    "performance_score": c.performance_score
                }
                for c in clones.values()
            ])
        except Exception as e:
            logger.error(f"Get clones error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/clones/{clone_id}")
    async def get_clone(clone_id: str):
        """Get a specific clone by ID."""
        try:
            clone = clone_orchestrator.get_clone(clone_id)
            if not clone:
                raise HTTPException(status_code=404, detail="Clone not found")
            
            return JSONResponse({
                "id": clone.id,
                "name": clone.name,
                "role": clone.role.value,
                "skills": clone.skills,
                "availability": clone.availability,
                "current_task": clone.current_task,
                "performance_score": clone.performance_score,
                "metadata": clone.metadata
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get clone error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/clones/available")
    async def get_available_clones(min_availability: float = 0.5):
        """Get available clones."""
        try:
            clones = clone_orchestrator.get_available_clones(min_availability)
            return JSONResponse([
                {
                    "id": c.id,
                    "name": c.name,
                    "role": c.role.value,
                    "skills": c.skills,
                    "availability": c.availability,
                    "performance_score": c.performance_score
                }
                for c in clones
            ])
        except Exception as e:
            logger.error(f"Get available clones error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/clones/skill/{skill}")
    async def get_clones_by_skill(skill: str):
        """Get clones with a specific skill."""
        try:
            clones = clone_orchestrator.get_clones_by_skill(skill)
            return JSONResponse([
                {
                    "id": c.id,
                    "name": c.name,
                    "role": c.role.value,
                    "skills": c.skills,
                    "availability": c.availability,
                    "performance_score": c.performance_score
                }
                for c in clones
            ])
        except Exception as e:
            logger.error(f"Get clones by skill error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/clones/task")
    async def create_task(req: CreateTaskRequest):
        """Create a new task for delegation."""
        try:
            task_id = clone_orchestrator.create_task(
                description=req.description,
                required_skills=req.required_skills,
                priority=req.priority,
                metadata=req.metadata
            )
            
            return JSONResponse({
                "id": task_id,
                "description": req.description,
                "required_skills": req.required_skills,
                "priority": req.priority,
                "status": "pending"
            })
        except Exception as e:
            logger.error(f"Create task error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/clones/task/{task_id}/assign")
    async def assign_task(task_id: str, req: AssignTaskRequest):
        """Assign a task to a clone."""
        try:
            assigned_clone_id = clone_orchestrator.assign_task(task_id, req.clone_id)
            if not assigned_clone_id:
                raise HTTPException(status_code=400, detail="Failed to assign task")
            
            return JSONResponse({
                "task_id": task_id,
                "assigned_to": assigned_clone_id,
                "status": "assigned"
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Assign task error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/clones/task/{task_id}/complete")
    async def complete_task(task_id: str, req: CompleteTaskRequest):
        """Mark a task as completed."""
        try:
            success = clone_orchestrator.complete_task(task_id, req.result, req.success)
            if not success:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return JSONResponse({
                "task_id": task_id,
                "status": "completed" if req.success else "failed",
                "success": req.success
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Complete task error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/clones/consensus")
    async def create_consensus(req: ConsensusRequest):
        """Create a consensus decision."""
        try:
            # Convert string to enum
            try:
                consensus_type = ConsensusType(req.consensus_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid consensus_type: {req.consensus_type}")
            
            # Convert role strings to enums if provided
            required_roles = None
            if req.required_roles:
                try:
                    required_roles = [CloneRole(r) for r in req.required_roles]
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=f"Invalid role: {e}")
            
            decision_id = clone_orchestrator.create_consensus_decision(
                description=req.description,
                consensus_type=consensus_type,
                required_roles=required_roles
            )
            
            return JSONResponse({
                "id": decision_id,
                "description": req.description,
                "consensus_type": req.consensus_type,
                "status": "pending"
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Create consensus error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/clones/consensus/{decision_id}/vote")
    async def cast_vote(decision_id: str, req: VoteRequest):
        """Cast a vote on a consensus decision."""
        try:
            success = clone_orchestrator.cast_vote(
                decision_id=decision_id,
                clone_id=req.clone_id,
                vote=req.vote,
                reasoning=req.reasoning
            )
            if not success:
                raise HTTPException(status_code=400, detail="Failed to cast vote")
            
            return JSONResponse({
                "decision_id": decision_id,
                "clone_id": req.clone_id,
                "vote": req.vote,
                "status": "voted"
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Cast vote error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/clones/consensus/{decision_id}")
    async def get_consensus(decision_id: str):
        """Get a consensus decision."""
        try:
            decision = clone_orchestrator.decisions.get(decision_id)
            if not decision:
                raise HTTPException(status_code=404, detail="Decision not found")
            
            return JSONResponse({
                "id": decision.id,
                "description": decision.description,
                "consensus_type": decision.consensus_type.value,
                "required_clones": decision.required_clones,
                "votes": [
                    {
                        "clone_id": v.clone_id,
                        "vote": v.vote,
                        "reasoning": v.reasoning,
                        "timestamp": v.timestamp
                    }
                    for v in decision.votes
                ],
                "status": decision.status,
                "result": decision.result,
                "created_at": decision.created_at,
                "resolved_at": decision.resolved_at
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get consensus error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/clones/status")
    async def get_clones_status():
        """Get overall clone orchestrator status."""
        try:
            status = clone_orchestrator.get_status()
            return JSONResponse(status)
        except Exception as e:
            logger.error(f"Get clones status error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
