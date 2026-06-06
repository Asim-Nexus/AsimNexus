
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
Audit Logger - Comprehensive audit logging
Tracks all system actions for security and compliance
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Audit action types"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    MODIFY = "modify"
    ACCESS = "access"
    LOGIN = "login"
    LOGOUT = "logout"


@dataclass
class AuditLog:
    """Audit log entry"""
    log_id: str
    action: AuditAction
    user: str
    resource: str
    details: str
    timestamp: str
    ip_address: Optional[str] = None


class AuditLogger:
    """
    Audit Logger - Comprehensive audit logging
    
    Tracks:
    - User actions
    - System events
    - Security events
    - Compliance requirements
    """
    
    def __init__(self):
        self.audit_logs: List[AuditLog] = []
        logger.info("Audit Logger initialized")
    
    def log_action(self, action: AuditAction, user: str, resource: str, details: str, ip_address: Optional[str] = None) -> AuditLog:
        """Log an action"""
        log = AuditLog(
            log_id=f"audit_{len(self.audit_logs)}",
            action=action,
            user=user,
            resource=resource,
            details=details,
            timestamp=datetime.now().isoformat(),
            ip_address=ip_address
        )
        
        self.audit_logs.append(log)
        logger.info(f"AUDIT: {user} {action.value} {resource} - {details}")
        
        return log
    
    def get_user_logs(self, user: str) -> List[AuditLog]:
        """Get all logs for a specific user"""
        return [log for log in self.audit_logs if log.user == user]
    
    def get_resource_logs(self, resource: str) -> List[AuditLog]:
        """Get all logs for a specific resource"""
        return [log for log in self.audit_logs if log.resource == resource]
    
    def get_action_logs(self, action: AuditAction) -> List[AuditLog]:
        """Get all logs for a specific action"""
        return [log for log in self.audit_logs if log.action == action]
    
    def get_audit_summary(self) -> Dict[str, any]:
        """Get audit summary"""
        action_counts = {}
        for log in self.audit_logs:
            action_counts[log.action.value] = action_counts.get(log.action.value, 0) + 1
        
        return {
            "total_logs": len(self.audit_logs),
            "action_counts": action_counts,
            "unique_users": len(set(log.user for log in self.audit_logs)),
            "unique_resources": len(set(log.resource for log in self.audit_logs))
        }


def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    return AuditLogger()
