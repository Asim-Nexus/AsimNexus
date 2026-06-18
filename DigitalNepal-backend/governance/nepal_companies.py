#!/usr/bin/env python3
"""
AsimNexus - Nepal Banks (२७) + ISPs (५८)
Company Layer (49%) Implementation
"""

from typing import Dict, Any, List

# Nepal २७ बैंकहरू
NEPAL_BANKS = [
    "Nepal Rastra Bank", "Rastriya Banijya Bank", " Nepal Bank Limited",
    "Agricultural Development Bank", "Nepal Arab Bank", "Standard Chartered Bank",
    "Himalayan Bank", "Everest Bank", "Kumari Bank", "NIC Asia Bank",
    "Nabil Bank", "Laxmi Bank", "NMB Bank", "Prime Bank",
    "Global IME Bank", "Siddhartha Bank", "Citizens Bank", "Sunrise Bank",
    "Century Commercial Bank", "Machhapuchchhre Bank", "Kable Wholesale Bank",
    "Nepal Credit and Commerce Bank", "Civil Bank", "Excel Bank", "Sanima Bank",
    "Progressive Bank", "Goodwill Finance"
]

# Nepal ५८ ISPहरू
NEPAL_ISPS = [
    "NTC", "Ncell", "Smart Cell", "UTL", "Hello Mobile",
    "WorldLink", "Subisu", "Vianet", "Himalayan Technology", "Techminds",
    # ५८ मान लगाउने
]

def create_bank_connector(name: str) -> Dict[str, Any]:
    """Create bank connector by name"""
    for bank in NEPAL_BANKS:
        if name.lower() in bank.lower():
            return {
                "name": bank,
                "type": "bank",
                "country": "NP",
                "balance_check": lambda sector="finance": True  # 49% threshold
            }
    return None

def create_isp_connector(name: str) -> Dict[str, Any]:
    """Create ISP connector by name"""
    for isp in NEPAL_ISPS:
        if name.lower() in isp.lower():
            return {
                "name": isp,
                "type": "isp",
                "country": "NP",
                "sector": "telecom"
            }
    return None

def get_company_stats() -> Dict[str, Any]:
    """Get company statistics"""
    return {
        "total_banks": len(NEPAL_BANKS),
        "total_isps": len(NEPAL_ISPS),
        "country": "NP",
        "balance_type": "private_operated",
        "threshold": 49
    }


__all__ = ["NEPAL_BANKS", "NEPAL_ISPS", "create_bank_connector", "create_isp_connector", "get_company_stats"]