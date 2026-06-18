#!/usr/bin/env python3
"""
AsimNexus World OS - World Connector Manager
🌐 Manages all country connectors
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from connectors.country_template import CountryConnector, CountryConfig, SectorType
from connectors.nepal import NEPAL_MINISTRIES, NEPAL_PROVINCES, ALL_DISTRICTS as NEPAL_DISTRICTS
from connectors.india import INDIA_MINISTRIES, INDIA_STATES, INDIA_ALL_DISTRICTS
from connectors.usa import USA_DEPARTMENTS, USA_STATES, USA_ALL_COUNTIES

# ─── Country Configurations ─────────────────────────────────────────────

WORLD_COUNTRIES = {
    "NP": CountryConfig(
        code="NP",
        name="Nepal",
        government_sectors=["infrastructure", "governance", "healthcare", "education", "agriculture"],
        company_sectors=["finance", "technology", "commerce"],
        citizen_services=["identity", "healthcare", "education"]
    ),
    "IN": CountryConfig(
        code="IN",
        name="India",
        government_sectors=["governance", "healthcare", "education", "agriculture", "railways"],
        company_sectors=["finance", "technology", "manufacturing"],
        citizen_services=["identity", "healthcare", "education"]
    ),
    "US": CountryConfig(
        code="US",
        name="USA",
        government_sectors=["governance", "healthcare", "education", "agriculture", "defense"],
        company_sectors=["finance", "technology", "commerce"],
        citizen_services=["identity", "healthcare", "education"]
    )
}

# ─── World Manager ───────────────────────────────────────────────────────

class WorldConnectorManager:
    """Manages all country connectors"""
    
    def __init__(self):
        self._countries: Dict[str, CountryConnector] = {}
        
    def get_country(self, code: str) -> Optional[CountryConnector]:
        """Get country connector"""
        if code not in self._countries:
            config = WORLD_COUNTRIES.get(code)
            if config:
                self._countries[code] = CountryConnector(config)
        return self._countries.get(code)
    
    def list_countries(self) -> list:
        """List all available country codes"""
        return list(WORLD_COUNTRIES.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get world statistics"""
        return {
            "total_countries": len(WORLD_COUNTRIES),
            "countries": self.list_countries(),
            "nepal_ministries": len(NEPAL_MINISTRIES),
            "india_ministries": len(INDIA_MINISTRIES),
            "usa_departments": len(USA_DEPARTMENTS)
        }

# ─── Singleton ───────────────────────────────────────────────────────────

_manager_instance = None

def get_world_manager() -> WorldConnectorManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = WorldConnectorManager()
    return _manager_instance


__all__ = ["WorldConnectorManager", "get_world_manager", "WORLD_COUNTRIES"]