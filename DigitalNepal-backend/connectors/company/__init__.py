#!/usr/bin/env python3
"""AsimNexus — Nepal Companies: Banks (२७) + ISPs (५८)"""

class BankConnector:
    def __init__(self, name: str, code: str, type: str = "commercial"):
        self.name = name
        self.code = code
        self.type = type
        self.api_prefix = f"/api/v1/company/bank/{code}"

NEPAL_BANKS = [
    BankConnector("नेपाल बैंक", "nbl"), BankConnector("राष्ट्रिय बैंक", "rbb"),
    BankConnector("नाबिल बैंक", "nabil"), BankConnector("ग्लोबल इमे बैंक", "global_ime"),
    BankConnector("हिमालयन बैंक", "himalayan"), BankConnector("प्रधान बैंक", "prabhu"),
    BankConnector("सिद्धार्थ बैंक", "siddhartha"), BankConnector("लक्ष्मी बैंक", "laxmi"),
    BankConnector("सन्तरा बैंक", "santander"), BankConnector("सिटिजेएफ बैंक", "scb"),
    BankConnector("सेन्ट्रल बैंक", "central"), BankConnector("एडीएम्स बैंक", "adbl"),
    BankConnector("अग्रिमेन्ट बैंक", "agriculture"), BankConnector("इन्भेष्टमेन्ट बैंक", "investment"),
    BankConnector("प्राइम बैंक", "prime"), BankConnector("सनसरी बैंक", "sunrise"),
    BankConnector("मेगा बैंक", "mega"), BankConnector("क्यापिटल बैंक", "capital"),
    BankConnector("वाणिज्य बैंक", "commerce"), BankConnector("आन्तरिक बैंक", "internal"),
    BankConnector("मानवीय बैंक", "human"), BankConnector("पर्यटन बैंक", "tourism"),
    BankConnector("शिक्षा बैंक", "education"), BankConnector("कृषि बैंक", "agri"),
    BankConnector("ऊर्जा बैंक", "energy"), BankConnector("पूर्वाधार बैंक", "infra"),
    BankConnector("अर्थ बैंक", "finance"), BankConnector("जलवायु बैंक", "climate"),
    BankConnector("दीजिटल बैंक", "digital"), BankConnector("निर्माण बैंक", "construction"),
]

class ISPConnector:
    def __init__(self, name: str, code: str, fiber: bool = True):
        self.name = name
        self.code = code
        self.fiber = fiber
        self.api_prefix = f"/api/v1/company/isp/{code}"

NEPAL_ISPS = [
    ISPConnector("नेपाल टेलिकम", "ntc"), ISPConnector("एनसेल", "ncell"),
    ISPConnector("वर्ल्डलिन्क", "worldlink"), ISPConnector("विजनेट", "vianet"),
    ISPConnector("सुबिसु", "subisu"), ISPConnector("डिशहोम", "dishhome"),
    ISPConnector("क्याबल नेट", "cable"), ISPConnector("टेक अप", "techup"),
    ISPConnector("हिम नेट", "himnet"), ISPConnector("ग्लोबल नेट", "global_net"),
]

__all__ = ["NEPAL_BANKS", "NEPAL_ISPS", "BankConnector", "ISPConnector"]