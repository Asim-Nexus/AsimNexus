#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade clone orchestration
ASIMNEXUS Clone Orchestrator
============================
15 Founder Clones task delegation and consensus.
Distributed intelligence layer for AsimNexus.
"""

import logging
import sqlite3
import json
import secrets
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger("AsimNexus.CloneOrchestrator")


class CloneRole(Enum):
    """Specialized roles for founder clones."""
    ARCHITECT = "architect"           # System design and architecture
    ENGINEER = "engineer"             # Implementation and debugging
    SCIENTIST = "scientist"           # Research and analysis
    DIPLOMAT = "diplomat"             # Communication and coordination
    STRATEGIST = "strategist"         # Planning and decision making
    ARTIST = "artist"                 # Creative and design
    TEACHER = "teacher"               # Education and explanation
    GUARDIAN = "guardian"             # Security and safety
    EXPLORER = "explorer"             # Discovery and innovation
    BUILDER = "builder"               # Construction and assembly
    HEALER = "healer"                 # Problem solving and repair
    VISIONARY = "visionary"           # Long-term planning
    WARRIOR = "warrior"               # Defense and protection
    SAGE = "sage"                    # Wisdom and guidance
    MERCHANT = "merchant"             # Resource management


class TaskStatus(Enum):
    """Status of tasks assigned to clones."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConsensusType(Enum):
    """Types of consensus mechanisms."""
    UNANIMOUS = "unanimous"           # All must agree
    MAJORITY = "majority"             # Simple majority
    SUPERMAJORITY = "supermajority"   # 2/3 majority
    WEIGHTED = "weighted"             # Weighted by role importance


@dataclass
class Clone:
    """Founder clone with specialized skills."""
    id: str
    name: str
    role: CloneRole
    skills: List[str]
    availability: float = 1.0  # 0.0 to 1.0
    current_task: Optional[str] = None
    performance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Task to be delegated to clones."""
    id: str
    description: str
    required_skills: List[str]
    priority: int = 5  # 1-10
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None  # Clone ID
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsensusVote:
    """Vote from a clone on a decision."""
    clone_id: str
    decision_id: str
    vote: bool  # True for approve, False for reject
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ConsensusDecision:
    """Decision requiring consensus among clones."""
    id: str
    description: str
    consensus_type: ConsensusType
    required_clones: List[str]  # Clone IDs that must vote
    votes: List[ConsensusVote] = field(default_factory=list)
    status: str = "pending"  # pending, approved, rejected
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: Optional[str] = None
    result: Optional[bool] = None


class CloneOrchestrator:
    """
    Orchestrates 15 Founder Clones for task delegation and consensus.
    Manages clone states, task assignment, and decision making.
    """
    
    def __init__(self, db_path: str = "data/clone_orchestrator.db"):
        self.db_path = db_path
        self.clones: Dict[str, Clone] = {}
        self.tasks: Dict[str, Task] = {}
        self.decisions: Dict[str, ConsensusDecision] = {}
        
        self._init_db()
        self._init_founder_clones()
        
        logger.info(f"🧬 CloneOrchestrator initialized with {len(self.clones)} founder clones")
    
    def _init_db(self):
        """Initialize database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Clones table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clones (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    skills TEXT NOT NULL,
                    availability REAL DEFAULT 1.0,
                    current_task TEXT,
                    performance_score REAL DEFAULT 1.0,
                    metadata TEXT
                )
            """)
            
            # Tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    required_skills TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    status TEXT NOT NULL,
                    assigned_to TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    result TEXT,
                    metadata TEXT
                )
            """)
            
            # Consensus decisions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS consensus_decisions (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    consensus_type TEXT NOT NULL,
                    required_clones TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    result INTEGER
                )
            """)
            
            # Votes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    id TEXT PRIMARY KEY,
                    decision_id TEXT NOT NULL,
                    clone_id TEXT NOT NULL,
                    vote INTEGER NOT NULL,
                    reasoning TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (decision_id) REFERENCES consensus_decisions(id),
                    FOREIGN KEY (clone_id) REFERENCES clones(id)
                )
            """)
            
            conn.commit()
    
    def _init_founder_clones(self):
        """Initialize the 15 Founder Clones with their roles and skills."""
        founder_clones = [
            Clone(
                id="clone_architect",
                name="Atlas",
                role=CloneRole.ARCHITECT,
                skills=["system_design", "architecture", "patterns", "scalability"]
            ),
            Clone(
                id="clone_engineer",
                name="Forge",
                role=CloneRole.ENGINEER,
                skills=["implementation", "debugging", "optimization", "testing"]
            ),
            Clone(
                id="clone_scientist",
                name="Nova",
                role=CloneRole.SCIENTIST,
                skills=["research", "analysis", "experimentation", "data_science"]
            ),
            Clone(
                id="clone_diplomat",
                name="Harmony",
                role=CloneRole.DIPLOMAT,
                skills=["communication", "coordination", "negotiation", "mediation"]
            ),
            Clone(
                id="clone_strategist",
                name="Vision",
                role=CloneRole.STRATEGIST,
                skills=["planning", "decision_making", "risk_assessment", "optimization"]
            ),
            Clone(
                id="clone_artist",
                name="Muse",
                role=CloneRole.ARTIST,
                skills=["design", "creativity", "aesthetics", "user_experience"]
            ),
            Clone(
                id="clone_teacher",
                name="Sage",
                role=CloneRole.TEACHER,
                skills=["education", "explanation", "documentation", "mentoring"]
            ),
            Clone(
                id="clone_guardian",
                name="Shield",
                role=CloneRole.GUARDIAN,
                skills=["security", "safety", "compliance", "auditing"]
            ),
            Clone(
                id="clone_explorer",
                name="Scout",
                role=CloneRole.EXPLORER,
                skills=["discovery", "innovation", "exploration", "experimentation"]
            ),
            Clone(
                id="clone_builder",
                name="Construct",
                role=CloneRole.BUILDER,
                skills=["construction", "assembly", "integration", "deployment"]
            ),
            Clone(
                id="clone_healer",
                name="Remedy",
                role=CloneRole.HEALER,
                skills=["problem_solving", "repair", "troubleshooting", "optimization"]
            ),
            Clone(
                id="clone_visionary",
                name="Oracle",
                role=CloneRole.VISIONARY,
                skills=["long_term_planning", "foresight", "trend_analysis", "strategy"]
            ),
            Clone(
                id="clone_warrior",
                name="Defender",
                role=CloneRole.WARRIOR,
                skills=["defense", "protection", "resilience", "security"]
            ),
            Clone(
                id="clone_sage",
                name="Wisdom",
                role=CloneRole.SAGE,
                skills=["wisdom", "guidance", "counsel", "ethics"]
            ),
            Clone(
                id="clone_merchant",
                name="Balance",
                role=CloneRole.MERCHANT,
                skills=["resource_management", "optimization", "efficiency", "planning"]
            ),
        ]
        
        for clone in founder_clones:
            self.clones[clone.id] = clone
            self._persist_clone(clone)
    
    def _persist_clone(self, clone: Clone):
        """Persist clone to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO clones (id, name, role, skills, availability, current_task, performance_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clone.id,
                clone.name,
                clone.role.value,
                json.dumps(clone.skills),
                clone.availability,
                clone.current_task,
                clone.performance_score,
                json.dumps(clone.metadata)
            ))
            conn.commit()
    
    def get_clone(self, clone_id: str) -> Optional[Clone]:
        """Get a clone by ID."""
        return self.clones.get(clone_id)
    
    def get_available_clones(self, min_availability: float = 0.5) -> List[Clone]:
        """Get clones with availability above threshold."""
        return [c for c in self.clones.values() if c.availability >= min_availability]
    
    def get_clones_by_skill(self, skill: str) -> List[Clone]:
        """Get clones that have a specific skill."""
        return [c for c in self.clones.values() if skill in c.skills]
    
    def create_task(self, description: str, required_skills: List[str],
                   priority: int = 5, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new task for delegation.
        Returns task ID.
        """
        task_id = secrets.token_hex(8)
        task = Task(
            id=task_id,
            description=description,
            required_skills=required_skills,
            priority=priority,
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        self._persist_task(task)
        
        logger.info(f"📋 Created task {task_id}: {description[:50]}...")
        return task_id
    
    def _persist_task(self, task: Task):
        """Persist task to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks (id, description, required_skills, priority, status, assigned_to, created_at, completed_at, result, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.description,
                json.dumps(task.required_skills),
                task.priority,
                task.status.value,
                task.assigned_to,
                task.created_at,
                task.completed_at,
                json.dumps(task.result) if task.result else None,
                json.dumps(task.metadata)
            ))
            conn.commit()
    
    def assign_task(self, task_id: str, clone_id: Optional[str] = None) -> Optional[str]:
        """
        Assign a task to a clone.
        If clone_id is None, automatically selects best available clone.
        Returns the assigned clone ID.
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return None
        
        if task.status != TaskStatus.PENDING:
            logger.warning(f"Task {task_id} is not pending (status: {task.status})")
            return None
        
        # Auto-select clone if not specified
        if clone_id is None:
            clone_id = self._select_best_clone(task)
            if not clone_id:
                logger.warning(f"No suitable clone found for task {task_id}")
                return None
        
        clone = self.clones.get(clone_id)
        if not clone:
            logger.warning(f"Clone {clone_id} not found")
            return None
        
        # Assign task
        task.assigned_to = clone_id
        task.status = TaskStatus.ASSIGNED
        clone.current_task = task_id
        clone.availability = max(0.0, clone.availability - 0.3)  # Reduce availability
        
        self._persist_task(task)
        self._persist_clone(clone)
        
        logger.info(f"✅ Assigned task {task_id} to clone {clone.name} ({clone.role.value})")
        return clone_id
    
    def _select_best_clone(self, task: Task) -> Optional[str]:
        """Select the best available clone for a task based on skills and availability."""
        candidates = []
        
        for clone in self.clones.values():
            if clone.availability < 0.3:
                continue
            
            # Calculate skill match score
            skill_match = len(set(clone.skills) & set(task.required_skills))
            if skill_match == 0:
                continue
            
            # Calculate total score (skill match + availability + performance)
            score = skill_match * 10 + clone.availability * 5 + clone.performance_score * 3
            candidates.append((clone.id, score))
        
        if not candidates:
            return None
        
        # Sort by score and return best
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def complete_task(self, task_id: str, result: Dict[str, Any], success: bool = True) -> bool:
        """Mark a task as completed with result."""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.utcnow().isoformat()
        task.result = result
        
        # Free up the assigned clone
        if task.assigned_to:
            clone = self.clones.get(task.assigned_to)
            if clone:
                clone.current_task = None
                clone.availability = min(1.0, clone.availability + 0.3)
                if success:
                    clone.performance_score = min(1.0, clone.performance_score + 0.05)
                else:
                    clone.performance_score = max(0.0, clone.performance_score - 0.1)
                self._persist_clone(clone)
        
        self._persist_task(task)
        
        logger.info(f"✅ Task {task_id} completed (success: {success})")
        return True
    
    def create_consensus_decision(self, description: str, consensus_type: ConsensusType,
                                 required_roles: Optional[List[CloneRole]] = None) -> str:
        """
        Create a decision requiring consensus.
        Returns decision ID.
        """
        decision_id = secrets.token_hex(8)
        
        # Determine required clones
        if required_roles:
            required_clones = [c.id for c in self.clones.values() if c.role in required_roles]
        else:
            # Default: all clones
            required_clones = list(self.clones.keys())
        
        decision = ConsensusDecision(
            id=decision_id,
            description=description,
            consensus_type=consensus_type,
            required_clones=required_clones
        )
        
        self.decisions[decision_id] = decision
        self._persist_decision(decision)
        
        logger.info(f"🗳️  Created consensus decision {decision_id}: {description[:50]}...")
        return decision_id
    
    def _persist_decision(self, decision: ConsensusDecision):
        """Persist decision to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO consensus_decisions (id, description, consensus_type, required_clones, status, created_at, resolved_at, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision.id,
                decision.description,
                decision.consensus_type.value,
                json.dumps(decision.required_clones),
                decision.status,
                decision.created_at,
                decision.resolved_at,
                1 if decision.result else 0 if decision.result is not None else None
            ))
            conn.commit()
    
    def cast_vote(self, decision_id: str, clone_id: str, vote: bool, reasoning: str) -> bool:
        """Cast a vote on a consensus decision."""
        decision = self.decisions.get(decision_id)
        if not decision:
            logger.warning(f"Decision {decision_id} not found")
            return False
        
        if clone_id not in decision.required_clones:
            logger.warning(f"Clone {clone_id} not in required clones for decision {decision_id}")
            return False
        
        if decision.status != "pending":
            logger.warning(f"Decision {decision_id} is not pending (status: {decision.status})")
            return False
        
        # Check if clone already voted
        for existing_vote in decision.votes:
            if existing_vote.clone_id == clone_id:
                logger.warning(f"Clone {clone_id} already voted on decision {decision_id}")
                return False
        
        # Add vote
        vote_obj = ConsensusVote(
            clone_id=clone_id,
            decision_id=decision_id,
            vote=vote,
            reasoning=reasoning
        )
        decision.votes.append(vote_obj)
        
        # Persist vote
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO votes (id, decision_id, clone_id, vote, reasoning, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (secrets.token_hex(8), decision_id, clone_id, 1 if vote else 0, reasoning, vote_obj.timestamp))
            conn.commit()
        
        # Check if consensus reached
        self._check_consensus(decision)
        
        logger.info(f"🗳️  Clone {clone_id} voted {vote} on decision {decision_id}")
        return True
    
    def _check_consensus(self, decision: ConsensusDecision):
        """Check if consensus has been reached for a decision."""
        required_count = len(decision.required_clones)
        current_votes = len(decision.votes)
        
        if current_votes < required_count:
            return  # Not all votes cast yet
        
        # Count votes
        approve_count = sum(1 for v in decision.votes if v.vote)
        reject_count = required_count - approve_count
        
        # Determine result based on consensus type
        result = None
        
        if decision.consensus_type == ConsensusType.UNANIMOUS:
            result = approve_count == required_count
        elif decision.consensus_type == ConsensusType.MAJORITY:
            result = approve_count > reject_count
        elif decision.consensus_type == ConsensusType.SUPERMAJORITY:
            result = approve_count >= (required_count * 2 / 3)
        elif decision.consensus_type == ConsensusType.WEIGHTED:
            # Simple weighted: architect, engineer, guardian have more weight
            weight_map = {
                CloneRole.ARCHITECT: 2.0,
                CloneRole.ENGINEER: 2.0,
                CloneRole.GUARDIAN: 2.0,
            }
            approve_weight = 0.0
            reject_weight = 0.0
            for vote in decision.votes:
                clone = self.clones.get(vote.clone_id)
                weight = weight_map.get(clone.role, 1.0) if clone else 1.0
                if vote.vote:
                    approve_weight += weight
                else:
                    reject_weight += weight
            result = approve_weight > reject_weight
        
        # Update decision status
        if result is not None:
            decision.status = "approved" if result else "rejected"
            decision.result = result
            decision.resolved_at = datetime.utcnow().isoformat()
            self._persist_decision(decision)
            
            logger.info(f"🗳️  Decision {decision.id} resolved: {decision.status} ({approve_count}/{required_count})")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall orchestrator status."""
        total_clones = len(self.clones)
        available_clones = len(self.get_available_clones())
        
        total_tasks = len(self.tasks)
        pending_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        in_progress_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS])
        
        total_decisions = len(self.decisions)
        pending_decisions = len([d for d in self.decisions.values() if d.status == "pending"])
        
        return {
            "clones": {
                "total": total_clones,
                "available": available_clones,
                "busy": total_clones - available_clones
            },
            "tasks": {
                "total": total_tasks,
                "pending": pending_tasks,
                "in_progress": in_progress_tasks,
                "completed": total_tasks - pending_tasks - in_progress_tasks
            },
            "decisions": {
                "total": total_decisions,
                "pending": pending_decisions,
                "resolved": total_decisions - pending_decisions
            }
        }


# Global clone orchestrator instance
_clone_orchestrator: Optional[CloneOrchestrator] = None


def get_clone_orchestrator(db_path: str = "data/clone_orchestrator.db") -> CloneOrchestrator:
    """Get or create global clone orchestrator instance."""
    global _clone_orchestrator
    if _clone_orchestrator is None:
        _clone_orchestrator = CloneOrchestrator(db_path)
    return _clone_orchestrator


def reset_clone_orchestrator():
    """Reset global clone orchestrator instance (for testing)."""
    global _clone_orchestrator
    _clone_orchestrator = None
