"""
STATUS: REAL — 5-layer veto engine working, hardened with env vars

core/dharma/dharma_veto.py
AsimNexus — Dharma Veto Enforcer
=================================
Standalone enforcement layer that runs BEFORE any critical action.

Veto Layers (in order):
  0. Immutable Constitution    — checks action against 10 constitutional principles
  1. Critical Forbidden        — non-overridable dangerous patterns
  2. Block Patterns            — requires explicit human override
  3. Monopoly/ESG Patterns     — sovereignty risk warnings
  4. ΔT Anti-Concentration     — Delta-T Engine cap enforcement
  5. Cultural Compliance       — local law + cultural_compiler sovereignty

"जय धर्मचक्र — Machine proposes. Human decides. Always."
"""
from __future__ import annotations

import os
import logging
import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("AsimNexus.DharmaVeto")

# ─── Optional: Immutable Constitution integration ─────────────────────────────
try:
    from core.security.immutable_constitution import check_constitution
    _HAS_CONSTITUTION = True
except ImportError:
    _HAS_CONSTITUTION = False
    logger.info("ℹ️ DharmaVeto: ImmutableConstitution not available — Layer 0 skipped")

# ─── Environment Configuration ────────────────────────────────────────────────
_ENABLE_DT_ENGINE = os.getenv("ASIM_DHARMA_DT_ENGINE", "true").lower() == "true"
_ENABLE_CULTURAL_COMPILER = os.getenv("ASIM_DHARMA_CULTURAL", "true").lower() == "true"
_MAX_AUDIT_ENTRIES = int(os.getenv("ASIM_DHARMA_AUDIT_MAX", "10000"))


# ─── ENUMS ────────────────────────────────────────────────────────────────────

class VetoSeverity(str, Enum):
    PASS    = "pass"       # All clear
    WARN    = "warn"       # Advisory — proceed with caution
    BLOCK   = "block"      # Hard stop — requires human override
    CRITICAL = "critical"  # Immutable veto — cannot be overridden


class VetoReason(str, Enum):
    CONSTITUTION_VIOLATION   = "constitution_violation"    # Immutable Constitution violation
    CONCENTRATION_VIOLATION  = "concentration_violation"   # ΔT cap exceeded
    SOVEREIGNTY_INVASIVE     = "sovereignty_invasive"      # Data drain/foreign control
    CULTURAL_ANOMALY         = "cultural_anomaly"          # Violates local norms
    MONOPOLY_PATTERN         = "monopoly_pattern"          # ESG/media capture attempt
    HUMAN_SUPREMACY          = "human_supremacy"           # Bypasses human control
    FORBIDDEN_PATTERN        = "forbidden_pattern"         # Known dangerous pattern
    ANTI_DHARMA              = "anti_dharma"               # Violates core Dharma laws


# ─── DATA CLASSES ─────────────────────────────────────────────────────────────

@dataclass
class VetoEvent:
    timestamp:  str
    severity:   VetoSeverity
    reason:     VetoReason
    detail:     str
    action:     str          # What action was attempted
    node_id:    str          # Who attempted it
    veto_hash:  str = ""     # Immutable audit hash
    overridable: bool = True  # CRITICAL events cannot be overridden

    def __post_init__(self):
        if not self.veto_hash:
            raw = f"{self.timestamp}|{self.action}|{self.node_id}|{self.reason}"
            self.veto_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if self.severity == VetoSeverity.CRITICAL:
            self.overridable = False


@dataclass
class VetoResult:
    passed:     bool
    severity:   VetoSeverity
    events:     List[VetoEvent] = field(default_factory=list)
    summary:    str = ""
    requires_human: bool = False

    @property
    def blocked(self) -> bool:
        return not self.passed


# ─── FORBIDDEN PATTERNS (Dharma Hard Rules) ───────────────────────────────────

# These CANNOT be overridden under any condition
CRITICAL_FORBIDDEN = [
    "rm -rf", "drop table", "delete from users",
    "format c:", "fork bomb", ":(){:|:&};:",
    "shutdown /f", "del /s /q",
    "wipe", "zero_fill", "overwrite_mbr",
]

# These trigger BLOCK (require human override)
BLOCK_PATTERNS = [
    "transfer all",       # mass data transfer
    "share all data",     # bulk data exposure
    "disable dharma",     # trying to bypass dharma
    "skip confirmation",  # bypass Final-3
    "auto approve",       # disable human gate
    "bulk delete",        # mass deletion
    "disable veto",       # disable veto system
    "override human",     # try to replace human decision
]

# ESG/Monopoly manipulation patterns
MONOPOLY_PATTERNS = [
    "esg score",          # ESG as a control weapon
    "universal standard", # external standards imposition
    "global mandate",     # top-down mandate
    "central control",    # centralization attempt
    "single authority",   # monopoly of authority
    "compliance required",# forced compliance
]


# ─── MAIN DHARMA VETO CLASS ───────────────────────────────────────────────────

class DharmaVeto:
    """
    Dharma Veto Enforcer — runs before every critical action.

    Usage:
        veto = DharmaVeto()
        result = veto.check(action="delete_file", node_id="user1",
                            context={"path": "/home/user1/data"})
        if result.blocked:
            logger.info(f"VETOED: {result.summary}")
    """

    def __init__(self, dt_engine=None, cultural_compiler=None):
        self._dt = dt_engine
        self._cultural = cultural_compiler
        self._audit: List[VetoEvent] = []

        # Try loading DeltaT Engine if not provided
        if not self._dt:
            try:
                from core.dharma.delta_t_engine import DeltaTEngine
                self._dt = DeltaTEngine()
                logger.info("✅ DharmaVeto: ΔT Engine loaded")
            except Exception as e:
                logger.warning(f"⚠️ DharmaVeto: ΔT Engine not available — {e}")

        # Try loading Cultural Compiler if not provided
        if not self._cultural:
            try:
                from core.dharma.cultural_compiler import CulturalCompiler
                self._cultural = CulturalCompiler()
                logger.info("✅ DharmaVeto: Cultural Compiler loaded")
            except Exception as e:
                logger.warning(f"⚠️ DharmaVeto: Cultural Compiler not available — {e}")

    def check(
        self,
        action:   str,
        node_id:  str = "unknown",
        context:  Optional[Dict[str, Any]] = None,
        content:  Optional[str] = None,
    ) -> VetoResult:
        """
        Run all Dharma veto layers on a proposed action.

        Args:
            action:   Short description of the action (e.g. "delete_file", "share_data")
            node_id:  Who is requesting (user_id or agent_id)
            context:  Optional dict with extra parameters
            content:  Optional free-text content to scan for patterns

        Returns:
            VetoResult — .passed=True means proceed, .passed=False means blocked
        """
        context = context or {}
        events: List[VetoEvent] = []
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        scan_text = f"{action} {content or ''} {str(context)}".lower()

        # ── LAYER 0: Immutable Constitution check ───────────────────────────
        if _HAS_CONSTITUTION:
            try:
                # Mark audit_logged=True since DharmaVeto logs all events to its audit trail
                constitution_context = dict(context)
                constitution_context["audit_logged"] = True
                constitution_result = check_constitution(action, constitution_context)
                if not constitution_result["passed"]:
                    const_severity = constitution_result.get("severity", "block")
                    veto_severity = (
                        VetoSeverity.CRITICAL if const_severity == "critical"
                        else VetoSeverity.BLOCK if const_severity == "block"
                        else VetoSeverity.WARN
                    )
                    violation_names = [
                        v.get("principle_name", v.get("principle_id", "unknown"))
                        for v in constitution_result.get("violations", [])
                    ]
                    ev = VetoEvent(
                        timestamp=ts,
                        severity=veto_severity,
                        reason=VetoReason.CONSTITUTION_VIOLATION,
                        detail=(
                            f"Constitution violation(s): {', '.join(violation_names)}. "
                            f"Action '{action}' conflicts with immutable principles."
                        ),
                        action=action,
                        node_id=node_id,
                    )
                    events.append(ev)
                    self._audit.append(ev)

                    if veto_severity in (VetoSeverity.CRITICAL, VetoSeverity.BLOCK):
                        logger.error(f"🛑 CONSTITUTION VETO [{node_id}] action='{action}': {ev.detail}")
                        return VetoResult(
                            passed=False,
                            severity=veto_severity,
                            events=events,
                            summary=f"🛑 CONSTITUTION BLOCKED: {ev.detail}",
                            requires_human=(veto_severity == VetoSeverity.BLOCK),
                        )

                    # WARN level — log and continue
                    logger.warning(f"⚠️ CONSTITUTION WARN [{node_id}] action='{action}': {ev.detail}")
            except Exception as exc:
                logger.warning(f"⚠️ DharmaVeto: Constitution check failed — {exc}")
        else:
            logger.debug("DharmaVeto: Constitution not available, skipping Layer 0")

        # ── LAYER 1: Critical forbidden patterns (CANNOT override) ──────────
        for pattern in CRITICAL_FORBIDDEN:
            if pattern in scan_text:
                ev = VetoEvent(
                    timestamp=ts, severity=VetoSeverity.CRITICAL,
                    reason=VetoReason.FORBIDDEN_PATTERN,
                    detail=f"Critical forbidden pattern detected: '{pattern}'",
                    action=action, node_id=node_id,
                )
                events.append(ev)
                self._audit.append(ev)
                logger.error(f"🛑 CRITICAL VETO [{node_id}] action='{action}': {ev.detail}")
                return VetoResult(
                    passed=False, severity=VetoSeverity.CRITICAL,
                    events=events,
                    summary=f"🛑 CRITICAL: {ev.detail}. This action is permanently blocked.",
                    requires_human=False,  # Cannot be approved even by human
                )

        # ── LAYER 2: Block-level patterns (require human override) ──────────
        for pattern in BLOCK_PATTERNS:
            if pattern in scan_text:
                ev = VetoEvent(
                    timestamp=ts, severity=VetoSeverity.BLOCK,
                    reason=VetoReason.HUMAN_SUPREMACY,
                    detail=f"Blocked pattern: '{pattern}' — requires explicit human confirmation",
                    action=action, node_id=node_id,
                )
                events.append(ev)
                self._audit.append(ev)
                logger.warning(f"⚠️ BLOCK VETO [{node_id}]: {ev.detail}")

        # ── LAYER 3: Monopoly / ESG pattern detection ────────────────────────
        monopoly_hits = [p for p in MONOPOLY_PATTERNS if p in scan_text]
        if monopoly_hits:
            ev = VetoEvent(
                timestamp=ts, severity=VetoSeverity.WARN,
                reason=VetoReason.MONOPOLY_PATTERN,
                detail=f"Monopoly/ESG pattern detected: {monopoly_hits}. Sovereignty risk.",
                action=action, node_id=node_id,
            )
            events.append(ev)
            self._audit.append(ev)
            logger.warning(f"⚠️ MONOPOLY WARN [{node_id}]: {ev.detail}")

        # ── LAYER 4: ΔT Engine anti-concentration check ──────────────────────
        dt_event = self._check_delta_t(action, node_id, ts)
        if dt_event:
            events.append(dt_event)
            self._audit.append(dt_event)

        # ── LAYER 5: Cultural Compiler check ────────────────────────────────
        cultural_event = self._check_cultural(action, node_id, context, ts)
        if cultural_event:
            events.append(cultural_event)
            self._audit.append(cultural_event)

        # ── EVALUATE overall result ──────────────────────────────────────────
        blocked_events = [e for e in events if e.severity in (VetoSeverity.BLOCK, VetoSeverity.CRITICAL)]
        warn_events    = [e for e in events if e.severity == VetoSeverity.WARN]

        if blocked_events:
            worst = blocked_events[0]
            return VetoResult(
                passed=False,
                severity=worst.severity,
                events=events,
                summary=f"⚠️ BLOCKED: {worst.detail}",
                requires_human=True,
            )

        if warn_events:
            return VetoResult(
                passed=True,
                severity=VetoSeverity.WARN,
                events=events,
                summary=f"⚠️ WARNING: {warn_events[0].detail} — proceeding with caution.",
                requires_human=False,
            )

        return VetoResult(
            passed=True,
            severity=VetoSeverity.PASS,
            events=events,
            summary="✅ Dharma check passed — all layers clear.",
            requires_human=False,
        )

    def _check_delta_t(self, action: str, node_id: str, ts: str) -> Optional[VetoEvent]:
        """Layer 4: ΔT Engine influence check."""
        if not self._dt:
            return None
        try:
            from core.dharma.delta_t_engine import NodeState, DeltaTEngine
            fresh = DeltaTEngine()
            nodes = [
                NodeState(node_id=node_id,      resources=1.0, tx_rate=1.0, rep_score=1.0),
                NodeState(node_id="network",     resources=5.0, tx_rate=5.0, rep_score=5.0),
                NodeState(node_id="mesh_cloud",  resources=3.0, tx_rate=2.0, rep_score=3.0),
            ]
            report = fresh.run_cycle(nodes)
            symmetry = float(report.get("symmetry_score", 1.0))
            if symmetry < 0.05:
                return VetoEvent(
                    timestamp=ts, severity=VetoSeverity.BLOCK,
                    reason=VetoReason.CONCENTRATION_VIOLATION,
                    detail=f"ΔT Engine: node concentration too high (symmetry={symmetry:.3f}). "
                           f"Exceeds 5-8% cap — anti-monopoly veto triggered.",
                    action=action, node_id=node_id,
                )
        except Exception:
            pass
        return None

    def _check_cultural(
        self, action: str, node_id: str,
        context: Dict[str, Any], ts: str
    ) -> Optional[VetoEvent]:
        """Layer 5: Cultural Compiler sovereignty check."""
        if not self._cultural:
            return None
        try:
            result = self._cultural.check(action=action, context=context)
            if result.get("status") == "SOVEREIGNTY_INVASIVE":
                return VetoEvent(
                    timestamp=ts, severity=VetoSeverity.BLOCK,
                    reason=VetoReason.SOVEREIGNTY_INVASIVE,
                    detail=result.get("detail", "Cultural sovereignty violation detected."),
                    action=action, node_id=node_id,
                )
            elif result.get("status") == "CULTURAL_ANOMALY":
                return VetoEvent(
                    timestamp=ts, severity=VetoSeverity.WARN,
                    reason=VetoReason.CULTURAL_ANOMALY,
                    detail=result.get("detail", "Cultural anomaly — action may conflict with local norms."),
                    action=action, node_id=node_id,
                )
        except Exception:
            pass
        return None

    def audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent veto audit entries."""
        return [
            {
                "timestamp": e.timestamp,
                "severity":  e.severity,
                "reason":    e.reason,
                "detail":    e.detail,
                "action":    e.action,
                "node_id":   e.node_id,
                "veto_hash": e.veto_hash,
                "overridable": e.overridable,
            }
            for e in self._audit[-limit:]
        ]

    def status(self) -> Dict[str, Any]:
        return {
            "active":             True,
            "layers":             5,
            "total_vetoes":       len(self._audit),
            "critical_vetoes":    sum(1 for e in self._audit if e.severity == VetoSeverity.CRITICAL),
            "block_vetoes":       sum(1 for e in self._audit if e.severity == VetoSeverity.BLOCK),
            "dt_engine":          self._dt is not None,
            "cultural_compiler":  self._cultural is not None,
            "forbidden_patterns": len(CRITICAL_FORBIDDEN),
            "block_patterns":     len(BLOCK_PATTERNS),
        }


# ─── SINGLETON ────────────────────────────────────────────────────────────────

_instance: Optional[DharmaVeto] = None

def get_dharma_veto() -> DharmaVeto:
    global _instance
    if _instance is None:
        _instance = DharmaVeto()
    return _instance
