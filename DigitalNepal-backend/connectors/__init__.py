# AsimNexus World OS - Connectors Package
# Clean unified structure

from .nepal_connectors import (
    MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS,
    get_entity, get_registry
)

__all__ = [
    "MINISTRIES", "PROVINCES", "DISTRICTS", "BANKS", "ISPS",
    "get_entity", "get_registry"
]