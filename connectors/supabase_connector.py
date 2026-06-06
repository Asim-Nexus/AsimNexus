
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Supabase Connector
============================
Connector for Supabase API
Provides integration with Supabase for database, auth, and storage
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("SupabaseConnector")

# Try to import supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("supabase not installed. Install with: pip install supabase")

# Try to import psycopg2 for direct database access
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not installed. Install with: pip install psycopg2-binary")


class SupabaseConnector:
    """
    Supabase Connector
    
    Provides:
    - Database operations (via Supabase client)
    - Authentication
    - Storage operations
    - Realtime subscriptions
    - Direct PostgreSQL access
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        database_url: Optional[str] = None
    ):
        self.logger = logging.getLogger("SupabaseConnector")
        self.url = url
        self.key = key
        self.database_url = database_url
        self.client: Optional[Client] = None
        self.direct_connection = None
        self.configured = False
        
        if SUPABASE_AVAILABLE and url and key:
            try:
                self.client = create_client(url, key)
                self.configured = True
                self.logger.info("Supabase client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Supabase client: {e}")
        
        if PSYCOPG2_AVAILABLE and database_url:
            try:
                self.direct_connection = psycopg2.connect(database_url)
                self.logger.info("Supabase direct connection initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize direct connection: {e}")
    
    def is_available(self) -> bool:
        """Check if connector is available"""
        return self.configured or self.direct_connection is not None
    
    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict] = None,
        limit: Optional[int] = None
    ) -> Optional[List[Dict]]:
        """
        Select data from a table
        
        Args:
            table: Table name
            columns: Columns to select
            filters: Filter conditions
            limit: Maximum number of rows
            
        Returns:
            List of rows
        """
        if not self.is_available() or not self.client:
            self.logger.warning("Supabase connector not available")
            return None
        
        try:
            query = self.client.table(table).select(columns)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            self.logger.error(f"Failed to select data: {e}")
            return None
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Optional[Dict]:
        """
        Insert data into a table
        
        Args:
            table: Table name
            data: Data to insert
            
        Returns:
            Inserted row
        """
        if not self.is_available() or not self.client:
            self.logger.warning("Supabase connector not available")
            return None
        
        try:
            result = self.client.table(table).insert(data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            self.logger.error(f"Failed to insert data: {e}")
            return None
    
    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> Optional[List[Dict]]:
        """
        Update data in a table
        
        Args:
            table: Table name
            data: Data to update
            filters: Filter conditions
            
        Returns:
            Updated rows
        """
        if not self.is_available() or not self.client:
            self.logger.warning("Supabase connector not available")
            return None
        
        try:
            query = self.client.table(table).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            self.logger.error(f"Failed to update data: {e}")
            return None
    
    async def delete(
        self,
        table: str,
        filters: Dict[str, Any]
    ) -> bool:
        """
        Delete data from a table
        
        Args:
            table: Table name
            filters: Filter conditions
            
        Returns:
            Success status
        """
        if not self.is_available() or not self.client:
            self.logger.warning("Supabase connector not available")
            return False
        
        try:
            query = self.client.table(table).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            query.execute()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete data: {e}")
            return False
    
    async def execute_sql(self, sql: str) -> Optional[List[Dict]]:
        """
        Execute raw SQL query (requires direct connection)
        
        Args:
            sql: SQL query
            
        Returns:
            Query results
        """
        if not self.direct_connection:
            self.logger.warning("Direct connection not available")
            return None
        
        try:
            cursor = self.direct_connection.cursor()
            cursor.execute(sql)
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            cursor.close()
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to execute SQL: {e}")
            return None
    
    async def upload_file(
        self,
        bucket: str,
        path: str,
        file_content: bytes,
        content_type: str = "application/octet-stream"
    ) -> bool:
        """
        Upload a file to Supabase storage
        
        Args:
            bucket: Storage bucket name
            path: File path in bucket
            file_content: File content
            content_type: MIME type
            
        Returns:
            Success status
        """
        if not self.is_available() or not self.client:
            self.logger.warning("Supabase connector not available")
            return False
        
        try:
            self.client.storage.from_(bucket).upload(
                path,
                file_content,
                {"content-type": content_type}
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload file: {e}")
            return False
    
    async def get_file_url(
        self,
        bucket: str,
        path: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Get a signed URL for a file
        
        Args:
            bucket: Storage bucket name
            path: File path in bucket
            expires_in: URL expiration time in seconds
            
        Returns:
            Signed URL
        """
        if not self.is_available() or not self.client:
            self.logger.warning("Supabase connector not available")
            return None
        
        try:
            url = self.client.storage.from_(bucket).create_signed_url(
                path,
                expires_in
            )
            return url
            
        except Exception as e:
            self.logger.error(f"Failed to get file URL: {e}")
            return None
    
    async def auth_sign_up(self, email: str, password: str) -> Optional[Dict]:
        """
        Sign up a new user
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User data
        """
        if not self.is_available() or not self.client:
            self.logger.warning("Supabase connector not available")
            return None
        
        try:
            result = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            return result.user.dict() if result.user else None
            
        except Exception as e:
            self.logger.error(f"Failed to sign up: {e}")
            return None
    
    async def auth_sign_in(self, email: str, password: str) -> Optional[Dict]:
        """
        Sign in a user
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Session data
        """
        if not self.is_available() or not self.client:
            self.logger.warning("Supabase connector not available")
            return None
        
        try:
            result = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return result.session.dict() if result.session else None
            
        except Exception as e:
            self.logger.error(f"Failed to sign in: {e}")
            return None
    
    def close(self):
        """Close connections"""
        if self.direct_connection:
            self.direct_connection.close()
            self.logger.info("Direct connection closed")
    
    def get_stats(self) -> Dict:
        """Get connector statistics"""
        return {
            "available": self.is_available(),
            "supabase_installed": SUPABASE_AVAILABLE,
            "psycopg2_installed": PSYCOPG2_AVAILABLE,
            "configured": self.configured,
            "has_client": self.client is not None,
            "has_direct_connection": self.direct_connection is not None,
            "url": self.url
        }
