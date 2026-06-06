
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test OCR Engine
==============
Test document intelligence system
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from ocr_engine import get_ocr_engine, OCRBackend, DocumentType

def test_ocr_engine():
    """Test OCR Engine functionality"""
    
    print("🧪 Testing OCR Engine")
    print("=" * 60)
    
    ocr = get_ocr_engine()
    
    # Test 1: Get status
    print("\n📊 OCR Engine Status:")
    status = ocr.get_status()
    print(f"   Backend: {status['backend']}")
    print(f"   Initialized: {status['initialized']}")
    print(f"   Supported Documents: {status['supported_documents']}")
    print(f"   Supported Languages: {status['supported_languages']}")
    
    # Test 2: Test with mock citizenship document
    print("\n📄 Testing Citizenship Document (Mock):")
    # Since we don't have real images, we'll test with a non-existent path
    # which will trigger mock extraction based on filename
    citizenship_result = ocr.extract_text("sample_citizenship.jpg")
    print(f"   Document Type: {citizenship_result.document_type.value}")
    print(f"   Confidence: {citizenship_result.confidence:.2f}")
    print(f"   Language: {citizenship_result.language_detected}")
    print(f"   Extracted Fields:")
    for key, value in citizenship_result.fields.items():
        print(f"      {key}: {value}")
    
    # Test 3: Test with mock license document
    print("\n📄 Testing License Document (Mock):")
    license_result = ocr.extract_text("sample_license.jpg")
    print(f"   Document Type: {license_result.document_type.value}")
    print(f"   Confidence: {license_result.confidence:.2f}")
    print(f"   Extracted Fields:")
    for key, value in license_result.fields.items():
        print(f"      {key}: {value}")
    
    # Test 4: Test with mock passport document
    print("\n📄 Testing Passport Document (Mock):")
    passport_result = ocr.extract_text("sample_passport.jpg")
    print(f"   Document Type: {passport_result.document_type.value}")
    print(f"   Confidence: {passport_result.confidence:.2f}")
    print(f"   Extracted Fields:")
    for key, value in passport_result.fields.items():
        print(f"      {key}: {value}")
    
    # Test 5: Verify document authenticity
    print("\n🔍 Document Authenticity Verification:")
    verification = ocr.verify_document_authenticity(citizenship_result)
    print(f"   Is Authentic: {verification['is_authentic']}")
    print(f"   Confidence: {verification['confidence']:.2f}")
    print(f"   Checks Passed: {len(verification['checks'])}")
    print(f"   Issues Found: {len(verification['issues'])}")
    if verification['checks']:
        print("   Checks:")
        for check in verification['checks']:
            print(f"      ✅ {check}")
    if verification['issues']:
        print("   Issues:")
        for issue in verification['issues']:
            print(f"      ⚠️ {issue}")
    
    # Test 6: Test document type detection
    print("\n🔎 Document Type Detection:")
    test_texts = [
        "नागरिकता प्रमाणपत्र\nCitizenship Certificate",
        "चालक अनुमति पत्र\nDriving License",
        "राहदानी\nPassport Document",
        "Unknown document text"
    ]
    for text in test_texts:
        doc_type = ocr._detect_document_type(text)
        print(f"   '{text[:30]}...' -> {doc_type.value}")
    
    print("\n" + "=" * 60)
    print("🎯 Test Complete")
    print("=" * 60)
    print("\n💡 OCR Engine ready for document intelligence!")
    print("\n📝 To use with real documents:")
    print("   1. Install EasyOCR: pip install easyocr")
    print("   2. Or install Tesseract: pip install pytesseract")
    print("   3. Place document images in the folder")
    print("   4. Run: ocr.extract_text('path/to/image.jpg')")

if __name__ == "__main__":
    test_ocr_engine()
