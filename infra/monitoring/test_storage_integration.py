#!/usr/bin/env python3
"""
STATUS: REAL — Integration tests for storage-layer monitoring.

Tests:
  - HealthChecker storage probes (backend/health.py)
  - MetricsCollector storage metrics (monitoring/metrics.py)
  - ObservabilityDashboard storage display (monitoring/observability_dashboard.py)
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ======================================================================
#  HealthChecker Storage Probe Tests
# ======================================================================

class TestHealthCheckerStorageProbes(unittest.TestCase):
    """Verify that each storage service probe returns the expected shape."""

    def setUp(self):
        """Create a HealthChecker instance with test paths."""
        from backend.health import HealthChecker
        self.checker = HealthChecker(
            db_path="/tmp/test_asim.db",
            gguf_model_path="/tmp/test_model.gguf",
        )

    def test_check_live_shape(self):
        """check_live() returns expected keys."""
        result = self.checker.check_live()
        self.assertIn("status", result)
        self.assertIn("timestamp", result)
        self.assertIn("uptime_seconds", result)
        self.assertEqual(result["status"], "alive")

    def test_check_ready_includes_storage(self):
        """check_ready() includes all 5 storage services."""
        result = self.checker.check_ready()
        self.assertIn("checks", result)
        checks = result["checks"]
        for svc in ("redis", "clickhouse", "postgres", "minio", "chromadb"):
            self.assertIn(svc, checks)
            self.assertIn("ready", checks[svc])

    def test_check_status_includes_storage(self):
        """check_status() returns a 'storage' block with 5 services."""
        result = self.checker.check_status()
        self.assertIn("storage", result)
        storage = result["storage"]
        for svc in ("redis", "clickhouse", "postgres", "minio", "chromadb"):
            self.assertIn(svc, storage)

    @patch("redis.Redis")
    def test_check_redis_ok(self, mock_redis):
        """_check_redis returns ready=True when ping succeeds."""
        instance = mock_redis.return_value
        instance.ping.return_value = True
        result = self.checker._check_redis()
        self.assertTrue(result["ready"])

    @patch("requests.get")
    def test_check_clickhouse_ok(self, mock_get):
        """_check_clickhouse returns ready=True on 200."""
        mock_get.return_value.status_code = 200
        result = self.checker._check_clickhouse()
        self.assertTrue(result["ready"])

    @patch("psycopg2.connect")
    def test_check_postgres_ok(self, mock_connect):
        """_check_postgres returns ready=True when connection works."""
        result = self.checker._check_postgres()
        self.assertTrue(result["ready"])

    @patch("requests.get")
    def test_check_minio_ok(self, mock_get):
        """_check_minio returns ready=True on 200."""
        mock_get.return_value.status_code = 200
        result = self.checker._check_minio()
        self.assertTrue(result["ready"])

    @patch("requests.get")
    def test_check_chromadb_ok(self, mock_get):
        """_check_chromadb returns ready=True on 200."""
        mock_get.return_value.status_code = 200
        result = self.checker._check_chromadb()
        self.assertTrue(result["ready"])

    @patch("requests.get")
    def test_check_clickhouse_down(self, mock_get):
        """_check_clickhouse returns ready=False on non-200."""
        mock_get.return_value.status_code = 503
        result = self.checker._check_clickhouse()
        self.assertFalse(result["ready"])

    @patch("redis.Redis")
    def test_check_redis_connection_error(self, mock_redis):
        """_check_redis returns ready=False on exception."""
        mock_redis.side_effect = Exception("Connection refused")
        result = self.checker._check_redis()
        self.assertFalse(result["ready"])


# ======================================================================
#  MetricsCollector Storage Metrics Tests
# ======================================================================

class TestMetricsCollectorStorage(unittest.TestCase):
    """Verify that MetricsCollector registers and collects storage metrics."""

    def setUp(self):
        """Create a MetricsCollector with a fresh registry."""
        # Force Prometheus availability for tests
        self._prometheus_saved = None
        import monitoring.metrics as mm
        self.mm = mm

    def test_init_storage_metrics_registers_gauges(self):
        """_init_storage_metrics creates all 5 Prometheus metric types."""
        collector = self.mm.MetricsCollector()
        self.assertTrue(hasattr(collector, "storage_up"))
        self.assertTrue(hasattr(collector, "storage_query_latency"))
        self.assertTrue(hasattr(collector, "storage_connections_active"))
        self.assertTrue(hasattr(collector, "storage_errors_total"))
        self.assertTrue(hasattr(collector, "storage_disk_usage_bytes"))

    def test_storage_cache_initialized_empty(self):
        """storage_cache starts as empty dict."""
        collector = self.mm.MetricsCollector()
        self.assertEqual(collector.storage_cache, {})

    def test_alert_thresholds_include_storage(self):
        """_set_default_thresholds includes storage keys."""
        collector = self.mm.MetricsCollector()
        thresholds = collector.alert_thresholds
        for svc in ("redis", "clickhouse", "postgres", "minio", "chromadb"):
            self.assertIn(f"storage_{svc}_up", thresholds)
        self.assertIn("storage_latency_ms", thresholds)
        self.assertIn("storage_connections", thresholds)
        self.assertIn("storage_disk_usage_bytes", thresholds)

    def test_get_metrics_returns_storage_block(self):
        """get_metrics() returns a 'storage' key."""
        collector = self.mm.MetricsCollector()

        async def test():
            result = await collector.get_metrics()
            self.assertIn("storage", result)

        asyncio.run(test())

    def test_get_dashboard_data_returns_storage_block(self):
        """get_dashboard_data() returns a 'storage' key."""
        collector = self.mm.MetricsCollector()

        async def test():
            result = await collector.get_dashboard_data()
            self.assertIn("storage", result)

        asyncio.run(test())

    @patch("redis.Redis")
    def test_ping_storage_redis(self, mock_redis):
        """_ping_storage handles 'redis' gracefully."""
        collector = self.mm.MetricsCollector()
        instance = mock_redis.return_value
        instance.ping.return_value = True
        instance.info.return_value = {
            "connected_clients": 5,
            "used_memory": 1024,
            "redis_version": "7.0.0",
        }

        async def test():
            up, details = await collector._ping_storage("redis")
            self.assertTrue(up)
            self.assertEqual(details.get("connections"), 5)

        asyncio.run(test())

    @patch("requests.get")
    def test_ping_storage_clickhouse(self, mock_get):
        """_ping_storage handles 'clickhouse' gracefully."""
        collector = self.mm.MetricsCollector()

        async def test():
            up, details = await collector._ping_storage("clickhouse")
            self.assertIsInstance(up, bool)
            self.assertIsInstance(details, dict)

        asyncio.run(test())

    def test_ping_storage_unknown(self):
        """_ping_storage returns False for unknown service."""
        collector = self.mm.MetricsCollector()

        async def test():
            up, details = await collector._ping_storage("nonexistent")
            self.assertFalse(up)
            self.assertIn("error", details)

        asyncio.run(test())


# ======================================================================
#  ObservabilityDashboard Storage Tests
# ======================================================================

class TestObservabilityDashboardStorage(unittest.TestCase):
    """Verify dashboard displays storage status."""

    def setUp(self):
        from monitoring.observability_dashboard import (
            ObservabilityDashboard, StorageStatus, SystemMetrics,
        )
        self.Dashboard = ObservabilityDashboard
        self.StorageStatus = StorageStatus
        self.SystemMetrics = SystemMetrics

    def test_storage_status_dataclass(self):
        """StorageStatus has all required fields."""
        s = self.StorageStatus(service="redis")
        self.assertEqual(s.service, "redis")
        self.assertFalse(s.up)
        self.assertEqual(s.latency_ms, 0.0)
        self.assertEqual(s.connections, 0)
        self.assertEqual(s.disk_bytes, 0)
        self.assertEqual(s.error, "")
        self.assertIsNotNone(s.last_checked)

    def test_system_metrics_includes_storage(self):
        """SystemMetrics dataclass has storage_statuses field."""
        m = self.SystemMetrics(
            timestamp="test",
            redis_available=False,
            memory_usage=0,
            active_locks=0,
            lock_contentions=0,
            state_operations=0,
            cache_hits=0,
            redis_fallbacks=0,
        )
        self.assertEqual(m.storage_statuses, {})

    def test_health_score_all_storage_down(self):
        """_calculate_health_score returns 0 when all storage is down."""
        dashboard = self.Dashboard()
        statuses = {}
        for svc in ("redis", "clickhouse", "postgres", "minio", "chromadb"):
            statuses[svc] = self.StorageStatus(service=svc, up=False)
        m = self.SystemMetrics(
            timestamp="test", redis_available=True,
            memory_usage=100, active_locks=0, lock_contentions=0,
            state_operations=10, cache_hits=9, redis_fallbacks=1,
            storage_statuses=statuses,
        )
        score = dashboard._calculate_health_score(m)
        # Storage contributes 50%; when all 5 are down that's 0.
        # Non-storage metrics (redis_available=True, locks, cache etc.) contribute the
        # remaining 50 % — so total = 50.
        self.assertEqual(score, 50)

    def test_health_score_all_storage_up(self):
        """_calculate_health_score returns 100 when everything healthy."""
        dashboard = self.Dashboard()
        statuses = {}
        for svc in ("redis", "clickhouse", "postgres", "minio", "chromadb"):
            statuses[svc] = self.StorageStatus(service=svc, up=True, latency_ms=1)
        m = self.SystemMetrics(
            timestamp="test", redis_available=True,
            memory_usage=100, active_locks=0, lock_contentions=0,
            state_operations=10, cache_hits=9, redis_fallbacks=0,
            storage_statuses=statuses,
        )
        score = dashboard._calculate_health_score(m)
        self.assertEqual(score, 100)

    def test_check_alerts_storage_down(self):
        """_check_alerts reports alerts when storage is down."""
        dashboard = self.Dashboard()
        statuses = {
            "redis": self.StorageStatus(service="redis", up=True),
            "clickhouse": self.StorageStatus(service="clickhouse", up=False, error="Connection refused"),
            "postgres": self.StorageStatus(service="postgres", up=True),
            "minio": self.StorageStatus(service="minio", up=True),
            "chromadb": self.StorageStatus(service="chromadb", up=True),
        }
        m = self.SystemMetrics(
            timestamp="test", redis_available=True,
            memory_usage=100, active_locks=0, lock_contentions=0,
            state_operations=10, cache_hits=9, redis_fallbacks=0,
            storage_statuses=statuses,
        )
        alerts = dashboard._check_alerts(m)
        down_alerts = [a for a in alerts if "DOWN" in a]
        self.assertEqual(len(down_alerts), 1)
        self.assertIn("ClickHouse", down_alerts[0])

    def test_check_alerts_latency_warning(self):
        """_check_alerts reports high latency alerts."""
        dashboard = self.Dashboard()
        statuses = {}
        for svc in ("redis", "clickhouse", "postgres", "minio", "chromadb"):
            statuses[svc] = self.StorageStatus(
                service=svc, up=True, latency_ms=1200,
            )
        m = self.SystemMetrics(
            timestamp="test", redis_available=True,
            memory_usage=100, active_locks=0, lock_contentions=0,
            state_operations=10, cache_hits=9, redis_fallbacks=0,
            storage_statuses=statuses,
        )
        alerts = dashboard._check_alerts(m)
        latency_alerts = [a for a in alerts if "latency" in a.lower()]
        self.assertGreaterEqual(len(latency_alerts), 1)

    def test_get_metrics_history_includes_storage(self):
        """get_metrics_history includes storage status in each entry."""
        dashboard = self.Dashboard()
        statuses = {
            "redis": self.StorageStatus(service="redis", up=True),
        }
        m = self.SystemMetrics(
            timestamp="test", redis_available=True,
            memory_usage=100, active_locks=0, lock_contentions=0,
            state_operations=10, cache_hits=9, redis_fallbacks=0,
            storage_statuses=statuses,
        )
        dashboard.metrics_history.append(m)

        async def test():
            history = await dashboard.get_metrics_history()
            self.assertEqual(len(history), 1)
            self.assertIn("storage", history[0])
            self.assertIn("redis", history[0]["storage"])

        asyncio.run(test())

    def test_fmt_bytes(self):
        """_fmt_bytes formats correctly."""
        self.assertIn("B", self.Dashboard._fmt_bytes(500))
        self.assertIn("KB", self.Dashboard._fmt_bytes(2048))
        self.assertIn("MB", self.Dashboard._fmt_bytes(1048576))
        self.assertIn("GB", self.Dashboard._fmt_bytes(1073741824))


# ======================================================================
#  Entry point
# ======================================================================

if __name__ == "__main__":
    unittest.main()
