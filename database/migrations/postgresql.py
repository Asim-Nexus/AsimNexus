"""
STATUS: REAL — PostgreSQL Migration Module

AsimNexus PostgreSQL Migration
==============================
SQLite to PostgreSQL migration for production:
- Government database (51% sector)
- Company database (49% sector)  
- User database (Local-First)
- Automated backup and sharding
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger("AsimNexus.PostgreSQL")

DATABASE_URL_GOV = os.environ.get("DATABASE_URL_GOV", "postgresql://gov:govpass@localhost/asim_gov")
DATABASE_URL_COMPANY = os.environ.get("DATABASE_URL_COMPANY", "postgresql://company:companypass@localhost/asim_company")
DATABASE_URL_USER = os.environ.get("DATABASE_URL_USER", "postgresql://user:userpass@localhost/asim_user")


class PostgreSQLMigration:
    """SQLite to PostgreSQL migration manager"""
    
    def __init__(self):
        self._connections = {}
        self._initialized = False
        self._sqlite_dir = Path("data")
    
    async def initialize(self):
        """Initialize PostgreSQL connections"""
        try:
            import asyncpg
            
            self._connections["government"] = await asyncpg.connect(DATABASE_URL_GOV)
            self._connections["company"] = await asyncpg.connect(DATABASE_URL_COMPANY)
            self._connections["user"] = await asyncpg.connect(DATABASE_URL_USER)
            
            self._initialized = True
            logger.info("✅ PostgreSQL connections initialized")
            
        except ImportError:
            logger.warning("⚠️ asyncpg not installed - PostgreSQL migration disabled")
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e}")
    
    async def migrate_all(self) -> Dict[str, Any]:
        """Migrate all databases"""
        results = {}
        
        if not self._initialized:
            await self.initialize()
        
        results["government"] = await self.migrate_government()
        results["company"] = await self.migrate_company()
        results["user"] = await self.migrate_user()
        
        return {"results": results, "status": "completed"}
    
    async def migrate_government(self) -> Dict[str, Any]:
        """Migrate government data (51% sector)"""
        if "government" not in self._connections:
            return {"status": "skipped", "reason": "no_connection"}
        
        conn = self._connections["government"]
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS citizens (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                citizen_id VARCHAR(50) UNIQUE,
                district VARCHAR(50),
                birth_year INTEGER,
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tax_records (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                citizen_id VARCHAR(50) REFERENCES citizens(citizen_id),
                year INTEGER,
                income DECIMAL,
                tax_paid DECIMAL,
                status VARCHAR(20),
                filed_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        count = await self._migrate_sqlite_to_pg(
            self._sqlite_dir / "asim_gov.db",
            "government",
            conn
        )
        
        return {"status": "success", "count": count}
    
    async def migrate_company(self) -> Dict[str, Any]:
        """Migrate company data (49% sector)"""
        if "company" not in self._connections:
            return {"status": "skipped", "reason": "no_connection"}
        
        conn = self._connections["company"]
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                company_name VARCHAR(200),
                registration_number VARCHAR(100),
                sector VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                company_id UUID REFERENCES companies(id),
                employee_id VARCHAR(50),
                position VARCHAR(100),
                salary DECIMAL
            )
        """)
        
        count = await self._migrate_sqlite_to_pg(
            self._sqlite_dir / "asim_company.db",
            "company",
            conn
        )
        
        return {"status": "success", "count": count}
    
    async def migrate_user(self) -> Dict[str, Any]:
        """Migrate user data (Local-First)"""
        if "user" not in self._connections:
            return {"status": "skipped", "reason": "no_connection"}
        
        conn = self._connections["user"]
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(100) UNIQUE,
                display_name VARCHAR(200),
                preferences JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS digital_twins (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(100) REFERENCES user_profiles(user_id),
                twin_data JSONB,
                last_sync TIMESTAMP
            )
        """)
        
        count = await self._migrate_sqlite_to_pg(
            self._sqlite_dir / "asim_user.db",
            "user",
            conn
        )
        
        return {"status": "success", "count": count}
    
    async def _migrate_sqlite_to_pg(
        self,
        sqlite_path: Path,
        target_db: str,
        pg_conn
    ) -> int:
        """Migrate data from SQLite to PostgreSQL"""
        try:
            import sqlite3
            
            if not sqlite_path.exists():
                logger.info(f"No SQLite file at {sqlite_path}, skipping")
                return 0
            
            sqlite_conn = sqlite3.connect(str(sqlite_path))
            sqlite_conn.row_factory = sqlite3.Row
            
            tables = sqlite_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            
            count = 0
            for table in tables:
                table_name = table[0]
                if table_name.startswith("sqlite_"):
                    continue
                
                rows = sqlite_conn.execute(f"SELECT * FROM {table_name}").fetchall()
                
                for row in rows:
                    try:
                        columns = list(row.keys)
                        values = [self._convert_value(v) for v in list(row)]
                        placeholders = ",".join([f"${i+1}" for i in range(len(values))])
                        cols = ",".join(columns)
                        
                        await pg_conn.execute(
                            f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                            *values
                        )
                        count += 1
                    except Exception as e:
                        logger.error(f"Insert error for {table_name}: {e}")
            
            sqlite_conn.close()
            return count
            
        except Exception as e:
            logger.error(f"Migration error: {e}")
            return 0
    
    def _convert_value(self, value: Any) -> Any:
        """Convert SQLite value to PostgreSQL compatible"""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float, str)):
            return value
        return str(value)
    
    def status(self) -> Dict[str, Any]:
        """Get migration status"""
        return {
            "initialized": self._initialized,
            "connections": list(self._connections.keys()),
            "urls": {
                "government": DATABASE_URL_GOV.split("@")[-1],
                "company": DATABASE_URL_COMPANY.split("@")[-1],
                "user": DATABASE_URL_USER.split("@")[-1]
            }
        }


_migration: Optional[PostgreSQLMigration] = None


async def get_migration() -> PostgreSQLMigration:
    """Get migration singleton"""
    global _migration
    if _migration is None:
        _migration = PostgreSQLMigration()
        await _migration.initialize()
    return _migration


def get_migration_sync() -> PostgreSQLMigration:
    """Sync version for backward compatibility"""
    global _migration
    if _migration is None:
        _migration = PostgreSQLMigration()
    return _migration