#!/usr/bin/env python3
"""
Demo Task Registration without MinIO
Shows how to register and work with tasks locally without full infrastructure.
"""

import json
import os
import sys
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def show_task_registration_steps():
    """Show the complete task registration workflow."""
    print_section("TASK REGISTRATION WORKFLOW")

    print("🔧 Complete Registration Steps:")
    print()

    print("1. Prerequisites:")
    print("   ✅ Docker services running (MongoDB, Redis, MinIO)")
    print("   ✅ Dependencies installed (opencv-python, celery, redis)")
    print("   ✅ Virtual environment activated")
    print()

    print("2. Task Directory Structure:")
    print("   tasks/examples/face_detection/")
    print("   ├── task.py          # Task implementation")
    print("   ├── task.json        # Task metadata")
    print("   └── requirements.txt # Dependencies")
    print()

    print("3. Registration Commands:")
    print("   # Register from task directory (not JSON file)")
    print("   ./venv/bin/python -m tools.task_manager register tasks/examples/face_detection")
    print("   ./venv/bin/python -m tools.task_manager register tasks/examples/face_attribute")
    print("   ./venv/bin/python -m tools.task_manager register tasks/examples/face_extractor")
    print()

    print("4. Verification Commands:")
    print("   ./venv/bin/python -m tools.task_manager list")
    print("   ./venv/bin/python -m tools.task_manager info face_detection")

def show_current_status():
    """Show current system status."""
    print_section("CURRENT SYSTEM STATUS")

    # Check task directories
    task_dirs = [
        "tasks/examples/face_detection",
        "tasks/examples/face_attribute",
        "tasks/examples/face_extractor"
    ]

    print("📁 Available Task Directories:")
    for task_dir in task_dirs:
        if os.path.exists(task_dir):
            task_py = os.path.exists(f"{task_dir}/task.py")
            task_json = os.path.exists(f"{task_dir}/task.json")
            print(f"   ✅ {task_dir}")
            print(f"      task.py: {'✅' if task_py else '❌'}")
            print(f"      task.json: {'✅' if task_json else '❌'}")

            if task_json:
                with open(f"{task_dir}/task.json", 'r') as f:
                    config = json.load(f)
                print(f"      Task ID: {config.get('task_id', 'N/A')}")
                print(f"      Queue: {config.get('queue', 'N/A')}")
        else:
            print(f"   ❌ {task_dir} (not found)")
        print()

    # Check services
    print("🔧 Service Status:")
    services = [
        ("MongoDB", "localhost:27017"),
        ("MinIO", "localhost:9000"),
        ("Redis", "localhost:6379")
    ]

    for service_name, endpoint in services:
        # This is just for display - actual checking would require more setup
        print(f"   📡 {service_name}: {endpoint}")

def show_troubleshooting():
    """Show common troubleshooting steps."""
    print_section("TROUBLESHOOTING REGISTRATION ISSUES")

    print("❌ Common Issues and Solutions:")
    print()

    print("1. 'No module named cv2' Error:")
    print("   Solution: ./venv/bin/pip install opencv-python numpy")
    print()

    print("2. 'No module named celery' Error:")
    print("   Solution: ./venv/bin/pip install celery redis")
    print()

    print("3. MinIO Connection Error:")
    print("   - Check: docker compose ps")
    print("   - Restart: docker compose restart minio")
    print("   - Config: Check config.json MinIO settings")
    print()

    print("4. Task Validation Failed:")
    print("   - Check: task.py has proper Task class")
    print("   - Check: task.json has valid JSON format")
    print("   - Check: requirements.txt dependencies installed")
    print()

    print("5. 'Task folder not found' Error:")
    print("   - Use directory path: tasks/examples/face_detection")
    print("   - NOT JSON file: demo_face_detection_task.json")
    print()

def show_alternative_workflow():
    """Show alternative workflow without full registration."""
    print_section("ALTERNATIVE: DIRECT TASK EXECUTION")

    print("🚀 If registration fails, you can test tasks directly:")
    print()

    print("1. Test Individual Tasks:")
    print("   ./venv/bin/python -m tools.task_manager test face_detection '\"test.jpg\"'")
    print("   ./venv/bin/python -m tools.task_manager test simple_face_detector '\"test.jpg\"'")
    print()

    print("2. Use Working Demo Scripts:")
    print("   python demo_face_processing.py")
    print("   python simple_registration_demo.py")
    print("   python json_pipeline_demo.py")
    print()

    print("3. Test Pipeline Configurations:")
    print("   python demo_step_by_step.py  # Shows complete workflow")
    print("   python get_info.py          # Shows current configurations")

def show_minio_fix():
    """Show how to fix MinIO issues."""
    print_section("FIXING MINIO AUTHENTICATION")

    print("🔧 MinIO Authentication Fix:")
    print()

    print("1. Check MinIO container logs:")
    print("   docker compose logs minio")
    print()

    print("2. Reset MinIO credentials:")
    print("   docker compose down")
    print("   docker volume rm worker-task-manager_minio_data")
    print("   docker compose up -d")
    print()

    print("3. Update config.json if needed:")
    print("   {")
    print('     "minio": {')
    print('       "endpoint": "localhost:9000",')
    print('       "access_key": "minioadmin",')
    print('       "secret_key": "minioadmin123",')  # Updated default
    print('       "bucket": "ai-tasks",')
    print('       "secure": false')
    print("     }")
    print("   }")

def main():
    """Main demo function."""
    print("📋 TASK REGISTRATION GUIDE")
    print("How to register tasks in the Worker Task Manager system")

    show_current_status()
    show_task_registration_steps()
    show_troubleshooting()
    show_minio_fix()
    show_alternative_workflow()

    print_section("SUMMARY")
    print("✅ Task registration requires:")
    print("   1. Task directory with task.py and task.json")
    print("   2. All dependencies installed")
    print("   3. Services running (MongoDB, MinIO, Redis)")
    print("   4. Proper MinIO authentication")
    print()
    print("🎯 Quick Start (if services working):")
    print("   ./venv/bin/python -m tools.task_manager register tasks/examples/face_detection")
    print("   ./venv/bin/python -m tools.task_manager list")
    print()
    print("🚀 Alternative (if registration fails):")
    print("   python demo_step_by_step.py")

if __name__ == "__main__":
    main()