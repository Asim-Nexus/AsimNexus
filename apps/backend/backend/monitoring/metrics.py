#!/usr/bin/env python3
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
📊 ASIMNEXUS Metrics Monitor
Phase 4: Mobile & Production Optimization
CPU/RAM usage & AI API response time tracking for Performance Monitoring
"""

import asyncio
import psutil
import time
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import redis

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_usage_percent: float = 0.0
    network_io: Dict[str, float] = None
    active_connections: int = 0
    ai_response_time: float = 0.0
    error_rate: float = 0.0
    uptime_seconds: int = 0
    timestamp: datetime = None

@dataclass
class PerformanceAlert:
    """Performance alert structure"""
    alert_type: str = ""
    severity: str = "info"
    message: str = ""
    threshold: float = 0.0
    current_value: float = 0.0
    timestamp: datetime = None

class MetricsMonitor:
    """ASIMNEXUS Performance Monitoring System"""
    
    def __init__(self):
        self.logger = logging.getLogger("ASIMNEXUS_MetricsMonitor")
        self.metrics = SystemMetrics()
        self.alerts: List[PerformanceAlert] = []
        self.monitoring_active = False
        self.redis_client = self._init_redis()
        self.start_time = datetime.now()
        
    def _init_redis(self):
        """Initialize Redis for metrics storage"""
        try:
            return redis.Redis(
                host='localhost',
                port=6379,
                db=2,  # Metrics DB
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
        except Exception as e:
            self.logger.error(f"🚨 Redis initialization failed: {e}")
            return None
            
    async def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network metrics
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Update metrics
            self.metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_io=network_io,
                active_connections=self._get_active_connections(),
                ai_response_time=await self._get_ai_response_time(),
                error_rate=await self._get_error_rate(),
                uptime_seconds=int((datetime.now() - self.start_time).total_seconds()),
                timestamp=datetime.now()
            )
            
            # Check for performance alerts
            await self._check_performance_alerts()
            
            return self.metrics
            
        except Exception as e:
            self.logger.error(f"🚨 Metrics collection failed: {e}")
            return self.metrics
            
    def _get_active_connections(self) -> int:
        """Get active connection count"""
        # This would integrate with socket manager
        return 0  # Placeholder - would connect to socket_manager
        
    async def _get_ai_response_time(self) -> float:
        """Get average AI response time"""
        # This would integrate with AI system
        return 0.5  # Placeholder - would measure actual AI response times
        
    async def _get_error_rate(self) -> float:
        """Get current error rate"""
        # This would integrate with error tracking
        return 0.02  # Placeholder - 2% error rate
        
    async def _check_performance_alerts(self):
        """Check for performance issues and create alerts"""
        alerts = []
        
        # CPU alert
        if self.metrics.cpu_percent > 80:
            alerts.append(PerformanceAlert(
                alert_type="cpu_high",
                severity="warning",
                message=f"CPU usage is {self.metrics.cpu_percent:.1f}%",
                threshold=80.0,
                current_value=self.metrics.cpu_percent,
                timestamp=datetime.now()
            ))
            
        # Memory alert
        if self.metrics.memory_percent > 85:
            alerts.append(PerformanceAlert(
                alert_type="memory_high",
                severity="warning",
                message=f"Memory usage is {self.metrics.memory_percent:.1f}%",
                threshold=85.0,
                current_value=self.metrics.memory_percent,
                timestamp=datetime.now()
            ))
            
        # Disk alert
        if self.metrics.disk_usage_percent > 90:
            alerts.append(PerformanceAlert(
                alert_type="disk_high",
                severity="critical",
                message=f"Disk usage is {self.metrics.disk_usage_percent:.1f}%",
                threshold=90.0,
                current_value=self.metrics.disk_usage_percent,
                timestamp=datetime.now()
            ))
            
        # AI response time alert
        if self.metrics.ai_response_time > 2.0:
            alerts.append(PerformanceAlert(
                alert_type="ai_slow",
                severity="warning",
                message=f"AI response time is {self.metrics.ai_response_time:.2f}s",
                threshold=2.0,
                current_value=self.metrics.ai_response_time,
                timestamp=datetime.now()
            ))
            
        # Add new alerts to list
        if alerts:
            self.alerts.extend(alerts)
            
            # Store in Redis
            if self.redis_client:
                for alert in alerts:
                    self.redis_client.lpush('performance_alerts', json.dumps({
                        **alert.__dict__,
                        'timestamp': datetime.now().isoformat()
                    }))
                    self.redis_client.ltrim('performance_alerts', 0, 99)  # Keep last 100 alerts
                    
            # Log alerts
            for alert in alerts:
                self.logger.warning(f"⚠️ Performance Alert: {alert.message}")
                
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return {
            'current_metrics': self.metrics.__dict__,
            'active_alerts': len([a for a in self.alerts if (datetime.now() - a.timestamp).total_seconds() < 3600]),
            'total_alerts_24h': len(self.alerts),
            'performance_score': self._calculate_performance_score(),
            'health_status': self._get_health_status(),
            'recommendations': self._get_performance_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
        
    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        score = 100.0
        
        # CPU impact
        if self.metrics.cpu_percent > 80:
            score -= 20
        elif self.metrics.cpu_percent > 60:
            score -= 10
            
        # Memory impact
        if self.metrics.memory_percent > 85:
            score -= 25
        elif self.metrics.memory_percent > 70:
            score -= 15
            
        # Disk impact
        if self.metrics.disk_usage_percent > 90:
            score -= 30
        elif self.metrics.disk_usage_percent > 80:
            score -= 15
            
        # AI response time impact
        if self.metrics.ai_response_time > 2.0:
            score -= 20
        elif self.metrics.ai_response_time > 1.0:
            score -= 10
            
        return max(0.0, score)
        
    def _get_health_status(self) -> str:
        """Get system health status"""
        score = self._calculate_performance_score()
        
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "fair"
        elif score >= 60:
            return "poor"
        else:
            return "critical"
            
    def _get_performance_recommendations(self) -> List[str]:
        """Get performance improvement recommendations"""
        recommendations = []
        
        if self.metrics.cpu_percent > 80:
            recommendations.append("Consider scaling CPU resources or optimizing CPU-intensive tasks")
            
        if self.metrics.memory_percent > 85:
            recommendations.append("Increase memory allocation or implement memory optimization")
            
        if self.metrics.disk_usage_percent > 90:
            recommendations.append("Clean up disk space or expand storage capacity")
            
        if self.metrics.ai_response_time > 2.0:
            recommendations.append("Optimize AI model performance or implement caching")
            
        if self.metrics.error_rate > 0.05:
            recommendations.append("Investigate and fix error sources")
            
        return recommendations if recommendations else ["System performance is optimal"]
        
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.logger.info("📊 Performance monitoring started")
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        self.logger.info("📊 Performance monitoring stopped")

# Global metrics monitor instance
metrics_monitor = MetricsMonitor()

if __name__ == "__main__":
    print("📊 ASIMNEXUS Metrics Monitor Starting...")
    
    async def demo():
        monitor = MetricsMonitor()
        monitor.start_monitoring()
        
        while True:
            metrics = await monitor.collect_metrics()
            summary = await monitor.get_metrics_summary()
            
            print(f"📊 Performance Score: {summary['performance_score']:.1f}/100")
            print(f"🏥 Health Status: {summary['health_status']}")
            print(f"⚠️ Active Alerts: {summary['active_alerts']}")
            
            await asyncio.sleep(30)  # Update every 30 seconds
    
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\n📊 Performance monitoring stopped")
