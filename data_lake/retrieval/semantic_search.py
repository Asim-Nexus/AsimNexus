"""
Data Lake: Semantic Search
==========================
Vector-based semantic search for the Data Lake using ChromaDB.

Enables natural language queries like:
- "What is the tax rate for IT companies in Nepal?"
- "Show me all cyber crime laws in South Asia"
- "What are the labor law requirements for foreign workers?"
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("DataLake.SemanticSearch")


@dataclass
class SearchResult:
    """Result of a semantic search."""
    query: str
    results: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    search_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": self.results,
            "total_count": self.total_count,
            "search_time_ms": self.search_time_ms,
        }


class SemanticSearchEngine:
    """
    Vector-based semantic search using ChromaDB.
    
    Falls back to keyword search if ChromaDB is not available.
    """
    
    def __init__(self, collection_name: str = "data_lake_docs"):
        self.collection_name = collection_name
        self._collection = None
        self._chroma_client = None
        self._init_chromadb()
    
    def _init_chromadb(self):
        """Initialize ChromaDB client."""
        try:
            import chromadb
            self._chroma_client = chromadb.Client()
            try:
                self._collection = self._chroma_client.get_collection(self.collection_name)
            except Exception:
                self._collection = self._chroma_client.create_collection(self.collection_name)
            logger.info(f"Semantic search using ChromaDB collection: {self.collection_name}")
        except ImportError:
            logger.warning("ChromaDB not available, using keyword search fallback")
            self._chroma_client = None
    
    def index_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """
        Index a document for semantic search.
        
        Args:
            doc_id: Unique document identifier
            content: Document text content
            metadata: Optional metadata
        """
        if self._collection is None:
            logger.debug(f"ChromaDB not available, skipping index for {doc_id}")
            return
        
        try:
            self._collection.add(
                documents=[content],
                metadatas=[metadata or {}],
                ids=[doc_id],
            )
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
    
    def index_documents(self, documents: List[Tuple[str, str, Dict[str, Any]]]):
        """
        Index multiple documents.
        
        Args:
            documents: List of (doc_id, content, metadata) tuples
        """
        if self._collection is None:
            logger.debug("ChromaDB not available, skipping batch index")
            return
        
        try:
            ids = [d[0] for d in documents]
            contents = [d[1] for d in documents]
            metadatas = [d[2] for d in documents]
            
            self._collection.add(
                documents=contents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"Indexed {len(documents)} documents")
        except Exception as e:
            logger.error(f"Failed to batch index documents: {e}")
    
    def search(self, query: str, n_results: int = 10,
               filter_criteria: Dict[str, Any] = None) -> SearchResult:
        """
        Search for documents semantically similar to the query.
        
        Args:
            query: Natural language query
            n_results: Maximum number of results
            filter_criteria: Optional metadata filters
            
        Returns:
            SearchResult with matching documents
        """
        t0 = time.time()
        
        if self._collection is not None:
            result = self._vector_search(query, n_results, filter_criteria)
        else:
            result = self._keyword_search(query, n_results, filter_criteria)
        
        result.search_time_ms = (time.time() - t0) * 1000
        return result
    
    def _vector_search(self, query: str, n_results: int,
                       filter_criteria: Dict[str, Any] = None) -> SearchResult:
        """Search using ChromaDB vector similarity."""
        try:
            where = filter_criteria if filter_criteria else None
            
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
            )
            
            formatted_results = []
            if results["ids"]:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                    })
            
            return SearchResult(
                query=query,
                results=formatted_results,
                total_count=len(formatted_results),
                search_time_ms=0.0,
            )
        
        except Exception as e:
            logger.error(f"Vector search failed: {e}, falling back to keyword search")
            return self._keyword_search(query, n_results, filter_criteria)
    
    def _keyword_search(self, query: str, n_results: int,
                        filter_criteria: Dict[str, Any] = None) -> SearchResult:
        """Fallback keyword-based search."""
        # This is a simplified keyword search
        # In production, this would use the structured query engine
        from data_lake.retrieval.structured_query import query_engine
        
        result = query_engine.query(query, limit=n_results)
        
        return SearchResult(
            query=query,
            results=result.results,
            total_count=result.total_count,
            search_time_ms=0.0,
        )
    
    def delete_document(self, doc_id: str):
        """Delete a document from the index."""
        if self._collection is None:
            return
        try:
            self._collection.delete(ids=[doc_id])
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if self._collection is None:
            return {"status": "not_available", "reason": "ChromaDB not installed"}
        
        try:
            count = self._collection.count()
            return {
                "status": "available",
                "document_count": count,
                "collection_name": self.collection_name,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Singleton
semantic_search = SemanticSearchEngine()
