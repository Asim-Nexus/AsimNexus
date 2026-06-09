#!/usr/bin/env python3
"""Task Distributor — Distributed task allocation and execution across the swarm.

Enables distributing computational tasks across AsimNexus instances in the
swarm. Supports multiple scheduling strategies, task queuing, result
collection, and failure handling.

Typical usage::

    distributor = TaskDistributor()
    task_id = distributor.dispatch_task(
        task_type="inference",
        payload={"prompt": "..."},
        strategy=SchedulingStrategy.ROUND_ROBIN,
    )
    result = distributor.collect_result(task_id, timeout=30)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Priority levels for task scheduling."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskStatus(Enum):
    """Status of a distributed task."""
    PENDING = auto()
    QUEUED = auto()
    ASSIGNED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    TIMEOUT = auto()
    CANCELLED = auto()


class SchedulingStrategy(Enum):
    """Strategies for assigning tasks to nodes."""
    ROUND_ROBIN = auto()       # Cycle through available nodes
    LEAST_LOADED = auto()      # Node with fewest active tasks
    RANDOM = auto()            # Random selection
    AFFINITY = auto()          # Node with matching capabilities
    REPUTATION = auto()        # Highest-reputation node


@dataclass
class Task:
    """A distributed task in the swarm."""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_node: Optional[str] = None
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timeout_seconds: int = 60
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    @property
    def duration_ms(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds() * 1000
        return None


@dataclass
class SwarmNode:
    """A registered node in the swarm."""
    node_id: str
    address: str
    capabilities: Set[str] = field(default_factory=set)
    active_tasks: int = 0
    max_concurrent_tasks: int = 5
    reputation_score: float = 0.5
    last_heartbeat: Optional[str] = None
    is_online: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskDistributor:
    """Distributes and tracks computational tasks across swarm nodes.

    Features:
    - Multiple scheduling strategies (round-robin, least-loaded, affinity)
    - Task queue with priority sorting
    - Heartbeat-based node health tracking
    - Result collection with timeout
    - Failure detection and re-dispatch
    """

    def __init__(self, node_id: Optional[str] = None):
        self.node_id = node_id or f"distributor-{uuid.uuid4().hex[:8]}"
        self._tasks: Dict[str, Task] = {}
        self._nodes: Dict[str, SwarmNode] = {}
        self._round_robin_index: int = 0
        self._handlers: Dict[str, Callable] = {}

    # ── Node Management ─────────────────────────────────────────────────────

    def register_node(self, node_id: str, address: str,
                      capabilities: Optional[List[str]] = None,
                      max_concurrent: int = 5) -> SwarmNode:
        """Register a node in the swarm."""
        node = SwarmNode(
            node_id=node_id,
            address=address,
            capabilities=set(capabilities or []),
            max_concurrent_tasks=max_concurrent,
            last_heartbeat=datetime.utcnow().isoformat(),
        )
        self._nodes[node_id] = node
        logger.info("Registered swarm node %s at %s (%d capabilities)",
                     node_id, address, len(node.capabilities))
        return node

    def unregister_node(self, node_id: str) -> bool:
        """Remove a node from the swarm."""
        if node_id in self._nodes:
            del self._nodes[node_id]
            logger.info("Unregistered swarm node %s", node_id)
            return True
        return False

    def get_node(self, node_id: str) -> Optional[SwarmNode]:
        """Get a registered node by ID."""
        return self._nodes.get(node_id)

    def get_online_nodes(self) -> List[SwarmNode]:
        """Get all currently online nodes."""
        return [n for n in self._nodes.values() if n.is_online]

    def heartbeat(self, node_id: str) -> bool:
        """Record a heartbeat from a node."""
        node = self._nodes.get(node_id)
        if not node:
            return False
        node.last_heartbeat = datetime.utcnow().isoformat()
        node.is_online = True
        return True

    def check_node_health(self, max_age_seconds: int = 30) -> List[str]:
        """Mark nodes as offline if heartbeat is too old."""
        now = datetime.utcnow()
        stale = []
        for node in self._nodes.values():
            if node.last_heartbeat:
                last = datetime.fromisoformat(node.last_heartbeat)
                if (now - last).total_seconds() > max_age_seconds:
                    node.is_online = False
                    stale.append(node.node_id)
        return stale

    # ── Task Management ─────────────────────────────────────────────────────

    def dispatch_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        strategy: SchedulingStrategy = SchedulingStrategy.ROUND_ROBIN,
        timeout_seconds: int = 60,
        affinity: Optional[str] = None,
    ) -> Optional[str]:
        """Dispatch a task to the swarm.

        Args:
            task_type: Type/category of the task.
            payload: Task data/parameters.
            priority: Scheduling priority.
            strategy: Node selection strategy.
            timeout_seconds: Max execution time.
            affinity: Required capability for affinity scheduling.

        Returns:
            task_id if dispatched, None if no suitable node.
        """
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        task = Task(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority,
            status=TaskStatus.QUEUED,
            timeout_seconds=timeout_seconds,
        )

        # Select target node
        node = self._select_node(strategy, task_type, affinity)
        if not node:
            logger.warning("No available node for task %s (type=%s)", task_id, task_type)
            task.status = TaskStatus.FAILED
            task.error = "No available node"
            self._tasks[task_id] = task
            return None

        task.assigned_node = node.node_id
        task.status = TaskStatus.ASSIGNED
        node.active_tasks += 1
        self._tasks[task_id] = task

        logger.info("Dispatched task %s (type=%s, priority=%s) to node %s",
                     task_id, task_type, priority.name, node.node_id)
        return task_id

    def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Mark a task as completed with a result."""
        task = self._tasks.get(task_id)
        if not task or task.status not in (TaskStatus.ASSIGNED, TaskStatus.RUNNING):
            return False

        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.utcnow().isoformat()

        # Decrement active count on assigned node
        if task.assigned_node:
            node = self._nodes.get(task.assigned_node)
            if node:
                node.active_tasks = max(0, node.active_tasks - 1)

        logger.info("Task %s completed by node %s", task_id, task.assigned_node)
        return True

    def fail_task(self, task_id: str, error: str) -> bool:
        """Mark a task as failed."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.FAILED
        task.error = error
        task.completed_at = datetime.utcnow().isoformat()

        if task.assigned_node:
            node = self._nodes.get(task.assigned_node)
            if node:
                node.active_tasks = max(0, node.active_tasks - 1)

        logger.warning("Task %s failed: %s", task_id, error)
        return True

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or assigned task."""
        task = self._tasks.get(task_id)
        if not task or task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return False

        task.status = TaskStatus.CANCELLED
        if task.assigned_node:
            node = self._nodes.get(task.assigned_node)
            if node:
                node.active_tasks = max(0, node.active_tasks - 1)

        logger.info("Task %s cancelled", task_id)
        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_pending_tasks(self) -> List[Task]:
        """Get all queued or assigned tasks."""
        return [t for t in self._tasks.values()
                if t.status in (TaskStatus.QUEUED, TaskStatus.ASSIGNED)]

    def get_tasks_by_node(self, node_id: str) -> List[Task]:
        """Get all tasks assigned to a specific node."""
        return [t for t in self._tasks.values() if t.assigned_node == node_id]

    def get_tasks_by_type(self, task_type: str) -> List[Task]:
        """Get all tasks of a specific type."""
        return [t for t in self._tasks.values() if t.task_type == task_type]

    def check_timeouts(self) -> List[str]:
        """Find and mark timed-out tasks. Returns list of timed-out task IDs."""
        timed_out: List[str] = []
        now = datetime.utcnow()

        for task in list(self._tasks.values()):
            if task.status not in (TaskStatus.ASSIGNED, TaskStatus.RUNNING):
                continue
            if task.started_at:
                started = datetime.fromisoformat(task.started_at)
                if (now - started).total_seconds() > task.timeout_seconds:
                    task.status = TaskStatus.TIMEOUT
                    task.error = f"Timed out after {task.timeout_seconds}s"
                    timed_out.append(task.task_id)
                    if task.assigned_node:
                        node = self._nodes.get(task.assigned_node)
                        if node:
                            node.active_tasks = max(0, node.active_tasks - 1)

        return timed_out

    def get_stats(self) -> Dict:
        """Get distributor statistics."""
        return {
            "node_id": self.node_id,
            "registered_nodes": len(self._nodes),
            "online_nodes": len(self.get_online_nodes()),
            "total_tasks_dispatched": len(self._tasks),
            "tasks_by_status": {
                s.name: len([t for t in self._tasks.values() if t.status == s])
                for s in TaskStatus
            },
            "pending_tasks": len(self.get_pending_tasks()),
            "total_active_tasks": sum(n.active_tasks for n in self._nodes.values()),
        }

    def register_handler(self, task_type: str, handler: Callable):
        """Register a local handler for a task type."""
        self._handlers[task_type] = handler
        logger.info("Registered handler for task type: %s", task_type)

    # ── Internal Methods ────────────────────────────────────────────────────

    def _select_node(self, strategy: SchedulingStrategy, task_type: str,
                     affinity: Optional[str] = None) -> Optional[SwarmNode]:
        """Select a node based on the scheduling strategy."""
        online = self.get_online_nodes()
        if not online:
            return None

        if strategy == SchedulingStrategy.ROUND_ROBIN:
            return self._select_round_robin(online)

        elif strategy == SchedulingStrategy.LEAST_LOADED:
            return self._select_least_loaded(online)

        elif strategy == SchedulingStrategy.RANDOM:
            import random
            return random.choice(online)

        elif strategy == SchedulingStrategy.AFFINITY:
            if affinity:
                matching = [n for n in online if affinity in n.capabilities]
                return self._select_least_loaded(matching) if matching else None
            return self._select_least_loaded(online)

        elif strategy == SchedulingStrategy.REPUTATION:
            return max(online, key=lambda n: n.reputation_score)

        return self._select_least_loaded(online)

    def _select_round_robin(self, nodes: List[SwarmNode]) -> SwarmNode:
        """Select node using round-robin."""
        node = nodes[self._round_robin_index % len(nodes)]
        self._round_robin_index = (self._round_robin_index + 1) % len(nodes)
        return node

    def _select_least_loaded(self, nodes: List[SwarmNode]) -> Optional[SwarmNode]:
        """Select node with fewest active tasks."""
        if not nodes:
            return None
        return min(nodes, key=lambda n: n.active_tasks / max(n.max_concurrent_tasks, 1))


def get_task_distributor(node_id: Optional[str] = None) -> TaskDistributor:
    """Factory function to get a TaskDistributor instance."""
    return TaskDistributor(node_id=node_id)
