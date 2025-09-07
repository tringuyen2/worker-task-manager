# task_register.py - Tool để đăng ký tasks vào hệ thống
import os
import sys
import argparse
import json
import zipfile
from typing import List, Dict, Any
from datetime import datetime

from config import load_config, TaskConfig
from database import DatabaseManager
from storage import StorageManager

def create_task_zip(task_folder: str, output_zip: str, exclude_files: List[str] = None) -> bool:
    """Tạo zip file từ task folder"""
    if exclude_files is None:
        exclude_files = ['.git', '__pycache__', '.pytest_cache', '.DS_Store', '*.pyc', '.env']
    
    try:
        if not os.path.exists(task_folder):
            print(f"❌ Task folder not found: {task_folder}")
            return False
        
        print(f"📦 Creating zip file: {output_zip}")
        
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(task_folder):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if not any(d.startswith(exc.replace('*', '')) for exc in exclude_files)]
                
                for file in files:
                    # Skip excluded files
                    if any(file.endswith(exc.replace('*', '')) or file == exc for exc in exclude_files):
                        continue
                    
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, task_folder)
                    zipf.write(file_path, arcname)
                    print(f"  ✅ Added: {arcname}")
        
        print(f"✅ Zip file created successfully: {output_zip}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create zip file: {e}")
        return False

def detect_task_info(task_folder: str) -> Dict[str, Any]:
    """Tự động detect thông tin task từ folder"""
    info = {
        "task_id": os.path.basename(task_folder),
        "task_name": os.path.basename(task_folder).replace('_', ' ').title(),
        "description": f"AI Task: {os.path.basename(task_folder)}",
        "entry_point": "task.py",
        "requirements": []
    }
    
    # Detect entry point
    possible_entry_points = ["task.py", "main.py", "run.py", "app.py"]
    for entry in possible_entry_points:
        if os.path.exists(os.path.join(task_folder, entry)):
            info["entry_point"] = entry
            break
    
    # Read requirements from requirements.txt
    req_file = os.path.join(task_folder, "requirements.txt")
    if os.path.exists(req_file):
        try:
            with open(req_file, 'r') as f:
                requirements = [line.strip() for line in f.readlines() 
                              if line.strip() and not line.startswith('#')]
                info["requirements"] = requirements
        except Exception as e:
            print(f"⚠️ Warning: Could not read requirements.txt: {e}")
    
    # Read metadata from task.json if exists
    metadata_file = os.path.join(task_folder, "task.json")
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                info.update(metadata)
        except Exception as e:
            print(f"⚠️ Warning: Could not read task.json: {e}")
    
    return info

def register_task(config_path: str, task_folder: str, task_info: Dict[str, Any] = None) -> bool:
    """Đăng ký task vào hệ thống"""
    try:
        # Load config
        config = load_config(config_path)
        
        # Auto-detect task info if not provided
        if not task_info:
            task_info = detect_task_info(task_folder)
        
        print(f"📝 Task Information:")
        print(f"   Task ID: {task_info['task_id']}")
        print(f"   Task Name: {task_info['task_name']}")
        print(f"   Description: {task_info['description']}")
        print(f"   Entry Point: {task_info['entry_point']}")
        print(f"   Requirements: {task_info['requirements']}")
        
        # Create zip file
        zip_filename = f"{task_info['task_id']}.zip"
        temp_zip_path = os.path.join("/tmp", zip_filename)
        
        if not create_task_zip(task_folder, temp_zip_path):
            return False
        
        # Initialize managers
        db_manager = DatabaseManager(config)
        storage_manager = StorageManager(config)
        
        if not db_manager.connect():
            print("❌ Failed to connect to database")
            return False
        
        if not storage_manager.connect():
            print("❌ Failed to connect to storage")
            return False
        
        # Upload to MinIO
        print(f"☁️ Uploading to storage...")
        if not storage_manager.upload_task_zip(task_info['task_id'], temp_zip_path):
            print("❌ Failed to upload task zip")
            return False
        
        # Create task config
        task_config = TaskConfig(
            task_id=task_info['task_id'],
            task_name=task_info['task_name'],
            description=task_info['description'],
            version=task_info.get('version', '1.0.0'),
            zip_file=zip_filename,
            entry_point=task_info['entry_point'],
            requirements=task_info['requirements'],
            metadata=task_info.get('metadata', {})
        )
        
        # Register in database
        print(f"💾 Registering in database...")
        if not db_manager.register_task(task_config):
            print("❌ Failed to register task in database")
            return False
        
        # Cleanup temp file
        os.remove(temp_zip_path)
        
        print(f"✅ Task registered successfully: {task_info['task_id']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to register task: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_registered_tasks(config_path: str):
    """List tất cả tasks đã đăng ký"""
    try:
        config = load_config(config_path)
        db_manager = DatabaseManager(config)
        
        if not db_manager.connect():
            print("❌ Failed to connect to database")
            return
        
        tasks = db_manager.list_all_tasks()
        
        if not tasks:
            print("📋 No tasks found in database")
            return
        
        print(f"📋 Registered Tasks ({len(tasks)} total):")
        print("-" * 80)
        
        for task in tasks:
            status = "🟢 Enabled" if task.enabled else "🔴 Disabled"
            print(f"ID: {task.task_id}")
            print(f"Name: {task.task_name}")
            print(f"Description: {task.description}")
            print(f"Version: {task.version}")
            print(f"Status: {status}")
            print(f"Created: {task.created_at}")
            print(f"Requirements: {', '.join(task.requirements) if task.requirements else 'None'}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Failed to list tasks: {e}")

def create_task_template(task_id: str, task_folder: str):
    """Tạo template cho task mới"""
    try:
        os.makedirs(task_folder, exist_ok=True)
        
        # Create task.py template
        task_py_content = f'''# {task_id} - AI Task Implementation
from abc import ABC, abstractmethod
from typing import List, Any
import logging

logger = logging.getLogger(__name__)

class BaseTask(ABC):
    """Base class cho tất cả AI tasks"""
    
    def __init__(self):
        self.task_name = self.__class__.__name__
        
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Xử lý input và trả về kết quả"""
        pass
    
    @abstractmethod
    def get_requirements(self) -> List[str]:
        """Trả về list các thư viện cần thiết"""
        pass
    
    def get_description(self) -> str:
        """Mô tả task"""
        return f"AI Task: {{self.task_name}}"

class {task_id.replace('_', '').title()}Task(BaseTask):
    """Implementation cho {task_id} task"""
    
    def __init__(self):
        super().__init__()
        logger.info(f"{{self.task_name}} initialized")
    
    def process(self, input_data: Any) -> Any:
        """
        Process input data
        Args:
            input_data: Input data to process
        Returns:
            Processed result
        """
        try:
            logger.info(f"Processing {{self.task_name}} with input: {{type(input_data)}}")
            
            # TODO: Implement your task logic here
            result = {{
                "task_id": "{task_id}",
                "input_type": str(type(input_data)),
                "input_data": str(input_data),
                "processed": True,
                "message": "Task completed successfully"
            }}
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing {{self.task_name}}: {{e}}")
            return {{"error": f"Processing failed: {{str(e)}}"}}
    
    def get_requirements(self) -> List[str]:
        """Return required packages"""
        return []  # TODO: Add your requirements here
    
    def get_description(self) -> str:
        """Task description"""
        return "{task_id.replace('_', ' ').title()} - AI Task"

# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    task = {task_id.replace('_', '').title()}Task()
    
    # Test with sample input
    test_input = "test data"
    result = task.process(test_input)
    print(f"Result: {{result}}")
'''
        
        # Create task.json metadata
        task_json_content = {
            "task_id": task_id,
            "task_name": task_id.replace('_', ' ').title(),
            "description": f"{task_id.replace('_', ' ').title()} - AI Task Implementation",
            "version": "1.0.0",
            "author": "AI Developer",
            "entry_point": "task.py",
            "metadata": {
                "category": "general",
                "tags": ["ai", "task"],
                "input_type": "any",
                "output_type": "dict"
            }
        }
        
        # Create requirements.txt
        requirements_content = '''# Add your Python package requirements here
# Example:
# numpy>=1.19.0
# opencv-python>=4.5.0
# tensorflow>=2.6.0
'''
        
        # Write files
        with open(os.path.join(task_folder, "task.py"), 'w') as f:
            f.write(task_py_content)
        
        with open(os.path.join(task_folder, "task.json"), 'w') as f:
            json.dump(task_json_content, f, indent=2)
        
        with open(os.path.join(task_folder, "requirements.txt"), 'w') as f:
            f.write(requirements_content)
        
        with open(os.path.join(task_folder, "README.md"), 'w') as f:
            f.write(f"""# {task_id.replace('_', ' ').title()} Task

## Description
AI Task implementation for {task_id}.

## Usage
```python
from task import {task_id.replace('_', '').title()}Task

task = {task_id.replace('_', '').title()}Task()
result = task.process("your input data")
print(result)
```

## Requirements
See requirements.txt for dependencies.

## Implementation Notes
- Implement your logic in the `process()` method
- Add required packages to requirements.txt
- Update task.json metadata as needed
""")
        
        print(f"✅ Task template created: {task_folder}")
        print(f"📝 Files created:")
        print(f"   - task.py (main implementation)")
        print(f"   - task.json (metadata)")
        print(f"   - requirements.txt (dependencies)")
        print(f"   - README.md (documentation)")
        
    except Exception as e:
        print(f"❌ Failed to create task template: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='AI Task Registration Tool')
    parser.add_argument('--config', default='config.json', help='Config file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register a new task')
    register_parser.add_argument('--folder', required=True, help='Task folder path')
    register_parser.add_argument('--task-id', help='Override task ID')
    register_parser.add_argument('--name', help='Override task name')
    register_parser.add_argument('--description', help='Override description')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List registered tasks')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create task template')
    create_parser.add_argument('--task-id', required=True, help='Task ID')
    create_parser.add_argument('--folder', help='Output folder (default: ./tasks/{task_id})')
    
    args = parser.parse_args()
    
    if args.command == 'register':
        task_info = None
        if args.task_id or args.name or args.description:
            task_info = detect_task_info(args.folder)
            if args.task_id:
                task_info['task_id'] = args.task_id
            if args.name:
                task_info['task_name'] = args.name
            if args.description:
                task_info['description'] = args.description
        
        register_task(args.config, args.folder, task_info)
        
    elif args.command == 'list':
        list_registered_tasks(args.config)
        
    elif args.command == 'create':
        folder = args.folder or os.path.join("./tasks", args.task_id)
        create_task_template(args.task_id, folder)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()