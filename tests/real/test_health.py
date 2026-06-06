#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade health probe tests
ASIMNEXUS Health Probe Tests
============================
Tests for Kubernetes-style health checks:
- /health/live — Process alive check
- /health/ready — Dependency readiness check
- /health/status — Full system status
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

from backend.health import HealthChecker, get_health_checker


class TestHealthChecker:
    """Test suite for HealthChecker class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        # Close the file descriptor so SQLite can use it
        import os
        os.close(fd)
        Path(path).unlink(missing_ok=True)
        yield path
        # Force garbage collection and retry deletion
        import gc
        gc.collect()
        for _ in range(5):
            try:
                Path(path).unlink(missing_ok=True)
                break
            except PermissionError:
                import time
                time.sleep(0.1)

    @pytest.fixture
    def temp_model_file(self):
        """Create temporary model file for testing."""
        fd, path = tempfile.mkstemp(suffix=".gguf")
        # Close the file descriptor
        import os
        os.close(fd)
        Path(path).write_bytes(b"fake model data")
        yield path
        # Force garbage collection and retry deletion
        import gc
        gc.collect()
        for _ in range(5):
            try:
                Path(path).unlink(missing_ok=True)
                break
            except PermissionError:
                import time
                time.sleep(0.1)

    @pytest.fixture
    def health_checker(self, temp_db, temp_model_file):
        """Create HealthChecker instance with temp files and mock storage services."""
        from unittest.mock import patch
        checker = HealthChecker(temp_db, temp_model_file)
        # Patch storage service checks so they don't require running services
        patchers = [
            patch.object(checker, "_check_redis",
                         return_value={"ready": True, "message": "Mocked Redis"}),
            patch.object(checker, "_check_clickhouse",
                         return_value={"ready": True, "message": "Mocked ClickHouse"}),
            patch.object(checker, "_check_postgres",
                         return_value={"ready": True, "message": "Mocked PostgreSQL"}),
            patch.object(checker, "_check_minio",
                         return_value={"ready": True, "message": "Mocked MinIO"}),
            patch.object(checker, "_check_chromadb",
                         return_value={"ready": True, "message": "Mocked ChromaDB"}),
        ]
        for p in patchers:
            p.start()
        yield checker
        for p in patchers:
            p.stop()

    def test_check_live(self, health_checker):
        """Test liveness probe always returns alive status."""
        result = health_checker.check_live()

        assert result["status"] == "alive"
        assert "timestamp" in result
        assert "uptime_seconds" in result
        assert result["uptime_seconds"] >= 0

    def test_check_ready_with_db(self, health_checker, temp_db):
        """Test readiness probe with accessible database."""
        # Create a simple database
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()
        conn.close()

        result = health_checker.check_ready()

        assert "status" in result
        assert "timestamp" in result
        assert "checks" in result
        assert "all_ready" in result
        assert "database" in result["checks"]
        assert "model_file" in result["checks"]
        assert result["checks"]["database"]["ready"] == True
        assert result["checks"]["model_file"]["ready"] == True
        assert result["all_ready"] == True

    def test_check_ready_without_db(self, health_checker):
        """Test readiness probe with missing database."""
        # Use non-existent database path
        bad_checker = HealthChecker("/nonexistent/path.db", health_checker.gguf_model_path)
        result = bad_checker.check_ready()

        assert result["all_ready"] == False
        assert result["checks"]["database"]["ready"] == False
        assert "not found" in result["checks"]["database"]["message"]

    def test_check_ready_without_model(self, health_checker, temp_db):
        """Test readiness probe with missing model file."""
        # Use non-existent model path
        bad_checker = HealthChecker(temp_db, "/nonexistent/model.gguf")
        result = bad_checker.check_ready()

        assert result["all_ready"] == False
        assert result["checks"]["model_file"]["ready"] == False
        assert "not found" in result["checks"]["model_file"]["message"]

    def test_check_status(self, health_checker, temp_db):
        """Test full status check."""
        # Create a simple database
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.execute("INSERT INTO test VALUES (1)")
        conn.commit()
        conn.close()

        result = health_checker.check_status()

        assert "status" in result
        assert "timestamp" in result
        assert "uptime_seconds" in result
        assert "readiness" in result
        assert "dependencies" in result
        assert "modules" in result
        assert "system" in result
        assert "database" in result["dependencies"]
        assert "model_file" in result["dependencies"]

    def test_get_database_status(self, health_checker, temp_db):
        """Test detailed database status."""
        # Create database with users and messages tables
        conn = sqlite3.connect(temp_db)
        conn.execute("""
            CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT)
        """)
        conn.execute("INSERT INTO users VALUES ('1', 'test@example.com')")
        conn.execute("""
            CREATE TABLE messages (id TEXT PRIMARY KEY, content TEXT)
        """)
        conn.execute("INSERT INTO messages VALUES ('1', 'hello')")
        conn.commit()
        conn.close()

        status = health_checker._get_database_status()

        assert status["status"] == "connected"
        assert status["path"] == temp_db
        assert status["tables_count"] >= 2
        assert status["users_count"] == 1
        assert status["messages_count"] == 1
        assert "size_bytes" in status
        assert "size_mb" in status

    def test_get_model_file_status(self, health_checker, temp_model_file):
        """Test detailed model file status."""
        status = health_checker._get_model_file_status()

        assert status["status"] == "exists"
        assert "path" in status
        assert "size_bytes" in status
        assert "size_gb" in status
        assert "modified" in status

    def test_get_module_status(self, health_checker):
        """Test module status check."""
        status = health_checker._get_module_status()

        assert isinstance(status, dict)
        # Check that some expected modules are present
        expected_modules = [
            "user_identity", "world_clones", "hybrid_router",
            "vector_memory", "safety_veto", "dharma_veto"
        ]
        for module in expected_modules:
            assert module in status
            assert "status" in status[module]

    def test_get_system_metrics(self, health_checker):
        """Test system metrics collection."""
        metrics = health_checker._get_system_metrics()

        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "disk_percent" in metrics
        # Values should be either numbers or None (if psutil not installed)

    def test_get_health_checker_singleton(self, temp_db, temp_model_file):
        """Test that get_health_checker creates instance with correct paths."""
        checker1 = get_health_checker(temp_db, temp_model_file)
        checker2 = get_health_checker(temp_db, temp_model_file)

        # Each call creates a new instance (for test isolation)
        assert checker1.db_path == temp_db
        assert checker1.gguf_model_path == temp_model_file
        assert checker2.db_path == temp_db
        assert checker2.gguf_model_path == temp_model_file


class TestHealthRoutes:
    """Test suite for health route integration."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        # Close the file descriptor so SQLite can use it
        import os
        os.close(fd)
        Path(path).unlink(missing_ok=True)
        yield path
        # Force garbage collection and retry deletion
        import gc
        gc.collect()
        for _ in range(5):
            try:
                Path(path).unlink(missing_ok=True)
                break
            except PermissionError:
                import time
                time.sleep(0.1)

    @pytest.fixture
    def temp_model_file(self):
        """Create temporary model file for testing."""
        fd, path = tempfile.mkstemp(suffix=".gguf")
        # Close the file descriptor
        import os
        os.close(fd)
        Path(path).write_bytes(b"fake model data")
        yield path
        # Force garbage collection and retry deletion
        import gc
        gc.collect()
        for _ in range(5):
            try:
                Path(path).unlink(missing_ok=True)
                break
            except PermissionError:
                import time
                time.sleep(0.1)

    @pytest.fixture
    def app(self, temp_db, temp_model_file):
        """Create FastAPI app with health routes."""
        from unittest.mock import patch
        from fastapi import FastAPI
        from backend.health import setup_health_routes

        # Initialize the database first
        import sqlite3
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()
        conn.close()

        app = FastAPI()
        setup_health_routes(app, temp_db, temp_model_file)
        # Patch storage service checks to return ready=True (they're not running locally)
        patchers = [
            patch("backend.health.HealthChecker._check_redis",
                  return_value={"ready": True, "message": "Mocked Redis"}),
            patch("backend.health.HealthChecker._check_clickhouse",
                  return_value={"ready": True, "message": "Mocked ClickHouse"}),
            patch("backend.health.HealthChecker._check_postgres",
                  return_value={"ready": True, "message": "Mocked PostgreSQL"}),
            patch("backend.health.HealthChecker._check_minio",
                  return_value={"ready": True, "message": "Mocked MinIO"}),
            patch("backend.health.HealthChecker._check_chromadb",
                  return_value={"ready": True, "message": "Mocked ChromaDB"}),
        ]
        for p in patchers:
            p.start()
        yield app
        for p in patchers:
            p.stop()

    @pytest.fixture
    def client(self, app):
        """Create test client for FastAPI app."""
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_health_live_route(self, client):
        """Test /health/live endpoint."""
        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "uptime_seconds" in data

    def test_health_ready_route_success(self, client):
        """Test /health/ready endpoint when all dependencies are ready."""
        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["all_ready"] == True
        assert "checks" in data

    def test_health_ready_route_failure(self, temp_db):
        """Test /health/ready endpoint when dependencies are not ready."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from backend.health import setup_health_routes

        # Create app with non-existent database
        app = FastAPI()
        setup_health_routes(app, "/nonexistent/db.db", "/nonexistent/model.gguf")
        client = TestClient(app)

        response = client.get("/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["all_ready"] == False

    def test_health_status_route(self, client):
        """Test /health/status endpoint."""
        response = client.get("/health/status")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "readiness" in data
        assert "dependencies" in data
        assert "modules" in data
        assert "system" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
