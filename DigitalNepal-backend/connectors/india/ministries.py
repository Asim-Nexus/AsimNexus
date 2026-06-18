#!/usr/bin/env python3
"""
AsimNexus World OS - India Connectors
🇮🇳 India Government (५०+ मन्त्रालय), २८ राज्य, ७७४ जिल्ला
"""

from typing import List, Dict
from dataclasses import dataclass

from connectors.ministry_template import MinistryConfig, MinistrySector

# ─── India Government ────────────────────────────────────────────────────

INDIA_MINISTRIES = [
    MinistryConfig("PM Office", MinistrySector.GOVERNANCE, "/api/v1/in/gov/pm", True, False),
    MinistryConfig("Finance", MinistrySector.FINANCE, "/api/v1/in/gov/finance", True, False),
    MinistryConfig("Home Affairs", MinistrySector.GOVERNANCE, "/api/v1/in/gov/home", True, False),
    MinistryConfig("Health", MinistrySector.HEALTHCARE, "/api/v1/in/gov/health", True, False),
    MinistryConfig("Education", MinistrySector.EDUCATION, "/api/v1/in/gov/education", True, False),
    MinistryConfig("Agriculture", MinistrySector.AGRICULTURE, "/api/v1/in/gov/agriculture", True, False),
    MinistryConfig("Railways", MinistrySector.GOVERNANCE, "/api/v1/in/gov/railways", True, False),
    MinistryConfig("Defense", MinistrySector.GOVERNANCE, "/api/v1/in/gov/defense", True, False),
    MinistryConfig("External Affairs", MinistrySector.GOVERNANCE, "/api/v1/in/gov/external", True, False),
]

INDIA_STATES = [
    {"code": "AP", "name": "Andhra Pradesh", "capital": "Amaravati"},
    {"code": "BR", "name": "Bihar", "capital": "Patna"},
    {"code": "CG", "name": "Chhattisgarh", "capital": "Raipur"},
    {"code": "DL", "name": "Delhi", "capital": "New Delhi"},
    {"code": "GJ", "name": "Gujarat", "capital": "Gandhinagar"},
    {"code": "HR", "name": "Haryana", "capital": "Chandigarh"},
    {"code": "JK", "name": "Jammu Kashmir", "capital": "Srinagar"},
    {"code": "JH", "name": "Jharkhand", "capital": "Ranchi"},
    {"code": "KA", "name": "Karnataka", "capital": "Bengaluru"},
    {"code": "KL", "name": "Kerala", "capital": "Thiruvananthapuram"},
    {"code": "MH", "name": "Maharashtra", "capital": "Mumbai"},
    {"code": "PB", "name": "Punjab", "capital": "Chandigarh"},
    {"code": "RJ", "name": "Rajasthan", "capital": "Jaipur"},
    {"code": "TN", "name": "Tamil Nadu", "capital": "Chennai"},
    {"code": "TS", "name": "Telangana", "capital": "Hyderabad"},
    {"code": "UP", "name": "Uttar Pradesh", "capital": "Lucknow"},
    {"code": "WB", "name": "West Bengal", "capital": "Kolkata"},
]

def create_district_template(total: int = 774) -> List[Dict]:
    districts = []
    for i in range(1, total + 1):
        districts.append({
            "code": f"INDT{i:04d}",
            "name": f"District {i}",
            "state": INDIA_STATES[i % len(INDIA_STATES)]["code"],
            "type": "district"
        })
    return districts

INDIA_ALL_DISTRICTS = create_district_template(774)

# ─── Exports ───────────────────────────────────────────────────────────────

__all__ = [
    "INDIA_MINISTRIES", "INDIA_STATES", "INDIA_ALL_DISTRICTS"
]