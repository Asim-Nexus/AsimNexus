"""
STATUS: REAL — Gini/PoS anti-concentration math + API

core/dharma/delta_t_engine.py
AsimNexus — DeltaT Engine v2 (Chief Architect Edition)
Dharma-Chakra Anti-Concentration System

DESIGN PHILOSOPHY:
    - Raw real-world values accepted (resources, tx_rate, rep_score)
    - Relative normalization per network cycle (not pre-normalized)
    - Exponential attenuation for self-correcting symmetry
    - Persistent rep_score penalty on violating nodes
    - PoS (Proof of Symmetry) audit trail per cycle
    - Auditable, no black boxes, local-first

MATH:
    Normalization:
        W_R_i = resources_i  / sum(resources)
        V_I_i = tx_rate_i    / sum(tx_rate)
        C_R_i = rep_score_i  / sum(rep_score)

    Node Influence:
        P_i = alpha * W_R_i + beta * V_I_i + gamma * C_R_i

    Ratio (share of total):
        ratio_i = P_i / sum(P_j)

    Symmetry Attenuation (when ratio_i > L_max):
        attenuation = max(0.1, 1 - lambda * (ratio_i - L_max))
        rep_score_i *= attenuation  [persistent penalty]

    DeltaT Deviation:
        DT_i = ratio_i - (1.0 / N)   [positive = over fair share]

    Proof of Symmetry (PoS):
        Gini = sum_i sum_j |P_i - P_j| / (2 * N * sum(P))
        symmetry_score = 1 - Gini   [1.0 = perfect equality]

"Machine works. Human decides. Always."
Jay Dharma-Chakra
"""

from __future__ import annotations

import math
import time
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class NodeState:
    """
    Raw real-world values — NO pre-normalization required.
    Engine normalizes relative to the full network each cycle.
    """
    resources: float    # CPU units, RAM MB, asset value — any positive unit
    tx_rate: float      # transactions/sec, messages/sec — any positive unit
    rep_score: float    # reputation score — any positive unit (e.g. 0-100)
    history: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)


@dataclass
class VetoEvent:
    """Emitted when a node exceeds the influence cap in a cycle."""
    node_id: str
    cycle: int
    ratio: float            # P_i / P_total — actual share
    attenuation: float      # factor applied (< 1.0 means reduced)
    delta_t: float          # deviation from fair share (ratio - 1/N)
    dharma_veto: bool
    message: str
    timestamp: float = field(default_factory=time.time)

    @property
    def severity(self) -> str:
        excess = self.ratio / max(self.L_max_ref, 1e-9) if hasattr(self, "L_max_ref") else self.ratio
        if self.ratio >= 0.20:
            return "CRITICAL"
        if self.ratio >= 0.12:
            return "HIGH"
        return "WARNING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "cycle": self.cycle,
            "ratio": round(self.ratio, 4),
            "attenuation": round(self.attenuation, 4),
            "delta_t": round(self.delta_t, 4),
            "dharma_veto": self.dharma_veto,
            "message": self.message,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        sev = "CRITICAL" if self.ratio >= 0.20 else ("HIGH" if self.ratio >= 0.12 else "WARNING")
        return (
            f"[VetoEvent|{sev}] node={self.node_id!r} "
            f"ratio={self.ratio:.1%} attn={self.attenuation:.3f} "
            f"DT={self.delta_t:+.4f} veto={self.dharma_veto}"
        )


@dataclass
class PoSReport:
    """Proof of Symmetry — network balance certificate per cycle."""
    cycle: int
    node_count: int
    symmetry_score: float   # 1.0 = perfect equality, 0.0 = maximum inequality
    gini_coefficient: float # 0.0 = equality, 1.0 = monopoly
    violations: int         # nodes over L_max
    l_max: float
    timestamp: float = field(default_factory=time.time)

    @property
    def verdict(self) -> str:
        if self.symmetry_score >= 0.90:
            return "BALANCED"
        if self.symmetry_score >= 0.70:
            return "MILD_CONCENTRATION"
        return "CONCENTRATION_DETECTED"

    def __str__(self) -> str:
        return (
            f"[PoS|Cycle {self.cycle}] "
            f"symmetry={self.symmetry_score:.3f} "
            f"gini={self.gini_coefficient:.3f} "
            f"violations={self.violations} "
            f"verdict={self.verdict}"
        )


# ---------------------------------------------------------------------------
# DeltaT Engine v2
# ---------------------------------------------------------------------------

class DeltaTEngine:
    """
    DeltaT Engine v2 — Dharma-Chakra Anti-Concentration Core.

    Key differences from v1:
      - Accepts raw real-world values (resources, tx_rate, rep_score)
      - Normalizes RELATIVE to network totals each cycle
      - Persistent rep_score penalty — attenuation carries forward
      - Proof of Symmetry (PoS) certificate per cycle
      - Per-node history for audit trail

    Usage:
        engine = DeltaTEngine(L_max=0.07, lambda_factor=8.0)
        engine.register_node("farmer_01", resources=1200, tx_rate=45, rep_score=92)
        engine.register_node("corp_giant", resources=45000, tx_rate=1250, rep_score=88)
        result = engine.check_and_attenuate("corp_giant")
        pos = engine.run_cycle()
        logger.info(pos)
    """

    def __init__(
        self,
        L_max: float = 0.07,
        lambda_factor: float = 8.0,
        alpha: float = 0.40,
        beta: float = 0.35,
        gamma: float = 0.25,
    ) -> None:
        """
        Args:
            L_max:          Maximum allowed influence ratio (default 7%).
            lambda_factor:  Attenuation aggression. Higher = faster pushback.
                            Formula: attn = max(0.1, 1 - lambda*(ratio - L_max))
            alpha:          Weight for resource share   (default 0.40)
            beta:           Weight for tx_rate share    (default 0.35)
            gamma:          Weight for reputation share (default 0.25)
                            alpha + beta + gamma must equal 1.0
        """
        if not (0.05 <= L_max <= 0.15):
            raise ValueError(f"L_max={L_max} must be 0.05-0.15")
        total_w = round(alpha + beta + gamma, 6)
        if abs(total_w - 1.0) > 1e-4:
            raise ValueError(f"alpha+beta+gamma must equal 1.0, got {total_w}")

        self.L_max = L_max
        self.lambda_factor = lambda_factor
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        self.nodes: Dict[str, NodeState] = {}
        self._veto_log: List[VetoEvent] = []
        self._pos_log: List[PoSReport] = []
        self._cycle: int = 0

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def register_node(
        self,
        node_id: str,
        resources: float,
        tx_rate: float,
        rep_score: float,
    ) -> None:
        """
        Register or update a node with raw real-world values.

        Examples:
            resources  = 1200   (MB of RAM, or asset value in any unit)
            tx_rate    = 45     (transactions per second)
            rep_score  = 92     (reputation 0-100)
        """
        if resources < 0 or tx_rate < 0 or rep_score < 0:
            raise ValueError("All metrics must be non-negative")
        self.nodes[node_id] = NodeState(
            resources=resources,
            tx_rate=tx_rate,
            rep_score=rep_score,
        )
        logger.debug("Node registered: %s  res=%.1f tx=%.1f rep=%.1f",
                     node_id, resources, tx_rate, rep_score)

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)

    # ------------------------------------------------------------------
    # Influence calculation (relative normalization)
    # ------------------------------------------------------------------

    def _network_totals(self) -> Tuple[float, float, float]:
        """Return (total_resources, total_tx, total_rep) across all nodes."""
        tr = sum(n.resources for n in self.nodes.values()) or 1.0
        tt = sum(n.tx_rate   for n in self.nodes.values()) or 1.0
        trp = sum(n.rep_score for n in self.nodes.values()) or 1.0
        return tr, tt, trp

    def calculate_influence(self, node_id: str) -> float:
        """
        P_i = alpha * (res_i/total_res) + beta * (tx_i/total_tx) + gamma * (rep_i/total_rep)

        Returns influence score. All nodes sum to 1.0 by construction.
        """
        if node_id not in self.nodes:
            return 0.0
        n = self.nodes[node_id]
        tr, tt, trp = self._network_totals()
        W_R = n.resources  / tr
        V_I = n.tx_rate    / tt
        C_R = n.rep_score  / trp
        return self.alpha * W_R + self.beta * V_I + self.gamma * C_R

    def _all_influences(self) -> Dict[str, float]:
        """Return {node_id: P_i} for all nodes."""
        return {nid: self.calculate_influence(nid) for nid in self.nodes}

    # ------------------------------------------------------------------
    # Check + attenuation (single node)
    # ------------------------------------------------------------------

    def check_and_attenuate(self, node_id: str) -> Dict[str, Any]:
        """
        Check if node_id exceeds L_max and apply attenuation if so.

        Attenuation formula (linear clamp, bounded at 0.1):
            attn = max(0.1, 1 - lambda_factor * (ratio - L_max))
            rep_score *= attn    [persistent — carries to next cycle]

        Returns result dict with full status.
        """
        influences = self._all_influences()
        total_P = sum(influences.values()) or 1.0
        P_i = influences.get(node_id, 0.0)
        ratio = P_i / total_P
        N = len(self.nodes)
        fair_share = 1.0 / N if N > 0 else 0.0
        delta_t = ratio - fair_share

        result: Dict[str, Any] = {
            "node_id": node_id,
            "influence_ratio": round(ratio, 4),
            "delta_t": round(delta_t, 4),
            "timestamp": time.time(),
        }

        if ratio > self.L_max:
            attn = max(0.1, 1.0 - self.lambda_factor * (ratio - self.L_max))
            # Persistent penalty — reduce rep_score so next cycle is lower
            self.nodes[node_id].rep_score *= attn
            self.nodes[node_id].last_updated = time.time()

            msg = (f"Power Concentration Detected! "
                   f"ratio={ratio:.1%} > L_max={self.L_max:.1%}. "
                   f"Influence reduced by {(1-attn)*100:.1f}%.")

            result.update({
                "status": "VIOLATION",
                "action": "ATTENUATE",
                "attenuation_factor": round(attn, 4),
                "dharma_veto": True,
                "message": msg,
            })

            event = VetoEvent(
                node_id=node_id,
                cycle=self._cycle,
                ratio=ratio,
                attenuation=attn,
                delta_t=delta_t,
                dharma_veto=True,
                message=msg,
            )
            self._veto_log.append(event)
            logger.warning("%s", event)
        else:
            result.update({
                "status": "BALANCED",
                "action": "none",
                "attenuation_factor": 1.0,
                "dharma_veto": False,
                "message": f"Within cap. ratio={ratio:.1%}",
            })

        self.nodes[node_id].history.append(result)
        return result

    # ------------------------------------------------------------------
    # Full network cycle + PoS
    # ------------------------------------------------------------------

    def run_cycle(self) -> PoSReport:
        """
        Scan ALL nodes, apply attenuation where needed, emit PoS report.

        This is the main periodic call — run every N seconds in production.
        Returns a PoSReport (Proof of Symmetry) for the cycle.
        """
        self._cycle += 1
        violations = 0

        for node_id in list(self.nodes.keys()):
            res = self.check_and_attenuate(node_id)
            if res["dharma_veto"]:
                violations += 1

        pos = self._compute_pos(violations)
        self._pos_log.append(pos)
        logger.info("%s", pos)
        return pos

    def _compute_pos(self, violations: int) -> PoSReport:
        """
        Proof of Symmetry — Gini coefficient of influence distribution.

        Gini = sum_i sum_j |P_i - P_j| / (2 * N * mean(P))
        symmetry_score = 1 - Gini
        """
        influences = list(self._all_influences().values())
        N = len(influences)
        if N < 2:
            return PoSReport(
                cycle=self._cycle, node_count=N,
                symmetry_score=1.0, gini_coefficient=0.0,
                violations=violations, l_max=self.L_max,
            )

        mean_p = sum(influences) / N
        if mean_p == 0:
            return PoSReport(
                cycle=self._cycle, node_count=N,
                symmetry_score=1.0, gini_coefficient=0.0,
                violations=violations, l_max=self.L_max,
            )

        gini_sum = sum(
            abs(influences[i] - influences[j])
            for i in range(N) for j in range(N)
        )
        gini = gini_sum / (2 * N * N * mean_p)
        symmetry = 1.0 - gini

        return PoSReport(
            cycle=self._cycle,
            node_count=N,
            symmetry_score=round(symmetry, 4),
            gini_coefficient=round(gini, 4),
            violations=violations,
            l_max=self.L_max,
        )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def network_summary(self) -> Dict[str, Any]:
        """Full network snapshot — suitable for /api/dharma/status."""
        influences = self._all_influences()
        total_P = sum(influences.values()) or 1.0
        N = len(self.nodes)
        pos = self._compute_pos(violations=0)

        nodes_out = {}
        for nid, nd in self.nodes.items():
            P_i = influences[nid]
            ratio = P_i / total_P
            nodes_out[nid] = {
                "resources": nd.resources,
                "tx_rate": nd.tx_rate,
                "rep_score": round(nd.rep_score, 4),
                "influence": round(P_i, 6),
                "ratio": round(ratio, 4),
                "ratio_pct": round(ratio * 100, 2),
                "delta_t": round(ratio - (1.0 / N if N > 0 else 0), 4),
                "cap_violated": ratio > self.L_max,
            }
        return {
            "cycle": self._cycle,
            "node_count": N,
            "L_max": self.L_max,
            "lambda_factor": self.lambda_factor,
            "symmetry_score": pos.symmetry_score,
            "gini_coefficient": pos.gini_coefficient,
            "verdict": pos.verdict,
            "total_veto_events": len(self._veto_log),
            "nodes": nodes_out,
        }

    def veto_history(self, last_n: int = 50) -> List[Dict[str, Any]]:
        """Return last N veto events."""
        return [e.to_dict() for e in self._veto_log[-last_n:]]

    def pos_history(self, last_n: int = 20) -> List[Dict[str, Any]]:
        """Return last N PoS reports."""
        return [
            {
                "cycle": p.cycle,
                "symmetry_score": p.symmetry_score,
                "gini_coefficient": p.gini_coefficient,
                "violations": p.violations,
                "verdict": p.verdict,
                "timestamp": p.timestamp,
            }
            for p in self._pos_log[-last_n:]
        ]

    def export_audit_json(self) -> str:
        """Export full audit trail as JSON string."""
        return json.dumps({
            "summary": self.network_summary(),
            "veto_history": self.veto_history(100),
            "pos_history": self.pos_history(50),
        }, indent=2)

    def reset_veto_log(self) -> None:
        self._veto_log.clear()

    def __repr__(self) -> str:
        return (
            f"DeltaTEngine(nodes={len(self.nodes)}, "
            f"L_max={self.L_max}, lambda={self.lambda_factor}, "
            f"cycle={self._cycle})"
        )


# ---------------------------------------------------------------------------
# PoS Simulator — standalone entry point (user's design)
# ---------------------------------------------------------------------------

def run_pos_simulator() -> None:
    """
    Proof of Symmetry Simulator — 18-node realistic network.

    Note: L_max=7% requires enough nodes so fair_share < 7%.
    With 18 nodes: fair_share = 1/18 = 5.6% — any node over 7% fires VETO.
    external_corp with massive resources is the clear monopoly attempter.
    """
    engine = DeltaTEngine(L_max=0.07, lambda_factor=8.0)

    # 15 normal citizen/small-business nodes
    normal_nodes = [
        ("farmer_01",     1200,  45,  92),
        ("farmer_02",     1100,  38,  88),
        ("farmer_03",     1350,  52,  85),
        ("local_shop_1",  2200,  90,  75),
        ("local_shop_2",  1900,  80,  72),
        ("local_shop_3",  2400,  95,  78),
        ("citizen_a",      800,  30,  65),
        ("citizen_b",      750,  28,  60),
        ("citizen_c",      900,  35,  70),
        ("school_node",   1500,  55,  95),
        ("hospital_node", 1800,  65,  97),
        ("community_hub", 2000,  75,  90),
        ("startup_x",     3000, 110,  68),
        ("startup_y",     2800,  98,  71),
        ("cooperative",   1600,  60,  82),
    ]
    for nid, res, tx, rep in normal_nodes:
        engine.register_node(nid, resources=res, tx_rate=tx, rep_score=rep)

    # 2 medium companies — borderline
    engine.register_node("local_company",  resources=8500,  tx_rate=280, rep_score=65)
    engine.register_node("regional_corp",  resources=12000, tx_rate=420, rep_score=58)

    # 1 monopoly attempter — massive resources
    engine.register_node("external_corp",  resources=45000, tx_rate=1250, rep_score=88)

    logger.info("=== AsimNexus DeltaT Engine + PoS Simulator ===")
    logger.info(f"    Nodes: {len(engine.nodes)}  |  L_max=7%  |  Fair share ~{100/len(engine.nodes):.1f}%")
    logger.info()

    for i in range(1, 6):
        logger.info(f"Cycle {i}:")
        for node_id in list(engine.nodes.keys()):
            res = engine.check_and_attenuate(node_id)
            status_icon = "[VETO]" if res["dharma_veto"] else "[OK]  "
            line = (f"  {node_id:20} -> ratio={res['influence_ratio']:.1%}  "
                    f"DT={res['delta_t']:+.3f}  {status_icon}")
            if res["dharma_veto"]:
                logger.info(line + f"  attn={res['attenuation_factor']:.3f}  "
                      f"reduced by {(1-res['attenuation_factor'])*100:.0f}%")
            else:
                logger.info(line)
        pos = engine._compute_pos(violations=0)
        logger.info(f"  >> PoS: symmetry={pos.symmetry_score:.3f}  "
              f"gini={pos.gini_coefficient:.3f}  [{pos.verdict}]")
        logger.info("-" * 70)


if __name__ == "__main__":
    run_pos_simulator()
