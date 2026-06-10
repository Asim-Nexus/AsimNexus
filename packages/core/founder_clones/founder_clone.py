
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Founder Clone - Individual Founder Implementation
Each founder clone has unique personality, capabilities, and decision-making style
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import yaml

logger = logging.getLogger(__name__)


class FounderRole(Enum):
    """Founder roles"""
    CEO = "CEO"
    CTO = "CTO"
    CFO = "CFO"
    COO = "COO"
    CPO = "CPO"
    CHRO = "CHRO"
    CMO = "CMO"
    CLO = "CLO"
    CSO = "CSO"
    CDO = "CDO"
    CIO = "CIO"
    VP_ENGINEERING = "VP_Engineering"
    VP_PRODUCT = "VP_Product"
    VP_SALES = "VP_Sales"
    VP_OPS = "VP_Ops"


class DecisionStyle(Enum):
    """Decision-making styles"""
    STRATEGIC = "strategic"
    ANALYTICAL = "analytical"
    PRUDENT = "prudent"
    OPERATIONAL = "operational"
    USER_CENTRIC = "user_centric"
    PEOPLE_FOCUSED = "people_focused"
    CREATIVE = "creative"
    CAUTIOUS = "cautious"
    SECURITY_FOCUSED = "security_focused"
    MODERATE = "moderate"


@dataclass
class FounderCloneConfig:
    """Configuration for a founder clone"""
    founder_id: str
    name: str
    role: FounderRole
    responsibilities: List[str]
    model_name: str
    device: str
    context_window: int
    temperature: float
    decision_style: DecisionStyle
    risk_tolerance: str
    communication_style: str
    leadership_style: str
    capabilities: List[str]
    hardware_requirements: Dict[str, Any]
    location: Dict[str, str]
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'FounderCloneConfig':
        """Load configuration from YAML file"""
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        founder = config['founder']
        model = config['model']
        personality = config['personality']
        hardware = config['hardware_requirements']
        location = config['location']
        
        return cls(
            founder_id=founder['id'],
            name=founder['name'],
            role=FounderRole(founder['role']),
            responsibilities=founder['responsibilities'],
            model_name=model['name'],
            device=model['device'],
            context_window=model['context_window'],
            temperature=model['temperature'],
            decision_style=DecisionStyle(personality['decision_style']),
            risk_tolerance=personality['risk_tolerance'],
            communication_style=personality['communication_style'],
            leadership_style=personality['leadership_style'],
            capabilities=config['capabilities'],
            hardware_requirements=hardware,
            location=location
        )


@dataclass
class FounderState:
    """Current state of a founder clone"""
    active: bool = False
    last_activity: Optional[str] = None
    decisions_made: int = 0
    tasks_completed: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    current_task: Optional[str] = None


class FounderClone:
    """
    Founder Clone - Individual Founder Implementation
    
    Each founder clone:
    - Has unique personality and decision-making style
    - Manages specific responsibilities
    - Communicates with other founders
    - Makes decisions in their domain
    - Can be deployed on different hardware
    """
    
    def __init__(self, config: FounderCloneConfig):
        self.config = config
        self.state = FounderState()
        self.message_queue: List[Dict] = []
        self.decision_history: List[Dict] = []
        
        logger.info(f"Founder Clone initialized: {config.name} ({config.role.value})")
    
    def activate(self) -> bool:
        """Activate the founder clone"""
        self.state.active = True
        self.state.last_activity = datetime.now().isoformat()
        logger.info(f"Founder {self.config.name} activated")
        return True
    
    def deactivate(self) -> bool:
        """Deactivate the founder clone"""
        self.state.active = False
        self.state.last_activity = datetime.now().isoformat()
        logger.info(f"Founder {self.config.name} deactivated")
        return True
    
    def make_decision(self, context: str, options: List[str]) -> Dict[str, Any]:
        """
        Make a decision based on context and options
        
        This uses the founder's decision-making style:
        - Strategic founders consider long-term
        - Analytical founders use data
        - Creative founders think outside the box
        - etc.
        """
        # In real implementation, would use LLM with founder's personality
        # For now, use simple logic based on decision style
        
        decision = {
            "founder_id": self.config.founder_id,
            "founder_name": self.config.name,
            "role": self.config.role.value,
            "decision_style": self.config.decision_style.value,
            "context": context,
            "selected_option": options[0] if options else None,
            "reasoning": f"Decision made based on {self.config.decision_style.value} style",
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat()
        }
        
        self.state.decisions_made += 1
        self.decision_history.append(decision)
        
        logger.info(f"Founder {self.config.name} made decision: {decision['selected_option']}")
        
        return decision
    
    def send_message(self, recipient_id: str, message: str) -> bool:
        """Send a message to another founder"""
        msg = {
            "sender_id": self.config.founder_id,
            "sender_name": self.config.name,
            "recipient_id": recipient_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        self.state.messages_sent += 1
        self.message_queue.append(msg)
        
        logger.info(f"Founder {self.config.name} sent message to {recipient_id}")
        
        return True
    
    def receive_message(self, message: Dict[str, Any]) -> bool:
        """Receive a message from another founder"""
        self.state.messages_received += 1
        self.state.last_activity = datetime.now().isoformat()
        
        logger.info(f"Founder {self.config.name} received message from {message['sender_name']}")
        
        return True
    
    def assign_task(self, task: str, priority: str = "medium") -> bool:
        """Assign a task to the founder"""
        self.state.current_task = task
        self.state.last_activity = datetime.now().isoformat()
        
        logger.info(f"Founder {self.config.name} assigned task: {task} (priority: {priority})")
        
        return True
    
    def complete_task(self) -> bool:
        """Mark current task as complete"""
        if self.state.current_task:
            self.state.tasks_completed += 1
            task = self.state.current_task
            self.state.current_task = None
            self.state.last_activity = datetime.now().isoformat()
            
            logger.info(f"Founder {self.config.name} completed task: {task}")
            
            return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the founder clone"""
        return {
            "founder_id": self.config.founder_id,
            "name": self.config.name,
            "role": self.config.role.value,
            "active": self.state.active,
            "last_activity": self.state.last_activity,
            "decisions_made": self.state.decisions_made,
            "tasks_completed": self.state.tasks_completed,
            "messages_sent": self.state.messages_sent,
            "messages_received": self.state.messages_received,
            "current_task": self.state.current_task,
            "decision_style": self.config.decision_style.value,
            "capabilities": self.config.capabilities
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get founder configuration"""
        return {
            "founder_id": self.config.founder_id,
            "name": self.config.name,
            "role": self.config.role.value,
            "responsibilities": self.config.responsibilities,
            "model_name": self.config.model_name,
            "device": self.config.device,
            "temperature": self.config.temperature,
            "decision_style": self.config.decision_style.value,
            "location": self.config.location
        }
