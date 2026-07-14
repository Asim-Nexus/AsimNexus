#!/usr/bin/env python3
"""
AsimNexus = World OS - Unified Backend
======================================
Single entry point for all AsimNexus functionality.
Optimized with lazy loading for fast startup.
"""

import os
import sys
import asyncio
import logging
import time as _time_module
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware

# ── Structured JSON Logging ──────────────────────────────────────────────
# In production, use python-json-logger for structured log output.
# Set ASIM_LOG_FORMAT=json to enable JSON logging (default: plain text).
try:
    from pythonjsonlogger import jsonlogger
    _log_handler = logging.StreamHandler()
    if os.environ.get("ASIM_LOG_FORMAT", "").lower() == "json":
        _formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s %(module)s %(funcName)s %(lineno)d",
            datefmt="%Y-%m-%dT%H:%M:%S%z"
        )
    else:
        _formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s:%(module)s:%(lineno)d — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    _log_handler.setFormatter(_formatter)
    logging.basicConfig(level=os.environ.get("ASIM_LOG_LEVEL", "INFO").upper(), handlers=[_log_handler])
except ImportError:
    # Fallback to basic logging if python-json-logger not installed
    logging.basicConfig(
        level=os.environ.get("ASIM_LOG_LEVEL", "INFO").upper(),
        format="[%(asctime)s] %(levelname)-8s %(name)s:%(module)s:%(lineno)d — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

logger = logging.getLogger("AsimNexus")

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# ── Lazy Loader ──────────────────────────────────────────────────────────
# All heavy imports are deferred via LazyImporter / LazySingleton.
# They resolve on first attribute access, not at module level.
from core.lazy_loader import (
    # Core engines
    lazy_consensus_engine,
    lazy_clone_consensus,
    lazy_compliance,
    lazy_entity_bridge,
    lazy_security_layer,
    # LLM
    lazy_llm_gateway,
    # Clones
    lazy_world_clones,
    # Connectors
    lazy_connectors,
    lazy_hospitals,
    lazy_palikas,
    lazy_hotels,
    # Singletons
    lazy_orchestrator,
    lazy_os_executor,
    lazy_tool_registry,
    lazy_multi_mesh,
    lazy_offline_sync,
    lazy_sync_engine,
    lazy_kademlia,
    lazy_federation,
    lazy_vector_memory,
    lazy_db_manager,
    lazy_identity,
    lazy_governance,
    lazy_dharma,
    lazy_evolution,
    lazy_rag,
    lazy_mcp,
    lazy_clone_voting,
)

# Config — lightweight, import eagerly
try:
    from asim_config import get_config
    config = get_config()
except ImportError:
    config = None

# Process start time for uptime tracking
_start_time = _time_module.time()

# Module-level globals used by lifespan() via `global` declaration
llm_gateway = None
local_llm = None
redis_mgr = None
discovery_engine = None

# ── Health Checker ───────────────────────────────────────────────────────
class _HealthChecker:
    """Minimal health checker stub that returns basic system status."""
    async def get_status(self) -> dict:
        import psutil
        return {
            "status": "healthy",
            "uptime": 0,
            "cpu": psutil.cpu_percent(interval=0),
            "memory": psutil.virtual_memory()._asdict() if hasattr(psutil.virtual_memory(), '_asdict') else {},
        }
health_checker = _HealthChecker()


# ── Lazy Globals Builder ─────────────────────────────────────────────────
def _build_app_globals() -> dict:
    """Build the shared state dict for route modules.
    Called once inside lifespan, so all lazy imports resolve at startup
    rather than at module-import time.
    """
    # Resolve lazy imports
    _ConsensusEngine = lazy_consensus_engine.ConsensusEngine
    _CloneConsensusVoting = lazy_clone_consensus.CloneConsensusVoting
    _ComplianceEngine = lazy_compliance.ComplianceEngine
    _EntityBridge = lazy_entity_bridge.EntityBridge
    _ZKPProof = lazy_security_layer.ZKPProof
    _HSMService = lazy_security_layer.HSMService

    # Connectors
    _MINISTRIES = getattr(lazy_connectors, "MINISTRIES", {})
    _PROVINCES = getattr(lazy_connectors, "PROVINCES", {})
    _DISTRICTS = getattr(lazy_connectors, "DISTRICTS", {})
    _BANKS = getattr(lazy_connectors, "BANKS", {})
    _ISPS = getattr(lazy_connectors, "ISPS", {})
    _UNIVERSITIES = getattr(lazy_connectors, "UNIVERSITIES", {})
    _SCHOOLS = getattr(lazy_connectors, "SCHOOLS", {})
    _HOSPITALS = getattr(lazy_hospitals, "HOSPITALS", {})
    _PALIKAS = getattr(lazy_palikas, "PALIKAS", {})
    _HOTELS = getattr(lazy_hotels, "HOTELS", {})

    # World clones
    _WORLD_CLONE_CONFIGS = getattr(lazy_world_clones, "WORLD_CLONE_CONFIGS", [])
    _CLONES_AVAILABLE = lazy_world_clones.is_available()

    # LLM
    _LLM_AVAILABLE = lazy_llm_gateway.is_available()

    return {
        "orchestrator": lazy_orchestrator.instance,
        "llm_gateway": None,  # Set during lifespan startup
        "local_llm": None,    # Set during lifespan startup
        "redis_mgr": None,    # Set during lifespan startup
        "LLM_AVAILABLE": _LLM_AVAILABLE,
        "CLONES_AVAILABLE": _CLONES_AVAILABLE,
        "WORLD_CLONE_CONFIGS": _WORLD_CLONE_CONFIGS,
        "MINISTRIES": _MINISTRIES,
        "PROVINCES": _PROVINCES,
        "DISTRICTS": _DISTRICTS,
        "BANKS": _BANKS,
        "ISPS": _ISPS,
        "UNIVERSITIES": _UNIVERSITIES,
        "SCHOOLS": _SCHOOLS,
        "HOSPITALS": _HOSPITALS,
        "PALIKAS": _PALIKAS,
        "HOTELS": _HOTELS,
        "ConsensusEngine": _ConsensusEngine,
        "CloneConsensusVoting": lazy_clone_voting.instance,
        "ComplianceEngine": _ComplianceEngine,
        "EntityBridge": _EntityBridge,
        "ZKPProof": _ZKPProof,
        "HSMService": _HSMService,
        # OS Control
        "os_executor": lazy_os_executor.instance,
        "tool_manager": lazy_tool_registry.instance,
        # Mesh
        "mesh_manager": lazy_multi_mesh.instance,
        "sync_engine": lazy_sync_engine.instance,
        "offline_engine": lazy_offline_sync.instance,
        "discovery_engine": None,  # Set during lifespan startup
        "dht_manager": lazy_kademlia.instance,
        "federation_manager": lazy_federation.instance,
        # Memory / DB
        "memory_manager": lazy_vector_memory.instance,
        "db_manager": lazy_db_manager.instance,
        # Identity
        "identity_manager": lazy_identity.instance,
        # Governance / Dharma / Evolution
        "consensus_engine": _ConsensusEngine,
        "dharma_engine": lazy_dharma.instance,
        "evolution_engine": lazy_evolution.instance,
        "governance_engine": lazy_governance.instance,
        # Analytics / RAG
        "analytics_engine": _AnalyticsEngine(),
        "rag_engine": lazy_rag.instance,
        "health_checker": health_checker,
        # MCP
        "_mcp": lazy_mcp.instance,
    }


# ── Analytics Engine Stub ────────────────────────────────────────────────
class _AnalyticsEngine:
    """Minimal analytics engine stub that returns empty/safe defaults."""
    async def get_overview(self) -> dict:
        return {"cpu": 0, "memory": 0, "network": 0, "status": "inactive"}
    async def get_activity(self) -> dict:
        return {"activities": [], "count": 0}
    async def get_full_analytics(self, user_id: str) -> dict:
        return {"user_id": user_id, "analytics": {}}


# ── Fallback Auth Manager ────────────────────────────────────────────────
class _FallbackAuthManager:
    """Minimal auth manager that handles basic login/refresh without DB."""
    def login(self, username: str, password: str) -> dict:
        if username and password:
            return {"success": True, "token": "fallback_token", "user": {"id": username, "email": f"{username}@local"}}
        raise HTTPException(status_code=401, detail="Invalid credentials")
    def refresh_token(self, token: str) -> dict:
        return {"success": True, "token": "refreshed_fallback_token"}

auth_manager = _FallbackAuthManager()


# ── Lifespan ─────────────────────────────────────────────────────────────
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    global llm_gateway, local_llm, redis_mgr, discovery_engine

    # ── Resolve lazy imports & build globals ────────────────────────────
    _app_globals = _build_app_globals()

    # ── Initialize LLM Gateway ──────────────────────────────────────────
    llm_gateway = None
    if lazy_llm_gateway.is_available():
        try:
            llm_gateway = lazy_llm_gateway.unified_llm_gateway
            await llm_gateway.initialize()
            _app_globals["llm_gateway"] = llm_gateway
        except Exception as e:
            print(f"LLM gateway init failed: {e}")

    # ── Register Monitoring Middleware ──────────────────────────────────
    try:
        from core.monitoring_middleware import set_monitoring, PrometheusMonitoringMiddleware
        for m in app.user_middleware:
            if isinstance(m, PrometheusMonitoringMiddleware):
                await set_monitoring(m)
    except Exception as e:
        print(f"Monitoring middleware init skipped: {e}")

    # ── Initialize Redis ────────────────────────────────────────────────
    redis_mgr = None
    try:
        from core.redis_manager import AsimRedisManager
        redis_mgr = AsimRedisManager.get_instance()
        redis_mgr.redis.ping()
        _app_globals["redis_mgr"] = redis_mgr
    except Exception as e:
        print(f"Redis not available: {e}")

    # ── Initialize Local LLM ────────────────────────────────────────────
    local_llm = None
    try:
        from core.gateway.local_llm_connector import LocalLLM
        model_path = Path("models/Qwen3-4B-distill-deepseek-opus-gemini-Q8_0.gguf")
        if model_path.exists():
            local_llm = await LocalLLM.get_instance()
            _app_globals["local_llm"] = local_llm
    except Exception as e:
        print(f"Local LLM init skipped: {e}")

    # ── Auto-Discovery Engine ───────────────────────────────────────────
    discovery_engine = None
    try:
        from core.mesh.autodiscovery import get_auto_discovery
        import socket
        _hostname = socket.gethostname()
        discovery_engine = get_auto_discovery(node_id=f"asimnexus-{_hostname}")
        _app_globals["discovery_engine"] = discovery_engine
    except Exception as e:
        print(f"AutoDiscovery init skipped: {e}")

    # ── Auto-Ingest RAG Data ────────────────────────────────────────────
    try:
        from core.knowledge.rag_engine import RAGEngine
        rag = RAGEngine()
        data_dir = Path("data")
        if data_dir.exists():
            print("Starting Auto-Ingest for RAG...")
            for file_path in data_dir.glob("*.txt"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                        chunks = rag.chunk_document(text, {"source": file_path.name})
                        rag.add_documents(chunks)
                        print(f"Ingested {file_path.name} into Neutron Star")
                except Exception as e:
                    print(f"Failed to ingest {file_path.name}: {e}")
    except Exception as e:
        print(f"RAG init skipped: {e}")

    # ── Self-Awareness Auto-Scan on Startup ─────────────────────────────
    _self_awareness_task = None
    try:
        from core.self_awareness import get_scanner, get_knowledge
        scanner = get_scanner()
        knowledge = get_knowledge()
        print("[SelfAwareness] Scanning codebase on startup...")
        result = scanner.scan()
        knowledge.refresh(scanner)
        print(
            "[SelfAwareness] Scan complete: %d modules, %d packages, %d routes, %d issues"
            % (len(result.modules), len(result.packages),
               sum(len(v) for v in result.route_index.values()),
               len(result.errors))
        )
    except Exception as e:
        print(f"[SelfAwareness] Auto-scan skipped: {e}")

    # ── Start Scheduled Re-Scan Background Task ─────────────────────────
    try:
        from core.self_awareness import get_scanner, get_knowledge
        async def _self_awareness_rescan_loop():
            interval = 3600
            while True:
                try:
                    await asyncio.sleep(interval)
                    s = get_scanner()
                    k = get_knowledge()
                    print("[SelfAwareness] Scheduled re-scan starting...")
                    result = s.scan()
                    k.refresh(s)
                    print(
                        "[SelfAwareness] Re-scan complete: %d modules, %d routes"
                        % (len(result.modules), sum(len(v) for v in result.route_index.values()))
                    )
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[SelfAwareness] Re-scan error: {e}")
        _self_awareness_task = asyncio.create_task(_self_awareness_rescan_loop())
        print("[SelfAwareness] Scheduled re-scan task started (interval=3600s)")
    except Exception as e:
        print(f"[SelfAwareness] Scheduled re-scan skipped: {e}")

    # ── Wire EvolutionEngine to SelfBuilder via EvolutionBridge ─────────
    try:
        from core.evolution.evolution_engine import get_evolution_engine
        from core.self_awareness.evolution_bridge import get_bridge
        engine = get_evolution_engine()
        bridge = get_bridge()
        suggestions = engine.get_suggestions(status="approved")
        for s in suggestions:
            bridge.process_evolution_suggestion(s.to_dict())
        print("[SelfAwareness] Wired EvolutionEngine: %d approved suggestions processed" % len(suggestions))
    except Exception as e:
        print(f"[SelfAwareness] EvolutionEngine wiring skipped: {e}")

    # ── Wire MirrorModule to SelfBuilder via EvolutionBridge ────────────
    try:
        from core.mirror.mirror_module import get_mirror_module
        from core.self_awareness.evolution_bridge import get_bridge
        mirror = get_mirror_module()
        bridge = get_bridge()
        reflections = mirror.get_recent_reflections(limit=10)
        for ref in reflections:
            bridge.process_mirror_reflection(ref.to_dict() if hasattr(ref, 'to_dict') else ref)
        print("[SelfAwareness] Wired MirrorModule: %d reflections processed" % len(reflections))
    except Exception as e:
        print(f"[SelfAwareness] MirrorModule wiring skipped: {e}")

    # ── Wire DreamingEngine to SelfBuilder via EvolutionBridge ──────────
    try:
        from core.dreaming.dreaming_engine import dreaming_engine
        from core.self_awareness.evolution_bridge import get_bridge
        bridge = get_bridge()
        lessons = dreaming_engine.get_recent_lessons(limit=20)
        for lesson in lessons:
            bridge.process_dream_lesson(lesson)
        print("[SelfAwareness] Wired DreamingEngine: %d lessons processed via bridge" % len(lessons))
    except Exception as e:
        print(f"[SelfAwareness] DreamingEngine bridge wiring skipped: {e}")

    # ── Start Scheduled Mirror Reflection Processing ────────────────────
    _mirror_reflection_task = None
    try:
        from core.mirror.mirror_module import get_mirror
        from core.self_awareness.evolution_bridge import get_bridge
        async def _mirror_reflection_loop():
            interval = 1800  # Every 30 minutes
            while True:
                try:
                    await asyncio.sleep(interval)
                    mirror = get_mirror("system", user_type="ai")
                    bridge = get_bridge()
                    report = mirror.get_daily_report()
                    contradiction_rate = report.get("contradiction_rate", 0)
                    total_contradictions = report.get("total_contradictions", 0)
                    if contradiction_rate > 0.2 or total_contradictions > 3:
                        bridge.process_mirror_reflection({
                            "reflection_id": f"sched_{int(_time_module.time())}",
                            "contradiction_count": total_contradictions,
                            "contradiction_rate": contradiction_rate,
                            "source": "scheduled_mirror_check",
                            "description": f"Contradiction rate={contradiction_rate}, total={total_contradictions}",
                        })
                        print("[MirrorScheduler] Processed reflection: rate=%.2f, total=%d"
                              % (contradiction_rate, total_contradictions))
                    # Also check for unapplied high-confidence suggestions
                    for sug in mirror.evolution_suggestions:
                        if not sug.applied and getattr(sug, 'confidence', 0) > 0.7:
                            bridge.process_mirror_reflection({
                                "reflection_id": f"sug_{sug.suggestion_id}",
                                "contradiction_count": 0,
                                "contradiction_rate": 0,
                                "source": "scheduled_mirror_suggestion",
                                "description": f"High-confidence suggestion: {sug.description[:100]}",
                            })
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[MirrorScheduler] Check error: {e}")
        _mirror_reflection_task = asyncio.create_task(_mirror_reflection_loop())
        print("[MirrorScheduler] Scheduled reflection processing started (interval=1800s)")
    except Exception as e:
        print(f"[MirrorScheduler] Scheduled processing skipped: {e}")

    # ── Start Scheduled EvolutionEngine Suggestion Processing ───────────
    _evolution_suggestion_task = None
    try:
        from core.evolution.evolution_engine import get_evolution_engine
        from core.self_awareness.evolution_bridge import get_bridge
        async def _evolution_suggestion_loop():
            interval = 3600  # Every 60 minutes
            while True:
                try:
                    await asyncio.sleep(interval)
                    engine = get_evolution_engine()
                    bridge = get_bridge()
                    # Process newly approved suggestions
                    approved = engine.get_suggestions(status="approved")
                    for s in approved:
                        bridge.process_evolution_suggestion(s.to_dict())
                    # Process high-confidence pending suggestions for auto-approval
                    pending = engine.get_suggestions(status="pending")
                    for s in pending:
                        if getattr(s, 'confidence', 0) > 0.85:
                            engine.approve_suggestion(s.suggestion_id)
                            bridge.process_evolution_suggestion(s.to_dict())
                            print("[EvolutionScheduler] Auto-approved suggestion: %s (conf=%.2f)"
                                  % (s.suggestion_id[:8], s.confidence))
                    if approved or pending:
                        print("[EvolutionScheduler] Processed %d approved + %d pending suggestions"
                              % (len(approved), len(pending)))
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[EvolutionScheduler] Check error: {e}")
        _evolution_suggestion_task = asyncio.create_task(_evolution_suggestion_loop())
        print("[EvolutionScheduler] Scheduled suggestion processing started (interval=3600s)")
    except Exception as e:
        print(f"[EvolutionScheduler] Scheduled processing skipped: {e}")

    # ── Initialize Soul Key Security Protocol ───────────────────────────
    try:
        from core.security.soul_key import get_soul_key_protocol
        protocol = get_soul_key_protocol()
        stats = protocol.get_stats()
        print("[SoulKey] Protocol initialized: %d keys, %d events, %d lockouts"
              % (stats.get("total_soul_keys", 0), stats.get("total_events", 0),
                 stats.get("total_lockouts", 0)))
    except Exception as e:
        print(f"[SoulKey] Initialization skipped: {e}")

    # ── Initialize AutoBuilder & Run Initial Gap Analysis ───────────────
    _auto_build_task = None
    try:
        from core.self_awareness import get_auto_builder, get_scanner, get_knowledge
        auto_builder = get_auto_builder()
        scanner = get_scanner()
        knowledge = get_knowledge()
        print("[AutoBuilder] Running initial gap analysis...")
        async def _initial_auto_build():
            try:
                cycle = await auto_builder.run_cycle()
                print(
                    "[AutoBuilder] Initial cycle complete: status=%s, gaps=%d, actions=%d, "
                    "tests_passed=%d/%d, duration=%.1fs"
                    % (
                        cycle.status,
                        cycle.gaps_found,
                        cycle.actions_succeeded,
                        cycle.tests_passed_before,
                        cycle.tests_before,
                        cycle.duration_seconds,
                    )
                )
            except Exception as e:
                print(f"[AutoBuilder] Initial cycle error: {e}")
        asyncio.create_task(_initial_auto_build())
        print("[AutoBuilder] Initial gap analysis triggered")
    except Exception as e:
        print(f"[AutoBuilder] Initialization skipped: {e}")

    # ── Start Scheduled Auto-Build Background Task ──────────────────────
    try:
        from core.self_awareness import get_auto_builder
        async def _auto_build_loop():
            interval = 7200
            while True:
                try:
                    await asyncio.sleep(interval)
                    ab = get_auto_builder()
                    print("[AutoBuilder] Scheduled build cycle starting...")
                    cycle = await ab.run_cycle()
                    print(
                        "[AutoBuilder] Cycle complete: status=%s, gaps=%d, actions=%d, "
                        "tests_passed=%d/%d, duration=%.1fs"
                        % (
                            cycle.status,
                            cycle.gaps_found,
                            cycle.actions_succeeded,
                            cycle.tests_passed_before,
                            cycle.tests_before,
                            cycle.duration_seconds,
                        )
                    )
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[AutoBuilder] Cycle error: {e}")
        _auto_build_task = asyncio.create_task(_auto_build_loop())
        print("[AutoBuilder] Scheduled build task started (interval=7200s)")
    except Exception as e:
        print(f"[AutoBuilder] Scheduled build skipped: {e}")

    # ── Start Dreaming Engine Background Task ───────────────────────────
    _dreaming_task = None
    try:
        from core.dreaming.dreaming_engine import dreaming_engine
        _dreaming_task = asyncio.create_task(dreaming_engine.start())
        print("[Dreaming] Engine background task started (cycle=%ds)" % dreaming_engine.cycle_interval)
    except Exception as e:
        print(f"[Dreaming] Engine start skipped: {e}")

    # ── Initialize Mesh Node ────────────────────────────────────────────
    _mesh_node_initialized = False
    try:
        from core.mesh import get_mesh_coordinator, NodeType
        mesh = get_mesh_coordinator()
        await mesh.initialize_local_node(
            node_type=NodeType.PERSONAL,
            name="AsimNexus",
            country="NP"
        )
        _mesh_node_initialized = True
        print(f"[Mesh] Local node initialized: {mesh.local_node.node_id}")
    except Exception as e:
        print(f"[Mesh] Node init skipped: {e}")

    # ── Inject dreaming engine into globals ─────────────────────────────
    try:
        from core.dreaming.dreaming_engine import dreaming_engine
        _app_globals["dreaming_engine"] = dreaming_engine
    except Exception:
        _app_globals["dreaming_engine"] = None

    # ── Route re-registration with full globals ──────────────────────────
    # Routes are already registered at module level; this updates the
    # module-level globals (orchestrator, LLM_AVAILABLE, etc.) with the
    # real initialized values from lifespan.
    _lazy_register_routes(app, _app_globals)

    yield  # Application runs here

    # ── SHUTDOWN ────────────────────────────────────────────────────────
    if llm_gateway:
        await llm_gateway.close()

    # Stop Self-Awareness background task
    if _self_awareness_task is not None:
        try:
            _self_awareness_task.cancel()
            print("[SelfAwareness] Re-scan task stopped")
        except Exception as e:
            print(f"[SelfAwareness] Stop error: {e}")

    # Stop Auto-Build background task
    if _auto_build_task is not None:
        try:
            _auto_build_task.cancel()
            print("[AutoBuilder] Build task stopped")
        except Exception as e:
            print(f"[AutoBuilder] Stop error: {e}")

    # Stop Dreaming Engine background task
    if _dreaming_task is not None:
        try:
            from core.dreaming.dreaming_engine import dreaming_engine
            dreaming_engine.stop()
            _dreaming_task.cancel()
            print("[Dreaming] Engine stopped")
        except Exception as e:
            print(f"[Dreaming] Engine stop: {e}")

    # Stop Mirror Reflection background task
    if _mirror_reflection_task is not None:
        try:
            _mirror_reflection_task.cancel()
            print("[MirrorScheduler] Reflection task stopped")
        except Exception as e:
            print(f"[MirrorScheduler] Stop error: {e}")

    # Stop Evolution Suggestion background task
    if _evolution_suggestion_task is not None:
        try:
            _evolution_suggestion_task.cancel()
            print("[EvolutionScheduler] Suggestion task stopped")
        except Exception as e:
            print(f"[EvolutionScheduler] Stop error: {e}")


# ── Lazy Route Registration ──────────────────────────────────────────────
def _lazy_register_routes(app: FastAPI, _app_globals: dict):
    """Import and register all route modules lazily inside lifespan."""
    # WebSocket routes
    try:
        from core.api.ws_routes import router as ws_router
        app.include_router(ws_router)
    except Exception as e:
        print(f"WebSocket routes skipped: {e}")

    # Core API endpoint modules
    try:
        from core.api_endpoints.register_routes import register_all_routes
        register_all_routes(app)
        logger.info('Core API endpoint modules registered (economy, governance, sectors, real-time, kernel, global-agent, hardening)')
    except Exception as e:
        logger.warning('Core API endpoint registration skipped: %s', e)

    # Route modules
    try:
        from routes.nepal import init_nepal_data
        from routes.chat import init_chat
        from routes.auth import init_auth
        from routes.marketplace import init_marketplace
        from routes.mesh import init_mesh
        from routes.os_control import init_os_control
        from routes.identity import init_identity
        from routes.consensus import init_consensus
        from routes.analytics import init_analytics
        from routes.memory import init_memory
        from routes.mcp import init_mcp
        from routes.healing import init_healing
        from routes.universal import init_universal
        from routes.sovereignty import init_sovereignty
        from routes.infrastructure import init_infrastructure
        from routes.finance import init_finance
        from routes.government import init_government
        from routes.governance import init_governance
        from routes.enterprise import init_enterprise
        from routes.security import init_security
        from routes.rbe import init_rbe
        from routes.depin import init_depin
        from routes.blockchain_identity import init_blockchain_identity
        from routes.jobs import init_jobs
        from routes.pwa import init_pwa
        from routes.release import init_release
        from routes.self_awareness import init_self_awareness
        from routes.stakeholder import init_stakeholder
        from routes.arvr import init_arvr
        from routes.soul_key import init_soul_key
        from routes.universe import init_universe
        from routes.mirror import init_mirror
        from routes.dreaming import init_dreaming
        from routes.evolution import init_evolution
        from routes.dharma import init_dharma
        from routes.founder_clones import init_founder_clones
        from routes.learning import init_learning
        from routes.observability import init_observability
        from routes.registry import init_registry
        from routes.deploy import init_deploy
        from routes.push import init_push
        from routes.bugs import init_bugs
        from routes.clones import init_clones
        from routes.offline import init_offline
        from routes.override import init_override
        from routes.router import init_router
        from routes.health import init_health

        init_nepal_data(_app_globals)
        init_chat(_app_globals)
        init_auth(_app_globals)
        init_marketplace(_app_globals)
        init_mesh(_app_globals)
        init_os_control(_app_globals)
        init_identity(_app_globals)
        init_consensus(_app_globals)
        init_analytics(_app_globals)
        init_memory(_app_globals)
        init_mcp(_app_globals)
        init_healing(_app_globals)
        init_universal(_app_globals)
        init_sovereignty(_app_globals)
        init_infrastructure(_app_globals)
        init_finance(_app_globals)
        init_government(_app_globals)
        init_governance(_app_globals)
        init_enterprise(_app_globals)
        init_security(_app_globals)
        init_rbe(_app_globals)
        init_depin(_app_globals)
        init_blockchain_identity(_app_globals)
        init_jobs(_app_globals)
        init_pwa(_app_globals)
        init_release(_app_globals)
        init_self_awareness(_app_globals)
        init_stakeholder(_app_globals)
        init_arvr(_app_globals)
        init_soul_key(_app_globals)
        init_universe(_app_globals)
        init_mirror(_app_globals)
        init_dreaming(_app_globals)
        init_evolution(_app_globals)
        init_dharma(_app_globals)
        init_founder_clones(_app_globals)
        init_learning(_app_globals)
        init_observability(_app_globals)
        init_registry(_app_globals)
        init_deploy(_app_globals)
        init_push(_app_globals)
        init_bugs(_app_globals)
        init_clones(_app_globals)
        init_offline(_app_globals)
        init_override(_app_globals)
        init_router(_app_globals)
        init_health(_app_globals)

        # Register all route routers with the app
        from routes import register_routes
        register_routes(app)

        logger.info(f"All route modules initialized and registered ({len(app.routes)} total routes)")
    except Exception as e:
        logger.error(f"Route registration failed: {e}", exc_info=True)


# ── FastAPI App Creation ─────────────────────────────────────────────────
app = FastAPI(
    title="AsimNexus World OS",
    version="1.0.0",
    description="Nepal National Digital Operating System - Citizen/Company/Government API",
    lifespan=lifespan
)

# ── Middleware Registration ──────────────────────────────────────────────
# These are lightweight wrappers; the actual heavy imports happen inside them.

# Tightened CORS — allow known origins only; use env var for production
_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,https://asimnexus.app"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID", "X-Correlation-ID"],
    expose_headers=["X-Request-ID", "X-Correlation-ID"],
    max_age=600,
)

# Auth, Monitoring & Security Middlewares
# These are imported here but their heavy dependencies load lazily inside.
from core.security.auth_middleware import AuthMiddleware
from core.monitoring_middleware import PrometheusMonitoringMiddleware
from core.security_headers_middleware import SecurityHeadersMiddleware
app.add_middleware(AuthMiddleware)
app.add_middleware(PrometheusMonitoringMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# ── Route Registration (module-level, so routes are available immediately) ─
# Route init functions receive empty globals; they handle None gracefully.
_lazy_register_routes(app, {})

# ── Root Endpoints ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "AsimNexus World OS", "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/system/info")
async def system_info():
    return {"os": "Windows", "python": "3.11", "llm": "Qwen3-4B"}


# ── Health Probe Routes ──────────────────────────────────────────────────

@app.get("/health/live")
async def health_live():
    """Kubernetes liveness probe."""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@app.get("/health/ready")
async def health_ready():
    """Kubernetes readiness probe."""
    checks = {
        "database": False,
        "redis": False,
        "self_awareness": False,
    }
    try:
        from core.self_awareness import get_knowledge
        knowledge = get_knowledge()
        summary = knowledge.get_summary()
        checks["self_awareness"] = True
    except Exception:
        pass
    all_ready = all(checks.values())
    return {
        "status": "ready" if all_ready else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health/status")
async def health_status():
    """Full health status of the system with detailed component checks."""
    import time as _time
    start = _time.time()
    checks = {}
    # Database check
    try:
        from database import get_db
        db = get_db()
        checks["database"] = {"status": "ok", "latency_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}
    # Self-awareness check
    try:
        from core.self_awareness import get_knowledge, get_scanner
        knowledge = get_knowledge()
        summary = knowledge.get_summary()
        checks["self_awareness"] = {
            "status": "ok",
            "modules": summary.total_modules,
            "routes": summary.total_routes,
            "issues": summary.total_issues,
            "last_scan": summary.last_scan,
        }
    except Exception as e:
        checks["self_awareness"] = {"status": "error", "error": str(e)}
    # Mesh check
    try:
        from core.mesh import get_mesh_coordinator
        coordinator = get_mesh_coordinator()
        stats = coordinator.get_mesh_stats() if coordinator else {}
        checks["mesh"] = {"status": "ok", "peers": stats.get("total_nodes", 0)}
    except Exception as e:
        checks["mesh"] = {"status": "error", "error": str(e)}
    # Evolution engine check
    try:
        from core.evolution.evolution_engine import get_evolution_engine
        engine = get_evolution_engine()
        stats = engine.get_stats()
        checks["evolution"] = {"status": "ok", "suggestions": stats.get("total_suggestions", 0)}
    except Exception as e:
        checks["evolution"] = {"status": "error", "error": str(e)}
    # Dreaming engine check
    try:
        from core.dreaming.dreaming_engine import dreaming_engine
        status = dreaming_engine.status()
        checks["dreaming"] = {"status": "ok", "running": status.get("running", False)}
    except Exception as e:
        checks["dreaming"] = {"status": "error", "error": str(e)}
    elapsed_ms = round((_time.time() - start) * 1000, 2)
    all_ok = all(c.get("status") == "ok" for c in checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "version": "2.0.0-RC2",
        "uptime_seconds": _time.time() - _start_time,
        "checks": checks,
        "latency_ms": elapsed_ms,
        "timestamp": datetime.now().isoformat(),
    }


# ── Mesh & Socket.IO Routes ──────────────────────────────────────────────

@app.get("/mesh/nodes")
async def mesh_nodes_public():
    """Public mesh nodes listing."""
    try:
        from core.mesh import get_mesh_coordinator
        coordinator = get_mesh_coordinator()
        nodes = coordinator.get_active_nodes() if coordinator else []
        return {"nodes": nodes, "count": len(nodes)}
    except Exception:
        return {"nodes": [], "count": 0}


@app.get("/socket.io/")
async def socket_io():
    """Socket.IO endpoint placeholder."""
    return {"status": "socket.io available", "protocol": "websocket"}


# ── Prometheus Metrics Endpoint ──────────────────────────────────────────

@app.get("/metrics")
async def metrics(request: Request):
    """Prometheus-compatible metrics endpoint in text format."""
    from core.prometheus_metrics import generate_metrics
    from fastapi.responses import PlainTextResponse, JSONResponse
    accept = request.headers.get("accept", "")
    if "text/plain" in accept or "application/openmetrics-text" in accept:
        return PlainTextResponse(generate_metrics(), media_type="text/plain; charset=utf-8")
    # Fallback: JSON format for backward compatibility
    from core.prometheus_metrics import get_metrics_dict
    return JSONResponse(get_metrics_dict())


# _process_brain_message is defined in routes/chat.py (canonical version)
# All endpoints use the routes/chat.py version via the chat router.
# _smart_response is defined in routes/chat.py (canonical version)
# All route handlers have been moved to routes/ modules.
# See routes/__init__.py for registration and individual modules for implementations.
# Memory system uses core/vectormemory.py VectorMemory (via app_globals["memory_manager"])
