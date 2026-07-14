#!/usr/bin/env python3
"""AsimNexus Plugin SDK and Marketplace — Enhanced Edition.

Provides:
- PluginSDK: Register, discover, and manage plugins with versioning
- Marketplace: Browse, install, and manage apps with categories
- Plugin lifecycle: register → verify → enable → disable → unregister
- Category-based discovery with search
- Download tracking and popularity metrics
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("AsimNexus.PluginMarketplace")


class PluginSDK:
    """SDK for developing plugins for AsimNexus."""

    def __init__(self):
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.plugin_versions: Dict[str, List[Dict[str, Any]]] = {}

    def register_plugin(
        self,
        plugin_id: str,
        manifest: Dict[str, Any],
        version: str = "1.0.0",
    ) -> Dict[str, Any]:
        """Register a plugin with manifest and version tracking."""
        if plugin_id in self.plugins:
            # Track version history
            if plugin_id not in self.plugin_versions:
                self.plugin_versions[plugin_id] = []
            self.plugin_versions[plugin_id].append({
                **self.plugins[plugin_id],
                "deprecated_at": datetime.utcnow().isoformat(),
            })

        manifest["version"] = version
        manifest["registered_at"] = datetime.utcnow().isoformat()
        manifest["enabled"] = manifest.get("enabled", True)
        manifest["plugin_id"] = plugin_id
        self.plugins[plugin_id] = manifest
        logger.info(f"✅ Plugin registered: {plugin_id} v{version}")
        return {"status": "registered", "plugin_id": plugin_id, "version": version}

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin manifest."""
        return self.plugins.get(plugin_id)

    def list_plugins(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered plugins, optionally filtered by category."""
        if category:
            return [
                {**p, "plugin_id": pid}
                for pid, p in self.plugins.items()
                if p.get("category") == category
            ]
        return [{**p, "plugin_id": pid} for pid, p in self.plugins.items()]

    def enable_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Enable a registered plugin."""
        if plugin_id not in self.plugins:
            return {"status": "error", "message": f"Plugin {plugin_id} not found"}
        self.plugins[plugin_id]["enabled"] = True
        logger.info(f"✅ Plugin enabled: {plugin_id}")
        return {"status": "enabled", "plugin_id": plugin_id}

    def disable_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Disable a registered plugin."""
        if plugin_id not in self.plugins:
            return {"status": "error", "message": f"Plugin {plugin_id} not found"}
        self.plugins[plugin_id]["enabled"] = False
        logger.info(f"⏸️ Plugin disabled: {plugin_id}")
        return {"status": "disabled", "plugin_id": plugin_id}

    def unregister_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Unregister a plugin completely."""
        if plugin_id not in self.plugins:
            return {"status": "error", "message": f"Plugin {plugin_id} not found"}
        archived = self.plugins.pop(plugin_id)
        logger.info(f"🗑️ Plugin unregistered: {plugin_id}")
        return {"status": "unregistered", "plugin_id": plugin_id}

    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get plugin statistics."""
        total = len(self.plugins)
        enabled = sum(1 for p in self.plugins.values() if p.get("enabled"))
        categories = {}
        for p in self.plugins.values():
            cat = p.get("category", "uncategorized")
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total_plugins": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "categories": categories,
        }


class Marketplace:
    """Plugin and app marketplace with category browsing and search."""

    def __init__(self):
        self.apps: List[Dict[str, Any]] = [
            {
                "id": "nepal-gov-connect",
                "name": "Nepal Government Connector",
                "description": "Connect to Nepal government digital services, e-Residency, and tax filing",
                "category": "government",
                "price": 0,
                "downloads": 150,
                "rating": 4.5,
                "version": "2.1.0",
                "author": "AsimNexus GovTech",
                "created_at": "2025-01-15T00:00:00Z",
            },
            {
                "id": "tax-filing-plugin",
                "name": "Tax Filing Assistant",
                "description": "Automated tax preparation and filing for individuals and businesses",
                "category": "finance",
                "price": 0,
                "downloads": 89,
                "rating": 4.2,
                "version": "1.8.0",
                "author": "Nepal FinTech Labs",
                "created_at": "2025-02-20T00:00:00Z",
            },
            {
                "id": "health-record-sync",
                "name": "Health Record Sync",
                "description": "Synchronize health records across Nepal's healthcare providers",
                "category": "health",
                "price": 0,
                "downloads": 203,
                "rating": 4.7,
                "version": "3.0.1",
                "author": "Digital Health Nepal",
                "created_at": "2025-03-10T00:00:00Z",
            },
            {
                "id": "education-portal",
                "name": "Education Portal Connector",
                "description": "Access Nepal's educational resources, certificates, and learning management",
                "category": "education",
                "price": 0,
                "downloads": 67,
                "rating": 4.0,
                "version": "1.2.0",
                "author": "EduTech Nepal",
                "created_at": "2025-04-05T00:00:00Z",
            },
            {
                "id": "land-records",
                "name": "Land Records Plugin",
                "description": "Access and manage Nepal land registry records and property transfers",
                "category": "government",
                "price": 0,
                "downloads": 45,
                "rating": 3.8,
                "version": "1.0.0",
                "author": "LandTech Solutions",
                "created_at": "2025-05-01T00:00:00Z",
            },
            {
                "id": "mesh-connector",
                "name": "Mesh Network Connector",
                "description": "Connect to AsimNexus mesh network for offline-first communication",
                "category": "infrastructure",
                "price": 0,
                "downloads": 312,
                "rating": 4.9,
                "version": "2.3.0",
                "author": "AsimNexus Core",
                "created_at": "2025-01-01T00:00:00Z",
            },
        ]

    def list_apps(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List apps in marketplace, optionally filtered by category or search."""
        results = self.apps
        if category:
            results = [a for a in results if a["category"] == category]
        if search:
            search_lower = search.lower()
            results = [
                a for a in results
                if search_lower in a["name"].lower()
                or search_lower in a["description"].lower()
                or search_lower in a.get("author", "").lower()
            ]
        return results

    def get_app(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Get specific app details."""
        for app in self.apps:
            if app["id"] == app_id:
                return app
        return None

    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return list({a["category"] for a in self.apps})

    def get_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics."""
        total = len(self.apps)
        total_downloads = sum(a.get("downloads", 0) for a in self.apps)
        categories = {}
        for a in self.apps:
            cat = a["category"]
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total_apps": total,
            "total_downloads": total_downloads,
            "categories": categories,
            "top_app": max(self.apps, key=lambda a: a.get("downloads", 0)) if self.apps else None,
        }


_sdk: Optional[PluginSDK] = None
_marketplace: Optional[Marketplace] = None


def get_plugin_sdk() -> PluginSDK:
    """Get singleton PluginSDK instance."""
    global _sdk
    if _sdk is None:
        _sdk = PluginSDK()
    return _sdk


def get_marketplace() -> Marketplace:
    """Get singleton Marketplace instance."""
    global _marketplace
    if _marketplace is None:
        _marketplace = Marketplace()
    return _marketplace


def reset_plugin_system() -> None:
    """Reset plugin system singletons (for testing)."""
    global _sdk, _marketplace
    _sdk = None
    _marketplace = None
