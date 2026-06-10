"""
ASIMNEXUS Decentralized Task Bus
================================
Full REAL implementation with JSONL persistence.
Distributed task queue with agent assignment, priority queuing, retries.

Features:
- Agent node registration with capabilities
- Task submission with priority levels
- Capability-based task assignment
- Automatic retry with configurable max retries
- Priority-ordered queue
- JSONL persistence
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger("TaskBus")

TASKBUS_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "taskbus.jsonl"
TASKBUS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskState(Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


PRIORITY_ORDER = {
    TaskPriority.CRITICAL: 0,
    TaskPriority.HIGH: 1,
    TaskPriority.MEDIUM: 2,
    TaskPriority.LOW: 3,
}


@dataclass
class BusTask:
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: str
    state: str
    assigned_agent: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    retry_count: int
    max_retries: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    timeout_seconds: int
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusTask":
        return cls(**data)


@dataclass
class AgentNode:
    node_id: str
    agent_id: str
    display_name: str
    capabilities: List[str]
    current_tasks: List[str]
    max_concurrent_tasks: int
    total_tasks_completed: int
    is_online: bool
    registered_at: str
    last_heartbeat: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentNode":
        return cls(**data)


class DecentralizedTaskBus:
    def __init__(self):
        self.tasks: Dict[str, BusTask] = {}
        self.agents: Dict[str, AgentNode] = {}
        self.task_queue: List[str] = []
        self._load_from_db()

    def _persist(self, entry_type: str, data: Dict[str, Any]) -> None:
        try:
            record = {"__type__": entry_type, **data}
            with open(TASKBUS_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Persist failed: {e}")

    def _load_from_db(self) -> None:
        path = TASKBUS_DB_PATH
        if not path.exists():
            logger.info("🚌 Task Bus initialized (no existing data)")
            return
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    entry_type = data.pop("__type__", None)
                    if entry_type == "task":
                        task = BusTask.from_dict(data)
                        self.tasks[task.task_id] = task
                        if task.state in (TaskState.QUEUED.value, TaskState.RETRYING.value):
                            self.task_queue.append(task.task_id)
                    elif entry_type == "agent":
                        agent = AgentNode.from_dict(data)
                        self.agents[agent.node_id] = agent
            self._sort_queue()
            logger.info(f"🚌 Loaded {len(self.tasks)} tasks, {len(self.agents)} agents")
        except Exception as e:
            logger.warning(f"Failed to load task bus: {e}")

    def _sort_queue(self) -> None:
        self.task_queue.sort(key=lambda tid: PRIORITY_ORDER.get(
            TaskPriority(self.tasks[tid].priority), 99))

    def register_agent(self, agent_id: str, capabilities: List[str],
                       display_name: str = "", max_concurrent: int = 5,
                       metadata: Dict[str, Any] = None) -> AgentNode:
        for node in self.agents.values():
            if node.agent_id == agent_id:
                return node
        node = AgentNode(
            node_id=f"node_{uuid.uuid4().hex[:12]}",
            agent_id=agent_id,
            display_name=display_name or agent_id,
            capabilities=capabilities,
            current_tasks=[],
            max_concurrent_tasks=max_concurrent,
            total_tasks_completed=0,
            is_online=True,
            registered_at=datetime.utcnow().isoformat(),
            last_heartbeat=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        self.agents[node.node_id] = node
        self._persist("agent", node.to_dict())
        logger.info(f"✅ Agent registered: {agent_id} with {len(capabilities)} capabilities")
        return node

    def unregister_agent(self, node_id: str) -> bool:
        if node_id not in self.agents:
            return False
        agent = self.agents.pop(node_id)
        # Reassign active tasks back to queue
        to_reassign = [t for t in self.tasks.values()
                       if t.assigned_agent == agent.agent_id
                       and t.state in (TaskState.ASSIGNED.value, TaskState.RUNNING.value)]
        for t in to_reassign:
            t.state = TaskState.QUEUED.value
            t.assigned_agent = None
            self.task_queue.append(t.task_id)
            self._persist("task", t.to_dict())
        self._sort_queue()
        logger.info(f"🗑️ Agent unregistered: {node_id}")
        return True

    def submit_task(self, task_type: str, payload: Dict[str, Any],
                    priority: TaskPriority = TaskPriority.MEDIUM,
                    max_retries: int = 3, timeout_seconds: int = 300,
                    metadata: Dict[str, Any] = None) -> BusTask:
        task = BusTask(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            task_type=task_type,
            payload=payload,
            priority=priority.value,
            state=TaskState.QUEUED.value,
            assigned_agent=None,
            result=None,
            error=None,
            retry_count=0,
            max_retries=max_retries,
            created_at=datetime.utcnow().isoformat(),
            started_at=None,
            completed_at=None,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {},
        )
        self.tasks[task.task_id] = task
        self.task_queue.append(task.task_id)
        self._sort_queue()
        self._persist("task", task.to_dict())
        logger.info(f"📥 Task submitted: {task.task_id} [{priority.value}] {task_type}")
        return task

    def assign_next_task(self, agent_id: str) -> Optional[Dict[str, Any]]:
        agent_node = None
        for node in self.agents.values():
            if node.agent_id == agent_id:
                agent_node = node
                break
        if not agent_node or not agent_node.is_online:
            return None
        if len(agent_node.current_tasks) >= agent_node.max_concurrent_tasks:
            return None
        for task_id in self.task_queue:
            if task_id not in self.tasks:
                continue
            task = self.tasks[task_id]
            if task.state not in (TaskState.QUEUED.value, TaskState.RETRYING.value):
                continue
            required_caps = task.payload.get("required_capabilities", [])
            if all(cap in agent_node.capabilities for cap in required_caps):
                task.state = TaskState.ASSIGNED.value
                task.assigned_agent = agent_id
                task.started_at = datetime.utcnow().isoformat()
                agent_node.current_tasks.append(task_id)
                agent_node.last_heartbeat = datetime.utcnow().isoformat()
                self.task_queue.remove(task_id)
                self._persist("task", task.to_dict())
                self._persist("agent", agent_node.to_dict())
                logger.info(f"➡️ Task {task_id} assigned to {agent_id}")
                return task.to_dict()
        return None

    def start_task(self, task_id: str, agent_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        task = self.tasks[task_id]
        if task.assigned_agent != agent_id:
            return False
        if task.state != TaskState.ASSIGNED.value:
            return False
        task.state = TaskState.RUNNING.value
        task.started_at = datetime.utcnow().isoformat()
        self._persist("task", task.to_dict())
        logger.info(f"▶️ Task {task_id} running on {agent_id}")
        return True

    def complete_task(self, task_id: str, agent_id: str,
                      result: Dict[str, Any]) -> bool:
        if task_id not in self.tasks:
            return False
        task = self.tasks[task_id]
        if task.assigned_agent != agent_id:
            return False
        task.state = TaskState.COMPLETED.value
        task.result = result
        task.completed_at = datetime.utcnow().isoformat()
        self._remove_from_agent(task_id, agent_id)
        for node in self.agents.values():
            if node.agent_id == agent_id:
                node.total_tasks_completed += 1
                self._persist("agent", node.to_dict())
                break
        self._persist("task", task.to_dict())
        logger.info(f"✅ Task {task_id} completed by {agent_id}")
        return True

    def fail_task(self, task_id: str, agent_id: str, error: str) -> bool:
        if task_id not in self.tasks:
            return False
        task = self.tasks[task_id]
        if task.assigned_agent != agent_id:
            return False
        if task.retry_count < task.max_retries:
            task.state = TaskState.RETRYING.value
            task.retry_count += 1
            task.error = error
            self._remove_from_agent(task_id, agent_id)
            self.task_queue.append(task_id)
            self._sort_queue()
            logger.info(f"🔄 Task {task_id} retrying ({task.retry_count}/{task.max_retries})")
        else:
            task.state = TaskState.FAILED.value
            task.error = error
            task.completed_at = datetime.utcnow().isoformat()
            self._remove_from_agent(task_id, agent_id)
            logger.info(f"❌ Task {task_id} failed after {task.retry_count} retries: {error}")
        self._persist("task", task.to_dict())
        return True

    def cancel_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        task = self.tasks[task_id]
        old_state = task.state
        task.state = TaskState.CANCELLED.value
        if task.assigned_agent:
            self._remove_from_agent(task_id, task.assigned_agent)
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)
        self._persist("task", task.to_dict())
        logger.info(f"🗑️ Task {task_id} cancelled (was {old_state})")
        return True

    def _remove_from_agent(self, task_id: str, agent_id: str) -> None:
        for node in self.agents.values():
            if node.agent_id == agent_id and task_id in node.current_tasks:
                node.current_tasks.remove(task_id)
                self._persist("agent", node.to_dict())
                break

    def heartbeat(self, agent_id: str) -> bool:
        for node in self.agents.values():
            if node.agent_id == agent_id:
                node.last_heartbeat = datetime.utcnow().isoformat()
                node.is_online = True
                self._persist("agent", node.to_dict())
                return True
        return False

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        t = self.tasks.get(task_id)
        return t.to_dict() if t else None

    def get_agent_tasks(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        result = [t.to_dict() for t in self.tasks.values()
                  if t.assigned_agent == agent_id]
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result[:limit]

    def list_tasks(self, state: Optional[str] = None, task_type: Optional[str] = None,
                   limit: int = 50) -> List[Dict[str, Any]]:
        result = list(self.tasks.values())
        if state:
            result = [t for t in result if t.state == state]
        if task_type:
            result = [t for t in result if t.task_type == task_type]
        result.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in result[:limit]]

    def list_agents(self, online_only: bool = False) -> List[Dict[str, Any]]:
        agents = list(self.agents.values())
        if online_only:
            agents = [a for a in agents if a.is_online]
        return [a.to_dict() for a in agents]

    def get_bus_status(self) -> Dict[str, Any]:
        state_counts = {}
        for task in self.tasks.values():
            state_counts[task.state] = state_counts.get(task.state, 0) + 1
        active_tasks = sum(1 for t in self.tasks.values()
                           if t.state in (TaskState.ASSIGNED.value, TaskState.RUNNING.value))
        total_capacity = sum(a.max_concurrent_tasks for a in self.agents.values())
        current_load = sum(len(a.current_tasks) for a in self.agents.values())
        return {
            "total_tasks": len(self.tasks),
            "queued_tasks": len(self.task_queue),
            "active_tasks": active_tasks,
            "completed_tasks": state_counts.get(TaskState.COMPLETED.value, 0),
            "failed_tasks": state_counts.get(TaskState.FAILED.value, 0),
            "state_distribution": state_counts,
            "registered_agents": len(self.agents),
            "online_agents": sum(1 for a in self.agents.values() if a.is_online),
            "total_capacity": total_capacity,
            "current_load": current_load,
            "utilization_pct": round((current_load / max(total_capacity, 1)) * 100, 1),
        }


_task_bus: Optional[DecentralizedTaskBus] = None


def get_task_bus() -> DecentralizedTaskBus:
    global _task_bus
    if _task_bus is None:
        _task_bus = DecentralizedTaskBus()
    return _task_bus


def reset_task_bus() -> None:
    global _task_bus
    _task_bus = None
