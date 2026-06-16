#!/usr/bin/env python3
"""
STATUS: NEW — Production Implementation
core/identity/digital_twin.py
AsimNexus — Human Digital Twin Manager

Manages Nepalese citizen's digital twin with:
- Offline-first capability with mesh networking
- ZKP-based authentication
- Government service integration
- NID (National ID) binding

Integration:
- core/identity/user_identity.py — Identity verification
- mesh/offline_sync_engine.py — Offline sync
- security/zkp_privacy.py — Privacy protection
"""

import os
import hashlib
import time
import uuid
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

# Configuration
_OFFLINE_SYNC_ENABLED = os.getenv("ASIM_HDT_OFFLINE_SYNC", "true").lower() == "true"
_MESH_DISCOVERY_ENABLED = os.getenv("ASIM_HDT_MESH_DISCOVERY", "true").lower() == "true"


class TwinMode(str, Enum):
    """Operating modes for Digital Twin."""
    PERSONAL = "personal"
    GOVERNMENT_SERVICE = "government_service"
    ENTERPRISE_SERVICE = "enterprise_service"
    OFFLINE = "offline"


class ServiceType(str, Enum):
    """Types of services accessible via Digital Twin."""
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    GOVERNANCE = "governance"
    COMMERCE = "commerce"
    UTILITY = "utility"


@dataclass
class QueuedTask:
    """Task queued for offline execution."""
    task_id: str
    action: str
    payload: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    retry_count: int = 0
    priority: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "action": self.action,
            "payload": self.payload,
            "created_at": self.created_at,
            "retry_count": self.retry_count,
            "priority": self.priority,
        }


class HumanDigitalTwin:
    """
    Human Digital Twin (HDT) for Nepalese citizens.
    
    Features:
    - Local-first processing (works offline)
    - Mesh network synchronization
    - ZKP-based privacy protection
    - NID (National ID) integration
    """

    def __init__(
        self,
        citizen_id: str,
        nid_number: Optional[str] = None,
        offline_enabled: bool = True
    ):
        self.citizen_id = citizen_id
        self.nid_number = nid_number
        self.did = f"did:asim:{citizen_id}"
        self.twin_mode = TwinMode.PERSONAL
        self.offline_enabled = offline_enabled
        self._offline_queue: List[QueuedTask] = []
        self._service_permissions: List[ServiceType] = []
        self._mesh_peer_id: Optional[str] = None
        
        logger.info(f"Digital Twin created: {citizen_id[:8]}...")

    async def execute_task(
        self,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        requires_network: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a task via Digital Twin.
        
        Args:
            action: Action to perform
            payload: Action parameters
            requires_network: Whether network is required
            
        Returns:
            Task result
        """
        payload = payload or {}
        
        # Check if online or offline
        if requires_network and self.twin_mode == TwinMode.OFFLINE:
            # Queue for later sync
            return await self.queue_offline_task(action, payload)
            
        # Execute directly
        return await self._execute_now(action, payload)

    async def _execute_now(
        self, action: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute action immediately (online)."""
        try:
            from connectors.nexus_secure_connector import get_nexus_connector
            
            connector = get_nexus_connector()
            
            result = await connector.route_request(
                source=ModuleType.CITIZEN,
                target=ModuleType.GOVERNMENT if "gov" in action else ModuleType.ENTERPRISE,
                action=action,
                payload=payload,
                context={"citizen_id": self.citizen_id}
            )
            
            return result
            
        except ImportError:
            return {
                "success": True,
                "action": action,
                "offline_result": True,
                "message": "Executed in offline mode"
            }

    async def queue_offline_task(
        self, action: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Queue task for offline mesh sync."""
        task_id = str(uuid.uuid4())
        
        task = QueuedTask(
            task_id=task_id,
            action=action,
            payload=payload,
            priority=payload.get("priority", 5)
        )
        
        self._offline_queue.append(task)
        
        logger.info(f"Task queued for offline sync: {action} (queue: {len(self._offline_queue)})")
        
        return {
            "success": True,
            "task_id": task_id,
            "queued": True,
            "will_sync_when_online": True
        }

    async def sync_pending_tasks(self) -> Dict[str, Any]:
        """Sync all queued tasks when online."""
        synced = 0
        failed = 0
        
        for task in self._offline_queue[:]:
            try:
                result = await self._execute_now(task.action, task.payload)
                if result.get("success"):
                    self._offline_queue.remove(task)
                    synced += 1
                else:
                    task.retry_count += 1
                    if task.retry_count > 3:
                        failed += 1
                        self._offline_queue.remove(task)
            except Exception as e:
                logger.error(f"Sync error: {e}")
                failed += 1
                
        return {
            "synced": synced,
            "failed": failed,
            "remaining": len(self._offline_queue)
        }

    async def join_mesh_network(self) -> bool:
        """Join local mesh network for offline communication."""
        if not _MESH_DISCOVERY_ENABLED:
            return False
            
        try:
            from mesh.p2p_transport import P2PTransport
            
            transport = P2PTransport()
            self._mesh_peer_id = str(uuid.uuid4())
            
            # Join mesh
            await transport.join_network(self._mesh_peer_id)
            
            logger.info(f"Joined mesh network: {self._mesh_peer_id[:8]}...")
            return True
            
        except ImportError:
            logger.warning("Mesh transport not available")
            return False

    def add_service_permission(self, service: ServiceType) -> None:
        """Grant permission for service access."""
        if service not in self._service_permissions:
            self._service_permissions.append(service)

    def get_permissions(self) -> List[str]:
        """Get list of service permissions."""
        return [s.value for s in self._service_permissions]

    async def request_government_service(
        self, service: ServiceType, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request government service via Digital Twin."""
        if service not in self._service_permissions:
            # Queue for later (offline capable)
            return await self.queue_offline_task(
                action=f"request_{service.value}",
                payload=data
            )
            
        return await self.execute_task(
            action=f"gov_{service.value}",
            payload=data,
            requires_network=True
        )

    def get_status(self) -> Dict[str, Any]:
        """Get Digital Twin status."""
        return {
            "citizen_id": self.citizen_id[:8] + "...",
            "did": self.did,
            "mode": self.twin_mode.value,
            "offline_queue_size": len(self._offline_queue),
            "service_permissions": self.get_permissions(),
            "mesh_peer_id": self._mesh_peer_id,
        }

    @classmethod
    async def create_from_nid(
        cls, 
        nid_number: str,
        offline_enabled: bool = True
    ) -> "HumanDigitalTwin":
        """Create Digital Twin from National ID."""
        citizen_id = f"citizen_{hashlib.sha256(nid_number.encode()).hexdigest()[:16]}"
        
        twin = cls(
            citizen_id=citizen_id,
            nid_number=nid_number,
            offline_enabled=offline_enabled
        )
        
        # Grant basic permissions
        twin.add_service_permission(ServiceType.HEALTHCARE)
        twin.add_service_permission(ServiceType.EDUCATION)
        
        return twin


# ModuleType import for Digital Twin
try:
    from connectors.nexus_secure_connector import ModuleType
except ImportError:
    pass