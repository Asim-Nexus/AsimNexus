"""
Data Lake: Structured Query
===========================
Provides structured query capabilities for the Data Lake.

Supports:
- Query by section, clause, amendment
- Jurisdiction-filtered queries
- Date-range queries (effective date, amendment date)
- Document type filtering
- Tag-based queries
- Version-aware queries ("What was the rule in 2023?")
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("DataLake.StructuredQuery")


@dataclass
class QueryResult:
    """Result of a structured query."""
    query: str
    results: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    query_time_ms: float = 0.0
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": self.results,
            "total_count": self.total_count,
            "query_time_ms": self.query_time_ms,
            "filters_applied": self.filters_applied,
        }


@dataclass
class QueryFilter:
    """Filter criteria for structured queries."""
    jurisdiction: Optional[str] = None
    doc_type: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    section: Optional[str] = None
    clause: Optional[str] = None
    version: Optional[int] = None
    language: Optional[str] = None


class StructuredQueryEngine:
    """
    Provides structured query capabilities for the Data Lake.
    
    Queries can be expressed as:
    - Natural language: "What is the tax rate in Nepal?"
    - Structured: {"jurisdiction": "np", "doc_type": "act", "tags": ["tax"]}
    - Section reference: "Section 45 of IT Act 2079"
    """
    
    def __init__(self, storage_path: str = "data/data_lake_records.json"):
        self.storage_path = storage_path
        self.records: List[Dict[str, Any]] = []
        self._load_records()
    
    def _load_records(self):
        """Load records from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
                logger.info(f"Loaded {len(self.records)} records for querying")
            except Exception as e:
                logger.warning(f"Failed to load records: {e}")
    
    def query(self, query_text: str, filters: QueryFilter = None,
              limit: int = 20, offset: int = 0) -> QueryResult:
        """
        Execute a structured query.
        
        Args:
            query_text: The query text (natural language or structured)
            filters: Optional filters to apply
            limit: Maximum results to return
            offset: Results offset for pagination
            
        Returns:
            QueryResult with matching records
        """
        import time
        start_time = time.time()
        
        filters = filters or QueryFilter()
        results = []
        
        # Parse query for structured references
        parsed = self._parse_query(query_text)
        
        # Merge parsed filters with provided filters
        effective_filters = self._merge_filters(parsed, filters)
        
        # Apply filters
        for record in self.records:
            if self._matches_filters(record, effective_filters):
                # Score relevance
                score = self._score_relevance(record, query_text, effective_filters)
                results.append((score, record))
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Apply pagination
        paginated = [r[1] for r in results[offset:offset + limit]]
        
        query_time = (time.time() - start_time) * 1000
        
        return QueryResult(
            query=query_text,
            results=paginated,
            total_count=len(results),
            query_time_ms=query_time,
            filters_applied={
                "jurisdiction": effective_filters.jurisdiction,
                "doc_type": effective_filters.doc_type,
                "tags": effective_filters.tags,
                "date_from": effective_filters.date_from,
                "date_to": effective_filters.date_to,
                "section": effective_filters.section,
                "clause": effective_filters.clause,
                "version": effective_filters.version,
            },
        )
    
    def _parse_query(self, query_text: str) -> QueryFilter:
        """Parse a query text for structured references."""
        filters = QueryFilter()
        
        # Section reference: "Section 45" or "Sec 45"
        section_match = re.search(r'(?:Section|Sec|S\.)\s*(\d+[A-Za-z]?)', query_text, re.IGNORECASE)
        if section_match:
            filters.section = section_match.group(1)
        
        # Clause reference: "Clause 3" or "Cl 3"
        clause_match = re.search(r'(?:Clause|Cl\.)\s*(\d+[A-Za-z]?)', query_text, re.IGNORECASE)
        if clause_match:
            filters.clause = clause_match.group(1)
        
        # Jurisdiction detection
        jurisdictions = {
            "nepal": "np", "india": "in", "united states": "us",
            "usa": "us", "uk": "gb", "united kingdom": "gb",
            "european union": "eu", "canada": "ca", "australia": "au",
        }
        query_lower = query_text.lower()
        for name, code in jurisdictions.items():
            if name in query_lower:
                filters.jurisdiction = code
                break
        
        # Document type detection
        doc_types = ["act", "regulation", "judgment", "policy", "circular", "treaty", "constitution"]
        for doc_type in doc_types:
            if doc_type in query_lower:
                filters.doc_type = doc_type
                break
        
        # Year detection (for version-aware queries)
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', query_text)
        if year_match:
            year = year_match.group(1)
            filters.date_from = f"{year}-01-01"
            filters.date_to = f"{year}-12-31"
        
        return filters
    
    def _merge_filters(self, parsed: QueryFilter, provided: QueryFilter) -> QueryFilter:
        """Merge parsed filters with provided filters (provided takes precedence)."""
        return QueryFilter(
            jurisdiction=provided.jurisdiction or parsed.jurisdiction,
            doc_type=provided.doc_type or parsed.doc_type,
            tags=provided.tags or parsed.tags,
            date_from=provided.date_from or parsed.date_from,
            date_to=provided.date_to or parsed.date_to,
            section=provided.section or parsed.section,
            clause=provided.clause or parsed.clause,
            version=provided.version or parsed.version,
            language=provided.language or parsed.language,
        )
    
    def _matches_filters(self, record: Dict[str, Any], filters: QueryFilter) -> bool:
        """Check if a record matches the given filters."""
        if filters.jurisdiction and record.get("jurisdiction") != filters.jurisdiction:
            return False
        
        if filters.doc_type and record.get("doc_type") != filters.doc_type:
            return False
        
        if filters.tags:
            record_tags = set(record.get("tags", []))
            if not any(tag in record_tags for tag in filters.tags):
                return False
        
        if filters.section:
            sections = record.get("sections", [])
            if not any(s.get("number") == filters.section for s in sections):
                return False
        
        if filters.date_from:
            effective_date = record.get("effective_date", "")
            if effective_date and effective_date < filters.date_from:
                return False
        
        if filters.date_to:
            effective_date = record.get("effective_date", "")
            if effective_date and effective_date > filters.date_to:
                return False
        
        if filters.version is not None:
            if record.get("version") != filters.version:
                return False
        
        if filters.language and record.get("language") != filters.language:
            return False
        
        return True
    
    def _score_relevance(self, record: Dict[str, Any], query: str, filters: QueryFilter) -> float:
        """Score the relevance of a record to a query."""
        score = 0.0
        query_lower = query.lower()
        
        # Title match (highest weight)
        title = record.get("title", "").lower()
        if query_lower in title:
            score += 10.0
        elif any(word in title for word in query_lower.split()):
            score += 5.0
        
        # Tag match
        record_tags = [t.lower() for t in record.get("tags", [])]
        for word in query_lower.split():
            if word in record_tags:
                score += 3.0
        
        # Content match
        content = record.get("content", "").lower()[:5000]
        word_count = sum(1 for word in query_lower.split() if word in content)
        score += word_count * 0.5
        
        # Exact filter match bonus
        if filters.jurisdiction and record.get("jurisdiction") == filters.jurisdiction:
            score += 2.0
        if filters.doc_type and record.get("doc_type") == filters.doc_type:
            score += 2.0
        
        return score
    
    def get_by_jurisdiction(self, jurisdiction: str) -> List[Dict[str, Any]]:
        """Get all records for a jurisdiction."""
        return [r for r in self.records if r.get("jurisdiction") == jurisdiction]
    
    def get_by_type(self, doc_type: str) -> List[Dict[str, Any]]:
        """Get all records of a document type."""
        return [r for r in self.records if r.get("doc_type") == doc_type]
    
    def get_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get all records with a specific tag."""
        return [r for r in self.records if tag in r.get("tags", [])]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get query engine statistics."""
        jurisdictions = {}
        doc_types = {}
        for r in self.records:
            j = r.get("jurisdiction", "unknown")
            jurisdictions[j] = jurisdictions.get(j, 0) + 1
            dt = r.get("doc_type", "unknown")
            doc_types[dt] = doc_types.get(dt, 0) + 1
        
        return {
            "total_records": len(self.records),
            "jurisdictions": jurisdictions,
            "doc_types": doc_types,
        }


# Singleton
query_engine = StructuredQueryEngine()
