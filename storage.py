from minio import Minio
from minio.error import S3Error
import os
import zipfile
import tempfile
import shutil
from typing import Optional, List
import logging
from config import WorkerConfig

logger = logging.getLogger(__name__)

class StorageManager:
    """Quản lý storage operations với MinIO"""
    
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.client: Optional[Minio] = None
        self.bucket_name = config.minio["bucket"]
        self.connect()
    
    def connect(self) -> bool:
        """Kết nối tới MinIO"""
        try:
            minio_config = self.config.minio
            
            self.client = Minio(
                minio_config["endpoint"],
                access_key=minio_config["access_key"],
                secret_key=minio_config["secret_key"],
                secure=minio_config.get("secure", False)
            )
            
            # Test connection
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"✅ Created bucket: {self.bucket_name}")
            
            logger.info("✅ Connected to MinIO successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MinIO: {e}")
            return False
    
    def upload_task_zip(self, task_id: str, zip_path: str) -> bool:
        """Upload task zip file lên MinIO"""
        try:
            if not os.path.exists(zip_path):
                logger.error(f"❌ Zip file not found: {zip_path}")
                return False
            
            object_name = f"tasks/{task_id}.zip"
            
            # Upload file
            self.client.fput_object(
                self.bucket_name,
                object_name,
                zip_path,
                content_type="application/zip"
            )
            
            logger.info(f"✅ Uploaded task zip: {task_id}")
            return True
            
        except S3Error as e:
            logger.error(f"❌ Failed to upload task zip {task_id}: {e}")
            return False
    
    def download_task_zip(self, task_id: str, local_path: str) -> bool:
        """Download task zip file từ MinIO"""
        try:
            object_name = f"tasks/{task_id}.zip"
            
            # Create directory if not exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file
            self.client.fget_object(
                self.bucket_name,
                object_name,
                local_path
            )
            
            logger.info(f"✅ Downloaded task zip: {task_id}")
            return True
            
        except S3Error as e:
            logger.error(f"❌ Failed to download task zip {task_id}: {e}")
            return False
    
    def extract_task(self, task_id: str, zip_path: str, extract_path: str) -> bool:
        """Extract task zip file"""
        try:
            # Create extraction directory
            os.makedirs(extract_path, exist_ok=True)
            
            # Extract zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            logger.info(f"✅ Extracted task: {task_id} to {extract_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to extract task {task_id}: {e}")
            return False
    
    def create_task_zip(self, task_folder: str, output_zip: str) -> bool:
        """Tạo zip file từ task folder"""
        try:
            if not os.path.exists(task_folder):
                logger.error(f"❌ Task folder not found: {task_folder}")
                return False
            
            # Create zip file
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(task_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, task_folder)
                        zipf.write(file_path, arcname)
            
            logger.info(f"✅ Created task zip: {output_zip}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create task zip: {e}")
            return False
    
    def list_task_files(self) -> List[str]:
        """Liệt kê tất cả task files trong MinIO"""
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix="tasks/",
                recursive=True
            )
            
            task_files = []
            for obj in objects:
                if obj.object_name.endswith('.zip'):
                    task_id = os.path.basename(obj.object_name).replace('.zip', '')
                    task_files.append(task_id)
            
            logger.info(f"✅ Found {len(task_files)} task files in storage")
            return task_files
            
        except S3Error as e:
            logger.error(f"❌ Failed to list task files: {e}")
            return []
    
    def delete_task_zip(self, task_id: str) -> bool:
        """Xóa task zip file từ MinIO"""
        try:
            object_name = f"tasks/{task_id}.zip"
            
            self.client.remove_object(self.bucket_name, object_name)
            
            logger.info(f"✅ Deleted task zip: {task_id}")
            return True
            
        except S3Error as e:
            logger.error(f"❌ Failed to delete task zip {task_id}: {e}")
            return False
    
    def get_task_cache_path(self, task_id: str) -> str:
        """Lấy đường dẫn cache cho task"""
        return os.path.join(self.config.task_cache_dir, task_id)
    
    def get_task_zip_path(self, task_id: str) -> str:
        """Lấy đường dẫn zip file cho task"""
        return os.path.join(self.config.task_cache_dir, f"{task_id}.zip")
    
    def cleanup_task_cache(self, task_id: str) -> bool:
        """Dọn dẹp cache của task"""
        try:
            cache_path = self.get_task_cache_path(task_id)
            zip_path = self.get_task_zip_path(task_id)
            
            # Remove extracted files
            if os.path.exists(cache_path):
                shutil.rmtree(cache_path)
            
            # Remove zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
            logger.info(f"✅ Cleaned up cache for task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup cache for task {task_id}: {e}")
            return False