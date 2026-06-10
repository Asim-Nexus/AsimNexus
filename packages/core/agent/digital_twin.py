
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Human Digital Twin (HDT)
==================================
Creates and manages digital twins of users
Learns from user behavior, preferences, and history
Acts on behalf of user within defined boundaries
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib

logger = logging.getLogger("ASIM_DIGITAL_TWIN")

class TwinState(Enum):
    """Digital twin lifecycle states"""
    INACTIVE = "inactive"
    LEARNING = "learning"
    ACTIVE = "active"
    EXECUTING = "executing"
    PAUSED = "paused"
    ARCHIVED = "archived"

class TwinCapability(Enum):
    """What the twin is authorized to do"""
    READ_EMAIL = "read_email"
    SEND_MESSAGE = "send_message"
    SCHEDULE = "schedule"
    RESEARCH = "research"
    NEGOTIATE = "negotiate"
    SIGN_CONTRACT = "sign_contract"
    MAKE_PAYMENT = "make_payment"
    ADMIN = "admin"

@dataclass
class TwinProfile:
    """Digital twin profile"""
    twin_id: str
    user_id: str
    name: str
    created_at: datetime
    state: TwinState
    
    # Learning data
    behavior_patterns: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    decision_history: List[Dict] = field(default_factory=list)
    
    # Capabilities
    authorized_capabilities: List[TwinCapability] = field(default_factory=list)
    confidence_threshold: float = 0.7
    
    # Contract execution
    active_contracts: List[str] = field(default_factory=list)
    completed_contracts: int = 0
    
    # Limits
    max_contract_duration: int = 30  # days
    max_contract_value: float = 1000.0  # USD
    daily_action_limit: int = 10
    
    # Audit
    last_action: Optional[datetime] = None
    total_actions: int = 0

class HumanDigitalTwin:
    """
    Human Digital Twin Manager
    
    Features:
    - Creates digital representation of user
    - Learns from user behavior
    - Executes contracts within boundaries
    - Requires human approval for high-stakes actions
    """
    
    def __init__(self):
        self.twins: Dict[str, TwinProfile] = {}
        self.learning_data: Dict[str, List[Dict]] = {}
        self.action_log: List[Dict] = []
        
        logger.info("👤 Human Digital Twin system initialized")
    
    def create_twin(self, user_id: str, name: str,
                   capabilities: List[TwinCapability] = None) -> TwinProfile:
        """Create new digital twin for user"""
        
        twin_id = f"twin_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Default capabilities (limited by default)
        default_caps = [
            TwinCapability.READ_EMAIL,
            TwinCapability.SEND_MESSAGE,
            TwinCapability.SCHEDULE,
            TwinCapability.RESEARCH
        ]
        
        twin = TwinProfile(
            twin_id=twin_id,
            user_id=user_id,
            name=name,
            created_at=datetime.now(),
            state=TwinState.LEARNING,
            authorized_capabilities=capabilities or default_caps,
            preferences={
                'communication_style': 'professional',
                'risk_tolerance': 'low',
                'working_hours': {'start': 9, 'end': 17},
                'preferred_currency': 'USD',
                'auto_approve_threshold': 100  # Auto-approve contracts under $100
            }
        )
        
        self.twins[twin_id] = twin
        self.learning_data[twin_id] = []
        
        logger.info(f"👤 Twin created: {twin_id} for {user_id}")
        return twin
    
    def learn_from_action(self, twin_id: str, action: str, context: Dict,
                         outcome: str, user_feedback: str = None):
        """Learn from user actions and feedback"""
        if twin_id not in self.twins:
            return False
        
        learning_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'context': context,
            'outcome': outcome,
            'feedback': user_feedback,
            'pattern_hash': self._hash_pattern(action, context)
        }
        
        self.learning_data[twin_id].append(learning_entry)
        
        # Update behavior patterns
        twin = self.twins[twin_id]
        pattern_key = f"{action}_{context.get('type', 'general')}"
        
        if pattern_key not in twin.behavior_patterns:
            twin.behavior_patterns[pattern_key] = {
                'count': 0,
                'success_rate': 0.0,
                'last_updated': datetime.now().isoformat()
            }
        
        pattern = twin.behavior_patterns[pattern_key]
        pattern['count'] += 1
        pattern['success_rate'] = (
            (pattern['success_rate'] * (pattern['count'] - 1) + (1 if outcome == 'success' else 0))
            / pattern['count']
        )
        pattern['last_updated'] = datetime.now().isoformat()
        
        # Transition from learning to active after enough data
        if twin.state == TwinState.LEARNING and len(self.learning_data[twin_id]) >= 10:
            twin.state = TwinState.ACTIVE
            logger.info(f"👤 Twin {twin_id} graduated to ACTIVE")
        
        return True
    
    def _hash_pattern(self, action: str, context: Dict) -> str:
        """Create hash of behavior pattern"""
        pattern_str = f"{action}:{json.dumps(context, sort_keys=True)}"
        return hashlib.sha256(pattern_str.encode()).hexdigest()[:16]
    
    def can_execute(self, twin_id: str, action: str, value: float = 0) -> Dict:
        """Check if twin can execute action"""
        if twin_id not in self.twins:
            return {'allowed': False, 'reason': 'Twin not found'}
        
        twin = self.twins[twin_id]
        
        # Check state
        if twin.state not in [TwinState.ACTIVE, TwinState.EXECUTING]:
            return {
                'allowed': False,
                'reason': f'Twin is {twin.state.value}, not ready for execution'
            }
        
        # Check daily action limit
        today = datetime.now().date()
        daily_actions = sum(
            1 for log in self.action_log
            if log.get('twin_id') == twin_id
            and datetime.fromisoformat(log.get('timestamp', '1970-01-01')).date() == today
        )
        
        if daily_actions >= twin.daily_action_limit:
            return {
                'allowed': False,
                'reason': f'Daily action limit ({twin.daily_action_limit}) reached'
            }
        
        # Check value limit
        if value > twin.max_contract_value:
            return {
                'allowed': False,
                'reason': f'Value (${value}) exceeds max (${twin.max_contract_value})'
            }
        
        # Check if capability is authorized
        required_cap = self._get_required_capability(action)
        if required_cap and required_cap not in twin.authorized_capabilities:
            return {
                'allowed': False,
                'reason': f'Capability {required_cap.value} not authorized'
            }
        
        # Calculate confidence score
        confidence = self._calculate_confidence(twin_id, action)
        
        # Check if human approval needed
        needs_approval = (
            value > twin.preferences.get('auto_approve_threshold', 100) or
            confidence < twin.confidence_threshold or
            required_cap in [TwinCapability.SIGN_CONTRACT, TwinCapability.MAKE_PAYMENT]
        )
        
        return {
            'allowed': True,
            'confidence': confidence,
            'needs_human_approval': needs_approval,
            'reason': 'Execution approved' if not needs_approval else 'Requires human approval'
        }
    
    def _get_required_capability(self, action: str) -> Optional[TwinCapability]:
        """Get required capability for action"""
        action_caps = {
            'read_email': TwinCapability.READ_EMAIL,
            'send_message': TwinCapability.SEND_MESSAGE,
            'schedule_meeting': TwinCapability.SCHEDULE,
            'research': TwinCapability.RESEARCH,
            'negotiate': TwinCapability.NEGOTIATE,
            'sign_contract': TwinCapability.SIGN_CONTRACT,
            'make_payment': TwinCapability.MAKE_PAYMENT
        }
        return action_caps.get(action)
    
    def _calculate_confidence(self, twin_id: str, action: str) -> float:
        """Calculate confidence score for action"""
        twin = self.twins.get(twin_id)
        if not twin:
            return 0.0
        
        # Base confidence from learning data
        base_confidence = 0.5
        
        # Check if we've seen this pattern before
        pattern_key = f"{action}_general"
        if pattern_key in twin.behavior_patterns:
            pattern = twin.behavior_patterns[pattern_key]
            base_confidence = pattern['success_rate']
        
        # Adjust based on twin experience
        experience_bonus = min(twin.total_actions / 100, 0.2)  # Max 0.2 bonus
        
        return min(base_confidence + experience_bonus, 1.0)
    
    def execute_action(self, twin_id: str, action: str, params: Dict,
                      approved_by_human: bool = False) -> Dict:
        """Execute action on behalf of user"""
        
        # Check if can execute
        value = params.get('value', 0)
        permission = self.can_execute(twin_id, action, value)
        
        if not permission['allowed']:
            return {
                'success': False,
                'error': permission['reason']
            }
        
        # Check if needs human approval
        if permission['needs_human_approval'] and not approved_by_human:
            return {
                'success': False,
                'error': 'Requires human approval',
                'needs_approval': True,
                'approval_request': {
                    'twin_id': twin_id,
                    'action': action,
                    'params': params,
                    'confidence': permission['confidence']
                }
            }
        
        # Execute action (placeholder - real implementation would do actual work)
        twin = self.twins[twin_id]
        twin.state = TwinState.EXECUTING
        
        # Log action
        action_record = {
            'timestamp': datetime.now().isoformat(),
            'twin_id': twin_id,
            'user_id': twin.user_id,
            'action': action,
            'params': params,
            'human_approved': approved_by_human,
            'confidence': permission['confidence']
        }
        self.action_log.append(action_record)
        
        # Update twin stats
        twin.total_actions += 1
        twin.last_action = datetime.now()
        
        # Return to active state
        twin.state = TwinState.ACTIVE
        
        logger.info(f"✅ Twin {twin_id} executed {action}")
        
        return {
            'success': True,
            'action_id': f"action_{len(self.action_log)}",
            'executed_by': twin_id,
            'human_approved': approved_by_human,
            'confidence': permission['confidence']
        }
    
    def add_capability(self, twin_id: str, capability: TwinCapability,
                      user_approved: bool = False) -> bool:
        """Add capability to twin (requires user approval for sensitive caps)"""
        if twin_id not in self.twins:
            return False
        
        twin = self.twins[twin_id]
        
        # Sensitive capabilities require explicit approval
        sensitive_caps = [TwinCapability.SIGN_CONTRACT, TwinCapability.MAKE_PAYMENT, TwinCapability.ADMIN]
        
        if capability in sensitive_caps and not user_approved:
            logger.warning(f"Capability {capability.value} requires user approval")
            return False
        
        if capability not in twin.authorized_capabilities:
            twin.authorized_capabilities.append(capability)
            logger.info(f"✅ Added capability {capability.value} to {twin_id}")
        
        return True
    
    def get_twin(self, twin_id: str) -> Optional[TwinProfile]:
        """Get twin by ID"""
        return self.twins.get(twin_id)
    
    def get_user_twins(self, user_id: str) -> List[TwinProfile]:
        """Get all twins for user"""
        return [
            twin for twin in self.twins.values()
            if twin.user_id == user_id
        ]
    
    def get_twin_stats(self, twin_id: str) -> Dict:
        """Get twin statistics"""
        twin = self.twins.get(twin_id)
        if not twin:
            return {'error': 'Twin not found'}
        
        learning_data = self.learning_data.get(twin_id, [])
        
        return {
            'twin_id': twin_id,
            'user_id': twin.user_id,
            'name': twin.name,
            'state': twin.state.value,
            'created_at': twin.created_at.isoformat(),
            'capabilities': [c.value for c in twin.authorized_capabilities],
            'learning_entries': len(learning_data),
            'behavior_patterns': len(twin.behavior_patterns),
            'total_actions': twin.total_actions,
            'active_contracts': len(twin.active_contracts),
            'completed_contracts': twin.completed_contracts,
            'confidence_threshold': twin.confidence_threshold,
            'limits': {
                'max_contract_duration': twin.max_contract_duration,
                'max_contract_value': twin.max_contract_value,
                'daily_action_limit': twin.daily_action_limit
            }
        }
    
    def pause_twin(self, twin_id: str, reason: str) -> bool:
        """Pause twin execution"""
        if twin_id not in self.twins:
            return False
        
        self.twins[twin_id].state = TwinState.PAUSED
        logger.info(f"⏸️ Twin {twin_id} paused: {reason}")
        return True
    
    def resume_twin(self, twin_id: str) -> bool:
        """Resume twin execution"""
        if twin_id not in self.twins:
            return False
        
        self.twins[twin_id].state = TwinState.ACTIVE
        logger.info(f"▶️ Twin {twin_id} resumed")
        return True

_hdt = None

def get_human_digital_twin() -> HumanDigitalTwin:
    """Get HDT singleton"""
    global _hdt
    if _hdt is None:
        _hdt = HumanDigitalTwin()
    return _hdt

if __name__ == "__main__":
    import sys
    
    hdt = get_human_digital_twin()
    
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        twin = hdt.create_twin("user_001", "My Digital Twin")
        print(f"Created twin: {twin.twin_id}")
        print(f"State: {twin.state.value}")
        print(f"Capabilities: {[c.value for c in twin.authorized_capabilities]}")
        
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        twin_id = sys.argv[2] if len(sys.argv) > 2 else "twin_user_001"
        print(json.dumps(hdt.get_twin_stats(twin_id), indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "learn":
        twin_id = sys.argv[2] if len(sys.argv) > 2 else "twin_user_001"
        hdt.learn_from_action(
            twin_id,
            "schedule_meeting",
            {'type': 'work', 'participants': 3},
            'success'
        )
        print(f"Added learning data to {twin_id}")
        
    else:
        print("Usage: python digital_twin.py [create|stats <twin_id>|learn <twin_id>]")
