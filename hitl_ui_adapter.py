"""
Human-in-the-Loop (HITL) UI Adapter
====================================
Adapter that shows approval prompts in the Odysseus UI when the Gateway
requires human approval for high-risk actions.

This bridges the AsimNexus Gateway's approval system with the Odysseus
frontend, allowing users to approve/reject high-risk tool executions.

Usage:
    from hitl_ui_adapter import HITLAdapter
    
    adapter = HITLAdapter()
    
    # When a tool requires approval:
    approval_id = await adapter.prompt_for_approval(
        capability_id="fs:write",
        target="/etc/config",
        requester="user123",
        risk_tier="HIGH",
        schema=approval_schema
    )
    
    # Wait for user response:
    result = await adapter.wait_for_approval(approval_id, timeout=300)
    if result["approved"]:
        # Execute the tool
        pass
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from gateway_client import gateway_client

logger = logging.getLogger("HITLAdapter")


class HITLTimeoutError(Exception):
    """Raised when HITL approval times out."""
    pass


class HITLAdapter:
    """
    Adapter for Human-in-the-Loop approval prompts.
    
    Features:
    - Generates UI-ready approval prompts
    - Manages approval state (pending, approved, rejected, expired)
    - Supports timeout-based auto-rejection
    - Integrates with Gateway audit ledger
    - Provides WebSocket events for real-time UI updates
    - Supports multiple concurrent approval requests
    """
    
    def __init__(self, default_timeout: int = 300):
        self.default_timeout = default_timeout
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}
        self._approval_events: Dict[str, asyncio.Event] = {}
        self._approval_results: Dict[str, Dict[str, Any]] = {}
        self._listeners: List[Callable] = []
    
    def add_listener(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a listener for approval events (for WebSocket broadcast)."""
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove a listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self, event: Dict[str, Any]):
        """Notify all listeners of an approval event."""
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Listener error: {e}")
    
    async def prompt_for_approval(
        self,
        capability_id: str,
        target: str,
        requester: str,
        risk_tier: str,
        schema: Dict[str, Any] = None,
        timeout: int = None,
    ) -> str:
        """
        Create an approval prompt and return the approval ID.
        
        The UI should listen for approval events and show the prompt.
        
        Returns:
            approval_id: The ID to use when approving/rejecting
        """
        approval_id = str(uuid.uuid4())
        timeout = timeout or self.default_timeout
        
        approval_data = {
            "approval_id": approval_id,
            "capability_id": capability_id,
            "target": target,
            "requester": requester,
            "risk_tier": risk_tier,
            "schema": schema or {},
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": datetime.fromtimestamp(
                time.time() + timeout, tz=timezone.utc
            ).isoformat(),
            "timeout": timeout,
        }
        
        self._pending_approvals[approval_id] = approval_data
        self._approval_events[approval_id] = asyncio.Event()
        
        # Notify listeners (UI will pick this up via WebSocket)
        self._notify_listeners({
            "type": "approval_required",
            "approval_id": approval_id,
            "data": self._build_ui_prompt(approval_data),
        })
        
        logger.info(
            f"HITL: Approval required for {capability_id} -> {target} "
            f"(risk: {risk_tier}, id: {approval_id})"
        )
        
        return approval_id
    
    def _build_ui_prompt(self, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a UI-ready approval prompt from approval data."""
        schema = approval_data.get("schema", {})
        capability = schema.get("capability", {})
        
        return {
            "type": "high_risk_approval",
            "approval_id": approval_data["approval_id"],
            "title": f"⚠️ High-Risk Action: {capability.get('action', approval_data['capability_id'])}",
            "description": capability.get("description", "Unknown action"),
            "risk": capability.get("risk", "Unknown risk"),
            "risk_tier": approval_data["risk_tier"],
            "target": approval_data["target"],
            "requester": approval_data["requester"],
            "can_be_undone": capability.get("can_be_undone", False),
            "requires_reason": approval_data["risk_tier"] in ("HIGH", "CRITICAL"),
            "timeout_seconds": approval_data["timeout"],
            "expires_at": approval_data["expires_at"],
            "actions": [
                {
                    "id": "approve",
                    "label": "✅ Approve",
                    "style": "danger" if approval_data["risk_tier"] == "CRITICAL" else "warning",
                    "requires_reason": approval_data["risk_tier"] in ("HIGH", "CRITICAL"),
                },
                {
                    "id": "reject",
                    "label": "❌ Reject",
                    "style": "default",
                    "requires_reason": True,
                },
            ],
            "ui_hint": (
                "This action requires your explicit approval before it can proceed. "
                "Please review the details carefully."
            ),
        }
    
    async def wait_for_approval(
        self,
        approval_id: str,
        timeout: int = None,
    ) -> Dict[str, Any]:
        """
        Wait for a user to approve or reject a request.
        
        Returns:
            Dict with keys: approved (bool), reason (str), approver (str)
        
        Raises:
            HITLTimeoutError: If the approval times out
        """
        event = self._approval_events.get(approval_id)
        if event is None:
            raise ValueError(f"Unknown approval ID: {approval_id}")
        
        timeout = timeout or self.default_timeout
        
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            # Auto-reject on timeout
            result = {
                "approved": False,
                "reason": "Approval timed out",
                "approver": "system",
                "status": "expired",
            }
            self._approval_results[approval_id] = result
            if approval_id in self._pending_approvals:
                self._pending_approvals[approval_id]["status"] = "expired"
            
            # Notify listeners
            self._notify_listeners({
                "type": "approval_expired",
                "approval_id": approval_id,
            })
            
            raise HITLTimeoutError(f"Approval {approval_id} timed out after {timeout}s")
        
        result = self._approval_results.get(approval_id, {
            "approved": False,
            "reason": "Unknown",
            "approver": "unknown",
        })
        
        return result
    
    async def approve(self, approval_id: str, approver: str, reason: str = "") -> bool:
        """
        Approve a pending request.
        
        Returns:
            True if the approval was successful
        """
        if approval_id not in self._pending_approvals:
            logger.warning(f"Approval {approval_id} not found")
            return False
        
        approval_data = self._pending_approvals[approval_id]
        
        # Check if expired
        if approval_data["status"] == "expired":
            logger.warning(f"Approval {approval_id} already expired")
            return False
        
        # Approve via Gateway
        try:
            gateway_result = await gateway_client.approve(
                request_id=approval_data.get("schema", {}).get("request_id", approval_id),
                approver=approver,
                reason=reason,
            )
        except Exception as e:
            logger.error(f"Gateway approval failed: {e}")
            return False
        
        result = {
            "approved": True,
            "reason": reason,
            "approver": approver,
            "status": "approved",
            "gateway_result": gateway_result,
        }
        
        self._approval_results[approval_id] = result
        self._pending_approvals[approval_id]["status"] = "approved"
        
        # Signal waiting coroutines
        if approval_id in self._approval_events:
            self._approval_events[approval_id].set()
        
        # Notify listeners
        self._notify_listeners({
            "type": "approval_result",
            "approval_id": approval_id,
            "approved": True,
            "approver": approver,
        })
        
        logger.info(f"HITL: Approved by {approver}: {approval_data['capability_id']} -> {approval_data['target']}")
        return True
    
    async def reject(self, approval_id: str, approver: str, reason: str) -> bool:
        """
        Reject a pending request.
        
        Returns:
            True if the rejection was successful
        """
        if approval_id not in self._pending_approvals:
            logger.warning(f"Approval {approval_id} not found")
            return False
        
        approval_data = self._pending_approvals[approval_id]
        
        # Check if expired
        if approval_data["status"] == "expired":
            logger.warning(f"Approval {approval_id} already expired")
            return False
        
        # Reject via Gateway
        try:
            gateway_result = await gateway_client.reject(
                request_id=approval_data.get("schema", {}).get("request_id", approval_id),
                approver=approver,
                reason=reason,
            )
        except Exception as e:
            logger.error(f"Gateway rejection failed: {e}")
            return False
        
        result = {
            "approved": False,
            "reason": reason,
            "approver": approver,
            "status": "rejected",
            "gateway_result": gateway_result,
        }
        
        self._approval_results[approval_id] = result
        self._pending_approvals[approval_id]["status"] = "rejected"
        
        # Signal waiting coroutines
        if approval_id in self._approval_events:
            self._approval_events[approval_id].set()
        
        # Notify listeners
        self._notify_listeners({
            "type": "approval_result",
            "approval_id": approval_id,
            "approved": False,
            "approver": approver,
        })
        
        logger.info(f"HITL: Rejected by {approver}: {approval_data['capability_id']} -> {approval_data['target']}")
        return True
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approvals."""
        return [
            {
                "approval_id": aid,
                "data": self._build_ui_prompt(adata),
                "status": adata["status"],
                "created_at": adata["created_at"],
                "expires_at": adata["expires_at"],
            }
            for aid, adata in self._pending_approvals.items()
            if adata["status"] == "pending"
        ]
    
    def get_approval_status(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an approval request."""
        if approval_id in self._approval_results:
            return self._approval_results[approval_id]
        if approval_id in self._pending_approvals:
            return {"status": self._pending_approvals[approval_id]["status"]}
        return None
    
    def cleanup_expired(self):
        """Remove expired approvals from pending list."""
        now = time.time()
        expired = []
        for aid, adata in self._pending_approvals.items():
            if adata["status"] == "pending":
                try:
                    expires = datetime.fromisoformat(adata["expires_at"]).timestamp()
                    if now > expires:
                        expired.append(aid)
                except (ValueError, KeyError):
                    expired.append(aid)
        
        for aid in expired:
            self._pending_approvals[aid]["status"] = "expired"
            if aid in self._approval_events:
                self._approval_events[aid].set()
            self._notify_listeners({
                "type": "approval_expired",
                "approval_id": aid,
            })


# Singleton instance
hitl_adapter = HITLAdapter()
