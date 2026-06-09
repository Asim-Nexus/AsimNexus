# Rollback Procedure

> **Applies to:** AsimNexus RC-1 (v1.1.0-rc.1)

---

## Overview

AsimNexus uses the [`backend/release.py`](../backend/release.py) system for release lifecycle management. Rollbacks are recorded in `deploy/release/rollback_log.jsonl`.

---

## Quick Rollback

### Step 1: List Available Releases

```python
from backend.release import list_releases

# List all releases for the docker target
releases = list_releases(target="docker")
for r in releases:
    print(f"{r['version']} — {'CURRENT' if r.get('is_current') else 'available'}")
```

### Step 2: Check Current Release

```python
from backend.release import current_release

current = current_release(target="docker")
print(current)
# Returns: {"version": "1.1.0-rc.1", "is_current": true, ...}
```

### Step 3: Rollback to a Previous Version

```python
from backend.release import record_rollback

# Record the rollback and update the current pointer
record_rollback(
    from_version="1.1.0-rc.1",
    to_version="<previous_stable_version>",
    target="docker"
)
```

### Step 4: Verify

```python
from backend.release import current_release

current = current_release(target="docker")
assert current["version"] == "<previous_stable_version>"
print(f"Rollback confirmed. Current: {current['version']}")
```

---

## CLI One-Liner

```bash
python -c "from backend.release import record_rollback; record_rollback(from_version='1.1.0-rc.1', to_version='<prev>', target='docker'); print('Rollback complete')"
```

---

## Git Rollback (Safety Net)

If the release system itself is corrupted:

```bash
# Find the last known good commit
git log --oneline -20

# Rollback to it
git reset --hard <last_good_commit_hash>

# Verify
python -c "from backend.release import current_release; print(current_release(target='docker'))"
```

---

## Rollback Log

All rollbacks are recorded in [`deploy/release/rollback_log.jsonl`](../deploy/release/rollback_log.jsonl) in append-only format:

```json
{"action": "rollback", "target": "docker", "from_version": "1.1.0-rc.1", "to_version": "1.0.0", "timestamp": "2026-06-07T16:00:00Z"}
```

---

## When to Rollback

Rollback when any of these occur after deployment:

1. **Critical test failure** — previously passing tests now fail
2. **API regression** — endpoints return 500 errors
3. **Security vulnerability** — discovered in newly deployed code
4. **Data corruption** — persistent state is corrupted
5. **Performance degradation** — >50% increase in p95 latency
