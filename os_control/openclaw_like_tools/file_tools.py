
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS OpenClaw File Tools
Capability-based file operations with safety checks
"""

import os
import json
import logging
import shutil
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class FileOperation(Enum):
    """File operation types"""
    LIST = "list"
    READ = "read"
    WRITE = "write"
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    CREATE_DIR = "create_dir"
    GET_INFO = "get_info"

@dataclass
class FileOperationResult:
    """Result of file operation"""
    success: bool
    operation: FileOperation
    path: str
    message: str
    data: Any = None
    error: Optional[str] = None

class FileTools:
    """Safe file operations with capability checks"""
    
    def __init__(self):
        self.logger = logging.getLogger("FileTools")
        self.allowed_extensions = {
            '.txt', '.json', '.py', '.md', '.csv', '.log',
            '.html', '.css', '.js', '.xml', '.yaml', '.yml'
        }
        self.restricted_paths = [
            'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
            'C:\\Users\\Default', 'C:\\ProgramData'
        ]
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def _is_path_safe(self, path: str) -> tuple[bool, str]:
        """Check if path is safe for operations"""
        try:
            # Normalize path
            abs_path = os.path.abspath(path)
            
            # Check restricted paths
            for restricted in self.restricted_paths:
                if abs_path.lower().startswith(restricted.lower()):
                    return False, f"Access to restricted path: {restricted}"
            
            # Check if path exists and is accessible
            if os.path.exists(abs_path):
                if not os.access(abs_path, os.R_OK):
                    return False, "Path not readable"
            
            return True, "Path is safe"
            
        except Exception as e:
            return False, f"Path validation error: {str(e)}"
    
    def _check_file_safety(self, path: str, operation: FileOperation) -> tuple[bool, str]:
        """Check file safety for operations"""
        safe, message = self._is_path_safe(path)
        if not safe:
            return False, message
        
        # Check extension for write operations (even for new files)
        if operation == FileOperation.WRITE:
            ext = os.path.splitext(path)[1].lower()
            if ext not in self.allowed_extensions:
                return False, f"File type not allowed: {ext}"
        
        if operation in [FileOperation.READ, FileOperation.WRITE, FileOperation.DELETE]:
            if os.path.isfile(path):
                # Check file size
                try:
                    file_size = os.path.getsize(path)
                    if file_size > self.max_file_size:
                        return False, f"File too large: {file_size} bytes"
                except OSError as e:
                    self.logger.debug(f"Cannot access file size: {e}")
                    return False, "Cannot access file size"
        
        return True, "File is safe"
    
    def list_directory(self, path: str = ".", show_hidden: bool = False) -> FileOperationResult:
        """List directory contents"""
        try:
            safe, message = self._is_path_safe(path)
            if not safe:
                return FileOperationResult(False, FileOperation.LIST, path, message)
            
            if not os.path.exists(path):
                return FileOperationResult(False, FileOperation.LIST, path, "Path does not exist")
            
            if not os.path.isdir(path):
                return FileOperationResult(False, FileOperation.LIST, path, "Path is not a directory")
            
            items = []
            for item in os.listdir(path):
                if not show_hidden and item.startswith('.'):
                    continue
                
                item_path = os.path.join(path, item)
                try:
                    stat = os.stat(item_path)
                    items.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size": stat.st_size if os.path.isfile(item_path) else 0,
                        "modified": stat.st_mtime,
                        "readable": os.access(item_path, os.R_OK),
                        "writable": os.access(item_path, os.W_OK)
                    })
                except Exception as e:
                    self.logger.debug(f"Cannot access item: {e}")
                    items.append({
                        "name": item,
                        "type": "unknown",
                        "size": 0,
                        "modified": 0,
                        "readable": False,
                        "writable": False
                    })
            
            return FileOperationResult(
                True, FileOperation.LIST, path, 
                f"Listed {len(items)} items", items
            )
            
        except Exception as e:
            return FileOperationResult(False, FileOperation.LIST, path, f"List failed: {str(e)}", error=str(e))
    
    def read_file(self, path: str, max_lines: int = 1000) -> FileOperationResult:
        """Read file content safely"""
        try:
            safe, message = self._check_file_safety(path, FileOperation.READ)
            if not safe:
                return FileOperationResult(False, FileOperation.READ, path, message)
            
            if not os.path.isfile(path):
                return FileOperationResult(False, FileOperation.READ, path, "Path is not a file")
            
            # Read file with size limit
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append("... (truncated)")
                        break
                    lines.append(line.rstrip('\n'))
            
            content = '\n'.join(lines)
            
            return FileOperationResult(
                True, FileOperation.READ, path,
                f"Read {len(lines)} lines", content
            )
            
        except Exception as e:
            return FileOperationResult(False, FileOperation.READ, path, f"Read failed: {str(e)}", error=str(e))
    
    def write_file_safe(self, path: str, content: str, backup: bool = True) -> FileOperationResult:
        """Write file content safely with backup"""
        try:
            safe, message = self._check_file_safety(path, FileOperation.WRITE)
            if not safe:
                return FileOperationResult(False, FileOperation.WRITE, path, message)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Create backup if file exists
            if backup and os.path.exists(path):
                backup_path = f"{path}.backup.{int(time.time())}"
                shutil.copy2(path, backup_path)
                self.logger.info(f"Created backup: {backup_path}")
            
            # Write content
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return FileOperationResult(
                True, FileOperation.WRITE, path,
                f"Written {len(content)} characters"
            )
            
        except Exception as e:
            return FileOperationResult(False, FileOperation.WRITE, path, f"Write failed: {str(e)}", error=str(e))
    
    def copy_file(self, src: str, dst: str) -> FileOperationResult:
        """Copy file safely"""
        try:
            # Check source
            safe_src, msg_src = self._check_file_safety(src, FileOperation.READ)
            if not safe_src:
                return FileOperationResult(False, FileOperation.COPY, src, f"Source unsafe: {msg_src}")
            
            # Check destination
            safe_dst, msg_dst = self._check_file_safety(dst, FileOperation.WRITE)
            if not safe_dst:
                return FileOperationResult(False, FileOperation.COPY, dst, f"Destination unsafe: {msg_dst}")
            
            if not os.path.isfile(src):
                return FileOperationResult(False, FileOperation.COPY, src, "Source is not a file")
            
            # Create destination directory
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            
            # Copy file
            shutil.copy2(src, dst)
            
            return FileOperationResult(
                True, FileOperation.COPY, src,
                f"Copied to {dst}"
            )
            
        except Exception as e:
            return FileOperationResult(False, FileOperation.COPY, src, f"Copy failed: {str(e)}", error=str(e))
    
    def move_file(self, src: str, dst: str) -> FileOperationResult:
        """Move file safely"""
        try:
            # Check source
            safe_src, msg_src = self._is_path_safe(src)
            if not safe_src:
                return FileOperationResult(False, FileOperation.MOVE, src, f"Source unsafe: {msg_src}")
            
            # Check destination
            safe_dst, msg_dst = self._is_path_safe(dst)
            if not safe_dst:
                return FileOperationResult(False, FileOperation.MOVE, dst, f"Destination unsafe: {msg_dst}")
            
            if not os.path.exists(src):
                return FileOperationResult(False, FileOperation.MOVE, src, "Source does not exist")
            
            # Create destination directory
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            
            # Move file
            shutil.move(src, dst)
            
            return FileOperationResult(
                True, FileOperation.MOVE, src,
                f"Moved to {dst}"
            )
            
        except Exception as e:
            return FileOperationResult(False, FileOperation.MOVE, src, f"Move failed: {str(e)}", error=str(e))
    
    def delete_file_safe(self, path: str, confirm: bool = False) -> FileOperationResult:
        """Delete file safely with confirmation"""
        try:
            if not confirm:
                return FileOperationResult(False, FileOperation.DELETE, path, "Deletion requires confirmation")
            
            safe, message = self._check_file_safety(path, FileOperation.DELETE)
            if not safe:
                return FileOperationResult(False, FileOperation.DELETE, path, message)
            
            if not os.path.exists(path):
                return FileOperationResult(False, FileOperation.DELETE, path, "Path does not exist")
            
            # Move to recycle bin instead of permanent delete
            import send2trash
            send2trash.send2trash(path)
            
            return FileOperationResult(
                True, FileOperation.DELETE, path,
                "Moved to recycle bin"
            )
            
        except ImportError:
            # Fallback to permanent delete if send2trash not available
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
            
            return FileOperationResult(
                True, FileOperation.DELETE, path,
                "Permanently deleted (send2trash not available)"
            )
            
        except Exception as e:
            return FileOperationResult(False, FileOperation.DELETE, path, f"Delete failed: {str(e)}", error=str(e))
    
    def create_directory(self, path: str) -> FileOperationResult:
        """Create directory"""
        try:
            safe, message = self._is_path_safe(path)
            if not safe:
                return FileOperationResult(False, FileOperation.CREATE_DIR, path, message)
            
            os.makedirs(path, exist_ok=True)
            
            return FileOperationResult(
                True, FileOperation.CREATE_DIR, path,
                "Directory created"
            )
            
        except Exception as e:
            return FileOperationResult(False, FileOperation.CREATE_DIR, path, f"Create failed: {str(e)}", error=str(e))
    
    def get_file_info(self, path: str) -> FileOperationResult:
        """Get file/directory information"""
        try:
            safe, message = self._is_path_safe(path)
            if not safe:
                return FileOperationResult(False, FileOperation.GET_INFO, path, message)
            
            if not os.path.exists(path):
                return FileOperationResult(False, FileOperation.GET_INFO, path, "Path does not exist")
            
            stat = os.stat(path)
            
            info = {
                "path": path,
                "type": "directory" if os.path.isdir(path) else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "readable": os.access(path, os.R_OK),
                "writable": os.access(path, os.W_OK),
                "executable": os.access(path, os.X_OK)
            }
            
            if os.path.isfile(path):
                ext = os.path.splitext(path)[1].lower()
                info["extension"] = ext
                info["allowed_type"] = ext in self.allowed_extensions
            
            return FileOperationResult(
                True, FileOperation.GET_INFO, path,
                "File info retrieved", info
            )
            
        except Exception as e:
            return FileOperationResult(False, FileOperation.GET_INFO, path, f"Info failed: {str(e)}", error=str(e))

# Global file tools instance
file_tools = FileTools()
