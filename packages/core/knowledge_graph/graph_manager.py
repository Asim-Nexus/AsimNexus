
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Graph Manager - Manages multiple knowledge graphs
"""

import logging
from typing import Dict, Optional, Any
from .knowledge_graph import KnowledgeGraph, Node, Edge, get_knowledge_graph

logger = logging.getLogger(__name__)


class GraphManager:
    """Manages multiple knowledge graphs"""
    
    def __init__(self):
        self.graphs: Dict[str, KnowledgeGraph] = {}
        logger.info("Graph Manager initialized")
    
    def create_graph(self, graph_id: str) -> KnowledgeGraph:
        """Create a new knowledge graph"""
        if graph_id in self.graphs:
            logger.warning(f"Graph already exists: {graph_id}")
            return self.graphs[graph_id]
        
        graph = KnowledgeGraph(graph_id)
        self.graphs[graph_id] = graph
        logger.info(f"Graph created: {graph_id}")
        return graph
    
    def get_graph(self, graph_id: str) -> Optional[KnowledgeGraph]:
        """Get an existing graph"""
        return self.graphs.get(graph_id)
    
    def delete_graph(self, graph_id: str):
        """Delete a graph"""
        if graph_id in self.graphs:
            del self.graphs[graph_id]
            logger.info(f"Graph deleted: {graph_id}")
    
    def list_graphs(self) -> list:
        """List all graph IDs"""
        return list(self.graphs.keys())
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all graphs"""
        return {
            'total_graphs': len(self.graphs),
            'graph_ids': list(self.graphs.keys()),
            'graph_stats': {
                graph_id: graph.get_stats()
                for graph_id, graph in self.graphs.items()
            }
        }


def get_graph_manager() -> GraphManager:
    """Get graph manager instance"""
    return GraphManager()
