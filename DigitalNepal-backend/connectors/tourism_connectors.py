#!/usr/bin/env python3
"""AsimNexus Tourism Connector
Hotels, Travel, Tourism Nepal
"""

TOURISM_ENTITY = {
    "hotels": {
        "everest": {"name": "एभरेस्ट होटल", "district": "काठमाडौं", "rooms": 100},
        "annapurna": {"name": "अन्नपूर्णा होटल", "district": "कास्की", "rooms": 80},
        "pokhara": {"name": "पोखरा लक्सेस", "district": "कास्की", "rooms": 200},
    },
    "tourism_ministry": {
        "sector": "tourism",
        "balance": "51%",
        "services": ["tourism_registration", "travel_permits", "cultural_preservation"]
    }
}

def get_hotel(code: str) -> dict:
    return TOURISM_ENTITY["hotels"].get(code)

def get_tourism_stats() -> dict:
    return {
        "total_hotels": len(TOURISM_ENTITY["hotels"]),
        "sector": TOURISM_ENTITY["tourism_ministry"]["sector"]
    }

__all__ = ["TOURISM_ENTITY", "get_hotel", "get_tourism_stats"]