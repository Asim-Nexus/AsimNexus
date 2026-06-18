#!/usr/bin/env python3
"""
AsimNexus = Digital Nepal Prototype
Full integration of Governance + User + Company + Mesh + Knowledge layers
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus_core import get_nexus

# ─── Unified Backend ─────────────────────────────────────────────────────────

nexus = get_nexus()

app = FastAPI(
    title="Digital Nepal - AsimNexus API",
    version="1.0.0",
    description="Nepal National Digital Operating System - Citizen/Company/Government API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# ─── User Endpoints ────────────────────────────────────────────────────────

@app.post("/api/v1/user/create")
async def create_citizen(user_id: str, citizen_data: str = "{}"):
    """Create citizen digital twin"""
    import json
    data = json.loads(citizen_data) if citizen_data else {}
    result = nexus.create_citizen(user_id, data)
    return result

@app.post("/api/v1/user/chat")
async def user_chat(message: str, user_id: str = "user"):
    """Citizen chat with ethical guard"""
    return nexus.citizen_chat(message, user_id)

# ─── Government Endpoints ───────────────────────────────────────────────────

@app.post("/api/v1/gov/propose")
async def government_action(sector: str, action: str):
    """Government action - 51% threshold enforcement"""
    return nexus.government_action(sector, action)

@app.post("/api/v1/gov/vote")
async def founder_vote(topic: str, sector: str, votes: str = "{}"):
    """Founder Clones 8/15 consensus"""
    import json
    return nexus.founder_vote(topic, sector, json.loads(votes) if votes else {})

# ─── Company Endpoints ──────────────────────────────────────────────────────

@app.post("/api/v1/company/action")
async def company_action(sector: str, action: str):
    """Company action - 49% threshold enforcement"""
    return nexus.company_action(sector, action)

# ─── Nepal Connectors Endpoints ───────────────────────────────────────────────────

@app.get("/api/v1/np/ministries")
async def nepal_ministries():
    """Get all Nepal ministries"""
    from connectors.nepal_connectors import MINISTRIES
    return {"count": len(MINISTRIES), "ministries": list(MINISTRIES.values())}

@app.get("/api/v1/np/provinces")
async def nepal_provinces():
    """Get all Nepal provinces"""
    from connectors.nepal_connectors import PROVINCES
    return {"count": len(PROVINCES), "provinces": list(PROVINCES.values())}

@app.get("/api/v1/np/districts")
async def nepal_districts():
    """Get all Nepal districts"""
    from connectors.nepal_connectors import DISTRICTS
    return {"count": len(DISTRICTS), "districts": list(DISTRICTS.values())}

@app.get("/api/v1/np/banks")
async def nepal_banks():
    """Get all Nepal banks"""
    from connectors.nepal_connectors import BANKS
    return {"count": len(BANKS), "banks": list(BANKS.values())}

@app.get("/api/v1/np/isps")
async def nepal_isps():
    """Get all Nepal ISPs"""
    from connectors.nepal_connectors import ISPS
    return {"count": len(ISPS), "isps": list(ISPS.values())}

# ─── Education Endpoints ──────────────────────────────────────────────────────

@app.get("/api/v1/education/universities")
async def get_universities():
    """Get all Nepal universities"""
    from connectors.education_connectors import UNIVERSITIES
    return {"count": len(UNIVERSITIES), "universities": list(UNIVERSITIES.values())}

@app.get("/api/v1/education/schools")
async def get_schools():
    """Get Nepal schools (sample)"""
    from connectors.education_connectors import SCHOOLS
    return {"count": len(SCHOOLS), "schools": list(SCHOOLS.values())}

@app.post("/api/v1/education/verify")
async def verify_edu_cert(cert_id: str):
    """Verify education certificate"""
    from connectors.education_connectors import verify_certificate
    return verify_certificate(cert_id)

# ─── Health Endpoints ──────────────────────────────────────────────────────────

@app.get("/api/v1/health/hospitals")
async def get_hospitals():
    """Get all Nepal hospitals"""
    from connectors.health_connectors import HOSPITALS
    return {"count": len(HOSPITALS), "hospitals": list(HOSPITALS.values())}

@app.post("/api/v1/health/record")
async def get_health_record(patient_id: str):
    """Get patient health record"""
    from connectors.health_connectors import get_health_record
    return get_health_record(patient_id)

# ─── Palika Endpoints ────────────────────────────────────────────────────────

@app.get("/api/v1/np/palikas")
async def nepal_palikas():
    """Get Nepal palikas (sample)"""
    from connectors.palika_connectors import PALIKAS
    return {"count": len(PALIKAS), "palikas": list(PALIKAS.values())[:50]}

# ─── Knowledge Endpoints ─────────────────────────────────────────────────────

@app.get("/api/v1/knowledge/foundations")
async def knowledge_foundations():
    """Get 9 knowledge foundations"""
    from knowledge import FOUNDATIONS
    return {"count": len(FOUNDATIONS), "foundations": list(FOUNDATIONS.values())}

# ─── Mesh Endpoints ─────────────────────────────────────────────────────────

@app.post("/api/v1/mesh/sync")
async def mesh_sync(crdt_id: str, operation: str, key: str = None, value: str = None):
    """Queue sync for offline/connectivity issues"""
    return nexus.sync_operation(crdt_id, operation, key, value)

@app.get("/api/v1/mesh/status")
async def mesh_get_status():
    """Get sync status"""
    return nexus.mesh_status()

# ─── System Endpoints ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "Digital Nepal - AsimNexus", "timestamp": datetime.now().isoformat(), "status": "operational"}

@app.get("/api/v1/status")
async def system_status():
    """Full system status"""
    return nexus.full_status()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)