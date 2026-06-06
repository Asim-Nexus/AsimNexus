
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Agent Switch API
==========================
API for activating/deactivating Agent Mode
Human-in-the-Loop task management
Payment and earnings tracking
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

logger = logging.getLogger("AgentSwitchAPI")

class AgentModeDuration(Enum):
    """Agent mode duration options"""
    FIVE_DAYS = 5
    FIFTEEN_DAYS = 15
    THIRTY_DAYS = 30
    NINETY_DAYS = 90

class AgentStatus(Enum):
    """Agent status"""
    NORMAL_USER = "normal_user"
    AGENT_ACTIVE = "agent_active"
    AGENT_PAUSED = "agent_paUSED"

class SkillCategory(Enum):
    """Skill categories for agent mode"""
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    FINANCE = "finance"
    EDUCATION = "education"
    TECHNICAL = "technical"
    ADMINISTRATIVE = "administrative"
    CREATIVE = "creative"
    RESEARCH = "research"

# Pydantic models for API
class ActivateAgentModeRequest(BaseModel):
    """Request to activate agent mode"""
    user_id: str
    duration_days: int
    skill_focus: str
    bio: Optional[str] = None
    certifications: Optional[List[str]] = None
    experience_years: Optional[int] = 0

class DeactivateAgentModeRequest(BaseModel):
    """Request to deactivate agent mode"""
    user_id: str
    session_id: str

class CompleteTaskRequest(BaseModel):
    """Request to complete a task"""
    user_id: str
    task_id: str
    human_decision: str
    confidence: float

class AgentModeResponse(BaseModel):
    """Response for agent mode operations"""
    success: bool
    message: str
    session_id: Optional[str] = None
    status: Optional[str] = None
    earnings: Optional[float] = None
    tasks_completed: Optional[int] = None

class AgentSwitchAPI:
    """
    Agent Switch API for Agent Mode activation
    FastAPI-based REST API
    """
    
    def __init__(self):
        self.app = FastAPI(title="ASIMNEXUS Agent Switch API", version="1.0")
        self.security = HTTPBearer()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.task_assignments: Dict[str, Dict[str, Any]] = {}
        self.earnings_ledger: Dict[str, List[Dict[str, Any]]] = {}
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self) -> None:
        """Setup API routes"""
        
        @self.app.post("/api/agent/activate")
        async def activate_agent_mode(
            request: ActivateAgentModeRequest,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ) -> AgentModeResponse:
            """Activate agent mode for a user"""
            try:
                logger.info(f"🔄 Activating agent mode for user: {request.user_id}")
                
                # Validate duration
                valid_durations = [d.value for d in AgentModeDuration]
                if request.duration_days not in valid_durations:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid duration. Valid options: {valid_durations}"
                    )
                
                # Validate skill focus
                valid_skills = [s.value for s in SkillCategory]
                if request.skill_focus not in valid_skills:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid skill focus. Valid options: {valid_skills}"
                    )
                
                # Check if user already has active session
                existing_session = self._get_active_session(request.user_id)
                if existing_session:
                    return AgentModeResponse(
                        success=False,
                        message="User already has an active agent session",
                        session_id=existing_session["session_id"],
                        status=existing_session["status"]
                    )
                
                # Create agent session
                session_id = f"session_{uuid.uuid4().hex[:12]}"
                session = {
                    "session_id": session_id,
                    "user_id": request.user_id,
                    "duration_days": request.duration_days,
                    "skill_focus": request.skill_focus,
                    "start_time": datetime.utcnow().isoformat(),
                    "end_time": (datetime.utcnow() + timedelta(days=request.duration_days)).isoformat(),
                    "status": "agent_active",
                    "tasks_completed": 0,
                    "earnings": 0.0,
                    "performance_score": 0.0,
                    "bio": request.bio,
                    "certifications": request.certifications or [],
                    "experience_years": request.experience_years or 0
                }
                
                self.active_sessions[session_id] = session
                
                # Update user profile
                self.user_profiles[request.user_id] = {
                    "user_id": request.user_id,
                    "skill_focus": request.skill_focus,
                    "certifications": request.certifications or [],
                    "experience_years": request.experience_years or 0,
                    "total_sessions": 1,
                    "total_earnings": 0.0,
                    "total_tasks_completed": 0
                }
                
                logger.info(f"✅ Agent mode activated: {session_id}")
                
                return AgentModeResponse(
                    success=True,
                    message="Agent mode activated successfully",
                    session_id=session_id,
                    status="agent_active"
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Agent mode activation error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/agent/deactivate")
        async def deactivate_agent_mode(
            request: DeactivateAgentModeRequest,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ) -> AgentModeResponse:
            """Deactivate agent mode for a user"""
            try:
                logger.info(f"🛑 Deactivating agent mode: {request.session_id}")
                
                session = self.active_sessions.get(request.session_id)
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                if session["user_id"] != request.user_id:
                    raise HTTPException(status_code=403, detail="Unauthorized")
                
                # Update session status
                session["status"] = "normal_user"
                session["end_time"] = datetime.utcnow().isoformat()
                
                # Calculate final performance score
                session["performance_score"] = self._calculate_performance_score(session)
                
                # Save earnings
                if session["earnings"] > 0:
                    if request.user_id not in self.earnings_ledger:
                        self.earnings_ledger[request.user_id] = []
                    
                    self.earnings_ledger[request.user_id].append({
                        "session_id": request.session_id,
                        "amount": session["earnings"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Update user profile
                if request.user_id in self.user_profiles:
                    profile = self.user_profiles[request.user_id]
                    profile["total_earnings"] += session["earnings"]
                    profile["total_tasks_completed"] += session["tasks_completed"]
                
                logger.info(f"✅ Agent mode deactivated: {request.session_id}")
                
                return AgentModeResponse(
                    success=True,
                    message="Agent mode deactivated successfully",
                    earnings=session["earnings"],
                    tasks_completed=session["tasks_completed"]
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Agent mode deactivation error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/agent/complete-task")
        async def complete_task(
            request: CompleteTaskRequest,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ) -> AgentModeResponse:
            """Complete a task and earn payment"""
            try:
                logger.info(f"✅ Completing task: {request.task_id}")
                
                # Get active session
                session = self._get_active_session(request.user_id)
                if not session:
                    raise HTTPException(status_code=404, detail="No active agent session")
                
                # Get task assignment
                task = self.task_assignments.get(request.task_id)
                if not task:
                    raise HTTPException(status_code=404, detail="Task not found")
                
                if task["assigned_to"] != request.user_id:
                    raise HTTPException(status_code=403, detail="Task not assigned to this user")
                
                # Update task status
                task["status"] = "completed"
                task["completed_at"] = datetime.utcnow().isoformat()
                task["human_decision"] = request.human_decision
                task["confidence"] = request.confidence
                
                # Update session
                session["tasks_completed"] += 1
                session["earnings"] += task["payment"]
                
                # Add feedback to session
                if "feedback" not in session:
                    session["feedback"] = []
                
                session["feedback"].append({
                    "task_id": request.task_id,
                    "human_decision": request.human_decision,
                    "confidence": request.confidence,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"✅ Task completed: {request.task_id}")
                logger.info(f"💰 Earnings: {task['payment']}")
                
                return AgentModeResponse(
                    success=True,
                    message="Task completed successfully",
                    earnings=task["payment"],
                    tasks_completed=session["tasks_completed"]
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Task completion error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/agent/status/{user_id}")
        async def get_agent_status(
            user_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ) -> Dict[str, Any]:
            """Get agent status for a user"""
            try:
                session = self._get_active_session(user_id)
                profile = self.user_profiles.get(user_id, {})
                
                return {
                    "user_id": user_id,
                    "has_active_session": session is not None,
                    "session": session if session else None,
                    "profile": profile,
                    "total_earnings": profile.get("total_earnings", 0.0),
                    "total_tasks_completed": profile.get("total_tasks_completed", 0)
                }
                
            except Exception as e:
                logger.error(f"❌ Status check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/agent/tasks/{user_id}")
        async def get_assigned_tasks(
            user_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ) -> List[Dict[str, Any]]:
            """Get tasks assigned to an agent"""
            try:
                assigned_tasks = [
                    task for task in self.task_assignments.values()
                    if task.get("assigned_to") == user_id and task["status"] == "assigned"
                ]
                
                return assigned_tasks
                
            except Exception as e:
                logger.error(f"❌ Task retrieval error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/agent/earnings/{user_id}")
        async def get_earnings(
            user_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ) -> Dict[str, Any]:
            """Get earnings history for a user"""
            try:
                earnings = self.earnings_ledger.get(user_id, [])
                total_earnings = sum(e["amount"] for e in earnings)
                
                return {
                    "user_id": user_id,
                    "total_earnings": total_earnings,
                    "earnings_history": earnings,
                    "transaction_count": len(earnings)
                }
                
            except Exception as e:
                logger.error(f"❌ Earnings retrieval error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _get_active_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get active session for a user"""
        for session in self.active_sessions.values():
            if session["user_id"] == user_id and session["status"] == "agent_active":
                # Check if session is still valid
                end_time = datetime.fromisoformat(session["end_time"])
                if datetime.utcnow() < end_time:
                    return session
        
        return None
    
    def _calculate_performance_score(self, session: Dict[str, Any]) -> float:
        """Calculate performance score for a session"""
        try:
            if session["tasks_completed"] == 0:
                return 0.0
            
            feedback = session.get("feedback", [])
            if not feedback:
                return 50.0
            
            total_confidence = sum(f.get("confidence", 0.5) for f in feedback)
            avg_confidence = total_confidence / len(feedback)
            
            performance_score = avg_confidence * 100
            return round(performance_score, 2)
            
        except Exception as e:
            logger.error(f"❌ Performance score calculation error: {e}")
            return 0.0
    
    async def assign_task_to_agent(
        self,
        task_type: str,
        description: str,
        priority: str,
        deadline: datetime,
        payment: float,
        required_skill: str
    ) -> Optional[Dict[str, Any]]:
        """Assign a task to an available agent"""
        try:
            logger.info(f"📋 Assigning task: {task_type}")
            
            # Find available agents with required skill
            available_agents = [
                session for session in self.active_sessions.values()
                if session["status"] == "agent_active"
                and session["skill_focus"] == required_skill
            ]
            
            if not available_agents:
                logger.warning(f"⚠️ No available agents for skill: {required_skill}")
                return None
            
            # Select best agent based on performance
            best_agent = max(
                available_agents,
                key=lambda s: s.get("performance_score", 0)
            )
            
            # Create task assignment
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            task = {
                "task_id": task_id,
                "task_type": task_type,
                "description": description,
                "priority": priority,
                "deadline": deadline.isoformat(),
                "payment": payment,
                "required_skill": required_skill,
                "assigned_to": best_agent["user_id"],
                "assigned_at": datetime.utcnow().isoformat(),
                "status": "assigned"
            }
            
            self.task_assignments[task_id] = task
            
            logger.info(f"✅ Task assigned to agent: {best_agent['user_id']}")
            return task
            
        except Exception as e:
            logger.error(f"❌ Task assignment error: {e}")
            return None
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get API status"""
        return {
            "active_sessions": len(self.active_sessions),
            "total_users": len(self.user_profiles),
            "pending_tasks": len([t for t in self.task_assignments.values() if t["status"] == "assigned"]),
            "completed_tasks": len([t for t in self.task_assignments.values() if t["status"] == "completed"]),
            "total_earnings_paid": sum(
                sum(e["amount"] for e in earnings)
                for earnings in self.earnings_ledger.values()
            )
        }

# Global API instance
_agent_switch_api = AgentSwitchAPI()

async def main():
    """Main entry point for testing"""
    # Test activating agent mode
    activation_request = ActivateAgentModeRequest(
        user_id="user_001",
        duration_days=30,
        skill_focus="healthcare",
        bio="Experienced medical doctor",
        certifications=["MBBS", "MD"],
        experience_years=15
    )
    
    response = await _agent_switch_api.app.routes[0].endpoint(activation_request, None)
    print(f"Activation response: {response}")
    
    # Get status
    status = _agent_switch_api.get_api_status()
    print(f"API status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
