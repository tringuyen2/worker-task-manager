#!/usr/bin/env python3
"""
Task Manager CLI Tool
"""
import os
import json
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from loguru import logger

from core.config.manager import get_config, config_manager
from core.database.operations import db_ops
from core.database.models import TaskMetadata, TaskType
from core.storage.operations import storage_ops
from core.task_loader.validator import TaskValidator

console = Console()
validator = TaskValidator()


@click.group()
@click.option('--config', '-c', default='config.json', help='Configuration file path')
def cli(config):
    """AI Task Manager CLI"""
    # Set config path
    config_manager.config_path = Path(config)


@cli.command()
@click.argument('task_id')
@click.option('--name', '-n', help='Task name')
@click.option('--description', '-d', help='Task description')
@click.option('--author', '-a', help='Task author')
@click.option('--category', '-cat', default='general', help='Task category')
@click.option('--template', '-t', type=click.Choice(['simple', 'ml', 'vision', 'nlp']), default='simple', help='Task template')
def create(task_id, name, description, author, category, template):
    """Create a new task template"""
    try:
        task_dir = Path(f"tasks/{task_id}")
        
        if task_dir.exists():
            console.print(f"[red]Task directory already exists: {task_dir}[/red]")
            return
        
        # Create task directory
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Create task.py based on template
        task_py_content = get_task_template(template, task_id, name or task_id)
        with open(task_dir / "task.py", 'w') as f:
            f.write(task_py_content)
        
        # Create task.json
        task_config = {
            "task_id": task_id,
            "name": name or task_id,
            "description": description or f"AI task: {task_id}",
            "version": "1.0.0",
            "author": author or "Unknown",
            "category": category,
            "entry_point": "task.Task",
            "requirements": get_template_requirements(template),
            "tags": [template, category]
        }
        
        with open(task_dir / "task.json", 'w') as f:
            json.dump(task_config, f, indent=2)
        
        # Create requirements.txt
        requirements = get_template_requirements(template)
        if requirements:
            with open(task_dir / "requirements.txt", 'w') as f:
                f.write('\n'.join(requirements))
        
        console.print(f"[green]✓ Task template created: {task_dir}[/green]")
        console.print(f"[yellow]Edit {task_dir}/task.py to implement your task logic[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Failed to create task: {e}[/red]")


@cli.command()
@click.argument('task_folder')
@click.option('--task-id', help='Override task ID from config')
@click.option('--validate-only', is_flag=True, help='Only validate, do not register')
def register(task_folder, task_id, validate_only):
    """Register a task with the system"""
    try:
        task_path = Path(task_folder)
        if not task_path.exists():
            console.print(f"[red]Task folder not found: {task_folder}[/red]")
            return
        
        # Load task configuration
        config_file = task_path / "task.json"
        if not config_file.exists():
            console.print(f"[red]Task configuration not found: {config_file}[/red]")
            return
        
        with open(config_file, 'r') as f:
            task_config = json.load(f)
        
        # Override task ID if provided
        if task_id:
            task_config['task_id'] = task_id
        
        # Validate task configuration
        if not validator.validate_task_config(task_config):
            console.print("[red]Task configuration validation failed[/red]")
            return
        
        # Validate task code
        try:
            from core.task_loader.loader import task_loader
            task_instance = task_loader._load_task_from_path(str(task_path), type('MockMetadata', (), task_config)())
            
            if not validator.validate_task(task_instance):
                console.print("[red]Task code validation failed[/red]")
                return
            
            console.print("[green]✓ Task validation passed[/green]")
            
        except Exception as e:
            console.print(f"[red]Task validation failed: {e}[/red]")
            return
        
        if validate_only:
            console.print("[yellow]Validation only - task not registered[/yellow]")
            return
        
        # Upload task package
        with Progress() as progress:
            upload_task = progress.add_task("Uploading task package...", total=100)
            
            storage_info = storage_ops.upload_task_package(task_config['task_id'], str(task_path))
            progress.update(upload_task, advance=50)
            
            if not storage_info:
                console.print("[red]Failed to upload task package[/red]")
                return
            
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
            
            progress.update(upload_task, advance=30)
            
            # Save to database
            if db_ops.create_task_metadata(task_metadata):
                progress.update(upload_task, advance=20)
                console.print(f"[green]✓ Task registered successfully: {task_config['task_id']}[/green]")
                
                # Update worker configuration
                from core.config.models import TaskConfig
                
                worker_task_config = TaskConfig(
                    task_id=task_config['task_id'],
                    queue=task_config.get('queue', 'default'),
                    priority=task_config.get('priority', 5),
                    timeout=task_config.get('timeout', 300)
                )
                
                config_manager.update_task_config(task_config['task_id'], worker_task_config)
                console.print("[green]✓ Worker configuration updated[/green]")
                
            else:
                console.print("[red]Failed to save task metadata[/red]")
        
    except Exception as e:
        console.print(f"[red]Failed to register task: {e}[/red]")


@cli.command()
def list():
    """List all registered tasks"""
    try:
        tasks = db_ops.list_tasks()
        
        if not tasks:
            console.print("[yellow]No tasks found[/yellow]")
            return
        
        table = Table(title="Registered Tasks")
        table.add_column("Task ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Version", style="yellow")
        table.add_column("Category", style="blue")
        table.add_column("Author", style="magenta")
        table.add_column("Active", style="red")
        table.add_column("Created", style="white")
        
        for task in tasks:
            table.add_row(
                task.task_id,
                task.name,
                task.version,
                task.category,
                task.author,
                "✓" if task.is_active else "✗",
                task.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Failed to list tasks: {e}[/red]")


@cli.command()
@click.argument('task_id')
def info(task_id):
    """Show detailed task information"""
    try:
        task_metadata = db_ops.get_task_metadata(task_id)
        
        if not task_metadata:
            console.print(f"[red]Task not found: {task_id}[/red]")
            return
        
        # Create info panel
        info_text = f"""
[bold cyan]Task ID:[/bold cyan] {task_metadata.task_id}
[bold cyan]Name:[/bold cyan] {task_metadata.name}
[bold cyan]Description:[/bold cyan] {task_metadata.description}
[bold cyan]Version:[/bold cyan] {task_metadata.version}
[bold cyan]Author:[/bold cyan] {task_metadata.author}
[bold cyan]Category:[/bold cyan] {task_metadata.category}
[bold cyan]Entry Point:[/bold cyan] {task_metadata.entry_point}
[bold cyan]Queue:[/bold cyan] {task_metadata.queue}
[bold cyan]Priority:[/bold cyan] {task_metadata.priority}
[bold cyan]Timeout:[/bold cyan] {task_metadata.timeout}s
[bold cyan]Active:[/bold cyan] {"Yes" if task_metadata.is_active else "No"}
[bold cyan]Created:[/bold cyan] {task_metadata.created_at}
[bold cyan]Updated:[/bold cyan] {task_metadata.updated_at}
[bold cyan]Storage Path:[/bold cyan] {task_metadata.storage_path}
[bold cyan]File Size:[/bold cyan] {task_metadata.file_size} bytes
[bold cyan]Requirements:[/bold cyan] {', '.join(task_metadata.requirements)}
[bold cyan]Tags:[/bold cyan] {', '.join(task_metadata.tags)}
        """
        
        panel = Panel(info_text.strip(), title=f"Task Information: {task_id}", border_style="blue")
        console.print(panel)
        
        # Get execution statistics
        stats = db_ops.get_task_statistics(task_id)
        if stats:
            stats_text = f"""
[bold green]Total Executions:[/bold green] {stats.get('total_executions', 0)}
[bold green]Successful:[/bold green] {stats.get('successful', 0)}
[bold green]Failed:[/bold green] {stats.get('failed', 0)}
[bold green]Running:[/bold green] {stats.get('running', 0)}
[bold green]Pending:[/bold green] {stats.get('pending', 0)}
[bold green]Average Duration:[/bold green] {stats.get('avg_duration', 0):.2f}s
            """
            
            stats_panel = Panel(stats_text.strip(), title="Execution Statistics (Last 7 days)", border_style="green")
            console.print(stats_panel)
        
    except Exception as e:
        console.print(f"[red]Failed to get task info: {e}[/red]")


@cli.command()
@click.argument('task_id')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def delete(task_id, confirm):
    """Delete a task"""
    try:
        task_metadata = db_ops.get_task_metadata(task_id)
        
        if not task_metadata:
            console.print(f"[red]Task not found: {task_id}[/red]")
            return
        
        if not confirm:
            if not click.confirm(f"Are you sure you want to delete task '{task_id}'?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return
        
        # Delete from storage
        if not storage_ops.delete_package(task_metadata.storage_path):
            console.print("[yellow]Warning: Failed to delete task package from storage[/yellow]")
        
        # Delete from database
        if db_ops.delete_task_metadata(task_id):
            console.print(f"[green]✓ Task deleted: {task_id}[/green]")
            
            # Remove from worker configuration
            config_manager.remove_task(task_id)
            console.print("[green]✓ Worker configuration updated[/green]")
        else:
            console.print("[red]Failed to delete task from database[/red]")
        
    except Exception as e:
        console.print(f"[red]Failed to delete task: {e}[/red]")


@cli.command()
@click.argument('task_id')
@click.option('--enable/--disable', default=True, help='Enable or disable task')
def toggle(task_id, enable):
    """Enable or disable a task"""
    try:
        if db_ops.update_task_metadata(task_id, {"is_active": enable}):
            status = "enabled" if enable else "disabled"
            console.print(f"[green]✓ Task {status}: {task_id}[/green]")
        else:
            console.print(f"[red]Failed to update task: {task_id}[/red]")
        
    except Exception as e:
        console.print(f"[red]Failed to toggle task: {e}[/red]")


@cli.command()
@click.argument('task_id')
@click.argument('input_data')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='json', help='Input data format')
def test(task_id, input_data, format):
    """Test a task with sample input"""
    try:
        from core.task_loader.loader import task_loader
        
        # Load task
        task_instance = task_loader.load_task(task_id)
        if not task_instance:
            console.print(f"[red]Failed to load task: {task_id}[/red]")
            return
        
        # Parse input data
        if format == 'json':
            try:
                parsed_input = json.loads(input_data)
            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON input: {e}[/red]")
                return
        else:
            parsed_input = input_data
        
        console.print(f"[yellow]Testing task: {task_id}[/yellow]")
        console.print(f"[yellow]Input: {parsed_input}[/yellow]")
        
        # Execute task
        with Progress() as progress:
            test_task = progress.add_task("Executing task...", total=100)
            
            try:
                result = task_instance.process(parsed_input)
                progress.update(test_task, advance=100)
                
                console.print("[green]✓ Task execution completed[/green]")
                console.print(f"[cyan]Result:[/cyan] {result}")
                
            except Exception as e:
                progress.update(test_task, advance=100)
                console.print(f"[red]Task execution failed: {e}[/red]")
        
    except Exception as e:
        console.print(f"[red]Failed to test task: {e}[/red]")


def get_task_template(template_type, task_id, task_name):
    """Get task template code"""
    templates = {
        'simple': f'''"""
{task_name} - Simple AI Task
"""
from tasks.base.task_base import TaskBase
from typing import Any


class Task(TaskBase):
    """Simple AI task implementation"""
    
    def __init__(self):
        super().__init__()
    
    def process(self, input_data: Any) -> Any:
        """
        Process input data
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processed result
        """
        # TODO: Implement your task logic here
        self.log_info(f"Processing input: {{type(input_data).__name__}}")
        
        # Example processing
        result = {{
            "task_id": "{task_id}",
            "input_type": type(input_data).__name__,
            "processed": True,
            "result": f"Processed: {{input_data}}"
        }}
        
        return result
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data"""
        # TODO: Add input validation logic
        return input_data is not None
    
    def get_requirements(self) -> list:
        """Get required packages"""
        return []
''',
        
        'ml': f'''"""
{task_name} - Machine Learning Task
"""
from tasks.base.task_base import MLTask
from typing import Any
import numpy as np


class Task(MLTask):
    """Machine Learning task implementation"""
    
    def __init__(self):
        super().__init__()
    
    def load_model(self):
        """Load ML model"""
        # TODO: Load your ML model here
        # Example: return joblib.load('model.pkl')
        self.log_info("Loading ML model...")
        return None  # Replace with actual model loading
    
    def predict(self, preprocessed_input: Any) -> Any:
        """Run model prediction"""
        # TODO: Implement model prediction
        self.log_info("Running model prediction...")
        
        # Example prediction
        if isinstance(preprocessed_input, (list, np.ndarray)):
            # Simulate model prediction
            return {{
                "prediction": "example_class",
                "confidence": 0.95,
                "features": len(preprocessed_input) if hasattr(preprocessed_input, '__len__') else 1
            }}
        
        return {{"prediction": "unknown", "confidence": 0.0}}
    
    def preprocess_input(self, input_data: Any) -> Any:
        """Preprocess input data"""
        # TODO: Implement preprocessing
        self.log_info("Preprocessing input data...")
        return input_data
    
    def postprocess_output(self, output_data: Any) -> Any:
        """Postprocess output data"""
        # TODO: Implement postprocessing
        self.log_info("Postprocessing output data...")
        return output_data
    
    def get_requirements(self) -> list:
        """Get required packages"""
        return [
            "numpy>=1.24.0",
            "scikit-learn>=1.3.0"
        ]
''',
        
        'vision': f'''"""
{task_name} - Computer Vision Task
"""
from tasks.base.task_base import MLTask
from typing import Any
import cv2
import numpy as np


class Task(MLTask):
    """Computer Vision task implementation"""
    
    def __init__(self):
        super().__init__()
    
    def load_model(self):
        """Load vision model"""
        # TODO: Load your vision model here
        self.log_info("Loading vision model...")
        return None  # Replace with actual model loading
    
    def predict(self, preprocessed_input: Any) -> Any:
        """Run vision model prediction"""
        # TODO: Implement vision prediction
        self.log_info("Running vision prediction...")
        
        if isinstance(preprocessed_input, np.ndarray):
            height, width = preprocessed_input.shape[:2]
            return {{
                "detection": "example_object",
                "confidence": 0.90,
                "bbox": [10, 10, 100, 100],
                "image_size": [width, height]
            }}
        
        return {{"detection": None, "confidence": 0.0}}
    
    def preprocess_input(self, input_data: Any) -> Any:
        """Preprocess image data"""
        self.log_info("Preprocessing image data...")
        
        if isinstance(input_data, str):
            # Load image from path
            image = cv2.imread(input_data)
            if image is None:
                raise ValueError(f"Could not load image: {{input_data}}")
            return image
        elif isinstance(input_data, np.ndarray):
            return input_data
        else:
            raise ValueError("Input must be image path or numpy array")
    
    def get_requirements(self) -> list:
        """Get required packages"""
        return [
            "opencv-python>=4.8.0",
            "numpy>=1.24.0",
            "Pillow>=10.0.0"
        ]
''',
        
        'nlp': f'''"""
{task_name} - Natural Language Processing Task
"""
from tasks.base.task_base import MLTask
from typing import Any


class Task(MLTask):
    """NLP task implementation"""
    
    def __init__(self):
        super().__init__()
    
    def load_model(self):
        """Load NLP model"""
        # TODO: Load your NLP model here
        self.log_info("Loading NLP model...")
        return None  # Replace with actual model loading
    
    def predict(self, preprocessed_input: Any) -> Any:
        """Run NLP model prediction"""
        # TODO: Implement NLP prediction
        self.log_info("Running NLP prediction...")
        
        if isinstance(preprocessed_input, str):
            return {{
                "text": preprocessed_input,
                "sentiment": "positive",
                "confidence": 0.85,
                "tokens": len(preprocessed_input.split())
            }}
        
        return {{"sentiment": "neutral", "confidence": 0.0}}
    
    def preprocess_input(self, input_data: Any) -> Any:
        """Preprocess text data"""
        self.log_info("Preprocessing text data...")
        
        if isinstance(input_data, str):
            # Basic text preprocessing
            text = input_data.strip().lower()
            return text
        else:
            raise ValueError("Input must be a string")
    
    def get_requirements(self) -> list:
        """Get required packages"""
        return [
            "transformers>=4.30.0",
            "torch>=2.0.0",
            "nltk>=3.8.0"
        ]
'''
    }
    
    return templates.get(template_type, templates['simple'])


def get_template_requirements(template_type):
    """Get requirements for template type"""
    requirements_map = {
        'simple': [],
        'ml': ["numpy>=1.24.0", "scikit-learn>=1.3.0"],
        'vision': ["opencv-python>=4.8.0", "numpy>=1.24.0", "Pillow>=10.0.0"],
        'nlp': ["transformers>=4.30.0", "torch>=2.0.0", "nltk>=3.8.0"]
    }
    
    return requirements_map.get(template_type, [])


if __name__ == '__main__':
    cli()