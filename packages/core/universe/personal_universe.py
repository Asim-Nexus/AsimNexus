
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Personal Universe Manager
=====================================
Manages user's complete lifecycle in AsimNexus
Personal data, preferences, history, connections
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger("ASIM_UNIVERSE")

class UniverseLayer(Enum):
    """5 layers of personal universe"""
    PERSONAL = 1      # Self
    FAMILY = 2        # Family connections
    COMMUNITY = 3     # Local community
    ENTERPRISE = 4    # Work/Company
    SOVEREIGN = 5     # Country/Global

class UserState(Enum):
    """User lifecycle states"""
    CREATED = "created"
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    PAUSED = "paused"
    MIGRATING = "migrating"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    CLOSED = "closed"

@dataclass
class PersonalUniverse:
    """User's personal universe"""
    user_id: str
    display_name: str
    email: str
    created_at: datetime
    state: UserState
    
    # 5 Universe Layers
    layers: Dict[int, Dict] = field(default_factory=dict)
    
    # Personal Data
    preferences: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    connections: Dict[str, List[str]] = field(default_factory=dict)
    
    # System Data
    clone_id: Optional[str] = None
    wallet_id: Optional[str] = None
    identity_id: Optional[str] = None
    
    # Metadata
    last_active: datetime = field(default_factory=datetime.now)
    data_size_mb: float = 0.0
    mesh_nodes: List[str] = field(default_factory=list)

class PersonalUniverseManager:
    """
    Personal Universe Manager
    Manages user's complete lifecycle
    """
    
    def __init__(self):
        self.universes: Dict[str, PersonalUniverse] = {}
        self.layer_templates = self._create_layer_templates()
    
    def _create_layer_templates(self) -> Dict[int, Dict]:
        """Create default templates for each layer"""
        return {
            UniverseLayer.PERSONAL.value: {
                'name': 'Personal',
                'components': ['clone', 'wallet', 'preferences', 'data'],
                'sovereignty': 'full',
                'access': ['self']
            },
            UniverseLayer.FAMILY.value: {
                'name': 'Family',
                'components': ['family_tree', 'shared_memories', 'inheritance'],
                'sovereignty': 'shared',
                'access': ['family_members']
            },
            UniverseLayer.COMMUNITY.value: {
                'name': 'Community',
                'components': ['local_services', 'events', 'help_network'],
                'sovereignty': 'community',
                'access': ['community_members']
            },
            UniverseLayer.ENTERPRISE.value: {
                'name': 'Enterprise',
                'components': ['work_projects', 'skills', 'reputation'],
                'sovereignty': 'company',
                'access': ['colleagues']
            },
            UniverseLayer.SOVEREIGN.value: {
                'name': 'Sovereign',
                'components': ['citizenship', 'tax', 'legal_identity'],
                'sovereignty': 'country',
                'access': ['government']
            }
        }
    
    def create_universe(self, user_id: str, email: str, 
                       display_name: str) -> PersonalUniverse:
        """Create new personal universe for user"""
        
        universe = PersonalUniverse(
            user_id=user_id,
            display_name=display_name,
            email=email,
            created_at=datetime.now(),
            state=UserState.ONBOARDING,
            layers={
                1: {'status': 'initializing', 'components': []},
                2: {'status': 'pending', 'components': []},
                3: {'status': 'pending', 'components': []},
                4: {'status': 'pending', 'components': []},
                5: {'status': 'pending', 'components': []}
            },
            preferences={
                'language': 'ne',
                'currency': 'NPR',
                'theme': 'dark',
                'privacy_level': 'high',
                'offline_mode': True
            },
            connections={
                'family': [],
                'friends': [],
                'colleagues': [],
                'community': [],
                'mesh_peers': []
            }
        )
        
        self.universes[user_id] = universe
        
        logger.info(f"🌌 Universe created for {user_id}: {display_name}")
        return universe
    
    def activate_layer(self, user_id: str, layer: UniverseLayer, 
                      config: Dict) -> bool:
        """Activate a universe layer for user"""
        if user_id not in self.universes:
            return False
        
        universe = self.universes[user_id]
        template = self.layer_templates[layer.value]
        
        universe.layers[layer.value] = {
            'status': 'active',
            'activated_at': datetime.now().isoformat(),
            'components': template['components'],
            'config': config,
            'sovereignty': template['sovereignty']
        }
        
        logger.info(f"✨ Layer {layer.name} activated for {user_id}")
        return True
    
    def record_activity(self, user_id: str, activity_type: str, 
                       details: Dict):
        """Record user activity in history"""
        if user_id not in self.universes:
            return
        
        universe = self.universes[user_id]
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'details': details,
            'layer': details.get('layer', 1)
        }
        
        universe.history.append(entry)
        universe.last_active = datetime.now()
        
        # Keep history manageable (last 1000 entries)
        if len(universe.history) > 1000:
            universe.history = universe.history[-1000:]
    
    def add_connection(self, user_id: str, connection_type: str, 
                      connection_id: str):
        """Add connection to user's network"""
        if user_id not in self.universes:
            return False
        
        universe = self.universes[user_id]
        
        if connection_type not in universe.connections:
            universe.connections[connection_type] = []
        
        if connection_id not in universe.connections[connection_type]:
            universe.connections[connection_type].append(connection_id)
        
        return True
    
    def get_universe_status(self, user_id: str) -> Dict[str, Any]:
        """Get complete universe status"""
        if user_id not in self.universes:
            return {'error': 'Universe not found'}
        
        universe = self.universes[user_id]
        
        # Count active layers
        active_layers = sum(
            1 for l in universe.layers.values()
            if l.get('status') == 'active'
        )
        
        return {
            'user_id': user_id,
            'display_name': universe.display_name,
            'state': universe.state.value,
            'created_at': universe.created_at.isoformat(),
            'last_active': universe.last_active.isoformat(),
            'active_layers': active_layers,
            'total_layers': 5,
            'layers': {
                layer: {
                    'name': self.layer_templates[int(layer)]['name'],
                    'status': data.get('status', 'unknown'),
                    'sovereignty': data.get('sovereignty', 'unknown')
                }
                for layer, data in universe.layers.items()
            },
            'connections': {
                type: len(connections)
                for type, connections in universe.connections.items()
            },
            'history_count': len(universe.history),
            'preferences': universe.preferences,
            'system_ids': {
                'clone': universe.clone_id,
                'wallet': universe.wallet_id,
                'identity': universe.identity_id
            }
        }
    
    def update_state(self, user_id: str, new_state: UserState) -> bool:
        """Update user's universe state"""
        if user_id not in self.universes:
            return False
        
        old_state = self.universes[user_id].state
        self.universes[user_id].state = new_state
        
        logger.info(f"🔄 Universe state: {user_id} {old_state.value} → {new_state.value}")
        return True
    
    def get_lifecycle_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user's lifecycle summary"""
        if user_id not in self.universes:
            return {'error': 'Universe not found'}
        
        universe = self.universes[user_id]
        
        # Calculate lifecycle metrics
        age_days = (datetime.now() - universe.created_at).days
        
        # Activity analysis
        activity_types = {}
        for entry in universe.history:
            t = entry['type']
            activity_types[t] = activity_types.get(t, 0) + 1
        
        return {
            'user_id': user_id,
            'universe_age_days': age_days,
            'state': universe.state.value,
            'activation_progress': sum(
                1 for l in universe.layers.values()
                if l.get('status') == 'active'
            ) / 5 * 100,
            'most_active_layer': max(
                universe.layers.items(),
                key=lambda x: x[1].get('activity_count', 0)
            )[0] if universe.layers else None,
            'activity_summary': activity_types,
            'connection_network_size': sum(
                len(c) for c in universe.connections.values()
            ),
            'data_sovereignty_score': self._calculate_sovereignty_score(universe)
        }
    
    def _calculate_sovereignty_score(self, universe: PersonalUniverse) -> float:
        """Calculate data sovereignty score"""
        score = 0.0
        
        # Personal layer active = 40%
        if universe.layers.get(1, {}).get('status') == 'active':
            score += 0.4
        
        # High privacy preference = 20%
        if universe.preferences.get('privacy_level') == 'high':
            score += 0.2
        
        # Offline mode enabled = 20%
        if universe.preferences.get('offline_mode'):
            score += 0.2
        
        # Data stored locally (simulated) = 20%
        score += 0.2
        
        return round(score * 100, 1)
    
    def migrate_universe(self, user_id: str, new_node: str) -> bool:
        """Migrate universe to new mesh node"""
        if user_id not in self.universes:
            return False
        
        universe = self.universes[user_id]
        
        # Set migrating state
        old_state = universe.state
        universe.state = UserState.MIGRATING
        
        # Add to new node
        universe.mesh_nodes.append(new_node)
        
        # Record migration
        self.record_activity(user_id, 'universe_migration', {
            'from_node': universe.mesh_nodes[0] if universe.mesh_nodes else 'unknown',
            'to_node': new_node,
            'timestamp': datetime.now().isoformat()
        })
        
        # Restore state
        universe.state = old_state
        
        logger.info(f"🚀 Universe migrated: {user_id} → {new_node}")
        return True
    
    def archive_universe(self, user_id: str, reason: str = "User request") -> bool:
        """Archive universe (soft delete, can be restored)"""
        if user_id not in self.universes:
            return False
        
        universe = self.universes[user_id]
        
        # Deactivate all layers
        for layer_name in universe.layers:
            universe.layers[layer_name]['status'] = 'archived'
        
        # Set state
        universe.state = UserState.ARCHIVED
        
        # Record
        self.record_activity(user_id, 'universe_archived', {
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'previous_state': universe.state.value
        })
        
        logger.info(f"📦 Universe archived: {user_id} (reason: {reason})")
        return True
    
    def reactivate_universe(self, user_id: str) -> bool:
        """Reactivate archived universe"""
        if user_id not in self.universes:
            return False
        
        universe = self.universes[user_id]
        
        if universe.state != UserState.ARCHIVED:
            logger.warning(f"Cannot reactivate: {user_id} is not archived")
            return False
        
        # Reactivate personal layer
        universe.layers[UniverseLayer.PERSONAL.value]['status'] = 'active'
        
        # Set state
        universe.state = UserState.ACTIVE
        
        # Record
        self.record_activity(user_id, 'universe_reactivated', {
            'timestamp': datetime.now().isoformat(),
            'previous_state': 'archived'
        })
        
        logger.info(f"🔄 Universe reactivated: {user_id}")
        return True
    
    def suspend_universe(self, user_id: str, reason: str, duration_hours: int = 24) -> bool:
        """Temporarily suspend universe"""
        if user_id not in self.universes:
            return False
        
        universe = self.universes[user_id]
        
        # Set state
        previous_state = universe.state
        universe.state = UserState.SUSPENDED
        
        # Schedule reactivation
        resume_time = datetime.now() + timedelta(hours=duration_hours)
        
        # Record
        self.record_activity(user_id, 'universe_suspended', {
            'reason': reason,
            'duration_hours': duration_hours,
            'resume_at': resume_time.isoformat(),
            'previous_state': previous_state.value
        })
        
        logger.info(f"⏸️ Universe suspended: {user_id} for {duration_hours}h ({reason})")
        return True
    
    def delete_universe_permanently(self, user_id: str, confirmed: bool = False) -> bool:
        """Permanently delete universe (GDPR right to be forgotten)"""
        if not confirmed:
            logger.error("Permanent deletion requires confirmation")
            return False
        
        if user_id not in self.universes:
            return False
        
        # Log deletion
        universe = self.universes[user_id]
        self.record_activity(user_id, 'universe_deleted_permanently', {
            'timestamp': datetime.now().isoformat(),
            'final_layers': list(universe.layers.keys()),
            'data_exported': True  # Assuming data was exported before deletion
        })
        
        # Remove from memory
        del self.universes[user_id]
        
        logger.info(f"🗑️ Universe permanently deleted: {user_id}")
        return True
    
    def calculate_privacy_score(self, user_id: str) -> float:
        """Calculate privacy score for a user's universe"""
        if user_id not in self.universes:
            return 0.0
        universe = self.universes[user_id]
        return self._calculate_sovereignty_score(universe)

    def get_lifecycle_summary(self, user_id: str) -> Dict[str, Any]:
        """Get complete lifecycle summary for user"""
        if user_id not in self.universes:
            return {'error': 'Universe not found'}
        
        universe = self.universes[user_id]
        
        # Calculate lifecycle metrics
        age_days = (datetime.now() - universe.created_at).days
        
        active_layers = sum(
            1 for l in universe.layers.values()
            if l.get('status') == 'active'
        )
        
        return {
            'user_id': user_id,
            'current_state': universe.state.value,
            'created_at': universe.created_at.isoformat(),
            'age_days': age_days,
            'active_layers': active_layers,
            'total_layers': len(universe.layers),
            'mesh_nodes': len(universe.mesh_nodes),
            'activity_count': len(universe.history),
            'last_activity': universe.history[-1]['timestamp'] if universe.history else None,
            'privacy_score': self.calculate_privacy_score(user_id),
            'available_transitions': self._get_available_transitions(universe.state)
        }
    
    def _get_available_transitions(self, state: UserState) -> List[str]:
        """Get available lifecycle transitions from current state"""
        transitions = {
            UserState.CREATED: ['activate', 'archive', 'delete'],
            UserState.ACTIVE: ['suspend', 'archive', 'migrate', 'delete'],
            UserState.SUSPENDED: ['reactivate', 'archive'],
            UserState.ARCHIVED: ['reactivate', 'delete'],
            UserState.MIGRATING: [],  # Automatic transition
        }
        return transitions.get(state, [])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get universe statistics"""
        total = len(self.universes)
        
        states = {}
        for u in self.universes.values():
            states[u.state.value] = states.get(u.state.value, 0) + 1
        
        avg_layers = sum(
            sum(1 for l in u.layers.values() if l.get('status') == 'active')
            for u in self.universes.values()
        ) / total if total else 0
        
        return {
            'total_universes': total,
            'by_state': states,
            'avg_active_layers': round(avg_layers, 2),
            'layer_templates': len(self.layer_templates)
        }

_manager = None

def get_universe_manager() -> PersonalUniverseManager:
    """Get universe manager singleton"""
    global _manager
    if _manager is None:
        _manager = PersonalUniverseManager()
    return _manager

if __name__ == "__main__":
    import sys
    
    manager = get_universe_manager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        universe = manager.create_universe("user_001", "ram@example.com", "Ram")
        manager.activate_layer("user_001", UniverseLayer.PERSONAL, {})
        print(json.dumps(manager.get_universe_status("user_001"), indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(manager.get_universe_status("user_001"), indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "lifecycle":
        print(json.dumps(manager.get_lifecycle_summary("user_001"), indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(manager.get_stats(), indent=2))
        
    else:
        print("Usage: python personal_universe.py [create|status|lifecycle|stats]")
