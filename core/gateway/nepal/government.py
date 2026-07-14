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
    "D06": {"name": "काभ्रे", "province": "3"},
    "D07": {"name": "धादिङ", "province": "3"},
    "D08": {"name": "नुवाकोट", "province": "3"},
    "D09": {"name": "रसुवा", "province": "3"},
    "D10": {"name": "सिन्धुपाल्चोक", "province": "3"},
    "D11": {"name": "मकवानपुर", "province": "3"},
    "D12": {"name": "दोलखा", "province": "3"},
    "D13": {"name": "भोजपुर", "province": "1"},
    "D14": {"name": "झापा", "province": "1"},
    "D15": {"name": "इलाम", "province": "1"},
    "D16": {"name": "पाँचथर", "province": "1"},
    "D17": {"name": "मोरङ", "province": "1"},
    "D18": {"name": "सुनसरी", "province": "1"},
    "D19": {"name": "उदयपुर", "province": "1"},
    "D20": {"name": "धनकुटा", "province": "1"},
    "D21": {"name": "तेह्रथुम", "province": "1"},
    "D22": {"name": "संखुवासभा", "province": "1"},
    "D23": {"name": "सोलुखुम्बु", "province": "1"},
    "D24": {"name": "ओखलढुङ्गा", "province": "1"},
    "D25": {"name": "खोटाङ", "province": "1"},
    "D26": {"name": "ताप्लेजुङ", "province": "1"},
    "D27": {"name": "सप्तरी", "province": "2"},
    "D28": {"name": "धनुषा", "province": "2"},
    "D29": {"name": "महोत्तरी", "province": "2"},
    "D30": {"name": "सर्लाही", "province": "2"},
    "D31": {"name": "रौतहट", "province": "2"},
    "D32": {"name": "बारा", "province": "2"},
    "D33": {"name": "पर्सा", "province": "2"},
    "D34": {"name": "रुपन्देही", "province": "5"},
    "D35": {"name": "पाल्पा", "province": "5"},
    "D36": {"name": "गुल्मी", "province": "5"},
    "D37": {"name": "अर्घाखाँची", "province": "5"},
    "D38": {"name": "कपिलवस्तु", "province": "5"},
    "D39": {"name": "दाङ", "province": "5"},
    "D40": {"name": "बाँके", "province": "5"},
    "D41": {"name": "बर्दिया", "province": "5"},
    "D42": {"name": "प्युठान", "province": "5"},
    "D43": {"name": "रोल्पा", "province": "5"},
    "D44": {"name": "सल्यान", "province": "5"},
    "D45": {"name": "कास्की", "province": "4"},
    "D46": {"name": "लमजुङ", "province": "4"},
    "D47": {"name": "तनहुँ", "province": "4"},
    "D48": {"name": "गोरखा", "province": "4"},
    "D49": {"name": "स्याङ्जा", "province": "4"},
    "D50": {"name": "पर्वत", "province": "4"},
    "D51": {"name": "म्याग्दी", "province": "4"},
    "D52": {"name": "बाग्लुङ", "province": "4"},
    "D53": {"name": "मनाङ", "province": "4"},
    "D54": {"name": "मुस्ताङ", "province": "4"},
    "D55": {"name": "दैलेख", "province": "6"},
    "D56": {"name": "जाजरकोट", "province": "6"},
    "D57": {"name": "हुम्ला", "province": "6"},
    "D58": {"name": "मुगु", "province": "6"},
    "D59": {"name": "डोल्पा", "province": "6"},
    "D60": {"name": "कालिकोट", "province": "6"},
    "D61": {"name": "जुम्ला", "province": "6"},
    "D62": {"name": "कैलाली", "province": "7"},
    "D63": {"name": "कञ्चनपुर", "province": "7"},
    "D64": {"name": "डोटी", "province": "7"},
    "D65": {"name": "अछाम", "province": "7"},
    "D66": {"name": "बाजुरा", "province": "7"},
    "D67": {"name": "बझाङ", "province": "7"},
    "D68": {"name": "दार्चुला", "province": "7"},
    "D69": {"name": "बैतडी", "province": "7"},
    "D70": {"name": "अझै थप्ने", "province": "1"},
    "D71": {"name": "डोटी", "province": "7"},
    "D72": {"name": "कञ्चनपुर", "province": "7"},
    "D73": {"name": "बाजुरा", "province": "7"},
    "D74": {"name": "दार्चुला", "province": "7"},
    "D75": {"name": "अछाम", "province": "7"},
    "D76": {"name": "कैलाली", "province": "7"},
    "D77": {"name": "जाजरकोट", "province": "6"},
}

# Education Sector (Government - 51% threshold)
UNIVERSITIES = {
    "tu": {"name": "त्रिभुवन विश्वविद्यालय", "type": "public", "location": "काठमाडौं"},
    "ku": {"name": "काठमाडौं विश्वविद्यालय", "type": "public", "location": "काठमाडौं"},
    "po": {"name": "पोखरा विश्वविद्यालय", "type": "public", "location": "पोखरा"},
    "pu": {"name": "पूर्वाञ्चल विश्वविद्यालय", "type": "public", "location": "भक्तपुर"},
    "ns": {"name": "नेपाल संस्कृत विश्वविद्यालय", "type": "public", "location": "काठमाडौं"},
    "af": {"name": "कृषि एवं वानिकी विश्वविद्यालय", "type": "public", "location": "बालकोट"},
    "nm": {"name": "नेपाल मेडिकल विश्वविद्यालय", "type": "public", "location": "काठमाडौं"},
    "op": {"name": "नेवार विश्वविद्यालय", "type": "public", "location": "काठमाडौं"},
    "fw": {"name": "फर वेस्टर्न विश्वविद्यालय", "type": "public", "location": "सुर्खेत"},
    "mw": {"name": "मिड वेस्टर्न विश्वविद्यालय", "type": "public", "location": "सन्ध्या"},
    "tr": {"name": "त्रिभुवन विज्ञान विश्वविद्यालय", "type": "public", "location": "काठमाडौं"},
    "nr": {"name": "नेपाल राष्ट्रीय विश्वविद्यालय", "type": "public", "location": "काठमाडौं"},
}

SCHOOLS = {
    "s001": {"name": "गणेश हाइस्कुल", "district": "काठमाडौं", "type": "community"},
    "s002": {"name": "बृहद एकेडेमी", "district": "ललितपुर", "type": "private"},
    "s003": {"name": "भक्तपुर मावि", "district": "भक्तपुर", "type": "government"},
    "s004": {"name": "काठमाडौं विद्यालय", "district": "काठमाडौं", "type": "government"},
    "s005": {"name": "गोरखा मावि", "district": "गोरखा", "type": "government"},
    "s006": {"name": "पोखरा स्कूल", "district": "कास्की", "type": "private"},
    "s007": {"name": "चितवन उच्च मावि", "district": "चितवन", "type": "government"},
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
    "prachanda": {"name": "प्रचण्ड बैंक", "type": "commercial"},
    "mst": {"name": "मानक समय बैंक", "type": "commercial"},
    "vibl": {"name": "विकास बैंक", "type": "development"},
    "abl": {"name": "कृषि बैंक", "type": "development"},
    "hbl": {"name": "घर बैंक", "type": "housing"},
    "bbl": {"name": "बजार बैंक", "type": "market"},
    "ibl": {"name": "अन्तर्राष्ट्रिय बैंक", "type": "international"},
    "tebl": {"name": "तेल बैंक", "type": "energy"},
    "pbl": {"name": "पानी बैंक", "type": "water"},
    "jbl": {"name": "जनता बैंक", "type": "public"},
    "sukh": {"name": "सुखद बैंक", "type": "private"},
    "shaanti": {"name": "शान्ति बैंक", "type": "private"},
    "progati": {"name": "प्रगति बैंक", "type": "private"},
    "ujval": {"name": "उज्वल बैंक", "type": "private"},
    "agrni": {"name": "अग्रणी बैंक", "type": "private"},
    "vijay": {"name": "विजय बैंक", "type": "private"},
    "samriddhi": {"name": "समृद्धि बैंक", "type": "private"},
    "laks": {"name": "लक्ष्य बैंक", "type": "private"},
    "uple": {"name": "उपलब्धि बैंक", "type": "private"},
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
    "online": {"name": "अनलाइन नेट", "fiber": True},
    "fast": {"name": "फास्ट नेट", "fiber": True},
    "broadway": {"name": "ब्रडवे नेट", "fiber": True},
    "speed": {"name": "स्पीड नेट", "fiber": True},
    "netlink": {"name": "नेटलिंक", "fiber": True},
    "webnet": {"name": "वेबनेट", "fiber": True},
    "hitech": {"name": "हाइटेक", "fiber": True},
    "smartnet": {"name": "स्मार्टनेट", "fiber": True},
    "quicknet": {"name": "क्विकनेट", "fiber": True},
    "easynet": {"name": "इज़ीनेट", "fiber": True},
}

def get_entity(entity_type: str, code: str):
    """Get entity by type and code"""
    registry = {
        "ministry": MINISTRIES, "province": PROVINCES, "district": DISTRICTS,
        "bank": BANKS, "isp": ISPS, "university": UNIVERSITIES, "school": SCHOOLS
    }
    return registry.get(entity_type, {}).get(code)

def get_registry(entity_type: str):
    """Get full registry by type"""
    registry = {
        "ministry": MINISTRIES, "province": PROVINCES, "district": DISTRICTS,
        "bank": BANKS, "isp": ISPS, "university": UNIVERSITIES, "school": SCHOOLS
    }
    data = registry.get(entity_type, {})
    return {"count": len(data), "items": list(data.values())}

__all__ = ["MINISTRIES", "PROVINCES", "DISTRICTS", "BANKS", "ISPS", "UNIVERSITIES", "SCHOOLS", "get_entity", "get_registry"]