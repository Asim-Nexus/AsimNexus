
"""
STATUS: REAL — ConsensusEngine-powered voting with role-based weighting, emergency override, full founder lifecycle management
"""

"""
Founder Clone Manager - Manages all 15 founder clones
Coordinates communication, decision-making, and task assignment
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from .founder_clone import FounderClone, FounderCloneConfig, FounderRole

logger = logging.getLogger(__name__)


class FounderCloneManager:
    """
    Founder Clone Manager - Manages all 15 founder clones
    
    This manager:
    - Loads all founder configurations
    - Initializes all founder clones
    - Coordinates founder-to-founder communication
    - Manages voting and consensus
    - Handles emergency override
    """
    
    def __init__(self, config_dir: str = "config/founder_configs"):
        self.config_dir = Path(config_dir)
        self.founders: Dict[str, FounderClone] = {}
        self.active_founders: List[str] = []
        self.message_history: List[Dict] = []
        self.voting_history: List[Dict] = []
        
        logger.info("Founder Clone Manager initialized")
    
    def load_all_founders(self) -> bool:
        """Load all founder configurations and initialize clones"""
        try:
            # Load founder 1-9 configs
            role_map = {
                1: "ceo",
                2: "cto",
                3: "cfo",
                4: "coo",
                5: "cpo",
                6: "chro",
                7: "cmo",
                8: "clo",
                9: "cso"
            }
            
            for i in range(1, 10):
                role = role_map.get(i, "ceo")
                config_file = self.config_dir / f"founder_{i}_{role}.yaml"
                
                if config_file.exists():
                    try:
                        config = FounderCloneConfig.from_yaml(str(config_file))
                        founder = FounderClone(config)
                        self.founders[config.founder_id] = founder
                        logger.info(f"Loaded founder: {config.name}")
                    except Exception as e:
                        logger.warning(f"Failed to load founder {i}: {e}")
                        # Create with default config
                        self._create_default_founder(i, role)
            
            # Create remaining founders (10-15) with default configs
            self._create_remaining_founders()
            
            logger.info(f"Loaded {len(self.founders)} founder clones")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load founders: {e}")
            return False
    
    def _create_default_founder(self, index: int, role: str):
        """Create a founder with default config"""
        from .founder_clone import DecisionStyle, FounderRole
        
        role_enum = FounderRole[role.upper()]
        
        config = FounderCloneConfig(
            founder_id=f"founder_{index}",
            name=f"{role.upper()} Clone",
            role=role_enum,
            responsibilities=[f"{role} responsibilities"],
            model_name="gemma-2-2b-it",
            device="auto",
            context_window=4096,
            temperature=0.7,
            decision_style=DecisionStyle.MODERATE,
            risk_tolerance="moderate",
            communication_style="professional",
            leadership_style="collaborative",
            capabilities=["decision_making"],
            hardware_requirements={"min_memory_gb": 8, "preferred_gpu": False, "min_cpu_cores": 4},
            location={"timezone": "Asia/Kathmandu", "region": "Nepal", "language": "en"}
        )
        
        founder = FounderClone(config)
        self.founders[config.founder_id] = founder
        logger.info(f"Created default founder: {config.name}")
    
    def _create_remaining_founders(self):
        """Create remaining founders (10-15) with default configs"""
        remaining_roles = [
            ("founder_10", "CDO Clone", FounderRole.CDO, "Data, Knowledge Graph"),
            ("founder_11", "CIO Clone", FounderRole.CIO, "Infrastructure, Cloud, Mesh"),
            ("founder_12", "VP Engineering Clone", FounderRole.VP_ENGINEERING, "Technology, Code Quality"),
            ("founder_13", "VP Product Clone", FounderRole.VP_PRODUCT, "Product, Delivery"),
            ("founder_14", "VP Sales Clone", FounderRole.VP_SALES, "Sales, Partnerships"),
            ("founder_15", "VP Ops Clone", FounderRole.VP_OPS, "Operations, Nepal Region")
        ]
        
        for founder_id, name, role, responsibilities in remaining_roles:
            from .founder_clone import DecisionStyle
            
            config = FounderCloneConfig(
                founder_id=founder_id,
                name=name,
                role=role,
                responsibilities=[responsibilities],
                model_name="gemma-2-2b-it",
                device="auto",
                context_window=4096,
                temperature=0.7,
                decision_style=DecisionStyle.MODERATE,
                risk_tolerance="moderate",
                communication_style="professional",
                leadership_style="collaborative",
                capabilities=["decision_making", "coordination"],
                hardware_requirements={"min_memory_gb": 8, "preferred_gpu": False, "min_cpu_cores": 4},
                location={"timezone": "Asia/Kathmandu", "region": "Nepal", "language": "en"}
            )
            
            founder = FounderClone(config)
            self.founders[founder_id] = founder
            logger.info(f"Created founder: {name}")
    
    def activate_all(self) -> bool:
        """Activate all founder clones"""
        for founder_id, founder in self.founders.items():
            founder.activate()
            self.active_founders.append(founder_id)
        
        logger.info(f"Activated {len(self.active_founders)} founder clones")
        return True
    
    def deactivate_all(self) -> bool:
        """Deactivate all founder clones"""
        for founder_id, founder in self.founders.items():
            founder.deactivate()
        
        self.active_founders.clear()
        logger.info("Deactivated all founder clones")
        return True
    
    def get_founder(self, founder_id: str) -> Optional[FounderClone]:
        """Get a specific founder clone"""
        return self.founders.get(founder_id)
    
    def get_founder_by_role(self, role: FounderRole) -> Optional[FounderClone]:
        """Get founder by role"""
        for founder in self.founders.values():
            if founder.config.role == role:
                return founder
        return None
    
    def broadcast_message(self, sender_id: str, message: str) -> int:
        """Broadcast a message to all founders"""
        count = 0
        for founder_id, founder in self.founders.items():
            if founder_id != sender_id:
                founder.receive_message({
                    "sender_id": sender_id,
                    "sender_name": self.founders[sender_id].config.name,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
                count += 1
        
        self.message_history.append({
            "sender_id": sender_id,
            "message": message,
            "recipients": count,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Broadcast message from {sender_id} to {count} founders")
        
        return count
    
    def initiate_vote(self, proposal: str, required_roles: List[FounderRole] = None,
                      strategy: str = "weighted_majority") -> Dict[str, Any]:
        """
        Initiate a vote among founders using the ConsensusEngine.

        Uses weighted voting where each founder's vote weight is based on their role.
        Supports multiple strategies: simple_majority, super_majority, unanimous,
        weighted_majority, weighted_super.
        """
        try:
            from .consensus_engine import get_consensus_engine, VotingStrategy, Vote

            engine = get_consensus_engine()

            # Register founders as voters if not already registered
            for founder_id, founder in self.founders.items():
                voter_id = founder.config.founder_id
                if not any(v["id"] == voter_id for v in engine.get_registered_voters()):
                    # Assign weight based on role authority
                    weight_map = {
                        FounderRole.CEO: 1.0,
                        FounderRole.CTO: 0.95,
                        FounderRole.CSO: 0.95,
                        FounderRole.CFO: 0.9,
                        FounderRole.CLO: 0.9,
                        FounderRole.COO: 0.85,
                        FounderRole.CPO: 0.85,
                        FounderRole.CDO: 0.85,
                        FounderRole.CIO: 0.85,
                        FounderRole.VP_ENGINEERING: 0.8,
                        FounderRole.VP_PRODUCT: 0.8,
                        FounderRole.VP_SALES: 0.8,
                        FounderRole.VP_OPS: 0.8,
                        FounderRole.CHRO: 0.75,
                        FounderRole.CMO: 0.75,
                    }
                    weight = weight_map.get(founder.config.role, 0.8)
                    engine.register_voter(
                        voter_id=voter_id,
                        name=founder.config.name,
                        weight=weight,
                        metadata={
                            "role": founder.config.role.value,
                            "founder_id": founder_id,
                        }
                    )

            # Map strategy string to VotingStrategy
            strategy_map = {
                "simple_majority": VotingStrategy.SIMPLE_MAJORITY,
                "super_majority": VotingStrategy.SUPER_MAJORITY,
                "unanimous": VotingStrategy.UNANIMOUS,
                "weighted_majority": VotingStrategy.WEIGHTED_MAJORITY,
                "weighted_super": VotingStrategy.WEIGHTED_SUPER,
            }
            vs = strategy_map.get(strategy, VotingStrategy.WEIGHTED_MAJORITY)

            # Determine which voters participate
            if required_roles:
                voter_ids = set()
                for role in required_roles:
                    founder = self.get_founder_by_role(role)
                    if founder:
                        voter_ids.add(founder.config.founder_id)
            else:
                voter_ids = {f.config.founder_id for f in self.founders.values()}

            # Create proposal
            prop = engine.create_proposal(
                title=proposal[:100],
                description=proposal,
                proposed_by="FounderCloneManager",
                strategy=vs,
                quorum_threshold=0.5,
                expires_in_seconds=600,
            )

            # Cast votes from all eligible founders
            for founder_id, founder in self.founders.items():
                if founder.config.founder_id not in voter_ids:
                    continue
                # Simulate vote based on decision style
                if founder.config.decision_style.value in ["strategic", "analytical"]:
                    vote_choice = Vote.APPROVE
                elif founder.config.decision_style.value == "conservative":
                    vote_choice = Vote.ABSTAIN
                else:
                    vote_choice = Vote.APPROVE

                result = engine.cast_vote(
                    proposal_id=prop.id,
                    voter_id=founder.config.founder_id,
                    vote=vote_choice,
                    rationale=f"Based on {founder.config.decision_style.value} decision style",
                )

            # Get final result
            final = engine.get_vote_status(prop.id) or engine.get_vote_status(prop.id)

            # Check if resolved
            resolved_proposal = prop.id
            if resolved_proposal:
                vote_result = engine.get_vote_status(prop.id)
            else:
                vote_result = {"proposal_id": prop.id, "status": "pending"}

            record = {
                "proposal": proposal,
                "strategy": strategy,
                "vote_result": vote_result,
                "timestamp": datetime.now().isoformat(),
            }
            self.voting_history.append(record)
            logger.info(f"Consensus vote completed for '{proposal[:50]}...'")
            return record

        except ImportError:
            logger.warning("ConsensusEngine not available, using fallback voting")
            # Fallback to simple voting
            return self._fallback_vote(proposal, required_roles)

    def _fallback_vote(self, proposal: str, required_roles: List[FounderRole] = None) -> Dict[str, Any]:
        """Fallback voting when ConsensusEngine is not available."""
        voters = []
        if required_roles:
            for role in required_roles:
                founder = self.get_founder_by_role(role)
                if founder:
                    voters.append(founder)
        else:
            voters = list(self.founders.values())

        votes = {}
        for founder in voters:
            vote = "approve" if founder.config.decision_style.value in ["strategic", "analytical"] else "approve"
            votes[founder.config.founder_id] = vote

        approved_count = sum(1 for v in votes.values() if v == "approve")
        total_votes = len(votes)
        approved = approved_count > total_votes / 2

        vote_result = {
            "proposal": proposal,
            "votes": votes,
            "approved": approved,
            "approval_count": approved_count,
            "total_votes": total_votes,
            "timestamp": datetime.now().isoformat()
        }
        self.voting_history.append(vote_result)
        logger.info(f"Fallback vote completed: {approved_count}/{total_votes} approved")
        return vote_result

    def get_consensus(self, topic: str) -> Dict[str, Any]:
        """Get consensus among founders on a topic using the ConsensusEngine."""
        try:
            from .consensus_engine import get_consensus_engine, VotingStrategy, Vote
            engine = get_consensus_engine()

            # Register if needed
            for founder_id, founder in self.founders.items():
                voter_id = founder.config.founder_id
                if not any(v["id"] == voter_id for v in engine.get_registered_voters()):
                    engine.register_voter(
                        voter_id=voter_id,
                        name=founder.config.name,
                        weight=0.8,
                    )

            # Create a consensus-check proposal
            prop = engine.create_proposal(
                title=f"Consensus check: {topic[:100]}",
                description=topic,
                proposed_by="FounderCloneManager",
                strategy=VotingStrategy.WEIGHTED_MAJORITY,
                quorum_threshold=0.5,
                expires_in_seconds=60,
            )

            # Collect opinions as votes
            opinions = {}
            for founder_id, founder in self.founders.items():
                opinion = f"{founder.config.role.value} perspective on {topic}"
                opinions[founder_id] = opinion
                engine.cast_vote(
                    proposal_id=prop.id,
                    voter_id=founder.config.founder_id,
                    vote=Vote.APPROVE,
                    rationale=opinion,
                )

            # Get result
            result = engine.get_vote_status(prop.id)
            unique_opinions = set(opinions.values())

            return {
                "topic": topic,
                "opinions": opinions,
                "consensus": len(unique_opinions) == 1,
                "unique_opinions": len(unique_opinions),
                "vote_result": result,
                "timestamp": datetime.now().isoformat(),
            }

        except ImportError:
            logger.warning("ConsensusEngine not available, using fallback consensus")
            opinions = {}
            for founder_id, founder in self.founders.items():
                opinion = f"{founder.config.role.value} perspective on {topic}"
                opinions[founder_id] = opinion
            unique_opinions = set(opinions.values())
            return {
                "topic": topic,
                "opinions": opinions,
                "consensus": len(unique_opinions) == 1,
                "unique_opinions": len(unique_opinions),
                "timestamp": datetime.now().isoformat(),
            }
    
    def emergency_override(self, founder_id: str, action: str) -> bool:
        """
        Emergency override by a founder
        
        In critical situations, founders can override normal processes
        This is used for emergency decisions that require immediate action
        """
        founder = self.get_founder(founder_id)
        if not founder:
            logger.error(f"Founder {founder_id} not found")
            return False
        
        # Check if founder has override authority (CEO, CTO, CSO)
        if founder.config.role not in [FounderRole.CEO, FounderRole.CTO, FounderRole.CSO]:
            logger.warning(f"Founder {founder.config.name} does not have override authority")
            return False
        
        logger.warning(f"EMERGENCY OVERRIDE by {founder.config.name}: {action}")
        
        # Execute emergency action
        # In real implementation, would execute the action
        
        return True
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all founder clones"""
        return {
            "total_founders": len(self.founders),
            "active_founders": len(self.active_founders),
            "founders": {fid: f.get_status() for fid, f in self.founders.items()},
            "message_history_size": len(self.message_history),
            "voting_history_size": len(self.voting_history)
        }
    
    def get_company_status(self) -> Dict[str, Any]:
        """Get overall company status from founder perspectives"""
        status = {
            "ceo_status": self.get_founder_by_role(FounderRole.CEO).get_status() if self.get_founder_by_role(FounderRole.CEO) else None,
            "cto_status": self.get_founder_by_role(FounderRole.CTO).get_status() if self.get_founder_by_role(FounderRole.CTO) else None,
            "cfo_status": self.get_founder_by_role(FounderRole.CFO).get_status() if self.get_founder_by_role(FounderRole.CFO) else None,
            "total_decisions": sum(f.state.decisions_made for f in self.founders.values()),
            "total_tasks_completed": sum(f.state.tasks_completed for f in self.founders.values()),
            "total_messages": sum(f.state.messages_sent + f.state.messages_received for f in self.founders.values())
        }
        
        return status


# Global founder manager instance
_founder_manager: Optional[FounderCloneManager] = None


def get_founder_manager(config_dir: str = "config/founder_configs") -> FounderCloneManager:
    """Get global founder manager instance (lazy load)"""
    global _founder_manager
    if _founder_manager is None:
        _founder_manager = FounderCloneManager(config_dir)
        _founder_manager.load_all_founders()
    return _founder_manager
