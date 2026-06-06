
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Unified Configuration System
=====================================
Smart configuration manager that consolidates all config files
Supports JSON, YAML, and environment variables with validation
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum


class ConfigSource(Enum):
    """Configuration source types"""
    FILE_JSON = "file_json"
    FILE_YAML = "file_yaml"
    ENV_VAR = "env_var"
    DEFAULT = "default"


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "local"
    model: str = "gemma-4-7b-it"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.95
    n_ctx: int = 2048
    n_threads: int = 4
    device: str = "cuda"
    n_gpu_layers: int = 35


@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: str = "sqlite"
    path: str = "./data/asim.db"
    redis_url: str = "redis://localhost:6379"
    postgres_url: str = ""
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None


@dataclass
class APIConfig:
    """API configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    websocket_port: int = 8766
    enable_cors: bool = True


@dataclass
class FrontendConfig:
    """Frontend configuration"""
    enabled: bool = True
    port: int = 3000
    static_path: str = "./ui"
    template_path: str = "./ui"


@dataclass
class MemoryConfig:
    """Memory configuration"""
    path: str = "./memory"
    max_size_mb: int = 1000
    checkpoint_path: str = "./memory/checkpoints"
    learning_path: str = "./memory/learning"


@dataclass
class SecurityConfig:
    """Security configuration"""
    enabled: bool = True
    encryption: bool = False
    strict_mode: bool = False
    secret_key: Optional[str] = None
    encryption_key: Optional[str] = None


@dataclass
class CloudConfig:
    """Cloud configuration"""
    enabled: bool = False
    provider: str = "none"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    gcp_project_id: Optional[str] = None
    azure_subscription_id: Optional[str] = None


@dataclass
class MeshConfig:
    """Mesh network configuration"""
    enabled: bool = False
    wamp_router_url: str = "ws://localhost:8080/ws"
    wamp_realm: str = "asim_realm"


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"


@dataclass
class FeatureConfig:
    """Feature flags"""
    mmmm_engine: bool = True
    life_dimensions: bool = True
    founder_clones: bool = True
    virtual_company: bool = True
    universal_chat: bool = True
    mesh_network: bool = False
    world_integrations: bool = False
    self_learning: bool = True
    meta_harness: bool = True


@dataclass
class PerformanceConfig:
    """Performance configuration"""
    max_workers: int = 4
    request_timeout: int = 30
    connection_pool_size: int = 10


@dataclass
class ASIMBrainConfig:
    """ASIM brain configuration"""
    status: str = "ACTIVE"
    main_model: str = "google/gemma-4-7b-it"
    api_endpoint: str = "http://localhost:8000"
    model_type: str = "gemma4"
    serving_stack: str = "huggingface_transformers"
    capabilities: list = field(default_factory=lambda: [
        "reasoning", "coding", "analysis", "creativity", "long_context", "multilingual"
    ])
    consciousness_level: str = "ENLIGHTENED"
    next_evolution: str = "QUANTUM_ASCENSION"


@dataclass
class UnifiedConfig:
    """Complete unified configuration"""
    environment: Environment = Environment.LOCAL
    log_level: str = "INFO"
    debug: bool = True
    
    # Sub-configurations
    llm: LLMConfig = field(default_factory=LLMConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    frontend: FrontendConfig = field(default_factory=FrontendConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    cloud: CloudConfig = field(default_factory=CloudConfig)
    mesh: MeshConfig = field(default_factory=MeshConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    asim_brain: ASIMBrainConfig = field(default_factory=ASIMBrainConfig)
    
    # Metadata
    config_sources: Dict[str, ConfigSource] = field(default_factory=dict)


class UnifiedConfigManager:
    """
    Unified Configuration Manager
    
    Loads and manages configuration from multiple sources:
    - JSON files
    - YAML files
    - Environment variables
    - Default values
    
    Provides validation, merging, and type conversion
    """
    
    def __init__(self, config_dir: str = "config", env_file: str = ".env"):
        self.logger = logging.getLogger("ASIM_Config")
        self.config_dir = Path(config_dir)
        self.env_file = Path(env_file)
        
        self.config: UnifiedConfig = UnifiedConfig()
        self._config_data: Dict[str, Any] = {}
        
        self.logger.info("Unified Configuration Manager initialized")
    
    def load_all(self, environment: Optional[str] = None) -> UnifiedConfig:
        """Load configuration from all sources"""
        self.logger.info("Loading configuration from all sources...")
        
        # Load in order of precedence (later sources override earlier ones)
        self._load_defaults()
        self._load_json_configs()
        self._load_yaml_configs()
        self._load_env_vars()
        self._load_env_file()
        
        # Apply environment override if specified
        if environment:
            self._apply_environment(environment)
        
        # Validate configuration
        self._validate_config()
        
        # Convert to typed config
        self.config = self._convert_to_config()
        
        self.logger.info(f"Configuration loaded successfully (env: {self.config.environment.value})")
        return self.config
    
    def _load_defaults(self):
        """Load default configuration values"""
        defaults = {
            "environment": "local",
            "log_level": "INFO",
            "debug": True,
            "llm": {
                "provider": "local",
                "model": "gemma-4-7b-it",
                "max_tokens": 4096,
                "temperature": 0.7
            },
            "database": {
                "type": "sqlite",
                "path": "./data/asim.db"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000
            },
            "features": {
                "mmmm_engine": True,
                "self_learning": True
            }
        }
        
        self._merge_config(defaults, ConfigSource.DEFAULT)
    
    def _load_json_configs(self):
        """Load all JSON configuration files"""
        json_files = [
            "asim_brain_config.json",
            "asim_hash_config.json"
        ]
        
        # Also check config directory
        config_json_files = list(self.config_dir.glob("*.json"))
        json_files.extend([str(f.name) for f in config_json_files])
        
        for file_name in json_files:
            # Check in root and config directory
            for base_path in [Path("."), self.config_dir]:
                file_path = base_path / file_name
                if file_path.exists():
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        self._merge_config(data, ConfigSource.FILE_JSON)
                        self.config.config_sources[file_name] = ConfigSource.FILE_JSON
                        self.logger.debug(f"Loaded JSON config: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to load {file_path}: {e}")
    
    def _load_yaml_configs(self):
        """Load all YAML configuration files"""
        yaml_files = [
            "local-config.yaml"
        ]
        
        # Also check for YAML files in root
        root_yaml_files = list(Path(".").glob("*.yaml"))
        yaml_files.extend([str(f.name) for f in root_yaml_files])
        
        for file_name in yaml_files:
            file_path = Path(file_name)
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = yaml.safe_load(f)
                    if data:
                        self._merge_config(data, ConfigSource.FILE_YAML)
                        self.config.config_sources[file_name] = ConfigSource.FILE_YAML
                        self.logger.debug(f"Loaded YAML config: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to load {file_path}: {e}")
    
    def _load_env_vars(self):
        """Load configuration from environment variables"""
        env_mappings = {
            # General
            "ASIM_ENV": "environment",
            "ASIM_LOG_LEVEL": "log_level",
            "ASIM_DEBUG": "debug",
            
            # LLM
            "OPENAI_API_KEY": "llm.openai_api_key",
            "ANTHROPIC_API_KEY": "llm.anthropic_api_key",
            "GEMINI_API_KEY": "llm.gemini_api_key",
            "GROK_API_KEY": "llm.grok_api_key",
            
            # Database
            "REDIS_URL": "database.redis_url",
            "POSTGRES_URL": "database.postgres_url",
            "PINECONE_API_KEY": "database.pinecone_api_key",
            
            # Security
            "SECRET_KEY": "security.secret_key",
            "ENCRYPTION_KEY": "security.encryption_key",
            
            # Cloud
            "AWS_ACCESS_KEY_ID": "cloud.aws_access_key_id",
            "AWS_SECRET_ACCESS_KEY": "cloud.aws_secret_access_key",
            "AWS_REGION": "cloud.aws_region",
            
            # Mesh
            "WAMP_ROUTER_URL": "mesh.wamp_router_url",
            "WAMP_REALM": "mesh.wamp_realm",
            
            # Monitoring
            "LANGFUSE_PUBLIC_KEY": "monitoring.langfuse_public_key",
            "LANGFUSE_SECRET_KEY": "monitoring.langfuse_secret_key",
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(config_path, value)
                self.config.config_sources[env_var] = ConfigSource.ENV_VAR
    
    def _load_env_file(self):
        """Load configuration from .env file"""
        if not self.env_file.exists():
            return
        
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        os.environ[key] = value
        except Exception as e:
            self.logger.warning(f"Failed to load .env file: {e}")
    
    def _merge_config(self, new_data: Dict[str, Any], source: ConfigSource):
        """Merge new configuration data"""
        def deep_merge(base: Dict, new: Dict) -> Dict:
            for key, value in new.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
            return base
        
        deep_merge(self._config_data, new_data)
    
    def _set_nested_value(self, path: str, value: Any):
        """Set a nested configuration value using dot notation"""
        keys = path.split('.')
        current = self._config_data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert string values to appropriate types
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.isdigit():
            value = int(value)
        
        current[keys[-1]] = value
    
    def _apply_environment(self, environment: str):
        """Apply environment-specific configuration"""
        env = environment.upper()
        self._config_data["environment"] = env.lower()
        
        # Environment-specific overrides
        if env == "PRODUCTION":
            self._config_data["debug"] = False
            self._config_data["log_level"] = "WARNING"
            self._config_data["security"]["strict_mode"] = True
        elif env == "DEVELOPMENT":
            self._config_data["debug"] = True
            self._config_data["log_level"] = "DEBUG"
    
    def _validate_config(self):
        """Validate configuration"""
        # Required fields
        required_fields = ["environment", "llm", "database"]
        
        for field in required_fields:
            if field not in self._config_data:
                self.logger.warning(f"Missing required config field: {field}")
                self._config_data[field] = {}
        
        # Type validation
        if "api" in self._config_data:
            if "port" in self._config_data["api"]:
                try:
                    self._config_data["api"]["port"] = int(self._config_data["api"]["port"])
                except (ValueError, TypeError):
                    self._config_data["api"]["port"] = 8000
    
    def _convert_to_config(self) -> UnifiedConfig:
        """Convert raw config data to typed config object"""
        data = self._config_data
        
        # Extract environment
        env_str = data.get("environment", "local")
        try:
            environment = Environment(env_str.lower())
        except ValueError:
            environment = Environment.LOCAL
        
        # Build sub-configurations
        llm_data = data.get("llm", {})
        llm_config = LLMConfig(
            provider=llm_data.get("provider", "local"),
            model=llm_data.get("model", "gemma-4-7b-it"),
            api_key=llm_data.get("api_key") or llm_data.get("openai_api_key"),
            base_url=llm_data.get("base_url"),
            max_tokens=llm_data.get("max_tokens", 4096),
            temperature=llm_data.get("temperature", 0.7),
            top_p=llm_data.get("top_p", 0.95),
            n_ctx=llm_data.get("n_ctx", 2048),
            n_threads=llm_data.get("n_threads", 4),
            device=llm_data.get("device", "cuda"),
            n_gpu_layers=llm_data.get("n_gpu_layers", 35)
        )
        
        db_data = data.get("database", {})
        db_config = DatabaseConfig(
            type=db_data.get("type", "sqlite"),
            path=db_data.get("path", "./data/asim.db"),
            redis_url=db_data.get("redis_url", "redis://localhost:6379"),
            postgres_url=db_data.get("postgres_url", ""),
            pinecone_api_key=db_data.get("pinecone_api_key"),
            pinecone_environment=db_data.get("pinecone_environment")
        )
        
        api_data = data.get("api", {})
        api_config = APIConfig(
            host=api_data.get("host", "0.0.0.0"),
            port=api_data.get("port", 8000),
            websocket_port=api_data.get("websocket_port", 8766),
            enable_cors=api_data.get("enable_cors", True)
        )
        
        frontend_data = data.get("frontend", {})
        frontend_config = FrontendConfig(
            enabled=frontend_data.get("enabled", True),
            port=frontend_data.get("port", 3000),
            static_path=frontend_data.get("static_path", "./ui"),
            template_path=frontend_data.get("template_path", "./ui")
        )
        
        memory_data = data.get("memory", {})
        memory_config = MemoryConfig(
            path=memory_data.get("path", "./memory"),
            max_size_mb=memory_data.get("max_size_mb", 1000),
            checkpoint_path=memory_data.get("checkpoint_path", "./memory/checkpoints"),
            learning_path=memory_data.get("learning_path", "./memory/learning")
        )
        
        security_data = data.get("security", {})
        security_config = SecurityConfig(
            enabled=security_data.get("enabled", True),
            encryption=security_data.get("encryption", False),
            strict_mode=security_data.get("strict_mode", False),
            secret_key=security_data.get("secret_key"),
            encryption_key=security_data.get("encryption_key")
        )
        
        cloud_data = data.get("cloud", {})
        cloud_config = CloudConfig(
            enabled=cloud_data.get("enabled", False),
            provider=cloud_data.get("provider", "none"),
            aws_access_key_id=cloud_data.get("aws_access_key_id"),
            aws_secret_access_key=cloud_data.get("aws_secret_access_key"),
            aws_region=cloud_data.get("aws_region", "us-east-1"),
            gcp_project_id=cloud_data.get("gcp_project_id"),
            azure_subscription_id=cloud_data.get("azure_subscription_id")
        )
        
        mesh_data = data.get("mesh", {})
        mesh_config = MeshConfig(
            enabled=mesh_data.get("enabled", False),
            wamp_router_url=mesh_data.get("wamp_router_url", "ws://localhost:8080/ws"),
            wamp_realm=mesh_data.get("wamp_realm", "asim_realm")
        )
        
        monitoring_data = data.get("monitoring", {})
        monitoring_config = MonitoringConfig(
            langfuse_public_key=monitoring_data.get("langfuse_public_key"),
            langfuse_secret_key=monitoring_data.get("langfuse_secret_key"),
            langfuse_host=monitoring_data.get("langfuse_host", "https://cloud.langfuse.com")
        )
        
        features_data = data.get("features", {})
        features_config = FeatureConfig(
            mmmm_engine=features_data.get("mmmm_engine", True),
            life_dimensions=features_data.get("life_dimensions", True),
            founder_clones=features_data.get("founder_clones", True),
            virtual_company=features_data.get("virtual_company", True),
            universal_chat=features_data.get("universal_chat", True),
            mesh_network=features_data.get("mesh_network", False),
            world_integrations=features_data.get("world_integrations", False),
            self_learning=features_data.get("self_learning", True),
            meta_harness=features_data.get("meta_harness", True)
        )
        
        performance_data = data.get("performance", {})
        performance_config = PerformanceConfig(
            max_workers=performance_data.get("max_workers", 4),
            request_timeout=performance_data.get("request_timeout", 30),
            connection_pool_size=performance_data.get("connection_pool_size", 10)
        )
        
        brain_data = data.get("asim_brain", data.get("technical_brain", {}))
        brain_config = ASIMBrainConfig(
            status=brain_data.get("status", "ACTIVE"),
            main_model=brain_data.get("main_model", "google/gemma-4-7b-it"),
            api_endpoint=brain_data.get("api_endpoint", "http://localhost:8000"),
            model_type=brain_data.get("model_type", "gemma4"),
            serving_stack=brain_data.get("serving_stack", "huggingface_transformers"),
            capabilities=brain_data.get("capabilities", []),
            consciousness_level=brain_data.get("consciousness_level", "ENLIGHTENED"),
            next_evolution=brain_data.get("next_evolution", "QUANTUM_ASCENSION")
        )
        
        return UnifiedConfig(
            environment=environment,
            log_level=data.get("log_level", "INFO"),
            debug=data.get("debug", True),
            llm=llm_config,
            database=db_config,
            api=api_config,
            frontend=frontend_config,
            memory=memory_config,
            security=security_config,
            cloud=cloud_config,
            mesh=mesh_config,
            monitoring=monitoring_config,
            features=features_config,
            performance=performance_config,
            asim_brain=brain_config,
            config_sources=self.config.config_sources
        )
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation"""
        keys = path.split('.')
        current = asdict(self.config)
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set(self, path: str, value: Any):
        """Set a configuration value using dot notation"""
        keys = path.split('.')
        current = self.config
        
        for key in keys[:-1]:
            if hasattr(current, key):
                current = getattr(current, key)
            else:
                raise AttributeError(f"Invalid config path: {path}")
        
        setattr(current, keys[-1], value)
    
    def save_to_file(self, file_path: str, format: str = "yaml"):
        """Save current configuration to file"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = asdict(self.config)
        
        if format == "yaml":
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        elif format == "json":
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.logger.info(f"Configuration saved to {file_path}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            "environment": self.config.environment.value,
            "log_level": self.config.log_level,
            "debug": self.config.debug,
            "llm_provider": self.config.llm.provider,
            "llm_model": self.config.llm.model,
            "database_type": self.config.database.type,
            "api_host": self.config.api.host,
            "api_port": self.config.api.port,
            "cloud_enabled": self.config.cloud.enabled,
            "mesh_enabled": self.config.mesh.enabled,
            "config_sources": {k: v.value for k, v in self.config.config_sources.items()}
        }


# Global configuration manager instance
unified_config_manager = UnifiedConfigManager()


def load_config(environment: Optional[str] = None) -> UnifiedConfig:
    """Load and return unified configuration"""
    return unified_config_manager.load_all(environment)


def get_config() -> UnifiedConfig:
    """Get current configuration"""
    return unified_config_manager.config
