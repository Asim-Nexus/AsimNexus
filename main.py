
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
AsimNexus — World OS Entry Point
=================================
One Kernel, Infinite Worlds.

Usage:
    python main.py                  # Start with defaults
    python main.py --offline        # Local LLM only
    python main.py --port 8080      # Custom port
    python main.py --no-frontend    # Backend only
"""
import asyncio
import logging
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

LOG_LEVEL = os.getenv("ASIM_LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("AsimNexus")


def parse_args():
    parser = argparse.ArgumentParser(description="AsimNexus World OS")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--offline", action="store_true", help="Use local LLM only")
    parser.add_argument("--no-frontend", action="store_true", help="Backend only mode")
    parser.add_argument("--dev", action="store_true", help="Development mode (hot reload)")
    return parser.parse_args()


async def start_backend(host: str, port: int, offline: bool, dev: bool):
    """Start AsimNexus backend — graceful degradation on missing deps."""
    logger.info("Starting AsimNexus backend...")

    # 1. Hardware detection
    try:
        from core.hardware_aware_processor import get_hardware_aware_processor
        hw = get_hardware_aware_processor()
        hw_status = hw.get_hardware_status()
        logger.info(f"Hardware: {hw_status}")
    except Exception as e:
        logger.warning(f"Hardware detection skipped: {e}")

    # 2. Core engine
    asim_instance = None
    try:
        from core.new_architecture_integration import NewASIMNEXUS
        asim_instance = NewASIMNEXUS()
        await asim_instance.initialize()
        logger.info("AsimNexus Core Engine ready")
    except Exception as e:
        logger.warning(f"Core engine partial init: {e}")

    # 3. Automation OS
    try:
        from core.automation_os import get_automation_os
        automation_os = get_automation_os()
        automation_os.initialize()
        logger.info("Automation OS ready")
    except Exception as e:
        logger.warning(f"Automation OS skipped: {e}")

    # 4. Universal API Bridge (connects to OpenAI, Google, Tesla, etc.)
    try:
        from core.mcp.api_bridge import get_api_bridge
        bridge = await get_api_bridge()
        providers = bridge.list_providers()
        logger.info(f"Universal API Bridge ready: {len(providers)} providers")
    except Exception as e:
        logger.warning(f"API Bridge skipped: {e}")

    # 5. Auto Discovery Service (network discovery)
    try:
        from core.network.auto_discovery import start_discovery
        node_id = f"asim-node-{os.getenv('USER', 'anonymous')}"
        discovery = await start_discovery(node_id=node_id, node_type="personal")
        logger.info(f"Auto Discovery started: {discovery.node_id}")
    except Exception as e:
        logger.warning(f"Auto Discovery skipped: {e}")

    # 6. Local LLM (offline GGUF models)
    try:
        from core.llm.local_llm import get_local_llm
        llm = await get_local_llm()
        status = llm.get_status()
        if status["available"]:
            logger.info(f"Local LLM ready: {status['current_model'] or 'no model loaded'}")
        else:
            logger.info("Local LLM not available (install llama-cpp-python)")
    except Exception as e:
        logger.warning(f"Local LLM skipped: {e}")

    # 7. API server
    try:
        from core.api_endpoints import app, set_asim_instance
        import uvicorn

        if asim_instance:
            set_asim_instance(asim_instance)

        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info",
            reload=dev,
        )
        server = uvicorn.Server(config)
        logger.info(f"API server starting at http://{host}:{port}")
        await server.serve()
    except ImportError:
        logger.error("uvicorn not installed. Run: pip install uvicorn fastapi")
        sys.exit(1)


def start_frontend(frontend_port: int = 3000):
    """Start React frontend in background."""
    import subprocess
    frontend_path = Path(__file__).parent / "frontend" / "react"
    if not frontend_path.exists():
        logger.warning("Frontend directory not found — skipping")
        return None

    logger.info(f"Starting frontend at http://localhost:{frontend_port}")
    proc = subprocess.Popen(
        ["npm", "start"],
        cwd=str(frontend_path),
        env={**os.environ, "PORT": str(frontend_port), "BROWSER": "none"},
    )
    return proc


async def main():
    args = parse_args()

    logger.info("=" * 50)
    logger.info("  AsimNexus — World OS")
    logger.info("  One Kernel, Infinite Worlds")
    logger.info("=" * 50)
    logger.info(f"Mode: {'OFFLINE' if args.offline else 'ONLINE'}")
    logger.info(f"Port: {args.port}")

    if args.offline:
        os.environ["ASIM_OFFLINE"] = "true"

    # Start frontend in background (unless disabled)
    frontend_proc = None
    if not args.no_frontend:
        frontend_proc = start_frontend()

    try:
        await start_backend(
            host=args.host,
            port=args.port,
            offline=args.offline,
            dev=args.dev,
        )
    except KeyboardInterrupt:
        logger.info("Shutting down AsimNexus...")
    finally:
        if frontend_proc:
            frontend_proc.terminate()
        logger.info("AsimNexus stopped.")


if __name__ == "__main__":
    asyncio.run(main())
