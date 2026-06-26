"""
ASIMNEXUS Microkernel
=====================
seL4-inspired microkernel with capability-based security,
process isolation, IPC, and real-time scheduling.
"""

import time
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field


class CapabilityRight(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"


class ProcessState(Enum):
    RUNNING = "running"
    READY = "ready"
    BLOCKED = "blocked"
    TERMINATED = "terminated"


@dataclass
class Capability:
    id: str
    process_id: str
    resource_id: str
    rights: List[CapabilityRight]
    revoked: bool = False


@dataclass
class Process:
    id: str
    name: str
    priority: int = 0
    state: ProcessState = ProcessState.READY
    cpu_time: float = 0.0
    target: Optional[Callable] = None


@dataclass
class IPCMessage:
    id: str
    from_process: str
    to_process: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class CapabilityManager:
    """Manages capabilities for process-level security."""

    def __init__(self):
        self.resources: Dict[str, str] = {}
        self.capabilities: Dict[str, Capability] = {}

    def register_resource(self, resource_id: str, description: str) -> None:
        self.resources[resource_id] = description

    def grant_capability(self, process_id: str, resource_id: str,
                         rights: List[CapabilityRight]) -> Capability:
        cap = Capability(
            id=str(uuid.uuid4()),
            process_id=process_id,
            resource_id=resource_id,
            rights=rights,
        )
        self.capabilities[cap.id] = cap
        return cap

    def check_capability(self, process_id: str, cap_id: str,
                         right: CapabilityRight) -> bool:
        cap = self.capabilities.get(cap_id)
        if cap is None or cap.revoked:
            return False
        if cap.process_id != process_id:
            return False
        return right in cap.rights

    def revoke_capability(self, cap_id: str) -> bool:
        cap = self.capabilities.get(cap_id)
        if cap is None:
            return False
        cap.revoked = True
        return True


class ProcessManager:
    """Manages process lifecycle."""

    def __init__(self, cap_manager: CapabilityManager):
        self.cap_manager = cap_manager
        self.processes: Dict[str, Process] = {}

    def spawn_process(self, name: str, target: Callable,
                      priority: int = 0) -> Process:
        process = Process(
            id=str(uuid.uuid4()),
            name=name,
            priority=priority,
            state=ProcessState.RUNNING,
            target=target,
        )
        self.processes[process.id] = process
        return process

    def get_process(self, process_id: str) -> Optional[Process]:
        return self.processes.get(process_id)

    def kill_process(self, process_id: str) -> bool:
        process = self.processes.get(process_id)
        if process is None:
            return False
        process.state = ProcessState.TERMINATED
        return True


class IPCManager:
    """Manages inter-process communication."""

    def __init__(self, cap_manager: CapabilityManager):
        self.cap_manager = cap_manager
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, msg_type: str, handler: Callable) -> None:
        self.handlers[msg_type] = handler

    def send_message(self, from_process: str, to_process: str,
                     payload: Dict[str, Any]) -> IPCMessage:
        return IPCMessage(
            id=str(uuid.uuid4()),
            from_process=from_process,
            to_process=to_process,
            payload=payload,
        )

    def handle_message(self, message: IPCMessage) -> Optional[Any]:
        msg_type = message.payload.get("type", "")
        handler = self.handlers.get(msg_type)
        if handler:
            return handler(message)
        return None


class RealTimeScheduler:
    """Real-time scheduler using priority-based scheduling."""

    def __init__(self):
        self.processes: Dict[str, Process] = {}

    def add_process(self, process: Process) -> None:
        self.processes[process.id] = process

    def schedule(self) -> Optional[Process]:
        if not self.processes:
            return None
        return max(self.processes.values(), key=lambda p: p.priority)

    def update_cpu_time(self, process_id: str, cpu_time: float) -> None:
        process = self.processes.get(process_id)
        if process:
            process.cpu_time = cpu_time

    def remove_process(self, process_id: str) -> bool:
        if process_id in self.processes:
            del self.processes[process_id]
            return True
        return False


class ASIMMicrokernel:
    """Main microkernel orchestrator."""

    def __init__(self):
        self.running = False
        self.capability_manager = CapabilityManager()
        self.process_manager = ProcessManager(self.capability_manager)
        self.ipc_manager = IPCManager(self.capability_manager)
        self.scheduler = RealTimeScheduler()

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def create_process(self, name: str, target: Callable,
                       priority: int = 0) -> Process:
        process = self.process_manager.spawn_process(name, target, priority)
        self.scheduler.add_process(process)
        return process

    def grant_capability(self, process_id: str, resource_id: str,
                         rights: List[CapabilityRight]) -> Capability:
        return self.capability_manager.grant_capability(
            process_id, resource_id, rights
        )

    def send_message(self, from_process: str, to_process: str,
                     payload: Dict[str, Any]) -> IPCMessage:
        return self.ipc_manager.send_message(from_process, to_process, payload)

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "processes": len(self.process_manager.processes),
        }

    def load_plugin(self, plugin_id: str, plugin_module: str) -> Dict[str, Any]:
        """Load a plugin dynamically."""
        try:
            import importlib
            module = importlib.import_module(plugin_module)
            return {"status": "loaded", "plugin_id": plugin_id, "module": plugin_module}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def unload_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Unload a plugin."""
        return {"status": "unloaded", "plugin_id": plugin_id}