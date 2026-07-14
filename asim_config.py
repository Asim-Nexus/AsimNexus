"""
ASIMNEXUS Unified Configuration
================================
Single source of truth for all ASIM settings.
All environment variables used across the codebase are documented here.

Usage:
    from asim_config import get_config, AsimConfig
    cfg = get_config()
    print(cfg.log_level)
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def _bool(val: str, default: str = "false") -> bool:
    return os.getenv(val, default).lower() in ("1", "true", "yes")


def _int(val: str, default: str) -> int:
    return int(os.getenv(val, default))


def _float(val: str, default: str) -> float:
    return float(os.getenv(val, default))


def _str(val: str, default: str = "") -> str:
    return os.getenv(val, default)


def _json(val: str, default: str = "{}") -> Any:
    return json.loads(os.getenv(val, default))


def _list(val: str, default: str = "") -> List[str]:
    raw = os.getenv(val, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


@dataclass
class AsimConfig:
    """Unified ASIMNEXUS configuration — all env vars documented here."""

    # ═══════════════════════════════════════════════════════════════
    # Core Server
    # ═══════════════════════════════════════════════════════════════
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    data_dir: str = "data"
    db_path: str = "data/asim_core.db"
    release_channel: str = "stable"
    test_mode: bool = False

    # ═══════════════════════════════════════════════════════════════
    # CORS & Security
    # ═══════════════════════════════════════════════════════════════
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000", "http://localhost:8000"
    ])
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    use_hsm: bool = False
    pkcs11_lib_path: str = ""
    jwt_hsm_pin: str = "1234"
    jwt_hsm_key_label: str = "jwt-key"
    jwt_public_key_pem_file: str = "public_key.pem"
    security_mode: str = "strict"  # strict | relaxed | debug
    require_mtls: bool = True
    require_oauth2: bool = True

    # ═══════════════════════════════════════════════════════════════
    # LLM Providers
    # ═══════════════════════════════════════════════════════════════
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"
    grok_api_key: Optional[str] = None
    grok_model: str = "grok-beta"
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    nvidia_api_key: Optional[str] = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_nim_model: str = "meta/llama-3.1-8b-instruct"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma2:2b"
    llm_engine_url: str = "http://localhost:8000"

    # ═══════════════════════════════════════════════════════════════
    # Local Model
    # ═══════════════════════════════════════════════════════════════
    local_model_enabled: bool = True
    local_model_path: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════
    # Nepal-First Locale
    # ═══════════════════════════════════════════════════════════════
    default_locale: str = "ne-NP"
    default_language: str = "ne"
    default_currency: str = "NPR"

    # ═══════════════════════════════════════════════════════════════
    # Cloud / WAMP
    # ═══════════════════════════════════════════════════════════════
    cloud_enabled: bool = True
    cloud_url: str = "https://api.asim-nexus.ai"
    cloud_api_key: Optional[str] = None
    wamp_enabled: bool = False
    wamp_url: str = "ws://localhost:8080/ws"
    wamp_realm: str = "asim_nexus"

    # ═══════════════════════════════════════════════════════════════
    # Storage / Memory
    # ═══════════════════════════════════════════════════════════════
    memory_path: str = "memory"
    clone_storage_path: str = "memory/clones"
    vector_db_path: str = "data/vector_memory.db"
    embedding_backend: str = "chromadb"
    chroma_path: str = "data/chromadb"
    chroma_collection: str = "asimnexus_memories"
    vector_prune_days: int = 90
    vector_keep_per_type: int = 100
    embedding_cache_size: int = 10000

    # ═══════════════════════════════════════════════════════════════
    # Redis
    # ═══════════════════════════════════════════════════════════════
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # ═══════════════════════════════════════════════════════════════
    # Rate Limiting
    # ═══════════════════════════════════════════════════════════════
    rate_limit_default: int = 100
    rate_limit_window: int = 60

    # ═══════════════════════════════════════════════════════════════
    # Self-Awareness
    # ═══════════════════════════════════════════════════════════════
    knowledge_dir: str = "data/self_knowledge"
    auto_scan: bool = False
    scan_interval_seconds: int = 3600
    auto_build_interval_seconds: int = 7200

    # ═══════════════════════════════════════════════════════════════
    # Mesh Network
    # ═══════════════════════════════════════════════════════════════
    node_id: str = ""
    mesh_heartbeat_interval: float = 30.0
    mesh_node_discovery_interval: float = 60.0
    mesh_node_startup_timeout: float = 30.0
    mesh_auto_recover: bool = True
    mesh_enable_relay: bool = True
    mesh_enable_rendezvous: bool = True
    mesh_enable_multihop: bool = True
    mesh_default: str = "local"
    mesh_db_path: str = "data/mesh_routing.jsonl"
    mesh_health_timeout: int = 10
    mesh_auto_switch_interval: int = 30
    mesh_dht_k: int = 20
    mesh_dht_alpha: int = 3
    mesh_dht_port: int = 7332
    mesh_dht_refresh_interval: float = 3600.0
    mesh_dht_ttl: float = 86400.0
    mesh_bootstrap_port: int = 7335
    mesh_bootstrap_max_nodes: int = 50
    mesh_bootstrap_node_timeout: int = 3600
    mesh_bootstrap_cache_ttl: int = 300
    mesh_bootstrap_seeds: str = ""
    mesh_relay_port: int = 7334
    mesh_relay_session_timeout: int = 300
    mesh_relay_max_sessions: int = 100
    mesh_rendezvous_port: int = 7336
    mesh_hole_punch_retries: int = 3
    mesh_hole_punch_timeout: int = 10
    mesh_punch_interval: float = 0.1
    mesh_punch_keepalive: float = 15.0
    mesh_stun_servers: str = ""
    mesh_turn_servers: str = ""
    mesh_turn_username: str = ""
    mesh_turn_password: str = ""
    mesh_turn_server: str = "turn:localhost:3478"
    mesh_stun_timeout: int = 5
    mesh_stun_retries: int = 2
    mesh_max_hops: int = 5
    mesh_path_discovery_timeout: float = 10.0
    mesh_path_discovery_ttl: int = 5
    mesh_path_refresh_interval: float = 120.0
    mesh_store_forward_expiry: float = 3600.0
    mesh_multihop_retry: float = 30.0
    mesh_max_path_age: float = 300.0
    mesh_max_stored_msgs: int = 1000
    mesh_crdt_op_max_age: float = 86400.0
    mesh_discovery_port: int = 7331
    mesh_discovery_interval: int = 30
    mesh_discovery_timeout: int = 5
    mesh_beacon_interval: int = 60
    mesh_stale_node_age: int = 300
    mesh_node_registry_db: str = "data/node_registry.db"
    single_machine_peers: str = ""
    p2p_peer_discovery_interval: int = 60
    p2p_health_ping_interval: int = 30
    p2p_max_peers_per_mesh: int = 50

    # ═══════════════════════════════════════════════════════════════
    # Sync / Offline
    # ═══════════════════════════════════════════════════════════════
    sync_db_path: str = "data/offline_sync.jsonl"
    sync_interval: int = 15
    sync_batch_size: int = 50
    sync_max_retries: int = 5
    sync_retry_backoff: int = 30

    # ═══════════════════════════════════════════════════════════════
    # Load Shedding
    # ═══════════════════════════════════════════════════════════════
    load_shed_capacity: int = 100
    load_shed_refill_rate: float = 10.0
    load_shed_max_latency_ms: float = 500.0
    load_shed_min_bandwidth_kbps: float = 100.0

    # ═══════════════════════════════════════════════════════════════
    # Circuit Breaker
    # ═══════════════════════════════════════════════════════════════
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 30
    circuit_breaker_half_open_max_requests: int = 3

    # ═══════════════════════════════════════════════════════════════
    # Device Registry
    # ═══════════════════════════════════════════════════════════════
    scan_interval: int = 30
    health_interval: int = 15
    stale_timeout: int = 300
    discovery_port: int = 7331
    max_backup_paths: int = 3

    # ═══════════════════════════════════════════════════════════════
    # Governance
    # ═══════════════════════════════════════════════════════════════
    gov_audit_db_path: str = "data/governance_audit.jsonl"
    gov_audit_max: int = 100000
    gov_db_path: str = "data/national_gov_layer.jsonl"
    gov_emergency_threshold: int = 3
    gov_quorum_percent: int = 51
    gov_voting_period_hours: int = 72
    gov_min_voting_weight: float = 1.0
    anchor_db_path: str = "data/constitution_anchors.jsonl"
    fed_node_id: str = ""
    fed_data_dir: str = "data/federation"
    fed_sync_interval: int = 60
    fed_max_peers: int = 64
    fed_jurisdiction: str = "NP"
    fed_compliance: bool = True
    compliance_cross_border_db: str = "data/cross_border_compliance.jsonl"

    # ═══════════════════════════════════════════════════════════════
    # Security / Level3 / TPM / HSM
    # ═══════════════════════════════════════════════════════════════
    level3_audit_db: str = "data/level3_audit.db"
    level3_webhook_url: Optional[str] = None
    power_balance_db_path: str = "data/power_balance_constitution.jsonl"
    tpm_provider: str = "software"
    tpm_device: str = ""
    tpm_pcr: str = "7,11"
    hsm_provider: str = "software"
    hsm_key_label: str = "asimnexus-gov-key"
    hsm_slot: str = "0"
    hsm_connector: str = "http://localhost:12345"

    # ═══════════════════════════════════════════════════════════════
    # Consensus
    # ═══════════════════════════════════════════════════════════════
    consensus_quorum: int = 8
    consensus_timeout: int = 60

    # ═══════════════════════════════════════════════════════════════
    # Agent System
    # ═══════════════════════════════════════════════════════════════
    agent_max_steps: int = 25
    agent_step_timeout: int = 60
    agent_session_timeout: int = 600
    agent_llm_provider: str = "openai"
    agent_llm_model: str = "gpt-4"
    agent_max_renewals: int = 3
    agent_cooling_off_hours: int = 72
    agent_expiry_warning_hours: int = 48

    # ═══════════════════════════════════════════════════════════════
    # Dharma / Veto
    # ═══════════════════════════════════════════════════════════════
    dharma_dt_engine: bool = True
    dharma_cultural: bool = True
    dharma_audit_max: int = 10000
    veto_finance_threshold: int = 1000
    veto_zkp_ttl: int = 300
    veto_audit_max: int = 10000

    # ═══════════════════════════════════════════════════════════════
    # World Clones
    # ═══════════════════════════════════════════════════════════════
    worldclone_timeout: int = 15
    worldclone_max_clones: int = 5
    worldclone_default_sector: str = "general"
    worldclone_agent_mode: bool = False

    # ═══════════════════════════════════════════════════════════════
    # Life Journey
    # ═══════════════════════════════════════════════════════════════
    life_db_path: str = "data/life_journey.jsonl"

    # ═══════════════════════════════════════════════════════════════
    # Connectors
    # ═══════════════════════════════════════════════════════════════
    connector_auth: bool = True
    whatsapp_api_key: Optional[str] = None
    whatsapp_phone_id: Optional[str] = None
    whatsapp_webhook_secret: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_webhook_url: Optional[str] = None
    discord_bot_token: Optional[str] = None
    discord_app_id: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    slack_bot_token: Optional[str] = None
    slack_webhook_url: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════
    # Database Migrations (PostgreSQL)
    # ═══════════════════════════════════════════════════════════════
    database_url_gov: str = "postgresql://gov:govpass@localhost/asim_gov"
    database_url_company: str = "postgresql://company:companypass@localhost/asim_company"
    database_url_user: str = "postgresql://user:userpass@localhost/asim_user"

    # ═══════════════════════════════════════════════════════════════
    # Backup
    # ═══════════════════════════════════════════════════════════════
    backup_s3_enabled: bool = False
    backup_s3_bucket: str = "asimnexus-backups"
    backup_s3_prefix: str = "database"
    backup_s3_endpoint: str = ""
    backup_aws_access_key: str = ""
    backup_aws_secret_key: str = ""

    # ═══════════════════════════════════════════════════════════════
    # Frontend
    # ═══════════════════════════════════════════════════════════════
    react_app_api_url: str = "http://localhost:8000"
    react_app_ws_url: str = "ws://localhost:8000"

    # ═══════════════════════════════════════════════════════════════
    # Offline Mode
    # ═══════════════════════════════════════════════════════════════
    offline_mode: bool = False

    # ═══════════════════════════════════════════════════════════════
    # NVIDIA API Keys (JSON)
    # ═══════════════════════════════════════════════════════════════
    nvidia_api_keys_json: str = "{}"

    @classmethod
    def from_env(cls) -> "AsimConfig":
        """Load config from environment variables."""
        return cls(
            # Core Server
            host=_str("ASIM_HOST", "127.0.0.1"),
            port=_int("ASIM_PORT", "8000"),
            log_level=_str("ASIM_LOG_LEVEL", "INFO"),
            data_dir=_str("ASIM_DATA_DIR", "data"),
            db_path=_str("ASIM_DB_PATH", "data/asim_core.db"),
            release_channel=_str("ASIM_RELEASE_CHANNEL", "stable"),
            test_mode=_bool("ASIM_TEST_MODE"),

            # CORS & Security
            cors_origins=_list("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"),
            jwt_secret=_str("JWT_SECRET", ""),
            jwt_algorithm=_str("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=_int("ACCESS_TOKEN_EXPIRE_MINUTES", "30"),
            refresh_token_expire_days=_int("REFRESH_TOKEN_EXPIRE_DAYS", "7"),
            use_hsm=_bool("JWT_USE_HSM"),
            pkcs11_lib_path=_str("PKCS11_LIB_PATH"),
            jwt_hsm_pin=_str("JWT_HSM_PIN", "1234"),
            jwt_hsm_key_label=_str("JWT_HSM_KEY_LABEL", "jwt-key"),
            jwt_public_key_pem_file=_str("JWT_PUBLIC_KEY_PEM_FILE", "public_key.pem"),
            security_mode=_str("ASIM_SECURITY_MODE", "strict"),

            # LLM Providers
            openai_api_key=_str("OPENAI_API_KEY") or None,
            openai_model=_str("OPENAI_MODEL", "gpt-4o-mini"),
            anthropic_api_key=_str("ANTHROPIC_API_KEY") or None,
            anthropic_model=_str("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            gemini_api_key=_str("GEMINI_API_KEY") or None,
            gemini_model=_str("GEMINI_MODEL", "gemini-1.5-flash"),
            grok_api_key=_str("GROK_API_KEY") or None,
            grok_model=_str("GROK_MODEL", "grok-beta"),
            deepseek_api_key=_str("DEEPSEEK_API_KEY") or None,
            deepseek_model=_str("DEEPSEEK_MODEL", "deepseek-chat"),
            nvidia_api_key=_str("NVIDIA_API_KEY") or None,
            nvidia_base_url=_str("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            nvidia_nim_model=_str("NVIDIA_NIM_MODEL", "meta/llama-3.1-8b-instruct"),
            ollama_url=_str("OLLAMA_URL", "http://localhost:11434"),
            ollama_model=_str("OLLAMA_MODEL", "gemma2:2b"),
            llm_engine_url=_str("LLM_ENGINE_URL", "http://localhost:8000"),

            # Local Model
            local_model_enabled=_bool("ASIM_LOCAL_MODEL_ENABLED", "true"),
            local_model_path=_str("ASIM_LOCAL_MODEL_PATH") or None,

            # Nepal-First Locale
            default_locale=_str("ASIM_LOCALE", "ne-NP"),
            default_language=_str("ASIM_LANGUAGE", "ne"),
            default_currency=_str("ASIM_CURRENCY", "NPR"),

            # Cloud / WAMP
            cloud_enabled=_bool("ASIM_CLOUD_ENABLED", "true"),
            cloud_url=_str("ASIM_CLOUD_URL", "https://api.asim-nexus.ai"),
            cloud_api_key=_str("ASIM_CLOUD_API_KEY") or None,
            wamp_enabled=_bool("ASIM_WAMP_ENABLED"),
            wamp_url=_str("ASIM_WAMP_URL", "ws://localhost:8080/ws"),
            wamp_realm=_str("ASIM_WAMP_REALM", "asim_nexus"),

            # Storage / Memory
            memory_path=_str("ASIM_MEMORY_PATH", "memory"),
            clone_storage_path=_str("ASIM_CLONE_STORAGE_PATH", "memory/clones"),
            vector_db_path=_str("ASIM_VECTOR_DB_PATH", "data/vector_memory.db"),
            embedding_backend=_str("ASIM_EMBEDDING_BACKEND", "chromadb"),
            chroma_path=_str("ASIM_CHROMA_PATH", "data/chromadb"),
            chroma_collection=_str("ASIM_CHROMA_COLLECTION", "asimnexus_memories"),
            vector_prune_days=_int("ASIM_VECTOR_PRUNE_DAYS", "90"),
            vector_keep_per_type=_int("ASIM_VECTOR_KEEP_PER_TYPE", "100"),
            embedding_cache_size=_int("ASIM_EMBEDDING_CACHE_SIZE", "10000"),

            # Redis
            redis_host=_str("REDIS_HOST", "localhost"),
            redis_port=_int("REDIS_PORT", "6379"),
            redis_db=_int("REDIS_DB", "0"),

            # Rate Limiting
            rate_limit_default=_int("ASIM_RATE_LIMIT_DEFAULT", "100"),
            rate_limit_window=_int("ASIM_RATE_LIMIT_WINDOW", "60"),

            # Self-Awareness
            knowledge_dir=_str("ASIM_KNOWLEDGE_DIR", "data/self_knowledge"),
            auto_scan=_bool("ASIM_AUTO_SCAN"),
            scan_interval_seconds=_int("ASIM_SCAN_INTERVAL_SECONDS", "3600"),
            auto_build_interval_seconds=_int("ASIM_AUTO_BUILD_INTERVAL_SECONDS", "7200"),

            # Mesh Network
            node_id=_str("ASIM_NODE_ID", ""),
            mesh_heartbeat_interval=_float("ASIM_MESH_HEARTBEAT_INTERVAL", "30"),
            mesh_node_discovery_interval=_float("ASIM_MESH_NODE_DISCOVERY_INTERVAL", "60"),
            mesh_node_startup_timeout=_float("ASIM_MESH_NODE_STARTUP_TIMEOUT", "30"),
            mesh_auto_recover=_bool("ASIM_MESH_AUTO_RECOVER", "true"),
            mesh_enable_relay=_bool("ASIM_MESH_ENABLE_RELAY", "true"),
            mesh_enable_rendezvous=_bool("ASIM_MESH_ENABLE_RENDEZVOUS", "true"),
            mesh_enable_multihop=_bool("ASIM_MESH_ENABLE_MULTIHOP", "true"),
            mesh_default=_str("ASIM_MESH_DEFAULT", "local"),
            mesh_db_path=_str("ASIM_MESH_DB_PATH", "data/mesh_routing.jsonl"),
            mesh_health_timeout=_int("ASIM_MESH_HEALTH_TIMEOUT", "10"),
            mesh_auto_switch_interval=_int("ASIM_MESH_AUTO_SWITCH_INTERVAL", "30"),
            mesh_dht_k=_int("ASIM_MESH_DHT_K", "20"),
            mesh_dht_alpha=_int("ASIM_MESH_DHT_ALPHA", "3"),
            mesh_dht_port=_int("ASIM_MESH_DHT_PORT", "7332"),
            mesh_dht_refresh_interval=_float("ASIM_MESH_DHT_REFRESH_INTERVAL", "3600"),
            mesh_dht_ttl=_float("ASIM_MESH_DHT_TTL", "86400"),
            mesh_bootstrap_port=_int("ASIM_MESH_BOOTSTRAP_PORT", "7335"),
            mesh_bootstrap_max_nodes=_int("ASIM_MESH_BOOTSTRAP_MAX_NODES", "50"),
            mesh_bootstrap_node_timeout=_int("ASIM_MESH_BOOTSTRAP_NODE_TIMEOUT", "3600"),
            mesh_bootstrap_cache_ttl=_int("ASIM_MESH_BOOTSTRAP_CACHE_TTL", "300"),
            mesh_bootstrap_seeds=_str("ASIM_MESH_BOOTSTRAP_SEEDS", ""),
            mesh_relay_port=_int("ASIM_MESH_RELAY_PORT", "7334"),
            mesh_relay_session_timeout=_int("ASIM_MESH_RELAY_SESSION_TIMEOUT", "300"),
            mesh_relay_max_sessions=_int("ASIM_MESH_RELAY_MAX_SESSIONS", "100"),
            mesh_rendezvous_port=_int("ASIM_MESH_RENDEZVOUS_PORT", "7336"),
            mesh_hole_punch_retries=_int("ASIM_MESH_HOLE_PUNCH_RETRIES", "3"),
            mesh_hole_punch_timeout=_int("ASIM_MESH_HOLE_PUNCH_TIMEOUT", "10"),
            mesh_punch_interval=_float("ASIM_MESH_PUNCH_INTERVAL", "0.1"),
            mesh_punch_keepalive=_float("ASIM_MESH_PUNCH_KEEPALIVE", "15"),
            mesh_stun_servers=_str("ASIM_MESH_STUN_SERVERS", ""),
            mesh_turn_servers=_str("ASIM_MESH_TURN_SERVERS", ""),
            mesh_turn_username=_str("ASIM_MESH_TURN_USERNAME", ""),
            mesh_turn_password=_str("ASIM_MESH_TURN_PASSWORD", ""),
            mesh_turn_server=_str("ASIM_MESH_TURN_SERVER", "turn:localhost:3478"),
            mesh_stun_timeout=_int("ASIM_MESH_STUN_TIMEOUT", "5"),
            mesh_stun_retries=_int("ASIM_MESH_STUN_RETRIES", "2"),
            mesh_max_hops=_int("ASIM_MESH_MAX_HOPS", "5"),
            mesh_path_discovery_timeout=_float("ASIM_MESH_PATH_DISCOVERY_TIMEOUT", "10"),
            mesh_path_discovery_ttl=_int("ASIM_MESH_PATH_DISCOVERY_TTL", "5"),
            mesh_path_refresh_interval=_float("ASIM_MESH_PATH_REFRESH_INTERVAL", "120"),
            mesh_store_forward_expiry=_float("ASIM_MESH_STORE_FORWARD_EXPIRY", "3600"),
            mesh_multihop_retry=_float("ASIM_MESH_MULTIHOP_RETRY", "30"),
            mesh_max_path_age=_float("ASIM_MESH_MAX_PATH_AGE", "300"),
            mesh_max_stored_msgs=_int("ASIM_MESH_MAX_STORED_MSGS", "1000"),
            mesh_crdt_op_max_age=_float("ASIM_MESH_CRDT_OP_MAX_AGE", "86400"),
            mesh_discovery_port=_int("ASIM_MESH_DISCOVERY_PORT", "7331"),
            mesh_discovery_interval=_int("ASIM_MESH_DISCOVERY_INTERVAL", "30"),
            mesh_discovery_timeout=_int("ASIM_MESH_DISCOVERY_TIMEOUT", "5"),
            mesh_beacon_interval=_int("ASIM_MESH_BEACON_INTERVAL", "60"),
            mesh_stale_node_age=_int("ASIM_MESH_STALE_NODE_AGE", "300"),
            mesh_node_registry_db=_str("ASIM_MESH_NODE_REGISTRY_DB", "data/node_registry.db"),
            single_machine_peers=_str("ASIM_SINGLE_MACHINE_PEERS", ""),
            p2p_peer_discovery_interval=_int("ASIM_P2P_PEER_DISCOVERY_INTERVAL", "60"),
            p2p_health_ping_interval=_int("ASIM_P2P_HEALTH_PING_INTERVAL", "30"),
            p2p_max_peers_per_mesh=_int("ASIM_P2P_MAX_PEERS_PER_MESH", "50"),

            # Sync / Offline
            sync_db_path=_str("ASIM_SYNC_DB_PATH", "data/offline_sync.jsonl"),
            sync_interval=_int("ASIM_SYNC_INTERVAL", "15"),
            sync_batch_size=_int("ASIM_SYNC_BATCH_SIZE", "50"),
            sync_max_retries=_int("ASIM_SYNC_MAX_RETRIES", "5"),
            sync_retry_backoff=_int("ASIM_SYNC_RETRY_BACKOFF", "30"),

            # Load Shedding
            load_shed_capacity=_int("ASIM_LOAD_SHED_CAPACITY", "100"),
            load_shed_refill_rate=_float("ASIM_LOAD_SHED_REFILL_RATE", "10"),
            load_shed_max_latency_ms=_float("ASIM_LOAD_SHED_MAX_LATENCY_MS", "500"),
            load_shed_min_bandwidth_kbps=_float("ASIM_LOAD_SHED_MIN_BANDWIDTH_KBPS", "100"),

            # Circuit Breaker
            circuit_breaker_failure_threshold=_int("ASIM_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"),
            circuit_breaker_recovery_timeout=_int("ASIM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30"),
            circuit_breaker_half_open_max_requests=_int("ASIM_CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS", "3"),

            # Device Registry
            scan_interval=_int("ASIM_SCAN_INTERVAL", "30"),
            health_interval=_int("ASIM_HEALTH_INTERVAL", "15"),
            stale_timeout=_int("ASIM_STALE_TIMEOUT", "300"),
            discovery_port=_int("ASIM_DISCOVERY_PORT", "7331"),
            max_backup_paths=_int("ASIM_MAX_BACKUP_PATHS", "3"),

            # Governance
            gov_audit_db_path=_str("ASIM_GOV_AUDIT_DB_PATH", "data/governance_audit.jsonl"),
            gov_audit_max=_int("ASIM_GOV_AUDIT_MAX", "100000"),
            gov_db_path=_str("ASIM_GOV_DB_PATH", "data/national_gov_layer.jsonl"),
            gov_emergency_threshold=_int("ASIM_GOV_EMERGENCY_THRESHOLD", "3"),
            gov_quorum_percent=_int("ASIM_GOV_QUORUM_PERCENT", "51"),
            gov_voting_period_hours=_int("ASIM_GOV_VOTING_PERIOD_HOURS", "72"),
            gov_min_voting_weight=_float("ASIM_GOV_MIN_VOTING_WEIGHT", "1.0"),
            anchor_db_path=_str("ASIM_ANCHOR_DB_PATH", "data/constitution_anchors.jsonl"),
            fed_node_id=_str("ASIM_FED_NODE_ID", ""),
            fed_data_dir=_str("ASIM_FED_DATA_DIR", "data/federation"),
            fed_sync_interval=_int("ASIM_FED_SYNC_INTERVAL", "60"),
            fed_max_peers=_int("ASIM_FED_MAX_PEERS", "64"),
            fed_jurisdiction=_str("ASIM_FED_JURISDICTION", "NP"),
            fed_compliance=_bool("ASIM_FED_COMPLIANCE", "true"),
            compliance_cross_border_db=_str("ASIM_COMPLIANCE_CROSS_BORDER_DB", "data/cross_border_compliance.jsonl"),

            # Security / Level3 / TPM / HSM
            level3_audit_db=_str("ASIM_LEVEL3_AUDIT_DB", "data/level3_audit.db"),
            level3_webhook_url=_str("ASIM_LEVEL3_WEBHOOK_URL") or None,
            power_balance_db_path=_str("ASIM_POWER_BALANCE_DB_PATH", "data/power_balance_constitution.jsonl"),
            tpm_provider=_str("ASIM_TPM_PROVIDER", "software"),
            tpm_device=_str("ASIM_TPM_DEVICE", ""),
            tpm_pcr=_str("ASIM_TPM_PCR", "7,11"),
            hsm_provider=_str("ASIM_HSM_PROVIDER", "software"),
            hsm_key_label=_str("ASIM_HSM_KEY_LABEL", "asimnexus-gov-key"),
            hsm_slot=_str("ASIM_HSM_SLOT", "0"),
            hsm_connector=_str("ASIM_HSM_CONNECTOR", "http://localhost:12345"),

            # Consensus
            consensus_quorum=_int("ASIM_CONSENSUS_QUORUM", "8"),
            consensus_timeout=_int("ASIM_CONSENSUS_TIMEOUT", "60"),

            # Agent System
            agent_max_steps=_int("ASIM_AGENT_MAX_STEPS", "25"),
            agent_step_timeout=_int("ASIM_AGENT_STEP_TIMEOUT", "60"),
            agent_session_timeout=_int("ASIM_AGENT_SESSION_TIMEOUT", "600"),
            agent_llm_provider=_str("ASIM_AGENT_LLM_PROVIDER", "openai"),
            agent_llm_model=_str("ASIM_AGENT_LLM_MODEL", "gpt-4"),
            agent_max_renewals=_int("ASIM_AGENT_MAX_RENEWALS", "3"),
            agent_cooling_off_hours=_int("ASIM_AGENT_COOLING_OFF_HOURS", "72"),
            agent_expiry_warning_hours=_int("ASIM_AGENT_EXPIRY_WARNING_HOURS", "48"),

            # Dharma / Veto
            dharma_dt_engine=_bool("ASIM_DHARMA_DT_ENGINE", "true"),
            dharma_cultural=_bool("ASIM_DHARMA_CULTURAL", "true"),
            dharma_audit_max=_int("ASIM_DHARMA_AUDIT_MAX", "10000"),
            veto_finance_threshold=_int("ASIM_VETO_FINANCE_THRESHOLD", "1000"),
            veto_zkp_ttl=_int("ASIM_VETO_ZKP_TTL", "300"),
            veto_audit_max=_int("ASIM_VETO_AUDIT_MAX", "10000"),

            # World Clones
            worldclone_timeout=_int("ASIM_WORLDCLONE_TIMEOUT", "15"),
            worldclone_max_clones=_int("ASIM_WORLDCLONE_MAX_CLONES", "5"),
            worldclone_default_sector=_str("ASIM_WORLDCLONE_DEFAULT_SECTOR", "general"),
            worldclone_agent_mode=_bool("ASIM_WORLDCLONE_AGENT_MODE"),

            # Life Journey
            life_db_path=_str("ASIM_LIFE_DB_PATH", "data/life_journey.jsonl"),

            # Connectors
            connector_auth=_bool("ASIM_CONNECTOR_AUTH", "true"),
            whatsapp_api_key=_str("WHATSAPP_API_KEY") or None,
            whatsapp_phone_id=_str("WHATSAPP_PHONE_ID") or None,
            whatsapp_webhook_secret=_str("WHATSAPP_WEBHOOK_SECRET") or None,
            telegram_bot_token=_str("TELEGRAM_BOT_TOKEN") or None,
            telegram_webhook_url=_str("TELEGRAM_WEBHOOK_URL") or None,
            discord_bot_token=_str("DISCORD_BOT_TOKEN") or None,
            discord_app_id=_str("DISCORD_APP_ID") or None,
            discord_webhook_url=_str("DISCORD_WEBHOOK_URL") or None,
            slack_bot_token=_str("SLACK_BOT_TOKEN") or None,
            slack_webhook_url=_str("SLACK_WEBHOOK_URL") or None,

            # Database Migrations (PostgreSQL)
            database_url_gov=_str("DATABASE_URL_GOV", "postgresql://gov:govpass@localhost/asim_gov"),
            database_url_company=_str("DATABASE_URL_COMPANY", "postgresql://company:companypass@localhost/asim_company"),
            database_url_user=_str("DATABASE_URL_USER", "postgresql://user:userpass@localhost/asim_user"),

            # Backup
            backup_s3_enabled=_bool("BACKUP_S3_ENABLED"),
            backup_s3_bucket=_str("BACKUP_S3_BUCKET", "asimnexus-backups"),
            backup_s3_prefix=_str("BACKUP_S3_PREFIX", "database"),
            backup_s3_endpoint=_str("BACKUP_S3_ENDPOINT", ""),
            backup_aws_access_key=_str("BACKUP_AWS_ACCESS_KEY", ""),
            backup_aws_secret_key=_str("BACKUP_AWS_SECRET_KEY", ""),

            # Frontend
            react_app_api_url=_str("REACT_APP_API_URL", "http://localhost:8000"),
            react_app_ws_url=_str("REACT_APP_WS_URL", "ws://localhost:8000"),

            # Offline Mode
            offline_mode=_bool("OFFLINE_MODE"),

            # NVIDIA API Keys (JSON)
            nvidia_api_keys_json=_str("ASIM_NVIDIA_API_KEYS", "{}"),
        )

    @classmethod
    def from_file(cls, path: str = "asim_config.yaml") -> "AsimConfig":
        """Load config from YAML file"""
        if not os.path.exists(path):
            return cls.from_env()

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }

    def to_env_dict(self) -> Dict[str, str]:
        """Convert to environment variable dictionary (for export)."""
        mapping = {
            "host": "ASIM_HOST",
            "port": "ASIM_PORT",
            "log_level": "ASIM_LOG_LEVEL",
            "data_dir": "ASIM_DATA_DIR",
            "db_path": "ASIM_DB_PATH",
            "release_channel": "ASIM_RELEASE_CHANNEL",
            "jwt_secret": "JWT_SECRET",
            "cors_origins": "CORS_ORIGINS",
            "openai_api_key": "OPENAI_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "gemini_api_key": "GEMINI_API_KEY",
        }
        result = {}
        for attr, env_var in mapping.items():
            val = getattr(self, attr, None)
            if val is not None:
                if isinstance(val, list):
                    result[env_var] = ",".join(val)
                elif isinstance(val, bool):
                    result[env_var] = "true" if val else "false"
                else:
                    result[env_var] = str(val)
        return result


# Global config instance
_config: Optional[AsimConfig] = None


def get_config() -> AsimConfig:
    """Get global config (lazy load)"""
    global _config
    if _config is None:
        _config = AsimConfig.from_env()
    return _config


def set_config(config: AsimConfig):
    """Set global config"""
    global _config
    _config = config


# Load on import
config = get_config()
