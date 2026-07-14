"""
AsimNexus Government Module
============================
Bridge module providing GovernmentManager and GovernmentStatus for routes/government.py
and routes/analytics.py. Delegates to core/governance/* for actual implementations.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("AsimNexus.Government")


class GovernmentStatus(str, Enum):
    """Status of the government integration system."""
    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class GovernmentManager:
    """Central government manager — handles identity, e-Residency, tax, signatures."""

    def __init__(self):
        self._status = GovernmentStatus.ACTIVE
        self._identity_countries = [
            "NP", "US", "UK", "EU", "IN", "CA", "AU", "JP", "SG", "AE"
        ]
        self._eresidency_programs = [
            {"id": "er-np", "name": "Nepal e-Residency", "country": "NP", "fee": 0},
            {"id": "er-ee", "name": "Estonia e-Residency", "country": "EE", "fee": 100},
            {"id": "er-uae", "name": "UAE Virtual Work", "country": "AE", "fee": 0},
            {"id": "er-sg", "name": "Singapore EntrePass", "country": "SG", "fee": 500},
        ]
        self._tax_countries = [
            "NP", "US", "UK", "IN", "CA", "AU", "DE", "FR", "SG", "AE"
        ]
        self._signature_regions = [
            {"id": "np", "name": "Nepal", "standard": "NP DSC"},
            {"id": "eu", "name": "European Union", "standard": "eIDAS"},
            {"id": "us", "name": "United States", "standard": "ESIGN"},
            {"id": "uk", "name": "United Kingdom", "standard": "UK ESIGN"},
            {"id": "in", "name": "India", "standard": "DSC"},
        ]
        self._services = {
            "NP": [
                {"id": "citizenship", "name": "Digital Citizenship"},
                {"id": "passport", "name": "e-Passport"},
                {"id": "pan", "name": "PAN Registration"},
                {"id": "company", "name": "Company Registration"},
                {"id": "land", "name": "Land Records"},
            ],
            "US": [
                {"id": "ssn", "name": "SSN Verification"},
                {"id": "passport", "name": "US Passport"},
                {"id": "ein", "name": "EIN Registration"},
            ],
            "default": [
                {"id": "identity", "name": "Digital Identity"},
                {"id": "tax", "name": "Tax Filing"},
            ],
        }
        self._active_identities = 0
        self._identity_records: Dict[str, Dict[str, Any]] = {}

    def get_status(self) -> GovernmentStatus:
        return self._status

    def get_identity_countries_count(self) -> int:
        return len(self._identity_countries)

    def get_eresidency_programs_count(self) -> int:
        return len(self._eresidency_programs)

    def get_tax_countries_count(self) -> int:
        return len(self._tax_countries)

    def get_signature_regions_count(self) -> int:
        return len(self._signature_regions)

    def get_active_identities_count(self) -> int:
        return self._active_identities

    def get_services_count(self) -> int:
        total = 0
        for svcs in self._services.values():
            total += len(svcs)
        return total

    def get_identity_countries(self) -> List[str]:
        return list(self._identity_countries)

    def create_identity(self, user_id: str, country: str = "NP",
                        identity_type: str = "basic",
                        metadata: Dict = None) -> Dict[str, Any]:
        self._active_identities += 1
        identity_id = f"id_{user_id}_{country}_{self._active_identities}"
        record = {
            "identity_id": identity_id,
            "user_id": user_id,
            "country": country.upper(),
            "identity_type": identity_type,
            "status": "created",
            "verification_level": 0,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        self._identity_records[identity_id] = record
        return record

    def verify_identity(self, identity_id: str, verification_level: int = 1,
                        documents: List[str] = None) -> Dict[str, Any]:
        record = self._identity_records.get(identity_id)
        if not record:
            return {"status": "not_found", "identity_id": identity_id}
        record["verification_level"] = verification_level
        record["status"] = "verified" if verification_level >= 2 else "partial"
        record["documents"] = documents or []
        record["verified_at"] = datetime.utcnow().isoformat()
        return record

    def get_eresidency_programs(self) -> List[Dict[str, Any]]:
        return list(self._eresidency_programs)

    def apply_eresidency(self, user_id: str, program_id: str,
                         documents: List[str] = None,
                         reason: str = "") -> Dict[str, Any]:
        program = None
        for p in self._eresidency_programs:
            if p["id"] == program_id:
                program = p
                break
        return {
            "application_id": f"er_{user_id}_{program_id}",
            "user_id": user_id,
            "program": program or {"id": program_id, "name": "Unknown"},
            "status": "submitted",
            "documents": documents or [],
            "reason": reason,
            "applied_at": datetime.utcnow().isoformat(),
        }

    def get_tax_countries(self) -> List[str]:
        return list(self._tax_countries)

    def calculate_tax(self, user_id: str, country: str = "NP",
                      income: float = 0, deductions: List[Dict] = None,
                      tax_year: int = 2024) -> Dict[str, Any]:
        deductions = deductions or []
        total_deductions = sum(d.get("amount", 0) for d in deductions)
        taxable_income = max(0, income - total_deductions)
        if country.upper() == "NP":
            if taxable_income <= 500000:
                tax = taxable_income * 0.01
            elif taxable_income <= 700000:
                tax = 5000 + (taxable_income - 500000) * 0.10
            elif taxable_income <= 1000000:
                tax = 25000 + (taxable_income - 700000) * 0.20
            else:
                tax = 85000 + (taxable_income - 1000000) * 0.30
        elif country.upper() == "US":
            tax = taxable_income * 0.22
        else:
            tax = taxable_income * 0.15
        return {
            "user_id": user_id,
            "country": country.upper(),
            "tax_year": tax_year,
            "gross_income": income,
            "total_deductions": total_deductions,
            "taxable_income": taxable_income,
            "tax_amount": round(tax, 2),
            "effective_rate": round(tax / income * 100, 2) if income > 0 else 0,
        }

    def prepare_tax_return(self, user_id: str, country: str = "NP",
                           income: float = 0, deductions: List[Dict] = None,
                           tax_year: int = 2024,
                           filing_status: str = "single") -> Dict[str, Any]:
        calculation = self.calculate_tax(user_id, country, income, deductions, tax_year)
        return {
            **calculation,
            "filing_status": filing_status,
            "return_id": f"tr_{user_id}_{tax_year}",
            "status": "prepared",
            "prepared_at": datetime.utcnow().isoformat(),
        }

    def get_services(self, country: str) -> List[Dict[str, str]]:
        return self._services.get(country.upper(), self._services["default"])

    def get_signature_regions(self) -> List[Dict[str, str]]:
        return list(self._signature_regions)


# ─── Singleton ─────────────────────────────────────────────────────────────────

_government_manager_instance: Optional[GovernmentManager] = None


def get_government_manager() -> GovernmentManager:
    """Get or create the GovernmentManager singleton."""
    global _government_manager_instance
    if _government_manager_instance is None:
        _government_manager_instance = GovernmentManager()
    return _government_manager_instance


def reset_government_manager() -> None:
    """Reset the GovernmentManager singleton (for testing)."""
    global _government_manager_instance
    _government_manager_instance = None


# ─── Async helpers for analytics ──────────────────────────────────────────────


async def get_government_status() -> Dict[str, Any]:
    """Get government system status (async, for analytics)."""
    gm = get_government_manager()
    return {
        "status": gm.get_status().value,
        "identity_countries": gm.get_identity_countries_count(),
        "total_identities": gm.get_active_identities_count(),
        "eresidency_programs": gm.get_eresidency_programs_count(),
        "tax_countries": gm.get_tax_countries_count(),
    }


async def get_identity_stats() -> Dict[str, Any]:
    """Get identity statistics (async, for analytics)."""
    gm = get_government_manager()
    return {
        "total_identities": gm.get_active_identities_count(),
        "countries": gm.get_identity_countries_count(),
    }


async def get_tax_info() -> Dict[str, Any]:
    """Get tax information (async, for analytics)."""
    gm = get_government_manager()
    return {
        "tax_countries": gm.get_tax_countries_count(),
        "signature_regions": gm.get_signature_regions_count(),
    }


__all__ = [
    "GovernmentManager",
    "GovernmentStatus",
    "get_government_manager",
    "reset_government_manager",
    "get_government_status",
    "get_identity_stats",
    "get_tax_info",
]
