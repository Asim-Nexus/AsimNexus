# AsimNexus World OS - Connectors Package
# Templates for all countries, ministries, companies

from .country_template import CountryConfig, SectorType, CountryConnector, get_country, NEPAL_CONFIG
from .ministry_template import MinistrySector, MinistryConfig, MinistryConnector, get_ministry, list_ministries
from .world_manager import WorldConnectorManager, get_world_manager, WORLD_COUNTRIES

# Import country-specific connectors
from . import nepal
from . import india
from . import usa

__all__ = [
    "CountryConfig", "SectorType", "CountryConnector", "get_country", "NEPAL_CONFIG",
    "MinistrySector", "MinistryConfig", "MinistryConnector", "get_ministry", "list_ministries",
    "WorldConnectorManager", "get_world_manager", "WORLD_COUNTRIES",
    "nepal", "india", "usa"
]