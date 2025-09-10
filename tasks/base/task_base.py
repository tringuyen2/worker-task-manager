"""
Base class for all AI tasks
"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional
from loguru import logger


class TaskBase(ABC):
    """Abstract base class for all AI tasks"""
    
    def __init__(self):
        self._task_id: Optional[str] = None
        self._config: Dict[str, Any] = {}
        self._metadata: Optional[Any] = None
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """
        Process input data and return result
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processed result
        """
        pass
    
    def get_requirements(self) -> List[str]:
        """
        Get list of required Python packages
        
        Returns:
            List of package names with versions
        """
        return []
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data before processing
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get task information
        
        Returns:
            Dictionary with task information
        """
        return {
            "task_id": self._task_id,
            "name": self.__class__.__name__,
            "description": self.__doc__ or "",
            "config": self._config
        }
    
    def setup(self):
        """
        Setup method called before first execution
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
        """Log info message with task context"""
        logger.info(f"[{self._task_id}] {message}")
    
    def log_warning(self, message: str):
        """Log warning message with task context"""
        logger.warning(f"[{self._task_id}] {message}")
    
    def log_error(self, message: str):
        """Log error message with task context"""
        logger.error(f"[{self._task_id}] {message}")
    
    @property
    def task_id(self) -> Optional[str]:
        """Get task ID"""
        return self._task_id
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get task configuration"""
        return self._config
    
    @property
    def metadata(self) -> Optional[Any]:
        """Get task metadata"""
        return self._metadata


class SimpleTask(TaskBase):
    """
    Simple task base class for basic AI tasks
    Provides common functionality and error handling
    """
    
    def __init__(self):
        super().__init__()
        self._is_setup = False
    
    def process(self, input_data: Any) -> Any:
        """
        Process with automatic setup/cleanup and error handling
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processed result
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
            self.log_info(f"Starting processing with input type: {type(input_data).__name__}")
            
            # Call actual processing method
            result = self._process_impl(input_data)
            
            # Log completion
            self.log_info(f"Processing completed, result type: {type(result).__name__}")
            
            return result
            
        except Exception as e:
            self.log_error(f"Processing failed: {e}")
            raise
        finally:
            # Cleanup
            try:
                self.cleanup()
            except Exception as e:
                self.log_warning(f"Cleanup failed: {e}")
    
    @abstractmethod
    def _process_impl(self, input_data: Any) -> Any:
        """
        Actual processing implementation
        Override this method in subclasses
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processed result
        """
        pass


class MLTask(SimpleTask):
    """
    Base class for Machine Learning tasks
    Provides common ML functionality
    """
    
    def __init__(self):
        super().__init__()
        self._model = None
        self._is_model_loaded = False
    
    def setup(self):
        """Setup ML model"""
        try:
            self.log_info("Loading ML model...")
            self._model = self.load_model()
            self._is_model_loaded = True
            self.log_info("ML model loaded successfully")
        except Exception as e:
            self.log_error(f"Failed to load ML model: {e}")
            raise
    
    def cleanup(self):
        """Cleanup ML model"""
        try:
            if self._model is not None:
                self.unload_model()
                self._model = None
                self._is_model_loaded = False
                self.log_info("ML model unloaded")
        except Exception as e:
            self.log_warning(f"Failed to unload ML model: {e}")
    
    def load_model(self):
        """
        Load ML model
        Override in subclasses
        
        Returns:
            Loaded model
        """
        return None
    
    def unload_model(self):
        """
        Unload ML model
        Override in subclasses if needed
        """
        pass
    
    def preprocess_input(self, input_data: Any) -> Any:
        """
        Preprocess input data
        Override in subclasses
        
        Args:
            input_data: Raw input data
            
        Returns:
            Preprocessed data
        """
        return input_data
    
    def postprocess_output(self, output_data: Any) -> Any:
        """
        Postprocess output data
        Override in subclasses
        
        Args:
            output_data: Raw model output
            
        Returns:
            Postprocessed result
        """
        return output_data
    
    def _process_impl(self, input_data: Any) -> Any:
        """
        ML task processing implementation
        
        Args:
            input_data: Input data
            
        Returns:
            Processed result
        """
        if not self._is_model_loaded:
            raise RuntimeError("Model not loaded")
        
        # Preprocess input
        preprocessed_input = self.preprocess_input(input_data)
        
        # Run inference
        raw_output = self.predict(preprocessed_input)
        
        # Postprocess output
        result = self.postprocess_output(raw_output)
        
        return result
    
    @abstractmethod
    def predict(self, preprocessed_input: Any) -> Any:
        """
        Run model prediction
        Override in subclasses
        
        Args:
            preprocessed_input: Preprocessed input data
            
        Returns:
            Raw model output
        """
        pass
    
    @property
    def model(self):
        """Get loaded model"""
        return self._model
    
    @property
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._is_model_loaded