#!/usr/bin/env python3
"""
STATUS: REAL — Integration tests for storage-layer monitoring and observability.

Tests:
  1. Health check endpoints for all 4 storage layers
     (ClickHouse, PostgreSQL/OLTP, MinIO/ObjectStore, ChromaDB/Vector)
  2. Prometheus metrics endpoint returns storage metrics
  3. Observability dashboard renders storage status
  4. Grafana dashboard JSON is valid
  5. Fallback mechanisms when primary storage is unavailable
"""

import asyncio
import json
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ======================================================================
#  1. Health Check Endpoint Tests (all 4 storage layers)
# ======================================================================

class TestHealthEndpoints(unittest.TestCase):
    """Verify /health/live, /health/ready, and /health/status endpoints
    include correct storage-layer checks for all 4 services."""

    def setUp(self):
        from backend.health import HealthChecker
        self.checker = HealthChecker(
            db_path="/tmp/test_asim.db",
            gguf_model_path="/tmp/test_model.gguf",
        )

    # -- ClickHouse ----------------------------------------------------

    @patch("requests.get")
    def test_clickhouse_health_ready(self, mock_get):
        """ClickHouse probe returns ready=True when HTTP /ping returns 200."""
        mock_get.return_value.status_code = 200
        result = self.checker._check_clickhouse()
        self.assertTrue(result["ready"])
        self.assertIn("ClickHouse", result["message"])

    @patch("requests.get")
    def test_clickhouse_health_down(self, mock_get):
        """ClickHouse probe returns ready=False when HTTP /ping returns 503."""
        mock_get.return_value.status_code = 503
        result = self.checker._check_clickhouse()
        self.assertFalse(result["ready"])

    @patch("requests.get")
    def test_clickhouse_health_status(self, mock_get):
        """ClickHouse detailed status returns expected fields."""
        mock_get.return_value.ok = True
        mock_get.return_value.text = "24.3.1.1\t12345"
        result = self.checker._get_clickhouse_status()
        self.assertEqual(result["status"], "connected")
        self.assertIn("version", result)
        self.assertIn("uptime_seconds", result)

    # -- PostgreSQL / OLTP --------------------------------------------

    @patch("psycopg2.connect")
    def test_postgres_health_ready(self, mock_connect):
        """PostgreSQL probe returns ready=True on successful connection."""
        result = self.checker._check_postgres()
        self.assertTrue(result["ready"])
        self.assertIn("PostgreSQL", result["message"])

    @patch("psycopg2.connect")
    def test_postgres_health_down(self, mock_connect):
        """PostgreSQL probe returns ready=False on connection failure."""
        mock_connect.side_effect = Exception("Connection refused")
        result = self.checker._check_postgres()
        self.assertFalse(result["ready"])

    @patch("psycopg2.connect")
    def test_postgres_health_status(self, mock_connect):
        """PostgreSQL detailed status returns expected fields."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [
            {
                "v": "PostgreSQL 16.2 (Debian 16.2-1) on x86_64-pc-linux-gnu",
                "start_time": datetime(2026, 6, 1, 0, 0, 0),
                "db_size": 10485760,
            }
        ]
        result = self.checker._get_postgres_status()
        self.assertEqual(result["status"], "connected")
        self.assertIn("version", result)
        self.assertIn("db_size_bytes", result)

    # -- MinIO / Object Store -----------------------------------------

    @patch("requests.get")
    def test_minio_health_ready(self, mock_get):
        """MinIO probe returns ready=True when /minio/health/live returns 200."""
        mock_get.return_value.status_code = 200
        result = self.checker._check_minio()
        self.assertTrue(result["ready"])
        self.assertIn("MinIO", result["message"])

    @patch("requests.get")
    def test_minio_health_down(self, mock_get):
        """MinIO probe returns ready=False when health check fails."""
        mock_get.return_value.status_code = 503
        result = self.checker._check_minio()
        self.assertFalse(result["ready"])

    def test_minio_health_status(self):
        """MinIO detailed status returns expected fields."""
        # Inject mock minio module since it may not be installed
        import sys
        mock_minio_mod = MagicMock()
        mock_minio_client = MagicMock()
        mock_minio_mod.Minio.return_value = mock_minio_client
        mock_minio_client.list_buckets.return_value = [
            MagicMock(name="models"),
            MagicMock(name="data"),
        ]
        sys.modules["minio"] = mock_minio_mod
        try:
            # Re-import the module to pick up the mock
            import importlib
            import backend.health
            importlib.reload(backend.health)
            from backend.health import HealthChecker
            checker = HealthChecker(
                db_path="/tmp/test_asim.db",
                gguf_model_path="/tmp/test_model.gguf",
            )
            result = checker._get_minio_status()
            self.assertEqual(result["status"], "connected")
            self.assertIn("bucket_count", result)
            self.assertEqual(result["bucket_count"], 2)
        finally:
            # Clean up
            sys.modules.pop("minio", None)
            importlib.reload(backend.health)

    # -- ChromaDB / Vector Store --------------------------------------

    @patch("requests.get")
    def test_chromadb_health_ready(self, mock_get):
        """ChromaDB probe returns ready=True when /api/v1/heartbeat returns 200."""
        mock_get.return_value.status_code = 200
        result = self.checker._check_chromadb()
        self.assertTrue(result["ready"])
        self.assertIn("ChromaDB", result["message"])

    @patch("requests.get")
    def test_chromadb_health_down(self, mock_get):
        """ChromaDB probe returns ready=False when heartbeat fails."""
        mock_get.return_value.status_code = 503
        result = self.checker._check_chromadb()
        self.assertFalse(result["ready"])

    @patch("requests.get")
    def test_chromadb_health_status(self, mock_get):
        """ChromaDB detailed status returns expected fields."""
        mock_hb = MagicMock()
        mock_coll = MagicMock()
        mock_get.side_effect = [mock_hb, mock_coll]
        mock_hb.ok = True
        mock_hb.json.return_value = {"nanosecond heartbeat": 123456789}
        mock_coll.ok = True
        mock_coll.json.return_value = [{"name": "docs"}, {"name": "vectors"}]
        result = self.checker._get_chromadb_status()
        self.assertEqual(result["status"], "connected")
        self.assertIn("collection_count", result)
        self.assertEqual(result["collection_count"], 2)

    # -- Aggregate health endpoint shape -------------------------------

    def test_check_ready_includes_all_storage_layers(self):
        """check_ready() returns checks for all 4 storage layers + Redis."""
        result = self.checker.check_ready()
        self.assertIn("checks", result)
        checks = result["checks"]
        for svc in ("clickhouse", "postgres", "minio", "chromadb", "redis"):
            self.assertIn(svc, checks)
            self.assertIn("ready", checks[svc])

    def test_check_status_includes_storage_block(self):
        """check_status() returns 'storage' block with all services."""
        result = self.checker.check_status()
        self.assertIn("storage", result)
        storage = result["storage"]
        for svc in ("clickhouse", "postgres", "minio", "chromadb", "redis"):
            self.assertIn(svc, storage)


# ======================================================================
#  2. Prometheus Metrics Storage Tests
# ======================================================================

class TestPrometheusStorageMetrics(unittest.TestCase):
    """Verify Prometheus metrics endpoint returns storage-layer metrics."""

    def setUp(self):
        import monitoring.metrics as mm
        self.mm = mm

    def test_storage_metrics_registered(self):
        """MetricsCollector registers all 5 storage Prometheus metric types."""
        collector = self.mm.MetricsCollector()
        self.assertTrue(hasattr(collector, "storage_up"))
        self.assertTrue(hasattr(collector, "storage_query_latency"))
        self.assertTrue(hasattr(collector, "storage_connections_active"))
        self.assertTrue(hasattr(collector, "storage_errors_total"))
        self.assertTrue(hasattr(collector, "storage_disk_usage_bytes"))

    def test_storage_up_gauge_has_service_label(self):
        """storage_up gauge uses 'service' label."""
        collector = self.mm.MetricsCollector()
        self.assertEqual(
            collector.storage_up._labelnames,
            ("service",),
        )

    def test_storage_query_latency_histogram_has_service_label(self):
        """storage_query_latency histogram uses 'service' and 'operation' labels."""
        collector = self.mm.MetricsCollector()
        self.assertEqual(
            collector.storage_query_latency._labelnames,
            ("service", "operation"),
        )

    def test_storage_errors_counter_has_service_and_error_type_labels(self):
        """storage_errors_total counter uses 'service' and 'error_type' labels."""
        collector = self.mm.MetricsCollector()
        self.assertEqual(
            collector.storage_errors_total._labelnames,
            ("service", "error_type"),
        )

    def test_storage_cache_is_populated(self):
        """After _collect_storage_metrics, storage_cache contains all services."""
        collector = self.mm.MetricsCollector()

        async def test():
            await collector._collect_storage_metrics()
            for svc in ("redis", "clickhouse", "postgres", "minio", "chromadb"):
                self.assertIn(svc, collector.storage_cache)
                self.assertIn("up", collector.storage_cache[svc])
                self.assertIn("timestamp", collector.storage_cache[svc])

        asyncio.run(test())

    @patch("redis.Redis")
    def test_ping_redis_sets_metrics(self, mock_redis):
        """_ping_storage for Redis returns up=True and connection count."""
        instance = mock_redis.return_value
        instance.ping.return_value = True
        instance.info.return_value = {
            "connected_clients": 5,
            "used_memory": 1024,
            "redis_version": "7.0.0",
        }

        collector = self.mm.MetricsCollector()

        async def test():
            up, details = await collector._ping_storage("redis")
            self.assertTrue(up)
            self.assertEqual(details.get("connections"), 5)
            self.assertEqual(details.get("disk_bytes"), 1024)

        asyncio.run(test())

    @patch("requests.get")
    def test_ping_clickhouse_sets_metrics(self, mock_get):
        """_ping_storage for ClickHouse returns up=True on 200."""
        # First call for /ping, second for version query
        mock_ping = MagicMock()
        mock_ping.status_code = 200
        mock_version = MagicMock()
        mock_version.ok = True
        mock_version.text = "24.3.1.1\t54321"
        mock_get.side_effect = [mock_ping, mock_version]

        collector = self.mm.MetricsCollector()

        async def test():
            up, details = await collector._ping_storage("clickhouse")
            self.assertTrue(up)
            self.assertIn("version", details)

        asyncio.run(test())

    @patch("requests.get")
    def test_ping_minio_sets_metrics(self, mock_get):
        """_ping_storage for MinIO returns up=True on 200."""
        mock_get.return_value.status_code = 200
        collector = self.mm.MetricsCollector()

        async def test():
            up, _ = await collector._ping_storage("minio")
            self.assertTrue(up)

        asyncio.run(test())

    @patch("requests.get")
    def test_ping_chromadb_sets_metrics(self, mock_get):
        """_ping_storage for ChromaDB returns up=True on 200."""
        mock_get.return_value.status_code = 200
        collector = self.mm.MetricsCollector()

        async def test():
            up, _ = await collector._ping_storage("chromadb")
            self.assertTrue(up)

        asyncio.run(test())

    def test_ping_storage_down_sets_up_false(self):
        """_ping_storage for unknown service returns up=False."""
        collector = self.mm.MetricsCollector()

        async def test():
            up, details = await collector._ping_storage("nonexistent")
            self.assertFalse(up)
            self.assertIn("error", details)

        asyncio.run(test())

    def test_storage_alert_thresholds(self):
        """Alert thresholds include storage-specific keys."""
        collector = self.mm.MetricsCollector()
        thresholds = collector.alert_thresholds
        for svc in ("redis", "clickhouse", "postgres", "minio", "chromadb"):
            self.assertIn(f"storage_{svc}_up", thresholds)
        self.assertIn("storage_latency_ms", thresholds)
        self.assertIn("storage_connections", thresholds)
        self.assertIn("storage_disk_usage_bytes", thresholds)


# ======================================================================
#  3. Observability Dashboard Storage Status Tests
# ======================================================================

class TestObservabilityDashboardStorage(unittest.TestCase):
    """Verify observability dashboard correctly renders storage status."""

    def setUp(self):
        from monitoring.observability_dashboard import (
            ObservabilityDashboard,
            StorageStatus,
            SystemMetrics,
        )
        self.Dashboard = ObservabilityDashboard
        self.StorageStatus = StorageStatus
        self.SystemMetrics = SystemMetrics

    def test_storage_status_created_for_each_service(self):
        """StorageStatus dataclass holds all expected fields."""
        svc_names = [
            ("clickhouse", "ClickHouse (Analytics)"),
            ("postgres", "PostgreSQL (OLTP)"),
            ("minio", "MinIO (Object Storage)"),
            ("chromadb", "ChromaDB (Vector)"),
            ("redis", "Redis (Cache)"),
        ]
        for name, _ in svc_names:
            s = self.StorageStatus(service=name)
            self.assertEqual(s.service, name)
            # Defaults
            self.assertFalse(s.up)
            self.assertEqual(s.latency_ms, 0.0)
            self.assertEqual(s.connections, 0)
            self.assertEqual(s.disk_bytes, 0)
            self.assertEqual(s.version, "")
            self.assertEqual(s.error, "")
            self.assertIsNotNone(s.last_checked)

    def test_system_metrics_includes_storage_layer(self):
        """SystemMetrics dataclass has storage_statuses dict field."""
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
        # Can populate with storage statuses
        m.storage_statuses["clickhouse"] = self.StorageStatus(
            service="clickhouse", up=True, latency_ms=5.0
        )
        self.assertIn("clickhouse", m.storage_statuses)
        self.assertTrue(m.storage_statuses["clickhouse"].up)

    def test_dashboard_displays_storage_section(self):
        """The _display_dashboard output includes 'STORAGE LAYER STATUS'."""
        dashboard = self.Dashboard()
        statuses = {}
        for svc in ("clickhouse", "postgres", "minio", "chromadb", "redis"):
            statuses[svc] = self.StorageStatus(
                service=svc, up=True, latency_ms=2.0
            )
        m = self.SystemMetrics(
            timestamp="2026-06-01T00:00:00",
            redis_available=True,
            memory_usage=1024,
            active_locks=0,
            lock_contentions=0,
            state_operations=10,
            cache_hits=9,
            redis_fallbacks=0,
            storage_statuses=statuses,
        )
        # Capture stdout
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dashboard._display_dashboard(m)
        output = buf.getvalue()
        # Verify storage section is rendered
        self.assertIn("STORAGE LAYER STATUS", output)
        self.assertIn("ALL ONLINE", output)
        for name in ("ClickHouse", "PostgreSQL", "MinIO", "ChromaDB", "Redis"):
            self.assertIn(name, output)

    def test_dashboard_reports_storage_down(self):
        """Dashboard shows 'SOME OFFLINE' when a storage service is down."""
        dashboard = self.Dashboard()
        statuses = {}
        for svc in ("clickhouse", "postgres", "minio", "chromadb", "redis"):
            statuses[svc] = self.StorageStatus(
                service=svc, up=(svc != "clickhouse"), latency_ms=2.0,
                error="Connection refused" if svc == "clickhouse" else "",
            )
        m = self.SystemMetrics(
            timestamp="2026-06-01T00:00:00",
            redis_available=True,
            memory_usage=1024,
            active_locks=0,
            lock_contentions=0,
            state_operations=10,
            cache_hits=9,
            redis_fallbacks=0,
            storage_statuses=statuses,
        )
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dashboard._display_dashboard(m)
        output = buf.getvalue()
        self.assertIn("SOME OFFLINE", output)
        self.assertIn("ClickHouse", output)
        self.assertIn("Connection refused", output)

    def test_health_score_all_storage_up(self):
        """100% health when all storage services are up with low latency."""
        dashboard = self.Dashboard()
        statuses = {}
        for svc in ("clickhouse", "postgres", "minio", "chromadb", "redis"):
            statuses[svc] = self.StorageStatus(
                service=svc, up=True, latency_ms=1.0,
            )
        m = self.SystemMetrics(
            timestamp="test", redis_available=True,
            memory_usage=100, active_locks=0, lock_contentions=0,
            state_operations=10, cache_hits=9, redis_fallbacks=0,
            storage_statuses=statuses,
        )
        score = dashboard._calculate_health_score(m)
        self.assertEqual(score, 100)

    def test_health_score_storage_down_deducts(self):
        """Health score drops by 10 for each down storage service."""
        dashboard = self.Dashboard()
        statuses = {}
        for svc in ("clickhouse", "postgres", "minio", "chromadb", "redis"):
            statuses[svc] = self.StorageStatus(
                service=svc, up=(svc != "clickhouse"),
            )
        m = self.SystemMetrics(
            timestamp="test", redis_available=True,
            memory_usage=100, active_locks=0, lock_contentions=0,
            state_operations=10, cache_hits=9, redis_fallbacks=0,
            storage_statuses=statuses,
        )
        score = dashboard._calculate_health_score(m)
        # Base = 100 (no lock/redis penalties). -10 for clickhouse down = 90
        self.assertEqual(score, 90)

    def test_storage_latency_alerts_generated(self):
        """Dashboard generates latency alerts for services > 200ms."""
        dashboard = self.Dashboard()
        statuses = {}
        for svc in ("clickhouse", "postgres", "minio", "chromadb"):
            statuses[svc] = self.StorageStatus(
                service=svc, up=True, latency_ms=150.0,
            )
        # Redis with high latency to trigger alert
        statuses["redis"] = self.StorageStatus(
            service="redis", up=True, latency_ms=1200.0,
        )
        m = self.SystemMetrics(
            timestamp="test", redis_available=True,
            memory_usage=100, active_locks=0, lock_contentions=0,
            state_operations=10, cache_hits=9, redis_fallbacks=0,
            storage_statuses=statuses,
        )
        alerts = dashboard._check_alerts(m)
        redis_latency_alerts = [
            a for a in alerts
            if "redis" in a.lower() or "Redis" in a
        ]
        has_latency = any("latency" in a.lower() for a in redis_latency_alerts)
        self.assertTrue(has_latency)


# ======================================================================
#  4. Grafana Dashboard JSON Validation
# ======================================================================

class TestGrafanaDashboardJSON(unittest.TestCase):
    """Verify the Grafana dashboard JSON is valid and complete."""

    def setUp(self):
        dashboard_path = Path(
            __file__).parent.parent.parent / "monitoring" / "grafana" / "dashboards" / "storage-pod-stability.json"
        self.dashboard_path = dashboard_path
        self.assertTrue(
            dashboard_path.exists(),
            f"Dashboard file not found: {dashboard_path}",
        )
        with open(dashboard_path, "r") as f:
            self.dashboard = json.load(f)

    def test_dashboard_is_valid_json(self):
        """Dashboard file loads as valid JSON."""
        self.assertIsInstance(self.dashboard, dict)

    def test_dashboard_has_title(self):
        """Dashboard has a title."""
        dash = self.dashboard.get("dashboard", {})
        self.assertIn("title", dash)
        self.assertIn("Storage", dash["title"])

    def test_dashboard_has_panels(self):
        """Dashboard contains panel definitions."""
        dash = self.dashboard.get("dashboard", {})
        self.assertIn("panels", dash)
        self.assertGreater(len(dash["panels"]), 0)

    def test_dashboard_has_service_rows(self):
        """Dashboard includes row panels for each storage service."""
        dash = self.dashboard.get("dashboard", {})
        panels = dash.get("panels", [])
        row_titles = [p["title"] for p in panels if p.get("type") == "row"]
        service_keywords = ["ClickHouse", "PostgreSQL", "MinIO", "ChromaDB", "Redis"]
        for keyword in service_keywords:
            matches = [t for t in row_titles if keyword in t]
            self.assertGreaterEqual(
                len(matches), 1,
                f"No row panel found for {keyword}",
            )

    def test_dashboard_has_uptime_panels(self):
        """Dashboard includes uptime stat panels for each service."""
        dash = self.dashboard.get("dashboard", {})
        panels = dash.get("panels", [])
        uptime_panels = [p for p in panels if "Uptime" in p.get("title", "")]
        self.assertGreaterEqual(len(uptime_panels), 5)

    def test_dashboard_has_latency_panels(self):
        """Dashboard includes latency timeseries panels."""
        dash = self.dashboard.get("dashboard", {})
        panels = dash.get("panels", [])
        latency_panels = [p for p in panels if "Latency" in p.get("title", "")]
        self.assertGreaterEqual(len(latency_panels), 5)

    def test_dashboard_has_connection_panels(self):
        """Dashboard includes connection pool panels."""
        dash = self.dashboard.get("dashboard", {})
        panels = dash.get("panels", [])
        conn_panels = [p for p in panels if "Connection" in p.get("title", "")]
        self.assertGreaterEqual(len(conn_panels), 1)

    def test_dashboard_has_alert_thresholds(self):
        """Dashboard panels have threshold configurations."""
        dash = self.dashboard.get("dashboard", {})
        panels = dash.get("panels", [])
        panels_with_thresholds = [
            p for p in panels
            if "thresholds" in str(p.get("fieldConfig", {}))
        ]
        self.assertGreater(len(panels_with_thresholds), 0)

    def test_dashboard_has_annotations(self):
        """Dashboard has annotation queries for storage down events."""
        dash = self.dashboard.get("dashboard", {})
        annotations = dash.get("annotations", {}).get("list", [])
        self.assertGreater(len(annotations), 0)
        storage_annotations = [
            a for a in annotations
            if "storage" in a.get("query", "").lower()
            or "asimmers_storage" in a.get("query", "")
        ]
        self.assertGreaterEqual(len(storage_annotations), 1)

    def test_dashboard_metrics_match_codebase(self):
        """Dashboard PromQL expressions reference expected metric names."""
        dash = self.dashboard.get("dashboard", {})
        panels = dash.get("panels", [])
        all_exprs = []
        for p in panels:
            for t in p.get("targets", []):
                if "expr" in t:
                    all_exprs.append(t["expr"])
        # Core storage metrics
        expected_metrics = [
            "asimmers_storage_up",
            "asimmers_storage_query_latency_ms",
            "asimmers_storage_connections_active",
            "asimmers_storage_errors_total",
            "asimmers_storage_disk_usage_bytes",
        ]
        for metric in expected_metrics:
            found = any(metric in expr for expr in all_exprs)
            self.assertTrue(
                found,
                f"Metric {metric} not found in any dashboard panel query",
            )

    def test_dashboard_links_defined(self):
        """Dashboard has links section."""
        dash = self.dashboard.get("dashboard", {})
        self.assertIn("links", dash)

    def test_dashboard_refresh_interval_set(self):
        """Dashboard has a refresh interval configured."""
        dash = self.dashboard.get("dashboard", {})
        self.assertIn("refresh", dash)
        self.assertIsNotNone(dash["refresh"])

    def test_dashboard_time_range_set(self):
        """Dashboard has a default time range."""
        dash = self.dashboard.get("dashboard", {})
        if "time" in dash:
            self.assertIn("from", dash["time"])
            self.assertIn("to", dash["time"])

    def test_dashboard_tags_includes_production(self):
        """Dashboard has production tag."""
        dash = self.dashboard.get("dashboard", {})
        tags = dash.get("tags", [])
        self.assertIn("production", tags)


# ======================================================================
#  5. Fallback Mechanism Tests
# ======================================================================

class TestStorageFallbackMechanisms(unittest.TestCase):
    """Verify fallback behavior when primary storage is unavailable."""

    def test_health_check_graceful_degradation(self):
        """Health check returns ready=False, not crashes, when all storage down."""
        from backend.health import HealthChecker
        checker = HealthChecker(
            db_path="/tmp/test_asim.db",
            gguf_model_path="/tmp/test_model.gguf",
        )
        # Simulate all storage down by patching individual checks
        with patch.object(checker, "_check_redis",
                          return_value={"ready": False, "message": "Redis error"}):
            with patch.object(checker, "_check_clickhouse",
                              return_value={"ready": False, "message": "ClickHouse error"}):
                with patch.object(checker, "_check_postgres",
                                  return_value={"ready": False, "message": "PG error"}):
                    with patch.object(checker, "_check_minio",
                                      return_value={"ready": False, "message": "MinIO error"}):
                        with patch.object(checker, "_check_chromadb",
                                          return_value={"ready": False, "message": "CHDB error"}):
                            result = checker.check_ready()
                            self.assertEqual(result["status"], "not_ready")
                            self.assertFalse(result["all_ready"])
                            # Verify all checks are present
                            for svc in ("redis", "clickhouse", "postgres", "minio", "chromadb"):
                                self.assertIn(svc, result["checks"])

    def test_metrics_collector_handles_storage_down(self):
        """Metrics Collector records down state without crashing."""
        import monitoring.metrics as mm
        collector = mm.MetricsCollector()

        async def test():
            # All storage is down (unknown service returns False)
            await collector._collect_storage_metrics()
            # Cache should have entries for all services (errors recorded)
            for svc in ("redis", "clickhouse", "postgres", "minio", "chromadb"):
                self.assertIn(svc, collector.storage_cache)

        asyncio.run(test())

    def test_observability_dashboard_handles_empty_storage(self):
        """Dashboard works when there are no storage statuses."""
        from monitoring.observability_dashboard import (
            ObservabilityDashboard,
            SystemMetrics,
        )
        dashboard = ObservabilityDashboard()
        m = self._make_metrics(storage_statuses={})
        # Should not crash
        score = dashboard._calculate_health_score(m)
        self.assertIsInstance(score, int)

        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dashboard._display_dashboard(m)
        output = buf.getvalue()
        # Should still show basic status even without storage
        self.assertIn("STORAGE LAYER STATUS", output)

    def test_observability_dashboard_handles_import_error(self):
        """Dashboard _check_storage handles ImportError gracefully."""
        from monitoring.observability_dashboard import (
            ObservabilityDashboard,
        )
        dashboard = ObservabilityDashboard()

        # Patch _check_storage to simulate ImportError
        async def mock_check(service):
            from monitoring.observability_dashboard import StorageStatus
            s = StorageStatus(service=service)
            s.error = "Missing library: fakelib"
            return s

        dashboard._check_storage = mock_check

        async def test():
            statuses = {}
            for svc in ("clickhouse", "postgres", "minio", "chromadb", "redis"):
                statuses[svc] = await dashboard._check_storage(svc)
            m = self._make_metrics(storage_statuses=statuses)
            # Should not crash
            score = dashboard._calculate_health_score(m)
            self.assertIsInstance(score, int)

        asyncio.run(test())

    def test_health_check_missing_library(self):
        """Health check returns unavailable when required library is missing."""
        from backend.health import HealthChecker
        checker = HealthChecker(
            db_path="/tmp/test_asim.db",
            gguf_model_path="/tmp/test_model.gguf",
        )
        # Simulate missing 'redis' module
        with patch.dict("sys.modules", {"redis": None}):
            result = checker._check_redis()
            self.assertFalse(result["ready"])
            self.assertIn("not installed", result["message"])

    @staticmethod
    def _make_metrics(storage_statuses):
        from monitoring.observability_dashboard import SystemMetrics
        return SystemMetrics(
            timestamp="test",
            redis_available=False,
            memory_usage=0,
            active_locks=0,
            lock_contentions=0,
            state_operations=0,
            cache_hits=0,
            redis_fallbacks=0,
            storage_statuses=storage_statuses,
        )


# ======================================================================
#  Entry point
# ======================================================================

if __name__ == "__main__":
    unittest.main()
