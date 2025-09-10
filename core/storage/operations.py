"""
MinIO storage operations for task and pipeline files
"""
import os
import zipfile
import tempfile
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, BinaryIO
from io import BytesIO
from minio.error import S3Error
from loguru import logger

from .connection import get_minio_connection


class StorageOperations:
    """Storage operations manager"""
    
    def __init__(self):
        self.conn = get_minio_connection()
        self.bucket = self.conn.config.bucket
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _calculate_bytes_hash(self, data: bytes) -> str:
        """Calculate SHA256 hash of bytes"""
        return hashlib.sha256(data).hexdigest()
    
    def upload_task_package(self, task_id: str, task_folder: str) -> Optional[Dict[str, Any]]:
        """
        Upload task package as ZIP file
        
        Args:
            task_id: Unique task identifier
            task_folder: Path to task folder containing task.py, etc.
            
        Returns:
            Dict with storage info or None if failed
        """
        try:
            task_path = Path(task_folder)
            if not task_path.exists():
                raise FileNotFoundError(f"Task folder not found: {task_folder}")
            
            # Create temporary ZIP file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                zip_path = tmp_file.name
            
            try:
                # Create ZIP archive
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in task_path.rglob('*'):
                        if file_path.is_file():
                            # Add file to zip with relative path
                            arcname = file_path.relative_to(task_path)
                            zipf.write(file_path, arcname)
                
                # Calculate file info
                file_size = os.path.getsize(zip_path)
                file_hash = self._calculate_file_hash(zip_path)
                
                # Upload to MinIO
                object_name = f"tasks/{task_id}/{task_id}_v1.0.0.zip"
                
                with open(zip_path, 'rb') as file_data:
                    self.conn.client.put_object(
                        self.bucket,
                        object_name,
                        file_data,
                        file_size,
                        content_type='application/zip'
                    )
                
                logger.info(f"Uploaded task package: {object_name}")
                
                return {
                    "storage_path": object_name,
                    "file_hash": file_hash,
                    "file_size": file_size
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(zip_path):
                    os.unlink(zip_path)
                
        except Exception as e:
            logger.error(f"Failed to upload task package {task_id}: {e}")
            return None
    
    def upload_pipeline_package(self, pipeline_id: str, pipeline_folder: str) -> Optional[Dict[str, Any]]:
        """
        Upload pipeline package as ZIP file
        
        Args:
            pipeline_id: Unique pipeline identifier
            pipeline_folder: Path to pipeline folder
            
        Returns:
            Dict with storage info or None if failed
        """
        try:
            pipeline_path = Path(pipeline_folder)
            if not pipeline_path.exists():
                raise FileNotFoundError(f"Pipeline folder not found: {pipeline_folder}")
            
            # Create temporary ZIP file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                zip_path = tmp_file.name
            
            try:
                # Create ZIP archive
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in pipeline_path.rglob('*'):
                        if file_path.is_file():
                            # Add file to zip with relative path
                            arcname = file_path.relative_to(pipeline_path)
                            zipf.write(file_path, arcname)
                
                # Calculate file info
                file_size = os.path.getsize(zip_path)
                file_hash = self._calculate_file_hash(zip_path)
                
                # Upload to MinIO
                object_name = f"pipelines/{pipeline_id}/{pipeline_id}_v1.0.0.zip"
                
                with open(zip_path, 'rb') as file_data:
                    self.conn.client.put_object(
                        self.bucket,
                        object_name,
                        file_data,
                        file_size,
                        content_type='application/zip'
                    )
                
                logger.info(f"Uploaded pipeline package: {object_name}")
                
                return {
                    "storage_path": object_name,
                    "file_hash": file_hash,
                    "file_size": file_size
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(zip_path):
                    os.unlink(zip_path)
                
        except Exception as e:
            logger.error(f"Failed to upload pipeline package {pipeline_id}: {e}")
            return None
    
    def download_task_package(self, storage_path: str, extract_to: str) -> bool:
        """
        Download and extract task package
        
        Args:
            storage_path: MinIO object path
            extract_to: Local directory to extract to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            extract_path = Path(extract_to)
            extract_path.mkdir(parents=True, exist_ok=True)
            
            # Download file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                zip_path = tmp_file.name
            
            try:
                self.conn.client.fget_object(self.bucket, storage_path, zip_path)
                
                # Extract ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(extract_path)
                
                logger.info(f"Downloaded and extracted pipeline package to: {extract_path}")
                return True
                
            finally:
                # Clean up temporary file
                if os.path.exists(zip_path):
                    os.unlink(zip_path)
                
        except Exception as e:
            logger.error(f"Failed to download pipeline package {storage_path}: {e}")
            return False
    
    def verify_file_integrity(self, storage_path: str, expected_hash: str) -> bool:
        """
        Verify file integrity by comparing hash
        
        Args:
            storage_path: MinIO object path
            expected_hash: Expected SHA256 hash
            
        Returns:
            True if hash matches, False otherwise
        """
        try:
            # Download file to memory and calculate hash
            response = self.conn.client.get_object(self.bucket, storage_path)
            data = response.read()
            response.close()
            
            actual_hash = self._calculate_bytes_hash(data)
            return actual_hash == expected_hash
            
        except Exception as e:
            logger.error(f"Failed to verify file integrity {storage_path}: {e}")
            return False
    
    def list_task_packages(self, prefix: str = "tasks/") -> List[Dict[str, Any]]:
        """
        List all task packages in storage
        
        Args:
            prefix: Object prefix to filter
            
        Returns:
            List of package info dictionaries
        """
        try:
            objects = self.conn.client.list_objects(self.bucket, prefix=prefix, recursive=True)
            packages = []
            
            for obj in objects:
                if obj.object_name.endswith('.zip'):
                    packages.append({
                        "name": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "etag": obj.etag
                    })
            
            return packages
            
        except Exception as e:
            logger.error(f"Failed to list task packages: {e}")
            return []
    
    def list_pipeline_packages(self, prefix: str = "pipelines/") -> List[Dict[str, Any]]:
        """
        List all pipeline packages in storage
        
        Args:
            prefix: Object prefix to filter
            
        Returns:
            List of package info dictionaries
        """
        try:
            objects = self.conn.client.list_objects(self.bucket, prefix=prefix, recursive=True)
            packages = []
            
            for obj in objects:
                if obj.object_name.endswith('.zip'):
                    packages.append({
                        "name": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "etag": obj.etag
                    })
            
            return packages
            
        except Exception as e:
            logger.error(f"Failed to list pipeline packages: {e}")
            return []
    
    def delete_package(self, storage_path: str) -> bool:
        """
        Delete package from storage
        
        Args:
            storage_path: MinIO object path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn.client.remove_object(self.bucket, storage_path)
            logger.info(f"Deleted package: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete package {storage_path}: {e}")
            return False
    
    def get_package_info(self, storage_path: str) -> Optional[Dict[str, Any]]:
        """
        Get package information
        
        Args:
            storage_path: MinIO object path
            
        Returns:
            Package info dict or None if not found
        """
        try:
            stat = self.conn.client.stat_object(self.bucket, storage_path)
            return {
                "name": storage_path,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type
            }
            
        except Exception as e:
            logger.error(f"Failed to get package info {storage_path}: {e}")
            return None
    
    def upload_file(self, file_path: str, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Upload arbitrary file to storage
        
        Args:
            file_path: Local file path
            object_name: MinIO object name
            
        Returns:
            Upload info dict or None if failed
        """
        try:
            file_size = os.path.getsize(file_path)
            file_hash = self._calculate_file_hash(file_path)
            
            with open(file_path, 'rb') as file_data:
                self.conn.client.put_object(
                    self.bucket,
                    object_name,
                    file_data,
                    file_size
                )
            
            logger.info(f"Uploaded file: {object_name}")
            
            return {
                "storage_path": object_name,
                "file_hash": file_hash,
                "file_size": file_size
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            return None
    
    def download_file(self, object_name: str, file_path: str) -> bool:
        """
        Download file from storage
        
        Args:
            object_name: MinIO object name
            file_path: Local file path to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.conn.client.fget_object(self.bucket, object_name, file_path)
            logger.info(f"Downloaded file: {object_name} -> {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file {object_name}: {e}")
            return False
    
    def cleanup_old_packages(self, days: int = 30) -> int:
        """
        Cleanup old packages based on age
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of packages deleted
        """
        try:
            from datetime import datetime, timedelta
            
            threshold = datetime.utcnow() - timedelta(days=days)
            objects = self.conn.client.list_objects(self.bucket, recursive=True)
            deleted_count = 0
            
            for obj in objects:
                if obj.last_modified < threshold:
                    try:
                        self.conn.client.remove_object(self.bucket, obj.object_name)
                        deleted_count += 1
                        logger.info(f"Cleaned up old package: {obj.object_name}")
                    except Exception as e:
                        logger.error(f"Failed to delete old package {obj.object_name}: {e}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old packages: {e}")
            return 0



    
    def download_pipeline_package(self, storage_path: str, extract_to: str) -> bool:
        """
        Download and extract pipeline package
        
        Args:
            storage_path: MinIO object path
            extract_to: Local directory to extract to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            extract_path = Path(extract_to)
            extract_path.mkdir(parents=True, exist_ok=True)
            
            # Download file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                zip_path = tmp_file.name
            
            try:
                self.conn.client.fget_object(self.bucket, storage_path, zip_path)
                
                # Extract ZIP file
                # storage_ops = StorageOperations()
                with zipfile.ZipFile(zip_path,  'r') as zipf:
                    zipf.extractall(extract_path)
                
                logger.info(f"Downloaded and extracted task package to: {extract_path}")
                return True
                
            finally:
                # Clean up temporary file
                if os.path.exists(zip_path):
                    os.unlink(zip_path)
                
        except Exception as e:
            logger.error(f"Failed to download task package {storage_path}: {e}")
            return False
        

storage_ops = StorageOperations()