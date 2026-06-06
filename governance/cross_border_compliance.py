"""
Cross-Border Compliance Engine — AsimNexus Regional & Data Sovereignty Controls.

Extends the base ComplianceEngine with:
  - Regional compliance rules (GDPR EU, Nepal IT Bill 2081, etc.)
  - Data sovereignty enforcement (data stays within jurisdiction)
  - Cross-border data flow controls with consent tracking
  - Jurisdiction-aware policy evaluation

Integration:
  - Uses :class:`governance.compliance_engine.ComplianceEngine` as base
  - Persists via :class:`storage.oltp_engine.OltpEngine`
  - Audits via :class:`governance.governance_audit.GovernanceAudit`

Usage:
    from governance.cross_border_compliance import CrossBorderComplianceEngine

    cbc = CrossBorderComplianceEngine()
    await cbc.start()

    result = await cbc.check_cross_border_data_flow(
        data_classification="RESTRICTED",
        origin_jurisdiction="NP",
        destination_jurisdiction="US",
    )
"""

from __future__ import annotations

import asyncio
import enum
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment defaults
# ---------------------------------------------------------------------------

_CROSS_BORDER_DB = os.environ.get(
    "ASIM_COMPLIANCE_CROSS_BORDER_DB",
    os.path.join(os.path.expanduser("~"), ".asimnexus", "cross_border_compliance.jsonl"),
)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Jurisdiction(str, enum.Enum):
    """Recognised legal jurisdictions."""
    GLOBAL = "GL"
    NEPAL = "NP"
    INDIA = "IN"
    EU = "EU"
    US = "US"
    UK = "UK"
    CHINA = "CN"
    SINGAPORE = "SG"
    UAE = "AE"
    JAPAN = "JP"
    AUSTRALIA = "AU"
    BRAZIL = "BR"
    CANADA = "CA"

class DataSovereigntyPolicy(str, enum.Enum):
    """Data sovereignty enforcement levels."""
    STRICT_SOVEREIGNTY = "strict_sovereignty"   # Data MUST stay in jurisdiction
    CONDITIONAL = "conditional"                  # Allowed with explicit consent / safeguards
    OPEN = "open"                                 # No restrictions

class CrossBorderStatus(str, enum.Enum):
    """Outcome of a cross-border data flow check."""
    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_CONSENT = "requires_consent"
    REQUIRES_REVIEW = "requires_review"
    PENDING = "pending"

class RegionalComplianceFramework(str, enum.Enum):
    """Supported regional compliance frameworks."""
    GDPR = "gdpr"                                 # EU General Data Protection Regulation
    NEPAL_IT_BILL = "nepal_it_bill"              # Nepal IT Bill 2081
    INDIA_DPDP = "india_dpdp"                    # India Digital Personal Data Protection
    US_PRIVACY = "us_privacy"                    # US state-level privacy (CCPA, etc.)
    UK_GDPR = "uk_gdpr"                          # UK GDPR variant
    CHINA_PIPL = "china_pipl"                    # China Personal Information Protection Law
    SINGAPORE_PDPA = "singapore_pdpa"            # Singapore Personal Data Protection Act
    BRAZIL_LGPD = "brazil_lgpd"                  # Brazil Lei Geral de Proteção de Dados
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RegionalRule:
    """A compliance rule specific to a jurisdiction and framework."""
    rule_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    jurisdiction: Jurisdiction = Jurisdiction.GLOBAL
    framework: RegionalComplianceFramework = RegionalComplianceFramework.CUSTOM
    data_classification: str = "CONFIDENTIAL"  # PUBLIC / INTERNAL / CONFIDENTIAL / RESTRICTED / SECRET
    sovereignty_policy: DataSovereigntyPolicy = DataSovereigntyPolicy.OPEN
    requires_consent: bool = False
    requires_audit: bool = True
    max_allowed_classification: str = "CONFIDENTIAL"  # highest classification allowed
    description: str = ""
    rules: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RegionalRule":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class CrossBorderFlow:
    """Record of a cross-border data flow request and its resolution."""
    flow_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    data_classification: str = ""
    origin_jurisdiction: str = ""
    destination_jurisdiction: str = ""
    purpose: str = ""
    status: CrossBorderStatus = CrossBorderStatus.PENDING
    checked_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    consent_given: bool = False
    consent_by: str = ""
    reviewed_by: str = ""
    notes: str = ""
    policy_overrides: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CrossBorderFlow":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Default regional rules
# ---------------------------------------------------------------------------

def _default_regional_rules() -> List[RegionalRule]:
    """Return the built-in set of regional compliance rules."""
    return [
        # Nepal IT Bill 2081 — strict sovereignty
        RegionalRule(
            jurisdiction=Jurisdiction.NEPAL,
            framework=RegionalComplianceFramework.NEPAL_IT_BILL,
            data_classification="RESTRICTED",
            sovereignty_policy=DataSovereigntyPolicy.STRICT_SOVEREIGNTY,
            requires_consent=True,
            requires_audit=True,
            max_allowed_classification="CONFIDENTIAL",
            description="Nepal IT Bill 2081: restricted data must remain in Nepal",
            rules={
                "data_localization": True,
                "government_override": True,
                "cross_border_prohibited": True,
            },
        ),
        RegionalRule(
            jurisdiction=Jurisdiction.NEPAL,
            framework=RegionalComplianceFramework.NEPAL_IT_BILL,
            data_classification="CONFIDENTIAL",
            sovereignty_policy=DataSovereigntyPolicy.CONDITIONAL,
            requires_consent=True,
            requires_audit=True,
            max_allowed_classification="CONFIDENTIAL",
            description="Nepal IT Bill 2081: confidential data requires consent for cross-border",
            rules={
                "data_localization": True,
                "government_override": True,
                "cross_border_prohibited": False,
            },
        ),
        # GDPR — EU
        RegionalRule(
            jurisdiction=Jurisdiction.EU,
            framework=RegionalComplianceFramework.GDPR,
            data_classification="RESTRICTED",
            sovereignty_policy=DataSovereigntyPolicy.CONDITIONAL,
            requires_consent=True,
            requires_audit=True,
            max_allowed_classification="CONFIDENTIAL",
            description="GDPR: restricted data requires explicit consent & SCC for cross-border",
            rules={
                "adequate_jurisdictions": ["EU", "UK", "CH"],
                "requires_scc": True,
                "consent_required": True,
                "dpo_notification_required": True,
            },
        ),
        RegionalRule(
            jurisdiction=Jurisdiction.EU,
            framework=RegionalComplianceFramework.GDPR,
            data_classification="CONFIDENTIAL",
            sovereignty_policy=DataSovereigntyPolicy.CONDITIONAL,
            requires_consent=True,
            requires_audit=True,
            max_allowed_classification="CONFIDENTIAL",
            description="GDPR: confidential data requires consent for cross-border transfer",
            rules={
                "adequate_jurisdictions": ["EU", "UK", "CH", "JP", "CA"],
                "requires_scc": False,
                "consent_required": True,
            },
        ),
        # India DPDP
        RegionalRule(
            jurisdiction=Jurisdiction.INDIA,
            framework=RegionalComplianceFramework.INDIA_DPDP,
            data_classification="RESTRICTED",
            sovereignty_policy=DataSovereigntyPolicy.CONDITIONAL,
            requires_consent=True,
            requires_audit=True,
            max_allowed_classification="CONFIDENTIAL",
            description="India DPDP: restricted data requires consent for cross-border",
            rules={
                "data_localization": True,
                "consent_required": True,
                "government_override": True,
            },
        ),
        # US Privacy
        RegionalRule(
            jurisdiction=Jurisdiction.US,
            framework=RegionalComplianceFramework.US_PRIVACY,
            data_classification="CONFIDENTIAL",
            sovereignty_policy=DataSovereigntyPolicy.OPEN,
            requires_consent=False,
            requires_audit=True,
            max_allowed_classification="SECRET",
            description="US privacy: open cross-border with audit",
            rules={
                "ccpa_compliant": True,
                "state_specific": True,
            },
        ),
        # Singapore PDPA
        RegionalRule(
            jurisdiction=Jurisdiction.SINGAPORE,
            framework=RegionalComplianceFramework.SINGAPORE_PDPA,
            data_classification="CONFIDENTIAL",
            sovereignty_policy=DataSovereigntyPolicy.OPEN,
            requires_consent=False,
            requires_audit=True,
            max_allowed_classification="CONFIDENTIAL",
            description="Singapore PDPA: open cross-border with audit obligations",
            rules={
                "consent_required": False,
                "notification_required": True,
            },
        ),
        # China PIPL
        RegionalRule(
            jurisdiction=Jurisdiction.CHINA,
            framework=RegionalComplianceFramework.CHINA_PIPL,
            data_classification="CONFIDENTIAL",
            sovereignty_policy=DataSovereigntyPolicy.STRICT_SOVEREIGNTY,
            requires_consent=True,
            requires_audit=True,
            max_allowed_classification="INTERNAL",
            description="China PIPL: strict data localization for most data",
            rules={
                "data_localization": True,
                "security_assessment_required": True,
                "government_approval_required": True,
            },
        ),
        # Global default
        RegionalRule(
            jurisdiction=Jurisdiction.GLOBAL,
            framework=RegionalComplianceFramework.CUSTOM,
            data_classification="CONFIDENTIAL",
            sovereignty_policy=DataSovereigntyPolicy.CONDITIONAL,
            requires_consent=True,
            requires_audit=True,
            max_allowed_classification="CONFIDENTIAL",
            description="Global default: consent required for cross-border confidential data",
            rules={"default": True},
        ),
    ]


# ---------------------------------------------------------------------------
# Classification hierarchy for comparisons
# ---------------------------------------------------------------------------

_CLASSIFICATION_ORDER: Dict[str, int] = {
    "PUBLIC": 0,
    "INTERNAL": 1,
    "CONFIDENTIAL": 2,
    "RESTRICTED": 3,
    "SECRET": 4,
}


def _classification_level(name: str) -> int:
    return _CLASSIFICATION_ORDER.get(name.upper(), 0)


# ---------------------------------------------------------------------------
# CrossBorderComplianceEngine
# ---------------------------------------------------------------------------

class CrossBorderComplianceEngine:
    """
    Cross-border compliance engine with regional rules, data sovereignty,
    and data flow controls.

    Complements the base :class:`governance.compliance_engine.ComplianceEngine`
    by adding jurisdiction-aware policy evaluation.

    Usage::

        cbc = CrossBorderComplianceEngine()
        await cbc.start()

        # Check a cross-border data flow
        result = await cbc.check_cross_border_data_flow(
            data_classification="CONFIDENTIAL",
            origin_jurisdiction="NP",
            destination_jurisdiction="EU",
            purpose="Clinical trial data sharing",
        )

        # Register a custom regional rule
        cbc.register_regional_rule(my_rule)

        # Get a compliance report
        report = await cbc.get_compliance_report()
    """

    def __init__(
        self,
        db_path: str = _CROSS_BORDER_DB,
        base_compliance: Optional[Any] = None,
        audit_engine: Optional[Any] = None,
        oltp_engine: Optional[Any] = None,
    ) -> None:
        self._db_path = db_path
        self._base_compliance = base_compliance
        self._audit = audit_engine
        self._oltp = oltp_engine

        self._lock = asyncio.Lock()
        self._regional_rules: Dict[str, RegionalRule] = {}  # rule_id -> rule
        self._flow_log: List[CrossBorderFlow] = []

        # Ensure DB directory exists
        db_dir = os.path.dirname(self._db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Initialise with default rules
        self._init_default_rules()

    def _init_default_rules(self) -> None:
        """Load the built-in regional rules."""
        for rule in _default_regional_rules():
            self._regional_rules[rule.rule_id] = rule
        logger.info("CrossBorderComplianceEngine: loaded %d default regional rules",
                     len(self._regional_rules))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the engine — load persisted data."""
        self._load_flow_log()
        logger.info("CrossBorderComplianceEngine started (%d regional rules, %d historical flows)",
                     len(self._regional_rules), len(self._flow_log))

    async def stop(self) -> None:
        """Stop and persist state."""
        self._save_flow_log()
        logger.info("CrossBorderComplianceEngine stopped")

    # ------------------------------------------------------------------
    # Regional rules management
    # ------------------------------------------------------------------

    def register_regional_rule(self, rule: RegionalRule) -> bool:
        """Register a custom regional compliance rule."""
        self._regional_rules[rule.rule_id] = rule
        logger.info("Registered regional rule %s: %s for %s",
                     rule.rule_id, rule.framework.value, rule.jurisdiction.value)
        return True

    def remove_regional_rule(self, rule_id: str) -> bool:
        """Remove a regional rule by ID."""
        if rule_id in self._regional_rules:
            del self._regional_rules[rule_id]
            logger.info("Removed regional rule %s", rule_id)
            return True
        return False

    def get_regional_rules(
        self,
        jurisdiction: Optional[Jurisdiction] = None,
        framework: Optional[RegionalComplianceFramework] = None,
    ) -> List[Dict[str, Any]]:
        """List regional rules, optionally filtered."""
        rules = list(self._regional_rules.values())
        if jurisdiction:
            rules = [r for r in rules if r.jurisdiction == jurisdiction]
        if framework:
            rules = [r for r in rules if r.framework == framework]
        return [r.to_dict() for r in rules]

    # ------------------------------------------------------------------
    # Cross-border data flow checks
    # ------------------------------------------------------------------

    async def check_cross_border_data_flow(
        self,
        data_classification: str,
        origin_jurisdiction: str,
        destination_jurisdiction: str,
        purpose: str = "",
        actor_did: str = "",
        require_consent: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluate whether a cross-border data flow is permitted.

        Returns a dict with:
          - allowed (bool)
          - status (CrossBorderStatus)
          - matched_rules (list)
          - requires_consent (bool)
          - flow_id (str)
          - reason (str)
        """
        classification = data_classification.upper()
        origin = origin_jurisdiction.upper()
        destination = destination_jurisdiction.upper()

        # Find matching rules for origin jurisdiction
        matching_rules = [
            r for r in self._regional_rules.values()
            if r.jurisdiction.value == origin and r.enabled
        ]
        # Also include global rules
        matching_rules += [
            r for r in self._regional_rules.values()
            if r.jurisdiction == Jurisdiction.GLOBAL and r.enabled
        ]

        if not matching_rules:
            result = {
                "allowed": True,
                "status": CrossBorderStatus.ALLOWED.value,
                "matched_rules": [],
                "requires_consent": False,
                "flow_id": "",
                "reason": "No matching regional rules — allowed by default",
            }
            await self._log_flow(data_classification, origin, destination,
                                  purpose, CrossBorderStatus.ALLOWED)
            return result

        # Evaluate each matching rule
        reasons: List[str] = []
        requires_consent = False
        denied = False

        for rule in matching_rules:
            # Check classification level
            if _classification_level(classification) > _classification_level(rule.max_allowed_classification):
                denied = True
                reasons.append(
                    f"Classification '{classification}' exceeds max allowed "
                    f"'{rule.max_allowed_classification}' per {rule.framework.value}"
                )
                continue

            # Check sovereignty policy
            if rule.sovereignty_policy == DataSovereigntyPolicy.STRICT_SOVEREIGNTY:
                denied = True
                reasons.append(
                    f"Data sovereignty policy '{rule.sovereignty_policy.value}' "
                    f"prohibits cross-border transfer from {origin}"
                )
                continue

            # Check consent requirement
            if rule.requires_consent:
                requires_consent = True
                reasons.append(
                    f"Consent required per {rule.framework.value} "
                    f"for classification '{classification}'"
                )

            # Check if destination is in adequate jurisdictions list
            adequate = rule.rules.get("adequate_jurisdictions", [])
            if adequate and destination not in adequate:
                if rule.requires_consent:
                    requires_consent = True
                    reasons.append(
                        f"Destination {destination} not in adequate list for "
                        f"{rule.framework.value} — consent required"
                    )
                else:
                    reasons.append(
                        f"Destination {destination} not in adequate list for "
                        f"{rule.framework.value}"
                    )

        if denied:
            status = CrossBorderStatus.DENIED
        elif requires_consent and require_consent:
            status = CrossBorderStatus.REQUIRES_CONSENT
        else:
            status = CrossBorderStatus.ALLOWED

        flow = await self._log_flow(
            data_classification, origin, destination,
            purpose, status, consent_given=False,
        )

        result = {
            "allowed": status == CrossBorderStatus.ALLOWED,
            "status": status.value,
            "matched_rules": [r.rule_id for r in matching_rules],
            "requires_consent": requires_consent,
            "flow_id": flow.flow_id,
            "reason": "; ".join(reasons) if reasons else "OK",
        }

        # Audit if audit engine available
        if self._audit is not None:
            await self._audit.record(
                action="cross_border_data_flow",
                actor=actor_did or "system",
                resource="compliance",
                details=result,
                severity="WARNING" if denied else "INFO",
                proposal_id=flow.flow_id,
            )

        return result

    async def provide_consent(
        self,
        flow_id: str,
        consented_by: str,
        notes: str = "",
    ) -> bool:
        """Provide explicit consent for a cross-border data flow."""
        async with self._lock:
            for flow in self._flow_log:
                if flow.flow_id == flow_id:
                    flow.status = CrossBorderStatus.ALLOWED
                    flow.consent_given = True
                    flow.consent_by = consented_by
                    flow.resolved_at = time.time()
                    flow.notes = notes
                    self._save_flow_log()
                    logger.info("Consent provided for cross-border flow %s by %s",
                                flow_id, consented_by)
                    return True
        return False

    async def deny_flow(self, flow_id: str, reviewed_by: str, notes: str = "") -> bool:
        """Manually deny a cross-border data flow."""
        async with self._lock:
            for flow in self._flow_log:
                if flow.flow_id == flow_id:
                    flow.status = CrossBorderStatus.DENIED
                    flow.reviewed_by = reviewed_by
                    flow.resolved_at = time.time()
                    flow.notes = notes
                    self._save_flow_log()
                    logger.info("Cross-border flow %s denied by %s", flow_id, reviewed_by)
                    return True
        return False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_flow(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific cross-border flow record."""
        async with self._lock:
            for flow in self._flow_log:
                if flow.flow_id == flow_id:
                    return flow.to_dict()
        return None

    async def list_flows(
        self,
        status: Optional[CrossBorderStatus] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List cross-border flows, optionally filtered."""
        async with self._lock:
            flows = list(self._flow_log)
        if status:
            flows = [f for f in flows if f.status == status]
        if origin:
            flows = [f for f in flows if f.origin_jurisdiction == origin.upper()]
        if destination:
            flows = [f for f in flows if f.destination_jurisdiction == destination.upper()]
        flows.sort(key=lambda f: f.checked_at, reverse=True)
        return [f.to_dict() for f in flows[:limit]]

    async def get_compliance_report(self) -> Dict[str, Any]:
        """Generate a cross-border compliance report."""
        async with self._lock:
            total_flows = len(self._flow_log)
            allowed = sum(1 for f in self._flow_log if f.status == CrossBorderStatus.ALLOWED)
            denied = sum(1 for f in self._flow_log if f.status == CrossBorderStatus.DENIED)
            pending_consent = sum(
                1 for f in self._flow_log if f.status == CrossBorderStatus.REQUIRES_CONSENT
            )
            pending_review = sum(
                1 for f in self._flow_log if f.status == CrossBorderStatus.REQUIRES_REVIEW
            )

        return {
            "engine": "CrossBorderComplianceEngine",
            "regional_rules_count": len(self._regional_rules),
            "total_cross_border_flows": total_flows,
            "allowed": allowed,
            "denied": denied,
            "pending_consent": pending_consent,
            "pending_review": pending_review,
            "jurisdictions_covered": sorted(set(
                r.jurisdiction.value for r in self._regional_rules
            )),
            "frameworks": sorted(set(
                r.framework.value for r in self._regional_rules
            )),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _log_flow(
        self,
        data_classification: str,
        origin: str,
        destination: str,
        purpose: str,
        status: CrossBorderStatus,
        consent_given: bool = False,
    ) -> CrossBorderFlow:
        """Create and store a cross-border flow record."""
        flow = CrossBorderFlow(
            data_classification=data_classification.upper(),
            origin_jurisdiction=origin,
            destination_jurisdiction=destination,
            purpose=purpose,
            status=status,
            consent_given=consent_given,
            resolved_at=time.time() if status in (
                CrossBorderStatus.ALLOWED, CrossBorderStatus.DENIED
            ) else None,
        )
        async with self._lock:
            self._flow_log.append(flow)
            self._save_flow_log()
        return flow

    def _save_flow_log(self) -> None:
        """Persist flow log to JSONL."""
        try:
            with open(self._db_path, "w", encoding="utf-8") as f:
                for flow in self._flow_log:
                    f.write(json.dumps(flow.to_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.error("Failed to save cross-border flow log: %s", exc)

    def _load_flow_log(self) -> None:
        """Load flow log from JSONL."""
        if not os.path.exists(self._db_path):
            return
        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        flow = CrossBorderFlow.from_dict(data)
                        self._flow_log.append(flow)
                    except json.JSONDecodeError:
                        continue
            logger.info("CrossBorderComplianceEngine: loaded %d flows from %s",
                        len(self._flow_log), self._db_path)
        except Exception as exc:
            logger.warning("Failed to load cross-border flow log: %s", exc)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_cbc_lock = asyncio.Lock()
_cbc_instance: Optional[CrossBorderComplianceEngine] = None


async def get_cross_border_compliance(
    base_compliance: Optional[Any] = None,
    audit_engine: Optional[Any] = None,
    oltp_engine: Optional[Any] = None,
) -> CrossBorderComplianceEngine:
    """Get or create the singleton CrossBorderComplianceEngine."""
    global _cbc_instance
    if _cbc_instance is None:
        async with _cbc_lock:
            if _cbc_instance is None:
                _cbc_instance = CrossBorderComplianceEngine(
                    base_compliance=base_compliance,
                    audit_engine=audit_engine,
                    oltp_engine=oltp_engine,
                )
    return _cbc_instance


def reset_cross_border_compliance() -> None:
    """Reset the singleton (for testing)."""
    global _cbc_instance
    _cbc_instance = None
