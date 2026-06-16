"""
STATUS: REAL — Tripartite router for Government/Company/Citizen modes

AsimNexus Tripartite Router
=============================
Routes requests across three operational modes:
- Government Mode (51% sovereignty)
- Enterprise Mode (49% agility)  
- Citizen Mode (Local-First)

Implements 51/49 governance model with Dharma Veto integration.
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger("AsimNexus.TripartiteRouter")

class OperationMode(Enum):
    """Three operational modes"""
    GOVERNMENT = "government"      # 51% - Sovereign functions
    ENTERPRISE = "enterprise"      # 49% - Commercial functions
    CITIZEN = "citizen"          # Local-First - Personal functions

@dataclass
class RoutingDecision:
    """Result of tripartite routing"""
    mode: OperationMode
    route: str
    confidence: float
    reason: str

class TripartiteRouter:
    """
    Routes requests across Government/Enterprise/Citizen modes
    
    Implements the 51/49 governance model:
    - Government: 51% - public welfare, sovereignty, regulation
    - Enterprise: 49% - commerce, innovation, private services
    - Citizen: Local-First - personal agency, privacy, autonomy
    """

    # Sector to mode mapping
    SECTOR_MODE_MAP = {
        "infrastructure": OperationMode.GOVERNMENT,
        "governance": OperationMode.GOVERNMENT,
        "healthcare": OperationMode.GOVERNMENT,
        "education": OperationMode.GOVERNMENT,
        "commercial": OperationMode.ENTERPRISE,
        "finance": OperationMode.ENTERPRISE,
        "technology": OperationMode.ENTERPRISE,
        "communication": OperationMode.GOVERNMENT,
        "tax": OperationMode.GOVERNMENT,
        "personal": OperationMode.CITIZEN,
        "family": OperationMode.CITIZEN,
        "health": OperationMode.CITIZEN,
    }

    # Route templates
    ROUTE_TEMPLATES = {
        OperationMode.GOVERNMENT: "/api/v1/gov/{sector}/{action}",
        OperationMode.ENTERPRISE: "/api/v1/company/{sector}/{action}",
        OperationMode.CITIZEN: "/api/v1/user/{sector}/{action}",
    }

    def __init__(self):
        self._dharma_check_enabled = True
        logger.info("🔀 TripartiteRouter initialized with 51/49 model")

    async def route_request(
        self, 
        request_type: str,
        sector: str,
        user_context: Optional[Dict] = None,
        priority_concerns: Optional[List[str]] = None
    ) -> RoutingDecision:
        """
        Determine appropriate mode and route for request
        
        Args:
            request_type: Type of request (tax_calculation, etc.)
            sector: Sector identifier (tax, health, commerce, etc.)
            user_context: Optional user context (citizenship, company_role, etc.)
            priority_concerns: Priority flags (sovereignty, innovation, etc.)
        
        Returns:
            RoutingDecision with mode and route
        """
        # Step 1: Determine mode based on sector
        mode = self.SECTOR_MODE_MAP.get(sector, OperationMode.CITIZEN)

        # Step 2: Check priority concerns for overrides
        if priority_concerns:
            if "sovereignty" in priority_concerns:
                mode = OperationMode.GOVERNMENT
            elif "innovation" in priority_concerns and mode == OperationMode.GOVERNMENT:
                mode = OperationMode.ENTERPRISE

        # Step 3: Apply Dharma Veto check
        if self._dharma_check_enabled:
            veto_result = await self._apply_dharma_check(request_type, sector, user_context)
            if veto_result.get("blocked"):
                mode = OperationMode.GOVERNMENT  # Always government for veto
                logger.warning(f"Dharma Veto applied to: {request_type}")

        # Step 4: Generate route
        route = self._generate_route(mode, sector, request_type)

        return RoutingDecision(
            mode=mode,
            route=route,
            confidence=0.95,
            reason=f"Sector '{sector}' mapped to {mode.value} mode"
        )

    async def _apply_dharma_check(
        self, 
        request_type: str, 
        sector: str, 
        user_context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Apply Dharma Veto layer check"""
        try:
            from core.dharma.safety_veto import SafetyVeto
            veto = SafetyVeto()
            
            check_input = f"{request_type} in {sector}"
            result = veto.check(check_input)
            
            return result
        except Exception as e:
            logger.debug(f"Dharma check skipped: {e}")
            return {"allowed": True}

    def _generate_route(self, mode: OperationMode, sector: str, action: str) -> str:
        """Generate API route based on mode and sector"""
        template = self.ROUTE_TEMPLATES[mode]
        return template.format(sector=sector, action=action)

    def get_mode_handlers(self) -> Dict[str, Any]:
        """Get handler classes for each mode"""
        return {
            "government": self._get_government_handlers(),
            "enterprise": self._get_enterprise_handlers(),
            "citizen": self._get_citizen_handlers()
        }

    def _get_government_handlers(self) -> Dict[str, str]:
        """Government mode handlers"""
        return {
            "tax": "core.nepal.tax_llm",
            "identity": "core.nepal.government_integrations",
            "health": "core.nepal.health_registry",
            "education": "core.nepal.paper_digitalizer",
            "infrastructure": "core.nepal.banking_integrations"
        }

    def _get_enterprise_handlers(self) -> Dict[str, str]:
        """Enterprise mode handlers"""
        return {
            "commerce": "core.economy.job_marketplace",
            "finance": "core.economy.wallet",
            "hr": "core.founder_clones.founder_clone_system",
            "supply_chain": "core.world.economy.rbe_algorithm"
        }

    def _get_citizen_handlers(self) -> Dict[str, str]:
        """Citizen mode handlers"""
        return {
            "personal": "core.identity.personal_os",
            "health": "core.identity.digital_twin",
            "family": "core.nepal.cultural_features",
            "finance": "core.banking_integrations",
            "work": "core.economy.job_marketplace"
        }

    def status(self) -> Dict[str, Any]:
        """Get router status"""
        return {
            "modes": [m.value for m in OperationMode],
            "sectors_mapped": len(self.SECTOR_MODE_MAP),
            "route_templates": len(self.ROUTE_TEMPLATES),
            "dharma_check": self._dharma_check_enabled
        }

# Singleton
_router: Optional[TripartiteRouter] = None

def get_tripartite_router() -> TripartiteRouter:
    """Get or create Tripartite Router singleton"""
    global _router
    if _router is None:
        _router = TripartiteRouter()
    return _router