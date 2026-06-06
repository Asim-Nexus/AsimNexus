
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""Admin Dashboard for ASIMNEXUS Monitoring."""
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import asyncio
import json


class AdminDashboard:
    """Admin dashboard for system monitoring and management."""
    
    def __init__(self, asim_nexus_instance, audit_logger=None, host='0.0.0.0', port=8080):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.asim = asim_nexus_instance
        self.audit_logger = audit_logger
        self.host = host
        self.port = port
        
        self._setup_routes()
        self._setup_socket_events()
        self._start_background_tasks()
    
    def _setup_routes(self):
        """Setup dashboard routes."""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/stats')
        def stats():
            """Get system statistics."""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                stats = loop.run_until_complete(self.asim.get_stats())
                loop.close()
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/logs')
        def logs():
            """Get recent logs."""
            if not self.audit_logger:
                return jsonify({'logs': []})
            
            recent_logs = self.audit_logger.audit_logs[-100:]  # Last 100
            return jsonify({
                'logs': [
                    {
                        'log_id': log.log_id,
                        'action': log.action.value,
                        'user': log.user,
                        'resource': log.resource,
                        'details': log.details,
                        'timestamp': log.timestamp,
                        'ip_address': log.ip_address
                    }
                    for log in recent_logs
                ]
            })
        
        @self.app.route('/api/agents')
        def agents():
            """Get agent status."""
            # Placeholder - would integrate with agent system
            return jsonify({
                'agents': [
                    {'id': 'planner_001', 'role': 'planner', 'status': 'idle'},
                    {'id': 'executor_001', 'role': 'executor', 'status': 'busy'},
                    {'id': 'analyst_001', 'role': 'analyst', 'status': 'idle'},
                ]
            })
        
        @self.app.route('/api/tasks')
        def tasks():
            """Get running tasks."""
            return jsonify({
                'tasks': [
                    {'id': 'task_001', 'status': 'running', 'progress': 45},
                    {'id': 'task_002', 'status': 'pending', 'progress': 0},
                    {'id': 'task_003', 'status': 'completed', 'progress': 100},
                ]
            })
    
    def _setup_socket_events(self):
        """Setup real-time updates."""
        
        @self.socketio.on('connect')
        def handle_connect():
            emit('connected', {'status': 'dashboard_connected'})
    
    def _start_background_tasks(self):
        """Start background monitoring."""
        def emit_stats():
            """Emit stats periodically."""
            while True:
                try:
                    self.socketio.sleep(5)  # Every 5 seconds
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    stats = loop.run_until_complete(self.asim.get_stats())
                    loop.close()
                    self.socketio.emit('stats_update', stats)
                except Exception as e:
                    print(f"Stats emission error: {e}")
        
        self.socketio.start_background_task(emit_stats)
    
    def run(self, debug=False):
        """Run dashboard server."""
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)


DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ASIMNEXUS Admin Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f0f1e;
            color: #fff;
        }
        .header { 
            padding: 20px 40px; 
            background: linear-gradient(90deg, #1a1a3e, #2d2d5a);
            border-bottom: 3px solid #e94560;
        }
        .header h1 { color: #e94560; }
        .container { 
            display: grid; 
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            padding: 20px 40px;
        }
        .card {
            background: #1a1a3e;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #2d2d5a;
        }
        .card h3 { color: #e94560; margin-bottom: 15px; }
        .metric { 
            display: flex; 
            justify-content: space-between; 
            padding: 10px 0;
            border-bottom: 1px solid #2d2d5a;
        }
        .metric:last-child { border-bottom: none; }
        .metric-value { color: #4ecca3; font-weight: bold; }
        .status-online { color: #4ecca3; }
        .status-busy { color: #ffc107; }
        .status-offline { color: #e94560; }
        .logs-container {
            grid-column: span 2;
            max-height: 400px;
            overflow-y: auto;
        }
        .log-entry {
            font-family: monospace;
            font-size: 12px;
            padding: 8px;
            border-bottom: 1px solid #2d2d5a;
            display: flex;
            gap: 15px;
        }
        .log-time { color: #888; }
        .log-action { color: #4ecca3; }
        .log-user { color: #ffc107; }
        .agent-grid {
            grid-column: span 2;
        }
        .agent-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: #2d2d5a;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .task-bar {
            height: 20px;
            background: #2d2d5a;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .task-progress {
            height: 100%;
            background: linear-gradient(90deg, #e94560, #4ecca3);
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔧 ASIMNEXUS Admin Dashboard</h1>
        <p>System Monitoring & Management</p>
    </div>
    
    <div class="container">
        <!-- Cache Stats -->
        <div class="card">
            <h3>📦 Cache Statistics</h3>
            <div id="cacheStats">
                <div class="metric">
                    <span>L1 Cache Size</span>
                    <span class="metric-value" id="l1Size">-</span>
                </div>
                <div class="metric">
                    <span>L1 Hit Rate</span>
                    <span class="metric-value" id="l1HitRate">-</span>
                </div>
                <div class="metric">
                    <span>L2 Available</span>
                    <span class="metric-value" id="l2Available">-</span>
                </div>
            </div>
        </div>
        
        <!-- Cost Stats -->
        <div class="card">
            <h3>💰 Cost Tracking</h3>
            <div id="costStats">
                <div class="metric">
                    <span>Daily Cost</span>
                    <span class="metric-value" id="dailyCost">-</span>
                </div>
                <div class="metric">
                    <span>Monthly Cost</span>
                    <span class="metric-value" id="monthlyCost">-</span>
                </div>
                <div class="metric">
                    <span>Budget Remaining</span>
                    <span class="metric-value" id="budgetRemaining">-</span>
                </div>
            </div>
        </div>
        
        <!-- Agents -->
        <div class="card agent-grid">
            <h3>🤖 Agent Status</h3>
            <div id="agentList">
                <div class="agent-card">
                    <div>
                        <strong>planner_001</strong>
                        <div style="font-size:12px;color:#888">Planner Agent</div>
                    </div>
                    <span class="status-online">● Idle</span>
                </div>
                <div class="agent-card">
                    <div>
                        <strong>executor_001</strong>
                        <div style="font-size:12px;color:#888">Executor Agent</div>
                    </div>
                    <span class="status-busy">● Busy</span>
                </div>
                <div class="agent-card">
                    <div>
                        <strong>analyst_001</strong>
                        <div style="font-size:12px;color:#888">Analyst Agent</div>
                    </div>
                    <span class="status-online">● Idle</span>
                </div>
            </div>
        </div>
        
        <!-- Tasks -->
        <div class="card">
            <h3>⚙️ Running Tasks</h3>
            <div id="taskList">
                <div class="metric">
                    <span>task_001</span>
                    <span class="status-busy">Running (45%)</span>
                </div>
                <div class="task-bar">
                    <div class="task-progress" style="width:45%"></div>
                </div>
                <div class="metric">
                    <span>task_002</span>
                    <span>Pending</span>
                </div>
                <div class="task-bar">
                    <div class="task-progress" style="width:0%"></div>
                </div>
            </div>
        </div>
        
        <!-- Logs -->
        <div class="card logs-container">
            <h3>📋 Recent Audit Logs</h3>
            <div id="logContainer">
                <div class="log-entry">
                    <span class="log-time">2024-01-15 10:30:45</span>
                    <span class="log-action">EXECUTE</span>
                    <span class="log-user">user_001</span>
                    <span>file_read: config.json</span>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        
        socket.on('stats_update', (stats) => {
            // Update cache stats
            if (stats.cache) {
                document.getElementById('l1Size').textContent = stats.cache.l1?.size || '-';
                document.getElementById('l1HitRate').textContent = 
                    stats.cache.l1?.hit_rate ? (stats.cache.l1.hit_rate * 100).toFixed(1) + '%' : '-';
                document.getElementById('l2Available').textContent = 
                    stats.cache.l2_available ? 'Yes' : 'No';
            }
            
            // Update cost stats
            if (stats.llm_cost) {
                document.getElementById('dailyCost').textContent = '$' + 
                    (stats.llm_cost.daily_cost || 0).toFixed(4);
                document.getElementById('monthlyCost').textContent = '$' + 
                    (stats.llm_cost.monthly_cost || 0).toFixed(2);
                const remaining = (stats.llm_cost.daily_limit || 10) - 
                    (stats.llm_cost.daily_cost || 0);
                document.getElementById('budgetRemaining').textContent = '$' + remaining.toFixed(2);
            }
        });
        
        // Fetch initial data
        fetch('/api/stats').then(r => r.json()).then(data => {
            if (data.cache) {
                document.getElementById('l1Size').textContent = data.cache.l1?.size || '-';
            }
        });
        
        fetch('/api/logs').then(r => r.json()).then(data => {
            const container = document.getElementById('logContainer');
            container.innerHTML = data.logs.map(log => `
                <div class="log-entry">
                    <span class="log-time">${new Date(log.timestamp).toLocaleString()}</span>
                    <span class="log-action">${log.action.toUpperCase()}</span>
                    <span class="log-user">${log.user}</span>
                    <span>${log.resource}: ${log.details}</span>
                </div>
            `).join('');
        });
    </script>
</body>
</html>
'''
