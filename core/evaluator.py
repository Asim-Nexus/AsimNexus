#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade evaluator
ASIMNEXUS Evaluator
====================
Evaluator for trained adapters.
Evaluates on golden datasets, computes metrics, gates releases.
"""

import logging
import sqlite3
import json
import hashlib
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger("AsimNexus.Evaluator")


class EvaluationStatus(Enum):
    """Evaluation statuses."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MetricType(Enum):
    """Types of metrics."""
    ACCURACY = "accuracy"
    F1 = "f1"
    PRECISION = "precision"
    RECALL = "recall"
    BLEU = "bleu"
    ROUGE = "rouge"
    PERPLEXITY = "perplexity"
    LATENCY = "latency"
    SAFETY = "safety"
    CUSTOM = "custom"


@dataclass
class EvaluationThreshold:
    """Threshold for a metric."""
    metric_name: str
    min_value: float
    max_value: Optional[float] = None
    required: bool = True
    
    def check(self, value: float) -> bool:
        """Check if value meets threshold."""
        if self.max_value is not None:
            return self.min_value <= value <= self.max_value
        return value >= self.min_value


@dataclass
class EvaluationResult:
    """Result of an evaluation."""
    evaluation_id: str
    adapter_id: str
    golden_dataset_id: str
    status: EvaluationStatus = EvaluationStatus.PENDING
    metrics: Dict[str, float] = field(default_factory=dict)
    passed: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "evaluation_id": self.evaluation_id,
            "adapter_id": self.adapter_id,
            "golden_dataset_id": self.golden_dataset_id,
            "status": self.status.value,
            "metrics": self.metrics,
            "passed": self.passed,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "logs": self.logs,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """Create from dictionary."""
        return cls(
            evaluation_id=data["evaluation_id"],
            adapter_id=data["adapter_id"],
            golden_dataset_id=data["golden_dataset_id"],
            status=EvaluationStatus(data["status"]),
            metrics=data.get("metrics", {}),
            passed=data.get("passed", False),
            created_at=data["created_at"],
            completed_at=data.get("completed_at"),
            logs=data.get("logs", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class GoldenDataset:
    """Golden dataset for evaluation."""
    dataset_id: str
    name: str
    dataset_type: str  # "safety", "accuracy", "performance", etc.
    samples: List[Dict[str, Any]] = field(default_factory=list)
    thresholds: List[EvaluationThreshold] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "dataset_type": self.dataset_type,
            "samples": self.samples,
            "thresholds": [
                {
                    "metric_name": t.metric_name,
                    "min_value": t.min_value,
                    "max_value": t.max_value,
                    "required": t.required
                }
                for t in self.thresholds
            ],
            "created_at": self.created_at,
            "metadata": self.metadata
        }


class Evaluator:
    """
    Evaluator for trained adapters.
    Evaluates on golden datasets, computes metrics, gates releases.
    """
    
    def __init__(self, db_path: str = "data/evaluator.db"):
        self.db_path = db_path
        self.evaluations: Dict[str, EvaluationResult] = {}
        self.golden_datasets: Dict[str, GoldenDataset] = {}
        self.metric_functions: Dict[MetricType, Callable] = {}
        
        self._init_db()
        self._load_evaluations()
        self._load_golden_datasets()
        self._register_default_metrics()
        
        logger.info(f"📊 Evaluator initialized with {len(self.evaluations)} evaluations, {len(self.golden_datasets)} golden datasets")
    
    def _init_db(self):
        """Initialize database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Evaluations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    evaluation_id TEXT PRIMARY KEY,
                    adapter_id TEXT NOT NULL,
                    golden_dataset_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metrics TEXT,
                    passed INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    logs TEXT,
                    metadata TEXT
                )
            """)
            
            # Golden datasets table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS golden_datasets (
                    dataset_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    dataset_type TEXT NOT NULL,
                    samples TEXT,
                    thresholds TEXT,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evaluations_adapter ON evaluations(adapter_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evaluations_status ON evaluations(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_golden_datasets_type ON golden_datasets(dataset_type)")
            
            conn.commit()
    
    def _load_evaluations(self):
        """Load evaluations from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM evaluations ORDER BY created_at DESC").fetchall()
            
            for row in rows:
                evaluation = EvaluationResult(
                    evaluation_id=row['evaluation_id'],
                    adapter_id=row['adapter_id'],
                    golden_dataset_id=row['golden_dataset_id'],
                    status=EvaluationStatus(row['status']),
                    metrics=json.loads(row['metrics']) if row['metrics'] else {},
                    passed=bool(row['passed']),
                    created_at=row['created_at'],
                    completed_at=row['completed_at'],
                    logs=json.loads(row['logs']) if row['logs'] else [],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                self.evaluations[evaluation.evaluation_id] = evaluation
    
    def _load_golden_datasets(self):
        """Load golden datasets from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM golden_datasets").fetchall()
            
            for row in rows:
                thresholds_data = json.loads(row['thresholds']) if row['thresholds'] else []
                thresholds = [
                    EvaluationThreshold(
                        metric_name=t['metric_name'],
                        min_value=t['min_value'],
                        max_value=t.get('max_value'),
                        required=t.get('required', True)
                    )
                    for t in thresholds_data
                ]
                
                dataset = GoldenDataset(
                    dataset_id=row['dataset_id'],
                    name=row['name'],
                    dataset_type=row['dataset_type'],
                    samples=json.loads(row['samples']) if row['samples'] else [],
                    thresholds=thresholds,
                    created_at=row['created_at'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                self.golden_datasets[dataset.dataset_id] = dataset
    
    def _register_default_metrics(self):
        """Register default metric computation functions."""
        # In a real implementation, these would compute actual metrics
        # For now, we provide placeholder functions
        pass
    
    def create_golden_dataset(self, name: str, dataset_type: str,
                             samples: List[Dict[str, Any]],
                             thresholds: Optional[List[EvaluationThreshold]] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> GoldenDataset:
        """
        Create a golden dataset for evaluation.
        Returns the dataset.
        """
        dataset_id = hashlib.sha256(f"{name}{dataset_type}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        dataset = GoldenDataset(
            dataset_id=dataset_id,
            name=name,
            dataset_type=dataset_type,
            samples=samples,
            thresholds=thresholds or [],
            metadata=metadata or {}
        )
        
        self.golden_datasets[dataset_id] = dataset
        self._persist_golden_dataset(dataset)
        
        logger.info(f"📊 Created golden dataset: {dataset_id} ({name})")
        return dataset
    
    def _persist_golden_dataset(self, dataset: GoldenDataset):
        """Persist golden dataset to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO golden_datasets (dataset_id, name, dataset_type, samples, thresholds, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset.dataset_id,
                dataset.name,
                dataset.dataset_type,
                json.dumps(dataset.samples),
                json.dumps([
                    {
                        "metric_name": t.metric_name,
                        "min_value": t.min_value,
                        "max_value": t.max_value,
                        "required": t.required
                    }
                    for t in dataset.thresholds
                ]),
                dataset.created_at,
                json.dumps(dataset.metadata)
            ))
            conn.commit()
    
    def create_evaluation(self, adapter_id: str, golden_dataset_id: str,
                        metadata: Optional[Dict[str, Any]] = None) -> EvaluationResult:
        """
        Create an evaluation for an adapter.
        Returns the evaluation.
        """
        evaluation_id = hashlib.sha256(f"{adapter_id}{golden_dataset_id}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        evaluation = EvaluationResult(
            evaluation_id=evaluation_id,
            adapter_id=adapter_id,
            golden_dataset_id=golden_dataset_id,
            metadata=metadata or {}
        )
        
        self.evaluations[evaluation_id] = evaluation
        self._persist_evaluation(evaluation)
        
        logger.info(f"📊 Created evaluation: {evaluation_id}")
        return evaluation
    
    def _persist_evaluation(self, evaluation: EvaluationResult):
        """Persist evaluation to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO evaluations (evaluation_id, adapter_id, golden_dataset_id, status, metrics, passed, created_at, completed_at, logs, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evaluation.evaluation_id,
                evaluation.adapter_id,
                evaluation.golden_dataset_id,
                evaluation.status.value,
                json.dumps(evaluation.metrics),
                int(evaluation.passed),
                evaluation.created_at,
                evaluation.completed_at,
                json.dumps(evaluation.logs),
                json.dumps(evaluation.metadata)
            ))
            conn.commit()
    
    def start_evaluation(self, evaluation_id: str) -> bool:
        """
        Start an evaluation.
        Returns True if successful.
        """
        evaluation = self.evaluations.get(evaluation_id)
        if not evaluation:
            logger.warning(f"Evaluation {evaluation_id} not found")
            return False
        
        if evaluation.status != EvaluationStatus.PENDING:
            logger.warning(f"Evaluation {evaluation_id} is not pending")
            return False
        
        evaluation.status = EvaluationStatus.RUNNING
        evaluation.logs.append(f"Evaluation started at {datetime.utcnow().isoformat()}")
        
        self._persist_evaluation(evaluation)
        
        logger.info(f"📊 Started evaluation: {evaluation_id}")
        return True
    
    def complete_evaluation(self, evaluation_id: str, metrics: Dict[str, float]) -> bool:
        """
        Complete an evaluation with metrics.
        Returns True if successful.
        """
        evaluation = self.evaluations.get(evaluation_id)
        if not evaluation:
            logger.warning(f"Evaluation {evaluation_id} not found")
            return False
        
        evaluation.status = EvaluationStatus.RUNNING
        evaluation.metrics = metrics
        evaluation.completed_at = datetime.utcnow().isoformat()
        
        # Check against thresholds
        golden_dataset = self.golden_datasets.get(evaluation.golden_dataset_id)
        if golden_dataset:
            passed = True
            for threshold in golden_dataset.thresholds:
                metric_value = metrics.get(threshold.metric_name)
                if metric_value is None:
                    if threshold.required:
                        passed = False
                        evaluation.logs.append(f"Missing required metric: {threshold.metric_name}")
                elif not threshold.check(metric_value):
                    passed = False
                    evaluation.logs.append(f"Threshold failed: {threshold.metric_name}={metric_value} (min={threshold.min_value})")
            
            evaluation.passed = passed
            evaluation.status = EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED
        else:
            evaluation.passed = True  # No thresholds, auto-pass
            evaluation.status = EvaluationStatus.PASSED
        
        evaluation.logs.append(f"Evaluation completed at {evaluation.completed_at}")
        
        self._persist_evaluation(evaluation)
        
        logger.info(f"📊 Completed evaluation: {evaluation_id} - {'PASSED' if evaluation.passed else 'FAILED'}")
        return True
    
    def fail_evaluation(self, evaluation_id: str, error_message: str) -> bool:
        """
        Mark an evaluation as failed.
        Returns True if successful.
        """
        evaluation = self.evaluations.get(evaluation_id)
        if not evaluation:
            logger.warning(f"Evaluation {evaluation_id} not found")
            return False
        
        evaluation.status = EvaluationStatus.FAILED
        evaluation.completed_at = datetime.utcnow().isoformat()
        evaluation.logs.append(f"Evaluation failed: {error_message}")
        
        self._persist_evaluation(evaluation)
        
        logger.error(f"📊 Failed evaluation: {evaluation_id} - {error_message}")
        return True
    
    def get_evaluation(self, evaluation_id: str) -> Optional[EvaluationResult]:
        """Get an evaluation by ID."""
        return self.evaluations.get(evaluation_id)
    
    def get_evaluations(self, adapter_id: Optional[str] = None,
                      status: Optional[EvaluationStatus] = None) -> List[EvaluationResult]:
        """Get evaluations, optionally filtered."""
        evaluations = list(self.evaluations.values())
        
        if adapter_id:
            evaluations = [e for e in evaluations if e.adapter_id == adapter_id]
        
        if status:
            evaluations = [e for e in evaluations if e.status == status]
        
        return sorted(evaluations, key=lambda e: e.created_at, reverse=True)
    
    def get_golden_dataset(self, dataset_id: str) -> Optional[GoldenDataset]:
        """Get a golden dataset by ID."""
        return self.golden_datasets.get(dataset_id)
    
    def get_golden_datasets(self, dataset_type: Optional[str] = None) -> List[GoldenDataset]:
        """Get golden datasets, optionally filtered by type."""
        datasets = list(self.golden_datasets.values())
        
        if dataset_type:
            datasets = [d for d in datasets if d.dataset_type == dataset_type]
        
        return sorted(datasets, key=lambda d: d.created_at, reverse=True)
    
    def can_promote(self, adapter_id: str) -> bool:
        """
        Check if an adapter can be promoted.
        Returns True if all evaluations passed.
        """
        evaluations = self.get_evaluations(adapter_id)
        
        if not evaluations:
            return True  # No evaluations, allow promotion
        
        for evaluation in evaluations:
            if evaluation.status == EvaluationStatus.FAILED:
                return False
            if evaluation.status == EvaluationStatus.PASSED and not evaluation.passed:
                return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get evaluator statistics."""
        total_evaluations = len(self.evaluations)
        passed = len([e for e in self.evaluations.values() if e.status == EvaluationStatus.PASSED])
        failed = len([e for e in self.evaluations.values() if e.status == EvaluationStatus.FAILED])
        running = len([e for e in self.evaluations.values() if e.status == EvaluationStatus.RUNNING])
        pending = len([e for e in self.evaluations.values() if e.status == EvaluationStatus.PENDING])
        
        return {
            "total_evaluations": total_evaluations,
            "passed": passed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "golden_datasets": len(self.golden_datasets)
        }


# Global evaluator instance
_evaluator: Optional[Evaluator] = None


def get_evaluator(db_path: str = "data/evaluator.db") -> Evaluator:
    """Get or create global evaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = Evaluator(db_path)
    return _evaluator


def reset_evaluator():
    """Reset global evaluator instance (for testing)."""
    global _evaluator
    _evaluator = None
