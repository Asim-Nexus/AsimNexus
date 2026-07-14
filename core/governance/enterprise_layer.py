"""Enterprise Layer — Commercial governance for the 49% private sector.

Manages:
- Enterprise licensing and compliance
- Commercial use policies
- Proprietary extension governance
- Corporate data handling rules
- Audit trails for enterprise actions

This is the 49% private side of the 51/49 governance model.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class EnterpriseTier(Enum):
    """Enterprise subscription/licensing tier."""
    FREE = "free"
    STARTER = "starter"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"


class ComplianceStatus(Enum):
    """Compliance check result."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    EXEMPT = "exempt"


@dataclass
class EnterpriseLicense:
    """An enterprise license record."""
    license_id: str
    organization: str
    tier: EnterpriseTier
    jurisdiction: str
    max_users: int
    max_agents: int
    features: List[str]
    expires_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    active: bool = True


@dataclass
class ComplianceRecord:
    """A compliance check record."""
    record_id: str
    organization: str
    action: str
    status: ComplianceStatus
    details: str
    checked_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class EnterpriseLayer:
    """Governance layer for enterprise/commercial operations.

    Enforces licensing, compliance, and commercial use policies
    for the 49% private sector of the AsimNexus governance model.
    """

    def __init__(self):
        self._licenses: Dict[str, EnterpriseLicense] = {}
        self._compliance_log: List[ComplianceRecord] = []

    def register_license(
        self,
        organization: str,
        tier: EnterpriseTier,
        jurisdiction: str,
        max_users: int = 10,
        max_agents: int = 5,
        features: Optional[List[str]] = None,
    ) -> EnterpriseLicense:
        """Register a new enterprise license."""
        license_id = str(uuid.uuid4())
        license = EnterpriseLicense(
            license_id=license_id,
            organization=organization,
            tier=tier,
            jurisdiction=jurisdiction,
            max_users=max_users,
            max_agents=max_agents,
            features=features or ["basic"],
        )
        self._licenses[license_id] = license
        logger.info(f"Registered {tier.value} license for {organization}: {license_id}")
        return license

    def check_compliance(
        self,
        organization: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ComplianceRecord:
        """Check if an action is compliant with enterprise policies.

        Args:
            organization: The organization performing the action.
            action: The action being checked.
            context: Additional context (user count, agent count, features used).

        Returns:
            ComplianceRecord with the check result.
        """
        context = context or {}
        record_id = str(uuid.uuid4())

        # Find active license for organization
        license = self._find_license(organization)

        if not license:
            record = ComplianceRecord(
                record_id=record_id,
                organization=organization,
                action=action,
                status=ComplianceStatus.NON_COMPLIANT,
                details="No active license found for organization",
            )
            self._compliance_log.append(record)
            return record

        if not license.active:
            record = ComplianceRecord(
                record_id=record_id,
                organization=organization,
                action=action,
                status=ComplianceStatus.NON_COMPLIANT,
                details="License is deactivated",
            )
            self._compliance_log.append(record)
            return record

        # Check user count limits
        current_users = context.get("current_users", 0)
        if current_users > license.max_users:
            record = ComplianceRecord(
                record_id=record_id,
                organization=organization,
                action=action,
                status=ComplianceStatus.NON_COMPLIANT,
                details=f"User count {current_users} exceeds license limit {license.max_users}",
            )
            self._compliance_log.append(record)
            return record

        # Check agent count limits
        current_agents = context.get("current_agents", 0)
        if current_agents > license.max_agents:
            record = ComplianceRecord(
                record_id=record_id,
                organization=organization,
                action=action,
                status=ComplianceStatus.NON_COMPLIANT,
                details=f"Agent count {current_agents} exceeds license limit {license.max_agents}",
            )
            self._compliance_log.append(record)
            return record

        # Check feature access
        required_feature = context.get("required_feature")
        if required_feature and required_feature not in license.features:
            record = ComplianceRecord(
                record_id=record_id,
                organization=organization,
                action=action,
                status=ComplianceStatus.NON_COMPLIANT,
                details=f"Feature '{required_feature}' not in license ({license.tier.value})",
            )
            self._compliance_log.append(record)
            return record

        record = ComplianceRecord(
            record_id=record_id,
            organization=organization,
            action=action,
            status=ComplianceStatus.COMPLIANT,
            details=f"Compliant under {license.tier.value} license",
        )
        self._compliance_log.append(record)
        return record

    def _find_license(self, organization: str) -> Optional[EnterpriseLicense]:
        """Find an active license for an organization."""
        for license in self._licenses.values():
            if license.organization == organization and license.active:
                return license
        return None

    def get_license(self, license_id: str) -> Optional[EnterpriseLicense]:
        """Get a license by ID."""
        return self._licenses.get(license_id)

    def deactivate_license(self, license_id: str) -> bool:
        """Deactivate a license."""
        license = self._licenses.get(license_id)
        if license:
            license.active = False
            return True
        return False

    def get_compliance_log(
        self, organization: Optional[str] = None, limit: int = 100
    ) -> List[ComplianceRecord]:
        """Get compliance check history."""
        if organization:
            return [
                r for r in self._compliance_log
                if r.organization == organization
            ][:limit]
        return self._compliance_log[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get enterprise layer statistics."""
        active_licenses = sum(1 for l in self._licenses.values() if l.active)
        compliance_breakdown = {}
        for record in self._compliance_log:
            status = record.status.value
            compliance_breakdown[status] = compliance_breakdown.get(status, 0) + 1

        return {
            "total_licenses": len(self._licenses),
            "active_licenses": active_licenses,
            "total_compliance_checks": len(self._compliance_log),
            "compliance_breakdown": compliance_breakdown,
            "organizations": list(set(
                l.organization for l in self._licenses.values()
            )),
        }
