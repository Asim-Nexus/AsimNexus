"""European Union Policy Pack — Governs operations within EU/EEA jurisdiction.

Based on:
- General Data Protection Regulation (GDPR) 2016/679
- EU AI Act 2024
- eIDAS Regulation (electronic identification)
- Digital Services Act (DSA)
- Digital Markets Act (DMA)
- NIS2 Directive (cybersecurity)
"""

from core.governance.country_packs import CountryPack

EUPolicyPack = CountryPack(
    code="eu",
    name="European Union",
    description="EU jurisdiction policy pack — GDPR, AI Act, eIDAS, DSA, DMA, NIS2",
    default_language="en",
    data_localization_required=True,  # GDPR adequacy decisions required
    requires_sovereign_approval=[
        "gov:policy_write",
        "gov:veto",
        "datalake:ingest",
        "datalake:query",
        "auth:manage",
        "mesh:connect",
        "mesh:sync",
    ],
    restricted_capabilities=[
        "gov:veto",
        "datalake:ingest",  # GDPR Article 9 — special category data
    ],
    privacy_standard="GDPR",  # General Data Protection Regulation
)
