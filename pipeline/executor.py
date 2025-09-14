"""
Pipeline execution engine
"""
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger

from core.config.manager import get_config
from core.task_loader.loader import task_loader
from core.database.operations import db_ops
from core.database.models import ExecutionRecord, TaskStatus, TaskType


class PipelineExecutor:
    """Pipeline execution engine"""
    
    def __init__(self):
        self.config = get_config().worker
    
    def execute_pipeline(self, pipeline_instance: Any, input_data: Any, execution_id: str) -> Any:
        """
        Execute pipeline instance
        
        Args:
            pipeline_instance: Pipeline instance to execute
            input_data: Input data for pipeline
            execution_id: Execution identifier
            
        Returns:
            Pipeline execution result
        """
        try:
            logger.info(f"Starting pipeline execution: {pipeline_instance._pipeline_id} [{execution_id}]")
            
            # Create execution record
            self._create_pipeline_execution_record(pipeline_instance, input_data, execution_id)
            
            # Execute pipeline
            result = pipeline_instance.execute(input_data)
            
            # Update execution record with success
            self._update_execution_record_success(execution_id, result)
            
            logger.info(f"Pipeline execution completed: {pipeline_instance._pipeline_id} [{execution_id}]")
            return result
            
        except Exception as e:
            # Update execution record with error
            self._update_execution_record_error(execution_id, e)
            logger.error(f"Pipeline execution failed: {pipeline_instance._pipeline_id} [{execution_id}] - {e}")
            raise
    
    def execute_task_in_pipeline(self, task_id: str, input_data: Any, pipeline_execution_id: str) -> Any:
        """
        Execute individual task within pipeline context
        
        Args:
            task_id: Task identifier
            input_data: Input data for task
            pipeline_execution_id: Parent pipeline execution ID
            
        Returns:
            Task execution result
        """
        try:
            # Generate task execution ID
            task_execution_id = f"{pipeline_execution_id}_task_{task_id}_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"Executing task in pipeline: {task_id} [{task_execution_id}]")
            
            # Load task
            task_instance = task_loader.load_task(task_id)
            if not task_instance:
                raise RuntimeError(f"Failed to load task: {task_id}")
            
            # Create task execution record
            self._create_task_execution_record(task_instance, input_data, task_execution_id, pipeline_execution_id)
            
            # Execute task
            result = task_instance.process(input_data)
            
            # Update execution record with success
            self._update_execution_record_success(task_execution_id, result)
            
            logger.info(f"Task execution in pipeline completed: {task_id} [{task_execution_id}]")
            return result
            
        except Exception as e:
            # Update execution record with error
            self._update_execution_record_error(task_execution_id, e)
            logger.error(f"Task execution in pipeline failed: {task_id} [{task_execution_id}] - {e}")
            raise
    
    def _create_pipeline_execution_record(self, pipeline_instance: Any, input_data: Any, execution_id: str):
        """Create pipeline execution record"""
        try:
            execution_record = ExecutionRecord(
                execution_id=execution_id,
                celery_task_id=execution_id,  # Same as execution_id for pipelines
                pipeline_id=pipeline_instance._pipeline_id,
                task_type=TaskType.PIPELINE,
                worker_id=self.config.worker_id,
                worker_hostname="localhost",  # Will be updated by Celery signals
                queue="pipeline",
                status=TaskStatus.RUNNING,
                started_at=datetime.utcnow(),
                input_data={"input": input_data} if input_data is not None else {}
            )
            
            db_ops.create_execution_record(execution_record)
            
        except Exception as e:
            logger.error(f"Failed to create pipeline execution record: {e}")
    
    def _create_task_execution_record(self, task_instance: Any, input_data: Any, execution_id: str, pipeline_execution_id: str):
        """Create task execution record"""
        try:
            execution_record = ExecutionRecord(
                execution_id=execution_id,
                celery_task_id=pipeline_execution_id,  # Link to parent pipeline
                task_id=task_instance._task_id,
                task_type=TaskType.SINGLE,
                worker_id=self.config.worker_id,
                worker_hostname="localhost",
                queue="default",
                status=TaskStatus.RUNNING,
                started_at=datetime.utcnow(),
                input_data={"input": input_data} if input_data is not None else {},
                metadata={"pipeline_execution_id": pipeline_execution_id}
            )
            
            db_ops.create_execution_record(execution_record)
            
        except Exception as e:
            logger.error(f"Failed to create task execution record: {e}")
    
    def _update_execution_record_success(self, execution_id: str, result: Any):
        """Update execution record with success"""
        try:
            updates = {
                "status": TaskStatus.SUCCESS,
                "completed_at": datetime.utcnow(),
                "output_data": {"result": result} if result is not None else {}
            }
            
            # Calculate duration
            execution_record = db_ops.get_execution_record(execution_id)
            if execution_record and execution_record.started_at:
                duration = (datetime.utcnow() - execution_record.started_at).total_seconds()
                updates["duration"] = duration
            
            db_ops.update_execution_record(execution_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to update execution record success: {e}")
    
    def _update_execution_record_error(self, execution_id: str, error: Exception):
        """Update execution record with error"""
        try:
            import traceback
            
            updates = {
                "status": TaskStatus.FAILED,
                "completed_at": datetime.utcnow(),
                "error_message": str(error),
                "error_traceback": traceback.format_exc()
            }
            
            # Calculate duration
            execution_record = db_ops.get_execution_record(execution_id)
            if execution_record and execution_record.started_at:
                duration = (datetime.utcnow() - execution_record.started_at).total_seconds()
                updates["duration"] = duration
            
            db_ops.update_execution_record(execution_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to update execution record error: {e}")


class CeleryPipelineExecutor(PipelineExecutor):
    """
    Pipeline executor that uses Celery for task execution
    """
    
    def execute_task_in_pipeline(self, task_id: str, input_data: Any, pipeline_execution_id: str) -> Any:
        """
        Execute task using Celery within pipeline context
        
        Args:
            task_id: Task identifier
            input_data: Input data for task
            pipeline_execution_id: Parent pipeline execution ID
            
        Returns:
            Task execution result
        """
        try:
            from ..worker.task_registry import task_registry
            
            # Check if task is registered
            if not task_registry.is_task_registered(task_id):
                raise RuntimeError(f"Task not registered with Celery: {task_id}")
            
            # Submit task to Celery
            task = task_registry.registered_tasks[task_id]
            
            # Generate task execution ID
            task_execution_id = f"{pipeline_execution_id}_task_{task_id}_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"Submitting task to Celery in pipeline: {task_id} [{task_execution_id}]")
            
            # Execute task synchronously (get result)
            result = task.apply(args=[input_data, task_execution_id])
            
            if result.successful():
                task_result = result.result
                logger.info(f"Celery task in pipeline completed: {task_id} [{task_execution_id}]")
                return task_result.get('result') if isinstance(task_result, dict) else task_result
            else:
                error_msg = f"Celery task failed: {result.traceback}"
                logger.error(f"Celery task in pipeline failed: {task_id} [{task_execution_id}] - {error_msg}")
                raise RuntimeError(error_msg)
            
        except Exception as e:
            logger.error(f"Failed to execute Celery task in pipeline: {task_id} - {e}")
            raise


class SequentialPipelineExecutor(PipelineExecutor):
    """
    Sequential pipeline executor implementation
    """
    
    def execute_pipeline_tasks(self, task_list: List[str], input_data: Any, pipeline_execution_id: str) -> Any:
        """
        Execute tasks sequentially
        
        Args:
            task_list: List of task IDs to execute
            input_data: Initial input data
            pipeline_execution_id: Pipeline execution ID
            
        Returns:
            Final result
        """
        current_data = input_data
        task_results = {}
        
        logger.info(f"Executing {len(task_list)} tasks sequentially in pipeline [{pipeline_execution_id}]")
        
        for i, task_id in enumerate(task_list):
            try:
                logger.info(f"Executing sequential task {i+1}/{len(task_list)}: {task_id}")
                
                # Execute task
                task_result = self.execute_task_in_pipeline(task_id, current_data, pipeline_execution_id)
                
                # Store result
                task_results[task_id] = task_result
                
                # Use task result as input for next task
                current_data = task_result
                
                logger.info(f"Sequential task {task_id} completed successfully")
                
            except Exception as e:
                logger.error(f"Sequential task {task_id} failed: {e}")
                raise
        
        return {
            "final_result": current_data,
            "task_results": task_results
        }


class ParallelPipelineExecutor(PipelineExecutor):
    """
    Parallel pipeline executor implementation
    """
    
    def execute_pipeline_tasks(self, task_list: List[str], input_data: Any, pipeline_execution_id: str) -> Any:
        """
        Execute tasks in parallel
        
        Args:
            task_list: List of task IDs to execute
            input_data: Input data for all tasks
            pipeline_execution_id: Pipeline execution ID
            
        Returns:
            Combined results
        """
        import concurrent.futures
        
        logger.info(f"Executing {len(task_list)} tasks in parallel in pipeline [{pipeline_execution_id}]")
        
        # Execute tasks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(task_list)) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.execute_task_in_pipeline, task_id, input_data, pipeline_execution_id): task_id
                for task_id in task_list
            }
            
            # Collect results
            task_results = {}
            errors = {}
            
            for future in concurrent.futures.as_completed(future_to_task):
                task_id = future_to_task[future]
                try:
                    result = future.result()
                    task_results[task_id] = result
                    logger.info(f"Parallel task {task_id} completed successfully")
                    
                except Exception as e:
                    errors[task_id] = e
                    logger.error(f"Parallel task {task_id} failed: {e}")
            
            # Handle errors
            if errors:
                failed_tasks = list(errors.keys())
                error_msg = f"Tasks failed in parallel execution: {failed_tasks}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        return {
            "task_results": task_results,
            "successful_tasks": list(task_results.keys())
        }


# Global pipeline executor instances
pipeline_executor = PipelineExecutor()
celery_pipeline_executor = CeleryPipelineExecutor()
sequential_pipeline_executor = SequentialPipelineExecutor()
parallel_pipeline_executor = ParallelPipelineExecutor()