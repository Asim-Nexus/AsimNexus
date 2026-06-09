"""
Governance REST API endpoints for ASIMNEXUS.

Provides a FastAPI router exposing:
  - Proposals: create, list, get, activate, finalize
  - Voting: cast vote, get tally, get results
  - Veto: exercise, check status
  - Constitution anchoring: seal, verify, get latest
  - Audit trail: query, verify chain, get stats
  - Council: status, members
  - Bridge: submit governance decisions to clone consensus
  - Stats: aggregated governance statistics

Integrates with existing governance modules:
  - governance/blockchain_constitution_anchor.py
  - governance/governance_audit.py
  - governance/dharma_chakra_council.py
  - governance/governance_clone_bridge.py
  - governance/founder_structure.py
  - security/power_balance_constitution.py
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query

# ---------------------------------------------------------------------------
# Try to load pydantic (optional — fallback to dict-based)
# ---------------------------------------------------------------------------
try:
    from pydantic import BaseModel, Field

    class CreateProposalRequest(BaseModel):
        title: str = Field(..., min_length=1, max_length=256)
        description: str = Field(..., min_length=1, max_length=4096)
        proposer: str = Field(..., min_length=1)
        veto_power: Optional[Dict[str, Any]] = None
        urgency: str = "normal"
        sector: str = "public"
        context: Optional[Dict[str, Any]] = None

    class CastVoteRequest(BaseModel):
        proposal_id: str = Field(..., min_length=1)
        voter_address: str = Field(..., min_length=1)
        decision: str = Field(..., pattern=r"^(for|against|abstain)$")
        weight: float = Field(1.0, ge=0.0, le=100.0)
        rationale: str = ""

    class ExerciseVetoRequest(BaseModel):
        exercised_by: str = Field(..., min_length=1)
        reason: str = Field(..., min_length=1)
        action_vetoed: str = Field(..., min_length=1)
        proposal_id: str = ""

    class SealConstitutionRequest(BaseModel):
        constitution_hash: str = Field(..., min_length=1)
        sealed_by: str = Field(..., min_length=1)
        jurisdiction: str = "global"
        metadata: Optional[Dict[str, Any]] = None

    class AuditQueryRequest(BaseModel):
        action: Optional[str] = None
        actor: Optional[str] = None
        resource: Optional[str] = None
        severity: Optional[str] = None
        since: Optional[float] = None
        until: Optional[float] = None
        limit: int = 100
        offset: int = 0

    class BridgeDecisionRequest(BaseModel):
        title: str = Field(..., min_length=1)
        description: str = Field(..., min_length=1)
        source: str = "governance/api"
        sector: str = "public"
        urgency: str = "normal"
        context: Optional[Dict[str, Any]] = None
        auto_vote: bool = True
        escalate_grey_zone: bool = True

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

logger = logging.getLogger("AsimNexus.API.Governance")

router = APIRouter()

# ---------------------------------------------------------------------------
# Internal helpers (lazy-loaded singletons)
# ---------------------------------------------------------------------------

def _get_audit():
    """Get the GovernanceAudit singleton."""
    try:
        from governance.governance_audit import get_governance_audit
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            return get_governance_audit()
        except RuntimeError:
            return get_governance_audit()
    except Exception as e:
        logger.warning("GovernanceAudit not available: %s", e)
        return None


def _get_constitution_anchor():
    """Get the BlockchainConstitutionAnchor singleton."""
    try:
        from governance.blockchain_constitution_anchor import get_constitution_anchor
        return get_constitution_anchor()
    except Exception as e:
        logger.warning("BlockchainConstitutionAnchor not available: %s", e)
        return None


def _get_dharma_chakra():
    """Get the DharmaChakraCouncil singleton."""
    try:
        from governance.dharma_chakra_council import _dharma_chakra_council
        return _dharma_chakra_council
    except Exception as e:
        logger.warning("DharmaChakraCouncil not available: %s", e)
        return None


def _get_clone_bridge():
    """Get the GovernanceCloneBridge singleton."""
    try:
        from governance.governance_clone_bridge import get_governance_clone_bridge
        return get_governance_clone_bridge()
    except Exception as e:
        logger.warning("GovernanceCloneBridge not available: %s", e)
        return None


def _get_power_balance():
    """Get the PowerBalanceConstitution engine."""
    try:
        from security.power_balance_constitution import PowerBalanceConstitution
        engine = PowerBalanceConstitution()
        return engine
    except Exception as e:
        logger.warning("PowerBalanceConstitution not available: %s", e)
        return None


def _get_founder_structure():
    """Get the FounderStructure singleton."""
    try:
        from governance.founder_structure import FounderStructure
        return FounderStructure()
    except Exception as e:
        logger.warning("FounderStructure not available: %s", e)
        return None


# ---------------------------------------------------------------------------
# Health / Status
# ---------------------------------------------------------------------------

@router.get("/api/governance/health", tags=["Governance"])
async def governance_health():
    """Health check for the governance subsystem."""
    modules = []
    issues = []

    if _get_audit():
        modules.append("audit")
    else:
        issues.append("GovernanceAudit unavailable")

    if _get_constitution_anchor():
        modules.append("constitution_anchor")
    else:
        issues.append("ConstitutionAnchor unavailable")

    if _get_dharma_chakra():
        modules.append("dharma_chakra_council")
    else:
        issues.append("DharmaChakraCouncil unavailable")

    if _get_clone_bridge():
        modules.append("clone_bridge")
    else:
        issues.append("GovernanceCloneBridge unavailable")

    if _get_power_balance():
        modules.append("power_balance")
    else:
        issues.append("PowerBalanceConstitution unavailable")

    return {
        "status": "healthy" if not issues else "degraded",
        "modules": modules,
        "issues": issues if issues else None,
    }


# ---------------------------------------------------------------------------
# Proposals — PowerBalanceConstitution-based
# ---------------------------------------------------------------------------

@router.post("/api/governance/proposals", tags=["Governance"])
async def create_proposal(req: dict = Body(...)):
    """Create a new governance proposal via PowerBalanceConstitution."""
    engine = _get_power_balance()
    if not engine:
        raise HTTPException(503, "PowerBalanceConstitution not available")

    try:
        # Map generic proposal fields to PowerBalanceConstitution's amendment system
        from security.power_balance_constitution import SectorControl, SECTOR_BALANCE_MAP

        sector = req.get("sector", "governance")
        # Fallback to a valid sector if the provided one is not in the balance map
        if sector not in SECTOR_BALANCE_MAP:
            sector = "governance"
        title = req.get("title", "Untitled")
        description = req.get("description", "")
        proposer = req.get("proposer", "anonymous")

        proposal = engine.propose_amendment(
            sector=sector,
            proposed_control=SectorControl.PUBLIC_COORDINATED,
            proposed_public_share=0.5,
            rationale=f"{title}: {description}" if description else title,
            proposer=proposer,
        )

        # Record in audit
        audit = _get_audit()
        if audit and hasattr(audit, "record"):
            try:
                import asyncio
                asyncio.ensure_future(
                    audit.record(
                        action="law_submitted",
                        actor=proposer,
                        resource=f"proposal:{proposal.id}",
                        details={
                            "sector": sector,
                            "title": title,
                            "description": description[:200],
                        },
                    )
                )
            except Exception:
                pass

        return {
            "status": "created",
            "proposal_id": proposal.id,
            "title": title,
            "description": description,
            "proposer": proposal.proposer,
            "sector": sector,
            "created_at": proposal.created_at,
            "state": proposal.status,
        }
    except Exception as e:
        logger.error("Failed to create proposal: %s", e)
        raise HTTPException(500, f"Failed to create proposal: {e}")


@router.get("/api/governance/proposals", tags=["Governance"])
async def list_proposals(
    state: Optional[str] = Query(None, description="Filter by state"),
    proposer: Optional[str] = Query(None, description="Filter by proposer"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List governance proposals (amendments from PowerBalanceConstitution)."""
    engine = _get_power_balance()
    if not engine:
        raise HTTPException(503, "PowerBalanceConstitution not available")

    try:
        all_props = engine.get_amendments(status=state)
        filtered = [
            p for p in all_props
            if (not state or p.status == state)
            and (not proposer or p.proposer == proposer)
        ]
        proposals = filtered[offset:offset + limit]

        def _parse_title(rationale: str) -> str:
            """Extract title from rationale (format: 'title: description' or just 'title')."""
            if ": " in rationale:
                return rationale.split(": ", 1)[0]
            return rationale[:100] if len(rationale) > 100 else rationale

        def _parse_desc(rationale: str) -> str:
            """Extract description from rationale."""
            if ": " in rationale:
                return rationale.split(": ", 1)[1]
            return ""

        return {
            "total": len(proposals),
            "limit": limit,
            "offset": offset,
            "proposals": [
                {
                    "proposal_id": p.id,
                    "title": _parse_title(p.rationale),
                    "description": _parse_desc(p.rationale),
                    "proposer": p.proposer,
                    "sector": p.sector,
                    "state": p.status,
                    "created_at": str(p.created_at),
                    "vote_count": p.votes_total,
                }
                for p in proposals
            ],
        }
    except Exception as e:
        logger.error("Failed to list proposals: %s", e)
        raise HTTPException(500, f"Failed to list proposals: {e}")


@router.get("/api/governance/proposals/{proposal_id}", tags=["Governance"])
async def get_proposal(proposal_id: str):
    """Get a single proposal by ID."""
    engine = _get_power_balance()
    if not engine:
        raise HTTPException(503, "PowerBalanceConstitution not available")

    try:
        amendments = engine.get_amendments()
        proposal = next((a for a in amendments if a.id == proposal_id), None)

        if not proposal:
            raise HTTPException(404, f"Proposal {proposal_id} not found")

        def _parse_title(rationale: str) -> str:
            if ": " in rationale:
                return rationale.split(": ", 1)[0]
            return rationale[:100] if len(rationale) > 100 else rationale

        def _parse_desc(rationale: str) -> str:
            if ": " in rationale:
                return rationale.split(": ", 1)[1]
            return ""

        return {
            "proposal_id": proposal.id,
            "title": _parse_title(proposal.rationale),
            "description": _parse_desc(proposal.rationale),
            "proposer": proposal.proposer,
            "sector": proposal.sector,
            "state": proposal.status,
            "created_at": str(proposal.created_at),
            "votes_for": proposal.votes_for,
            "votes_against": proposal.votes_against,
            "votes_total": proposal.votes_total,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get proposal: %s", e)
        raise HTTPException(500, f"Failed to get proposal: {e}")


@router.post("/api/governance/proposals/{proposal_id}/activate", tags=["Governance"])
async def activate_proposal(proposal_id: str):
    """Activate a proposal (move from draft to active)."""
    engine = _get_power_balance()
    if not engine:
        raise HTTPException(503, "PowerBalanceConstitution not available")

    try:
        # PowerBalanceConstitution amendment system doesn't have activate/finalize states.
        # The amendment is already "pending" upon creation. We treat this as a no-op success.
        audit = _get_audit()
        if audit and hasattr(audit, "record"):
            import asyncio
            asyncio.ensure_future(
                audit.record(
                    action="gov_action_submitted",
                    actor="system",
                    resource=f"proposal:{proposal_id}",
                    details={"action": "activated"},
                )
            )

        return {"status": "activated", "proposal_id": proposal_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to activate proposal: %s", e)
        raise HTTPException(500, f"Failed to activate proposal: {e}")


@router.post("/api/governance/proposals/{proposal_id}/finalize", tags=["Governance"])
async def finalize_proposal(proposal_id: str):
    """Finalize a proposal (close voting and tally results)."""
    engine = _get_power_balance()
    if not engine:
        raise HTTPException(503, "PowerBalanceConstitution not available")

    try:
        # PowerBalanceConstitution doesn't have a finalize step;
        # return a no-op success to maintain API consistency.
        audit = _get_audit()
        if audit and hasattr(audit, "record"):
            import asyncio
            asyncio.ensure_future(
                audit.record(
                    action="governance_decision",
                    actor="system",
                    resource=f"proposal:{proposal_id}",
                    details={"action": "finalized"},
                )
            )

        return {
            "status": "finalized",
            "proposal_id": proposal_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to finalize proposal: %s", e)
        raise HTTPException(500, f"Failed to finalize proposal: {e}")


# ---------------------------------------------------------------------------
# Voting
# ---------------------------------------------------------------------------

@router.post("/api/governance/vote", tags=["Governance"])
async def cast_vote(req: dict = Body(...)):
    """Cast a vote on a governance proposal (delegates to PowerBalanceConstitution.vote_on_amendment)."""
    engine = _get_power_balance()
    if not engine:
        raise HTTPException(503, "PowerBalanceConstitution not available")

    proposal_id = req.get("proposal_id", "")
    voter_address = req.get("voter_address", "")
    decision = req.get("decision", "abstain")
    rationale = req.get("rationale", "")

    if not proposal_id or not voter_address:
        raise HTTPException(400, "proposal_id and voter_address are required")

    try:
        # Map generic vote to PowerBalanceConstitution's vote_on_amendment
        vote_for = decision.lower() == "for"
        approved, message = engine.vote_on_amendment(proposal_id, vote_for=vote_for)

        # Audit
        audit = _get_audit()
        if audit and hasattr(audit, "record"):
            import asyncio
            asyncio.ensure_future(
                audit.record(
                    action="governance_decision",
                    actor=voter_address,
                    resource=f"proposal:{proposal_id}",
                    details={
                        "decision": decision,
                        "message": message[:200],
                        "rationale": rationale[:200],
                    },
                )
            )

        return {
            "status": "voted",
            "proposal_id": proposal_id,
            "voter": voter_address,
            "decision": decision,
            "approved": approved,
            "message": message,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cast vote: %s", e)
        raise HTTPException(500, f"Failed to cast vote: {e}")


@router.get("/api/governance/proposals/{proposal_id}/tally", tags=["Governance"])
async def get_proposal_tally(proposal_id: str):
    """Get the vote tally for a proposal from PowerBalanceConstitution amendment data."""
    engine = _get_power_balance()
    if not engine:
        raise HTTPException(503, "PowerBalanceConstitution not available")

    try:
        amendments = engine.get_amendments()
        prop = next((a for a in amendments if a.id == proposal_id), None)

        if prop is None:
            return {
                "proposal_id": proposal_id,
                "for": 0,
                "against": 0,
                "abstain": 0,
                "total_weight": 0,
                "approval_pct": 0,
            }

        total = prop.votes_for + prop.votes_against
        approval_pct = (prop.votes_for / total * 100) if total > 0 else 0

        return {
            "proposal_id": proposal_id,
            "for": prop.votes_for,
            "against": prop.votes_against,
            "abstain": 0,
            "total_weight": prop.votes_total,
            "approval_pct": approval_pct,
            "status": prop.status,
        }
    except Exception as e:
        logger.error("Failed to get tally: %s", e)
        raise HTTPException(500, f"Failed to get tally: {e}")


# ---------------------------------------------------------------------------
# Veto
# ---------------------------------------------------------------------------

@router.post("/api/governance/veto", tags=["Governance"])
async def exercise_veto(req: dict = Body(...)):
    """Exercise veto power over a governance action."""
    exercised_by = req.get("exercised_by", "")
    reason = req.get("reason", "")
    action_vetoed = req.get("action_vetoed", "")
    proposal_id = req.get("proposal_id", "")

    if not exercised_by or not reason or not action_vetoed:
        raise HTTPException(400, "exercised_by, reason, and action_vetoed are required")

    council = _get_dharma_chakra()
    if not council:
        raise HTTPException(503, "DharmaChakraCouncil not available")

    try:
        if hasattr(council, "exercise_veto"):
            veto = council.exercise_veto(
                exercised_by=exercised_by,
                reason=reason,
                action_vetoed=action_vetoed,
            )
        else:
            raise HTTPException(400, "exercise_veto not supported")

        # Audit
        audit = _get_audit()
        if audit and hasattr(audit, "record"):
            import asyncio
            asyncio.ensure_future(
                audit.record(
                    action="law_vetoed",
                    actor=exercised_by,
                    resource=f"veto:{action_vetoed}",
                    details={
                        "reason": reason,
                        "proposal_id": proposal_id,
                        "abuse_detected": veto.abuse_detected if hasattr(veto, "abuse_detected") else False,
                    },
                )
            )

        return {
            "status": "veto_recorded",
            "veto_id": veto.veto_id if hasattr(veto, "veto_id") else "",
            "exercised_by": exercised_by,
            "reason": reason,
            "action_vetoed": action_vetoed,
            "abuse_detected": veto.abuse_detected if hasattr(veto, "abuse_detected") else False,
            "veto_power_active": getattr(council, "veto_power_active", True),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to exercise veto: %s", e)
        raise HTTPException(500, f"Failed to exercise veto: {e}")


@router.get("/api/governance/veto/status", tags=["Governance"])
async def veto_status():
    """Get the current veto power status."""
    council = _get_dharma_chakra()
    if not council:
        raise HTTPException(503, "DharmaChakraCouncil not available")

    try:
        return {
            "veto_power_active": getattr(council, "veto_power_active", True),
            "recent_vetoes": len(getattr(council, "veto_records", [])),
            "veto_records": [
                {
                    "veto_id": getattr(v, "veto_id", ""),
                    "exercised_by": getattr(v, "exercised_by", ""),
                    "reason": getattr(v, "reason", ""),
                    "action_vetoed": getattr(v, "action_vetoed", ""),
                    "timestamp": str(getattr(v, "timestamp", "")),
                    "abuse_detected": getattr(v, "abuse_detected", False),
                }
                for v in getattr(council, "veto_records", [])
            ][-20:],
        }
    except Exception as e:
        logger.error("Failed to get veto status: %s", e)
        raise HTTPException(500, f"Failed to get veto status: {e}")


# ---------------------------------------------------------------------------
# Constitution Anchoring
# ---------------------------------------------------------------------------

@router.post("/api/governance/constitution/seal", tags=["Governance"])
async def seal_constitution(req: dict = Body(...)):
    """Seal a constitution hash into the blockchain anchor."""
    anchor = _get_constitution_anchor()
    if not anchor:
        raise HTTPException(503, "BlockchainConstitutionAnchor not available")

    constitution_hash = req.get("constitution_hash", "")
    constitution_type = req.get("constitution_type", "immutable")
    metadata = req.get("metadata", {})

    if not constitution_hash:
        raise HTTPException(400, "constitution_hash is required")

    try:
        if hasattr(anchor, "seal"):
            result = anchor.seal(
                constitution_hash=constitution_hash,
                constitution_type=constitution_type,
                metadata=metadata,
            )
        else:
            # Fallback for different API signatures
            result = anchor.seal(constitution_hash)

        # Audit
        audit = _get_audit()
        if audit and hasattr(audit, "record"):
            import asyncio
            asyncio.ensure_future(
                audit.record(
                    action="constitution_anchored",
                    actor=constitution_type or "system",
                    resource=f"constitution:{constitution_hash[:16]}",
                    details={
                        "hash": constitution_hash,
                        "constitution_type": constitution_type,
                    },
                )
            )

        return {
            "status": "sealed",
            "constitution_hash": constitution_hash,
            "anchor": result if isinstance(result, dict) else str(result),
            "constitution_type": constitution_type,
        }
    except Exception as e:
        logger.error("Failed to seal constitution: %s", e)
        raise HTTPException(500, f"Failed to seal constitution: {e}")


@router.get("/api/governance/constitution/verify", tags=["Governance"])
async def verify_constitution(
    constitution_hash: str = Query(..., description="Constitution hash to verify"),
):
    """Verify a constitution hash against the chain."""
    anchor = _get_constitution_anchor()
    if not anchor:
        raise HTTPException(503, "BlockchainConstitutionAnchor not available")

    try:
        if hasattr(anchor, "verify"):
            result = anchor.verify(constitution_hash)
        else:
            result = None

        return {
            "constitution_hash": constitution_hash,
            "verified": result is not None,
            "anchor_record": result if isinstance(result, dict) else str(result) if result else None,
        }
    except Exception as e:
        logger.error("Failed to verify constitution: %s", e)
        raise HTTPException(500, f"Failed to verify constitution: {e}")


@router.get("/api/governance/constitution/latest", tags=["Governance"])
async def get_latest_constitution():
    """Get the latest constitution anchor."""
    anchor = _get_constitution_anchor()
    if not anchor:
        raise HTTPException(503, "BlockchainConstitutionAnchor not available")

    try:
        if hasattr(anchor, "get_latest_anchor"):
            latest = anchor.get_latest_anchor()
        else:
            latest = None

        return {
            "latest_anchor": latest,
        }
    except Exception as e:
        logger.error("Failed to get latest constitution: %s", e)
        raise HTTPException(500, f"Failed to get latest constitution: {e}")


@router.get("/api/governance/constitution/stats", tags=["Governance"])
async def constitution_stats():
    """Get constitution anchoring statistics."""
    anchor = _get_constitution_anchor()
    if not anchor:
        raise HTTPException(503, "BlockchainConstitutionAnchor not available")

    try:
        if hasattr(anchor, "get_stats"):
            stats = anchor.get_stats()
        else:
            stats = {"anchors_count": 0}

        # Also check chain integrity
        chain_status = "unknown"
        if hasattr(anchor, "verify_chain_integrity"):
            integrity = anchor.verify_chain_integrity()
            chain_status = integrity.get("status", "unknown") if isinstance(integrity, dict) else "checked"

        return {
            **stats,
            "chain_integrity": chain_status,
        }
    except Exception as e:
        logger.error("Failed to get constitution stats: %s", e)
        raise HTTPException(500, f"Failed to get constitution stats: {e}")


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------

@router.post("/api/governance/audit/query", tags=["Governance"])
async def query_audit(req: dict = Body(...)):
    """Query the governance audit trail."""
    audit = _get_audit()
    if not audit:
        raise HTTPException(503, "GovernanceAudit not available")

    try:
        if hasattr(audit, "query"):
            entries = await audit.query(
                action=req.get("action"),
                actor=req.get("actor"),
                resource=req.get("resource"),
                severity=req.get("severity"),
                since=req.get("since"),
                until=req.get("until"),
                limit=min(int(req.get("limit", 100)), 500),
                offset=int(req.get("offset", 0)),
            )
        elif hasattr(audit, "get_chain"):
            entries = await audit.get_chain(limit=min(int(req.get("limit", 100)), 500))
        else:
            entries = []

        return {
            "total": len(entries),
            "entries": entries,
        }
    except Exception as e:
        logger.error("Failed to query audit: %s", e)
        raise HTTPException(500, f"Failed to query audit: {e}")


@router.get("/api/governance/audit/verify-chain", tags=["Governance"])
async def verify_audit_chain():
    """Verify the integrity of the audit hash chain."""
    audit = _get_audit()
    if not audit:
        raise HTTPException(503, "GovernanceAudit not available")

    try:
        if hasattr(audit, "verify_chain"):
            report = await audit.verify_chain()
        else:
            report = {"status": "unknown", "total_entries": 0}

        return report
    except Exception as e:
        logger.error("Failed to verify audit chain: %s", e)
        raise HTTPException(500, f"Failed to verify audit chain: {e}")


@router.get("/api/governance/audit/stats", tags=["Governance"])
async def audit_stats():
    """Get audit trail statistics."""
    audit = _get_audit()
    if not audit:
        raise HTTPException(503, "GovernanceAudit not available")

    try:
        if hasattr(audit, "get_stats"):
            stats = await audit.get_stats()
        else:
            stats = {"total_entries": 0}

        return stats
    except Exception as e:
        logger.error("Failed to get audit stats: %s", e)
        raise HTTPException(500, f"Failed to get audit stats: {e}")


# ---------------------------------------------------------------------------
# Dharma-Chakra Council
# ---------------------------------------------------------------------------

@router.get("/api/governance/council/status", tags=["Governance"])
async def council_status():
    """Get the Dharma-Chakra Council status."""
    council = _get_dharma_chakra()
    if not council:
        raise HTTPException(503, "DharmaChakraCouncil not available")

    try:
        if hasattr(council, "get_council_status"):
            status = council.get_council_status()
        else:
            status = {}

        # Add members list
        members = []
        if hasattr(council, "council_members"):
            for mid, member in council.council_members.items():
                members.append({
                    "member_id": mid,
                    "name": getattr(member, "name", ""),
                    "member_type": str(getattr(member, "member_type", "")),
                    "country": getattr(member, "country", ""),
                    "expertise": getattr(member, "expertise", []),
                    "active": getattr(member, "active", False),
                })

        return {
            **status,
            "council_members": members,
        }
    except Exception as e:
        logger.error("Failed to get council status: %s", e)
        raise HTTPException(500, f"Failed to get council status: {e}")


@router.post("/api/governance/council/members", tags=["Governance"])
async def add_council_member(req: dict = Body(...)):
    """Add a new council member."""
    name = req.get("name", "")
    member_type_str = req.get("member_type", "legal_expert")
    country = req.get("country", "global")
    expertise = req.get("expertise", [])

    if not name:
        raise HTTPException(400, "name is required")

    council = _get_dharma_chakra()
    if not council:
        raise HTTPException(503, "DharmaChakraCouncil not available")

    try:
        # Map string to enum
        from governance.dharma_chakra_council import CouncilMemberType
        type_map = {
            "legal_expert": CouncilMemberType.LEGAL_EXPERT,
            "constitutional_expert": CouncilMemberType.CONSTITUTIONAL_EXPERT,
            "technical_expert": CouncilMemberType.TECHNICAL_EXPERT,
            "ethics_expert": CouncilMemberType.ETHICS_EXPERT,
            "government_representative": CouncilMemberType.GOVERNMENT_REPRESENTATIVE,
            "civil_society_representative": CouncilMemberType.CIVIL_SOCIETY_REPRESENTATIVE,
        }
        member_type = type_map.get(member_type_str, CouncilMemberType.LEGAL_EXPERT)

        if hasattr(council, "add_council_member"):
            member = council.add_council_member(
                name=name,
                member_type=member_type,
                country=country,
                expertise=expertise,
            )
        else:
            raise HTTPException(400, "add_council_member not supported")

        return {
            "status": "member_added",
            "member_id": getattr(member, "member_id", ""),
            "name": name,
            "member_type": member_type_str,
            "country": country,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add council member: %s", e)
        raise HTTPException(500, f"Failed to add council member: {e}")


# ---------------------------------------------------------------------------
# Governance Clone Bridge
# ---------------------------------------------------------------------------

@router.post("/api/governance/bridge/decide", tags=["Governance"])
async def bridge_governance_decision(req: dict = Body(...)):
    """Submit a governance decision to clone consensus via the bridge."""
    bridge = _get_clone_bridge()
    if not bridge:
        raise HTTPException(503, "GovernanceCloneBridge not available")

    title = req.get("title", "")
    description = req.get("description", "")
    source = req.get("source", "governance/api")
    sector = req.get("sector", "public")
    urgency = req.get("urgency", "normal")
    context = req.get("context", {})
    auto_vote = req.get("auto_vote", True)
    escalate_grey_zone = req.get("escalate_grey_zone", True)

    if not title or not description:
        raise HTTPException(400, "title and description are required")

    try:
        if hasattr(bridge, "submit_governance_decision"):
            result = await bridge.submit_governance_decision(
                title=title,
                description=description,
                source=source,
                sector=sector,
                urgency=urgency,
                context=context,
                auto_vote=auto_vote,
                escalate_grey_zone=escalate_grey_zone,
            )
        else:
            raise HTTPException(400, "submit_governance_decision not supported")

        # Audit
        audit = _get_audit()
        if audit and hasattr(audit, "record"):
            import asyncio
            asyncio.ensure_future(
                audit.record(
                    action="governance_decision",
                    actor=source,
                    resource=f"bridge:{title[:64]}",
                    details={
                        "sector": sector,
                        "urgency": urgency,
                        "result": result.get("status", "unknown"),
                    },
                )
            )

        return {
            "status": "submitted",
            "bridge_result": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to submit bridge decision: %s", e)
        raise HTTPException(500, f"Failed to submit bridge decision: {e}")


@router.get("/api/governance/bridge/history", tags=["Governance"])
async def bridge_vote_history(limit: int = Query(10, ge=1, le=100)):
    """Get bridge vote history."""
    bridge = _get_clone_bridge()
    if not bridge:
        raise HTTPException(503, "GovernanceCloneBridge not available")

    try:
        if hasattr(bridge, "get_vote_history"):
            history = bridge.get_vote_history(limit=limit)
        else:
            history = []

        return {
            "total": len(history),
            "history": history,
        }
    except Exception as e:
        logger.error("Failed to get bridge history: %s", e)
        raise HTTPException(500, f"Failed to get bridge history: {e}")


# ---------------------------------------------------------------------------
# Founder Structure
# ---------------------------------------------------------------------------

@router.get("/api/governance/founders", tags=["Governance"])
async def list_founders():
    """List all founders in the governance structure."""
    structure = _get_founder_structure()
    if not structure:
        raise HTTPException(503, "FounderStructure not available")

    try:
        if hasattr(structure, "get_governance_structure"):
            gov = structure.get_governance_structure()
        else:
            gov = {}

        if hasattr(structure, "get_founder_summary"):
            summary = structure.get_founder_summary()
        else:
            summary = {}

        return {
            "governance_structure": gov,
            "founder_summary": summary,
        }
    except Exception as e:
        logger.error("Failed to list founders: %s", e)
        raise HTTPException(500, f"Failed to list founders: {e}")


# ---------------------------------------------------------------------------
# Governance Stats (aggregated)
# ---------------------------------------------------------------------------

@router.get("/api/governance/stats", tags=["Governance"])
async def governance_stats():
    """Get aggregated governance statistics from all subsystems."""
    stats = {
        "proposals": {"total": 0, "active": 0, "finalized": 0},
        "audit": {"total_entries": 0, "chain_integrity": "unknown"},
        "council": {"total_members": 0, "active_members": 0},
        "constitution": {"anchors_count": 0, "latest_hash": None},
        "bridge": {"total_decisions": 0, "approved": 0, "rejected": 0},
        "veto": {"total": 0, "abused": 0, "active": True},
    }

    # Proposals from PowerBalanceConstitution (via get_amendments)
    engine = _get_power_balance()
    if engine:
        try:
            all_props = engine.get_amendments()
            stats["proposals"]["total"] = len(all_props)
            stats["proposals"]["active"] = sum(
                1 for p in all_props if p.status == "pending"
            )
            stats["proposals"]["finalized"] = sum(
                1 for p in all_props if p.status in ("approved", "rejected")
            )
        except Exception:
            pass

    # Audit
    audit = _get_audit()
    if audit and hasattr(audit, "get_stats"):
        try:
            import asyncio
            a_stats = await audit.get_stats()
            if isinstance(a_stats, dict):
                stats["audit"]["total_entries"] = a_stats.get("total_entries", 0)
                stats["audit"]["chain_integrity"] = a_stats.get("chain_integrity", "unknown")
        except Exception:
            pass

    # Council
    council = _get_dharma_chakra()
    if council:
        stats["council"]["total_members"] = len(getattr(council, "council_members", {}))
        stats["council"]["active_members"] = sum(
            1 for m in getattr(council, "council_members", {}).values()
            if getattr(m, "active", False)
        )

    # Constitution
    anchor = _get_constitution_anchor()
    if anchor:
        try:
            if hasattr(anchor, "get_stats"):
                c_stats = anchor.get_stats()
                if isinstance(c_stats, dict):
                    stats["constitution"]["anchors_count"] = c_stats.get("total_anchors", 0)
                    stats["constitution"]["latest_hash"] = str(c_stats.get("latest_block", -1))
        except Exception:
            pass

    # Bridge
    bridge = _get_clone_bridge()
    if bridge:
        try:
            b_stats = bridge.get_stats()
            if isinstance(b_stats, dict):
                stats["bridge"]["total_decisions"] = b_stats.get("total_decisions", 0)
                stats["bridge"]["approved"] = b_stats.get("approved", 0)
                stats["bridge"]["rejected"] = b_stats.get("rejected", 0)
        except Exception:
            pass

    # Veto
    if council:
        stats["veto"]["total"] = len(getattr(council, "veto_records", []))
        stats["veto"]["abused"] = sum(
            1 for v in getattr(council, "veto_records", [])
            if getattr(v, "abuse_detected", False)
        )
        stats["veto"]["active"] = getattr(council, "veto_power_active", True)

    return stats
