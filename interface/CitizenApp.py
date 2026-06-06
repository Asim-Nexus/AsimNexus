
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Citizen Application
=============================
Citizen interface for ASIMNEXUS
Personal clone management
Agent mode activation
Task and earnings tracking
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("CitizenApp")

class AgentModeDuration(Enum):
    """Agent mode duration options"""
    FIVE_DAYS = 5
    FIFTEEN_DAYS = 15
    THIRTY_DAYS = 30

class TaskStatus(Enum):
    """Task status"""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"

@dataclass
class CitizenProfile:
    """Citizen profile"""
    citizen_id: str
    name: str
    email: str
    phone: str
    date_of_birth: str
    nationality: str
    address: Dict[str, str]
    skills: List[str]
    certifications: List[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class AgentModeSession:
    """Agent mode session"""
    session_id: str
    citizen_id: str
    duration_days: int
    start_time: datetime
    end_time: datetime
    status: str  # "active", "completed", "paused"
    tasks_completed: int = 0
    earnings: float = 0.0
    performance_score: float = 0.0

@dataclass
class CitizenTask:
    """Task assigned to citizen"""
    task_id: str
    citizen_id: str
    task_type: str
    description: str
    priority: str  # "low", "medium", "high", "critical"
    deadline: datetime
    status: TaskStatus
    assigned_at: datetime
    completed_at: Optional[datetime] = None
    payment: float = 0.0
    client_feedback: Optional[str] = None

class CitizenApplication:
    """
    Citizen Application for ASIMNEXUS
    Personal clone management and agent mode
    """
    
    def __init__(self):
        self.citizens: Dict[str, CitizenProfile] = {}
        self.agent_sessions: Dict[str, AgentModeSession] = {}
        self.tasks: Dict[str, CitizenTask] = {}
        self.earnings_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize application
        self._initialize_application()
        
    def _initialize_application(self) -> None:
        """Initialize the citizen application"""
        logger.info("👤 Initializing Citizen Application...")
        logger.info("🧬 Features: Personal Clone, Agent Mode, Task Management")
        
        logger.info("✅ Citizen Application initialized")
    
    async def register_citizen(
        self,
        name: str,
        email: str,
        phone: str,
        date_of_birth: str,
        nationality: str,
        address: Dict[str, str],
        skills: List[str],
        certifications: List[str] = None
    ) -> CitizenProfile:
        """Register a new citizen"""
        try:
            logger.info(f"👤 Registering citizen: {name}")
            
            citizen = CitizenProfile(
                citizen_id=f"citizen_{uuid.uuid4().hex[:12]}",
                name=name,
                email=email,
                phone=phone,
                date_of_birth=date_of_birth,
                nationality=nationality,
                address=address,
                skills=skills,
                certifications=certifications or [],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.citizens[citizen.citizen_id] = citizen
            self.earnings_history[citizen.citizen_id] = []
            
            logger.info(f"✅ Citizen registered: {citizen.citizen_id}")
            return citizen
            
        except Exception as e:
            logger.error(f"❌ Citizen registration error: {e}")
            raise
    
    async def activate_agent_mode(
        self,
        citizen_id: str,
        duration: AgentModeDuration
    ) -> AgentModeSession:
        """Activate agent mode for citizen"""
        try:
            citizen = self.citizens.get(citizen_id)
            
            if not citizen:
                raise Exception("Citizen not found")
            
            # Check if citizen already has active session
            if citizen_id in self.agent_sessions:
                existing_session = self.agent_sessions[citizen_id]
                if existing_session.status == "active":
                    raise Exception("Agent mode already active")
            
            logger.info(f"🔄 Activating agent mode for citizen: {citizen_id}")
            logger.info(f"⏱️ Duration: {duration.value} days")
            
            session = AgentModeSession(
                session_id=f"session_{uuid.uuid4().hex[:12]}",
                citizen_id=citizen_id,
                duration_days=duration.value,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(days=duration.value),
                status="active"
            )
            
            self.agent_sessions[citizen_id] = session
            
            logger.info(f"✅ Agent mode activated: {session.session_id}")
            logger.info(f"📅 Valid until: {session.end_time}")
            
            return session
            
        except Exception as e:
            logger.error(f"❌ Agent mode activation error: {e}")
            raise
    
    async def deactivate_agent_mode(self, citizen_id: str) -> bool:
        """Deactivate agent mode for citizen"""
        try:
            session = self.agent_sessions.get(citizen_id)
            
            if not session:
                logger.warning("⚠️ No active agent mode session")
                return False
            
            logger.info(f"🛑 Deactivating agent mode for citizen: {citizen_id}")
            
            # Update session status
            session.status = "completed"
            session.end_time = datetime.utcnow()
            
            # Calculate final performance score
            session.performance_score = self._calculate_performance_score(citizen_id)
            
            # Save earnings
            if session.earnings > 0:
                self.earnings_history[citizen_id].append({
                    "session_id": session.session_id,
                    "amount": session.earnings,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            logger.info("✅ Agent mode deactivated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Agent mode deactivation error: {e}")
            return False
    
    async def receive_task(
        self,
        citizen_id: str,
        task_type: str,
        description: str,
        priority: str,
        deadline: datetime,
        payment: float
    ) -> CitizenTask:
        """Receive a task assignment"""
        try:
            citizen = self.citizens.get(citizen_id)
            
            if not citizen:
                raise Exception("Citizen not found")
            
            # Check if citizen has active agent mode
            if citizen_id not in self.agent_sessions:
                raise Exception("Agent mode not active")
            
            session = self.agent_sessions[citizen_id]
            if session.status != "active":
                raise Exception("Agent mode not active")
            
            logger.info(f"📋 Task assigned to citizen: {citizen_id}")
            
            task = CitizenTask(
                task_id=f"task_{uuid.uuid4().hex[:12]}",
                citizen_id=citizen_id,
                task_type=task_type,
                description=description,
                priority=priority,
                deadline=deadline,
                status=TaskStatus.ASSIGNED,
                assigned_at=datetime.utcnow(),
                payment=payment
            )
            
            self.tasks[task.task_id] = task
            
            logger.info(f"✅ Task assigned: {task.task_id}")
            return task
            
        except Exception as e:
            logger.error(f"❌ Task assignment error: {e}")
            raise
    
    async def complete_task(
        self,
        task_id: str,
        result: str,
        confidence: float
    ) -> bool:
        """Complete a task"""
        try:
            task = self.tasks.get(task_id)
            
            if not task:
                raise Exception("Task not found")
            
            logger.info(f"✅ Completing task: {task_id}")
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            # Update session stats
            session = self.agent_sessions.get(task.citizen_id)
            if session:
                session.tasks_completed += 1
                session.earnings += task.payment
            
            logger.info(f"💰 Earnings: {task.payment}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Task completion error: {e}")
            return False
    
    def _calculate_performance_score(self, citizen_id: str) -> float:
        """Calculate performance score for citizen"""
        try:
            session = self.agent_sessions.get(citizen_id)
            
            if not session or session.tasks_completed == 0:
                return 0.0
            
            # Calculate based on tasks completed and earnings
            performance = (session.tasks_completed * 10) + (session.earnings / 100)
            performance = min(performance, 100.0)
            
            return round(performance, 2)
            
        except Exception as e:
            logger.error(f"❌ Performance score calculation error: {e}")
            return 0.0
    
    async def get_citizen_status(self, citizen_id: str) -> Dict[str, Any]:
        """Get citizen status"""
        try:
            citizen = self.citizens.get(citizen_id)
            
            if not citizen:
                return {"success": False, "error": "Citizen not found"}
            
            session = self.agent_sessions.get(citizen_id)
            citizen_tasks = [t for t in self.tasks.values() if t.citizen_id == citizen_id]
            total_earnings = sum(e["amount"] for e in self.earnings_history.get(citizen_id, []))
            
            return {
                "success": True,
                "citizen_id": citizen.citizen_id,
                "name": citizen.name,
                "email": citizen.email,
                "skills": citizen.skills,
                "certifications": citizen.certifications,
                "agent_mode_active": session is not None and session.status == "active",
                "current_session": {
                    "session_id": session.session_id,
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat(),
                    "tasks_completed": session.tasks_completed,
                    "earnings": session.earnings,
                    "performance_score": session.performance_score
                } if session else None,
                "total_tasks": len(citizen_tasks),
                "completed_tasks": len([t for t in citizen_tasks if t.status == TaskStatus.COMPLETED]),
                "total_earnings": total_earnings,
                "pending_tasks": len([t for t in citizen_tasks if t.status == TaskStatus.ASSIGNED])
            }
            
        except Exception as e:
            logger.error(f"❌ Citizen status error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_available_tasks(self, citizen_id: str) -> List[Dict[str, Any]]:
        """Get available tasks for citizen"""
        try:
            citizen = self.citizens.get(citizen_id)
            
            if not citizen:
                return []
            
            # Get tasks assigned to this citizen
            citizen_tasks = [
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "description": task.description,
                    "priority": task.priority,
                    "deadline": task.deadline.isoformat(),
                    "status": task.status.value,
                    "payment": task.payment,
                    "assigned_at": task.assigned_at.isoformat()
                }
                for task in self.tasks.values()
                if task.citizen_id == citizen_id
            ]
            
            return citizen_tasks
            
        except Exception as e:
            logger.error(f"❌ Available tasks error: {e}")
            return []
    
    def get_application_status(self) -> Dict[str, Any]:
        """Get application status"""
        return {
            "total_citizens": len(self.citizens),
            "active_agent_sessions": len([s for s in self.agent_sessions.values() if s.status == "active"]),
            "total_tasks": len(self.tasks),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
            "total_earnings": sum(
                sum(e["amount"] for e in earnings)
                for earnings in self.earnings_history.values()
            )
        }

# Global citizen application instance
_citizen_app = CitizenApplication()

async def main():
    """Main entry point for testing"""
    # Register a citizen
    citizen = await _citizen_app.register_citizen(
        name="Ram Bahadur",
        email="ram@example.com",
        phone="+977-9800000000",
        date_of_birth="1980-01-01",
        nationality="Nepal",
        address={"city": "Kathmandu", "country": "Nepal"},
        skills=["healthcare", "medical"],
        certifications=["MBBS", "MD"]
    )
    
    print(f"Citizen registered: {citizen.name}")
    
    # Activate agent mode
    session = await _citizen_app.activate_agent_mode(
        citizen_id=citizen.citizen_id,
        duration=AgentModeDuration.THIRTY_DAYS
    )
    
    print(f"Agent mode activated: {session.session_id}")
    
    # Receive a task
    task = await _citizen_app.receive_task(
        citizen_id=citizen.citizen_id,
        task_type="document_verification",
        description="Verify medical documents",
        priority="high",
        deadline=datetime.utcnow() + timedelta(days=2),
        payment=50.0
    )
    
    print(f"Task assigned: {task.task_id}")
    
    # Complete the task
    await _citizen_app.complete_task(
        task_id=task.task_id,
        result="Documents verified successfully",
        confidence=0.95
    )
    
    # Get citizen status
    status = await _citizen_app.get_citizen_status(citizen.citizen_id)
    print(f"Citizen status: {status}")
    
    # Get application status
    app_status = _citizen_app.get_application_status()
    print(f"Application status: {app_status}")

if __name__ == "__main__":
    asyncio.run(main())
