#!/usr/bin/env python3
"""AsimNexus Disaster Recovery - Automated Backup System"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class DisasterRecoveryManager:
    """Manages automated backups and disaster recovery procedures."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a full system backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        items_backed_up = []
        errors = []
        
        # Backup data directory
        data_dir = Path("data")
        if data_dir.exists():
            try:
                shutil.copytree(data_dir, backup_path / "data", dirs_exist_ok=True)
                items_backed_up.append("data/")
            except Exception as e:
                errors.append(f"data: {str(e)}")
        
        # Backup critical config files
        for config_file in [".env", "kilo.json", "docker-compose.yml"]:
            config_path = Path(config_file)
            if config_path.exists():
                try:
                    shutil.copy(config_path, backup_path / f"config_{config_file}")
                    items_backed_up.append(config_file)
                except Exception as e:
                    errors.append(f"{config_file}: {str(e)}")
        
        # Create backup manifest
        manifest = {
            "backup_name": backup_name,
            "created_at": timestamp,
            "items": items_backed_up,
            "errors": errors,
        }
        
        with open(backup_path / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
        
        return {
            "status": "success",
            "backup_name": backup_name,
            "items_backed_up": items_backed_up,
            "errors": errors,
        }
    
    def list_backups(self) -> list:
        """List all available backups."""
        backups = []
        for backup in self.backup_dir.iterdir():
            if backup.is_dir():
                manifest_path = backup / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        backups.append(json.load(f))
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """Restore from a backup."""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            return {"status": "error", "error": f"Backup {backup_name} not found"}
        
        restored = []
        errors = []
        
        # Restore data directory
        backed_up_data = backup_path / "data"
        if backed_up_data.exists():
            try:
                data_dir = Path("data")
                shutil.rmtree(data_dir, ignore_errors=True)
                shutil.copytree(backed_up_data, data_dir)
                restored.append("data/")
            except Exception as e:
                errors.append(f"data: {str(e)}")
        
        return {
            "status": "success" if not errors else "partial",
            "restored_items": restored,
            "errors": errors,
        }


# Singleton instance
_drm: Optional[DisasterRecoveryManager] = None


def get_disaster_recovery_manager() -> DisasterRecoveryManager:
    global _drm
    if _drm is None:
        _drm = DisasterRecoveryManager()
    return _drm