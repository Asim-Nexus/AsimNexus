"""
core/consensus/founder_to_clone_map.py
AsimNexus — Bidirectional mapping between FounderRole and CloneConsensusEngine clones

Each FounderRole maps to one or more clone domains, and each clone domain
can have multiple founders. This enables the consensus engine to call the
correct founder's NVIDIA API when voting on a proposal.

Mappings:
  FounderRole → Clone (domain-based relevance)
  Clone → FounderRole(s) (founders with relevant expertise)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.founder_clones.founder_clone_system import FounderRole

# ─── FOUNDER → CLONE MAPPING TABLE ─────────────────────────────────────────────
# Each entry maps a FounderRole to the clone(s) most relevant to its specialization.
# The `relevance_weight` (0.0–1.0) indicates how relevant this founder is to that
# clone's domain; used for ΔT-weighted voting.

_CEO_CLONES = ["clone_15", "clone_01"]   # Sovereignty Guard, Dharma Guardian
_CTO_CLONES = ["clone_02"]                # Tech Architect
_CFO_CLONES = ["clone_05"]                # Economic Analyst
_COO_CLONES = ["clone_12", "clone_08", "clone_10"]  # Mesh Coordinator, Health Advisor, Environment Watch
_CPO_CLONES = ["clone_03"]                # Community Weaver
_CHRO_CLONES = ["clone_07", "clone_09"]   # Cultural Keeper, Education Guide
_CMO_CLONES = ["clone_03"]                # Community Weaver
_CLO_CLONES = ["clone_04", "clone_14"]    # Legal Counsel, Contract Auditor
_CSO_CLONES = ["clone_06", "clone_11"]    # Security Sentinel, Identity Protector
_CDO_CLONES = ["clone_13"]                # Memory Keeper
_CIO_CLONES = ["clone_02"]                # Tech Architect
_VP_ENG_CLONES = ["clone_02"]             # Tech Architect
_VP_PROD_CLONES = ["clone_03"]            # Community Weaver
_VP_SALES_CLONES = ["clone_05"]           # Economic Analyst
_VP_OPS_CLONES = ["clone_12"]             # Mesh Coordinator

# ─── FULL BIDIRECTIONAL MAP ────────────────────────────────────────────────────

FOUNDER_TO_CLONES: Dict[FounderRole, List[str]] = {
    FounderRole.CEO:            _CEO_CLONES,
    FounderRole.CTO:            _CTO_CLONES,
    FounderRole.CFO:            _CFO_CLONES,
    FounderRole.COO:            _COO_CLONES,
    FounderRole.CPO:            _CPO_CLONES,
    FounderRole.CHRO:           _CHRO_CLONES,
    FounderRole.CMO:            _CMO_CLONES,
    FounderRole.CLO:            _CLO_CLONES,
    FounderRole.CSO:            _CSO_CLONES,
    FounderRole.CDO:            _CDO_CLONES,
    FounderRole.CIO:            _CIO_CLONES,
    FounderRole.VP_ENGINEERING: _VP_ENG_CLONES,
    FounderRole.VP_PRODUCT:     _VP_PROD_CLONES,
    FounderRole.VP_SALES:       _VP_SALES_CLONES,
    FounderRole.VP_OPS:         _VP_OPS_CLONES,
}

# ─── RELEVANCE WEIGHTS (for ΔT-weighted voting) ────────────────────────────────
# Primary mapping gets weight 1.0; secondary mappings (a founder mapped to
# multiple clones for the same domain) get lower weights.

FOUNDER_CLONE_WEIGHTS: Dict[Tuple[FounderRole, str], float] = {
    # CEO → Sovereignty Guard (primary), Dharma Guardian (secondary)
    (FounderRole.CEO, "clone_15"): 1.0,
    (FounderRole.CEO, "clone_01"): 0.8,
    # CTO → Tech Architect
    (FounderRole.CTO, "clone_02"): 1.0,
    # CFO → Economic Analyst
    (FounderRole.CFO, "clone_05"): 1.0,
    # COO → Mesh Coordinator (primary), Health Advisor, Environment Watch
    (FounderRole.COO, "clone_12"): 1.0,
    (FounderRole.COO, "clone_08"): 0.7,
    (FounderRole.COO, "clone_10"): 0.7,
    # CPO → Community Weaver
    (FounderRole.CPO, "clone_03"): 1.0,
    # CHRO → Cultural Keeper (primary), Education Guide
    (FounderRole.CHRO, "clone_07"): 1.0,
    (FounderRole.CHRO, "clone_09"): 0.8,
    # CMO → Community Weaver
    (FounderRole.CMO, "clone_03"): 0.9,
    # CLO → Legal Counsel (primary), Contract Auditor
    (FounderRole.CLO, "clone_04"): 1.0,
    (FounderRole.CLO, "clone_14"): 0.9,
    # CSO → Security Sentinel (primary), Identity Protector
    (FounderRole.CSO, "clone_06"): 1.0,
    (FounderRole.CSO, "clone_11"): 0.8,
    # CDO → Memory Keeper
    (FounderRole.CDO, "clone_13"): 1.0,
    # CIO → Tech Architect
    (FounderRole.CIO, "clone_02"): 0.9,
    # VP Engineering → Tech Architect
    (FounderRole.VP_ENGINEERING, "clone_02"): 0.8,
    # VP Product → Community Weaver
    (FounderRole.VP_PRODUCT, "clone_03"): 0.8,
    # VP Sales → Economic Analyst
    (FounderRole.VP_SALES, "clone_05"): 0.8,
    # VP Ops → Mesh Coordinator
    (FounderRole.VP_OPS, "clone_12"): 0.9,
}

# ─── REVERSE MAP: CLONE → FOUNDERS ─────────────────────────────────────────────

_CLONE_TO_FOUNDERS: Dict[str, List[FounderRole]] = {}

for founder, clones in FOUNDER_TO_CLONES.items():
    for clone_id in clones:
        if clone_id not in _CLONE_TO_FOUNDERS:
            _CLONE_TO_FOUNDERS[clone_id] = []
        _CLONE_TO_FOUNDERS[clone_id].append(founder)

# ─── CLONE NAMES BY ID ─────────────────────────────────────────────────────────

CLONE_NAMES: Dict[str, str] = {
    "clone_01": "Dharma Guardian",
    "clone_02": "Tech Architect",
    "clone_03": "Community Weaver",
    "clone_04": "Legal Counsel",
    "clone_05": "Economic Analyst",
    "clone_06": "Security Sentinel",
    "clone_07": "Cultural Keeper",
    "clone_08": "Health Advisor",
    "clone_09": "Education Guide",
    "clone_10": "Environment Watch",
    "clone_11": "Identity Protector",
    "clone_12": "Mesh Coordinator",
    "clone_13": "Memory Keeper",
    "clone_14": "Contract Auditor",
    "clone_15": "Sovereignty Guard",
}

# ─── PUBLIC API ────────────────────────────────────────────────────────────────


def get_clone_for_founder(role: FounderRole) -> List[str]:
    """Return the clone IDs mapped to a given founder role.

    Args:
        role: A FounderRole enum value.

    Returns:
        List of clone IDs (e.g. ["clone_02"]).
    """
    return FOUNDER_TO_CLONES.get(role, [])


def get_founders_for_clone(clone_id: str) -> List[FounderRole]:
    """Return the founder roles mapped to a given clone ID.

    Args:
        clone_id: A clone ID string (e.g. "clone_02").

    Returns:
        List of FounderRole values.
    """
    return _CLONE_TO_FOUNDERS.get(clone_id, [])


def get_all_mappings() -> Dict[str, Dict[str, List[str]]]:
    """Return the full bidirectional mapping as a serializable dict.

    Returns:
        {
            "founder_to_clones": { "CEO": ["clone_15", ...], ... },
            "clone_to_founders": { "clone_01": [FounderRole.CEO, ...], ... },
        }
    """
    return {
        "founder_to_clones": {
            role.name: [c for c in clones]
            for role, clones in FOUNDER_TO_CLONES.items()
        },
        "clone_to_founders": {
            cid: [role.name for role in founders]
            for cid, founders in _CLONE_TO_FOUNDERS.items()
        },
    }


def get_vote_weight(founder: FounderRole, clone_id: str) -> float:
    """Get the ΔT weight for a founder voting on a clone's behalf.

    Args:
        founder: The FounderRole casting the vote.
        clone_id: The clone ID the vote is for.

    Returns:
        Weight between 0.0 and 1.0. Returns 0.0 if no mapping exists.
    """
    return FOUNDER_CLONE_WEIGHTS.get((founder, clone_id), 0.0)


def get_clone_name(clone_id: str) -> str:
    """Return the human-readable name for a clone ID."""
    return CLONE_NAMES.get(clone_id, clone_id)


def clone_id_from_name(name: str) -> Optional[str]:
    """Reverse-lookup a clone ID from its human-readable name."""
    for cid, cname in CLONE_NAMES.items():
        if cname.lower() == name.lower():
            return cid
    return None
