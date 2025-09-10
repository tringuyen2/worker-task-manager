"""
Celery application configuration and setup
"""
from celery import Celery
from celery.signals import worker_ready, worker_shutdown, task_prerun, task_postrun, task_failure
from kombu import Queue, Exchange
from loguru import logger

from ..core.config.manager import get_config
from ..core.database.connection import init_database
from ..core.storage.connection import init_storage


def create_celery_app() -> Celery:
    """Create and configure Celery application"""
    
    config = get_config()
    celery_config = config.worker.celery
    
    # Create Celery app
    app = Celery('ai_worker')
    
    # Update configuration
    app.conf.update(
        broker_url=celery_config.broker_url,
        result_backend=celery_config.result_backend,
        task_serializer=celery_config.task_serializer,
        accept_content=celery_config.accept_content,
        result_serializer=celery_config.result_serializer,
        timezone=celery_config.timezone,
        enable_utc=celery_config.enable_utc,
        worker_prefetch_multiplier=celery_config.worker_prefetch_multiplier,
        task_acks_late=celery_config.task_acks_late,
        worker_max_tasks_per_child=celery_config.worker_max_tasks_per_child,
        
        # Task routing
        task_routes=celery_config.task_routes,
        
        # Queue configuration
        task_default_queue='default',
        task_default_exchange='default',
        task_default_exchange_type='direct',
        task_default_routing_key='default',
        
        # Worker configuration
        worker_disable_rate_limits=True,
        worker_pool_restarts=True,
        
        # Task execution
        task_always_eager=False,
        task_eager_propagates=True,
        task_ignore_result=False,
        task_store_eager_result=True,
        
        # Error handling
        task_reject_on_worker_lost=True,
        task_acks_on_failure_or_timeout=True,
        
        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
        
        # Security
        worker_hijack_root_logger=False,
        worker_log_color=False,
    )
    
    # Define queues
    app.conf.task_queues = (
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('vision', Exchange('vision'), routing_key='vision'),
        Queue('nlp', Exchange('nlp'), routing_key='nlp'),
        Queue('pipeline', Exchange('pipeline'), routing_key='pipeline'),
        Queue('high_priority', Exchange('high_priority'), routing_key='high_priority'),
        Queue('low_priority', Exchange('low_priority'), routing_key='low_priority'),
    )
    
    return app


# Create global Celery app
celery_app = create_celery_app()


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready signal"""
    logger.info(f"Worker {sender} is ready")
    
    # Initialize connections
    if not init_database():
        logger.error("Failed to initialize database connection")
    
    if not init_storage():
        logger.error("Failed to initialize storage connection")
    
    # Load and register tasks
    from .task_registry import task_registry
    task_registry.load_and_register_tasks()
    
    # Register worker status
    from .worker_manager import worker_manager
    worker_manager.register_worker()


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Handle worker shutdown signal"""
    logger.info(f"Worker {sender} is shutting down")
    
    # Unregister worker
    from .worker_manager import worker_manager
    worker_manager.unregister_worker()


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Handle task prerun signal"""
    from datetime import datetime
    from ..core.database.operations import db_ops
    from ..core.database.models import ExecutionRecord, TaskStatus
    
    logger.info(f"Task starting: {task.name} [{task_id}]")
    
    # Create execution record
    try:
        execution_record = ExecutionRecord(
            execution_id=task_id,
            celery_task_id=task_id,
            task_id=task.name,
            worker_id=get_config().worker.worker_id,
            worker_hostname=sender.hostname if sender else "unknown",
            queue=task.request.delivery_info.get('routing_key', 'default') if hasattr(task, 'request') else 'default',
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow(),
            input_data={"args": args, "kwargs": kwargs}
        )
        
        db_ops.create_execution_record(execution_record)
        
    except Exception as e:
        logger.error(f"Failed to create execution record: {e}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kw):
    """Handle task postrun signal"""
    from datetime import datetime
    from ..core.database.operations import db_ops
    from ..core.database.models import TaskStatus
    
    logger.info(f"Task completed: {task.name} [{task_id}] - {state}")
    
    # Update execution record
    try:
        updates = {
            "status": TaskStatus.SUCCESS if state == "SUCCESS" else TaskStatus.FAILED,
            "completed_at": datetime.utcnow(),
            "output_data": retval if state == "SUCCESS" else None
        }
        
        # Calculate duration
        execution_record = db_ops.get_execution_record(task_id)
        if execution_record and execution_record.started_at:
            duration = (datetime.utcnow() - execution_record.started_at).total_seconds()
            updates["duration"] = duration
        
        db_ops.update_execution_record(task_id, updates)
        
    except Exception as e:
        logger.error(f"Failed to update execution record: {e}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kw):
    """Handle task failure signal"""
    from datetime import datetime
    from ..core.database.operations import db_ops
    from ..core.database.models import TaskStatus
    
    logger.error(f"Task failed: {sender.name} [{task_id}] - {exception}")
    
    # Update execution record with error
    try:
        updates = {
            "status": TaskStatus.FAILED,
            "completed_at": datetime.utcnow(),
            "error_message": str(exception),
            "error_traceback": str(traceback) if traceback else None
        }
        
        # Calculate duration
        execution_record = db_ops.get_execution_record(task_id)
        if execution_record and execution_record.started_at:
            duration = (datetime.utcnow() - execution_record.started_at).total_seconds()
            updates["duration"] = duration
        
        db_ops.update_execution_record(task_id, updates)
        
    except Exception as e:
        logger.error(f"Failed to update execution record on failure: {e}")


# Task decorator with default configuration
def ai_task(name=None, queue='default', priority=5, max_retries=3, timeout=300, **kwargs):
    """
    Decorator for AI tasks with default configuration
    
    Args:
        name: Task name
        queue: Queue name
        priority: Task priority
        max_retries: Maximum retry attempts
        timeout: Task timeout in seconds
        **kwargs: Additional Celery task options
    """
    def decorator(func):
        task_kwargs = {
            'name': name or func.__name__,
            'queue': queue,
            'priority': priority,
            'max_retries': max_retries,
            'soft_time_limit': timeout,
            'time_limit': timeout + 30,
            **kwargs
        }
        return celery_app.task(**task_kwargs)(func)
    
    return decorator


# Export for easy import
__all__ = ['celery_app', 'ai_task']