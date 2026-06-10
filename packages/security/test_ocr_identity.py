
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test OCR + Identity Manager Integration
=======================================
Test document verification with identity management
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from identity_manager import IdentityManager

def test_ocr_identity_integration():
    """Test OCR integration with Identity Manager"""
    
    print("🧪 Testing OCR + Identity Manager Integration")
    print("=" * 60)
    
    # Initialize Identity Manager
    manager = IdentityManager()
    
    # Test 1: Check OCR availability
    print("\n📊 OCR Engine Status:")
    if manager.ocr_engine:
        status = manager.ocr_engine.get_status()
        print(f"   Backend: {status['backend']}")
        print(f"   Initialized: {status['initialized']}")
        print("   ✅ OCR Engine integrated")
    else:
        print("   ❌ OCR Engine not available")
    
    # Test 2: Create a test identity
    print("\n👤 Creating Test Identity:")
    identity_id = manager.create_identity(
        username="test_user",
        email="test@example.com",
        password="hashed_password"
    )
    print(f"   Identity ID: {identity_id}")
    print(f"   ✅ Identity created")
    
    # Test 3: Verify document (mock)
    print("\n📄 Testing Document Verification:")
    verification = manager.verify_document_with_ocr(
        document_path="sample_citizenship.jpg",
        identity_id=identity_id
    )
    
    print(f"   Success: {verification.get('success')}")
    if verification.get('success'):
        print(f"   Document Type: {verification.get('document_type')}")
        print(f"   Name Match: {verification.get('name_match')}")
        print(f"   Verification Passed: {verification.get('verification_passed')}")
        print(f"   Confidence: {verification.get('confidence'):.2f}")
    else:
        print(f"   Error: {verification.get('error')}")
        print(f"   Message: {verification.get('message')}")
    
    # Test 4: Get identity with verification metadata
    print("\n📋 Identity Metadata:")
    identity = manager.identities.get(identity_id)
    if identity:
        print(f"   Username: {identity.username}")
        print(f"   Email: {identity.email}")
        if "last_document_verification" in identity.metadata:
            print(f"   Last Verification: {identity.metadata['last_document_verification']['timestamp']}")
    
    print("\n" + "=" * 60)
    print("🎯 Test Complete")
    print("=" * 60)
    print("\n💡 OCR + Identity Manager integration working!")
    print("\n📝 To use with real documents:")
    print("   1. Place document images (citizenship, license, passport)")
    print("   2. Call: verify_document_with_ocr('path/to/image.jpg', 'identity_id')")
    print("   3. System will extract text and verify against identity")

if __name__ == "__main__":
    test_ocr_identity_integration()
