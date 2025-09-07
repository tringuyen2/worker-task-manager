# ai_worker.py - Main AI Worker Application
import os
import sys
import time
import uuid
import argparse
import logging
from typing import Any, Dict, Optional
from datetime import datetime
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import load_config, WorkerConfig, TaskExecutionResult
from database import DatabaseManager
from storage import StorageManager
from task_loader import TaskLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_worker.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AIWorker:
    """Main AI Worker class"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = load_config(config_path)
        self.db_manager: Optional[DatabaseManager] = None
        self.storage_manager: Optional[StorageManager] = None
        self.task_loader: Optional[TaskLoader] = None
        self.executor: Optional[ThreadPoolExecutor] = None
        self.running = False
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def initialize(self) -> bool:
        """Khởi tạo tất cả components"""
        try:
            logger.info("🚀 Initializing AI Worker...")
            logger.info(f"   Worker ID: {self.config.worker_id}")
            logger.info(f"   Worker Name: {self.config.worker_name}")
            logger.info(f"   Active Tasks: {self.config.active_tasks}")
            
            # Initialize database manager
            logger.info("📊 Initializing database connection...")
            self.db_manager = DatabaseManager(self.config)
            if not self.db_manager.connect():
                logger.error("❌ Failed to initialize database connection")
                return False
            
            # Register worker
            if not self.db_manager.register_worker():
                logger.error("❌ Failed to register worker")
                return False
            
            # Initialize storage manager
            logger.info("💾 Initializing storage connection...")
            self.storage_manager = StorageManager(self.config)
            if not self.storage_manager.connect():
                logger.error("❌ Failed to initialize storage connection")
                return False
            
            # Initialize task loader
            logger.info("📦 Initializing task loader...")
            self.task_loader = TaskLoader(self.config, self.db_manager, self.storage_manager)
            
            # Load active tasks
            logger.info("🔄 Loading active tasks...")
            if not self.task_loader.load_active_tasks():
                logger.warning("⚠️ No tasks loaded, worker will run without tasks")
            
            # Initialize thread pool
            self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_tasks)
            
            logger.info("✅ AI Worker initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Worker: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def start(self):
        """Start the worker"""
        if not self.initialize():
            logger.error("❌ Failed to initialize worker, exiting")
            return
        
        self.running = True
        logger.info("🏃 AI Worker started and ready to process tasks")
        
        try:
            # Update worker status
            self.db_manager.update_worker_status("running")
            
            # Keep worker alive
            while self.running:
                # Update heartbeat
                self.db_manager.update_worker_status("running")
                
                # Sleep for a bit
                time.sleep(30)  # Update status every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        except Exception as e:
            logger.error(f"❌ Worker error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the worker gracefully"""
        logger.info("🛑 Stopping AI Worker...")
        self.running = False
        
        try:
            # Shutdown thread pool
            if self.executor:
                logger.info("⏳ Waiting for running tasks to complete...")
                self.executor.shutdown(wait=True, timeout=60)
            
            # Cleanup tasks
            if self.task_loader:
                logger.info("🧹 Cleaning up tasks...")
                self.task_loader.cleanup_all_tasks()
            
            # Update worker status
            if self.db_manager:
                self.db_manager.update_worker_status("stopped")
                self.db_manager.close()
            
            logger.info("✅ AI Worker stopped gracefully")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
    
    def process_task(self, task_id: str, input_data: Any) -> Dict[str, Any]:
        """Process a task request"""
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"🎯 Processing task: {task_id} (execution: {execution_id})")
        
        try:
            # Get task instance
            task_instance = self.task_loader.get_task(task_id)
            if not task_instance:
                error_msg = f"Task not found or not loaded: {task_id}"
                logger.error(f"❌ {error_msg}")
                
                # Save error result
                self._save_execution_result(
                    task_id, execution_id, input_data, None,
                    "error", error_msg, time.time() - start_time
                )
                
                return {
                    "success": False,
                    "error": error_msg,
                    "execution_id": execution_id
                }
            
            # Process task
            result = task_instance.process(input_data)
            execution_time = time.time() - start_time
            
            # Check if result indicates error
            if isinstance(result, dict) and "error" in result:
                logger.error(f"❌ Task execution error: {result['error']}")
                self._save_execution_result(
                    task_id, execution_id, input_data, result,
                    "error", result["error"], execution_time
                )
                
                return {
                    "success": False,
                    "error": result["error"],
                    "execution_id": execution_id,
                    "execution_time": execution_time
                }
            else:
                logger.info(f"✅ Task completed successfully: {task_id} (execution: {execution_id})")
                self._save_execution_result(
                    task_id, execution_id, input_data, result,
                    "success", None, execution_time
                )
                
                return {
                    "success": True,
                    "result": result,
                    "execution_id": execution_id,
                    "execution_time": execution_time
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Task execution failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            self._save_execution_result(
                task_id, execution_id, input_data, None,
                "error", error_msg, execution_time
            )
            
            return {
                "success": False,
                "error": error_msg,
                "execution_id": execution_id,
                "execution_time": execution_time
            }
    
    def process_task_async(self, task_id: str, input_data: Any) -> str:
        """Process task asynchronously"""
        if not self.executor:
            raise RuntimeError("Worker not initialized")
        
        execution_id = str(uuid.uuid4())
        future = self.executor.submit(self.process_task, task_id, input_data)
        
        logger.info(f"🚀 Started async task processing: {task_id} (execution: {execution_id})")
        return execution_id
    
    def _save_execution_result(self, task_id: str, execution_id: str, 
                             input_data: Any, output_data: Any,
                             status: str, error_message: Optional[str],
                             execution_time: float):
        """Save execution result to database"""
        try:
            result = TaskExecutionResult(
                task_id=task_id,
                execution_id=execution_id,
                input_data=input_data,
                output_data=output_data,
                status=status,
                error_message=error_message,
                execution_time=execution_time
            )
            
            self.db_manager.save_execution_result(result)
            
        except Exception as e:
            logger.error(f"❌ Failed to save execution result: {e}")
    
    def list_tasks(self) -> Dict[str, Any]:
        """List all loaded tasks"""
        if not self.task_loader:
            return {"error": "Worker not initialized"}
        
        tasks = []
        for task_id in self.task_loader.list_loaded_tasks():
            task_config = self.task_loader.get_task_config(task_id)
            task_instance = self.task_loader.get_task(task_id)
            
            if task_config and task_instance:
                tasks.append({
                    "task_id": task_id,
                    "task_name": task_config.task_name,
                    "description": task_instance.get_description(),
                    "version": task_config.version,
                    "requirements": task_config.requirements
                })
        
        return {
            "worker_id": self.config.worker_id,
            "worker_name": self.config.worker_name,
            "tasks": tasks,
            "total_tasks": len(tasks)
        }
    
    def reload_task(self, task_id: str) -> Dict[str, Any]:
        """Reload a specific task"""
        if not self.task_loader:
            return {"error": "Worker not initialized"}
        
        try:
            if self.task_loader.reload_task(task_id):
                return {"success": True, "message": f"Task reloaded: {task_id}"}
            else:
                return {"success": False, "error": f"Failed to reload task: {task_id}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='AI Task Worker')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--task', type=str, help='Task ID to run')
    parser.add_argument('--input', type=str, help='Input data for task')
    parser.add_argument('--list', action='store_true', help='List loaded tasks')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    args = parser.parse_args()
    
    # Initialize worker
    worker = AIWorker(args.config)
    
    if args.list:
        # List tasks mode
        if not worker.initialize():
            print("❌ Failed to initialize worker")
            return
        
        result = worker.list_tasks()
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"📋 Worker: {result['worker_name']} ({result['worker_id']})")
            print(f"📊 Total tasks: {result['total_tasks']}")
            for task in result['tasks']:
                print(f"  ✅ {task['task_id']}: {task['description']}")
        
        worker.stop()
        return
    
    if args.task:
        # Single task execution mode
        if not worker.initialize():
            print("❌ Failed to initialize worker")
            return
        
        result = worker.process_task(args.task, args.input)
        if result['success']:
            print(f"✅ Task completed successfully")
            print(f"🎯 Result: {result['result']}")
            print(f"⏱️  Execution time: {result['execution_time']:.2f}s")
        else:
            print(f"❌ Task failed: {result['error']}")
        
        worker.stop()
        return
    
    if args.daemon:
        # Daemon mode
        worker.start()
    else:
        # Interactive mode
        print("=== AI Task Worker ===")
        print("Use --daemon to run as daemon")
        print("Use --list to show loaded tasks")
        print("Use --task <task_id> --input <input> to run single task")

if __name__ == "__main__":
    main()