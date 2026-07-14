"""Nepal Policy Pack — Governs operations within Nepali jurisdiction.

Based on:
- Constitution of Nepal 2015
- IT Act 2063 (2008)
- Data localization requirements per Nepal's IT Bill
- Nepal Rastra Bank directives on data sovereignty
"""

import asyncio
from typing import Dict, Any, Optional
from core.governance.country_packs import CountryPack


class NepalGovernmentIntegration:
    """REAL Nepal Government Integration — Tax LLM + SMS Gateway"""
    
    def __init__(self):
        self._tax_llm = None
        self._sms_gateway = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Nepal-specific services"""
        try:
            from core.nepal.tax_llm import get_tax_llm
            from core.mesh.sms_gateway import get_sms_gateway
            self._tax_llm = get_tax_llm()  # sync factory
            self._sms_gateway = get_sms_gateway()
            self._initialized = True
        except Exception as e:
            print(f"Nepal integration init warning: {e}")
            self._initialized = False
    
    async def verify_tax_compliance(self, citizen_id: str, year: int) -> Dict[str, Any]:
        """Verify tax compliance for Nepali citizen"""
        if not self._tax_llm:
            return {"status": "error", "message": "Tax LLM not initialized"}
        
        return await self._tax_llm.calculate_tax_due(citizen_id, year)
    
    async def send_gov_sms(self, phone: str, message: str) -> bool:
        """Send government SMS via NTC/Ncell gateway"""
        if self._sms_gateway:
            return await self._sms_gateway.send_sms(phone, message, priority="high")
        return False
    
    def status(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "tax_llm": self._tax_llm is not None,
            "sms_gateway": self._sms_gateway is not None
        }


# Singleton
_nepal_gov: Optional[NepalGovernmentIntegration] = None


async def get_nepal_government() -> NepalGovernmentIntegration:
    """Get Nepal Government Integration singleton"""
    global _nepal_gov
    if _nepal_gov is None:
        _nepal_gov = NepalGovernmentIntegration()
        await _nepal_gov.initialize()
    return _nepal_gov


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
