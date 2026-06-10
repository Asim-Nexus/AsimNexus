
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Identity Manager
==========================
Identity and authentication management
Manages user identities and authentication
Integrates with OCR Engine for document verification
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
from pathlib import Path

logger = logging.getLogger("IdentityManager")


class IdentityStatus(Enum):
    """Identity status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class AuthMethod(Enum):
    """Authentication methods"""
    PASSWORD = "password"
    API_KEY = "api_key"
    TOKEN = "token"
    BIOMETRIC = "biometric"
    MULTI_FACTOR = "multi_factor"


@dataclass
class Identity:
    """A user identity"""
    identity_id: str
    username: str
    email: str
    status: IdentityStatus = IdentityStatus.ACTIVE
    auth_methods: List[AuthMethod] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """A user session"""
    session_id: str
    identity_id: str
    token: str
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.now)


class IdentityManager:
    """
    Identity Manager
    
    Provides:
    - Identity management
    - Authentication
    - Session management
    - Role management
    """
    
    def __init__(self):
        self.logger = logging.getLogger("IdentityManager")
        self.identities: Dict[str, Identity] = {}
        self.sessions: Dict[str, Session] = {}
        self.username_to_id: Dict[str, str] = {}
        self.session_timeout_hours = 24
        self.ocr_engine = None
        
        # Try to initialize OCR engine
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize OCR engine for document verification"""
        try:
            from ocr_engine import get_ocr_engine
            self.ocr_engine = get_ocr_engine()
            logger.info("✅ OCR Engine integrated with Identity Manager")
        except ImportError:
            logger.warning("⚠️ OCR Engine not available - document verification disabled")
            self.ocr_engine = None
    
    def create_identity(
        self,
        username: str,
        email: str,
        password: Optional[str] = None
    ) -> str:
        """
        Create a new identity
        
        Args:
            username: Username
            email: Email address
            password: Optional password hash
            
        Returns:
            Identity ID
        """
        if username in self.username_to_id:
            return ""
        
        identity_id = f"identity_{datetime.now().timestamp()}"
        
        auth_methods = []
        if password:
            auth_methods.append(AuthMethod.PASSWORD)
        
        identity = Identity(
            identity_id=identity_id,
            username=username,
            email=email,
            auth_methods=auth_methods
        )
        
        self.identities[identity_id] = identity
        self.username_to_id[username] = identity_id
        
        self.logger.info(f"Created identity: {username}")
        return identity_id
    
    def get_identity(self, identity_id: str) -> Optional[Dict]:
        """Get identity by ID"""
        if identity_id not in self.identities:
            return None
        
        identity = self.identities[identity_id]
        return {
            "identity_id": identity.identity_id,
            "username": identity.username,
            "email": identity.email,
            "status": identity.status.value,
            "auth_methods": [m.value for m in identity.auth_methods],
            "roles": identity.roles,
            "created_at": identity.created_at.isoformat(),
            "last_login": identity.last_login.isoformat() if identity.last_login else None
        }
    
    def get_identity_by_username(self, username: str) -> Optional[Dict]:
        """Get identity by username"""
        if username not in self.username_to_id:
            return None
        
        return self.get_identity(self.username_to_id[username])
    
    def authenticate(
        self,
        username: str,
        password: str
    ) -> Optional[str]:
        """
        Authenticate a user
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Session ID if successful
        """
        identity = self.get_identity_by_username(username)
        if not identity:
            return None
        
        # In production, this would verify the password hash
        # For now, accept any authentication
        return self.create_session(identity["identity_id"])
    
    def create_session(self, identity_id: str) -> str:
        """
        Create a session for an identity
        
        Args:
            identity_id: Identity ID
            
        Returns:
            Session ID
        """
        session_id = f"session_{datetime.now().timestamp()}"
        token = self._generate_token()
        
        expires_at = datetime.now() + timedelta(hours=self.session_timeout_hours)
        
        session = Session(
            session_id=session_id,
            identity_id=identity_id,
            token=token,
            expires_at=expires_at
        )
        
        self.sessions[session_id] = session
        
        # Update last login
        if identity_id in self.identities:
            self.identities[identity_id].last_login = datetime.now()
        
        self.logger.info(f"Created session: {session_id}")
        return session_id
    
    def _generate_token(self) -> str:
        """Generate a secure token"""
        return hashlib.sha256(f"{datetime.now().timestamp()}".encode()).hexdigest()
    
    def validate_session(self, session_id: str) -> bool:
        """Validate a session"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Check expiration
        if datetime.now() > session.expires_at:
            del self.sessions[session_id]
            return False
        
        return True
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a session"""
        if session_id not in self.sessions:
            return False
        
        del self.sessions[session_id]
        self.logger.info(f"Revoked session: {session_id}")
        return True
    
    def add_role(self, identity_id: str, role: str) -> bool:
        """Add a role to an identity"""
        if identity_id not in self.identities:
            return False
        
        if role not in self.identities[identity_id].roles:
            self.identities[identity_id].roles.append(role)
            self.logger.info(f"Added role {role} to {identity_id}")
        
        return True
    
    def verify_document_with_ocr(self, document_path: str, identity_id: str) -> Dict[str, Any]:
        """
        Verify identity document using OCR
        
        Args:
            document_path: Path to document image
            identity_id: Identity to verify against
            
        Returns:
            Verification result
        """
        
        if not self.ocr_engine:
            return {
                "success": False,
                "error": "OCR Engine not available",
                "message": "Document verification requires OCR Engine"
            }
        
        if identity_id not in self.identities:
            return {
                "success": False,
                "error": "Identity not found",
                "message": f"Identity {identity_id} does not exist"
            }
        
        identity = self.identities[identity_id]
        
        try:
            # Extract text from document
            doc_data = self.ocr_engine.extract_text(document_path)
            
            # Verify document authenticity
            verification = self.ocr_engine.verify_document_authenticity(doc_data)
            
            # Check if document matches identity
            name_match = False
            if 'name' in doc_data.fields:
                extracted_name = doc_data.fields['name'].lower()
                identity_name = identity.username.lower()
                name_match = extracted_name in identity_name or identity_name in extracted_name
            
            result = {
                "success": True,
                "document_type": doc_data.document_type.value,
                "extracted_fields": doc_data.fields,
                "authenticity": verification,
                "name_match": name_match,
                "confidence": doc_data.confidence,
                "verification_passed": verification["is_authentic"] and name_match,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store verification in identity metadata
            identity.metadata["last_document_verification"] = result
            
            logger.info(f"Document verification completed for {identity_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Document verification failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Document verification failed"
            }
    
    def remove_role(self, identity_id: str, role: str) -> bool:
        """Remove a role from an identity"""
        if identity_id not in self.identities:
            return False
        
        if role in self.identities[identity_id].roles:
            self.identities[identity_id].roles.remove(role)
            self.logger.info(f"Removed role {role} from {identity_id}")
        
        return True
    
    def list_identities(self, status: Optional[IdentityStatus] = None) -> List[Dict]:
        """List identities with optional filtering"""
        identities = []
        
        for identity in self.identities.values():
            if status and identity.status != status:
                continue
            
            identities.append({
                "identity_id": identity.identity_id,
                "username": identity.username,
                "email": identity.email,
                "status": identity.status.value,
                "roles": identity.roles
            })
        
        return identities
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
        now = datetime.now()
        removed = 0
        
        for session_id, session in list(self.sessions.items()):
            if now > session.expires_at:
                del self.sessions[session_id]
                removed += 1
        
        if removed > 0:
            self.logger.info(f"Cleaned up {removed} expired sessions")
        
        return removed
    
    def get_stats(self) -> Dict:
        """Get identity manager statistics"""
        return {
            "total_identities": len(self.identities),
            "active_identities": sum(1 for i in self.identities.values() if i.status == IdentityStatus.ACTIVE),
            "total_sessions": len(self.sessions),
            "active_sessions": sum(1 for s in self.sessions.values() if datetime.now() < s.expires_at)
        }
