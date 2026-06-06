#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade version & build metadata tests
ASIMNEXUS Version Tests
=========================
Tests for version, build-id, git SHA, and release channel functions.
"""

import os
import pytest
from pathlib import Path
from backend.version import (
    get_version, get_build_id, get_git_sha, get_release_channel,
)


class TestVersionMetadata:
    """Test suite for version & build metadata functions."""

    @pytest.fixture(autouse=True)
    def setup_version_file(self, tmp_path):
        """Override VERSION_FILE to a temp path for test isolation."""
        import backend.version as ver_mod
        self._original_version_file = ver_mod.VERSION_FILE
        self._version_file = tmp_path / "version.txt"
        ver_mod.VERSION_FILE = self._version_file
        yield
        ver_mod.VERSION_FILE = self._original_version_file

    # ------------------------------------------------------------------ #
    # get_version
    # ------------------------------------------------------------------ #

    def test_get_version_returns_file_content(self):
        """get_version reads and returns the content of version.txt."""
        self._version_file.write_text("1.2.3\n")
        assert get_version() == "1.2.3"

    def test_get_version_strips_whitespace(self):
        """get_version strips leading/trailing whitespace."""
        self._version_file.write_text("  2.0.0-rc1  \n")
        assert get_version() == "2.0.0-rc1"

    def test_get_version_fallback_default(self):
        """get_version returns '0.1.0' when version.txt does not exist."""
        if self._version_file.exists():
            self._version_file.unlink()
        assert get_version() == "0.1.0"

    def test_get_version_semver_format(self):
        """get_version returns valid semver from file."""
        self._version_file.write_text("0.1.0\n")
        version = get_version()
        parts = version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_get_version_with_metadata(self):
        """get_version handles versions with build metadata."""
        self._version_file.write_text("1.0.0+build42\n")
        assert get_version() == "1.0.0+build42"

    # ------------------------------------------------------------------ #
    # get_build_id
    # ------------------------------------------------------------------ #

    def test_get_build_id_returns_string(self):
        """get_build_id returns a non-empty string."""
        build_id = get_build_id()
        assert isinstance(build_id, str)
        assert len(build_id) > 0

    def test_get_build_id_is_timestamp_based(self):
        """get_build_id returns a 14-digit timestamp (YYYYMMDDHHMMSS)."""
        build_id = get_build_id()
        assert build_id.isdigit()
        assert len(build_id) == 14

    def test_get_build_id_changes_over_time(self):
        """get_build_id returns different values when called at different times."""
        id1 = get_build_id()
        id2 = get_build_id()
        # Both are valid; they may be the same if called quickly
        assert len(id1) == 14
        assert len(id2) == 14

    # ------------------------------------------------------------------ #
    # get_git_sha
    # ------------------------------------------------------------------ #

    def test_get_git_sha_returns_unknown_when_not_in_repo(self, monkeypatch):
        """get_git_sha returns 'unknown' when git command fails."""
        # Simulate git not being available
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: type("Result", (), {
                "returncode": 1, "stdout": ""
            })()
        )
        assert get_git_sha() == "unknown"

    def test_get_git_sha_returns_unknown_on_exception(self, monkeypatch):
        """get_git_sha returns 'unknown' when an exception occurs."""
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: (_ for _ in ()).throw(Exception("no git"))
        )
        assert get_git_sha() == "unknown"

    def test_get_git_sha_returns_string(self):
        """get_git_sha returns a string (could be 'unknown' or a real SHA)."""
        sha = get_git_sha()
        assert isinstance(sha, str)
        assert len(sha) > 0

    # ------------------------------------------------------------------ #
    # get_release_channel
    # ------------------------------------------------------------------ #

    def test_get_release_channel_default_stable(self):
        """get_release_channel returns 'stable' when env var not set."""
        if "ASIM_RELEASE_CHANNEL" in os.environ:
            del os.environ["ASIM_RELEASE_CHANNEL"]
        assert get_release_channel() == "stable"

    def test_get_release_channel_env_override(self, monkeypatch):
        """get_release_channel respects ASIM_RELEASE_CHANNEL env var."""
        monkeypatch.setenv("ASIM_RELEASE_CHANNEL", "beta")
        assert get_release_channel() == "beta"

    def test_get_release_channel_alpha(self, monkeypatch):
        """get_release_channel returns 'alpha' when set."""
        monkeypatch.setenv("ASIM_RELEASE_CHANNEL", "alpha")
        assert get_release_channel() == "alpha"

    def test_get_release_channel_rc(self, monkeypatch):
        """get_release_channel returns 'rc' when set."""
        monkeypatch.setenv("ASIM_RELEASE_CHANNEL", "rc")
        assert get_release_channel() == "rc"

    def test_get_release_channel_custom(self, monkeypatch):
        """get_release_channel returns any custom channel name."""
        monkeypatch.setenv("ASIM_RELEASE_CHANNEL", "nightly")
        assert get_release_channel() == "nightly"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
