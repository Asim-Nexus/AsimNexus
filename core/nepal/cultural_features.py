"""
Nepal Cultural Features
=======================
Nepali cultural context, festival calendar, and social norms.

Features:
    - Festival calendar (major Nepali festivals with dates)
    - Cultural context for AI interactions
    - Social norms and etiquette
    - Regional/caste diversity awareness
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("AsimNexus.Nepal.Culture")

# Major Nepali festivals (approximate dates, updated yearly)
_FESTIVALS = [
    {
        "name": "Vishu/New Year",
        "nepali_name": "नयाँ वर्ष",
        "month": "Baisakh",
        "approx_date": "April 13-14",
        "type": "national",
        "description": "Nepali New Year (Bikram Sambat)",
        "significance": "First day of Baisakh, start of Nepali calendar",
    },
    {
        "name": "Buddha Jayanti",
        "nepali_name": "बुद्ध जयन्ती",
        "month": "Baisakh/Jestha",
        "approx_date": "May (full moon)",
        "type": "religious",
        "description": "Birth anniversary of Lord Buddha",
        "significance": "Celebrated in Lumbini (birthplace of Buddha)",
    },
    {
        "name": "Janai Purnima / Rakshya Bandhan",
        "nepali_name": "जनै पूर्णिमा / रक्षा बन्धन",
        "month": "Shrawan/Bhadra",
        "approx_date": "August (full moon)",
        "type": "religious",
        "description": "Sacred thread festival / sibling bond festival",
        "significance": "Hindu men change sacred thread; sisters tie rakhi",
    },
    {
        "name": "Gai Jatra",
        "nepali_name": "गाई जात्रा",
        "month": "Bhadra",
        "approx_date": "August-September",
        "type": "festival",
        "description": "Cow festival — honoring deceased family members",
        "significance": "Unique to Nepal; comedy and satire performances",
    },
    {
        "name": "Indra Jatra",
        "nepali_name": "इन्द्र जात्रा",
        "month": "Bhadra",
        "approx_date": "September",
        "type": "festival",
        "description": "Festival of Indra (Kathmandu Valley)",
        "significance": "Kumari (Living Goddess) procession",
    },
    {
        "name": "Dashain",
        "nepali_name": "दशैं",
        "month": "Ashwin",
        "approx_date": "September-October",
        "type": "national",
        "description": "Biggest Nepali festival (15 days)",
        "significance": "Victory of good over evil; family reunions",
        "duration_days": 15,
    },
    {
        "name": "Tihar / Deepawali",
        "nepali_name": "तिहार / दीपावली",
        "month": "Kartik",
        "approx_date": "October-November",
        "type": "national",
        "description": "Festival of lights (5 days)",
        "significance": "Worship of crows, dogs, cows, Laxmi, and brothers",
        "duration_days": 5,
    },
    {
        "name": "Chhath Parva",
        "nepali_name": "छठ पर्व",
        "month": "Kartik",
        "approx_date": "October-November",
        "type": "religious",
        "description": "Sun worship festival (Terai region)",
        "significance": "Offering to Surya (Sun God) at riversides",
    },
    {
        "name": "Maha Shivaratri",
        "nepali_name": "महा शिवरात्रि",
        "month": "Falgun",
        "approx_date": "February-March",
        "type": "religious",
        "description": "Night of Lord Shiva",
        "significance": "Pashupatinath Temple pilgrimage",
    },
    {
        "name": "Holi",
        "nepali_name": "होली",
        "month": "Falgun",
        "approx_date": "March (full moon)",
        "type": "festival",
        "description": "Festival of colors",
        "significance": "Celebration of spring and color",
    },
]


def get_cultural_status() -> Dict:
    """Return Nepal cultural features status."""
    return {
        "country": "Nepal",
        "festivals_tracked": len(_FESTIVALS),
        "features": [
            "Festival calendar with approximate dates",
            "Cultural context for AI interactions",
            "Social norms and etiquette awareness",
            "Regional diversity understanding",
        ],
        "status": "active",
    }


def get_festival_calendar() -> List[Dict]:
    """Return the full festival calendar."""
    return list(_FESTIVALS)


def get_upcoming_festivals(count: int = 3) -> List[Dict]:
    """Return the next N upcoming festivals based on current date.

    Args:
        count: Number of upcoming festivals to return

    Returns:
        List of upcoming festival dicts (estimated).
    """
    # Order festivals by approximate month order (Baisakh=1, ... Chaitra=12)
    month_order = {
        "Baisakh": 1, "Jestha": 2, "Ashadh": 3, "Shrawan": 4,
        "Bhadra": 5, "Ashwin": 6, "Kartik": 7, "Mangsir": 8,
        "Poush": 9, "Magh": 10, "Falgun": 11, "Chaitra": 12,
    }
    sorted_festivals = sorted(
        _FESTIVALS,
        key=lambda f: month_order.get(f["month"], 99),
    )
    return sorted_festivals[:count]


def get_cultural_context(topic: Optional[str] = None) -> Dict:
    """Get cultural context for AI interactions in Nepal.

    Args:
        topic: Optional specific topic (e.g. "greetings", "business", "festivals")

    Returns:
        Cultural context dict.
    """
    base_context = {
        "country": "Nepal",
        "languages": ["Nepali", "English"],
        "greetings": {
            "formal": "Namaste (नमस्ते)",
            "informal": "K cha? (के छ?)",
            "respect": "Use 'tapain' (तपाईं) for elders",
        },
        "social_norms": [
            "Remove shoes before entering homes",
            "Right hand for giving/receiving",
            "Avoid pointing feet at people or shrines",
            "Head is considered sacred — avoid touching",
        ],
        "business_etiquette": [
            "Hierarchy and seniority respected",
            "Relationship-building before business",
            "Punctuality appreciated but flexibly observed",
            "Modest dress expected",
        ],
        "diversity_awareness": [
            "Over 120 ethnic groups and castes",
            "Nepali is lingua franca; many mother tongues",
            "Religious: Hindu (81%), Buddhist (9%), Muslim (4%)",
            "Regional differences: Mountain, Hill, Terai",
        ],
    }

    if topic == "greetings":
        return {"topic": "greetings", **base_context["greetings"]}
    elif topic == "business":
        return {
            "topic": "business_etiquette",
            "business_etiquette": base_context["business_etiquette"],
        }
    elif topic == "festivals":
        return {
            "topic": "festivals",
            "festivals": _FESTIVALS,
            "upcoming": get_upcoming_festivals(3),
        }
    else:
        return base_context
