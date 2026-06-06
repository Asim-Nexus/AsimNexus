#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade model registry tests
ASIMNEXUS Model Registry Tests
==============================
Tests for model versioning, registration, rollback, and integrity verification.
"""

import os
import gc
import json
import time
import pytest
import sqlite3
import tempfile
import hashlib
from pathlib import Path
from backend.registry import (
    ModelRegistry, get_model_registry, reset_model_registry,
    RegisterModelRequest, RollbackRequest
)


class TestModelRegistry:
    """Test suite for ModelRegistry class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        Path(path).unlink(missing_ok=True)
        yield path
        gc.collect()
        for _ in range(5):
            try:
                Path(path).unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.1)

    @pytest.fixture
    def temp_model_file(self):
        """Create a temporary model file for registration."""
        fd, path = tempfile.mkstemp(suffix=".gguf")
        os.close(fd)
        Path(path).write_bytes(b"fake model binary data v1")
        yield path
        Path(path).unlink(missing_ok=True)

    @pytest.fixture
    def temp_model_file_v2(self):
        """Create a second version of a model file."""
        fd, path = tempfile.mkstemp(suffix=".gguf")
        os.close(fd)
        Path(path).write_bytes(b"fake model binary data v2 - with improvements")
        yield path
        Path(path).unlink(missing_ok=True)

    @pytest.fixture
    def registry(self, temp_db):
        """Create ModelRegistry with temp database."""
        reset_model_registry()
        return ModelRegistry(temp_db)

    def test_init_db_creates_tables(self, temp_db):
        """Test that database tables are created on init."""
        registry = ModelRegistry(temp_db)
        with sqlite3.connect(temp_db) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]
            assert "model_registry" in table_names

    def test_register_model(self, registry, temp_model_file):
        """Test registering a new model version."""
        model = registry.register_model(
            name="test-model",
            version="1.0.0",
            file_path=temp_model_file,
            created_by="test-user",
            metadata={"description": "Test model v1"}
        )

        assert model.name == "test-model"
        assert model.version == "1.0.0"
        assert model.is_active is True
        assert model.created_by == "test-user"
        assert model.metadata["description"] == "Test model v1"
        assert model.file_hash is not None
        assert model.signature is not None
        assert model.rollback_to is None  # First version, no rollback pointer

    def test_register_model_file_not_found(self, registry):
        """Test registering with non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            registry.register_model(
                name="test-model",
                version="1.0.0",
                file_path="/nonexistent/model.gguf"
            )

    def test_register_multiple_versions(self, registry, temp_model_file, temp_model_file_v2):
        """Test registering multiple versions of the same model."""
        v1 = registry.register_model(
            name="test-model",
            version="1.0.0",
            file_path=temp_model_file
        )
        assert v1.is_active is True
        assert v1.rollback_to is None

        v2 = registry.register_model(
            name="test-model",
            version="2.0.0",
            file_path=temp_model_file_v2
        )
        assert v2.is_active is True
        assert v2.rollback_to == v1.id  # Points to v1

        # v1 should now be inactive
        v1_check = registry.get_model("test-model", "1.0.0")
        assert v1_check.is_active is False

    def test_get_active_model(self, registry, temp_model_file, temp_model_file_v2):
        """Test getting the currently active model version."""
        registry.register_model(name="test-model", version="1.0.0", file_path=temp_model_file)
        registry.register_model(name="test-model", version="2.0.0", file_path=temp_model_file_v2)

        active = registry.get_active_model("test-model")
        assert active is not None
        assert active.version == "2.0.0"

    def test_get_active_model_not_found(self, registry):
        """Test getting active model when none exists."""
        active = registry.get_active_model("nonexistent")
        assert active is None

    def test_get_model_by_version(self, registry, temp_model_file):
        """Test getting a specific model version."""
        registry.register_model(name="test-model", version="1.0.0", file_path=temp_model_file)

        model = registry.get_model("test-model", "1.0.0")
        assert model is not None
        assert model.version == "1.0.0"

        model = registry.get_model("test-model", "2.0.0")
        assert model is None

    def test_list_versions(self, registry, temp_model_file, temp_model_file_v2):
        """Test listing all versions of a model."""
        registry.register_model(name="test-model", version="1.0.0", file_path=temp_model_file)
        registry.register_model(name="test-model", version="2.0.0", file_path=temp_model_file_v2)

        versions = registry.list_versions("test-model")
        assert len(versions) == 2
        # Most recent first
        assert versions[0].version == "2.0.0"
        assert versions[1].version == "1.0.0"

    def test_rollback_to_previous_version(self, registry, temp_model_file, temp_model_file_v2):
        """Test rolling back to the previous version."""
        v1 = registry.register_model(name="test-model", version="1.0.0", file_path=temp_model_file)
        v2 = registry.register_model(name="test-model", version="2.0.0", file_path=temp_model_file_v2)

        # Rollback to previous (v1)
        rolled_back = registry.rollback("test-model")
        assert rolled_back.version == "1.0.0"
        assert rolled_back.is_active is True

        # v2 should now be inactive
        v2_check = registry.get_model("test-model", "2.0.0")
        assert v2_check.is_active is False

    def test_rollback_to_specific_version(self, registry, temp_model_file, temp_model_file_v2):
        """Test rolling back to a specific version."""
        registry.register_model(name="test-model", version="1.0.0", file_path=temp_model_file)
        registry.register_model(name="test-model", version="2.0.0", file_path=temp_model_file_v2)

        # Rollback to v1 explicitly
        rolled_back = registry.rollback("test-model", target_version="1.0.0")
        assert rolled_back.version == "1.0.0"
        assert rolled_back.is_active is True

    def test_rollback_no_previous_version(self, registry, temp_model_file):
        """Test rollback when there's no previous version."""
        registry.register_model(name="test-model", version="1.0.0", file_path=temp_model_file)

        with pytest.raises(ValueError, match="No rollback pointer"):
            registry.rollback("test-model")

    def test_rollback_target_not_found(self, registry, temp_model_file):
        """Test rollback to non-existent version."""
        registry.register_model(name="test-model", version="1.0.0", file_path=temp_model_file)

        with pytest.raises(ValueError, match="Target version not found"):
            registry.rollback("test-model", target_version="99.0.0")

    def test_verify_integrity_valid(self, registry, temp_model_file):
        """Test integrity verification passes for unmodified file."""
        registry.register_model(name="test-model", version="1.0.0", file_path=temp_model_file)

        valid = registry.verify_integrity("test-model", "1.0.0")
        assert valid is True

    def test_verify_integrity_tampered(self, registry, temp_model_file):
        """Test integrity verification fails for modified file."""
        registry.register_model(name="test-model", version="1.0.0", file_path=temp_model_file)

        # Tamper with the file
        Path(temp_model_file).write_bytes(b"tampered data")

        valid = registry.verify_integrity("test-model", "1.0.0")
        assert valid is False

    def test_verify_integrity_missing_file(self, registry, temp_model_file):
        """Test integrity verification fails for missing file."""
        registry.register_model(name="test-model", version="1.0.0", file_path=temp_model_file)

        # Delete the file
        Path(temp_model_file).unlink()

        valid = registry.verify_integrity("test-model", "1.0.0")
        assert valid is False

    def test_get_registry_status(self, registry, temp_model_file, temp_model_file_v2):
        """Test getting overall registry status."""
        registry.register_model(name="model-a", version="1.0.0", file_path=temp_model_file)
        registry.register_model(name="model-b", version="1.0.0", file_path=temp_model_file_v2)

        status = registry.get_registry_status()
        assert status["total_versions"] == 2
        assert status["active_versions"] == 2
        assert status["unique_models"] == 2
        assert "model-a" in status["models"]
        assert "model-b" in status["models"]

    def test_file_hash_calculation(self, registry, temp_model_file):
        """Test SHA-256 hash calculation."""
        expected_hash = hashlib.sha256(b"fake model binary data v1").hexdigest()
        actual_hash = registry._calculate_file_hash(Path(temp_model_file))
        assert actual_hash == expected_hash

    def test_signature_generation(self, registry):
        """Test signature generation is deterministic."""
        sig1 = registry._generate_signature("abc123", "1.0.0", {"key": "value"})
        sig2 = registry._generate_signature("abc123", "1.0.0", {"key": "value"})
        assert sig1 == sig2

        # Different version should produce different signature
        sig3 = registry._generate_signature("abc123", "2.0.0", {"key": "value"})
        assert sig1 != sig3


class TestRegistryRoutes:
    """Test suite for registry API routes."""

    @pytest.fixture
    def temp_db(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        Path(path).unlink(missing_ok=True)
        yield path
        gc.collect()
        for _ in range(5):
            try:
                Path(path).unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.1)

    @pytest.fixture
    def temp_model_file(self):
        fd, path = tempfile.mkstemp(suffix=".gguf")
        os.close(fd)
        Path(path).write_bytes(b"route test model data")
        yield path
        Path(path).unlink(missing_ok=True)

    @pytest.fixture
    def app(self, temp_db, temp_model_file):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from backend.registry import setup_registry_routes, get_model_registry

        app = FastAPI()
        setup_registry_routes(app, temp_db)

        # Pre-register a model for route tests
        registry = get_model_registry()
        registry.register_model(
            name="route-model",
            version="1.0.0",
            file_path=temp_model_file,
            created_by="test"
        )

        return app

    @pytest.fixture
    def client(self, app):
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_register_route(self, client, temp_model_file):
        """Test POST /api/registry/register endpoint."""
        resp = client.post("/api/registry/register", json={
            "name": "new-model",
            "version": "1.0.0",
            "file_path": temp_model_file,
            "created_by": "test-user",
            "metadata": {"purpose": "testing"}
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "new-model"
        assert data["version"] == "1.0.0"
        assert data["is_active"] is True

    def test_get_active_route(self, client):
        """Test GET /api/registry/active/{name} endpoint."""
        resp = client.get("/api/registry/active/route-model")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "route-model"
        assert data["version"] == "1.0.0"

    def test_get_active_not_found(self, client):
        """Test GET /api/registry/active/{name} for non-existent model."""
        resp = client.get("/api/registry/active/nonexistent")
        assert resp.status_code == 404

    def test_list_versions_route(self, client):
        """Test GET /api/registry/versions/{name} endpoint."""
        resp = client.get("/api/registry/versions/route-model")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["name"] == "route-model"

    def test_get_model_route(self, client):
        """Test GET /api/registry/{name}/{version} endpoint."""
        resp = client.get("/api/registry/route-model/1.0.0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "1.0.0"

    def test_get_model_not_found(self, client):
        """Test GET /api/registry/{name}/{version} for non-existent."""
        resp = client.get("/api/registry/route-model/99.0.0")
        assert resp.status_code == 404

    def test_rollback_route(self, client, temp_model_file):
        """Test POST /api/registry/rollback/{name} endpoint."""
        # Register v2 first
        client.post("/api/registry/register", json={
            "name": "route-model",
            "version": "2.0.0",
            "file_path": temp_model_file,
            "created_by": "test"
        })

        # Rollback to v1
        resp = client.post("/api/registry/rollback/route-model", json={
            "target_version": "1.0.0"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "1.0.0"

    def test_verify_integrity_route(self, client):
        """Test GET /api/registry/verify/{name}/{version} endpoint."""
        resp = client.get("/api/registry/verify/route-model/1.0.0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True

    def test_registry_status_route(self, client):
        """Test GET /api/registry/status endpoint."""
        resp = client.get("/api/registry/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_versions" in data
        assert "active_versions" in data
        assert "unique_models" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
