#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade dataset builder
ASIMNEXUS Dataset Builder
=========================
Dataset builder for learning pipeline.
Captures feedback, cleans data, labels samples, creates snapshots.
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
import re

logger = logging.getLogger("AsimNexus.DatasetBuilder")


class DatasetType(Enum):
    """Types of datasets."""
    CHAT = "chat"
    INSTRUCTION = "instruction"
    PREFERENCE = "preference"
    SAFETY = "safety"
    CODE = "code"


class LabelType(Enum):
    """Types of labels."""
    QUALITY = "quality"  # 1-5 rating
    CORRECTNESS = "correctness"  # binary
    SAFETY = "safety"  # safe/unsafe
    HELPFULNESS = "helpfulness"  # 1-5 rating
    CUSTOM = "custom"


class DataQuality(Enum):
    """Data quality levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class DataSample:
    """Single data sample."""
    id: str
    input_text: str
    output_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    quality: DataQuality = DataQuality.UNKNOWN
    labels: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "input_text": self.input_text,
            "output_text": self.output_text,
            "metadata": self.metadata,
            "source": self.source,
            "timestamp": self.timestamp,
            "quality": self.quality.value,
            "labels": self.labels
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSample':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            input_text=data["input_text"],
            output_text=data.get("output_text"),
            metadata=data.get("metadata", {}),
            source=data.get("source", "unknown"),
            timestamp=data.get("timestamp"),
            quality=DataQuality(data.get("quality", "unknown")),
            labels=data.get("labels", {})
        )


@dataclass
class DatasetSnapshot:
    """Versioned dataset snapshot."""
    snapshot_id: str
    dataset_type: DatasetType
    samples: List[DataSample]
    version: int
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    parent_snapshot_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "dataset_type": self.dataset_type.value,
            "samples": [s.to_dict() for s in self.samples],
            "version": self.version,
            "created_at": self.created_at,
            "parent_snapshot_id": self.parent_snapshot_id,
            "metadata": self.metadata,
            "stats": self.stats
        }


class DatasetBuilder:
    """
    Dataset builder for learning pipeline.
    Captures feedback, cleans data, labels samples, creates snapshots.
    """
    
    def __init__(self, db_path: str = "data/dataset_builder.db"):
        self.db_path = db_path
        self.snapshots: Dict[str, DatasetSnapshot] = {}
        self.current_samples: List[DataSample] = []
        
        self._init_db()
        self._load_snapshots()
        
        logger.info(f"📦 DatasetBuilder initialized with {len(self.snapshots)} snapshots")
    
    def _init_db(self):
        """Initialize database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Snapshots table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    dataset_type TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    parent_snapshot_id TEXT,
                    metadata TEXT,
                    stats TEXT,
                    sample_count INTEGER NOT NULL
                )
            """)
            
            # Samples table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS samples (
                    id TEXT PRIMARY KEY,
                    snapshot_id TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    output_text TEXT,
                    metadata TEXT,
                    source TEXT,
                    timestamp TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    labels TEXT,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
                )
            """)
            
            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_samples_snapshot ON samples(snapshot_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_samples_quality ON samples(quality)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_type ON snapshots(dataset_type)")
            
            conn.commit()
    
    def _load_snapshots(self):
        """Load snapshots from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM snapshots ORDER BY version DESC").fetchall()
            
            for row in rows:
                # Load samples for this snapshot
                sample_rows = conn.execute(
                    "SELECT * FROM samples WHERE snapshot_id=?",
                    (row['snapshot_id'],)
                ).fetchall()
                
                samples = []
                for srow in sample_rows:
                    sample = DataSample(
                        id=srow['id'],
                        input_text=srow['input_text'],
                        output_text=srow['output_text'],
                        metadata=json.loads(srow['metadata']) if srow['metadata'] else {},
                        source=srow['source'],
                        timestamp=srow['timestamp'],
                        quality=DataQuality(srow['quality']),
                        labels=json.loads(srow['labels']) if srow['labels'] else {}
                    )
                    samples.append(sample)
                
                snapshot = DatasetSnapshot(
                    snapshot_id=row['snapshot_id'],
                    dataset_type=DatasetType(row['dataset_type']),
                    samples=samples,
                    version=row['version'],
                    created_at=row['created_at'],
                    parent_snapshot_id=row['parent_snapshot_id'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    stats=json.loads(row['stats']) if row['stats'] else {}
                )
                self.snapshots[snapshot.snapshot_id] = snapshot
    
    def capture_sample(self, input_text: str, output_text: Optional[str] = None,
                      source: str = "manual", metadata: Optional[Dict[str, Any]] = None) -> DataSample:
        """
        Capture a data sample from feedback.
        Returns the captured sample.
        """
        sample_id = hashlib.sha256(f"{input_text}{output_text}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        sample = DataSample(
            id=sample_id,
            input_text=input_text,
            output_text=output_text,
            source=source,
            metadata=metadata or {}
        )
        
        self.current_samples.append(sample)
        logger.debug(f"📦 Captured sample: {sample_id}")
        return sample
    
    def clean_sample(self, sample: DataSample) -> DataSample:
        """
        Clean a data sample.
        Removes PII, normalizes text, filters low-quality content.
        """
        cleaned_input = self._clean_text(sample.input_text)
        cleaned_output = self._clean_text(sample.output_text) if sample.output_text else None
        
        # Check quality
        quality = self._assess_quality(cleaned_input, cleaned_output)
        
        sample.input_text = cleaned_input
        sample.output_text = cleaned_output
        sample.quality = quality
        
        return sample
    
    def _clean_text(self, text: Optional[str]) -> str:
        """Clean text by removing PII and normalizing."""
        if not text:
            return ""
        
        # Remove common PII patterns (basic implementation)
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        # Phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        # SSN-like patterns
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _assess_quality(self, input_text: str, output_text: Optional[str] = None) -> DataQuality:
        """Assess quality of a sample."""
        if not input_text or len(input_text.strip()) < 10:
            return DataQuality.LOW
        
        if output_text and len(output_text.strip()) < 5:
            return DataQuality.LOW
        
        # Check for meaningful content
        if input_text.count('?') > 5 or input_text.count('!') > 5:
            return DataQuality.LOW
        
        return DataQuality.MEDIUM
    
    def label_sample(self, sample: DataSample, label_type: LabelType, value: Any) -> DataSample:
        """
        Label a data sample.
        Returns the labeled sample.
        """
        sample.labels[label_type.value] = value
        logger.debug(f"📦 Labeled sample {sample.id}: {label_type.value}={value}")
        return sample
    
    def create_snapshot(self, dataset_type: DatasetType, 
                       samples: Optional[List[DataSample]] = None,
                       parent_snapshot_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> DatasetSnapshot:
        """
        Create a versioned dataset snapshot.
        Returns the snapshot.
        """
        # Use provided samples or current samples
        snapshot_samples = samples or self.current_samples.copy()
        
        # Clean all samples
        cleaned_samples = [self.clean_sample(s) for s in snapshot_samples]
        
        # Filter by quality
        filtered_samples = [s for s in cleaned_samples if s.quality != DataQuality.LOW]
        
        # Generate snapshot ID
        snapshot_id = hashlib.sha256(f"{dataset_type.value}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        # Get next version
        version = 1
        if parent_snapshot_id and parent_snapshot_id in self.snapshots:
            version = self.snapshots[parent_snapshot_id].version + 1
        elif self.snapshots:
            version = max(s.version for s in self.snapshots.values()) + 1
        
        # Calculate stats
        stats = self._calculate_stats(filtered_samples)
        
        snapshot = DatasetSnapshot(
            snapshot_id=snapshot_id,
            dataset_type=dataset_type,
            samples=filtered_samples,
            version=version,
            parent_snapshot_id=parent_snapshot_id,
            metadata=metadata or {},
            stats=stats
        )
        
        # Persist to database
        self._persist_snapshot(snapshot)
        
        # Clear current samples
        self.current_samples = []
        
        logger.info(f"📦 Created snapshot {snapshot_id} (v{version}) with {len(filtered_samples)} samples")
        return snapshot
    
    def _calculate_stats(self, samples: List[DataSample]) -> Dict[str, Any]:
        """Calculate statistics for a dataset."""
        if not samples:
            return {"sample_count": 0}
        
        quality_counts = {}
        for quality in DataQuality:
            quality_counts[quality.value] = len([s for s in samples if s.quality == quality])
        
        avg_input_length = sum(len(s.input_text) for s in samples) / len(samples)
        avg_output_length = sum(len(s.output_text or "") for s in samples) / len(samples)
        
        return {
            "sample_count": len(samples),
            "quality_distribution": quality_counts,
            "avg_input_length": avg_input_length,
            "avg_output_length": avg_output_length,
            "sources": list(set(s.source for s in samples))
        }
    
    def _persist_snapshot(self, snapshot: DatasetSnapshot):
        """Persist snapshot to database."""
        with sqlite3.connect(self.db_path) as conn:
            # Insert snapshot
            conn.execute("""
                INSERT OR REPLACE INTO snapshots (snapshot_id, dataset_type, version, created_at, parent_snapshot_id, metadata, stats, sample_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.snapshot_id,
                snapshot.dataset_type.value,
                snapshot.version,
                snapshot.created_at,
                snapshot.parent_snapshot_id,
                json.dumps(snapshot.metadata),
                json.dumps(snapshot.stats),
                len(snapshot.samples)
            ))
            
            # Insert samples
            for sample in snapshot.samples:
                conn.execute("""
                    INSERT OR REPLACE INTO samples (id, snapshot_id, input_text, output_text, metadata, source, timestamp, quality, labels)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sample.id,
                    snapshot.snapshot_id,
                    sample.input_text,
                    sample.output_text,
                    json.dumps(sample.metadata),
                    sample.source,
                    sample.timestamp,
                    sample.quality.value,
                    json.dumps(sample.labels)
                ))
            
            conn.commit()
        
        # Add to in-memory cache
        self.snapshots[snapshot.snapshot_id] = snapshot
    
    def get_snapshot(self, snapshot_id: str) -> Optional[DatasetSnapshot]:
        """Get a snapshot by ID."""
        return self.snapshots.get(snapshot_id)
    
    def get_latest_snapshot(self, dataset_type: Optional[DatasetType] = None) -> Optional[DatasetSnapshot]:
        """Get the latest snapshot, optionally filtered by type."""
        snapshots = list(self.snapshots.values())
        
        if dataset_type:
            snapshots = [s for s in snapshots if s.dataset_type == dataset_type]
        
        if not snapshots:
            return None
        
        return max(snapshots, key=lambda s: s.version)
    
    def get_snapshots(self, dataset_type: Optional[DatasetType] = None) -> List[DatasetSnapshot]:
        """Get all snapshots, optionally filtered by type."""
        snapshots = list(self.snapshots.values())
        
        if dataset_type:
            snapshots = [s for s in snapshots if s.dataset_type == dataset_type]
        
        return sorted(snapshots, key=lambda s: s.version, reverse=True)
    
    def export_snapshot(self, snapshot_id: str, format: str = "jsonl") -> str:
        """
        Export a snapshot to a file.
        Returns the file path.
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        output_dir = Path("data/datasets")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{snapshot_id}.{format}"
        
        if format == "jsonl":
            with open(output_path, 'w', encoding='utf-8') as f:
                for sample in snapshot.samples:
                    f.write(json.dumps(sample.to_dict()) + '\n')
        elif format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot.to_dict(), f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"📦 Exported snapshot {snapshot_id} to {output_path}")
        return str(output_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dataset builder statistics."""
        total_samples = sum(len(s.samples) for s in self.snapshots.values())
        
        by_type = {}
        for dtype in DatasetType:
            snapshots = self.get_snapshots(dtype)
            by_type[dtype.value] = {
                "snapshot_count": len(snapshots),
                "total_samples": sum(len(s.samples) for s in snapshots)
            }
        
        return {
            "total_snapshots": len(self.snapshots),
            "total_samples": total_samples,
            "current_samples": len(self.current_samples),
            "by_type": by_type
        }


# Global dataset builder instance
_dataset_builder: Optional[DatasetBuilder] = None


def get_dataset_builder(db_path: str = "data/dataset_builder.db") -> DatasetBuilder:
    """Get or create global dataset builder instance."""
    global _dataset_builder
    if _dataset_builder is None:
        _dataset_builder = DatasetBuilder(db_path)
    return _dataset_builder


def reset_dataset_builder():
    """Reset global dataset builder instance (for testing)."""
    global _dataset_builder
    _dataset_builder = None
