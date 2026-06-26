# AsimNexus World OS - Connectors Package

from .nepal_connectors import (
    MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS, UNIVERSITIES, SCHOOLS,
    get_entity, get_registry
)
from .health_connectors import (
    HOSPITALS, HEALTH_PROGRAMS, get_hospital, book_appointment, get_health_record
)
from .palika_connectors import PALIKAS, get_palika
from .tourism_connectors import HOTELS, TOURISM_SERVICES, get_hotel

__all__ = [
    "MINISTRIES", "PROVINCES", "DISTRICTS", "BANKS", "ISPS", "PALIKAS", "HOTELS",
    "UNIVERSITIES", "SCHOOLS", "HOSPITALS",
    "get_entity", "get_registry", "get_hospital", "get_palika", "get_hotel"
]