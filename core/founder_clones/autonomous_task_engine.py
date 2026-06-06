
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Autonomous Task Execution Engine
===========================================
24/7 autonomous operation engine that:
1. Manages the 5 optimized founder clones
2. Routes chat commands to appropriate founders
3. Executes autonomous tasks on schedule
4. Integrates with all external APIs
5. Self-operates the entire ASIMNEXUS company

This is the BRAIN of the autonomous system.
"""

import asyncio
import logging
import json
import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task Priority Levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    MAINTENANCE = "maintenance"


class TaskStatus(Enum):
    """Task Status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AutonomousTaskEngine:
    """
    Autonomous Task Execution Engine for ASIMNEXUS
    
    Coordinates:
    - 5 Optimized Founder Clones
    - Unified API Key Manager
    - Task queue with priority management
    - 24/7 autonomous operation loop
    - Chat-based command interface
    """
    
    def __init__(self):
        self.founder_system = None
        self.api_key_manager = None
        self.autonomous_running = False
        self.autonomous_task_interval = 300  # 5 minutes
        self.task_queue: List[Dict] = []
        self.completed_tasks: List[Dict] = []
        self.max_history = 1000
        self.chat_history: List[Dict] = []
        self.max_chat_history = 500
        self.system_status = "initializing"
        
    def initialize(self):
        """Initialize all subsystems"""
        try:
            # Initialize API Key Manager
            from core.founder_clones.unified_api_key_manager import get_unified_api_key_manager
            self.api_key_manager = get_unified_api_key_manager()
            logger.info(f"API Key Manager initialized: {self.api_key_manager.get_status_summary()}")
            
            # Get NVIDIA keys for founder system
            nvidia_keys = self.api_key_manager.get_nvidia_keys_for_founders()
            
            # Initialize Optimized Founder System
            from core.founder_clones.optimized_founder_system import get_optimized_founder_system
            self.founder_system = get_optimized_founder_system(nvidia_keys)
            logger.info(f"Founder System initialized: {len(self.founder_system.founders)} founders")
            
            self.system_status = "operational"
            logger.info("🚀 ASIMNEXUS Autonomous Task Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Autonomous Task Engine: {e}")
            self.system_status = f"error: {str(e)}"
    
    async def process_chat_message(self, message: str, user_id: str = "web_user") -> Dict:
        """Main entry point: Process a chat message from frontend
        
        This is the PRIMARY interface between the frontend chat and the entire ASIMNEXUS system.
        It handles:
        1. API key addition from chat
        2. Founder command routing
        3. Natural language task assignment
        4. System status queries
        5. Autonomous mode control
        """
        message_lower = message.lower().strip()
        
        # Store in chat history
        self.chat_history.append({
            "role": "user",
            "content": message,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # === Priority 1: API Key Detection ===
            # Check if user is adding an API key
            if any(k in message_lower for k in ['api key', 'connect api', 'api connect', 'add api', 'mcp server',
                                                  'aiza', 'sk-', 'nvapi-', 'api_key']):
                result = self.api_key_manager.add_api_key_from_chat(message)
                if result.get('success'):
                    # Refresh founder system with new keys
                    await self._refresh_founder_keys()
                    
                    response = result['message']
                    self._add_assistant_message(response)
                    return {
                        "response": response,
                        "type": "api_key_added",
                        "key_id": result.get('key_id'),
                        "timestamp": datetime.now().isoformat()
                    }
            
            # === Priority 2: Direct Commands ===
            # /status, /founders, /tasks, /autopilot, /assign, /models, /help, /keys
            if message_lower.startswith('/'):
                result = await self._handle_command(message, user_id)
                self._add_assistant_message(result.get('response', ''))
                return result
            
            # === Priority 3: Founder System Commands ===
            # Route to optimized founder system
            if self.founder_system:
                result = await self.founder_system.process_chat_command(message, user_id)
                self._add_assistant_message(result.get('response', ''))
                return result
            
            # === Fallback ===
            response = "ASIMNEXUS is initializing. Please try again in a moment."
            self._add_assistant_message(response)
            return {"response": response, "type": "fallback"}
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            error_response = f"Error processing your request: {str(e)}"
            self._add_assistant_message(error_response)
            return {"response": error_response, "type": "error"}
    
    async def _handle_command(self, message: str, user_id: str) -> Dict:
        """Handle slash commands"""
        message_lower = message.lower().strip()
        
        # /keys - API key management
        if message_lower in ['/keys', '/api', '/apis']:
            return {
                "response": self.api_key_manager.get_status_text(),
                "type": "api_keys"
            }
        
        # /addkey - Add API key with structured format
        if message_lower.startswith('/addkey'):
            parts = message.split(maxsplit=1)
            if len(parts) > 1:
                result = self.api_key_manager.add_api_key_from_chat(parts[1])
                if result.get('success'):
                    await self._refresh_founder_keys()
                return result
            return {
                "response": "Usage: /addkey <api key info>\nExample: /addkey nvapi-xxx for nvidia nim",
                "type": "help"
            }
        
        # /removekey - Remove API key
        if message_lower.startswith('/removekey'):
            parts = message.split(maxsplit=1)
            if len(parts) > 1:
                success = self.api_key_manager.remove_api_key(parts[1].strip())
                if success:
                    await self._refresh_founder_keys()
                    return {"response": f"✅ API key '{parts[1].strip()}' removed", "type": "api_key_removed"}
                return {"response": f"❌ Key '{parts[1].strip()}' not found", "type": "error"}
            return {"response": "Usage: /removekey <key_id>", "type": "help"}
        
        # /autopilot - Toggle autonomous mode
        if message_lower.startswith('/autopilot'):
            return await self.founder_system._handle_autopilot_command(message_lower)
        
        # All other commands route to founder system
        if self.founder_system:
            return await self.founder_system.process_chat_command(message, user_id)
        
        return {"response": "Command not available", "type": "error"}
    
    async def _refresh_founder_keys(self):
        """Refresh founder system with updated API keys"""
        if self.founder_system and self.api_key_manager:
            nvidia_keys = self.api_key_manager.get_nvidia_keys_for_founders()
            self.founder_system.nvidia_api_keys = nvidia_keys
            # Re-initialize founders with new keys
            self.founder_system._initialize_founders()
            logger.info(f"Refreshed founder keys: {len(nvidia_keys)} NVIDIA keys available")
    
    def _add_assistant_message(self, content: str):
        """Add assistant message to chat history"""
        self.chat_history.append({
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Trim history
        if len(self.chat_history) > self.max_chat_history:
            self.chat_history = self.chat_history[-self.max_chat_history:]
    
    async def add_task(self, description: str, priority: str = "normal", 
                       assigned_founder: str = None, task_type: str = "user") -> Dict:
        """Add a task to the execution queue"""
        task = {
            "id": f"task_{int(time.time())}_{len(self.task_queue)}",
            "description": description,
            "priority": priority,
            "assigned_founder": assigned_founder,
            "task_type": task_type,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "created_by": "user"
        }
        
        if assigned_founder and self.founder_system:
            # Assign to specific founder
            from core.founder_clones.optimized_founder_system import OptimizedFounderRole
            founder_map = {
                'ceo': OptimizedFounderRole.CEO_STRATEGY,
                'cto': OptimizedFounderRole.CTO_INNOVATION,
                'cfo': OptimizedFounderRole.CFO_OPERATIONS,
                'cpo': OptimizedFounderRole.CPO_MARKET,
                'cdo': OptimizedFounderRole.CDO_ANALYTICS,
            }
            role = founder_map.get(assigned_founder.lower())
            if role:
                founder = self.founder_system.founders.get(role)
                if founder:
                    founder.add_autonomous_task(description, task_type, priority)
                    task["status"] = "assigned"
        
        self.task_queue.append(task)
        return task
    
    async def execute_next_task(self) -> Optional[Dict]:
        """Execute the next highest priority task"""
        if not self.task_queue:
            return None
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3, "maintenance": 4}
        self.task_queue.sort(key=lambda t: priority_order.get(t.get('priority', 'normal'), 2))
        
        task = self.task_queue.pop(0)
        task['status'] = 'running'
        task['started_at'] = datetime.now().isoformat()
        
        try:
            if self.founder_system:
                result = await self.founder_system.process_chat_command(task['description'])
                task['status'] = 'completed'
                task['result'] = result
                task['completed_at'] = datetime.now().isoformat()
            else:
                task['status'] = 'failed'
                task['error'] = 'Founder system not available'
        except Exception as e:
            task['status'] = 'failed'
            task['error'] = str(e)
        
        self.completed_tasks.append(task)
        if len(self.completed_tasks) > self.max_history:
            self.completed_tasks = self.completed_tasks[-self.max_history:]
        
        return task
    
    async def start_autonomous_loop(self):
        """Start the 24/7 autonomous operation loop"""
        if not self.founder_system:
            logger.error("Cannot start autonomous loop: founder system not initialized")
            return
        
        self.autonomous_running = True
        self.founder_system.autonomous_running = True
        logger.info("🤖 ASIMNEXUS 24/7 Autonomous Loop Started")
        
        # Start founder autonomous loop in background
        asyncio.create_task(self.founder_system.start_autonomous_loop())
        
        # Main autonomous loop
        while self.autonomous_running:
            try:
                # Execute any pending user tasks
                if self.task_queue:
                    await self.execute_next_task()
                
                # Periodic health check
                await self._periodic_health_check()
                
                # Wait for next cycle
                await asyncio.sleep(self.autonomous_task_interval)
                
            except Exception as e:
                logger.error(f"Autonomous loop error: {e}")
                await asyncio.sleep(60)
    
    async def _periodic_health_check(self):
        """Periodic health check of all systems"""
        # Check API key health
        if self.api_key_manager:
            health = self.api_key_manager.health_check_all()
            for key_id, status in health.items():
                if status.get('status') == 'rate_limited':
                    logger.info(f"API key {key_id} is rate limited, checking reset...")
        
        # Check founder health
        if self.founder_system:
            for role, founder in self.founder_system.founders.items():
                if not founder.active:
                    logger.warning(f"Founder {founder.config.name} is inactive!")
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        founder_status = {}
        if self.founder_system:
            founder_status = self.founder_system.get_all_founders_status()
        
        api_status = {}
        if self.api_key_manager:
            api_status = self.api_key_manager.get_status_summary()
        
        return {
            "system": "ASIMNEXUS Autonomous Task Engine",
            "status": self.system_status,
            "autonomous_mode": self.autonomous_running,
            "founders": founder_status,
            "api_keys": api_status,
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "chat_messages": len(self.chat_history),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_chat_history(self, limit: int = 50) -> List[Dict]:
        """Get recent chat history"""
        return self.chat_history[-limit:]


# === Singleton Instance ===
_instance = None

def get_autonomous_task_engine() -> AutonomousTaskEngine:
    """Get or create the singleton AutonomousTaskEngine instance"""
    global _instance
    if _instance is None:
        _instance = AutonomousTaskEngine()
    return _instance
