"""
Multi-Worker Manager for task-specific workers
"""
import os
import sys
import subprocess
import signal
import time
import psutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger

from core.config.manager import get_config
from core.database.operations import db_ops


class TaskWorker:
    """Individual task worker process"""
    
    def __init__(self, task_id: str, config: Dict[str, Any]):
        self.task_id = task_id
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.worker_name = f"{task_id}_worker"
        
    def start(self) -> bool:
        """Start the task worker process"""
        try:
            cmd = [
                sys.executable, '-m', 'celery',
                '-A', 'worker.celery_app:celery_app',
                'worker',
                '--loglevel', self.config.get('log_level', 'INFO'),
                '-Q', self.config['queue'],
                '-c', str(self.config.get('concurrency', 1)),
                '-n', f"{self.worker_name}@%h",
                '--without-gossip',  # Reduce overhead
                '--without-mingle',  # Reduce startup time
            ]
            
            # Add memory limit if specified
            if 'memory_limit' in self.config:
                cmd.extend(['--max-memory-per-child', self.config['memory_limit']])
            
            # Add task timeout
            if 'timeout' in self.config:
                cmd.extend(['--task-time-limit', str(self.config['timeout'])])
            
            logger.info(f"Starting worker for task {self.task_id}: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit to check if process started successfully
            time.sleep(2)
            if self.process.poll() is None:
                logger.info(f"Task worker {self.task_id} started successfully (PID: {self.process.pid})")
                return True
            else:
                stdout, stderr = self.process.communicate()
                logger.error(f"Task worker {self.task_id} failed to start: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start task worker {self.task_id}: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the task worker process"""
        try:
            if self.process and self.process.poll() is None:
                # Graceful shutdown
                self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=30)
                    logger.info(f"Task worker {self.task_id} stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if not stopped gracefully
                    self.process.kill()
                    self.process.wait()
                    logger.warning(f"Task worker {self.task_id} force killed")
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop task worker {self.task_id}: {e}")
            return False
    
    def is_alive(self) -> bool:
        """Check if worker process is alive"""
        return self.process is not None and self.process.poll() is None
    
    def get_status(self) -> Dict[str, Any]:
        """Get worker status information"""
        status = {
            "task_id": self.task_id,
            "worker_name": self.worker_name,
            "is_alive": self.is_alive(),
            "pid": self.process.pid if self.process else None,
            "config": self.config
        }
        
        # Get resource usage if process is alive
        if self.is_alive():
            try:
                proc = psutil.Process(self.process.pid)
                status.update({
                    "memory_mb": proc.memory_info().rss / 1024 / 1024,
                    "cpu_percent": proc.cpu_percent(),
                    "create_time": proc.create_time()
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return status


class MultiWorkerManager:
    """Manager for multiple task-specific workers"""
    
    def __init__(self):
        self.task_workers: Dict[str, TaskWorker] = {}
        self.config = get_config()
        
    def get_task_worker_config(self, task_id: str) -> Dict[str, Any]:
        """Get worker configuration for specific task"""
        # Get from multi_worker config if exists
        if hasattr(self.config.worker, 'multi_worker') and self.config.worker.multi_worker:
            task_workers_config = getattr(self.config.worker.multi_worker, 'task_workers', {})
            if task_id in task_workers_config:
                return task_workers_config[task_id]
        
        # Fallback to default task config
        task_config = self.config.worker.task_configs.get(task_id)
        if task_config:
            return {
                "queue": getattr(task_config, 'queue', task_id),
                "concurrency": 1,
                "timeout": getattr(task_config, 'timeout', 300),
                "memory_limit": getattr(task_config, 'memory_limit', None),
                "log_level": "INFO"
            }
        
        # Default config
        return {
            "queue": task_id,
            "concurrency": 1,
            "timeout": 300,
            "log_level": "INFO"
        }
    
    def start_task_worker(self, task_id: str) -> bool:
        """Start worker for specific task"""
        try:
            if task_id in self.task_workers:
                if self.task_workers[task_id].is_alive():
                    logger.warning(f"Task worker {task_id} is already running")
                    return True
                else:
                    # Remove dead worker
                    del self.task_workers[task_id]
            
            # Get worker configuration
            worker_config = self.get_task_worker_config(task_id)
            
            # Create and start worker
            worker = TaskWorker(task_id, worker_config)
            if worker.start():
                self.task_workers[task_id] = worker
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to start task worker {task_id}: {e}")
            return False
    
    def stop_task_worker(self, task_id: str) -> bool:
        """Stop worker for specific task"""
        try:
            if task_id in self.task_workers:
                worker = self.task_workers[task_id]
                if worker.stop():
                    del self.task_workers[task_id]
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop task worker {task_id}: {e}")
            return False
    
    def start_all_task_workers(self) -> bool:
        """Start workers for all active tasks"""
        try:
            active_tasks = self.config.worker.active_tasks
            success_count = 0
            
            logger.info(f"Starting workers for {len(active_tasks)} tasks")
            
            for task_id in active_tasks:
                if self.start_task_worker(task_id):
                    success_count += 1
                else:
                    logger.error(f"Failed to start worker for task: {task_id}")
            
            logger.info(f"Successfully started {success_count}/{len(active_tasks)} task workers")
            return success_count == len(active_tasks)
            
        except Exception as e:
            logger.error(f"Failed to start all task workers: {e}")
            return False
    
    def stop_all_task_workers(self) -> bool:
        """Stop all task workers"""
        try:
            workers_to_stop = list(self.task_workers.keys())
            success_count = 0
            
            logger.info(f"Stopping {len(workers_to_stop)} task workers")
            
            for task_id in workers_to_stop:
                if self.stop_task_worker(task_id):
                    success_count += 1
            
            logger.info(f"Successfully stopped {success_count}/{len(workers_to_stop)} task workers")
            return success_count == len(workers_to_stop)
            
        except Exception as e:
            logger.error(f"Failed to stop all task workers: {e}")
            return False
    
    def restart_task_worker(self, task_id: str) -> bool:
        """Restart worker for specific task"""
        logger.info(f"Restarting task worker: {task_id}")
        self.stop_task_worker(task_id)
        time.sleep(1)  # Brief pause
        return self.start_task_worker(task_id)
    
    def get_worker_status(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of workers"""
        if task_id:
            if task_id in self.task_workers:
                return self.task_workers[task_id].get_status()
            else:
                return {"error": f"Worker for task {task_id} not found"}
        
        # Get status of all workers
        status = {
            "total_workers": len(self.task_workers),
            "alive_workers": sum(1 for w in self.task_workers.values() if w.is_alive()),
            "workers": {}
        }
        
        for task_id, worker in self.task_workers.items():
            status["workers"][task_id] = worker.get_status()
        
        return status
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all workers"""
        health_status = {
            "healthy": True,
            "total_workers": len(self.task_workers),
            "healthy_workers": 0,
            "unhealthy_workers": [],
            "worker_details": {}
        }
        
        for task_id, worker in self.task_workers.items():
            is_healthy = worker.is_alive()
            worker_status = worker.get_status()
            
            health_status["worker_details"][task_id] = {
                "healthy": is_healthy,
                "status": worker_status
            }
            
            if is_healthy:
                health_status["healthy_workers"] += 1
            else:
                health_status["unhealthy_workers"].append(task_id)
                health_status["healthy"] = False
        
        return health_status
    
    def cleanup_dead_workers(self):
        """Remove dead workers from registry"""
        dead_workers = []
        for task_id, worker in self.task_workers.items():
            if not worker.is_alive():
                dead_workers.append(task_id)
        
        for task_id in dead_workers:
            logger.warning(f"Removing dead worker: {task_id}")
            del self.task_workers[task_id]
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down all workers...")
            self.stop_all_task_workers()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


# Global multi-worker manager instance
multi_worker_manager = MultiWorkerManager()