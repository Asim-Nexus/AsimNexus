#!/usr/bin/env python3
"""AsimNexus — Nepal १८ Ministries"""

from .ministry_base import MinistryConnector
from typing import Dict, Any

class PMOffice(MinistryConnector):
    def __init__(self):
        super().__init__("प्रधानमन्त्री कार्यालय", "pm_office", "51%")
        self.responsibilities = ["साइबर सुरक्षा", "डाटा गभर्नेन्स", "AI समन्वय", "राष्ट्रिय सुरक्षा"]

class FinanceMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("अर्थ मन्त्रालय", "finance", "51%")
        self.responsibilities = ["कर प्रणाली", "बजेट", "वित्तीय नीति"]

class HomeMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("गृह मन्त्रालय", "home", "51%")
        self.responsibilities = ["कानून व्यवस्था", "प्रहरी", "नागरिकता", "अध्यागमन"]

class HealthMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("स्वास्थ्य मन्त्रालय", "health", "51%")
        self.responsibilities = ["स्वास्थ्य नीति", "खाद्य सुरक्षा", "स्वास्थ्य बीमा"]

class EducationMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("शिक्षा मन्त्रालय", "education", "51%")
        self.responsibilities = ["शिक्षा नीति", "विद्यालय", "विश्वविद्यालय"]

class AgricultureMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("कृषि मन्त्रालय", "agriculture", "51%")
        self.responsibilities = ["कृषि", "वन", "वातावरण"]

class TourismMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("पर्यटन मन्त्रालय", "tourism", "51%")
        self.responsibilities = ["पर्यटन", "संस्कृति", "नागरिक उड्डयन"]

class EnergyMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("ऊर्जा मन्त्रालय", "energy", "51%")
        self.responsibilities = ["हाइड्रोपावर", "सिँचाइ", "नवीकरणीय ऊर्जा"]

class IndustryMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("उद्योग मन्त्रालय", "industry", "51%")
        self.responsibilities = ["उद्योग", "व्यापार", "FDI"]

class TelecomMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("सूचना तथा सञ्चार मन्त्रालय", "telecom", "51%")
        self.responsibilities = ["टेलिकम", "ISP", "प्रेस"]

class LandMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("भूमि मन्त्रालय", "land", "51%")
        self.responsibilities = ["जग्गा", "सहकारी", "संघीय मामिला"]

class LawMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("कानून मन्त्रालय", "law", "51%")
        self.responsibilities = ["कानून", "न्याय"]

class ForeignMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("परराष्ट्र मन्त्रालय", "foreign", "51%")
        self.responsibilities = ["कूटनीति", "राहदानी"]

class DefenseMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("रक्षा मन्त्रालय", "defense", "51%")
        self.responsibilities = ["नेपाली सेना", "राष्ट्रिय सुरक्षा"]

class ScienceMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("विज्ञान मन्त्रालय", "science", "51%")
        self.responsibilities = ["AI", "अनुसन्धान", "प्रविधि"]

class InfrastructureMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("भौतिक पूर्वाधार मन्त्रालय", "infrastructure", "51%")
        self.responsibilities = ["सडक", "रेल", "यातायात"]

class YouthMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("युवा, श्रम मन्त्रालय", "youth", "51%")
        self.responsibilities = ["रोजगार", "श्रम"]

class WomenMinistry(MinistryConnector):
    def __init__(self):
        super().__init__("महिला, बालबालिका मन्त्रालय", "women", "51%")
        self.responsibilities = ["सामाजिक सुरक्षा", "महिला अधिकार"]

NEPAL_MINISTRIES = [
    PMOffice(), FinanceMinistry(), HomeMinistry(), HealthMinistry(),
    EducationMinistry(), AgricultureMinistry(), TourismMinistry(), EnergyMinistry(),
    IndustryMinistry(), TelecomMinistry(), LandMinistry(), LawMinistry(),
    ForeignMinistry(), DefenseMinistry(), ScienceMinistry(), InfrastructureMinistry(),
    YouthMinistry(), WomenMinistry()
]

def get_ministry(sector: str) -> MinistryConnector:
    for m in NEPAL_MINISTRIES:
        if m.sector == sector:
            return m
    return None

__all__ = ["NEPAL_MINISTRIES", "MinistryConnector"]