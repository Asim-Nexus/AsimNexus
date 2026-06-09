#!/usr/bin/env python3
"""Global Swarm Intelligence (Phase 9).

Enables federated learning across AsimNexus instances, distributed task
execution, a global knowledge graph, swarm consensus via the existing
consensus engine, and emergency broadcast via the existing relay system.

Modules:
    federated_learning: Federated model training across instances
    task_distributor: Distributed task allocation and execution
    knowledge_graph: Global shared knowledge graph
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

__all__ = [
    "FederatedLearning",
    "TaskDistributor",
    "KnowledgeGraph",
    "get_federated_learning",
    "get_task_distributor",
    "get_knowledge_graph",
]

# Global singletons
_federated_learning: Optional["FederatedLearning"] = None
_task_distributor: Optional["TaskDistributor"] = None
_knowledge_graph: Optional["KnowledgeGraph"] = None


def get_federated_learning() -> "FederatedLearning":
    """Get or create the singleton FederatedLearning instance."""
    global _federated_learning
    if _federated_learning is None:
        from swarm.federated_learning import FederatedLearning
        _federated_learning = FederatedLearning()
    return _federated_learning


def get_task_distributor() -> "TaskDistributor":
    """Get or create the singleton TaskDistributor instance."""
    global _task_distributor
    if _task_distributor is None:
        from swarm.task_distributor import TaskDistributor
        _task_distributor = TaskDistributor()
    return _task_distributor


def get_knowledge_graph() -> "KnowledgeGraph":
    """Get or create the singleton KnowledgeGraph instance."""
    global _knowledge_graph
    if _knowledge_graph is None:
        from swarm.knowledge_graph import KnowledgeGraph
        _knowledge_graph = KnowledgeGraph()
    return _knowledge_graph


def reset_all():
    """Reset all singleton instances (for testing)."""
    global _federated_learning, _task_distributor, _knowledge_graph
    _federated_learning = None
    _task_distributor = None
    _knowledge_graph = None
