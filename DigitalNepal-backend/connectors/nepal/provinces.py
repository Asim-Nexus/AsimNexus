#!/usr/bin/env python3
"""
AsimNexus World OS - Nepal Provinces (७)
७ प्रदेशहरूको लागि Template लागू
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# ─── Province Configuration ─────────────────────────────────────────────────

NEPAL_PROVINCES = [
    {"code": "KOS", "name": "कोशीपुर", "capital": "भोजपुर", "districts": 14},
    {"code": "LUM", "name": "लुम्बिनी", "capital": "विजयपुर", "districts": 12},
    {"code": "BAG", "name": "बागेश्वर", "capital": "काठमाडौं", "districts": 14},
    {"code": "GAND", "name": "गण्डकी", "capital": "पोखरा", "districts": 10},
    {"code": "LUMC", "name": "लुम्बिनी", "capital": "ललितपुर", "districts": 12},
    {"code": "KARN", "name": "कर्णाली", "capital": "बीरबन्धुनagar", "districts": 10},
    {"code": "SAGR", "name": "सगरमाथा", "capital": "रामेछाप", "districts": 10},
]

# ─── Province Management ─────────────────────────────────────────────────────

_PROVINCE_CACHE: Dict[str, Any] = {}

def get_province(code: str) -> Optional[Dict]:
    """Get province by code"""
    for p in NEPAL_PROVINCES:
        if p["code"] == code:
            return p
    return None

def list_provinces() -> List[Dict]:
    """List all 7 provinces"""
    return NEPAL_PROVINCES

def get_province_stats() -> Dict[str, Any]:
    """Get province statistics"""
    return {
        "total_provinces": len(NEPAL_PROVINCES),
        "country": "NP",
        "total_districts": sum(p["districts"] for p in NEPAL_PROVINCES),
        "provinces": [p["name"] for p in NEPAL_PROVINCES]
    }


__all__ = ["NEPAL_PROVINCES", "get_province", "list_provinces", "get_province_stats"]