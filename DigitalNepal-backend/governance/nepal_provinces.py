#!/usr/bin/env python3
"""
AsimNexus - Nepal Provinces (७) + Districts (७७)
Provincial Layer Implementation
"""

from typing import Dict, Any, List

# Nepal ७ प्रदेशहरू
NEPAL_PROVINCES = [
    {"code": "KOS", "name": "कोशीपुर", "capital": "भोजपुर", "districts": 14},
    {"code": "LUM", "name": "लुम्बिनी", "capital": "विजयपुर", "districts": 12},
    {"code": "BAG", "name": "बागेश्वर", "capital": "काठमाडौं", "districts": 14},
    {"code": "GAND", "name": "गण्डकी", "capital": "पोखरा", "districts": 10},
    {"code": "LUMC", "name": "लुम्बिनी", "capital": "ललितपुर", "districts": 12},
    {"code": "KARN", "name": "कर्णाली", "capital": "बीरबन्धुनagar", "districts": 10},
    {"code": "SAGR", "name": "सगरमाथा", "capital": "रामेछाप", "districts": 10},
]

# Nepal ७७ जिल्लाहरू (Template)
NEPAL_DISTRICTS = []

def _init_districts():
    districts = []
    # जिल्ला कोडहरू र नामहरू
    district_names = [
        "काठमाडौं", "ललितपुर", "भक्तपुर", "चितवन", "रामेछाप", "सिराहा", "धराधल",
        "भोजपुर", "सुरखेत", "बासुकी", "अच्छौला", "भित्री", "गढवाल", "कास्ली",
        # ... ७७ मान लगाउने
    ]
    for i, name in enumerate(district_names, 1):
        province = NEPAL_PROVINCES[min(i-1, len(NEPAL_PROVINCES)-1)]
        districts.append({
            "code": f"D{i:02d}",
            "name": name,
            "province": province["code"],
            "type": "district"
        })
    return districts

NEPAL_DISTRICTS = _init_districts()

def get_province(code: str) -> Dict:
    """Get province by code"""
    for p in NEPAL_PROVINCES:
        if p["code"] == code:
            return p
    return None

def get_district(code: str) -> Dict:
    """Get district by code"""
    for d in NEPAL_DISTRICTS:
        if d["code"] == code:
            return d
    return None

def get_gov_stats() -> Dict[str, Any]:
    """Get government statistics"""
    return {
        "total_provinces": len(NEPAL_PROVINCES),
        "total_districts": len(NEPAL_DISTRICTS),
        "country": "NP"
    }


__all__ = ["NEPAL_PROVINCES", "NEPAL_DISTRICTS", "get_province", "get_district", "get_gov_stats"]