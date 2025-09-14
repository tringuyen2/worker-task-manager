#!/usr/bin/env python3
"""
Direct script to upload fixed tasks without Rich console issues
"""
import json
from pathlib import Path
from core.config.manager import config_manager
from core.database.operations import db_ops
from core.database.models import TaskMetadata, TaskType
from core.storage.operations import storage_ops
from core.task_loader.validator import TaskValidator

def upload_task(task_folder: str, task_id: str = None):
    """Upload a task to storage"""
    try:
        task_path = Path(task_folder)
        if not task_path.exists():
            print(f"ERROR: Task folder not found: {task_folder}")
            return False

        # Load task configuration
        config_file = task_path / "task.json"
        if not config_file.exists():
            print(f"ERROR: Task configuration not found: {config_file}")
            return False

        with open(config_file, 'r') as f:
            task_config = json.load(f)

        # Override task ID if provided
        if task_id:
            task_config['task_id'] = task_id

        print(f"Uploading task: {task_config['task_id']}")
        print(f"Task name: {task_config['name']}")
        print(f"Version: {task_config['version']}")

        # Validate task
        validator = TaskValidator()
        if not validator.validate_task_config(task_config):
            print("ERROR: Task configuration validation failed")
            return False

        print("SUCCESS: Task configuration validation passed")

        # Upload task package
        print("Uploading task package...")
        storage_info = storage_ops.upload_task_package(task_config['task_id'], str(task_path))

        if not storage_info:
            print("ERROR: Failed to upload task package")
            return False

        print(f"SUCCESS: Task package uploaded: {storage_info['storage_path']}")

        # Create task metadata
        task_metadata = TaskMetadata(
            task_id=task_config['task_id'],
            name=task_config['name'],
            description=task_config.get('description', ''),
            version=task_config.get('version', '1.0.0'),
            author=task_config.get('author', ''),
            task_type=TaskType.SINGLE,
            entry_point=task_config['entry_point'],
            requirements=task_config.get('requirements', []),
            storage_path=storage_info['storage_path'],
            file_hash=storage_info['file_hash'],
            file_size=storage_info['file_size'],
            tags=task_config.get('tags', []),
            category=task_config.get('category', 'general')
        )

        # Save to database
        if db_ops.create_task_metadata(task_metadata):
            print(f"SUCCESS: Task registered in database: {task_config['task_id']}")

            # Update worker configuration
            from core.config.models import TaskConfig

            worker_task_config = TaskConfig(
                task_id=task_config['task_id'],
                queue=task_config.get('queue', 'default'),
                priority=task_config.get('priority', 5),
                timeout=task_config.get('timeout', 300)
            )

            config_manager.update_task_config(task_config['task_id'], worker_task_config)
            print("SUCCESS: Worker configuration updated")
            return True

        else:
            print("ERROR: Failed to save task metadata to database")
            return False

    except Exception as e:
        print(f"ERROR: Failed to upload task: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Upload both fixed tasks"""
    print("=== UPLOADING FIXED TASKS TO STORAGE ===")

    # Set config path
    config_manager.config_path = Path('config.json')

    tasks_to_upload = [
        ("tasks/examples/face_attribute_fixed", "face_attribute"),
        ("tasks/examples/face_extractor_fixed", "face_extractor")
    ]

    results = []
    for task_folder, task_id in tasks_to_upload:
        print(f"\n--- Uploading {task_id} ---")
        success = upload_task(task_folder, task_id)
        results.append((task_id, success))

        if success:
            print(f"SUCCESS: Successfully uploaded {task_id}")
        else:
            print(f"FAILED: Failed to upload {task_id}")

    print(f"\n=== UPLOAD SUMMARY ===")
    for task_id, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"{task_id}: {status}")

    all_success = all(success for _, success in results)
    if all_success:
        print("\nSUCCESS: All tasks uploaded successfully!")
        print("\nNow you can run the pipeline and both parallel tasks should work correctly.")
    else:
        print("\nFAILED: Some tasks failed to upload.")

if __name__ == "__main__":
    main()