
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Founder Clone Dashboard
Provides dashboard and reporting for founder clones
"""

import logging
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FounderMetrics:
    """Metrics for a founder clone"""
    founder_id: str
    name: str
    role: str
    decisions_made: int
    tasks_completed: int
    messages_sent: int
    votes_participated: int
    uptime: float


class FounderDashboard:
    """
    Founder Clone Dashboard
    
    Provides:
    - Real-time metrics
    - Performance tracking
    - Activity reports
    - Analytics
    """
    
    def __init__(self, founder_manager):
        self.founder_manager = founder_manager
        self.metrics_history: List[FounderMetrics] = []
        logger.info("Founder Dashboard initialized")
    
    def collect_metrics(self) -> List[FounderMetrics]:
        """Collect metrics for all founders"""
        metrics = []
        
        for founder_id, founder in self.founder_manager.founders.items():
            metric = FounderMetrics(
                founder_id=founder_id,
                name=founder.config.name,
                role=founder.config.role.value,
                decisions_made=len(founder.decision_history),
                tasks_completed=founder.state.tasks_completed,
                messages_sent=len(founder.message_queue),
                votes_participated=0,  # Would track actual votes
                uptime=1.0  # Would track actual uptime
            )
            metrics.append(metric)
        
        self.metrics_history.extend(metrics)
        return metrics
    
    def get_dashboard_data(self) -> Dict:
        """Get complete dashboard data"""
        metrics = self.collect_metrics()
        
        return {
            "total_founders": len(metrics),
            "total_decisions": sum(m.decisions_made for m in metrics),
            "total_tasks": sum(m.tasks_completed for m in metrics),
            "total_messages": sum(m.messages_sent for m in metrics),
            "founders": [
                {
                    "id": m.founder_id,
                    "name": m.name,
                    "role": m.role,
                    "decisions": m.decisions_made,
                    "tasks": m.tasks_completed,
                    "messages": m.messages_sent
                }
                for m in metrics
            ]
        }
    
    def generate_report(self) -> Dict:
        """Generate performance report"""
        metrics = self.collect_metrics()
        
        return {
            "report_type": "Founder Performance",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_founders": len(metrics),
                "active_founders": len([m for m in metrics if m.uptime > 0]),
                "total_decisions": sum(m.decisions_made for m in metrics),
                "total_tasks": sum(m.tasks_completed for m in metrics)
            },
            "by_role": self._group_by_role(metrics)
        }
    
    def _group_by_role(self, metrics: List[FounderMetrics]) -> Dict:
        """Group metrics by role"""
        role_groups = {}
        for m in metrics:
            if m.role not in role_groups:
                role_groups[m.role] = {
                    "count": 0,
                    "decisions": 0,
                    "tasks": 0
                }
            role_groups[m.role]["count"] += 1
            role_groups[m.role]["decisions"] += m.decisions_made
            role_groups[m.role]["tasks"] += m.tasks_completed
        return role_groups
