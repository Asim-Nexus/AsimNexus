"""
STATUS: REAL — Validation script for STATUS headers
Usage: python tools/check_status_labels.py
Checks for missing STATUS headers and overclaim words.
"""

import sys
from pathlib import Path

EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "node_modules", "media"}
EXCLUDE_FILES = {"check_status_labels.py"}  # skip self
REQUIRED_STATUS = {"STATUS: REAL", "STATUS: PARTIAL", "STATUS: CONCEPT", "STATUS: STUB"}
FORBIDDEN_WORDS = [
    "world-ready", "100% secure", "production-grade",
    "fully implemented", "supercomputer",
]

def check_file(filepath: Path) -> list:
    """Check a single Python file for STATUS header and forbidden words."""
    issues = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except UnicodeDecodeError:
        try:
            content = filepath.read_text(encoding="latin-1", errors="ignore")
        except Exception:
            return issues
    except Exception:
        return issues

    # Check for STATUS header
    has_status = any(s in content for s in REQUIRED_STATUS)
    if not has_status:
        issues.append(f"Missing STATUS header")

    # Check for forbidden words (case-insensitive)
    lower = content.lower()
    for word in FORBIDDEN_WORDS:
        if word.lower() in lower:
            issues.append(f"Forbidden word: '{word}'")

    return issues


def main():
    root = Path(__file__).resolve().parent.parent
    errors = []
    checked = 0

    for pyfile in root.rglob("*.py"):
        # Skip excluded directories and files
        if any(ex in str(pyfile) for ex in EXCLUDE_DIRS):
            continue
        if pyfile.name in EXCLUDE_FILES:
            continue
        # Skip empty __init__.py files
        if pyfile.name == "__init__.py" and pyfile.stat().st_size < 50:
            continue

        checked += 1
        file_issues = check_file(pyfile)
        for issue in file_issues:
            errors.append(f"{pyfile.relative_to(root)}: {issue}")

    print(f"Checked {checked} Python files")
    if errors:
        print(f"\nFound {len(errors)} issue(s):")
        for e in errors:
            print(f"  [FAIL] {e}")
        sys.exit(1)
    else:
        print("\n[PASS] All files have proper STATUS headers")
        print("[PASS] No forbidden words found")
        sys.exit(0)


if __name__ == "__main__":
    main()
