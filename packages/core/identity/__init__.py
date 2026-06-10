"""
core/identity/__init__.py
AsimNexus — Identity subsystem package.

Exports:
  - UserIdentitySystem, get_identity_system, reset_identity_system
  - IdentityStatus, IdentityLevel, VerificationMethod
  - IdentityRecord, IdentityCredential
  - DIDSystem, get_did_system, reset_did_system
  - DIDMethod, DIDStatus, DIDDocument, DIDRecord
"""

from .user_identity import (
    UserIdentitySystem,
    get_identity_system,
    reset_identity_system,
    IdentityStatus,
    IdentityLevel,
    VerificationMethod,
    IdentityRecord,
    IdentityCredential,
)
from .did_system import (
    DIDSystem,
    get_did_system,
    reset_did_system,
    DIDMethod,
    DIDStatus,
    DIDDocument,
    DIDRecord,
)

__all__ = [
    # Identity
    "UserIdentitySystem",
    "get_identity_system",
    "reset_identity_system",
    "IdentityStatus",
    "IdentityLevel",
    "VerificationMethod",
    "IdentityRecord",
    "IdentityCredential",
    # DID
    "DIDSystem",
    "get_did_system",
    "reset_did_system",
    "DIDMethod",
    "DIDStatus",
    "DIDDocument",
    "DIDRecord",
]
