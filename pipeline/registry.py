"""
Pipeline Registry for managing custom pipelines
"""
import uuid
import time
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from .models import BasePipeline, TaskStep, PipelineResult, PipelineStage
from .face_processing_pipeline import FaceProcessingPipeline
from .json_loader import json_pipeline_loader
from worker.task_registry import task_registry
from core.config.manager import get_config


class PipelineRegistry:
    """Registry for custom pipelines with Celery integration"""

    def __init__(self):
        self.registered_pipelines: Dict[str, BasePipeline] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

    def register_pipeline(self, pipeline: BasePipeline) -> bool:
        """Register a pipeline"""
        try:
            self.registered_pipelines[pipeline.pipeline_id] = pipeline
            logger.info(f"Registered pipeline: {pipeline.pipeline_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register pipeline {pipeline.pipeline_id}: {e}")
            return False

    def unregister_pipeline(self, pipeline_id: str) -> bool:
        """Unregister a pipeline"""
        try:
            if pipeline_id in self.registered_pipelines:
                del self.registered_pipelines[pipeline_id]
                logger.info(f"Unregistered pipeline: {pipeline_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister pipeline {pipeline_id}: {e}")
            return False

    def get_pipeline(self, pipeline_id: str) -> Optional[BasePipeline]:
        """Get a registered pipeline"""
        return self.registered_pipelines.get(pipeline_id)

    def list_pipelines(self) -> List[str]:
        """List all registered pipeline IDs"""
        return list(self.registered_pipelines.keys())

    def execute_pipeline(self, pipeline_id: str, input_data: Any) -> PipelineResult:
        """Execute a pipeline with Celery workers"""
        execution_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Get pipeline
            pipeline = self.get_pipeline(pipeline_id)
            if not pipeline:
                raise ValueError(f"Pipeline not found: {pipeline_id}")

            # Validate input
            if not pipeline.validate_input(input_data):
                raise ValueError("Pipeline input validation failed")

            logger.info(f"Starting pipeline execution: {pipeline_id} [{execution_id}]")

            # Get pipeline steps
            steps = pipeline.define_steps()
            step_results: Dict[str, Any] = {}

            # Execute steps in dependency order
            step_results = self._execute_steps(pipeline, steps, input_data, execution_id)

            # Process final results
            final_result = pipeline.process_results(step_results)

            execution_time = time.time() - start_time

            logger.info(f"Pipeline execution completed: {pipeline_id} [{execution_id}] in {execution_time:.2f}s")

            return PipelineResult(
                pipeline_id=pipeline_id,
                execution_id=execution_id,
                status=PipelineStage.COMPLETED,
                results=final_result,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Pipeline execution failed: {pipeline_id} [{execution_id}]: {e}")

            return PipelineResult(
                pipeline_id=pipeline_id,
                execution_id=execution_id,
                status=PipelineStage.FAILED,
                results={},
                execution_time=execution_time,
                error=str(e)
            )

    def _execute_steps(self, pipeline: BasePipeline, steps: List[TaskStep],
                      input_data: Any, execution_id: str) -> Dict[str, Any]:
        """Execute pipeline steps respecting dependencies and parallelism"""
        step_results: Dict[str, Any] = {}
        completed_steps: set = set()

        # Group steps by dependencies and parallel groups
        remaining_steps = steps.copy()

        while remaining_steps:
            # Find steps that can be executed (all dependencies completed)
            ready_steps = []
            for step in remaining_steps:
                if not step.depends_on or all(dep in completed_steps for dep in step.depends_on):
                    ready_steps.append(step)

            if not ready_steps:
                raise RuntimeError("Circular dependency detected in pipeline steps")

            # Group ready steps by parallel group
            parallel_groups: Dict[str, List[TaskStep]] = {}
            sequential_steps: List[TaskStep] = []

            for step in ready_steps:
                if step.parallel_group:
                    if step.parallel_group not in parallel_groups:
                        parallel_groups[step.parallel_group] = []
                    parallel_groups[step.parallel_group].append(step)
                else:
                    sequential_steps.append(step)

            # Execute sequential steps first
            for step in sequential_steps:
                step_input = self._prepare_step_input(pipeline, step, input_data, step_results)
                result = self._execute_single_step(step, step_input)
                step_results[step.task_id] = result
                completed_steps.add(step.task_id)
                remaining_steps.remove(step)

            # Execute parallel groups
            for group_name, group_steps in parallel_groups.items():
                logger.info(f"Executing parallel group '{group_name}' with {len(group_steps)} steps")
                group_results = self._execute_parallel_steps(pipeline, group_steps, input_data, step_results)

                for step, result in group_results:
                    step_results[step.task_id] = result
                    completed_steps.add(step.task_id)
                    remaining_steps.remove(step)

        return step_results

    def _prepare_step_input(self, pipeline: BasePipeline, step: TaskStep,
                           original_input: Any, step_results: Dict[str, Any]) -> Any:
        """Prepare input for a step"""
        if hasattr(pipeline, 'prepare_step_input'):
            return pipeline.prepare_step_input(step, original_input, step_results)
        return step.input_data or original_input

    def _execute_single_step(self, step: TaskStep, input_data: Any) -> Any:
        """Execute a single step using Celery if available, otherwise direct execution"""
        try:
            logger.info(f"Executing step: {step.task_id}")

            # Try to use Celery task first
            if task_registry.is_task_registered(step.task_id):
                # For demo, execute synchronously (in production, you'd use Celery async)
                from pipeline.router import task_router
                result = task_router.execute_task_sync(step.task_id, input_data)

                if result.status == "success":
                    return result.result
                else:
                    raise RuntimeError(f"Task failed: {result.error}")
            else:
                # Fallback to direct task execution
                from core.task_loader.loader import task_loader
                task_instance = task_loader.load_task(step.task_id)

                if not task_instance:
                    raise RuntimeError(f"Task not found: {step.task_id}")

                return task_instance.process(input_data)

        except Exception as e:
            logger.error(f"Step {step.task_id} failed: {e}")
            raise

    def _execute_parallel_steps(self, pipeline: BasePipeline, steps: List[TaskStep],
                               original_input: Any, step_results: Dict[str, Any]) -> List[Tuple[TaskStep, Any]]:
        """Execute multiple steps in parallel"""
        futures = []

        for step in steps:
            step_input = self._prepare_step_input(pipeline, step, original_input, step_results)

            # Handle case where step_input is a list (for parallel processing of faces)
            if isinstance(step_input, list):
                # Execute each item in the list
                for item_input in step_input:
                    future = self.executor.submit(self._execute_single_step, step, item_input)
                    futures.append((step, future, item_input))
            else:
                future = self.executor.submit(self._execute_single_step, step, step_input)
                futures.append((step, future, step_input))

        # Collect results
        results = []
        step_grouped_results: Dict[str, List[Any]] = {}

        for step, future, input_data in futures:
            try:
                result = future.result()

                # Group results by step for list inputs
                if step.task_id not in step_grouped_results:
                    step_grouped_results[step.task_id] = []
                step_grouped_results[step.task_id].append(result)

            except Exception as e:
                logger.error(f"Parallel step {step.task_id} failed: {e}")
                # Still add empty result to maintain structure
                if step.task_id not in step_grouped_results:
                    step_grouped_results[step.task_id] = []
                step_grouped_results[step.task_id].append(None)

        # Convert grouped results back to step results
        for step in steps:
            step_results_list = step_grouped_results.get(step.task_id, [])
            if len(step_results_list) == 1:
                results.append((step, step_results_list[0]))
            else:
                results.append((step, step_results_list))

        return results

    def register_builtin_pipelines(self):
        """Register built-in pipelines"""
        # Register face processing pipeline
        face_pipeline = FaceProcessingPipeline()
        self.register_pipeline(face_pipeline)

        logger.info("Registered built-in pipelines")

    def register_json_pipelines(self, config_path: Optional[str] = None) -> int:
        """Register pipelines from JSON configuration file"""
        try:
            # Load configuration
            if not json_pipeline_loader.load_config(config_path):
                logger.error("Failed to load JSON pipeline config")
                return 0

            # Validate configuration
            if not json_pipeline_loader.validate_config():
                logger.error("JSON pipeline config validation failed")
                return 0

            # Create and register all enabled pipelines
            pipelines = json_pipeline_loader.create_all_enabled_pipelines()
            registered_count = 0

            for pipeline in pipelines:
                if self.register_pipeline(pipeline):
                    registered_count += 1

            logger.info(f"Registered {registered_count} pipelines from JSON config")
            return registered_count

        except Exception as e:
            logger.error(f"Failed to register JSON pipelines: {e}")
            return 0

    def register_all_pipelines(self, json_config_path: Optional[str] = None) -> int:
        """Register both built-in and JSON-configured pipelines"""
        total_registered = 0

        # Register built-in pipelines
        try:
            self.register_builtin_pipelines()
            total_registered += 1  # Face processing pipeline
        except Exception as e:
            logger.error(f"Failed to register built-in pipelines: {e}")

        # Register JSON pipelines
        json_count = self.register_json_pipelines(json_config_path)
        total_registered += json_count

        logger.info(f"Total pipelines registered: {total_registered}")
        return total_registered

    def get_pipeline_info(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline information"""
        pipeline = self.get_pipeline(pipeline_id)
        if pipeline:
            return pipeline.get_info()
        return None


# Global pipeline registry instance
pipeline_registry = PipelineRegistry()