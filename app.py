#!/usr/bin/env python3
"""
AsimNexus = World OS - Unified Backend
======================================
Single entry point for all AsimNexus functionality.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Core module imports with fallbacks
try:
    from core.consensus_engine import ConsensusEngine
except ImportError:
    class ConsensusEngine:
        def get_stats(self): return {"total_rounds": 0}
        def start_round(self, **kwargs): return None

try:
    from core.compliance_engine import ComplianceEngine
except ImportError:
    class ComplianceEngine:
        def check_decision(self, sector, is_public_decision=False): 
            class R: verdict = type('V', (), {'value': 'allow'})()
            return R()
        def get_stats(self): return {"total_sectors": 8}

try:
    from core.security_layer import SecurityLayer
except ImportError:
    class SecurityLayer:
        def get_stats(self): return {"total_checked": 0}

# Import connectors
try:
    from connectors.nepal_connectors import (
        MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS,
        UNIVERSITIES, SCHOOLS, get_entity, get_registry
    )
except ImportError:
    MINISTRIES = PROVINCES = DISTRICTS = BANKS = ISPS = UNIVERSITIES = SCHOOLS = {}
    def get_entity(t, c): return None
    def get_registry(t): return {"count": 0, "items": []}

# Import health connectors
try:
    from connectors.health_connectors import HOSPITALS, get_health_record
except ImportError:
    HOSPITALS = {}
    def get_health_record(p): return {}

# Import palika connectors
try:
    from connectors.palika_connectors import PALIKAS, get_palika
except ImportError:
    PALIKAS = {}
    def get_palika(c): return None

# Import tourism connectors
try:
    from connectors.tourism_connectors import HOTELS, TOURISM_SERVICES, get_hotel
except ImportError:
    HOTELS = TOURISM_SERVICES = {}
    def get_hotel(c): return None

# Create FastAPI app
app = FastAPI(
    title="AsimNexus World OS",
    version="1.0.0",
    description="Nepal National Digital Operating System - Citizen/Company/Government API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# Initialize engines
consensus = ConsensusEngine()
compliance = ComplianceEngine()
security = SecurityLayer()

# ─── Root Endpoints ────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "AsimNexus World OS", "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/system/info")
async def system_info():
    return {"os": "Windows", "python": "3.11", "llm": "Qwen3-4B"}

# ─── Nepal Connectors Endpoints ────────────────────────────────────────────

@app.get("/api/v1/np/ministries")
async def ministries():
    return {"count": len(MINISTRIES), "ministries": list(MINISTRIES.values())}

@app.get("/api/v1/np/provinces")
async def provinces():
    return {"count": len(PROVINCES), "provinces": list(PROVINCES.values())}

@app.get("/api/v1/np/districts")
async def districts():
    return {"count": len(DISTRICTS), "districts": list(DISTRICTS.values())}

@app.get("/api/v1/np/banks")
async def banks():
    return {"count": len(BANKS), "banks": list(BANKS.values())}

@app.get("/api/v1/np/isps")
async def isps():
    return {"count": len(ISPS), "isps": list(ISPS.values())}

@app.get("/api/v1/education/universities")
async def universities():
    return {"count": len(UNIVERSITIES), "universities": list(UNIVERSITIES.values())}

@app.get("/api/v1/education/schools")
async def schools():
    return {"count": len(SCHOOLS), "schools": list(SCHOOLS.values())}

@app.get("/api/v1/health/hospitals")
async def hospitals():
    return {"count": len(HOSPITALS), "hospitals": list(HOSPITALS.values())}

@app.get("/api/v1/np/palikas")
async def palikas():
    return {"count": len(PALIKAS), "palikas": list(PALIKAS.values())[:50]}

@app.get("/api/v1/tourism/hotels")
async def hotels():
    return {"count": len(HOTELS), "hotels": list(HOTELS.values())}

# ─── Chat Endpoints ──────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(message: str, user_id: str = "web_user"):
    return {"success": True, "response": f"Processed: {message}"}

# ─── Tools Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/tools")
async def list_tools():
    try:
        from os_control.tool_registry import tool_registry
        tools = [{"name": r.tool_id, "description": r.description} 
                 for r in tool_registry.list_tools()]
        return {"success": True, "tools": tools, "count": len(tools)}
    except ImportError:
        return {"success": True, "tools": [], "count": 0}

@app.get("/api/os/tools")
async def os_tools():
    return await list_tools()

# ─── Mesh Endpoints ──────────────────────────────────────────────────────────

@app.get("/api/mesh/status")
async def mesh_status():
    return {"is_online": True, "total_operations": 0}

# ─── Main Entry ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)