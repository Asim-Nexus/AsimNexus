
"""
governance/compliance_engine.py
AsimNexus — Compliance & Governance Engine
=============================================
Regulatory compliance, policy enforcement, audit trails.

Env vars:
  ASIM_COMPLIANCE_AUDIT_HOURS — default audit trail window (default: 24)
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger("AsimNexus.Compliance")

_DEFAULT_AUDIT_HOURS = int(os.getenv("ASIM_COMPLIANCE_AUDIT_HOURS", "24"))


class ComplianceSector(Enum):
    """Regulatory sectors"""
    GOVERNMENT = "government"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    PRIVATE = "private"
    TECHNOLOGY = "technology"


class DataClassification(Enum):
    """Data sensitivity levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    SECRET = "secret"


class CompliancePolicy:
    """Individual compliance policy rule"""
    
    def __init__(self, 
                 policy_id: str,
                 name: str,
                 sector: ComplianceSector,
                 description: str,
                 requirements: List[str],
                 enforcement_level: str = "must"):
        """Initialize compliance policy"""
        self.policy_id = policy_id
        self.name = name
        self.sector = sector
        self.description = description
        self.requirements = requirements
        self.enforcement_level = enforcement_level  # must, should, recommended
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "sector": self.sector.value,
            "description": self.description,
            "requirements": self.requirements,
            "enforcement_level": self.enforcement_level,
            "created_at": self.created_at
        }


class ComplianceEngine:
    """Compliance and governance enforcement"""
    
    def __init__(self):
        """Initialize compliance engine"""
        self.policies: Dict[str, CompliancePolicy] = {}
        self.compliance_checks: List[dict] = []
        self.violations: List[dict] = []
        
        # Initialize standard policies
        self._initialize_standard_policies()
        logger.info("✅ Compliance engine initialized")
    
    def _initialize_standard_policies(self):
        """Initialize standard compliance policies"""
        
        # GDPR (Europe/Private Sector)
        gdpr = CompliancePolicy(
            policy_id="gdpr_001",
            name="GDPR Compliance",
            sector=ComplianceSector.PRIVATE,
            description="General Data Protection Regulation (Europe)",
            requirements=[
                "User consent required for data collection",
                "Right to access user data",
                "Right to be forgotten (data deletion)",
                "Data isolation by geography",
                "Breach notification within 72 hours",
                "Data Privacy Impact Assessment for high-risk",
                "Appointment of Data Protection Officer",
                "Record of processing activities"
            ]
        )
        self.policies["gdpr_001"] = gdpr
        
        # HIPAA (Healthcare)
        hipaa = CompliancePolicy(
            policy_id="hipaa_001",
            name="HIPAA Compliance",
            sector=ComplianceSector.HEALTHCARE,
            description="Health Insurance Portability and Accountability Act (US)",
            requirements=[
                "PHI encryption at rest and in transit",
                "Access controls and authentication",
                "Audit logging of PHI access",
                "Breach notification procedures",
                "Business Associate Agreements",
                "Annual security awareness training",
                "Disaster recovery and business continuity",
                "Authorization and access management"
            ]
        )
        self.policies["hipaa_001"] = hipaa
        
        # PCI-DSS (Finance/Payment)
        pci = CompliancePolicy(
            policy_id="pci_dss_001",
            name="PCI-DSS Compliance",
            sector=ComplianceSector.FINANCE,
            description="Payment Card Industry Data Security Standard",
            requirements=[
                "Firewall configuration and maintenance",
                "Remove default passwords and security parameters",
                "Protect stored cardholder data",
                "Encrypt transmission of cardholder data",
                "Protect against malware",
                "Secure and documented access procedures",
                "Regular security testing",
                "Policy on information security"
            ]
        )
        self.policies["pci_dss_001"] = pci
        
        # FedRAMP (US Government)
        fedramp = CompliancePolicy(
            policy_id="fedramp_001",
            name="FedRAMP Compliance",
            sector=ComplianceSector.GOVERNMENT,
            description="Federal Risk and Authorization Management Program (US)",
            requirements=[
                "Security controls per NIST 800-53",
                "Continuous monitoring and compliance",
                "System security plan documentation",
                "Incident response procedures",
                "Penetration testing (annual)",
                "Vulnerability scanning (monthly)",
                "Supply chain risk management",
                "Federal contractor baseline requirements"
            ]
        )
        self.policies["fedramp_001"] = fedramp
        
        # FERPA (Education)
        ferpa = CompliancePolicy(
            policy_id="ferpa_001",
            name="FERPA Compliance",
            sector=ComplianceSector.EDUCATION,
            description="Family Educational Rights and Privacy Act (US)",
            requirements=[
                "Student privacy protection",
                "Parent/student access to records",
                "Parental consent for disclosure",
                "Secure record storage",
                "Record destruction policies",
                "Staff training on privacy",
                "Documentation of information sharing",
                "Breach notification procedures"
            ]
        )
        self.policies["ferpa_001"] = ferpa
        
        logger.info(f"Initialized {len(self.policies)} standard compliance policies")
    
    def register_policy(self, policy: CompliancePolicy) -> bool:
        """Register a new compliance policy"""
        try:
            if policy.policy_id in self.policies:
                logger.warning(f"Policy {policy.policy_id} already exists, overwriting")
            
            self.policies[policy.policy_id] = policy
            logger.info(f"Registered policy: {policy.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register policy: {e}")
            return False
    
    def get_policy(self, policy_id: str) -> Optional[CompliancePolicy]:
        """Get a compliance policy"""
        return self.policies.get(policy_id)
    
    def get_policies_by_sector(self, sector: ComplianceSector) -> List[CompliancePolicy]:
        """Get all policies for a sector"""
        return [p for p in self.policies.values() if p.sector == sector]
    
    def check_data_compliance(self, 
                            data_classification: DataClassification,
                            sector: ComplianceSector,
                            user_id: str,
                            data_size_mb: int) -> Dict[str, Any]:
        """Check if data handling complies with policy"""
        
        check_result = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "data_classification": data_classification.value,
            "sector": sector.value,
            "data_size_mb": data_size_mb,
            "compliant": True,
            "violations": [],
            "warnings": []
        }
        
        # Get applicable policies
        policies = self.get_policies_by_sector(sector)
        
        for policy in policies:
            # Check data classification requirements
            if data_classification == DataClassification.SECRET:
                check_result["violations"].append(f"SECRET data requires explicit policy approval: {policy.name}")
                check_result["compliant"] = False
            
            elif data_classification == DataClassification.RESTRICTED:
                check_result["warnings"].append(f"RESTRICTED data requires compliance audit: {policy.name}")
            
            # Check data volume limits
            if data_size_mb > 1000 and data_classification in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED]:
                check_result["violations"].append(f"Large volume of sensitive data ({data_size_mb}MB) without approval")
                check_result["compliant"] = False
        
        self.compliance_checks.append(check_result)
        logger.debug(f"Compliance check result: {check_result['compliant']} for {user_id}")
        return check_result
    
    def log_violation(self, 
                     violation_type: str,
                     policy_id: str,
                     description: str,
                     severity: str = "high",
                     user_id: Optional[str] = None) -> str:
        """Log a compliance violation"""
        
        violation = {
            "timestamp": datetime.now().isoformat(),
            "violation_id": f"vio_{int(datetime.now().timestamp() * 1000000)}",
            "violation_type": violation_type,
            "policy_id": policy_id,
            "description": description,
            "severity": severity,
            "user_id": user_id,
            "status": "open"
        }
        
        self.violations.append(violation)
        logger.warning(f"⚠️  Compliance violation logged: {violation['violation_id']} - {violation_type}")
        return violation["violation_id"]
    
    def resolve_violation(self, violation_id: str, resolution: str) -> bool:
        """Mark violation as resolved"""
        try:
            for violation in self.violations:
                if violation["violation_id"] == violation_id:
                    violation["status"] = "resolved"
                    violation["resolved_at"] = datetime.now().isoformat()
                    violation["resolution_notes"] = resolution
                    logger.info(f"✅ Violation resolved: {violation_id}")
                    return True
            
            logger.error(f"Violation {violation_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to resolve violation: {e}")
            return False
    
    def get_compliance_report(self) -> dict:
        """Generate compliance report"""
        
        open_violations = [v for v in self.violations if v["status"] == "open"]
        resolved_violations = [v for v in self.violations if v["status"] == "resolved"]
        
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for violation in open_violations:
            severity = violation.get("severity", "medium").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        compliance_score = 100
        if len(open_violations) > 0:
            compliance_score = max(0, 100 - (len(open_violations) * 5))
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_policies": len(self.policies),
            "total_violations": len(self.violations),
            "open_violations": len(open_violations),
            "resolved_violations": len(resolved_violations),
            "severity_breakdown": severity_counts,
            "compliance_score": compliance_score,
            "compliant": compliance_score >= 95,
            "total_checks": len(self.compliance_checks),
            "recent_violations": open_violations[:10]
        }
        
        return report
    
    def get_audit_trail(self, hours: Optional[int] = None) -> List[dict]:
        """Get audit trail of compliance checks and violations"""
        if hours is None:
            hours = _DEFAULT_AUDIT_HOURS
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_events = []
        
        # Add compliance checks
        for check in self.compliance_checks:
            check_time = datetime.fromisoformat(check["timestamp"])
            if check_time > cutoff_time:
                recent_events.append({
                    "timestamp": check["timestamp"],
                    "event_type": "compliance_check",
                    "data": check
                })
        
        # Add violations
        for violation in self.violations:
            vio_time = datetime.fromisoformat(violation["timestamp"])
            if vio_time > cutoff_time:
                recent_events.append({
                    "timestamp": violation["timestamp"],
                    "event_type": "violation",
                    "data": violation
                })
        
        # Sort by timestamp
        recent_events.sort(key=lambda x: x["timestamp"], reverse=True)
        return recent_events
    
    def export_compliance_state(self, filepath: str = "compliance_state.json") -> bool:
        """Export compliance state to JSON"""
        try:
            state = {
                "exported_at": datetime.now().isoformat(),
                "policies": self._serialize_policies(),
                "violations": self.violations,
                "compliance_checks": self.compliance_checks,
                "report": self.get_compliance_report()
            }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"✅ Compliance state exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export compliance state: {e}")
            return False
    
    def _serialize_policies(self) -> List[dict]:
        """Serialize policies for export"""
        return [p.to_dict() for p in self.policies.values()]


# Singleton instance
_compliance_engine: Optional[ComplianceEngine] = None


def get_compliance_engine() -> ComplianceEngine:
    """Get singleton compliance engine instance"""
    global _compliance_engine
    if _compliance_engine is None:
        _compliance_engine = ComplianceEngine()
    return _compliance_engine
