"""
Pipeline Models and Base Classes
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PipelineStage(Enum):
    """Pipeline execution stages"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskStep:
    """Individual task step in pipeline"""
    task_id: str
    input_data: Any
    depends_on: Optional[List[str]] = None
    parallel_group: Optional[str] = None
    timeout: Optional[int] = None
    retry_count: int = 3


@dataclass
class PipelineResult:
    """Pipeline execution result"""
    pipeline_id: str
    execution_id: str
    status: PipelineStage
    results: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None


class BasePipeline(ABC):
    """Base class for all pipelines"""

    def __init__(self, pipeline_id: str, name: str, description: str = ""):
        self.pipeline_id = pipeline_id
        self.name = name
        self.description = description
        self.steps: List[TaskStep] = []
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    def define_steps(self) -> List[TaskStep]:
        """Define the pipeline steps"""
        pass

    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """Validate pipeline input"""
        pass

    @abstractmethod
    def process_results(self, step_results: Dict[str, Any]) -> Any:
        """Process and aggregate step results"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get pipeline information"""
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "description": self.description,
            "steps": len(self.steps),
            "metadata": self.metadata
        }


class CustomPipeline(BasePipeline):
    """Custom pipeline implementation"""

    def __init__(self, pipeline_id: str, name: str, description: str = "",
                 step_definitions: Optional[List[TaskStep]] = None,
                 input_validator: Optional[callable] = None,
                 result_processor: Optional[callable] = None):
        super().__init__(pipeline_id, name, description)
        self.step_definitions = step_definitions or []
        self.input_validator = input_validator
        self.result_processor = result_processor

    def define_steps(self) -> List[TaskStep]:
        """Define the pipeline steps"""
        return self.step_definitions

    def validate_input(self, input_data: Any) -> bool:
        """Validate pipeline input"""
        if self.input_validator:
            return self.input_validator(input_data)
        return True

    def process_results(self, step_results: Dict[str, Any]) -> Any:
        """Process and aggregate step results"""
        if self.result_processor:
            return self.result_processor(step_results)
        return step_results