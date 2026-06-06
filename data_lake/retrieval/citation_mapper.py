"""
Data Lake: Citation Mapper
==========================
Maps citations between legal documents, enabling cross-referencing.

Features:
- Law → Amendment → Case citation chains
- Cross-jurisdiction citation mapping
- Version-aware citations
- Citation graph for relationship analysis
"""

import json
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("DataLake.CitationMapper")


@dataclass
class Citation:
    """A citation between two documents."""
    source_id: str
    target_id: str
    citation_type: str  # "amends", "references", "overrules", "implements"
    context: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "citation_type": self.citation_type,
            "context": self.context[:200],
            "timestamp": self.timestamp,
        }


@dataclass
class CitationGraph:
    """A graph of citations between documents."""
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    edges: List[Citation] = field(default_factory=list)


class CitationMapper:
    """
    Maps citations between legal documents.
    
    Usage:
        mapper = CitationMapper()
        
        # Add a citation
        mapper.add_citation("np-it-act-2079", "np-it-amendment-2080", "amends")
        
        # Get citation chain
        chain = mapper.get_citation_chain("np-it-act-2079")
        
        # Get related documents
        related = mapper.get_related_documents("np-it-act-2079")
    """
    
    def __init__(self, storage_path: str = "data/data_lake_citations.json"):
        self.storage_path = storage_path
        self.graph = CitationGraph()
        self._load()
    
    def _load(self):
        """Load citations from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.graph.nodes = data.get("nodes", {})
                    self.graph.edges = [Citation(**e) for e in data.get("edges", [])]
                logger.info(f"Loaded {len(self.graph.edges)} citations")
            except Exception as e:
                logger.warning(f"Failed to load citations: {e}")
    
    def _save(self):
        """Save citations to storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({
                    "nodes": self.graph.nodes,
                    "edges": [e.to_dict() for e in self.graph.edges],
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save citations: {e}")
    
    def add_node(self, node_id: str, metadata: Dict[str, Any] = None):
        """Add a document node to the citation graph."""
        if node_id not in self.graph.nodes:
            self.graph.nodes[node_id] = metadata or {}
            self._save()
    
    def add_citation(self, source_id: str, target_id: str,
                     citation_type: str, context: str = ""):
        """
        Add a citation between two documents.
        
        Args:
            source_id: The document that contains the citation
            target_id: The document being cited
            citation_type: Type of citation (amends, references, overrules, implements)
            context: The surrounding text context
        """
        # Ensure both nodes exist
        self.add_node(source_id)
        self.add_node(target_id)
        
        citation = Citation(
            source_id=source_id,
            target_id=target_id,
            citation_type=citation_type,
            context=context,
        )
        
        self.graph.edges.append(citation)
        self._save()
        
        logger.info(f"Added citation: {source_id} {citation_type} {target_id}")
    
    def get_citation_chain(self, doc_id: str, max_depth: int = 5) -> List[List[Citation]]:
        """
        Get the citation chain for a document (both directions).
        
        Returns:
            List of citation chains (forward and backward)
        """
        chains = []
        
        # Forward chain (doc → amendments → amendments of amendments)
        forward = self._traverse_forward(doc_id, set(), max_depth)
        if forward:
            chains.append(forward)
        
        # Backward chain (doc → original law → amendments of original)
        backward = self._traverse_backward(doc_id, set(), max_depth)
        if backward:
            chains.append(backward)
        
        return chains
    
    def _traverse_forward(self, doc_id: str, visited: Set[str],
                          max_depth: int, depth: int = 0) -> List[Citation]:
        """Traverse forward citations (what this doc cites)."""
        if depth >= max_depth or doc_id in visited:
            return []
        
        visited.add(doc_id)
        chain = []
        
        for edge in self.graph.edges:
            if edge.source_id == doc_id and edge.target_id not in visited:
                chain.append(edge)
                chain.extend(self._traverse_forward(
                    edge.target_id, visited, max_depth, depth + 1))
        
        return chain
    
    def _traverse_backward(self, doc_id: str, visited: Set[str],
                           max_depth: int, depth: int = 0) -> List[Citation]:
        """Traverse backward citations (what cites this doc)."""
        if depth >= max_depth or doc_id in visited:
            return []
        
        visited.add(doc_id)
        chain = []
        
        for edge in self.graph.edges:
            if edge.target_id == doc_id and edge.source_id not in visited:
                chain.append(edge)
                chain.extend(self._traverse_backward(
                    edge.source_id, visited, max_depth, depth + 1))
        
        return chain
    
    def get_related_documents(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all documents related to a given document."""
        related = set()
        
        for edge in self.graph.edges:
            if edge.source_id == doc_id:
                related.add(edge.target_id)
            if edge.target_id == doc_id:
                related.add(edge.source_id)
        
        return [
            {"id": rid, "metadata": self.graph.nodes.get(rid, {})}
            for rid in sorted(related)
        ]
    
    def get_citation_stats(self) -> Dict[str, Any]:
        """Get citation statistics."""
        citation_types = defaultdict(int)
        for edge in self.graph.edges:
            citation_types[edge.citation_type] += 1
        
        return {
            "total_documents": len(self.graph.nodes),
            "total_citations": len(self.graph.edges),
            "citation_types": dict(citation_types),
            "most_cited": self._get_most_cited(5),
        }
    
    def _get_most_cited(self, n: int) -> List[Dict[str, Any]]:
        """Get the most cited documents."""
        citation_count = defaultdict(int)
        for edge in self.graph.edges:
            citation_count[edge.target_id] += 1
        
        sorted_docs = sorted(citation_count.items(), key=lambda x: x[1], reverse=True)
        return [
            {"doc_id": doc_id, "citation_count": count, "metadata": self.graph.nodes.get(doc_id, {})}
            for doc_id, count in sorted_docs[:n]
        ]


# Singleton
citation_mapper = CitationMapper()
