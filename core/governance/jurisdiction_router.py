"""Jurisdiction Router — Routes requests to the appropriate governance layer.

Determines which jurisdiction's policies apply based on:
1. User's declared location / IP geolocation
2. Data residency requirements
3. Service provider jurisdiction
4. Contractual choice of law

Routes to:
- GovernmentLayer for sovereign/government actions
- EnterpriseLayer for commercial/corporate actions
- CountryPack for jurisdiction-specific rules
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.governance.country_packs import CountryPack, get_country_pack
from core.governance.cross_border import CrossBorderResolver

logger = logging.getLogger(__name__)


class RoutingDomain(Enum):
    """The governance domain a request belongs to."""
    GOVERNMENT = "government"       # Sovereign/government actions
    ENTERPRISE = "enterprise"       # Commercial/corporate actions
    PERSONAL = "personal"           # Individual user actions
    CROSS_BORDER = "cross_border"   # Multi-jurisdiction actions


@dataclass
class RoutingDecision:
    """The result of jurisdiction routing."""
    domain: RoutingDomain
    primary_jurisdiction: str
    applied_pack: Optional[CountryPack]
    requires_sovereign_approval: bool
    requires_enterprise_approval: bool
    warnings: List[str] = field(default_factory=list)


class JurisdictionRouter:
    """Routes requests to the appropriate governance layer based on jurisdiction.

    Integrates with the Gateway's VersionedPolicyEngine to apply
    the correct policy pack for each request.
    """

    # Default jurisdiction if detection fails
    DEFAULT_JURISDICTION = "us"

    def __init__(self):
        self._cross_border = CrossBorderResolver()

    def route(
        self,
        capability_id: str,
        user_jurisdiction: Optional[str] = None,
        data_jurisdictions: Optional[List[str]] = None,
        user_role: str = "user",
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """Route a capability request to the appropriate governance domain.

        Args:
            capability_id: The capability being requested.
            user_jurisdiction: ISO code of the user's jurisdiction.
            data_jurisdictions: ISO codes where relevant data resides.
            user_role: Role of the user (admin, government, enterprise, user).
            context: Additional routing context.

        Returns:
            RoutingDecision with the resolved domain and jurisdiction.
        """
        context = context or {}
        user_jurisdiction = user_jurisdiction or self.DEFAULT_JURISDICTION
        data_jurisdictions = data_jurisdictions or []
        warnings: List[str] = []

        # Determine routing domain based on capability and role
        domain = self._determine_domain(capability_id, user_role)

        # Resolve jurisdiction
        resolved_jurisdiction, resolved_pack, cross_warnings = (
            self._cross_border.resolve(
                primary_jurisdiction=user_jurisdiction,
                secondary_jurisdictions=data_jurisdictions,
                capability_id=capability_id,
                context=context,
            )
        )
        warnings.extend(cross_warnings)

        # Check if sovereign approval is needed
        requires_sovereign = False
        if resolved_pack and capability_id in resolved_pack.requires_sovereign_approval:
            requires_sovereign = True
            warnings.append(
                f"Capability '{capability_id}' requires sovereign approval "
                f"in {resolved_jurisdiction}"
            )

        # Check if enterprise approval is needed
        requires_enterprise = (
            domain == RoutingDomain.ENTERPRISE
            and capability_id in ("gov:policy_write", "config:write", "auth:manage")
        )

        return RoutingDecision(
            domain=domain,
            primary_jurisdiction=resolved_jurisdiction,
            applied_pack=resolved_pack,
            requires_sovereign_approval=requires_sovereign,
            requires_enterprise_approval=requires_enterprise,
            warnings=warnings,
        )

    def _determine_domain(self, capability_id: str, user_role: str) -> RoutingDomain:
        """Determine which governance domain a capability belongs to."""
        # Government capabilities
        if capability_id.startswith("gov:"):
            return RoutingDomain.GOVERNMENT

        # Enterprise capabilities
        if user_role == "enterprise" or capability_id in (
            "config:write", "auth:manage", "agent:deploy"
        ):
            return RoutingDomain.ENTERPRISE

        # Cross-border data operations
        if capability_id.startswith("datalake:") or capability_id.startswith("mesh:"):
            return RoutingDomain.CROSS_BORDER

        # Default to personal
        return RoutingDomain.PERSONAL

    def get_applicable_pack(
        self, jurisdiction: str
    ) -> Optional[CountryPack]:
        """Get the policy pack for a given jurisdiction."""
        return get_country_pack(jurisdiction)

    def list_available_jurisdictions(self) -> List[Dict[str, str]]:
        """List all jurisdictions with available policy packs."""
        from core.governance.country_packs import list_available_packs
        return list_available_packs()
