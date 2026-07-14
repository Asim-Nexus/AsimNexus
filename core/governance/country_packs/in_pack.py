"""India Policy Pack — Governs operations within Indian jurisdiction.

Based on:
- Constitution of India 1950
- Information Technology Act 2000 (amended 2008)
- Digital Personal Data Protection Act 2023
- RBI data localization directives
- Aadhaar Act 2016
"""

from core.governance.country_packs import CountryPack

IndiaPolicyPack = CountryPack(
    code="in",
    name="India",
    description="India jurisdiction policy pack — IT Act 2000, DPDPA 2023, RBI localization",
    default_language="hi",
    data_localization_required=True,
    requires_sovereign_approval=[
        "gov:policy_write",
        "gov:veto",
        "datalake:verify",
        "auth:manage",
        "mesh:connect",
        "datalake:ingest",
    ],
    restricted_capabilities=[
        "gov:veto",
        "datalake:ingest",  # Sensitive data ingestion needs approval
    ],
    privacy_standard="DPDPA",  # Digital Personal Data Protection Act 2023
)
