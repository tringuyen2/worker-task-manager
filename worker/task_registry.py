"""
Dynamic task registration for Celery worker
"""
import uuid
from typing import Dict, Any, List, Optional
from loguru import logger

from .celery_app import celery_app, ai_task
from ..core.config.manager import get_config
from ..core.task_loader.loader import task_loader
from ..core.database.operations import db_ops
from ..core.database.models import ExecutionRecord, TaskStatus, TaskType
from ..pipeline.executor import pipeline_executor


class TaskRegistry:
    """Registry for dynamic task registration"""
    
    def __init__(self):
        self.registered_tasks: Dict[str, Any] = {}
        self.registered_pipelines: Dict[str, Any] = {}
    
    def load_and_register_tasks(self):
        """Load and register all active tasks and pipelines"""
        config = get_config().worker
        
        # Load and register tasks
        for task_id in config.active_tasks:
            self.register_task(task_id)
        
        # Load and register pipelines
        for pipeline_id in config.active_pipelines:
            self.register_pipeline(pipeline_id)
    
    def register_task(self, task_id: str) -> bool:
        """
        Register a single task with Celery
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load task
            task_instance = task_loader.load_task(task_id)
            if not task_instance:
                logger.error(f"Failed to load task: {task_id}")
                return False
            
            # Get task configuration
            task_config = get_config().worker.task_configs.get(task_id)
            queue = getattr(task_config, 'queue', 'default') if task_config else 'default'
            priority = getattr(task_config, 'priority', 5) if task_config else 5
            max_retries = getattr(task_config, 'max_retries', 3) if task_config else 3
            timeout = getattr(task_config, 'timeout', 300) if task_config else 300
            
            # Create Celery task function
            def task_function(input_data: Any, execution_id: Optional[str] = None):
                """Dynamic task execution function"""
                if not execution_id:
                    execution_id = str(uuid.uuid4())
                
                try:
                    logger.info(f"Executing task {task_id} with execution_id: {execution_id}")
                    
                    # Execute task
                    result = task_instance.process(input_data)
                    
                    logger.info(f"Task {task_id} completed successfully")
                    return {
                        "execution_id": execution_id,
                        "task_id": task_id,
                        "status": "success",
                        "result": result
                    }
                    
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    raise
            
            # Register with Celery using decorator
            registered_task = ai_task(
                name=task_id,
                queue=queue,
                priority=priority,
                max_retries=max_retries,
                timeout=timeout
            )(task_function)
            
            self.registered_tasks[task_id] = registered_task
            logger.info(f"Registered task: {task_id} on queue: {queue}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register task {task_id}: {e}")
            return False
    
    def register_pipeline(self, pipeline_id: str) -> bool:
        """
        Register a pipeline with Celery
        
        Args:
            pipeline_id: Pipeline identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load pipeline
            pipeline_instance = task_loader.load_pipeline(pipeline_id)
            if not pipeline_instance:
                logger.error(f"Failed to load pipeline: {pipeline_id}")
                return False
            
            # Get pipeline configuration
            pipeline_config = get_config().worker.pipeline_configs.get(pipeline_id)
            queue = getattr(pipeline_config, 'queue', 'pipeline') if pipeline_config else 'pipeline'
            priority = getattr(pipeline_config, 'priority', 5) if pipeline_config else 5
            timeout = getattr(pipeline_config, 'timeout', 600) if pipeline_config else 600
            
            # Create Celery pipeline function
            def pipeline_function(input_data: Any, execution_id: Optional[str] = None):
                """Dynamic pipeline execution function"""
                if not execution_id:
                    execution_id = str(uuid.uuid4())
                
                try:
                    logger.info(f"Executing pipeline {pipeline_id} with execution_id: {execution_id}")
                    
                    # Execute pipeline
                    result = pipeline_executor.execute_pipeline(
                        pipeline_instance, 
                        input_data, 
                        execution_id
                    )
                    
                    logger.info(f"Pipeline {pipeline_id} completed successfully")
                    return {
                        "execution_id": execution_id,
                        "pipeline_id": pipeline_id,
                        "status": "success",
                        "result": result
                    }
                    
                except Exception as e:
                    logger.error(f"Pipeline {pipeline_id} failed: {e}")
                    raise
            
            # Register with Celery using decorator
            registered_pipeline = ai_task(
                name=pipeline_id,
                queue=queue,
                priority=priority,
                timeout=timeout
            )(pipeline_function)
            
            self.registered_pipelines[pipeline_id] = registered_pipeline
            logger.info(f"Registered pipeline: {pipeline_id} on queue: {queue}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register pipeline {pipeline_id}: {e}")
            return False
    
    def unregister_task(self, task_id: str) -> bool:
        """
        Unregister a task
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if task_id in self.registered_tasks:
                del self.registered_tasks[task_id]
                # Unload from task loader
                task_loader.unload_task(task_id)
                logger.info(f"Unregistered task: {task_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to unregister task {task_id}: {e}")
            return False
    
    def unregister_pipeline(self, pipeline_id: str) -> bool:
        """
        Unregister a pipeline
        
        Args:
            pipeline_id: Pipeline identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if pipeline_id in self.registered_pipelines:
                del self.registered_pipelines[pipeline_id]
                # Unload from task loader
                task_loader.unload_pipeline(pipeline_id)
                logger.info(f"Unregistered pipeline: {pipeline_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to unregister pipeline {pipeline_id}: {e}")
            return False
    
    def reload_task(self, task_id: str) -> bool:
        """
        Reload a task (unregister and register again)
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.unregister_task(task_id)
            return self.register_task(task_id)
            
        except Exception as e:
            logger.error(f"Failed to reload task {task_id}: {e}")
            return False
    
    def reload_pipeline(self, pipeline_id: str) -> bool:
        """
        Reload a pipeline (unregister and register again)
        
        Args:
            pipeline_id: Pipeline identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.unregister_pipeline(pipeline_id)
            return self.register_pipeline(pipeline_id)
            
        except Exception as e:
            logger.error(f"Failed to reload pipeline {pipeline_id}: {e}")
            return False
    
    def get_registered_tasks(self) -> List[str]:
        """Get list of registered task IDs"""
        return list(self.registered_tasks.keys())
    
    def get_registered_pipelines(self) -> List[str]:
        """Get list of registered pipeline IDs"""
        return list(self.registered_pipelines.keys())
    
    def is_task_registered(self, task_id: str) -> bool:
        """Check if task is registered"""
        return task_id in self.registered_tasks
    
    def is_pipeline_registered(self, pipeline_id: str) -> bool:
        """Check if pipeline is registered"""
        return pipeline_id in self.registered_pipelines
    
    def submit_task(self, task_id: str, input_data: Any, **kwargs) -> Optional[str]:
        """
        Submit task for execution
        
        Args:
            task_id: Task identifier
            input_data: Input data for task
            **kwargs: Additional Celery options
            
        Returns:
            Execution ID if successful, None otherwise
        """
        try:
            if not self.is_task_registered(task_id):
                logger.error(f"Task not registered: {task_id}")
                return None
            
            # Generate execution ID
            execution_id = str(uuid.uuid4())
            
            # Submit to Celery
            task = self.registered_tasks[task_id]
            result = task.delay(input_data, execution_id, **kwargs)
            
            logger.info(f"Submitted task {task_id} with execution_id: {execution_id}, celery_id: {result.id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to submit task {task_id}: {e}")
            return None
    
    def submit_pipeline(self, pipeline_id: str, input_data: Any, **kwargs) -> Optional[str]:
        """
        Submit pipeline for execution
        
        Args:
            pipeline_id: Pipeline identifier
            input_data: Input data for pipeline
            **kwargs: Additional Celery options
            
        Returns:
            Execution ID if successful, None otherwise
        """
        try:
            if not self.is_pipeline_registered(pipeline_id):
                logger.error(f"Pipeline not registered: {pipeline_id}")
                return None
            
            # Generate execution ID
            execution_id = str(uuid.uuid4())
            
            # Submit to Celery
            pipeline = self.registered_pipelines[pipeline_id]
            result = pipeline.delay(input_data, execution_id, **kwargs)
            
            logger.info(f"Submitted pipeline {pipeline_id} with execution_id: {execution_id}, celery_id: {result.id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to submit pipeline {pipeline_id}: {e}")
            return None
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task information"""
        try:
            if not self.is_task_registered(task_id):
                return None
            
            # Get metadata from database
            metadata = db_ops.get_task_metadata(task_id)
            if not metadata:
                return None
            
            # Get task configuration
            task_config = get_config().worker.task_configs.get(task_id)
            
            return {
                "task_id": task_id,
                "name": metadata.name,
                "description": metadata.description,
                "version": metadata.version,
                "author": metadata.author,
                "queue": getattr(task_config, 'queue', 'default') if task_config else 'default',
                "priority": getattr(task_config, 'priority', 5) if task_config else 5,
                "timeout": getattr(task_config, 'timeout', 300) if task_config else 300,
                "is_registered": True,
                "is_active": metadata.is_active
            }
            
        except Exception as e:
            logger.error(f"Failed to get task info {task_id}: {e}")
            return None
    
    def get_pipeline_info(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline information"""
        try:
            if not self.is_pipeline_registered(pipeline_id):
                return None
            
            # Get metadata from database
            metadata = db_ops.get_pipeline_metadata(pipeline_id)
            if not metadata:
                return None
            
            # Get pipeline configuration
            pipeline_config = get_config().worker.pipeline_configs.get(pipeline_id)
            
            return {
                "pipeline_id": pipeline_id,
                "name": metadata.name,
                "description": metadata.description,
                "version": metadata.version,
                "author": metadata.author,
                "tasks": metadata.tasks,
                "parallel": metadata.parallel,
                "fail_fast": metadata.fail_fast,
                "queue": getattr(pipeline_config, 'queue', 'pipeline') if pipeline_config else 'pipeline',
                "priority": getattr(pipeline_config, 'priority', 5) if pipeline_config else 5,
                "timeout": getattr(pipeline_config, 'timeout', 600) if pipeline_config else 600,
                "is_registered": True,
                "is_active": metadata.is_active
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline info {pipeline_id}: {e}")
            return None


# Global task registry instance
task_registry = TaskRegistry()