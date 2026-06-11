"""
Nepal Telecom Integrations
==========================
Supported telecom operators and SMS/voice services in Nepal.

Key operators:
    - Nepal Telecom (NTC) — ntcone.net
    - Ncell (ncells.com)
    - SmartCell (smartcell.com.np)
    - UTL (utlnet.net.np)
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("AsimNexus.Nepal.Telecom")

_OPERATORS = {
    "ntc": {
        "name": "Nepal Telecom",
        "short_name": "NTC",
        "country_code": "977",
        "prefixes": ["974", "975", "976", "984", "985", "986"],
        "status": "active",
        "services": ["sms", "voice", "data", "ussd"],
    },
    "ncell": {
        "name": "Ncell",
        "short_name": "Ncell",
        "country_code": "977",
        "prefixes": ["981", "982", "983", "984"],
        "status": "active",
        "services": ["sms", "voice", "data", "ussd"],
    },
    "smartcell": {
        "name": "SmartCell",
        "short_name": "SmartCell",
        "country_code": "977",
        "prefixes": ["960", "961", "962"],
        "status": "active",
        "services": ["sms", "voice", "data"],
    },
    "utl": {
        "name": "United Telecom Limited",
        "short_name": "UTL",
        "country_code": "977",
        "prefixes": ["976"],
        "status": "active",
        "services": ["sms", "voice"],
    },
}


def get_telecom_status() -> Dict:
    """Return overall Nepal telecom integration status."""
    active = sum(1 for o in _OPERATORS.values() if o["status"] == "active")
    return {
        "country": "Nepal",
        "operators_available": active,
        "total_operators": len(_OPERATORS),
        "operators": list(_OPERATORS.keys()),
        "country_code": "977",
        "status": "active",
    }


def get_supported_operators() -> List[Dict]:
    """Return list of supported telecom operators."""
    return list(_OPERATORS.values())


def detect_operator(phone_number: str) -> Optional[Dict]:
    """Detect telecom operator from a Nepal phone number.

    Args:
        phone_number: Phone number (with or without +977 prefix)

    Returns:
        Operator dict or None if not detected.
    """
    cleaned = phone_number.replace("+", "").replace(" ", "").replace("-", "")
    if cleaned.startswith("977"):
        cleaned = cleaned[3:]

    for op in _OPERATORS.values():
        for prefix in op["prefixes"]:
            if cleaned.startswith(prefix):
                return op
    return None


def send_sms(to: str, message: str, operator: Optional[str] = None,
             metadata: Optional[Dict] = None) -> Dict:
    """Simulate sending an SMS via a Nepal telecom operator.

    Args:
        to: Recipient phone number
        message: SMS content (max 160 chars per segment)
        operator: Specific operator key (auto-detected if None)
        metadata: Optional metadata

    Returns:
        SMS send result dict.
    """
    detected = detect_operator(to)
    if not detected:
        return {
            "success": False,
            "error": f"Could not detect operator for number: {to}",
        }

    if operator and operator.lower() not in _OPERATORS:
        return {
            "success": False,
            "error": f"Unknown operator: {operator}",
            "known_operators": list(_OPERATORS.keys()),
        }

    op = _OPERATORS.get(operator.lower()) if operator else detected
    segments = max(1, (len(message) + 159) // 160)

    logger.info(
        "Sending SMS via %s to %s (%d segment(s))",
        op["name"], to, segments,
    )

    return {
        "success": True,
        "operator": op["name"],
        "to": to,
        "segments": segments,
        "message_length": len(message),
        "message_id": f"SMS-{op['short_name']}-{hash(str(metadata)) % 10**8:08d}",
        "status": "queued",
    }
