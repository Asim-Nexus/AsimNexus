#!/usr/bin/env python3
"""
STATUS: REAL — v1.0.1 observability dashboard
ASIMNEXUS Observability Dashboard
Real-time monitoring of Redis vs Memory status, system metrics,
and storage-layer services (ClickHouse, PostgreSQL, MinIO, ChromaDB, Redis).

Metric names standardized to: asim.<service>.<metric_name>
Service ownership tags: mesh, storage, security, consensus, os_control
Alert cooldown: minimum time between repeated alerts
"""
import asyncio
import time
import json
import os
from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# ------------------------------------------------------------------ #
#  Severity levels for incidents                                     #
# ------------------------------------------------------------------ #


class Severity(Enum):
    CRITICAL = "CRITICAL"  # Service down, data loss
    HIGH = "HIGH"          # Degraded but operational
    MEDIUM = "MEDIUM"      # Non-critical issue
    LOW = "LOW"            # Informational


# Default cooldown between repeated alerts (seconds)
DEFAULT_ALERT_COOLDOWN_SECONDS = 300


# ------------------------------------------------------------------ #
#  Service ownership tags                                             #
# ------------------------------------------------------------------ #

SERVICE_TAGS = {
    "redis": "storage",
    "clickhouse": "storage",
    "postgres": "storage",
    "minio": "storage",
    "chromadb": "storage",
    "mesh": "mesh",
    "dht": "mesh",
    "crdt": "mesh",
    "consensus": "consensus",
    "security": "security",
    "os_control": "os_control",
}


# ------------------------------------------------------------------ #
#  Storage service connection config (mirrors backend/health.py)     #
# ------------------------------------------------------------------ #

STORAGE_CONFIG = {
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "timeout": 3,
        "display": "Redis (Cache)",
    },
    "clickhouse": {
        "host": os.getenv("CLICKHOUSE_HOST", "localhost"),
        "http_port": int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123")),
        "timeout": 5,
        "display": "ClickHouse (Analytics)",
    },
    "postgres": {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "user": os.getenv("POSTGRES_USER", "asimnexus"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
        "dbname": os.getenv("POSTGRES_DB", "asimnexus"),
        "timeout": 5,
        "display": "PostgreSQL (OLTP)",
    },
    "minio": {
        "host": os.getenv("MINIO_HOST", "localhost"),
        "api_port": int(os.getenv("MINIO_API_PORT", "9000")),
        "timeout": 5,
        "display": "MinIO (Object Storage)",
    },
    "chromadb": {
        "host": os.getenv("CHROMADB_HOST", "localhost"),
        "port": int(os.getenv("CHROMADB_PORT", "8000")),
        "timeout": 5,
        "display": "ChromaDB (Vector)",
    },
}

STORAGE_SERVICES = list(STORAGE_CONFIG.keys())


@dataclass
class StorageStatus:
    """Per-service storage status snapshot."""
    service: str
    up: bool = False
    latency_ms: float = 0.0
    connections: int = 0
    disk_bytes: int = 0
    version: str = ""
    error: str = ""
    last_checked: str = ""
    service_tag: str = "storage"  # Service ownership tag
    metric_prefix: str = "asim.storage"  # Standardized metric prefix


@dataclass
class SystemMetrics:
    """Real-time system metrics with storage layer."""
    timestamp: str
    # Legacy fields — standardized prefix: asim.system.*
    redis_available: bool
    memory_usage: int
    active_locks: int
    lock_contentions: int
    state_operations: int
    cache_hits: int
    redis_fallbacks: int
    # New storage fields
    storage_statuses: Dict[str, StorageStatus] = field(default_factory=dict)

    def metric_name(self, base: str) -> str:
        """Generate standardized metric name: asim.<service>.<metric_name>"""
        return f"asim.system.{base}"

    @staticmethod
    def storage_metric(service: str, metric: str) -> str:
        """Generate standardized storage metric name."""
        return f"asim.storage.{service}.{metric}"


class ObservabilityDashboard:
    """Real-time monitoring dashboard for ASIMNEXUS with storage layer visibility.

    Features:
    - Service ownership tags (mesh, storage, security, consensus, os_control)
    - Standardized metric naming (asim.<service>.<metric_name>)
    - Incident severity levels (CRITICAL, HIGH, MEDIUM, LOW)
    - Alert cooldown to reduce noise
    """

    def __init__(self, alert_cooldown_seconds: int = DEFAULT_ALERT_COOLDOWN_SECONDS):
        self.state_manager = None
        self.lock_manager = None
        self.metrics_history: List[SystemMetrics] = []
        self.is_running = False
        self.monitoring_task = None
        self.alert_cooldown_seconds = alert_cooldown_seconds
        self._last_alert_times: Dict[str, float] = {}

        # Lazy-import state manager to avoid circular imports
        try:
            from core.state_manager import get_state_manager, StateNamespace
            from core.lock_manager import get_lock_manager
            self.state_manager = get_state_manager()
            self.lock_manager = get_lock_manager()
        except ImportError:
            pass

    async def start_monitoring(self, update_interval: int = 5):
        """Start real-time monitoring."""
        print("🔍 Starting ASIMNEXUS Observability Dashboard...")
        self.is_running = True

        if self.lock_manager:
            self.lock_manager.initialize()

        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop(update_interval)
        )
        print(f"✅ Dashboard started - Update interval: {update_interval}s")

    async def stop_monitoring(self):
        """Stop monitoring."""
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
        print("🛑 Dashboard stopped")

    async def _monitoring_loop(self, interval: int):
        """Main monitoring loop."""
        while self.is_running:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-100:]
                self._display_dashboard(metrics)
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(interval)

    async def _collect_metrics(self) -> SystemMetrics:
        """Collect current system and storage metrics."""
        try:
            # Legacy metrics (state-manager Redis)
            redis_available = False
            memory_usage = 0
            active_locks = 0
            lock_contentions = 0
            state_operations = 0
            cache_hits = 0
            redis_fallbacks = 0

            if self.state_manager and hasattr(self.state_manager, '_redis'):
                try:
                    redis_available = self.state_manager._redis.available
                except Exception:
                    pass

            if self.lock_manager:
                try:
                    lock_stats = self.lock_manager.get_lock_statistics()
                    active_locks = lock_stats.get('active_locks', 0)
                    lock_contentions = lock_stats.get('conflicts_prevented', 0)
                except Exception:
                    pass

            if self.state_manager:
                state_stats = getattr(self.state_manager, '_stats', {})
                state_operations = state_stats.get('reads', 0) + state_stats.get('writes', 0)
                cache_hits = state_stats.get('cache_hits', 0)
                redis_fallbacks = state_stats.get('redis_fallbacks', 0)

            memory_usage = len(self.metrics_history) * 1024

        except Exception:
            redis_available = False
            memory_usage = 0
            active_locks = 0
            lock_contentions = 0
            state_operations = 0
            cache_hits = 0
            redis_fallbacks = 0

        # Collect storage service statuses
        storage_statuses = {}
        for svc in STORAGE_SERVICES:
            storage_statuses[svc] = await self._check_storage(svc)

        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            redis_available=redis_available,
            memory_usage=memory_usage,
            active_locks=active_locks,
            lock_contentions=lock_contentions,
            state_operations=state_operations,
            cache_hits=cache_hits,
            redis_fallbacks=redis_fallbacks,
            storage_statuses=storage_statuses,
        )

    async def _check_storage(self, service: str) -> StorageStatus:
        """
        Ping a storage service and return a StorageStatus snapshot.
        Mirrors the probe logic in backend/health.py and monitoring/metrics.py.
        """
        svc_tag = SERVICE_TAGS.get(service, "storage")
        prefix = f"asim.{svc_tag}"
        status = StorageStatus(
            service=service,
            last_checked=datetime.now().isoformat(),
            service_tag=svc_tag,
            metric_prefix=prefix,
        )
        cfg = STORAGE_CONFIG[service]

        try:
            if service == "redis":
                import redis as r
                client = r.Redis(
                    host=cfg["host"], port=cfg["port"],
                    socket_connect_timeout=cfg["timeout"],
                    decode_responses=True,
                )
                t0 = time.time()
                client.ping()
                status.latency_ms = (time.time() - t0) * 1000
                info = client.info()
                status.up = True
                status.connections = info.get("connected_clients", 0)
                status.disk_bytes = info.get("used_memory", 0)
                status.version = info.get("redis_version", "")
                client.close()

            elif service == "clickhouse":
                import requests
                url = f"http://{cfg['host']}:{cfg['http_port']}/ping"
                t0 = time.time()
                resp = requests.get(url, timeout=cfg["timeout"])
                status.latency_ms = (time.time() - t0) * 1000
                if resp.status_code == 200:
                    status.up = True
                    q = requests.get(
                        f"http://{cfg['host']}:{cfg['http_port']}/?query=SELECT version()",
                        timeout=cfg["timeout"],
                    )
                    status.version = q.text.strip() if q.ok else ""
                else:
                    status.error = f"HTTP {resp.status_code}"

            elif service == "postgres":
                import psycopg2
                t0 = time.time()
                conn = psycopg2.connect(
                    host=cfg["host"], port=cfg["port"],
                    user=cfg["user"], password=cfg["password"],
                    dbname=cfg["dbname"], connect_timeout=cfg["timeout"],
                )
                status.latency_ms = (time.time() - t0) * 1000
                cur = conn.cursor()
                cur.execute("SELECT version()")
                status.version = cur.fetchone()[0].split(",")[0]
                cur.execute("SELECT COUNT(*) FROM pg_stat_activity")
                status.connections = cur.fetchone()[0]
                cur.execute("SELECT pg_database_size(current_database())")
                status.disk_bytes = cur.fetchone()[0]
                status.up = True
                conn.close()

            elif service == "minio":
                import requests
                url = f"http://{cfg['host']}:{cfg['api_port']}/minio/health/live"
                t0 = time.time()
                resp = requests.get(url, timeout=cfg["timeout"])
                status.latency_ms = (time.time() - t0) * 1000
                if resp.status_code == 200:
                    status.up = True
                else:
                    status.error = f"HTTP {resp.status_code}"

            elif service == "chromadb":
                import requests
                url = f"http://{cfg['host']}:{cfg['port']}/api/v1/heartbeat"
                t0 = time.time()
                resp = requests.get(url, timeout=cfg["timeout"])
                status.latency_ms = (time.time() - t0) * 1000
                if resp.status_code == 200:
                    status.up = True
                else:
                    status.error = f"HTTP {resp.status_code}"

        except ImportError as e:
            status.error = f"Missing library: {e}"
        except Exception as e:
            status.error = str(e)

        return status

    # ------------------------------------------------------------------ #
    #  Dashboard display                                                  #
    # ------------------------------------------------------------------ #

    def _display_dashboard(self, metrics: SystemMetrics):
        """Display real-time dashboard with storage status."""
        print("\n" + "=" * 90)
        print(f"🔍 ASIMNEXUS OBSERVABILITY DASHBOARD - {metrics.timestamp[:19]}")
        print("=" * 90)

        # Service ownership summary
        print(f"\n🏷️  SERVICE OWNERSHIP TAGS:")
        for svc in STORAGE_SERVICES:
            s = metrics.storage_statuses.get(svc)
            if s:
                print(f"   {svc:15s} → {s.service_tag:15s} | metric: {s.metric_prefix}.{svc}.*")

        # Legacy backend status
        redis_status = "🟢 ONLINE" if metrics.redis_available else "🔴 OFFLINE"
        print(f"\n📊 BACKEND STATUS:")
        print(f"   State Redis: {redis_status}")
        print(f"   Memory: {'🟢 ACTIVE (Fallback)' if not metrics.redis_available else '🟢 ACTIVE'}")
        print(f"   Memory Usage: {metrics.memory_usage:,} bytes")

        # Storage layer status
        print(f"\n🗄️  STORAGE LAYER STATUS:")
        all_up = all(s.up for s in metrics.storage_statuses.values())
        overall = "🟢 ALL ONLINE" if all_up else "🔴 SOME OFFLINE"
        print(f"   Overall: {overall}")
        for svc in STORAGE_SERVICES:
            s = metrics.storage_statuses.get(svc)
            if not s:
                continue
            icon = "🟢" if s.up else "🔴"
            display_name = STORAGE_CONFIG[svc]["display"]
            latency = f"{s.latency_ms:.1f}ms" if s.latency_ms > 0 else "N/A"
            conns = f" | {s.connections} conns" if s.connections else ""
            disk = f" | {self._fmt_bytes(s.disk_bytes)}" if s.disk_bytes else ""
            err = f" | ❌ {s.error}" if s.error else ""
            print(f"   {icon} {display_name:25s} | latency: {latency:8s}{conns}{disk}{err}")

        # Lock Metrics
        print(f"\n🔒 LOCK METRICS:")
        print(f"   Active Locks: {metrics.active_locks}")
        print(f"   Lock Contentions: {metrics.lock_contentions}")
        print(f"   Lock Conflicts Prevented: {metrics.lock_contentions}")

        # State Manager Metrics
        print(f"\n💾 STATE MANAGER METRICS:")
        print(f"   Total Operations: {metrics.state_operations}")
        print(f"   Cache Hits: {metrics.cache_hits}")
        print(f"   Redis Fallbacks: {metrics.redis_fallbacks}")

        # System Health
        health_score = self._calculate_health_score(metrics)
        health_emoji = "🟢" if health_score >= 80 else "🟡" if health_score >= 60 else "🔴"
        print(f"\n🏥 SYSTEM HEALTH: {health_emoji} {health_score}%")

        # Alerts
        alerts = self._check_alerts(metrics)
        if alerts:
            print(f"\n🚨 ALERTS:")
            for alert in alerts:
                print(f"   • {alert}")

    @staticmethod
    def _fmt_bytes(b: int) -> str:
        """Format bytes to human-readable."""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if b < 1024:
                return f"{b:.1f}{unit}"
            b /= 1024
        return f"{b:.1f}PB"

    def _calculate_health_score(self, metrics: SystemMetrics) -> int:
        """Calculate overall system health score including storage."""
        score = 100

        # Redis availability (20% weight)
        if not metrics.redis_available:
            score -= 20

        # Lock contentions (10% weight)
        if metrics.lock_contentions > 10:
            score -= 10
        elif metrics.lock_contentions > 5:
            score -= 5

        # Redis fallbacks (10% weight)
        if metrics.redis_fallbacks > 20:
            score -= 10
        elif metrics.redis_fallbacks > 10:
            score -= 5

        # Cache hit rate (10% weight)
        if metrics.state_operations > 0:
            cache_rate = metrics.cache_hits / metrics.state_operations
            if cache_rate < 0.5:
                score -= 10
            elif cache_rate < 0.7:
                score -= 5

        # Storage services (50% weight — 10% each)
        for svc in STORAGE_SERVICES:
            s = metrics.storage_statuses.get(svc)
            if s and not s.up:
                score -= 10
            elif s and s.latency_ms > 1000:
                score -= 5  # High latency penalty
            elif s and s.latency_ms > 200:
                score -= 2

        return max(0, score)

    def _check_alerts(self, metrics: SystemMetrics) -> List[str]:
        """Check for system and storage alerts with cooldown."""
        alerts = []
        now = time.time()

        def _should_alert(alert_key: str) -> bool:
            """Check if enough time has passed since last alert."""
            last = self._last_alert_times.get(alert_key, 0.0)
            if now - last < self.alert_cooldown_seconds:
                return False
            self._last_alert_times[alert_key] = now
            return True

        # Legacy alerts (with cooldown)
        if not metrics.redis_available:
            if _should_alert("redis_offline"):
                alerts.append(f"[{Severity.CRITICAL.value}] State Redis server is offline — Using memory fallback")
        if metrics.active_locks > 20:
            if _should_alert("high_locks"):
                alerts.append(f"[{Severity.HIGH.value}] High lock count: {metrics.active_locks} locks active")
        if metrics.lock_contentions > 5:
            if _should_alert("lock_contention"):
                alerts.append(f"[{Severity.MEDIUM.value}] Lock contention detected: {metrics.lock_contentions} conflicts")
        if metrics.redis_fallbacks > 10:
            if _should_alert("redis_fallbacks"):
                alerts.append(f"[{Severity.MEDIUM.value}] High Redis fallbacks: {metrics.redis_fallbacks} operations")

        # Storage service alerts (with cooldown + severity)
        for svc in STORAGE_SERVICES:
            s = metrics.storage_statuses.get(svc)
            if s is None:
                continue
            display_name = STORAGE_CONFIG[svc]["display"]
            if not s.up:
                key = f"storage_down_{svc}"
                if _should_alert(key):
                    alerts.append(
                        f"[{Severity.CRITICAL.value}] {display_name} is DOWN"
                        f"{' — ' + s.error if s.error else ''}"
                    )
            elif s.latency_ms > 1000:
                key = f"storage_high_latency_{svc}"
                if _should_alert(key):
                    alerts.append(
                        f"[{Severity.HIGH.value}] {display_name} high latency: {s.latency_ms:.0f}ms"
                    )
            elif s.latency_ms > 200:
                key = f"storage_elevated_latency_{svc}"
                if _should_alert(key):
                    alerts.append(
                        f"[{Severity.MEDIUM.value}] {display_name} elevated latency: {s.latency_ms:.0f}ms"
                    )

        return alerts

    # ------------------------------------------------------------------ #
    #  History export                                                     #
    # ------------------------------------------------------------------ #

    async def get_metrics_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get metrics history for analysis."""
        return [
            {
                'timestamp': m.timestamp,
                'redis_available': m.redis_available,
                'memory_usage': m.memory_usage,
                'active_locks': m.active_locks,
                'lock_contentions': m.lock_contentions,
                'state_operations': m.state_operations,
                'cache_hits': m.cache_hits,
                'redis_fallbacks': m.redis_fallbacks,
                'storage': {
                    svc: {
                        'up': s.up,
                        'latency_ms': s.latency_ms,
                        'connections': s.connections,
                        'disk_bytes': s.disk_bytes,
                        'error': s.error,
                    }
                    for svc, s in m.storage_statuses.items()
                },
            }
            for m in self.metrics_history[-limit:]
        ]

    async def export_metrics(self, filename: str = "asimnexus_metrics.json"):
        """Export metrics to file."""
        history = await self.get_metrics_history()
        with open(filename, 'w') as f:
            json.dump(history, f, indent=2)
        print(f"📊 Metrics exported to {filename}")


# Global dashboard instance
_observability_dashboard = None


def get_observability_dashboard() -> ObservabilityDashboard:
    """Get global observability dashboard instance."""
    global _observability_dashboard
    if _observability_dashboard is None:
        _observability_dashboard = ObservabilityDashboard()
    return _observability_dashboard


async def main():
    """Main function to run the dashboard."""
    dashboard = get_observability_dashboard()
    try:
        await dashboard.start_monitoring(update_interval=5)
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Stopping dashboard...")
    finally:
        await dashboard.stop_monitoring()
        await dashboard.export_metrics()


if __name__ == "__main__":
    asyncio.run(main())
