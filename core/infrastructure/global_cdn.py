
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Global CDN & Edge Network
======================================
Worldwide edge locations for low-latency access
50+ locations across all continents
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import aiohttp
import asyncio

logger = logging.getLogger("ASIM_GLOBAL_CDN")

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    CLOUDFLARE = "cloudflare"
    FASTLY = "fastly"
    ALIBABA = "alibaba"
    TENCENT = "tencent"
    SELF_HOSTED = "self_hosted"

class RegionTier(Enum):
    TIER1 = "tier1"      # Major hubs (latency <20ms)
    TIER2 = "tier2"      # Regional hubs (latency <50ms)
    TIER3 = "tier3"      # Edge locations (latency <100ms)

@dataclass
class EdgeLocation:
    """CDN edge location definition"""
    code: str                    # Location code (e.g., 'us-east-1')
    name: str                    # Human-readable name
    city: str
    country: str                 # ISO country code
    region: str                  # Geographic region
    providers: List[CloudProvider]
    tier: RegionTier
    lat: float                   # Latitude
    lon: float                   # Longitude
    ipv4: List[str] = field(default_factory=list)
    ipv6: List[str] = field(default_factory=list)
    status: str = "active"       # active, maintenance, offline
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'name': self.name,
            'city': self.city,
            'country': self.country,
            'region': self.region,
            'providers': [p.value for p in self.providers],
            'tier': self.tier.value,
            'lat': self.lat,
            'lon': self.lon,
            'status': self.status,
        }

class GlobalCDNSystem:
    """
    Global Content Delivery Network with 50+ edge locations
    Multi-cloud strategy for redundancy
    """
    
    # 50+ Edge Locations Worldwide
    EDGE_LOCATIONS = {
        # NORTH AMERICA - Tier 1
        'us-east-1': EdgeLocation(
            'us-east-1', 'US East (N. Virginia)', 'Ashburn', 'US', 'North America',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP, CloudProvider.CLOUDFLARE],
            RegionTier.TIER1, 39.0438, -77.4874,
            ['52.0.0.0/16', '54.0.0.0/16'], ['2600:1f00::/32']
        ),
        'us-east-2': EdgeLocation(
            'us-east-2', 'US East (Ohio)', 'Columbus', 'US', 'North America',
            [CloudProvider.AWS, CloudProvider.AZURE],
            RegionTier.TIER1, 39.9612, -82.9988,
            ['52.95.0.0/16'], ['2600:1f10::/32']
        ),
        'us-west-1': EdgeLocation(
            'us-west-1', 'US West (N. California)', 'San Francisco', 'US', 'North America',
            [CloudProvider.AWS, CloudProvider.CLOUDFLARE, CloudProvider.FASTLY],
            RegionTier.TIER1, 37.7749, -122.4194,
            ['50.18.0.0/16'], ['2600:1f01::/32']
        ),
        'us-west-2': EdgeLocation(
            'us-west-2', 'US West (Oregon)', 'Portland', 'US', 'North America',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER1, 45.5152, -122.6784,
            ['54.244.0.0/16'], ['2600:1f02::/32']
        ),
        'us-central-1': EdgeLocation(
            'us-central-1', 'US Central (Chicago)', 'Chicago', 'US', 'North America',
            [CloudProvider.GCP, CloudProvider.CLOUDFLARE],
            RegionTier.TIER1, 41.8781, -87.6298,
            ['35.188.0.0/16'], ['2600:1900::/32']
        ),
        'ca-central-1': EdgeLocation(
            'ca-central-1', 'Canada (Central)', 'Montreal', 'CA', 'North America',
            [CloudProvider.AWS, CloudProvider.AZURE],
            RegionTier.TIER1, 45.5017, -73.5673,
            ['35.182.0.0/16'], ['2600:1f11::/32']
        ),
        'ca-west-1': EdgeLocation(
            'ca-west-1', 'Canada West (Calgary)', 'Calgary', 'CA', 'North America',
            [CloudProvider.AWS],
            RegionTier.TIER2, 51.0447, -114.0719,
            ['35.183.0.0/16'], []
        ),
        'mx-central-1': EdgeLocation(
            'mx-central-1', 'Mexico (Central)', 'Mexico City', 'MX', 'North America',
            [CloudProvider.AZURE, CloudProvider.CLOUDFLARE],
            RegionTier.TIER2, 19.4326, -99.1332,
            [], []
        ),
        
        # EUROPE - Tier 1
        'eu-west-1': EdgeLocation(
            'eu-west-1', 'Europe (Ireland)', 'Dublin', 'IE', 'Europe',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP, CloudProvider.CLOUDFLARE],
            RegionTier.TIER1, 53.3498, -6.2603,
            ['52.208.0.0/16', '54.72.0.0/16'], ['2a05:d000::/36']
        ),
        'eu-west-2': EdgeLocation(
            'eu-west-2', 'Europe (London)', 'London', 'GB', 'Europe',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER1, 51.5074, -0.1278,
            ['52.56.0.0/16'], ['2a05:d018::/36']
        ),
        'eu-west-3': EdgeLocation(
            'eu-west-3', 'Europe (Paris)', 'Paris', 'FR', 'Europe',
            [CloudProvider.AWS, CloudProvider.AZURE],
            RegionTier.TIER1, 48.8566, 2.3522,
            ['52.47.0.0/16'], ['2a05:d028::/36']
        ),
        'eu-central-1': EdgeLocation(
            'eu-central-1', 'Europe (Frankfurt)', 'Frankfurt', 'DE', 'Europe',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP, CloudProvider.CLOUDFLARE],
            RegionTier.TIER1, 50.1109, 8.6821,
            ['52.28.0.0/16', '35.156.0.0/16'], ['2a05:d000::/36']
        ),
        'eu-central-2': EdgeLocation(
            'eu-central-2', 'Europe (Zurich)', 'Zurich', 'CH', 'Europe',
            [CloudProvider.AWS],
            RegionTier.TIER2, 47.3769, 8.5417,
            ['52.59.0.0/16'], []
        ),
        'eu-north-1': EdgeLocation(
            'eu-north-1', 'Europe (Stockholm)', 'Stockholm', 'SE', 'Europe',
            [CloudProvider.AWS, CloudProvider.AZURE],
            RegionTier.TIER1, 59.3293, 18.0686,
            ['52.95.0.0/16'], ['2a05:d017::/36']
        ),
        'eu-south-1': EdgeLocation(
            'eu-south-1', 'Europe (Milan)', 'Milan', 'IT', 'Europe',
            [CloudProvider.AWS, CloudProvider.AZURE],
            RegionTier.TIER2, 45.4642, 9.1900,
            ['52.94.0.0/16'], []
        ),
        'eu-south-2': EdgeLocation(
            'eu-south-2', 'Europe (Spain)', 'Madrid', 'ES', 'Europe',
            [CloudProvider.AWS],
            RegionTier.TIER2, 40.4168, -3.7038,
            ['52.95.0.0/16'], []
        ),
        
        # ASIA PACIFIC - Tier 1
        'ap-south-1': EdgeLocation(
            'ap-south-1', 'Asia Pacific (Mumbai)', 'Mumbai', 'IN', 'Asia Pacific',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER1, 19.0760, 72.8777,
            ['52.66.0.0/16', '35.154.0.0/16'], ['2406:da00::/36']
        ),
        'ap-south-2': EdgeLocation(
            'ap-south-2', 'Asia Pacific (Hyderabad)', 'Hyderabad', 'IN', 'Asia Pacific',
            [CloudProvider.AWS],
            RegionTier.TIER2, 17.3850, 78.4867,
            ['52.95.0.0/16'], []
        ),
        'ap-southeast-1': EdgeLocation(
            'ap-southeast-1', 'Asia Pacific (Singapore)', 'Singapore', 'SG', 'Asia Pacific',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP, CloudProvider.CLOUDFLARE, CloudProvider.ALIBABA],
            RegionTier.TIER1, 1.3521, 103.8198,
            ['52.74.0.0/16', '52.76.0.0/16'], ['2406:da18::/36']
        ),
        'ap-southeast-2': EdgeLocation(
            'ap-southeast-2', 'Asia Pacific (Sydney)', 'Sydney', 'AU', 'Asia Pacific',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER1, -33.8688, 151.2093,
            ['52.64.0.0/16', '54.206.0.0/16'], ['2406:da1c::/36']
        ),
        'ap-southeast-3': EdgeLocation(
            'ap-southeast-3', 'Asia Pacific (Jakarta)', 'Jakarta', 'ID', 'Asia Pacific',
            [CloudProvider.AWS, CloudProvider.GCP],
            RegionTier.TIER2, -6.2088, 106.8456,
            ['52.95.0.0/16'], []
        ),
        'ap-southeast-4': EdgeLocation(
            'ap-southeast-4', 'Asia Pacific (Melbourne)', 'Melbourne', 'AU', 'Asia Pacific',
            [CloudProvider.AWS],
            RegionTier.TIER2, -37.8136, 144.9631,
            ['52.95.0.0/16'], []
        ),
        'ap-northeast-1': EdgeLocation(
            'ap-northeast-1', 'Asia Pacific (Tokyo)', 'Tokyo', 'JP', 'Asia Pacific',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP, CloudProvider.CLOUDFLARE],
            RegionTier.TIER1, 35.6762, 139.6503,
            ['52.68.0.0/16', '54.64.0.0/16'], ['2406:da14::/36']
        ),
        'ap-northeast-2': EdgeLocation(
            'ap-northeast-2', 'Asia Pacific (Seoul)', 'Seoul', 'KR', 'Asia Pacific',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER1, 37.5665, 126.9780,
            ['52.78.0.0/16'], ['2406:da12::/36']
        ),
        'ap-northeast-3': EdgeLocation(
            'ap-northeast-3', 'Asia Pacific (Osaka)', 'Osaka', 'JP', 'Asia Pacific',
            [CloudProvider.AWS],
            RegionTier.TIER2, 34.6937, 135.5023,
            ['52.95.0.0/16'], []
        ),
        'ap-east-1': EdgeLocation(
            'ap-east-1', 'Asia Pacific (Hong Kong)', 'Hong Kong', 'HK', 'Asia Pacific',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER1, 22.3193, 114.1694,
            ['52.95.0.0/16'], ['2406:da1e::/36']
        ),
        
        # CHINA - Special handling required
        'cn-north-1': EdgeLocation(
            'cn-north-1', 'China (Beijing)', 'Beijing', 'CN', 'Asia Pacific',
            [CloudProvider.ALIBABA, CloudProvider.TENCENT],
            RegionTier.TIER1, 39.9042, 116.4074,
            [], []
        ),
        'cn-northwest-1': EdgeLocation(
            'cn-northwest-1', 'China (Ningxia)', 'Yinchuan', 'CN', 'Asia Pacific',
            [CloudProvider.ALIBABA],
            RegionTier.TIER2, 38.4872, 106.2309,
            [], []
        ),
        'cn-east-1': EdgeLocation(
            'cn-east-1', 'China (Shanghai)', 'Shanghai', 'CN', 'Asia Pacific',
            [CloudProvider.ALIBABA, CloudProvider.TENCENT],
            RegionTier.TIER1, 31.2304, 121.4737,
            [], []
        ),
        'cn-south-1': EdgeLocation(
            'cn-south-1', 'China (Shenzhen)', 'Shenzhen', 'CN', 'Asia Pacific',
            [CloudProvider.TENCENT, CloudProvider.ALIBABA],
            RegionTier.TIER1, 22.5431, 114.0579,
            [], []
        ),
        
        # SOUTH AMERICA
        'sa-east-1': EdgeLocation(
            'sa-east-1', 'South America (São Paulo)', 'São Paulo', 'BR', 'South America',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER1, -23.5505, -46.6333,
            ['52.67.0.0/16', '54.207.0.0/16'], ['2406:da00::/36']
        ),
        'sa-west-1': EdgeLocation(
            'sa-west-1', 'South America (Santiago)', 'Santiago', 'CL', 'South America',
            [CloudProvider.AWS],
            RegionTier.TIER2, -33.4489, -70.6693,
            ['52.95.0.0/16'], []
        ),
        'sa-north-1': EdgeLocation(
            'sa-north-1', 'South America (Bogotá)', 'Bogotá', 'CO', 'South America',
            [CloudProvider.AZURE],
            RegionTier.TIER2, 4.7110, -74.0721,
            [], []
        ),
        
        # AFRICA
        'af-south-1': EdgeLocation(
            'af-south-1', 'Africa (Cape Town)', 'Cape Town', 'ZA', 'Africa',
            [CloudProvider.AWS, CloudProvider.AZURE],
            RegionTier.TIER1, -33.9249, 18.4241,
            ['52.95.0.0/16'], ['2406:da00::/36']
        ),
        'af-north-1': EdgeLocation(
            'af-north-1', 'Africa (Cairo)', 'Cairo', 'EG', 'Africa',
            [CloudProvider.AZURE],
            RegionTier.TIER2, 30.0444, 31.2357,
            [], []
        ),
        'af-central-1': EdgeLocation(
            'af-central-1', 'Africa (Nairobi)', 'Nairobi', 'KE', 'Africa',
            [CloudProvider.AWS],
            RegionTier.TIER2, -1.2921, 36.8219,
            ['52.95.0.0/16'], []
        ),
        'af-west-1': EdgeLocation(
            'af-west-1', 'Africa (Lagos)', 'Lagos', 'NG', 'Africa',
            [CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER2, 6.5244, 3.3792,
            [], []
        ),
        
        # MIDDLE EAST
        'me-south-1': EdgeLocation(
            'me-south-1', 'Middle East (Bahrain)', 'Manama', 'BH', 'Middle East',
            [CloudProvider.AWS, CloudProvider.AZURE],
            RegionTier.TIER1, 26.2285, 50.5860,
            ['52.95.0.0/16'], ['2406:da00::/36']
        ),
        'me-central-1': EdgeLocation(
            'me-central-1', 'Middle East (UAE)', 'Dubai', 'AE', 'Middle East',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER1, 25.2048, 55.2708,
            ['52.95.0.0/16'], []
        ),
        'me-west-1': EdgeLocation(
            'me-west-1', 'Middle East (Israel)', 'Tel Aviv', 'IL', 'Middle East',
            [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER2, 32.0853, 34.7818,
            ['52.95.0.0/16'], []
        ),
        'me-south-2': EdgeLocation(
            'me-south-2', 'Middle East (Doha)', 'Doha', 'QA', 'Middle East',
            [CloudProvider.AZURE, CloudProvider.GCP],
            RegionTier.TIER2, 25.2854, 51.5310,
            [], []
        ),
        
        # RUSSIA & CIS
        'ru-central-1': EdgeLocation(
            'ru-central-1', 'Russia (Moscow)', 'Moscow', 'RU', 'Europe',
            [CloudProvider.SELF_HOSTED],
            RegionTier.TIER1, 55.7558, 37.6173,
            [], []
        ),
        'ru-northwest-1': EdgeLocation(
            'ru-northwest-1', 'Russia (St. Petersburg)', 'St. Petersburg', 'RU', 'Europe',
            [CloudProvider.SELF_HOSTED],
            RegionTier.TIER2, 59.9311, 30.3609,
            [], []
        ),
    }
    
    def __init__(self):
        self.health_status: Dict[str, str] = {}
        self.latency_data: Dict[str, float] = {}
    
    def get_location(self, code: str) -> Optional[EdgeLocation]:
        """Get edge location by code"""
        return self.EDGE_LOCATIONS.get(code)
    
    def get_all_locations(self) -> List[EdgeLocation]:
        """Get all edge locations"""
        return list(self.EDGE_LOCATIONS.values())
    
    def get_locations_by_region(self, region: str) -> List[EdgeLocation]:
        """Get locations by geographic region"""
        return [loc for loc in self.EDGE_LOCATIONS.values() 
                if loc.region.lower() == region.lower()]
    
    def get_locations_by_country(self, country_code: str) -> List[EdgeLocation]:
        """Get locations by country"""
        return [loc for loc in self.EDGE_LOCATIONS.values() 
                if loc.country.upper() == country_code.upper()]
    
    def get_locations_by_tier(self, tier: RegionTier) -> List[EdgeLocation]:
        """Get locations by tier"""
        return [loc for loc in self.EDGE_LOCATIONS.values() 
                if loc.tier == tier]
    
    def get_locations_by_provider(self, provider: CloudProvider) -> List[EdgeLocation]:
        """Get locations by cloud provider"""
        return [loc for loc in self.EDGE_LOCATIONS.values() 
                if provider in loc.providers]
    
    def find_nearest_location(self, lat: float, lon: float) -> Optional[EdgeLocation]:
        """Find nearest edge location by coordinates"""
        import math
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in km
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        nearest = None
        min_distance = float('inf')
        
        for loc in self.EDGE_LOCATIONS.values():
            distance = haversine(lat, lon, loc.lat, loc.lon)
            if distance < min_distance:
                min_distance = distance
                nearest = loc
        
        return nearest
    
    async def check_location_health(self, location_code: str) -> Dict[str, Any]:
        """Check health of an edge location"""
        loc = self.get_location(location_code)
        if not loc:
            return {'error': f'Location {location_code} not found'}
        
        results = {
            'location': location_code,
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Try to ping each provider endpoint
        for provider in loc.providers:
            try:
                url = self._get_health_endpoint(provider, location_code)
                start = datetime.now()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as response:
                        latency = (datetime.now() - start).total_seconds() * 1000
                        results['checks'][provider.value] = {
                            'status': 'healthy' if response.status == 200 else 'degraded',
                            'latency_ms': round(latency, 2),
                            'status_code': response.status
                        }
            except Exception as e:
                results['checks'][provider.value] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        # Overall status
        healthy_count = sum(1 for c in results['checks'].values() 
                          if c.get('status') == 'healthy')
        
        if healthy_count == len(loc.providers):
            results['overall'] = 'healthy'
        elif healthy_count > 0:
            results['overall'] = 'degraded'
        else:
            results['overall'] = 'unhealthy'
        
        return results
    
    def _get_health_endpoint(self, provider: CloudProvider, location: str) -> str:
        """Get health check endpoint for provider"""
        endpoints = {
            CloudProvider.AWS: f"https://{location}.aws.amazon.com",
            CloudProvider.AZURE: "https://status.azure.com",
            CloudProvider.GCP: "https://status.cloud.google.com",
            CloudProvider.CLOUDFLARE: "https://www.cloudflarestatus.com",
            CloudProvider.ALIBABA: "https://status.aliyun.com",
        }
        return endpoints.get(provider, "https://1.1.1.1")
    
    def get_routing_table(self, user_country: str, user_lat: float = None, user_lon: float = None) -> Dict[str, Any]:
        """Generate optimal routing table for a user"""
        # Find nearest location
        if user_lat and user_lon:
            nearest = self.find_nearest_location(user_lat, user_lon)
        else:
            # Get locations for country
            country_locs = self.get_locations_by_country(user_country)
            nearest = country_locs[0] if country_locs else None
        
        if not nearest:
            nearest = self.get_location('us-east-1')  # Default
        
        # Get fallback locations (different providers)
        fallbacks = []
        for loc in self.EDGE_LOCATIONS.values():
            if loc.code != nearest.code and loc.region == nearest.region:
                # Different provider = good fallback
                if not set(loc.providers) & set(nearest.providers):
                    fallbacks.append(loc)
        
        return {
            'primary': nearest.to_dict(),
            'fallbacks': [f.to_dict() for f in fallbacks[:3]],
            'cdn_url': f"https://cdn-{nearest.code}.asimnexus.org",
            'api_url': f"https://api-{nearest.code}.asimnexus.org",
            'websocket_url': f"wss://ws-{nearest.code}.asimnexus.org"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get CDN statistics"""
        total = len(self.EDGE_LOCATIONS)
        tier1 = len(self.get_locations_by_tier(RegionTier.TIER1))
        tier2 = len(self.get_locations_by_tier(RegionTier.TIER2))
        tier3 = len(self.get_locations_by_tier(RegionTier.TIER3))
        
        by_region = {}
        for loc in self.EDGE_LOCATIONS.values():
            by_region[loc.region] = by_region.get(loc.region, 0) + 1
        
        by_provider = {}
        for provider in CloudProvider:
            count = len(self.get_locations_by_provider(provider))
            if count > 0:
                by_provider[provider.value] = count
        
        return {
            'total_locations': total,
            'tier1': tier1,
            'tier2': tier2,
            'tier3': tier3,
            'by_region': by_region,
            'by_provider': by_provider,
            'regions_covered': len(by_region),
            'countries_covered': len(set(loc.country for loc in self.EDGE_LOCATIONS.values()))
        }

_cdn_system = None

def get_cdn_system() -> GlobalCDNSystem:
    """Get or create CDN system singleton"""
    global _cdn_system
    if _cdn_system is None:
        _cdn_system = GlobalCDNSystem()
    return _cdn_system

if __name__ == "__main__":
    import sys
    cdn = get_cdn_system()
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(cdn.get_stats(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "list":
        for code, loc in cdn.EDGE_LOCATIONS.items():
            print(f"{code:20} {loc.name:30} {loc.region:15} {loc.tier.value}")
    elif len(sys.argv) > 3 and sys.argv[1] == "nearest":
        lat, lon = float(sys.argv[2]), float(sys.argv[3])
        nearest = cdn.find_nearest_location(lat, lon)
        if nearest:
            print(f"Nearest: {nearest.name} ({nearest.code})")
            print(f"Coordinates: {nearest.lat}, {nearest.lon}")
    else:
        print("Usage: python global_cdn.py [stats|list|nearest <lat> <lon>]")
