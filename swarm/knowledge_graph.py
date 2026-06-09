#!/usr/bin/env python3
"""Global Shared Knowledge Graph — Distributed semantic memory for swarm intelligence.

Maintains a distributed shared knowledge graph across AsimNexus instances,
enabling entities, relationships, and semantic querying across the swarm.

Typical usage::

    kg = KnowledgeGraph()
    node_id = kg.add_node("agent-1", labels={"Person", "Agent"}, properties={"name": "Alice"})
    kg.add_edge(node_id, "concept-1", relationship="KNOWS", weight=0.9)
    results = kg.query("alice")
    neighbors = kg.get_neighbors(node_id, max_hops=2)
"""

from __future__ import annotations

import copy
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ── Data Classes ──────────────────────────────────────────────────────────────


@dataclass
class KnowledgeNode:
    """A node in the global knowledge graph representing an entity or concept.

    Attributes:
        node_id: Unique identifier for this node.
        labels: Set of categorical labels (e.g. {"Person", "Agent"}).
        properties: Arbitrary key-value properties describing the node.
        created_at: ISO-8601 timestamp of creation.
        updated_at: ISO-8601 timestamp of last update.
        source: Identifier of the originating swarm instance or user.
    """

    node_id: str
    labels: Set[str] = field(default_factory=set)
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    source: str = ""

    def __post_init__(self):
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "node_id": self.node_id,
            "labels": list(self.labels),
            "properties": self.properties,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeNode":
        """Deserialize from a dict produced by ``to_dict()``."""
        data = dict(data)
        if "labels" in data and isinstance(data["labels"], list):
            data["labels"] = set(data["labels"])
        return cls(**data)


@dataclass
class KnowledgeEdge:
    """A directed, weighted relationship between two knowledge nodes.

    Attributes:
        edge_id: Unique identifier for this edge.
        source_id: Node ID of the source (subject).
        target_id: Node ID of the target (object).
        relationship: Label describing the relationship (e.g. "KNOWS", "DERIVED_FROM").
        weight: Numeric weight/strength of the relationship (0.0 to 1.0).
        properties: Arbitrary key-value properties for the edge.
        created_at: ISO-8601 timestamp of creation.
        updated_at: ISO-8601 timestamp of last update.
    """

    edge_id: str
    source_id: str
    target_id: str
    relationship: str = "RELATED_TO"
    weight: float = 0.5
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship": self.relationship,
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEdge":
        """Deserialize from a dict produced by ``to_dict()``."""
        return cls(**data)


@dataclass
class QueryResult:
    """Result of a knowledge graph query.

    Attributes:
        nodes: Matching knowledge nodes.
        edges: Edges connecting the matching nodes (where applicable).
        query: The original query text.
        elapsed_ms: Query execution time in milliseconds.
    """

    nodes: List[KnowledgeNode] = field(default_factory=list)
    edges: List[KnowledgeEdge] = field(default_factory=list)
    query: str = ""
    elapsed_ms: float = 0.0


# ── Knowledge Graph ───────────────────────────────────────────────────────────


class KnowledgeGraph:
    """Global shared knowledge graph for swarm intelligence.

    Maintains a distributed semantic memory of entities (nodes),
    relationships (edges), and supports fuzzy text-based queries,
    neighbor traversal, importance scoring, merge-based distributed
    sync, and JSON persistence.

    Features:
    - Add / update / delete nodes with labels and properties
    - Add / update / delete weighted, typed edges between nodes
    - Fuzzy text matching on node properties
    - N-hop neighbor queries
    - Merge operations for distributed synchronisation across swarm nodes
    - Importance tracking based on connectivity (degree centrality)
    - Save / load to / from JSON files
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__), "..", "data", "knowledge_graph"
        )
        os.makedirs(self.storage_dir, exist_ok=True)

        self._nodes: Dict[str, KnowledgeNode] = {}
        self._edges: Dict[str, KnowledgeEdge] = {}

        # Index: source_id -> list of edge_ids
        self._outgoing: Dict[str, List[str]] = {}
        # Index: target_id -> list of edge_ids
        self._incoming: Dict[str, List[str]] = {}

    # ── Node Operations ───────────────────────────────────────────────────────

    def add_node(
        self,
        node_id: str,
        labels: Optional[Set[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        source: str = "",
    ) -> str:
        """Add a new node to the knowledge graph.

        Args:
            node_id: Unique identifier for the node.
            labels: Optional set of categorical labels.
            properties: Optional key-value properties.
            source: Identifier of the originating instance.

        Returns:
            The node_id of the newly created node.

        Raises:
            ValueError: If a node with the same ID already exists.
        """
        if node_id in self._nodes:
            raise ValueError(f"Node '{node_id}' already exists in the knowledge graph")

        node = KnowledgeNode(
            node_id=node_id,
            labels=labels or set(),
            properties=properties or {},
            source=source,
        )
        self._nodes[node_id] = node
        self._outgoing.setdefault(node_id, [])
        self._incoming.setdefault(node_id, [])
        logger.info("Added node '%s' (labels=%s, source=%s)", node_id, node.labels, source)
        return node_id

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Retrieve a node by its ID.

        Args:
            node_id: The unique identifier of the node.

        Returns:
            The KnowledgeNode if found, else None.
        """
        return self._nodes.get(node_id)

    def update_node(
        self,
        node_id: str,
        labels: Optional[Set[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        merge_properties: bool = True,
    ) -> bool:
        """Update an existing node's labels and/or properties.

        Args:
            node_id: The unique identifier of the node to update.
            labels: If provided, replaces all labels. Pass an empty set to clear labels.
            properties: If provided, updates properties. When ``merge_properties`` is
                True (default), individual keys are merged; otherwise replaces all.
            merge_properties: If True, merge new properties into existing ones;
                if False, replace all properties entirely.

        Returns:
            True if the node was found and updated, False otherwise.
        """
        node = self._nodes.get(node_id)
        if not node:
            logger.warning("Cannot update node '%s': not found", node_id)
            return False

        if labels is not None:
            node.labels = labels

        if properties is not None:
            if merge_properties:
                node.properties.update(properties)
            else:
                node.properties = properties

        node.updated_at = datetime.utcnow().isoformat()
        logger.info("Updated node '%s'", node_id)
        return True

    def delete_node(self, node_id: str) -> bool:
        """Delete a node and all its incident edges.

        Args:
            node_id: The unique identifier of the node to delete.

        Returns:
            True if the node was found and deleted, False otherwise.
        """
        if node_id not in self._nodes:
            return False

        # Collect all edges incident to this node
        incident = set(self._outgoing.get(node_id, []))
        incident.update(self._incoming.get(node_id, []))

        for edge_id in incident:
            self._delete_edge_by_id(edge_id)

        del self._nodes[node_id]
        self._outgoing.pop(node_id, None)
        self._incoming.pop(node_id, None)

        logger.info("Deleted node '%s' (removed %d incident edges)", node_id, len(incident))
        return True

    def get_all_nodes(self) -> List[KnowledgeNode]:
        """Get all nodes currently in the knowledge graph."""
        return list(self._nodes.values())

    def get_nodes_by_label(self, label: str) -> List[KnowledgeNode]:
        """Get all nodes that have a specific label.

        Args:
            label: The label to filter by.

        Returns:
            List of matching KnowledgeNode objects.
        """
        return [n for n in self._nodes.values() if label in n.labels]

    # ── Edge Operations ───────────────────────────────────────────────────────

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str = "RELATED_TO",
        weight: float = 0.5,
        edge_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a directed edge between two nodes.

        Args:
            source_id: Node ID of the source (subject).
            target_id: Node ID of the target (object).
            relationship: Label describing the relationship.
            weight: Numeric weight/strength (0.0 to 1.0).
            edge_id: Optional custom edge ID; auto-generated if not provided.
            properties: Optional key-value properties for the edge.

        Returns:
            The edge_id of the newly created edge.

        Raises:
            ValueError: If source or target nodes do not exist, or the edge already exists.
        """
        if source_id not in self._nodes:
            raise ValueError(f"Source node '{source_id}' does not exist")
        if target_id not in self._nodes:
            raise ValueError(f"Target node '{target_id}' does not exist")

        eid = edge_id or f"edge-{os.urandom(6).hex()}"

        if eid in self._edges:
            raise ValueError(f"Edge '{eid}' already exists")

        edge = KnowledgeEdge(
            edge_id=eid,
            source_id=source_id,
            target_id=target_id,
            relationship=relationship,
            weight=max(0.0, min(1.0, weight)),
            properties=properties or {},
        )
        self._edges[eid] = edge
        self._outgoing.setdefault(source_id, []).append(eid)
        self._incoming.setdefault(target_id, []).append(eid)

        logger.info(
            "Added edge '%s' (%s --[%s]--> %s, weight=%.2f)",
            eid, source_id, relationship, target_id, weight,
        )
        return eid

    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """Retrieve an edge by its ID.

        Args:
            edge_id: The unique identifier of the edge.

        Returns:
            The KnowledgeEdge if found, else None.
        """
        return self._edges.get(edge_id)

    def update_edge(
        self,
        edge_id: str,
        relationship: Optional[str] = None,
        weight: Optional[float] = None,
        properties: Optional[Dict[str, Any]] = None,
        merge_properties: bool = True,
    ) -> bool:
        """Update an existing edge's attributes.

        Args:
            edge_id: The unique identifier of the edge to update.
            relationship: If provided, replaces the relationship label.
            weight: If provided, replaces the weight (clamped to [0.0, 1.0]).
            properties: If provided, updates properties (merged by default).
            merge_properties: If True, merge new properties into existing ones.

        Returns:
            True if the edge was found and updated, False otherwise.
        """
        edge = self._edges.get(edge_id)
        if not edge:
            logger.warning("Cannot update edge '%s': not found", edge_id)
            return False

        if relationship is not None:
            edge.relationship = relationship

        if weight is not None:
            edge.weight = max(0.0, min(1.0, weight))

        if properties is not None:
            if merge_properties:
                edge.properties.update(properties)
            else:
                edge.properties = properties

        edge.updated_at = datetime.utcnow().isoformat()
        logger.info("Updated edge '%s'", edge_id)
        return True

    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge by its ID.

        Args:
            edge_id: The unique identifier of the edge to delete.

        Returns:
            True if the edge was found and deleted, False otherwise.
        """
        return self._delete_edge_by_id(edge_id)

    def _delete_edge_by_id(self, edge_id: str) -> bool:
        """Internal: remove an edge and update indexes."""
        edge = self._edges.pop(edge_id, None)
        if not edge:
            return False

        # Remove from outgoing index
        out_list = self._outgoing.get(edge.source_id, [])
        if edge_id in out_list:
            out_list.remove(edge_id)

        # Remove from incoming index
        in_list = self._incoming.get(edge.target_id, [])
        if edge_id in in_list:
            in_list.remove(edge_id)

        return True

    def get_edges_for_node(self, node_id: str) -> List[KnowledgeEdge]:
        """Get all edges incident to a node (both outgoing and incoming).

        Args:
            node_id: The node ID.

        Returns:
            List of incident KnowledgeEdge objects.
        """
        edge_ids = set(self._outgoing.get(node_id, []))
        edge_ids.update(self._incoming.get(node_id, []))
        return [self._edges[eid] for eid in edge_ids if eid in self._edges]

    def get_outgoing_edges(self, node_id: str) -> List[KnowledgeEdge]:
        """Get all edges where the node is the source.

        Args:
            node_id: The source node ID.

        Returns:
            List of outgoing KnowledgeEdge objects.
        """
        return [self._edges[eid] for eid in self._outgoing.get(node_id, []) if eid in self._edges]

    def get_incoming_edges(self, node_id: str) -> List[KnowledgeEdge]:
        """Get all edges where the node is the target.

        Args:
            node_id: The target node ID.

        Returns:
            List of incoming KnowledgeEdge objects.
        """
        return [self._edges[eid] for eid in self._incoming.get(node_id, []) if eid in self._edges]

    def get_all_edges(self) -> List[KnowledgeEdge]:
        """Get all edges in the knowledge graph."""
        return list(self._edges.values())

    # ── Query Operations ──────────────────────────────────────────────────────

    def query(self, text: str, threshold: float = 0.3) -> QueryResult:
        """Fuzzy-match nodes whose properties contain the query text.

        Compares ``text`` (case-insensitive) against all string property values
        of every node. Results are sorted by descending match score.

        Args:
            text: The search text.
            threshold: Minimum match score (0.0 to 1.0) to include a node.

        Returns:
            A QueryResult with matching nodes, their incident edges, and
            the elapsed time.
        """
        start = time.perf_counter()
        text_lower = text.lower()

        scored_nodes: List[Tuple[float, KnowledgeNode]] = []

        for node in self._nodes.values():
            score = self._fuzzy_match_node(node, text_lower)
            if score >= threshold:
                scored_nodes.append((score, node))

        # Sort descending by score
        scored_nodes.sort(key=lambda t: t[0], reverse=True)
        matched_nodes = [n for _, n in scored_nodes]

        # Collect edges between matched nodes
        matched_ids = {n.node_id for n in matched_nodes}
        matched_edges = [
            e for e in self._edges.values()
            if e.source_id in matched_ids and e.target_id in matched_ids
        ]

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        logger.info(
            "Query '%s' returned %d nodes, %d edges in %.1f ms",
            text, len(matched_nodes), len(matched_edges), elapsed_ms,
        )

        return QueryResult(
            nodes=matched_nodes,
            edges=matched_edges,
            query=text,
            elapsed_ms=elapsed_ms,
        )

    def _fuzzy_match_node(self, node: KnowledgeNode, text_lower: str) -> float:
        """Compute a simple fuzzy match score for a node against query text.

        Checks the node_id, labels, and all string property values.
        Returns a score in [0.0, 1.0].
        """
        score = 0.0
        checks = 0

        # Check node_id
        if text_lower in node.node_id.lower():
            score += 1.0
        checks += 1

        # Check labels
        for label in node.labels:
            checks += 1
            if text_lower in label.lower():
                score += 0.8

        # Check string property values
        for key, val in node.properties.items():
            checks += 1
            if isinstance(val, str) and text_lower in val.lower():
                score += 0.6
            elif isinstance(val, (int, float)):
                # If the query looks numeric, check for partial match
                if text_lower in str(val).lower():
                    score += 0.4

        return score / max(checks, 1)

    # ── Neighbor Query ────────────────────────────────────────────────────────

    def get_neighbors(
        self, node_id: str, max_hops: int = 1, min_weight: float = 0.0
    ) -> QueryResult:
        """Retrieve all nodes reachable within *max_hops* from the given node.

        Uses BFS traversal along directed edges (both outgoing and incoming),
        respecting the minimum edge weight filter.

        Args:
            node_id: The starting node ID.
            max_hops: Maximum traversal depth (default 1 = direct neighbors).
            min_weight: Minimum edge weight to traverse (0.0 = no filter).

        Returns:
            A QueryResult containing the reachable nodes and traversed edges.
        """
        start = time.perf_counter()

        if node_id not in self._nodes:
            logger.warning("Neighbor query failed: node '%s' not found", node_id)
            return QueryResult(
                query=f"neighbors({node_id}, hops={max_hops})",
            )

        visited_nodes: Set[str] = {node_id}
        visited_edges: Set[str] = set()
        frontier: Set[str] = {node_id}

        for _ in range(max_hops):
            if not frontier:
                break
            next_frontier: Set[str] = set()

            for current in frontier:
                for edge_id in self._outgoing.get(current, []):
                    edge = self._edges.get(edge_id)
                    if edge and edge.weight >= min_weight and edge.target_id not in visited_nodes:
                        visited_nodes.add(edge.target_id)
                        visited_edges.add(edge_id)
                        next_frontier.add(edge.target_id)

                for edge_id in self._incoming.get(current, []):
                    edge = self._edges.get(edge_id)
                    if edge and edge.weight >= min_weight and edge.source_id not in visited_nodes:
                        visited_nodes.add(edge.source_id)
                        visited_edges.add(edge_id)
                        next_frontier.add(edge.source_id)

            frontier = next_frontier

        # Exclude the starting node itself from results
        result_nodes = [self._nodes[nid] for nid in visited_nodes if nid != node_id]
        result_edges = [self._edges[eid] for eid in visited_edges if eid in self._edges]

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        logger.info(
            "Neighbor query '%s' (hops=%d) returned %d nodes, %d edges in %.1f ms",
            node_id, max_hops, len(result_nodes), len(result_edges), elapsed_ms,
        )

        return QueryResult(
            nodes=result_nodes,
            edges=result_edges,
            query=f"neighbors({node_id}, hops={max_hops})",
            elapsed_ms=elapsed_ms,
        )

    # ── Importance Scoring ────────────────────────────────────────────────────

    def get_importance(self, node_id: str) -> float:
        """Compute the importance score of a node based on connectivity.

        Importance is derived from degree centrality – the number of incident
        edges relative to the total possible connections in the graph.

        Args:
            node_id: The node ID.

        Returns:
            A float between 0.0 (isolated) and 1.0 (connected to all others).
        """
        node_count = len(self._nodes)
        if node_count <= 1:
            return 0.0

        degree = len(self._outgoing.get(node_id, [])) + len(self._incoming.get(node_id, []))
        max_possible = 2 * (node_count - 1)  # directed: incoming + outgoing
        return degree / max_possible if max_possible > 0 else 0.0

    def get_importance_scores(self) -> Dict[str, float]:
        """Compute importance scores for all nodes in the graph.

        Returns:
            Dict mapping node_id -> importance score (0.0 to 1.0).
        """
        return {nid: self.get_importance(nid) for nid in self._nodes}

    def get_top_nodes(self, n: int = 10) -> List[Tuple[str, float]]:
        """Get the *n* most important nodes, sorted descending by importance.

        Args:
            n: Maximum number of nodes to return.

        Returns:
            List of (node_id, importance_score) tuples.
        """
        scores = self.get_importance_scores()
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:n]

    # ── Merge Operations (Distributed Sync) ───────────────────────────────────

    def merge(self, other: "KnowledgeGraph") -> Dict[str, Any]:
        """Merge another KnowledgeGraph into this one.

        New nodes and edges from *other* are added; existing nodes have their
        labels and properties merged (incoming data takes precedence on conflict).
        Existing edges are updated if the relationship or weight differs.

        Args:
            other: Another KnowledgeGraph instance to merge into this one.

        Returns:
            A summary dict with counts of added/updated nodes and edges.
        """
        start = time.perf_counter()
        added_nodes = 0
        updated_nodes = 0
        added_edges = 0
        updated_edges = 0

        # Merge nodes
        for node_id, node in other._nodes.items():
            if node_id not in self._nodes:
                # Deep copy to avoid shared references
                self._nodes[node_id] = copy.deepcopy(node)
                self._outgoing.setdefault(node_id, [])
                self._incoming.setdefault(node_id, [])
                added_nodes += 1
            else:
                existing = self._nodes[node_id]
                existing.labels.update(node.labels)
                existing.properties.update(node.properties)
                if node.source and not existing.source:
                    existing.source = node.source
                existing.updated_at = datetime.utcnow().isoformat()
                updated_nodes += 1

        # Merge edges
        for edge_id, edge in other._edges.items():
            if edge_id not in self._edges:
                new_edge = copy.deepcopy(edge)
                self._edges[edge_id] = new_edge
                self._outgoing.setdefault(edge.source_id, []).append(edge_id)
                self._incoming.setdefault(edge.target_id, []).append(edge_id)
                added_edges += 1
            else:
                existing = self._edges[edge_id]
                existing.relationship = edge.relationship
                existing.weight = edge.weight
                existing.properties.update(edge.properties)
                existing.updated_at = datetime.utcnow().isoformat()
                updated_edges += 1

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        logger.info(
            "Merged knowledge graph: +%d nodes, +%d edges in %.1f ms",
            added_nodes, added_edges, elapsed_ms,
        )

        return {
            "added_nodes": added_nodes,
            "updated_nodes": updated_nodes,
            "added_edges": added_edges,
            "updated_edges": updated_edges,
            "elapsed_ms": elapsed_ms,
        }

    def merge_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge nodes/edges from a serialized dict (e.g. received from another instance).

        Args:
            data: Dict with ``nodes`` and ``edges`` keys (lists of dicts).

        Returns:
            A summary dict with counts of added/updated nodes and edges.
        """
        temp = KnowledgeGraph(storage_dir=self.storage_dir)
        for nd in data.get("nodes", []):
            node = KnowledgeNode.from_dict(nd)
            temp._nodes[node.node_id] = node
            temp._outgoing.setdefault(node.node_id, [])
            temp._incoming.setdefault(node.node_id, [])

        for ed in data.get("edges", []):
            edge = KnowledgeEdge.from_dict(ed)
            temp._edges[edge.edge_id] = edge
            temp._outgoing.setdefault(edge.source_id, []).append(edge.edge_id)
            temp._incoming.setdefault(edge.target_id, []).append(edge.edge_id)

        return self.merge(temp)

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics about the knowledge graph.

        Returns:
            Dict with node count, edge count, density, average degree, etc.
        """
        node_count = len(self._nodes)
        edge_count = len(self._edges)
        density = 0.0
        avg_degree = 0.0

        if node_count > 1:
            max_possible = node_count * (node_count - 1)  # directed
            density = edge_count / max_possible if max_possible > 0 else 0.0
            total_degree = sum(
                len(self._outgoing.get(nid, [])) + len(self._incoming.get(nid, []))
                for nid in self._nodes
            )
            avg_degree = total_degree / node_count

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "density": round(density, 6),
            "avg_degree": round(avg_degree, 4),
            "label_counts": self._count_by_label(),
            "relationship_counts": self._count_by_relationship(),
            "total_importance": sum(self.get_importance_scores().values()),
        }

    def _count_by_label(self) -> Dict[str, int]:
        """Count nodes grouped by label."""
        counts: Dict[str, int] = {}
        for node in self._nodes.values():
            for label in node.labels:
                counts[label] = counts.get(label, 0) + 1
        return counts

    def _count_by_relationship(self) -> Dict[str, int]:
        """Count edges grouped by relationship type."""
        counts: Dict[str, int] = {}
        for edge in self._edges.values():
            counts[edge.relationship] = counts.get(edge.relationship, 0) + 1
        return counts

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, file_path: Optional[str] = None) -> str:
        """Persist the entire knowledge graph to a JSON file.

        Args:
            file_path: Optional path; defaults to ``{storage_dir}/knowledge_graph.json``.

        Returns:
            The file path the graph was saved to.
        """
        path = file_path or os.path.join(self.storage_dir, "knowledge_graph.json")
        data = {
            "saved_at": datetime.utcnow().isoformat(),
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Knowledge graph saved to %s (%d nodes, %d edges)",
                        path, data["node_count"], data["edge_count"])
        except Exception as exc:
            logger.exception("Failed to save knowledge graph to %s: %s", path, exc)
        return path

    def load(self, file_path: Optional[str] = None) -> int:
        """Load a knowledge graph from a JSON file, merging with current data.

        Args:
            file_path: Optional path; defaults to ``{storage_dir}/knowledge_graph.json``.

        Returns:
            The number of nodes loaded, or 0 if the file does not exist.
        """
        path = file_path or os.path.join(self.storage_dir, "knowledge_graph.json")
        if not os.path.isfile(path):
            logger.warning("No knowledge graph file found at %s", path)
            return 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            logger.exception("Failed to load knowledge graph from %s: %s", path, exc)
            return 0

        node_count = len(data.get("nodes", []))
        self.merge_from_dict(data)
        logger.info("Loaded %d nodes from %s", node_count, path)
        return node_count

    def export_graph(self) -> Dict[str, Any]:
        """Export the full graph as a serializable dict (no side effects).

        Returns:
            Dict with ``nodes`` and ``edges`` keys, each a list of dicts.
        """
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
        }


# ── Factory ───────────────────────────────────────────────────────────────────


def get_knowledge_graph(storage_dir: Optional[str] = None) -> KnowledgeGraph:
    """Factory function to create a new KnowledgeGraph instance.

    Args:
        storage_dir: Optional directory path for persistence.
            If not provided, defaults to ``data/knowledge_graph/``.

    Returns:
        A new KnowledgeGraph instance.
    """
    return KnowledgeGraph(storage_dir=storage_dir)
