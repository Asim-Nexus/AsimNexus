#!/usr/bin/env python3
"""
governance/governance_clone_bridge.py
AsimNexus — Governance ↔ Clone Consensus Bridge
================================================

Wires governance decisions (from governance/ modules and core/governance/consensus.py)
through the World Clone ensemble consensus voting system.

Flow:
  1. A governance decision is initiated (e.g., policy change, jurisdiction rule)
  2. The bridge submits it as a consensus proposal to the World Clone ConsensusEngine
  3. Relevant clones vote based on their domain expertise
  4. The result feeds back into the governance system for execution

This implements the 51/49 model: 51% public governance + 49% private enterprise,
both vetted through the multi-clone consensus layer.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("AsimNexus.GovernanceCloneBridge")


@dataclass
class GovernanceVoteRequest:
    """A governance decision that needs clone consensus."""
    request_id: str
    title: str
    description: str
    source: str                     # e.g. "governance/cross_border", "governance/jurisdiction_router"
    sector: str                     # e.g. "public", "private", "mixed"
    urgency: str = "normal"         # "low", "normal", "high", "critical"
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class GovernanceVoteResult:
    """Result of a governance decision submitted to clone consensus."""
    request_id: str
    title: str
    approved: bool
    confidence: float
    vote_count: int
    approval_pct: float
    escalated_to_human: bool = False
    human_resolved: bool = False
    human_approved: Optional[bool] = None
    details: Dict[str, Any] = field(default_factory=dict)
    completed_at: str = ""


class GovernanceCloneBridge:
    """
    Bridges governance decisions to the World Clone consensus engine.

    Usage:
        bridge = GovernanceCloneBridge()
        result = await bridge.submit_governance_decision(
            title="Update EU data residency policy",
            description="...",
            source="governance/jurisdiction_router",
            sector="public",
        )
    """

    def __init__(self):
        self._orchestrator = None
        self._governance_engine = None
        self._results: Dict[str, GovernanceVoteResult] = {}
        self._initialized = False

    async def _ensure_initialized(self) -> bool:
        """Lazy-load the World Clone orchestrator and governance engine."""
        if self._initialized:
            return True
        try:
            from core.founder_clones.world_clones import get_world_clones
            self._orchestrator = get_world_clones()
        except Exception as e:
            logger.warning(f"WorldCloneOrchestrator not available: {e}")
            return False

        try:
            from core.governance.consensus import get_governance
            self._governance_engine = get_governance()
        except Exception as e:
            logger.warning(f"GovernanceEngine not available: {e}")

        self._initialized = True
        return True

    async def submit_governance_decision(
        self,
        title: str,
        description: str,
        source: str = "governance/system",
        sector: str = "public",
        urgency: str = "normal",
        context: Optional[Dict[str, Any]] = None,
        auto_vote: bool = True,
        escalate_grey_zone: bool = True,
    ) -> Dict[str, Any]:
        """
        Submit a governance decision to the World Clone consensus system.

        Args:
            title: Short title of the governance decision.
            description: Detailed description.
            source: Which governance module this originates from.
            sector: "public" (51%) or "private" (49%) sector.
            urgency: "low", "normal", "high", "critical".
            context: Extra context data for the vote.
            auto_vote: If True, automatically cast votes from domain-relevant clones.
            escalate_grey_zone: If True, auto-escalate to human if consensus is ambiguous.

        Returns:
            Dict with the result including proposal_id, status, and decision.
        """
        if not await self._ensure_initialized():
            return {"error": "GovernanceCloneBridge not available — WorldClones not initialized"}

        if not self._orchestrator:
            return {"error": "WorldCloneOrchestrator not available"}

        # Determine voting strategy based on sector and urgency
        strategy = "weighted_majority"
        quorum = 0.5
        expires = 600  # 10 minutes default

        if urgency == "critical":
            strategy = "weighted_super"
            quorum = 0.67
            expires = 300  # 5 minutes for critical decisions
        elif urgency == "high":
            strategy = "weighted_super"
            quorum = 0.6
            expires = 600
        elif urgency == "low":
            strategy = "simple_majority"
            quorum = 0.4
            expires = 1800  # 30 minutes

        merge_context = {
            "source": source,
            "sector": sector,
            "urgency": urgency,
            **(context or {}),
        }

        # Create the proposal via the orchestrator
        proposal = await self._orchestrator.initiate_consensus_vote(
            title=title,
            description=description,
            proposed_by=f"governance:{source}",
            strategy=strategy,
            quorum_threshold=quorum,
            expires_in_seconds=expires,
            context=merge_context,
        )

        if "error" in proposal:
            return proposal

        proposal_id = proposal["proposal_id"]

        # Auto-cast votes from domain-relevant clones
        if auto_vote:
            vote_results = await self._auto_cast_votes(
                proposal_id=proposal_id,
                title=title,
                description=description,
                sector=sector,
                context=merge_context,
                escalate_grey_zone=escalate_grey_zone,
            )
            return vote_results

        return {
            "status": "proposal_created",
            "proposal_id": proposal_id,
            "message": "Proposal created. Cast votes manually.",
            **proposal,
        }

    async def _auto_cast_votes(
        self,
        proposal_id: str,
        title: str,
        description: str,
        sector: str,
        context: Dict[str, Any],
        escalate_grey_zone: bool,
    ) -> Dict[str, Any]:
        """
        Auto-cast votes from all registered clones based on their domain relevance
        to the governance decision.
        """
        if not self._orchestrator:
            return {"error": "Orchestrator not available"}

        # Get all clones
        clones = self._orchestrator.get_all_clones()
        if not clones:
            return {"error": "No clones registered"}

        # Keyword-based relevance scoring
        description_lower = (title + " " + description).lower()
        sector_keywords = {
            "public": [
                "policy", "government", "regulation", "compliance", "law",
                "public", "citizen", "rights", "transparency", "democracy",
                "नीति", "सरकार", "नियम", "कानून", "नागरिक",
            ],
            "private": [
                "enterprise", "commercial", "business", "proprietary",
                "license", "profit", "market", "corporate", "trade",
                "व्यवसाय", "वाणिज्य", "बजार", "लाइसेन्स",
            ],
            "mixed": [
                "partnership", "public-private", "collaboration", "joint",
                "साझेदारी", "सहकार्य",
            ],
        }

        # Map roles to governance-relevant domains
        role_vote_map = {
            "Governance Advisor": "approve",
            "Legal Guardian": "approve",
            "Harmony Keeper": "approve",
            "Security Sentinel": "approve",
            "Social Harmonizer": "approve",
            "Strategic Planner": "approve",
            "Financial Oracle": "approve",
            "Environmental Steward": "approve",
            "Tech Architect": "approve",
            "Innovation Catalyst": "approve",
            "Research Explorer": "approve",
            "Health Sage": "abstain",
            "Education Mentor": "abstain",
            "Logistics Master": "abstain",
            "Creative Muse": "abstain",
        }

        # Adjust voting based on sector keywords
        sector_text = " ".join(sector_keywords.get(sector, sector_keywords["public"]))
        sector_match = any(kw in description_lower for kw in sector_text.split())

        votes_cast = 0
        last_result = None

        for clone in clones:
            role = clone.get("role", "")
            vote_choice = role_vote_map.get(role, "abstain")

            # If governance-specific sector, governance-related clones approve more strongly
            if sector_match and role in (
                "Governance Advisor", "Legal Guardian", "Harmony Keeper"
            ):
                vote_choice = "approve"

            rationale = (
                f"Auto-vote based on governance '{sector}' sector decision: {title[:100]}"
            )

            result = await self._orchestrator.cast_clone_vote(
                proposal_id=proposal_id,
                clone_role=role,
                vote=vote_choice,
                rationale=rationale,
            )

            if result.get("status") == "resolved":
                last_result = result
                break

            votes_cast += 1

        if last_result and last_result.get("status") == "resolved":
            resolved_result = last_result["result"]
            approval_pct = (
                resolved_result.get("approval_weight", 0) /
                max(resolved_result.get("total_weight", 1), 0.001)
            )

            # Check grey zone and escalate if needed
            escalated = False
            if escalate_grey_zone and 0.35 <= approval_pct <= 0.65:
                escalation = await self._orchestrator.auto_escalate_if_needed(
                    proposal_id=proposal_id,
                    approval_pct=approval_pct,
                )
                escalated = escalation is not None

            # Record result
            gov_result = GovernanceVoteResult(
                request_id=proposal_id,
                title=title,
                approved=resolved_result.get("passed", False),
                confidence=approval_pct,
                vote_count=resolved_result.get("voter_count", 0),
                approval_pct=approval_pct,
                escalated_to_human=escalated,
                details={
                    "source": context.get("source", "unknown"),
                    "sector": context.get("sector", "public"),
                    "strategy": resolved_result.get("strategy", "weighted_majority"),
                },
            )
            self._results[proposal_id] = gov_result

            return {
                "status": "resolved",
                "proposal_id": proposal_id,
                "approved": gov_result.approved,
                "confidence": round(gov_result.confidence, 3),
                "vote_count": gov_result.vote_count,
                "approval_pct": round(gov_result.approval_pct, 3),
                "escalated_to_human": gov_result.escalated_to_human,
                "details": gov_result.details,
            }

        return {
            "status": "voting_in_progress",
            "proposal_id": proposal_id,
            "votes_cast": votes_cast,
            "message": "Votes cast, awaiting resolution.",
        }

    async def submit_to_governance_engine(
        self,
        proposal_id: str,
        passed: bool,
        confidence: float,
    ) -> Dict[str, Any]:
        """
        Feed a clone consensus result back into the GovernanceEngine
        (core/governance/consensus.py) for formal governance execution.
        """
        if not self._governance_engine:
            return {"error": "GovernanceEngine not available"}

        # Create a governance proposal reflecting the clone decision
        prop = self._governance_engine.create_proposal(
            title=f"Clone Consensus: {proposal_id}",
            description=f"Auto-generated from clone vote {proposal_id}. "
                        f"Passed: {passed}, Confidence: {confidence:.2%}",
            proposer="governance_clone_bridge",
        )

        # Activate and finalize based on clone decision
        self._governance_engine.activate_proposal(prop.proposal_id)

        # Cast the clone decision as a governance vote
        self._governance_engine.cast_vote(
            proposal_id=prop.proposal_id,
            voter_address="governance_clone_bridge",
            decision="for" if passed else "against",
            weight=confidence,
        )

        # Finalize
        self._governance_engine.finalize_proposal(prop.proposal_id)

        return {
            "status": "submitted_to_governance",
            "governance_proposal_id": prop.proposal_id,
            "clone_decision": "passed" if passed else "rejected",
            "clone_confidence": confidence,
        }

    def get_vote_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent governance-to-clone vote results."""
        sorted_results = sorted(
            self._results.values(),
            key=lambda r: r.completed_at if hasattr(r, 'completed_at') else "",
            reverse=True,
        )
        return [
            {
                "request_id": r.request_id,
                "title": r.title,
                "approved": r.approved,
                "confidence": round(r.confidence, 3),
                "approval_pct": round(r.approval_pct, 3),
                "escalated_to_human": r.escalated_to_human,
            }
            for r in sorted_results[:limit]
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        total = len(self._results)
        approved = sum(1 for r in self._results.values() if r.approved)
        rejected = total - approved
        escalated = sum(1 for r in self._results.values() if r.escalated_to_human)

        return {
            "total_decisions": total,
            "approved": approved,
            "rejected": rejected,
            "escalated_to_human": escalated,
            "orchestrator_connected": self._orchestrator is not None,
            "governance_engine_connected": self._governance_engine is not None,
        }


# ─── Singleton ────────────────────────────────────────────────────────────────
_bridge: Optional[GovernanceCloneBridge] = None


def get_governance_clone_bridge() -> GovernanceCloneBridge:
    """Get or create the singleton GovernanceCloneBridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = GovernanceCloneBridge()
    return _bridge


def reset_governance_clone_bridge() -> None:
    """Reset the singleton (for testing)."""
    global _bridge
    _bridge = None
