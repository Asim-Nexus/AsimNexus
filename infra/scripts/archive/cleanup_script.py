#!/usr/bin/env python3
"""
STATUS: REAL — Maintenance script

ASIMNEXUS Codebase Cleanup Script
Removes duplicate and legacy files safely
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Base directory
BASE_DIR = Path("c:/AsimNexus")

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def remove_file(filepath):
    """Safely remove a file"""
    try:
        full_path = BASE_DIR / filepath
        if full_path.exists():
            full_path.unlink()
            log(f"✅ Removed: {filepath}")
            return True
        else:
            log(f"⚠️ Not found: {filepath}")
            return False
    except Exception as e:
        log(f"❌ Error removing {filepath}: {e}")
        return False

def remove_directory(dirpath):
    """Safely remove a directory"""
    try:
        full_path = BASE_DIR / dirpath
        if full_path.exists() and full_path.is_dir():
            shutil.rmtree(full_path)
            log(f"✅ Removed directory: {dirpath}")
            return True
        else:
            log(f"⚠️ Directory not found: {dirpath}")
            return False
    except Exception as e:
        log(f"❌ Error removing directory {dirpath}: {e}")
        return False

def main():
    log("Starting ASIMNEXUS Cleanup...")
    log("=" * 60)
    
    removed_count = 0
    
    # Phase 1: Remove old orchestrators
    log("\n📦 Phase 1: Removing old orchestrators...")
    orchestrators = [
        "core/orchestrator.py",
        "core/unified_orchestrator.py", 
        "core/agents/multi_agent_orchestrator.py",
        "core/world_os_orchestrator.py",
        "core/job_orchestrator.py",
        "core/master_orchestrator_tools.py",
    ]
    
    for file in orchestrators:
        if remove_file(file):
            removed_count += 1
    
    # Phase 2: Remove old routers
    log("\n🌐 Phase 2: Removing old routers...")
    routers = [
        "core/function_calling/tool_router.py",
        "core/context_router.py",
    ]
    
    for file in routers:
        if remove_file(file):
            removed_count += 1
    
    # Phase 3: Remove 15 CEO clones
    log("\n🤖 Phase 3: Removing 15 CEO clone agents...")
    clones = [
        "core/agents/clones/ai_ml_clone.py",
        "core/agents/clones/ceo_clone.py",
        "core/agents/clones/cfo_clone.py",
        "core/agents/clones/cmo_clone.py",
        "core/agents/clones/coo_clone.py",
        "core/agents/clones/cto_clone.py",
        "core/agents/clones/data_clone.py",
        "core/agents/clones/devops_clone.py",
        "core/agents/clones/frontend_clone.py",
        "core/agents/clones/hr_clone.py",
        "core/agents/clones/innovation_clone.py",
        "core/agents/clones/legal_clone.py",
        "core/agents/clones/nepal_clone.py",
        "core/agents/clones/security_clone.py",
        "core/agents/clones/support_clone.py",
    ]
    
    for file in clones:
        if remove_file(file):
            removed_count += 1
    
    # Remove empty clones directory
    remove_directory("core/agents/clones")
    
    # Phase 4: Remove legacy agent systems
    log("\n🔧 Phase 4: Removing legacy agent systems...")
    if remove_file("agents/unified_agent_system.py"):
        removed_count += 1
    
    # Phase 5: Remove legacy folders
    log("\n📁 Phase 5: Removing legacy folders...")
    legacy_folders = [
        "core/multi_agent",
        "core/worker_agents", 
        "core/saga",
        "core/agent_coordination",
    ]
    
    for folder in legacy_folders:
        remove_directory(folder)
    
    # Phase 6: Remove old multi_agent_orchestrator_v2
    log("\n📦 Phase 6: Removing v2 orchestrator...")
    if remove_file("core/multi_agent/multi_agent_orchestrator_v2.py"):
        removed_count += 1
    
    # Summary
    log("\n" + "=" * 60)
    log(f"Cleanup complete!")
    log(f"Total items processed: {removed_count}")
    log(f"Timestamp: {datetime.now().isoformat()}")
    log("\n⚠️  IMPORTANT:")
    log("1. Review main.py for old imports")
    log("2. Update asimnexus_unified_server.py references")
    log("3. Run tests to verify: pytest tests/ -v")
    log("4. Commit changes: git add -A && git commit -m \"Cleanup: Removed {removed_count} legacy files\"")

if __name__ == "__main__":
    main()
