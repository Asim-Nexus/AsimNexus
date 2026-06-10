
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Context Compactor
===========================
Context compaction and optimization
Reduces context size while preserving important information
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ContextCompactor")


class CompactionStrategy(Enum):
    """Compaction strategies"""
    IMPORTANCE_BASED = "importance_based"
    TEMPORAL = "temporal"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


@dataclass
class CompactionResult:
    """Result of context compaction"""
    original_size: int
    compressed_size: int
    compression_ratio: float
    preserved_items: int
    removed_items: int
    strategy: CompactionStrategy


class ContextCompactor:
    """
    Context Compactor
    
    Provides:
    - Context analysis
    - Importance scoring
    - Context compaction
    - Size optimization
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ContextCompactor")
        self.compaction_history: List[CompactionResult] = []
    
    def analyze_context(self, context: Dict[str, Any]) -> Dict:
        """
        Analyze context to identify important items
        
        Args:
            context: Context dictionary
            
        Returns:
            Analysis results
        """
        total_items = len(context)
        importance_scores = {}
        
        for key, value in context.items():
            score = self._calculate_importance(key, value)
            importance_scores[key] = score
        
        return {
            "total_items": total_items,
            "importance_scores": importance_scores,
            "average_importance": sum(importance_scores.values()) / total_items if total_items > 0 else 0
        }
    
    def _calculate_importance(self, key: str, value: Any) -> float:
        """Calculate importance score for a context item"""
        score = 0.5  # Base score
        
        # Check for important keywords in key
        important_keywords = ["user", "task", "goal", "important", "critical"]
        for keyword in important_keywords:
            if keyword.lower() in key.lower():
                score += 0.2
        
        # Check value size (smaller values might be more important)
        value_str = str(value)
        if len(value_str) < 100:
            score += 0.1
        elif len(value_str) > 1000:
            score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def compact_context(
        self,
        context: Dict[str, Any],
        target_size: Optional[int] = None,
        strategy: CompactionStrategy = CompactionStrategy.IMPORTANCE_BASED
    ) -> tuple[Dict[str, Any], CompactionResult]:
        """
        Compact context to reduce size
        
        Args:
            context: Context dictionary
            target_size: Target size in items
            strategy: Compaction strategy
            
        Returns:
            Compact context and result
        """
        original_size = len(context)
        
        if target_size is None:
            target_size = max(10, int(original_size * 0.7))
        
        analysis = self.analyze_context(context)
        
        if strategy == CompactionStrategy.IMPORTANCE_BASED:
            compact_context = self._compact_by_importance(
                context,
                analysis["importance_scores"],
                target_size
            )
        else:
            # Default to importance-based
            compact_context = self._compact_by_importance(
                context,
                analysis["importance_scores"],
                target_size
            )
        
        compressed_size = len(compact_context)
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        result = CompactionResult(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            preserved_items=compressed_size,
            removed_items=original_size - compressed_size,
            strategy=strategy
        )
        
        self.compaction_history.append(result)
        
        self.logger.info(f"Compacted context: {original_size} -> {compressed_size} items")
        
        return compact_context, result
    
    def _compact_by_importance(
        self,
        context: Dict[str, Any],
        scores: Dict[str, float],
        target_size: int
    ) -> Dict[str, Any]:
        """Compact context by importance scores"""
        # Sort items by importance
        sorted_items = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Keep top items
        top_items = sorted_items[:target_size]
        
        return {key: context[key] for key, _ in top_items}
    
    def get_compaction_history(self, limit: int = 50) -> List[Dict]:
        """Get compaction history"""
        return [
            {
                "original_size": r.original_size,
                "compressed_size": r.compressed_size,
                "compression_ratio": r.compression_ratio,
                "strategy": r.strategy.value
            }
            for r in self.compaction_history[-limit:]
        ]
    
    def get_stats(self) -> Dict:
        """Get compactor statistics"""
        if not self.compaction_history:
            return {"total_compactions": 0}
        
        avg_ratio = sum(r.compression_ratio for r in self.compaction_history) / len(self.compaction_history)
        
        return {
            "total_compactions": len(self.compaction_history),
            "average_compression_ratio": round(avg_ratio, 3),
            "total_items_saved": sum(r.original_size - r.compressed_size for r in self.compaction_history)
        }
