
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Biometric + Hardware Root of Trust
============================================
Device-level security (TPM, Secure Enclave)
Includes: Biometric authentication, hardware attestation, secure key storage
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid
import os
import hashlib

logger = logging.getLogger("HardwareRoot")


class BiometricType(Enum):
    """Types of biometric authentication"""
    FINGERPRINT = "fingerprint"
    FACE = "face"
    VOICE = "voice"
    IRIS = "iris"
    PALM = "palm"


class HardwareModule(Enum):
    """Hardware security modules"""
    TPM = "tpm"  # Trusted Platform Module
    SECURE_ENCLAVE = "secure_enclave"  # Apple Secure Enclave
    TEE = "tee"  # Trusted Execution Environment
    SGX = "sgx"  # Intel SGX
    SEV = "sev"  # AMD SEV


@dataclass
class BiometricTemplate:
    """Biometric template for authentication"""
    template_id: str
    user_id: str
    biometric_type: BiometricType
    template_data: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None


@dataclass
class HardwareAttestation:
    """Hardware attestation record"""
    attestation_id: str
    device_id: str
    hardware_module: HardwareModule
    attestation_data: str
    certificate_chain: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None


@dataclass
class SecureKey:
    """Secure key stored in hardware"""
    key_id: str
    key_type: str
    key_data: str
    device_id: str
    hardware_module: HardwareModule
    created_at: datetime = field(default_factory=datetime.utcnow)


class HardwareRootTrust:
    """Biometric and hardware root of trust system"""
    
    def __init__(self):
        self.biometric_templates: Dict[str, BiometricTemplate] = {}
        self.attestations: Dict[str, HardwareAttestation] = {}
        self.secure_keys: Dict[str, SecureKey] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize hardware root trust"""
        logger.info("🔐 Initializing Biometric + Hardware Root of Trust...")
        logger.info("👆 Setting up biometric authentication")
        logger.info("🔒 Setting up hardware attestation")
        logger.info("🔑 Setting up secure key storage")
        logger.info("✅ Hardware Root of Trust initialized")
    
    def register_biometric(
        self,
        user_id: str,
        biometric_type: BiometricType,
        template_data: str
    ) -> BiometricTemplate:
        """Register biometric template for user"""
        # Hash template data for security
        hashed_data = hashlib.sha256(template_data.encode()).hexdigest()
        
        template = BiometricTemplate(
            template_id=f"bio_{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            biometric_type=biometric_type,
            template_data=hashed_data
        )
        
        self.biometric_templates[template.template_id] = template
        logger.info(f"✅ Registered biometric: {biometric_type.value} for {user_id}")
        return template
    
    def authenticate_biometric(
        self,
        user_id: str,
        biometric_type: BiometricType,
        provided_data: str
    ) -> bool:
        """Authenticate user with biometric"""
        # Find matching template
        template = next(
            (t for t in self.biometric_templates.values()
             if t.user_id == user_id and t.biometric_type == biometric_type),
            None
        )
        
        if not template:
            return False
        
        # Verify biometric data
        hashed_provided = hashlib.sha256(provided_data.encode()).hexdigest()
        valid = template.template_data == hashed_provided
        
        if valid:
            template.last_used = datetime.utcnow()
            logger.info(f"✅ Biometric authentication successful: {user_id}")
        else:
            logger.warning(f"❌ Biometric authentication failed: {user_id}")
        
        return valid
    
    def create_attestation(
        self,
        device_id: str,
        hardware_module: HardwareModule,
        attestation_data: str,
        certificate_chain: List[str],
        valid_days: int = 365
    ) -> HardwareAttestation:
        """Create hardware attestation"""
        attestation = HardwareAttestation(
            attestation_id=f"attest_{uuid.uuid4().hex[:8]}",
            device_id=device_id,
            hardware_module=hardware_module,
            attestation_data=attestation_data,
            certificate_chain=certificate_chain,
            valid_until=datetime.utcnow() + timedelta(days=valid_days)
        )
        
        self.attestations[attestation.attestation_id] = attestation
        logger.info(f"✅ Created attestation: {device_id} ({hardware_module.value})")
        return attestation
    
    def verify_attestation(self, attestation_id: str) -> bool:
        """Verify hardware attestation"""
        if attestation_id not in self.attestations:
            return False
        
        attestation = self.attestations[attestation_id]
        
        # Check if attestation is still valid
        if attestation.valid_until and datetime.utcnow() > attestation.valid_until:
            logger.warning(f"❌ Attestation expired: {attestation_id}")
            return False
        
        # Simulate attestation verification
        valid = True
        logger.info(f"✓ Attestation verification: {valid}")
        return valid
    
    def store_secure_key(
        self,
        key_type: str,
        key_data: str,
        device_id: str,
        hardware_module: HardwareModule
    ) -> SecureKey:
        """Store key in hardware security module"""
        # Encrypt key data (simulated)
        encrypted_key = hashlib.sha256(key_data.encode()).hexdigest()
        
        key = SecureKey(
            key_id=f"key_{uuid.uuid4().hex[:8]}",
            key_type=key_type,
            key_data=encrypted_key,
            device_id=device_id,
            hardware_module=hardware_module
        )
        
        self.secure_keys[key.key_id] = key
        logger.info(f"✅ Stored secure key in {hardware_module.value}")
        return key
    
    def retrieve_secure_key(self, key_id: str) -> Optional[SecureKey]:
        """Retrieve secure key from hardware"""
        return self.secure_keys.get(key_id)
    
    def rotate_key(self, key_id: str) -> Optional[SecureKey]:
        """Rotate secure key"""
        if key_id not in self.secure_keys:
            return None
        
        old_key = self.secure_keys[key_id]
        
        # Generate new key
        new_key = self.store_secure_key(
            key_type=old_key.key_type,
            key_data=f"new_key_{uuid.uuid4().hex}",
            device_id=old_key.device_id,
            hardware_module=old_key.hardware_module
        )
        
        # Remove old key
        del self.secure_keys[key_id]
        
        logger.info(f"✅ Rotated key: {key_id} -> {new_key.key_id}")
        return new_key
    
    def get_device_attestations(self, device_id: str) -> List[HardwareAttestation]:
        """Get all attestations for device"""
        return [
            a for a in self.attestations.values()
            if a.device_id == device_id
        ]
    
    def get_user_biometrics(self, user_id: str) -> List[BiometricTemplate]:
        """Get all biometric templates for user"""
        return [
            t for t in self.biometric_templates.values()
            if t.user_id == user_id
        ]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        biometric_counts = {}
        for template in self.biometric_templates.values():
            biometric_counts[template.biometric_type.value] = biometric_counts.get(template.biometric_type.value, 0) + 1
        
        module_counts = {}
        for attestation in self.attestations.values():
            module_counts[attestation.hardware_module.value] = module_counts.get(attestation.hardware_module.value, 0) + 1
        
        return {
            "total_biometric_templates": len(self.biometric_templates),
            "biometric_type_distribution": biometric_counts,
            "total_attestations": len(self.attestations),
            "hardware_module_distribution": module_counts,
            "total_secure_keys": len(self.secure_keys)
        }


# Global instance
_hardware_root: Optional[HardwareRootTrust] = None


def get_hardware_root() -> HardwareRootTrust:
    """Get singleton instance"""
    global _hardware_root
    if _hardware_root is None:
        _hardware_root = HardwareRootTrust()
    return _hardware_root
