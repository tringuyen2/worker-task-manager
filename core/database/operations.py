"""
Database operations for task and pipeline management
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pymongo import ReturnDocument
from loguru import logger

from .connection import get_mongodb_connection
from .models import (
    TaskMetadata, PipelineMetadata, ExecutionRecord, 
    WorkerStatus, TaskStatus, TaskType
)


class DatabaseOperations:
    """Database operations manager"""
    
    def __init__(self):
        self.conn = get_mongodb_connection()
    
    # Task Metadata Operations
    
    def create_task_metadata(self, task_metadata: TaskMetadata) -> bool:
        """Create new task metadata"""
        try:
            collection = self.conn.get_collection("task_metadata")
            result = collection.insert_one(task_metadata.model_dump())
            logger.info(f"Task metadata created: {task_metadata.task_id}")
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create task metadata {task_metadata.task_id}: {e}")
            return False
    
    def get_task_metadata(self, task_id: str) -> Optional[TaskMetadata]:
        """Get task metadata by ID"""
        try:
            collection = self.conn.get_collection("task_metadata")
            doc = collection.find_one({"task_id": task_id})
            return TaskMetadata(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get task metadata {task_id}: {e}")
            return None
    
    def update_task_metadata(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update task metadata"""
        try:
            updates["updated_at"] = datetime.utcnow()
            collection = self.conn.get_collection("task_metadata")
            result = collection.update_one(
                {"task_id": task_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update task metadata {task_id}: {e}")
            return False
    
    def list_tasks(self, active_only: bool = True, category: Optional[str] = None) -> List[TaskMetadata]:
        """List all tasks"""
        try:
            collection = self.conn.get_collection("task_metadata")
            query = {}
            if active_only:
                query["is_active"] = True
            if category:
                query["category"] = category
            
            docs = collection.find(query).sort("created_at", -1)
            return [TaskMetadata(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []
    
    def delete_task_metadata(self, task_id: str) -> bool:
        """Delete task metadata"""
        try:
            collection = self.conn.get_collection("task_metadata")
            result = collection.delete_one({"task_id": task_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete task metadata {task_id}: {e}")
            return False
    
    # Pipeline Metadata Operations
    
    def create_pipeline_metadata(self, pipeline_metadata: PipelineMetadata) -> bool:
        """Create new pipeline metadata"""
        try:
            collection = self.conn.get_collection("pipeline_metadata")
            result = collection.insert_one(pipeline_metadata.model_dump())
            logger.info(f"Pipeline metadata created: {pipeline_metadata.pipeline_id}")
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create pipeline metadata {pipeline_metadata.pipeline_id}: {e}")
            return False
    
    def get_pipeline_metadata(self, pipeline_id: str) -> Optional[PipelineMetadata]:
        """Get pipeline metadata by ID"""
        try:
            collection = self.conn.get_collection("pipeline_metadata")
            doc = collection.find_one({"pipeline_id": pipeline_id})
            return PipelineMetadata(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get pipeline metadata {pipeline_id}: {e}")
            return None
    
    def update_pipeline_metadata(self, pipeline_id: str, updates: Dict[str, Any]) -> bool:
        """Update pipeline metadata"""
        try:
            updates["updated_at"] = datetime.utcnow()
            collection = self.conn.get_collection("pipeline_metadata")
            result = collection.update_one(
                {"pipeline_id": pipeline_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update pipeline metadata {pipeline_id}: {e}")
            return False
    
    def list_pipelines(self, active_only: bool = True, category: Optional[str] = None) -> List[PipelineMetadata]:
        """List all pipelines"""
        try:
            collection = self.conn.get_collection("pipeline_metadata")
            query = {}
            if active_only:
                query["is_active"] = True
            if category:
                query["category"] = category
            
            docs = collection.find(query).sort("created_at", -1)
            return [PipelineMetadata(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to list pipelines: {e}")
            return []
    
    def delete_pipeline_metadata(self, pipeline_id: str) -> bool:
        """Delete pipeline metadata"""
        try:
            collection = self.conn.get_collection("pipeline_metadata")
            result = collection.delete_one({"pipeline_id": pipeline_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete pipeline metadata {pipeline_id}: {e}")
            return False
    
    # Execution Records Operations
    
    def create_execution_record(self, execution_record: ExecutionRecord) -> bool:
        """Create new execution record"""
        try:
            collection = self.conn.get_collection("execution_records")
            result = collection.insert_one(execution_record.model_dump())
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create execution record {execution_record.execution_id}: {e}")
            return False
    
    def update_execution_record(self, execution_id: str, updates: Dict[str, Any]) -> bool:
        """Update execution record"""
        try:
            collection = self.conn.get_collection("execution_records")
            result = collection.update_one(
                {"execution_id": execution_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update execution record {execution_id}: {e}")
            return False
    
    def get_execution_record(self, execution_id: str) -> Optional[ExecutionRecord]:
        """Get execution record by ID"""
        try:
            collection = self.conn.get_collection("execution_records")
            doc = collection.find_one({"execution_id": execution_id})
            return ExecutionRecord(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get execution record {execution_id}: {e}")
            return None
    
    def list_execution_records(
        self, 
        task_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[ExecutionRecord]:
        """List execution records with filters"""
        try:
            collection = self.conn.get_collection("execution_records")
            query = {}
            if task_id:
                query["task_id"] = task_id
            if pipeline_id:
                query["pipeline_id"] = pipeline_id
            if worker_id:
                query["worker_id"] = worker_id
            if status:
                query["status"] = status
            
            docs = collection.find(query).sort("created_at", -1).limit(limit)
            return [ExecutionRecord(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to list execution records: {e}")
            return []
    
    # Worker Status Operations
    
    def update_worker_status(self, worker_status: WorkerStatus) -> bool:
        """Update or create worker status"""
        try:
            collection = self.conn.get_collection("worker_status")
            result = collection.update_one(
                {"worker_id": worker_status.worker_id},
                {"$set": worker_status.model_dump()},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Failed to update worker status {worker_status.worker_id}: {e}")
            return False
    
    def get_worker_status(self, worker_id: str) -> Optional[WorkerStatus]:
        """Get worker status by ID"""
        try:
            collection = self.conn.get_collection("worker_status")
            doc = collection.find_one({"worker_id": worker_id})
            return WorkerStatus(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get worker status {worker_id}: {e}")
            return None
    
    def list_active_workers(self, heartbeat_threshold_minutes: int = 5) -> List[WorkerStatus]:
        """List active workers based on heartbeat"""
        try:
            threshold = datetime.utcnow() - timedelta(minutes=heartbeat_threshold_minutes)
            collection = self.conn.get_collection("worker_status")
            docs = collection.find({
                "is_active": True,
                "last_heartbeat": {"$gte": threshold}
            }).sort("last_heartbeat", -1)
            return [WorkerStatus(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to list active workers: {e}")
            return []
    
    def cleanup_old_records(self, days: int = 30) -> bool:
        """Cleanup old execution records"""
        try:
            threshold = datetime.utcnow() - timedelta(days=days)
            collection = self.conn.get_collection("execution_records")
            result = collection.delete_many({"created_at": {"$lt": threshold}})
            logger.info(f"Cleaned up {result.deleted_count} old execution records")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            return False
    
    # Statistics Operations
    
    def get_task_statistics(self, task_id: str, days: int = 7) -> Dict[str, Any]:
        """Get task execution statistics"""
        try:
            threshold = datetime.utcnow() - timedelta(days=days)
            collection = self.conn.get_collection("execution_records")
            
            pipeline = [
                {"$match": {"task_id": task_id, "created_at": {"$gte": threshold}}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_duration": {"$avg": "$duration"},
                    "total_duration": {"$sum": "$duration"}
                }}
            ]
            
            results = list(collection.aggregate(pipeline))
            
            stats = {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "pending": 0,
                "running": 0,
                "avg_duration": 0,
                "total_duration": 0
            }
            
            for result in results:
                status = result["_id"]
                count = result["count"]
                stats["total_executions"] += count
                
                if status == TaskStatus.SUCCESS:
                    stats["successful"] = count
                    stats["avg_duration"] = result.get("avg_duration", 0)
                    stats["total_duration"] = result.get("total_duration", 0)
                elif status == TaskStatus.FAILED:
                    stats["failed"] = count
                elif status == TaskStatus.PENDING:
                    stats["pending"] = count
                elif status == TaskStatus.RUNNING:
                    stats["running"] = count
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get task statistics {task_id}: {e}")
            return {}


# Global database operations instance
db_ops = DatabaseOperations()