#!/usr/bin/env python3
"""AsimNexus Tourism Connector - Nepal Tourism
Hotels, Travel, Tourism Organizations
"""

HOTELS = {
    "ktm001": {"name": "होटल डाटार", "district": "काठमाडौं", "rooms": 150},
    "ktm002": {"name": "होटल यक्षा", "district": "काठमाडौं", "rooms": 200},
    "ktm003": {"name": "होटल सान्‍ट्रल", "district": "काठमाडौं", "rooms": 180},
    "lpt001": {"name": "ललितपुर प्यामर्स", "district": "ललितपुर", "rooms": 120},
    "bpt001": {"name": "भक्तपुर हर्पर", "district": "भक्तपुर", "rooms": 90},
    "pkr001": {"name": "फेवा भूटी होटल", "district": "कास्की", "rooms": 250},
    "pkr002": {"name": "मेरा होटल", "district": "कास्की", "rooms": 150},
    "pkr003": {"name": "ट्रिपल टॉवर्स", "district": "कास्की", "rooms": 180},
    "gm001": {"name": "गोरखा मेडिटेशन", "district": "गोरखा", "rooms": 100},
    "ctv001": {"name": "चितवन रिज़ोर्ट", "district": "चितवन", "rooms": 220},
    "rm001": {"name": "रामेछाप मन्दिर", "district": "रामेछाप", "rooms": 80},
    "srt001": {"name": "सप्तरी ग्लोरिया", "district": "सप्तरी", "rooms": 110},
    "jnk001": {"name": "जनकपुर धाम", "district": "धनुषा", "rooms": 150},
    "btl001": {"name": "बुटवल समुद्र", "district": "रुपन्देही", "rooms": 130},
    "plp001": {"name": "पाल्पा माउन्टेन", "district": "पाल्पा", "rooms": 90},
    "sdn001": {"name": "सुर्खेत एनापूर्णा", "district": "सुर्खेत", "rooms": 100},
    "dlp001": {"name": "डोल्पा ट्रेकिङ", "district": "डोल्पा", "rooms": 60},
    "kcp001": {"name": "कञ्चनपुर घर", "district": "कञ्चनपुर", "rooms": 120},
    "dhg001": {"name": "धनगढी बीच", "district": "कैलाली", "rooms": 140},
}

TOURISM_SERVICES = {
    "mountaineering": {"desc": "एभरेस्ट ट्रेक"},
    "trekking": {"desc": "ट्रेकिङ सर्ट"},
    "cultural": {"desc": "सांस्कृतिक घुमाइँ"},
    "wildlife": {"desc": "वन्यजन्तु घुमाइँ"},
}

def get_hotel(code: str) -> dict:
    return HOTELS.get(code)

__all__ = ["HOTELS", "TOURISM_SERVICES", "get_hotel"]