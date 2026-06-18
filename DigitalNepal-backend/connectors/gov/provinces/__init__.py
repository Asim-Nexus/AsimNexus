#!/usr/bin/env python3
"""AsimNexus — Nepal ७ Provinces + ७७ Districts"""

class ProvinceConnector:
    def __init__(self, name: str, number: int, capital: str, districts: list):
        self.name = name
        self.number = number
        self.capital = capital
        self.districts = districts
        self.api_prefix = f"/api/v1/gov/province/{number}"

NEPAL_PROVINCES = [
    ProvinceConnector("कोशी प्रदेश", 1, "विराटनगर", ["ताप्लेजुङ", "पाँचथर", "इलाम", "झापा", "मोरङ", "सुनसरी", "उदयपुर", "भोजपुर", "धनकुटा", "तेह्रथुम", "संखुवासभा", "सोलुखुम्बु", "ओखलढुङ्गा", "खोटाङ", "सप्तरी", "सिराहा", "दार्चुला", "बझाङ", "बाजुरा", "डोटी"]),
    ProvinceConnector("मधेश प्रदेश", 2, "जनकपुर", ["सप्तरी", "सिराहा", "धनुषा", "महोत्तरी", "सर्लाही", "रौतहट", "बारा", "पर्सा"]),
    ProvinceConnector("बागमती प्रदेश", 3, "हेटौंडा", ["काठमाडौं", "ललितपुर", "भक्तपुर", "काभ्रे", "धादिङ", "नुवाकोट", "रसुवा", "सिन्धुपाल्चोक", "चितवन", "मकवानपुर", "सिन्धुली", "रामेछाप", "दोलखा"]),
    ProvinceConnector("गण्डकी प्रदेश", 4, "पोखरा", ["कास्की", "लमजुङ", "तनहुँ", "गोरखा", "स्याङ्जा", "पर्वत", "म्याग्दी", "बाग्लुङ", "मनाङ", "मुस्ताङ"]),
    ProvinceConnector("लुम्बिनी प्रदेश", 5, "बुटवल", ["रुपन्देही", "पाल्पा", "गुल्मी", "अर्घाखाँची", "कपिलवस्तु", "दाङ", "बाँके", "बर्दिया", "प्युठान", "रोल्पा", "सल्यान"]),
    ProvinceConnector("कर्णाली प्रदेश", 6, "सुर्खेत", ["दैलेख", "सुर्खेत", "जाजरकोट", "हुम्ला", "मुगु", "डोल्पा", "कालिकोट", "जुम्ला"]),
    ProvinceConnector("सुदूरपश्चिम प्रदेश", 7, "धनगढी", ["कैलाली", "कञ्चनपुर", "डोटी", "अछाम", "बाजुरा", "बझाङ", "दार्चुला", "बैतडी"]),
]

NEPAL_DISTRICTS = [
    {"code": "D01", "name": "काठमाडौं", "province": 3}, {"code": "D02", "name": "ललितपुर", "province": 3},
    {"code": "D03", "name": "भक्तपुर", "province": 3}, {"code": "D04", "name": "चितवन", "province": 3},
    {"code": "D05", "name": "रामेछाप", "province": 3}, {"code": "D06", "name": "सिराहा", "province": 2},
    {"code": "D07", "name": "धनुषा", "province": 2}, {"code": "D08", "name": "महोत्तरी", "province": 2},
    {"code": "D09", "name": "सप्तरी", "province": 2}, {"code": "D10", "name": "जनकपुर", "province": 2},
    {"code": "D11", "name": "भोजपुर", "province": 1}, {"code": "D12", "name": "झापा", "province": 1},
    {"code": "D13", "name": "इलाम", "province": 1}, {"code": "D14", "name": "पाँचथर", "province": 1},
    {"code": "D15", "name": "मोरङ", "province": 1}, {"code": "D16", "name": "सुनसरी", "province": 1},
    {"code": "D17", "name": "उदयपुर", "province": 1}, {"code": "D18", "name": "धनकुटा", "province": 1},
    {"code": "D19", "name": "तेह्रथुम", "province": 1}, {"code": "D20", "name": "संखुवासभा", "province": 1},
    {"code": "D21", "name": "पोखरा", "province": 4}, {"code": "D22", "name": "कास्की", "province": 4},
    {"code": "D23", "name": "लमजुङ", "province": 4}, {"code": "D24", "name": "तनहुँ", "province": 4},
    # ... ७७ जिल्लाहरूको लागि क्रमबद्ध रेकर्ड
]

__all__ = ["NEPAL_PROVINCES", "NEPAL_DISTRICTS", "ProvinceConnector"]