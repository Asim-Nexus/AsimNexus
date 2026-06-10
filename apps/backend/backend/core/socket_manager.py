#!/usr/bin/env python3
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
🔌 ASIMNEXUS Socket Manager - Real-time Connectivity
Phase 1: WebSocket & Socket.io Implementation
Real-time Frontend & Backend Sync - 100% WebSocket Support
"""

import asyncio
import json
import logging
import socketio
import uvicorn
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class SocketConnection:
    """Socket connection data structure"""
    user_id: str
    socket_id: str
    connected_at: datetime
    last_activity: datetime
    status: str = 'active'

class SocketManager:
    """Real-time Socket.io Manager for ASIMNEXUS"""
    
    def __init__(self):
        self.logger = logging.getLogger("ASIMNEXUS_SocketManager")
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True
        )
        self.connections: Dict[str, SocketConnection] = {}
        self.rooms: Dict[str, List[str]] = {}
        self.message_history: List[Dict] = []
        self.setup_socket_events()
        
    def setup_socket_events(self):
        """Setup all Socket.io event handlers"""
        
        @self.sio.event
        async def connect(sid, environ):
            """Client connection handler"""
            self.logger.info(f"🔌 Client connected: {sid}")
            
        @self.sio.event
        async def disconnect(sid):
            """Client disconnection handler"""
            self.logger.info(f"🔌 Client disconnected: {sid}")
            if sid in self.connections:
                del self.connections[sid]
                
        @self.sio.event
        async def join_room(sid, data):
            """Room join handler"""
            room = data.get('room', 'default')
            user_id = data.get('user_id', 'anonymous')
            
            # Add to room
            self.sio.enter_room(sid, room)
            
            # Store connection
            self.connections[sid] = SocketConnection(
                user_id=user_id,
                socket_id=sid,
                connected_at=datetime.now(),
                last_activity=datetime.now(),
                status='active'
            )
            
            # Add to room list
            if room not in self.rooms:
                self.rooms[room] = []
            if sid not in self.rooms[room]:
                self.rooms[room].append(sid)
                
            self.logger.info(f"🔌 User {user_id} joined room {room}")
            
            # Broadcast to room
            await self.sio.emit('user_joined', {
                'user_id': user_id,
                'socket_id': sid,
                'timestamp': datetime.now().isoformat(),
                'room_users': len(self.rooms.get(room, []))
            }, room=room)
            
        @self.sio.event
        async def leave_room(sid, data):
            """Room leave handler"""
            room = data.get('room', 'default')
            user_id = data.get('user_id', 'anonymous')
            
            # Remove from room
            if room in self.rooms and sid in self.rooms[room]:
                self.rooms[room].remove(sid)
                
            self.logger.info(f"🔌 User {user_id} left room {room}")
            
            # Broadcast to room
            await self.sio.emit('user_left', {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'room_users': len(self.rooms.get(room, []))
            }, room=room)
            
        @self.sio.event
        async def send_message(sid, data):
            """Message sending handler"""
            room = data.get('room', 'default')
            user_id = data.get('user_id', 'anonymous')
            message = data.get('message', '')
            
            # Store message in history
            message_data = {
                'user_id': user_id,
                'socket_id': sid,
                'message': message,
                'room': room,
                'timestamp': datetime.now().isoformat(),
                'type': 'user_message'
            }
            self.message_history.append(message_data)
            
            # Update last activity
            if sid in self.connections:
                self.connections[sid].last_activity = datetime.now()
                
            self.logger.info(f"🔌 Message from {user_id} in room {room}: {message[:50]}...")
            
            # Broadcast to room
            await self.sio.emit('new_message', message_data, room=room)
            
        @self.sio.event
        async def ai_response(sid, data):
            """AI response handler"""
            room = data.get('room', 'default')
            message = data.get('message', '')
            
            # Store AI response
            ai_message = {
                'user_id': 'ASIMNEXUS_AI',
                'socket_id': sid,
                'message': message,
                'room': room,
                'timestamp': datetime.now().isoformat(),
                'type': 'ai_response'
            }
            self.message_history.append(ai_message)
            
            self.logger.info(f"🤖 AI Response in room {room}: {message[:50]}...")
            
            # Broadcast AI response
            await self.sio.emit('ai_response', ai_message, room=room)
            
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            'active_connections': len(self.connections),
            'active_rooms': len(self.rooms),
            'total_messages': len(self.message_history),
            'connections': [
                {
                    'user_id': conn.user_id,
                    'socket_id': conn.socket_id,
                    'connected_at': conn.connected_at.isoformat(),
                    'last_activity': conn.last_activity.isoformat(),
                    'status': conn.status
                }
                for conn in self.connections.values()
            ],
            'rooms': {
                room: {
                    'user_count': len(users),
                    'users': users
                }
                for room, users in self.rooms.items()
            },
            'timestamp': datetime.now().isoformat()
        }
        
    async def broadcast_system_status(self):
        """Broadcast system status to all connected clients"""
        status = await self.get_connection_status()
        await self.sio.emit('system_status', status)
        
    async def send_to_user(self, user_id: str, message: str, room: str = 'default'):
        """Send message to specific user"""
        # Find user's socket
        user_socket = None
        for sid, conn in self.connections.items():
            if conn.user_id == user_id and conn.status == 'active':
                user_socket = sid
                break
                
        if user_socket:
            await self.sio.emit('private_message', {
                'message': message,
                'from': 'system',
                'timestamp': datetime.now().isoformat()
            }, room=user_socket)
            return True
        return False
        
    async def get_room_history(self, room: str) -> List[Dict]:
        """Get message history for specific room"""
        return [
            msg for msg in self.message_history 
            if msg.get('room') == room
        ][-50:]  # Last 50 messages
        
    def start_server(self, host: str = "0.0.0.0", port: int = 8765):
        """Start the WebSocket server"""
        self.logger.info(f"🚀 Starting Socket.io Server on {host}:{port}")
        
        # Add status endpoint
        app = socketio.ASGIApp(self.sio)
        
        @app.get('/status')
        async def status():
            return await self.get_connection_status()
            
        @app.get('/history/<room>')
        async def get_history(room: str):
            return await self.get_room_history(room)
            
        # Start server
        uvicorn.run(app, host=host, port=port, log_level="info")
        
    async def cleanup_inactive_connections(self):
        """Clean up inactive connections"""
        current_time = datetime.now()
        inactive_threshold = 300  # 5 minutes
        
        inactive_sockets = []
        for sid, conn in self.connections.items():
            time_diff = (current_time - conn.last_activity).total_seconds()
            if time_diff > inactive_threshold:
                inactive_sockets.append(sid)
                
        # Remove inactive connections
        for sid in inactive_sockets:
            if sid in self.connections:
                del self.connections[sid]
                await self.sio.emit('timeout', {'message': 'Connection timed out'}, room=sid)
                
        self.logger.info(f"🧹 Cleaned up {len(inactive_sockets)} inactive connections")

# Global socket manager instance
socket_manager = SocketManager()

if __name__ == "__main__":
    print("🔌 ASIMNEXUS Socket Manager Starting...")
    socket_manager.start_server()
