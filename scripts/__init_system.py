#!/usr/bin/env python3
"""
System initialization script
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config.manager import config_manager
from core.database.connection import init_database
from core.storage.connection import init_storage

console = Console()


def check_dependencies():
    """Check if required services are running"""
    console.print("[yellow]Checking dependencies...[/yellow]")
    
    services = {
        "MongoDB": ("mongodb://localhost:27017", "mongosh --eval 'db.runCommand({ping: 1})'"),
        "MinIO": ("http://localhost:9000", "curl -f http://localhost:9000/minio/health/ready"),
        "Redis": ("redis://localhost:6379", "redis-cli ping")
    }
    
    for service, (url, check_cmd) in services.items():
        try:
            result = subprocess.run(
                check_cmd.split(),
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                console.print(f"[green]✓ {service} is running[/green]")
            else:
                console.print(f"[red]✗ {service} is not responding[/red]")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            console.print(f"[red]✗ {service} check failed[/red]")
            return False
    
    return True


def setup_directories():
    """Create necessary directories"""
    console.print("[yellow]Setting up directories...[/yellow]")
    
    directories = [
        "task_cache",
        "pipeline_cache",
        "logs",
        "tasks/examples",
        "tasks/pipelines"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓ Created directory: {directory}[/green]")


def initialize_config():
    """Initialize configuration"""
    console.print("[yellow]Initializing configuration...[/yellow]")
    
    config_file = Path("config.json")
    
    if not config_file.exists():
        # Create default config
        config = config_manager.create_default_config()
        console.print("[green]✓ Created default configuration[/green]")
    else:
        # Load existing config
        config = config_manager.load_config()
        console.print("[green]✓ Loaded existing configuration[/green]")
    
    return config


def initialize_database():
    """Initialize database connection and schema"""
    console.print("[yellow]Initializing database...[/yellow]")
    
    try:
        if init_database():
            console.print("[green]✓ Database initialized successfully[/green]")
            return True
        else:
            console.print("[red]✗ Failed to initialize database[/red]")
            return False
    except Exception as e:
        console.print(f"[red]✗ Database initialization error: {e}[/red]")
        return False


def initialize_storage():
    """Initialize storage connection and buckets"""
    console.print("[yellow]Initializing storage...[/yellow]")
    
    try:
        if init_storage():
            console.print("[green]✓ Storage initialized successfully[/green]")
            return True
        else:
            console.print("[red]✗ Failed to initialize storage[/red]")
            return False
    except Exception as e:
        console.print(f"[red]✗ Storage initialization error: {e}[/red]")
        return False


def register_example_tasks():
    """Register example tasks"""
    console.print("[yellow]Registering example tasks...[/yellow]")
    
    try:
        from core.database.operations import db_ops
        from core.database.models import TaskMetadata, TaskType
        from core.storage.operations import storage_ops
        
        # Register face detection task
        face_detection_path = "tasks/examples/face_detection"
        if Path(face_detection_path).exists():
            # Load task config
            with open(f"{face_detection_path}/task.json", 'r') as f:
                task_config = json.load(f)
            
            # Upload package
            storage_info = storage_ops.upload_task_package(
                task_config['task_id'], 
                face_detection_path
            )
            
            if storage_info:
                # Create metadata
                task_metadata = TaskMetadata(
                    task_id=task_config['task_id'],
                    name=task_config['name'],
                    description=task_config['description'],
                    version=task_config['version'],
                    author=task_config['author'],
                    task_type=TaskType.SINGLE,
                    entry_point=task_config['entry_point'],
                    requirements=task_config['requirements'],
                    storage_path=storage_info['storage_path'],
                    file_hash=storage_info['file_hash'],
                    file_size=storage_info['file_size'],
                    tags=task_config['tags'],
                    category=task_config['category']
                )
                
                if db_ops.create_task_metadata(task_metadata):
                    console.print("[green]✓ Registered face_detection task[/green]")
                else:
                    console.print("[yellow]⚠ Face detection task already exists[/yellow]")
        
        # Register text sentiment task
        text_sentiment_path = "tasks/examples/text_sentiment"
        if Path(text_sentiment_path).exists():
            # Load task config
            with open(f"{text_sentiment_path}/task.json", 'r') as f:
                task_config = json.load(f)
            
            # Upload package
            storage_info = storage_ops.upload_task_package(
                task_config['task_id'], 
                text_sentiment_path
            )
            
            if storage_info:
                # Create metadata
                task_metadata = TaskMetadata(
                    task_id=task_config['task_id'],
                    name=task_config['name'],
                    description=task_config['description'],
                    version=task_config['version'],
                    author=task_config['author'],
                    task_type=TaskType.SINGLE,
                    entry_point=task_config['entry_point'],
                    requirements=task_config['requirements'],
                    storage_path=storage_info['storage_path'],
                    file_hash=storage_info['file_hash'],
                    file_size=storage_info['file_size'],
                    tags=task_config['tags'],
                    category=task_config['category']
                )
                
                if db_ops.create_task_metadata(task_metadata):
                    console.print("[green]✓ Registered text_sentiment task[/green]")
                else:
                    console.print("[yellow]⚠ Text sentiment task already exists[/yellow]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Failed to register example tasks: {e}[/red]")
        return False


def install_requirements():
    """Install Python requirements"""
    console.print("[yellow]Installing requirements...[/yellow]")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Requirements installed successfully[/green]")
            return True
        else:
            console.print(f"[red]✗ Failed to install requirements: {result.stderr}[/red]")
            return False
    except Exception as e:
        console.print(f"[red]✗ Requirements installation error: {e}[/red]")
        return False


def create_startup_scripts():
    """Create startup scripts"""
    console.print("[yellow]Creating startup scripts...[/yellow]")
    
    # Create start_worker.sh
    start_worker_script = """#!/bin/bash
# AI Worker Startup Script

echo "Starting AI Worker System..."

# Check if services are running
echo "Checking dependencies..."
if ! docker-compose ps | grep -q "running"; then
    echo "Starting Docker services..."
    docker-compose up -d
    sleep 10
fi

# Start worker
echo "Starting worker..."
python3 -m tools.worker_cli start --daemon

echo "Worker started successfully!"
echo "Monitor with: python3 -m tools.worker_cli monitor"
echo "Check status with: python3 -m tools.worker_cli status"
"""
    
    with open("start_worker.sh", 'w') as f:
        f.write(start_worker_script)
    
    os.chmod("start_worker.sh", 0o755)
    console.print("[green]✓ Created start_worker.sh[/green]")
    
    # Create stop_worker.sh
    stop_worker_script = """#!/bin/bash
# AI Worker Stop Script

echo "Stopping AI Worker System..."

# Stop worker
python3 -m tools.worker_cli stop

echo "Worker stopped!"
"""
    
    with open("stop_worker.sh", 'w') as f:
        f.write(stop_worker_script)
    
    os.chmod("stop_worker.sh", 0o755)
    console.print("[green]✓ Created stop_worker.sh[/green]")


def run_health_check():
    """Run system health check"""
    console.print("[yellow]Running health check...[/yellow]")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "tools.worker_cli", "health"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Health check passed[/green]")
            return True
        else:
            console.print(f"[yellow]⚠ Health check warnings: {result.stdout}[/yellow]")
            return True  # Still continue even with warnings
    except Exception as e:
        console.print(f"[red]✗ Health check failed: {e}[/red]")
        return False


def main():
    """Main initialization function"""
    console.print(Panel(
        "[bold blue]AI Task Worker System Initialization[/bold blue]",
        subtitle="Setting up the complete system"
    ))
    
    steps = [
        ("Checking dependencies", check_dependencies),
        ("Installing requirements", install_requirements),
        ("Setting up directories", setup_directories),
        ("Initializing configuration", initialize_config),
        ("Initializing database", initialize_database),
        ("Initializing storage", initialize_storage),
        ("Registering example tasks", register_example_tasks),
        ("Creating startup scripts", create_startup_scripts),
        ("Running health check", run_health_check)
    ]
    
    with Progress() as progress:
        task = progress.add_task("Initializing system...", total=len(steps))
        
        for step_name, step_func in steps:
            progress.update(task, description=f"[yellow]{step_name}...[/yellow]")
            
            try:
                if step_func():
                    progress.advance(task)
                else:
                    console.print(f"[red]✗ Failed: {step_name}[/red]")
                    return False
            except Exception as e:
                console.print(f"[red]✗ Error in {step_name}: {e}[/red]")
                return False
    
    # Success message
    success_message = """
[bold green]🎉 System Initialization Complete![/bold green]

[cyan]Next Steps:[/cyan]
1. Start the system: [bold]./start_worker.sh[/bold]
2. Check status: [bold]python3 -m tools.worker_cli status[/bold]
3. Monitor worker: [bold]python3 -m tools.worker_cli monitor[/bold]
4. Test a task: [bold]python3 -m tools.task_manager test face_detection '"/path/to/image.jpg"'[/bold]

[cyan]Management Commands:[/cyan]
• List tasks: [bold]python3 -m tools.task_manager list[/bold]
• Create task: [bold]python3 -m tools.task_manager create my_task[/bold]
• Worker status: [bold]python3 -m tools.worker_cli status[/bold]
• View logs: [bold]tail -f logs/worker.log[/bold]

[cyan]Web Interfaces:[/cyan]
• Flower (Celery Monitor): http://localhost:5555
• MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)

[yellow]The system is ready to process AI tasks![/yellow]
    """
    
    console.print(Panel(success_message.strip(), title="Initialization Complete", border_style="green"))
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Initialization cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Initialization failed: {e}[/red]")
        sys.exit(1)