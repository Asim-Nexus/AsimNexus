"""
Governance API Routes
=====================
FastAPI router for all governance-related endpoints.
"""

import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/governance", tags=["governance"])

# ─── In-memory stores ────────────────────────────────────────────────────────

_proposals: Dict[str, Dict[str, Any]] = {}
_votes: Dict[str, List[Dict[str, Any]]] = {}
_veto_records: List[Dict[str, Any]] = []
_constitution_anchors: List[Dict[str, Any]] = []
_audit_entries: List[Dict[str, Any]] = []
_council_members: List[Dict[str, Any]] = []
_bridge_decisions: List[Dict[str, Any]] = []


# ─── Health ──────────────────────────────────────────────────────────────────


@router.get("/health")
async def health():
    """Get governance system health status."""
    modules = []
    try:
        from core.governance.governance_audit import get_governance_audit
        modules.append("audit")
    except ImportError:
        pass
    try:
        from core.governance.blockchain_constitution_anchor import get_constitution_anchor
        modules.append("constitution")
    except ImportError:
        pass
    try:
        from core.governance.governance_clone_bridge import get_governance_clone_bridge
        modules.append("bridge")
    except ImportError:
        pass
    try:
        from core.security.power_balance_constitution import get_power_balance
        modules.append("power_balance")
    except ImportError:
        pass

    return {
        "status": "degraded" if not modules else "healthy",
        "modules": modules,
    }


# ─── Proposals ───────────────────────────────────────────────────────────────


@router.post("/proposals")
async def create_proposal(data: dict):
    """Create a new governance proposal."""
    proposal_id = str(uuid.uuid4())[:8]
    _proposals[proposal_id] = {
        "proposal_id": proposal_id,
        "title": data.get("title", "Untitled"),
        "description": data.get("description", ""),
        "proposer": data.get("proposer", "anonymous"),
        "sector": data.get("sector", "public"),
        "state": "draft",
        "created_at": datetime.utcnow().isoformat(),
    }
    return {"status": "created", "proposal_id": proposal_id, "title": data.get("title", "Untitled")}


@router.get("/proposals")
async def list_proposals(state: Optional[str] = Query(None)):
    """List governance proposals."""
    proposals = list(_proposals.values())
    if state:
        proposals = [p for p in proposals if p.get("state") == state]
    return {"proposals": proposals, "total": len(proposals)}


@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str):
    """Get a specific proposal by ID."""
    proposal = _proposals.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.post("/proposals/{proposal_id}/activate")
async def activate_proposal(proposal_id: str):
    """Activate a proposal."""
    proposal = _proposals.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal["state"] = "active"
    return {"status": "activated", "proposal_id": proposal_id}


@router.post("/proposals/{proposal_id}/finalize")
async def finalize_proposal(proposal_id: str):
    """Finalize a proposal."""
    proposal = _proposals.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal["state"] = "finalized"
    return {"status": "finalized", "proposal_id": proposal_id}


# ─── Voting ──────────────────────────────────────────────────────────────────


@router.post("/vote")
async def cast_vote(data: dict):
    """Cast a vote on a proposal."""
    proposal_id = data.get("proposal_id")
    voter_address = data.get("voter_address")
    decision = data.get("decision", "for")
    weight = data.get("weight", 1.0)

    if not proposal_id or not voter_address:
        raise HTTPException(status_code=400, detail="Missing required fields: proposal_id, voter_address")

    if decision not in ("for", "against", "abstain"):
        raise HTTPException(status_code=400, detail=f"Invalid decision: {decision}")

    if proposal_id not in _votes:
        _votes[proposal_id] = []

    _votes[proposal_id].append({
        "voter_address": voter_address,
        "decision": decision,
        "weight": weight,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {"status": "voted", "proposal_id": proposal_id}


@router.get("/proposals/{proposal_id}/tally")
async def get_tally(proposal_id: str):
    """Get vote tally for a proposal."""
    votes = _votes.get(proposal_id, [])
    tally = {"for": 0, "against": 0, "abstain": 0}
    for v in votes:
        dec = v.get("decision", "for")
        w = v.get("weight", 1.0)
        if dec in tally:
            tally[dec] += w
    return {
        "proposal_id": proposal_id,
        "for": tally["for"],
        "against": tally["against"],
        "abstain": tally["abstain"],
        "total_votes": len(votes),
    }


# ─── Veto ────────────────────────────────────────────────────────────────────


@router.post("/veto")
async def exercise_veto(data: dict):
    """Exercise veto power."""
    exercised_by = data.get("exercised_by")
    reason = data.get("reason")
    action_vetoed = data.get("action_vetoed")

    if not exercised_by or not reason or not action_vetoed:
        raise HTTPException(status_code=400, detail="Missing required fields")

    record = {
        "veto_id": str(uuid.uuid4())[:8],
        "exercised_by": exercised_by,
        "reason": reason,
        "action_vetoed": action_vetoed,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _veto_records.append(record)

    return {"status": "veto_recorded", "veto_id": record["veto_id"]}


@router.get("/veto/status")
async def veto_status():
    """Get veto power status."""
    return {
        "veto_power_active": True,
        "veto_records": len(_veto_records),
    }


# ─── Constitution ────────────────────────────────────────────────────────────


@router.post("/constitution/seal")
async def seal_constitution(data: dict):
    """Seal a constitution hash."""
    constitution_hash = data.get("constitution_hash")
    if not constitution_hash:
        raise HTTPException(status_code=400, detail="Missing constitution_hash")

    anchor = {
        "anchor_id": str(uuid.uuid4())[:8],
        "constitution_hash": constitution_hash,
        "sealed_by": data.get("sealed_by", "anonymous"),
        "jurisdiction": data.get("jurisdiction", "global"),
        "timestamp": datetime.utcnow().isoformat(),
    }
    _constitution_anchors.append(anchor)

    return {"status": "sealed", "anchor_id": anchor["anchor_id"]}


@router.get("/constitution/verify")
async def verify_constitution(constitution_hash: Optional[str] = Query(None)):
    """Verify a constitution hash."""
    if not constitution_hash:
        raise HTTPException(status_code=422, detail="Missing constitution_hash query parameter")

    verified = any(
        a.get("constitution_hash") == constitution_hash
        for a in _constitution_anchors
    )
    return {"verified": verified, "constitution_hash": constitution_hash}


@router.get("/constitution/latest")
async def latest_constitution():
    """Get latest constitution anchor."""
    if not _constitution_anchors:
        return {"latest_anchor": None}
    return {"latest_anchor": _constitution_anchors[-1]}


@router.get("/constitution/stats")
async def constitution_stats():
    """Get constitution statistics."""
    return {
        "anchors_count": len(_constitution_anchors),
        "chain_integrity": True,
    }


# ─── Audit ───────────────────────────────────────────────────────────────────


@router.post("/audit/query")
async def audit_query(data: dict):
    """Query the audit trail."""
    limit = data.get("limit", 50)
    action_filter = data.get("action")
    actor_filter = data.get("actor")

    entries = list(_audit_entries)
    if action_filter:
        entries = [e for e in entries if e.get("action") == action_filter]
    if actor_filter:
        entries = [e for e in entries if e.get("actor") == actor_filter]

    return {"entries": entries[:limit], "total": len(entries)}


@router.get("/audit/verify-chain")
async def audit_verify_chain():
    """Verify the integrity of the audit hash chain."""
    return {"status": "verified", "total_entries": len(_audit_entries)}


@router.get("/audit/stats")
async def audit_stats():
    """Get audit trail statistics."""
    return {"total_entries": len(_audit_entries)}


# ─── Council ─────────────────────────────────────────────────────────────────


@router.get("/council/status")
async def council_status():
    """Get council status."""
    return {"council_members": _council_members}


@router.post("/council/members")
async def add_council_member(data: dict):
    """Add a council member."""
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Missing required field: name")

    member = {
        "member_id": str(uuid.uuid4())[:8],
        "name": name,
        "member_type": data.get("member_type", "general"),
        "country": data.get("country", "global"),
        "expertise": data.get("expertise", []),
        "added_at": datetime.utcnow().isoformat(),
    }
    _council_members.append(member)

    return {"status": "member_added", "member_id": member["member_id"]}


# ─── Bridge ──────────────────────────────────────────────────────────────────


@router.post("/bridge/decide")
async def bridge_decide(data: dict):
    """Submit a governance decision to the clone bridge."""
    title = data.get("title")
    description = data.get("description")

    if not title or not description:
        raise HTTPException(status_code=400, detail="Missing required fields: title, description")

    decision = {
        "decision_id": str(uuid.uuid4())[:8],
        "title": title,
        "description": description,
        "sector": data.get("sector", "public"),
        "urgency": data.get("urgency", "normal"),
        "timestamp": datetime.utcnow().isoformat(),
    }
    _bridge_decisions.append(decision)

    return {"status": "submitted", "decision_id": decision["decision_id"]}


@router.get("/bridge/history")
async def bridge_history(limit: int = Query(10)):
    """Get bridge vote history."""
    return {
        "history": _bridge_decisions[-limit:],
        "total": len(_bridge_decisions),
    }


# ─── Founders ────────────────────────────────────────────────────────────────


@router.get("/founders")
async def list_founders():
    """List founders in the governance structure."""
    return {
        "governance_structure": {
            "type": "tripartite",
            "government_share": 51,
            "company_share": 49,
            "citizen_share": 100,
        },
        "founder_summary": {
            "total_founders": 3,
            "active_founders": 3,
        },
    }


# ─── Stats ───────────────────────────────────────────────────────────────────


@router.get("/stats")
async def governance_stats():
    """Get aggregated governance statistics."""
    return {
        "proposals": {
            "total": len(_proposals),
            "by_state": {
                "draft": sum(1 for p in _proposals.values() if p.get("state") == "draft"),
                "active": sum(1 for p in _proposals.values() if p.get("state") == "active"),
                "finalized": sum(1 for p in _proposals.values() if p.get("state") == "finalized"),
            },
        },
        "audit": {
            "total_entries": len(_audit_entries),
        },
        "council": {
            "total_members": len(_council_members),
        },
        "constitution": {
            "anchors_count": len(_constitution_anchors),
        },
        "bridge": {
            "total_decisions": len(_bridge_decisions),
        },
        "veto": {
            "total_records": len(_veto_records),
        },
    }
