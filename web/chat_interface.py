
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""Web-based Chat Interface for ASIMNEXUS."""
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import asyncio
import json
from datetime import datetime
from typing import Dict, Optional
import uuid


class ChatInterface:
    """Web-based chat interface for ASIMNEXUS."""
    
    def __init__(self, asim_nexus_instance, host='0.0.0.0', port=3000):
        self.app = Flask(__name__)
        self.app.secret_key = str(uuid.uuid4())
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.asim = asim_nexus_instance
        self.host = host
        self.port = port
        
        # Setup routes
        self._setup_routes()
        self._setup_socket_events()
    
    def _setup_routes(self):
        """Setup HTTP routes."""
        
        @self.app.route('/')
        def index():
            """Main chat page."""
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
            return render_template('chat.html')
        
        @self.app.route('/api/chat', methods=['POST'])
        def api_chat():
            """REST API endpoint for chat."""
            data = request.json
            user_message = data.get('message', '')
            session_id = data.get('session_id', session.get('session_id', str(uuid.uuid4())))
            
            if not user_message:
                return jsonify({'error': 'No message provided'}), 400
            
            # Process through ASIMNEXUS
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.asim.process(user_message, {'session_id': session_id})
                )
                loop.close()
                
                return jsonify({
                    'response': result.get('response', 'No response'),
                    'request_id': result.get('request_id'),
                    'intent': result.get('intent'),
                    'confidence': result.get('confidence'),
                    'total_time_ms': result.get('total_time_ms'),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stats')
        def api_stats():
            """Get system statistics."""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                stats = loop.run_until_complete(self.asim.get_stats())
                loop.close()
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _setup_socket_events(self):
        """Setup WebSocket events."""
        
        @self.socketio.on('connect')
        def handle_connect():
            emit('connected', {'status': 'connected', 'timestamp': datetime.now().isoformat()})
        
        @self.socketio.on('message')
        def handle_message(data):
            """Handle incoming chat message via WebSocket."""
            user_message = data.get('message', '')
            session_id = data.get('session_id', str(uuid.uuid4()))
            
            if not user_message:
                emit('error', {'message': 'No message provided'})
                return
            
            # Emit typing indicator
            emit('typing', {'status': 'ASIM is thinking...'})
            
            try:
                # Process through ASIMNEXUS
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.asim.process(user_message, {'session_id': session_id})
                )
                loop.close()
                
                # Send response
                emit('response', {
                    'message': result.get('response'),
                    'request_id': result.get('request_id'),
                    'intent': result.get('intent'),
                    'confidence': result.get('confidence'),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                emit('error', {'message': str(e)})
    
    def run(self, debug=False):
        """Run the web server."""
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)


# HTML template (should be in templates/chat.html)
CHAT_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ASIMNEXUS Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header { 
            padding: 20px; 
            background: #16213e; 
            border-bottom: 2px solid #0f3460;
        }
        .header h1 { color: #e94560; }
        .chat-container { 
            flex: 1; 
            overflow-y: auto; 
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .message { 
            max-width: 80%; 
            padding: 12px 18px; 
            border-radius: 18px;
            line-height: 1.5;
        }
        .user-message { 
            align-self: flex-end; 
            background: #e94560; 
            color: white;
        }
        .bot-message { 
            align-self: flex-start; 
            background: #16213e; 
            border: 1px solid #0f3460;
        }
        .input-container { 
            padding: 20px; 
            background: #16213e;
            display: flex;
            gap: 10px;
        }
        #messageInput { 
            flex: 1; 
            padding: 15px;
            border: none;
            border-radius: 25px;
            background: #0f3460;
            color: white;
            font-size: 16px;
        }
        #sendBtn { 
            padding: 15px 30px;
            border: none;
            border-radius: 25px;
            background: #e94560;
            color: white;
            cursor: pointer;
            font-size: 16px;
        }
        #sendBtn:hover { background: #ff6b6b; }
        .typing { 
            font-style: italic; 
            color: #888;
            padding: 10px;
        }
        .metadata {
            font-size: 11px;
            color: #888;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 ASIMNEXUS</h1>
        <p>Super Intelligent Autonomous Digital Clone</p>
    </div>
    
    <div class="chat-container" id="chatContainer">
        <div class="message bot-message">
            👋 Namaste! I am ASIMNEXUS, your AI assistant. How can I help you today?
        </div>
    </div>
    
    <div class="typing" id="typingIndicator" style="display:none;"></div>
    
    <div class="input-container">
        <input type="text" id="messageInput" placeholder="Type your message..." />
        <button id="sendBtn">Send</button>
    </div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const typingIndicator = document.getElementById('typingIndicator');
        
        let sessionId = localStorage.getItem('asim_session_id');
        if (!sessionId) {
            sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2);
            localStorage.setItem('asim_session_id', sessionId);
        }
        
        function addMessage(text, isUser, metadata = {}) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            msgDiv.textContent = text;
            
            if (metadata.intent) {
                const metaDiv = document.createElement('div');
                metaDiv.className = 'metadata';
                metaDiv.textContent = `Intent: ${metadata.intent} | Confidence: ${(metadata.confidence * 100).toFixed(0)}% | Time: ${metadata.time_ms}ms`;
                msgDiv.appendChild(metaDiv);
            }
            
            chatContainer.appendChild(msgDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function sendMessage() {
            const text = messageInput.value.trim();
            if (!text) return;
            
            addMessage(text, true);
            messageInput.value = '';
            
            socket.emit('message', { message: text, session_id: sessionId });
        }
        
        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        
        socket.on('typing', (data) => {
            typingIndicator.textContent = data.status;
            typingIndicator.style.display = 'block';
        });
        
        socket.on('response', (data) => {
            typingIndicator.style.display = 'none';
            addMessage(data.message, false, {
                intent: data.intent,
                confidence: data.confidence,
                time_ms: data.total_time_ms
            });
        });
        
        socket.on('error', (data) => {
            typingIndicator.style.display = 'none';
            addMessage('❌ Error: ' + data.message, false);
        });
    </script>
</body>
</html>
'''
