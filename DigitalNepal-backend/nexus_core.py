#!/usr/bin/env python3
"""
AsimNexus = Digital World - Unified Core Interface
Integrates all modules + Country/Ministry templates
"""

import os
import sys
from pathlib import Path

# Fix: backend directory मा path
sys.path.insert(0, str(Path(__file__).parent))

# Core modules
from core.dharma_chakra.veto_engine import (
    DharmaVetoEngine, get_veto_engine, VetoLevel, VetoResult
)
from security.power_balance_constitution import (
    PowerBalanceConstitution, SectorControl, get_power_balance, BalanceResult
)
from core.consensus.clone_consensus_voting import (
    CloneConsensusVoting, get_consensus_engine, VoteChoice
)
from core.life_journey import (
    LifeJourneyModule, LifeStage, TransitionStatus, get_life_journey_module
)
from mesh.offline_sync_engine import (
    OfflineSyncEngine, get_offline_sync_engine, SyncPriority, SyncStatus
)

# Country/Ministry templates
from connectors.country_template import get_country, CountryConfig
from connectors.ministry_template import get_ministry, list_ministries

# ─── Unified World Interface ──────────────────────────────────────────────────────

class AsimNexusWorld:
    """
    Single interface for Digital World OS.
    Supports Nepal, India, USA, UK and all countries.
    """
    
    def __init__(self):
        self._veto = get_veto_engine()
        self._balance = get_power_balance()
        self._consensus = get_consensus_engine()
        self._life = get_life_journey_module()
        self._mesh = get_offline_sync_engine()
        
    def create_citizen(self, user_id: str, country: str = "NP", citizen_data: dict = None) -> dict:
        """Create citizen digital twin - birth stage"""
        profile = self._life.create_profile(user_id, metadata=citizen_data or {})
        return {
            "user_id": user_id,
            "country": country,
            "stage": profile.current_stage.value,
            "services": list(profile.services_active),
            "sector": "citizen"
        }
    
    def citizen_chat(self, message: str, user_id: str = "user", country: str = "NP") -> dict:
        """Citizen chat with Dharma Veto protection"""
        result = self._veto.check(message=message, sector="user", agent_id=user_id)
        if result.level == VetoLevel.BLOCK:
            return {"status": "blocked", "reason": result.reason, "country": country}
        if result.requires_human:
            return {"status": "requires_confirmation", "reason": result.reason, "country": country}
        return {"status": "approved", "response": f"Processed: {message}", "country": country}
    
    def company_action(self, sector: str, action: str, country: str = "NP") -> dict:
        """Company action through 49% threshold"""
        result = self._balance.check_decision(sector, is_public_decision=False)
        return {
            "verdict": result.verdict.value,
            "sector": sector,
            "country": country,
            "message": result.message,
            "status": "blocked" if result.verdict.value == "block" else "approved"
        }
    
    def government_action(self, sector: str, action: str, country: str = "NP") -> dict:
        """Government action through 51% threshold"""
        result = self._balance.check_decision(sector, is_public_decision=True)
        return {
            "verdict": result.verdict.value,
            "sector": sector,
            "country": country,
            "public_share": result.current_public_share,
            "status": "blocked" if result.verdict.value == "block" else "approved"
        }
    
    def founder_vote(self, topic: str, sector: str, country: str = "NP", votes: dict = None) -> dict:
        """15 Founder Clones 8/15 consensus voting"""
        round_obj = self._consensus.start_round(topic=topic, sector=sector)
        if votes:
            for voter, choice in votes.items():
                choice_enum = VoteChoice.APPROVE if choice == "approve" else VoteChoice.REJECT
                self._consensus.cast_vote(round_obj.round_id, voter, choice_enum)
        return {
            "round_id": round_obj.round_id,
            "outcome": round_obj.outcome,
            "country": country,
            "required_votes": 8
        }
    
    def sync_operation(self, crdt_id: str, operation: str, key: str = None, value: str = None) -> dict:
        """Queue operation for offline sync"""
        op = self._mesh.enqueue_operation(crdt_id, operation, key=key, value=value)
        return {"operation_id": op.id, "status": op.status.value}
    
    def mesh_status(self) -> dict:
        """Get sync status"""
        status = self._mesh.get_sync_status()
        return status.to_dict()
    
    def full_status(self) -> dict:
        """Get complete system status"""
        return {
            "governance": {
                "power_balance": self._balance.get_stats(),
                "founder_consensus": self._consensus.get_stats()
            },
            "security": {"veto": self._veto.get_stats()},
            "users": {"life_journey": self._life.get_stats()},
            "mesh": {"sync": self._mesh.get_stats()}
        }


# ─── Singleton ──────────────────────────────────────────────────────────────

_nexus_singleton = None

def get_nexus() -> AsimNexusWorld:
    global _nexus_singleton
    if _nexus_singleton is None:
        _nexus_singleton = AsimNexusWorld()
    return _nexus_singleton


if __name__ == "__main__":
    nexus = get_nexus()
    print("AsimNexus World OS initialized")
    print(f"Status: {nexus.full_status()}")