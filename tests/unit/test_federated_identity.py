import pytest
from core.identity.federated_identity import FederatedIdentity

def test_federated_identity_creation():
    identity = FederatedIdentity("user123")
    assert identity.user_id == "user123"
    assert identity.base["uid"] == "user123"

def test_federated_identity_twins():
    identity = FederatedIdentity("user123")
    citizen = identity.get_twin("citizen")
    company = identity.get_twin("company")
    government = identity.get_twin("government")
    
    assert citizen["twin_id"] == "citizen_user123"
    assert company["twin_id"] == "company_user123"
    assert government["twin_id"] == "government_user123"

def test_federated_identity_fallback():
    identity = FederatedIdentity("user123")
    fallback = identity.get_twin("unknown_mode")
    assert fallback["twin_id"] == "citizen_user123"
