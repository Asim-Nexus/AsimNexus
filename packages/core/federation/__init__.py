"""
core/federation/__init__.py
AsimNexus — Federation Protocol & Global Governance
"""

from .global_federation import (
    GCounter,
    LWWRegister,
    ORSet,
    FederatedPeer,
    FederatedNodeState,
    GlobalFederationManager,
    get_federation,
)

from .federation_protocol_enhanced import (
    FederationHandshake,
    HandshakeStatus,
    HeartbeatMonitor,
    MessageType,
    PeerStatus,
    SyncStateMessage,
    ConsensusVoteMessage,
    SyncScope,
    PeerHealthRecord,
)

from .global_federation_governor import (
    GlobalFederationGovernor,
    JoinProposal,
    ProposalStatus,
    FederationEvent,
    FederationEventType,
    get_global_federation_governor,
    reset_global_federation_governor,
)

__all__ = [
    # CRDT primitives
    'GCounter',
    'LWWRegister',
    'ORSet',
    # Peer / state
    'FederatedPeer',
    'FederatedNodeState',
    'GlobalFederationManager',
    'get_federation',
    # Enhanced protocol
    'FederationHandshake',
    'HandshakeStatus',
    'HeartbeatMonitor',
    'MessageType',
    'PeerStatus',
    'SyncStateMessage',
    'ConsensusVoteMessage',
    'SyncScope',
    'PeerHealthRecord',
    # Global governor
    'GlobalFederationGovernor',
    'JoinProposal',
    'ProposalStatus',
    'FederationEvent',
    'FederationEventType',
    'get_global_federation_governor',
    'reset_global_federation_governor',
]
