#!/usr/bin/env python3
"""AsimNexus Plugin SDK and Marketplace"""
from typing import Dict, Any, List, Optional


class PluginSDK:
    """SDK for developing plugins for AsimNexus."""

    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.marketplace_apps: List[Dict[str, Any]] = []

    def register_plugin(self, plugin_id: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Register a plugin with manifest."""
        self.plugins[plugin_id] = manifest
        return {"status": "registered", "plugin_id": plugin_id}

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin manifest."""
        return self.plugins.get(plugin_id)

    def list_plugins(self) -> List[str]:
        """List all registered plugin IDs."""
        return list(self.plugins.keys())


class Marketplace:
    """Plugin and app marketplace."""

    def __init__(self):
        self.apps: List[Dict[str, Any]] = [
            {"id": "nepal-gov-connect", "name": "Nepal Government Connector", "category": "government", "price": 0, "downloads": 150},
            {"id": "tax-filing-plugin", "name": "Tax Filing Assistant", "category": "finance", "price": 0, "downloads": 89},
            {"id": "health-record-sync", "name": "Health Record Sync", "category": "health", "price": 0, "downloads": 203},
        ]

    def list_apps(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List apps in marketplace, optionally filtered by category."""
        if category:
            return [a for a in self.apps if a["category"] == category]
        return self.apps

    def get_app(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Get specific app details."""
        for app in self.apps:
            if app["id"] == app_id:
                return app
        return None


_sdk: Optional[PluginSDK] = None
_marketplace: Optional[Marketplace] = None


def get_plugin_sdk() -> PluginSDK:
    global _sdk
    if _sdk is None:
        _sdk = PluginSDK()
    return _sdk


def get_marketplace() -> Marketplace:
    global _marketplace
    if _marketplace is None:
        _marketplace = Marketplace()
    return _marketplace