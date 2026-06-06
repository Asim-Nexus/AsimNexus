"""PostgreSQL adapter for Data Lake document persistence.

Stores tagged documents, verification results, and citation graphs
in a relational schema optimized for legal/governance document retrieval.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    logger.warning("asyncpg not installed — PostgreSQL adapter unavailable")


@dataclass
class StorageConfig:
    """PostgreSQL connection configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "asimnexus_datalake"
    user: str = "asimnexus"
    password: str = ""
    min_connections: int = 2
    max_connections: int = 10


SCHEMA_SQL = """
-- Data Lake document storage schema
CREATE TABLE IF NOT EXISTS documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_hash     VARCHAR(64) NOT NULL UNIQUE,
    title           TEXT,
    doc_type        VARCHAR(50),
    jurisdiction    VARCHAR(10),
    language        VARCHAR(10),
    content_text    TEXT,
    metadata_json   JSONB DEFAULT '{}',
    tags            TEXT[] DEFAULT '{}',
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_verifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID REFERENCES documents(id) ON DELETE CASCADE,
    trust_score     REAL DEFAULT 0.0,
    source_url      TEXT,
    source_type     VARCHAR(50),
    chain_verified  BOOLEAN DEFAULT FALSE,
    warnings        TEXT[] DEFAULT '{}',
    verified_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_embeddings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER DEFAULT 0,
    chunk_text      TEXT,
    embedding       REAL[],
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS citations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_doc_id   UUID REFERENCES documents(id) ON DELETE CASCADE,
    target_doc_id   UUID REFERENCES documents(id) ON DELETE CASCADE,
    citation_type   VARCHAR(50) DEFAULT 'references',
    context         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON documents(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN(metadata_json);
CREATE INDEX IF NOT EXISTS idx_citations_source ON citations(source_doc_id);
CREATE INDEX IF NOT EXISTS idx_citations_target ON citations(target_doc_id);
"""


class PostgresAdapter:
    """Async PostgreSQL adapter for Data Lake document storage.

    Provides CRUD operations for documents, verifications, embeddings,
    and citations with connection pooling.
    """

    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> bool:
        """Initialize connection pool and create schema."""
        if not HAS_ASYNCPG:
            logger.error("asyncpg is required for PostgreSQL adapter")
            return False

        try:
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
            )
            # Create schema
            async with self._pool.acquire() as conn:
                await conn.execute(SCHEMA_SQL)
            logger.info("PostgreSQL adapter connected and schema initialized")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            self._pool = None
            return False

    async def disconnect(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def store_document(self, doc_data: Dict[str, Any]) -> Optional[str]:
        """Store a document and return its ID."""
        if not self._pool:
            logger.error("PostgreSQL not connected")
            return None

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO documents (source_hash, title, doc_type, jurisdiction,
                                           language, content_text, metadata_json, tags)
                    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::text[])
                    ON CONFLICT (source_hash)
                    DO UPDATE SET updated_at = NOW()
                    RETURNING id
                    """,
                    doc_data.get("source_hash"),
                    doc_data.get("title"),
                    doc_data.get("doc_type"),
                    doc_data.get("jurisdiction"),
                    doc_data.get("language"),
                    doc_data.get("content_text"),
                    json.dumps(doc_data.get("metadata", {})),
                    doc_data.get("tags", []),
                )
                return str(row["id"]) if row else None
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            return None

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID."""
        if not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM documents WHERE id = $1::uuid", doc_id
                )
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None

    async def search_documents(
        self,
        jurisdiction: Optional[str] = None,
        doc_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        query_text: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search documents with filters."""
        if not self._pool:
            return []

        conditions = []
        params = []
        param_idx = 1

        if jurisdiction:
            conditions.append(f"jurisdiction = ${param_idx}")
            params.append(jurisdiction)
            param_idx += 1

        if doc_type:
            conditions.append(f"doc_type = ${param_idx}")
            params.append(doc_type)
            param_idx += 1

        if tags:
            conditions.append(f"tags && ${param_idx}::text[]")
            params.append(tags)
            param_idx += 1

        if query_text:
            conditions.append(
                f"content_text ILIKE ${param_idx} || '%'"
            )
            params.append(query_text)
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT id, title, doc_type, jurisdiction, language,
                           metadata_json, tags, ingested_at
                    FROM documents
                    WHERE {where_clause}
                    ORDER BY ingested_at DESC
                    LIMIT ${param_idx} OFFSET ${param_idx + 1}
                    """,
                    *params,
                    limit,
                    offset,
                )
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []

    async def store_verification(
        self, document_id: str, verification: Dict[str, Any]
    ) -> Optional[str]:
        """Store verification result for a document."""
        if not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO document_verifications
                        (document_id, trust_score, source_url, source_type,
                         chain_verified, warnings)
                    VALUES ($1::uuid, $2, $3, $4, $5, $6::text[])
                    RETURNING id
                    """,
                    document_id,
                    verification.get("trust_score", 0.0),
                    verification.get("source_url", ""),
                    verification.get("source_type", "unknown"),
                    verification.get("chain_verified", False),
                    verification.get("warnings", []),
                )
                return str(row["id"]) if row else None
        except Exception as e:
            logger.error(f"Failed to store verification: {e}")
            return None

    async def store_citation(
        self,
        source_doc_id: str,
        target_doc_id: str,
        citation_type: str = "references",
        context: Optional[str] = None,
    ) -> Optional[str]:
        """Store a citation relationship between documents."""
        if not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO citations (source_doc_id, target_doc_id,
                                           citation_type, context)
                    VALUES ($1::uuid, $2::uuid, $3, $4)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """,
                    source_doc_id,
                    target_doc_id,
                    citation_type,
                    context or "",
                )
                return str(row["id"]) if row else None
        except Exception as e:
            logger.error(f"Failed to store citation: {e}")
            return None

    async def get_citations(
        self, document_id: str, direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """Get citations for a document (outgoing, incoming, or both)."""
        if not self._pool:
            return []

        try:
            async with self._pool.acquire() as conn:
                if direction == "outgoing":
                    rows = await conn.fetch(
                        """
                        SELECT c.*, d.title as target_title
                        FROM citations c
                        JOIN documents d ON d.id = c.target_doc_id
                        WHERE c.source_doc_id = $1::uuid
                        """,
                        document_id,
                    )
                elif direction == "incoming":
                    rows = await conn.fetch(
                        """
                        SELECT c.*, d.title as source_title
                        FROM citations c
                        JOIN documents d ON d.id = c.source_doc_id
                        WHERE c.target_doc_id = $1::uuid
                        """,
                        document_id,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT c.*, sd.title as source_title, td.title as target_title
                        FROM citations c
                        JOIN documents sd ON sd.id = c.source_doc_id
                        JOIN documents td ON td.id = c.target_doc_id
                        WHERE c.source_doc_id = $1::uuid
                           OR c.target_doc_id = $1::uuid
                        """,
                        document_id,
                    )
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get citations: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        if not self._pool:
            return {"connected": False}

        try:
            async with self._pool.acquire() as conn:
                doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
                ver_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM document_verifications"
                )
                cit_count = await conn.fetchval("SELECT COUNT(*) FROM citations")
                jurisdictions = await conn.fetch(
                    "SELECT jurisdiction, COUNT(*) as cnt FROM documents "
                    "WHERE jurisdiction IS NOT NULL GROUP BY jurisdiction "
                    "ORDER BY cnt DESC LIMIT 10"
                )
                return {
                    "connected": True,
                    "document_count": doc_count or 0,
                    "verification_count": ver_count or 0,
                    "citation_count": cit_count or 0,
                    "jurisdictions": {
                        row["jurisdiction"]: row["cnt"]
                        for row in jurisdictions
                    },
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"connected": True, "error": str(e)}
