
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS MongoDB Connector
============================
Connector for MongoDB Atlas
Provides integration with MongoDB for database operations
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("MongoDBConnector")

# Try to import pymongo
try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    logger.warning("pymongo not installed. Install with: pip install pymongo")


class MongoDBConnector:
    """
    MongoDB Connector
    
    Provides:
    - Connect to MongoDB Atlas
    - Insert documents
    - Find documents
    - Update documents
    - Delete documents
    - Aggregate queries
    - Index management
    """
    
    def __init__(self, connection_string: Optional[str] = None, database_name: str = "asimnexus"):
        self.logger = logging.getLogger("MongoDBConnector")
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.database = None
        self.configured = False
        
        if PYMONGO_AVAILABLE and connection_string:
            try:
                self.client = MongoClient(connection_string)
                # Test connection
                self.client.admin.command('ping')
                self.database = self.client[database_name]
                self.configured = True
                self.logger.info(f"MongoDB connector initialized (database: {database_name})")
            except Exception as e:
                self.logger.error(f"Failed to initialize MongoDB: {e}")
    
    def is_available(self) -> bool:
        """Check if connector is available"""
        return PYMONGO_AVAILABLE and self.configured
    
    async def insert_one(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> Optional[str]:
        """
        Insert a single document
        
        Args:
            collection: Collection name
            document: Document to insert
            
        Returns:
            Inserted document ID
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            result = self.database[collection].insert_one(document)
            return str(result.inserted_id)
            
        except PyMongoError as e:
            self.logger.error(f"Failed to insert document: {e}")
            return None
    
    async def insert_many(
        self,
        collection: str,
        documents: List[Dict[str, Any]]
    ) -> Optional[List[str]]:
        """
        Insert multiple documents
        
        Args:
            collection: Collection name
            documents: List of documents to insert
            
        Returns:
            List of inserted document IDs
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            result = self.database[collection].insert_many(documents)
            return [str(id) for id in result.inserted_ids]
            
        except PyMongoError as e:
            self.logger.error(f"Failed to insert documents: {e}")
            return None
    
    async def find_one(
        self,
        collection: str,
        filter: Optional[Dict] = None,
        projection: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Find a single document
        
        Args:
            collection: Collection name
            filter: Query filter
            projection: Fields to include/exclude
            
        Returns:
            Found document or None
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            document = self.database[collection].find_one(
                filter or {},
                projection
            )
            
            if document:
                # Convert ObjectId to string
                document['_id'] = str(document['_id'])
            
            return document
            
        except PyMongoError as e:
            self.logger.error(f"Failed to find document: {e}")
            return None
    
    async def find_many(
        self,
        collection: str,
        filter: Optional[Dict] = None,
        projection: Optional[Dict] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        sort: Optional[List[tuple]] = None
    ) -> Optional[List[Dict]]:
        """
        Find multiple documents
        
        Args:
            collection: Collection name
            filter: Query filter
            projection: Fields to include/exclude
            limit: Maximum number of documents
            skip: Number of documents to skip
            sort: Sort specification
            
        Returns:
            List of documents
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            query = self.database[collection].find(filter or {}, projection)
            
            if sort:
                query = query.sort(sort)
            if skip:
                query = query.skip(skip)
            if limit:
                query = query.limit(limit)
            
            documents = list(query)
            
            # Convert ObjectIds to strings
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            
            return documents
            
        except PyMongoError as e:
            self.logger.error(f"Failed to find documents: {e}")
            return None
    
    async def update_one(
        self,
        collection: str,
        filter: Dict,
        update: Dict,
        upsert: bool = False
    ) -> Optional[int]:
        """
        Update a single document
        
        Args:
            collection: Collection name
            filter: Query filter
            update: Update operations
            upsert: Insert if not exists
            
        Returns:
            Number of modified documents
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            result = self.database[collection].update_one(
                filter,
                update,
                upsert=upsert
            )
            return result.modified_count
            
        except PyMongoError as e:
            self.logger.error(f"Failed to update document: {e}")
            return None
    
    async def update_many(
        self,
        collection: str,
        filter: Dict,
        update: Dict
    ) -> Optional[int]:
        """
        Update multiple documents
        
        Args:
            collection: Collection name
            filter: Query filter
            update: Update operations
            
        Returns:
            Number of modified documents
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            result = self.database[collection].update_many(filter, update)
            return result.modified_count
            
        except PyMongoError as e:
            self.logger.error(f"Failed to update documents: {e}")
            return None
    
    async def delete_one(
        self,
        collection: str,
        filter: Dict
    ) -> Optional[int]:
        """
        Delete a single document
        
        Args:
            collection: Collection name
            filter: Query filter
            
        Returns:
            Number of deleted documents
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            result = self.database[collection].delete_one(filter)
            return result.deleted_count
            
        except PyMongoError as e:
            self.logger.error(f"Failed to delete document: {e}")
            return None
    
    async def delete_many(
        self,
        collection: str,
        filter: Dict
    ) -> Optional[int]:
        """
        Delete multiple documents
        
        Args:
            collection: Collection name
            filter: Query filter
            
        Returns:
            Number of deleted documents
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            result = self.database[collection].delete_many(filter)
            return result.deleted_count
            
        except PyMongoError as e:
            self.logger.error(f"Failed to delete documents: {e}")
            return None
    
    async def count_documents(
        self,
        collection: str,
        filter: Optional[Dict] = None
    ) -> Optional[int]:
        """
        Count documents in a collection
        
        Args:
            collection: Collection name
            filter: Query filter
            
        Returns:
            Number of documents
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            count = self.database[collection].count_documents(filter or {})
            return count
            
        except PyMongoError as e:
            self.logger.error(f"Failed to count documents: {e}")
            return None
    
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict]
    ) -> Optional[List[Dict]]:
        """
        Execute aggregation pipeline
        
        Args:
            collection: Collection name
            pipeline: Aggregation pipeline
            
        Returns:
            Aggregation results
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            results = list(self.database[collection].aggregate(pipeline))
            
            # Convert ObjectIds to strings
            for doc in results:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            
            return results
            
        except PyMongoError as e:
            self.logger.error(f"Failed to execute aggregation: {e}")
            return None
    
    async def create_index(
        self,
        collection: str,
        keys: Dict,
        unique: bool = False
    ) -> bool:
        """
        Create an index on a collection
        
        Args:
            collection: Collection name
            keys: Index keys
            unique: Whether index should be unique
            
        Returns:
            Success status
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return False
        
        try:
            self.database[collection].create_index(keys, unique=unique)
            return True
            
        except PyMongoError as e:
            self.logger.error(f"Failed to create index: {e}")
            return False
    
    async def list_collections(self) -> Optional[List[str]]:
        """
        List all collections in the database
        
        Returns:
            List of collection names
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return None
        
        try:
            collections = self.database.list_collection_names()
            return collections
            
        except PyMongoError as e:
            self.logger.error(f"Failed to list collections: {e}")
            return None
    
    async def drop_collection(self, collection: str) -> bool:
        """
        Drop a collection
        
        Args:
            collection: Collection name
            
        Returns:
            Success status
        """
        if not self.is_available():
            self.logger.warning("MongoDB connector not available")
            return False
        
        try:
            self.database[collection].drop()
            return True
            
        except PyMongoError as e:
            self.logger.error(f"Failed to drop collection: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")
    
    def get_stats(self) -> Dict:
        """Get connector statistics"""
        return {
            "available": self.is_available(),
            "pymongo_installed": PYMONGO_AVAILABLE,
            "configured": self.configured,
            "database_name": self.database_name,
            "has_client": self.client is not None,
            "has_database": self.database is not None
        }
