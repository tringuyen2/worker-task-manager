"""
Base class for all AI pipelines
"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, Union
from loguru import logger


class PipelineBase(ABC):
    """Abstract base class for all AI pipelines"""
    
    def __init__(self):
        self._pipeline_id: Optional[str] = None
        self._config: Dict[str, Any] = {}
        self._metadata: Optional[Any] = None
        self._task_results: Dict[str, Any] = {}
    
    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """
        Execute pipeline with input data
        
        Args:
            input_data: Input data for pipeline
            
        Returns:
            Pipeline result
        """
        pass
    
    def get_tasks(self) -> List[str]:
        """
        Get list of task IDs in pipeline
        
        Returns:
            List of task IDs
        """
        return []
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data before execution
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get pipeline information
        
        Returns:
            Dictionary with pipeline information
        """
        return {
            "pipeline_id": self._pipeline_id,
            "name": self.__class__.__name__,
            "description": self.__doc__ or "",
            "tasks": self.get_tasks(),
            "config": self._config
        }
    
    def setup(self):
        """
        Setup method called before execution
        Override in subclasses if needed
        """
        pass
    
    def cleanup(self):
        """
        Cleanup method called after execution
        Override in subclasses if needed
        """
        pass
    
    def log_info(self, message: str):
        """Log info message with pipeline context"""
        logger.info(f"[{self._pipeline_id}] {message}")
    
    def log_warning(self, message: str):
        """Log warning message with pipeline context"""
        logger.warning(f"[{self._pipeline_id}] {message}")
    
    def log_error(self, message: str):
        """Log error message with pipeline context"""
        logger.error(f"[{self._pipeline_id}] {message}")
    
    @property
    def pipeline_id(self) -> Optional[str]:
        """Get pipeline ID"""
        return self._pipeline_id
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get pipeline configuration"""
        return self._config
    
    @property
    def metadata(self) -> Optional[Any]:
        """Get pipeline metadata"""
        return self._metadata
    
    @property
    def task_results(self) -> Dict[str, Any]:
        """Get intermediate task results"""
        return self._task_results


class SequentialPipeline(PipelineBase):
    """
    Sequential pipeline base class
    Executes tasks one after another
    """
    
    def __init__(self):
        super().__init__()
        self._is_setup = False
    
    def execute(self, input_data: Any) -> Any:
        """
        Execute pipeline sequentially
        
        Args:
            input_data: Input data for pipeline
            
        Returns:
            Pipeline result
        """
        try:
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError("Input validation failed")
            
            # Setup if needed
            if not self._is_setup:
                self.setup()
                self._is_setup = True
            
            # Log start
            self.log_info(f"Starting sequential execution with input type: {type(input_data).__name__}")
            
            # Execute tasks sequentially
            result = self._execute_sequential(input_data)
            
            # Log completion
            self.log_info(f"Sequential execution completed, result type: {type(result).__name__}")
            
            return result
            
        except Exception as e:
            self.log_error(f"Sequential execution failed: {e}")
            raise
        finally:
            # Cleanup
            try:
                self.cleanup()
            except Exception as e:
                self.log_warning(f"Cleanup failed: {e}")
    
    def _execute_sequential(self, input_data: Any) -> Any:
        """
        Execute tasks sequentially
        
        Args:
            input_data: Input data
            
        Returns:
            Final result
        """
        current_data = input_data
        task_list = self.get_tasks()
        
        self.log_info(f"Executing {len(task_list)} tasks sequentially")
        
        for i, task_id in enumerate(task_list):
            try:
                self.log_info(f"Executing task {i+1}/{len(task_list)}: {task_id}")
                
                # Execute individual task
                task_result = self.execute_task(task_id, current_data)
                
                # Store task result
                self._task_results[task_id] = task_result
                
                # Process task result for next task
                current_data = self.process_task_result(task_id, task_result, current_data)
                
                self.log_info(f"Task {task_id} completed successfully")
                
            except Exception as e:
                self.log_error(f"Task {task_id} failed: {e}")
                if self.should_stop_on_error(task_id, e):
                    raise
                else:
                    # Continue with error handling
                    current_data = self.handle_task_error(task_id, e, current_data)
        
        # Process final result
        final_result = self.process_final_result(current_data)
        
        return final_result
    
    @abstractmethod
    def execute_task(self, task_id: str, input_data: Any) -> Any:
        """
        Execute individual task
        Override in subclasses
        
        Args:
            task_id: Task identifier
            input_data: Input data for task
            
        Returns:
            Task result
        """
        pass
    
    def process_task_result(self, task_id: str, task_result: Any, current_data: Any) -> Any:
        """
        Process task result for next task
        Override in subclasses if needed
        
        Args:
            task_id: Task identifier
            task_result: Result from task
            current_data: Current pipeline data
            
        Returns:
            Data for next task
        """
        return task_result
    
    def process_final_result(self, final_data: Any) -> Any:
        """
        Process final pipeline result
        Override in subclasses if needed
        
        Args:
            final_data: Final data from last task
            
        Returns:
            Final pipeline result
        """
        return final_data
    
    def should_stop_on_error(self, task_id: str, error: Exception) -> bool:
        """
        Determine if pipeline should stop on task error
        Override in subclasses if needed
        
        Args:
            task_id: Task that failed
            error: Exception that occurred
            
        Returns:
            True to stop pipeline, False to continue
        """
        return True  # Default: stop on first error
    
    def handle_task_error(self, task_id: str, error: Exception, current_data: Any) -> Any:
        """
        Handle task error and return data for next task
        Override in subclasses if needed
        
        Args:
            task_id: Task that failed
            error: Exception that occurred
            current_data: Current pipeline data
            
        Returns:
            Data for next task
        """
        return current_data


class ParallelPipeline(PipelineBase):
    """
    Parallel pipeline base class
    Executes tasks in parallel
    """
    
    def __init__(self):
        super().__init__()
        self._is_setup = False
    
    def execute(self, input_data: Any) -> Any:
        """
        Execute pipeline in parallel
        
        Args:
            input_data: Input data for pipeline
            
        Returns:
            Pipeline result
        """
        try:
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError("Input validation failed")
            
            # Setup if needed
            if not self._is_setup:
                self.setup()
                self._is_setup = True
            
            # Log start
            self.log_info(f"Starting parallel execution with input type: {type(input_data).__name__}")
            
            # Execute tasks in parallel
            result = self._execute_parallel(input_data)
            
            # Log completion
            self.log_info(f"Parallel execution completed, result type: {type(result).__name__}")
            
            return result
            
        except Exception as e:
            self.log_error(f"Parallel execution failed: {e}")
            raise
        finally:
            # Cleanup
            try:
                self.cleanup()
            except Exception as e:
                self.log_warning(f"Cleanup failed: {e}")
    
    def _execute_parallel(self, input_data: Any) -> Any:
        """
        Execute tasks in parallel
        
        Args:
            input_data: Input data
            
        Returns:
            Final result
        """
        import concurrent.futures
        
        task_list = self.get_tasks()
        self.log_info(f"Executing {len(task_list)} tasks in parallel")
        
        # Prepare input data for each task
        task_inputs = self.prepare_parallel_inputs(input_data, task_list)
        
        # Execute tasks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(task_list)) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.execute_task, task_id, task_inputs.get(task_id, input_data)): task_id
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
                    self._task_results[task_id] = result
                    self.log_info(f"Task {task_id} completed successfully")
                    
                except Exception as e:
                    errors[task_id] = e
                    self.log_error(f"Task {task_id} failed: {e}")
            
            # Handle errors
            if errors and self.should_fail_on_any_error():
                failed_tasks = list(errors.keys())
                raise RuntimeError(f"Tasks failed: {failed_tasks}")
        
        # Process parallel results
        final_result = self.process_parallel_results(task_results, input_data)
        
        return final_result
    
    def prepare_parallel_inputs(self, input_data: Any, task_list: List[str]) -> Dict[str, Any]:
        """
        Prepare input data for parallel tasks
        Override in subclasses if needed
        
        Args:
            input_data: Original input data
            task_list: List of task IDs
            
        Returns:
            Dictionary mapping task_id to input data
        """
        # Default: all tasks get same input
        return {task_id: input_data for task_id in task_list}
    
    @abstractmethod
    def execute_task(self, task_id: str, input_data: Any) -> Any:
        """
        Execute individual task
        Override in subclasses
        
        Args:
            task_id: Task identifier
            input_data: Input data for task
            
        Returns:
            Task result
        """
        pass
    
    def process_parallel_results(self, task_results: Dict[str, Any], input_data: Any) -> Any:
        """
        Process results from parallel tasks
        Override in subclasses
        
        Args:
            task_results: Dictionary of task_id -> result
            input_data: Original input data
            
        Returns:
            Final pipeline result
        """
        return task_results
    
    def should_fail_on_any_error(self) -> bool:
        """
        Determine if pipeline should fail if any task fails
        Override in subclasses if needed
        
        Returns:
            True to fail on any error, False to continue
        """
        return True  # Default: fail if any task fails


class ConditionalPipeline(SequentialPipeline):
    """
    Conditional pipeline base class
    Executes tasks based on conditions
    """
    
    def _execute_sequential(self, input_data: Any) -> Any:
        """
        Execute tasks conditionally
        
        Args:
            input_data: Input data
            
        Returns:
            Final result
        """
        current_data = input_data
        task_list = self.get_tasks()
        
        self.log_info(f"Executing conditional pipeline with {len(task_list)} potential tasks")
        
        executed_tasks = []
        
        for task_id in task_list:
            # Check if task should be executed
            if self.should_execute_task(task_id, current_data):
                try:
                    self.log_info(f"Executing conditional task: {task_id}")
                    
                    # Execute task
                    task_result = self.execute_task(task_id, current_data)
                    
                    # Store task result
                    self._task_results[task_id] = task_result
                    executed_tasks.append(task_id)
                    
                    # Process task result
                    current_data = self.process_task_result(task_id, task_result, current_data)
                    
                    self.log_info(f"Conditional task {task_id} completed successfully")
                    
                    # Check if should continue
                    if not self.should_continue_after_task(task_id, task_result, current_data):
                        self.log_info(f"Pipeline stopped after task {task_id}")
                        break
                    
                except Exception as e:
                    self.log_error(f"Conditional task {task_id} failed: {e}")
                    if self.should_stop_on_error(task_id, e):
                        raise
            else:
                self.log_info(f"Skipping conditional task: {task_id}")
        
        self.log_info(f"Executed {len(executed_tasks)} tasks: {executed_tasks}")
        
        # Process final result
        final_result = self.process_final_result(current_data)
        
        return final_result
    
    @abstractmethod
    def should_execute_task(self, task_id: str, current_data: Any) -> bool:
        """
        Determine if task should be executed
        Override in subclasses
        
        Args:
            task_id: Task identifier
            current_data: Current pipeline data
            
        Returns:
            True to execute task, False to skip
        """
        pass
    
    def should_continue_after_task(self, task_id: str, task_result: Any, current_data: Any) -> bool:
        """
        Determine if pipeline should continue after task
        Override in subclasses if needed
        
        Args:
            task_id: Task that was executed
            task_result: Result from task
            current_data: Current pipeline data
            
        Returns:
            True to continue, False to stop
        """
        return True  # Default: continue


class BranchingPipeline(PipelineBase):
    """
    Branching pipeline base class
    Routes data through different task branches
    """
    
    def execute(self, input_data: Any) -> Any:
        """
        Execute branching pipeline
        
        Args:
            input_data: Input data for pipeline
            
        Returns:
            Pipeline result
        """
        try:
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError("Input validation failed")
            
            # Setup if needed
            self.setup()
            
            # Log start
            self.log_info(f"Starting branching execution with input type: {type(input_data).__name__}")
            
            # Determine branch
            branch = self.select_branch(input_data)
            self.log_info(f"Selected branch: {branch}")
            
            # Execute branch
            result = self.execute_branch(branch, input_data)
            
            # Log completion
            self.log_info(f"Branching execution completed, result type: {type(result).__name__}")
            
            return result
            
        except Exception as e:
            self.log_error(f"Branching execution failed: {e}")
            raise
        finally:
            # Cleanup
            try:
                self.cleanup()
            except Exception as e:
                self.log_warning(f"Cleanup failed: {e}")
    
    @abstractmethod
    def select_branch(self, input_data: Any) -> str:
        """
        Select which branch to execute
        Override in subclasses
        
        Args:
            input_data: Input data
            
        Returns:
            Branch identifier
        """
        pass
    
    @abstractmethod
    def execute_branch(self, branch: str, input_data: Any) -> Any:
        """
        Execute specific branch
        Override in subclasses
        
        Args:
            branch: Branch identifier
            input_data: Input data
            
        Returns:
            Branch result
        """
        pass
    
    def get_available_branches(self) -> List[str]:
        """
        Get list of available branches
        Override in subclasses
        
        Returns:
            List of branch identifiers
        """
        return []