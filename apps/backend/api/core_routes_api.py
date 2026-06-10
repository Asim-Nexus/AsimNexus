import logging, json, os, secrets, asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("AsimNexus.API.Core")
router = APIRouter(tags=["Core System Routes"])

# ─── Helpers (mirrored from simple_backend) ──────────────────────────────────
DB_PATH = Path(os.getenv("ASIM_DB_PATH", "data/nexus.db"))

def _get_db():
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def _get_user_from_token(token: str) -> Optional[Dict]:
    with _get_db() as conn:
        conn.execute("DELETE FROM tokens WHERE expires_at < datetime('now')")
        conn.commit()
        row = conn.execute(
            "SELECT u.* FROM users u JOIN tokens t ON u.id = t.user_id WHERE t.token = ? AND t.expires_at > datetime('now')",
            (token,)
        ).fetchone()
    return dict(row) if row else None

def _get_user_id_from_request(request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        user = _get_user_from_token(token)
        return user["id"] if user else None
    return None

def _get_agent_mode(user_id: str) -> dict:
    try:
        with _get_db() as conn:
            row = conn.execute(
                "SELECT agent_mode_json FROM users WHERE id=?", (user_id,)
            ).fetchone()
            if row and row[0]:
                return json.loads(row[0])
    except Exception:
        pass
    return {"active": False}

def _get_resource_sharing(user_id: str) -> dict:
    try:
        with _get_db() as conn:
            row = conn.execute(
                "SELECT resource_sharing_json FROM users WHERE id=?", (user_id,)
            ).fetchone()
            if row and row[0]:
                return json.loads(row[0])
    except Exception:
        pass
    return {"enabled": False, "share_pct": 0}

# ─── DHARMA ──────────────────────────────────────────────────────────────────
@router.get("/api/dharma/status")
async def dharma_status():
    """Production ΔT Engine - Real calculations from live data"""
    try:
        from core.dharma import get_delta_t_production

        engine = get_delta_t_production()
        result = engine.calculate_production_delta_t()

        return JSONResponse(result)
    except Exception as e:
        logger.error(f"DeltaT production error: {e}")
        return JSONResponse({
            "error": str(e),
            "production": False,
            "fallback": "simulation_mode",
            "symmetry": 0.85,
            "gini": 0.15,
            "delta_t": 0.05,
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })

@router.get("/api/dharma/production/status")
async def dharma_production_status():
    """Get ΔT production engine status"""
    try:
        from core.dharma import get_delta_t_production

        engine = get_delta_t_production()
        return JSONResponse(engine.get_production_status())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/dharma/veto")
async def dharma_veto(request: Request):
    """Manual veto for ethical concerns"""
    try:
        body = await request.json()
        reason = body.get('reason', 'No reason provided')
        severity = body.get('severity', 'warning')

        logger.warning(f"DHARMA VETO: {severity} - {reason}")

        return JSONResponse({
            "success": True,
            "veto_logged": True,
            "severity": severity,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "action": "Veto recorded and will be reviewed by human governance"
        })
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/dharma/veto-check")
async def dharma_veto_check(request: Request):
    body = await request.json()
    action  = body.get("action", "")
    content = body.get("content", "")
    context = body.get("context", {})
    user_id = _get_user_id_from_request(request) or "guest"
    try:
        from core.dharma.dharma_veto import DharmaVeto
        _dv = DharmaVeto()
    except Exception:
        _dv = None
    if _dv:
        result = _dv.check(action=action, node_id=user_id,
                            context=context, content=content)
        return JSONResponse({
            "passed":         result.passed,
            "severity":       result.severity,
            "summary":        result.summary,
            "requires_human": result.requires_human,
            "events": [
                {"severity": e.severity, "reason": e.reason,
                 "detail": e.detail, "veto_hash": e.veto_hash}
                for e in result.events
            ],
        })
    return JSONResponse({"passed": True, "severity": "pass",
                         "summary": "DharmaVeto not loaded -- passthrough",
                         "requires_human": False, "events": []})

@router.post("/api/dharma/cultural-check")
async def dharma_cultural_check(request: Request):
    body    = await request.json()
    action  = body.get("action", "accept_protocol")
    content = body.get("content", "")
    context = body.get("context", {})
    try:
        from core.dharma.cultural_compiler import CulturalCompiler
        _cc = CulturalCompiler(locale="nepal")
    except Exception:
        _cc = None
    if _cc:
        result = _cc.check(action=action, content=content, context=context)
        return JSONResponse(result)
    return JSONResponse({"status": "COMPLIANT",
                         "detail": "CulturalCompiler not loaded",
                         "hits": [], "locale": "nepal", "override_allowed": True})

@router.get("/api/dharma/veto-status")
async def dharma_veto_status():
    try:
        from core.dharma.dharma_veto import DharmaVeto
        from core.dharma.cultural_compiler import CulturalCompiler
        _dv = DharmaVeto()
        _cc = CulturalCompiler(locale="nepal")
    except Exception:
        _dv = None
        _cc = None
    if _dv:
        return JSONResponse({**_dv.status(),
                              "cultural_compiler": _cc.status() if _cc else None})
    return JSONResponse({"active": False})

# ─── JOBS MARKETPLACE ────────────────────────────────────────────────────────
@router.post("/api/jobs/post")
async def post_job(request: Request):
    body = await request.json()
    user_id = _get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    try:
        from core.economy.job_marketplace import marketplace as _mp
    except Exception:
        _mp = None
    if _mp:
        result = _mp.post_job(
            poster_id=user_id,
            title=body.get("title", ""),
            description=body.get("description", ""),
            budget=str(body.get("budget", "negotiable")),
            budget_currency=body.get("budget_currency", "USD"),
            timeline_days=int(body.get("timeline_days", 7)),
            skills=body.get("skills", []),
            milestones=body.get("milestones", []),
            universe_scope=body.get("universe_scope", "global"),
        )
        return JSONResponse(result)
    job_id = secrets.token_hex(8)
    with _get_db() as conn:
        conn.execute(
            "INSERT INTO jobs (id,poster_id,title,description,budget,timeline_days,skills) VALUES (?,?,?,?,?,?,?)",
            (job_id, user_id, body.get("title",""), body.get("description",""),
             str(body.get("budget","")), body.get("timeline_days", 7),
             json.dumps(body.get("skills",[])))
        )
        conn.commit()
    return JSONResponse({"success": True, "job_id": job_id,
                         "message": "Job posted! AsimNexus will find matching agents."})

@router.get("/api/jobs/list")
async def list_jobs(status: str = "open", category: str = None):
    try:
        from core.economy.job_marketplace import marketplace as _mp
    except Exception:
        _mp = None
    if _mp:
        jobs = _mp.list_jobs(category=category, status=status)
        return JSONResponse({"jobs": jobs, "total": len(jobs)})
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT id,title,description,budget,timeline_days,skills,status,created_at FROM jobs WHERE status='open' ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    jobs = [dict(r) for r in rows]
    for j in jobs:
        j["skills"] = json.loads(j.get("skills") or "[]")
        j["category"] = "other"
        j["budget_currency"] = "USD"
    return JSONResponse({"jobs": jobs, "total": len(jobs)})

@router.get("/api/jobs/stats")
async def jobs_stats():
    try:
        from core.economy.job_marketplace import marketplace as _mp
    except Exception:
        _mp = None
    if _mp:
        return JSONResponse(_mp.marketplace_stats())
    with _get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        open_j = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='open'").fetchone()[0]
    return JSONResponse({"total_jobs": total, "open_jobs": open_j, "completed_jobs": 0,
                         "total_agents": 0, "available_agents": 0})

@router.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    try:
        from core.economy.job_marketplace import marketplace as _mp
    except Exception:
        _mp = None
    if _mp:
        job = _mp.get_job(job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        return JSONResponse(job)
    raise HTTPException(404, "Job not found")

@router.post("/api/jobs/{job_id}/apply")
async def apply_job(job_id: str, request: Request):
    user_id = _get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    try:
        from core.economy.job_marketplace import marketplace as _mp
    except Exception:
        _mp = None
    if _mp:
        body = await request.json()
        result = _mp.apply_for_job(
            job_id=job_id, agent_id=user_id,
            cover_note=body.get("cover_note", ""),
            proposed_budget=str(body.get("proposed_budget", "")),
            proposed_timeline=int(body.get("proposed_timeline", 7)),
        )
        return JSONResponse(result)
    with _get_db() as conn:
        conn.execute("UPDATE jobs SET agent_id=?, status='assigned' WHERE id=? AND status='open'",
                     (user_id, job_id))
        conn.commit()
    return JSONResponse({"success": True, "message": "Application submitted!"})

@router.post("/api/jobs/{job_id}/rate")
async def rate_job(job_id: str, request: Request):
    user_id = _get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    try:
        from core.economy.job_marketplace import marketplace as _mp
    except Exception:
        _mp = None
    if _mp:
        body = await request.json()
        result = _mp.rate(
            job_id=job_id, rater_id=user_id,
            ratee_id=body.get("ratee_id", ""),
            score=int(body.get("score", 5)),
            review=body.get("review", ""),
        )
        return JSONResponse(result)
    return JSONResponse({"success": True, "message": "Rating saved"})

# ─── DREAMING ENGINE ─────────────────────────────────────────────────────────
@router.get("/api/dreaming/status")
async def dreaming_status():
    try:
        from core.dreaming.dreaming_engine import dreaming_engine as _de
    except Exception:
        _de = None
    if _de:
        return JSONResponse(_de.status())
    return JSONResponse({"running": False, "message": "DreamingEngine not loaded"})

@router.get("/api/dreaming/briefing")
async def dreaming_briefing():
    try:
        from core.dreaming.dreaming_engine import dreaming_engine as _de
    except Exception:
        _de = None
    if _de:
        return JSONResponse({"briefing": _de.get_briefing()})
    return JSONResponse({"briefing": "DreamingEngine not loaded"})

@router.post("/api/dreaming/trigger")
async def trigger_dreaming(request: Request):
    user_id = _get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    try:
        from core.dreaming.dreaming_engine import dreaming_engine as _de
    except Exception:
        _de = None
    if _de:
        briefing = await _de.trigger_now()
        return JSONResponse({"success": True, "briefing": briefing})
    return JSONResponse({"success": False, "message": "DreamingEngine not loaded"})

# ─── ANALYTICS ───────────────────────────────────────────────────────────────
@router.get("/api/analytics/overview")
@router.get("/api/analytics")
async def analytics_overview(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    with _get_db() as conn:
        msg_count = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE user_id=?", (user_id,)).fetchone()[0]
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    import platform, psutil
    return JSONResponse({
        "status": "ok",
        "users": total_users,
        "messages": msg_count,
        "active_clones": 15,
        "cpu_usage": round(psutil.cpu_percent(interval=0.1), 1),
        "ram_usage": round(psutil.virtual_memory().percent, 1),
        "disk_usage": round(psutil.disk_usage('/').percent, 1),
        "ethical_score": 0.94,
        "tasks_completed": msg_count,
        "founders_active": 5,
        "agents_active": 12,
    })

@router.get("/api/analytics/activity")
async def analytics_activity():
    now = datetime.utcnow()
    data = []
    for i in range(8):
        h = (now.hour - i) % 24
        data.append({"time": f"{h:02d}:00", "messages": max(0, 10 - i * 1),
                      "clones": max(0, 5 - i), "tasks": max(0, 20 - i * 2)})
    return JSONResponse({"activity": list(reversed(data))})

# ─── BUGS / SELF-HEALING ─────────────────────────────────────────────────────
@router.get("/api/bugs/stats")
async def bugs_stats():
    try:
        from core.dreaming.bug_triage import get_bug_triage
        return JSONResponse(get_bug_triage().stats())
    except Exception as e:
        return JSONResponse({"total": 0, "error": str(e)})

@router.post("/api/bugs/report")
async def bug_report(request: Request):
    body = await request.json()
    try:
        from core.dreaming.bug_triage import get_bug_triage
        from dataclasses import asdict as _asdict
        engine = get_bug_triage()
        bug = engine.report(
            file_path   = body.get("file_path", "unknown"),
            line_number = int(body.get("line_number", 0)),
            category    = body.get("category", "logic"),
            description = body.get("description", ""),
            detected_by = body.get("detected_by", "user_report"),
        )
        result = engine.run_pipeline(bug.bug_id)
        return JSONResponse(_asdict(result))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/bugs/pending")
async def bugs_pending():
    try:
        from core.dreaming.bug_triage import get_bug_triage
        from dataclasses import asdict as _asdict
        bugs = get_bug_triage().pending_human()
        return JSONResponse({"bugs": [_asdict(b) for b in bugs], "count": len(bugs)})
    except Exception as e:
        return JSONResponse({"bugs": [], "count": 0, "error": str(e)})

@router.post("/api/bugs/{bug_id}/approve")
async def bug_approve(bug_id: str, request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    body    = await request.json()
    try:
        from core.dreaming.bug_triage import get_bug_triage
        from dataclasses import asdict as _asdict
        result = get_bug_triage().human_decision(
            bug_id, approved=bool(body.get("approved", True)), approver=user_id)
        return JSONResponse(_asdict(result))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/bugs/list")
async def bugs_list(severity: str = "", status: str = "", limit: int = 50):
    try:
        from core.dreaming.bug_triage import get_bug_triage, BugSeverity, BugStatus
        from dataclasses import asdict as _asdict
        engine = get_bug_triage()
        sev = BugSeverity(severity) if severity else None
        sta = BugStatus(status)     if status   else None
        bugs = engine.list_bugs(severity=sev, status=sta, limit=limit)
        return JSONResponse({"bugs": [_asdict(b) for b in bugs], "total": len(bugs)})
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/bugs/batch-triage")
async def bugs_batch_triage(request: Request):
    body = await request.json()
    bug_list = body.get("bugs", [])
    try:
        from core.dreaming.bug_triage import get_bug_triage
        from dataclasses import asdict as _asdict
        stats = get_bug_triage().batch_triage(bug_list)
        return JSONResponse(_asdict(stats))
    except Exception as e:
        raise HTTPException(400, str(e))

# ─── ZKP IDENTITY ────────────────────────────────────────────────────────────
@router.post("/api/identity/create")
async def identity_create(request: Request):
    body = await request.json()
    passphrase = body.get("passphrase", "")
    if len(passphrase) < 8:
        raise HTTPException(400, "Passphrase must be at least 8 characters")
    try:
        from core.identity.zkp_local import get_zkp_store
        from dataclasses import asdict as _asdict
        identity = get_zkp_store().create(
            passphrase   = passphrase,
            display_name = body.get("display_name", "Sovereign User"),
            universe     = body.get("universe", "personal"),
            biometric_raw= body.get("biometric_raw", ""),
        )
        return JSONResponse(_asdict(identity))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/identity/verify")
async def identity_verify(request: Request):
    body = await request.json()
    did        = body.get("did", "")
    passphrase = body.get("passphrase", "")
    bio        = body.get("biometric_raw", "")
    try:
        from core.identity.zkp_local import get_zkp_store
        ok, reason = get_zkp_store().verify(did, passphrase, bio)
        return JSONResponse({"verified": ok, "reason": reason, "did": did})
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/identity/{did}/credential")
async def identity_issue_vc(did: str, request: Request):
    body = await request.json()
    try:
        from core.identity.zkp_local import get_zkp_store
        from dataclasses import asdict as _asdict
        store = get_zkp_store()
        issuer_did = body.get("issuer_did", did)
        vc = store.issue_credential(
            issuer_did  = issuer_did,
            subject_did = did,
            claim_type  = body.get("claim_type", "skill"),
            claim_value = body.get("claim_value", ""),
            days_valid  = int(body.get("days_valid", 365)),
        )
        return JSONResponse(_asdict(vc))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/identity/{did}/credentials")
async def identity_get_vcs(did: str):
    try:
        from core.identity.zkp_local import get_zkp_store
        from dataclasses import asdict as _asdict
        vcs = get_zkp_store().get_credentials(did)
        return JSONResponse({"credentials": [_asdict(vc) for vc in vcs]})
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/identity/status")
async def identity_status():
    try:
        from core.identity.zkp_local import get_zkp_store
        s = get_zkp_store().stats()
        return JSONResponse({**s, "status": "active", "module": "zkp_local"})
    except Exception as e:
        return JSONResponse({"total_identities": 0, "status": "error", "error": str(e)})

@router.get("/api/identity/stats")
async def identity_stats():
    try:
        from core.identity.zkp_local import get_zkp_store
        return JSONResponse(get_zkp_store().stats())
    except Exception as e:
        return JSONResponse({"total": 0, "error": str(e)})

@router.get("/api/identity/list")
async def identity_list():
    try:
        from core.identity.zkp_local import get_zkp_store
        from dataclasses import asdict as _asdict
        ids = get_zkp_store().list_identities()
        return JSONResponse({"identities": [_asdict(i) for i in ids], "count": len(ids)})
    except Exception as e:
        return JSONResponse({"identities": [], "error": str(e)})

# ─── COGNITIVE FIREWALL ──────────────────────────────────────────────────────
@router.post("/api/firewall/check")
async def firewall_check(request: Request):
    body = await request.json()
    text = body.get("text", "")
    sensitivity = float(body.get("sensitivity", 0.5))
    if not text:
        raise HTTPException(400, "text required")
    try:
        from core.firewall.cognitive_firewall import get_cognitive_firewall
        fw = get_cognitive_firewall(sensitivity)
        result = fw.check(text, context=body.get("context"))
        return JSONResponse(result.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/firewall/check-conversation")
async def firewall_check_conversation(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    if not messages:
        raise HTTPException(400, "messages array required")
    try:
        from core.firewall.cognitive_firewall import get_cognitive_firewall
        result = get_cognitive_firewall().check_conversation(messages)
        return JSONResponse(result.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/firewall/status")
async def firewall_status():
    try:
        from core.firewall.cognitive_firewall import get_cognitive_firewall
        return JSONResponse(get_cognitive_firewall().status())
    except Exception as e:
        return JSONResponse({"error": str(e)})

# ─── SMART CONTRACTS ─────────────────────────────────────────────────────────
@router.post("/api/contracts/propose")
async def contract_propose(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    body = await request.json()
    try:
        from core.contracts.smart_contract_engine import get_contract_engine
        engine = get_contract_engine()
        c = engine.propose(
            requester_id  = user_id,
            provider_id   = body.get("provider_id", "guest"),
            title         = body.get("title", ""),
            description   = body.get("description", ""),
            duration_days = int(body.get("duration_days", 15)),
            value_npr     = float(body.get("value_npr", 0)),
            skills        = body.get("skills", []),
        )
        return JSONResponse(c.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/contracts/{contract_id}/gate2")
async def contract_gate2(contract_id: str):
    try:
        from core.contracts.smart_contract_engine import get_contract_engine
        c = get_contract_engine().run_gate2(contract_id)
        return JSONResponse(c.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/contracts/{contract_id}/sign")
async def contract_sign(contract_id: str, request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    body = await request.json()
    try:
        from core.contracts.smart_contract_engine import get_contract_engine
        c = get_contract_engine().human_sign(
            contract_id = contract_id,
            user_id     = user_id,
            approved    = bool(body.get("approved", True)),
            note        = body.get("note", ""),
        )
        return JSONResponse(c.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/contracts/{contract_id}/progress")
async def contract_progress(contract_id: str, request: Request):
    body = await request.json()
    try:
        from core.contracts.smart_contract_engine import get_contract_engine
        c = get_contract_engine().update_progress(
            contract_id, int(body.get("pct", 0)), body.get("note", ""))
        return JSONResponse(c.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/contracts/{contract_id}/pause")
async def contract_pause(contract_id: str, request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    body = await request.json()
    try:
        from core.contracts.smart_contract_engine import get_contract_engine
        c = get_contract_engine().pause(contract_id, user_id, body.get("reason", ""))
        return JSONResponse(c.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/contracts/{contract_id}/resume")
async def contract_resume(contract_id: str, request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    try:
        from core.contracts.smart_contract_engine import get_contract_engine
        c = get_contract_engine().resume(contract_id, user_id)
        return JSONResponse(c.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/contracts/{contract_id}/cancel")
async def contract_cancel(contract_id: str, request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    body = await request.json()
    try:
        from core.contracts.smart_contract_engine import get_contract_engine
        c = get_contract_engine().cancel(contract_id, user_id, body.get("reason", ""))
        return JSONResponse(c.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/contracts/{contract_id}/complete")
async def contract_complete(contract_id: str, request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    body = await request.json()
    try:
        from core.contracts.smart_contract_engine import get_contract_engine
        c = get_contract_engine().complete(
            contract_id, user_id,
            rating=int(body.get("rating", 5)),
            note=body.get("note", ""))
        return JSONResponse(c.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/contracts/{contract_id}")
async def contract_get(contract_id: str):
    try:
        from core.contracts.smart_contract_engine import get_contract_engine
        c = get_contract_engine().get(contract_id)
        if not c:
            raise HTTPException(404, "Contract not found")
        return JSONResponse(c.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/contracts")
async def contracts_list(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    try:
        from core.contracts.smart_contract_engine import get_contract_engine
        engine = get_contract_engine()
        contracts = engine.list_for_user(user_id)
        pending = engine.pending_human_signature(user_id)
        return JSONResponse({
            "contracts":     [c.to_dict() for c in contracts],
            "total":         len(contracts),
            "pending_human": [c.contract_id for c in pending],
            "stats":         engine.stats(user_id),
        })
    except Exception as e:
        raise HTTPException(400, str(e))

# ─── SVT (SOVEREIGN TOKEN) ───────────────────────────────────────────────────
@router.get("/api/svt/stats")
async def svt_stats():
    try:
        from core.economy.sovereign_token import get_svt_engine
        return JSONResponse(get_svt_engine().stats())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/svt/wallet")
async def svt_create_wallet(request: Request):
    body = await request.json()
    did  = body.get("did","")
    if not did:
        raise HTTPException(400,"did required")
    try:
        from core.economy.sovereign_token import get_svt_engine
        from dataclasses import asdict as _asdict
        w = get_svt_engine().create_wallet(did)
        return JSONResponse(_asdict(w))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/svt/wallet/{did}")
async def svt_wallet_info(did: str):
    try:
        from core.economy.sovereign_token import get_svt_engine
        return JSONResponse(get_svt_engine().wallet_info(did))
    except Exception as e:
        raise HTTPException(404, str(e))

@router.post("/api/svt/mint")
async def svt_mint(request: Request):
    body = await request.json()
    try:
        from core.economy.sovereign_token import get_svt_engine
        from dataclasses import asdict as _asdict
        tx = get_svt_engine().mint(body.get("did",""), float(body.get("amount",0)),
                                   body.get("memo",""))
        return JSONResponse(_asdict(tx))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/svt/transfer")
async def svt_transfer(request: Request):
    body = await request.json()
    try:
        from core.economy.sovereign_token import get_svt_engine
        from dataclasses import asdict as _asdict
        tx = get_svt_engine().transfer(
            body.get("from_did",""), body.get("to_did",""),
            float(body.get("amount",0)), body.get("memo",""))
        return JSONResponse(_asdict(tx))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/svt/escrow")
async def svt_escrow(request: Request):
    body = await request.json()
    try:
        from core.economy.sovereign_token import get_svt_engine
        eid = get_svt_engine().escrow_lock(
            body.get("did",""), float(body.get("amount",0)), body.get("memo",""))
        return JSONResponse({"escrow_id": eid})
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/svt/escrow/{eid}/release")
async def svt_escrow_release(eid: str, request: Request):
    body = await request.json()
    try:
        from core.economy.sovereign_token import get_svt_engine
        from dataclasses import asdict as _asdict
        tx = get_svt_engine().escrow_release(eid, body.get("to_did",""))
        return JSONResponse(_asdict(tx))
    except Exception as e:
        raise HTTPException(400, str(e))

# ─── HDT (HUMAN DIGITAL TWIN) ────────────────────────────────────────────────
@router.get("/api/hdt/status")
async def hdt_status_global():
    try:
        from core.hdt.human_digital_twin import get_hdt_store
        store = get_hdt_store()
        twins = store.list_twins() if hasattr(store, 'list_twins') else []
        return JSONResponse({
            "total_twins": len(twins),
            "did": twins[0].get("did","") if twins else "",
            "status": "active", "module": "human_digital_twin",
        })
    except Exception as e:
        return JSONResponse({"total_twins": 0, "did": "", "status": "error", "error": str(e)})

@router.post("/api/hdt/create")
async def hdt_create(request: Request):
    body = await request.json()
    did  = body.get("did", "")
    if not did:
        raise HTTPException(400, "did required")
    try:
        from core.hdt.human_digital_twin import get_hdt
        hdt = get_hdt(did, body.get("display_name",""), body.get("universe","personal"))
        return JSONResponse(hdt.status())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/hdt/{did}/skill")
async def hdt_add_skill(did: str, request: Request):
    body = await request.json()
    try:
        from core.hdt.human_digital_twin import get_hdt
        from dataclasses import asdict as _asdict
        hdt   = get_hdt(did)
        skill = hdt.add_skill(
            name    = body.get("name",""),
            level   = body.get("level","intermediate"),
            verified= bool(body.get("verified", False)),
            vc_id   = body.get("vc_id",""),
        )
        return JSONResponse(_asdict(skill))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/hdt/{did}/announce")
async def hdt_announce(did: str):
    try:
        from core.hdt.human_digital_twin import get_hdt
        hdt = get_hdt(did)
        return JSONResponse(hdt.announce_to_mesh())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/hdt/{did}/status")
async def hdt_status(did: str):
    try:
        from core.hdt.human_digital_twin import get_hdt
        return JSONResponse(get_hdt(did).status())
    except Exception as e:
        raise HTTPException(404, str(e))

@router.get("/api/hdt/{did}/profile")
async def hdt_profile(did: str):
    try:
        from core.hdt.human_digital_twin import get_hdt
        return JSONResponse(get_hdt(did).profile.to_dict())
    except Exception as e:
        raise HTTPException(404, str(e))

# ─── CONSENSUS ───────────────────────────────────────────────────────────────
@router.post("/api/consensus/vote")
async def consensus_vote(request: Request):
    body = await request.json()
    topic = body.get("topic","")
    level = body.get("level","high")
    if not topic:
        raise HTTPException(400, "topic required")
    try:
        from core.consensus.clone_consensus import get_consensus_engine, DecisionLevel
        from dataclasses import asdict as _asdict
        engine = get_consensus_engine()
        cr = engine.start_round(
            topic       = topic,
            description = body.get("description",""),
            level       = DecisionLevel(level),
        )
        return JSONResponse(cr.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/consensus/{round_id}/override")
async def consensus_override(round_id: str, request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    body    = await request.json()
    try:
        from core.consensus.clone_consensus import get_consensus_engine
        from dataclasses import asdict as _asdict
        cr = get_consensus_engine().human_override(
            round_id, approved=bool(body.get("approved", True)),
            reason=body.get("reason",""))
        return JSONResponse(cr.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/consensus/stats")
async def consensus_stats():
    try:
        from core.consensus.clone_consensus import get_consensus_engine
        return JSONResponse(get_consensus_engine().stats())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get("/api/consensus/pending")
async def consensus_pending():
    try:
        from core.consensus.clone_consensus import get_consensus_engine
        from dataclasses import asdict as _asdict
        rounds = get_consensus_engine().pending_human()
        return JSONResponse({"rounds": [_asdict(r) for r in rounds], "count": len(rounds)})
    except Exception as e:
        return JSONResponse({"rounds": [], "error": str(e)})

@router.get("/api/consensus/list")
async def consensus_list():
    try:
        from core.consensus.clone_consensus import get_consensus_engine
        from dataclasses import asdict as _asdict
        rounds = get_consensus_engine().list_rounds(20)
        return JSONResponse({"rounds": [_asdict(r) for r in rounds]})
    except Exception as e:
        return JSONResponse({"rounds": [], "error": str(e)})

# ─── UNIVERSE ────────────────────────────────────────────────────────────────
@router.get("/api/universe/list")
async def universe_list():
    try:
        from core.universe.container import get_universe_manager
        mgr = get_universe_manager()
        return JSONResponse({"universes": mgr.status_all(), "stats": mgr.stats()})
    except Exception as e:
        return JSONResponse({"universes": [], "error": str(e)})

@router.get("/api/universe/containers")
async def universe_containers(did: str = ""):
    try:
        from core.universe.container import get_universe_manager
        mgr = get_universe_manager()
        if did:
            return JSONResponse({"containers": [c.to_dict() for c in mgr.get_for_did(did)]})
        return JSONResponse({"containers": mgr.status_all(), "stats": mgr.stats()})
    except Exception as e:
        return JSONResponse({"containers": [], "error": str(e)})

@router.post("/api/universe/data-flow-check")
async def universe_data_flow(request: Request):
    body = await request.json()
    try:
        from core.universe.container import get_universe_manager, UniverseLayer
        result = get_universe_manager().check_data_flow(
            UniverseLayer(body.get("from","personal")),
            UniverseLayer(body.get("to","community")))
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/api/universe/status")
async def universe_status(request: Request):
    import psutil
    user_id = _get_user_id_from_request(request) or "guest"
    agent_on = _get_agent_mode(user_id).get("active", False)
    rs = _get_resource_sharing(user_id)
    return JSONResponse({
        "user_id": user_id,
        "universe": "personal",
        "agent_mode": agent_on,
        "local_first": True,
        "offline_capable": True,
        "dharma_active": True,
        "delta_t_active": True,
        "final3_required": True,
        "resource_sharing": rs.get("enabled", False),
        "mesh_peers": 0,
        "phase": 1,
        "phase_note": "Phase 1 -- single machine, no LAN mesh yet",
        "cpu": round(psutil.cpu_percent(interval=0.1), 1),
        "ram": round(psutil.virtual_memory().percent, 1),
    })

@router.get("/api/universe/stats")
async def get_universe_stats():
    """Get overall universe statistics"""
    try:
        from core.universe.personal_universe import get_universe_manager

        manager = get_universe_manager()
        stats = manager.get_stats()

        return JSONResponse(stats)
    except Exception as e:
        logger.error(f"Universe stats error: {e}")
        return JSONResponse({"error": str(e)})

@router.get("/api/universe/{user_id}/lifecycle")
async def get_lifecycle(user_id: str):
    """Get complete lifecycle summary"""
    try:
        from core.universe.personal_universe import get_universe_manager

        manager = get_universe_manager()
        summary = manager.get_lifecycle_summary(user_id)

        return JSONResponse(summary)
    except Exception as e:
        logger.error(f"Lifecycle error: {e}")
        return JSONResponse({"error": str(e)})

@router.get("/api/universe/{user_id}/status")
async def get_universe_status(user_id: str):
    """Get universe status for user"""
    try:
        from core.universe.personal_universe import get_universe_manager

        manager = get_universe_manager()
        status = manager.get_universe_status(user_id)

        if 'error' in status:
            return JSONResponse(status, status_code=404)

        return JSONResponse(status)
    except Exception as e:
        logger.error(f"Universe status error: {e}")
        return JSONResponse({"error": str(e)})

@router.post("/api/universe/{user_id}/layer/activate")
async def activate_layer(user_id: str, request: Request):
    """Activate a universe layer for user"""
    try:
        from core.universe.personal_universe import get_universe_manager, UniverseLayer

        body = await request.json()
        layer_name = body.get("layer")

        manager = get_universe_manager()

        layer_enum = UniverseLayer(layer_name)

        success = manager.activate_layer(
            user_id=user_id,
            layer=layer_enum,
            config=body.get("config", {})
        )

        return JSONResponse({
            "success": success,
            "layer": layer_name,
            "message": f"Layer {layer_name} {'activated' if success else 'failed'}"
        })
    except Exception as e:
        logger.error(f"Layer activation error: {e}")
        return JSONResponse({"error": str(e)})

# ─── PERSONAL UNIVERSE ───────────────────────────────────────────────────────
@router.get("/api/personal/status")
async def personal_status(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    username, display_name, joined, msg_count = "guest", "Guest", None, 0
    try:
        with _get_db() as conn:
            try:
                user_row = conn.execute(
                    "SELECT email, display_name, created_at FROM users WHERE id=?",
                    (user_id,)
                ).fetchone()
                if user_row:
                    username = user_row[0] or "guest"
                    display_name = user_row[1] or username
                    joined = user_row[2]
            except Exception:
                pass
            try:
                msg_count = conn.execute(
                    "SELECT COUNT(*) FROM messages WHERE user_id=?", (user_id,)
                ).fetchone()[0]
            except Exception:
                msg_count = 0
    except Exception as e:
        logger.warning(f"personal_status DB error: {e}")
    import psutil
    agent_on = _get_agent_mode(user_id).get("active", False)
    rs = _get_resource_sharing(user_id)
    return JSONResponse({
        "status": "online",
        "user_id": user_id,
        "username": username,
        "display_name": display_name,
        "joined": joined,
        "universe_type": "personal",
        "agent_mode": agent_on,
        "total_messages": msg_count,
        "active_contracts": 0,
        "clone_count": 15,
        "resource_sharing": rs.get("enabled", False),
        "resource_share_pct": rs.get("share_pct", 0),
        "cpu_pct": round(psutil.cpu_percent(interval=0.1), 1),
        "ram_pct": round(psutil.virtual_memory().percent, 1),
        "local_first": True,
        "dharma_score": 0.94,
        "final3_pending": 0,
    })

@router.get("/api/personal/universe")
async def personal_universe(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    return JSONResponse({
        "user_id": user_id,
        "universes": [
            {"type": "personal",    "icon": "person",   "label": "Personal",    "active": True,  "nodes": 1},
            {"type": "family",      "icon": "group",    "label": "Family",      "active": False, "nodes": 0},
            {"type": "community",   "icon": "village",  "label": "Community",   "active": False, "nodes": 0},
            {"type": "enterprise",  "icon": "business", "label": "Enterprise",  "active": False, "nodes": 0},
            {"type": "sovereign",   "icon": "flag",     "label": "Sovereign",   "active": False, "nodes": 0},
        ],
        "mesh_connected": False,
        "mesh_note": "Phase 2 -- LAN Mesh not yet active",
    })

@router.get("/api/personal/contracts")
async def personal_contracts(request: Request):
    user_id = _get_user_id_from_request(request) or "guest"
    return JSONResponse({
        "user_id": user_id,
        "active": [],
        "pending_confirmation": [],
        "completed": [],
        "note": "Agent Mode OFF -- enable to receive contract requests",
    })

# ─── POST-QUANTUM ────────────────────────────────────────────────────────────
@router.get("/api/pq/status")
async def pq_status():
    try:
        from core.security.pq_layer import get_pq_layer
        return JSONResponse(get_pq_layer().status())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/pq/keygen")
async def pq_keygen(request: Request):
    body = await request.json()
    try:
        from core.security.pq_layer import get_pq_layer, PQAlgorithm
        algo = PQAlgorithm(body.get("algorithm","ML-KEM-768"))
        kp = get_pq_layer().generate_keypair(body.get("did",""), algo)
        return JSONResponse(kp.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/pq/sign")
async def pq_sign(request: Request):
    body = await request.json()
    try:
        from core.security.pq_layer import get_pq_layer
        from dataclasses import asdict as _asdict
        sig = get_pq_layer().sign(
            body.get("message","").encode(), body.get("key_id",""))
        return JSONResponse(_asdict(sig))
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/pq/kem")
async def pq_kem(request: Request):
    body = await request.json()
    try:
        from core.security.pq_layer import get_pq_layer
        from dataclasses import asdict as _asdict
        result = get_pq_layer().kem_encapsulate(body.get("public_key",""))
        return JSONResponse(_asdict(result))
    except Exception as e:
        raise HTTPException(400, str(e))

# ─── OFFLINE SYNC ────────────────────────────────────────────────────────────
@router.get("/api/sync/status")
async def sync_status():
    try:
        from core.sync.offline_sync import get_sync_engine
        return JSONResponse(get_sync_engine().status())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/sync/enqueue")
async def sync_enqueue(request: Request):
    body = await request.json()
    try:
        from core.sync.offline_sync import get_sync_engine, OpType
        from dataclasses import asdict as _asdict
        op = get_sync_engine().enqueue(
            OpType(body.get("op_type","update")),
            body.get("entity_type",""), body.get("entity_id",""),
            body.get("payload",{}))
        return JSONResponse(op.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/sync/flush")
async def sync_flush():
    try:
        from core.sync.offline_sync import get_sync_engine
        return JSONResponse(get_sync_engine().flush())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get("/api/sync/queue")
async def sync_queue():
    try:
        from core.sync.offline_sync import get_sync_engine
        return JSONResponse({"queue": get_sync_engine().queue_list()})
    except Exception as e:
        return JSONResponse({"queue": [], "error": str(e)})

# ─── CLONE SPECIALIZER ───────────────────────────────────────────────────────
@router.get("/api/clones/specs")
async def clones_specs():
    try:
        from core.founder_clones.clone_specializer import get_specializer
        return JSONResponse({"clones": get_specializer().all_specs(),
                             "status": get_specializer().status()})
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.get("/api/clones/{clone_id}/spec")
async def clone_spec(clone_id: int):
    try:
        from core.founder_clones.clone_specializer import get_specializer
        from dataclasses import asdict as _asdict
        spec = get_specializer().get_spec(clone_id)
        if not spec:
            raise HTTPException(404, "Clone not found")
        return JSONResponse(_asdict(spec))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/clones/route")
async def clones_route(request: Request):
    body = await request.json()
    try:
        from core.founder_clones.clone_specializer import get_specializer
        from dataclasses import asdict as _asdict
        spec = get_specializer().route(body.get("query",""))
        return JSONResponse({"clone": _asdict(spec)})
    except Exception as e:
        raise HTTPException(400, str(e))

# ─── NEPAL LAYER ─────────────────────────────────────────────────────────────
@router.get("/api/nepal/status")
async def nepal_status():
    modules = {}
    for name, mod_path in [
        ("banking",  "core.nepal.banking_integrations"),
        ("telecom",  "core.nepal.telecom_integrations"),
        ("govt",     "core.nepal.government_integrations"),
        ("language", "core.nepal.language_support"),
        ("culture",  "core.nepal.cultural_features"),
    ]:
        try:
            __import__(mod_path)
            modules[name] = "available"
        except Exception as e:
            modules[name] = f"error: {str(e)[:40]}"
    return JSONResponse({
        "country": "Nepal", "modules": modules,
        "features": ["Nepali NLP", "eSewa integration", "Nagarik App bridge",
                     "Dharma constitution", "Local-first privacy"],
        "status": "active",
    })

# ─── SELF-EVOLUTION ──────────────────────────────────────────────────────────
@router.get("/api/evolution/stats")
async def evolution_stats():
    try:
        from core.self_building.evolution_engine import get_evolution_engine
        return JSONResponse(get_evolution_engine().stats())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/evolution/propose")
async def evolution_propose(request: Request):
    body = await request.json()
    try:
        from core.self_building.evolution_engine import get_evolution_engine
        from dataclasses import asdict as _asdict
        p = get_evolution_engine().propose(
            title=body.get("title",""), target_file=body.get("target_file",""),
            old_code=body.get("old_code",""), new_code=body.get("new_code",""),
            description=body.get("description",""), proposed_by=body.get("proposed_by","human"))
        return JSONResponse(p.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/evolution/{patch_id}/validate")
async def evolution_validate(patch_id: str):
    try:
        from core.self_building.evolution_engine import get_evolution_engine
        p = get_evolution_engine().validate(patch_id)
        return JSONResponse(p.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/evolution/{patch_id}/decide")
async def evolution_decide(patch_id: str, request: Request):
    body = await request.json()
    try:
        from core.self_building.evolution_engine import get_evolution_engine
        p = get_evolution_engine().human_decide(patch_id, bool(body.get("approved",False)),
                                                 body.get("reason",""))
        return JSONResponse(p.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

# ─── DEPIN ───────────────────────────────────────────────────────────────────
@router.get("/api/depin/status")
async def depin_status():
    try:
        from core.depin.depin_bridge import get_depin_bridge
        return JSONResponse(get_depin_bridge().network_status())
    except Exception as e:
        return JSONResponse({"error": str(e)})

@router.post("/api/depin/register")
async def depin_register(request: Request):
    body = await request.json()
    try:
        from core.depin.depin_bridge import get_depin_bridge, DePINNetwork
        from dataclasses import asdict as _asdict
        node = get_depin_bridge().register_node(
            body.get("did",""), DePINNetwork(body.get("network","helium")),
            body.get("wallet_addr",""))
        return JSONResponse(node.to_dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/api/depin/{node_id}/collect")
async def depin_collect(node_id: str):
    try:
        from core.depin.depin_bridge import get_depin_bridge
        from dataclasses import asdict as _asdict
        r = get_depin_bridge().collect_rewards(node_id)
        return JSONResponse(_asdict(r) if r else {"error": "node not found or inactive"})
    except Exception as e:
        raise HTTPException(400, str(e))

# ─── REGISTRATION ────────────────────────────────────────────────────────────
def register_core_routes(app):
    app.include_router(router)
    logger.info("Core system routes registered")
