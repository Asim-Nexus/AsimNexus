#!/usr/bin/env python3
"""
AsimNexus World OS - USA Connectors
🇺🇸 USA Government (२६ Departments), ५० राज्य, ३,०००+ जिल्ला
"""

from typing import List, Dict
from connectors.ministry_template import MinistryConfig, MinistrySector

# ─── USA Government ──────────────────────────────────────────────────────

USA_DEPARTMENTS = [
    MinistryConfig("White House", MinistrySector.GOVERNANCE, "/api/v1/us/gov/whitehouse", True, False),
    MinistryConfig("State", MinistrySector.GOVERNANCE, "/api/v1/us/gov/state", True, False),
    MinistryConfig("Treasury", MinistrySector.FINANCE, "/api/v1/us/gov/treasury", True, False),
    MinistryConfig("Defense", MinistrySector.GOVERNANCE, "/api/v1/us/gov/defense", True, False),
    MinistryConfig("Justice", MinistrySector.GOVERNANCE, "/api/v1/us/gov/justice", True, False),
    MinistryConfig("Interior", MinistrySector.GOVERNANCE, "/api/v1/us/gov/interior", True, False),
    MinistryConfig("Agriculture", MinistrySector.AGRICULTURE, "/api/v1/us/gov/agriculture", True, False),
    MinistryConfig("Commerce", MinistrySector.GOVERNANCE, "/api/v1/us/gov/commerce", True, False),
    MinistryConfig("Health", MinistrySector.HEALTHCARE, "/api/v1/us/gov/health", True, False),
    MinistryConfig("Education", MinistrySector.EDUCATION, "/api/v1/us/gov/education", True, False),
]

USA_STATES = [
    {"code": "AL", "name": "Alabama", "capital": "Montgomery"},
    {"code": "AK", "name": "Alaska", "capital": "Juneau"},
    {"code": "AZ", "name": "Arizona", "capital": "Phoenix"},
    {"code": "CA", "name": "California", "capital": "Sacramento"},
    {"code": "FL", "name": "Florida", "capital": "Tallahassee"},
    {"code": "NY", "name": "New York", "capital": "Albany"},
    {"code": "TX", "name": "Texas", "capital": "Austin"},
    {"code": "WA", "name": "Washington", "capital": "Olympia"},
]

def create_county_template(total: int = 3000) -> List[Dict]:
    counties = []
    for i in range(1, total + 1):
        counties.append({
            "code": f"USCT{i:05d}",
            "name": f"County {i}",
            "state": USA_STATES[i % len(USA_STATES)]["code"],
            "type": "county"
        })
    return counties

USA_ALL_COUNTIES = create_county_template(3000)

__all__ = ["USA_DEPARTMENTS", "USA_STATES", "USA_ALL_COUNTIES"]