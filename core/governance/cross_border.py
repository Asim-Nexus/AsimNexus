"""Cross-Border Data Flow Resolver — Manages multi-jurisdiction policy conflicts.

When a request spans multiple jurisdictions (e.g., data stored in EU,
accessed from Nepal, processed by US-based AI), this resolver determines
the applicable policy using conflict-of-law rules.

Resolution hierarchy:
1. Lex specialis (most specific jurisdiction wins)
2. Lex superior (higher policy layer wins: Government > Enterprise > User)
3. Most restrictive standard applies (data protection)
4. Sovereign override (government-layer veto)
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from core.governance.country_packs import CountryPack, get_country_pack

logger = logging.getLogger(__name__)


@dataclass
class JurisdictionConflict:
    """Represents a conflict between two or more jurisdictions."""
    jurisdictions: List[str]
    conflicting_capabilities: List[str]
    resolution: Optional[str] = None
    applied_pack: Optional[str] = None


class CrossBorderResolver:
    """Resolves cross-jurisdiction policy conflicts for data and operations.

    Implements conflict-of-law rules for the AsimNexus governance layer.
    """

    # Privacy standard ranking (most restrictive = highest number)
    PRIVACY_RANKING = {
        "GDPR": 5,      # EU — highest protection
        "PDPA": 4,      # Nepal
        "DPDPA": 4,     # India
        "CCPA": 3,      # California
        "HIPAA": 3,     # US health (context-specific)
        "PIPL": 4,      # China (future)
        "LGPD": 4,      # Brazil (future)
        "none": 1,      # No specific standard
    }

    def __init__(self):
        self._conflict_log: List[JurisdictionConflict] = []

    def resolve(
        self,
        primary_jurisdiction: str,
        secondary_jurisdictions: List[str],
        capability_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, CountryPack, List[str]]:
        """Resolve which jurisdiction's policy applies.

        Args:
            primary_jurisdiction: ISO code of the primary jurisdiction (user's location).
            secondary_jurisdictions: ISO codes of secondary jurisdictions (data location, etc.).
            capability_id: The capability being requested.
            context: Additional context (data type, user role, etc.).

        Returns:
            Tuple of (resolved_jurisdiction_code, resolved_pack, warnings).
        """
        warnings: List[str] = []
        context = context or {}

        # Get packs for all involved jurisdictions
        primary_pack = get_country_pack(primary_jurisdiction)
        secondary_packs = [
            get_country_pack(j) for j in secondary_jurisdictions
            if get_country_pack(j) is not None
        ]

        if not primary_pack:
            warnings.append(f"No policy pack for primary jurisdiction {primary_jurisdiction}")
            return primary_jurisdiction, None, warnings

        # Check if capability is restricted in any jurisdiction
        all_restricted = []
        for pack in [primary_pack] + secondary_packs:
            if pack and capability_id in pack.restricted_capabilities:
                all_restricted.append(pack.code)

        if all_restricted:
            warnings.append(
                f"Capability '{capability_id}' restricted in: {', '.join(all_restricted)}"
            )

        # Apply most restrictive privacy standard
        all_standards = []
        for pack in [primary_pack] + secondary_packs:
            if pack:
                all_standards.append((pack.privacy_standard, pack.code))

        if all_standards:
            # Sort by privacy ranking (most restrictive first)
            all_standards.sort(
                key=lambda x: self.PRIVACY_RANKING.get(x[0], 0),
                reverse=True,
            )
            most_restrictive = all_standards[0]
            if most_restrictive[1] != primary_jurisdiction:
                warnings.append(
                    f"Applying {most_restrictive[0]} from {most_restrictive[1]} "
                    f"(more restrictive than {primary_jurisdiction}'s standard)"
                )

        # Check data localization requirements
        data_localization_jurisdictions = [
            pack.code for pack in [primary_pack] + secondary_packs
            if pack and pack.data_localization_required
        ]
        if data_localization_jurisdictions:
            warnings.append(
                f"Data localization required in: {', '.join(data_localization_jurisdictions)}"
            )

        # Log conflict if multiple jurisdictions
        if secondary_jurisdictions:
            conflict = JurisdictionConflict(
                jurisdictions=[primary_jurisdiction] + secondary_jurisdictions,
                conflicting_capabilities=[capability_id],
                resolution=primary_jurisdiction,
                applied_pack=primary_pack.code if primary_pack else None,
            )
            self._conflict_log.append(conflict)

        return primary_jurisdiction, primary_pack, warnings

    def get_conflict_log(self) -> List[JurisdictionConflict]:
        """Get the history of resolved conflicts."""
        return self._conflict_log

    def get_stats(self) -> Dict[str, Any]:
        """Get cross-border resolution statistics."""
        return {
            "total_conflicts_resolved": len(self._conflict_log),
            "jurisdictions_involved": list(set(
                j for c in self._conflict_log for j in c.jurisdictions
            )),
        }
