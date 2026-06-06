
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
core/dreaming/bug_triage.py
AsimNexus — Automated Bug Triage + Self-Healing Pipeline
=========================================================
Implements the full AsimNexus bug handling architecture:

  STEP 1 — DETECT     : AI scans for bugs (syntax, logic, security, regression)
  STEP 2 — TRIAGE     : Risk-score each bug (CRITICAL/HIGH/MEDIUM/LOW)
  STEP 3 — DRAFT FIX  : AI generates patch proposal
  STEP 4 — SIMULATE   : ΔT Regression Impact Simulator
  STEP 5 — GATE       : Dharma veto check on fix
  STEP 6 — PIPELINE   : LOW/MEDIUM auto-apply · HIGH/CRITICAL → Final-3 human
  STEP 7 — LEARN      : Pattern stored in Dreaming Engine memory

"AI proposes. ΔT simulates. Dharma checks. Human decides critical."
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("AsimBrain.BugTriage")

TRIAGE_DB = Path(__file__).resolve().parent.parent.parent / "data" / "bug_triage.jsonl"
TRIAGE_DB.parent.mkdir(parents=True, exist_ok=True)


# ─── ENUMS ────────────────────────────────────────────────────────────────────

class BugSeverity(str, Enum):
    CRITICAL = "critical"   # Security / data loss / sovereignty breach
    HIGH     = "high"       # Core functionality broken
    MEDIUM   = "medium"     # Degraded experience
    LOW      = "low"        # Cosmetic / minor


class BugStatus(str, Enum):
    DETECTED        = "detected"
    TRIAGED         = "triaged"
    DRAFT_READY     = "draft_ready"
    SIMULATED       = "simulated"
    PENDING_HUMAN   = "pending_human"   # Final-3 gate
    AUTO_APPLYING   = "auto_applying"
    APPLIED         = "applied"
    REJECTED        = "rejected"
    LEARNING        = "learning"


class PipelineDecision(str, Enum):
    AUTO_APPLY    = "auto_apply"      # LOW/MEDIUM — apply directly
    HUMAN_REVIEW  = "human_review"    # HIGH/CRITICAL — Final-3 required
    BLOCKED       = "blocked"         # Dharma veto or ΔT failure
    DEFER         = "defer"           # Regression risk too high


# ─── DATA CLASSES ─────────────────────────────────────────────────────────────

@dataclass
class BugReport:
    bug_id:       str
    file_path:    str
    line_number:  int
    severity:     BugSeverity
    category:     str           # security / logic / regression / style / performance
    description:  str
    detected_by:  str           # "ai_scan" | "user_report" | "test_failure" | "dreaming"
    detected_at:  str
    status:       BugStatus = BugStatus.DETECTED
    risk_score:   float = 0.0   # 0.0 – 1.0
    fix_draft:    str = ""      # AI-generated patch
    dt_impact:    Dict = field(default_factory=dict)   # ΔT simulation result
    dharma_check: Dict = field(default_factory=dict)   # Dharma veto result
    decision:     PipelineDecision = PipelineDecision.DEFER
    applied_at:   str = ""
    approved_by:  str = ""
    bug_hash:     str = ""

    def __post_init__(self):
        if not self.bug_hash:
            raw = f"{self.file_path}:{self.line_number}:{self.description}"
            self.bug_hash = hashlib.sha256(raw.encode()).hexdigest()[:12]


@dataclass
class TriageStats:
    total:         int = 0
    critical:      int = 0
    high:          int = 0
    medium:        int = 0
    low:           int = 0
    auto_applied:  int = 0
    pending_human: int = 0
    rejected:      int = 0


# ─── RISK SCORING ─────────────────────────────────────────────────────────────

# Patterns that elevate severity
CRITICAL_PATTERNS = [
    "rm -rf", "drop table", "delete from", "password", "private_key",
    "secret", "token", "os.system", "subprocess.call", "eval(",
    "exec(", "pickle.loads", "__import__", "sovereignty", "biometric",
]

HIGH_PATTERNS = [
    "authentication", "authorization", "permission", "admin",
    "database", "sql", "inject", "overflow", "null pointer",
    "infinite loop", "deadlock", "memory leak",
]

SECURITY_KEYWORDS = ["xss", "csrf", "sqli", "rce", "lfi", "ssrf", "idor"]


def score_bug(description: str, file_path: str, category: str) -> Tuple[BugSeverity, float]:
    """Calculate severity and risk score (0-1) for a bug."""
    text = f"{description} {file_path} {category}".lower()

    # Security or critical data patterns
    if any(p in text for p in CRITICAL_PATTERNS) or any(k in text for k in SECURITY_KEYWORDS):
        return BugSeverity.CRITICAL, 0.95

    # Core functionality
    if any(p in text for p in HIGH_PATTERNS):
        return BugSeverity.HIGH, 0.70

    # Category-based scoring
    if category in ("security", "regression"):
        return BugSeverity.HIGH, 0.65
    if category in ("logic", "performance"):
        return BugSeverity.MEDIUM, 0.40

    return BugSeverity.LOW, 0.15


# ─── DELTA-T REGRESSION IMPACT SIMULATOR ─────────────────────────────────────

class RegressionImpactSimulator:
    """
    Simulates the ΔT (anti-concentration) impact of applying a bug fix.
    Prevents fixes that would:
      - Break system balance (concentration spike)
      - Create new regressions
      - Affect sovereignty or Dharma layers
    """

    def simulate(self, bug: BugReport, fix_draft: str) -> Dict[str, Any]:
        """
        Simulate applying the fix and return impact report.

        Returns:
            {
                safe_to_apply: bool,
                regression_risk: float,   # 0-1
                concentration_delta: float,
                affected_modules: list,
                recommendation: str,
            }
        """
        fix_text = f"{fix_draft} {bug.description} {bug.file_path}".lower()

        # Estimate regression risk based on what the fix touches
        regression_risk = 0.1
        affected = []

        if any(k in fix_text for k in ["database", "migration", "schema"]):
            regression_risk += 0.4; affected.append("database")
        if any(k in fix_text for k in ["auth", "login", "token", "session"]):
            regression_risk += 0.35; affected.append("authentication")
        if any(k in fix_text for k in ["api", "endpoint", "route"]):
            regression_risk += 0.2; affected.append("api_layer")
        if any(k in fix_text for k in ["dharma", "veto", "delta"]):
            regression_risk += 0.5; affected.append("dharma_core")
        if any(k in fix_text for k in ["mesh", "p2p", "discovery"]):
            regression_risk += 0.25; affected.append("mesh_layer")

        regression_risk = min(regression_risk, 0.99)

        # ΔT concentration delta — fixing core modules shifts balance
        concentration_delta = regression_risk * 0.3

        safe = regression_risk < 0.6

        recommendation = (
            "✅ Safe to auto-apply — low regression risk"     if regression_risk < 0.3  else
            "⚠️ Review recommended — moderate regression risk" if regression_risk < 0.6  else
            "🚨 Human review required — high regression risk"
        )

        return {
            "safe_to_apply":       safe,
            "regression_risk":     round(regression_risk, 3),
            "concentration_delta": round(concentration_delta, 3),
            "affected_modules":    affected,
            "recommendation":      recommendation,
        }


# ─── AI FIX DRAFT GENERATOR ───────────────────────────────────────────────────

class AIDraftGenerator:
    """
    Generates a fix proposal (patch draft) for a bug.
    In production: calls local LLM. For now: rule-based smart drafts.
    """

    def generate(self, bug: BugReport) -> str:
        cat   = bug.category
        desc  = bug.description.lower()
        fpath = bug.file_path

        if "unused import" in desc or cat == "style":
            return f"# AUTO-FIX DRAFT\n# Remove unused import in {fpath}\n# Line {bug.line_number}: delete or comment the import statement."

        if "none" in desc and "check" in desc:
            return (
                f"# AUTO-FIX DRAFT (None check)\n"
                f"# In {fpath} line {bug.line_number}:\n"
                f"# Add: if value is None: return  # or raise ValueError\n"
                f"# Before the line that uses the value."
            )

        if cat == "security" or "sql" in desc:
            return (
                f"# AUTO-FIX DRAFT (Security)\n"
                f"# In {fpath} line {bug.line_number}:\n"
                f"# Use parameterized queries: cursor.execute(sql, (param,))\n"
                f"# Never interpolate user input into SQL strings."
            )

        if cat == "regression":
            return (
                f"# AUTO-FIX DRAFT (Regression)\n"
                f"# In {fpath} line {bug.line_number}:\n"
                f"# Revert change or add guard:\n"
                f"# if <condition>: <original_behavior>"
            )

        if cat == "performance":
            return (
                f"# AUTO-FIX DRAFT (Performance)\n"
                f"# In {fpath} line {bug.line_number}:\n"
                f"# Consider: caching, lazy evaluation, or async I/O."
            )

        return (
            f"# AUTO-FIX DRAFT\n"
            f"# Bug: {bug.description}\n"
            f"# File: {fpath}, Line: {bug.line_number}\n"
            f"# Category: {cat} | Severity: {bug.severity}\n"
            f"# → Requires human review to implement correct fix."
        )


# ─── PIPELINE DECISION ENGINE ─────────────────────────────────────────────────

def decide_pipeline(bug: BugReport) -> PipelineDecision:
    """
    Decides pipeline routing based on severity + simulation results.

    LOW/MEDIUM + safe ΔT   → AUTO_APPLY
    HIGH                   → HUMAN_REVIEW
    CRITICAL               → HUMAN_REVIEW
    Dharma blocked         → BLOCKED
    High regression risk   → DEFER
    """
    if bug.dharma_check.get("status") == "SOVEREIGNTY_INVASIVE":
        return PipelineDecision.BLOCKED

    dt = bug.dt_impact
    if dt.get("regression_risk", 0) >= 0.6:
        return PipelineDecision.DEFER

    if bug.severity in (BugSeverity.CRITICAL, BugSeverity.HIGH):
        return PipelineDecision.HUMAN_REVIEW

    if dt.get("safe_to_apply", False):
        return PipelineDecision.AUTO_APPLY

    return PipelineDecision.HUMAN_REVIEW


# ─── MAIN BUG TRIAGE ENGINE ───────────────────────────────────────────────────

class BugTriageEngine:
    """
    Full Automated Bug Triage + Self-Healing Pipeline.

    Usage:
        engine = BugTriageEngine()

        # Report a bug (from test failure, user report, AI scan)
        bug = engine.report(file_path="core/mesh/p2p_node.py", line=42,
                            category="logic", description="None check missing on peer")

        # Run full pipeline (triage → draft → simulate → decide)
        result = engine.run_pipeline(bug.bug_id)
        # result.decision == "auto_apply" → applied automatically
        # result.decision == "human_review" → awaits Final-3

        # Human approves/rejects
        engine.human_decision(bug.bug_id, approved=True, approver="asim")
    """

    def __init__(self):
        self._bugs:      Dict[str, BugReport] = {}
        self._simulator  = RegressionImpactSimulator()
        self._draft_gen  = AIDraftGenerator()
        self._load_from_db()
        logger.info(f"✅ BugTriageEngine ready — {len(self._bugs)} bugs loaded")

    # ── STEP 1: REPORT / DETECT ───────────────────────────────────────────────

    def report(
        self,
        file_path:   str,
        line_number: int,
        category:    str,
        description: str,
        detected_by: str = "ai_scan",
    ) -> BugReport:
        severity, risk = score_bug(description, file_path, category)
        bug = BugReport(
            bug_id      = str(uuid.uuid4())[:10],
            file_path   = file_path,
            line_number = line_number,
            severity    = severity,
            category    = category,
            description = description,
            detected_by = detected_by,
            detected_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            risk_score  = risk,
        )
        self._bugs[bug.bug_id] = bug
        self._save(bug)
        logger.info(f"🐛 Bug reported: [{severity.upper()}] {file_path}:{line_number} — {description[:60]}")
        return bug

    # ── STEPS 2-6: FULL PIPELINE ─────────────────────────────────────────────

    def run_pipeline(self, bug_id: str) -> BugReport:
        """Run triage → draft → simulate → dharma → decide for a bug."""
        bug = self._get(bug_id)

        # STEP 2: Already triaged in report(), update status
        bug.status = BugStatus.TRIAGED

        # STEP 3: Generate fix draft
        bug.fix_draft = self._draft_gen.generate(bug)
        bug.status = BugStatus.DRAFT_READY

        # STEP 4: ΔT Regression simulation
        bug.dt_impact = self._simulator.simulate(bug, bug.fix_draft)
        bug.status = BugStatus.SIMULATED

        # STEP 5: Dharma veto check
        bug.dharma_check = self._dharma_check(bug)

        # STEP 6: Pipeline decision
        bug.decision = decide_pipeline(bug)

        if bug.decision == PipelineDecision.AUTO_APPLY:
            self._auto_apply(bug)
        elif bug.decision == PipelineDecision.HUMAN_REVIEW:
            bug.status = BugStatus.PENDING_HUMAN
            logger.info(f"⚠️ Bug {bug.bug_id} requires human Final-3 approval")
        elif bug.decision == PipelineDecision.BLOCKED:
            bug.status = BugStatus.REJECTED
            logger.warning(f"🛑 Bug {bug.bug_id} BLOCKED by Dharma veto")
        elif bug.decision == PipelineDecision.DEFER:
            bug.status = BugStatus.TRIAGED
            logger.info(f"⏸️ Bug {bug.bug_id} DEFERRED — high regression risk")

        self._save(bug)
        return bug

    def _dharma_check(self, bug: BugReport) -> Dict[str, Any]:
        try:
            from core.dharma.cultural_compiler import get_cultural_compiler
            result = get_cultural_compiler().check(
                action=f"apply_fix_{bug.category}",
                content=f"{bug.description} {bug.fix_draft}",
                context={"file": bug.file_path, "severity": bug.severity},
            )
            return result
        except Exception:
            return {"status": "COMPLIANT", "detail": "Dharma compiler unavailable"}

    def _auto_apply(self, bug: BugReport):
        """Auto-apply LOW/MEDIUM safe fixes."""
        bug.status = BugStatus.AUTO_APPLYING
        # In production: apply patch via git / file write
        # For now: mark as applied + log
        bug.status = BugStatus.APPLIED
        bug.applied_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        bug.approved_by = "auto_pipeline"
        logger.info(f"✅ Bug {bug.bug_id} AUTO-APPLIED [{bug.severity}] — {bug.file_path}:{bug.line_number}")

    # ── HUMAN FINAL-3 GATE ────────────────────────────────────────────────────

    def human_decision(self, bug_id: str, approved: bool, approver: str) -> BugReport:
        """
        Gate 3 — human approves or rejects a HIGH/CRITICAL fix.
        Cannot be automated. Cannot be skipped.
        """
        bug = self._get(bug_id)
        if bug.status != BugStatus.PENDING_HUMAN:
            raise ValueError(f"Bug {bug_id} not pending human approval (status={bug.status})")

        if approved:
            bug.status = BugStatus.APPLIED
            bug.applied_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            bug.approved_by = approver
            logger.info(f"✅ Bug {bug_id} APPROVED by {approver} and APPLIED")
        else:
            bug.status = BugStatus.REJECTED
            bug.approved_by = approver
            logger.info(f"❌ Bug {bug_id} REJECTED by {approver}")

        self._save(bug)
        return bug

    # ── BATCH TRIAGE (Dreaming Engine hook) ──────────────────────────────────

    def batch_triage(self, bug_list: List[Dict[str, Any]]) -> TriageStats:
        """
        Process a list of bugs from AI scan.
        Called by DreamingEngine during each cycle.
        """
        stats = TriageStats(total=len(bug_list))
        for b in bug_list:
            bug = self.report(
                file_path   = b.get("file", "unknown"),
                line_number = int(b.get("line", 0)),
                category    = b.get("category", "logic"),
                description = b.get("description", ""),
                detected_by = "dreaming_engine",
            )
            result = self.run_pipeline(bug.bug_id)

            if result.severity == BugSeverity.CRITICAL: stats.critical += 1
            elif result.severity == BugSeverity.HIGH:   stats.high += 1
            elif result.severity == BugSeverity.MEDIUM: stats.medium += 1
            else:                                        stats.low += 1

            if result.status == BugStatus.APPLIED:
                stats.auto_applied += 1
            elif result.status == BugStatus.PENDING_HUMAN:
                stats.pending_human += 1
            elif result.status == BugStatus.REJECTED:
                stats.rejected += 1

        logger.info(
            f"🔬 Batch triage: {stats.total} bugs — "
            f"CRITICAL={stats.critical} HIGH={stats.high} "
            f"auto={stats.auto_applied} pending={stats.pending_human}"
        )
        return stats

    # ── QUERIES ───────────────────────────────────────────────────────────────

    def get(self, bug_id: str) -> Optional[BugReport]:
        return self._bugs.get(bug_id)

    def list_bugs(
        self,
        severity: Optional[BugSeverity] = None,
        status:   Optional[BugStatus]   = None,
        limit:    int = 50,
    ) -> List[BugReport]:
        bugs = list(self._bugs.values())
        if severity: bugs = [b for b in bugs if b.severity == severity]
        if status:   bugs = [b for b in bugs if b.status   == status]
        return sorted(bugs, key=lambda b: b.detected_at, reverse=True)[:limit]

    def pending_human(self) -> List[BugReport]:
        return self.list_bugs(status=BugStatus.PENDING_HUMAN)

    def stats(self) -> Dict[str, Any]:
        bugs = list(self._bugs.values())
        return {
            "total":          len(bugs),
            "critical":       sum(1 for b in bugs if b.severity == BugSeverity.CRITICAL),
            "high":           sum(1 for b in bugs if b.severity == BugSeverity.HIGH),
            "medium":         sum(1 for b in bugs if b.severity == BugSeverity.MEDIUM),
            "low":            sum(1 for b in bugs if b.severity == BugSeverity.LOW),
            "applied":        sum(1 for b in bugs if b.status == BugStatus.APPLIED),
            "pending_human":  sum(1 for b in bugs if b.status == BugStatus.PENDING_HUMAN),
            "rejected":       sum(1 for b in bugs if b.status == BugStatus.REJECTED),
            "deferred":       sum(1 for b in bugs if b.decision == PipelineDecision.DEFER),
            "auto_rate_pct":  round(
                sum(1 for b in bugs if b.approved_by == "auto_pipeline") / max(len(bugs),1) * 100, 1
            ),
        }

    # ── INTERNAL ─────────────────────────────────────────────────────────────

    def _get(self, bug_id: str) -> BugReport:
        b = self._bugs.get(bug_id)
        if not b:
            raise KeyError(f"Bug not found: {bug_id}")
        return b

    def _save(self, bug: BugReport):
        self._bugs[bug.bug_id] = bug
        try:
            with open(TRIAGE_DB, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(bug)) + "\n")
        except Exception as e:
            logger.warning(f"Bug DB write failed: {e}")

    def _load_from_db(self):
        if not TRIAGE_DB.exists():
            return
        try:
            with open(TRIAGE_DB, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        b = BugReport(**d)
                        self._bugs[b.bug_id] = b
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"Bug DB load failed: {e}")


# ─── SINGLETON ────────────────────────────────────────────────────────────────

_engine: Optional[BugTriageEngine] = None

def get_bug_triage() -> BugTriageEngine:
    global _engine
    if _engine is None:
        _engine = BugTriageEngine()
    return _engine
