
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Audit Log
===================
Security audit logging system
Records all security-related events and actions
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger("AuditLog")


class AuditEventType(Enum):
    """Types of audit events"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    SYSTEM_EVENT = "system_event"
    SECURITY_ALERT = "security_alert"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLogEntry:
    """An audit log entry"""
    entry_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str]
    action: str
    resource: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None


class AuditLog:
    """
    Audit Log System
    
    Provides:
    - Event logging
    - Log querying
    - Log retention
    - Compliance tracking
    """
    
    def __init__(self):
        self.logger = logging.getLogger("AuditLog")
        self.entries: List[AuditLogEntry] = []
        self.max_entries = 10000
        self.retention_days = 90
    
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """
        Log an audit event
        
        Args:
            event_type: Type of event
            action: Action performed
            resource: Resource affected
            user_id: User performing action
            severity: Severity level
            details: Additional details
            ip_address: IP address of user
            
        Returns:
            Entry ID
        """
        entry_id = f"audit_{datetime.now().timestamp()}"
        
        entry = AuditLogEntry(
            entry_id=entry_id,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            action=action,
            resource=resource,
            details=details or {},
            ip_address=ip_address
        )
        
        self.entries.append(entry)
        
        # Enforce max entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        
        self.logger.info(f"Logged audit event: {event_type.value} - {action}")
        return entry_id
    
    def query_logs(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query audit logs
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user
            resource: Filter by resource
            severity: Filter by severity
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            
        Returns:
            List of log entries
        """
        results = []
        
        for entry in self.entries:
            if event_type and entry.event_type != event_type:
                continue
            if user_id and entry.user_id != user_id:
                continue
            if resource and entry.resource != resource:
                continue
            if severity and entry.severity != severity:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            
            results.append({
                "entry_id": entry.entry_id,
                "event_type": entry.event_type.value,
                "severity": entry.severity.value,
                "user_id": entry.user_id,
                "action": entry.action,
                "resource": entry.resource,
                "timestamp": entry.timestamp.isoformat(),
                "ip_address": entry.ip_address
            })
        
        return results[-limit:]
    
    def get_entry(self, entry_id: str) -> Optional[Dict]:
        """Get entry by ID"""
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return {
                    "entry_id": entry.entry_id,
                    "event_type": entry.event_type.value,
                    "severity": entry.severity.value,
                    "user_id": entry.user_id,
                    "action": entry.action,
                    "resource": entry.resource,
                    "details": entry.details,
                    "timestamp": entry.timestamp.isoformat(),
                    "ip_address": entry.ip_address
                }
        return None
    
    def get_user_activity(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get activity for a specific user"""
        return self.query_logs(user_id=user_id, limit=limit)
    
    def get_resource_history(self, resource: str, limit: int = 50) -> List[Dict]:
        """Get history for a specific resource"""
        return self.query_logs(resource=resource, limit=limit)
    
    def cleanup_old_entries(self) -> int:
        """Remove entries older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        original_count = len(self.entries)
        
        self.entries = [
            entry for entry in self.entries
            if entry.timestamp >= cutoff
        ]
        
        removed = original_count - len(self.entries)
        if removed > 0:
            self.logger.info(f"Cleaned up {removed} old audit entries")
        
        return removed
    
    def get_stats(self) -> Dict:
        """Get audit log statistics"""
        event_counts = {}
        for entry in self.entries:
            event_type = entry.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        severity_counts = {}
        for entry in self.entries:
            severity = entry.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_entries": len(self.entries),
            "event_type_counts": event_counts,
            "severity_counts": severity_counts,
            "max_entries": self.max_entries,
            "retention_days": self.retention_days
        }


# Global audit log instance
audit_log = AuditLog()
