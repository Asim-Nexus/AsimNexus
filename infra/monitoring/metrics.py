#!/usr/bin/env python3
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Monitoring System - Real-time Metrics and Observability
================================================================

Based on industry best practices from enterprise monitoring systems
Implements Prometheus metrics, Grafana dashboards, and system monitoring

Storage-layer metrics added for:
  - Redis (cache layer)
  - ClickHouse (analytics)
  - PostgreSQL (OLTP)
  - MinIO (object storage)
  - ChromaDB (vector)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import time

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  Storage service connection settings (mirrors backend/health.py)   #
# ------------------------------------------------------------------ #

import os
STORAGE_CONFIG = {
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "timeout": 3,
    },
    "clickhouse": {
        "host": os.getenv("CLICKHOUSE_HOST", "localhost"),
        "http_port": int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123")),
        "timeout": 5,
    },
    "postgres": {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "user": os.getenv("POSTGRES_USER", "asimnexus"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
        "dbname": os.getenv("POSTGRES_DB", "asimnexus"),
        "timeout": 5,
    },
    "minio": {
        "host": os.getenv("MINIO_HOST", "localhost"),
        "api_port": int(os.getenv("MINIO_API_PORT", "9000")),
        "timeout": 5,
    },
    "chromadb": {
        "host": os.getenv("CHROMADB_HOST", "localhost"),
        "port": int(os.getenv("CHROMADB_PORT", "8000")),
        "timeout": 5,
    },
}

STORAGE_SERVICES = list(STORAGE_CONFIG.keys())


@dataclass
class MetricValue:
    """Metric value with timestamp"""
    value: float
    timestamp: datetime
    labels: Optional[Dict[str, str]] = None


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    timestamp: datetime


class MetricsCollector:
    """
    ASIMNEXUS Metrics Collector

    Features:
    - Prometheus metrics collection
    - System performance monitoring
    - Custom application metrics
    - Storage-layer metrics (Redis, ClickHouse, PostgreSQL, MinIO, ChromaDB)
    - Real-time dashboard data
    - Alert thresholds
    - Historical data storage
    """

    def __init__(self):
        self.registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None
        self.metrics: Dict[str, List[MetricValue]] = {}
        self.custom_metrics: Dict[str, Any] = {}
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}

        # Initialize Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self._init_prometheus_metrics()
            self._init_storage_metrics()

        # Default alert thresholds (including storage)
        self._set_default_thresholds()

        # System monitoring
        self.system_metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000

        # Storage metrics cache (latest values for dashboard)
        self.storage_cache: Dict[str, Dict[str, Any]] = {}

        logger.info("Metrics Collector initialized")

    # ------------------------------------------------------------------ #
    #  Prometheus metric initialisation                                   #
    # ------------------------------------------------------------------ #

    def _init_prometheus_metrics(self):
        """Initialize core Prometheus metrics."""
        # Request metrics
        self.request_counter = Counter(
            'asimnexus_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        self.request_duration = Histogram(
            'asimnexus_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        # System metrics
        self.cpu_usage = Gauge(
            'asimnexus_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        self.memory_usage = Gauge(
            'asimnexus_memory_usage_percent',
            'Memory usage percentage',
            registry=self.registry
        )
        # Application metrics
        self.active_agents = Gauge(
            'asimnexus_active_agents',
            'Number of active agents',
            registry=self.registry
        )
        self.memory_items = Gauge(
            'asimnexus_memory_items_total',
            'Total number of memory items',
            registry=self.registry
        )

    def _init_storage_metrics(self):
        """Initialize storage-layer Prometheus metrics."""

        # -- Reachability / uptime ---------------------------------- #
        self.storage_up = Gauge(
            'asimmers_storage_up',
            'Storage service reachability (1=up, 0=down)',
            ['service'],
            registry=self.registry,
        )

        # -- Query latency ------------------------------------------- #
        self.storage_query_latency = Histogram(
            'asimmers_storage_query_latency_ms',
            'Storage query/operation latency in milliseconds',
            ['service', 'operation'],
            buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000],
            registry=self.registry,
        )

        # -- Active connections -------------------------------------- #
        self.storage_connections_active = Gauge(
            'asimmers_storage_connections_active',
            'Active connections to the storage service',
            ['service'],
            registry=self.registry,
        )

        # -- Error counter ------------------------------------------- #
        self.storage_errors_total = Counter(
            'asimmers_storage_errors_total',
            'Total number of storage operation errors',
            ['service', 'error_type'],
            registry=self.registry,
        )

        # -- Disk / data usage --------------------------------------- #
        self.storage_disk_usage_bytes = Gauge(
            'asimmers_storage_disk_usage_bytes',
            'Storage service data directory size in bytes',
            ['service'],
            registry=self.registry,
        )

        logger.info("✅ Storage-layer Prometheus metrics initialized")

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                          #
    # ------------------------------------------------------------------ #

    async def initialize(self):
        """Initialize the metrics collector and start background loops."""
        logger.info("Initializing Metrics Collector...")
        self._set_default_thresholds()

        # Start system monitoring loop
        if PSUTIL_AVAILABLE:
            asyncio.create_task(self._system_monitoring_loop())

        # Start storage metrics collection loop
        asyncio.create_task(self._storage_metrics_loop())

        logger.info("✅ Metrics Collector initialized")

    def _set_default_thresholds(self):
        """Set default alert thresholds (including storage)."""
        self.alert_thresholds = {
            'cpu_usage': {'warning': 70.0, 'critical': 90.0},
            'memory_usage': {'warning': 80.0, 'critical': 95.0},
            'disk_usage': {'warning': 80.0, 'critical': 95.0},
            'response_time': {'warning': 2.0, 'critical': 5.0},
            'error_rate': {'warning': 0.05, 'critical': 0.1},
            # Storage-specific thresholds
            'storage_redis_up': {'warning': 0, 'critical': 0},
            'storage_clickhouse_up': {'warning': 0, 'critical': 0},
            'storage_postgres_up': {'warning': 0, 'critical': 0},
            'storage_minio_up': {'warning': 0, 'critical': 0},
            'storage_chromadb_up': {'warning': 0, 'critical': 0},
            'storage_latency_ms': {'warning': 200.0, 'critical': 1000.0},
            'storage_connections': {'warning': 80, 'critical': 150},
            'storage_disk_usage_bytes': {'warning': 10 * 1024**3, 'critical': 50 * 1024**3},  # 10GB / 50GB
        }

    # ------------------------------------------------------------------ #
    #  Background collection loops                                        #
    # ------------------------------------------------------------------ #

    async def _system_monitoring_loop(self):
        """Background system monitoring loop (every 10s)."""
        while True:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(30)

    async def _storage_metrics_loop(self):
        """Background storage metrics collection loop (every 15s)."""
        while True:
            try:
                await self._collect_storage_metrics()
                await asyncio.sleep(15)
            except Exception as e:
                logger.error(f"Storage metrics collection error: {e}")
                await asyncio.sleep(30)

    # ------------------------------------------------------------------ #
    #  System metric collection                                           #
    # ------------------------------------------------------------------ #

    async def _collect_system_metrics(self):
        """Collect system performance metrics via psutil."""
        if not PSUTIL_AVAILABLE:
            return
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            system_metrics = SystemMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv,
                },
                process_count=len(psutil.pids()),
                timestamp=datetime.now()
            )

            self.system_metrics_history.append(system_metrics)
            if len(self.system_metrics_history) > self.max_history_size:
                self.system_metrics_history.pop(0)

            if PROMETHEUS_AVAILABLE:
                self.cpu_usage.set(cpu_percent)
                self.memory_usage.set(memory.percent)

            await self._check_alerts(system_metrics)

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

    # ------------------------------------------------------------------ #
    #  Storage metric collection                                          #
    # ------------------------------------------------------------------ #

    async def _collect_storage_metrics(self):
        """Collect metrics from all storage services and push to Prometheus."""
        if not PROMETHEUS_AVAILABLE:
            return

        for service in STORAGE_SERVICES:
            try:
                up, details = await self._ping_storage(service)
                self.storage_up.labels(service=service).set(1 if up else 0)

                if up:
                    self.storage_connections_active.labels(
                        service=service
                    ).set(details.get("connections", 0))

                    self.storage_disk_usage_bytes.labels(
                        service=service
                    ).set(details.get("disk_bytes", 0))

                # Cache for dashboard
                self.storage_cache[service] = {
                    "up": up,
                    "timestamp": datetime.now().isoformat(),
                    **details,
                }

                # If down, record an error
                if not up:
                    self.storage_errors_total.labels(
                        service=service,
                        error_type="connection_failed",
                    ).inc()

            except Exception as e:
                logger.error(f"Storage metrics error for {service}: {e}")
                self.storage_up.labels(service=service).set(0)
                self.storage_errors_total.labels(
                    service=service,
                    error_type="collection_exception",
                ).inc()

    async def _ping_storage(self, service: str):
        """
        Ping a storage service and return (up: bool, details: dict).

        Uses the same endpoint logic as backend/health.py probes.
        """
        details: Dict[str, Any] = {}

        if service not in STORAGE_CONFIG:
            return False, {"error": f"Unknown storage service: {service}"}

        cfg = STORAGE_CONFIG[service]

        try:
            if service == "redis":
                import redis as r
                client = r.Redis(
                    host=cfg["host"], port=cfg["port"],
                    socket_connect_timeout=cfg["timeout"],
                    decode_responses=True,
                )
                client.ping()
                info = client.info()
                details["connections"] = info.get("connected_clients", 0)
                details["disk_bytes"] = info.get("used_memory", 0)
                details["version"] = info.get("redis_version", "")
                client.close()
                return True, details

            elif service == "clickhouse":
                import requests
                url = f"http://{cfg['host']}:{cfg['http_port']}/ping"
                resp = requests.get(url, timeout=cfg["timeout"])
                if resp.status_code != 200:
                    return False, {"error": f"HTTP {resp.status_code}"}
                # Get version & uptime
                q_url = f"http://{cfg['host']}:{cfg['http_port']}/?query=SELECT version(),uptime()"
                q = requests.get(q_url, timeout=cfg["timeout"])
                parts = q.text.strip().split("\t") if q.ok else []
                details["version"] = parts[0] if len(parts) >= 1 else ""
                details["disk_bytes"] = 0  # CH returns disk via system.disks
                details["connections"] = 0
                return True, details

            elif service == "postgres":
                import psycopg2
                conn = psycopg2.connect(
                    host=cfg["host"], port=cfg["port"],
                    user=cfg["user"], password=cfg["password"],
                    dbname=cfg["dbname"], connect_timeout=cfg["timeout"],
                )
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM pg_stat_activity")
                details["connections"] = cur.fetchone()[0]
                cur.execute("SELECT pg_database_size(current_database())")
                details["disk_bytes"] = cur.fetchone()[0]
                cur.execute("SELECT version()")
                details["version"] = cur.fetchone()[0].split(",")[0]
                conn.close()
                return True, details

            elif service == "minio":
                import requests
                url = f"http://{cfg['host']}:{cfg['api_port']}/minio/health/live"
                resp = requests.get(url, timeout=cfg["timeout"])
                if resp.status_code != 200:
                    return False, {"error": f"HTTP {resp.status_code}"}
                details["connections"] = 0
                details["disk_bytes"] = 0
                details["version"] = ""
                return True, details

            elif service == "chromadb":
                import requests
                url = f"http://{cfg['host']}:{cfg['port']}/api/v1/heartbeat"
                resp = requests.get(url, timeout=cfg["timeout"])
                if resp.status_code != 200:
                    return False, {"error": f"HTTP {resp.status_code}"}
                details["connections"] = 0
                details["disk_bytes"] = 0
                details["version"] = ""
                return True, details

            return False, {"error": f"Unknown service: {service}"}

        except ImportError as e:
            return False, {"error": f"Missing library: {e}"}
        except Exception as e:
            return False, {"error": str(e)}

    # ------------------------------------------------------------------ #
    #  Alert checking (existing, extended with storage)                   #
    # ------------------------------------------------------------------ #

    async def _check_alerts(self, metrics: SystemMetrics):
        """Check for alert conditions."""
        alerts = []

        # CPU alert
        if metrics.cpu_usage >= self.alert_thresholds['cpu_usage']['critical']:
            alerts.append({
                'type': 'critical', 'metric': 'cpu_usage',
                'value': metrics.cpu_usage,
                'threshold': self.alert_thresholds['cpu_usage']['critical'],
                'message': f'CPU usage is critically high: {metrics.cpu_usage:.1f}%'
            })
        elif metrics.cpu_usage >= self.alert_thresholds['cpu_usage']['warning']:
            alerts.append({
                'type': 'warning', 'metric': 'cpu_usage',
                'value': metrics.cpu_usage,
                'threshold': self.alert_thresholds['cpu_usage']['warning'],
                'message': f'CPU usage is high: {metrics.cpu_usage:.1f}%'
            })

        # Memory alert
        if metrics.memory_usage >= self.alert_thresholds['memory_usage']['critical']:
            alerts.append({
                'type': 'critical', 'metric': 'memory_usage',
                'value': metrics.memory_usage,
                'threshold': self.alert_thresholds['memory_usage']['critical'],
                'message': f'Memory usage is critically high: {metrics.memory_usage:.1f}%'
            })
        elif metrics.memory_usage >= self.alert_thresholds['memory_usage']['warning']:
            alerts.append({
                'type': 'warning', 'metric': 'memory_usage',
                'value': metrics.memory_usage,
                'threshold': self.alert_thresholds['memory_usage']['warning'],
                'message': f'Memory usage is high: {metrics.memory_usage:.1f}%'
            })

        # Storage alerts
        for svc in STORAGE_SERVICES:
            cached = self.storage_cache.get(svc, {})
            if not cached.get("up", False):
                alerts.append({
                    'type': 'critical',
                    'metric': f'storage_{svc}_up',
                    'value': 0,
                    'threshold': 1,
                    'message': f'{svc} storage service is DOWN'
                })

        for alert in alerts:
            logger.warning(f"ALERT: {alert['message']}")

    # ------------------------------------------------------------------ #
    #  Request recording (existing)                                       #
    # ------------------------------------------------------------------ #

    async def record_request(self, endpoint: str, status: str, duration: Optional[float] = None):
        """Record request metrics."""
        try:
            if PROMETHEUS_AVAILABLE:
                self.request_counter.labels(
                    method='GET', endpoint=endpoint, status=status
                ).inc()
                if duration is not None:
                    self.request_duration.labels(
                        method='GET', endpoint=endpoint
                    ).observe(duration)
            self._add_metric_value('requests', 1, {'endpoint': endpoint, 'status': status})
            if duration is not None:
                self._add_metric_value('response_time', duration, {'endpoint': endpoint})
        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")

    def _add_metric_value(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Add metric value to storage."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(MetricValue(value=value, timestamp=datetime.now(), labels=labels))
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]

    async def update_agent_count(self, count: int):
        """Update active agents count."""
        try:
            if PROMETHEUS_AVAILABLE:
                self.active_agents.set(count)
            self._add_metric_value('active_agents', count)
        except Exception as e:
            logger.error(f"Failed to update agent count: {e}")

    async def update_memory_items_count(self, count: int):
        """Update memory items count."""
        try:
            if PROMETHEUS_AVAILABLE:
                self.memory_items.set(count)
            self._add_metric_value('memory_items', count)
        except Exception as e:
            logger.error(f"Failed to update memory items count: {e}")

    # ------------------------------------------------------------------ #
    #  Metric accessors                                                   #
    # ------------------------------------------------------------------ #

    async def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        try:
            latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None
            request_metrics = self.metrics.get('requests', [])
            total_requests = len(request_metrics)
            error_requests = [r for r in request_metrics if r.labels and r.labels.get('status') == 'error']
            error_rate = len(error_requests) / max(total_requests, 1)
            response_times = self.metrics.get('response_time', [])
            avg_response_time = sum(r.value for r in response_times) / max(len(response_times), 1)

            prometheus_metrics = {}
            if PROMETHEUS_AVAILABLE:
                try:
                    prometheus_metrics = generate_latest(self.registry).decode('utf-8')
                except Exception as e:
                    logger.error(f"Failed to generate Prometheus metrics: {e}")

            return {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_usage': latest_system.cpu_usage if latest_system else 0,
                    'memory_usage': latest_system.memory_usage if latest_system else 0,
                    'disk_usage': latest_system.disk_usage if latest_system else 0,
                    'process_count': latest_system.process_count if latest_system else 0
                },
                'application': {
                    'total_requests': total_requests,
                    'error_rate': error_rate,
                    'avg_response_time': avg_response_time,
                    'active_agents': int(self.active_agents._value.get()) if PROMETHEUS_AVAILABLE and hasattr(self.active_agents, '_value') else 0,
                    'memory_items': int(self.memory_items._value.get()) if PROMETHEUS_AVAILABLE and hasattr(self.memory_items, '_value') else 0
                },
                'storage': self.storage_cache,
                'prometheus_metrics': prometheus_metrics,
                'alerts': await self._get_current_alerts()
            }
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {'error': str(e)}

    async def _get_current_alerts(self) -> List[Dict[str, Any]]:
        """Get current active alerts."""
        alerts = []
        if not self.system_metrics_history:
            return alerts
        latest = self.system_metrics_history[-1]

        if latest.cpu_usage >= self.alert_thresholds['cpu_usage']['warning']:
            alerts.append({
                'metric': 'cpu_usage', 'value': latest.cpu_usage,
                'threshold': self.alert_thresholds['cpu_usage']['warning'],
                'severity': 'warning' if latest.cpu_usage < self.alert_thresholds['cpu_usage']['critical'] else 'critical'
            })
        if latest.memory_usage >= self.alert_thresholds['memory_usage']['warning']:
            alerts.append({
                'metric': 'memory_usage', 'value': latest.memory_usage,
                'threshold': self.alert_thresholds['memory_usage']['warning'],
                'severity': 'warning' if latest.memory_usage < self.alert_thresholds['memory_usage']['critical'] else 'critical'
            })
        for svc in STORAGE_SERVICES:
            cached = self.storage_cache.get(svc, {})
            if not cached.get("up", False):
                alerts.append({
                    'metric': f'storage_{svc}_up', 'value': 0,
                    'threshold': 1, 'severity': 'critical',
                })
        return alerts

    async def get_metric_history(self, metric_name: str, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get metric history for specified time period."""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            if metric_name == 'system':
                return [
                    {'timestamp': m.timestamp.isoformat(), 'cpu_usage': m.cpu_usage,
                     'memory_usage': m.memory_usage, 'disk_usage': m.disk_usage,
                     'process_count': m.process_count}
                    for m in self.system_metrics_history if m.timestamp >= cutoff_time
                ]
            metric_values = self.metrics.get(metric_name, [])
            return [
                {'timestamp': m.timestamp.isoformat(), 'value': m.value, 'labels': m.labels}
                for m in metric_values if m.timestamp >= cutoff_time
            ]
        except Exception as e:
            logger.error(f"Failed to get metric history: {e}")
            return []

    async def set_alert_threshold(self, metric: str, warning: float, critical: float):
        """Set alert threshold for metric."""
        self.alert_thresholds[metric] = {'warning': warning, 'critical': critical}
        logger.info(f"Updated alert thresholds for {metric}: warning={warning}, critical={critical}")

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for visualization."""
        try:
            current_metrics = await self.get_metrics()
            system_history = await self.get_metric_history('system', 60)
            request_history = await self.get_metric_history('requests', 60)
            cpu_trend = self._calculate_trend([m['cpu_usage'] for m in system_history[-10:]]) if system_history else 'stable'
            memory_trend = self._calculate_trend([m['memory_usage'] for m in system_history[-10:]]) if system_history else 'stable'
            return {
                'current': current_metrics,
                'history': {'system': system_history, 'requests': request_history},
                'trends': {'cpu': cpu_trend, 'memory': memory_trend},
                'storage': self.storage_cache,
                'performance': {
                    'avg_response_time': current_metrics.get('application', {}).get('avg_response_time', 0),
                    'error_rate': current_metrics.get('application', {}).get('error_rate', 0),
                    'total_requests': current_metrics.get('application', {}).get('total_requests', 0)
                }
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {'error': str(e)}

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values."""
        if len(values) < 2:
            return 'stable'
        recent_avg = sum(values[-3:]) / min(3, len(values))
        older_avg = sum(values[-6:-3]) / max(3, len(values) - 3)
        if recent_avg > older_avg * 1.1:
            return 'increasing'
        elif recent_avg < older_avg * 0.9:
            return 'decreasing'
        return 'stable'

    async def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format."""
        try:
            metrics = await self.get_metrics()
            if format.lower() == 'json':
                return json.dumps(metrics, indent=2, default=str)
            elif format.lower() == 'prometheus' and PROMETHEUS_AVAILABLE:
                return generate_latest(self.registry).decode('utf-8')
            return json.dumps(metrics, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return json.dumps({'error': str(e)})

    async def stop(self):
        """Stop the metrics collector."""
        logger.info("Stopping Metrics Collector...")
        self.metrics.clear()
        self.system_metrics_history.clear()
        self.storage_cache.clear()
        logger.info("Metrics Collector stopped")


# Global instance
metrics_instance: Optional[MetricsCollector] = None


async def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global metrics_instance
    if not metrics_instance:
        metrics_instance = MetricsCollector()
        await metrics_instance.initialize()
    return metrics_instance


if __name__ == "__main__":
    async def test_metrics():
        """Test metrics collector."""
        collector = MetricsCollector()
        await collector.initialize()

        # Record some test metrics
        await collector.record_request('/test', 'success', 0.5)
        await collector.update_agent_count(5)
        await collector.update_memory_items_count(100)

        # Let storage metrics collect once
        await asyncio.sleep(2)
        await collector._collect_storage_metrics()

        metrics = await collector.get_metrics()
        print(f"Metrics: {json.dumps(metrics, indent=2, default=str)}")
        print(f"Storage cache: {json.dumps(collector.storage_cache, indent=2, default=str)}")

        await collector.stop()

    asyncio.run(test_metrics())
