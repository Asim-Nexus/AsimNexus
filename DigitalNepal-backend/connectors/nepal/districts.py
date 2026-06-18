#!/usr/bin/env python3
"""
AsimNexus World OS - Nepal Districts (७७)
७७ जिल्लाहरूको लागि Template लागू
"""

from typing import Dict, Any, List, Optional

# ─── Key Districts (Template - Expand to ७७) ─────────────────────────────────

NEPAL_DISTRICTS_SAMPLE = [
    # क्षेत्र १ - काठमाडौं उपत्यका
    {"code": "KTM", "name": "काठमाडौं", "province": "BAG", "type": "metropolitan"},
    {"code": "LAL", "name": "ललितपुर", "province": "BAG", "type": "sub-metropolitan"},
    {"code": "CHT", "name": "चितवन", "province": "LUM", "type": "district"},
    
    # क्षेत्र २ - पहाडी
    {"code": "PKR", "name": "पोखरा", "province": "GAND", "type": "district"},
    {"code": "BTK", "name": "बीटखोट", "province": "GAND", "type": "district"},
    
    # क्षेत्र ३ - तराई
    {"code": "BIR", "name": "बिराजपुर", "province": "KOS", "type": "district"},
    {"code": "NAR", "name": "नारायणखेल", "province": "LUM", "type": "district"},
    
    # Template for remaining ६७ districts
    {"code": "TPL", "name": "Template District", "province": "BAG", "type": "district"},
]

# ─── District Management Template ────────────────────────────────────────────

def create_district_template(total: int = 77) -> List[Dict]:
    """Create template for all 77 districts"""
    districts = NEPAL_DISTRICTS_SAMPLE.copy()
    while len(districts) < total:
        districts.append({
            "code": f"DT{len(districts)+1:03d}",
            "name": f"District {len(districts)+1}",
            "province": "TPL",
            "type": "district"
        })
    return districts[:total]

ALL_DISTRICTS = create_district_template(77)

def get_district(code: str) -> Optional[Dict]:
    """Get district by code"""
    for d in ALL_DISTRICTS:
        if d["code"] == code:
            return d
    return None

def list_districts() -> List[Dict]:
    """List all 77 districts"""
    return ALL_DISTRICTS

def get_district_stats() -> Dict[str, Any]:
    """Get district statistics"""
    return {
        "total_districts": len(ALL_DISTRICTS),
        "country": "NP",
        "by_province": {},
        "by_type": {}
    }


__all__ = [
    "NEPAL_DISTRICTS_SAMPLE", "ALL_DISTRICTS",
    "get_district", "list_districts", "get_district_stats",
    "create_district_template"
]