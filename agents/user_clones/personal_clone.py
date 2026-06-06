
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Personal Clone System
==============================
Personal AI Container for each citizen
Agent Mode activation for Human-in-the-Loop tasks
Local inference with quantized models
"""

import asyncio
import logging
import hashlib
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("PersonalClone")

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
    AGENT_PAUSED = "agent_paused"
    AGENT_TERMINATED = "agent_terminated"

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

@dataclass
class PersonalCloneProfile:
    """Personal clone profile"""
    clone_id: str
    user_id: str
    name: str
    email: str
    phone: str
    date_of_birth: str
    nationality: str
    address: Dict[str, str]
    skills: List[SkillCategory]
    certifications: List[str]
    experience_years: int
    bio: str
    created_at: datetime
    updated_at: datetime

@dataclass
class AgentModeSession:
    """Agent mode session"""
    session_id: str
    clone_id: str
    duration_days: int
    start_time: datetime
    end_time: datetime
    status: AgentStatus
    tasks_completed: int = 0
    earnings: float = 0.0
    performance_score: float = 0.0
    client_feedback: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class TaskAssignment:
    """Task assigned to agent"""
    task_id: str
    session_id: str
    client_id: str
    task_type: str
    description: str
    priority: str  # "low", "medium", "high", "critical"
    deadline: datetime
    status: str  # "assigned", "in_progress", "completed", "rejected"
    assigned_at: datetime
    completed_at: Optional[datetime] = None
    payment: float = 0.0

class PersonalClone:
    """
    Personal AI Clone for each citizen
    Can switch to Agent Mode for Human-in-the-Loop tasks
    """
    
    def __init__(self, user_id: str, profile_data: Dict[str, Any]):
        self.clone_id = f"clone_{uuid.uuid4().hex[:12]}"
        self.user_id = user_id
        self.profile = self._create_profile(profile_data)
        self.agent_mode_sessions: List[AgentModeSession] = []
        self.current_session: Optional[AgentModeSession] = None
        self.task_queue: List[TaskAssignment] = []
        self.completed_tasks: List[TaskAssignment] = []
        self.earnings_history: List[Dict[str, Any]] = []
        self.local_model_loaded = False
        self.inference_engine = None
        
        logger.info(f"🧬 Personal Clone created: {self.clone_id} for user: {user_id}")
    
    def _create_profile(self, profile_data: Dict[str, Any]) -> PersonalCloneProfile:
        """Create personal clone profile"""
        skills = [
            SkillCategory(skill) for skill in profile_data.get("skills", [])
        ]
        
        return PersonalCloneProfile(
            clone_id=self.clone_id,
            user_id=self.user_id,
            name=profile_data.get("name", ""),
            email=profile_data.get("email", ""),
            phone=profile_data.get("phone", ""),
            date_of_birth=profile_data.get("date_of_birth", ""),
            nationality=profile_data.get("nationality", "Nepal"),
            address=profile_data.get("address", {}),
            skills=skills,
            certifications=profile_data.get("certifications", []),
            experience_years=profile_data.get("experience_years", 0),
            bio=profile_data.get("bio", ""),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def activate_agent_mode(
        self,
        duration: AgentModeDuration,
        skill_focus: SkillCategory
    ) -> AgentModeSession:
        """
        Activate Agent Mode for Human-in-the-Loop tasks
        User becomes available to perform HITL tasks for others
        """
        try:
            logger.info(f"🔄 Activating Agent Mode for clone: {self.clone_id}")
            logger.info(f"⏱️ Duration: {duration.value} days")
            logger.info(f"🎯 Skill Focus: {skill_focus.value}")
            
            # Create new session
            session = AgentModeSession(
                session_id=f"session_{uuid.uuid4().hex[:12]}",
                clone_id=self.clone_id,
                duration_days=duration.value,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(days=duration.value),
                status=AgentStatus.AGENT_ACTIVE
            )
            
            self.current_session = session
            self.agent_mode_sessions.append(session)
            
            # Load local inference model
            await self._load_local_model(skill_focus)
            
            logger.info(f"✅ Agent Mode activated - Session: {session.session_id}")
            logger.info(f"📅 Valid until: {session.end_time}")
            
            return session
            
        except Exception as e:
            logger.error(f"❌ Agent Mode activation error: {e}")
            raise
    
    async def deactivate_agent_mode(self) -> bool:
        """Deactivate current Agent Mode session"""
        try:
            if not self.current_session:
                logger.warning("⚠️ No active Agent Mode session")
                return False
            
            logger.info(f"🛑 Deactivating Agent Mode for clone: {self.clone_id}")
            
            # Update session status
            self.current_session.status = AgentStatus.NORMAL_USER
            self.current_session.end_time = datetime.utcnow()
            
            # Calculate final performance score
            self.current_session.performance_score = self._calculate_performance_score()
            
            # Save earnings
            if self.current_session.earnings > 0:
                self.earnings_history.append({
                    "session_id": self.current_session.session_id,
                    "amount": self.current_session.earnings,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Unload local model
            await self._unload_local_model()
            
            self.current_session = None
            
            logger.info("✅ Agent Mode deactivated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Agent Mode deactivation error: {e}")
            return False
    
    async def _load_local_model(self, skill_focus: SkillCategory) -> None:
        """Load quantized local model for inference"""
        try:
            logger.info(f"🧠 Loading local model for skill: {skill_focus.value}")
            
            # In production, this would load a quantized model
            # For now, we simulate the loading
            self.local_model_loaded = True
            self.inference_engine = f"model_{skill_focus.value}_quantized"
            
            logger.info(f"✅ Local model loaded: {self.inference_engine}")
            
        except Exception as e:
            logger.error(f"❌ Local model loading error: {e}")
    
    async def _unload_local_model(self) -> None:
        """Unload local model to free resources"""
        try:
            if self.local_model_loaded:
                logger.info("🧠 Unloading local model...")
                self.local_model_loaded = False
                self.inference_engine = None
                logger.info("✅ Local model unloaded")
            
        except Exception as e:
            logger.error(f"❌ Local model unloading error: {e}")
    
    async def receive_task_assignment(self, task: TaskAssignment) -> bool:
        """Receive a task assignment from the system"""
        try:
            if not self.current_session or self.current_session.status != AgentStatus.AGENT_ACTIVE:
                logger.warning("⚠️ Clone not in Agent Mode")
                return False
            
            # Check if task matches skills
            if not self._task_matches_skills(task):
                logger.warning(f"⚠️ Task does not match clone skills: {task.task_type}")
                return False
            
            # Add to task queue
            self.task_queue.append(task)
            task.status = "assigned"
            task.assigned_at = datetime.utcnow()
            
            logger.info(f"📋 Task assigned: {task.task_id} to clone: {self.clone_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Task assignment error: {e}")
            return False
    
    def _task_matches_skills(self, task: TaskAssignment) -> bool:
        """Check if task matches clone's skills"""
        task_type_lower = task.task_type.lower()
        
        for skill in self.profile.skills:
            if skill.value.lower() in task_type_lower:
                return True
        
        return False
    
    async def process_task(self, task_id: str) -> Dict[str, Any]:
        """Process a task using local inference"""
        try:
            task = next((t for t in self.task_queue if t.task_id == task_id), None)
            
            if not task:
                return {"success": False, "error": "Task not found"}
            
            logger.info(f"⚙️ Processing task: {task.task_id}")
            
            # Update task status
            task.status = "in_progress"
            
            # Use local inference for initial analysis
            if self.local_model_loaded:
                analysis = await self._local_inference(task)
                task.description = f"{task.description}\n\nAI Analysis: {analysis}"
            
            # For HITL tasks, human input is required
            result = {
                "success": True,
                "task_id": task.task_id,
                "clone_id": self.clone_id,
                "status": "requires_human_input",
                "ai_analysis": analysis if self.local_model_loaded else "No AI analysis",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Task processed: {task.task_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Task processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _local_inference(self, task: TaskAssignment) -> str:
        """Perform local inference on task"""
        try:
            # Simulate local inference
            # In production, this would use the loaded quantized model
            analysis = f"Local inference analysis for task: {task.task_type}. Priority: {task.priority}. Estimated completion time: 2-4 hours."
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Local inference error: {e}")
            return "Inference failed"
    
    async def complete_task(
        self,
        task_id: str,
        human_decision: str,
        confidence: float
    ) -> bool:
        """Complete a task with human decision"""
        try:
            task = next((t for t in self.task_queue if t.task_id == task_id), None)
            
            if not task:
                logger.warning(f"⚠️ Task not found: {task_id}")
                return False
            
            logger.info(f"✅ Completing task: {task_id}")
            
            # Update task
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            
            # Move to completed tasks
            self.task_queue.remove(task)
            self.completed_tasks.append(task)
            
            # Update session stats
            if self.current_session:
                self.current_session.tasks_completed += 1
                self.current_session.earnings += task.payment
            
            # Add client feedback
            if self.current_session:
                self.current_session.client_feedback.append({
                    "task_id": task_id,
                    "human_decision": human_decision,
                    "confidence": confidence,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            logger.info(f"💰 Earnings: {task.payment}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Task completion error: {e}")
            return False
    
    def _calculate_performance_score(self) -> float:
        """Calculate performance score based on completed tasks"""
        if not self.current_session:
            return 0.0
        
        if self.current_session.tasks_completed == 0:
            return 0.0
        
        # Calculate average confidence from feedback
        total_confidence = sum(
            feedback.get("confidence", 0.5)
            for feedback in self.current_session.client_feedback
        )
        
        avg_confidence = total_confidence / len(self.current_session.client_feedback) if self.current_session.client_feedback else 0.5
        
        # Calculate task completion rate
        completion_rate = self.current_session.tasks_completed / (self.current_session.tasks_completed + len(self.task_queue))
        
        # Combine metrics
        performance_score = (avg_confidence * 0.6) + (completion_rate * 0.4)
        
        return round(performance_score * 100, 2)
    
    def get_clone_status(self) -> Dict[str, Any]:
        """Get current clone status"""
        return {
            "clone_id": self.clone_id,
            "user_id": self.user_id,
            "name": self.profile.name,
            "agent_mode_active": self.current_session is not None,
            "current_session": {
                "session_id": self.current_session.session_id,
                "start_time": self.current_session.start_time.isoformat(),
                "end_time": self.current_session.end_time.isoformat(),
                "tasks_completed": self.current_session.tasks_completed,
                "earnings": self.current_session.earnings,
                "performance_score": self.current_session.performance_score
            } if self.current_session else None,
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "total_earnings": sum(e["amount"] for e in self.earnings_history),
            "skills": [skill.value for skill in self.profile.skills],
            "local_model_loaded": self.local_model_loaded
        }

class PersonalCloneManager:
    """Manager for all personal clones"""
    
    def __init__(self):
        self.clones: Dict[str, PersonalClone] = {}
        self.active_agents: Dict[str, AgentModeSession] = {}
        self.task_pool: List[TaskAssignment] = []
        
        logger.info("🧬 Personal Clone Manager initialized")
    
    async def create_clone(self, user_id: str, profile_data: Dict[str, Any]) -> PersonalClone:
        """Create a new personal clone"""
        clone = PersonalClone(user_id, profile_data)
        self.clones[clone.clone_id] = clone
        return clone
    
    def get_clone(self, clone_id: str) -> Optional[PersonalClone]:
        """Get a personal clone by ID"""
        return self.clones.get(clone_id)
    
    def get_clone_by_user(self, user_id: str) -> Optional[PersonalClone]:
        """Get a personal clone by user ID"""
        for clone in self.clones.values():
            if clone.user_id == user_id:
                return clone
        return None
    
    async def assign_task_to_agent(
        self,
        task_type: str,
        description: str,
        priority: str,
        deadline: datetime,
        payment: float,
        required_skill: SkillCategory
    ) -> Optional[TaskAssignment]:
        """Assign a task to an available agent"""
        try:
            # Find available agents with required skill
            available_agents = [
                clone for clone in self.clones.values()
                if clone.current_session and clone.current_session.status == AgentStatus.AGENT_ACTIVE
                and required_skill in clone.profile.skills
            ]
            
            if not available_agents:
                logger.warning(f"⚠️ No available agents for skill: {required_skill.value}")
                return None
            
            # Select best agent based on performance
            best_agent = max(
                available_agents,
                key=lambda c: c.current_session.performance_score if c.current_session else 0
            )
            
            # Create task assignment
            task = TaskAssignment(
                task_id=f"task_{uuid.uuid4().hex[:12]}",
                session_id=best_agent.current_session.session_id,
                client_id="system",
                task_type=task_type,
                description=description,
                priority=priority,
                deadline=deadline,
                status="assigned",
                assigned_at=datetime.utcnow(),
                payment=payment
            )
            
            # Assign to agent
            success = await best_agent.receive_task_assignment(task)
            
            if success:
                self.task_pool.append(task)
                logger.info(f"✅ Task assigned to agent: {best_agent.clone_id}")
                return task
            else:
                return None
            
        except Exception as e:
            logger.error(f"❌ Task assignment error: {e}")
            return None
    
    def get_active_agents_count(self) -> int:
        """Get count of active agents"""
        return len([
            clone for clone in self.clones.values()
            if clone.current_session and clone.current_session.status == AgentStatus.AGENT_ACTIVE
        ])
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        total_earnings = sum(
            session.earnings
            for clone in self.clones.values()
            for session in clone.agent_mode_sessions
        )
        
        return {
            "total_clones": len(self.clones),
            "active_agents": self.get_active_agents_count(),
            "total_tasks_completed": sum(len(clone.completed_tasks) for clone in self.clones.values()),
            "pending_tasks": sum(len(clone.task_queue) for clone in self.clones.values()),
            "total_earnings": total_earnings,
            "average_performance": self._calculate_average_performance()
        }
    
    def _calculate_average_performance(self) -> float:
        """Calculate average performance across all agents"""
        active_sessions = [
            clone.current_session
            for clone in self.clones.values()
            if clone.current_session and clone.current_session.tasks_completed > 0
        ]
        
        if not active_sessions:
            return 0.0
        
        total_performance = sum(session.performance_score for session in active_sessions)
        return total_performance / len(active_sessions)

# Global clone manager
_clone_manager = PersonalCloneManager()

async def main():
    """Main entry point for testing"""
    # Create a test clone
    profile_data = {
        "name": "Dr. Ram Bahadur",
        "email": "ram@example.com",
        "phone": "+977-9800000000",
        "date_of_birth": "1980-01-01",
        "nationality": "Nepal",
        "address": {"city": "Kathmandu", "country": "Nepal"},
        "skills": ["healthcare", "medical"],
        "certifications": ["MBBS", "MD"],
        "experience_years": 15,
        "bio": "Experienced medical doctor"
    }
    
    clone = await _clone_manager.create_clone("user_001", profile_data)
    
    # Activate agent mode
    session = await clone.activate_agent_mode(
        duration=AgentModeDuration.THIRTY_DAYS,
        skill_focus=SkillCategory.HEALTHCARE
    )
    
    # Get status
    status = clone.get_clone_status()
    print(f"Clone Status: {status}")
    
    # Get system stats
    stats = _clone_manager.get_system_stats()
    print(f"System Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
