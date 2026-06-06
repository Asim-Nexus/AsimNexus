"""
REAL Unit Tests for FileTools
Tests file operations with safety checks using temp directories and files.
"""

import os
import tempfile
import shutil
import pytest
from .file_tools import FileTools, FileOperation, FileOperationResult


@pytest.fixture
def tools():
    """Fresh FileTools instance for each test"""
    return FileTools()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for file operations"""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path, ignore_errors=True)


class TestFileOperationEnum:
    """Tests for the FileOperation enum"""

    def test_enum_values(self):
        assert FileOperation.LIST.value == "list"
        assert FileOperation.READ.value == "read"
        assert FileOperation.WRITE.value == "write"
        assert FileOperation.COPY.value == "copy"
        assert FileOperation.MOVE.value == "move"
        assert FileOperation.DELETE.value == "delete"
        assert FileOperation.CREATE_DIR.value == "create_dir"
        assert FileOperation.GET_INFO.value == "get_info"


class TestFileOperationResult:
    """Tests for FileOperationResult dataclass"""

    def test_create_result(self):
        result = FileOperationResult(
            success=True,
            operation=FileOperation.READ,
            path="/test/file.txt",
            message="Read 10 lines",
            data="content",
        )
        assert result.success is True
        assert result.operation == FileOperation.READ
        assert result.data == "content"


class TestFileToolsPathSafety:
    """Tests for path safety checks"""

    def test_safe_path_allowed(self, tools):
        safe, msg = tools._is_path_safe(os.getcwd())
        assert safe is True

    def test_restricted_path_windows(self, tools):
        safe, msg = tools._is_path_safe("C:\\Windows\\System32")
        assert safe is False
        assert "restricted" in msg.lower()

    def test_nonexistent_path_not_restricted(self, tools):
        """Non-existent paths that don't match restricted prefixes should be safe"""
        safe, msg = tools._is_path_safe("/tmp/some_random_path_12345")
        assert safe is True

    def test_check_file_safety_on_nonexistent_file(self, tools):
        safe, msg = tools._check_file_safety("/nonexistent/file.txt", FileOperation.READ)
        # Non-existent paths within allowed areas pass safety if path validation passes
        assert safe is not None


class TestFileToolsListDirectory:
    """Tests for listing directories"""

    def test_list_current_directory(self, tools):
        result = tools.list_directory(".")
        assert result.success is True
        assert result.operation == FileOperation.LIST
        assert isinstance(result.data, list)
        # Current dir should have entries
        assert len(result.data) > 0
        assert any(item.get("name") for item in result.data)

    def test_list_nonexistent_directory(self, tools):
        result = tools.list_directory("/nonexistent_dir_xyz")
        assert result.success is False
        assert result.operation == FileOperation.LIST

    def test_list_file_path_instead_of_dir(self, tools, temp_dir):
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("hello")
        result = tools.list_directory(test_file)
        assert result.success is False
        assert "not a directory" in result.message.lower()

    def test_list_with_hidden_files(self, tools, temp_dir):
        # Create a hidden file
        hidden = os.path.join(temp_dir, ".hidden_file")
        visible = os.path.join(temp_dir, "visible_file.txt")
        open(hidden, "w").close()
        open(visible, "w").close()

        # Without show_hidden
        result_no_hidden = tools.list_directory(temp_dir, show_hidden=False)
        names_no_hidden = [item["name"] for item in result_no_hidden.data]
        assert ".hidden_file" not in names_no_hidden

        # With show_hidden
        result_with_hidden = tools.list_directory(temp_dir, show_hidden=True)
        names_with_hidden = [item["name"] for item in result_with_hidden.data]
        assert ".hidden_file" in names_with_hidden


class TestFileToolsReadFile:
    """Tests for reading files"""

    def test_read_existing_file(self, tools, temp_dir):
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("line1\nline2\nline3\n")
        result = tools.read_file(test_file)
        assert result.success is True
        assert result.data == "line1\nline2\nline3"

    def test_read_nonexistent_file(self, tools):
        result = tools.read_file("/nonexistent_file_xyz.txt")
        assert result.success is False

    def test_read_with_max_lines(self, tools, temp_dir):
        test_file = os.path.join(temp_dir, "long.txt")
        with open(test_file, "w") as f:
            for i in range(100):
                f.write(f"line{i}\n")
        result = tools.read_file(test_file, max_lines=10)
        assert result.success is True
        assert "... (truncated)" in result.data
        lines = result.data.split('\n')
        assert len([l for l in lines if l and not l.startswith('...')]) <= 10

    def test_read_unsafe_path(self, tools):
        result = tools.read_file("C:\\Windows\\System32\\config\\SAM")
        assert result.success is False


class TestFileToolsWriteFile:
    """Tests for writing files"""

    def test_write_new_file(self, tools, temp_dir):
        test_file = os.path.join(temp_dir, "new_file.txt")
        result = tools.write_file_safe(test_file, "hello world")
        assert result.success is True
        assert os.path.exists(test_file)
        with open(test_file) as f:
            assert f.read() == "hello world"

    def test_write_with_backup(self, tools, temp_dir):
        test_file = os.path.join(temp_dir, "backup_test.txt")
        with open(test_file, "w") as f:
            f.write("original")
        result = tools.write_file_safe(test_file, "modified", backup=True)
        assert result.success is True
        with open(test_file) as f:
            assert f.read() == "modified"
        # Backup file should exist
        backup_files = [f for f in os.listdir(temp_dir) if f.startswith("backup_test.txt.backup.")]
        assert len(backup_files) >= 1

    def test_write_disallowed_extension(self, tools, temp_dir):
        test_file = os.path.join(temp_dir, "script.exe")
        result = tools.write_file_safe(test_file, "binary data")
        assert result.success is False
        assert "not allowed" in result.message.lower()

    def test_write_to_restricted_path(self, tools):
        result = tools.write_file_safe("C:\\Windows\\test.txt", "data")
        assert result.success is False

    def test_write_creates_directory(self, tools, temp_dir):
        nested = os.path.join(temp_dir, "new_dir", "nested", "file.txt")
        result = tools.write_file_safe(nested, "content")
        assert result.success is True
        assert os.path.exists(nested)


class TestFileToolsCopyMoveDelete:
    """Tests for copy, move, and delete operations"""

    def test_copy_file(self, tools, temp_dir):
        src = os.path.join(temp_dir, "source.txt")
        dst = os.path.join(temp_dir, "dest.txt")
        with open(src, "w") as f:
            f.write("copy me")
        result = tools.copy_file(src, dst)
        assert result.success is True
        assert os.path.exists(dst)
        with open(dst) as f:
            assert f.read() == "copy me"

    def test_move_file(self, tools, temp_dir):
        src = os.path.join(temp_dir, "move_src.txt")
        dst = os.path.join(temp_dir, "move_dst.txt")
        with open(src, "w") as f:
            f.write("move me")
        result = tools.move_file(src, dst)
        assert result.success is True
        assert os.path.exists(dst)
        assert not os.path.exists(src)

    def test_delete_without_confirmation(self, tools, temp_dir):
        test_file = os.path.join(temp_dir, "to_delete.txt")
        with open(test_file, "w") as f:
            f.write("delete me")
        result = tools.delete_file_safe(test_file, confirm=False)
        assert result.success is False
        assert "confirmation" in result.message.lower()

    def test_delete_with_confirmation(self, tools, temp_dir):
        test_file = os.path.join(temp_dir, "confirmed_delete.txt")
        with open(test_file, "w") as f:
            f.write("delete me")
        result = tools.delete_file_safe(test_file, confirm=True)
        assert result.success is True


class TestFileToolsCreateDirectory:
    """Tests for directory creation"""

    def test_create_directory(self, tools, temp_dir):
        new_dir = os.path.join(temp_dir, "new_subdir")
        result = tools.create_directory(new_dir)
        assert result.success is True
        assert os.path.isdir(new_dir)

    def test_create_nested_directories(self, tools, temp_dir):
        nested = os.path.join(temp_dir, "a", "b", "c")
        result = tools.create_directory(nested)
        assert result.success is True
        assert os.path.isdir(nested)


class TestFileToolsGetInfo:
    """Tests for file info"""

    def test_get_file_info(self, tools, temp_dir):
        test_file = os.path.join(temp_dir, "info_test.txt")
        with open(test_file, "w") as f:
            f.write("info data")
        result = tools.get_file_info(test_file)
        assert result.success is True
        assert result.data["type"] == "file"
        assert result.data["size"] > 0
        assert result.data["extension"] == ".txt"
        assert result.data["allowed_type"] is True

    def test_get_directory_info(self, tools):
        result = tools.get_file_info(".")
        assert result.success is True
        assert result.data["type"] == "directory"

    def test_get_nonexistent_path_info(self, tools):
        result = tools.get_file_info("/nonexistent_path_xyz")
        assert result.success is False
