"""ChromaDB adapter for Data Lake vector embeddings storage.

Provides persistent vector storage for semantic search over
legal documents, governance policies, and verified sources.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    logger.warning("chromadb not installed — vector search unavailable")


@dataclass
class VectorDocument:
    """A document chunk with its vector embedding."""
    id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


DEFAULT_COLLECTION_NAME = "datalake_documents"
EMBEDDING_FUNCTION_NAME = "all-MiniLM-L6-v2"


class ChromaAdapter:
    """ChromaDB adapter for persistent vector storage.

    Manages document embeddings with metadata filtering,
    collection lifecycle, and batch operations.
    """

    def __init__(self, persist_directory: str = "data/chromadb"):
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None

    def connect(self) -> bool:
        """Initialize ChromaDB client and get/create the collection."""
        if not HAS_CHROMADB:
            logger.error("chromadb package is required")
            return False

        try:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=False,
                ),
            )
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=DEFAULT_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                f"ChromaDB connected at {self.persist_directory}, "
                f"collection '{DEFAULT_COLLECTION_NAME}' ready"
            )
            return True
        except Exception as e:
            logger.error(f"ChromaDB connection failed: {e}")
            self._client = None
            return False

    def disconnect(self):
        """Close ChromaDB connection (persists automatically)."""
        self._collection = None
        self._client = None
        logger.info("ChromaDB disconnected")

    def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
        embedding: Optional[List[float]] = None,
    ) -> Optional[str]:
        """Add a document chunk to the vector store.

        Args:
            text: The document text content.
            metadata: Optional metadata dict (jurisdiction, doc_type, tags, etc.).
            doc_id: Optional custom ID; auto-generated if not provided.
            embedding: Optional pre-computed embedding; auto-computed if not provided.

        Returns:
            The document ID if successful, None otherwise.
        """
        if not self._collection:
            logger.error("ChromaDB not connected")
            return None

        doc_id = doc_id or str(uuid.uuid4())
        metadata = metadata or {}

        try:
            self._collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id],
                embeddings=[embedding] if embedding else None,
            )
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document to ChromaDB: {e}")
            return None

    def add_documents(
        self,
        documents: List[VectorDocument],
    ) -> List[Optional[str]]:
        """Batch add multiple document chunks.

        Args:
            documents: List of VectorDocument objects.

        Returns:
            List of document IDs (None for failures).
        """
        if not self._collection:
            logger.error("ChromaDB not connected")
            return [None] * len(documents)

        results = []
        for doc in documents:
            result = self.add_document(
                text=doc.text,
                metadata=doc.metadata,
                doc_id=doc.id,
                embedding=doc.embedding,
            )
            results.append(result)
        return results

    def search(
        self,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        n_results: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents.

        Args:
            query_text: Text query (auto-embedded if no query_embedding).
            query_embedding: Pre-computed query embedding.
            n_results: Maximum number of results.
            filter_dict: Metadata filter (e.g., {"jurisdiction": "np"}).

        Returns:
            List of result dicts with id, text, metadata, and distance.
        """
        if not self._collection:
            logger.error("ChromaDB not connected")
            return []

        if not query_text and not query_embedding:
            logger.error("Either query_text or query_embedding required")
            return []

        try:
            kwargs = {
                "n_results": min(n_results, 100),
                "include": ["documents", "metadatas", "distances"],
            }

            if query_embedding:
                kwargs["query_embeddings"] = [query_embedding]
            else:
                kwargs["query_texts"] = [query_text]

            if filter_dict:
                kwargs["where"] = filter_dict

            results = self._collection.query(**kwargs)

            # Format results
            formatted = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    formatted.append({
                        "id": doc_id,
                        "text": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    })
            return formatted
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            return []

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the vector store."""
        if not self._collection:
            return False

        try:
            self._collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    def delete_by_filter(self, filter_dict: Dict[str, Any]) -> int:
        """Delete documents matching a metadata filter.

        Args:
            filter_dict: Metadata filter (e.g., {"jurisdiction": "np"}).

        Returns:
            Number of documents deleted.
        """
        if not self._collection:
            return 0

        try:
            # Get matching IDs first
            results = self._collection.get(where=filter_dict)
            if results and results["ids"]:
                self._collection.delete(ids=results["ids"])
                return len(results["ids"])
            return 0
        except Exception as e:
            logger.error(f"Failed to delete by filter: {e}")
            return 0

    def count(self) -> int:
        """Get total document count in the collection."""
        if not self._collection:
            return 0

        try:
            return self._collection.count()
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a single document by ID."""
        if not self._collection:
            return None

        try:
            results = self._collection.get(ids=[doc_id])
            if results and results["ids"]:
                return {
                    "id": results["ids"][0],
                    "text": results["documents"][0] if results["documents"] else "",
                    "metadata": results["metadatas"][0] if results["metadatas"] else {},
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None

    def list_collections(self) -> List[str]:
        """List all available collections."""
        if not self._client:
            return []

        try:
            collections = self._client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        if not self._collection:
            return {"connected": False}

        try:
            count = self._collection.count()
            # Sample metadata to show jurisdiction distribution
            all_metadatas = self._collection.get(limit=min(count, 1000))
            jurisdictions = {}
            if all_metadatas and all_metadatas["metadatas"]:
                for m in all_metadatas["metadatas"]:
                    if m and "jurisdiction" in m:
                        j = m["jurisdiction"]
                        jurisdictions[j] = jurisdictions.get(j, 0) + 1

            return {
                "connected": True,
                "document_count": count,
                "collection_name": DEFAULT_COLLECTION_NAME,
                "persist_directory": self.persist_directory,
                "jurisdictions": jurisdictions,
            }
        except Exception as e:
            logger.error(f"Failed to get ChromaDB stats: {e}")
            return {"connected": True, "error": str(e)}
