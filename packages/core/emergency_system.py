
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Emergency System
=========================
Emergency and disaster management
Manages emergency responses, alerts, and disaster coordination
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("EmergencySystem")


class DisasterType(Enum):
    """Types of disasters"""
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    FIRE = "fire"
    HURRICANE = "hurricane"
    TORNADO = "tornado"
    TSUNAMI = "tsunami"
    PANDEMIC = "pandemic"
    CIVIL_UNREST = "civil_unrest"
    TERRORISM = "terrorism"
    TECHNOLOGICAL = "technological"


class AlertLevel(Enum):
    """Alert levels"""
    INFO = "info"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


class EmergencyStatus(Enum):
    """Emergency status"""
    MONITORING = "monitoring"
    ACTIVE = "active"
    RESPONDING = "responding"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class EmergencyAlert:
    """An emergency alert"""
    alert_id: str
    disaster_type: DisasterType
    alert_level: AlertLevel
    location: str
    description: str
    affected_area: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class EmergencyResponse:
    """An emergency response operation"""
    response_id: str
    alert_id: str
    status: EmergencyStatus = EmergencyStatus.MONITORING
    resources_deployed: List[str] = field(default_factory=list)
    personnel_deployed: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmergencySystem:
    """
    Emergency System
    
    Provides:
    - Alert management
    - Response coordination
    - Resource tracking
    - Disaster monitoring
    """
    
    def __init__(self):
        self.logger = logging.getLogger("EmergencySystem")
        self.is_active = False
        self.alerts: Dict[str, EmergencyAlert] = {}
        self.responses: Dict[str, EmergencyResponse] = {}
        self.resources: Dict[str, Dict] = {}
    
    async def start(self):
        """Start the emergency system"""
        self.logger.info("Starting Emergency System...")
        self.is_active = True
        self.logger.info("Emergency System started")
    
    async def stop(self):
        """Stop the emergency system"""
        self.logger.info("Stopping Emergency System...")
        self.is_active = False
        self.logger.info("Emergency System stopped")
    
    def issue_alert(
        self,
        disaster_type: DisasterType,
        alert_level: AlertLevel,
        location: str,
        description: str,
        affected_area: str = "",
        expires_at: Optional[datetime] = None
    ) -> str:
        """
        Issue an emergency alert
        
        Args:
            disaster_type: Type of disaster
            alert_level: Alert level
            location: Location of emergency
            description: Alert description
            affected_area: Affected area
            expires_at: Alert expiration time
            
        Returns:
            Alert ID
        """
        alert_id = f"alert_{datetime.now().timestamp()}"
        
        alert = EmergencyAlert(
            alert_id=alert_id,
            disaster_type=disaster_type,
            alert_level=alert_level,
            location=location,
            description=description,
            affected_area=affected_area,
            expires_at=expires_at
        )
        
        self.alerts[alert_id] = alert
        
        self.logger.info(f"Issued emergency alert: {alert_id}")
        return alert_id
    
    def initiate_response(self, alert_id: str) -> str:
        """
        Initiate an emergency response
        
        Args:
            alert_id: Alert ID to respond to
            
        Returns:
            Response ID
        """
        if alert_id not in self.alerts:
            return ""
        
        response_id = f"response_{datetime.now().timestamp()}"
        
        response = EmergencyResponse(
            response_id=response_id,
            alert_id=alert_id,
            status=EmergencyStatus.RESPONDING
        )
        
        self.responses[response_id] = response
        
        self.logger.info(f"Initiated emergency response: {response_id}")
        return response_id
    
    def deploy_resource(self, response_id: str, resource_id: str) -> bool:
        """Deploy a resource to a response"""
        if response_id not in self.responses:
            return False
        
        if resource_id not in self.responses[response_id].resources_deployed:
            self.responses[response_id].resources_deployed.append(resource_id)
        
        return True
    
    def add_personnel(self, response_id: str, count: int) -> bool:
        """Add personnel to a response"""
        if response_id not in self.responses:
            return False
        
        self.responses[response_id].personnel_deployed += count
        return True
    
    def resolve_response(self, response_id: str) -> bool:
        """Mark a response as resolved"""
        if response_id not in self.responses:
            return False
        
        self.responses[response_id].status = EmergencyStatus.RESOLVED
        self.responses[response_id].resolved_at = datetime.now()
        
        self.logger.info(f"Resolved emergency response: {response_id}")
        return True
    
    def get_alert(self, alert_id: str) -> Optional[Dict]:
        """Get alert by ID"""
        if alert_id not in self.alerts:
            return None
        
        alert = self.alerts[alert_id]
        return {
            "alert_id": alert.alert_id,
            "disaster_type": alert.disaster_type.value,
            "alert_level": alert.alert_level.value,
            "location": alert.location,
            "description": alert.description,
            "affected_area": alert.affected_area,
            "timestamp": alert.timestamp.isoformat(),
            "expires_at": alert.expires_at.isoformat() if alert.expires_at else None
        }
    
    def get_response(self, response_id: str) -> Optional[Dict]:
        """Get response by ID"""
        if response_id not in self.responses:
            return None
        
        response = self.responses[response_id]
        return {
            "response_id": response.response_id,
            "alert_id": response.alert_id,
            "status": response.status.value,
            "resources_deployed": response.resources_deployed,
            "personnel_deployed": response.personnel_deployed,
            "started_at": response.started_at.isoformat(),
            "resolved_at": response.resolved_at.isoformat() if response.resolved_at else None
        }
    
    def list_alerts(
        self,
        disaster_type: Optional[DisasterType] = None,
        alert_level: Optional[AlertLevel] = None
    ) -> List[Dict]:
        """List alerts with optional filtering"""
        alerts = []
        
        for alert in self.alerts.values():
            if disaster_type and alert.disaster_type != disaster_type:
                continue
            if alert_level and alert.alert_level != alert_level:
                continue
            
            alerts.append({
                "alert_id": alert.alert_id,
                "disaster_type": alert.disaster_type.value,
                "alert_level": alert.alert_level.value,
                "location": alert.location,
                "timestamp": alert.timestamp.isoformat()
            })
        
        return alerts
    
    def list_responses(
        self,
        status: Optional[EmergencyStatus] = None
    ) -> List[Dict]:
        """List responses with optional filtering"""
        responses = []
        
        for response in self.responses.values():
            if status and response.status != status:
                continue
            
            responses.append({
                "response_id": response.response_id,
                "alert_id": response.alert_id,
                "status": response.status.value,
                "personnel_deployed": response.personnel_deployed,
                "started_at": response.started_at.isoformat()
            })
        
        return responses
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all currently active alerts"""
        now = datetime.now()
        active = []
        
        for alert in self.alerts.values():
            if alert.expires_at is None or now < alert.expires_at:
                active.append(self.get_alert(alert.alert_id))
        
        return active
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        disaster_counts = {}
        for alert in self.alerts.values():
            disaster = alert.disaster_type.value
            disaster_counts[disaster] = disaster_counts.get(disaster, 0) + 1
        
        status_counts = {}
        for response in self.responses.values():
            status = response.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "is_active": self.is_active,
            "total_alerts": len(self.alerts),
            "total_responses": len(self.responses),
            "total_resources": len(self.resources),
            "disaster_type_counts": disaster_counts,
            "response_status_counts": status_counts
        }
