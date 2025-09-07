import os
import sys
import importlib.util
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import subprocess
from config import TaskConfig, WorkerConfig
from database import DatabaseManager
from storage import StorageManager

logger = logging.getLogger(__name__)

class BaseTask(ABC):
    """Base class cho tất cả AI tasks"""
    
    def __init__(self):
        self.task_name = self.__class__.__name__
        
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Xử lý input và trả về kết quả"""
        pass
    
    @abstractmethod
    def get_requirements(self) -> List[str]:
        """Trả về list các thư viện cần thiết"""
        pass
    
    def get_description(self) -> str:
        """Mô tả task"""
        return f"AI Task: {self.task_name}"

class TaskLoader:
    """Quản lý việc load và chạy tasks"""
    
    def __init__(self, config: WorkerConfig, db_manager: DatabaseManager, storage_manager: StorageManager):
        self.config = config
        self.db_manager = db_manager
        self.storage_manager = storage_manager
        self.loaded_tasks: Dict[str, BaseTask] = {}
        self.task_configs: Dict[str, TaskConfig] = {}
        
        # Tạo cache directory
        os.makedirs(config.task_cache_dir, exist_ok=True)
    
    def load_active_tasks(self) -> bool:
        """Load tất cả tasks đang active từ config"""
        try:
            logger.info(f"🔄 Loading active tasks: {self.config.active_tasks}")
            
            # Lấy thông tin tasks từ database
            active_tasks = self.db_manager.get_active_tasks(self.config.active_tasks)
            
            if not active_tasks:
                logger.warning("⚠️ No active tasks found in database")
                return False
            
            success_count = 0
            for task_config in active_tasks:
                if self._load_task(task_config):
                    success_count += 1
            
            logger.info(f"✅ Successfully loaded {success_count}/{len(active_tasks)} tasks")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to load active tasks: {e}")
            return False
    
    def _load_task(self, task_config: TaskConfig) -> bool:
        """Load một task cụ thể"""
        try:
            task_id = task_config.task_id
            logger.info(f"📦 Loading task: {task_id}")
            
            # Download task zip if not exists
            zip_path = self.storage_manager.get_task_zip_path(task_id)
            if not os.path.exists(zip_path):
                if not self.storage_manager.download_task_zip(task_id, zip_path):
                    logger.error(f"❌ Failed to download task zip: {task_id}")
                    return False
            
            # Extract task
            extract_path = self.storage_manager.get_task_cache_path(task_id)
            if not os.path.exists(extract_path) or not os.listdir(extract_path):
                if not self.storage_manager.extract_task(task_id, zip_path, extract_path):
                    logger.error(f"❌ Failed to extract task: {task_id}")
                    return False
            
            # Install requirements
            if not self._install_requirements(task_config, extract_path):
                logger.warning(f"⚠️ Failed to install requirements for task: {task_id}")
            
            # Load task module
            task_instance = self._load_task_module(task_config, extract_path)
            if not task_instance:
                logger.error(f"❌ Failed to load task module: {task_id}")
                return False
            
            # Store loaded task
            self.loaded_tasks[task_id] = task_instance
            self.task_configs[task_id] = task_config
            
            logger.info(f"✅ Task loaded successfully: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load task {task_config.task_id}: {e}")
            return False
    
    def _install_requirements(self, task_config: TaskConfig, extract_path: str) -> bool:
        """Cài đặt requirements cho task"""
        try:
            # Check requirements.txt file
            req_file = os.path.join(extract_path, "requirements.txt")
            requirements = task_config.requirements.copy()
            
            if os.path.exists(req_file):
                with open(req_file, 'r') as f:
                    file_requirements = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
                    requirements.extend(file_requirements)
            
            if not requirements:
                logger.info(f"📦 No requirements to install for task: {task_config.task_id}")
                return True
            
            # Install requirements
            logger.info(f"📦 Installing requirements for task: {task_config.task_id}")
            logger.info(f"   Requirements: {requirements}")
            
            cmd = [sys.executable, "-m", "pip", "install"] + requirements
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Requirements installed successfully for task: {task_config.task_id}")
                return True
            else:
                logger.error(f"❌ Failed to install requirements for task: {task_config.task_id}")
                logger.error(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception installing requirements for task {task_config.task_id}: {e}")
            return False
    
    def _load_task_module(self, task_config: TaskConfig, extract_path: str) -> Optional[BaseTask]:
        """Load task module và tạo instance"""
        try:
            task_file = os.path.join(extract_path, task_config.entry_point)
            
            if not os.path.exists(task_file):
                logger.error(f"❌ Task entry point not found: {task_file}")
                return None
            
            # Add extract path to sys.path
            if extract_path not in sys.path:
                sys.path.insert(0, extract_path)
            
            # Import task module
            spec = importlib.util.spec_from_file_location(
                f"{task_config.task_id}_module",
                task_file
            )
            
            if not spec or not spec.loader:
                logger.error(f"❌ Failed to create module spec for task: {task_config.task_id}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # Add BaseTask to module namespace
            module.BaseTask = BaseTask
            
            # Execute module
            spec.loader.exec_module(module)
            
            # Find BaseTask subclass
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (hasattr(obj, '__bases__') and 
                    any(base.__name__ == 'BaseTask' for base in obj.__bases__) and 
                    obj.__name__ != 'BaseTask'):
                    
                    logger.info(f"✅ Found task class: {name}")
                    return obj()
            
            logger.error(f"❌ No BaseTask subclass found in task: {task_config.task_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to load task module {task_config.task_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_task(self, task_id: str) -> Optional[BaseTask]:
        """Lấy task instance"""
        return self.loaded_tasks.get(task_id)
    
    def get_task_config(self, task_id: str) -> Optional[TaskConfig]:
        """Lấy task config"""
        return self.task_configs.get(task_id)
    
    def list_loaded_tasks(self) -> List[str]:
        """Liệt kê các tasks đã load"""
        return list(self.loaded_tasks.keys())
    
    def reload_task(self, task_id: str) -> bool:
        """Reload một task"""
        try:
            # Get task config from database
            task_config = self.db_manager.get_task(task_id)
            if not task_config:
                logger.error(f"❌ Task config not found: {task_id}")
                return False
            
            # Cleanup existing task
            if task_id in self.loaded_tasks:
                del self.loaded_tasks[task_id]
            if task_id in self.task_configs:
                del self.task_configs[task_id]
            
            # Cleanup cache
            self.storage_manager.cleanup_task_cache(task_id)
            
            # Reload task
            return self._load_task(task_config)
            
        except Exception as e:
            logger.error(f"❌ Failed to reload task {task_id}: {e}")
            return False
    
    def unload_task(self, task_id: str) -> bool:
        """Unload một task"""
        try:
            if task_id in self.loaded_tasks:
                del self.loaded_tasks[task_id]
                logger.info(f"✅ Task unloaded: {task_id}")
            
            if task_id in self.task_configs:
                del self.task_configs[task_id]
            
            # Cleanup cache
            self.storage_manager.cleanup_task_cache(task_id)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to unload task {task_id}: {e}")
            return False
    
    def cleanup_all_tasks(self):
        """Cleanup tất cả tasks"""
        try:
            for task_id in list(self.loaded_tasks.keys()):
                self.unload_task(task_id)
            
            logger.info("✅ All tasks cleaned up")
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup tasks: {e}")