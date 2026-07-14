"""
Lazy Import Loader for AsimNexus
=================================
Defers heavy imports until first use, dramatically reducing startup time.
All module-level try/except imports in app.py are replaced with LazyImporter
instances that resolve on first attribute access.
"""

import importlib
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("AsimNexus.LazyLoader")


class LazyImporter:
    """Defers module import until first attribute access.

    Usage::

        lazy_consensus = LazyImporter("core.consensus_engine", "ConsensusEngine")
        # No import happens yet
        engine = lazy_consensus.ConsensusEngine()  # Import happens here
    """

    def __init__(self, module_name: str, *names: str,
                 fallback: Any = None,
                 fallback_factory: Optional[callable] = None):
        """
        Args:
            module_name: Fully-qualified module name to import.
            *names: Attribute names to expose from the module.
            fallback: Static fallback value if import fails.
            fallback_factory: Callable that returns a fallback instance.
        """
        self._module_name = module_name
        self._names = names
        self._fallback = fallback
        self._fallback_factory = fallback_factory
        self._module: Any = None
        self._import_error: Optional[Exception] = None
        self._resolved: Dict[str, Any] = {}

    def _ensure_imported(self) -> None:
        if self._module is not None:
            return
        try:
            self._module = importlib.import_module(self._module_name)
            for name in self._names:
                try:
                    self._resolved[name] = getattr(self._module, name)
                except AttributeError:
                    logger.debug("LazyImporter: %s has no attribute %s",
                                 self._module_name, name)
        except ImportError as e:
            self._import_error = e
            logger.debug("LazyImporter: %s not available (%s)",
                         self._module_name, e)
            if self._fallback_factory is not None:
                self._resolved["__fallback__"] = self._fallback_factory()
            elif self._fallback is not None:
                self._resolved["__fallback__"] = self._fallback

    def __getattr__(self, name: str) -> Any:
        self._ensure_imported()
        if name in self._resolved:
            return self._resolved[name]
        if self._module is not None:
            return getattr(self._module, name)
        if "__fallback__" in self._resolved:
            return self._resolved["__fallback__"]
        raise AttributeError(
            f"LazyImporter({self._module_name}): '{name}' not available"
        )

    def is_available(self) -> bool:
        """Check if the module was successfully imported."""
        self._ensure_imported()
        return self._module is not None

    def get_module(self) -> Any:
        """Return the imported module or None."""
        self._ensure_imported()
        return self._module

    def get_error(self) -> Optional[Exception]:
        """Return the import error if any."""
        self._ensure_imported()
        return self._import_error


class LazySingleton:
    """Defers creation of a singleton instance until first access.

    Usage::

        engine = LazySingleton("core.consensus_engine", "ConsensusEngine")
        # No import or instantiation yet
        stats = engine.instance.get_stats()  # Import + instantiation here
    """

    def __init__(self, module_name: str, class_name: str,
                 args: Tuple = None, kwargs: Dict[str, Any] = None,
                 fallback: Any = None,
                 fallback_factory: Optional[callable] = None):
        self._importer = LazyImporter(
            module_name, class_name,
            fallback=fallback,
            fallback_factory=fallback_factory,
        )
        self._class_name = class_name
        self._args = args or ()
        self._kwargs = kwargs or {}
        self._instance: Any = None
        self._init_error: Optional[Exception] = None

    @property
    def instance(self) -> Any:
        if self._instance is not None:
            return self._instance
        cls = getattr(self._importer, self._class_name, None)
        if cls is None:
            return self._importer.__fallback__ if hasattr(self._importer, "__fallback__") else None
        try:
            self._instance = cls(*self._args, **self._kwargs)
        except Exception as e:
            self._init_error = e
            logger.debug("LazySingleton: %s() failed (%s)", self._class_name, e)
            return None
        return self._instance

    def is_available(self) -> bool:
        return self.instance is not None

    def get_error(self) -> Optional[Exception]:
        return self._init_error or self._importer.get_error()


# ── Pre-built lazy references for AsimNexus ──────────────────────────────

# Core engines
lazy_consensus_engine = LazyImporter(
    "core.consensus_engine", "ConsensusEngine",
    fallback_factory=lambda: type("_ConsensusEngineStub", (), {
        "get_stats": lambda self: {"total_rounds": 0},
        "start_round": lambda self, **kw: None,
    })(),
)

lazy_clone_consensus = LazyImporter(
    "core.consensus.clone_consensus_voting", "CloneConsensusVoting",
    fallback_factory=lambda: type("_CloneConsensusStub", (), {
        "start_round": lambda self, **kw: {"status": "error", "message": "unavailable"},
        "vote": lambda self, **kw: {"status": "error", "message": "unavailable"},
        "get_stats": lambda self: {"status": "unavailable"},
    })(),
)

lazy_compliance = LazyImporter(
    "core.compliance_engine", "ComplianceEngine",
    fallback_factory=lambda: type("_ComplianceStub", (), {
        "check_decision": lambda self, sector, is_public_decision=False: (
            type("R", (), {"verdict": type("V", (), {"value": "allow"})()})()
        ),
        "get_stats": lambda self: {"total_sectors": 8},
    })(),
)

lazy_entity_bridge = LazyImporter(
    "core.entity_bridge", "EntityBridge",
    fallback=None,
)

lazy_security_layer = LazyImporter(
    "core.security_layer", "ZKPProof", "HSMService",
    fallback=None,
)

# LLM Gateway
lazy_llm_gateway = LazyImporter(
    "connectors.unified_llm_gateway",
    "unified_llm_gateway", "LLMProvider", "UnifiedCompletionRequest",
)

# World Clones
lazy_world_clones = LazyImporter(
    "core.founder_clones.world_clones", "WORLD_CLONE_CONFIGS", "CloneRole",
)

# Connectors
lazy_connectors = LazyImporter(
    "connectors.nepal.government",
    "MINISTRIES", "PROVINCES", "DISTRICTS", "BANKS", "ISPS",
    "UNIVERSITIES", "SCHOOLS",
)

lazy_hospitals = LazyImporter("connectors.health.hospitals", "HOSPITALS")
lazy_palikas = LazyImporter("connectors.local.palikas", "PALIKAS")
lazy_hotels = LazyImporter("connectors.tourism.hotels", "HOTELS")

# Orchestrator
lazy_orchestrator = LazySingleton(
    "core.orchestrator.orchestrator", "Orchestrator",
)

# OS Control
lazy_os_executor = LazySingleton(
    "core.orchestrator.os_tool_executor", "OsToolExecutor",
)

lazy_tool_registry = LazySingleton(
    "core.orchestrator.tool_registry", "ToolRegistry",
)

# Mesh
lazy_multi_mesh = LazySingleton(
    "mesh.multi_mesh_router", "MultiMeshRouter",
)

lazy_offline_sync = LazySingleton(
    "mesh.offline_sync_engine", "OfflineSyncEngine",
)

lazy_sync_engine = LazySingleton(
    "core.sync.offline_sync", "SyncEngine",
)

lazy_kademlia = LazySingleton(
    "mesh.kademlia_dht", "KademliaDHT",
)

lazy_federation = LazySingleton(
    "core.federation.federation_manager", "FederationManager",
)

# Memory / DB
lazy_vector_memory = LazySingleton(
    "core.vectormemory", "VectorMemory",
    kwargs={"db_path": "data/vector_memory.db"},
)

lazy_db_manager = LazySingleton(
    "database.db_manager", "DBManager",
)

# Identity
lazy_identity = LazySingleton(
    "core.security.identity_manager", "IdentityManager",
)

# Governance / Dharma / Evolution
lazy_governance = LazySingleton(
    "core.governance.consensus", "GovernanceEngine",
)

lazy_dharma = LazySingleton(
    "core.dharma_chakra.veto_engine", "DharmaVetoEngine",
)

lazy_evolution = LazySingleton(
    "core.evolution.evolution_engine", "EvolutionEngine",
)

# RAG
lazy_rag = LazySingleton(
    "knowledge.rag_engine", "RAGEngine",
)

# MCP
lazy_mcp = LazySingleton(
    "core.mcp.mcp_manager", "MCPManager",
)

# Clone Consensus Voting instance
lazy_clone_voting = LazySingleton(
    "core.consensus.clone_consensus_voting", "CloneConsensusVoting",
)
