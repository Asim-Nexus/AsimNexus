"""
Nepal Government Layer Tests
"""
import pytest
from fastapi.testclient import TestClient


def test_nepal_ministries():
    """Get Nepal ministries."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/nepal/ministries")
    assert response.status_code == 200
    data = response.json().get("data", response.json())
    assert len(data) >= 18


def test_nepal_provinces():
    """Get Nepal provinces."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/nepal/provinces")
    assert response.status_code == 200
    data = response.json().get("data", response.json())
    assert len(data) >= 7


def test_nepal_districts():
    """Get Nepal districts."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/nepal/districts")
    assert response.status_code == 200
    data = response.json().get("data", response.json())
    assert len(data) >= 77


def test_nepal_gov_layer():
    """Get Nepal gov layer status."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/nepal/gov-layer/status")
    assert response.status_code == 200


def test_nepal_gov_submit():
    """Submit Nepal government action."""
    from app import app
    client = TestClient(app)
    response = client.post("/api/nepal/gov-layer/submit", json={
        "action_type": "data_request",
        "entity": "अर्थ मन्त्रालय",
        "jurisdiction": "NP",
        "description": "नेपाली सरकार विकास"
    })
    assert response.status_code == 200