"""
Database models for MongoDB collections
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskType(str, Enum):
    """Task type"""
    SINGLE = "single"
    PIPELINE = "pipeline"


class TaskMetadata(BaseModel):
    """Task metadata stored in MongoDB"""
    task_id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Human readable name")
    description: str = Field(default="", description="Task description")
    version: str = Field(default="1.0.0", description="Task version")
    author: str = Field(default="", description="Task author")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Task specifications
    task_type: TaskType = TaskType.SINGLE
    entry_point: str = Field(..., description="Entry point module.class")
    requirements: List[str] = Field(default_factory=list)
    
    # MinIO storage info
    storage_path: str = Field(..., description="MinIO storage path")
    file_hash: str = Field(..., description="File hash for integrity")
    file_size: int = Field(..., description="File size in bytes")
    
    # Runtime info
    queue: str = Field(default="default", description="Celery queue name")
    priority: int = Field(default=5, description="Task priority 1-10")
    timeout: int = Field(default=300, description="Task timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    # Status
    is_active: bool = Field(default=True, description="Is task active")
    is_deprecated: bool = Field(default=False, description="Is task deprecated")
    
    # Tags and categories
    tags: List[str] = Field(default_factory=list)
    category: str = Field(default="general", description="Task category")


class PipelineMetadata(BaseModel):
    """Pipeline metadata stored in MongoDB"""
    pipeline_id: str = Field(..., description="Unique pipeline identifier")
    name: str = Field(..., description="Human readable name")
    description: str = Field(default="", description="Pipeline description")
    version: str = Field(default="1.0.0", description="Pipeline version")
    author: str = Field(default="", description="Pipeline author")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Pipeline specifications
    tasks: List[str] = Field(..., description="List of task IDs in order")
    parallel: bool = Field(default=False, description="Run tasks in parallel")
    fail_fast: bool = Field(default=True, description="Stop on first failure")
    
    # MinIO storage info
    storage_path: str = Field(..., description="MinIO storage path")
    file_hash: str = Field(..., description="File hash for integrity")
    file_size: int = Field(..., description="File size in bytes")
    
    # Runtime info
    queue: str = Field(default="pipeline", description="Celery queue name")
    priority: int = Field(default=5, description="Pipeline priority 1-10")
    timeout: int = Field(default=600, description="Pipeline timeout in seconds")
    
    # Status
    is_active: bool = Field(default=True, description="Is pipeline active")
    is_deprecated: bool = Field(default=False, description="Is pipeline deprecated")
    
    # Tags and categories
    tags: List[str] = Field(default_factory=list)
    category: str = Field(default="general", description="Pipeline category")


class ExecutionRecord(BaseModel):
    """Task/Pipeline execution record"""
    execution_id: str = Field(..., description="Unique execution ID")
    celery_task_id: str = Field(..., description="Celery task ID")
    
    # Task info
    task_id: Optional[str] = Field(None, description="Task ID if single task")
    pipeline_id: Optional[str] = Field(None, description="Pipeline ID if pipeline")
    task_type: TaskType = Field(..., description="Execution type")
    
    # Worker info
    worker_id: str = Field(..., description="Worker that executed the task")
    worker_hostname: str = Field(..., description="Worker hostname")
    queue: str = Field(..., description="Queue name")
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Execution details
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # Resource usage
    memory_usage: Optional[float] = None
    cpu_time: Optional[float] = None
    
    # Retry info
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkerStatus(BaseModel):
    """Worker status record"""
    worker_id: str = Field(..., description="Unique worker identifier")
    hostname: str = Field(..., description="Worker hostname")
    
    # Status
    is_active: bool = Field(default=True)
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    
    # Capabilities
    active_tasks: List[str] = Field(default_factory=list)
    active_pipelines: List[str] = Field(default_factory=list)
    queues: List[str] = Field(default_factory=list)
    
    # Resource info
    max_concurrent_tasks: int = Field(default=5)
    current_task_count: int = Field(default=0)
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    
    # Version info
    version: str = Field(default="1.0.0")
    python_version: str = Field(default="")
    celery_version: str = Field(default="")
    
    # Configuration
    config_version: str = Field(default="")
    config_hash: str = Field(default="")
    
    # Statistics
    total_tasks_executed: int = Field(default=0)
    successful_tasks: int = Field(default=0)
    failed_tasks: int = Field(default=0)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)