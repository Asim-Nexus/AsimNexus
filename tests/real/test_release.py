#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade release lifecycle tests
ASIMNEXUS Release Tests
========================
Tests for publish, list, current, set_current, and rollback operations.
"""

import json
import pytest
from pathlib import Path
from backend.release import (
    publish_release, list_releases, current_release,
    set_current_release, record_rollback,
    RELEASES_FILE
)


class TestReleaseLifecycle:
    """Test suite for release lifecycle management."""

    @pytest.fixture(autouse=True)
    def setup_releases_file(self, tmp_path):
        """Override RELEASES_FILE to a temp path for test isolation."""
        import backend.release as rel_mod
        self._original_releases_file = rel_mod.RELEASES_FILE
        rel_mod.RELEASES_FILE = tmp_path / "releases.json"
        rel_mod.RELEASES_FILE.parent.mkdir(parents=True, exist_ok=True)
        yield
        rel_mod.RELEASES_FILE = self._original_releases_file

    # ------------------------------------------------------------------ #
    # publish_release
    # ------------------------------------------------------------------ #

    def test_publish_release_creates_record(self):
        """publish_release writes a record with correct fields."""
        record = publish_release(version="1.0.0", target="docker", checksum="abc123")

        assert record["version"] == "1.0.0"
        assert record["target"] == "docker"
        assert record["checksum"] == "abc123"
        assert record["is_current"] is True
        assert record["published_at"].endswith("Z")

    def test_publish_release_unmarks_old_current(self):
        """Publishing a new release unmarks the previous current for the same target."""
        publish_release(version="1.0.0", target="docker", checksum="aaa")
        publish_release(version="2.0.0", target="docker", checksum="bbb")

        releases = list_releases(target="docker")
        assert len(releases) == 2

        # Only the latest should be marked current
        v1 = [r for r in releases if r["version"] == "1.0.0"][0]
        v2 = [r for r in releases if r["version"] == "2.0.0"][0]
        assert v1["is_current"] is False
        assert v2["is_current"] is True

    def test_publish_release_different_targets_independent(self):
        """Different targets have independent current-release markers."""
        publish_release(version="1.0.0", target="docker", checksum="aaa")
        publish_release(version="1.0.0", target="pwa", checksum="bbb")

        d_current = current_release(target="docker")
        p_current = current_release(target="pwa")

        assert d_current["version"] == "1.0.0"
        assert p_current["version"] == "1.0.0"

    # ------------------------------------------------------------------ #
    # list_releases
    # ------------------------------------------------------------------ #

    def test_list_releases_all(self):
        """list_releases returns all releases when no target filter."""
        publish_release(version="1.0.0", target="docker", checksum="a")
        publish_release(version="1.0.0", target="pwa", checksum="b")

        all_releases = list_releases()
        assert len(all_releases) == 2

    def test_list_releases_filtered_by_target(self):
        """list_releases filters correctly by target."""
        publish_release(version="1.0.0", target="docker", checksum="a")
        publish_release(version="1.0.0", target="pwa", checksum="b")
        publish_release(version="2.0.0", target="docker", checksum="c")

        docker_releases = list_releases(target="docker")
        assert len(docker_releases) == 2

    def test_list_releases_empty(self):
        """list_releases returns empty list when no releases exist."""
        assert list_releases() == []

    # ------------------------------------------------------------------ #
    # current_release
    # ------------------------------------------------------------------ #

    def test_current_release_returns_latest(self):
        """current_release returns the latest is_current release."""
        publish_release(version="1.0.0", target="docker", checksum="a")
        publish_release(version="2.0.0", target="docker", checksum="b")
        publish_release(version="3.0.0", target="docker", checksum="c")

        current = current_release(target="docker")
        assert current["version"] == "3.0.0"

    def test_current_release_no_target_returns_latest_any(self):
        """current_release without target returns the most recent current across all targets."""
        publish_release(version="1.0.0", target="docker", checksum="a")
        publish_release(version="1.0.0", target="pwa", checksum="b")

        current = current_release()
        # Both are current; reversed order picks the last appended
        assert current["target"] in ("docker", "pwa")

    def test_current_release_none_exists(self):
        """current_release returns fallback dict when no releases exist."""
        result = current_release(target="docker")
        assert result["version"] is None
        assert result["target"] == "docker"
        assert result["status"] == "no_current_release"

    # ------------------------------------------------------------------ #
    # set_current_release
    # ------------------------------------------------------------------ #

    def test_set_current_release_marks_version(self):
        """set_current_release marks a specific version as current."""
        publish_release(version="1.0.0", target="docker", checksum="a")
        publish_release(version="2.0.0", target="docker", checksum="b")

        # Switch current to 1.0.0
        set_current_release(version="1.0.0", target="docker")

        current = current_release(target="docker")
        assert current["version"] == "1.0.0"

    def test_set_current_release_not_found(self):
        """set_current_release raises ValueError for non-existent version."""
        publish_release(version="1.0.0", target="docker", checksum="a")

        with pytest.raises(ValueError, match="not found"):
            set_current_release(version="9.9.9", target="docker")

    def test_set_current_release_unmarks_others(self):
        """set_current_release unmarks all other versions for the same target."""
        publish_release(version="1.0.0", target="docker", checksum="a")
        publish_release(version="2.0.0", target="docker", checksum="b")

        set_current_release(version="1.0.0", target="docker")

        releases = list_releases(target="docker")
        v1 = [r for r in releases if r["version"] == "1.0.0"][0]
        v2 = [r for r in releases if r["version"] == "2.0.0"][0]
        assert v1["is_current"] is True
        assert v2["is_current"] is False

    # ------------------------------------------------------------------ #
    # record_rollback
    # ------------------------------------------------------------------ #

    def test_record_rollback_creates_entry(self, tmp_path):
        """record_rollback creates a log entry and updates current pointer."""
        import backend.release as rel_mod
        rel_mod.RELEASES_FILE = tmp_path / "releases.json"

        publish_release(version="1.0.0", target="docker", checksum="a")
        publish_release(version="2.0.0", target="docker", checksum="b")

        # Rollback from 2.0.0 to 1.0.0
        record = record_rollback(from_version="2.0.0", to_version="1.0.0", target="docker")

        assert record["action"] == "rollback"
        assert record["target"] == "docker"
        assert record["from_version"] == "2.0.0"
        assert record["to_version"] == "1.0.0"
        assert "timestamp" in record

        # Current should now point to 1.0.0
        current = current_release(target="docker")
        assert current["version"] == "1.0.0"

    def test_record_rollback_appends_to_jsonl(self, tmp_path):
        """record_rollback appends to a JSONL rollback log."""
        import backend.release as rel_mod
        rel_mod.RELEASES_FILE = tmp_path / "releases.json"

        publish_release(version="1.0.0", target="docker", checksum="a")
        publish_release(version="2.0.0", target="docker", checksum="b")

        record_rollback(from_version="2.0.0", to_version="1.0.0", target="docker")

        # Verify JSONL log exists
        rollback_log = tmp_path / "rollback_log.jsonl"
        assert rollback_log.exists()
        lines = rollback_log.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) >= 1
        entry = json.loads(lines[0])
        assert entry["action"] == "rollback"
        assert entry["from_version"] == "2.0.0"

    def test_record_rollback_to_nonexistent_version(self, tmp_path):
        """record_rollback raises ValueError when target version doesn't exist."""
        import backend.release as rel_mod
        rel_mod.RELEASES_FILE = tmp_path / "releases.json"

        publish_release(version="1.0.0", target="docker", checksum="a")

        with pytest.raises(ValueError, match="not found"):
            record_rollback(from_version="1.0.0", to_version="9.9.9", target="docker")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
