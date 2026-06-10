#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade adapter registry
ASIMNEXUS Adapter Registry
===========================
Adapter registry for version management.
Tracks adapter versions, promotions, and rollback history.
"""

import logging
import sqlite3
import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger("AsimNexus.AdapterRegistry")


class AdapterStatus(Enum):
    """Adapter statuses."""
    DRAFT = "draft"
    TRAINING = "training"
    EVALUATING = "evaluating"
    READY = "ready"
    PROMOTED = "promoted"
    DEPRECATED = "deprecated"
    ROLLED_BACK = "rolled_back"


class PromotionStage(Enum):
    """Promotion stages."""
    STAGING = "staging"
    CANARY = "canary"
    PRODUCTION = "production"


@dataclass
class AdapterVersion:
    """Adapter version information."""
    adapter_id: str
    version: int
    base_model_id: str
    training_job_id: str
    status: AdapterStatus = AdapterStatus.DRAFT
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    promoted_at: Optional[str] = None
    promotion_stage: Optional[PromotionStage] = None
    adapter_path: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    evaluation_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "adapter_id": self.adapter_id,
            "version": self.version,
            "base_model_id": self.base_model_id,
            "training_job_id": self.training_job_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "promoted_at": self.promoted_at,
            "promotion_stage": self.promotion_stage.value if self.promotion_stage else None,
            "adapter_path": self.adapter_path,
            "metrics": self.metrics,
            "evaluation_ids": self.evaluation_ids,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdapterVersion':
        """Create from dictionary."""
        return cls(
            adapter_id=data["adapter_id"],
            version=data["version"],
            base_model_id=data["base_model_id"],
            training_job_id=data["training_job_id"],
            status=AdapterStatus(data["status"]),
            created_at=data["created_at"],
            promoted_at=data.get("promoted_at"),
            promotion_stage=PromotionStage(data["promotion_stage"]) if data.get("promotion_stage") else None,
            adapter_path=data.get("adapter_path"),
            metrics=data.get("metrics", {}),
            evaluation_ids=data.get("evaluation_ids", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class RollbackEvent:
    """Rollback event."""
    event_id: str
    adapter_id: str
    from_version: int
    to_version: int
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdapterRegistry:
    """
    Adapter registry for version management.
    Tracks adapter versions, promotions, and rollback history.
    """
    
    def __init__(self, db_path: str = "data/adapter_registry.db"):
        self.db_path = db_path
        self.adapters: Dict[str, List[AdapterVersion]] = {}  # adapter_id -> list of versions
        self.rollback_events: List[RollbackEvent] = []
        
        self._init_db()
        self._load_adapters()
        self._load_rollback_events()
        
        logger.info(f"📦 AdapterRegistry initialized with {len(self.adapters)} adapters")
    
    def _init_db(self):
        """Initialize database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Adapters table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS adapters (
                    adapter_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    base_model_id TEXT NOT NULL,
                    training_job_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    promoted_at TEXT,
                    promotion_stage TEXT,
                    adapter_path TEXT,
                    metrics TEXT,
                    evaluation_ids TEXT,
                    metadata TEXT,
                    PRIMARY KEY (adapter_id, version)
                )
            """)
            
            # Rollback events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rollback_events (
                    event_id TEXT PRIMARY KEY,
                    adapter_id TEXT NOT NULL,
                    from_version INTEGER NOT NULL,
                    to_version INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_adapters_id ON adapters(adapter_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_adapters_status ON adapters(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rollback_adapter ON rollback_events(adapter_id)")
            
            conn.commit()
    
    def _load_adapters(self):
        """Load adapters from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM adapters ORDER BY adapter_id, version DESC").fetchall()
            
            for row in rows:
                adapter = AdapterVersion(
                    adapter_id=row['adapter_id'],
                    version=row['version'],
                    base_model_id=row['base_model_id'],
                    training_job_id=row['training_job_id'],
                    status=AdapterStatus(row['status']),
                    created_at=row['created_at'],
                    promoted_at=row['promoted_at'],
                    promotion_stage=PromotionStage(row['promotion_stage']) if row['promotion_stage'] else None,
                    adapter_path=row['adapter_path'],
                    metrics=json.loads(row['metrics']) if row['metrics'] else {},
                    evaluation_ids=json.loads(row['evaluation_ids']) if row['evaluation_ids'] else [],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                
                if adapter.adapter_id not in self.adapters:
                    self.adapters[adapter.adapter_id] = []
                self.adapters[adapter.adapter_id].append(adapter)
    
    def _load_rollback_events(self):
        """Load rollback events from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM rollback_events ORDER BY timestamp DESC").fetchall()
            
            for row in rows:
                event = RollbackEvent(
                    event_id=row['event_id'],
                    adapter_id=row['adapter_id'],
                    from_version=row['from_version'],
                    to_version=row['to_version'],
                    reason=row['reason'],
                    timestamp=row['timestamp'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                self.rollback_events.append(event)
    
    def register_adapter(self, base_model_id: str, training_job_id: str,
                         adapter_path: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> AdapterVersion:
        """
        Register a new adapter version.
        Returns the adapter version.
        """
        # Generate adapter ID from base model
        adapter_id = hashlib.sha256(base_model_id.encode()).hexdigest()[:16]
        
        # Get next version
        versions = self.adapters.get(adapter_id, [])
        next_version = 1
        if versions:
            next_version = max(v.version for v in versions) + 1
        
        adapter = AdapterVersion(
            adapter_id=adapter_id,
            version=next_version,
            base_model_id=base_model_id,
            training_job_id=training_job_id,
            adapter_path=adapter_path,
            metadata=metadata or {}
        )
        
        if adapter_id not in self.adapters:
            self.adapters[adapter_id] = []
        self.adapters[adapter_id].append(adapter)
        
        self._persist_adapter(adapter)
        
        logger.info(f"📦 Registered adapter: {adapter_id} v{next_version}")
        return adapter
    
    def _persist_adapter(self, adapter: AdapterVersion):
        """Persist adapter to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO adapters (adapter_id, version, base_model_id, training_job_id, status, created_at, promoted_at, promotion_stage, adapter_path, metrics, evaluation_ids, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                adapter.adapter_id,
                adapter.version,
                adapter.base_model_id,
                adapter.training_job_id,
                adapter.status.value,
                adapter.created_at,
                adapter.promoted_at,
                adapter.promotion_stage.value if adapter.promotion_stage else None,
                adapter.adapter_path,
                json.dumps(adapter.metrics),
                json.dumps(adapter.evaluation_ids),
                json.dumps(adapter.metadata)
            ))
            conn.commit()
    
    def update_adapter_status(self, adapter_id: str, version: int, status: AdapterStatus) -> bool:
        """
        Update adapter status.
        Returns True if successful.
        """
        versions = self.adapters.get(adapter_id, [])
        adapter = next((v for v in versions if v.version == version), None)
        
        if not adapter:
            logger.warning(f"Adapter {adapter_id} v{version} not found")
            return False
        
        adapter.status = status
        
        if status == AdapterStatus.PROMOTED:
            adapter.promoted_at = datetime.utcnow().isoformat()
        
        self._persist_adapter(adapter)
        
        logger.info(f"📦 Updated adapter {adapter_id} v{version} status to {status.value}")
        return True
    
    def promote_adapter(self, adapter_id: str, version: int, stage: PromotionStage,
                      evaluation_ids: Optional[List[str]] = None) -> bool:
        """
        Promote an adapter to a stage.
        Returns True if successful.
        """
        versions = self.adapters.get(adapter_id, [])
        adapter = next((v for v in versions if v.version == version), None)
        
        if not adapter:
            logger.warning(f"Adapter {adapter_id} v{version} not found")
            return False
        
        adapter.status = AdapterStatus.PROMOTED
        adapter.promotion_stage = stage
        adapter.promoted_at = datetime.utcnow().isoformat()
        
        if evaluation_ids:
            adapter.evaluation_ids = evaluation_ids
        
        self._persist_adapter(adapter)
        
        logger.info(f"📦 Promoted adapter {adapter_id} v{version} to {stage.value}")
        return True
    
    def rollback_adapter(self, adapter_id: str, from_version: int, to_version: int, reason: str) -> bool:
        """
        Rollback an adapter to a previous version.
        Returns True if successful.
        """
        versions = self.adapters.get(adapter_id, [])
        from_adapter = next((v for v in versions if v.version == from_version), None)
        to_adapter = next((v for v in versions if v.version == to_version), None)
        
        if not from_adapter or not to_adapter:
            logger.warning(f"Adapter versions not found for rollback")
            return False
        
        # Update statuses
        from_adapter.status = AdapterStatus.ROLLED_BACK
        to_adapter.status = AdapterStatus.PROMOTED
        to_adapter.promotion_stage = PromotionStage.PRODUCTION
        to_adapter.promoted_at = datetime.utcnow().isoformat()
        
        # Record rollback event
        event_id = hashlib.sha256(f"{adapter_id}{from_version}{to_version}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        event = RollbackEvent(
            event_id=event_id,
            adapter_id=adapter_id,
            from_version=from_version,
            to_version=to_version,
            reason=reason
        )
        self.rollback_events.append(event)
        self._persist_rollback_event(event)
        
        # Persist adapter changes
        self._persist_adapter(from_adapter)
        self._persist_adapter(to_adapter)
        
        logger.info(f"📦 Rolled back adapter {adapter_id} from v{from_version} to v{to_version}")
        return True
    
    def _persist_rollback_event(self, event: RollbackEvent):
        """Persist rollback event to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO rollback_events (event_id, adapter_id, from_version, to_version, reason, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.adapter_id,
                event.from_version,
                event.to_version,
                event.reason,
                event.timestamp,
                json.dumps(event.metadata)
            ))
            conn.commit()
    
    def get_adapter(self, adapter_id: str, version: Optional[int] = None) -> Optional[AdapterVersion]:
        """Get an adapter by ID and version."""
        versions = self.adapters.get(adapter_id, [])
        
        if version:
            return next((v for v in versions if v.version == version), None)
        
        # Return latest version
        if versions:
            return max(versions, key=lambda v: v.version)
        
        return None
    
    def get_adapter_versions(self, adapter_id: str) -> List[AdapterVersion]:
        """Get all versions of an adapter."""
        versions = self.adapters.get(adapter_id, [])
        return sorted(versions, key=lambda v: v.version, reverse=True)
    
    def get_adapters(self, status: Optional[AdapterStatus] = None,
                    promotion_stage: Optional[PromotionStage] = None) -> List[AdapterVersion]:
        """Get adapters, optionally filtered."""
        all_adapters = []
        for versions in self.adapters.values():
            all_adapters.extend(versions)
        
        if status:
            all_adapters = [a for a in all_adapters if a.status == status]
        
        if promotion_stage:
            all_adapters = [a for a in all_adapters if a.promotion_stage == promotion_stage]
        
        return sorted(all_adapters, key=lambda a: a.created_at, reverse=True)
    
    def get_production_adapter(self, adapter_id: str) -> Optional[AdapterVersion]:
        """Get the production adapter for an adapter ID."""
        versions = self.adapters.get(adapter_id, [])
        production = next(
            (v for v in versions if v.status == AdapterStatus.PROMOTED and v.promotion_stage == PromotionStage.PRODUCTION),
            None
        )
        return production
    
    def add_evaluation(self, adapter_id: str, version: int, evaluation_id: str) -> bool:
        """Add an evaluation ID to an adapter."""
        versions = self.adapters.get(adapter_id, [])
        adapter = next((v for v in versions if v.version == version), None)
        
        if not adapter:
            return False
        
        if evaluation_id not in adapter.evaluation_ids:
            adapter.evaluation_ids.append(evaluation_id)
            self._persist_adapter(adapter)
        
        return True
    
    def update_metrics(self, adapter_id: str, version: int, metrics: Dict[str, Any]) -> bool:
        """Update metrics for an adapter."""
        versions = self.adapters.get(adapter_id, [])
        adapter = next((v for v in versions if v.version == version), None)
        
        if not adapter:
            return False
        
        adapter.metrics.update(metrics)
        self._persist_adapter(adapter)
        
        return True
    
    def get_rollback_history(self, adapter_id: Optional[str] = None) -> List[RollbackEvent]:
        """Get rollback history, optionally filtered by adapter."""
        events = self.rollback_events
        
        if adapter_id:
            events = [e for e in events if e.adapter_id == adapter_id]
        
        return sorted(events, key=lambda e: e.timestamp, reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter registry statistics."""
        total_adapters = len(self.adapters)
        total_versions = sum(len(v) for v in self.adapters.values())
        
        by_status = {}
        for status in AdapterStatus:
            by_status[status.value] = len([a for v in self.adapters.values() for a in v if a.status == status])
        
        by_stage = {}
        for stage in PromotionStage:
            by_stage[stage.value] = len([a for v in self.adapters.values() for a in v if a.promotion_stage == stage])
        
        return {
            "total_adapters": total_adapters,
            "total_versions": total_versions,
            "by_status": by_status,
            "by_stage": by_stage,
            "rollback_events": len(self.rollback_events)
        }


# Global adapter registry instance
_adapter_registry: Optional[AdapterRegistry] = None


def get_adapter_registry(db_path: str = "data/adapter_registry.db") -> AdapterRegistry:
    """Get or create global adapter registry instance."""
    global _adapter_registry
    if _adapter_registry is None:
        _adapter_registry = AdapterRegistry(db_path)
    return _adapter_registry


def reset_adapter_registry():
    """Reset global adapter registry instance (for testing)."""
    global _adapter_registry
    _adapter_registry = None
