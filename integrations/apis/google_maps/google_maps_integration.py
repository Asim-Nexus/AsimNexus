
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Google Maps Integration
==================================
Google Maps API for location services
Includes: Geocoding, directions, places, distance matrix
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("GoogleMaps")


class LocationType(Enum):
    """Types of location queries"""
    ADDRESS = "address"
    PLACE = "place"
    LATLNG = "latlng"


@dataclass
class Location:
    """Location data"""
    location_id: str
    address: str
    latitude: float
    longitude: float
    place_id: Optional[str]
    formatted_address: str


@dataclass
class Route:
    """Route data"""
    route_id: str
    origin: Location
    destination: Location
    distance_meters: float
    duration_seconds: float
    steps: List[str]


class GoogleMaps:
    """Google Maps integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.locations: Dict[str, Location] = {}
        self.routes: Dict[str, Route] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Google Maps integration"""
        logger.info("🗺️  Initializing Google Maps Integration...")
        logger.info("📍 Setting up geocoding")
        logger.info("🧭 Setting up directions")
        logger.info("🏪 Setting up places search")
        logger.info("✅ Google Maps Integration initialized")
    
    async def geocode(self, address: str) -> Optional[Location]:
        """Convert address to coordinates"""
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            return None
        
        params = {
            "address": address,
            "key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/geocode/json",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("results"):
                            result = data["results"][0]
                            location = Location(
                                location_id=f"loc_{uuid.uuid4().hex[:8]}",
                                address=address,
                                latitude=result["geometry"]["location"]["lat"],
                                longitude=result["geometry"]["location"]["lng"],
                                place_id=result.get("place_id"),
                                formatted_address=result["formatted_address"]
                            )
                            self.locations[location.location_id] = location
                            logger.info(f"✅ Geocoded: {address}")
                            return location
                    return None
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return None
    
    async def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving"
    ) -> Optional[Route]:
        """Get directions between two locations"""
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            return None
        
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/directions/json",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("routes"):
                            route_data = data["routes"][0]
                            leg = route_data["legs"][0]
                            
                            route = Route(
                                route_id=f"route_{uuid.uuid4().hex[:8]}",
                                origin=Location(
                                    location_id=f"loc_{uuid.uuid4().hex[:8]}",
                                    address=origin,
                                    latitude=leg["start_location"]["lat"],
                                    longitude=leg["start_location"]["lng"],
                                    place_id=None,
                                    formatted_address=leg["start_address"]
                                ),
                                destination=Location(
                                    location_id=f"loc_{uuid.uuid4().hex[:8]}",
                                    address=destination,
                                    latitude=leg["end_location"]["lat"],
                                    longitude=leg["end_location"]["lng"],
                                    place_id=None,
                                    formatted_address=leg["end_address"]
                                ),
                                distance_meters=leg["distance"]["value"],
                                duration_seconds=leg["duration"]["value"],
                                steps=[step["html_instructions"] for step in leg["steps"]]
                            )
                            self.routes[route.route_id] = route
                            logger.info(f"✅ Directions found: {origin} -> {destination}")
                            return route
                    return None
        except Exception as e:
            logger.error(f"Directions error: {e}")
            return None
    
    async def search_places(
        self,
        query: str,
        location: Optional[str] = None,
        radius: int = 5000
    ) -> List[Dict[str, Any]]:
        """Search for places"""
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            return []
        
        params = {
            "query": query,
            "radius": radius,
            "key": self.api_key
        }
        
        if location:
            params["location"] = location
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/place/textsearch/json",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for place in data.get("results", []):
                            results.append({
                                "name": place.get("name"),
                                "address": place.get("formatted_address"),
                                "rating": place.get("rating"),
                                "place_id": place.get("place_id")
                            })
                        logger.info(f"✅ Found {len(results)} places")
                        return results
                    return []
        except Exception as e:
            logger.error(f"Places search error: {e}")
            return []
    
    def get_location(self, location_id: str) -> Optional[Location]:
        """Get location by ID"""
        return self.locations.get(location_id)
    
    def get_route(self, route_id: str) -> Optional[Route]:
        """Get route by ID"""
        return self.routes.get(route_id)


# Global instance
_google_maps: Optional[GoogleMaps] = None


def get_google_maps() -> GoogleMaps:
    """Get singleton instance"""
    global _google_maps
    if _google_maps is None:
        _google_maps = GoogleMaps()
    return _google_maps
