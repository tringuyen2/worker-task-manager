from pymongo import MongoClient
from pymongo.collection import Collection
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
from config import TaskConfig, TaskExecutionResult, WorkerConfig
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Quản lý kết nối và operations với MongoDB"""
    
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.client: Optional[MongoClient] = None
        self.db = None
        self.tasks_collection: Optional[Collection] = None
        self.executions_collection: Optional[Collection] = None
        self.workers_collection: Optional[Collection] = None
        self.connect()
    
    def connect(self):
        """Kết nối tới MongoDB"""
        try:
            mongo_config = self.config.mongodb
            
            # Tạo connection string
            if mongo_config.get("username") and mongo_config.get("password"):
                connection_string = (
                    f"mongodb://{mongo_config['username']}:{mongo_config['password']}"
                    f"@{mongo_config['host']}:{mongo_config['port']}/{mongo_config['database']}"
                )
            else:
                connection_string = (
                    f"mongodb://{mongo_config['host']}:{mongo_config['port']}"
                )
            
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.db = self.client[mongo_config["database"]]
            
            # Test connection
            self.client.admin.command('ping')
            
            # Initialize collections
            self.tasks_collection = self.db.tasks
            self.executions_collection = self.db.executions
            self.workers_collection = self.db.workers
            
            # Create indexes
            self._create_indexes()
            
            logger.info("✅ Connected to MongoDB successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    def _create_indexes(self):
        """Tạo indexes cho collections"""
        try:
            # Tasks collection indexes
            self.tasks_collection.create_index("task_id", unique=True)
            self.tasks_collection.create_index("enabled")
            self.tasks_collection.create_index("created_at")
            
            # Executions collection indexes
            self.executions_collection.create_index("task_id")
            self.executions_collection.create_index("execution_id", unique=True)
            self.executions_collection.create_index("timestamp")
            self.executions_collection.create_index("status")
            
            # Workers collection indexes
            self.workers_collection.create_index("worker_id", unique=True)
            
            logger.info("✅ Database indexes created")
            
        except Exception as e:
            logger.warning(f"⚠️ Error creating indexes: {e}")
    
    def register_task(self, task_config: TaskConfig) -> bool:
        """Đăng ký task vào database"""
        try:
            # Convert Pydantic model to dict
            task_data = task_config.dict()
            
            # Update timestamp
            task_data["updated_at"] = datetime.now()
            
            # Upsert task
            result = self.tasks_collection.replace_one(
                {"task_id": task_config.task_id},
                task_data,
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Task registered: {task_config.task_id}")
                return True
            else:
                logger.warning(f"⚠️ Task not modified: {task_config.task_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to register task {task_config.task_id}: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[TaskConfig]:
        """Lấy thông tin task từ database"""
        try:
            task_data = self.tasks_collection.find_one({"task_id": task_id})
            if task_data:
                # Remove MongoDB _id field
                task_data.pop("_id", None)
                return TaskConfig(**task_data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get task {task_id}: {e}")
            return None
    
    def get_active_tasks(self, task_ids: List[str]) -> List[TaskConfig]:
        """Lấy danh sách tasks đang active"""
        try:
            cursor = self.tasks_collection.find({
                "task_id": {"$in": task_ids},
                "enabled": True
            })
            
            tasks = []
            for task_data in cursor:
                task_data.pop("_id", None)
                tasks.append(TaskConfig(**task_data))
            
            logger.info(f"✅ Retrieved {len(tasks)} active tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"❌ Failed to get active tasks: {e}")
            return []
    
    def list_all_tasks(self) -> List[TaskConfig]:
        """Liệt kê tất cả tasks"""
        try:
            cursor = self.tasks_collection.find().sort("created_at", -1)
            
            tasks = []
            for task_data in cursor:
                task_data.pop("_id", None)
                tasks.append(TaskConfig(**task_data))
            
            return tasks
            
        except Exception as e:
            logger.error(f"❌ Failed to list tasks: {e}")
            return []
    
    def save_execution_result(self, result: TaskExecutionResult) -> bool:
        """Lưu kết quả thực thi task"""
        try:
            result_data = result.dict()
            
            # Insert execution result
            self.executions_collection.insert_one(result_data)
            
            logger.info(f"✅ Execution result saved: {result.execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save execution result: {e}")
            return False
    
    def get_execution_history(self, task_id: str, limit: int = 100) -> List[TaskExecutionResult]:
        """Lấy lịch sử thực thi task"""
        try:
            cursor = self.executions_collection.find(
                {"task_id": task_id}
            ).sort("timestamp", -1).limit(limit)
            
            results = []
            for result_data in cursor:
                result_data.pop("_id", None)
                results.append(TaskExecutionResult(**result_data))
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get execution history: {e}")
            return []
    
    def register_worker(self) -> bool:
        """Đăng ký worker vào database"""
        try:
            worker_data = self.config.dict()
            worker_data["last_seen"] = datetime.now()
            worker_data["status"] = "online"
            
            # Upsert worker
            result = self.workers_collection.replace_one(
                {"worker_id": self.config.worker_id},
                worker_data,
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Worker registered: {self.config.worker_id}")
                return True
            else:
                logger.warning(f"⚠️ Worker not modified: {self.config.worker_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to register worker: {e}")
            return False
    
    def update_worker_status(self, status: str = "online") -> bool:
        """Cập nhật trạng thái worker"""
        try:
            result = self.workers_collection.update_one(
                {"worker_id": self.config.worker_id},
                {
                    "$set": {
                        "status": status,
                        "last_seen": datetime.now()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to update worker status: {e}")
            return False
    
    def close(self):
        """Đóng kết nối database"""
        if self.client:
            self.update_worker_status("offline")
            self.client.close()
            logger.info("✅ Database connection closed")