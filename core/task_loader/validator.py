"""
Task and pipeline validation
"""
import inspect
from typing import Any, List, Dict
from loguru import logger


class TaskValidator:
    """Validator for tasks and pipelines"""
    
    def validate_task(self, task_instance: Any) -> bool:
        """
        Validate task instance
        
        Args:
            task_instance: Task instance to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required methods
            if not hasattr(task_instance, 'process'):
                logger.error("Task missing required 'process' method")
                return False
            
            # Check process method signature
            process_method = getattr(task_instance, 'process')
            sig = inspect.signature(process_method)
            
            # Should have at least one parameter (input_data)
            if len(sig.parameters) < 1:
                logger.error("Task 'process' method should accept input_data parameter")
                return False
            
            # Check optional methods
            optional_methods = ['get_requirements', 'validate_input', 'get_info']
            for method_name in optional_methods:
                if hasattr(task_instance, method_name):
                    method = getattr(task_instance, method_name)
                    if not callable(method):
                        logger.error(f"Task {method_name} should be callable")
                        return False
            
            # Validate get_requirements if present
            if hasattr(task_instance, 'get_requirements'):
                try:
                    requirements = task_instance.get_requirements()
                    if not isinstance(requirements, list):
                        logger.error("get_requirements should return a list")
                        return False
                except Exception as e:
                    logger.error(f"Error calling get_requirements: {e}")
                    return False
            
            # Validate get_info if present
            if hasattr(task_instance, 'get_info'):
                try:
                    info = task_instance.get_info()
                    if not isinstance(info, dict):
                        logger.error("get_info should return a dictionary")
                        return False
                except Exception as e:
                    logger.error(f"Error calling get_info: {e}")
                    return False
            
            logger.info(f"Task validation passed: {getattr(task_instance, '_task_id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Task validation failed: {e}")
            return False
    
    def validate_pipeline(self, pipeline_instance: Any) -> bool:
        """
        Validate pipeline instance
        
        Args:
            pipeline_instance: Pipeline instance to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required methods
            if not hasattr(pipeline_instance, 'execute'):
                logger.error("Pipeline missing required 'execute' method")
                return False
            
            # Check execute method signature
            execute_method = getattr(pipeline_instance, 'execute')
            sig = inspect.signature(execute_method)
            
            # Should have at least one parameter (input_data)
            if len(sig.parameters) < 1:
                logger.error("Pipeline 'execute' method should accept input_data parameter")
                return False
            
            # Check optional methods
            optional_methods = ['get_tasks', 'validate_input', 'get_info']
            for method_name in optional_methods:
                if hasattr(pipeline_instance, method_name):
                    method = getattr(pipeline_instance, method_name)
                    if not callable(method):
                        logger.error(f"Pipeline {method_name} should be callable")
                        return False
            
            # Validate get_tasks if present
            if hasattr(pipeline_instance, 'get_tasks'):
                try:
                    tasks = pipeline_instance.get_tasks()
                    if not isinstance(tasks, list):
                        logger.error("get_tasks should return a list")
                        return False
                    
                    # Check if all tasks are strings (task IDs)
                    for task in tasks:
                        if not isinstance(task, str):
                            logger.error("get_tasks should return list of task ID strings")
                            return False
                            
                except Exception as e:
                    logger.error(f"Error calling get_tasks: {e}")
                    return False
            
            # Validate get_info if present
            if hasattr(pipeline_instance, 'get_info'):
                try:
                    info = pipeline_instance.get_info()
                    if not isinstance(info, dict):
                        logger.error("get_info should return a dictionary")
                        return False
                except Exception as e:
                    logger.error(f"Error calling get_info: {e}")
                    return False
            
            logger.info(f"Pipeline validation passed: {getattr(pipeline_instance, '_pipeline_id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline validation failed: {e}")
            return False
    
    def validate_task_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate task configuration
        
        Args:
            config: Task configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_fields = ['task_id', 'name', 'entry_point']
            
            for field in required_fields:
                if field not in config:
                    logger.error(f"Task config missing required field: {field}")
                    return False
            
            # Validate data types
            if not isinstance(config['task_id'], str):
                logger.error("task_id should be a string")
                return False
            
            if not isinstance(config['name'], str):
                logger.error("name should be a string")
                return False
            
            if not isinstance(config['entry_point'], str):
                logger.error("entry_point should be a string")
                return False
            
            # Validate optional fields
            optional_fields = {
                'description': str,
                'version': str,
                'author': str,
                'requirements': list,
                'tags': list,
                'category': str,
                'timeout': int,
                'priority': int,
                'max_retries': int
            }
            
            for field, expected_type in optional_fields.items():
                if field in config and not isinstance(config[field], expected_type):
                    logger.error(f"{field} should be of type {expected_type.__name__}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Task config validation failed: {e}")
            return False
    
    def validate_pipeline_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate pipeline configuration
        
        Args:
            config: Pipeline configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_fields = ['pipeline_id', 'name', 'tasks']
            
            for field in required_fields:
                if field not in config:
                    logger.error(f"Pipeline config missing required field: {field}")
                    return False
            
            # Validate data types
            if not isinstance(config['pipeline_id'], str):
                logger.error("pipeline_id should be a string")
                return False
            
            if not isinstance(config['name'], str):
                logger.error("name should be a string")
                return False
            
            if not isinstance(config['tasks'], list):
                logger.error("tasks should be a list")
                return False
            
            # Validate tasks list
            for task in config['tasks']:
                if not isinstance(task, str):
                    logger.error("All tasks should be task ID strings")
                    return False
            
            # Validate optional fields
            optional_fields = {
                'description': str,
                'version': str,
                'author': str,
                'tags': list,
                'category': str,
                'parallel': bool,
                'fail_fast': bool,
                'timeout': int,
                'priority': int
            }
            
            for field, expected_type in optional_fields.items():
                if field in config and not isinstance(config[field], expected_type):
                    logger.error(f"{field} should be of type {expected_type.__name__}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline config validation failed: {e}")
            return False
    
    def validate_input_data(self, task_instance: Any, input_data: Any) -> bool:
        """
        Validate input data for task
        
        Args:
            task_instance: Task instance
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if task has custom validation
            if hasattr(task_instance, 'validate_input'):
                return task_instance.validate_input(input_data)
            
            # Basic validation - input should not be None
            if input_data is None:
                logger.error("Input data cannot be None")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            return False
    
    def get_validation_report(self, item_instance: Any, item_type: str = "task") -> Dict[str, Any]:
        """
        Get detailed validation report
        
        Args:
            item_instance: Task or pipeline instance
            item_type: "task" or "pipeline"
            
        Returns:
            Validation report dictionary
        """
        report = {
            "valid": False,
            "item_type": item_type,
            "errors": [],
            "warnings": [],
            "info": {}
        }
        
        try:
            if item_type == "task":
                report["valid"] = self.validate_task(item_instance)
            elif item_type == "pipeline":
                report["valid"] = self.validate_pipeline(item_instance)
            else:
                report["errors"].append(f"Unknown item type: {item_type}")
                return report
            
            # Collect additional info
            if hasattr(item_instance, 'get_info'):
                try:
                    report["info"] = item_instance.get_info()
                except Exception as e:
                    report["warnings"].append(f"Failed to get info: {e}")
            
            # Check for optional methods
            optional_methods = ['get_requirements', 'validate_input']
            for method in optional_methods:
                if hasattr(item_instance, method):
                    report["info"][f"has_{method}"] = True
                else:
                    report["info"][f"has_{method}"] = False
            
        except Exception as e:
            report["errors"].append(str(e))
        
        return report