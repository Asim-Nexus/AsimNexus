"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""Pytest configuration and shared fixtures.

Provides shared fixtures used across all test directories:
  - event_loop: Event loop for async tests
  - test_client: FastAPI TestClient pointing to the backend app
  - auth_user: Creates a test user and returns headers with JWT
  - temp_db: Overrides DB to use in-memory SQLite for tests
  - mock_biometric: Mocks BiometricHardwareGate to return success for Level-3 tests
  - mock_state_manager: Mock state manager
  - mock_model_connector: Mock model connector
  - sample_api_keys: Sample API keys
"""

import os
import sys
import pytest
import asyncio
import tempfile
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime
from pathlib import Path

def pytest_configure(config):
    """Configure pytest-asyncio default mode."""
    config.option.asyncio_mode = "auto"

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_state_manager():
    """Mock state manager for testing."""
    manager = Mock()
    manager.get = Mock(return_value=None)
    manager.set = Mock(return_value=True)
    manager.delete = Mock(return_value=True)
    return manager

@pytest.fixture
def mock_model_connector():
    """Mock model connector for testing."""
    connector = Mock()
    connector.generate = Mock(return_value="Test response")
    connector.get_model_for_task = Mock(return_value=Mock(name="test_model"))
    return connector

@pytest.fixture
def sample_api_keys():
    """Sample API keys for testing."""
    return {
        'openai': 'sk-test123',
        'anthropic': 'sk-ant-test123',
        'gemini': 'test-key-123'
    }

# ──────────────────────────────────────────────────────────────────────────── #
# Minimal App Fixture for API Tests (RC2)
# ──────────────────────────────────────────────────────────────────────────── #

@pytest.fixture(scope="session")
def app():
    """Build the FastAPI application - minimal version for testing."""
    try:
        # Try to import the real app
        from app import app as real_app
        return real_app
    except ImportError:
        # Create minimal FastAPI app for testing
        from fastapi import FastAPI
        test_app = FastAPI(title="AsimNexus Test")
        return test_app

@pytest.fixture
def test_client(app):
    """FastAPI TestClient pointing to the backend application."""
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client

@pytest.fixture
def temp_db():
    """Override DB to use a temporary SQLite database for tests."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name
    yield db_path
    try:
        os.unlink(db_path)
    except OSError:
        pass

@pytest.fixture
def auth_user(temp_db):
    """Create a test user and return authorization headers with JWT."""
    try:
        from core.security.auth_middleware import AuthManager
        auth_mgr = AuthManager()
        token = create_access_token({"user_id": "test", "email": "test@test.com"})
        return {
            "headers": {"Authorization": f"Bearer {token}"},
            "token": token,
            "user_id": "test",
            "email": "test@test.com",
        }
    except ImportError:
        # Fallback mock user
        return {
            "headers": {"Authorization": "Bearer test-token"},
            "token": "test-token",
            "user_id": "test",
            "email": "test@test.com",
        }

@pytest.fixture
def mock_biometric():
    """Mock BiometricHardwareGate to automatically pass biometric checks."""
    gate_instance = MagicMock()
    gate_instance.verify_biometric = AsyncMock(return_value={
        "verified": True,
        "confidence": 0.99,
        "method": "mock_biometric",
    })
    gate_instance.verify_and_lock = AsyncMock(return_value={
        "verified": True,
        "confidence": 0.99,
        "method": "mock_biometric",
        "locked": False,
    })
    gate_instance.get_status = MagicMock(return_value={
        "locked": False,
        "verified": True,
        "method": "mock_biometric",
        "timestamp": datetime.utcnow().isoformat(),
    })
    yield gate_instance

# Helper function for auth
def create_access_token(payload: dict) -> str:
    """Create a test JWT token."""
    import base64
    import json
    import time
    header = {"alg": "HS256", "typ": "JWT"}
    payload["exp"] = time.time() + 3600
    parts = [
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('='),
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('='),
        "test-signature"
    ]
    return ".".join(parts)