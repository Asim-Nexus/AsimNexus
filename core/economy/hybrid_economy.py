
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Human-Agent Hybrid Economy
===================================
Hybrid economy supporting both User Mode and Agent User Mode
Includes: Task execution, value exchange, mode switching, economy orchestration
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid
import os

logger = logging.getLogger("HybridEconomy")


class EconomyMode(Enum):
    """Economy operation modes"""
    USER_MODE = "user_mode"  # Human directs agents
    AGENT_USER_MODE = "agent_user_mode"  # Agents operate autonomously
    HYBRID = "hybrid"  # Mixed operation


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Economy task"""
    task_id: str
    description: str
    requester_id: str
    executor_id: Optional[str]
    reward: float
    status: TaskStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class EconomyAccount:
    """Economy account for user or agent"""
    account_id: str
    owner_id: str
    owner_type: str  # "user" or "agent"
    balance: float = 0.0
    tasks_completed: int = 0
    tasks_created: int = 0


class HybridEconomy:
    """Human-Agent Hybrid Economy System"""
    
    def __init__(self):
        self.current_mode: EconomyMode = EconomyMode.USER_MODE
        self.tasks: Dict[str, Task] = {}
        self.accounts: Dict[str, EconomyAccount] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize hybrid economy"""
        logger.info("💰 Initializing Human-Agent Hybrid Economy...")
        logger.info("👤 Setting up User Mode")
        logger.info("🤖 Setting up Agent User Mode")
        logger.info("🔄 Setting up Hybrid Mode")
        logger.info("✅ Hybrid Economy initialized")
    
    def set_mode(self, mode: EconomyMode) -> None:
        """Set economy operation mode"""
        self.current_mode = mode
        logger.info(f"✅ Economy mode set to: {mode.value}")
    
    def create_account(self, owner_id: str, owner_type: str) -> EconomyAccount:
        """Create economy account"""
        account = EconomyAccount(
            account_id=f"acc_{uuid.uuid4().hex[:8]}",
            owner_id=owner_id,
            owner_type=owner_type,
            balance=1000.0  # Initial balance
        )
        self.accounts[account.account_id] = account
        logger.info(f"✅ Created {owner_type} account: {owner_id}")
        return account
    
    def create_task(
        self,
        description: str,
        requester_id: str,
        reward: float
    ) -> Task:
        """Create a task"""
        task = Task(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            description=description,
            requester_id=requester_id,
            executor_id=None,
            reward=reward,
            status=TaskStatus.PENDING
        )
        self.tasks[task.task_id] = task
        
        # Update requester's task count
        for account in self.accounts.values():
            if account.owner_id == requester_id:
                account.tasks_created += 1
        
        logger.info(f"✅ Created task: {task.task_id}")
        return task
    
    def assign_task(self, task_id: str, executor_id: str) -> bool:
        """Assign task to executor"""
        if task_id in self.tasks:
            self.tasks[task_id].executor_id = executor_id
            self.tasks[task_id].status = TaskStatus.ASSIGNED
            logger.info(f"✅ Assigned task {task_id} to {executor_id}")
            return True
        return False
    
    def complete_task(self, task_id: str) -> bool:
        """Complete a task and transfer reward"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            # Transfer reward
            if task.executor_id:
                for account in self.accounts.values():
                    if account.owner_id == task.executor_id:
                        account.balance += task.reward
                        account.tasks_completed += 1
            
            # Deduct from requester
            for account in self.accounts.values():
                if account.owner_id == task.requester_id:
                    account.balance -= task.reward
            
            logger.info(f"✅ Completed task {task_id}, reward: {task.reward}")
            return True
        return False
    
    def get_account_balance(self, owner_id: str) -> Optional[float]:
        """Get account balance"""
        for account in self.accounts.values():
            if account.owner_id == owner_id:
                return account.balance
        return None
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
    
    def get_economy_summary(self) -> Dict[str, Any]:
        """Get economy summary"""
        total_balance = sum(a.balance for a in self.accounts.values())
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        
        return {
            "current_mode": self.current_mode.value,
            "total_accounts": len(self.accounts),
            "total_balance": total_balance,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": len(self.get_pending_tasks())
        }


# Global instance
_hybrid_economy: Optional[HybridEconomy] = None


def get_hybrid_economy() -> HybridEconomy:
    """Get singleton instance"""
    global _hybrid_economy
    if _hybrid_economy is None:
        _hybrid_economy = HybridEconomy()
    return _hybrid_economy
