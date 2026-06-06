
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Dharma-Chakra Council System
======================================
Digital Council for automated 51% government control
Experts review Global Law Sync reports
Auto-refactor when laws change
Prevent veto power abuse
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("DharmaChakraCouncil")

class CouncilMemberType(Enum):
    """Types of council members"""
    LEGAL_EXPERT = "legal_expert"
    CONSTITUTIONAL_EXPERT = "constitutional_expert"
    TECHNICAL_EXPERT = "technical_expert"
    ETHICS_EXPERT = "ethics_expert"
    GOVERNMENT_REPRESENTATIVE = "government_representative"
    CIVIL_SOCIETY_REPRESENTATIVE = "civil_society_representative"

class ReviewStatus(Enum):
    """Status of law review"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFICATION_REQUIRED = "modification_required"

class VetoStatus(Enum):
    """Status of veto power usage"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ABUSED = "abused"
    REVOKED = "revoked"

@dataclass
class CouncilMember:
    """Member of Dharma-Chakra Council"""
    member_id: str
    name: str
    member_type: CouncilMemberType
    country: str
    expertise: List[str]
    joined_at: datetime
    active: bool = True

@dataclass
class LawReview:
    """Review of a law change"""
    review_id: str
    law_id: str
    law_title: str
    country: str
    change_type: str  # "new", "amendment", "repeal"
    submitted_by: str
    submitted_at: datetime
    reviewed_by: List[str]
    review_status: ReviewStatus
    findings: str
    recommendation: str
    auto_refactor_required: bool = False
    completed_at: Optional[datetime] = None

@dataclass
class VetoRecord:
    """Record of veto power usage"""
    veto_id: str
    exercised_by: str
    reason: str
    action_vetoed: str
    timestamp: datetime
    status: VetoStatus
    abuse_detected: bool = False
    abuse_reason: str = ""

class DharmaChakraCouncil:
    """
    Dharma-Chakra Council System
    Digital Council for automated 51% government control
    Experts review Global Law Sync reports
    """
    
    def __init__(self):
        self.council_members: Dict[str, CouncilMember] = {}
        self.law_reviews: Dict[str, LawReview] = {}
        self.veto_records: List[VetoRecord] = []
        self.veto_power_active = True
        self.auto_refactor_enabled = True
        
        # Initialize council
        self._initialize_council()
        
    def _initialize_council(self) -> None:
        """Initialize the Dharma-Chakra Council"""
        logger.info("⚖️ Initializing Dharma-Chakra Council System...")
        logger.info("👥 Digital Council: Expert Review")
        logger.info("📜 Global Law Sync: Automated Monitoring")
        logger.info("🛡️ Veto Power: Abuse Prevention")
        logger.info("✅ Dharma-Chakra Council initialized")
        
        # Create default council members
        self._create_default_council_members()
    
    def _create_default_council_members(self) -> None:
        """Create default council members"""
        try:
            logger.info("👥 Creating default council members...")
            
            members = [
                {
                    "name": "Legal Expert 1",
                    "member_type": CouncilMemberType.LEGAL_EXPERT,
                    "country": "Nepal",
                    "expertise": ["constitutional_law", "international_law"]
                },
                {
                    "name": "Constitutional Expert 1",
                    "member_type": CouncilMemberType.CONSTITUTIONAL_EXPERT,
                    "country": "Nepal",
                    "expertise": ["constitution_interpretation", "human_rights"]
                },
                {
                    "name": "Technical Expert 1",
                    "member_type": CouncilMemberType.TECHNICAL_EXPERT,
                    "country": "Nepal",
                    "expertise": ["system_architecture", "security"]
                },
                {
                    "name": "Ethics Expert 1",
                    "member_type": CouncilMemberType.ETHICS_EXPERT,
                    "country": "Nepal",
                    "expertise": ["digital_ethics", "privacy"]
                },
                {
                    "name": "Government Representative",
                    "member_type": CouncilMemberType.GOVERNMENT_REPRESENTATIVE,
                    "country": "Nepal",
                    "expertise": ["policy", "governance"]
                },
                {
                    "name": "Civil Society Representative",
                    "member_type": CouncilMemberType.CIVIL_SOCIETY_REPRESENTATIVE,
                    "country": "Nepal",
                    "expertise": ["citizen_rights", "advocacy"]
                }
            ]
            
            for member_data in members:
                member = CouncilMember(
                    member_id=f"member_{uuid.uuid4().hex[:12]}",
                    name=member_data["name"],
                    member_type=member_data["member_type"],
                    country=member_data["country"],
                    expertise=member_data["expertise"],
                    joined_at=datetime.utcnow()
                )
                self.council_members[member.member_id] = member
            
            logger.info(f"✅ Created {len(self.council_members)} council members")
            
        except Exception as e:
            logger.error(f"❌ Council member creation error: {e}")
    
    def add_council_member(
        self,
        name: str,
        member_type: CouncilMemberType,
        country: str,
        expertise: List[str]
    ) -> CouncilMember:
        """Add a new council member"""
        try:
            logger.info(f"👤 Adding council member: {name}")
            
            member = CouncilMember(
                member_id=f"member_{uuid.uuid4().hex[:12]}",
                name=name,
                member_type=member_type,
                country=country,
                expertise=expertise,
                joined_at=datetime.utcnow()
            )
            
            self.council_members[member.member_id] = member
            
            logger.info(f"✅ Council member added: {member.member_id}")
            return member
            
        except Exception as e:
            logger.error(f"❌ Council member addition error: {e}")
            raise
    
    def submit_law_for_review(
        self,
        law_id: str,
        law_title: str,
        country: str,
        change_type: str,
        submitted_by: str
    ) -> LawReview:
        """Submit a law for council review"""
        try:
            logger.info(f"📜 Submitting law for review: {law_title}")
            logger.info(f"   Country: {country}")
            logger.info(f"   Change Type: {change_type}")
            
            review = LawReview(
                review_id=f"review_{uuid.uuid4().hex[:12]}",
                law_id=law_id,
                law_title=law_title,
                country=country,
                change_type=change_type,
                submitted_by=submitted_by,
                submitted_at=datetime.utcnow(),
                reviewed_by=[],
                review_status=ReviewStatus.PENDING,
                findings="",
                recommendation=""
            )
            
            self.law_reviews[review.review_id] = review
            
            logger.info(f"✅ Law submitted for review: {review.review_id}")
            return review
            
        except Exception as e:
            logger.error(f"❌ Law submission error: {e}")
            raise
    
    def review_law(
        self,
        review_id: str,
        reviewer_id: str,
        findings: str,
        recommendation: str,
        auto_refactor_required: bool = False
    ) -> LawReview:
        """Review a law submission"""
        try:
            review = self.law_reviews.get(review_id)
            
            if not review:
                raise Exception("Review not found")
            
            logger.info(f"📋 Reviewing law: {review.law_title}")
            logger.info(f"   Reviewer: {reviewer_id}")
            
            review.reviewed_by.append(reviewer_id)
            review.findings = findings
            review.recommendation = recommendation
            review.auto_refactor_required = auto_refactor_required
            review.review_status = ReviewStatus.UNDER_REVIEW
            
            # If all experts have reviewed, mark as complete
            required_reviewers = 3  # Minimum required
            if len(review.reviewed_by) >= required_reviewers:
                review.review_status = ReviewStatus.APPROVED if recommendation == "approve" else ReviewStatus.REJECTED
                review.completed_at = datetime.utcnow()
                
                # Trigger auto-refactor if required
                if auto_refactor_required and self.auto_refactor_enabled:
                    logger.info(f"🧬 Triggering auto-refactor for: {review.law_title}")
            
            logger.info(f"✅ Law review complete: {review.review_id}")
            return review
            
        except Exception as e:
            logger.error(f"❌ Law review error: {e}")
            raise
    
    def exercise_veto(
        self,
        exercised_by: str,
        reason: str,
        action_vetoed: str
    ) -> VetoRecord:
        """
        Exercise veto power
        Includes abuse detection
        """
        try:
            logger.info(f"🛡️ Veto power exercised by: {exercised_by}")
            logger.info(f"   Reason: {reason}")
            logger.info(f"   Action: {action_vetoed}")
            
            # Check for abuse
            abuse_detected = self._detect_veto_abuse(exercised_by, reason)
            
            veto = VetoRecord(
                veto_id=f"veto_{uuid.uuid4().hex[:12]}",
                exercised_by=exercised_by,
                reason=reason,
                action_vetoed=action_vetoed,
                timestamp=datetime.utcnow(),
                status=VetoStatus.SUSPENDED if abuse_detected else VetoStatus.ACTIVE,
                abuse_detected=abuse_detected,
                abuse_reason="Potential abuse detected" if abuse_detected else ""
            )
            
            self.veto_records.append(veto)
            
            if abuse_detected:
                logger.warning(f"⚠️ Veto abuse detected: {exercised_by}")
                self.veto_power_active = False
            
            logger.info(f"✅ Veto recorded: {veto.veto_id}")
            return veto
            
        except Exception as e:
            logger.error(f"❌ Veto exercise error: {e}")
            raise
    
    def _detect_veto_abuse(self, exercised_by: str, reason: str) -> bool:
        """Detect if veto power is being abused"""
        try:
            # Check veto frequency
            recent_vetoes = [
                v for v in self.veto_records
                if v.exercised_by == exercised_by
                and (datetime.utcnow() - v.timestamp).days < 30
            ]
            
            if len(recent_vetoes) > 5:
                return True  # Too many vetoes in 30 days
            
            # Check for vague reasons
            vague_reasons = ["personal", "dislike", "unspecified", "no reason"]
            if any(vague in reason.lower() for vague in vague_reasons):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Abuse detection error: {e}")
            return False
    
    def get_council_status(self) -> Dict[str, Any]:
        """Get council status"""
        active_members = len([m for m in self.council_members.values() if m.active])
        
        pending_reviews = len([r for r in self.law_reviews.values() if r.review_status == ReviewStatus.PENDING])
        completed_reviews = len([r for r in self.law_reviews.values() if r.review_status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]])
        
        recent_vetoes = len([v for v in self.veto_records if (datetime.utcnow() - v.timestamp).days < 30])
        abused_vetoes = len([v for v in self.veto_records if v.abuse_detected])
        
        return {
            "total_council_members": len(self.council_members),
            "active_members": active_members,
            "pending_law_reviews": pending_reviews,
            "completed_law_reviews": completed_reviews,
            "recent_vetoes": recent_vetoes,
            "abused_vetoes": abused_vetoes,
            "veto_power_active": self.veto_power_active,
            "auto_refactor_enabled": self.auto_refactor_enabled
        }

# Global Dharma-Chakra Council instance
_dharma_chakra_council = DharmaChakraCouncil()

def main():
    """Main entry point for testing"""
    # Submit law for review
    review = _dharma_chakra_council.submit_law_for_review(
        law_id="law_np_001",
        law_title="Digital Privacy Act Amendment",
        country="Nepal",
        change_type="amendment",
        submitted_by="government_np"
    )
    
    print(f"Law Submitted: {review.review_id}")
    
    # Review law
    reviewed = _dharma_chakra_council.review_law(
        review_id=review.review_id,
        reviewer_id="member_001",
        findings="Law aligns with constitutional privacy provisions",
        recommendation="approve",
        auto_refactor_required=True
    )
    
    print(f"Law Reviewed: {reviewed.review_status.value}")
    
    # Exercise veto
    veto = _dharma_chakra_council.exercise_veto(
        exercised_by="government_np",
        reason="National security concern",
        action_vetoed="Data export approval"
    )
    
    print(f"Veto Exercised: {veto.status.value}")
    
    # Get status
    status = _dharma_chakra_council.get_council_status()
    print(f"\nCouncil Status: {json.dumps(status, indent=2)}")

if __name__ == "__main__":
    main()
