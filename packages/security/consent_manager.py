
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Consent Manager
==========================
Consent management and tracking
Manages user consents and privacy preferences
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ConsentManager")


class ConsentType(Enum):
    """Types of consents"""
    DATA_PROCESSING = "data_processing"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    THIRD_PARTY = "third_party"
    PERSONALIZATION = "personalization"


class ConsentStatus(Enum):
    """Consent status"""
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    REVOKED = "revoked"


@dataclass
class ConsentRecord:
    """A consent record"""
    consent_id: str
    user_id: str
    consent_type: ConsentType
    status: ConsentStatus
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConsentManager:
    """
    Consent Manager
    
    Provides:
    - Consent tracking
    - Consent validation
    - Consent revocation
    - Compliance management
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ConsentManager")
        self.consents: Dict[str, ConsentRecord] = {}
        self.user_consents: Dict[str, List[str]] = {}  # user_id -> [consent_ids]
    
    def grant_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Grant consent for a user
        
        Args:
            user_id: User ID
            consent_type: Type of consent
            expires_at: Optional expiration date
            metadata: Additional metadata
            
        Returns:
            Consent ID
        """
        consent_id = f"consent_{consent_type.value}_{user_id}_{datetime.now().timestamp()}"
        
        # Revoke existing consent of same type
        self._revoke_existing_consent(user_id, consent_type)
        
        consent = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            consent_type=consent_type,
            status=ConsentStatus.GRANTED,
            granted_at=datetime.now(),
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self.consents[consent_id] = consent
        
        if user_id not in self.user_consents:
            self.user_consents[user_id] = []
        self.user_consents[user_id].append(consent_id)
        
        self.logger.info(f"Granted consent: {consent_type.value} for user {user_id}")
        return consent_id
    
    def revoke_consent(self, consent_id: str) -> bool:
        """Revoke a consent"""
        if consent_id not in self.consents:
            return False
        
        consent = self.consents[consent_id]
        consent.status = ConsentStatus.REVOKED
        consent.revoked_at = datetime.now()
        
        self.logger.info(f"Revoked consent: {consent_id}")
        return True
    
    def _revoke_existing_consent(self, user_id: str, consent_type: ConsentType):
        """Revoke existing consent of same type"""
        if user_id not in self.user_consents:
            return
        
        for consent_id in self.user_consents[user_id]:
            consent = self.consents.get(consent_id)
            if consent and consent.consent_type == consent_type and consent.status == ConsentStatus.GRANTED:
                self.revoke_consent(consent_id)
    
    def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Check if user has granted consent
        
        Args:
            user_id: User ID
            consent_type: Type of consent
            
        Returns:
            True if consent is granted and valid
        """
        if user_id not in self.user_consents:
            return False
        
        for consent_id in self.user_consents[user_id]:
            consent = self.consents.get(consent_id)
            if not consent:
                continue
            
            if consent.consent_type != consent_type:
                continue
            
            if consent.status != ConsentStatus.GRANTED:
                continue
            
            # Check expiration
            if consent.expires_at and datetime.now() > consent.expires_at:
                continue
            
            return True
        
        return False
    
    def get_consent(self, consent_id: str) -> Optional[Dict]:
        """Get consent by ID"""
        if consent_id not in self.consents:
            return None
        
        consent = self.consents[consent_id]
        return {
            "consent_id": consent.consent_id,
            "user_id": consent.user_id,
            "consent_type": consent.consent_type.value,
            "status": consent.status.value,
            "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
            "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
            "expires_at": consent.expires_at.isoformat() if consent.expires_at else None
        }
    
    def get_user_consents(self, user_id: str) -> List[Dict]:
        """Get all consents for a user"""
        if user_id not in self.user_consents:
            return []
        
        consents = []
        for consent_id in self.user_consents[user_id]:
            consent = self.consents.get(consent_id)
            if consent:
                consents.append({
                    "consent_id": consent.consent_id,
                    "consent_type": consent.consent_type.value,
                    "status": consent.status.value,
                    "granted_at": consent.granted_at.isoformat() if consent.granted_at else None
                })
        
        return consents
    
    def cleanup_expired_consents(self) -> int:
        """Remove expired consents"""
        now = datetime.now()
        removed = 0
        
        for consent_id, consent in list(self.consents.items()):
            if consent.expires_at and now > consent.expires_at:
                del self.consents[consent_id]
                if consent.user_id in self.user_consents:
                    self.user_consents[consent.user_id] = [
                        cid for cid in self.user_consents[consent.user_id]
                        if cid != consent_id
                    ]
                removed += 1
        
        if removed > 0:
            self.logger.info(f"Cleaned up {removed} expired consents")
        
        return removed
    
    def get_stats(self) -> Dict:
        """Get consent manager statistics"""
        granted = sum(1 for c in self.consents.values() if c.status == ConsentStatus.GRANTED)
        revoked = sum(1 for c in self.consents.values() if c.status == ConsentStatus.REVOKED)
        
        return {
            "total_consents": len(self.consents),
            "granted": granted,
            "revoked": revoked,
            "total_users": len(self.user_consents)
        }
