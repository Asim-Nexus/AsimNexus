"""
Self-Awareness Routes
=====================
API endpoints for AsimNexus self-awareness system — introspection, knowledge
queries, codebase scanning, and self-building capabilities.

These routes allow AsimNexus to understand and modify itself through a REST API.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from core.self_awareness import (
    CodebaseScanner,
    SelfBuilder,
    SelfKnowledge,
    get_auto_builder,
    get_builder,
    get_knowledge,
    get_scanner,
)
from core.self_awareness.codebase_scanner import ModuleInfo, RouteInfo, ScanResult
from core.self_awareness.gap_analyzer import GapAnalyzer, Gap
from routes.response import ok, error

logger = logging.getLogger(__name__)

router = APIRouter()


# ──────────────────────────────────────────────
#  Knowledge / Introspection
# ──────────────────────────────────────────────


@router.get("/api/self/knowledge/summary")
async def self_knowledge_summary():
    """Get a summary of AsimNexus's self-knowledge."""
    try:
        knowledge = get_knowledge()
        summary = knowledge.get_summary()
        return ok(data={
            "summary": {
                "total_modules": summary.total_modules,
                "total_packages": summary.total_packages,
                "total_classes": summary.total_classes,
                "total_functions": summary.total_functions,
                "total_routes": summary.total_routes,
                "total_lines": summary.total_lines,
                "total_issues": summary.total_issues,
                "open_issues": summary.open_issues,
                "last_scan": summary.last_scan,
                "last_updated": summary.last_updated,
            },
        })
    except Exception as e:
        logger.exception("Error getting knowledge summary")
        return error(str(e), status_code=500)


@router.get("/api/self/knowledge/modules")
async def self_list_modules(
    search: Optional[str] = Query(None, description="Filter modules by name pattern"),
    limit: int = Query(50, description="Max modules to return"),
    offset: int = Query(0, description="Pagination offset"),
):
    """List all known modules with metadata."""
    try:
        knowledge = get_knowledge()
        modules = knowledge.get_all_modules()

        # Filter by search pattern
        if search:
            search_lower = search.lower()
            modules = {p: m for p, m in modules.items() if search_lower in p.lower()}

        # Sort by package name
        sorted_packages = sorted(modules.keys())
        page = sorted_packages[offset:offset + limit]

        result = []
        for pkg in page:
            mod = modules[pkg]
            result.append({
                "package": mod.package,
                "filepath": mod.filepath,
                "lineno_count": mod.lineno_count,
                "class_count": len(mod.classes),
                "function_count": len(mod.functions),
                "route_count": len(mod.routes),
                "has_test": mod.has_test_file,
                "error_count": len(mod.errors),
            })

        return ok(data={
            "total": len(modules),
            "returned": len(result),
            "offset": offset,
            "modules": result,
        })
    except Exception as e:
        logger.exception("Error listing modules")
        return error(str(e), status_code=500)


@router.get("/api/self/knowledge/modules/{package:path}")
async def self_get_module(package: str):
    """Get detailed information about a specific module."""
    try:
        knowledge = get_knowledge()
        mod = knowledge.get_module(package)
        if not mod:
            return error(f"Module not found: {package}", status_code=404)

        return ok(data={
            "module": {
                "package": mod.package,
                "filepath": mod.filepath,
                "docstring": mod.docstring,
                "lineno_count": mod.lineno_count,
                "classes": [
                    {
                        "name": c.name,
                        "lineno": c.lineno,
                        "bases": c.bases,
                        "method_count": len(c.methods),
                        "docstring": c.docstring,
                    }
                    for c in mod.classes
                ],
                "functions": [
                    {
                        "name": f.name,
                        "lineno": f.lineno,
                        "is_async": f.is_async,
                        "is_method": f.is_method,
                        "args": f.args,
                        "return_annotation": f.return_annotation,
                    }
                    for f in mod.functions
                ],
                "routes": [
                    {
                        "method": r.method,
                        "path": r.path,
                        "func_name": r.func_name,
                        "lineno": r.lineno,
                        "summary": r.summary,
                    }
                    for r in mod.routes
                ],
                "imports": [
                    {
                        "module": i.module,
                        "names": i.names,
                        "lineno": i.lineno,
                    }
                    for i in mod.imports
                ],
                "has_test": mod.has_test_file,
                "test_filepath": mod.test_filepath,
                "errors": mod.errors,
            },
        })
    except Exception as e:
        logger.exception("Error getting module %s", package)
        return error(str(e), status_code=500)


@router.get("/api/self/knowledge/routes")
async def self_list_routes(
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    search: Optional[str] = Query(None, description="Search in route paths"),
    limit: int = Query(100, description="Max routes to return"),
):
    """List all registered API routes."""
    try:
        knowledge = get_knowledge()
        routes = knowledge.get_all_routes_flat()

        if method:
            routes = [r for r in routes if r.method.upper() == method.upper()]
        if search:
            search_lower = search.lower()
            routes = [r for r in routes if search_lower in r.path.lower()]

        # Sort by method then path
        routes.sort(key=lambda r: (r.method, r.path))

        return ok(data={
            "total": len(routes),
            "returned": min(len(routes), limit),
            "routes": [
                {
                    "method": r.method,
                    "path": r.path,
                    "func_name": r.func_name,
                    "lineno": r.lineno,
                    "summary": r.summary,
                }
                for r in routes[:limit]
            ],
        })
    except Exception as e:
        logger.exception("Error listing routes")
        return error(str(e), status_code=500)


@router.get("/api/self/knowledge/dependencies/{package:path}")
async def self_get_dependencies(package: str, reverse: bool = False):
    """Get dependency information for a module."""
    try:
        knowledge = get_knowledge()
        if reverse:
            deps = knowledge.get_dependents(package)
            label = "dependents"
        else:
            deps = knowledge.get_dependencies(package)
            label = "dependencies"

        return ok(data={
            "package": package,
            label: sorted(deps),
            "count": len(deps),
        })
    except Exception as e:
        logger.exception("Error getting dependencies for %s", package)
        return error(str(e), status_code=500)


@router.get("/api/self/knowledge/issues")
async def self_list_issues(
    module: Optional[str] = Query(None, description="Filter by module"),
    status: Optional[str] = Query(None, description="Filter by status (open/acknowledged/fixed/wontfix)"),
    issue_type: Optional[str] = Query(None, description="Filter by type (bug/warning/improvement/todo/bare_except)"),
    limit: int = Query(50, description="Max issues to return"),
):
    """List known issues in the codebase."""
    try:
        knowledge = get_knowledge()
        issues = knowledge.get_issues(module=module, status=status, issue_type=issue_type)

        return ok(data={
            "total": len(issues),
            "returned": min(len(issues), limit),
            "issues": [
                {
                    "issue_id": i.issue_id,
                    "module": i.module,
                    "issue_type": i.issue_type,
                    "description": i.description,
                    "lineno": i.lineno,
                    "severity": i.severity,
                    "status": i.status,
                    "timestamp": i.timestamp,
                }
                for i in issues[:limit]
            ],
        })
    except Exception as e:
        logger.exception("Error listing issues")
        return error(str(e), status_code=500)


# ──────────────────────────────────────────────
#  Scanning
# ──────────────────────────────────────────────


@router.post("/api/self/scan")
async def self_scan(
    subdirs: Optional[List[str]] = Body(None, description="Subdirectories to scan (e.g. ['core', 'routes'])"),
):
    """Trigger a codebase scan to refresh self-knowledge."""
    try:
        knowledge = get_knowledge()
        result = knowledge.refresh()

        return ok(data={
            "scan_result": {
                "total_files": result.total_files,
                "total_lines": result.total_lines,
                "total_classes": result.total_classes,
                "total_functions": result.total_functions,
                "total_routes": result.total_routes,
                "errors": result.errors[:20],  # Limit error reporting
            },
            "message": f"Scan complete: {result.total_files} files, {result.total_routes} routes",
        })
    except Exception as e:
        logger.exception("Error during codebase scan")
        return error(str(e), status_code=500)


@router.get("/api/self/scan/status")
async def self_scan_status():
    """Get the status of the last codebase scan."""
    try:
        knowledge = get_knowledge()
        summary = knowledge.get_summary()
        return ok(data={
            "last_scan": summary.last_scan,
            "last_updated": summary.last_updated,
            "has_been_scanned": summary.last_scan is not None,
        })
    except Exception as e:
        logger.exception("Error getting scan status")
        return error(str(e), status_code=500)


# ──────────────────────────────────────────────
#  Self-Building
# ──────────────────────────────────────────────


@router.post("/api/self/build/generate-route")
async def self_generate_route(
    module_name: str = Body(..., description="Route module name (e.g. 'health')"),
    routes: List[Dict[str, str]] = Body(..., description="List of route definitions"),
):
    """Generate a new route module."""
    try:
        builder = get_builder()
        result = builder.generate_route_module(module_name, routes)
        if not result.success:
            return error(result.error, status_code=400)
        return ok(data={
            "action": {
                "action_id": result.actions[0].action_id,
                "target_file": result.actions[0].target_file,
                "description": result.actions[0].description,
            },
            "summary": result.summary,
        })
    except Exception as e:
        logger.exception("Error generating route module")
        return error(str(e), status_code=500)


@router.post("/api/self/build/generate-test")
async def self_generate_test(
    source_module: str = Body(..., description="Dotted module path (e.g. 'core.security.auth_middleware')"),
    test_type: str = Body("unit", description="Test type: 'unit' or 'real'"),
):
    """Generate a test file for a source module."""
    try:
        builder = get_builder()
        result = builder.generate_test_file(source_module, test_type)
        if not result.success:
            return error(result.error, status_code=400)
        return ok(data={
            "action": {
                "action_id": result.actions[0].action_id,
                "target_file": result.actions[0].target_file,
                "description": result.actions[0].description,
            },
            "summary": result.summary,
        })
    except Exception as e:
        logger.exception("Error generating test file")
        return error(str(e), status_code=500)


@router.post("/api/self/build/fix-imports")
async def self_fix_imports(
    module_package: str = Body(..., description="Dotted module path to fix imports for"),
):
    """Fix missing imports in a module."""
    try:
        builder = get_builder()
        result = builder.fix_missing_imports(module_package)
        if not result.success:
            return error(result.error, status_code=400)
        return ok(data={
            "actions": [
                {
                    "action_id": a.action_id,
                    "target_file": a.target_file,
                    "description": a.description,
                }
                for a in result.actions
            ],
            "summary": result.summary,
        })
    except Exception as e:
        logger.exception("Error fixing imports")
        return error(str(e), status_code=500)


@router.post("/api/self/build/apply-patch")
async def self_apply_patch(
    filepath: str = Body(..., description="Path to the file to patch"),
    search: str = Body(..., description="Exact text to search for"),
    replace: str = Body(..., description="Text to replace with"),
    description: str = Body("", description="Human-readable description"),
):
    """Apply a search/replace patch to a file."""
    try:
        builder = get_builder()
        result = builder.apply_patch(filepath, search, replace, description)
        if not result.success:
            return error(result.error, status_code=400)
        return ok(data={
            "action": {
                "action_id": result.actions[0].action_id,
                "target_file": result.actions[0].target_file,
                "description": result.actions[0].description,
            },
            "summary": result.summary,
        })
    except Exception as e:
        logger.exception("Error applying patch")
        return error(str(e), status_code=500)


@router.post("/api/self/build/rollback/{action_id}")
async def self_rollback(action_id: str):
    """Rollback a previously applied build action."""
    try:
        builder = get_builder()
        result = builder.rollback(action_id)
        if not result.success:
            return error(result.error, status_code=400)
        return ok(data={
            "action": {
                "action_id": result.actions[0].action_id,
                "target_file": result.actions[0].target_file,
                "description": result.actions[0].description,
            },
            "summary": result.summary,
        })
    except Exception as e:
        logger.exception("Error rolling back action")
        return error(str(e), status_code=500)


@router.get("/api/self/build/history")
async def self_build_history(limit: int = Query(50, description="Max history entries")):
    """Get the build action history."""
    try:
        builder = get_builder()
        history = builder.get_action_history(limit)
        return ok(data={
            "total": len(history),
            "actions": [
                {
                    "action_id": a.action_id,
                    "action_type": a.action_type,
                    "target_file": a.target_file,
                    "description": a.description,
                    "status": a.status,
                    "timestamp": a.timestamp,
                    "error": a.error,
                }
                for a in history
            ],
        })
    except Exception as e:
        logger.exception("Error getting build history")
        return error(str(e), status_code=500)


@router.get("/api/self/build/stats")
async def self_build_stats():
    """Get builder statistics."""
    try:
        builder = get_builder()
        stats = builder.get_stats()
        return ok(data={"stats": stats})
    except Exception as e:
        logger.exception("Error getting builder stats")
        return error(str(e), status_code=500)


# ──────────────────────────────────────────────
#  Comprehensive Self-Report
# ──────────────────────────────────────────────


@router.get("/api/self/report")
async def self_report():
    """Get a comprehensive self-report about AsimNexus."""
    try:
        knowledge = get_knowledge()
        builder = get_builder()
        summary = knowledge.get_summary()
        build_stats = builder.get_stats()

        # Get module counts by category
        modules = knowledge.get_all_modules()
        core_modules = [p for p in modules if p.startswith("core")]
        route_modules = [p for p in modules if p.startswith("routes")]
        test_modules = [p for p in modules if "test" in p.lower()]

        return ok(data={
            "identity": {
                "name": "AsimNexus",
                "version": "1.0.0-rc2",
                "description": "Universal AI Operating System (World OS)",
            },
            "codebase": {
                "total_modules": summary.total_modules,
                "total_lines": summary.total_lines,
                "total_classes": summary.total_classes,
                "total_functions": summary.total_functions,
                "total_routes": summary.total_routes,
                "core_modules": len(core_modules),
                "route_modules": len(route_modules),
                "test_modules": len(test_modules),
            },
            "health": {
                "open_issues": summary.open_issues,
                "total_issues": summary.total_issues,
                "build_actions_applied": build_stats.get("applied", 0),
                "build_actions_rolled_back": build_stats.get("rolled_back", 0),
            },
            "last_scan": summary.last_scan,
            "last_updated": summary.last_updated,
        })
    except Exception as e:
        logger.exception("Error generating self-report")
        return error(str(e), status_code=500)


# ──────────────────────────────────────────────
#  AutoBuilder / Self-Building Loop
# ──────────────────────────────────────────────


@router.get("/api/self/build/cycles")
async def self_build_cycles(limit: int = Query(10, description="Max cycles to return")):
    """Get recent AutoBuilder build cycles with full status."""
    try:
        auto_builder = get_auto_builder()
        cycles = auto_builder.get_cycle_history(limit=limit)
        return ok(data={
            "cycles": [c.to_dict() for c in cycles],
            "count": len(cycles),
        })
    except Exception as e:
        logger.exception("Error getting build cycles")
        return error(str(e), status_code=500)


@router.get("/api/self/build/cycle/status")
async def self_build_cycle_status():
    """Get the current AutoBuilder status and latest cycle info."""
    try:
        auto_builder = get_auto_builder()
        stats = auto_builder.get_stats()
        cycles = auto_builder.get_cycle_history(limit=1)
        latest_cycle = cycles[0].to_dict() if cycles else None
        return ok(data={
            "stats": stats,
            "latest_cycle": latest_cycle,
            "auto_deploy_enabled": getattr(auto_builder, "_auto_deploy", False),
        })
    except Exception as e:
        logger.exception("Error getting build cycle status")
        return error(str(e), status_code=500)


@router.post("/api/self/build/run-cycle")
async def self_run_build_cycle():
    """Manually trigger a full self-building cycle (scan → analyze → build → test → deploy)."""
    try:
        auto_builder = get_auto_builder()
        cycle = await auto_builder.run_cycle()
        return ok(data={
            "cycle": cycle.to_dict(),
            "message": f"Build cycle {cycle.cycle_id} completed with status: {cycle.status}",
        })
    except Exception as e:
        logger.exception("Error running build cycle")
        return error(str(e), status_code=500)


# ──────────────────────────────────────────────
#  Gap Analysis
# ──────────────────────────────────────────────


@router.get("/api/self/gaps")
async def self_list_gaps(
    category: Optional[str] = Query(None, description="Filter by gap category"),
    min_priority: float = Query(0.0, description="Minimum priority score (0-1)"),
    max_gaps: int = Query(50, description="Maximum gaps to return"),
):
    """Run gap analysis and return prioritized gaps."""
    try:
        from core.self_awareness.gap_analyzer import GapAnalyzer
        scanner = get_scanner()
        knowledge = get_knowledge()
        analyzer = GapAnalyzer(scanner, knowledge)
        result = analyzer.analyze(scanner, knowledge)

        gaps = [g.to_dict() for g in result.gaps]
        # Filter by category
        if category:
            gaps = [g for g in gaps if g.get("category") == category]
        # Filter by priority
        gaps = [g for g in gaps if g.get("priority_score", 0) >= min_priority]
        # Sort by priority (highest first)
        gaps.sort(key=lambda g: g.get("priority_score", 0), reverse=True)
        # Limit
        gaps = gaps[:max_gaps]

        return ok(data={
            "gaps": gaps,
            "total_found": len(result.gaps),
            "returned": len(gaps),
            "categories": result.by_category(),
            "summary": result.to_dict().get("summary", {}),
        })
    except Exception as e:
        logger.exception("Error running gap analysis")
        return error(str(e), status_code=500)


@router.get("/api/self/gaps/categories")
async def self_gap_categories():
    """Get all gap categories with counts."""
    try:
        from core.self_awareness.gap_analyzer import GapAnalyzer
        scanner = get_scanner()
        knowledge = get_knowledge()
        analyzer = GapAnalyzer(scanner, knowledge)
        result = analyzer.analyze(scanner, knowledge)
        categories = result.by_category()
        return ok(data={
            "categories": {k: len(v) for k, v in categories.items()},
            "total": len(result.gaps),
        })
    except Exception as e:
        logger.exception("Error getting gap categories")
        return error(str(e), status_code=500)


# ──────────────────────────────────────────────
#  Deployment Status
# ──────────────────────────────────────────────


@router.get("/api/self/deploy/status")
async def self_deploy_status():
    """Get deployment status from the latest build cycle."""
    try:
        auto_builder = get_auto_builder()
        cycles = auto_builder.get_cycle_history(limit=5)
        deploy_info = []
        for c in cycles:
            if c.deployed:
                deploy_info.append({
                    "cycle_id": c.cycle_id,
                    "status": c.status,
                    "deploy_target": c.deploy_target,
                    "deploy_url": c.deploy_url,
                    "smoke_tests_passed": c.smoke_tests_passed,
                    "smoke_tests_total": c.smoke_tests_total,
                    "completed_at": c.completed_at,
                })
        return ok(data={
            "deployments": deploy_info,
            "total_deployments": len(deploy_info),
            "latest": deploy_info[0] if deploy_info else None,
        })
    except Exception as e:
        logger.exception("Error getting deploy status")
        return error(str(e), status_code=500)


# ── Self-Awareness Health ──────────────────────


@router.get("/api/self/health")
async def self_health():
    """Get the health status of all self-awareness components.

    Returns:
      - status: Overall health status (healthy/degraded/unhealthy)
      - components: Status of each self-awareness subsystem
      - timestamp: Current timestamp
    """
    try:
        from core.self_awareness import (
            get_scanner,
            get_knowledge,
            get_builder,
            get_gap_analyzer,
            get_auto_builder,
        )
        from core.self_awareness.evolution_bridge import get_bridge

        components = {}
        overall_status = "healthy"

        # Scanner health
        try:
            scanner = get_scanner()
            scan_result = scanner.scan(subdirs=["core"])
            components["scanner"] = {
                "status": "healthy",
                "modules_scanned": len(scan_result.modules) if scan_result else 0,
            }
        except Exception as e:
            components["scanner"] = {"status": "unhealthy", "error": str(e)}
            overall_status = "degraded"

        # Knowledge health
        try:
            knowledge = get_knowledge()
            summary = knowledge.get_summary()
            components["knowledge"] = {
                "status": "healthy",
                "total_modules": summary.total_modules,
                "total_routes": summary.total_routes,
                "total_issues": summary.total_issues,
            }
        except Exception as e:
            components["knowledge"] = {"status": "unhealthy", "error": str(e)}
            overall_status = "degraded"

        # Builder health
        try:
            builder = get_builder()
            stats = builder.get_stats()
            components["builder"] = {
                "status": "healthy",
                "total_actions": stats.get("total_actions", 0),
                "success_rate": stats.get("success_rate", 0),
            }
        except Exception as e:
            components["builder"] = {"status": "unhealthy", "error": str(e)}
            overall_status = "degraded"

        # Gap Analyzer health
        try:
            analyzer = get_gap_analyzer()
            result = analyzer.analyze()
            components["gap_analyzer"] = {
                "status": "healthy",
                "total_gaps": len(result.gaps),
                "categories": list(result.by_category().keys()),
            }
        except Exception as e:
            components["gap_analyzer"] = {"status": "unhealthy", "error": str(e)}
            overall_status = "degraded"

        # AutoBuilder health
        try:
            auto_builder = get_auto_builder()
            auto_stats = auto_builder.get_stats()
            components["auto_builder"] = {
                "status": "healthy",
                "total_cycles": auto_stats.get("total_cycles", 0),
                "last_cycle_status": auto_stats.get("last_cycle_status", "never_run"),
            }
        except Exception as e:
            components["auto_builder"] = {"status": "unhealthy", "error": str(e)}
            overall_status = "degraded"

        # Evolution Bridge health
        try:
            bridge = get_bridge()
            bridge_stats = bridge.get_stats()
            components["evolution_bridge"] = {
                "status": "healthy",
                "total_actions": bridge_stats.get("total_actions", 0),
            }
        except Exception as e:
            components["evolution_bridge"] = {"status": "unhealthy", "error": str(e)}
            overall_status = "degraded"

        return ok(data={
            "status": overall_status,
            "components": components,
        })
    except Exception as e:
        logger.exception("Self-awareness health check failed")
        return error(str(e))


# ── Initialization ─────────────────────────────


def init_self_awareness(app_globals: dict) -> None:
    """Initialize the self-awareness module."""
    logger.info("Initialized self-awareness routes")
    # Optionally trigger a background scan on startup
    # This is commented out to avoid slow startup — call POST /api/self/scan manually
    # or set ASIM_AUTO_SCAN=1 environment variable
    import os as _os
    if _os.getenv("ASIM_AUTO_SCAN", "0") == "1":
        try:
            knowledge = get_knowledge()
            knowledge.refresh()
            logger.info("Auto-scan completed on startup")
        except Exception as e:
            logger.warning("Auto-scan failed on startup: %s", e)
