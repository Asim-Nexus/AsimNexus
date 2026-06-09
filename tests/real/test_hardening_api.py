#!/usr/bin/env python3
"""
ASIMNEXUS Hardening & Security API Tests
==========================================
Tests for all hardening endpoints: health check, system integrity verification,
and security layers listing.
"""

import sys
import os
import json
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from fastapi import FastAPI


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_security_modules():
    """Mock all security module imports used by hardening API."""
    patches = []

    # Mock RBAC
    mock_rbac = MagicMock()
    mock_rbac.get_all_permissions.return_value = {"admin": ["read", "write", "delete"]}
    mock_get_rbac = MagicMock(return_value=mock_rbac)
    patches.append(patch("security.rbac.get_rbac", mock_get_rbac))

    # Mock InputSanitizer
    mock_sanitizer = MagicMock()
    mock_sanitizer.get_rules.return_value = {"sql_injection": True, "xss": True}
    mock_input_sanitizer = MagicMock(return_value=mock_sanitizer)
    patches.append(patch("security.input_sanitizer.InputSanitizer", mock_input_sanitizer))

    # Mock AuditLogger
    mock_audit_logger = MagicMock()
    patches.append(patch("security.audit_logger.AuditLogger", mock_audit_logger))

    # Mock ZeroTrust
    mock_zt = MagicMock()
    mock_zt.get_policy_summary.return_value = {"verify_all": True, "least_privilege": True}
    patches.append(patch("security.zero_trust.ZeroTrust", mock_zt))

    # Mock RiskValidator
    mock_rv = MagicMock()
    patches.append(patch("security.risk_validator.RiskValidator", mock_rv))

    # Mock DharmaChakraConstitution
    mock_dc = MagicMock()
    mock_dc.constitution_hash = "abc123def456"
    mock_dc.government_veto_threshold = 0.51
    mock_dc.private_sector_threshold = 0.49
    mock_dc._initialize_sector_permissions.return_value = {
        "hospital": {"gov_share": 0.51, "private_share": 0.49},
        "hotel": {"gov_share": 0.51, "private_share": 0.49},
        "education": {"gov_share": 0.51, "private_share": 0.49},
        "banking": {"gov_share": 0.51, "private_share": 0.49},
    }
    patches.append(patch(
        "core.dharma_chakra.constitution.DharmaChakraConstitution",
        return_value=mock_dc,
    ))

    # Mock PowerBalanceConstitution
    mock_pbc = MagicMock()
    mock_SECTOR_BALANCE_MAP = {
        "hospital": {"gov": 51, "private": 49},
        "hotel": {"gov": 51, "private": 49},
        "education": {"gov": 51, "private": 49},
        "banking": {"gov": 51, "private": 49},
    }
    patches.append(patch(
        "security.power_balance_constitution.PowerBalanceConstitution",
        return_value=mock_pbc,
    ))
    patches.append(patch(
        "security.power_balance_constitution.SECTOR_BALANCE_MAP",
        mock_SECTOR_BALANCE_MAP,
        create=True,
    ))

    # Start all patches
    for p in patches:
        p.start()

    yield

    # Stop all patches
    for p in patches:
        p.stop()


@pytest.fixture
def client(mock_security_modules):
    """Create test client with all security modules mocked."""
    app = FastAPI()
    from core.api_endpoints.hardening_api import router
    app.include_router(router)
    return TestClient(app)


# ─── Hardening Health Tests ──────────────────────────────────────────────────


class TestHardeningHealth:
    """Tests for the hardening health check endpoint."""

    def test_hardening_health_all_available(self, client):
        """GET /api/hardening/health returns healthy when all modules available."""
        response = client.get("/api/hardening/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["all_modules_available"] is True
        assert "modules" in data
        assert data["modules"]["rbac"]["available"] is True
        assert data["modules"]["input_sanitizer"]["available"] is True
        assert data["modules"]["audit_logger"]["available"] is True
        assert data["modules"]["zero_trust"]["available"] is True
        assert data["modules"]["risk_validator"]["available"] is True
        assert data["modules"]["dharma_chakra"]["available"] is True
        assert "timestamp" in data

    def test_hardening_health_with_failures(self, mock_security_modules):
        """Health returns degraded when modules are unavailable."""
        # Re-patch to simulate failures
        from security import rbac as rbac_module
        original_get_rbac = rbac_module.get_rbac

        def failing_get_rbac():
            raise ImportError("RBAC module not available")

        with patch("security.rbac.get_rbac", side_effect=failing_get_rbac):
            app = FastAPI()
            from core.api_endpoints.hardening_api import router
            app.include_router(router)
            c = TestClient(app)
            response = c.get("/api/hardening/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["all_modules_available"] is False
            assert data["modules"]["rbac"]["available"] is False

    def test_hardening_health_government_share(self, client):
        """Health response includes government/private shares from constitution."""
        response = client.get("/api/hardening/health")
        data = response.json()
        dharma = data["modules"]["dharma_chakra"]
        assert dharma["government_share"] == 0.51
        assert dharma["private_share"] == 0.49


# ─── System Integrity Verification Tests ─────────────────────────────────────


class TestHardeningVerify:
    """Tests for system integrity verification endpoint."""

    def test_verify_system_integrity_all_verified(self, client):
        """GET /api/hardening/verify returns verified for all layers."""
        response = client.get("/api/hardening/verify")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "verified"
        assert data["all_layers_verified"] is True
        assert data["layers"]["rbac"]["status"] == "verified"
        assert data["layers"]["input_sanitizer"]["status"] == "verified"
        assert data["layers"]["zero_trust"]["status"] == "verified"
        assert data["layers"]["dharma_chakra"]["status"] == "verified"
        assert "timestamp" in data

    def test_verify_system_integrity_with_failures(self, client):
        """Verify returns degraded when some layers fail."""
        with patch("security.input_sanitizer.InputSanitizer",
                   side_effect=ImportError("Not available")):
            app = FastAPI()
            from core.api_endpoints.hardening_api import router
            app.include_router(router)
            c = TestClient(app)
            response = c.get("/api/hardening/verify")
            data = response.json()
            assert data["all_layers_verified"] is False
            assert data["layers"]["input_sanitizer"]["status"] == "unavailable"


# ─── Security Layers Listing Tests ───────────────────────────────────────────


class TestSecurityLayers:
    """Tests for security layers listing endpoint."""

    def test_list_security_layers_all_active(self, client):
        """GET /api/hardening/security-layers returns all 7 layers."""
        response = client.get("/api/hardening/security-layers")
        assert response.status_code == 200
        data = response.json()
        assert data["total_layers"] == 7
        assert data["active_layers"] == 7
        assert data["protection_level"] == "7/7"
        assert len(data["layers"]) == 7

    def test_security_layers_structure(self, client):
        """Each layer has required fields."""
        response = client.get("/api/hardening/security-layers")
        data = response.json()
        for layer in data["layers"]:
            assert "layer" in layer
            assert "name" in layer
            assert "status" in layer
            assert "description" in layer

    def test_security_layers_ordering(self, client):
        """Layers are ordered 1-7."""
        response = client.get("/api/hardening/security-layers")
        data = response.json()
        layers = data["layers"]
        for i, layer in enumerate(layers, 1):
            assert layer["layer"] == i

    def test_security_layers_names(self, client):
        """Layer names match expected values."""
        response = client.get("/api/hardening/security-layers")
        data = response.json()
        names = [l["name"] for l in data["layers"]]
        assert "Dharma-Chakra Constitution" in names
        assert "Role-Based Access Control" in names
        assert "Input Sanitization" in names
        assert "Audit Logger" in names
        assert "Zero Trust" in names
        assert "Risk Validation" in names
        assert "Power Balance Constitution" in names


# ─── Error Handling Tests ────────────────────────────────────────────────────


class TestHardeningErrorHandling:
    """Tests for error handling in hardening endpoints."""

    def test_hardening_health_graceful_degradation(self, client):
        """Health endpoint gracefully handles partial failures."""
        with patch("security.zero_trust.ZeroTrust",
                   side_effect=Exception("Connection refused")):
            app = FastAPI()
            from core.api_endpoints.hardening_api import router
            app.include_router(router)
            c = TestClient(app)
            response = c.get("/api/hardening/health")
            assert response.status_code == 200
            data = response.json()
            assert data["modules"]["zero_trust"]["available"] is False
            assert "error" in data["modules"]["zero_trust"]
