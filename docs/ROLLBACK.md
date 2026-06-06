# Rollback Procedure

> **Applies to:** AsimNexus RC-1 (`1.0.0+build42`) and later  
> **Last updated:** 2026-05-31  
> **System:** [`backend/release.py`](backend/release.py) — Release lifecycle manager

---

## Overview

AsimNexus has a built-in release lifecycle management system that supports:

- **Publishing** new releases
- **Listing** all recorded releases
- **Checking** the current active release
- **Setting** a specific release as current
- **Recording** rollback events with full audit trail

All release metadata is stored in:
- [`deploy/release/releases.json`](deploy/release/releases.json) — Release history
- [`deploy/release/rollback_log.jsonl`](deploy/release/rollback_log.jsonl) — Append-only rollback audit trail
- [`deploy/release/version.txt`](deploy/release/version.txt) — Current version string

---

## Quick Rollback

### Using Python

```python
from backend.release import record_rollback, current_release, list_releases

# Step 1: Check what's currently deployed
current = current_release(target="docker")
print(f"Current: {current['version']}")

# Step 2: List all available releases
releases = list_releases(target="docker")
for r in releases:
    marker = "← CURRENT" if r.get("is_current") else ""
    print(f"  {r['version']} (published: {r['published_at']}) {marker}")

# Step 3: Rollback to a previous version
record_rollback(
    from_version="1.0.0+build42",    # the version you're rolling back FROM
    to_version="0.9.0",              # the version you're rolling back TO
    target="docker"                   # deployment target
)

# Step 4: Verify
updated = current_release(target="docker")
print(f"Now current: {updated['version']}")
```

### Using CLI

```bash
# Check current
python -c "from backend.release import current_release; print(current_release(target='docker'))"

# List releases
python -c "from backend.release import list_releases; [print(r['version'], r.get('is_current','')) for r in list_releases(target='docker')]"

# Rollback
python -c "from backend.release import record_rollback; r=record_rollback(from_version='1.0.0+build42', to_version='0.9.0', target='docker'); print('Rollback recorded:', r)"

# Verify
python -c "from backend.release import current_release; print('Current:', current_release(target='docker')['version'])"
```

---

## Manual Rollback (Git)

If the automated release system is unavailable, use Git:

```bash
# Find the RC-1 commit hash
git log --oneline | grep "RC-1"

# Revert to previous stable commit
git revert HEAD  # or: git checkout <previous-stable-tag>

# Verify version file
cat deploy/release/version.txt
```

After Git rollback, update the release system:

```python
from backend.release import publish_release, set_current_release

# Record the rolled-back version as current
publish_release(
    version="<rolled-back-version>",
    target="docker",
    checksum="post-rollback-restore"
)
```

---

## Release Lifecycle API Reference

| Function | Description |
|----------|-------------|
| [`publish_release()`](backend/release.py:43) | Record a new release. Auto-sets as current for target. |
| [`list_releases()`](backend/release.py:74) | List all releases, optionally filtered by target. |
| [`current_release()`](backend/release.py:82) | Get the currently-active release for a target. |
| [`set_current_release()`](backend/release.py:96) | Manually mark a version as current for target. |
| [`record_rollback()`](backend/release.py:113) | Record a rollback + update current pointer + append to audit log. |

---

## Rollback Audit Trail

Every rollback is recorded in [`deploy/release/rollback_log.jsonl`](deploy/release/rollback_log.jsonl) as an append-only JSON line:

```json
{"action": "rollback", "target": "docker", "from_version": "1.0.0+build42", "to_version": "0.9.0", "timestamp": "2026-05-31T12:00:00.000000Z"}
```

To view the rollback history:

```python
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
log_file = BASE / "deploy" / "release" / "rollback_log.jsonl"
if log_file.exists():
    for line in log_file.read_text().strip().split("\n"):
        print(line)
```

---

## Safety Checks

Before rolling back:

1. **Verify the target version exists** in [`deploy/release/releases.json`](deploy/release/releases.json)
2. **Check data compatibility** — ensure the rolled-back version can read the current database schema
3. **Notify users** — rollback may cause temporary service interruption
4. **Test after rollback** — verify `/health` endpoint returns OK

---

## Related

- [`docs/RELEASE_PROCESS.md`](RELEASE_PROCESS.md) — How to publish new releases
- [`docs/RELEASE_NOTES_RC1.md`](RELEASE_NOTES_RC1.md) — RC-1 release notes
- [`backend/release.py`](backend/release.py) — Source code for the release manager
- [`backend/version.py`](backend/version.py) — Version information utilities
