"""
Configuration manager for loading and managing application configuration
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

from .models import AppConfig, WorkerConfig, TaskConfig, PipelineConfig


class ConfigManager:
    """Configuration manager"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config: Optional[AppConfig] = None
        self._watchers = []
    
    def load_config(self) -> AppConfig:
        """Load configuration from file"""
        try:
            if not self.config_path.exists():
                logger.info(f"Config file {self.config_path} not found. Creating default config.")
                self.create_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self._config = AppConfig(**config_data)
            logger.info(f"Configuration loaded from {self.config_path}")
            return self._config
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            logger.info("Using default configuration")
            self._config = AppConfig()
            return self._config
    
    def save_config(self, config: Optional[AppConfig] = None) -> bool:
        """Save configuration to file"""
        try:
            config = config or self._config
            if not config:
                raise ValueError("No configuration to save")
            
            config_dict = config.model_dump(exclude_none=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def create_default_config(self) -> AppConfig:
        """Create and save default configuration"""
        config = AppConfig()
        
        # Set some example tasks
        config.worker.active_tasks = ["face_detection", "text_sentiment"]
        config.worker.active_pipelines = ["image_processing_pipeline"]
        
        # Example task configs
        config.worker.task_configs = {
            "face_detection": TaskConfig(
                task_id="face_detection",
                queue="vision",
                priority=7,
                timeout=120
            ),
            "text_sentiment": TaskConfig(
                task_id="text_sentiment",
                queue="nlp",
                priority=5,
                timeout=60
            )
        }
        
        # Example pipeline config
        config.worker.pipeline_configs = {
            "image_processing_pipeline": PipelineConfig(
                pipeline_id="image_processing_pipeline",
                tasks=["face_detection", "object_detection"],
                queue="pipeline",
                parallel=False
            )
        }
        
        self._config = config
        self.save_config(config)
        return config
    
    @property
    def config(self) -> AppConfig:
        """Get current configuration"""
        if not self._config:
            return self.load_config()
        return self._config
    
    def update_task_config(self, task_id: str, config: TaskConfig) -> bool:
        """Update task configuration"""
        try:
            if not self._config:
                self.load_config()
            
            self._config.worker.task_configs[task_id] = config
            if task_id not in self._config.worker.active_tasks:
                self._config.worker.active_tasks.append(task_id)
            
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Failed to update task config {task_id}: {e}")
            return False
    
    def update_pipeline_config(self, pipeline_id: str, config: PipelineConfig) -> bool:
        """Update pipeline configuration"""
        try:
            if not self._config:
                self.load_config()
            
            self._config.worker.pipeline_configs[pipeline_id] = config
            if pipeline_id not in self._config.worker.active_pipelines:
                self._config.worker.active_pipelines.append(pipeline_id)
            
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Failed to update pipeline config {pipeline_id}: {e}")
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """Remove task from configuration"""
        try:
            if not self._config:
                self.load_config()
            
            # Remove from active tasks
            if task_id in self._config.worker.active_tasks:
                self._config.worker.active_tasks.remove(task_id)
            
            # Remove task config
            if task_id in self._config.worker.task_configs:
                del self._config.worker.task_configs[task_id]
            
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Failed to remove task {task_id}: {e}")
            return False
    
    def remove_pipeline(self, pipeline_id: str) -> bool:
        """Remove pipeline from configuration"""
        try:
            if not self._config:
                self.load_config()
            
            # Remove from active pipelines
            if pipeline_id in self._config.worker.active_pipelines:
                self._config.worker.active_pipelines.remove(pipeline_id)
            
            # Remove pipeline config
            if pipeline_id in self._config.worker.pipeline_configs:
                del self._config.worker.pipeline_configs[pipeline_id]
            
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Failed to remove pipeline {pipeline_id}: {e}")
            return False
    
    def get_task_config(self, task_id: str) -> Optional[TaskConfig]:
        """Get task configuration"""
        if not self._config:
            self.load_config()
        return self._config.worker.task_configs.get(task_id)
    
    def get_pipeline_config(self, pipeline_id: str) -> Optional[PipelineConfig]:
        """Get pipeline configuration"""
        if not self._config:
            self.load_config()
        return self._config.worker.pipeline_configs.get(pipeline_id)
    
    def reload_config(self) -> AppConfig:
        """Reload configuration from file"""
        self._config = None
        return self.load_config()
    
    def validate_config(self) -> bool:
        """Validate current configuration"""
        try:
            if not self._config:
                self.load_config()
            
            # Validate that active tasks have configs
            for task_id in self._config.worker.active_tasks:
                if task_id not in self._config.worker.task_configs:
                    logger.warning(f"Active task {task_id} missing configuration")
            
            # Validate that active pipelines have configs
            for pipeline_id in self._config.worker.active_pipelines:
                if pipeline_id not in self._config.worker.pipeline_configs:
                    logger.warning(f"Active pipeline {pipeline_id} missing configuration")
            
            # Validate pipeline task dependencies
            for pipeline_id, pipeline_config in self._config.worker.pipeline_configs.items():
                for task_id in pipeline_config.tasks:
                    if task_id not in self._config.worker.task_configs:
                        logger.warning(f"Pipeline {pipeline_id} references missing task {task_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return False


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """Get application configuration"""
    return config_manager.config


def reload_config() -> AppConfig:
    """Reload configuration"""
    return config_manager.reload_config()