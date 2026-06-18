# AsimNexus World OS - Connectors Package
# Clean unified structure

from .nepal_connectors import (
    MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS,
    get_entity, get_registry
)
from .education_connectors import (
    UNIVERSITIES, SCHOOLS, get_university, get_school, verify_certificate
)
from .health_connectors import (
    HOSPITALS, HEALTH_PROGRAMS, get_hospital, book_appointment, get_health_record
)
from .palika_connectors import PALIKAS, get_palika, get_all_palikas
from .tourism_connectors import TOURISM_ENTITY

__all__ = [
    "MINISTRIES", "PROVINCES", "DISTRICTS", "BANKS", "ISPS", "PALIKAS",
    "UNIVERSITIES", "SCHOOLS", "HOSPITALS", "TOURISM_ENTITY",
    "get_entity", "get_registry", "get_university", "get_school", "get_hospital",
]