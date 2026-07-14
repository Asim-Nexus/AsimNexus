"""Country-specific policy packs for jurisdiction-aware governance.

Each country pack defines:
- Default policy rules (allow/deny) for capabilities
- Regulatory requirements (data localization, privacy standards)
- Sovereign override keys for government-layer policies
- Language and cultural defaults

Packs integrate with the Gateway's VersionedPolicyEngine
as the GOVERNMENT policy layer (highest precedence).
"""

from typing import Dict, List, Optional, Type
from dataclasses import dataclass, field


@dataclass
class CountryPack:
    """Base structure for a country policy pack."""
    code: str
    name: str
    description: str
    default_language: str
    data_localization_required: bool
    requires_sovereign_approval: List[str]  # capability IDs needing gov approval
    restricted_capabilities: List[str]  # capabilities denied by default
    privacy_standard: str  # e.g., "GDPR", "CCPA", "PDPA"


# Import country-specific packs after CountryPack is defined
# to avoid circular import (pack files import CountryPack from this module)
from core.governance.country_packs.np_pack import NepalPolicyPack
from core.governance.country_packs.in_pack import IndiaPolicyPack
from core.governance.country_packs.us_pack import USPolicyPack
from core.governance.country_packs.eu_pack import EUPolicyPack


# Registry of all available country packs
COUNTRY_PACKS: Dict[str, CountryPack] = {
    "np": NepalPolicyPack,
    "in": IndiaPolicyPack,
    "us": USPolicyPack,
    "eu": EUPolicyPack,
}


def get_country_pack(code: str) -> Optional[CountryPack]:
    """Get a country pack by ISO 3166-1 alpha-2 code."""
    return COUNTRY_PACKS.get(code.lower())


def list_available_packs() -> List[Dict[str, str]]:
    """List all available country packs."""
    return [
        {
            "code": pack.code,
            "name": pack.name,
            "description": pack.description,
            "language": pack.default_language,
        }
        for pack in COUNTRY_PACKS.values()
    ]


__all__ = [
    "CountryPack",
    "COUNTRY_PACKS",
    "get_country_pack",
    "list_available_packs",
    "NepalPolicyPack",
    "IndiaPolicyPack",
    "USPolicyPack",
    "EUPolicyPack",
]
