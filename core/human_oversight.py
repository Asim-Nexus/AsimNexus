
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Human Oversight
=========================
Human oversight and control mechanisms
Ensures human control over autonomous systems
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("HumanOversight")


class ApprovalStatus(Enum):
    """Approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ActionRisk(Enum):
    """Action risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    action: str
    description: str
    risk_level: ActionRisk
    requested_by: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class ASIMHumanOversight:
    """
    Human Oversight System
    
    Provides:
    - Action approval workflow
    - Risk assessment
    - Human-in-the-loop control
    - Audit trail
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ASIMHumanOversight")
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.approval_policies: Dict[str, ActionRisk] = {}
        self.audit_log: List[Dict] = []
        self.settings = {
            "require_approval_for_high_risk": True,
            "require_approval_for_critical": True,
            "auto_approve_low_risk": True,
            "approval_timeout_minutes": 60
        }
    
    def request_approval(
        self,
        action: str,
        description: str,
        risk_level: ActionRisk,
        requested_by: str
    ) -> str:
        """
        Request human approval for an action
        
        Args:
            action: Action description
            description: Detailed description
            risk_level: Risk level of action
            requested_by: Who is requesting
            
        Returns:
            Request ID
        """
        request_id = f"approval_{datetime.now().timestamp()}"
        
        # Check if auto-approval applies
        if risk_level == ActionRisk.LOW and self.settings["auto_approve_low_risk"]:
            self._log_audit(action, "auto_approved", requested_by)
            return request_id
        
        # Check if approval is required
        if risk_level == ActionRisk.LOW and not self.settings["require_approval_for_high_risk"]:
            self._log_audit(action, "auto_approved", requested_by)
            return request_id
        
        # Create approval request
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(minutes=self.settings["approval_timeout_minutes"])
        
        request = ApprovalRequest(
            request_id=request_id,
            action=action,
            description=description,
            risk_level=risk_level,
            requested_by=requested_by,
            status=ApprovalStatus.PENDING,
            expires_at=expires_at
        )
        
        self.approval_requests[request_id] = request
        self.logger.info(f"Approval requested: {request_id} - {action}")
        
        return request_id
    
    def approve_request(
        self,
        request_id: str,
        approved_by: str
    ) -> bool:
        """Approve a request"""
        if request_id not in self.approval_requests:
            return False
        
        request = self.approval_requests[request_id]
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approved_by
        
        self._log_audit(request.action, "approved", approved_by)
        self.logger.info(f"Request approved: {request_id}")
        
        return True
    
    def reject_request(
        self,
        request_id: str,
        rejected_by: str,
        reason: str
    ) -> bool:
        """Reject a request"""
        if request_id not in self.approval_requests:
            return False
        
        request = self.approval_requests[request_id]
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = reason
        
        self._log_audit(request.action, "rejected", rejected_by, reason)
        self.logger.info(f"Request rejected: {request_id} - {reason}")
        
        return True
    
    def get_request(self, request_id: str) -> Optional[Dict]:
        """Get request by ID"""
        if request_id not in self.approval_requests:
            return None
        
        request = self.approval_requests[request_id]
        
        # Check if expired
        if request.expires_at and datetime.now() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
        
        return {
            "request_id": request.request_id,
            "action": request.action,
            "description": request.description,
            "risk_level": request.risk_level.value,
            "requested_by": request.requested_by,
            "status": request.status.value,
            "created_at": request.created_at.isoformat(),
            "expires_at": request.expires_at.isoformat() if request.expires_at else None,
            "approved_by": request.approved_by,
            "rejection_reason": request.rejection_reason
        }
    
    def list_requests(
        self,
        status: Optional[ApprovalStatus] = None
    ) -> List[Dict]:
        """List requests with optional filtering"""
        requests = []
        
        for request in self.approval_requests.values():
            if status and request.status != status:
                continue
            
            requests.append({
                "request_id": request.request_id,
                "action": request.action,
                "risk_level": request.risk_level.value,
                "status": request.status.value,
                "created_at": request.created_at.isoformat()
            })
        
        return requests
    
    def set_policy(self, action_pattern: str, risk_level: ActionRisk):
        """Set approval policy for an action pattern"""
        self.approval_policies[action_pattern] = risk_level
        self.logger.info(f"Set policy: {action_pattern} -> {risk_level.value}")
    
    def get_policy(self, action: str) -> Optional[ActionRisk]:
        """Get policy for an action"""
        # Check exact match
        if action in self.approval_policies:
            return self.approval_policies[action]
        
        # Check pattern match
        for pattern, risk_level in self.approval_policies.items():
            if pattern in action:
                return risk_level
        
        return None
    
    def _log_audit(self, action: str, decision: str, actor: str, reason: Optional[str] = None):
        """Log audit entry"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "decision": decision,
            "actor": actor,
            "reason": reason
        }
        self.audit_log.append(entry)
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get audit log"""
        return self.audit_log[-limit:]
