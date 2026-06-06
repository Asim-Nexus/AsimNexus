#!/usr/bin/env python3
"""
core/universe/container.py
AsimNexus — Universe Container Manager

Provides a container abstraction over personal universes, managing
multi-universe orchestration, data flow between layers, and
container-level operations.

Provides:
  - UniverseContainer dataclass
  - UniverseContainerManager: main class
  - UniverseLayer enum (re-exported from personal_universe)
  - Singleton factory: get_universe_manager() / reset_universe_manager()
"""

import json
import logging
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# Re-export UniverseLayer from personal_universe for backward compatibility
from core.universe.personal_universe import UniverseLayer, PersonalUniverseManager


@dataclass
class UniverseContainer:
    """A container wrapping a personal universe with additional metadata"""
    container_id: str
    user_id: str
    display_name: str
    universe_type: str = "personal"  # personal | family | community | enterprise | sovereign
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    layer_status: Dict[int, str] = field(default_factory=dict)
    data_flow_rules: Dict[str, List[str]] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "container_id": self.container_id,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "universe_type": self.universe_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "layer_status": self.layer_status,
            "data_flow_rules": self.data_flow_rules,
            "tags": self.tags,
        }


class UniverseContainerManager:
    """
    Universe Container Manager.
    
    Manages multiple universe containers and provides:
    - Container lifecycle (create, activate, deactivate)
    - Data flow checking between layers
    - Container-level statistics
    - DID-based container lookup
    """

    def __init__(self):
        self.containers: Dict[str, UniverseContainer] = {}
        self._user_containers: Dict[str, List[str]] = {}  # user_id → [container_ids]
        self._did_container_index: Dict[str, str] = {}  # did → container_id

    def create_container(self, user_id: str, display_name: str,
                          universe_type: str = "personal",
                          did: Optional[str] = None,
                          tags: Optional[Dict] = None) -> UniverseContainer:
        """Create a new universe container"""
        import uuid
        container_id = f"uc_{uuid.uuid4().hex[:16]}"

        container = UniverseContainer(
            container_id=container_id,
            user_id=user_id,
            display_name=display_name,
            universe_type=universe_type,
            layer_status={
                1: "active" if universe_type == "personal" else "pending",
                2: "pending",
                3: "pending",
                4: "pending",
                5: "pending",
            },
            data_flow_rules=self._default_data_flow_rules(),
            tags=tags or {},
        )

        self.containers[container_id] = container

        if user_id not in self._user_containers:
            self._user_containers[user_id] = []
        self._user_containers[user_id].append(container_id)

        if did:
            self._did_container_index[did] = container_id

        logger.info(f"📦 Container created: {container_id} for {user_id}")
        return container

    def get_container(self, container_id: str) -> Optional[UniverseContainer]:
        """Get container by ID"""
        return self.containers.get(container_id)

    def get_for_did(self, did: str) -> List[UniverseContainer]:
        """Get containers associated with a DID"""
        container_id = self._did_container_index.get(did)
        if container_id and container_id in self.containers:
            return [self.containers[container_id]]
        return []

    def get_user_containers(self, user_id: str) -> List[UniverseContainer]:
        """Get all containers for a user"""
        container_ids = self._user_containers.get(user_id, [])
        return [self.containers[cid] for cid in container_ids if cid in self.containers]

    def activate_container(self, container_id: str) -> bool:
        """Activate a container"""
        container = self.containers.get(container_id)
        if not container:
            return False
        container.is_active = True
        container.updated_at = datetime.now()
        logger.info(f"✅ Container activated: {container_id}")
        return True

    def deactivate_container(self, container_id: str) -> bool:
        """Deactivate a container"""
        container = self.containers.get(container_id)
        if not container:
            return False
        container.is_active = False
        container.updated_at = datetime.now()
        logger.info(f"⏸️ Container deactivated: {container_id}")
        return True

    def activate_layer(self, container_id: str, layer: UniverseLayer) -> bool:
        """Activate a layer within a container"""
        container = self.containers.get(container_id)
        if not container:
            return False
        container.layer_status[layer.value] = "active"
        container.updated_at = datetime.now()
        logger.info(f"✨ Layer {layer.name} activated in {container_id}")
        return True

    def check_data_flow(self, from_layer: UniverseLayer,
                         to_layer: UniverseLayer) -> Dict[str, Any]:
        """
        Check if data flow is allowed between two layers.
        
        Data flow rules:
        - Personal → Family: Allowed (user controls personal data sharing)
        - Family → Community: Allowed with consent
        - Community → Enterprise: Requires anonymization
        - Enterprise → Sovereign: Requires legal compliance
        - Sovereign → Personal: Always allowed (read-only)
        """
        rules = {
            (UniverseLayer.PERSONAL, UniverseLayer.FAMILY): {
                "allowed": True,
                "requires_consent": True,
                "anonymization": False,
                "description": "Personal → Family: Allowed with user consent",
            },
            (UniverseLayer.FAMILY, UniverseLayer.COMMUNITY): {
                "allowed": True,
                "requires_consent": True,
                "anonymization": False,
                "description": "Family → Community: Allowed with family consent",
            },
            (UniverseLayer.COMMUNITY, UniverseLayer.ENTERPRISE): {
                "allowed": True,
                "requires_consent": True,
                "anonymization": True,
                "description": "Community → Enterprise: Requires anonymization",
            },
            (UniverseLayer.ENTERPRISE, UniverseLayer.SOVEREIGN): {
                "allowed": True,
                "requires_consent": True,
                "anonymization": True,
                "description": "Enterprise → Sovereign: Requires legal compliance",
            },
            (UniverseLayer.SOVEREIGN, UniverseLayer.PERSONAL): {
                "allowed": True,
                "requires_consent": False,
                "anonymization": False,
                "description": "Sovereign → Personal: Always allowed (read-only)",
            },
        }

        result = rules.get((from_layer, to_layer))
        if result:
            return {
                "allowed": result["allowed"],
                "from": from_layer.name,
                "to": to_layer.name,
                "requires_consent": result["requires_consent"],
                "anonymization_required": result["anonymization"],
                "description": result["description"],
            }

        # Default: deny
        return {
            "allowed": False,
            "from": from_layer.name,
            "to": to_layer.name,
            "requires_consent": True,
            "anonymization_required": True,
            "description": f"{from_layer.name} → {to_layer.name}: Not allowed by default",
        }

    def status_all(self) -> List[Dict[str, Any]]:
        """Get status of all containers"""
        return [
            container.to_dict()
            for container in self.containers.values()
        ]

    def stats(self) -> Dict[str, Any]:
        """Get container statistics"""
        total = len(self.containers)
        by_type = {}
        active = 0

        for container in self.containers.values():
            t = container.universe_type
            by_type[t] = by_type.get(t, 0) + 1
            if container.is_active:
                active += 1

        return {
            "total_containers": total,
            "active_containers": active,
            "by_type": by_type,
            "total_users": len(self._user_containers),
        }

    def _default_data_flow_rules(self) -> Dict[str, List[str]]:
        """Get default data flow rules between layers"""
        return {
            "layer_1_to_2": ["consent_required"],
            "layer_2_to_3": ["consent_required", "anonymization"],
            "layer_3_to_4": ["consent_required", "anonymization"],
            "layer_4_to_5": ["legal_compliance", "audit_required"],
            "layer_5_to_1": ["read_only"],
        }


# Singleton
_container_manager: Optional[UniverseContainerManager] = None


def get_universe_manager() -> UniverseContainerManager:
    """Get universe container manager singleton"""
    global _container_manager
    if _container_manager is None:
        _container_manager = UniverseContainerManager()
    return _container_manager


def reset_universe_manager() -> None:
    """Reset universe container manager singleton (for testing)"""
    global _container_manager
    _container_manager = None


if __name__ == "__main__":
    import sys

    manager = get_universe_manager()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Create container
        container = manager.create_container("user_001", "Ram's Universe")
        print(f"✅ Container: {container.container_id}")

        # Activate layer
        manager.activate_layer(container.container_id, UniverseLayer.PERSONAL)
        print(f"✅ Layer 1 activated")

        # Check data flow
        flow = manager.check_data_flow(UniverseLayer.PERSONAL, UniverseLayer.FAMILY)
        print(f"✅ Data flow: {flow['description']}")

        # Stats
        print(f"\n📊 Stats: {json.dumps(manager.stats(), indent=2)}")

    else:
        print("Usage: python container.py test")
