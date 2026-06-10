
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Knowledge Graph - In-memory knowledge graph implementation
"""

import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """A node in the knowledge graph"""
    id: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    node_type: str = "default"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'label': self.label,
            'properties': self.properties,
            'type': self.node_type,
            'created_at': self.created_at
        }


@dataclass
class Edge:
    """An edge in the knowledge graph"""
    id: str
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'relation': self.relation,
            'properties': self.properties,
            'weight': self.weight,
            'created_at': self.created_at
        }


class KnowledgeGraph:
    """In-memory knowledge graph"""
    
    def __init__(self, graph_id: str = "default"):
        self.graph_id = graph_id
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self.adjacency: Dict[str, Set[str]] = {}  # source -> set of targets
        self.reverse_adjacency: Dict[str, Set[str]] = {}  # target -> set of sources
        self.node_counter = 0
        self.edge_counter = 0
        logger.info(f"Knowledge graph created: {graph_id}")
    
    def add_node(self, label: str, properties: Optional[Dict[str, Any]] = None, node_type: str = "default") -> Node:
        """Add a node to the graph"""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        node = Node(
            id=node_id,
            label=label,
            properties=properties or {},
            node_type=node_type
        )
        
        self.nodes[node_id] = node
        self.adjacency[node_id] = set()
        self.reverse_adjacency[node_id] = set()
        
        logger.debug(f"Node added: {node_id} - {label}")
        return node
    
    def add_edge(self, source_id: str, target_id: str, relation: str, properties: Optional[Dict[str, Any]] = None, weight: float = 1.0) -> Optional[Edge]:
        """Add an edge to the graph"""
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(f"Cannot add edge: source or target node not found")
            return None
        
        edge_id = f"edge_{self.edge_counter}"
        self.edge_counter += 1
        
        edge = Edge(
            id=edge_id,
            source=source_id,
            target=target_id,
            relation=relation,
            properties=properties or {},
            weight=weight
        )
        
        self.edges[edge_id] = edge
        self.adjacency[source_id].add(target_id)
        self.reverse_adjacency[target_id].add(source_id)
        
        logger.debug(f"Edge added: {source_id} -> {target_id} ({relation})")
        return edge
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get an edge by ID"""
        return self.edges.get(edge_id)
    
    def get_neighbors(self, node_id: str) -> List[Node]:
        """Get all neighbors of a node"""
        if node_id not in self.adjacency:
            return []
        return [self.nodes[nid] for nid in self.adjacency[node_id] if nid in self.nodes]
    
    def get_related_nodes(self, node_id: str, relation: str) -> List[Node]:
        """Get nodes connected by specific relation"""
        if node_id not in self.adjacency:
            return []
        
        related = []
        for target_id in self.adjacency[node_id]:
            for edge in self.edges.values():
                if edge.source == node_id and edge.target == target_id and edge.relation == relation:
                    if target_id in self.nodes:
                        related.append(self.nodes[target_id])
                    break
        
        return related
    
    def find_nodes_by_property(self, key: str, value: Any) -> List[Node]:
        """Find nodes by property"""
        return [node for node in self.nodes.values() if node.properties.get(key) == value]
    
    def find_nodes_by_type(self, node_type: str) -> List[Node]:
        """Find nodes by type"""
        return [node for node in self.nodes.values() if node.node_type == node_type]
    
    def search_nodes(self, query: str) -> List[Node]:
        """Search nodes by label or properties"""
        query_lower = query.lower()
        results = []
        
        for node in self.nodes.values():
            if query_lower in node.label.lower():
                results.append(node)
                continue
            
            for prop_value in node.properties.values():
                if isinstance(prop_value, str) and query_lower in prop_value.lower():
                    results.append(node)
                    break
        
        return results
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node and its edges"""
        if node_id not in self.nodes:
            return False
        
        # Delete all edges connected to this node
        edges_to_delete = [
            edge_id for edge_id, edge in self.edges.items()
            if edge.source == node_id or edge.target == node_id
        ]
        
        for edge_id in edges_to_delete:
            self.delete_edge(edge_id)
        
        # Delete node
        del self.nodes[node_id]
        del self.adjacency[node_id]
        del self.reverse_adjacency[node_id]
        
        logger.debug(f"Node deleted: {node_id}")
        return True
    
    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge"""
        if edge_id not in self.edges:
            return False
        
        edge = self.edges[edge_id]
        
        # Update adjacency
        if edge.source in self.adjacency:
            self.adjacency[edge.source].discard(edge.target)
        
        if edge.target in self.reverse_adjacency:
            self.reverse_adjacency[edge.target].discard(edge.source)
        
        del self.edges[edge_id]
        logger.debug(f"Edge deleted: {edge_id}")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            'graph_id': self.graph_id,
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'node_types': list(set(node.node_type for node in self.nodes.values())),
            'relations': list(set(edge.relation for edge in self.edges.values()))
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire graph to dictionary"""
        return {
            'graph_id': self.graph_id,
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges.values()],
            'stats': self.get_stats()
        }


def get_knowledge_graph(graph_id: str = "default") -> KnowledgeGraph:
    """Get knowledge graph instance"""
    return KnowledgeGraph(graph_id)
