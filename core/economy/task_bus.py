
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Decentralized Task Bus
================================
Decentralized task bus for Agent Mode
Includes: Task queuing, distributed execution, result aggregation, fault tolerance
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

logger = logging.getLogger("TaskBus")


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskState(Enum):
    """Task execution states"""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class BusTask:
    """Task on the bus"""
    task_id: str
    payload: Dict[str, Any]
    priority: TaskPriority
    state: TaskState
    assigned_agent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class AgentNode:
    """Agent node in the decentralized network"""
    node_id: str
    agent_id: str
    capabilities: List[str]
    current_tasks: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    is_online: bool = True


class DecentralizedTaskBus:
    """Decentralized task bus for agent mode"""
    
    def __init__(self):
        self.tasks: Dict[str, BusTask] = {}
        self.agents: Dict[str, AgentNode] = {}
        self.task_queue: List[str] = []
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize task bus"""
        logger.info("🚌 Initializing Decentralized Task Bus...")
        logger.info("📦 Setting up task queuing")
        logger.info("🤖 Registering agent nodes")
        logger.info("🔄 Setting up distributed execution")
        logger.info("✅ Decentralized Task Bus initialized")
    
    def register_agent(
        self,
        agent_id: str,
        capabilities: List[str],
        max_concurrent: int = 5
    ) -> AgentNode:
        """Register an agent node"""
        node = AgentNode(
            node_id=f"node_{uuid.uuid4().hex[:8]}",
            agent_id=agent_id,
            capabilities=capabilities,
            max_concurrent_tasks=max_concurrent
        )
        self.agents[node.node_id] = node
        logger.info(f"✅ Registered agent: {agent_id}")
        return node
    
    def submit_task(
        self,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> BusTask:
        """Submit task to bus"""
        task = BusTask(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            payload=payload,
            priority=priority,
            state=TaskState.QUEUED
        )
        self.tasks[task.task_id] = task
        self.task_queue.append(task.task_id)
        
        # Sort queue by priority
        priority_order = {TaskPriority.CRITICAL: 0, TaskPriority.HIGH: 1, TaskPriority.MEDIUM: 2, TaskPriority.LOW: 3}
        self.task_queue.sort(key=lambda tid: priority_order[self.tasks[tid].priority])
        
        logger.info(f"✅ Submitted task: {task.task_id}")
        return task
    
    def assign_task(self, task_id: str, node_id: str) -> bool:
        """Assign task to agent node"""
        if task_id not in self.tasks or node_id not in self.agents:
            return False
        
        task = self.tasks[task_id]
        node = self.agents[node_id]
        
        if len(node.current_tasks) >= node.max_concurrent_tasks:
            return False
        
        task.state = TaskState.ASSIGNED
        task.assigned_agent = node.agent_id
        task.started_at = datetime.utcnow()
        
        node.current_tasks.append(task_id)
        self.task_queue.remove(task_id)
        
        logger.info(f"✅ Assigned task {task_id} to {node.agent_id}")
        return True
    
    def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Complete task with result"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.state = TaskState.COMPLETED
        task.result = result
        task.completed_at = datetime.utcnow()
        
        # Remove from agent's current tasks
        if task.assigned_agent:
            for node in self.agents.values():
                if node.agent_id == task.assigned_agent and task_id in node.current_tasks:
                    node.current_tasks.remove(task_id)
        
        logger.info(f"✅ Completed task {task_id}")
        return True
    
    def fail_task(self, task_id: str, error: str) -> bool:
        """Mark task as failed or retry"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if task.retry_count < task.max_retries:
            task.state = TaskState.RETRYING
            task.retry_count += 1
            task.error = error
            self.task_queue.append(task_id)
            logger.info(f"🔄 Retrying task {task_id} (attempt {task.retry_count})")
        else:
            task.state = TaskState.FAILED
            task.error = error
            
            # Remove from agent's current tasks
            if task.assigned_agent:
                for node in self.agents.values():
                    if node.agent_id == task.assigned_agent and task_id in node.current_tasks:
                        node.current_tasks.remove(task_id)
            
            logger.error(f"❌ Task {task_id} failed: {error}")
        
        return True
    
    def get_next_task(self, node_id: str) -> Optional[BusTask]:
        """Get next task for agent node"""
        if node_id not in self.agents:
            return None
        
        node = self.agents[node_id]
        if len(node.current_tasks) >= node.max_concurrent_tasks:
            return None
        
        # Find matching task
        for task_id in self.task_queue:
            task = self.tasks[task_id]
            if task.state == TaskState.QUEUED:
                # Check if agent has required capabilities
                required_caps = task.payload.get("required_capabilities", [])
                if all(cap in node.capabilities for cap in required_caps):
                    return task
        
        return None
    
    def get_bus_status(self) -> Dict[str, Any]:
        """Get bus status"""
        state_counts = {}
        for task in self.tasks.values():
            state_counts[task.state.value] = state_counts.get(task.state.value, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "queued_tasks": len(self.task_queue),
            "state_distribution": state_counts,
            "registered_agents": len(self.agents),
            "online_agents": sum(1 for a in self.agents.values() if a.is_online)
        }


# Global instance
_task_bus: Optional[DecentralizedTaskBus] = None


def get_task_bus() -> DecentralizedTaskBus:
    """Get singleton instance"""
    global _task_bus
    if _task_bus is None:
        _task_bus = DecentralizedTaskBus()
    return _task_bus
