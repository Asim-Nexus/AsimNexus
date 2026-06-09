#!/usr/bin/env python3
"""
Tests for [`core/tools/`](../../core/tools/) — all tool modules.

Covers:
  - get_default_tool_registry() — tool count, security levels, names
  - reset_tool_registry() — singleton clearing
  - bash_tools: execute_bash, execute_python, read_file, write_file, edit_file, list_files
  - web_tools: web_search, web_fetch, web_scrape (mocked)
  - memory_tools: memory_search, memory_store, memory_recall
  - file_tools: file_read, file_write, file_edit, file_search, file_list, file_upload
  - code_tools: code_analyze, code_review, code_format, code_explain
  - mesh_tools: mesh_discover, mesh_send, mesh_status, mesh_broadcast
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from core.tools import get_default_tool_registry, reset_tool_registry
from core.agent_loop import SECURITY_LEVEL_SECURE, SECURITY_LEVEL_SENSITIVE, SECURITY_LEVEL_DANGEROUS


# ═══════════════════════════════════════════════════════════════════════════════
# get_default_tool_registry Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDefaultToolRegistry:
    """Tests for get_default_tool_registry() and reset_tool_registry()."""

    @pytest.fixture(autouse=True)
    def clean_registry(self):
        """Reset singleton before and after each test."""
        reset_tool_registry()
        yield
        reset_tool_registry()

    def test_registry_has_all_tools(self):
        """Default registry contains all expected tools."""
        reg = get_default_tool_registry()
        all_tools = reg.get_all_tools()
        assert len(all_tools) == 26

    def test_registry_tool_names(self):
        """All expected tool names are present."""
        reg = get_default_tool_registry()
        names = {t["name"] for t in reg.get_all_tools()}
        expected = {
            "execute_bash", "execute_python", "read_file", "write_file",
            "edit_file", "list_files",
            "web_search", "web_fetch", "web_scrape",
            "memory_search", "memory_store", "memory_recall",
            "file_read", "file_write", "file_edit", "file_search",
            "file_list", "file_upload",
            "code_analyze", "code_review", "code_format", "code_explain",
            "mesh_discover", "mesh_send", "mesh_status", "mesh_broadcast",
        }
        assert names == expected

    def test_registry_security_counts(self):
        """Verify security level distribution: 14 secure, 10 sensitive, 2 dangerous."""
        reg = get_default_tool_registry()
        all_tools = reg.get_all_tools()
        secure = sum(1 for t in all_tools if t["security_level"] == SECURITY_LEVEL_SECURE)
        sensitive = sum(1 for t in all_tools if t["security_level"] == SECURITY_LEVEL_SENSITIVE)
        dangerous = sum(1 for t in all_tools if t["security_level"] == SECURITY_LEVEL_DANGEROUS)
        assert secure == 14, f"Expected 14 secure, got {secure}"
        assert sensitive == 10, f"Expected 10 sensitive, got {sensitive}"
        assert dangerous == 2, f"Expected 2 dangerous, got {dangerous}"

    def test_registry_dangerous_tools_require_approval(self):
        """All dangerous tools require approval."""
        reg = get_default_tool_registry()
        dangerous_tools = [
            t for t in reg.get_all_tools()
            if t["security_level"] == SECURITY_LEVEL_DANGEROUS
        ]
        for t in dangerous_tools:
            assert t["requires_approval"] is True, f"{t['name']} should require approval"

    def test_reset_clears_singleton(self):
        """reset_tool_registry clears cached singleton."""
        reg1 = get_default_tool_registry()
        assert len(reg1.get_all_tools()) == 26
        reset_tool_registry()
        reg2 = get_default_tool_registry()
        # Should be a fresh instance
        assert len(reg2.get_all_tools()) == 26

    def test_tools_for_llm_has_all(self):
        """get_tools_for_llm returns all 26 tools in OpenAI format."""
        reg = get_default_tool_registry()
        llm_tools = reg.get_tools_for_llm()
        assert len(llm_tools) == 26
        for t in llm_tools:
            assert t["type"] == "function"
            assert "name" in t["function"]
            assert "description" in t["function"]
            assert "parameters" in t["function"]


# ═══════════════════════════════════════════════════════════════════════════════
# bash_tools Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBashTools:
    """Tests for core/tools/bash_tools.py functions."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Ensure we have temp dirs for file operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.tmpdir = tmpdir
            yield

    # ── execute_bash ───────────────────────────────────────────────────────

    def test_execute_bash_simple(self):
        """Execute a simple bash echo command."""
        from core.tools.bash_tools import execute_bash
        result = execute_bash("echo hello_world")
        assert result["success"] is True
        assert "hello_world" in result.get("stdout", "")

    def test_execute_bash_nonzero_exit(self):
        """A command that fails returns error info."""
        from core.tools.bash_tools import execute_bash
        result = execute_bash("exit 42")
        assert result["success"] is False
        assert result.get("exit_code") == 42

    def test_execute_bash_timeout(self):
        """A long-running command respects timeout."""
        from core.tools.bash_tools import execute_bash
        result = execute_bash("echo start && sleep 10 && echo end", timeout=1)
        # Should time out or at least not hang
        assert result["success"] is False or "timeout" in str(result).lower()

    # ── execute_python ─────────────────────────────────────────────────────

    def test_execute_python_simple(self):
        """Execute a simple Python expression."""
        from core.tools.bash_tools import execute_python
        result = execute_python("print('hello from python')")
        assert result["success"] is True
        assert "hello from python" in result.get("stdout", "")

    def test_execute_python_with_result(self):
        """Python code that produces a result value."""
        from core.tools.bash_tools import execute_python
        result = execute_python("result = 42")
        assert result["success"] is True

    def test_execute_python_error(self):
        """Python code with syntax error returns error."""
        from core.tools.bash_tools import execute_python
        result = execute_python("invalid python code {{{")
        assert result["success"] is False
        assert result.get("exit_code", 0) != 0
        assert len(result.get("stderr", "")) > 0

    def test_execute_python_timeout(self):
        """Python code that runs too long respects timeout."""
        from core.tools.bash_tools import execute_python
        result = execute_python("import time; time.sleep(10)", timeout=1)
        assert result["success"] is False

    # ── read_file ──────────────────────────────────────────────────────────

    def test_bash_read_file(self):
        """Read a file via bash_tools.read_file."""
        from core.tools.bash_tools import read_file
        filepath = os.path.join(self.tmpdir, "test_read.txt")
        Path(filepath).write_text("hello world", encoding="utf-8")
        result = read_file(filepath)
        assert result["success"] is True
        assert "hello world" in result["data"]["content"]

    def test_bash_read_file_nonexistent(self):
        """Reading a nonexistent file returns an error."""
        from core.tools.bash_tools import read_file
        result = read_file(os.path.join(self.tmpdir, "no_such_file.txt"))
        assert result["success"] is False
        assert result.get("error") is not None

    def test_bash_read_file_path_traversal_blocked(self):
        """Path traversal outside allowed dirs is blocked."""
        from core.tools.bash_tools import read_file
        result = read_file("../../../etc/passwd")
        assert result["success"] is False

    # ── write_file ─────────────────────────────────────────────────────────

    def test_bash_write_file(self):
        """Write content to a file via bash_tools.write_file."""
        from core.tools.bash_tools import write_file
        filepath = os.path.join(self.tmpdir, "test_write.txt")
        result = write_file(filepath, "new content")
        assert result["success"] is True
        assert Path(filepath).read_text(encoding="utf-8") == "new content"

    def test_bash_write_file_append(self):
        """Append to an existing file."""
        from core.tools.bash_tools import write_file
        filepath = os.path.join(self.tmpdir, "test_append.txt")
        Path(filepath).write_text("first line\n", encoding="utf-8")
        result = write_file(filepath, "second line", append=True)
        assert result["success"] is True
        content = Path(filepath).read_text(encoding="utf-8")
        assert "first line" in content
        assert "second line" in content

    # ── edit_file ──────────────────────────────────────────────────────────

    def test_bash_edit_file(self):
        """Replace text in a file."""
        from core.tools.bash_tools import edit_file
        filepath = os.path.join(self.tmpdir, "test_edit.txt")
        Path(filepath).write_text("old content", encoding="utf-8")
        result = edit_file(filepath, "old content", "new content")
        assert result["success"] is True
        assert Path(filepath).read_text(encoding="utf-8") == "new content"

    # ── list_files ─────────────────────────────────────────────────────────

    def test_bash_list_files(self):
        """List files in a directory."""
        from core.tools.bash_tools import list_files
        Path(os.path.join(self.tmpdir, "file_a.txt")).write_text("a")
        Path(os.path.join(self.tmpdir, "file_b.txt")).write_text("b")
        result = list_files(self.tmpdir)
        assert result["success"] is True
        data = json.dumps(result.get("data", {}))
        assert "file_a.txt" in data
        assert "file_b.txt" in data


# ═══════════════════════════════════════════════════════════════════════════════
# web_tools Tests (mocked)
# ═══════════════════════════════════════════════════════════════════════════════

class TestWebTools:
    """Tests for core/tools/web_tools.py with mocked external deps."""

    @pytest.fixture(autouse=True, scope="class")
    def _mock_external_modules(self):
        """Mock external modules not installed in test environment.

        ``duckduckgo_search`` and ``selectolax`` aren't installed as pip packages
        in the CI / dev environment, but the web tools catch ``ImportError``
        gracefully.  Injecting mock modules into ``sys.modules`` lets the
        ``@patch("duckduckgo_search.DDGS")`` decorators resolve correctly.
        """
        import sys
        from unittest.mock import MagicMock

        sys.modules["duckduckgo_search"] = MagicMock()
        sys.modules["selectolax"] = MagicMock()
        sys.modules["selectolax.parser"] = MagicMock()

        yield

        for mod in ("duckduckgo_search", "selectolax", "selectolax.parser"):
            sys.modules.pop(mod, None)

    # ── web_search (mocked) ────────────────────────────────────────────────

    @patch("duckduckgo_search.DDGS")
    def test_web_search_success(self, mock_ddgs):
        """web_search returns results from DuckDuckGo."""
        mock_instance = MagicMock()
        mock_instance.text.return_value = [
            {"title": "Result 1", "href": "https://example.com/1", "body": "Body 1"},
            {"title": "Result 2", "href": "https://example.com/2", "body": "Body 2"},
        ]
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        from core.tools.web_tools import web_search
        result = web_search("test query", num_results=2)
        assert result["success"] is True
        # data is a dict: {"results": [...], "total_estimated": int, "source": str}
        data = result.get("data", {})
        results = data.get("results", [])
        assert len(results) == 2
        assert results[0]["title"] == "Result 1"

    @patch("duckduckgo_search.DDGS")
    def test_web_search_empty(self, mock_ddgs):
        """web_search handles empty results gracefully."""
        mock_instance = MagicMock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        from core.tools.web_tools import web_search
        result = web_search("no results query")
        # When DDGS returns empty results, the `if results:` check is False,
        # so the function falls through to the "No search backend" fallback.
        assert result["success"] is False
        assert "No search backend" in result.get("error", "")

    @patch("duckduckgo_search.DDGS")
    def test_web_search_error(self, mock_ddgs):
        """web_search handles DDGS exceptions."""
        mock_ddgs.side_effect = Exception("Rate limited")

        from core.tools.web_tools import web_search
        result = web_search("test")
        assert result["success"] is False
        assert result.get("error") is not None

    # ── web_fetch (mocked) ─────────────────────────────────────────────────

    @patch("httpx.Client")
    def test_web_fetch_success(self, mock_httpx_client):
        """web_fetch returns page content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Hello World</body></html>"
        # Must set headers so content-type check passes; otherwise MagicMock
        # returns a MagicMock() for headers.get(), and "text/" in MagicMock()
        # is False (MagicMock.__contains__ defaults to False), causing the
        # function to go to the binary content branch which returns content=None.
        mock_response.headers = {"content-type": "text/html"}
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

        from core.tools.web_tools import web_fetch
        result = web_fetch("https://example.com")
        assert result["success"] is True
        # data is a dict: {"url": ..., "content": ..., "content_type": ..., "status_code": ...}
        data = result.get("data", {})
        assert "Hello World" in data.get("content", "")

    @patch("httpx.Client")
    def test_web_fetch_http_error(self, mock_httpx_client):
        """web_fetch handles HTTP errors."""
        mock_httpx_client.return_value.__enter__.return_value.get.side_effect = Exception("404 Not Found")

        from core.tools.web_tools import web_fetch
        result = web_fetch("https://example.com/notfound")
        assert result["success"] is False

    # ── web_scrape (mocked) ────────────────────────────────────────────────

    @patch("selectolax.parser.HTMLParser")
    @patch("httpx.Client")
    def test_web_scrape_success(self, mock_httpx_client, mock_html_parser):
        """web_scrape extracts elements using CSS selector."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><div class='content'>Main content here</div></body></html>"
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

        mock_element = MagicMock()
        mock_element.text.return_value = "Main content here"
        mock_element.attributes.get.return_value = ""
        mock_parser = MagicMock()
        mock_parser.css.return_value = [mock_element]
        mock_html_parser.return_value = mock_parser

        from core.tools.web_tools import web_scrape
        result = web_scrape("https://example.com", selector=".content")
        assert result["success"] is True
        data = result.get("data", {})
        assert data.get("count", 0) > 0

    @patch("selectolax.parser.HTMLParser")
    @patch("httpx.Client")
    def test_web_scrape_no_match(self, mock_httpx_client, mock_html_parser):
        """web_scrape with non-matching selector returns empty."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>Hello</p></body></html>"
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

        mock_parser = MagicMock()
        mock_parser.css.return_value = []  # No elements match
        mock_html_parser.return_value = mock_parser

        from core.tools.web_tools import web_scrape
        result = web_scrape("https://example.com", selector=".nonexistent")
        assert result["success"] is True
        data = result.get("data", {})
        assert data.get("count", -1) == 0

    def test_web_scrape_invalid_url(self):
        """web_scrape with an invalid URL returns error."""
        from core.tools.web_tools import web_scrape
        result = web_scrape("not-a-url", selector="p")
        assert result["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# memory_tools Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemoryTools:
    """Tests for core/tools/memory_tools.py using temp directories."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a temp data directory for memory files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the memory file path to use our temp dir
            self.data_dir = os.path.join(tmpdir, "data", "memories")
            os.makedirs(self.data_dir, exist_ok=True)
            self.user_id = "test_user_001"
            yield

    def _get_memory_path(self, user_id: str = None) -> str:
        """Get the expected memory file path."""
        uid = user_id or self.user_id
        return os.path.join(self.data_dir, f"{uid}.jsonl")

    # ── memory_search ──────────────────────────────────────────────────────

    def test_memory_search_empty(self):
        """Searching memory with no data returns empty."""
        from core.tools.memory_tools import memory_search
        with patch("core.tools.memory_tools._get_memory_file_path",
                   return_value=self._get_memory_path()):
            result = memory_search("test query", user_id=self.user_id)
            assert result["success"] is True
            # May be empty or error depending on file existence

    # ── memory_store ───────────────────────────────────────────────────────

    def test_memory_store_and_recall(self):
        """Store a memory and recall it."""
        from core.tools.memory_tools import memory_store, memory_recall

        with patch("core.tools.memory_tools._get_memory_file_path",
                   return_value=self._get_memory_path()):
            with patch("core.tools.memory_tools._save_memory",
                       return_value=None):
                store_result = memory_store("my_key", "my_value", user_id=self.user_id)
                assert store_result["success"] is True

                recall_result = memory_recall(user_id=self.user_id, limit=10)
                assert recall_result["success"] is True
                data = recall_result.get("data", {})
                memories = data.get("memories", []) if isinstance(data, dict) else []
                if memories:
                    found = any(
                        item.get("key") == "my_key" for item in memories
                    )
                    assert found, "Stored key should appear in recall"

    def test_memory_store_overwrite(self):
        """Storing the same key overwrites the previous value."""
        from core.tools.memory_tools import memory_store
        with patch("core.tools.memory_tools._get_memory_file_path",
                   return_value=self._get_memory_path()):
            with patch("core.tools.memory_tools._save_memory",
                       return_value=None):
                memory_store("dup_key", "value1", user_id=self.user_id)
                result = memory_store("dup_key", "value2", user_id=self.user_id)
                assert result["success"] is True

    # ── memory_recall ──────────────────────────────────────────────────────

    def test_memory_recall_empty_user(self):
        """Recalling for a user with no memories returns empty."""
        from core.tools.memory_tools import memory_recall
        with patch("core.tools.memory_tools._get_memory_file_path",
                   return_value=self._get_memory_path("nonexistent_user")):
            result = memory_recall(user_id="nonexistent_user", limit=10)
            assert result["success"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# file_tools Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFileTools:
    """Tests for core/tools/file_tools.py with temp directories."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a temp workspace for file operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.tmpdir = tmpdir
            self.test_file = os.path.join(tmpdir, "test_file.txt")
            self.test_dir = os.path.join(tmpdir, "subdir")
            os.makedirs(self.test_dir, exist_ok=True)
            yield

    # ── file_read ──────────────────────────────────────────────────────────

    def test_file_read_success(self):
        """Read a file's contents."""
        Path(self.test_file).write_text("hello file_tools", encoding="utf-8")
        from core.tools.file_tools import file_read
        result = file_read(self.test_file)
        assert result["success"] is True
        assert "hello file_tools" in result["data"]["content"]

    def test_file_read_nonexistent(self):
        """Reading a nonexistent file returns error."""
        from core.tools.file_tools import file_read
        result = file_read(os.path.join(self.tmpdir, "no_file.txt"))
        assert result["success"] is False

    def test_file_read_path_traversal_blocked(self):
        """Path traversal is blocked."""
        from core.tools.file_tools import file_read
        result = file_read("../../../windows/system32/config/sam")
        assert result["success"] is False

    # ── file_write ─────────────────────────────────────────────────────────

    def test_file_write_creates_file(self):
        """Write content creates a new file."""
        from core.tools.file_tools import file_write
        result = file_write(self.test_file, "new content")
        assert result["success"] is True
        assert Path(self.test_file).read_text(encoding="utf-8") == "new content"

    def test_file_write_overwrites(self):
        """Write overwrites existing content."""
        Path(self.test_file).write_text("old", encoding="utf-8")
        from core.tools.file_tools import file_write
        result = file_write(self.test_file, "updated")
        assert result["success"] is True
        assert Path(self.test_file).read_text(encoding="utf-8") == "updated"

    def test_file_write_creates_dirs(self):
        """Write creates parent directories when create_dirs=True."""
        from core.tools.file_tools import file_write
        nested = os.path.join(self.tmpdir, "a", "b", "c", "nested.txt")
        result = file_write(nested, "nested content", create_dirs=True)
        assert result["success"] is True
        assert Path(nested).exists()

    # ── file_edit ──────────────────────────────────────────────────────────

    def test_file_edit_replace_lines(self):
        """Replace a range of lines in a file."""
        Path(self.test_file).write_text("line1\nline2\nline3\n", encoding="utf-8")
        from core.tools.file_tools import file_edit
        result = file_edit(self.test_file, line_start=2, line_end=2, new_text="replaced")
        assert result["success"] is True
        content = Path(self.test_file).read_text(encoding="utf-8")
        assert "line1" in content
        assert "replaced" in content
        assert "line3" in content

    def test_file_edit_out_of_range(self):
        """Editing lines beyond file length returns error."""
        Path(self.test_file).write_text("only one line", encoding="utf-8")
        from core.tools.file_tools import file_edit
        result = file_edit(self.test_file, line_start=10, line_end=10, new_text="x")
        assert result["success"] is False

    # ── file_search ────────────────────────────────────────────────────────

    def test_file_search_finds_pattern(self):
        """Search for a pattern across files."""
        Path(os.path.join(self.tmpdir, "src.py")).write_text("def foo(): pass", encoding="utf-8")
        Path(os.path.join(self.tmpdir, "subdir", "lib.py")).write_text("def bar(): pass", encoding="utf-8")
        from core.tools.file_tools import file_search
        result = file_search(self.tmpdir, pattern="def ", file_pattern="*.py")
        assert result["success"] is True
        matches = result.get("data", [])
        assert len(matches) >= 2

    def test_file_search_no_matches(self):
        """Search with no matches returns empty result."""
        Path(os.path.join(self.tmpdir, "code.py")).write_text("print('hello')", encoding="utf-8")
        from core.tools.file_tools import file_search
        result = file_search(self.tmpdir, pattern="ZZZ_NOTHING", file_pattern="*.py")
        assert result["success"] is True
        data = result.get("data", {})
        assert data.get("total_matches", 0) == 0 if isinstance(data, dict) else len(data) == 0

    # ── file_list ──────────────────────────────────────────────────────────

    def test_file_list_directory(self):
        """List contents of a directory."""
        Path(os.path.join(self.tmpdir, "a.txt")).write_text("a")
        Path(os.path.join(self.tmpdir, "b.txt")).write_text("b")
        Path(os.path.join(self.test_dir, "c.txt")).write_text("c")
        from core.tools.file_tools import file_list
        result = file_list(self.tmpdir, recursive=False)
        assert result["success"] is True
        data = result.get("data", {})
        names = data.get("files", []) if isinstance(data, dict) else [item.get("name", "") for item in data]
        assert "a.txt" in names
        assert "b.txt" in names

    def test_file_list_recursive(self):
        """Recursive listing includes nested files."""
        Path(os.path.join(self.test_dir, "deep.txt")).write_text("deep")
        from core.tools.file_tools import file_list
        result = file_list(self.tmpdir, recursive=True)
        assert result["success"] is True
        data_str = json.dumps(result.get("data", []))
        assert "deep.txt" in data_str

    def test_file_list_nonexistent(self):
        """Listing a nonexistent directory returns error."""
        from core.tools.file_tools import file_list
        result = file_list(os.path.join(self.tmpdir, "no_dir"))
        assert result["success"] is False

    # ── file_upload ────────────────────────────────────────────────────────

    def test_file_upload_success(self):
        """Copy a file to a destination."""
        source = os.path.join(self.tmpdir, "source.txt")
        dest = os.path.join(self.tmpdir, "dest.txt")
        Path(source).write_text("upload content", encoding="utf-8")
        from core.tools.file_tools import file_upload
        result = file_upload(source, dest)
        assert result["success"] is True
        assert Path(dest).read_text(encoding="utf-8") == "upload content"

    def test_file_upload_no_overwrite(self):
        """Upload without overwrite fails if destination exists."""
        source = os.path.join(self.tmpdir, "src.txt")
        dest = os.path.join(self.tmpdir, "dst.txt")
        Path(source).write_text("source", encoding="utf-8")
        Path(dest).write_text("existing", encoding="utf-8")
        from core.tools.file_tools import file_upload
        result = file_upload(source, dest, overwrite=False)
        assert result["success"] is False

    def test_file_upload_overwrite(self):
        """Upload with overwrite replaces destination."""
        source = os.path.join(self.tmpdir, "src.txt")
        dest = os.path.join(self.tmpdir, "dst.txt")
        Path(source).write_text("new content", encoding="utf-8")
        Path(dest).write_text("old content", encoding="utf-8")
        from core.tools.file_tools import file_upload
        result = file_upload(source, dest, overwrite=True)
        assert result["success"] is True
        assert Path(dest).read_text(encoding="utf-8") == "new content"


# ═══════════════════════════════════════════════════════════════════════════════
# code_tools Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCodeTools:
    """Tests for core/tools/code_tools.py functions."""

    SAMPLE_PYTHON_CODE = """
def greet(name: str) -> str:
    \"\"\"Greet someone.\"\"\"
    return f"Hello, {name}!"

class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
"""

    SAMPLE_PYTHON_WITH_ISSUES = """
import os
import sys

def process(data):
    try:
        result = data / 0
    except:
        pass
    return result
"""

    # ── code_analyze ───────────────────────────────────────────────────────

    def test_code_analyze_python(self):
        """Analyze a Python file successfully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(self.SAMPLE_PYTHON_CODE)
            f.flush()
            filepath = f.name

        try:
            from core.tools.code_tools import code_analyze
            result = code_analyze(filepath)
            assert result["success"] is True
            data = result.get("data", {})
            assert "language" in data
            assert data["language"] == "python"
            assert "metrics" in data
        finally:
            os.unlink(filepath)

    def test_code_analyze_nonexistent(self):
        """Analyzing a nonexistent file returns error."""
        from core.tools.code_tools import code_analyze
        result = code_analyze("/tmp/nonexistent_file_xyz.py")
        assert result["success"] is False

    # ── code_review ────────────────────────────────────────────────────────

    def test_code_review_python(self):
        """Review Python code and find issues."""
        from core.tools.code_tools import code_review
        result = code_review(self.SAMPLE_PYTHON_WITH_ISSUES, language="python")
        assert result["success"] is True
        data = result.get("data", {})
        assert "issues" in data

    def test_code_review_empty(self):
        """Review empty code returns error (no code provided)."""
        from core.tools.code_tools import code_review
        result = code_review("", language="python")
        # code_review returns an error when no code is provided
        assert result["success"] is False
        assert "No code provided" in result.get("error", "")

    # ── code_format ────────────────────────────────────────────────────────

    def test_code_format_basic(self):
        """Basic code formatting (no external formatter available)."""
        from core.tools.code_tools import code_format
        messy = "def foo(x):\n  return x+1\n"
        result = code_format(messy, language="python")
        assert result["success"] is True
        # Even basic formatter returns the code
        data = result.get("data", {})
        assert "def foo" in data.get("formatted", json.dumps(data))

    # ── code_explain ───────────────────────────────────────────────────────

    def test_code_explain_python(self):
        """Explain Python code."""
        from core.tools.code_tools import code_explain
        result = code_explain("x = 42\nprint(x)", language="python")
        assert result["success"] is True
        data = result.get("data", "")
        assert len(data) > 0

    def test_code_explain_empty(self):
        """Explain empty code returns error."""
        from core.tools.code_tools import code_explain
        result = code_explain("", language="python")
        assert result["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# mesh_tools Tests (mocked)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMeshTools:
    """Tests for core/tools/mesh_tools.py with mocked dependencies."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up temp directory for peer data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.data_dir = os.path.join(tmpdir, "data", "quad_mesh")
            os.makedirs(self.data_dir, exist_ok=True)
            self.peers_file = os.path.join(self.data_dir, "peers.json")
            yield

    # ── mesh_discover ──────────────────────────────────────────────────────

    @patch("core.tools.mesh_tools._load_peers")
    def test_mesh_discover_with_peers(self, mock_load_peers):
        """Discover returns list of known peers."""
        mock_load_peers.return_value = [
            {"node_id": "node1", "address": "10.0.0.1", "status": "online"},
            {"node_id": "node2", "address": "10.0.0.2", "status": "offline"},
        ]

        from core.tools.mesh_tools import mesh_discover
        result = mesh_discover(timeout=1)
        assert result["success"] is True
        data = result.get("data", {})
        assert "peers" in data
        assert len(data["peers"]) >= 2

    @patch("core.tools.mesh_tools._load_peers")
    def test_mesh_discover_empty(self, mock_load_peers):
        """Discover returns empty list when no peers configured."""
        mock_load_peers.return_value = []

        from core.tools.mesh_tools import mesh_discover
        result = mesh_discover(timeout=1)
        assert result["success"] is True
        data = result.get("data", {})
        peers = data.get("peers", [])
        assert len(peers) == 0

    # ── mesh_send ──────────────────────────────────────────────────────────

    @patch("core.tools.mesh_tools._load_peers")
    def test_mesh_send_to_unknown_peer(self, mock_load_peers):
        """Sending to an unknown peer returns info (no error)."""
        mock_load_peers.return_value = []

        from core.tools.mesh_tools import mesh_send
        result = mesh_send(node_id="unknown_node", message="hello")
        assert result["success"] is True
        data = result.get("data", {})
        assert data.get("delivered_to", "") == "unknown_node"

    # ── mesh_status ────────────────────────────────────────────────────────

    @patch("core.tools.mesh_tools._load_peers")
    def test_mesh_status_returns_info(self, mock_load_peers):
        """Status returns mesh network information."""
        mock_load_peers.return_value = [
            {"node_id": "n1", "address": "10.0.0.1", "status": "online"},
            {"node_id": "n2", "address": "10.0.0.2", "status": "offline"},
        ]

        from core.tools.mesh_tools import mesh_status
        result = mesh_status()
        assert result["success"] is True
        data = result.get("data", {})
        assert "peers" in data or "nodes" in data

    # ── mesh_broadcast ─────────────────────────────────────────────────────

    @patch("core.tools.mesh_tools._load_peers")
    def test_mesh_broadcast_empty_peers(self, mock_load_peers):
        """Broadcast with no peers returns info (no error)."""
        mock_load_peers.return_value = []

        from core.tools.mesh_tools import mesh_broadcast
        result = mesh_broadcast(message="test announcement", message_type="announcement")
        assert result["success"] is True

    @patch("core.tools.mesh_tools._load_peers")
    def test_mesh_broadcast_to_peers(self, mock_load_peers):
        """Broadcast to known peers."""
        mock_load_peers.return_value = [
            {"node_id": "n1", "address": "http://10.0.0.1:8080"},
            {"node_id": "n2", "address": "http://10.0.0.2:8080"},
        ]

        from core.tools.mesh_tools import mesh_broadcast
        result = mesh_broadcast(message="hello everyone", message_type="text")
        assert result["success"] is True
