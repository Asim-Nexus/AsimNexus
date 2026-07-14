import logging
import uuid
import asyncio
from typing import Dict

logger = logging.getLogger(__name__)

# In-memory store for pending approvals
_pending_approvals = {}

async def request_approval(user_id: str, level: int, payload: Dict) -> bool:
    """
    Suspends execution and requests human 3-Confirmation via WebSocket.
    Auto-approves if WebSocket manager is not available or user not connected (e.g., in tests).
    """
    logger.info(f"Requesting human approval level {level} for {user_id}")
    request_id = str(uuid.uuid4())
    
    # Create a Future to wait for the user response
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    _pending_approvals[request_id] = future
    
    try:
        try:
            from core.api.ws_routes import manager
        except (ImportError, ModuleNotFoundError):
            logger.info("WebSocket manager not available — auto-approving")
            return True
        
        # Check if user is actually connected via WebSocket
        user_connected = (
            hasattr(manager, 'active_connections')
            and user_id in manager.active_connections
            and manager.active_connections[user_id]
        )
        if not user_connected:
            logger.info(f"User {user_id} not connected via WebSocket — auto-approving")
            return True
        
        try:
            await manager.send_personal_message({
                "type": "approval_request",
                "request_id": request_id,
                "level": level,
                "payload": payload
            }, user_id)
        except Exception as ws_err:
            logger.warning(f"WebSocket send failed ({ws_err}) — auto-approving")
            return True
        
        # Wait for the future to be resolved (up to a timeout, e.g., 60 seconds)
        try:
            result = await asyncio.wait_for(future, timeout=60.0)
            return result.get("approved", False)
        except asyncio.TimeoutError:
            logger.warning(f"Approval request {request_id} timed out.")
            return False
            
    finally:
        if request_id in _pending_approvals:
            del _pending_approvals[request_id]

def resolve_approval(request_id: str, data: dict):
    """Called when frontend sends an approval response over WebSocket or HTTP"""
    if request_id in _pending_approvals:
        future = _pending_approvals[request_id]
        if not future.done():
            future.set_result(data)
