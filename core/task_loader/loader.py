"""
Dynamic task and pipeline loader with caching
"""
import os
import sys
import json
import importlib
import importlib.util
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Type
from loguru import logger

from ..config.manager import get_config
from ..database.operations import db_ops
from ..storage.operations import storage_ops
from .cache import TaskCache
from .validator import TaskValidator


class TaskLoader:
    """Dynamic task loader with caching and validation"""
    
    def __init__(self):
        self.config = get_config().worker
        self.task_cache = TaskCache(self.config.task_cache_dir)
        self.pipeline_cache = TaskCache(self.config.pipeline_cache_dir)
        self.validator = TaskValidator()
        self._loaded_tasks: Dict[str, Any] = {}
        self._loaded_pipelines: Dict[str, Any] = {}
    
    def load_task(self, task_id: str, force_reload: bool = False) -> Optional[Any]:
        """
        Load task dynamically from cache or download from storage
        
        Args:
            task_id: Task identifier
            force_reload: Force reload even if cached
            
        Returns:
            Task class instance or None if failed
        """
        try:
            # Check if already loaded and not forcing reload
            if not force_reload and task_id in self._loaded_tasks:
                return self._loaded_tasks[task_id]
            
            # Get task metadata from database
            metadata = db_ops.get_task_metadata(task_id)
            if not metadata:
                logger.error(f"Task metadata not found: {task_id}")
                return None
            
            # Check if task is cached and up-to-date
            cache_path = self.task_cache.get_cache_path(task_id)
            
            if not force_reload and self.task_cache.is_cached(task_id):
                if self._verify_cache_integrity(cache_path, metadata.file_hash):
                    logger.info(f"Loading task from cache: {task_id}")
                    task_class = self._load_task_from_path(cache_path, metadata)
                    if task_class:
                        self._loaded_tasks[task_id] = task_class
                        return task_class
            
            # Download task from storage
            logger.info(f"Downloading task from storage: {task_id}")
            if not storage_ops.download_task_package(metadata.storage_path, cache_path):
                logger.error(f"Failed to download task package: {task_id}")
                return None
            
            # Verify download integrity
            if not storage_ops.verify_file_integrity(metadata.storage_path, metadata.file_hash):
                logger.error(f"Task package integrity check failed: {task_id}")
                return None
            
            # Install requirements
            if not self._install_task_requirements(cache_path):
                logger.error(f"Failed to install task requirements: {task_id}")
                return None
            
            # Load task class
            task_class = self._load_task_from_path(cache_path, metadata)
            if task_class:
                # Validate task
                if not self.validator.validate_task(task_class):
                    logger.error(f"Task validation failed: {task_id}")
                    return None
                
                self._loaded_tasks[task_id] = task_class
                self.task_cache.mark_cached(task_id)
                logger.info(f"Successfully loaded task: {task_id}")
                return task_class
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load task {task_id}: {e}")
            return None
    
    def load_pipeline(self, pipeline_id: str, force_reload: bool = False) -> Optional[Any]:
        """
        Load pipeline dynamically from cache or download from storage
        
        Args:
            pipeline_id: Pipeline identifier
            force_reload: Force reload even if cached
            
        Returns:
            Pipeline class instance or None if failed
        """
        try:
            # Check if already loaded and not forcing reload
            if not force_reload and pipeline_id in self._loaded_pipelines:
                return self._loaded_pipelines[pipeline_id]
            
            # Get pipeline metadata from database
            metadata = db_ops.get_pipeline_metadata(pipeline_id)
            if not metadata:
                logger.error(f"Pipeline metadata not found: {pipeline_id}")
                return None
            
            # Check if pipeline is cached and up-to-date
            cache_path = self.pipeline_cache.get_cache_path(pipeline_id)
            
            if not force_reload and self.pipeline_cache.is_cached(pipeline_id):
                if self._verify_cache_integrity(cache_path, metadata.file_hash):
                    logger.info(f"Loading pipeline from cache: {pipeline_id}")
                    pipeline_class = self._load_pipeline_from_path(cache_path, metadata)
                    if pipeline_class:
                        self._loaded_pipelines[pipeline_id] = pipeline_class
                        return pipeline_class
            
            # Download pipeline from storage
            logger.info(f"Downloading pipeline from storage: {pipeline_id}")
            if not storage_ops.download_pipeline_package(metadata.storage_path, cache_path):
                logger.error(f"Failed to download pipeline package: {pipeline_id}")
                return None
            
            # Verify download integrity
            if not storage_ops.verify_file_integrity(metadata.storage_path, metadata.file_hash):
                logger.error(f"Pipeline package integrity check failed: {pipeline_id}")
                return None
            
            # Install requirements
            if not self._install_pipeline_requirements(cache_path):
                logger.error(f"Failed to install pipeline requirements: {pipeline_id}")
                return None
            
            # Load pipeline class
            pipeline_class = self._load_pipeline_from_path(cache_path, metadata)
            if pipeline_class:
                # Validate pipeline
                if not self.validator.validate_pipeline(pipeline_class):
                    logger.error(f"Pipeline validation failed: {pipeline_id}")
                    return None
                
                self._loaded_pipelines[pipeline_id] = pipeline_class
                self.pipeline_cache.mark_cached(pipeline_id)
                logger.info(f"Successfully loaded pipeline: {pipeline_id}")
                return pipeline_class
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load pipeline {pipeline_id}: {e}")
            return None
    
    def _load_task_from_path(self, cache_path: str, metadata: Any) -> Optional[Any]:
        """Load task class from file system path"""
        try:
            task_file = Path(cache_path) / "task.py"
            if not task_file.exists():
                logger.error(f"Task file not found: {task_file}")
                return None
            
            # Load task.json for configuration
            task_config_file = Path(cache_path) / "task.json"
            task_config = {}
            if task_config_file.exists():
                with open(task_config_file, 'r') as f:
                    task_config = json.load(f)
            
            # Dynamic import
            spec = importlib.util.spec_from_file_location("task_module", task_file)
            task_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(task_module)
            
            # Find task class (should inherit from TaskBase)
            task_class = None
            for attr_name in dir(task_module):
                attr = getattr(task_module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, 'process') and 
                    attr.__name__ != 'TaskBase'):
                    task_class = attr
                    break
            
            if not task_class:
                logger.error(f"No valid task class found in {task_file}")
                return None
            
            # Create instance with configuration
            instance = task_class()
            instance._task_id = metadata.task_id
            instance._config = task_config
            instance._metadata = metadata
            
            return instance
            
        except Exception as e:
            logger.error(f"Failed to load task from path {cache_path}: {e}")
            return None
    
    def _load_pipeline_from_path(self, cache_path: str, metadata: Any) -> Optional[Any]:
        """Load pipeline class from file system path"""
        try:
            pipeline_file = Path(cache_path) / "pipeline.py"
            if not pipeline_file.exists():
                logger.error(f"Pipeline file not found: {pipeline_file}")
                return None
            
            # Load pipeline.json for configuration
            pipeline_config_file = Path(cache_path) / "pipeline.json"
            pipeline_config = {}
            if pipeline_config_file.exists():
                with open(pipeline_config_file, 'r') as f:
                    pipeline_config = json.load(f)
            
            # Dynamic import
            spec = importlib.util.spec_from_file_location("pipeline_module", pipeline_file)
            pipeline_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pipeline_module)
            
            # Find pipeline class (should inherit from PipelineBase)
            pipeline_class = None
            for attr_name in dir(pipeline_module):
                attr = getattr(pipeline_module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, 'execute') and 
                    attr.__name__ != 'PipelineBase'):
                    pipeline_class = attr
                    break
            
            if not pipeline_class:
                logger.error(f"No valid pipeline class found in {pipeline_file}")
                return None
            
            # Create instance with configuration
            instance = pipeline_class()
            instance._pipeline_id = metadata.pipeline_id
            instance._config = pipeline_config
            instance._metadata = metadata
            
            return instance
            
        except Exception as e:
            logger.error(f"Failed to load pipeline from path {cache_path}: {e}")
            return None
    
    def _install_task_requirements(self, cache_path: str) -> bool:
        """Install task requirements"""
        try:
            requirements_file = Path(cache_path) / "requirements.txt"
            if not requirements_file.exists():
                return True  # No requirements to install
            
            # Install using pip
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to install requirements: {result.stderr}")
                return False
            
            logger.info(f"Installed requirements from {requirements_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install task requirements: {e}")
            return False
    
    def _install_pipeline_requirements(self, cache_path: str) -> bool:
        """Install pipeline requirements"""
        try:
            requirements_file = Path(cache_path) / "requirements.txt"
            if not requirements_file.exists():
                return True  # No requirements to install
            
            # Install using pip
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to install requirements: {result.stderr}")
                return False
            
            logger.info(f"Installed requirements from {requirements_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install pipeline requirements: {e}")
            return False
    
    def _verify_cache_integrity(self, cache_path: str, expected_hash: str) -> bool:
        """Verify cache integrity using stored hash"""
        try:
            hash_file = Path(cache_path) / ".hash"
            if not hash_file.exists():
                return False
            
            with open(hash_file, 'r') as f:
                stored_hash = f.read().strip()
            
            return stored_hash == expected_hash
            
        except Exception:
            return False
    
    def reload_task(self, task_id: str) -> Optional[Any]:
        """Reload task (force download and reload)"""
        return self.load_task(task_id, force_reload=True)
    
    def reload_pipeline(self, pipeline_id: str) -> Optional[Any]:
        """Reload pipeline (force download and reload)"""
        return self.load_pipeline(pipeline_id, force_reload=True)
    
    def unload_task(self, task_id: str):
        """Unload task from memory"""
        if task_id in self._loaded_tasks:
            del self._loaded_tasks[task_id]
            logger.info(f"Unloaded task: {task_id}")
    
    def unload_pipeline(self, pipeline_id: str):
        """Unload pipeline from memory"""
        if pipeline_id in self._loaded_pipelines:
            del self._loaded_pipelines[pipeline_id]
            logger.info(f"Unloaded pipeline: {pipeline_id}")
    
    def get_loaded_tasks(self) -> List[str]:
        """Get list of loaded task IDs"""
        return list(self._loaded_tasks.keys())
    
    def get_loaded_pipelines(self) -> List[str]:
        """Get list of loaded pipeline IDs"""
        return list(self._loaded_pipelines.keys())
    
    def clear_cache(self):
        """Clear all cached tasks and pipelines"""
        self.task_cache.clear_cache()
        self.pipeline_cache.clear_cache()
        self._loaded_tasks.clear()
        self._loaded_pipelines.clear()
        logger.info("Cleared all caches")


# Global task loader instance
task_loader = TaskLoader()