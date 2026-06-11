"""
AsimNexus — Nepal Integration Module
=====================================
Nepal-specific features: banking, telecom, government, language, and culture.

Sub-modules:
    banking_integrations    — eSewa, Khalti, ConnectIPS, etc.
    telecom_integrations    — NTC, Ncell, SmartCell
    government_integrations — Nagarik App, DoIT, e-ID bridge
    language_support        — Nepali NLP, Devanagari utilities
    cultural_features       — Festival calendar, cultural context
"""

from core.nepal.banking_integrations import (
    get_banking_status,
    get_supported_payment_methods,
    process_payment,
)
from core.nepal.telecom_integrations import (
    get_telecom_status,
    get_supported_operators,
    send_sms,
)
from core.nepal.government_integrations import (
    get_government_status,
    get_eid_countries,
    verify_identity,
)
from core.nepal.language_support import (
    get_language_status,
    transliterate,
    detect_language,
)
from core.nepal.cultural_features import (
    get_cultural_status,
    get_festival_calendar,
    get_cultural_context,
)

__all__ = [
    "get_banking_status", "get_supported_payment_methods", "process_payment",
    "get_telecom_status", "get_supported_operators", "send_sms",
    "get_government_status", "get_eid_countries", "verify_identity",
    "get_language_status", "transliterate", "detect_language",
    "get_cultural_status", "get_festival_calendar", "get_cultural_context",
]
