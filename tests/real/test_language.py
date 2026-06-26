"""
Phase 5.1: Multi-language Support Tests
"""
import pytest
from fastapi.testclient import TestClient


def test_language_manager_exists():
    """Language manager module exists."""
    from core.language_manager import LanguageManager
    assert LanguageManager is not None


def test_language_set():
    """Set language works."""
    from core.language_manager import LanguageManager
    lm = LanguageManager()
    result = lm.set_language("en")
    assert result["status"] == "success"


def test_language_translate():
    """Translation works."""
    from core.language_manager import LanguageManager
    lm = LanguageManager()
    assert lm.translate("hello", "ne") == "नमस्ते"
    assert lm.translate("hello", "en") == "Hello"


def test_language_status_endpoint():
    """Language status endpoint works."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/language/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_language_set_endpoint():
    """Language set endpoint works."""
    from app import app
    client = TestClient(app)
    response = client.post("/api/language/set", json={"lang_code": "en"})
    assert response.status_code == 200