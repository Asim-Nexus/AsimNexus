"""
AsimNexus Data Lake
===================
A verified, structured knowledge base for legal/public policy data.

The Data Lake provides:
- Ingestion: PDF/HTML → Text → Metadata → Structured JSON/XML
- Verification: Source verification, hash chains, version tracking
- Storage: PostgreSQL (structured), ChromaDB (vectors), JSONL (audit)
- Retrieval: Structured queries, semantic search, citation mapping

Core Principle: Every record has a source, timestamp, version, signer, hash, and jurisdiction.
"""

__version__ = "0.1.0"
