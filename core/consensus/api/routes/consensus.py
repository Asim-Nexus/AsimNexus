#!/usr/bin/env python3
"""
STATUS: NEW — Consensus API Routes
Consensus System API Endpoints
=============================
15 Founder Clones voting API.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from core.consensus.clone_consensus_voting import CloneConsensusVoting, get_consensus_engine

router = APIRouter(prefix="/api/v1/consensus", tags=["consensus"])


class ProposalRequest(BaseModel):
    title: str
    description: str
    sector: str = "general"
    gov_benefit: float = 0
    private_benefit: float = 0


@router.post("/vote")
async def consensus_vote(request: ProposalRequest):
    """15 Founder Clones vote."""
    engine = CloneConsensusVoting()
    result = await engine.vote(request.title, request.description, request.sector)
    return result


@router.post("/weighted-vote")
async def weighted_vote(request: ProposalRequest):
    """Weighted voting for government sector."""
    engine = CloneConsensusVoting()
    result = await engine.weighted_vote(
        request.title, 
        request.description, 
        request.sector,
        request.gov_benefit,
        request.private_benefit
    )
    return result


@router.get("/status")
async def consensus_status():
    """Consensus status."""
    return {
        "clones_count": 15,
        "voting_threshold": "8/15",
        "weighted_threshold": "51% for government sector"
    }