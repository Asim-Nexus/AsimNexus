
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
Citizen Agent Mode - Estonia-style Participation
Voluntary global agents contributing to security (Estonia Cyber Defence League)
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

class AgentStatus(Enum):
    OFFLINE = "offline"
    STANDBY = "standby"
    ACTIVE = "active"
    ENGAGED = "engaged"

class ContributionType(Enum):
    THREAT_REPORT = "threat_report"
    VULNERABILITY_REPORT = "vulnerability_report"
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    EDUCATION = "education"

class CitizenAgentMode:
    def __init__(self):
        self.agents = {}
        self.contributions = []
        self.credit_system = {}
        
    def register_agent(self, agent_id: str, skills: List[str]):
        """Register a citizen agent"""
        agent = {
            "id": agent_id,
            "skills": skills,
            "status": AgentStatus.STANDBY.value,
            "joined_at": datetime.now().isoformat(),
            "contributions_count": 0,
            "credits": 0
        }
        self.agents[agent_id] = agent
        self.credit_system[agent_id] = 0
        return agent
        
    def activate_agent(self, agent_id: str):
        """Activate agent for duty"""
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = AgentStatus.ACTIVE.value
            
    def submit_contribution(self, agent_id: str, contribution_type: ContributionType, data: Dict):
        """Submit security contribution"""
        if agent_id not in self.agents:
            return None
            
        contribution = {
            "agent_id": agent_id,
            "type": contribution_type.value,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "status": "pending_review"
        }
        self.contributions.append(contribution)
        
        # Update agent stats
        self.agents[agent_id]["contributions_count"] += 1
        self.agents[agent_id]["credits"] += self._calculate_credits(contribution_type)
        self.credit_system[agent_id] = self.agents[agent_id]["credits"]
        
        return contribution
        
    def _calculate_credits(self, contribution_type: ContributionType) -> int:
        """Calculate credits based on contribution type"""
        credit_values = {
            ContributionType.THREAT_REPORT: 10,
            ContributionType.VULNERABILITY_REPORT: 25,
            ContributionType.ANALYSIS: 15,
            ContributionType.VALIDATION: 5,
            ContributionType.EDUCATION: 20
        }
        return credit_values.get(contribution_type, 5)
        
    def get_agent_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top agents by credits"""
        sorted_agents = sorted(
            self.agents.values(),
            key=lambda x: x["credits"],
            reverse=True
        )
        return sorted_agents[:limit]
        
    def get_global_stats(self) -> Dict:
        """Get global citizen agent statistics"""
        return {
            "total_agents": len(self.agents),
            "active_agents": len([a for a in self.agents.values() if a["status"] == AgentStatus.ACTIVE.value]),
            "total_contributions": len(self.contributions),
            "total_credits_distributed": sum(self.credit_system.values())
        }
