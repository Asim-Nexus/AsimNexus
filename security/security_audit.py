
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Audit Log System
Every action logged with full audit trail and replay capability
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from security.security_base import BaseSecurityLayer, ActionType

class ActionType(Enum):
    """Types of actions"""
    BRAIN_THINK = "brain_think"
    TOOL_CALL = "tool_call"
    AGENT_ACTION = "agent_action"
    SYSTEM_COMMAND = "system_command"
    USER_REQUEST = "user_request"
    CONSTITUTION_CHECK = "constitution_check"
    DHARMA_CHECK = "dharma_check"
    SANDBOX_EXEC = "sandbox_exec"

class RiskLevel(Enum):
    """Risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEntry:
    """Single audit log entry"""
    timestamp: float
    action_type: ActionType
    action: str
    agent: str
    risk_level: RiskLevel
    result: str
    context: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    constitution_check: Optional[bool] = None
    dharma_score: Optional[float] = None
    sandbox_used: Optional[bool] = None

class AuditLog(BaseSecurityLayer):
    """Comprehensive audit logging system"""
    
    def __init__(self, log_path: str = None):
        super().__init__(name="audit_log")
        self.logger = logging.getLogger("AuditLog")
        self.log_path = log_path or self._get_default_path()
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.backup_count = 10
        self.session_id = self._generate_session_id()
        self._ensure_log_directory()
    
    def _get_default_path(self) -> str:
        """Get default audit log path"""
        base_path = Path(__file__).parent.parent / "logs"
        base_path.mkdir(exist_ok=True)
        return str(base_path / "audit.jsonl")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
    
    def _rotate_log_if_needed(self):
        """Rotate log file if it's too large"""
        try:
            if os.path.exists(self.log_path) and os.path.getsize(self.log_path) > self.max_file_size:
                # Rotate logs
                for i in range(self.backup_count - 1, 0, -1):
                    old_path = f"{self.log_path}.{i}"
                    new_path = f"{self.log_path}.{i + 1}"
                    if os.path.exists(old_path):
                        if os.path.exists(new_path):
                            os.remove(new_path)
                        os.rename(old_path, new_path)
                
                # Move current log to .1
                backup_path = f"{self.log_path}.1"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(self.log_path, backup_path)
                
                self.logger.info("Audit log rotated")
        except Exception as e:
            self.logger.error(f"Log rotation failed: {e}")
    
    def log_action(self, 
                   action_type: ActionType,
                   action: str,
                   agent: str,
                   risk_level: RiskLevel,
                   result: str,
                   context: Dict[str, Any] = None,
                   user_id: str = None,
                   constitution_check: bool = None,
                   dharma_score: float = None,
                   sandbox_used: bool = None):
        """Log an action with full audit trail"""
        
        entry = AuditEntry(
            timestamp=time.time(),
            action_type=action_type,
            action=action,
            agent=agent,
            risk_level=risk_level,
            result=result,
            context=context or {},
            user_id=user_id or "system",
            session_id=self.session_id,
            ip_address=self._get_client_ip(),
            constitution_check=constitution_check,
            dharma_score=dharma_score,
            sandbox_used=sandbox_used
        )
        
        try:
            self._rotate_log_if_needed()
            
            with open(self.log_path, 'a', encoding='utf-8') as f:
                json.dump(asdict(entry), f, ensure_ascii=False)
                f.write('\n')
            
            # Also log to standard logger for immediate visibility
            self.logger.info(f"AUDIT: {agent} performed {action_type.value} - {risk_level.value} risk - {result}")
            
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
    
    def _get_client_ip(self) -> Optional[str]:
        """Get client IP address (simplified)"""
        try:
            import socket
            return socket.gethostbyname(socket.gethostname())
        except Exception as e:
            self.logger.warning(f"Failed to get client IP: {e}")
            return None
    
    def get_recent_actions(self, limit: int = 100, agent: str = None) -> List[AuditEntry]:
        """Get recent actions from log"""
        actions = []
        
        try:
            if not os.path.exists(self.log_path):
                return actions
            
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Read from end (most recent first)
            for line in reversed(lines[-limit:]):
                try:
                    data = json.loads(line.strip())
                    entry = AuditEntry(**data)
                    
                    if agent is None or entry.agent == agent:
                        actions.append(entry)
                    
                    if len(actions) >= limit:
                        break
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to read audit log: {e}")
        
        return actions
    
    def get_action_history(self, 
                          start_time: float = None,
                          end_time: float = None,
                          action_type: ActionType = None,
                          risk_level: RiskLevel = None) -> List[AuditEntry]:
        """Get filtered action history"""
        actions = []
        
        try:
            if not os.path.exists(self.log_path):
                return actions
            
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        entry = AuditEntry(**data)
                        
                        # Time filter
                        if start_time and entry.timestamp < start_time:
                            continue
                        if end_time and entry.timestamp > end_time:
                            continue
                        
                        # Type filter
                        if action_type and entry.action_type != action_type:
                            continue
                        
                        # Risk filter
                        if risk_level and entry.risk_level != risk_level:
                            continue
                        
                        actions.append(entry)
                        
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Failed to read action history: {e}")
        
        return actions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        stats = {
            "total_actions": 0,
            "by_action_type": {},
            "by_risk_level": {},
            "by_agent": {},
            "recent_actions": 0,
            "high_risk_actions": 0,
            "constitution_violations": 0
        }
        
        try:
            if not os.path.exists(self.log_path):
                return stats
            
            # Last 24 hours
            last_24h = time.time() - 24 * 60 * 60
            
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        entry = AuditEntry(**data)
                        
                        stats["total_actions"] += 1
                        
                        # Recent actions (last 24h)
                        if entry.timestamp > last_24h:
                            stats["recent_actions"] += 1
                        
                        # By action type
                        action_type = entry.action_type.value
                        stats["by_action_type"][action_type] = stats["by_action_type"].get(action_type, 0) + 1
                        
                        # By risk level
                        risk = entry.risk_level.value
                        stats["by_risk_level"][risk] = stats["by_risk_level"].get(risk, 0) + 1
                        
                        # By agent
                        stats["by_agent"][entry.agent] = stats["by_agent"].get(entry.agent, 0) + 1
                        
                        # High risk actions
                        if entry.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                            stats["high_risk_actions"] += 1
                        
                        # Constitution violations
                        if entry.constitution_check is False:
                            stats["constitution_violations"] += 1
                        
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Failed to calculate statistics: {e}")
        
        return stats
    
    def export_audit_report(self, start_time: float = None, end_time: float = None) -> str:
        """Export audit report as JSON"""
        actions = self.get_action_history(start_time, end_time)
        
        report = {
            "generated_at": time.time(),
            "period": {
                "start": start_time,
                "end": end_time
            },
            "total_actions": len(actions),
            "actions": [asdict(action) for action in actions],
            "statistics": self.get_statistics()
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    # Implement abstract methods from BaseSecurityLayer
    async def initialize(self):
        """Initialize audit log"""
        self.logger.info("Audit Log initialized")
        return True
    
    async def authenticate(self, credentials: Dict) -> bool:
        """Authenticate - audit log is system-level, always authenticated"""
        return True
    
    async def authorize(self, user_id: str, action, resource: str) -> bool:
        """Authorize - audit logs all actions"""
        return True

# Global audit log instance
audit_log = AuditLog()
