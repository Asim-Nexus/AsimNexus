
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Messaging API Endpoints
=================================
FastAPI endpoints for messaging and AI orchestration
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger("ASIM_Messaging_API")

# Create router
router = APIRouter(prefix="/api", tags=["messaging"])


# ============== MESSAGING ENDPOINTS ==============

@router.post("/messaging/whatsapp/send")
async def send_whatsapp(to: str, message: str):
    """Send WhatsApp message"""
    try:
        from connectors.unified_messaging_connector import messaging_connector
        await messaging_connector.initialize()
        result = await messaging_connector.send_whatsapp_message(to, message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messaging/telegram/send")
async def send_telegram(chat_id: str, message: str):
    """Send Telegram message"""
    try:
        from connectors.unified_messaging_connector import messaging_connector
        await messaging_connector.initialize()
        result = await messaging_connector.send_telegram_message(chat_id, message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messaging/discord/send")
async def send_discord(channel_id: str, message: str):
    """Send Discord message"""
    try:
        from connectors.unified_messaging_connector import messaging_connector
        await messaging_connector.initialize()
        result = await messaging_connector.send_discord_message(channel_id, message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messaging/slack/send")
async def send_slack(channel: str, message: str):
    """Send Slack message"""
    try:
        from connectors.unified_messaging_connector import messaging_connector
        await messaging_connector.initialize()
        result = await messaging_connector.send_slack_message(channel, message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messaging/broadcast")
async def broadcast_message(message: str, platforms: List[str]):
    """Broadcast to multiple platforms"""
    try:
        from connectors.unified_messaging_connector import messaging_connector
        await messaging_connector.initialize()
        result = await messaging_connector.broadcast_message(message, platforms)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messaging/status")
async def messaging_status():
    """Get messaging connector status"""
    try:
        from connectors.unified_messaging_connector import messaging_connector
        return messaging_connector.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== AI ORCHESTRATOR ENDPOINTS ==============

@router.post("/ai/chat")
async def ai_chat(
    user_id: str,
    message: str,
    platform: str = "web",
    message_type: str = "text",
    processing_mode: str = "auto"
):
    """
    Main AI chat endpoint - processes through 15 Founder Clones
    Works with any platform: web, whatsapp, telegram, discord, slack
    """
    try:
        from core.multi_agent_orchestrator import orchestrator
        await orchestrator.initialize()
        
        response = await orchestrator.process_user_message(
            user_id=user_id,
            message=message,
            platform=platform,
            message_type=message_type,
            processing_mode=processing_mode
        )
        
        return {
            "user_id": user_id,
            "platform": platform,
            "user_message": message,
            "ai_response": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/clones/status")
async def clones_status():
    """Get status of all 15 Founder Clones"""
    try:
        from core.multi_agent_orchestrator import orchestrator
        await orchestrator.initialize()
        return orchestrator.get_clone_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/task/create")
async def create_task(
    task_type: str,
    description: str,
    clone_role: str,
    priority: str = "medium"
):
    """Create and assign task to a specific clone"""
    try:
        from core.multi_agent_orchestrator import orchestrator, CloneRole
        await orchestrator.initialize()
        
        role = CloneRole(clone_role)
        task = await orchestrator.create_task(
            task_type=task_type,
            description=description,
            assigned_clone=role,
            priority=priority
        )
        
        return {
            "task_id": task.task_id,
            "assigned_clone": clone_role,
            "status": task.status,
            "result": task.result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== SMART MODEL ROUTER ENDPOINTS ==============

@router.post("/ai/route")
async def route_message(message: str, preference: str = None):
    """Test the Smart Model Router - shows which model would be selected"""
    try:
        from connectors.smart_model_router import model_router
        model_router.initialize()
        selection = model_router.select_model(message, preference)
        return selection
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/models/recommended")
async def get_recommended_models():
    """Get model recommendations for different use cases"""
    try:
        from connectors.smart_model_router import model_router
        model_router.initialize()
        
        use_cases = ['simple_chat', 'coding', 'reasoning', 'creative', 'fast_reasoning', 'general']
        recommendations = {}
        
        for use_case in use_cases:
            recommendations[use_case] = model_router.get_recommended_model(use_case)
        
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/models/status")
async def model_router_status():
    """Get Smart Model Router status"""
    try:
        from connectors.smart_model_router import model_router
        model_router.initialize()
        return model_router.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== API INTEGRATION HUB ENDPOINTS ==============

@router.post("/workflow/execute")
async def execute_workflow(workflow_name: str, params: Dict):
    """Execute a multi-API workflow"""
    try:
        from core.api_integration_hub import api_hub
        result = await api_hub.execute_workflow(workflow_name, params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows")
async def list_workflows():
    """List available workflows"""
    try:
        from core.api_integration_hub import api_hub
        return {
            "workflows": api_hub.list_available_workflows()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/apis/status")
async def all_apis_status():
    """Get status of all APIs"""
    try:
        from core.api_integration_hub import api_hub
        return api_hub.get_all_api_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== WEBSOCKET FOR REAL-TIME CHAT ==============

@router.websocket("/ws/universal-chat")
async def universal_chat_websocket(websocket: WebSocket):
    """Universal WebSocket chat - works with all platforms"""
    await websocket.accept()
    
    try:
        from core.multi_agent_orchestrator import orchestrator
        await orchestrator.initialize()
        
        while True:
            data = await websocket.receive_json()
            
            user_id = data.get('user_id', 'anonymous')
            message = data.get('message', '')
            platform = data.get('platform', 'web')
            processing_mode = data.get('processing_mode', 'auto')
            
            # Process through AI Orchestrator
            response = await orchestrator.process_user_message(
                user_id=user_id,
                message=message,
                platform=platform,
                processing_mode=processing_mode
            )
            
            # Send response
            await websocket.send_json({
                'type': 'ai_response',
                'user_id': user_id,
                'platform': platform,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        logger.info("Client disconnected from universal chat")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
