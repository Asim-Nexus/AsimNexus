
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Mesh Layer - WebRTC Connections
==========================================
Peer-to-peer connections using WebRTC
For both LAN and global mesh
"""

import logging
import json
from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger("ASIM_MESH_WEBRTC")

class ConnectionState(Enum):
    """WebRTC connection states"""
    NEW = "new"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    CLOSED = "closed"

@dataclass
class PeerConnection:
    """WebRTC peer connection"""
    peer_id: str
    connection_id: str
    state: ConnectionState
    created_at: datetime
    last_activity: datetime
    data_channel_open: bool = False
    ice_servers: List[str] = None
    local_description: Dict = None
    remote_description: Dict = None

class WebRTCMesh:
    """
    WebRTC Mesh Network Manager
    
    Features:
    - P2P connections between nodes
    - Data channels for messaging
    - ICE server configuration
    - Automatic reconnection
    """
    
    def __init__(self, node_id: str, ice_servers: List[str] = None):
        self.node_id = node_id
        self.ice_servers = ice_servers or [
            "stun:stun.l.google.com:19302",
            "stun:stun1.l.google.com:19302"
        ]
        
        # Active connections
        self.connections: Dict[str, PeerConnection] = {}
        self.connection_handlers: Dict[str, Callable] = {}
        
        # Signaling state (for offer/answer exchange)
        self.pending_offers: Dict[str, Dict] = {}
        self.pending_answers: Dict[str, Dict] = {}
        
        # Message handlers
        self.message_handlers: List[Callable] = []
        
        # Connection monitoring
        self._monitor_task = None
        
        logger.info(f"🌐 WebRTC Mesh initialized: {node_id[:16]}")
    
    async def create_offer(self, peer_id: str) -> Dict:
        """Create WebRTC offer for peer"""
        connection_id = f"{self.node_id}_{peer_id}_{datetime.now().timestamp()}"
        
        # In real implementation, would use aiortc or similar
        # For now, create mock offer
        offer = {
            'type': 'offer',
            'sdp': f"mock_sdp_offer_{connection_id}",
            'ice_candidates': self.ice_servers,
            'connection_id': connection_id
        }
        
        self.pending_offers[peer_id] = offer
        
        # Create connection record
        self.connections[connection_id] = PeerConnection(
            peer_id=peer_id,
            connection_id=connection_id,
            state=ConnectionState.CONNECTING,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            local_description=offer
        )
        
        logger.info(f"Created offer for {peer_id[:16]}")
        return offer
    
    async def handle_offer(self, peer_id: str, offer: Dict) -> Dict:
        """Handle incoming offer and create answer"""
        connection_id = offer.get('connection_id')
        
        if not connection_id:
            connection_id = f"{peer_id}_{self.node_id}_{datetime.now().timestamp()}"
        
        # Create answer
        answer = {
            'type': 'answer',
            'sdp': f"mock_sdp_answer_{connection_id}",
            'ice_candidates': self.ice_servers,
            'connection_id': connection_id
        }
        
        self.pending_answers[peer_id] = answer
        
        # Create connection record
        self.connections[connection_id] = PeerConnection(
            peer_id=peer_id,
            connection_id=connection_id,
            state=ConnectionState.CONNECTING,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            remote_description=offer,
            local_description=answer
        )
        
        logger.info(f"Created answer for {peer_id[:16]}")
        
        # Simulate connection establishment
        await self._establish_connection(connection_id)
        
        return answer
    
    async def handle_answer(self, peer_id: str, answer: Dict) -> bool:
        """Handle incoming answer to our offer"""
        connection_id = answer.get('connection_id')
        
        if connection_id not in self.connections:
            logger.error(f"Unknown connection: {connection_id}")
            return False
        
        conn = self.connections[connection_id]
        conn.remote_description = answer
        conn.state = ConnectionState.CONNECTED
        conn.data_channel_open = True
        conn.last_activity = datetime.now()
        
        logger.info(f"Connection established: {peer_id[:16]}")
        
        # Notify handlers
        self._notify_connection_handlers(connection_id, 'connected')
        
        return True
    
    async def _establish_connection(self, connection_id: str):
        """Simulate connection establishment"""
        # In real implementation, would wait for ICE negotiation
        await asyncio.sleep(0.5)
        
        if connection_id in self.connections:
            conn = self.connections[connection_id]
            conn.state = ConnectionState.CONNECTED
            conn.data_channel_open = True
            conn.last_activity = datetime.now()
            
            self._notify_connection_handlers(connection_id, 'connected')
    
    async def send_message(self, connection_id: str, message: Dict) -> bool:
        """Send message over data channel"""
        if connection_id not in self.connections:
            logger.error(f"Connection not found: {connection_id}")
            return False
        
        conn = self.connections[connection_id]
        
        if conn.state != ConnectionState.CONNECTED or not conn.data_channel_open:
            logger.error(f"Data channel not open: {connection_id}")
            return False
        
        # In real implementation, would send via WebRTC data channel
        # For now, just log
        logger.debug(f"Sent message to {conn.peer_id[:16]}: {message.get('type')}")
        conn.last_activity = datetime.now()
        
        return True
    
    async def broadcast(self, message: Dict, exclude: Set[str] = None) -> Dict:
        """Broadcast message to all connected peers"""
        exclude = exclude or set()
        
        sent = 0
        failed = 0
        
        for conn_id, conn in self.connections.items():
            if conn.peer_id in exclude:
                continue
            
            if conn.state == ConnectionState.CONNECTED:
                success = await self.send_message(conn_id, message)
                if success:
                    sent += 1
                else:
                    failed += 1
        
        return {
            'sent': sent,
            'failed': failed,
            'total_peers': len(self.connections)
        }
    
    def on_message(self, handler: Callable):
        """Register message handler"""
        self.message_handlers.append(handler)
    
    def on_connection(self, handler: Callable):
        """Register connection state handler"""
        self.connection_handlers[handler.__name__] = handler
    
    def _notify_connection_handlers(self, connection_id: str, event: str):
        """Notify connection event handlers"""
        for name, handler in self.connection_handlers.items():
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(connection_id, event))
                else:
                    handler(connection_id, event)
            except Exception as e:
                logger.error(f"Handler error: {e}")
    
    def close_connection(self, connection_id: str):
        """Close specific connection"""
        if connection_id in self.connections:
            conn = self.connections[connection_id]
            conn.state = ConnectionState.CLOSED
            conn.data_channel_open = False
            
            self._notify_connection_handlers(connection_id, 'closed')
            
            del self.connections[connection_id]
            logger.info(f"Closed connection: {connection_id[:16]}")
    
    def get_connection(self, peer_id: str) -> Optional[PeerConnection]:
        """Get connection to specific peer"""
        for conn in self.connections.values():
            if conn.peer_id == peer_id and conn.state == ConnectionState.CONNECTED:
                return conn
        return None
    
    def get_all_connections(self) -> List[PeerConnection]:
        """Get all active connections"""
        return [
            conn for conn in self.connections.values()
            if conn.state == ConnectionState.CONNECTED
        ]
    
    async def _monitor_connections(self):
        """Monitor connections and reconnect if needed"""
        while True:
            try:
                now = datetime.now()
                
                for conn_id, conn in list(self.connections.items()):
                    # Check for stale connections
                    stale_threshold = 300  # 5 minutes
                    if (now - conn.last_activity).seconds > stale_threshold:
                        if conn.state == ConnectionState.CONNECTED:
                            logger.warning(f"Stale connection: {conn.peer_id[:16]}")
                            conn.state = ConnectionState.DISCONNECTED
                            self._notify_connection_handlers(conn_id, 'disconnected')
                    
                    # Reconnect if disconnected
                    if conn.state == ConnectionState.DISCONNECTED:
                        logger.info(f"Attempting reconnect: {conn.peer_id[:16]}")
                        # Would trigger reconnect here
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(30)
    
    def start_monitoring(self):
        """Start connection monitoring"""
        self._monitor_task = asyncio.create_task(self._monitor_connections())
        logger.info("Connection monitoring started")
    
    def stop_monitoring(self):
        """Stop connection monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            logger.info("Connection monitoring stopped")
    
    def get_stats(self) -> Dict:
        """Get WebRTC mesh statistics"""
        states = {}
        for conn in self.connections.values():
            s = conn.state.value
            states[s] = states.get(s, 0) + 1
        
        return {
            'node_id': self.node_id[:16] + "...",
            'total_connections': len(self.connections),
            'connected': len(self.get_all_connections()),
            'states': states,
            'ice_servers': len(self.ice_servers),
            'monitoring': self._monitor_task is not None
        }

_webrtc = None

def get_webrtc_mesh(node_id: str = None) -> WebRTCMesh:
    """Get WebRTC mesh singleton"""
    global _webrtc
    if _webrtc is None:
        _webrtc = WebRTCMesh(node_id or "unknown")
    return _webrtc

if __name__ == "__main__":
    import sys
    
    async def main():
        mesh = get_webrtc_mesh("test_node")
        
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            # Create test connection
            offer = await mesh.create_offer("peer_123")
            print(f"Created offer: {offer['connection_id'][:16]}")
            
            # Get stats
            print(f"Stats: {mesh.get_stats()}")
            
        elif len(sys.argv) > 1 and sys.argv[1] == "stats":
            print(json.dumps(mesh.get_stats(), indent=2))
            
        else:
            print("Usage: python webrtc_mesh.py [test|stats]")
    
    asyncio.run(main())
