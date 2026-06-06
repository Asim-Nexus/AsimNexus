#!/usr/bin/env python3
"""
tests/real/test_federation_protocol_enhanced.py
AsimNexus — Federation Protocol Enhanced Tests

Tests for core/federation/federation_protocol_enhanced.py:
  - FederationHandshake: creation, serialization, lifecycle
  - SyncStateMessage: encoding/decoding, scope handling, TTL
  - ConsensusVoteMessage: creation, serialization, edge cases
  - PeerHealthRecord: health tracking
  - HeartbeatMonitor: peer registration, health tracking, timeouts
  - Utility functions: create_did_challenge, verify_handshake_signature
"""

import asyncio
import time
import pytest
from typing import Dict, Any

from core.federation.federation_protocol_enhanced import (
    FederationHandshake,
    HandshakeStatus,
    SyncStateMessage,
    SyncScope,
    ConsensusVoteMessage,
    PeerHealthRecord,
    PeerStatus,
    HeartbeatMonitor,
    create_did_challenge,
    verify_handshake_signature,
    HANDSHAKE_TIMEOUT_SEC,
    SYNC_INTERVAL_SEC,
    HEARTBEAT_INTERVAL_SEC,
    HEARTBEAT_TIMEOUT_SEC,
    MAX_SYNC_BATCH,
)


# ── Constants Tests ─────────────────────────────────────────────────────────

class TestConstants:
    """Protocol constant values."""

    def test_handshake_timeout(self):
        assert HANDSHAKE_TIMEOUT_SEC == 30.0

    def test_sync_interval(self):
        assert SYNC_INTERVAL_SEC == 60

    def test_heartbeat_interval(self):
        assert HEARTBEAT_INTERVAL_SEC == 15

    def test_heartbeat_timeout(self):
        assert HEARTBEAT_TIMEOUT_SEC == 45.0

    def test_max_sync_batch(self):
        assert MAX_SYNC_BATCH == 100


# ── Handshake Status Enum Tests ─────────────────────────────────────────────

class TestHandshakeStatus:
    """HandshakeStatus enum values."""

    def test_values(self):
        assert HandshakeStatus.PENDING.value == "pending"
        assert HandshakeStatus.CHALLENGED.value == "challenged"
        assert HandshakeStatus.VERIFIED.value == "verified"
        assert HandshakeStatus.REJECTED.value == "rejected"
        assert HandshakeStatus.TIMEOUT.value == "timeout"

    def test_distinct(self):
        values = {s.value for s in HandshakeStatus}
        assert len(values) == 5


# ── FederationHandshake Tests ───────────────────────────────────────────────

class TestFederationHandshake:
    """FederationHandshake creation and serialization tests."""

    def test_create_default(self):
        hs = FederationHandshake()
        assert hs.handshake_id is not None
        assert len(hs.handshake_id) == 16
        assert hs.status == HandshakeStatus.PENDING
        assert hs.nonce is not None
        assert len(hs.nonce) == 24
        assert hs.created_at > 0
        assert hs.completed_at is None

    def test_create_with_fields(self):
        hs = FederationHandshake(
            initiator_did="did:example:initiator",
            initiator_node_id="node_initiator",
            peer_did="did:example:peer",
            peer_node_id="node_peer",
        )
        assert hs.initiator_did == "did:example:initiator"
        assert hs.initiator_node_id == "node_initiator"
        assert hs.peer_did == "did:example:peer"
        assert hs.peer_node_id == "node_peer"

    def test_elapsed_property(self):
        hs = FederationHandshake()
        time.sleep(0.01)
        assert hs.elapsed > 0.0

    def test_to_dict(self):
        hs = FederationHandshake(
            initiator_did="did:example:i",
            peer_did="did:example:p",
            status=HandshakeStatus.CHALLENGED,
        )
        d = hs.to_dict()
        assert d["initiator_did"] == "did:example:i"
        assert d["peer_did"] == "did:example:p"
        assert d["status"] == HandshakeStatus.CHALLENGED
        assert "handshake_id" in d
        assert "nonce" in d
        assert "created_at" in d

    def test_from_dict(self):
        hs = FederationHandshake(
            handshake_id="test_id_123",
            initiator_did="did:from",
            peer_did="did:to",
            status=HandshakeStatus.VERIFIED,
            session_id="sess_abc",
        )
        d = hs.to_dict()
        hs2 = FederationHandshake.from_dict(d)
        assert hs2.handshake_id == "test_id_123"
        assert hs2.initiator_did == "did:from"
        assert hs2.peer_did == "did:to"
        assert hs2.status == HandshakeStatus.VERIFIED
        assert hs2.session_id == "sess_abc"

    def test_from_dict_filters_unknown_keys(self):
        d = {
            "handshake_id": "known",
            "initiator_did": "did:known",
            "unknown_field": "should_be_filtered",
        }
        hs = FederationHandshake.from_dict(d)
        assert hs.handshake_id == "known"
        assert not hasattr(hs, "unknown_field")

    def test_lifecycle_transition(self):
        """Test a full handshake lifecycle via dict."""
        hs = FederationHandshake(
            initiator_did="did:a",
            initiator_node_id="node_a",
            peer_did="did:b",
            peer_node_id="node_b",
            nonce="nonce_123",
        )
        assert hs.status == HandshakeStatus.PENDING

        # Step 2: challenge
        hs.challenge_nonce = "challenge_456"
        hs.status = HandshakeStatus.CHALLENGED
        assert hs.status == HandshakeStatus.CHALLENGED

        # Step 3: response
        hs.signed_challenge = "signed_789"
        hs.status = HandshakeStatus.VERIFIED
        hs.session_id = "session_final"
        hs.completed_at = time.time()
        assert hs.status == HandshakeStatus.VERIFIED
        assert hs.completed_at is not None

    def test_metadata(self):
        hs = FederationHandshake(metadata={"version": "1.0", "protocol": "enhanced"})
        assert hs.metadata["version"] == "1.0"
        assert hs.metadata["protocol"] == "enhanced"


# ── SyncScope Enum Tests ────────────────────────────────────────────────────

class TestSyncScope:
    """SyncScope enum values."""

    def test_values(self):
        assert SyncScope.DELTA_ONLY.value == "delta_only"
        assert SyncScope.FULL_STATE.value == "full_state"
        assert SyncScope.CONSENSUS_ONLY.value == "consensus_only"
        assert SyncScope.GOVERNANCE_ONLY.value == "governance_only"

    def test_distinct(self):
        values = {s.value for s in SyncScope}
        assert len(values) == 4


# ── SyncStateMessage Tests ──────────────────────────────────────────────────

class TestSyncStateMessage:
    """SyncStateMessage encoding/decoding and serialization tests."""

    def test_create_default(self):
        msg = SyncStateMessage()
        assert msg.message_id is not None
        assert len(msg.message_id) == 16
        assert msg.scope == SyncScope.DELTA_ONLY
        assert msg.ttl == 3
        assert msg.state_packet == {}

    def test_create_with_fields(self):
        msg = SyncStateMessage(
            sender_node_id="node_sender",
            sender_did="did:sender",
            scope=SyncScope.FULL_STATE,
            state_packet={"key": "value"},
            round_id="round_1",
            ttl=2,
        )
        assert msg.sender_node_id == "node_sender"
        assert msg.sender_did == "did:sender"
        assert msg.scope == SyncScope.FULL_STATE
        assert msg.state_packet == {"key": "value"}
        assert msg.round_id == "round_1"
        assert msg.ttl == 2

    def test_to_dict(self):
        msg = SyncStateMessage(
            message_id="msg_001",
            sender_node_id="n1",
            sender_did="did:n1",
            scope=SyncScope.GOVERNANCE_ONLY,
            state_packet={"prop": "val"},
            ttl=1,
        )
        d = msg.to_dict()
        assert d["message_id"] == "msg_001"
        assert d["sender_node_id"] == "n1"
        assert d["scope"] == "governance_only"
        assert d["state_packet"] == {"prop": "val"}
        assert d["ttl"] == 1
        assert "timestamp" in d

    def test_from_dict(self):
        d = {
            "message_id": "restored_msg",
            "sender_node_id": "n_restored",
            "sender_did": "did:restored",
            "scope": "delta_only",
            "state_packet": {"restored": True},
            "round_id": "r1",
            "timestamp": 12345.0,
            "ttl": 5,
            "signature": "sig_abc",
        }
        msg = SyncStateMessage.from_dict(d)
        assert msg.message_id == "restored_msg"
        assert msg.sender_node_id == "n_restored"
        assert msg.scope == SyncScope.DELTA_ONLY
        assert msg.state_packet == {"restored": True}
        assert msg.round_id == "r1"
        assert msg.ttl == 5
        assert msg.signature == "sig_abc"

    def test_from_dict_invalid_scope_falls_back(self):
        d = {
            "scope": "invalid_scope_value",
            "state_packet": {},
        }
        msg = SyncStateMessage.from_dict(d)
        assert msg.scope == SyncScope.DELTA_ONLY

    def test_from_dict_missing_keys(self):
        msg = SyncStateMessage.from_dict({})
        assert msg.sender_node_id == ""
        assert msg.sender_did == ""
        assert msg.scope == SyncScope.DELTA_ONLY
        assert msg.state_packet == {}
        assert msg.ttl == 3

    def test_ttl_decrement(self):
        msg = SyncStateMessage(ttl=3)
        msg.ttl -= 1
        assert msg.ttl == 2

    def test_message_uniqueness(self):
        m1 = SyncStateMessage()
        m2 = SyncStateMessage()
        assert m1.message_id != m2.message_id

    def test_full_round_trip(self):
        original = SyncStateMessage(
            sender_node_id="n_orig",
            sender_did="did:orig",
            scope=SyncScope.CONSENSUS_ONLY,
            state_packet={"decision": "approve"},
            round_id="round_final",
            ttl=0,
            signature="sig_final",
        )
        d = original.to_dict()
        restored = SyncStateMessage.from_dict(d)
        assert restored.sender_node_id == original.sender_node_id
        assert restored.sender_did == original.sender_did
        assert restored.scope == original.scope
        assert restored.state_packet == original.state_packet
        assert restored.round_id == original.round_id
        assert restored.ttl == original.ttl
        assert restored.signature == original.signature


# ── ConsensusVoteMessage Tests ──────────────────────────────────────────────

class TestConsensusVoteMessage:
    """ConsensusVoteMessage creation and serialization tests."""

    def test_create_default(self):
        vote = ConsensusVoteMessage()
        assert vote.vote_id is not None
        assert vote.vote_choice == ""
        assert vote.confidence == 0.0
        assert vote.decision_level == "HIGH"

    def test_create_with_fields(self):
        vote = ConsensusVoteMessage(
            proposal_id="prop_001",
            proposal_topic="Add new peer",
            proposal_description="Should we admit node_x?",
            voter_node_id="node_voter",
            voter_did="did:voter",
            vote_choice="approve",
            reasoning="Trusted peer",
            confidence=0.95,
            dharma_weight=1.0,
            decision_level="CRITICAL",
        )
        assert vote.proposal_id == "prop_001"
        assert vote.proposal_topic == "Add new peer"
        assert vote.vote_choice == "approve"
        assert vote.confidence == 0.95
        assert vote.dharma_weight == 1.0
        assert vote.decision_level == "CRITICAL"

    def test_to_dict(self):
        vote = ConsensusVoteMessage(
            vote_id="vote_001",
            proposal_id="prop_001",
            vote_choice="reject",
            reasoning="Not enough information",
        )
        d = vote.to_dict()
        assert d["vote_id"] == "vote_001"
        assert d["proposal_id"] == "prop_001"
        assert d["vote_choice"] == "reject"
        assert d["reasoning"] == "Not enough information"

    def test_from_dict(self):
        d = {
            "vote_id": "restored_vote",
            "proposal_id": "prop_restored",
            "proposal_topic": "Test topic",
            "voter_node_id": "n_voter",
            "vote_choice": "abstain",
            "confidence": 0.5,
            "decision_level": "LOW",
        }
        vote = ConsensusVoteMessage.from_dict(d)
        assert vote.vote_id == "restored_vote"
        assert vote.proposal_id == "prop_restored"
        assert vote.vote_choice == "abstain"
        assert vote.confidence == 0.5
        assert vote.decision_level == "LOW"

    def test_from_dict_filters_unknown(self):
        d = {"vote_id": "v1", "unknown_field": "x"}
        vote = ConsensusVoteMessage.from_dict(d)
        assert vote.vote_id == "v1"
        assert not hasattr(vote, "unknown_field")

    def test_full_round_trip(self):
        original = ConsensusVoteMessage(
            proposal_id="prop_round",
            proposal_topic="Round trip",
            proposal_description="Testing round trip",
            voter_node_id="n_round",
            voter_did="did:round",
            vote_choice="approve",
            reasoning="Works",
            confidence=0.88,
            dharma_weight=2.0,
            decision_level="SOVEREIGNTY",
        )
        d = original.to_dict()
        restored = ConsensusVoteMessage.from_dict(d)
        assert restored.proposal_id == original.proposal_id
        assert restored.proposal_topic == original.proposal_topic
        assert restored.vote_choice == original.vote_choice
        assert restored.confidence == original.confidence
        assert restored.dharma_weight == original.dharma_weight
        assert restored.decision_level == original.decision_level


# ── PeerHealthRecord Tests ──────────────────────────────────────────────────

class TestPeerHealthRecord:
    """PeerHealthRecord creation and defaults."""

    def test_create_minimal(self):
        rec = PeerHealthRecord(peer_id="p1", peer_did="did:p1")
        assert rec.peer_id == "p1"
        assert rec.peer_did == "did:p1"
        assert rec.status == PeerStatus.UNKNOWN
        assert rec.last_heartbeat == 0.0
        assert rec.missed_beats == 0
        assert rec.latency_ms == 0.0
        assert rec.consecutive_failures == 0

    def test_create_with_all_fields(self):
        rec = PeerHealthRecord(
            peer_id="p2",
            peer_did="did:p2",
            status=PeerStatus.CONNECTED,
            last_heartbeat=1000.0,
            missed_beats=2,
            latency_ms=15.5,
            consecutive_failures=1,
            metadata={"region": "us-west"},
        )
        assert rec.status == PeerStatus.CONNECTED
        assert rec.last_heartbeat == 1000.0
        assert rec.missed_beats == 2
        assert rec.latency_ms == 15.5
        assert rec.consecutive_failures == 1
        assert rec.metadata == {"region": "us-west"}

    def test_last_seen_default(self):
        rec = PeerHealthRecord(peer_id="p3", peer_did="did:p3")
        assert rec.last_seen > 0


# ── HeartbeatMonitor Tests ──────────────────────────────────────────────────

class TestHeartbeatMonitor:
    """HeartbeatMonitor registration, health tracking, and timeout detection."""

    @pytest.mark.asyncio
    async def test_create(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        assert monitor._node_id == "test_node"
        assert not monitor._running
        assert monitor._task is None

    @pytest.mark.asyncio
    async def test_register_peer(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.register_peer("peer_1", "did:peer1")
        assert "peer_1" in monitor._peers
        assert monitor._peers["peer_1"].peer_did == "did:peer1"
        assert monitor._peers["peer_1"].status == PeerStatus.UNKNOWN

    @pytest.mark.asyncio
    async def test_register_peer_with_metadata(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.register_peer("peer_meta", "did:meta", metadata={"region": "eu"})
        assert monitor._peers["peer_meta"].metadata == {"region": "eu"}

    @pytest.mark.asyncio
    async def test_register_duplicate_peer(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.register_peer("p1", "did:p1")
        monitor.register_peer("p1", "did:p1_new")
        # Should not overwrite since peer already exists
        assert monitor._peers["p1"].peer_did == "did:p1"

    @pytest.mark.asyncio
    async def test_unregister_peer(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.register_peer("p1", "did:p1")
        assert "p1" in monitor._peers
        monitor.unregister_peer("p1")
        assert "p1" not in monitor._peers

    @pytest.mark.asyncio
    async def test_unregister_nonexistent(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.unregister_peer("ghost")
        assert True  # should not raise

    @pytest.mark.asyncio
    async def test_record_heartbeat(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.register_peer("p1", "did:p1")
        monitor.record_heartbeat("p1", latency_ms=12.5)
        rec = monitor._peers["p1"]
        assert rec.status == PeerStatus.CONNECTED
        assert rec.latency_ms == 12.5
        assert rec.missed_beats == 0
        assert rec.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_record_heartbeat_unknown_peer(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.record_heartbeat("unknown", 0.0)
        assert True  # should not raise

    @pytest.mark.asyncio
    async def test_record_ack(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.register_peer("p1", "did:p1")
        monitor.record_ack("p1")
        assert monitor._peers["p1"].last_heartbeat_ack > 0

    @pytest.mark.asyncio
    async def test_record_ack_unknown_peer(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.record_ack("unknown")
        assert True  # should not raise

    @pytest.mark.asyncio
    async def test_get_health_known_peer(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.register_peer("p1", "did:p1")
        monitor.record_heartbeat("p1", 5.0)
        health = monitor.get_health("p1")
        assert health is not None
        assert health["peer_id"] == "p1"
        assert health["peer_did"] == "did:p1"
        assert health["status"] == "connected"
        assert health["latency_ms"] == 5.0

    @pytest.mark.asyncio
    async def test_get_health_unknown_peer(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        assert monitor.get_health("ghost") is None

    @pytest.mark.asyncio
    async def test_get_all_health(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.register_peer("p1", "did:p1")
        monitor.register_peer("p2", "did:p2")
        all_h = monitor.get_all_health()
        assert len(all_h) == 2
        assert "p1" in all_h
        assert "p2" in all_h

    @pytest.mark.asyncio
    async def test_active_peers_property(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.register_peer("p1", "did:p1")
        monitor.register_peer("p2", "did:p2")
        monitor.record_heartbeat("p1", 0.0)
        active = monitor.active_peers
        assert "p1" in active
        assert "p2" not in active

    @pytest.mark.asyncio
    async def test_suspected_peers_property(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        monitor.register_peer("p1", "did:p1")
        # Not connected, not suspected initially
        suspected = monitor.suspected_peers
        assert suspected == []

    @pytest.mark.asyncio
    async def test_set_on_peer_dead_callback(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        callback_called = []

        def on_dead(pid, record):
            callback_called.append((pid, record))

        monitor.set_on_peer_dead(on_dead)
        assert monitor._on_peer_dead is not None

    @pytest.mark.asyncio
    async def test_set_on_peer_suspected_callback(self):
        monitor = HeartbeatMonitor(node_id="test_node")
        callback_called = []

        def on_suspected(pid, record):
            callback_called.append((pid, record))

        monitor.set_on_peer_suspected(on_suspected)
        assert monitor._on_peer_suspected is not None

    @pytest.mark.asyncio
    async def test_start_stop(self):
        monitor = HeartbeatMonitor(node_id="test_node", heartbeat_interval=0.1)
        assert not monitor._running
        await monitor.start()
        assert monitor._running
        assert monitor._task is not None
        await monitor.stop()
        assert not monitor._running
        assert monitor._task is None

    @pytest.mark.asyncio
    async def test_start_idempotent(self):
        monitor = HeartbeatMonitor(node_id="test_node", heartbeat_interval=0.1)
        await monitor.start()
        await monitor.start()  # second start should be no-op
        assert monitor._running
        await monitor.stop()

    @pytest.mark.asyncio
    async def test_timeout_detection(self):
        """Peers that miss heartbeats should be marked DEAD."""
        monitor = HeartbeatMonitor(
            node_id="test_node",
            heartbeat_interval=0.05,
            heartbeat_timeout=0.05,
            max_missed_beats=2,
        )
        monitor.register_peer("p1", "did:p1")
        monitor.record_heartbeat("p1", 0.0)

        # Run the monitor briefly
        await monitor.start()
        await asyncio.sleep(0.3)  # enough for missed beats to accumulate
        await monitor.stop()

        health = monitor.get_health("p1")
        assert health is not None
        # p1 missed heartbeats, should be DEAD or SUSPECTED
        assert health["status"] in ("dead", "suspected")

    @pytest.mark.asyncio
    async def test_dead_callback_invoked(self):
        """The on_peer_dead callback should fire when a peer goes DEAD."""
        monitor = HeartbeatMonitor(
            node_id="test_node",
            heartbeat_interval=0.05,
            heartbeat_timeout=0.05,
            max_missed_beats=2,
        )
        dead_peers = []

        def on_dead(pid, record):
            dead_peers.append(pid)

        monitor.set_on_peer_dead(on_dead)
        monitor.register_peer("p1", "did:p1")
        monitor.record_heartbeat("p1", 0.0)

        await monitor.start()
        await asyncio.sleep(0.3)
        await monitor.stop()

        assert len(dead_peers) >= 1
        assert "p1" in dead_peers

    @pytest.mark.asyncio
    async def test_heartbeat_recovers_peer(self):
        """Recording a heartbeat should reset missed_beats and restore CONNECTED."""
        monitor = HeartbeatMonitor(
            node_id="test_node",
            heartbeat_interval=0.05,
            heartbeat_timeout=0.05,
            max_missed_beats=3,
        )
        monitor.register_peer("p1", "did:p1")

        # Simulate some missed beats
        monitor._peers["p1"].missed_beats = 2
        monitor._peers["p1"].status = PeerStatus.SUSPECTED

        # Record heartbeat - should reset
        monitor.record_heartbeat("p1", 10.0)
        health = monitor.get_health("p1")
        assert health["status"] == "connected"
        assert health["missed_beats"] == 0

    @pytest.mark.asyncio
    async def test_large_number_of_peers(self):
        """Monitor should handle many peers."""
        monitor = HeartbeatMonitor(node_id="test_node", heartbeat_interval=0.5)
        for i in range(100):
            monitor.register_peer(f"p{i}", f"did:p{i}")
        assert len(monitor._peers) == 100
        all_h = monitor.get_all_health()
        assert len(all_h) == 100


# ── Utility Function Tests ──────────────────────────────────────────────────

class TestUtilityFunctions:
    """create_did_challenge and verify_handshake_signature tests."""

    def test_create_did_challenge(self):
        challenge = create_did_challenge("did:example:abc", "nonce_123")
        assert isinstance(challenge, str)
        assert len(challenge) == 64  # SHA-256 hex digest
        assert challenge == create_did_challenge("did:example:abc", "nonce_123")

    def test_create_did_challenge_deterministic(self):
        c1 = create_did_challenge("did:a", "n1")
        c2 = create_did_challenge("did:a", "n1")
        assert c1 == c2

    def test_create_did_challenge_different_nonce(self):
        c1 = create_did_challenge("did:a", "n1")
        c2 = create_did_challenge("did:a", "n2")
        assert c1 != c2

    def test_create_did_challenge_different_did(self):
        c1 = create_did_challenge("did:a", "n1")
        c2 = create_did_challenge("did:b", "n1")
        assert c1 != c2

    def test_verify_handshake_signature_valid(self):
        """Current implementation accepts non-empty signatures > 8 chars."""
        result = verify_handshake_signature(
            did="did:test",
            challenge="challenge_str",
            signature="valid_long_signature_here",
        )
        assert result is True

    def test_verify_handshake_signature_empty(self):
        result = verify_handshake_signature(
            did="did:test",
            challenge="challenge_str",
            signature="",
        )
        assert result is False

    def test_verify_handshake_signature_too_short(self):
        result = verify_handshake_signature(
            did="did:test",
            challenge="challenge_str",
            signature="short",
        )
        assert result is False

    def test_verify_handshake_signature_with_pem(self):
        """With public key PEM (currently unused but should not break)."""
        result = verify_handshake_signature(
            did="did:test",
            challenge="challenge_str",
            signature="valid_long_signature_here",
            public_key_pem="-----BEGIN PUBLIC KEY-----\n...",
        )
        assert result is True
