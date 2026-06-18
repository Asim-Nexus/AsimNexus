# AsimNexus World OS - Nepal Connectors
# 🇳🇵 Nepal Government, Economy, Culture

from .ministries import (
    NEPAL_MINISTRIES,
    get_nepal_ministry,
    list_nepal_ministries,
    get_ministry_stats
)
from .provinces import (
    NEPAL_PROVINCES,
    get_province,
    list_provinces,
    get_province_stats
)
from .districts import (
    ALL_DISTRICTS,
    get_district,
    list_districts,
    get_district_stats
)

__all__ = [
    "NEPAL_MINISTRIES", "get_nepal_ministry", "list_nepal_ministries", "get_ministry_stats",
    "NEPAL_PROVINCES", "get_province", "list_provinces", "get_province_stats",
    "ALL_DISTRICTS", "get_district", "list_districts", "get_district_stats"
]