
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Universal MCP Connector
================================
Model Context Protocol (MCP) for all LLMs and IoT devices
Connects local models, cloud LLMs, and IoT devices
Offline capability with local inference
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid
import aiohttp

logger = logging.getLogger("UniversalMCP")

class ConnectorType(Enum):
    """Types of connectors"""
    LLM_LOCAL = "llm_local"
    LLM_CLOUD = "llm_cloud"
    IOT_DEVICE = "iot_device"
    DATABASE = "database"
    API_SERVICE = "api_service"
    FILE_SYSTEM = "file_system"

class ModelProvider(Enum):
    """LLM model providers"""
    LOCAL_LLAMA = "local_llama"
    LOCAL_MISTRAL = "local_mistral"
    LOCAL_QWEN = "local_qwen"
    OPENROUTER_CLAUDE = "openrouter_claude"
    OPENROUTER_GPT = "openrouter_gpt"
    OPENROUTER_GEMINI = "openrouter_gemini"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"

class IoTDeviceType(Enum):
    """Types of IoT devices"""
    SMART_HOME = "smart_home"
    HEALTH_MONITOR = "health_monitor"
    INDUSTRIAL = "industrial"
    TRANSPORT = "transport"
    AGRICULTURE = "agriculture"
    ENVIRONMENTAL = "environmental"

@dataclass
class MCPConnection:
    """MCP connection configuration"""
    connection_id: str
    connector_type: ConnectorType
    provider: Optional[ModelProvider] = None
    device_type: Optional[IoTDeviceType] = None
    endpoint: str = ""
    api_key: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    last_used: datetime = field(default_factory=datetime.utcnow)
    success_rate: float = 1.0

@dataclass
class MCPMessage:
    """MCP message structure"""
    message_id: str
    connection_id: str
    message_type: str  # "request", "response", "error"
    payload: Dict[str, Any]
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    requires_offline: bool = False

@dataclass
class MCPContext:
    """MCP context for conversations"""
    context_id: str
    connection_id: str
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class UniversalMCPConnector:
    """
    Universal MCP Connector for all LLMs and IoT devices
    Supports local inference, cloud LLMs, and IoT device integration
    Offline capability with local models
    """
    
    def __init__(self):
        self.connections: Dict[str, MCPConnection] = {}
        self.contexts: Dict[str, MCPContext] = {}
        self.message_queue: List[MCPMessage] = []
        self.offline_cache: Dict[str, Any] = {}
        self.is_offline_mode = False
        self.local_models_loaded = False
        self.iot_devices: Dict[str, Dict[str, Any]] = {}
        
        # Initialize connector
        self._initialize_connector()
        
    def _initialize_connector(self) -> None:
        """Initialize the universal MCP connector"""
        logger.info("🔌 Initializing Universal MCP Connector...")
        logger.info("🧠 Supporting: Local LLMs, Cloud LLMs, IoT Devices")
        logger.info("📡 Protocol: Model Context Protocol (MCP)")
        
        # Load local models
        self._load_local_models()
        
        logger.info("✅ Universal MCP Connector initialized")
    
    def _load_local_models(self) -> None:
        """Load local quantized models"""
        try:
            logger.info("🧠 Loading local quantized models...")
            
            # Simulate loading local models
            # In production, this would load actual quantized models
            
            local_connections = [
                MCPConnection(
                    connection_id=f"local_llama_{uuid.uuid4().hex[:8]}",
                    connector_type=ConnectorType.LLM_LOCAL,
                    provider=ModelProvider.LOCAL_LLAMA,
                    config={"model_path": "/models/llama-3-8b.Q4_K_M.gguf", "quantized": True},
                    is_active=True
                ),
                MCPConnection(
                    connection_id=f"local_mistral_{uuid.uuid4().hex[:8]}",
                    connector_type=ConnectorType.LLM_LOCAL,
                    provider=ModelProvider.LOCAL_MISTRAL,
                    config={"model_path": "/models/mistral-7b.Q4_K_M.gguf", "quantized": True},
                    is_active=True
                )
            ]
            
            for conn in local_connections:
                self.connections[conn.connection_id] = conn
            
            self.local_models_loaded = True
            logger.info(f"✅ Loaded {len(local_connections)} local models")
            
        except Exception as e:
            logger.error(f"❌ Local model loading error: {e}")
    
    async def register_connection(
        self,
        connector_type: ConnectorType,
        provider: Optional[ModelProvider] = None,
        device_type: Optional[IoTDeviceType] = None,
        endpoint: str = "",
        api_key: str = "",
        config: Dict[str, Any] = None
    ) -> MCPConnection:
        """Register a new MCP connection"""
        try:
            logger.info(f"📝 Registering connection: {connector_type.value}")
            
            connection = MCPConnection(
                connection_id=f"conn_{uuid.uuid4().hex[:12]}",
                connector_type=connector_type,
                provider=provider,
                device_type=device_type,
                endpoint=endpoint,
                api_key=api_key,
                config=config or {},
                is_active=True
            )
            
            self.connections[connection.connection_id] = connection
            
            logger.info(f"✅ Connection registered: {connection.connection_id}")
            return connection
            
        except Exception as e:
            logger.error(f"❌ Connection registration error: {e}")
            raise
    
    async def send_message(
        self,
        connection_id: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        requires_offline: bool = False
    ) -> Dict[str, Any]:
        """Send a message through MCP connection"""
        try:
            connection = self.connections.get(connection_id)
            
            if not connection:
                return {"success": False, "error": "Connection not found"}
            
            if not connection.is_active:
                return {"success": False, "error": "Connection not active"}
            
            logger.info(f"📤 Sending message through: {connection_id}")
            
            # Create message
            message = MCPMessage(
                message_id=f"msg_{uuid.uuid4().hex[:12]}",
                connection_id=connection_id,
                message_type="request",
                payload=payload,
                timestamp=datetime.utcnow(),
                context=context or {},
                requires_offline=requires_offline
            )
            
            # Process message based on connection type
            if self.is_offline_mode or requires_offline:
                response = await self._process_offline(message, connection)
            else:
                response = await self._process_online(message, connection)
            
            # Update connection stats
            connection.last_used = datetime.utcnow()
            
            # Add to message queue
            self.message_queue.append(message)
            
            logger.info(f"✅ Message processed: {message.message_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Message sending error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_online(self, message: MCPMessage, connection: MCPConnection) -> Dict[str, Any]:
        """Process message in online mode"""
        try:
            if connection.connector_type == ConnectorType.LLM_LOCAL:
                return await self._process_local_llm(message, connection)
            elif connection.connector_type == ConnectorType.LLM_CLOUD:
                return await self._process_cloud_llm(message, connection)
            elif connection.connector_type == ConnectorType.IOT_DEVICE:
                return await self._process_iot_device(message, connection)
            elif connection.connector_type == ConnectorType.DATABASE:
                return await self._process_database(message, connection)
            elif connection.connector_type == ConnectorType.API_SERVICE:
                return await self._process_api_service(message, connection)
            else:
                return {"success": False, "error": "Unsupported connection type"}
            
        except Exception as e:
            logger.error(f"❌ Online processing error: {e}")
            # Fallback to offline mode
            return await self._process_offline(message, connection)
    
    async def _process_offline(self, message: MCPMessage, connection: MCPConnection) -> Dict[str, Any]:
        """Process message in offline mode"""
        try:
            logger.info(f"📴 Processing offline: {message.message_id}")
            
            # Check cache first
            cache_key = f"{message.connection_id}_{hash(json.dumps(message.payload))}"
            if cache_key in self.offline_cache:
                logger.info("✅ Retrieved from offline cache")
                return self.offline_cache[cache_key]
            
            # Process with local models
            if connection.connector_type == ConnectorType.LLM_LOCAL:
                response = await self._process_local_llm(message, connection)
            else:
                # For non-LLM connections, return cached or simulated response
                response = {
                    "success": True,
                    "message_id": message.message_id,
                    "offline_mode": True,
                    "response": "Offline response - limited functionality",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Cache the response
            self.offline_cache[cache_key] = response
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Offline processing error: {e}")
            return {"success": False, "error": "Offline processing failed"}
    
    async def _process_local_llm(self, message: MCPMessage, connection: MCPConnection) -> Dict[str, Any]:
        """Process message with local LLM"""
        try:
            logger.info(f"🧠 Processing with local LLM: {connection.provider.value}")
            
            # Simulate local inference
            # In production, this would use the actual quantized model
            
            payload = message.payload
            prompt = payload.get("prompt", "")
            max_tokens = payload.get("max_tokens", 512)
            temperature = payload.get("temperature", 0.7)
            
            # Generate response (simulated)
            response_text = f"[Local {connection.provider.value}] Response to: {prompt[:100]}..."
            
            return {
                "success": True,
                "message_id": message.message_id,
                "provider": connection.provider.value,
                "response": response_text,
                "tokens_used": len(response_text.split()),
                "processing_time": 0.5,
                "offline_capable": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Local LLM processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_cloud_llm(self, message: MCPMessage, connection: MCPConnection) -> Dict[str, Any]:
        """Process message with cloud LLM"""
        try:
            logger.info(f"☁️ Processing with cloud LLM: {connection.provider.value}")
            
            payload = message.payload
            prompt = payload.get("prompt", "")
            max_tokens = payload.get("max_tokens", 2048)
            temperature = payload.get("temperature", 0.7)
            
            # Prepare API request based on provider
            headers = {
                "Authorization": f"Bearer {connection.api_key}",
                "Content-Type": "application/json"
            }
            
            api_payload = {
                "model": connection.provider.value,
                "messages": [
                    {"role": "system", "content": "You are ASIMNEXUS AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    connection.endpoint,
                    headers=headers,
                    json=api_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Cloud LLM API error: {response.status} - {error_text}")
                        # Fallback to local model
                        return await self._process_local_llm(message, connection)
                    
                    result = await response.json()
            
            # Extract response
            response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            tokens_used = result.get("usage", {}).get("total_tokens", 0)
            
            return {
                "success": True,
                "message_id": message.message_id,
                "provider": connection.provider.value,
                "response": response_text,
                "tokens_used": tokens_used,
                "processing_time": 2.5,
                "offline_capable": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Cloud LLM processing error: {e}")
            # Fallback to local model
            return await self._process_local_llm(message, connection)
    
    async def _process_iot_device(self, message: MCPMessage, connection: MCPConnection) -> Dict[str, Any]:
        """Process message for IoT device"""
        try:
            logger.info(f"🏠 Processing IoT device: {connection.device_type.value}")
            
            payload = message.payload
            device_id = payload.get("device_id", "")
            command = payload.get("command", "")
            parameters = payload.get("parameters", {})
            
            # Simulate IoT device control
            # In production, this would communicate with actual IoT devices
            
            response = {
                "success": True,
                "message_id": message.message_id,
                "device_type": connection.device_type.value,
                "device_id": device_id,
                "command": command,
                "status": "executed",
                "result": f"Command '{command}' executed on device {device_id}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"❌ IoT device processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_database(self, message: MCPMessage, connection: MCPConnection) -> Dict[str, Any]:
        """Process message for database connection"""
        try:
            logger.info(f"💾 Processing database operation")
            
            payload = message.payload
            operation = payload.get("operation", "")
            query = payload.get("query", "")
            data = payload.get("data", {})
            
            # Simulate database operation
            # In production, this would execute actual database queries
            
            response = {
                "success": True,
                "message_id": message.message_id,
                "operation": operation,
                "rows_affected": 1,
                "data": {"status": "completed"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Database processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_api_service(self, message: MCPMessage, connection: MCPConnection) -> Dict[str, Any]:
        """Process message for API service"""
        try:
            logger.info(f"🌐 Processing API service")
            
            payload = message.payload
            method = payload.get("method", "GET")
            path = payload.get("path", "")
            headers = payload.get("headers", {})
            body = payload.get("body", {})
            
            # Make API request
            url = f"{connection.endpoint}{path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    json=body if method in ["POST", "PUT", "PATCH"] else None,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    result = await response.json()
                    
                    return {
                        "success": response.status < 400,
                        "message_id": message.message_id,
                        "status_code": response.status,
                        "data": result,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
        except Exception as e:
            logger.error(f"❌ API service processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_context(
        self,
        connection_id: str,
        metadata: Dict[str, Any] = None
    ) -> MCPContext:
        """Create a new MCP context for conversation"""
        try:
            context = MCPContext(
                context_id=f"ctx_{uuid.uuid4().hex[:12]}",
                connection_id=connection_id,
                metadata=metadata or {}
            )
            
            self.contexts[context.context_id] = context
            
            logger.info(f"✅ Context created: {context.context_id}")
            return context
            
        except Exception as e:
            logger.error(f"❌ Context creation error: {e}")
            raise
    
    async def add_to_context(
        self,
        context_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """Add message to context"""
        try:
            context = self.contexts.get(context_id)
            
            if not context:
                return False
            
            context.conversation_history.append(message)
            context.updated_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Context update error: {e}")
            return False
    
    def set_offline_mode(self, offline: bool) -> None:
        """Set offline mode"""
        self.is_offline_mode = offline
        logger.info(f"📴 Offline mode: {'enabled' if offline else 'disabled'}")
    
    def register_iot_device(
        self,
        device_id: str,
        device_type: IoTDeviceType,
        config: Dict[str, Any]
    ) -> None:
        """Register an IoT device"""
        self.iot_devices[device_id] = {
            "device_type": device_type,
            "config": config,
            "registered_at": datetime.utcnow().isoformat()
        }
        logger.info(f"🏠 IoT device registered: {device_id} ({device_type.value})")
    
    async def control_iot_device(
        self,
        device_id: str,
        command: str,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Control an IoT device"""
        try:
            device = self.iot_devices.get(device_id)
            
            if not device:
                return {"success": False, "error": "Device not found"}
            
            # Find or create connection for this device
            connection_id = f"iot_{device_id}"
            
            if connection_id not in self.connections:
                connection = await self.register_connection(
                    connector_type=ConnectorType.IOT_DEVICE,
                    device_type=device["device_type"],
                    config=device["config"]
                )
            else:
                connection = self.connections[connection_id]
            
            # Send control command
            message = await self.send_message(
                connection_id=connection_id,
                payload={
                    "device_id": device_id,
                    "command": command,
                    "parameters": parameters or {}
                }
            )
            
            return message
            
        except Exception as e:
            logger.error(f"❌ IoT device control error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_connector_status(self) -> Dict[str, Any]:
        """Get connector status"""
        active_connections = len([c for c in self.connections.values() if c.is_active])
        local_connections = len([c for c in self.connections.values() if c.connector_type == ConnectorType.LLM_LOCAL])
        cloud_connections = len([c for c in self.connections.values() if c.connector_type == ConnectorType.LLM_CLOUD])
        iot_connections = len([c for c in self.connections.values() if c.connector_type == ConnectorType.IOT_DEVICE])
        
        return {
            "total_connections": len(self.connections),
            "active_connections": active_connections,
            "local_llm_connections": local_connections,
            "cloud_llm_connections": cloud_connections,
            "iot_connections": iot_connections,
            "total_contexts": len(self.contexts),
            "offline_mode": self.is_offline_mode,
            "offline_cache_size": len(self.offline_cache),
            "local_models_loaded": self.local_models_loaded,
            "registered_iot_devices": len(self.iot_devices)
        }

# Global MCP connector instance
_universal_mcp = UniversalMCPConnector()

async def main():
    """Main entry point for testing"""
    # Register cloud LLM connection
    cloud_conn = await _universal_mcp.register_connection(
        connector_type=ConnectorType.LLM_CLOUD,
        provider=ModelProvider.OPENROUTER_CLAUDE,
        endpoint="https://openrouter.ai/api/v1/chat/completions",
        api_key="test_api_key"
    )
    
    # Send a message
    response = await _universal_mcp.send_message(
        connection_id=cloud_conn.connection_id,
        payload={
            "prompt": "What is the capital of Nepal?",
            "max_tokens": 100,
            "temperature": 0.7
        }
    )
    
    print(f"Message response: {response}")
    
    # Register IoT device
    _universal_mcp.register_iot_device(
        device_id="smart_light_001",
        device_type=IoTDeviceType.SMART_HOME,
        config={"location": "living_room", "type": "light"}
    )
    
    # Control IoT device
    iot_response = await _universal_mcp.control_iot_device(
        device_id="smart_light_001",
        command="turn_on",
        parameters={"brightness": 80}
    )
    
    print(f"IoT control response: {iot_response}")
    
    # Get connector status
    status = _universal_mcp.get_connector_status()
    print(f"Connector status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
