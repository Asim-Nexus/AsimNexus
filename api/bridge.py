
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS API Bridge
====================
FastAPI backend for Master Control Dashboard
Connects Neural Core with Web Frontend via WebSockets
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Add paths for modules
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "asim-nexus-root"))
sys.path.append(str(Path(__file__).parent.parent / "asim-nexus-root" / "dharma-chakra"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Import ASIMNEXUS Core
try:
    from core.neural_gateway import get_neural_gateway
    from kill_switch import get_kill_switch
    from constitutional_safety import get_constitutional_safety
    
    # Initialize core systems
    gateway = get_neural_gateway()
    kill_switch = get_kill_switch()
    safety = get_constitutional_safety()
    
    ASIMNEXUS_READY = True
    logging.info("✅ ASIMNEXUS Core Systems Initialized")
    
except Exception as e:
    logging.error(f"❌ Failed to initialize ASIMNEXUS Core: {e}")
    ASIMNEXUS_READY = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [API-BRIDGE] - %(message)s'
)

# Initialize FastAPI
app = FastAPI(
    title="ASIMNEXUS Master Control API",
    description="Neural Core to Frontend Bridge",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.system_status = {
            "timestamp": datetime.now().isoformat(),
            "neural_gateway": "offline",
            "safety_system": "offline",
            "kill_switch": "offline",
            "heartbeat": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "gpu_usage": 0
        }
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"🔌 WebSocket connected: {len(self.active_connections)} active")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logging.info(f"🔌 WebSocket disconnected: {len(self.active_connections)} active")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: Dict[str, Any]):
        if self.active_connections:
            message_str = json.dumps(message, default=str)
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    # Remove dead connections
                    self.active_connections.remove(connection)

manager = ConnectionManager()

# Pydantic models
class CommandRequest(BaseModel):
    command: str
    parameters: Dict[str, Any] = {}

class SystemStatus(BaseModel):
    timestamp: str
    neural_gateway: str
    safety_system: str
    kill_switch: str
    heartbeat: int
    cpu_usage: float
    memory_usage: float
    gpu_usage: float

class MemoryItem(BaseModel):
    id: str
    content: str
    timestamp: str
    type: str

# API Routes
@app.get("/")
async def root():
    return {"message": "ASIMNEXUS Master Control API", "status": "active"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "asimnexus_ready": ASIMNEXUS_READY,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/system/status")
async def get_system_status():
    """Get current ASIMNEXUS system status"""
    if not ASIMNEXUS_READY:
        return {"error": "ASIMNEXUS Core not initialized"}
    
    try:
        # Get health from neural gateway
        health = gateway.get_system_health()
        
        # Update system status
        manager.system_status.update({
            "timestamp": datetime.now().isoformat(),
            "neural_gateway": health.get("gateway", {}).get("status", "unknown"),
            "safety_system": "active",
            "kill_switch": "armed" if kill_switch.is_armed else "disarmed",
            "heartbeat": manager.system_status["heartbeat"] + 1,
            "cpu_usage": health.get("hardware", {}).get("cpu_usage", 0),
            "memory_usage": health.get("hardware", {}).get("memory_usage", 0),
            "gpu_usage": health.get("hardware", {}).get("gpu_usage", 0)
        })
        
        return SystemStatus(**manager.system_status)
        
    except Exception as e:
        return {"error": f"Failed to get system status: {e}"}

@app.get("/api/memory/stream")
async def get_memory_stream(limit: int = 50):
    """Get recent memory items"""
    if not ASIMNEXUS_READY:
        return {"error": "ASIMNEXUS Core not initialized"}
    
    try:
        memories = gateway.vector_memory.get_recent_memories(limit)
        return {
            "memories": [
                MemoryItem(
                    id=str(mem.id),
                    content=mem.content,
                    timestamp=mem.timestamp.isoformat(),
                    type=mem.memory_type
                ) for mem in memories
            ]
        }
    except Exception as e:
        return {"error": f"Failed to get memory stream: {e}"}

@app.get("/api/safety/policies")
async def get_safety_policies():
    """Get constitutional safety policies"""
    if not ASIMNEXUS_READY:
        return {"error": "ASIMNEXUS Core not initialized"}
    
    try:
        policies = safety.get_all_policies()
        return {"policies": policies}
    except Exception as e:
        return {"error": f"Failed to get safety policies: {e}"}

@app.post("/api/command/execute")
async def execute_command(request: CommandRequest):
    """Execute command on ASIMNEXUS"""
    if not ASIMNEXUS_READY:
        return {"error": "ASIMNEXUS Core not initialized"}
    
    try:
        # Validate command with safety system
        safety_check = safety.validate_action(request.command, request.parameters)
        
        if not safety_check["allowed"]:
            return {
                "success": False,
                "error": "Command blocked by safety system",
                "violations": safety_check.get("violations", [])
            }
        
        # Execute command through neural gateway
        from core.neural_gateway import NeuralRequest
        neural_req = NeuralRequest(
            request_id=f"web_{datetime.now().timestamp()}",
            action=request.command,
            context=request.parameters
        )
        
        response = await gateway.process_request(neural_req)
        
        return {
            "success": response.success,
            "result": response.result,
            "message": response.message
        }
        
    except Exception as e:
        return {"error": f"Command execution failed: {e}"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial status
        await manager.send_personal_message(
            json.dumps({"type": "connected", "message": "Connected to ASIMNEXUS"}),
            websocket
        )
        
        # Keep connection alive and send updates
        while True:
            # Broadcast system status every 2 seconds
            await asyncio.sleep(2)
            
            if ASIMNEXUS_READY:
                status = await get_system_status()
                await manager.broadcast({
                    "type": "system_update",
                    "data": status
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Background task for system monitoring
async def system_monitor():
    """Background task to monitor ASIMNEXUS systems"""
    while True:
        try:
            if ASIMNEXUS_READY:
                # Update system metrics
                health = gateway.get_system_health()
                
                # Broadcast heartbeat
                await manager.broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "neural_gateway": health.get("gateway", {}).get("status", "unknown"),
                        "safety_active": True,
                        "kill_switch_armed": kill_switch.is_armed,
                        "memory_count": health.get("memory", {}).get("total_memories", 0)
                    }
                })
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            logging.error(f"System monitor error: {e}")
            await asyncio.sleep(10)

# Mount static files for frontend
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # Static directory doesn't exist, skip mounting
    pass

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASIMNEXUS Master Control Dashboard</title>
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
                ASIMNEXUS Master Control
            </h1>
            <p class="text-center text-gray-400">Digital Sovereign Entity Interface</p>
        </header>

        <main class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- Neural Pulse Monitor -->
            <section class="bg-gray-900 rounded-lg p-6 border border-gray-800">
                <h2 class="text-xl font-semibold mb-4 flex items-center">
                    <i data-lucide="activity" class="mr-2"></i>
                    Neural Pulse Monitor
                </h2>
                <div id="neural-status" class="text-2xl font-bold mb-2">--</div>
                <div class="text-sm text-gray-400">Heartbeat: <span id="heartbeat">0</span></div>
                <div class="text-sm text-gray-400">CPU: <span id="cpu">0</span>%</div>
                <div class="text-sm text-gray-400">Memory: <span id="memory">0</span>%</div>
                <div class="text-sm text-gray-400">GPU: <span id="gpu">0</span>%</div>
            </section>

            <!-- Dharma-Chakra Status -->
            <section class="bg-gray-900 rounded-lg p-6 border border-gray-800">
                <h2 class="text-xl font-semibold mb-4 flex items-center">
                    <i data-lucide="shield" class="mr-2"></i>
                    Dharma-Chakra Status
                </h2>
                <div id="safety-status" class="text-2xl font-bold mb-2">--</div>
                <div class="text-sm text-gray-400">Policies Active: <span id="policies-count">0</span></div>
                <div class="text-sm text-gray-400">Kill Switch: <span id="kill-switch">--</span></div>
            </section>

            <!-- Memory Stream -->
            <section class="bg-gray-900 rounded-lg p-6 border border-gray-800">
                <h2 class="text-xl font-semibold mb-4 flex items-center">
                    <i data-lucide="database" class="mr-2"></i>
                    Memory Stream
                </h2>
                <div id="memory-count" class="text-2xl font-bold mb-2">--</div>
                <div id="memory-items" class="text-sm text-gray-400 max-h-32 overflow-y-auto">
                    Loading memories...
                </div>
            </section>

            <!-- Command Terminal -->
            <section class="bg-gray-900 rounded-lg p-6 border border-gray-800 md:col-span-2 lg:col-span-3">
                <h2 class="text-xl font-semibold mb-4 flex items-center">
                    <i data-lucide="terminal" class="mr-2"></i>
                    Command Terminal
                </h2>
                <div class="flex gap-2 mb-4">
                    <input 
                        type="text" 
                        id="command-input" 
                        placeholder="Enter ASIMNEXUS command..."
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
                    Ready for commands...
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
            console.log('Connected to ASIMNEXUS');
            updateStatus('connection', 'Connected', true);
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        ws.onclose = function(event) {
            console.log('Disconnected from ASIMNEXUS');
            updateStatus('connection', 'Disconnected', false);
        };

        function handleWebSocketMessage(data) {
            switch(data.type) {
                case 'system_update':
                    updateSystemStatus(data.data);
                    break;
                case 'heartbeat':
                    updateHeartbeat(data.data);
                    break;
                case 'command_result':
                    updateCommandOutput(data.data);
                    break;
            }
        }

        function updateSystemStatus(status) {
            document.getElementById('neural-status').textContent = status.neural_gateway;
            document.getElementById('neural-status').className = 
                status.neural_gateway === 'active' ? 'text-2xl font-bold mb-2 status-online' : 'text-2xl font-bold mb-2 status-offline';
            
            document.getElementById('cpu').textContent = status.cpu_usage.toFixed(1);
            document.getElementById('memory').textContent = status.memory_usage.toFixed(1);
            document.getElementById('gpu').textContent = status.gpu_usage.toFixed(1);
            document.getElementById('heartbeat').textContent = status.heartbeat;
            
            // Update safety status
            document.getElementById('safety-status').textContent = 'Active';
            document.getElementById('safety-status').className = 'text-2xl font-bold mb-2 status-online';
            document.getElementById('kill-switch').textContent = status.kill_switch;
            document.getElementById('kill-switch').className = 
                status.kill_switch === 'armed' ? 'status-online' : 'status-offline';
        }

        function updateHeartbeat(data) {
            document.getElementById('heartbeat').textContent = 
                parseInt(document.getElementById('heartbeat').textContent) + 1;
            
            // Add pulse animation
            document.getElementById('neural-status').classList.add('neural-pulse');
            setTimeout(() => {
                document.getElementById('neural-status').classList.remove('neural-pulse');
            }, 1000);
        }

        function updateCommandOutput(result) {
            const output = document.getElementById('command-output');
            const timestamp = new Date().toLocaleTimeString();
            output.innerHTML += `<div class="mb-1">[${timestamp}] ${result.message || result.error}</div>`;
            output.scrollTop = output.scrollHeight;
        }

        async function executeCommand() {
            const input = document.getElementById('command-input');
            const command = input.value.trim();
            
            if (!command) return;
            
            // Send command to backend
            try {
                const response = await fetch('/api/command/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: command, parameters: {}})
                });
                
                const result = await response.json();
                updateCommandOutput(result);
                
                if (result.success) {
                    input.value = '';
                }
            } catch (error) {
                updateCommandOutput({error: `Command failed: ${error.message}`});
            }
        }

        // Load initial data
        async function loadInitialData() {
            try {
                const statusResponse = await fetch('/api/system/status');
                const status = await statusResponse.json();
                updateSystemStatus(status);
                
                const memoryResponse = await fetch('/api/memory/stream');
                const memory = await memoryResponse.json();
                updateMemoryDisplay(memory.memories);
                
                const policiesResponse = await fetch('/api/safety/policies');
                const policies = await policiesResponse.json();
                document.getElementById('policies-count').textContent = policies.policies?.length || 0;
                
            } catch (error) {
                console.error('Failed to load initial data:', error);
            }
        }

        function updateMemoryDisplay(memories) {
            const container = document.getElementById('memory-items');
            const count = document.getElementById('memory-count');
            
            count.textContent = memories.length;
            
            if (memories.length === 0) {
                container.innerHTML = 'No memories yet...';
                return;
            }
            
            container.innerHTML = memories.slice(0, 5).map(mem => 
                `<div class="mb-1 text-xs">${mem.content.substring(0, 50)}...</div>`
            ).join('');
        }

        // Handle Enter key in command input
        document.getElementById('command-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeCommand();
            }
        });

        // Initialize on load
        loadInitialData();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=dashboard_html)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks"""
    logging.info("🚀 ASIMNEXUS API Bridge Starting...")
    
    # Start system monitor
    asyncio.create_task(system_monitor())
    
    logging.info("✅ ASIMNEXUS Master Control Dashboard Ready")
    logging.info("🌐 Dashboard available at: http://localhost:8000/dashboard")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logging.info("🛑 ASIMNEXUS API Bridge Shutting Down...")

# Run the app
if __name__ == "__main__":
    uvicorn.run(
        "bridge:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
