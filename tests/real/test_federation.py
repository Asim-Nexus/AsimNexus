"""
Phase 5.2: Federation Network Tests
"""
import pytest
from fastapi.testclient import TestClient

def test_federation_manager_exists():
    """Federation manager module exists."""
    from core.federation.global_federation import GlobalFederationManager
    assert GlobalFederationManager is not None

def test_federation_add_peer():
    """Add peer to federation."""
    from core.federation.global_federation import GlobalFederationManager
    fed = GlobalFederationManager(node_id="test_node")
    peer = fed.add_peer("did:test", "ws://localhost:9999")
    assert peer.peer_id is not None
    assert peer.endpoint == "ws://localhost:9999"

def test_federation_consent():
    """Consent to sync with peer."""
    from core.federation.global_federation import GlobalFederationManager
    fed = GlobalFederationManager(node_id="test_node2")
    fed.add_peer("did:test2", "ws://localhost:9999")
    fed.consent_peer(list(fed._peers.keys())[0])
    assert len(fed._consent) == 1

def test_federation_status_endpoint():
    """Federation status endpoint works."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/federation/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data