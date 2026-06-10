
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Bridge Gateway
========================
FastAPI Gateway connecting Backend Logic to Frontend Interface
Central entry point for all Global OS operations
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import json

# Add paths for core modules
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "core"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Import ASIMNEXUS Core Systems
from core.main_brain import get_main_brain
from core.neural_gateway import get_neural_gateway

logger = logging.getLogger("BridgeGateway")

# Pydantic Models
class CommandRequest(BaseModel):
    command: str
    parameters: Dict[str, Any] = {}
    layer: Optional[str] = None

class GlobalStatus(BaseModel):
    timestamp: str
    system_health: str
    neural_heartbeat: int
    active_layers: Dict[str, bool]
    global_metrics: Dict[str, Any]

class LayerStatus(BaseModel):
    layer_name: str
    active: bool
    health: float
    status: Dict[str, Any]
    last_updated: str

# Initialize FastAPI
app = FastAPI(
    title="ASIMNEXUS Global OS Gateway",
    description="Bridge between Global OS Backend and Frontend",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.main_brain = None
        self.neural_gateway = None
    
    async def initialize(self):
        """Initialize ASIMNEXUS systems"""
        try:
            self.main_brain = get_main_brain()
            self.neural_gateway = get_neural_gateway()
            
            # Initialize main brain
            if await self.main_brain.initialize():
                logger.info("✅ Main Brain initialized")
            else:
                logger.error("❌ Main Brain initialization failed")
                return False
            
            # Start consciousness loop
            asyncio.create_task(self.main_brain.start_consciousness_loop())
            
            logger.info("✅ ASIMNEXUS Global OS Gateway Ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Gateway initialization failed: {e}")
            return False
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 Frontend connected: {len(self.active_connections)} active")
        
        # Send initial status
        await self.send_personal_message({
            "type": "connected",
            "message": "Connected to ASIMNEXUS Global OS",
            "timestamp": datetime.now().isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 Frontend disconnected: {len(self.active_connections)} active")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            message_str = json.dumps(message, default=str)
            dead_connections = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    dead_connections.append(connection)
            
            # Remove dead connections
            for conn in dead_connections:
                self.active_connections.remove(conn)
    
    async def get_global_status(self) -> Dict[str, Any]:
        """Get complete global system status"""
        if not self.main_brain:
            return {"error": "Main Brain not initialized"}
        
        try:
            status = await self.main_brain.get_global_status()
            return status
        except Exception as e:
            logger.error(f"❌ Failed to get global status: {e}")
            return {"error": f"Status retrieval failed: {e}"}

# Global connection manager
manager = ConnectionManager()

# API Routes
@app.get("/")
async def root():
    return {
        "message": "ASIMNEXUS Global OS Gateway",
        "status": "active",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gateway_active": True,
        "main_brain_active": manager.main_brain is not None,
        "connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/global/status")
async def get_global_status():
    """Get complete global system status"""
    status = await manager.get_global_status()
    return status

@app.get("/api/layers/status")
async def get_layers_status():
    """Get status of all layers"""
    if not manager.main_brain:
        raise HTTPException(status_code=503, detail="Main Brain not initialized")
    
    try:
        global_status = await manager.main_brain.get_global_status()
        layers = global_status.get("layers", {})
        
        layer_statuses = []
        for layer_name, layer_data in layers.items():
            layer_statuses.append(LayerStatus(
                layer_name=layer_name,
                active=layer_data.get("active", False),
                health=layer_data.get("health", 0),
                status=layer_data,
                last_updated=datetime.now().isoformat()
            ))
        
        return {"layers": layer_statuses}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get layers status: {e}")

@app.post("/api/command/execute")
async def execute_command(request: CommandRequest):
    """Execute command on ASIMNEXUS Global OS"""
    if not manager.main_brain:
        raise HTTPException(status_code=503, detail="Main Brain not initialized")
    
    try:
        # Execute command through main brain
        result = await manager.main_brain.execute_global_command(
            request.command, 
            request.parameters
        )
        
        # Broadcast result to all connected clients
        await manager.broadcast({
            "type": "command_result",
            "command": request.command,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Command execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Command execution failed: {e}")

@app.get("/api/layers/{layer_name}/status")
async def get_layer_status(layer_name: str):
    """Get status of specific layer"""
    if not manager.main_brain:
        raise HTTPException(status_code=503, detail="Main Brain not initialized")
    
    try:
        global_status = await manager.main_brain.get_global_status()
        layers = global_status.get("layers", {})
        
        if layer_name not in layers:
            raise HTTPException(status_code=404, detail=f"Layer {layer_name} not found")
        
        return layers[layer_name]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get layer status: {e}")

@app.post("/api/layers/{layer_name}/command")
async def execute_layer_command(layer_name: str, request: CommandRequest):
    """Execute command on specific layer"""
    if not manager.main_brain:
        raise HTTPException(status_code=503, detail="Main Brain not initialized")
    
    try:
        # Route command to specific layer
        full_command = f"{layer_name}_{request.command}"
        result = await manager.main_brain.execute_global_command(
            full_command, 
            request.parameters
        )
        
        # Broadcast result
        await manager.broadcast({
            "type": "layer_command_result",
            "layer": layer_name,
            "command": request.command,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Layer command execution failed: {e}")

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "command":
                # Execute command
                result = await manager.main_brain.execute_global_command(
                    message.get("command", ""),
                    message.get("parameters", {})
                )
                
                # Send result back
                await manager.send_personal_message({
                    "type": "command_response",
                    "command": message.get("command"),
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            elif message.get("type") == "get_status":
                # Send current status
                status = await manager.get_global_status()
                await manager.send_personal_message({
                    "type": "status_update",
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            elif message.get("type") == "heartbeat":
                # Respond to heartbeat
                await manager.send_personal_message({
                    "type": "heartbeat_response",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            else:
                # Unknown message type
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Unknown message type: {message.get('type')}",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)

# Background Tasks
async def system_monitor():
    """Background task to monitor and broadcast system status"""
    while True:
        try:
            if manager.main_brain:
                # Get current status
                status = await manager.get_global_status()
                
                # Broadcast heartbeat
                await manager.broadcast({
                    "type": "system_heartbeat",
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                })
            
            await asyncio.sleep(5)  # Broadcast every 5 seconds
            
        except Exception as e:
            logger.error(f"❌ System monitor error: {e}")
            await asyncio.sleep(10)

# Static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass  # Static directory doesn't exist

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard"""
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASIMNEXUS Global OS Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body { background: #0a0a0a; color: #ffffff; }
        .neural-pulse { animation: pulse 2s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .status-online { color: #10b981; }
        .status-offline { color: #ef4444; }
        .sovereign-bg { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); }
    </style>
</head>
<body class="sovereign-bg min-h-screen">
    <div class="container mx-auto p-6">
        <header class="mb-8">
            <h1 class="text-4xl font-bold text-center mb-2">
                <i data-lucide="brain" class="inline-block mr-2"></i>
                ASIMNEXUS Global OS
            </h1>
            <p class="text-center text-gray-400">World Operating System Dashboard</p>
        </header>

        <main class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            <!-- Neural Heartbeat -->
            <section class="bg-gray-900 rounded-lg p-6 border border-gray-800">
                <h2 class="text-xl font-semibold mb-4 flex items-center">
                    <i data-lucide="activity" class="mr-2"></i>
                    Neural Heartbeat
                </h2>
                <div id="heartbeat" class="text-3xl font-bold mb-2 neural-pulse">--</div>
                <div id="system-health" class="text-sm text-gray-400">Health: --</div>
            </section>

            <!-- Layer Status -->
            <section class="bg-gray-900 rounded-lg p-6 border border-gray-800">
                <h2 class="text-xl font-semibold mb-4 flex items-center">
                    <i data-lucide="layers" class="mr-2"></i>
                    Active Layers
                </h2>
                <div id="layers-status" class="space-y-2">
                    <div class="text-sm text-gray-400">Loading layers...</div>
                </div>
            </section>

            <!-- Global Metrics -->
            <section class="bg-gray-900 rounded-lg p-6 border border-gray-800">
                <h2 class="text-xl font-semibold mb-4 flex items-center">
                    <i data-lucide="globe" class="mr-2"></i>
                    Global Metrics
                </h2>
                <div id="global-metrics" class="space-y-2">
                    <div class="text-sm text-gray-400">Loading metrics...</div>
                </div>
            </section>

            <!-- Command Terminal -->
            <section class="bg-gray-900 rounded-lg p-6 border border-gray-800 lg:col-span-2 xl:col-span-3">
                <h2 class="text-xl font-semibold mb-4 flex items-center">
                    <i data-lucide="terminal" class="mr-2"></i>
                    Global Command Terminal
                </h2>
                <div class="flex gap-2 mb-4">
                    <input 
                        type="text" 
                        id="command-input" 
                        placeholder="Enter Global OS command..."
                        class="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                    >
                    <button 
                        onclick="executeCommand()"
                        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded flex items-center"
                    >
                        <i data-lucide="play" class="w-4 h-4 mr-1"></i>
                        Execute
                    </button>
                </div>
                <div id="command-output" class="bg-gray-800 rounded p-3 h-32 overflow-y-auto text-sm font-mono">
                    Ready for Global OS commands...
                </div>
            </section>
        </main>
    </div>

    <script>
        // Initialize Lucide icons
        lucide.createIcons();

        // WebSocket connection
        const ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onopen = function(event) {
            console.log('🧠 Connected to ASIMNEXUS Global OS');
            updateStatus('connection', 'Connected', true);
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        ws.onclose = function(event) {
            console.log('🔌 Disconnected from ASIMNEXUS');
            updateStatus('connection', 'Disconnected', false);
        };

        function handleWebSocketMessage(data) {
            switch(data.type) {
                case 'system_heartbeat':
                    updateSystemStatus(data.status);
                    break;
                case 'command_response':
                    updateCommandOutput(data.result);
                    break;
                case 'status_update':
                    updateSystemStatus(data.status);
                    break;
            }
        }

        function updateSystemStatus(status) {
            // Update heartbeat
            const heartbeat = status.global_state?.neural_heartbeat || 0;
            document.getElementById('heartbeat').textContent = '#' + heartbeat;
            
            // Update system health
            const health = status.global_state?.system_health || 'unknown';
            document.getElementById('system-health').textContent = 'Health: ' + health.toUpperCase();
            
            // Update layers status
            const layers = status.layers || {};
            const layersHtml = Object.entries(layers).map(([name, data]) => `
                <div class="flex justify-between items-center">
                    <span class="text-sm">${name}</span>
                    <span class="text-xs ${data.active ? 'text-green-400' : 'text-red-400'}">
                        ${data.active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                </div>
            `).join('');
            document.getElementById('layers-status').innerHTML = layersHtml || '<div class="text-sm text-gray-400">No layers active</div>';
            
            // Update global metrics
            const metrics = status.global_state || {};
            const metricsHtml = `
                <div class="text-sm">Heartbeat: ${metrics.neural_heartbeat || 0}</div>
                <div class="text-sm">Health: ${metrics.system_health || 'unknown'}</div>
                <div class="text-sm">Connections: ${metrics.active_connections || 0}</div>
            `;
            document.getElementById('global-metrics').innerHTML = metricsHtml;
        }

        function updateCommandOutput(result) {
            const output = document.getElementById('command-output');
            const timestamp = new Date().toLocaleTimeString();
            const success = result.success ? '✅' : '❌';
            const message = result.message || result.error || 'Command processed';
            
            output.innerHTML += `<div class="mb-1">[${timestamp}] ${success} ${message}</div>`;
            output.scrollTop = output.scrollHeight;
        }

        async function executeCommand() {
            const input = document.getElementById('command-input');
            const command = input.value.trim();
            
            if (!command) return;
            
            // Send command via WebSocket
            ws.send(JSON.stringify({
                type: 'command',
                command: command,
                parameters: {}
            }));
            
            // Clear input
            input.value = '';
        }

        // Handle Enter key
        document.getElementById('command-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeCommand();
            }
        });

        // Request initial status
        setTimeout(() => {
            ws.send(JSON.stringify({ type: 'get_status' }));
        }, 1000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=dashboard_html)

# Startup Events
@app.on_event("startup")
async def startup_event():
    """Initialize ASIMNEXUS Global OS Gateway"""
    logger.info("🚀 ASIMNEXUS Global OS Gateway Starting...")
    
    # Initialize connection manager and systems
    if await manager.initialize():
        # Start background monitoring
        asyncio.create_task(system_monitor())
        
        logger.info("✅ ASIMNEXUS Global OS Gateway Ready")
        logger.info("🌐 Dashboard available at: http://localhost:8000/dashboard")
        logger.info("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    else:
        logger.error("❌ Failed to initialize ASIMNEXUS systems")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown gateway"""
    logger.info("🛑 ASIMNEXUS Global OS Gateway Shutting Down...")
    
    if manager.main_brain:
        await manager.main_brain.shutdown()

# Run the app
if __name__ == "__main__":
    uvicorn.run(
        "gateway:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
