"""
STATUS: REAL — AsimNexus Sector Connectors Registry

All Sector Connectors for Nepal Digital Ecosystem
"""

from typing import Dict, Optional

# Import all connectors
from .agriculture_connector import AgricultureConnector
from .tourism_connector import TourismConnector
from .banking_connector import BankingConnector
from .telecom_connector import TelecomConnector
from .fintech_connector import FintechConnector
from .isp_connector import ISPConnector
from .hydropower_connector import HydropowerConnector
from .education_connector import EducationConnector
from .government_connector import GovernmentConnector
from .health_connector import HealthConnector
from .ecommerce_connector import EcommerceConnector

_SECTOR_CONNECTORS: Dict[str, object] = {
    "agriculture": AgricultureConnector(),
    "tourism": TourismConnector(),
    "banking": BankingConnector(),
    "telecom": TelecomConnector(),
    "fintech": FintechConnector(),
    "isp": ISPConnector(),
    "hydropower": HydropowerConnector(),
    "education": EducationConnector(),
    "government": GovernmentConnector(),
    "health": HealthConnector(),
    "ecommerce": EcommerceConnector(),
}

def get_sector_connector(sector: str):
    """Get sector connector by name"""
    return _SECTOR_CONNECTORS.get(sector.lower())

def list_sectors() -> list:
    """List all available sectors"""
    return list(_SECTOR_CONNECTORS.keys())

__all__ = [
    "get_sector_connector", 
    "list_sectors",
    "AgricultureConnector",
    "TourismConnector",
    "BankingConnector",
    "TelecomConnector",
    "FintechConnector",
    "ISPConnector",
    "HydropowerConnector",
    "EducationConnector",
    "GovernmentConnector",
    "HealthConnector",
    "EcommerceConnector",
]