"""
STATUS: REAL — Batch labeling script for remaining ~1250 Python files
Usage: python tools/batch_label.py [--dry-run]
"""

import argparse
import re
from pathlib import Path

EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "node_modules", "media", "archive"}
STATUS_HEADER = re.compile(r'STATUS:\s*(REAL|PARTIAL|CONCEPT)', re.IGNORECASE)

# Batch classification rules (heuristic-based)
CLASSIFICATION_RULES = [
    # REAL: Production code with backend wiring, tests, or real logic
    ("REAL", [
        r'from fastapi|from starlette|@app\.(get|post|put|delete)',
        r'class.*Test.*:\s*\n|def test_|pytest\.',
        r'websockets\.(serve|connect)',
        r'DeltaTEngine|DharmaVeto|DreamingEngine|AsimBrain',
        r'Pedersen|Schnorr|commit\(.*blinding',
    ]),
    # PARTIAL: Framework/skeleton with simulation noted
    ("PARTIAL", [
        r'asyncio\.sleep\(.*simulate|# simulate|# TODO.*real',
        r'class.*Router|class.*Manager.*:|def route_|def connect_',
        r'placeholder|stub|mock|fake',
        r'CONFIG|settings|\.yaml|\.json.*config',
    ]),
    # CONCEPT: Design docs, diagrams, no execution logic
    ("CONCEPT", [
        r'diagram|architecture|vision|future|roadmap',
        r'would be|should be|could be|in production',
        r'class.*Enum|class.*Dataclass.*:\s*\n.*pass',
    ]),
    # STUB: Empty or minimal placeholder
    ("STUB", [
        r'^\s*(pass|\.\.\.|# TODO)\s*$',
        r'def .*\(\):\s*\n\s*pass',
    ]),
]

# Known overrides (file path -> status)
KNOWN_OVERRIDES = {
    "simple_backend.py": "REAL",
    "core/dharma/dharma_veto.py": "REAL",
    "core/dharma/delta_t_engine.py": "REAL",
    "core/dreaming/dreaming_engine.py": "REAL",
    "core/asim_brain.py": "REAL",
    "core/security/bulletproof_zkp.py": "PARTIAL",
    "mesh/mesh_routing_agent.py": "PARTIAL",
    "mesh/mesh_routing_agent_v2.py": "PARTIAL",
    "core/mesh/p2p_node.py": "PARTIAL",
    "core/kernel/microkernel.py": "CONCEPT",
    "core/depin/depin_bridge.py": "CONCEPT",
    "core/sovereign_kernel.py": "CONCEPT",
}


def classify_file(filepath: Path) -> str:
    """Heuristic classification of a Python file."""
    relpath = str(filepath).replace("\\", "/")

    # Check known overrides first
    for pattern, status in KNOWN_OVERRIDES.items():
        if pattern in relpath:
            return status

    # Check if already labeled
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return "UNKNOWN"

    if STATUS_HEADER.search(content):
        return "ALREADY_LABELED"

    # Apply heuristic rules
    for status, patterns in CLASSIFICATION_RULES:
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return status

    # Default based on size and location
    size = filepath.stat().st_size
    if size < 200:
        return "STUB"
    if "test" in relpath.lower():
        return "REAL"  # Test files are real
    if "config" in relpath.lower() or "settings" in relpath.lower():
        return "PARTIAL"
    if "docs" in relpath.lower() or "vision" in relpath.lower():
        return "CONCEPT"

    return "PARTIAL"  # Default: safer to under-claim


def add_status_header(filepath: Path, status: str, dry_run: bool = True):
    """Add STATUS header to a Python file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    if STATUS_HEADER.search(content):
        return False  # Already labeled

    # Find the docstring or first line
    lines = content.split('\n')
    insert_idx = 0

    # Skip shebang
    if lines and lines[0].startswith('#!'):
        insert_idx = 1

    # Skip blank lines after shebang
    while insert_idx < len(lines) and not lines[insert_idx].strip():
        insert_idx += 1

    # Build status comment
    status_line = f'"""\nSTATUS: {status} — Auto-labeled by batch_label.py\n"""\n\n'

    new_content = '\n'.join(lines[:insert_idx]) + '\n' + status_line + '\n'.join(lines[insert_idx:])

    if not dry_run:
        filepath.write_text(new_content, encoding="utf-8")

    return True


def main():
    parser = argparse.ArgumentParser(description="Batch label Python files with STATUS")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--apply", action="store_true", help="Actually write STATUS headers")
    args = parser.parse_args()

    dry_run = not args.apply
    root = Path(__file__).resolve().parent.parent

    stats = {"REAL": 0, "PARTIAL": 0, "CONCEPT": 0, "STUB": 0, "ALREADY_LABELED": 0, "UNKNOWN": 0}
    to_label = []

    for pyfile in root.rglob("*.py"):
        if any(ex in str(pyfile) for ex in EXCLUDE_DIRS):
            continue
        if pyfile.stat().st_size < 10:
            continue

        status = classify_file(pyfile)
        stats[status] = stats.get(status, 0) + 1

        if status not in ("ALREADY_LABELED", "UNKNOWN"):
            to_label.append((pyfile, status))

    print("=" * 60)
    print("BATCH LABELING REPORT")
    print("=" * 60)
    for status, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {status:20s}: {count:4d} files")
    print(f"\n  TOTAL: {sum(stats.values())} files")
    print(f"  TO LABEL: {len(to_label)} files")

    if dry_run:
        print("\n  [DRY RUN] No files modified. Use --apply to write headers.")
        # Show sample
        print("\n  Sample classifications:")
        for pyfile, status in to_label[:10]:
            print(f"    {status:10s} {pyfile.relative_to(root)}")
    else:
        applied = 0
        for pyfile, status in to_label:
            if add_status_header(pyfile, status, dry_run=False):
                applied += 1
        print(f"\n  [APPLIED] {applied} files updated with STATUS headers.")


if __name__ == "__main__":
    main()
