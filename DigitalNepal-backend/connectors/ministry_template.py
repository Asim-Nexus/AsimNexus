#!/usr/bin/env python3
"""
AsimNexus World OS - Ministry Template
Template for all ministries - clone for each ministry
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# ─── Sector Configuration ─────────────────────────────────────────────────────

class MinistrySector(Enum):
    INFRASTRUCTURE = "infrastructure"
    GOVERNANCE = "governance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    AGRICULTURE = "agriculture"
    TOURISM = "tourism"
    ENERGY = "energy"
    FINANCE = "finance"
    TECHNOLOGY = "technology"

# ─── Ministry Template ─────────────────────────────────────────────────────────

@dataclass
class MinistryConfig:
    name: str
    sector: MinistrySector
    api_endpoint: str
    requires_human: bool = True
    blockchain_verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "sector": self.sector.value,
            "api_endpoint": self.api_endpoint,
            "requires_human": self.requires_human,
            "blockchain_verified": self.blockchain_verified
        }

class MinistryConnector:
    """Template for all ministries - can be extended per country"""
    
    def __init__(self, config: MinistryConfig, country_code: str = "NP"):
        self.config = config
        self.country_code = country_code
        self._data_cache: Dict[str, Any] = {}
        
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process ministry request through 51% balance check"""
        # Import country connector
        from country_template import get_country
        
        country = get_country(self.country_code)
        if country:
            result = country.gov_action(self.config.sector.value, "process")
            if not result.get("allowed", False):
                return {"status": "rejected", "reason": result.get("reason")}
        
        # Process the request
        return {
            "status": "processed",
            "ministry": self.config.name,
            "request_id": request.get("id"),
            "result": self._execute(request)
        }
    
    def _execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ministry logic - override in subclass"""
        return {"processed": True, "data": request.get("data")}

# ─── Nepal Ministries (Base Implementation) ─────────────────────────────────

NEPAL_MINISTRIES = [
    MinistryConfig("PM Office", MinistrySector.GOVERNANCE, "/api/v1/gov/pm"),
    MinistryConfig("Finance", MinistrySector.FINANCE, "/api/v1/gov/finance"),
    MinistryConfig("Health", MinistrySector.HEALTHCARE, "/api/v1/gov/health"),
    MinistryConfig("Education", MinistrySector.EDUCATION, "/api/v1/gov/education"),
    MinistryConfig("Agriculture", MinistrySector.AGRICULTURE, "/api/v1/gov/agriculture"),
    MinistryConfig("Energy", MinistrySector.ENERGY, "/api/v1/gov/energy"),
    MinistryConfig("Tourism", MinistrySector.TOURISM, "/api/v1/gov/tourism"),
]

_MINISTRY_CONNECTORS: Dict[str, MinistryConnector] = {}

def get_ministry(name: str, country: str = "NP") -> Optional[MinistryConnector]:
    """Get ministry connector by name"""
    key = f"{country}:{name}"
    if key not in _MINISTRY_CONNECTORS:
        for config in NEPAL_MINISTRIES:
            if config.name.lower() == name.lower():
                _MINISTRY_CONNECTORS[key] = MinistryConnector(config, country)
    return _MINISTRY_CONNECTORS.get(key)

def list_ministries(country: str = "NP") -> List[MinistryConfig]:
    """List all ministries for a country"""
    return NEPAL_MINISTRIES if country == "NP" else []

__all__ = [
    "MinistrySector", "MinistryConfig", "MinistryConnector",
    "NEPAL_MINISTRIES", "get_ministry", "list_ministries"
]