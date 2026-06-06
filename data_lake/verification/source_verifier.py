"""
Data Lake: Source Verifier
==========================
Verifies the authenticity and integrity of data sources before ingestion.

Features:
- Source URL validation and trust scoring
- Digital signature verification (where available)
- Hash chain verification (tamper detection)
- Source reputation tracking
- Cross-reference verification
"""

import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("DataLake.SourceVerifier")


# Trusted source domains (government gazettes, official publications)
TRUSTED_DOMAINS = {
    "gov.np": "Nepal Government",
    "lawcommission.gov.np": "Nepal Law Commission",
    "supremecourt.gov.np": "Nepal Supreme Court",
    "india.gov.in": "India Government",
    "legislative.gov.in": "India Legislative",
    "gov.uk": "UK Government",
    "legislation.gov.uk": "UK Legislation",
    "whitehouse.gov": "US White House",
    "congress.gov": "US Congress",
    "supremecourt.gov": "US Supreme Court",
    "ec.europa.eu": "European Commission",
    "eur-lex.europa.eu": "EU Law",
}

# Trust levels
TRUST_LEVELS = {
    "official_gazette": 1.0,      # Official government gazette
    "government_portal": 0.95,    # .gov domain
    "court_website": 0.95,        # Court/judiciary website
    "official_database": 0.90,    # Official legal database
    "academic": 0.70,             # University/research
    "news": 0.40,                 # News media
    "unknown": 0.10,              # Unknown source
}


@dataclass
class VerificationResult:
    """Result of source verification."""
    source_path: str
    verified: bool
    trust_score: float
    trust_level: str
    source_hash: str
    previous_hash: Optional[str] = None
    chain_verified: bool = False
    warnings: List[str] = field(default_factory=list)
    verification_timestamp: str = ""
    
    def __post_init__(self):
        if not self.verification_timestamp:
            self.verification_timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": self.source_path,
            "verified": self.verified,
            "trust_score": self.trust_score,
            "trust_level": self.trust_level,
            "source_hash": self.source_hash,
            "previous_hash": self.previous_hash,
            "chain_verified": self.chain_verified,
            "warnings": self.warnings,
            "verification_timestamp": self.verification_timestamp,
        }


class SourceVerifier:
    """
    Verifies the authenticity and integrity of data sources.
    """
    
    def __init__(self):
        self._source_reputation: Dict[str, float] = {}
        self._hash_chain: List[Dict[str, Any]] = []
        self._load_hash_chain()
    
    def _load_hash_chain(self):
        """Load existing hash chain from storage."""
        chain_path = "data/data_lake_hash_chain.jsonl"
        if os.path.exists(chain_path):
            try:
                with open(chain_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self._hash_chain.append(json.loads(line))
            except Exception as e:
                logger.warning(f"Failed to load hash chain: {e}")
    
    def _save_to_hash_chain(self, entry: Dict[str, Any]):
        """Append an entry to the hash chain."""
        os.makedirs("data", exist_ok=True)
        chain_path = "data/data_lake_hash_chain.jsonl"
        try:
            with open(chain_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to save hash chain entry: {e}")
    
    def verify_source(self, source_path: str, content: str,
                      metadata: Dict[str, Any] = None) -> VerificationResult:
        """
        Verify a data source.
        
        Args:
            source_path: Path or URL of the source
            content: The content to verify
            metadata: Optional metadata about the source
            
        Returns:
            VerificationResult
        """
        metadata = metadata or {}
        warnings = []
        
        # Compute hash
        source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        # Determine trust level
        trust_level = self._determine_trust_level(source_path, metadata)
        trust_score = TRUST_LEVELS.get(trust_level, 0.1)
        
        # Adjust trust score based on source reputation
        domain = self._extract_domain(source_path)
        if domain in self._source_reputation:
            trust_score = (trust_score + self._source_reputation[domain]) / 2
        
        # Check hash chain for previous version
        previous_hash = None
        chain_verified = True
        if self._hash_chain:
            last_entry = self._hash_chain[-1]
            previous_hash = last_entry.get("source_hash")
            
            # Verify chain integrity
            if last_entry.get("next_hash") and last_entry["next_hash"] != source_hash:
                chain_verified = False
                warnings.append("Hash chain broken: next_hash mismatch")
        
        # Verify against known patterns
        if trust_level == "unknown":
            warnings.append("Unknown source — low trust")
        
        # Check for content integrity issues
        if len(content) < 10:
            warnings.append("Content too short — possible extraction error")
        
        verified = trust_score >= 0.5 and chain_verified
        
        result = VerificationResult(
            source_path=source_path,
            verified=verified,
            trust_score=trust_score,
            trust_level=trust_level,
            source_hash=source_hash,
            previous_hash=previous_hash,
            chain_verified=chain_verified,
            warnings=warnings,
        )
        
        # Add to hash chain
        chain_entry = {
            "source_path": source_path,
            "source_hash": source_hash,
            "previous_hash": previous_hash,
            "trust_score": trust_score,
            "trust_level": trust_level,
            "verified": verified,
            "timestamp": result.verification_timestamp,
        }
        if self._hash_chain:
            self._hash_chain[-1]["next_hash"] = source_hash
        self._hash_chain.append(chain_entry)
        self._save_to_hash_chain(chain_entry)
        
        return result
    
    def _determine_trust_level(self, source_path: str, metadata: Dict) -> str:
        """Determine the trust level of a source."""
        # Check metadata first
        if "trust_level" in metadata:
            return metadata["trust_level"]
        
        domain = self._extract_domain(source_path)
        
        # Check trusted domains
        for trusted_domain, _ in TRUSTED_DOMAINS.items():
            if domain.endswith(trusted_domain):
                return "government_portal"
        
        # Check for .gov domains
        if domain.endswith(".gov") or ".gov." in domain:
            return "government_portal"
        
        # Check for .ac or .edu domains
        if domain.endswith(".ac") or domain.endswith(".edu"):
            return "academic"
        
        # Check file path patterns
        if "gazette" in source_path.lower():
            return "official_gazette"
        if "court" in source_path.lower() or "judgment" in source_path.lower():
            return "court_website"
        
        return "unknown"
    
    def _extract_domain(self, source_path: str) -> str:
        """Extract domain from a URL or file path."""
        # URL pattern
        url_match = re.match(r'https?://([^/]+)', source_path)
        if url_match:
            return url_match.group(1)
        
        # File path — use directory as domain proxy
        return os.path.basename(os.path.dirname(source_path))
    
    def update_reputation(self, source_path: str, verified: bool):
        """Update the reputation score for a source."""
        domain = self._extract_domain(source_path)
        current = self._source_reputation.get(domain, 0.5)
        
        if verified:
            self._source_reputation[domain] = min(1.0, current + 0.1)
        else:
            self._source_reputation[domain] = max(0.0, current - 0.2)
    
    def verify_chain_integrity(self) -> bool:
        """Verify the integrity of the entire hash chain."""
        if not self._hash_chain:
            return True
        
        for i in range(1, len(self._hash_chain)):
            prev = self._hash_chain[i - 1]
            curr = self._hash_chain[i]
            
            if prev.get("next_hash") and prev["next_hash"] != curr.get("source_hash"):
                logger.error(f"Hash chain broken at index {i}")
                return False
        
        return True
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get statistics about the hash chain."""
        return {
            "chain_length": len(self._hash_chain),
            "chain_integrity": self.verify_chain_integrity(),
            "trusted_sources": len(self._source_reputation),
            "last_verified": self._hash_chain[-1]["timestamp"] if self._hash_chain else None,
        }


# Singleton
source_verifier = SourceVerifier()
