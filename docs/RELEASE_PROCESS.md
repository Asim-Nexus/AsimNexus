# Release Process

> **Applies to:** AsimNexus RC-1 (v1.1.0-rc.1)

---

## Overview

AsimNexus releases are managed via [`backend/release.py`](../backend/release.py). Each release is recorded in [`deploy/release/releases.json`](../deploy/release/releases.json) with version, target, checksum, and timestamp.

---

## Creating a New Release

### Step 1: Update Version

Edit [`deploy/release/version.txt`](../deploy/release/version.txt):

```
1.1.0-rc.1
```

### Step 2: Publish Release

```python
from backend.release import publish_release

publish_release(
    version="1.1.0-rc.1",
    target="docker",
    checksum="<sha256_of_artifact>"
)
```

### Step 3: Set as Current

```python
from backend.release import set_current_release

set_current_release(
    version="1.1.0-rc.1",
    target="docker"
)
```

### Step 4: Verify

```python
from backend.release import current_release

current = current_release(target="docker")
assert current["version"] == "1.1.0-rc.1"
assert current["is_current"] == True
print(f"Release {current['version']} is current")
```

---

## CLI One-Liner

```bash
python -c "
from backend.release import publish_release, set_current_release;
r = publish_release(version='1.1.0-rc.1', target='docker', checksum='rc-1-freeze');
print('Published:', r);
set_current_release(version='1.1.0-rc.1', target='docker');
from backend.release import current_release;
print('Current:', current_release(target='docker'))
"
```

---

## Release Checklist

- [ ] Version bumped in `deploy/release/version.txt`
- [ ] Release published via `publish_release()`
- [ ] Release set as current via `set_current_release()`
- [ ] Release notes written (see [`docs/RELEASE_NOTES_RC1.md`](../docs/RELEASE_NOTES_RC1.md))
- [ ] Rollback path documented (see [`docs/ROLLBACK.md`](ROLLBACK.md))
- [ ] Full test suite passes
- [ ] STATUS.md frozen (see [`docs/STATUS.md`](../docs/STATUS.md))

---

## Listing Releases

```python
from backend.release import list_releases

# All releases
all_releases = list_releases()

# Filtered by target
docker_releases = list_releases(target="docker")
```

---

## Version Schema

Versions follow a modified semver:

| Pattern | Example | Meaning |
|---------|---------|---------|
| `X.Y.Z-dev` | `1.1.0-dev` | Development build |
| `X.Y.Z-rc.N` | `1.1.0-rc.1` | Release candidate N |
| `X.Y.Z` | `1.1.0` | Stable release |
| `X.Y.Z+buildN` | `1.0.0+build42` | Stable release with build number |
