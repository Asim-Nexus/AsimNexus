"""
Phase 5.3: App Ecosystem (Plugin SDK, Marketplace) Tests
"""
import pytest
from fastapi.testclient import TestClient


def test_plugin_sdk_exists():
    """Plugin SDK module exists."""
    from core.plugin_marketplace import PluginSDK
    assert PluginSDK is not None


def test_plugin_register():
    """Register plugin works."""
    from core.plugin_marketplace import PluginSDK
    sdk = PluginSDK()
    result = sdk.register_plugin("test", {"name": "Test Plugin"})
    assert result["status"] == "registered"


def test_marketplace_exists():
    """Marketplace module exists."""
    from core.plugin_marketplace import Marketplace
    assert Marketplace is not None


def test_marketplace_list():
    """List marketplace apps."""
    from core.plugin_marketplace import Marketplace
    mp = Marketplace()
    apps = mp.list_apps()
    assert len(apps) >= 3


def test_marketplace_list_by_category():
    """List marketplace apps by category."""
    from core.plugin_marketplace import Marketplace
    mp = Marketplace()
    gov_apps = mp.list_apps("government")
    assert len(gov_apps) >= 1


def test_marketplace_status_endpoint():
    """Marketplace endpoint works."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/marketplace/apps")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data