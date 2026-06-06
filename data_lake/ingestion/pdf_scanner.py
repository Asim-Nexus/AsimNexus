"""
Data Lake: PDF Scanner
======================
Scans PDF documents and extracts text content for ingestion into the Data Lake.

Supports:
- Government gazettes, legal documents, court judgments
- Multi-page documents with table of contents
- Metadata extraction (title, date, author, jurisdiction)
- OCR fallback for scanned documents
"""

import hashlib
import json
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("DataLake.PDFScanner")


@dataclass
class ScannedDocument:
    """Result of scanning a PDF document."""
    source_path: str
    title: str
    content: str
    pages: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: List[Dict[str, Any]] = field(default_factory=list)
    source_hash: str = ""
    scan_timestamp: str = ""
    
    def __post_init__(self):
        if not self.source_hash:
            self.source_hash = hashlib.sha256(
                open(self.source_path, "rb").read()
            ).hexdigest() if os.path.exists(self.source_path) else ""
        if not self.scan_timestamp:
            self.scan_timestamp = datetime.utcnow().isoformat()


class PDFScanner:
    """
    Scans PDF documents and extracts structured content.
    
    Uses PyMuPDF (fitz) if available, falls back to pdfminer, then to basic text extraction.
    """
    
    def __init__(self):
        self._engine = None
        self._init_engine()
    
    def _init_engine(self):
        """Initialize the PDF extraction engine."""
        # Try PyMuPDF first (fastest, best quality)
        try:
            import fitz
            self._engine = "pymupdf"
            self._fitz = fitz
            logger.info("PDF Scanner using PyMuPDF engine")
            return
        except ImportError:
            pass
        
        # Try pdfminer as fallback
        try:
            from pdfminer.high_level import extract_text
            self._engine = "pdfminer"
            self._pdfminer_extract = extract_text
            logger.info("PDF Scanner using pdfminer engine")
            return
        except ImportError:
            pass
        
        # Try PyPDF2 as last resort
        try:
            import PyPDF2
            self._engine = "pypdf2"
            self._PyPDF2 = PyPDF2
            logger.info("PDF Scanner using PyPDF2 engine")
            return
        except ImportError:
            pass
        
        logger.warning("No PDF engine available. Install: pip install pymupdf")
        self._engine = None
    
    def scan(self, path: str, metadata: Dict[str, Any] = None) -> Optional[ScannedDocument]:
        """
        Scan a PDF document and extract its content.
        
        Args:
            path: Path to the PDF file
            metadata: Optional metadata to attach (jurisdiction, type, etc.)
            
        Returns:
            ScannedDocument with extracted content, or None on failure
        """
        if not os.path.exists(path):
            logger.error(f"PDF not found: {path}")
            return None
        
        if self._engine is None:
            logger.error("No PDF engine available")
            return None
        
        try:
            if self._engine == "pymupdf":
                return self._scan_pymupdf(path, metadata or {})
            elif self._engine == "pdfminer":
                return self._scan_pdfminer(path, metadata or {})
            elif self._engine == "pypdf2":
                return self._scan_pypdf2(path, metadata or {})
        except Exception as e:
            logger.error(f"Failed to scan PDF {path}: {e}")
            return None
    
    def _scan_pymupdf(self, path: str, metadata: Dict[str, Any]) -> ScannedDocument:
        """Scan using PyMuPDF."""
        doc = self._fitz.open(path)
        
        title = metadata.get("title", os.path.basename(path))
        content_parts = []
        sections = []
        current_section = None
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            content_parts.append(text)
            
            # Try to detect sections from text
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                # Detect section headers (all caps, numbered, or bold-like)
                if line and (re.match(r'^[A-Z\s]{4,}$', line) or re.match(r'^\d+\.\s+[A-Z]', line)):
                    if current_section:
                        sections.append(current_section)
                    current_section = {
                        "title": line,
                        "page": page_num + 1,
                        "content": "",
                    }
                elif current_section:
                    current_section["content"] += line + " "
        
        if current_section:
            sections.append(current_section)
        
        # Extract metadata from PDF
        pdf_meta = doc.metadata or {}
        doc.close()
        
        return ScannedDocument(
            source_path=path,
            title=metadata.get("title", pdf_meta.get("title", title)),
            content="\n".join(content_parts),
            pages=len(doc) if hasattr(doc, '__len__') else 0,
            metadata={
                "author": pdf_meta.get("author", ""),
                "subject": pdf_meta.get("subject", ""),
                "keywords": pdf_meta.get("keywords", ""),
                "producer": pdf_meta.get("producer", ""),
                "format": "pdf",
                **metadata,
            },
            sections=sections,
        )
    
    def _scan_pdfminer(self, path: str, metadata: Dict[str, Any]) -> ScannedDocument:
        """Scan using pdfminer."""
        text = self._pdfminer_extract(path)
        
        return ScannedDocument(
            source_path=path,
            title=metadata.get("title", os.path.basename(path)),
            content=text,
            pages=0,
            metadata={"format": "pdf", **metadata},
            sections=[],
        )
    
    def _scan_pypdf2(self, path: str, metadata: Dict[str, Any]) -> ScannedDocument:
        """Scan using PyPDF2."""
        with open(path, "rb") as f:
            reader = self._PyPDF2.PdfReader(f)
            content_parts = []
            for page in reader.pages:
                content_parts.append(page.extract_text() or "")
        
        return ScannedDocument(
            source_path=path,
            title=metadata.get("title", os.path.basename(path)),
            content="\n".join(content_parts),
            pages=len(reader.pages),
            metadata={"format": "pdf", **metadata},
            sections=[],
        )
    
    def scan_directory(self, directory: str, recursive: bool = True) -> List[ScannedDocument]:
        """Scan all PDF files in a directory."""
        results = []
        pattern = "**/*.pdf" if recursive else "*.pdf"
        
        for pdf_path in Path(directory).glob(pattern):
            doc = self.scan(str(pdf_path))
            if doc:
                results.append(doc)
                logger.info(f"Scanned: {pdf_path.name} ({doc.pages} pages)")
        
        return results


# Singleton
pdf_scanner = PDFScanner()
