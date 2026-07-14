"""AsimNexus Consensus module.

Provides consensus engines for clone voting, Raft distributed consensus,
and legacy compatibility shims.
"""

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
    get_consensus_engine,
    reset_consensus_engine,
)

from core.consensus.clone_consensus_voting import (
    CloneConsensusVoting,
    CloneVote,
    ConsensusRound,
)

from core.consensus.clone_consensus import (
    CloneConsensusEngine,
    DecisionLevel,
    ConsensusOutcome,
    ConsensusRoundResult,
    CloneConsensus,
)

from core.consensus.founder_to_clone_map import (
    FOUNDER_TO_CLONES,
    FOUNDER_CLONE_WEIGHTS,
    get_clone_for_founder,
    get_founders_for_clone,
    get_all_mappings,
    get_vote_weight,
    get_clone_name,
    clone_id_from_name,
)

from core.consensus.raft_engine import (
    RaftNodeState,
    RaftLogEntry,
    RaftSnapshot,
    RaftNode,
    ExtendedConsensusEngine,
)




__all__ = [
    # Core consensus
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
    # Clone consensus voting
    "CloneConsensusVoting",
    "CloneVote",
    "ConsensusRound",
    # Clone consensus
    "CloneConsensusEngine",
    "DecisionLevel",
    "ConsensusOutcome",
    "ConsensusRoundResult",
    "CloneConsensus",
    # Founder-to-clone mapping
    "FOUNDER_TO_CLONES",
    "FOUNDER_CLONE_WEIGHTS",
    "get_clone_for_founder",
    "get_founders_for_clone",
    "get_all_mappings",
    "get_vote_weight",
    "get_clone_name",
    "clone_id_from_name",
    # Raft consensus
    "RaftNodeState",
    "RaftLogEntry",
    "RaftSnapshot",
    "RaftNode",
    "ExtendedConsensusEngine",
    # Factory functions
    "get_consensus_engine",
    "reset_consensus_engine",
    "get_clone_consensus_engine",
    "get_raft_consensus_engine",
    "reset_raft_consensus_engine",
]
