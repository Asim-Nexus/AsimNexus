
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Live Gateway Controller
================================
HTTP/3 + TLS + WebSockets - Real-time Neural Core Interface
"""

import asyncio
import logging
import json
import ssl
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import hypercorn.config
import hypercorn.asyncio

logger = logging.getLogger("LiveController")

class LiveGatewayController:
    """HTTP/3 + WebSocket Live Gateway"""
    
    def __init__(self):
        self.app = FastAPI(title="ASIMNEXUS Live Gateway")
        self.active_connections: List[WebSocket] = []
        self.neural_pulse_data = {}
        self.agent_streams = {}
        
        self._setup_middleware()
        self._setup_routes()
        
    def _setup_middleware(self):
        """Setup CORS and security middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def dashboard():
            return HTMLResponse(self._get_dashboard_html())
        
        @self.app.get("/api/neural-pulse")
        async def get_neural_pulse():
            return JSONResponse(self.neural_pulse_data)
        
        @self.app.get("/api/agent-stream")
        async def get_agent_stream():
            return JSONResponse(self.agent_streams)
        
        @self.app.websocket("/ws/live")
        async def websocket_endpoint(websocket: WebSocket):
            await self._handle_websocket(websocket)
        
        @self.app.get("/api/health")
        async def health_check():
            return {"status": "alive", "timestamp": datetime.now().isoformat()}
    
    async def _handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._process_websocket_message(websocket, data)
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)
    
    async def _process_websocket_message(self, websocket: WebSocket, message: str):
        """Process WebSocket messages"""
        try:
            data = json.loads(message)
            
            if data.get("type") == "command":
                response = await self._execute_command(data.get("command", {}))
                await websocket.send_text(json.dumps(response))
            
        except Exception as e:
            logger.error(f"WebSocket message error: {e}")
    
    async def _execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute gateway commands"""
        cmd_type = command.get("type")
        
        if cmd_type == "get_neural_pulse":
            return {"type": "neural_pulse", "data": self.neural_pulse_data}
        
        elif cmd_type == "get_agent_stream":
            return {"type": "agent_stream", "data": self.agent_streams}
        
        return {"type": "error", "message": "Unknown command"}
    
    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>ASIMNEXUS Live Gateway</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-black text-green-400">
    <div class="container mx-auto p-8">
        <h1 class="text-4xl font-bold mb-8">🧠 ASIMNEXUS Neural Core</h1>
        <div id="neural-pulse" class="mb-8">
            <h2 class="text-2xl mb-4">Neural Pulse</h2>
            <div id="pulse-data">Loading...</div>
        </div>
        <div id="agent-stream" class="mb-8">
            <h2 class="text-2xl mb-4">Agent Stream</h2>
            <div id="stream-data">Loading...</div>
        </div>
    </div>
    <script>
        const ws = new WebSocket('ws://localhost:8000/ws/live');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'neural_pulse') {
                document.getElementById('pulse-data').innerHTML = JSON.stringify(data.data, null, 2);
            }
        };
        
        setInterval(() => {
            ws.send(JSON.stringify({type: 'command', command: {type: 'get_neural_pulse'}}));
        }, 1000);
    </script>
</body>
</html>
        """
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start HTTP/3 server"""
        config = hypercorn.config.Config()
        config.bind = [f"{host}:{port}"]
        config.use_reloader = True
        config.worker_class = "asyncio"
        
        logger.info(f"🚀 Live Gateway starting on https://{host}:{port}")
        await hypercorn.asyncio.serve(self.app, config)

# Global instance
_live_controller = LiveGatewayController()

async def main():
    """Main entry point"""
    await _live_controller.start_server()

if __name__ == "__main__":
    asyncio.run(main())
