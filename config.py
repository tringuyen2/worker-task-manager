import os
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

class TaskConfig(BaseModel):
    """Configuration cho một AI task"""
    task_id: str = Field(..., description="Unique task identifier")
    task_name: str = Field(..., description="Human readable task name")
    description: str = Field(..., description="Task description")
    version: str = Field(default="1.0.0", description="Task version")
    zip_file: str = Field(..., description="Zip file name in MinIO")
    entry_point: str = Field(default="task.py", description="Main task file")
    requirements: List[str] = Field(default=[], description="Python dependencies")
    enabled: bool = Field(default=True, description="Task enabled status")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class WorkerConfig(BaseModel):
    """Configuration cho AI Worker"""
    worker_id: str = Field(..., description="Unique worker identifier")
    worker_name: str = Field(..., description="Worker name")
    active_tasks: List[str] = Field(default=[], description="List of active task IDs")
    mongodb: Dict[str, str] = Field(..., description="MongoDB connection config")
    minio: Dict[str, str] = Field(..., description="MinIO connection config")
    task_cache_dir: str = Field(default="./task_cache", description="Local cache directory")
    auto_update: bool = Field(default=True, description="Auto update tasks from DB")
    max_concurrent_tasks: int = Field(default=5, description="Max concurrent tasks")

class TaskExecutionResult(BaseModel):
    """Kết quả thực thi task"""
    task_id: str
    execution_id: str
    input_data: Any
    output_data: Any
    status: str  # "success", "error", "running"
    error_message: Optional[str] = None
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.now)

# Default config template
DEFAULT_WORKER_CONFIG = {
    "worker_id": "worker_001",
    "worker_name": "AI Worker Node 1",
    "active_tasks": [
        "face_detection",
        "text_sentiment"
    ],
    "mongodb": {
        "host": "localhost",
        "port": "27017",
        "database": "ai_tasks",
        "username": "",
        "password": ""
    },
    "minio": {
        "endpoint": "localhost:9000",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "bucket": "ai-tasks",
        "secure": False
    },
    "task_cache_dir": "./task_cache",
    "auto_update": True,
    "max_concurrent_tasks": 5
}

def create_default_config(config_path: str = "config.json"):
    """Tạo config mặc định"""
    with open(config_path, 'w') as f:
        json.dump(DEFAULT_WORKER_CONFIG, f, indent=2, default=str)
    print(f"✅ Created default config: {config_path}")

def load_config(config_path: str = "config.json") -> WorkerConfig:
    """Load config từ file"""
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        print("Creating default config...")
        create_default_config(config_path)
    
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    return WorkerConfig(**config_data)