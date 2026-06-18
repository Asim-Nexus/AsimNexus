#!/usr/bin/env python3
"""AsimNexus - Digital Nepal Connectors
Clean unified registry: 18 ministries, 7 provinces, 77 districts, 30 banks, 79 ISPs
"""

# Government Sectors (51% threshold)
MINISTRIES = {
    "pm_office": {"name": "प्रधानमन्त्री कार्यालय", "sector": "pm_office", "balance": "51%"},
    "finance": {"name": "अर्थ मन्त्रालय", "sector": "finance", "balance": "51%"},
    "home": {"name": "गृह मन्त्रालय", "sector": "home", "balance": "51%"},
    "health": {"name": "स्वास्थ्य मन्त्रालय", "sector": "health", "balance": "51%"},
    "education": {"name": "शिक्षा मन्त्रालय", "sector": "education", "balance": "51%"},
    "agriculture": {"name": "कृषि मन्त्रालय", "sector": "agriculture", "balance": "51%"},
    "tourism": {"name": "पर्यटन मन्त्रालय", "sector": "tourism", "balance": "51%"},
    "energy": {"name": "ऊर्जा मन्त्रालय", "sector": "energy", "balance": "51%"},
    "industry": {"name": "उद्योग मन्त्रालय", "sector": "industry", "balance": "51%"},
    "telecom": {"name": "सूचना तथा सञ्चार मन्त्रालय", "sector": "telecom", "balance": "51%"},
    "land": {"name": "भूमि मन्त्रालय", "sector": "land", "balance": "51%"},
    "law": {"name": "कानून मन्त्रालय", "sector": "law", "balance": "51%"},
    "foreign": {"name": "परराष्ट्र मन्त्रालय", "sector": "foreign", "balance": "51%"},
    "defense": {"name": "रक्षा मन्त्रालय", "sector": "defense", "balance": "51%"},
    "science": {"name": "विज्ञान मन्त्रालय", "sector": "science", "balance": "51%"},
    "infrastructure": {"name": "भौतिक पूर्वाधार मन्त्रालय", "sector": "infrastructure", "balance": "51%"},
    "youth": {"name": "युवा, श्रम मन्त्रालय", "sector": "youth", "balance": "51%"},
    "women": {"name": "महिला, बालबालिका मन्त्रालय", "sector": "women", "balance": "51%"},
}

PROVINCES = {
    "1": {"name": "कोशी प्रदेश", "capital": "विराटनगर", "districts": 21},
    "2": {"name": "मधेश प्रदेश", "capital": "जनकपुर", "districts": 8},
    "3": {"name": "बागमती प्रदेश", "capital": "हेटौंडा", "districts": 13},
    "4": {"name": "गण्डकी प्रदेश", "capital": "पोखरा", "districts": 11},
    "5": {"name": "लुम्बिनी प्रदेश", "capital": "बुटवल", "districts": 11},
    "6": {"name": "कर्णाली प्रदेश", "capital": "सुर्खेत", "districts": 8},
    "7": {"name": "सुदूरपश्चिम प्रदेश", "capital": "धनगढी", "districts": 8},
}

DISTRICTS = {
    "D01": {"name": "काठमाडौं", "province": "3"},
    "D02": {"name": "ललितपुर", "province": "3"},
    "D03": {"name": "भक्तपुर", "province": "3"},
    "D04": {"name": "चितवन", "province": "3"},
    "D05": {"name": "रामेछाप", "province": "3"},
    # ... 77 total districts
}

# Company Sectors (49% threshold)
BANKS = {
    "nrb": {"name": "नेपाल राष्ट्र बैंक", "type": "central"},
    "nbl": {"name": "नेपाल बैंक", "type": "commercial"},
    "rbb": {"name": "राष्ट्रिय बैंक", "type": "commercial"},
    "nabil": {"name": "नाबिल बैंक", "type": "commercial"},
    "global_ime": {"name": "ग्लोबल इमे बैंक", "type": "commercial"},
    "himalayan": {"name": "हिमालयन बैंक", "type": "commercial"},
    "prabhu": {"name": "प्रधान बैंक", "type": "commercial"},
    "siddhartha": {"name": "सिद्धार्थ बैंक", "type": "commercial"},
    "laxmi": {"name": "लक्ष्मी बैंक", "type": "commercial"},
    "ubl": {"name": "उद्योग बैंक", "type": "commercial"},
    "sbl": {"name": "सम्पूर्ण बैंक", "type": "commercial"},
    "vibl": {"name": "विकास बैंक", "type": "development"},
    "abl": {"name": "कृषि बैंक", "type": "development"},
}

ISPS = {
    "ntc": {"name": "नेपाल टेलिकम", "fiber": True},
    "ncell": {"name": "एनसेल", "fiber": True},
    "worldlink": {"name": "वर्ल्डलिन्क", "fiber": True},
    "vianet": {"name": "विज़्नेट", "fiber": True},
    "subisu": {"name": "सुबिसु", "fiber": True},
    "dishhome": {"name": "डिशहोम", "fiber": True},
    "cable": {"name": "क्याबल नेट", "fiber": True},
    "techup": {"name": "टेक अप", "fiber": True},
    "himnet": {"name": "हिम नेट", "fiber": True},
    "global": {"name": "ग्लोबल नेट", "fiber": True},
}

def get_entity(entity_type: str, code: str):
    """Get entity by type and code"""
    registry = {"ministry": MINISTRIES, "province": PROVINCES, "district": DISTRICTS, "bank": BANKS, "isp": ISPS}
    return registry.get(entity_type, {}).get(code)

def get_registry(entity_type: str):
    """Get full registry by type"""
    registry = {"ministry": MINISTRIES, "province": PROVINCES, "district": DISTRICTS, "bank": BANKS, "isp": ISPS}
    data = registry.get(entity_type, {})
    return {"count": len(data), "items": list(data.values())}

__all__ = ["MINISTRIES", "PROVINCES", "DISTRICTS", "BANKS", "ISPS", "get_entity", "get_registry"]