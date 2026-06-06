#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade health probes
ASIMNEXUS Health Probe System
============================
Kubernetes-style health checks for production deployment:
- /health/live — Process alive check (always 200 if running)
- /health/ready — Dependency readiness check (DB, LLM, core modules, storage services)
- /health/status — Full system status with detailed metrics including storage layer
"""

import logging
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("AsimNexus.Health")

# Storage service connection settings (from environment or defaults)
STORAGE_CONFIG = {
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "timeout": 3,
    },
    "clickhouse": {
        "host": os.getenv("CLICKHOUSE_HOST", "localhost"),
        "http_port": int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123")),
        "native_port": int(os.getenv("CLICKHOUSE_NATIVE_PORT", "9000")),
        "timeout": 5,
    },
    "postgres": {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "user": os.getenv("POSTGRES_USER", "asimnexus"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
        "dbname": os.getenv("POSTGRES_DB", "asimnexus"),
        "timeout": 5,
    },
    "minio": {
        "host": os.getenv("MINIO_HOST", "localhost"),
        "api_port": int(os.getenv("MINIO_API_PORT", "9000")),
        "console_port": int(os.getenv("MINIO_CONSOLE_PORT", "9001")),
        "access_key": os.getenv("MINIO_ACCESS_KEY", ""),
        "secret_key": os.getenv("MINIO_SECRET_KEY", ""),
        "timeout": 5,
    },
    "chromadb": {
        "host": os.getenv("CHROMADB_HOST", "localhost"),
        "port": int(os.getenv("CHROMADB_PORT", "8000")),
        "timeout": 5,
    },
}


class HealthChecker:
    """Production-grade health probe system for AsimNexus backend."""

    def __init__(self, db_path: str, gguf_model_path: str):
        self.db_path = db_path
        self.gguf_model_path = gguf_model_path
        self.start_time = datetime.now()
        self.logger = logger

    # ------------------------------------------------------------------ #
    #  Public probes                                                      #
    # ------------------------------------------------------------------ #

    def check_live(self) -> Dict[str, Any]:
        """Liveness probe — always returns 200 if process is alive."""
        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }

    def check_ready(self) -> Dict[str, Any]:
        """Readiness probe — checks core deps + all storage services."""
        checks = {
            "database": self._check_database(),
            "model_file": self._check_model_file(),
            "redis": self._check_redis(),
            "clickhouse": self._check_clickhouse(),
            "postgres": self._check_postgres(),
            "minio": self._check_minio(),
            "chromadb": self._check_chromadb(),
        }
        all_ready = all(check["ready"] for check in checks.values())
        return {
            "status": "ready" if all_ready else "not_ready",
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
            "all_ready": all_ready
        }

    def check_status(self) -> Dict[str, Any]:
        """Full status check with storage layer diagnostics."""
        ready_result = self.check_ready()
        return {
            "status": ready_result["status"],
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "readiness": ready_result,
            "dependencies": {
                "database": self._get_database_status(),
                "model_file": self._get_model_file_status(),
            },
            "storage": {
                "redis": self._get_redis_status(),
                "clickhouse": self._get_clickhouse_status(),
                "postgres": self._get_postgres_status(),
                "minio": self._get_minio_status(),
                "chromadb": self._get_chromadb_status(),
            },
            "modules": self._get_module_status(),
            "system": self._get_system_metrics()
        }

    # ------------------------------------------------------------------ #
    #  Storage check helpers (ready=True / False)                         #
    # ------------------------------------------------------------------ #

    def _check_redis(self) -> Dict[str, Any]:
        """Check Redis reachability via PING."""
        cfg = STORAGE_CONFIG["redis"]
        try:
            import redis as redis_client
            r = redis_client.Redis(
                host=cfg["host"], port=cfg["port"],
                socket_connect_timeout=cfg["timeout"], decode_responses=True,
            )
            r.ping()
            return {"ready": True, "message": f"Redis reachable at {cfg['host']}:{cfg['port']}"}
        except ImportError:
            return {"ready": False, "message": "redis-py not installed"}
        except Exception as e:
            return {"ready": False, "message": f"Redis error: {e}"}

    def _check_clickhouse(self) -> Dict[str, Any]:
        """Check ClickHouse reachability via HTTP /ping."""
        cfg = STORAGE_CONFIG["clickhouse"]
        try:
            import requests
            url = f"http://{cfg['host']}:{cfg['http_port']}/ping"
            resp = requests.get(url, timeout=cfg["timeout"])
            if resp.status_code == 200:
                return {"ready": True, "message": f"ClickHouse reachable at {url}"}
            return {"ready": False, "message": f"ClickHouse returned HTTP {resp.status_code}"}
        except ImportError:
            return {"ready": False, "message": "requests not installed"}
        except Exception as e:
            return {"ready": False, "message": f"ClickHouse error: {e}"}

    def _check_postgres(self) -> Dict[str, Any]:
        """Check PostgreSQL reachability via connection."""
        cfg = STORAGE_CONFIG["postgres"]
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=cfg["host"], port=cfg["port"],
                user=cfg["user"], password=cfg["password"],
                dbname=cfg["dbname"], connect_timeout=cfg["timeout"],
            )
            conn.close()
            return {"ready": True, "message": f"PostgreSQL reachable at {cfg['host']}:{cfg['port']}"}
        except ImportError:
            return {"ready": False, "message": "psycopg2 not installed"}
        except Exception as e:
            return {"ready": False, "message": f"PostgreSQL error: {e}"}

    def _check_minio(self) -> Dict[str, Any]:
        """Check MinIO reachability via /minio/health/live."""
        cfg = STORAGE_CONFIG["minio"]
        try:
            import requests
            url = f"http://{cfg['host']}:{cfg['api_port']}/minio/health/live"
            resp = requests.get(url, timeout=cfg["timeout"])
            if resp.status_code == 200:
                return {"ready": True, "message": f"MinIO reachable at {url}"}
            return {"ready": False, "message": f"MinIO returned HTTP {resp.status_code}"}
        except ImportError:
            return {"ready": False, "message": "requests not installed"}
        except Exception as e:
            return {"ready": False, "message": f"MinIO error: {e}"}

    def _check_chromadb(self) -> Dict[str, Any]:
        """Check ChromaDB reachability via /api/v1/heartbeat."""
        cfg = STORAGE_CONFIG["chromadb"]
        try:
            import requests
            url = f"http://{cfg['host']}:{cfg['port']}/api/v1/heartbeat"
            resp = requests.get(url, timeout=cfg["timeout"])
            if resp.status_code == 200:
                return {"ready": True, "message": f"ChromaDB reachable at {url}"}
            return {"ready": False, "message": f"ChromaDB returned HTTP {resp.status_code}"}
        except ImportError:
            return {"ready": False, "message": "requests not installed"}
        except Exception as e:
            return {"ready": False, "message": f"ChromaDB error: {e}"}

    # ------------------------------------------------------------------ #
    #  Storage status reporters (detailed diagnostics)                    #
    # ------------------------------------------------------------------ #

    def _get_redis_status(self) -> Dict[str, Any]:
        cfg = STORAGE_CONFIG["redis"]
        try:
            import redis as redis_client
            r = redis_client.Redis(
                host=cfg["host"], port=cfg["port"],
                socket_connect_timeout=cfg["timeout"], decode_responses=True,
            )
            info = r.info()
            return {
                "status": "connected",
                "host": cfg["host"], "port": cfg["port"],
                "version": info.get("redis_version", "unknown"),
                "uptime_days": info.get("uptime_in_days", 0),
                "used_memory_bytes": info.get("used_memory", 0),
                "connected_clients": info.get("connected_clients", 0),
            }
        except ImportError:
            return {"status": "unavailable", "note": "redis-py not installed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _get_clickhouse_status(self) -> Dict[str, Any]:
        cfg = STORAGE_CONFIG["clickhouse"]
        try:
            import requests
            url = f"http://{cfg['host']}:{cfg['http_port']}/?query=SELECT version(),uptime()"
            resp = requests.get(url, timeout=cfg["timeout"])
            parts = resp.text.strip().split("\t") if resp.ok else ["unknown"]
            return {
                "status": "connected",
                "host": cfg["host"],
                "http_port": cfg["http_port"],
                "native_port": cfg["native_port"],
                "version": parts[0] if len(parts) >= 1 else "unknown",
                "uptime_seconds": int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0,
            }
        except ImportError:
            return {"status": "unavailable", "note": "requests not installed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _get_postgres_status(self) -> Dict[str, Any]:
        cfg = STORAGE_CONFIG["postgres"]
        try:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(
                host=cfg["host"], port=cfg["port"],
                user=cfg["user"], password=cfg["password"],
                dbname=cfg["dbname"], connect_timeout=cfg["timeout"],
            )
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT version() as v,
                       pg_postmaster_start_time as start_time,
                       pg_database_size(current_database()) as db_size
            """)
            row = cur.fetchone()
            conn.close()
            return {
                "status": "connected",
                "host": cfg["host"], "port": cfg["port"], "dbname": cfg["dbname"],
                "version": row["v"].split(",")[0] if row["v"] else "unknown",
                "start_time": row["start_time"].isoformat() if row.get("start_time") else None,
                "db_size_bytes": row["db_size"] if row.get("db_size") else 0,
            }
        except ImportError:
            return {"status": "unavailable", "note": "psycopg2 not installed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _get_minio_status(self) -> Dict[str, Any]:
        cfg = STORAGE_CONFIG["minio"]
        try:
            from minio import Minio
            client = Minio(
                f"{cfg['host']}:{cfg['api_port']}",
                access_key=cfg["access_key"],
                secret_key=cfg["secret_key"],
                secure=False,
            )
            buckets = client.list_buckets()
            return {
                "status": "connected",
                "host": cfg["host"],
                "api_port": cfg["api_port"],
                "console_port": cfg["console_port"],
                "bucket_count": len(buckets),
                "buckets": [b.name for b in buckets],
            }
        except ImportError:
            return {"status": "unavailable", "note": "minio-py SDK not installed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _get_chromadb_status(self) -> Dict[str, Any]:
        cfg = STORAGE_CONFIG["chromadb"]
        try:
            import requests
            hb = requests.get(
                f"http://{cfg['host']}:{cfg['port']}/api/v1/heartbeat",
                timeout=cfg["timeout"],
            )
            coll = requests.get(
                f"http://{cfg['host']}:{cfg['port']}/api/v1/collections",
                timeout=cfg["timeout"],
            )
            collections = coll.json() if coll.ok else []
            return {
                "status": "connected",
                "host": cfg["host"], "port": cfg["port"],
                "heartbeat": hb.json() if hb.ok else None,
                "collection_count": len(collections),
            }
        except ImportError:
            return {"status": "unavailable", "note": "requests not installed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ------------------------------------------------------------------ #
    #  Existing helper methods (unchanged)                                #
    # ------------------------------------------------------------------ #

    def _check_database(self) -> Dict[str, Any]:
        """Check if SQLite database is accessible."""
        if not Path(self.db_path).exists():
            return {"ready": False, "message": f"Database file not found: {self.db_path}"}
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT 1")
            conn.close()
            return {"ready": True, "message": "Database accessible"}
        except Exception as e:
            return {"ready": False, "message": f"Database error: {e}"}

    def _check_model_file(self) -> Dict[str, Any]:
        """Check if GGUF model file exists."""
        model_exists = Path(self.gguf_model_path).exists()
        if model_exists:
            return {"ready": True, "message": "Model file exists"}
        return {"ready": False, "message": f"Model file not found: {self.gguf_model_path}"}

    def _get_database_status(self) -> Dict[str, Any]:
        """Get detailed SQLite database status."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM messages")
            message_count = cursor.fetchone()[0]
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            conn.close()
            return {
                "status": "connected",
                "path": self.db_path,
                "tables_count": len(tables),
                "users_count": user_count,
                "messages_count": message_count,
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024 * 1024), 2)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _get_model_file_status(self) -> Dict[str, Any]:
        """Get detailed model file status."""
        model_path = Path(self.gguf_model_path)
        if not model_path.exists():
            return {"status": "not_found", "path": self.gguf_model_path}
        stat = model_path.stat()
        return {
            "status": "exists",
            "path": self.gguf_model_path,
            "size_bytes": stat.st_size,
            "size_gb": round(stat.st_size / (1024 * 1024 * 1024), 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

    def _get_module_status(self) -> Dict[str, Any]:
        """Get status of core modules (graceful fallback)."""
        modules = {}
        module_checks = {
            "user_identity": "core.identity.user_identity",
            "world_clones": "core.founder_clones.world_clones",
            "hybrid_router": "core.routing.hybrid_router",
            "vector_memory": "core.vectormemory",
            "node_registry": "core.network.node_registry",
            "safety_veto": "core.dharma_chakra.safety_veto",
            "personal_os": "core.identity.personal_os",
            "job_marketplace": "core.economy.job_marketplace",
            "dreaming_engine": "core.dreaming.dreaming_engine",
            "dharma_veto": "core.dharma.dharma_veto",
        }
        for name, module_path in module_checks.items():
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    __import__(module_path)
                modules[name] = {"status": "loaded"}
            except ImportError:
                modules[name] = {"status": "not_loaded"}
            except Exception as e:
                modules[name] = {"status": "error", "error": str(e)}
        return modules

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get basic system metrics."""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
            }
        except ImportError:
            return {
                "cpu_percent": None, "memory_percent": None,
                "disk_percent": None, "note": "psutil not installed"
            }


# ------------------------------------------------------------------ #
#  Global health checker instance & route wiring                      #
# ------------------------------------------------------------------ #

_health_checker: Optional[HealthChecker] = None


def get_health_checker(db_path: str = None, gguf_model_path: str = None) -> HealthChecker:
    """Get or create health checker instance.

    Falls back to environment variables if paths not provided:
    - ASIM_DB_PATH (default: data/asim_core.db)
    - ASIM_GGUF_MODEL_PATH (default: models/Qwen3-4B-distill-deepseek-opus-gemini-Q8_0.gguf)
    """
    global _health_checker
    if db_path is None:
        db_path = os.getenv("ASIM_DB_PATH", "data/asim_core.db")
    if gguf_model_path is None:
        gguf_model_path = os.getenv("ASIM_GGUF_MODEL_PATH",
                                     "models/Qwen3-4B-distill-deepseek-opus-gemini-Q8_0.gguf")
    _health_checker = HealthChecker(db_path, gguf_model_path)
    return _health_checker


def reset_health_checker():
    """Reset the global health checker instance (for testing)."""
    global _health_checker
    _health_checker = None


def setup_health_routes(app, db_path: str, gguf_model_path: str):
    """
    Setup health probe routes on FastAPI app.
    Call this from simple_backend.py to wire health endpoints.
    """
    from fastapi.responses import JSONResponse

    health_checker = get_health_checker(db_path, gguf_model_path)

    @app.get("/health/live")
    async def health_live():
        return JSONResponse(health_checker.check_live())

    @app.get("/health/ready")
    async def health_ready():
        result = health_checker.check_ready()
        status_code = 200 if result["all_ready"] else 503
        return JSONResponse(result, status_code=status_code)

    @app.get("/health/status")
    async def health_status():
        return JSONResponse(health_checker.check_status())

    logger.info("✅ Health probe routes registered: /health/live, /health/ready, /health/status")
