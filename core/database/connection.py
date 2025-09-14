"""
MongoDB connection management
"""
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from loguru import logger

from ..config.models import MongoDBConfig
from ..config.manager import get_config


class MongoDBConnection:
    """MongoDB connection manager"""
    
    def __init__(self, config: Optional[MongoDBConfig] = None):
        self.config = config or get_config().worker.mongodb
        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None
        
    def connect(self) -> bool:
        """Establish MongoDB connection"""
        try:
            self._client = MongoClient(
                self.config.connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test connection
            self._client.admin.command('ping')
            self._database = self._client[self.config.database]
            
            logger.info(f"Connected to MongoDB: {self.config.host}:{self.config.port}/{self.config.database}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("Disconnected from MongoDB")
    
    @property
    def client(self) -> MongoClient:
        """Get MongoDB client"""
        if self._client is None:
            if not self.connect():
                raise ConnectionError("Failed to connect to MongoDB")
        return self._client
    
    @property
    def database(self) -> Database:
        """Get database instance"""
        if self._database is None:
            if not self.connect():
                raise ConnectionError("Failed to connect to MongoDB")
        return self._database
    
    def get_collection(self, collection_name: str) -> Collection:
        """Get collection instance"""
        # logger.info(f"self.database: {self.database}")
        return self.database[collection_name]
    
    def create_indexes(self):
        """Create database indexes for performance"""
        try:
            db = self.database
            
            # Task metadata indexes
            tasks = db.task_metadata
            tasks.create_index([("task_id", 1)], unique=True)
            tasks.create_index([("is_active", 1)])
            tasks.create_index([("category", 1)])
            tasks.create_index([("tags", 1)])
            tasks.create_index([("created_at", -1)])
            
            # Pipeline metadata indexes
            pipelines = db.pipeline_metadata
            pipelines.create_index([("pipeline_id", 1)], unique=True)
            pipelines.create_index([("is_active", 1)])
            pipelines.create_index([("category", 1)])
            pipelines.create_index([("tags", 1)])
            pipelines.create_index([("created_at", -1)])
            
            # Execution records indexes
            executions = db.execution_records
            executions.create_index([("execution_id", 1)], unique=True)
            executions.create_index([("celery_task_id", 1)], unique=True)
            executions.create_index([("task_id", 1)])
            executions.create_index([("pipeline_id", 1)])
            executions.create_index([("worker_id", 1)])
            executions.create_index([("status", 1)])
            executions.create_index([("created_at", -1)])
            executions.create_index([("started_at", -1)])
            executions.create_index([("completed_at", -1)])
            
            # Worker status indexes
            workers = db.worker_status
            workers.create_index([("worker_id", 1)], unique=True)
            workers.create_index([("is_active", 1)])
            workers.create_index([("last_heartbeat", -1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
    
    def health_check(self) -> bool:
        """Check MongoDB connection health"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False


# Global connection instance
_mongodb_connection: Optional[MongoDBConnection] = None


def get_mongodb_connection() -> MongoDBConnection:
    """Get global MongoDB connection"""
    global _mongodb_connection
    if not _mongodb_connection:
        _mongodb_connection = MongoDBConnection()
    return _mongodb_connection


def init_database() -> bool:
    """Initialize database connection and indexes"""
    try:
        conn = get_mongodb_connection()
        if conn.connect():
            conn.create_indexes()
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False