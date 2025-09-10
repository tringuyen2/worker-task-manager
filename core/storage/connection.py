"""
MinIO connection management for task storage
"""
from typing import Optional
from minio import Minio
from minio.error import S3Error
from loguru import logger

from ..config.models import MinIOConfig
from ..config.manager import get_config


class MinIOConnection:
    """MinIO connection manager"""
    
    def __init__(self, config: Optional[MinIOConfig] = None):
        self.config = config or get_config().worker.minio
        self._client: Optional[Minio] = None
        
    def connect(self) -> bool:
        """Establish MinIO connection"""
        try:
            self._client = Minio(
                self.config.endpoint,
                access_key=self.config.access_key,
                secret_key=self.config.secret_key,
                secure=self.config.secure,
                region=self.config.region
            )
            
            # Test connection by checking if bucket exists or create it
            if not self._client.bucket_exists(self.config.bucket):
                self._client.make_bucket(
                    self.config.bucket,
                    location=self.config.region
                )
                logger.info(f"Created MinIO bucket: {self.config.bucket}")
            
            logger.info(f"Connected to MinIO: {self.config.endpoint}/{self.config.bucket}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MinIO: {e}")
            return False
    
    def disconnect(self):
        """Close MinIO connection"""
        self._client = None
        logger.info("Disconnected from MinIO")
    
    @property
    def client(self) -> Minio:
        """Get MinIO client"""
        if not self._client:
            if not self.connect():
                raise ConnectionError("Failed to connect to MinIO")
        return self._client
    
    def health_check(self) -> bool:
        """Check MinIO connection health"""
        try:
            return self.client.bucket_exists(self.config.bucket)
        except Exception:
            return False
    
    def create_bucket_if_not_exists(self, bucket_name: Optional[str] = None) -> bool:
        """Create bucket if it doesn't exist"""
        try:
            bucket = bucket_name or self.config.bucket
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket, location=self.config.region)
                logger.info(f"Created bucket: {bucket}")
            return True
        except Exception as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            return False


# Global connection instance
_minio_connection: Optional[MinIOConnection] = None


def get_minio_connection() -> MinIOConnection:
    """Get global MinIO connection"""
    global _minio_connection
    if not _minio_connection:
        _minio_connection = MinIOConnection()
    return _minio_connection


def init_storage() -> bool:
    """Initialize storage connection"""
    try:
        conn = get_minio_connection()
        return conn.connect()
    except Exception as e:
        logger.error(f"Failed to initialize storage: {e}")
        return False