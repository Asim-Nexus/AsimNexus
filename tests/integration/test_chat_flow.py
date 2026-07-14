import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app import app

client = TestClient(app)

def _get_auth_headers():
    """Login with admin credentials via the real AuthManager and return auth headers."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
        "device_id": "test-chat",
        "mode": "personal",
    })
    body = resp.json()
    # Response is wrapped in {"status": "ok", "data": {...}}
    data = body.get("data", body)
    # The real AuthManager returns Token model with access_token
    token = data.get("access_token") or data.get("token")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def test_chat_citizen_mode():
    headers = _get_auth_headers()
    response = client.post("/api/v1/chat", json={
        "message": "check my taxes",
        "user_id": "testuser",
        "mode": "citizen"
    }, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"
    data = body.get("data", {})
    assert "audit_id" in data

def test_chat_company_mode():
    headers = _get_auth_headers()
    response = client.post("/api/v1/chat", json={
        "message": "pay company VAT",
        "user_id": "testuser",
        "mode": "company"
    }, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"
    data = body.get("data", {})
    assert "audit_id" in data

def test_chat_hybrid_mode():
    headers = _get_auth_headers()
    response = client.post("/api/v1/chat", json={
        "message": "submit VAT to government",
        "user_id": "testuser",
        "mode": "hybrid"
    }, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"
    data = body.get("data", {})
    assert "audit_id" in data
