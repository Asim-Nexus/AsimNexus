"""
AsimNexus Soul Key Route Module
================================
REST API for the Soul Key Security Protocol — cryptographic identity
protection with Merkle Tree life events, hardware attestation, and
automated lockout mechanism.

Reference:
  - core/security/soul_key.py — Core Soul Key protocol implementation
  - docs/DIGITAL_NEPAL_ACT.md — Digital Nepal Act whitepaper
"""

import logging
from typing import Optional
from fastapi import APIRouter, Body, Query
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.SoulKey")

router = APIRouter(tags=["Soul Key"])

# Module-level globals (set via init_soul_key)
orchestrator = None


def init_soul_key(app_globals: dict) -> None:
    """Initialize soul key module with shared app state."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ─── Soul Key Lifecycle ────────────────────────────────────────────────────


@router.post("/api/soul-key/create")
async def soul_key_create(data: dict = Body(...)):
    """Create a new Soul Key for a citizen.

    Request body:
      - citizen_id (str, required): National ID or unique citizen identifier
      - device_fingerprint (str, required): TPM or hardware fingerprint
      - initial_events (list, optional): Initial life events to seed the Merkle Tree

    Returns:
      - soul_key: The created Soul Key (without raw event data)
      - merkle_root: The computed Merkle Root
      - life_hash: The final Life Hash
    """
    try:
        from core.security.soul_key import get_soul_key_protocol

        protocol = get_soul_key_protocol()
        citizen_id = data.get("citizen_id")
        device_fingerprint = data.get("device_fingerprint")

        if not citizen_id or not device_fingerprint:
            return error("citizen_id and device_fingerprint are required")

        soul_key = protocol.create_soul_key(citizen_id, device_fingerprint)

        # Add initial life events if provided
        initial_events = data.get("initial_events", [])
        for event in initial_events:
            protocol.add_life_event(
                citizen_id=citizen_id,
                event_type=event.get("event_type"),
                raw_data=event.get("raw_data", ""),
                metadata=event.get("metadata", {}),
            )

        return ok(
            data={
                "citizen_id": soul_key.citizen_id,
                "merkle_root": soul_key.merkle_root,
                "life_events_count": len(soul_key.life_events),
                "created_at": soul_key.created_at,
                "device_fingerprint": soul_key.device_fingerprint,
                "revoked": soul_key.revoked,
            }
        )
    except Exception as e:
        logger.error(f"Soul Key create error: {e}")
        return error(str(e))


@router.get("/api/soul-key/{citizen_id}")
async def soul_key_get(citizen_id: str):
    """Get a citizen's Soul Key details.

    Returns the Soul Key metadata (never raw event data).
    """
    try:
        from core.security.soul_key import get_soul_key_protocol

        protocol = get_soul_key_protocol()
        soul_key = protocol.get_soul_key(citizen_id)

        if soul_key is None:
            return error("Soul Key not found for citizen_id: %s" % citizen_id)

        return ok(
            data={
                "citizen_id": soul_key.citizen_id,
                "merkle_root": soul_key.merkle_root,
                "life_events_count": len(soul_key.life_events),
                "created_at": soul_key.created_at,
                "last_verified": soul_key.last_verified,
                "device_fingerprint": soul_key.device_fingerprint,
                "revoked": soul_key.revoked,
            }
        )
    except Exception as e:
        logger.error(f"Soul Key get error: {e}")
        return error(str(e))


# ─── Life Events ────────────────────────────────────────────────────────────


@router.post("/api/soul-key/{citizen_id}/events")
async def soul_key_add_event(citizen_id: str, data: dict = Body(...)):
    """Add a life event to a citizen's Soul Key Merkle Tree.

    Request body:
      - event_type (str, required): Type of life event (birth, citizenship, NID,
        education, land, health, tax, marriage, passport, license, voter, pension)
      - raw_data (str, required): Raw data to hash (NEVER stored)
      - metadata (dict, optional): Additional metadata

    Returns:
      - event_id: Unique event identifier
      - new_merkle_root: Updated Merkle Root after event insertion
    """
    try:
        from core.security.soul_key import get_soul_key_protocol

        protocol = get_soul_key_protocol()
        event_type = data.get("event_type")
        raw_data = data.get("raw_data", "")
        metadata = data.get("metadata", {})

        if not event_type:
            return error("event_type is required")

        event_id = protocol.add_life_event(citizen_id, event_type, raw_data, metadata)

        if event_id is None:
            return error("Failed to add life event. Check citizen_id and event_type.")

        # Get updated soul key for the new merkle root
        soul_key = protocol.get_soul_key(citizen_id)
        new_root = soul_key.merkle_root if soul_key else "unknown"

        return ok(
            data={
                "event_id": event_id,
                "new_merkle_root": new_root,
                "event_type": event_type,
            }
        )
    except Exception as e:
        logger.error(f"Soul Key add event error: {e}")
        return error(str(e))


@router.get("/api/soul-key/{citizen_id}/events")
async def soul_key_list_events(
    citizen_id: str,
    limit: int = Query(50, description="Max events to return"),
):
    """List life events for a citizen's Soul Key.

    Returns only event metadata (type, timestamp, event_id) — NEVER raw data.
    """
    try:
        from core.security.soul_key import get_soul_key_protocol

        protocol = get_soul_key_protocol()
        soul_key = protocol.get_soul_key(citizen_id)

        if soul_key is None:
            return error("Soul Key not found for citizen_id: %s" % citizen_id)

        events = []
        for event in soul_key.life_events[-limit:]:
            events.append(
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp,
                    "data_hash": event.data_hash,
                    "metadata": event.metadata,
                }
            )

        return ok(
            data={
                "citizen_id": citizen_id,
                "total_events": len(soul_key.life_events),
                "events": events,
            }
        )
    except Exception as e:
        logger.error(f"Soul Key list events error: {e}")
        return error(str(e))


# ─── Verification & Attestation ─────────────────────────────────────────────


@router.post("/api/soul-key/{citizen_id}/verify")
async def soul_key_verify(citizen_id: str):
    """Verify a citizen's Soul Key integrity.

    Recomputes the Merkle Root from stored event hashes and compares
    with the registered root. Returns True if the Soul Key is intact.
    """
    try:
        from core.security.soul_key import get_soul_key_protocol

        protocol = get_soul_key_protocol()
        is_valid = protocol.verify_soul_key(citizen_id)

        soul_key = protocol.get_soul_key(citizen_id)

        return ok(
            data={
                "citizen_id": citizen_id,
                "is_valid": is_valid,
                "merkle_root": soul_key.merkle_root if soul_key else None,
                "verified_at": soul_key.last_verified if soul_key else None,
            }
        )
    except Exception as e:
        logger.error(f"Soul Key verify error: {e}")
        return error(str(e))


@router.post("/api/soul-key/{citizen_id}/attest")
async def soul_key_attest(citizen_id: str, data: dict = Body(...)):
    """Perform hardware attestation for a citizen's Soul Key.

    Request body:
      - device_fingerprint (str, required): Current device fingerprint to verify

    Returns attestation result: trusted, mismatch, unknown_device, or tampered.
    """
    try:
        from core.security.soul_key import get_soul_key_protocol

        protocol = get_soul_key_protocol()
        device_fingerprint = data.get("device_fingerprint")

        if not device_fingerprint:
            return error("device_fingerprint is required")

        result = protocol.attest_device(citizen_id, device_fingerprint)

        return ok(
            data={
                "citizen_id": citizen_id,
                "result": result.value,
                "message": _attestation_message(result.value),
            }
        )
    except Exception as e:
        logger.error(f"Soul Key attest error: {e}")
        return error(str(e))


def _attestation_message(result: str) -> str:
    """Human-readable message for attestation result."""
    messages = {
        "trusted": "Device is trusted. Soul Key access granted.",
        "mismatch": "Device fingerprint mismatch. Access denied.",
        "unknown_device": "Unknown device. Registration required.",
        "tampered": "Device appears tampered. Lockout protocol initiated.",
    }
    return messages.get(result, "Unknown attestation result.")


# ─── Lockout Protocol ───────────────────────────────────────────────────────


@router.post("/api/soul-key/{citizen_id}/lockout")
async def soul_key_trigger_lockout(citizen_id: str, data: dict = Body(...)):
    """Trigger automated lockout for a citizen's Soul Key.

    Request body:
      - session_id (str, required): The session to revoke
      - device_fingerprint_attempted (str, required): The device that triggered lockout
      - reason (str, required): Reason for lockout

    Lockout stages:
      1. Session revocation on blockchain
      2. Data self-encryption with key escrow
      3. NCSC incident registration
    """
    try:
        from core.security.soul_key import get_soul_key_protocol

        protocol = get_soul_key_protocol()
        session_id = data.get("session_id")
        device_fingerprint_attempted = data.get("device_fingerprint_attempted")
        reason = data.get("reason")

        if not all([session_id, device_fingerprint_attempted, reason]):
            return error("session_id, device_fingerprint_attempted, and reason are required")

        record = protocol.trigger_lockout(
            citizen_id=citizen_id,
            session_id=session_id,
            device_fingerprint_attempted=device_fingerprint_attempted,
            reason=reason,
        )

        return ok(
            data={
                "record_id": record.record_id,
                "citizen_id": record.citizen_id,
                "state": record.state.value,
                "detected_at": record.detected_at,
                "reason": record.reason,
                "ncsc_incident_id": record.ncsc_incident_id,
                "message": "Lockout protocol initiated. Session revoked, data encrypted, NCSC notified.",
            }
        )
    except Exception as e:
        logger.error(f"Soul Key lockout error: {e}")
        return error(str(e))


@router.get("/api/soul-key/{citizen_id}/lockout-history")
async def soul_key_lockout_history(
    citizen_id: str,
    limit: int = Query(10, description="Max records to return"),
):
    """Get lockout history for a citizen's Soul Key."""
    try:
        from core.security.soul_key import get_soul_key_protocol

        protocol = get_soul_key_protocol()
        records = protocol.get_lockout_history(citizen_id, limit=limit)

        history = []
        for record in records:
            history.append(
                {
                    "record_id": record.record_id,
                    "state": record.state.value,
                    "detected_at": record.detected_at,
                    "reason": record.reason,
                    "ncsc_incident_id": record.ncsc_incident_id,
                }
            )

        return ok(
            data={
                "citizen_id": citizen_id,
                "total_records": len(history),
                "records": history,
            }
        )
    except Exception as e:
        logger.error(f"Soul Key lockout history error: {e}")
        return error(str(e))


@router.post("/api/soul-key/lockout/{record_id}/resolve")
async def soul_key_resolve_lockout(record_id: str):
    """Resolve a lockout record after verification."""
    try:
        from core.security.soul_key import get_soul_key_protocol

        protocol = get_soul_key_protocol()
        success = protocol.resolve_lockout(record_id)

        if success:
            return ok(data={"record_id": record_id, "resolved": True})
        else:
            return error("Failed to resolve lockout record: %s" % record_id)
    except Exception as e:
        logger.error(f"Soul Key resolve lockout error: {e}")
        return error(str(e))


# ─── Statistics ──────────────────────────────────────────────────────────────


@router.get("/api/soul-key/stats")
async def soul_key_stats():
    """Get Soul Key protocol statistics.

    Returns:
      - total_soul_keys: Number of registered Soul Keys
      - total_events: Total life events across all keys
      - total_lockouts: Total lockout records
      - active_keys: Number of active (non-revoked) keys
      - revoked_keys: Number of revoked keys
    """
    try:
        from core.security.soul_key import get_soul_key_protocol

        protocol = get_soul_key_protocol()
        stats = protocol.get_stats()

        return ok(data=stats)
    except Exception as e:
        logger.error(f"Soul Key stats error: {e}")
        return error(str(e))
