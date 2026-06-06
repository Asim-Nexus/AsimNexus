
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS OpenStreetMap Integration
==================================
OpenStreetMap API for location services
Includes: Geocoding, reverse geocoding, search, routing
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("OpenStreetMap")


@dataclass
class OSMLocation:
    """OpenStreetMap location data"""
    location_id: str
    address: str
    latitude: float
    longitude: float
    display_name: str
    osm_type: str


@dataclass
class OSMRoute:
    """OpenStreetMap route data"""
    route_id: str
    origin: OSMLocation
    destination: OSMLocation
    distance_meters: float
    duration_seconds: float
    geometry: List[List[float]]


class OpenStreetMap:
    """OpenStreetMap integration"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.routing_url = "https://router.project-osrm.org"
        self.locations: Dict[str, OSMLocation] = {}
        self.routes: Dict[str, OSMRoute] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize OpenStreetMap integration"""
        logger.info("🗺️  Initializing OpenStreetMap Integration...")
        logger.info("📍 Setting up geocoding")
        logger.info("🧭 Setting up routing")
        logger.info("🔍 Setting up search")
        logger.info("✅ OpenStreetMap Integration initialized")
    
    async def geocode(self, address: str) -> Optional[OSMLocation]:
        """Convert address to coordinates"""
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            result = data[0]
                            location = OSMLocation(
                                location_id=f"osm_loc_{uuid.uuid4().hex[:8]}",
                                address=address,
                                latitude=float(result["lat"]),
                                longitude=float(result["lon"]),
                                display_name=result["display_name"],
                                osm_type=result.get("osm_type", "")
                            )
                            self.locations[location.location_id] = location
                            logger.info(f"✅ Geocoded: {address}")
                            return location
                    return None
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return None
    
    async def reverse_geocode(self, lat: float, lon: float) -> Optional[OSMLocation]:
        """Convert coordinates to address"""
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/reverse",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            location = OSMLocation(
                                location_id=f"osm_loc_{uuid.uuid4().hex[:8]}",
                                address=data.get("display_name", ""),
                                latitude=lat,
                                longitude=lon,
                                display_name=data.get("display_name", ""),
                                osm_type=data.get("osm_type", "")
                            )
                            self.locations[location.location_id] = location
                            logger.info(f"✅ Reverse geocoded: {lat}, {lon}")
                            return location
                    return None
        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            return None
    
    async def get_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        profile: str = "driving"
    ) -> Optional[OSMRoute]:
        """Get route between two coordinates"""
        params = {
            "overview": "full",
            "geometries": "geojson"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.routing_url}/route/v1/{profile}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("routes"):
                            route_data = data["routes"][0]
                            
                            route = OSMRoute(
                                route_id=f"osm_route_{uuid.uuid4().hex[:8]}",
                                origin=OSMLocation(
                                    location_id=f"osm_loc_{uuid.uuid4().hex[:8]}",
                                    address="",
                                    latitude=origin_lat,
                                    longitude=origin_lon,
                                    display_name="",
                                    osm_type=""
                                ),
                                destination=OSMLocation(
                                    location_id=f"osm_loc_{uuid.uuid4().hex[:8]}",
                                    address="",
                                    latitude=dest_lat,
                                    longitude=dest_lon,
                                    display_name="",
                                    osm_type=""
                                ),
                                distance_meters=route_data["distance"],
                                duration_seconds=route_data["duration"],
                                geometry=route_data["geometry"]["coordinates"]
                            )
                            self.routes[route.route_id] = route
                            logger.info(f"✅ Route found: {route.distance_meters}m")
                            return route
                    return None
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return None
    
    async def search_places(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for places"""
        params = {
            "q": query,
            "format": "json",
            "limit": limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for place in data:
                            results.append({
                                "name": place.get("display_name"),
                                "lat": place.get("lat"),
                                "lon": place.get("lon"),
                                "osm_type": place.get("osm_type")
                            })
                        logger.info(f"✅ Found {len(results)} places")
                        return results
                    return []
        except Exception as e:
            logger.error(f"Places search error: {e}")
            return []
    
    def get_location(self, location_id: str) -> Optional[OSMLocation]:
        """Get location by ID"""
        return self.locations.get(location_id)
    
    def get_route(self, route_id: str) -> Optional[OSMRoute]:
        """Get route by ID"""
        return self.routes.get(route_id)


# Global instance
_osm: Optional[OpenStreetMap] = None


def get_osm() -> OpenStreetMap:
    """Get singleton instance"""
    global _osm
    if _osm is None:
        _osm = OpenStreetMap()
    return _osm
