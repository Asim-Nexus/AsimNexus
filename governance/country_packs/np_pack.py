"""Nepal Policy Pack — Governs operations within Nepali jurisdiction.

Based on:
- Constitution of Nepal 2015
- IT Act 2063 (2008)
- Data localization requirements per Nepal's IT Bill
- Nepal Rastra Bank directives on data sovereignty
"""

from governance.country_packs import CountryPack

NepalPolicyPack = CountryPack(
    code="np",
    name="Nepal",
    description="Nepal jurisdiction policy pack — Constitution of Nepal 2015, IT Act 2063",
    default_language="ne",
    data_localization_required=True,
    requires_sovereign_approval=[
        "gov:policy_write",
        "gov:veto",
        "datalake:verify",
        "hw:driver",
        "auth:manage",
        "mesh:connect",
    ],
    restricted_capabilities=[
        "gov:veto",  # Only government-layer can veto
        "hw:driver",  # Hardware drivers need sovereign approval
    ],
    privacy_standard="PDPA",  # Nepal's Personal Data Protection Act (draft)
)
