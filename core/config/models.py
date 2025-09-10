"""
Configuration models using Pydantic for validation
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from pathlib import Path


class MongoDBConfig(BaseModel):
    """MongoDB configuration"""
    host: str = "localhost"
    port: int = 27017
    database: str = "ai_tasks"
    username: Optional[str] = None
    password: Optional[str] = None
    auth_source: str = "admin"
    
    @property
    def connection_string(self) -> str:
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?authSource={self.auth_source}"
        return f"mongodb://{self.host}:{self.port}/{self.database}"


class MinIOConfig(BaseModel):
    """MinIO configuration"""
    endpoint: str = "localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin123"
    bucket: str = "ai-tasks"
    secure: bool = False
    region: Optional[str] = None


class RedisConfig(BaseModel):
    """Redis configuration for Celery"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    
    @property
    def connection_string(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class CeleryConfig(BaseModel):
    """Celery configuration"""
    broker_url: Optional[str] = None
    result_backend: Optional[str] = None
    task_serializer: str = "json"
    accept_content: List[str] = ["json"]
    result_serializer: str = "json"
    timezone: str = "UTC"
    enable_utc: bool = True
    task_routes: Dict[str, Dict[str, str]] = {}
    worker_prefetch_multiplier: int = 1
    task_acks_late: bool = True
    worker_max_tasks_per_child: int = 1000


class TaskConfig(BaseModel):
    """Individual task configuration"""
    task_id: str
    enabled: bool = True
    queue: str = "default"
    priority: int = 5
    max_retries: int = 3
    retry_delay: int = 60
    timeout: int = 300
    memory_limit: Optional[str] = None
    cpu_limit: Optional[float] = None


class PipelineConfig(BaseModel):
    """Pipeline configuration"""
    pipeline_id: str
    enabled: bool = True
    tasks: List[str]
    queue: str = "pipeline"
    priority: int = 5
    parallel: bool = False
    fail_fast: bool = True


class WorkerConfig(BaseModel):
    """Main worker configuration"""
    worker_id: str = Field(default="worker_001")
    worker_name: str = Field(default="AI Worker Node 1")
    
    # Database configs
    mongodb: MongoDBConfig = Field(default_factory=MongoDBConfig)
    minio: MinIOConfig = Field(default_factory=MinIOConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    
    # Celery config
    celery: CeleryConfig = Field(default_factory=CeleryConfig)
    
    # Tasks and pipelines
    active_tasks: List[str] = Field(default_factory=list)
    active_pipelines: List[str] = Field(default_factory=list)
    task_configs: Dict[str, TaskConfig] = Field(default_factory=dict)
    pipeline_configs: Dict[str, PipelineConfig] = Field(default_factory=dict)
    
    # System settings
    task_cache_dir: str = "./task_cache"
    pipeline_cache_dir: str = "./pipeline_cache"
    auto_update: bool = True
    max_concurrent_tasks: int = 5
    health_check_interval: int = 30
    log_level: str = "INFO"
    
    @validator('task_cache_dir', 'pipeline_cache_dir')
    def validate_cache_dirs(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())
    
    def model_post_init(self, __context):
        """Post initialization to setup Celery URLs"""
        if not self.celery.broker_url:
            self.celery.broker_url = self.redis.connection_string
        if not self.celery.result_backend:
            self.celery.result_backend = self.redis.connection_string


class SystemConfig(BaseModel):
    """System-wide configuration"""
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    api_enabled: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Monitoring
    metrics_enabled: bool = True
    prometheus_port: int = 8001
    
    # Security
    api_key: Optional[str] = None
    jwt_secret: Optional[str] = None


class AppConfig(BaseModel):
    """Complete application configuration"""
    worker: WorkerConfig = Field(default_factory=WorkerConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)