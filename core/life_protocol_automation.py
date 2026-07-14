"""
Life Protocol Automation
========================
Automates life protocol tasks for digital twins.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProtocolPriority(Enum):
    """Priority levels for protocol tasks."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskType(Enum):
    """Types of automated tasks."""
    EDUCATION = "education"
    HEALTH = "health"
    FINANCE = "finance"
    SOCIAL = "social"
    CAREER = "career"
    PERSONAL_GROWTH = "personal_growth"


class TaskStatus(Enum):
    """Status of an automated task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AutomatedTask:
    """An automated task for a digital twin."""
    task_id: str
    twin_id: str
    event_type: TaskType
    status: TaskStatus
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None


class LifeProtocolAutomation:
    """System for automating life protocol tasks."""

    def __init__(self):
        self._lock = threading.Lock()
        self.tasks: Dict[str, AutomatedTask] = {}

    def auto_schedule_for_twin(self, twin_id: str) -> List[AutomatedTask]:
        """Auto-schedule tasks for a twin."""
        scheduled: List[AutomatedTask] = []
        task_types = [
            (TaskType.EDUCATION, "Complete education profile"),
            (TaskType.HEALTH, "Schedule health checkup"),
            (TaskType.FINANCE, "Review financial plan"),
            (TaskType.SOCIAL, "Update social connections"),
            (TaskType.CAREER, "Review career goals"),
            (TaskType.PERSONAL_GROWTH, "Set personal growth goals"),
        ]
        for task_type, description in task_types:
            task = AutomatedTask(
                task_id=f"task_{twin_id}_{task_type.value}_{datetime.now().timestamp()}",
                twin_id=twin_id,
                event_type=task_type,
                status=TaskStatus.PENDING,
                description=description,
            )
            with self._lock:
                self.tasks[task.task_id] = task
            scheduled.append(task)
        return scheduled

    def get_tasks_for_twin(self, twin_id: str) -> List[AutomatedTask]:
        """Get all tasks for a twin."""
        with self._lock:
            return [t for t in self.tasks.values() if t.twin_id == twin_id]

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a task."""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return {"status": "failed", "error": "Task not found"}
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = {"message": f"Task {task_id} completed successfully"}
            return {"status": "completed", "task_id": task_id}

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        with self._lock:
            return {
                "total_tasks": len(self.tasks),
                "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
                "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            }


_automation_instance: Optional[LifeProtocolAutomation] = None
_automation_lock: threading.Lock = threading.Lock()


def get_life_protocol_automation() -> LifeProtocolAutomation:
    """Get or create the singleton LifeProtocolAutomation instance."""
    global _automation_instance
    with _automation_lock:
        if _automation_instance is None:
            _automation_instance = LifeProtocolAutomation()
        return _automation_instance
