
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
AsimNexus Job Marketplace Engine
==================================
Global digital workforce marketplace.
- Job posting (giver), job taking (agent), AI matching
- Escrow-ready (funds locked until milestone completion)
- Smart contract hooks (milestones, disputes)
- Dharma-protected: no harmful jobs
- Rating & reputation system
"""

import json
import sqlite3
import secrets
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("AsimEconomy.Marketplace")

DB_PATH = Path(__file__).parent.parent.parent / "data" / "economy.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ── ENUMS ─────────────────────────────────────────────────────────────────────

class JobStatus(str, Enum):
    OPEN       = "open"
    ASSIGNED   = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW     = "review"
    COMPLETED  = "completed"
    DISPUTED   = "disputed"
    CANCELLED  = "cancelled"


class PaymentStatus(str, Enum):
    PENDING  = "pending"
    ESCROWED = "escrowed"
    RELEASED = "released"
    REFUNDED = "refunded"


class JobCategory(str, Enum):
    TECH         = "tech"
    HEALTH       = "health"
    EDUCATION    = "education"
    LEGAL        = "legal"
    FINANCE      = "finance"
    CREATIVE     = "creative"
    FARMING      = "farming"
    COMMUNITY    = "community"
    GOVERNANCE   = "governance"
    RESEARCH     = "research"
    TRANSLATION  = "translation"
    OTHER        = "other"


# ── DHARMA JOB VETO ──────────────────────────────────────────────────────────

BLOCKED_JOB_PATTERNS = [
    "weapon", "hack", "scam", "fraud", "illegal", "exploit",
    "abuse", "violence", "genocide", "drug", "trafficking",
    "हतियार", "धोखा", "अवैध",
]


def dharma_check_job(title: str, description: str) -> Optional[str]:
    text = (title + " " + description).lower()
    for pattern in BLOCKED_JOB_PATTERNS:
        if pattern in text:
            return f"Dharma-Chakra VETO: Job violates ethical constitution ({pattern})"
    return None


# ── AI SKILL MATCHER ──────────────────────────────────────────────────────────

SKILL_CATEGORY_MAP = {
    JobCategory.TECH:        ["python", "javascript", "react", "api", "code", "database", "ml", "ai"],
    JobCategory.HEALTH:      ["medical", "health", "nursing", "therapy", "diet", "wellness"],
    JobCategory.EDUCATION:   ["teaching", "tutoring", "writing", "curriculum", "research"],
    JobCategory.LEGAL:       ["legal", "contract", "law", "compliance", "rights"],
    JobCategory.FINANCE:     ["accounting", "tax", "finance", "budget", "audit"],
    JobCategory.CREATIVE:    ["design", "writing", "art", "photography", "video", "music"],
    JobCategory.FARMING:     ["agriculture", "farming", "crop", "soil", "irrigation"],
    JobCategory.COMMUNITY:   ["outreach", "social work", "community", "volunteer"],
    JobCategory.GOVERNANCE:  ["policy", "government", "civic", "public sector"],
    JobCategory.RESEARCH:    ["research", "analysis", "data", "science", "survey"],
    JobCategory.TRANSLATION: ["translate", "language", "interpreter", "localization"],
}


def ai_detect_category(title: str, description: str) -> JobCategory:
    text = (title + " " + description).lower()
    scores = {}
    for cat, keywords in SKILL_CATEGORY_MAP.items():
        scores[cat] = sum(1 for kw in keywords if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else JobCategory.OTHER


def ai_match_score(job: Dict, agent_skills: List[str]) -> float:
    cat = job.get("category", "other")
    job_skills = json.loads(job.get("skills", "[]"))
    job_text = (job.get("title", "") + " " + job.get("description", "")).lower()
    score = 0.0
    for skill in agent_skills:
        if skill.lower() in job_text:
            score += 0.3
        if skill.lower() in [s.lower() for s in job_skills]:
            score += 0.5
    return min(score, 1.0)


# ── DATABASE ──────────────────────────────────────────────────────────────────

def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                poster_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'other',
                budget TEXT DEFAULT 'negotiable',
                budget_currency TEXT DEFAULT 'USD',
                timeline_days INTEGER DEFAULT 7,
                skills TEXT DEFAULT '[]',
                milestones TEXT DEFAULT '[]',
                status TEXT DEFAULT 'open',
                payment_status TEXT DEFAULT 'pending',
                agent_id TEXT,
                escrow_amount REAL DEFAULT 0.0,
                universe_scope TEXT DEFAULT 'global',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                cover_note TEXT DEFAULT '',
                proposed_budget TEXT DEFAULT '',
                proposed_timeline INTEGER DEFAULT 7,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                amount REAL DEFAULT 0.0,
                status TEXT DEFAULT 'pending',
                due_date TEXT,
                completed_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                rater_id TEXT NOT NULL,
                ratee_id TEXT NOT NULL,
                score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
                review TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS disputes (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                raised_by TEXT NOT NULL,
                reason TEXT NOT NULL,
                evidence TEXT DEFAULT '',
                status TEXT DEFAULT 'open',
                resolution TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_profiles (
                user_id TEXT PRIMARY KEY,
                display_name TEXT,
                bio TEXT DEFAULT '',
                skills TEXT DEFAULT '[]',
                hourly_rate TEXT DEFAULT 'negotiable',
                completed_jobs INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0.0,
                available BOOLEAN DEFAULT 1,
                universe_scope TEXT DEFAULT 'global',
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    logger.info("✅ Economy DB initialized")


init_db()


# ── MARKETPLACE ENGINE ────────────────────────────────────────────────────────

class JobMarketplace:
    """
    AsimNexus Global Job Marketplace.
    All jobs Dharma-protected, AI-matched, escrow-ready.
    """

    # ── POST JOB ─────────────────────────────────────────────────────────────

    def post_job(self, poster_id: str, title: str, description: str = "",
                 budget: str = "negotiable", budget_currency: str = "USD",
                 timeline_days: int = 7, skills: List[str] = None,
                 milestones: List[Dict] = None,
                 universe_scope: str = "global") -> Dict[str, Any]:

        veto = dharma_check_job(title, description)
        if veto:
            return {"success": False, "error": veto}

        job_id = secrets.token_hex(8)
        category = ai_detect_category(title, description).value
        skills = skills or []
        milestones = milestones or []

        with _get_db() as conn:
            conn.execute("""
                INSERT INTO jobs (id, poster_id, title, description, category, budget,
                    budget_currency, timeline_days, skills, milestones, universe_scope)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (job_id, poster_id, title, description, category, budget,
                  budget_currency, timeline_days,
                  json.dumps(skills), json.dumps(milestones), universe_scope))

            for i, ms in enumerate(milestones):
                ms_id = secrets.token_hex(6)
                conn.execute("""
                    INSERT INTO milestones (id, job_id, title, description, amount, due_date)
                    VALUES (?,?,?,?,?,?)
                """, (ms_id, job_id, ms.get("title", f"Milestone {i+1}"),
                      ms.get("description", ""), ms.get("amount", 0),
                      ms.get("due_date", "")))
            conn.commit()

        logger.info(f"✅ Job posted: {job_id} — '{title}' [{category}]")
        return {"success": True, "job_id": job_id, "category": category,
                "message": f"Job posted! AsimNexus will find matching agents for '{title}'"}

    # ── LIST JOBS ─────────────────────────────────────────────────────────────

    def list_jobs(self, category: str = None, status: str = "open",
                  universe_scope: str = None, limit: int = 50) -> List[Dict]:
        query = "SELECT * FROM jobs WHERE status=?"
        params: List = [status]
        if category:
            query += " AND category=?"
            params.append(category)
        if universe_scope:
            query += " AND (universe_scope=? OR universe_scope='global')"
            params.append(universe_scope)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with _get_db() as conn:
            rows = conn.execute(query, params).fetchall()

        jobs = []
        for row in rows:
            j = dict(row)
            j["skills"] = json.loads(j.get("skills", "[]"))
            j["milestones"] = json.loads(j.get("milestones", "[]"))
            jobs.append(j)
        return jobs

    # ── GET JOB ───────────────────────────────────────────────────────────────

    def get_job(self, job_id: str) -> Optional[Dict]:
        with _get_db() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                return None
            j = dict(row)
            j["skills"] = json.loads(j.get("skills", "[]"))
            j["milestones_detail"] = [dict(r) for r in
                conn.execute("SELECT * FROM milestones WHERE job_id=?", (job_id,)).fetchall()]
            j["applications_count"] = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE job_id=?", (job_id,)).fetchone()[0]
        return j

    # ── APPLY FOR JOB ─────────────────────────────────────────────────────────

    def apply_for_job(self, job_id: str, agent_id: str, cover_note: str = "",
                      proposed_budget: str = "", proposed_timeline: int = 7) -> Dict[str, Any]:
        with _get_db() as conn:
            job = conn.execute("SELECT * FROM jobs WHERE id=? AND status='open'",
                               (job_id,)).fetchone()
            if not job:
                return {"success": False, "error": "Job not found or not open"}
            existing = conn.execute(
                "SELECT id FROM applications WHERE job_id=? AND agent_id=?",
                (job_id, agent_id)).fetchone()
            if existing:
                return {"success": False, "error": "Already applied"}
            app_id = secrets.token_hex(6)
            conn.execute("""
                INSERT INTO applications (id, job_id, agent_id, cover_note, proposed_budget, proposed_timeline)
                VALUES (?,?,?,?,?,?)
            """, (app_id, job_id, agent_id, cover_note, proposed_budget, proposed_timeline))
            conn.commit()
        return {"success": True, "application_id": app_id,
                "message": "Application submitted! Job giver will review."}

    # ── ASSIGN JOB ────────────────────────────────────────────────────────────

    def assign_job(self, job_id: str, poster_id: str, agent_id: str) -> Dict[str, Any]:
        with _get_db() as conn:
            job = conn.execute(
                "SELECT * FROM jobs WHERE id=? AND poster_id=? AND status='open'",
                (job_id, poster_id)).fetchone()
            if not job:
                return {"success": False, "error": "Job not found or not yours"}
            conn.execute("""
                UPDATE jobs SET agent_id=?, status='assigned', updated_at=datetime('now')
                WHERE id=?
            """, (agent_id, job_id))
            conn.commit()
        return {"success": True, "message": f"Job assigned to agent {agent_id}"}

    # ── COMPLETE MILESTONE ────────────────────────────────────────────────────

    def complete_milestone(self, job_id: str, milestone_id: str,
                           agent_id: str) -> Dict[str, Any]:
        with _get_db() as conn:
            job = conn.execute(
                "SELECT * FROM jobs WHERE id=? AND agent_id=?",
                (job_id, agent_id)).fetchone()
            if not job:
                return {"success": False, "error": "Not your job"}
            conn.execute("""
                UPDATE milestones SET status='completed', completed_at=datetime('now')
                WHERE id=? AND job_id=?
            """, (milestone_id, job_id))
            conn.execute("""
                UPDATE jobs SET status='review', updated_at=datetime('now') WHERE id=?
            """, (job_id,))
            conn.commit()
        return {"success": True, "message": "Milestone marked complete. Awaiting approval."}

    # ── RELEASE PAYMENT ───────────────────────────────────────────────────────

    def release_payment(self, job_id: str, poster_id: str) -> Dict[str, Any]:
        with _get_db() as conn:
            job = conn.execute(
                "SELECT * FROM jobs WHERE id=? AND poster_id=?",
                (job_id, poster_id)).fetchone()
            if not job:
                return {"success": False, "error": "Job not found"}
            conn.execute("""
                UPDATE jobs SET status='completed', payment_status='released',
                updated_at=datetime('now') WHERE id=?
            """, (job_id,))
            conn.commit()
        return {"success": True, "message": "Payment released! Job completed."}

    # ── RAISE DISPUTE ─────────────────────────────────────────────────────────

    def raise_dispute(self, job_id: str, raised_by: str, reason: str,
                      evidence: str = "") -> Dict[str, Any]:
        dispute_id = secrets.token_hex(6)
        with _get_db() as conn:
            conn.execute("""
                INSERT INTO disputes (id, job_id, raised_by, reason, evidence)
                VALUES (?,?,?,?,?)
            """, (dispute_id, job_id, raised_by, reason, evidence))
            conn.execute("UPDATE jobs SET status='disputed' WHERE id=?", (job_id,))
            conn.commit()
        return {"success": True, "dispute_id": dispute_id,
                "message": "Dispute raised. AsimNexus arbitration will review."}

    # ── RATE ──────────────────────────────────────────────────────────────────

    def rate(self, job_id: str, rater_id: str, ratee_id: str,
             score: int, review: str = "") -> Dict[str, Any]:
        if not 1 <= score <= 5:
            return {"success": False, "error": "Score must be 1-5"}
        rating_id = secrets.token_hex(6)
        with _get_db() as conn:
            conn.execute("""
                INSERT INTO ratings (id, job_id, rater_id, ratee_id, score, review)
                VALUES (?,?,?,?,?,?)
            """, (rating_id, job_id, rater_id, ratee_id, score, review))
            avg = conn.execute(
                "SELECT AVG(score) FROM ratings WHERE ratee_id=?",
                (ratee_id,)).fetchone()[0]
            count = conn.execute(
                "SELECT COUNT(*) FROM ratings WHERE ratee_id=?",
                (ratee_id,)).fetchone()[0]
            conn.execute("""
                INSERT INTO agent_profiles (user_id, avg_rating, completed_jobs)
                VALUES (?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET
                avg_rating=excluded.avg_rating,
                completed_jobs=excluded.completed_jobs
            """, (ratee_id, round(avg, 2), count))
            conn.commit()
        return {"success": True, "avg_rating": round(avg, 2),
                "message": f"Rating {score}/5 saved. Reputation updated."}

    # ── AI MATCH ──────────────────────────────────────────────────────────────

    def ai_match_jobs(self, agent_id: str, limit: int = 10) -> List[Dict]:
        with _get_db() as conn:
            profile = conn.execute(
                "SELECT * FROM agent_profiles WHERE user_id=?", (agent_id,)).fetchone()
        agent_skills = json.loads(dict(profile)["skills"]) if profile else []
        all_jobs = self.list_jobs(status="open", limit=100)
        scored = [(j, ai_match_score(j, agent_skills)) for j in all_jobs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [j for j, s in scored[:limit]]

    # ── AGENT PROFILE ─────────────────────────────────────────────────────────

    def update_agent_profile(self, user_id: str, display_name: str = "",
                              bio: str = "", skills: List[str] = None,
                              hourly_rate: str = "negotiable",
                              available: bool = True,
                              universe_scope: str = "global") -> Dict[str, Any]:
        with _get_db() as conn:
            conn.execute("""
                INSERT INTO agent_profiles (user_id, display_name, bio, skills, hourly_rate, available, universe_scope)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET
                display_name=excluded.display_name,
                bio=excluded.bio,
                skills=excluded.skills,
                hourly_rate=excluded.hourly_rate,
                available=excluded.available,
                universe_scope=excluded.universe_scope,
                updated_at=datetime('now')
            """, (user_id, display_name, bio, json.dumps(skills or []),
                  hourly_rate, available, universe_scope))
            conn.commit()
        return {"success": True, "message": "Agent profile updated"}

    def get_agent_profile(self, user_id: str) -> Optional[Dict]:
        with _get_db() as conn:
            row = conn.execute("SELECT * FROM agent_profiles WHERE user_id=?",
                               (user_id,)).fetchone()
        if not row:
            return None
        p = dict(row)
        p["skills"] = json.loads(p.get("skills", "[]"))
        return p

    # ── STATS ─────────────────────────────────────────────────────────────────

    def marketplace_stats(self) -> Dict[str, Any]:
        with _get_db() as conn:
            stats = {
                "total_jobs": conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                "open_jobs": conn.execute("SELECT COUNT(*) FROM jobs WHERE status='open'").fetchone()[0],
                "completed_jobs": conn.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0],
                "total_agents": conn.execute("SELECT COUNT(*) FROM agent_profiles").fetchone()[0],
                "available_agents": conn.execute("SELECT COUNT(*) FROM agent_profiles WHERE available=1").fetchone()[0],
                "total_ratings": conn.execute("SELECT COUNT(*) FROM ratings").fetchone()[0],
                "open_disputes": conn.execute("SELECT COUNT(*) FROM disputes WHERE status='open'").fetchone()[0],
            }
        return stats


# ── Singleton ─────────────────────────────────────────────────────────────────
marketplace = JobMarketplace()
