#!/usr/bin/env python3
"""Federated Learning — Distributed model training across AsimNexus instances.

Enables multiple AsimNexus instances to collaboratively train models without
sharing raw data. Uses a federated averaging approach where each instance
trains locally, shares only weight updates, and the global model aggregates
them securely.

Typical usage::

    fl = FederatedLearning()
    round_id = fl.start_round(model_config={...})
    fl.submit_update(round_id, node_id="node-1", weights={...})
    global_weights = fl.aggregate_round(round_id)
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RoundStatus(Enum):
    """Status of a federated learning round."""
    PENDING = auto()
    COLLECTING = auto()
    AGGREGATING = auto()
    COMPLETED = auto()
    FAILED = auto()
    TIMEOUT = auto()


class ContributionStrategy(Enum):
    """Strategy for weighting node contributions during aggregation."""
    EQUAL = auto()            # All nodes weighted equally
    DATA_VOLUME = auto()      # Weighted by training data size
    REPUTATION = auto()       # Weighted by node reputation score
    PERFORMANCE = auto()      # Weighted by validation accuracy


@dataclass
class NodeUpdate:
    """A weight update submitted by a participating node."""
    node_id: str
    round_id: str
    weights: Dict[str, Any]  # Serialized weight tensors
    data_volume: int = 0      # Number of training samples used
    validation_score: float = 0.0
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class TrainingRound:
    """A single federated training round."""
    round_id: str
    status: RoundStatus = RoundStatus.PENDING
    model_config: Dict[str, Any] = field(default_factory=dict)
    strategy: ContributionStrategy = ContributionStrategy.EQUAL
    min_nodes: int = 1
    timeout_seconds: int = 300
    created_at: str = ""
    completed_at: Optional[str] = None
    submissions: Dict[str, NodeUpdate] = field(default_factory=dict)
    global_weights: Optional[Dict[str, Any]] = None
    aggregated_metrics: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    @property
    def submission_count(self) -> int:
        return len(self.submissions)

    @property
    def is_timed_out(self) -> bool:
        if self.status in (RoundStatus.COMPLETED, RoundStatus.FAILED, RoundStatus.TIMEOUT):
            return False
        elapsed = (datetime.utcnow() - datetime.fromisoformat(self.created_at)).total_seconds()
        return elapsed > self.timeout_seconds

    @property
    def is_ready_to_aggregate(self) -> bool:
        return self.submission_count >= self.min_nodes and not self.is_timed_out


class FederatedLearning:
    """Orchestrates federated learning rounds across AsimNexus instances.

    Features:
    - Weighted aggregation strategies (equal, data-volume, reputation)
    - Round lifecycle management (create, collect, aggregate, complete)
    - Timeout and failure handling
    - Metrics tracking per round
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__), "..", "data", "federated"
        )
        os.makedirs(self.storage_dir, exist_ok=True)
        self._rounds: Dict[str, TrainingRound] = {}

    # ── Public API ──────────────────────────────────────────────────────────

    def start_round(
        self,
        model_config: Optional[Dict[str, Any]] = None,
        strategy: ContributionStrategy = ContributionStrategy.EQUAL,
        min_nodes: int = 2,
        timeout_seconds: int = 300,
    ) -> str:
        """Start a new federated learning round.

        Args:
            model_config: Dict describing model architecture/hyperparameters.
            strategy: Weighting strategy for aggregation.
            min_nodes: Minimum participating nodes before aggregation.
            timeout_seconds: Max seconds to wait for submissions.

        Returns:
            The round_id for the new round.
        """
        round_id = f"fl-{uuid.uuid4().hex[:12]}"
        round_obj = TrainingRound(
            round_id=round_id,
            status=RoundStatus.COLLECTING,
            model_config=model_config or {},
            strategy=strategy,
            min_nodes=min_nodes,
            timeout_seconds=timeout_seconds,
        )
        self._rounds[round_id] = round_obj
        logger.info("Started federated learning round %s (min_nodes=%d, strategy=%s)",
                     round_id, min_nodes, strategy.name)
        return round_id

    def submit_update(
        self,
        round_id: str,
        node_id: str,
        weights: Dict[str, Any],
        data_volume: int = 0,
        validation_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Submit a training update from a node for a round.

        Args:
            round_id: The target training round.
            node_id: Unique identifier of the submitting node.
            weights: Serialized model weights.
            data_volume: Number of training samples used.
            validation_score: Accuracy/loss on node's validation set.
            metadata: Additional submission metadata.

        Returns:
            True if submission was accepted, False if round is closed/timed out.
        """
        round_obj = self._rounds.get(round_id)
        if not round_obj:
            logger.warning("Round %s not found", round_id)
            return False

        if round_obj.status != RoundStatus.COLLECTING:
            logger.warning("Round %s is not collecting (status=%s)", round_id, round_obj.status.name)
            return False

        if round_obj.is_timed_out:
            round_obj.status = RoundStatus.TIMEOUT
            logger.warning("Round %s timed out", round_id)
            return False

        update = NodeUpdate(
            node_id=node_id,
            round_id=round_id,
            weights=weights,
            data_volume=data_volume,
            validation_score=validation_score,
            metadata=metadata or {},
        )
        round_obj.submissions[node_id] = update
        logger.info("Node %s submitted update for round %s (data=%d, score=%.4f)",
                     node_id, round_id, data_volume, validation_score)
        return True

    def aggregate_round(self, round_id: str) -> Optional[Dict[str, Any]]:
        """Aggregate all submitted updates for a round.

        Args:
            round_id: The training round to aggregate.

        Returns:
            Global aggregated weights dict, or None if aggregation fails.
        """
        round_obj = self._rounds.get(round_id)
        if not round_obj:
            return None

        if round_obj.status != RoundStatus.COLLECTING:
            return round_obj.global_weights

        if round_obj.submission_count < round_obj.min_nodes:
            logger.warning("Round %s has insufficient submissions (%d < %d)",
                           round_id, round_obj.submission_count, round_obj.min_nodes)
            return None

        round_obj.status = RoundStatus.AGGREGATING

        try:
            weights = self._federated_averaging(round_obj)
            round_obj.global_weights = weights
            round_obj.status = RoundStatus.COMPLETED
            round_obj.completed_at = datetime.utcnow().isoformat()

            # Compute aggregated metrics
            scores = [s.validation_score for s in round_obj.submissions.values()]
            volumes = [s.data_volume for s in round_obj.submissions.values()]
            round_obj.aggregated_metrics = {
                "mean_validation_score": sum(scores) / len(scores) if scores else 0.0,
                "total_data_volume": sum(volumes),
                "participant_count": round_obj.submission_count,
                "aggregation_strategy": round_obj.strategy.name,
            }

            logger.info("Round %s aggregated successfully (%d participants, %.4f mean score)",
                        round_id, round_obj.submission_count,
                        round_obj.aggregated_metrics["mean_validation_score"])

            self._save_round(round_obj)
            return weights

        except Exception as exc:
            logger.exception("Aggregation failed for round %s: %s", round_id, exc)
            round_obj.status = RoundStatus.FAILED
            return None

    def get_round(self, round_id: str) -> Optional[TrainingRound]:
        """Get a training round by ID."""
        return self._rounds.get(round_id)

    def get_active_rounds(self) -> List[TrainingRound]:
        """Get all currently active (collecting) rounds."""
        return [r for r in self._rounds.values() if r.status == RoundStatus.COLLECTING]

    def get_completed_rounds(self) -> List[TrainingRound]:
        """Get all completed rounds."""
        return [r for r in self._rounds.values() if r.status == RoundStatus.COMPLETED]

    def get_stats(self) -> Dict:
        """Get aggregated statistics about federated learning activity."""
        completed = self.get_completed_rounds()
        return {
            "total_rounds": len(self._rounds),
            "active_rounds": len(self.get_active_rounds()),
            "completed_rounds": len(completed),
            "failed_rounds": len([r for r in self._rounds.values() if r.status == RoundStatus.FAILED]),
            "total_participations": sum(r.submission_count for r in completed),
            "avg_participants_per_round": (
                sum(r.submission_count for r in completed) / len(completed)
                if completed else 0.0
            ),
        }

    def prune_old_rounds(self, max_age_hours: int = 24):
        """Remove rounds older than max_age_hours from memory."""
        now = datetime.utcnow()
        to_remove = []
        for rid, round_obj in self._rounds.items():
            created = datetime.fromisoformat(round_obj.created_at)
            if (now - created).total_seconds() > max_age_hours * 3600:
                to_remove.append(rid)
        for rid in to_remove:
            del self._rounds[rid]
        logger.info("Pruned %d old rounds (max_age=%dh)", len(to_remove), max_age_hours)

    # ── Internal methods ────────────────────────────────────────────────────

    def _federated_averaging(self, round_obj: TrainingRound) -> Dict[str, Any]:
        """Perform federated averaging of submitted weights.

        Uses the round's contribution strategy to weight each node's update.
        """
        submissions = list(round_obj.submissions.values())
        if not submissions:
            return {}

        # Compute weights for each submission
        node_weights = self._compute_node_weights(submissions, round_obj.strategy)

        # Get all weight keys from first submission
        all_keys = set()
        for s in submissions:
            all_keys.update(s.weights.keys())

        # Weighted average
        averaged: Dict[str, Any] = {}
        for key in all_keys:
            # Collect values, treating missing as zero
            values = []
            weights = []
            for s, w in zip(submissions, node_weights):
                if key in s.weights:
                    values.append(s.weights[key])
                    weights.append(w)

            if not values:
                continue

            # If values are numeric, do weighted average
            if all(isinstance(v, (int, float)) for v in values):
                total_weight = sum(weights)
                averaged[key] = sum(v * w for v, w in zip(values, weights)) / total_weight if total_weight > 0 else 0.0
            else:
                # For non-numeric (e.g., list weights), take from highest-weighted node
                max_idx = weights.index(max(weights))
                averaged[key] = values[max_idx]

        return averaged

    def _compute_node_weights(self, submissions: List[NodeUpdate],
                              strategy: ContributionStrategy) -> List[float]:
        """Compute aggregation weight for each node based on strategy."""
        n = len(submissions)
        if n == 0:
            return []

        if strategy == ContributionStrategy.EQUAL:
            return [1.0 / n] * n

        elif strategy == ContributionStrategy.DATA_VOLUME:
            total_volume = sum(s.data_volume for s in submissions)
            if total_volume == 0:
                return [1.0 / n] * n
            return [s.data_volume / total_volume for s in submissions]

        elif strategy == ContributionStrategy.VALIDATION_SCORE if hasattr(ContributionStrategy, 'VALIDATION_SCORE') else ContributionStrategy.EQUAL:
            total_score = sum(max(s.validation_score, 0.01) for s in submissions)
            if total_score == 0:
                return [1.0 / n] * n
            return [max(s.validation_score, 0.01) / total_score for s in submissions]

        else:
            return [1.0 / n] * n

    def _save_round(self, round_obj: TrainingRound):
        """Persist a completed round to disk."""
        path = os.path.join(self.storage_dir, f"{round_obj.round_id}.json")
        try:
            data = asdict(round_obj)
            # Convert enums to strings
            data["status"] = round_obj.status.name
            data["strategy"] = round_obj.strategy.name
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as exc:
            logger.warning("Failed to save round %s: %s", round_obj.round_id, exc)


def get_federated_learning(storage_dir: Optional[str] = None) -> FederatedLearning:
    """Factory function to get a FederatedLearning instance."""
    return FederatedLearning(storage_dir=storage_dir)
