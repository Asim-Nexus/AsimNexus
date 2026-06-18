#!/usr/bin/env python3
"""
AsimNexus - Nepal Government Ministries (१८)
Government Layer (51%) Implementation
"""

from typing import Dict, Any, List
from connectors.ministry_template import MinistryConnector, MinistryConfig, MinistrySector

# Nepal १८ मन्त्रालयहरू
NEPAL_MINISTRIES = [
    MinistryConfig("PM Office", MinistrySector.GOVERNANCE, "/api/v1/np/gov/pm", True),
    MinistryConfig("Finance", MinistrySector.FINANCE, "/api/v1/np/gov/finance", True),
    MinistryConfig("Home Affairs", MinistrySector.GOVERNANCE, "/api/v1/np/gov/home", True),
    MinistryConfig("Health", MinistrySector.HEALTHCARE, "/api/v1/np/gov/health", True),
    MinistryConfig("Education", MinistrySector.EDUCATION, "/api/v1/np/gov/education", True),
    MinistryConfig("Agriculture", MinistrySector.AGRICULTURE, "/api/v1/np/gov/agriculture", True),
    MinistryConfig("Tourism", MinistrySector.AGRICULTURE, "/api/v1/np/gov/tourism", True),
    MinistryConfig("Energy", MinistrySector.ENERGY, "/api/v1/np/gov/energy", True),
    MinistryConfig("Industry", MinistrySector.GOVERNANCE, "/api/v1/np/gov/industry", True),
    MinistryConfig("Telecom", MinistrySector.GOVERNANCE, "/api/v1/np/gov/telecom", True),
    MinistryConfig("Land", MinistrySector.GOVERNANCE, "/api/v1/np/gov/land", True),
    MinistryConfig("Law", MinistrySector.GOVERNANCE, "/api/v1/np/gov/law", True),
    MinistryConfig("Foreign Affairs", MinistrySector.GOVERNANCE, "/api/v1/np/gov/foreign", True),
    MinistryConfig("Defense", MinistrySector.GOVERNANCE, "/api/v1/np/gov/defense", True),
    MinistryConfig("Science", MinistrySector.GOVERNANCE, "/api/v1/np/gov/science", True),
    MinistryConfig("Infrastructure", MinistrySector.GOVERNANCE, "/api/v1/np/gov/infrastructure", True),
    MinistryConfig("Youth", MinistrySector.GOVERNANCE, "/api/v1/np/gov/youth", True),
    MinistryConfig("Women", MinistrySector.GOVERNANCE, "/api/v1/np/gov/women", True),
]

def create_ministry_connector(name: str) -> MinistryConnector:
    """Create ministry connector by name"""
    for config in NEPAL_MINISTRIES:
        if config.name.lower() == name.lower():
            return MinistryConnector(config, "NP")
    return None

def get_all_ministries() -> List[MinistryConfig]:
    """Get all ministries"""
    return NEPAL_MINISTRIES

def get_gov_stats() -> Dict[str, Any]:
    """Get government statistics"""
    return {
        "total_ministries": len(NEPAL_MINISTRIES),
        "country": "NP",
        "balance_type": "public_coordinated",
        "threshold": 51
    }


__all__ = ["NEPAL_MINISTRIES", "create_ministry_connector", "get_all_ministries", "get_gov_stats"]