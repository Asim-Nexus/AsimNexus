#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade model registry
ASIMNEXUS Model Registry
========================
Model and adapter versioning with signatures and rollback support.
Ensures clean rollback paths for any model/adapter changes.
"""

import hashlib
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pydantic import BaseModel

logger = logging.getLogger("AsimNexus.Registry")


# Pydantic models for API requests
class RegisterModelRequest(BaseModel):
    """Request model for registering a model."""
    name: str
    version: str
    file_path: str
    created_by: Optional[str] = "system"
    metadata: Optional[Dict[str, Any]] = None


class RollbackRequest(BaseModel):
    """Request model for rollback."""
    target_version: Optional[str] = None


@dataclass
class ModelVersion:
    """Model/adapter version metadata."""
    id: str
    name: str
    version: str
    file_path: str
    file_hash: str
    signature: str
    created_at: str
    created_by: str
    metadata: Dict[str, Any]
    is_active: bool = True
    rollback_to: Optional[str] = None  # Pointer to previous version for rollback


class ModelRegistry:
    """
    Production-grade model registry with versioning, signatures, and rollback.
    Tracks all model/adapter changes with integrity verification.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logger
        self._init_db()

    def _init_db(self):
        """Initialize registry database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_registry (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    is_active INTEGER DEFAULT 1,
                    rollback_to TEXT,
                    UNIQUE(name, version)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_name ON model_registry(name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_active ON model_registry(is_active)
            """)
            conn.commit()
        self.logger.info("✅ Model registry database initialized")

    def register_model(
        self,
        name: str,
        version: str,
        file_path: str,
        created_by: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelVersion:
        """
        Register a new model/adapter version with hash and signature.
        Automatically handles rollback pointer to previous active version.
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Model file not found: {file_path}")

        # Calculate file hash (SHA-256)
        file_hash = self._calculate_file_hash(file_path_obj)

        # Generate signature (hash + metadata + timestamp)
        signature = self._generate_signature(file_hash, version, metadata)

        # Find previous active version for rollback pointer
        previous_active = self.get_active_model(name)

        # Create version ID
        version_id = hashlib.sha256(f"{name}:{version}:{file_hash}".encode()).hexdigest()[:32]

        # Deactivate previous version
        if previous_active:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE model_registry SET is_active = 0 WHERE id = ?",
                    (previous_active.id,)
                )
                conn.commit()

        # Insert new version
        model_version = ModelVersion(
            id=version_id,
            name=name,
            version=version,
            file_path=str(file_path_obj.absolute()),
            file_hash=file_hash,
            signature=signature,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            metadata=metadata or {},
            is_active=True,
            rollback_to=previous_active.id if previous_active else None
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO model_registry (
                    id, name, version, file_path, file_hash, signature,
                    created_at, created_by, metadata, is_active, rollback_to
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model_version.id,
                model_version.name,
                model_version.version,
                model_version.file_path,
                model_version.file_hash,
                model_version.signature,
                model_version.created_at,
                model_version.created_by,
                json.dumps(model_version.metadata),
                1 if model_version.is_active else 0,
                model_version.rollback_to
            ))
            conn.commit()

        self.logger.info(f"✅ Registered model: {name} v{version} (id: {version_id})")
        return model_version

    def get_active_model(self, name: str) -> Optional[ModelVersion]:
        """Get the currently active version of a model."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM model_registry WHERE name = ? AND is_active = 1",
                (name,)
            ).fetchone()

        if row:
            return self._row_to_model_version(row)
        return None

    def get_model(self, name: str, version: str) -> Optional[ModelVersion]:
        """Get a specific model version."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM model_registry WHERE name = ? AND version = ?",
                (name, version)
            ).fetchone()

        if row:
            return self._row_to_model_version(row)
        return None

    def list_versions(self, name: str) -> List[ModelVersion]:
        """List all versions of a model."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM model_registry WHERE name = ? ORDER BY created_at DESC",
                (name,)
            ).fetchall()

        return [self._row_to_model_version(row) for row in rows]

    def rollback(self, name: str, target_version: Optional[str] = None) -> Optional[ModelVersion]:
        """
        Rollback to a specific version or previous version.
        If target_version is None, rolls back to the version pointed by rollback_to.
        """
        current = self.get_active_model(name)
        if not current:
            raise ValueError(f"No active model found: {name}")

        # Determine target version
        if target_version:
            target = self.get_model(name, target_version)
            if not target:
                raise ValueError(f"Target version not found: {name} v{target_version}")
        else:
            # Rollback to previous version using rollback pointer
            if not current.rollback_to:
                raise ValueError(f"No rollback pointer available for {name}")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM model_registry WHERE id = ?",
                    (current.rollback_to,)
                ).fetchone()
            if row:
                target = self._row_to_model_version(row)
            else:
                raise ValueError(f"Rollback target not found: {current.rollback_to}")

        # Verify target file exists
        if not Path(target.file_path).exists():
            raise FileNotFoundError(f"Rollback target file not found: {target.file_path}")

        # Verify file integrity
        current_hash = self._calculate_file_hash(Path(target.file_path))
        if current_hash != target.file_hash:
            raise ValueError(f"File integrity check failed for rollback target")

        # Deactivate current
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE model_registry SET is_active = 0 WHERE id = ?",
                (current.id,)
            )

            # Activate target with new rollback pointer to current
            conn.execute(
                "UPDATE model_registry SET is_active = 1, rollback_to = ? WHERE id = ?",
                (current.id, target.id)
            )
            conn.commit()

        self.logger.info(f"✅ Rolled back {name} from v{current.version} to v{target.version}")

        # Re-fetch from database to get updated state
        return self.get_model(name, target.version)

    def verify_integrity(self, name: str, version: str) -> bool:
        """Verify model file integrity against stored hash."""
        model = self.get_model(name, version)
        if not model:
            return False

        file_path = Path(model.file_path)
        if not file_path.exists():
            return False

        current_hash = self._calculate_file_hash(file_path)
        return current_hash == model.file_hash

    def get_registry_status(self) -> Dict[str, Any]:
        """Get overall registry status."""
        with sqlite3.connect(self.db_path) as conn:
            # Count total models
            total = conn.execute("SELECT COUNT(*) FROM model_registry").fetchone()[0]

            # Count active models
            active = conn.execute("SELECT COUNT(*) FROM model_registry WHERE is_active = 1").fetchone()[0]

            # Get unique model names
            names = conn.execute("SELECT DISTINCT name FROM model_registry").fetchall()
            unique_names = [n[0] for n in names]

        return {
            "total_versions": total,
            "active_versions": active,
            "unique_models": len(unique_names),
            "models": unique_names,
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _generate_signature(self, file_hash: str, version: str, metadata: Optional[Dict]) -> str:
        """Generate signature from file hash, version, and metadata."""
        signature_data = f"{file_hash}:{version}:{json.dumps(metadata or {}, sort_keys=True)}"
        return hashlib.sha256(signature_data.encode()).hexdigest()

    def _row_to_model_version(self, row: sqlite3.Row) -> ModelVersion:
        """Convert database row to ModelVersion dataclass."""
        return ModelVersion(
            id=row["id"],
            name=row["name"],
            version=row["version"],
            file_path=row["file_path"],
            file_hash=row["file_hash"],
            signature=row["signature"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            metadata=json.loads(row["metadata"]),
            is_active=bool(row["is_active"]),
            rollback_to=row["rollback_to"]
        )


# Global registry instance
_model_registry: Optional[ModelRegistry] = None
_registry_db_path: Optional[str] = None


def get_model_registry(db_path: Optional[str] = None) -> ModelRegistry:
    """Get or create model registry instance."""
    global _model_registry, _registry_db_path
    if db_path is not None:
        _registry_db_path = db_path
        _model_registry = ModelRegistry(db_path)
    elif _model_registry is None:
        if _registry_db_path is None:
            raise ValueError("Registry db_path not set")
        _model_registry = ModelRegistry(_registry_db_path)
    return _model_registry


def reset_model_registry():
    """Reset the global model registry instance (for testing)."""
    global _model_registry, _registry_db_path
    _model_registry = None
    _registry_db_path = None


def setup_registry_routes(app, db_path: str):
    """
    Setup model registry API routes on FastAPI app.
    Call this from simple_backend.py to wire registry endpoints.
    """
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse

    # Initialize registry with the provided db_path
    get_model_registry(db_path)

    @app.post("/api/registry/register")
    async def register_model(req: RegisterModelRequest):
        """Register a new model/adapter version."""
        try:
            registry = get_model_registry()
            model = registry.register_model(
                name=req.name,
                version=req.version,
                file_path=req.file_path,
                created_by=req.created_by,
                metadata=req.metadata
            )
            return JSONResponse(asdict(model))
        except Exception as e:
            logger.error(f"Model registration error: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/registry/active/{name}")
    async def get_active_model(name: str):
        """Get currently active version of a model."""
        registry = get_model_registry()
        model = registry.get_active_model(name)
        if not model:
            raise HTTPException(status_code=404, detail=f"Active model not found: {name}")
        return JSONResponse(asdict(model))

    @app.get("/api/registry/versions/{name}")
    async def list_versions(name: str):
        """List all versions of a model."""
        try:
            registry = get_model_registry()
            versions = registry.list_versions(name)
            return JSONResponse([asdict(v) for v in versions])
        except Exception as e:
            logger.error(f"List versions error: {e}")
            return JSONResponse([])

    @app.get("/api/registry/{name}/{version}")
    async def get_model(name: str, version: str):
        """Get a specific model version."""
        registry = get_model_registry()
        model = registry.get_model(name, version)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {name} v{version}")
        return JSONResponse(asdict(model))

    @app.post("/api/registry/rollback/{name}")
    async def rollback_model(name: str, req: RollbackRequest):
        """Rollback to a specific or previous version."""
        try:
            registry = get_model_registry()
            model = registry.rollback(name, req.target_version)
            return JSONResponse(asdict(model))
        except Exception as e:
            logger.error(f"Rollback error: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/registry/verify/{name}/{version}")
    async def verify_integrity(name: str, version: str):
        """Verify model file integrity."""
        registry = get_model_registry()
        valid = registry.verify_integrity(name, version)
        return JSONResponse({"valid": valid})

    @app.get("/api/registry/status")
    async def get_registry_status():
        """Get overall registry status."""
        registry = get_model_registry()
        return JSONResponse(registry.get_registry_status())

    logger.info("✅ Model registry routes registered")
