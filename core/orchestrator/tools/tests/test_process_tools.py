"""
Real pytest tests for ProcessTools using mocked psutil
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple

# Ensure the module can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── Test ProcessInfo dataclass ──────────────────────────────────────────────

class TestProcessInfo:
    """Tests for the ProcessInfo dataclass"""

    def test_create_process_info(self):
        """Create a ProcessInfo with all fields"""
        from asim_tools.system.process_tools import ProcessInfo
        pi = ProcessInfo(
            pid=1234,
            name="python.exe",
            cpu_percent=5.5,
            memory_percent=10.2,
            status="running",
            create_time=1000000.0,
            exe_path="C:/Python/python.exe",
            cmdline=["python", "script.py"]
        )
        assert pi.pid == 1234
        assert pi.name == "python.exe"
        assert pi.cpu_percent == 5.5
        assert pi.memory_percent == 10.2
        assert pi.status == "running"
        assert pi.create_time == 1000000.0
        assert pi.exe_path == "C:/Python/python.exe"
        assert pi.cmdline == ["python", "script.py"]

    def test_create_process_info_minimal(self):
        """Create a ProcessInfo with only required fields"""
        from asim_tools.system.process_tools import ProcessInfo
        pi = ProcessInfo(
            pid=5678,
            name="notepad.exe",
            cpu_percent=0.0,
            memory_percent=0.5,
            status="sleeping",
            create_time=2000000.0
        )
        assert pi.pid == 5678
        assert pi.name == "notepad.exe"
        assert pi.exe_path is None
        assert pi.cmdline is None


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def tools():
    """Create a fresh ProcessTools instance"""
    from asim_tools.system.process_tools import ProcessTools
    return ProcessTools()


# ── Test ProcessTools.__init__ ─────────────────────────────────────────────

class TestProcessToolsInit:
    """Tests for ProcessTools initialization"""

    def test_init_defaults(self, tools):
        """Verify default safe/dangerous process lists"""
        assert "notepad.exe" in tools.safe_processes
        assert "calc.exe" in tools.safe_processes
        assert "mspaint.exe" in tools.safe_processes
        assert "explorer.exe" in tools.safe_processes
        assert "chrome.exe" in tools.safe_processes
        assert "firefox.exe" in tools.safe_processes
        assert "code.exe" in tools.safe_processes
        assert "python.exe" in tools.safe_processes
        assert len(tools.safe_processes) == 8

    def test_init_dangerous_processes(self, tools):
        """Verify dangerous processes list"""
        assert "system.exe" in tools.dangerous_processes
        assert "csrss.exe" in tools.dangerous_processes
        assert "winlogon.exe" in tools.dangerous_processes
        assert "lsass.exe" in tools.dangerous_processes
        assert "services.exe" in tools.dangerous_processes
        assert "svchost.exe" in tools.dangerous_processes
        assert len(tools.dangerous_processes) == 6


# ── Test list_processes ─────────────────────────────────────────────────────

class TestProcessToolsListProcesses:
    """Tests for list_processes"""

    def test_list_processes_returns_list(self, tools, monkeypatch):
        """list_processes should return a list of ProcessInfo"""
        mock_proc = MagicMock()
        mock_proc.info = {
            'pid': 100,
            'name': 'python.exe',
            'cpu_percent': 2.5,
            'memory_percent': 5.0,
            'status': 'running',
            'create_time': 1000.0,
            'exe': '/usr/bin/python',
            'cmdline': ['python', 'test.py']
        }

        import psutil
        monkeypatch.setattr(psutil, 'process_iter', lambda *args, **kw: [mock_proc])

        from asim_tools.system.process_tools import ProcessInfo
        result = tools.list_processes()
        assert len(result) == 1
        assert isinstance(result[0], ProcessInfo)
        assert result[0].name == "python.exe"
        assert result[0].pid == 100

    def test_list_processes_with_filter(self, tools, monkeypatch):
        """list_processes should filter by name"""
        mock_proc1 = MagicMock()
        mock_proc1.info = {
            'pid': 100, 'name': 'python.exe', 'cpu_percent': 2.5,
            'memory_percent': 5.0, 'status': 'running', 'create_time': 1000.0,
            'exe': '/usr/bin/python', 'cmdline': ['python', 't.py']
        }
        mock_proc2 = MagicMock()
        mock_proc2.info = {
            'pid': 200, 'name': 'notepad.exe', 'cpu_percent': 0.0,
            'memory_percent': 1.0, 'status': 'sleeping', 'create_time': 1001.0,
            'exe': 'C:/Windows/notepad.exe', 'cmdline': ['notepad.exe']
        }

        import psutil
        monkeypatch.setattr(psutil, 'process_iter', lambda *args, **kw: [mock_proc1, mock_proc2])

        result = tools.list_processes(filter_name="python")
        assert len(result) == 1
        assert result[0].name == "python.exe"

    def test_list_processes_handles_no_such_process(self, tools, monkeypatch):
        """list_processes should skip processes that vanish"""
        import psutil
        mock_proc = MagicMock()
        type(mock_proc).info = PropertyMock(side_effect=psutil.NoSuchProcess(999))

        monkeypatch.setattr(psutil, 'process_iter', lambda *args, **kw: [mock_proc])

        result = tools.list_processes()
        assert len(result) == 0

    def test_list_processes_empty_no_processes(self, tools, monkeypatch):
        """list_processes should return empty list when no processes"""
        import psutil
        monkeypatch.setattr(psutil, 'process_iter', lambda *args, **kw: [])
        result = tools.list_processes()
        assert len(result) == 0


# ── Test get_process_by_name ───────────────────────────────────────────────

class TestProcessToolsGetProcessByName:
    """Tests for get_process_by_name"""

    def test_get_process_by_name_found(self, tools, monkeypatch):
        """get_process_by_name should return matching process"""
        mock_proc = MagicMock()
        mock_proc.info = {
            'pid': 100, 'name': 'python.exe', 'cpu_percent': 2.5,
            'memory_percent': 5.0, 'status': 'running', 'create_time': 1000.0,
            'exe': '/usr/bin/python', 'cmdline': ['python', 't.py']
        }

        import psutil
        monkeypatch.setattr(psutil, 'process_iter', lambda *args, **kw: [mock_proc])

        result = tools.get_process_by_name("python")
        assert result is not None
        assert result.name == "python.exe"

    def test_get_process_by_name_not_found(self, tools, monkeypatch):
        """get_process_by_name should return None when no match"""
        import psutil
        monkeypatch.setattr(psutil, 'process_iter', lambda *args, **kw: [])
        result = tools.get_process_by_name("nonexistent.exe")
        assert result is None


# ── Test is_safe_to_manage ─────────────────────────────────────────────────

class TestProcessToolsIsSafeToManage:
    """Tests for is_safe_to_manage"""

    def test_dangerous_process_rejected(self, tools):
        """Dangerous process should be rejected"""
        from asim_tools.system.process_tools import ProcessInfo
        proc = ProcessInfo(
            pid=1, name="lsass.exe", cpu_percent=0, memory_percent=0,
            status="running", create_time=0
        )
        safe, reason = tools.is_safe_to_manage(proc)
        assert safe is False
        assert "critical system process" in reason.lower()

    def test_safe_process_ownership_check_pass(self, tools, monkeypatch):
        """Safe process owned by current user should pass"""
        from asim_tools.system.process_tools import ProcessInfo
        proc = ProcessInfo(
            pid=100, name="notepad.exe", cpu_percent=0, memory_percent=0,
            status="running", create_time=0
        )

        monkeypatch.setattr('os.getlogin', lambda: "testuser")

        mock_psutil_proc = MagicMock()
        mock_psutil_proc.username.return_value = "testuser"
        import psutil
        monkeypatch.setattr(psutil, 'Process', lambda pid: mock_psutil_proc)

        safe, reason = tools.is_safe_to_manage(proc)
        assert safe is True
        assert "safe to manage" in reason.lower()

    def test_safe_process_different_owner_rejected(self, tools, monkeypatch):
        """Safe process owned by different user should be rejected"""
        from asim_tools.system.process_tools import ProcessInfo
        proc = ProcessInfo(
            pid=100, name="notepad.exe", cpu_percent=0, memory_percent=0,
            status="running", create_time=0
        )

        monkeypatch.setattr('os.getlogin', lambda: "testuser")

        mock_psutil_proc = MagicMock()
        mock_psutil_proc.username.return_value = "otheruser"
        import psutil
        monkeypatch.setattr(psutil, 'Process', lambda pid: mock_psutil_proc)

        safe, reason = tools.is_safe_to_manage(proc)
        assert safe is False
        assert "different user" in reason.lower()


# ── Test focus_window ──────────────────────────────────────────────────────

class TestProcessToolsFocusWindow:
    """Tests for focus_window"""

    def test_focus_window_automation_not_available(self, tools):
        """focus_window should return False when automation unavailable"""
        # Force automation_available to False
        tools.automation_available = False
        result = tools.focus_window("Test Window")
        assert result is False

    def test_focus_window_found(self, tools):
        """focus_window should return True when window is found"""
        import sys
        mock_pywinauto = MagicMock()
        sys.modules['pywinauto'] = mock_pywinauto
        tools.automation_available = True

        mock_window = MagicMock()
        mock_window.window_text.return_value = "Test Window Title"
        mock_desktop = MagicMock()
        mock_desktop.windows.return_value = [mock_window]
        mock_pywinauto.Desktop.return_value = mock_desktop

        result = tools.focus_window("Test Window")
        assert result is True
        mock_window.set_focus.assert_called_once()

    def test_focus_window_not_found(self, tools):
        """focus_window should return False when window is not found"""
        import sys
        mock_pywinauto = MagicMock()
        sys.modules['pywinauto'] = mock_pywinauto
        tools.automation_available = True

        mock_desktop = MagicMock()
        mock_desktop.windows.return_value = []
        mock_pywinauto.Desktop.return_value = mock_desktop

        result = tools.focus_window("Nonexistent")
        assert result is False


# ── Test close_application ─────────────────────────────────────────────────

class TestProcessToolsCloseApplication:
    """Tests for close_application"""

    def test_close_application_not_found(self, tools, monkeypatch):
        """close_application should return False when process not found"""
        import psutil
        monkeypatch.setattr(psutil, 'process_iter', lambda *args, **kw: [])
        result = tools.close_application("nonexistent.exe")
        assert result is False

    def test_close_application_unsafe_process(self, tools, monkeypatch):
        """close_application should not close dangerous processes"""
        mock_proc = MagicMock()
        mock_proc.info = {
            'pid': 1, 'name': 'lsass.exe', 'cpu_percent': 0, 'memory_percent': 0,
            'status': 'running', 'create_time': 0, 'exe': 'C:/Windows/lsass.exe',
            'cmdline': ['lsass.exe']
        }
        import psutil
        monkeypatch.setattr(psutil, 'process_iter', lambda *args, **kw: [mock_proc])

        result = tools.close_application("lsass.exe")
        assert result is False

    def test_close_application_terminate(self, tools, monkeypatch):
        """close_application should terminate the process gracefully"""
        mock_proc_info = MagicMock()
        mock_proc_info.info = {
            'pid': 100, 'name': 'notepad.exe', 'cpu_percent': 0, 'memory_percent': 0,
            'status': 'running', 'create_time': 0, 'exe': 'C:/Windows/notepad.exe',
            'cmdline': ['notepad.exe']
        }

        import psutil
        monkeypatch.setattr(psutil, 'process_iter', lambda *args, **kw: [mock_proc_info])

        mock_psutil_proc = MagicMock()
        monkeypatch.setattr(psutil, 'Process', lambda pid: mock_psutil_proc)

        # Mock os.getlogin and psutil.Process.username for safety check
        monkeypatch.setattr('os.getlogin', lambda: "testuser")
        mock_owner_proc = MagicMock()
        mock_owner_proc.username.return_value = "testuser"
        # Need to be careful here - the safety check calls psutil.Process(pid).username()
        # But close_application also calls psutil.Process(pid) for terminate
        # Let's use a side_effect to return different mocks

        real_process = psutil.Process

        def mock_process_factory(pid):
            if pid == 100:
                return mock_psutil_proc
            return mock_owner_proc

        # Simpler approach: just patch os.getlogin and the username check
        monkeypatch.setattr('os.getlogin', lambda: "testuser")
        # Override the Process class behavior for username
        original_process = psutil.Process

        class MockProcessWithOwner:
            def __init__(self, pid):
                self.pid = pid
            def username(self):
                return "testuser"
            def terminate(self):
                pass
            def kill(self):
                pass
            def wait(self, timeout=5):
                pass

        monkeypatch.setattr(psutil, 'Process', MockProcessWithOwner)

        result = tools.close_application("notepad.exe")
        assert result is True


# ── Test start_application ─────────────────────────────────────────────────

class TestProcessToolsStartApplication:
    """Tests for start_application"""

    def test_start_application_path_not_found(self, tools):
        """start_application should return False when path doesn't exist"""
        result = tools.start_application("C:/nonexistent/app.exe")
        assert result is False

    @patch('subprocess.Popen')
    def test_start_application_success(self, mock_popen, tools, tmp_path):
        """start_application should return True when app starts"""
        app_path = tmp_path / "test_app.exe"
        app_path.write_text("dummy")
        app_path_str = str(app_path)

        result = tools.start_application(app_path_str)
        assert result is True
        mock_popen.assert_called_once_with([app_path_str], shell=False)

    @patch('subprocess.Popen')
    def test_start_application_with_arguments(self, mock_popen, tools, tmp_path):
        """start_application should pass arguments"""
        app_path = tmp_path / "test_app.exe"
        app_path.write_text("dummy")

        result = tools.start_application(str(app_path), arguments=["--flag", "value"])
        assert result is True
        mock_popen.assert_called_once_with([str(app_path), "--flag", "value"], shell=False)


# ── Test get_system_info ───────────────────────────────────────────────────

class TestProcessToolsGetSystemInfo:
    """Tests for get_system_info"""

    def test_get_system_info_returns_dict(self, tools, monkeypatch):
        """get_system_info should return a dict with process info"""
        mock_proc1 = MagicMock()
        mock_proc1.info = {'status': 'running', 'cpu_percent': 10.0, 'memory_percent': 5.0}
        mock_proc2 = MagicMock()
        mock_proc2.info = {'status': 'sleeping', 'cpu_percent': 0.0, 'memory_percent': 2.0}
        mock_proc3 = MagicMock()
        mock_proc3.info = {'status': 'running', 'cpu_percent': 20.0, 'memory_percent': 8.0}

        import psutil
        monkeypatch.setattr(psutil, 'process_iter', lambda *args, **kw: [mock_proc1, mock_proc2, mock_proc3])

        result = tools.get_system_info()
        assert result["total_processes"] == 3
        assert result["process_counts"]["running"] == 2
        assert result["process_counts"]["sleeping"] == 1
        assert result["total_cpu_usage"] == 30.0
        assert result["total_memory_usage"] == 15.0

    def test_get_system_info_handles_exception(self, tools, monkeypatch):
        """get_system_info should handle psutil exceptions gracefully"""
        import psutil

        def failing_iter(**kw):
            raise Exception("psutil error")

        monkeypatch.setattr(psutil, 'process_iter', failing_iter)

        result = tools.get_system_info()
        assert result == {}


# ── Test safe_automation_check ─────────────────────────────────────────────

class TestProcessToolsSafeAutomationCheck:
    """Tests for safe_automation_check"""

    def test_safe_automation_not_available(self, tools):
        """safe_automation_check should return False when libs not installed"""
        tools.automation_available = False
        result, message = tools.safe_automation_check()
        assert result is False
        assert "not installed" in message.lower()

    def test_safe_automation_available(self, tools):
        """safe_automation_check should return True when automation is ready"""
        import asim_tools.system.process_tools as pt
        mock_pyautogui = MagicMock()
        mock_pyautogui.position.return_value = (100, 200)
        pt.pyautogui = mock_pyautogui

        tools.automation_available = True
        result, message = tools.safe_automation_check()
        assert result is True
        assert "ready" in message.lower()


# ── Test macro methods ─────────────────────────────────────────────────────

class TestProcessToolsMacro:
    """Tests for macro recording/playback"""

    def test_record_macro_not_available(self, tools):
        """record_simple_macro should return False when automation unavailable"""
        tools.automation_available = False
        result = tools.record_simple_macro("test_macro", 5)
        assert result is False

    def test_record_macro_available(self, tools):
        """record_simple_macro should return True when automation available"""
        tools.automation_available = True
        result = tools.record_simple_macro("test_macro", 5)
        assert result is True

    def test_play_macro_not_available(self, tools):
        """play_simple_macro should return False when automation unavailable"""
        tools.automation_available = False
        result = tools.play_simple_macro("test_macro")
        assert result is False

    def test_play_macro_available(self, tools):
        """play_simple_macro should return True when automation available"""
        tools.automation_available = True
        result = tools.play_simple_macro("test_macro")
        assert result is True
