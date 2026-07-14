"""United States Policy Pack — Governs operations within US jurisdiction.

Based on:
- US Constitution
- Federal Information Security Modernization Act (FISMA)
- California Consumer Privacy Act (CCPA) / CPRA
- HIPAA (health data)
- SOX (financial data)
- State-level variations
"""

from core.governance.country_packs import CountryPack

USPolicyPack = CountryPack(
    code="us",
    name="United States",
    description="US jurisdiction policy pack — FISMA, CCPA, HIPAA, SOX compliance",
    default_language="en",
    data_localization_required=False,  # Federal level; states may differ
    requires_sovereign_approval=[
        "gov:policy_write",
        "gov:veto",
        "datalake:verify",
        "hw:driver",
    ],
    restricted_capabilities=[
        "gov:veto",
    ],
    privacy_standard="CCPA",  # California Consumer Privacy Act (baseline)
)
