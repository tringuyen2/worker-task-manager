#!/usr/bin/env python3
"""
Face Processing Pipeline Demo
Shows how to register tasks, start workers, and execute pipelines
"""
import sys
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from pipeline.registry import pipeline_registry
from worker.task_registry import task_registry
from core.config.manager import get_config


def demo_pipeline_registration():
    """Demo 1: Register and list pipelines"""
    print("\n" + "="*60)
    print("DEMO 1: Pipeline Registration")
    print("="*60)

    # Register built-in pipelines
    pipeline_registry.register_builtin_pipelines()

    # List registered pipelines
    pipelines = pipeline_registry.list_pipelines()
    print(f"\nRegistered Pipelines ({len(pipelines)}):")
    for pipeline_id in pipelines:
        info = pipeline_registry.get_pipeline_info(pipeline_id)
        print(f"  • {pipeline_id}: {info.get('name', 'N/A')}")
        print(f"    Description: {info.get('description', 'N/A')}")
        print(f"    Steps: {info.get('steps', 0)}")
        print()


def demo_task_registration():
    """Demo 2: Register tasks"""
    print("\n" + "="*60)
    print("DEMO 2: Task Registration")
    print("="*60)

    # Load and register tasks
    task_registry.load_and_register_tasks()

    # List registered tasks
    tasks = task_registry.get_registered_tasks()
    print(f"\nRegistered Tasks ({len(tasks)}):")
    for task_id in tasks:
        info = task_registry.get_task_info(task_id)
        if info:
            print(f"  • {task_id}")
            print(f"    Queue: {info.get('queue', 'default')}")
            print(f"    Priority: {info.get('priority', 5)}")
            print(f"    Timeout: {info.get('timeout', 300)}s")
        print()


def demo_pipeline_execution():
    """Demo 3: Execute face processing pipeline"""
    print("\n" + "="*60)
    print("DEMO 3: Pipeline Execution")
    print("="*60)

    # Register components
    pipeline_registry.register_builtin_pipelines()
    task_registry.load_and_register_tasks()

    # Input data
    input_data = {"image_path": "test.jpg"}
    print(f"Input: {input_data}")

    # Execute pipeline
    print("\nExecuting face_processing_pipeline...")
    start_time = time.time()

    result = pipeline_registry.execute_pipeline("face_processing_pipeline", input_data)

    execution_time = time.time() - start_time

    # Show results
    print(f"\nExecution completed in {execution_time:.2f}s")
    print(f"Status: {result.status.value}")

    if result.status.value == "completed":
        faces = result.results.get('faces', [])
        summary = result.results.get('processing_summary', {})

        print(f"\nProcessing Summary:")
        print(f"  • Total faces detected: {summary.get('total_faces_detected', 0)}")
        print(f"  • Faces with attributes: {summary.get('faces_with_attributes', 0)}")
        print(f"  • Faces with features: {summary.get('faces_with_features', 0)}")

        if faces:
            print(f"\nFace Details:")
            for face in faces:
                print(f"  Face {face.get('face_id', 'N/A')}:")
                print(f"    Bbox: {face.get('bbox', 'N/A')}")
                print(f"    Confidence: {face.get('confidence', 'N/A'):.2f}")
                print(f"    Has attributes: {'Yes' if face.get('attributes') else 'No'}")
                print(f"    Has features: {'Yes' if face.get('features') else 'No'}")
                print()
    else:
        print(f"Error: {result.error}")


def demo_worker_commands():
    """Demo 4: Show worker commands"""
    print("\n" + "="*60)
    print("DEMO 4: Celery Worker Commands")
    print("="*60)

    config = get_config().worker

    print("To start individual task workers:")
    print()

    for task_id in config.active_tasks:
        task_config = config.task_configs.get(task_id)
        if task_config:
            queue = getattr(task_config, 'queue', task_id)
            print(f"# Start {task_id} worker:")
            print(f"python -m scripts.start_worker start --task {task_id}")
            print(f"# Or manually with celery:")
            print(f"celery -A worker.celery_app:celery_app worker --loglevel=INFO -Q {queue} -n {task_id}_worker@%h")
            print()

    print("To start all workers:")
    print("python -m scripts.start_worker start")
    print()
    print("To monitor workers:")
    print("python -m scripts.start_worker monitor")
    print()


def demo_pipeline_with_workers():
    """Demo 5: Show how to use with Celery workers (instructions)"""
    print("\n" + "="*60)
    print("DEMO 5: Using with Celery Workers")
    print("="*60)

    print("To use this system with Celery workers:")
    print()
    print("1. Start Redis (required for Celery broker):")
    print("   Make sure your Redis instance is running (configured in config.json)")
    print()
    print("2. Start workers for each task:")
    print("   python -m scripts.start_worker start")
    print()
    print("3. Execute pipeline with workers:")
    print('   python -m tools.pipeline_cli_registry execute face_processing_pipeline \'{"image_path": "test.jpg"}\' --workers')
    print()
    print("4. Monitor worker status:")
    print("   python -m scripts.start_worker status")
    print()


def main():
    """Run all demos"""
    print("Face Processing Pipeline System Demo")
    print("====================================")

    try:
        # Configure logging
        logger.remove()
        logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

        # Run demos
        demo_pipeline_registration()
        demo_task_registration()
        demo_pipeline_execution()
        demo_worker_commands()
        demo_pipeline_with_workers()

        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print()
        print("The system is now ready to use. You have:")
        print("✓ Custom pipeline registration system")
        print("✓ Task-specific Celery workers")
        print("✓ Face processing pipeline with parallel execution")
        print("✓ CLI tools for pipeline management")
        print()
        print("Next steps:")
        print("1. Start Celery workers with: python -m scripts.start_worker start")
        print("2. Execute pipelines with: python -m tools.pipeline_cli_registry execute")
        print()

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()