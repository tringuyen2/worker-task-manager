"""
Worker lifecycle management and monitoring
"""
import os
import platform
import socket
import threading
import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

from core.config.manager import get_config
from core.database.operations import db_ops
from core.database.models import WorkerStatus


class WorkerManager:
    """Worker lifecycle and monitoring manager"""
    
    def __init__(self):
        self.config = get_config().worker
        self.worker_id = self.config.worker_id
        self.hostname = socket.gethostname()
        self.is_running = False
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.heartbeat_interval = self.config.health_check_interval
        
    def register_worker(self) -> bool:
        """Register worker with the system"""
        try:
            worker_status = WorkerStatus(
                worker_id=self.worker_id,
                hostname=self.hostname,
                is_active=True,
                last_heartbeat=datetime.utcnow(),
                active_tasks=self.config.active_tasks,
                active_pipelines=self.config.active_pipelines,
                queues=self._get_worker_queues(),
                max_concurrent_tasks=self.config.max_concurrent_tasks,
                current_task_count=0,
                memory_usage=self._get_memory_usage(),
                cpu_usage=self._get_cpu_usage(),
                version="1.0.0",
                python_version=platform.python_version(),
                celery_version=self._get_celery_version(),
                config_version=self._get_config_version(),
                config_hash=self._get_config_hash(),
                total_tasks_executed=0,
                successful_tasks=0,
                failed_tasks=0,
                metadata=self._get_worker_metadata()
            )
            
            success = db_ops.update_worker_status(worker_status)
            if success:
                logger.info(f"Worker {self.worker_id} registered successfully")
                self._start_heartbeat()
                return True
            else:
                logger.error(f"Failed to register worker {self.worker_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to register worker: {e}")
            return False
    
    def unregister_worker(self) -> bool:
        """Unregister worker from the system"""
        try:
            self._stop_heartbeat()
            
            # Mark worker as inactive
            updates = {
                "is_active": False,
                "last_heartbeat": datetime.utcnow()
            }
            
            success = db_ops.update_worker_status(
                WorkerStatus(worker_id=self.worker_id, hostname=self.hostname, **updates)
            )
            
            if success:
                logger.info(f"Worker {self.worker_id} unregistered successfully")
                return True
            else:
                logger.error(f"Failed to unregister worker {self.worker_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to unregister worker: {e}")
            return False
    
    def _start_heartbeat(self):
        """Start heartbeat thread"""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            return
        
        self.is_running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        logger.info("Heartbeat thread started")
    
    def _stop_heartbeat(self):
        """Stop heartbeat thread"""
        self.is_running = False
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)
        logger.info("Heartbeat thread stopped")
    
    def _heartbeat_loop(self):
        """Heartbeat loop to update worker status"""
        while self.is_running:
            try:
                self._send_heartbeat()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                time.sleep(5)  # Wait a bit before retrying
    
    def _send_heartbeat(self):
        """Send heartbeat update"""
        try:
            # Get current statistics
            stats = self._get_worker_statistics()
            
            updates = {
                "last_heartbeat": datetime.utcnow(),
                "current_task_count": stats.get("current_tasks", 0),
                "memory_usage": self._get_memory_usage(),
                "cpu_usage": self._get_cpu_usage(),
                "total_tasks_executed": stats.get("total_executed", 0),
                "successful_tasks": stats.get("successful", 0),
                "failed_tasks": stats.get("failed", 0)
            }
            
            worker_status = WorkerStatus(
                worker_id=self.worker_id,
                hostname=self.hostname,
                **updates
            )
            
            db_ops.update_worker_status(worker_status)
            
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
    
    def _get_worker_queues(self) -> list:
        """Get list of queues this worker listens to"""
        try:
            from .celery_app import celery_app
            queues = []
            
            # Add task queues
            for task_id in self.config.active_tasks:
                task_config = self.config.task_configs.get(task_id)
                if task_config:
                    queue = getattr(task_config, 'queue', 'default')
                    if queue not in queues:
                        queues.append(queue)
            
            # Add pipeline queues
            for pipeline_id in self.config.active_pipelines:
                pipeline_config = self.config.pipeline_configs.get(pipeline_id)
                if pipeline_config:
                    queue = getattr(pipeline_config, 'queue', 'pipeline')
                    if queue not in queues:
                        queues.append(queue)
            
            # Ensure default queue is included
            if 'default' not in queues:
                queues.append('default')
            
            return queues
            
        except Exception as e:
            logger.error(f"Failed to get worker queues: {e}")
            return ['default']
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # MB
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=1)
        except Exception:
            return 0.0
    
    def _get_celery_version(self) -> str:
        """Get Celery version"""
        try:
            import celery
            return celery.__version__
        except Exception:
            return "unknown"
    
    def _get_config_version(self) -> str:
        """Get configuration version"""
        try:
            return get_config().system.version
        except Exception:
            return "unknown"
    
    def _get_config_hash(self) -> str:
        """Get configuration hash"""
        try:
            import hashlib
            import json
            
            config_dict = get_config().model_dump()
            config_str = json.dumps(config_dict, sort_keys=True)
            return hashlib.md5(config_str.encode()).hexdigest()
        except Exception:
            return "unknown"
    
    def _get_worker_metadata(self) -> Dict[str, Any]:
        """Get worker metadata"""
        try:
            return {
                "platform": platform.platform(),
                "python_implementation": platform.python_implementation(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "pid": os.getpid(),
                "started_at": datetime.utcnow().isoformat(),
                "working_directory": os.getcwd()
            }
        except Exception:
            return {}
    
    def _get_worker_statistics(self) -> Dict[str, Any]:
        """Get worker execution statistics"""
        try:
            # Get statistics from database
            stats = {
                "current_tasks": 0,
                "total_executed": 0,
                "successful": 0,
                "failed": 0
            }
            
            # Get execution records for this worker
            records = db_ops.list_execution_records(worker_id=self.worker_id, limit=1000)
            
            stats["total_executed"] = len(records)
            stats["successful"] = len([r for r in records if r.status.value == "success"])
            stats["failed"] = len([r for r in records if r.status.value == "failed"])
            stats["current_tasks"] = len([r for r in records if r.status.value == "running"])
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get worker statistics: {e}")
            return {
                "current_tasks": 0,
                "total_executed": 0,
                "successful": 0,
                "failed": 0
            }
    
    def get_worker_info(self) -> Dict[str, Any]:
        """Get comprehensive worker information"""
        try:
            worker_status = db_ops.get_worker_status(self.worker_id)
            if not worker_status:
                return {}
            
            return {
                "worker_id": self.worker_id,
                "hostname": self.hostname,
                "is_active": worker_status.is_active,
                "last_heartbeat": worker_status.last_heartbeat.isoformat() if worker_status.last_heartbeat else None,
                "active_tasks": worker_status.active_tasks,
                "active_pipelines": worker_status.active_pipelines,
                "queues": worker_status.queues,
                "max_concurrent_tasks": worker_status.max_concurrent_tasks,
                "current_task_count": worker_status.current_task_count,
                "memory_usage_mb": worker_status.memory_usage,
                "cpu_usage_percent": worker_status.cpu_usage,
                "version": worker_status.version,
                "python_version": worker_status.python_version,
                "celery_version": worker_status.celery_version,
                "total_tasks_executed": worker_status.total_tasks_executed,
                "successful_tasks": worker_status.successful_tasks,
                "failed_tasks": worker_status.failed_tasks,
                "metadata": worker_status.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get worker info: {e}")
            return {}
    
    def update_task_count(self, increment: int = 0):
        """Update current task count"""
        try:
            worker_status = db_ops.get_worker_status(self.worker_id)
            if worker_status:
                new_count = max(0, worker_status.current_task_count + increment)
                updates = {"current_task_count": new_count}
                
                updated_status = WorkerStatus(
                    worker_id=self.worker_id,
                    hostname=self.hostname,
                    **updates
                )
                db_ops.update_worker_status(updated_status)
                
        except Exception as e:
            logger.error(f"Failed to update task count: {e}")
    
    def is_healthy(self) -> bool:
        """Check if worker is healthy"""
        try:
            # Check memory usage
            memory_usage = self._get_memory_usage()
            if memory_usage > 2048:  # 2GB limit
                logger.warning(f"High memory usage: {memory_usage}MB")
                return False
            
            # Check CPU usage
            cpu_usage = self._get_cpu_usage()
            if cpu_usage > 95:  # 95% CPU limit
                logger.warning(f"High CPU usage: {cpu_usage}%")
                return False
            
            # Check disk space
            try:
                disk_usage = psutil.disk_usage('/')
                if disk_usage.percent > 90:  # 90% disk usage limit
                    logger.warning(f"High disk usage: {disk_usage.percent}%")
                    return False
            except Exception:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Global worker manager instance
worker_manager = WorkerManager()