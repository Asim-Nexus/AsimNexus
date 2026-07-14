"""
Extended Consensus Engine Proxy Layer (Legacy Shim)
====================================================
Provides backward-compatible imports for code referencing core.consensus_engine.
All actual implementation has been moved to core/consensus/raft_engine.py.

This shim re-exports everything from the canonical location so existing
imports (e.g. `from core.consensus_engine import ConsensusEngine`) continue
to work without modification.
"""

import logging
from typing import Dict, Any, Optional, List

from core.consensus.raft_engine import (
    RaftNodeState,
    RaftLogEntry,
    RaftSnapshot,
    RaftNode,
    ExtendedConsensusEngine,
    get_consensus_engine,
    reset_consensus_engine,
)

from core.consensus.consensus_engine import (
    ConsensusEngine,
    VotingMode,
    VoteChoice,
    ProposalStatus,
    ArbiterDecision,
    Voter,
    Vote,
    Proposal,
    ConsensusResult,
    Delegation,
    CloneConsensusFacade,
)

logger = logging.getLogger("AsimNexus.ConsensusEngine.Shim")

# Re-export all public symbols for backward compatibility
__all__ = [
    "RaftNodeState",
    "RaftLogEntry",
    "RaftSnapshot",
    "RaftNode",
    "ExtendedConsensusEngine",
    "ConsensusEngine",
    "VotingMode",
    "VoteChoice",
    "ProposalStatus",
    "ArbiterDecision",
    "Voter",
    "Vote",
    "Proposal",
    "ConsensusResult",
    "Delegation",
    "CloneConsensusFacade",
    "get_consensus_engine",
    "reset_consensus_engine",
]
