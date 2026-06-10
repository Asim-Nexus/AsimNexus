
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS OCR Engine
===================
Document Intelligence System
Extracts text from ID documents (Citizenship, License, Passport)
Supports Nepali and English languages
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

# Optional dependencies - handle gracefully if not installed
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("⚠️ OpenCV (cv2) not available - image preprocessing disabled")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("⚠️ NumPy not available - some features disabled")

logger = logging.getLogger("OCREngine")


class DocumentType(Enum):
    """Types of documents supported"""
    CITIZENSHIP = "citizenship"
    LICENSE = "license"
    PASSPORT = "passport"
    UNKNOWN = "unknown"


class OCRBackend(Enum):
    """OCR backend options"""
    EASYOCR = "easyocr"
    TESSERACT = "tesseract"
    MOCK = "mock"


@dataclass
class DocumentData:
    """Extracted document data"""
    document_type: DocumentType
    text: str
    fields: Dict[str, str]
    confidence: float
    language_detected: str
    timestamp: datetime = field(default_factory=datetime.now)


class OCREngine:
    """
    OCR Engine for Document Intelligence
    
    Features:
    - Image preprocessing (grayscale, noise reduction)
    - Multi-language support (Nepali, English)
    - Document type detection
    - Field extraction (name, ID number, etc.)
    - Format verification
    """
    
    def __init__(self, backend: OCRBackend = OCRBackend.MOCK):
        self.logger = logging.getLogger("OCREngine")
        self.backend = backend
        self.supported_docs = ["citizenship", "license", "passport"]
        self.ocr_initialized = False
        self.reader = None
        
        # Initialize chosen backend
        self._initialize_backend()
        
        logger.info(f"✅ OCR Engine initialized with {backend.value} backend")
    
    def _initialize_backend(self):
        """Initialize OCR backend"""
        
        if self.backend == OCRBackend.EASYOCR:
            try:
                import easyocr
                self.reader = easyocr.Reader(['en', 'ne'], gpu=False)
                self.ocr_initialized = True
                logger.info("✅ EasyOCR initialized")
            except ImportError:
                logger.warning("⚠️ EasyOCR not installed, falling back to mock")
                self.backend = OCRBackend.MOCK
                self.ocr_initialized = True
            except Exception as e:
                logger.error(f"❌ EasyOCR initialization failed: {e}")
                self.backend = OCRBackend.MOCK
                self.ocr_initialized = True
        
        elif self.backend == OCRBackend.TESSERACT:
            try:
                import pytesseract
                # Test tesseract availability
                pytesseract.get_tesseract_version()
                self.ocr_initialized = True
                logger.info("✅ Tesseract initialized")
            except ImportError:
                logger.warning("⚠️ pytesseract not installed, falling back to mock")
                self.backend = OCRBackend.MOCK
                self.ocr_initialized = True
            except Exception as e:
                logger.error(f"❌ Tesseract initialization failed: {e}")
                self.backend = OCRBackend.MOCK
                self.ocr_initialized = True
        
        else:  # MOCK
            self.ocr_initialized = True
            logger.info("✅ Mock OCR backend ready")
    
    def preprocess_image(self, image_path: str) -> Optional[str]:
        """
        Preprocess image for better OCR accuracy
        
        Steps:
        1. Load image
        2. Convert to grayscale
        3. Apply noise reduction
        4. Enhance contrast
        5. Thresholding
        
        Args:
            image_path: Path to image file
            
        Returns:
            Preprocessed image path or None if failed
        """
        
        if not CV2_AVAILABLE:
            logger.warning("⚠️ OpenCV not available - skipping preprocessing")
            return image_path  # Return original path
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"❌ Failed to load image: {image_path}")
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction (Gaussian blur)
            denoised = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Enhance contrast (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Apply adaptive thresholding
            thresholded = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Save preprocessed image
            preprocessed_path = image_path.replace('.', '_preprocessed.')
            cv2.imwrite(preprocessed_path, thresholded)
            
            logger.debug(f"✅ Image preprocessed: {image_path}")
            return preprocessed_path
            
        except Exception as e:
            logger.error(f"❌ Image preprocessing failed: {e}")
            return image_path  # Return original path on failure
    
    def extract_text(self, image_path: str, lang: str = 'nep+eng') -> DocumentData:
        """
        Extract text from document image
        
        Args:
            image_path: Path to image file
            lang: Language code (nep+eng for both)
            
        Returns:
            DocumentData with extracted information
        """
        
        if not os.path.exists(image_path):
            logger.error(f"❌ Image not found: {image_path}")
            return self._create_mock_result(DocumentType.UNKNOWN, "Image not found")
        
        # Preprocess image (returns path string)
        processed_path = self.preprocess_image(image_path)
        if processed_path is None:
            return self._create_mock_result(DocumentType.UNKNOWN, "Preprocessing failed")
        
        # Extract text based on backend
        if self.backend == OCRBackend.EASYOCR and self.reader:
            return self._extract_easyocr(processed_path, image_path)
        elif self.backend == OCRBackend.TESSERACT:
            return self._extract_tesseract(processed_path, image_path, lang)
        else:
            # Mock mode
            return self._extract_mock(image_path)
    
    def _extract_easyocr(self, image_path: str, original_path: str) -> DocumentData:
        """Extract text using EasyOCR"""
        
        try:
            # Perform OCR
            results = self.reader.readtext(image_path)
            
            # Combine all text
            text = ' '.join([result[1] for result in results])
            
            # Calculate average confidence
            confidences = [result[2] for result in results]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Detect document type
            doc_type = self._detect_document_type(text)
            
            # Extract fields
            fields = self._extract_fields(text, doc_type)
            
            return DocumentData(
                document_type=doc_type,
                text=text,
                fields=fields,
                confidence=avg_confidence,
                language_detected="nep+eng"
            )
            
        except Exception as e:
            logger.error(f"❌ EasyOCR extraction failed: {e}")
            return self._create_mock_result(DocumentType.UNKNOWN, str(e))
    
    def _extract_tesseract(self, image_path: str, original_path: str, lang: str) -> DocumentData:
        """Extract text using Tesseract"""
        
        try:
            import pytesseract
            
            # Perform OCR
            text = pytesseract.image_to_string(image_path, lang=lang)
            
            # Detect document type
            doc_type = self._detect_document_type(text)
            
            # Extract fields
            fields = self._extract_fields(text, doc_type)
            
            return DocumentData(
                document_type=doc_type,
                text=text,
                fields=fields,
                confidence=0.85,  # Tesseract doesn't provide per-char confidence easily
                language_detected=lang
            )
            
        except Exception as e:
            logger.error(f"❌ Tesseract extraction failed: {e}")
            return self._create_mock_result(DocumentType.UNKNOWN, str(e))
    
    def _extract_mock(self, image_path: str) -> DocumentData:
        """Mock extraction for testing"""
        
        # Simulate document detection based on filename
        filename = Path(image_path).name.lower()
        
        if "citizenship" in filename:
            doc_type = DocumentType.CITIZENSHIP
            text = "नागरिकता प्रमाणपत्र\nName: नेपाली नागरिक\nCitizenship No: 12345678\nDistrict: काठमाडौँ"
            fields = {
                "name": "नेपाली नागरिक",
                "citizenship_number": "12345678",
                "district": "काठमाडौँ",
                "document_type": "citizenship"
            }
        elif "license" in filename:
            doc_type = DocumentType.LICENSE
            text = "चालक अनुमति पत्र\nDriving License\nLicense No: NEP123456\nName: Driver Name\nCategory: Two Wheeler"
            fields = {
                "name": "Driver Name",
                "license_number": "NEP123456",
                "category": "Two Wheeler",
                "document_type": "license"
            }
        elif "passport" in filename:
            doc_type = DocumentType.PASSPORT
            text = "राहदानी / Passport\nPassport No: N1234567\nName: Passport Holder\nNationality: Nepali"
            fields = {
                "name": "Passport Holder",
                "passport_number": "N1234567",
                "nationality": "Nepali",
                "document_type": "passport"
            }
        else:
            doc_type = DocumentType.UNKNOWN
            text = "Unknown document type"
            fields = {}
        
        return DocumentData(
            document_type=doc_type,
            text=text,
            fields=fields,
            confidence=0.75,
            language_detected="nep+eng"
        )
    
    def _create_mock_result(self, doc_type: DocumentType, error_msg: str) -> DocumentData:
        """Create mock result for errors"""
        
        return DocumentData(
            document_type=doc_type,
            text=f"Error: {error_msg}",
            fields={},
            confidence=0.0,
            language_detected="unknown"
        )
    
    def _detect_document_type(self, text: str) -> DocumentType:
        """
        Detect document type from extracted text
        
        Args:
            text: Extracted text
            
        Returns:
            Document type
        """
        
        text_lower = text.lower()
        
        # Citizenship keywords
        citizenship_keywords = ['नागरिकता', 'citizenship', 'citizen', 'pramanpatra']
        if any(keyword in text_lower for keyword in citizenship_keywords):
            return DocumentType.CITIZENSHIP
        
        # License keywords
        license_keywords = ['चालक', 'license', 'driving', 'anumati', 'patra']
        if any(keyword in text_lower for keyword in license_keywords):
            return DocumentType.LICENSE
        
        # Passport keywords
        passport_keywords = ['राहदानी', 'passport', 'travel', 'document']
        if any(keyword in text_lower for keyword in passport_keywords):
            return DocumentType.PASSPORT
        
        return DocumentType.UNKNOWN
    
    def _extract_fields(self, text: str, doc_type: DocumentType) -> Dict[str, str]:
        """
        Extract structured fields from text based on document type
        
        Args:
            text: Extracted text
            doc_type: Document type
            
        Returns:
            Dictionary of extracted fields
        """
        
        fields = {}
        lines = text.split('\n')
        
        if doc_type == DocumentType.CITIZENSHIP:
            # Extract citizenship number
            for line in lines:
                if 'citizenship' in line.lower() or 'नागरिकता' in line.lower():
                    # Look for numbers
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        fields['citizenship_number'] = numbers[0]
                elif 'district' in line.lower() or 'जिल्ला' in line.lower():
                    fields['district'] = line.split(':')[-1].strip() if ':' in line else line.strip()
                elif 'name' in line.lower() or 'नाम' in line.lower():
                    fields['name'] = line.split(':')[-1].strip() if ':' in line else line.strip()
        
        elif doc_type == DocumentType.LICENSE:
            # Extract license number
            for line in lines:
                if 'license' in line.lower():
                    import re
                    numbers = re.findall(r'[A-Z0-9]+', line)
                    if numbers:
                        fields['license_number'] = numbers[0]
                elif 'category' in line.lower():
                    fields['category'] = line.split(':')[-1].strip() if ':' in line else line.strip()
                elif 'name' in line.lower():
                    fields['name'] = line.split(':')[-1].strip() if ':' in line else line.strip()
        
        elif doc_type == DocumentType.PASSPORT:
            # Extract passport number
            for line in lines:
                if 'passport' in line.lower():
                    import re
                    numbers = re.findall(r'[A-Z0-9]+', line)
                    if numbers:
                        fields['passport_number'] = numbers[0]
                elif 'nationality' in line.lower():
                    fields['nationality'] = line.split(':')[-1].strip() if ':' in line else line.strip()
                elif 'name' in line.lower():
                    fields['name'] = line.split(':')[-1].strip() if ':' in line else line.strip()
        
        fields['document_type'] = doc_type.value
        return fields
    
    def verify_document_authenticity(self, extracted_data: DocumentData) -> Dict[str, Any]:
        """
        Verify document authenticity based on format and structure
        
        Args:
            extracted_data: Extracted document data
            
        Returns:
            Verification result
        """
        
        verification = {
            "is_authentic": False,
            "confidence": 0.0,
            "checks": [],
            "issues": []
        }
        
        try:
            # Check 1: Document type is known
            if extracted_data.document_type == DocumentType.UNKNOWN:
                verification["issues"].append("Unknown document type")
            else:
                verification["checks"].append(f"Document type detected: {extracted_data.document_type.value}")
            
            # Check 2: Confidence threshold
            if extracted_data.confidence < 0.5:
                verification["issues"].append(f"Low OCR confidence: {extracted_data.confidence:.2f}")
            else:
                verification["checks"].append(f"OCR confidence acceptable: {extracted_data.confidence:.2f}")
            
            # Check 3: Required fields present
            doc_type = extracted_data.document_type
            if doc_type == DocumentType.CITIZENSHIP:
                required_fields = ['citizenship_number', 'name']
            elif doc_type == DocumentType.LICENSE:
                required_fields = ['license_number', 'name']
            elif doc_type == DocumentType.PASSPORT:
                required_fields = ['passport_number', 'name']
            else:
                required_fields = []
            
            for field in required_fields:
                if field in extracted_data.fields:
                    verification["checks"].append(f"Required field present: {field}")
                else:
                    verification["issues"].append(f"Missing required field: {field}")
            
            # Calculate overall authenticity score
            total_checks = len(verification["checks"]) + len(verification["issues"])
            if total_checks > 0:
                verification["confidence"] = len(verification["checks"]) / total_checks
            
            verification["is_authentic"] = verification["confidence"] > 0.6
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            verification["issues"].append(f"Verification error: {e}")
        
        return verification
    
    def get_status(self) -> Dict[str, Any]:
        """Get OCR engine status"""
        
        return {
            "backend": self.backend.value,
            "initialized": self.ocr_initialized,
            "supported_documents": self.supported_docs,
            "supported_languages": ["nepali", "english"]
        }


# Global OCR engine instance
ocr_engine = OCREngine()


def get_ocr_engine() -> OCREngine:
    """Get global OCR engine instance"""
    return ocr_engine
