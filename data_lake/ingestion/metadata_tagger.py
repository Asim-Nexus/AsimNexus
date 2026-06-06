"""
Data Lake: Metadata Tagger
==========================
Tags extracted documents with structured metadata for the Data Lake.

Adds:
- Jurisdiction tagging (country, state, region)
- Document type classification (act, regulation, judgment, policy, etc.)
- Date extraction (effective date, amendment date, publication date)
- Keyword extraction
- Cross-reference detection
- Language detection
"""

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("DataLake.MetadataTagger")


# Known jurisdictions (ISO 3166-1 alpha-2 codes)
JURISDICTIONS = {
    "np": "Nepal",
    "in": "India",
    "us": "United States",
    "gb": "United Kingdom",
    "eu": "European Union",
    "ca": "Canada",
    "au": "Australia",
    "jp": "Japan",
    "cn": "China",
    "de": "Germany",
    "fr": "France",
    "sg": "Singapore",
    "my": "Malaysia",
    "th": "Thailand",
    "bd": "Bangladesh",
    "lk": "Sri Lanka",
    "pk": "Pakistan",
    "af": "Afghanistan",
    "bt": "Bhutan",
    "mv": "Maldives",
}

# Document type patterns
DOC_TYPE_PATTERNS = {
    "act": [r"\bact\b", r"\bordinance\b", r"\bstatute\b", r"\blegislation\b"],
    "regulation": [r"\bregulation\b", r"\brule\b", r"\bdirective\b", r"\border\b"],
    "judgment": [r"\bjudgment\b", r"\bdecision\b", r"\bruling\b", r"\bverdict\b", r"\bcourt\b"],
    "policy": [r"\bpolicy\b", r"\bguideline\b", r"\bframework\b", r"\bstrategy\b"],
    "circular": [r"\bcircular\b", r"\bnotification\b", r"\bgazette\b", r"\bnotice\b"],
    "treaty": [r"\btreaty\b", r"\bconvention\b", r"\bprotocol\b", r"\bagreement\b"],
    "constitution": [r"\bconstitution\b", r"\bconstitutional\b"],
    "contract": [r"\bcontract\b", r"\bagreement\b", r"\bmou\b", r"\bmoa\b"],
}


@dataclass
class TaggedDocument:
    """A document with full metadata tagging."""
    source_path: str
    title: str
    content: str
    doc_type: str = "unknown"
    jurisdiction: str = "unknown"
    language: str = "unknown"
    effective_date: Optional[str] = None
    publication_date: Optional[str] = None
    version: int = 1
    tags: List[str] = field(default_factory=list)
    references: List[Dict[str, str]] = field(default_factory=list)
    source_hash: str = ""
    tagging_timestamp: str = ""
    
    def __post_init__(self):
        if not self.tagging_timestamp:
            self.tagging_timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "source_path": self.source_path,
            "title": self.title,
            "doc_type": self.doc_type,
            "jurisdiction": self.jurisdiction,
            "language": self.language,
            "effective_date": self.effective_date,
            "publication_date": self.publication_date,
            "version": self.version,
            "tags": self.tags,
            "references": self.references,
            "source_hash": self.source_hash,
            "tagging_timestamp": self.tagging_timestamp,
        }


class MetadataTagger:
    """
    Tags documents with structured metadata for the Data Lake.
    """
    
    def tag(self, content: str, source_path: str = "", title: str = "",
            existing_metadata: Dict[str, Any] = None) -> TaggedDocument:
        """
        Tag a document with metadata.
        
        Args:
            content: The document text content
            source_path: Original file path
            title: Document title
            existing_metadata: Pre-existing metadata to incorporate
            
        Returns:
            TaggedDocument with all metadata
        """
        metadata = existing_metadata or {}
        
        # Compute source hash
        source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        # Detect document type
        doc_type = self._detect_doc_type(content, metadata)
        
        # Detect jurisdiction
        jurisdiction = self._detect_jurisdiction(content, metadata)
        
        # Detect language
        language = self._detect_language(content, metadata)
        
        # Extract dates
        effective_date = self._extract_date(content, metadata, "effective")
        publication_date = self._extract_date(content, metadata, "publication")
        
        # Extract tags
        tags = self._extract_tags(content, doc_type, jurisdiction)
        
        # Detect references
        references = self._detect_references(content)
        
        return TaggedDocument(
            source_path=source_path,
            title=title or metadata.get("title", "Untitled"),
            content=content,
            doc_type=doc_type,
            jurisdiction=jurisdiction,
            language=language,
            effective_date=effective_date,
            publication_date=publication_date,
            version=metadata.get("version", 1),
            tags=tags,
            references=references,
            source_hash=source_hash,
        )
    
    def _detect_doc_type(self, content: str, metadata: Dict) -> str:
        """Detect document type from content and metadata."""
        # Check metadata first
        if "doc_type" in metadata:
            return metadata["doc_type"]
        
        # Check title
        title = metadata.get("title", "")
        content_lower = (title + " " + content[:5000]).lower()
        
        for doc_type, patterns in DOC_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return doc_type
        
        return "unknown"
    
    def _detect_jurisdiction(self, content: str, metadata: Dict) -> str:
        """Detect jurisdiction from content and metadata."""
        # Check metadata first
        if "jurisdiction" in metadata:
            return metadata["jurisdiction"]
        
        # Check for country names in content
        content_lower = content[:5000].lower()
        for code, name in JURISDICTIONS.items():
            if name.lower() in content_lower:
                return code
        
        return "unknown"
    
    def _detect_language(self, content: str, metadata: Dict) -> str:
        """Detect language from content and metadata."""
        if "language" in metadata:
            return metadata["language"]
        
        # Simple heuristic: check for common words
        content_lower = content[:2000].lower()
        
        # English indicators
        english_words = {"the", "and", "for", "are", "this", "that", "with", "from", "shall", "pursuant"}
        if english_words & set(content_lower.split()):
            return "en"
        
        # Nepali indicators (Devanagari script)
        if re.search(r'[\u0900-\u097F]', content_lower):
            return "ne"
        
        return "unknown"
    
    def _extract_date(self, content: str, metadata: Dict, date_type: str) -> Optional[str]:
        """Extract a date from content or metadata."""
        # Check metadata first
        for key in (date_type, f"{date_type}_date", f"{date_type[:3]}_date"):
            if key in metadata:
                return metadata[key]
        
        # Try to find dates in content
        date_patterns = [
            r'\b(\d{4})-(\d{2})-(\d{2})\b',  # ISO format
            r'\b(\d{2})/(\d{2})/(\d{4})\b',  # US format
            r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content[:2000])
            if match:
                return match.group(0)
        
        return None
    
    def _extract_tags(self, content: str, doc_type: str, jurisdiction: str) -> List[str]:
        """Extract relevant tags from content."""
        tags = set()
        
        # Add type and jurisdiction tags
        if doc_type != "unknown":
            tags.add(doc_type)
        if jurisdiction != "unknown":
            tags.add(jurisdiction)
        
        # Extract key terms from content
        content_lower = content.lower()
        
        # Legal/domain-specific terms
        domain_terms = [
            "cyber", "crime", "tax", "labor", "environment", "health",
            "education", "trade", "commerce", "banking", "finance",
            "property", "family", "criminal", "civil", "constitutional",
            "human rights", "corruption", "election", "defense",
        ]
        
        for term in domain_terms:
            if term in content_lower:
                tags.add(term.replace(" ", "_"))
        
        return sorted(tags)
    
    def _detect_references(self, content: str) -> List[Dict[str, str]]:
        """Detect cross-references to other documents."""
        references = []
        
        # Pattern: "Act No. X of Year" or "Section X of Act Y"
        patterns = [
            (r'Act\s+No\.?\s*(\d+)\s+of\s+(\d{4})', "act"),
            (r'Section\s+(\d+[A-Za-z]?)', "section"),
            (r'Article\s+(\d+[A-Za-z]?)', "article"),
            (r'Rule\s+(\d+[A-Za-z]?)', "rule"),
            (r'Regulation\s+(\d+)', "regulation"),
            (r'Case\s+No\.?\s*([\d/]+)', "case"),
            (r'Judgment\s+([\w\s]+\(\d{4}\))', "judgment"),
        ]
        
        for pattern, ref_type in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                ref = {
                    "type": ref_type,
                    "reference": match.group(0),
                    "context": content[max(0, match.start()-50):match.end()+50],
                }
                if ref not in references:
                    references.append(ref)
        
        return references


# Singleton
metadata_tagger = MetadataTagger()
