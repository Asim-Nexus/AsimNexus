"""
AsimNexus CDN Manager Stub
===========================
Stub module for CDN edge location management.
Provides sensible defaults until full CDN implementation is ready.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("AsimNexus.CDN")


class CDNManager:
    """CDN edge location manager (stub)."""

    def __init__(self):
        self._locations: List[Dict[str, Any]] = [
            {"id": "us-west", "name": "US West", "country": "US", "lat": 37.7749, "lon": -122.4194, "status": "active"},
            {"id": "us-east", "name": "US East", "country": "US", "lat": 40.7128, "lon": -74.0060, "status": "active"},
            {"id": "eu-west", "name": "EU West", "country": "DE", "lat": 50.1109, "lon": 8.6821, "status": "active"},
            {"id": "eu-central", "name": "EU Central", "country": "PL", "lat": 52.2297, "lon": 21.0122, "status": "active"},
            {"id": "ap-south", "name": "Asia South", "country": "IN", "lat": 19.0760, "lon": 72.8777, "status": "active"},
            {"id": "ap-east", "name": "Asia East", "country": "JP", "lat": 35.6762, "lon": 139.6503, "status": "active"},
            {"id": "sa-east", "name": "South America", "country": "BR", "lat": -23.5505, "lon": -46.6333, "status": "active"},
            {"id": "me-central", "name": "Middle East", "country": "AE", "lat": 25.2048, "lon": 55.2708, "status": "active"},
        ]

    def get_locations(self) -> List[Dict[str, Any]]:
        """Get all CDN edge locations."""
        return self._locations

    def get_active_count(self) -> int:
        """Get count of active CDN nodes."""
        return sum(1 for loc in self._locations if loc.get("status") == "active")

    def is_healthy(self) -> bool:
        """Check if CDN is healthy."""
        return self.get_active_count() > 0

    def get_optimal_route(self, country_code: str, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Get optimal CDN routing for a location."""
        # Simple nearest-by-country heuristic
        for loc in self._locations:
            if loc["country"] == country_code.upper():
                return {"edge": loc, "route": "direct", "latency_ms": 10}
        # Fallback to first active location
        for loc in self._locations:
            if loc.get("status") == "active":
                return {"edge": loc, "route": "fallback", "latency_ms": 100}
        return {"edge": None, "route": "unavailable", "latency_ms": -1}

    def get_nearest_node(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Find nearest CDN edge location by coordinates."""
        import math
        nearest = None
        min_dist = float("inf")
        for loc in self._locations:
            if loc.get("status") != "active":
                continue
            dist = math.sqrt((loc["lat"] - lat) ** 2 + (loc["lon"] - lon) ** 2)
            if dist < min_dist:
                min_dist = dist
                nearest = loc
        return nearest


# Singleton
_cdn_manager: Optional[CDNManager] = None


def get_cdn_manager() -> CDNManager:
    """Get CDN manager singleton."""
    global _cdn_manager
    if _cdn_manager is None:
        _cdn_manager = CDNManager()
    return _cdn_manager
