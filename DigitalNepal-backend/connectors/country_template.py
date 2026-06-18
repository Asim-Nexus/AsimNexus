#!/usr/bin/env python3
"""
AsimNexus World OS - Country Template
Template for all country connectors - clone this for each country
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# ─── Country Configuration ──────────────────────────────────────────────────

class SectorType(Enum):
    PUBLIC_COORDINATED = "public_coordinated"   # Government controlled
    PRIVATE_OPERATED = "private_operated"        # Private sector
    MIXED = "mixed"                            # Mixed control

@dataclass
class CountryConfig:
    code: str              # ISO code (NP, IN, US, UK)
    name: str            # Country name
    government_sectors: list  # Public sectors (>51%)
    company_sectors: list     # Private sectors (<49%)
    citizen_services: list    # Local-first services

# ─── Country Connector Template ─────────────────────────────────────────────

class CountryConnector:
    """
    Universal template for any country.
    Each country gets its own instance with specific configuration.
    """
    
    def __init__(self, config: CountryConfig):
        self.config = config
        self._init_sectors()
        
    def _init_sectors(self):
        """Initialize sector balance maps"""
        self.sectors: Dict[str, SectorType] = {}
        for sector in self.config.government_sectors:
            self.sectors[sector] = SectorType.PUBLIC_COORDINATED
        for sector in self.config.company_sectors:
            self.sectors[sector] = SectorType.PRIVATE_OPERATED
    
    def check_balance(self, sector: str, is_public: bool) -> Dict[str, Any]:
        """Check 51/49 power balance for this country/sector"""
        sector_type = self.sectors.get(sector, SectorType.MIXED)
        
        if sector_type == SectorType.PUBLIC_COORDINATED:
            # Must be public decision (51%+)
            return {
                "allowed": is_public,
                "threshold": 51,
                "sector": sector,
                "country": self.config.code,
                "reason": f"{sector} is public-coordinated (51%+ required)"
            }
        elif sector_type == SectorType.PRIVATE_OPERATED:
            # Must be private decision (49%+)
            return {
                "allowed": not is_public,
                "threshold": 49,
                "sector": sector,
                "country": self.config.code,
                "reason": f"{sector} is private-operated (49%+ private required)"
            }
        
        return {"allowed": True, "sector": sector, "country": self.config.code}
    
    def gov_action(self, sector: str, action: str) -> Dict[str, Any]:
        """Government action through 51% threshold"""
        result = self.check_balance(sector, is_public=True)
        result["action"] = action
        return result
    
    def company_action(self, sector: str, action: str) -> Dict[str, Any]:
        """Company action through 49% threshold"""
        result = self.check_balance(sector, is_public=False)
        result["action"] = action
        return result

# ─── Nepal Specific ───────────────────────────────────────────────────────────

NEPAL_CONFIG = CountryConfig(
    code="NP",
    name="Nepal",
    government_sectors=[
        "infrastructure", "governance", "healthcare", "education",
        "agriculture", "tourism", "energy", "defense"
    ],
    company_sectors=["finance", "technology", "commerce"],
    citizen_services=["identity", "healthcare", "education"]
)

# ─── Singleton Factory ────────────────────────────────────────────────────────

_CONNECTORS: Dict[str, CountryConnector] = {}

def get_country(code: str = "NP") -> CountryConnector:
    """Get or create country connector"""
    if code not in _CONNECTORS:
        configs = {"NP": NEPAL_CONFIG}
        config = configs.get(code)
        if config:
            _CONNECTORS[code] = CountryConnector(config)
    return _CONNECTORS.get(code)


__all__ = [
    "CountryConfig", "SectorType", "CountryConnector",
    "NEPAL_CONFIG", "get_country"
]