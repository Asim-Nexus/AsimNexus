"""
AsimNexus Policy Gateway: Gateway Router
=========================================
Central entry point for all Shell requests.
Integrates CapabilityRegistry, VersionedPolicyEngine, and AuditLedger.
Features: Request validation, Replay protection (Nonce+Expiry+Audience),
          Risk escalation, High-risk approval flow, Full audit logging,
          Approval timeout, Standardized export format,
          External API endpoint for Odysseus integration.
"""

import logging, threading, time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.gateway.capability_registry import RiskTier, registry as cap_registry
from core.gateway.versioned_packs import PolicyEffect, policy_engine
from core.gateway.audit_ledger import AuditAction, ledger

logger = logging.getLogger("GatewayRouter")

class RequestStatus(Enum):
    PENDING = "PENDING"; ALLOWED = "ALLOWED"; DENIED = "DENIED"
    ESCALATED = "ESCALATED"; EXPIRED = "EXPIRED"; REPLAY_DETECTED = "REPLAY_DETECTED"

@dataclass
class GatewayRequest:
    request_id: str; capability_id: str; target: str; requester: str
    nonce: str; expiry: str; audience: str
    context: Dict[str, Any] = field(default_factory=dict)
    approval_token: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class GatewayResponse:
    request_id: str; status: RequestStatus; risk_tier: str; reason: str
    requires_approval: bool = False
    approval_schema: Optional[Dict[str, Any]] = None
    audit_entry_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Standardized export format for gateway responses."""
        return {"request_id": self.request_id, "status": self.status.value,
                "risk_tier": self.risk_tier, "reason": self.reason,
                "requires_approval": self.requires_approval,
                "approval_schema": self.approval_schema,
                "audit_entry_id": self.audit_entry_id, "timestamp": self.timestamp}

class ReplayProtection:
    def __init__(self, max_age_seconds: int = 300):
        self._used_nonces: Dict[str, float] = {}; self._max_age = max_age_seconds

    def validate(self, request: GatewayRequest) -> Tuple[bool, str]:
        if request.nonce in self._used_nonces: return False, "Replay: nonce used"
        try:
            if datetime.fromisoformat(request.expiry) < datetime.now(timezone.utc):
                return False, "Request expired"
        except: return False, "Invalid expiry"
        if request.audience != "asim-nexus-kernel": return False, "Invalid audience"
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(request.timestamp)).total_seconds()
            if age > self._max_age: return False, f"Request too old: {age:.0f}s"
        except: return False, "Invalid timestamp"
        self._used_nonces[request.nonce] = time.time()
        cutoff = time.time() - 3600
        for k in list(self._used_nonces.keys()):
            if self._used_nonces[k] < cutoff: del self._used_nonces[k]
        return True, "Valid"

    def get_stats(self) -> Dict[str, Any]:
        return {"active_nonces": len(self._used_nonces), "max_age_seconds": self._max_age}

class HighRiskPromptSchema:
    """
    Standardized high-risk approval prompt schema (v2.0).
    Follows JSON Schema format for UI rendering.
    """

    # Capability metadata registry
    CAPABILITY_META = {
        "fs:read": {"description": "Read files from disk",
                     "action": lambda t: f"READ {t}",
                     "risk": "Data exposure — sensitive files may be read",
                     "can_be_undone": True},
        "fs:write": {"description": "Write files to disk",
                      "action": lambda t: f"WRITE {t}",
                      "risk": "File corruption or overwrite — data may be lost",
                      "can_be_undone": False},
        "sys:exec": {"description": "Execute system commands",
                      "action": lambda t: f"EXECUTE {t}",
                      "risk": "System modification — commands run with user privileges",
                      "can_be_undone": False},
        "net:http": {"description": "Send HTTP requests",
                      "action": lambda t: f"HTTP to {t}",
                      "risk": "External data send — information may leave the system",
                      "can_be_undone": True},
        "net:email_send": {"description": "Send emails",
                           "action": lambda t: f"EMAIL via {t}",
                           "risk": "Unauthorized email — may send on your behalf",
                           "can_be_undone": False},
    }

    @staticmethod
    def build(capability_id, target, requester, risk_tier, context):
        meta = HighRiskPromptSchema.CAPABILITY_META.get(capability_id, {})
        return {
            "schema_version": "2.0",
            "type": "high_risk_approval",
            "risk_tier": risk_tier,
            "capability": {
                "id": capability_id,
                "description": meta.get("description", "Unknown capability"),
                "action": meta.get("action", lambda t: f"Execute {capability_id}")(target),
                "risk": meta.get("risk", "Unknown risk"),
                "can_be_undone": meta.get("can_be_undone", False)
            },
            "target": target,
            "requester": requester,
            "context": context if isinstance(context, dict) else {},
            "approval_required": {
                "type": "explicit_confirmation",
                "timeout_seconds": 300,
                "requires_reason": risk_tier in ("HIGH", "CRITICAL"),
                "allowed_approvers": ["admin", "owner"],
                "ui_prompt": (
                    f"[HIGH-RISK] {meta.get('action', lambda t: f'Execute {capability_id}')(target)}\n"
                    f"Risk: {meta.get('risk', 'Unknown')}\n"
                    f"Requester: {requester}\n"
                    f"Tier: {risk_tier}\n"
                    f"Reason required: {'YES' if risk_tier in ('HIGH', 'CRITICAL') else 'NO'}"
                )
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

class GatewayRouter:
    def __init__(self, approval_timeout_seconds: int = 300):
        self._replay = ReplayProtection()
        self._pending_approvals: Dict[str, GatewayRequest] = {}
        self._approval_timeout = approval_timeout_seconds
        self._approval_timestamps: Dict[str, float] = {}
        # Start background cleanup thread for expired approvals
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired_approvals, daemon=True)
        self._cleanup_thread.start()

    def _cleanup_expired_approvals(self):
        """Background thread that periodically removes expired pending approvals."""
        while True:
            time.sleep(30)  # Check every 30 seconds
            now = time.time()
            expired = [rid for rid, ts in self._approval_timestamps.items()
                       if now - ts > self._approval_timeout]
            for rid in expired:
                request = self._pending_approvals.pop(rid, None)
                self._approval_timestamps.pop(rid, None)
                if request:
                    logger.info(f"Approval {rid} expired after {self._approval_timeout}s timeout")
                    ledger.record(AuditAction.REJECT, request.requester, "gateway:timeout", "gateway",
                        "human-in-the-loop", request.capability_id, request.target, "HIGH", "EXPIRED",
                        f"Approval timed out after {self._approval_timeout}s",
                        {"request_id": rid, "reason": "timeout"})

    def route_request(self, request: GatewayRequest) -> GatewayResponse:
        valid, reason = self._replay.validate(request)
        if not valid: return self._deny(request, RequestStatus.REPLAY_DETECTED, reason)
        try: risk_tier = cap_registry.evaluate_risk(request.capability_id, request.target)
        except PermissionError as e: return self._deny(request, RequestStatus.DENIED, str(e))
        effect, rule = policy_engine.resolve_rules(request.capability_id, request.target)
        # If policy explicitly denies, block it
        if effect == PolicyEffect.DENY:
            # But if the capability is registered (known), let risk decide instead of hard-deny
            # This allows registered capabilities to work even without explicit policy rules
            if risk_tier in (RiskTier.HIGH, RiskTier.CRITICAL):
                return self._escalate(request, risk_tier)
            return self._allow(request, risk_tier, "registry-default")
        if effect == PolicyEffect.ESCALATE:
            return self._escalate(request, risk_tier)
        if risk_tier in (RiskTier.HIGH, RiskTier.CRITICAL):
            return self._escalate(request, risk_tier)
        return self._allow(request, risk_tier, getattr(rule, 'pack_id', 'default'))

    def _allow(self, request, risk_tier, policy_id):
        entry = ledger.record(AuditAction.EXECUTE, request.requester, "gateway:auto", "kernel",
            policy_id, request.capability_id, request.target, risk_tier.value, "ALLOWED",
            f"Auto-allowed", {"request_id": request.request_id})
        return GatewayResponse(request.request_id, RequestStatus.ALLOWED, risk_tier.value,
                               f"Allowed", audit_entry_id=entry.entry_id)

    def _deny(self, request, status, reason):
        entry = ledger.record(AuditAction.REJECT, request.requester, "gateway:auto", "gateway",
            "default-deny", request.capability_id, request.target, "UNKNOWN", status.value,
            reason, {"request_id": request.request_id})
        return GatewayResponse(request.request_id, status, "UNKNOWN", reason, audit_entry_id=entry.entry_id)

    def _escalate(self, request, risk_tier):
        self._pending_approvals[request.request_id] = request
        self._approval_timestamps[request.request_id] = time.time()
        entry = ledger.record(AuditAction.ESCALATE, request.requester, "gateway:pending", "gateway",
            "human-in-the-loop", request.capability_id, request.target, risk_tier.value, "ESCALATED",
            f"Requires human approval", {"request_id": request.request_id})
        schema = HighRiskPromptSchema.build(request.capability_id, request.target,
                                            request.requester, risk_tier.value, request.context)
        return GatewayResponse(request.request_id, RequestStatus.ESCALATED, risk_tier.value,
                               "High-risk action requires approval", requires_approval=True,
                               approval_schema=schema, audit_entry_id=entry.entry_id)

    def approve_request(self, request_id, approver, reason):
        request = self._pending_approvals.pop(request_id, None)
        self._approval_timestamps.pop(request_id, None)
        if not request: return None
        try:
            if datetime.fromisoformat(request.expiry) < datetime.now(timezone.utc):
                return GatewayResponse(request_id, RequestStatus.EXPIRED, "UNKNOWN", "Expired")
        except: pass
        entry = ledger.record(AuditAction.APPROVE, request.requester, approver, "kernel",
            "human-in-the-loop", request.capability_id, request.target, "HIGH", "ALLOWED",
            f"Approved: {reason}", {"request_id": request_id})
        return GatewayResponse(request_id, RequestStatus.ALLOWED, "HIGH",
                               f"Approved by {approver}", audit_entry_id=entry.entry_id)

    def reject_request(self, request_id, approver, reason):
        request = self._pending_approvals.pop(request_id, None)
        self._approval_timestamps.pop(request_id, None)
        if not request: return None
        entry = ledger.record(AuditAction.REJECT, request.requester, approver, "gateway",
            "human-in-the-loop", request.capability_id, request.target, "HIGH", "DENIED",
            f"Rejected: {reason}", {"request_id": request_id})
        return GatewayResponse(request_id, RequestStatus.DENIED, "HIGH",
                               f"Rejected by {approver}", audit_entry_id=entry.entry_id)

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """List all pending approvals with their schemas."""
        result = []
        for rid, req in self._pending_approvals.items():
            result.append({"request_id": rid, "capability_id": req.capability_id,
                           "target": req.target, "requester": req.requester,
                           "timestamp": req.timestamp,
                           "schema": HighRiskPromptSchema.build(
                               req.capability_id, req.target, req.requester,
                               "PENDING", req.context)})
        return result

    def get_stats(self):
        return {"pending_approvals": len(self._pending_approvals),
                "approval_timeout_seconds": self._approval_timeout,
                "replay_protection": self._replay.get_stats(),
                "audit_ledger": ledger.get_stats()}

router = GatewayRouter()


# ─── External API Endpoint for Odysseus Integration ──────────────────────────

def create_gateway_api(app):
    """
    Register Gateway API endpoints on a FastAPI application.
    
    This allows external services (like Odysseus) to call the Gateway
    via HTTP REST instead of importing the Python module directly.
    
    Usage:
        from fastapi import FastAPI
        from core.gateway.router import create_gateway_api
        
        app = FastAPI()
        create_gateway_api(app)
    """
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    
    gateway_router = APIRouter(prefix="/gateway", tags=["gateway"])
    
    class CheckRequest(BaseModel):
        request_id: str
        capability_id: str
        target: str
        requester: str
        nonce: str
        expiry: str
        audience: str
        context: dict = {}
        approval_token: Optional[str] = None
        timestamp: str = ""
    
    class ApproveRequest(BaseModel):
        request_id: str
        approver: str
        reason: str = ""
    
    class AuditRequest(BaseModel):
        action: str
        requester: str
        approver: str
        executor: str
        policy_id: str
        capability_id: str
        target: str
        risk_tier: str
        status: str
        reason: str = ""
        metadata: dict = {}
    
    @gateway_router.post("/check")
    async def gateway_check(req: CheckRequest):
        """Check if a request is allowed through the Gateway."""
        try:
            gw_request = GatewayRequest(
                request_id=req.request_id,
                capability_id=req.capability_id,
                target=req.target,
                requester=req.requester,
                nonce=req.nonce,
                expiry=req.expiry,
                audience=req.audience,
                context=req.context,
                approval_token=req.approval_token,
                timestamp=req.timestamp or datetime.now(timezone.utc).isoformat(),
            )
            response = router.route_request(gw_request)
            return response.to_dict()
        except PermissionError as e:
            return {
                "request_id": req.request_id,
                "status": "DENIED",
                "risk_tier": "UNKNOWN",
                "reason": str(e),
                "requires_approval": False,
                "approval_schema": None,
                "audit_entry_id": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    
    @gateway_router.post("/approve")
    async def gateway_approve(req: ApproveRequest):
        """Approve a pending high-risk request."""
        response = router.approve_request(req.request_id, req.approver, req.reason)
        if response is None:
            raise HTTPException(status_code=404, detail="Request not found or already processed")
        return response.to_dict()
    
    @gateway_router.post("/reject")
    async def gateway_reject(req: ApproveRequest):
        """Reject a pending high-risk request."""
        response = router.reject_request(req.request_id, req.approver, req.reason)
        if response is None:
            raise HTTPException(status_code=404, detail="Request not found or already processed")
        return response.to_dict()
    
    @gateway_router.get("/pending")
    async def gateway_pending():
        """Get all pending approvals."""
        return {"pending_approvals": router.get_pending_approvals()}
    
    @gateway_router.get("/capabilities")
    async def gateway_capabilities():
        """Get all registered capabilities."""
        return {"capabilities": cap_registry.list_capabilities()}
    
    @gateway_router.get("/stats")
    async def gateway_stats():
        """Get Gateway statistics."""
        return router.get_stats()
    
    @gateway_router.get("/health")
    async def gateway_health():
        """Gateway health check."""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pending_approvals": len(router._pending_approvals),
            "capabilities": len(cap_registry._capabilities),
        }
    
    @gateway_router.post("/audit")
    async def gateway_audit(req: AuditRequest):
        """Log an action to the audit ledger."""
        try:
            action = AuditAction(req.action)
        except ValueError:
            action = AuditAction.EXECUTE
        
        entry = ledger.record(
            action=action,
            requester=req.requester,
            approver=req.approver,
            executor=req.executor,
            policy_id=req.policy_id,
            capability_id=req.capability_id,
            target=req.target,
            risk_tier=req.risk_tier,
            status=req.status,
            reason=req.reason,
            metadata=req.metadata,
        )
        return {"entry_id": entry.entry_id, "status": "recorded"}
    
    @gateway_router.get("/audit/entries")
    async def gateway_audit_entries(
        requester: Optional[str] = None,
        capability_id: Optional[str] = None,
        status: Optional[str] = None,
        risk_tier: Optional[str] = None,
        limit: int = 100,
    ):
        """Get audit ledger entries with optional filters."""
        entries = ledger.get_entries(
            requester=requester,
            capability_id=capability_id,
            status=status,
            risk_tier=risk_tier,
            limit=limit,
        )
        return {"entries": entries, "count": len(entries)}
    
    @gateway_router.get("/audit/verify")
    async def gateway_audit_verify():
        """Verify the integrity of the audit ledger."""
        return {
            "integrity_verified": ledger.verify_integrity(),
            "tampering_detected": ledger.detect_tampering(),
        }
    
    app.include_router(gateway_router)
    return gateway_router
