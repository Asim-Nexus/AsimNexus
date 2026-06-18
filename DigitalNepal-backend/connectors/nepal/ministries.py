#!/usr/bin/env python3
"""
AsimNexus World OS - Nepal Ministries (18)
विश्वव्यापी सरकारी संरचनाको लागि लागू गरिएको टेम्प्लेट
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import template
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from connectors.ministry_template import MinistryConnector, MinistryConfig, MinistrySector

# ─── Nepal Ministries Configuration ───────────────────────────────────────────

NEPAL_MINISTRIES = [
    # Federal Ministries (१८ मन्त्रालय)
    MinistryConfig("PM Office", MinistrySector.GOVERNANCE, "/api/v1/np/gov/pm", True, False),
    MinistryConfig("Finance", MinistrySector.FINANCE, "/api/v1/np/gov/finance", True, False),
    MinistryConfig("Home Affairs", MinistrySector.GOVERNANCE, "/api/v1/np/gov/home", True, False),
    MinistryConfig("Health", MinistrySector.HEALTHCARE, "/api/v1/np/gov/health", True, False),
    MinistryConfig("Education", MinistrySector.EDUCATION, "/api/v1/np/gov/education", True, False),
    MinistryConfig("Agriculture", MinistrySector.AGRICULTURE, "/api/v1/np/gov/agriculture", True, False),
    MinistryConfig("Tourism", MinistrySector.AGRICULTURE, "/api/v1/np/gov/tourism", True, False),
    MinistryConfig("Energy", MinistrySector.ENERGY, "/api/v1/np/gov/energy", True, False),
    MinistryConfig("Industry", MinistrySector.GOVERNANCE, "/api/v1/np/gov/industry", True, False),
    MinistryConfig("Telecom", MinistrySector.GOVERNANCE, "/api/v1/np/gov/telecom", True, False),
    MinistryConfig("Land", MinistrySector.GOVERNANCE, "/api/v1/np/gov/land", True, False),
    MinistryConfig("Law", MinistrySector.GOVERNANCE, "/api/v1/np/gov/law", True, False),
    MinistryConfig("Foreign Affairs", MinistrySector.GOVERNANCE, "/api/v1/np/gov/foreign", True, False),
    MinistryConfig("Defense", MinistrySector.GOVERNANCE, "/api/v1/np/gov/defense", True, False),
    MinistryConfig("Science", MinistrySector.GOVERNANCE, "/api/v1/np/gov/science", True, False),
    MinistryConfig("Infrastructure", MinistrySector.GOVERNANCE, "/api/v1/np/gov/infrastructure", True, False),
    MinistryConfig("Youth", MinistrySector.GOVERNANCE, "/api/v1/np/gov/youth", True, False),
    MinistryConfig("Women", MinistrySector.GOVERNANCE, "/api/v1/np/gov/women", True, False),
]

# ─── Ministry Management ───────────────────────────────────────────────────────

_MINISTRY_INSTANCES: Dict[str, MinistryConnector] = {}

def get_nepal_ministry(name: str) -> Optional[MinistryConnector]:
    """Get Nepal ministry connector by name"""
    for config in NEPAL_MINISTRIES:
        if config.name.lower() == name.lower():
            key = f"NP:{name}"
            if key not in _MINISTRY_INSTANCES:
                _MINISTRY_INSTANCES[key] = MinistryConnector(config, "NP")
            return _MINISTRY_INSTANCES[key]
    return None

def list_nepal_ministries() -> List[MinistryConfig]:
    """List all Nepal ministries"""
    return NEPAL_MINISTRIES

def get_ministry_stats() -> Dict[str, Any]:
    """Get Nepal ministries statistics"""
    return {
        "total_ministries": len(NEPAL_MINISTRIES),
        "country": "NP",
        "ministries": [m.name for m in NEPAL_MINISTRIES],
        "sectors": list(set(m.sector.value for m in NEPAL_MINISTRIES))
    }


__all__ = [
    "NEPAL_MINISTRIES",
    "get_nepal_ministry",
    "list_nepal_ministries", 
    "get_ministry_stats"
]