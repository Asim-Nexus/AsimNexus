#!/usr/bin/env python3
"""AsimNexus Database Layer
PostgreSQL + SQLite for local-first persistence
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "asimnexus.db"

class DatabaseLayer:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                profile TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                amount REAL,
                sector TEXT,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return {"id": row[0], "profile": row[1]} if row else None

# Singleton
_db = None

def get_db() -> DatabaseLayer:
    global _db
    if _db is None:
        _db = DatabaseLayer()
    return _db

__all__ = ["DatabaseLayer", "get_db"]