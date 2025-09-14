#!/usr/bin/env python3
"""
Worker CLI Tool
"""
import os
import sys
import signal
import subprocess
import time
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress
from loguru import logger

from core.config.manager import get_config, config_manager
from core.database.operations import db_ops
from worker.task_registry import task_registry

console = Console()


@click.group()
@click.option('--config', '-c', default='config.json', help='Configuration file path')
def cli(config):
    """AI Worker CLI"""
    # Set config path
    config_manager.config_path = Path(config)


@cli.command()
@click.option('--daemon', '-d', is_flag=True, help='Run as daemon')
@click.option('--loglevel', '-l', default='INFO', help='Log level')
@click.option('--queues', '-q', help='Comma-separated list of queues to listen to')
@click.option('--concurrency', '-c', type=int, help='Number of concurrent workers')
def start(daemon, loglevel, queues, concurrency):
    """Start the AI worker"""
    try:
        config = get_config()
        
        # Build Celery command
        cmd = [
            sys.executable, '-m', 'celery', 
            '-A', 'worker.celery_app:celery_app',  # Move -A before worker
            'worker',
            '--loglevel', loglevel
        ]
        
        # Add queues
        if queues:
            cmd.extend(['-Q', queues])
        else:
            # Use configured queues
            worker_queues = []
            for task_id in config.worker.active_tasks:
                task_config = config.worker.task_configs.get(task_id)
                if task_config:
                    queue = getattr(task_config, 'queue', 'default')
                    if queue not in worker_queues:
                        worker_queues.append(queue)
            
            if worker_queues:
                cmd.extend(['-Q', ','.join(worker_queues)])
        
        # Add concurrency
        if concurrency:
            cmd.extend(['-c', str(concurrency)])
        elif config.worker.max_concurrent_tasks:
            cmd.extend(['-c', str(config.worker.max_concurrent_tasks)])
        
        # Add worker name
        cmd.extend(['-n', f"{config.worker.worker_id}@%h"])
        
        console.print(f"[green]Starting worker: {config.worker.worker_name}[/green]")
        console.print(f"[yellow]Command: {' '.join(cmd)}[/yellow]")
        
        if daemon:
            # Run as daemon
            console.print("[blue]Running in daemon mode...[/blue]")
            
            # Set up signal handlers for graceful shutdown
            def signal_handler(signum, frame):
                console.print("\n[yellow]Shutting down worker...[/yellow]")
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Start worker process
            process = subprocess.Popen(cmd)
            
            try:
                process.wait()
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping worker...[/yellow]")
                process.terminate()
                process.wait()
        else:
            # Run interactively
            subprocess.run(cmd)
        
    except Exception as e:
        console.print(f"[red]Failed to start worker: {e}[/red]")


@cli.command()
def stop():
    """Stop running workers"""
    try:
        # Find running Celery processes
        result = subprocess.run([
            'pkill', '-f', 'celery worker'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Workers stopped[/green]")
        else:
            console.print("[yellow]No running workers found[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Failed to stop workers: {e}[/red]")


@cli.command()
def status():
    """Show worker status"""
    try:
        config = get_config()
        
        # Get worker status from database
        worker_status = db_ops.get_worker_status(config.worker.worker_id)
        
        if not worker_status:
            console.print("[yellow]Worker not registered[/yellow]")
            return
        
        # Create status panel
        status_text = f"""
[bold cyan]Worker ID:[/bold cyan] {worker_status.worker_id}
[bold cyan]Hostname:[/bold cyan] {worker_status.hostname}
[bold cyan]Active:[/bold cyan] {"Yes" if worker_status.is_active else "No"}
[bold cyan]Last Heartbeat:[/bold cyan] {worker_status.last_heartbeat}
[bold cyan]Current Tasks:[/bold cyan] {worker_status.current_task_count}/{worker_status.max_concurrent_tasks}
[bold cyan]Memory Usage:[/bold cyan] {worker_status.memory_usage:.1f} MB
[bold cyan]CPU Usage:[/bold cyan] {worker_status.cpu_usage:.1f}%
[bold cyan]Python Version:[/bold cyan] {worker_status.python_version}
[bold cyan]Celery Version:[/bold cyan] {worker_status.celery_version}
[bold cyan]Total Executed:[/bold cyan] {worker_status.total_tasks_executed}
[bold cyan]Successful:[/bold cyan] {worker_status.successful_tasks}
[bold cyan]Failed:[/bold cyan] {worker_status.failed_tasks}
        """
        
        panel = Panel(status_text.strip(), title="Worker Status", border_style="blue")
        console.print(panel)
        
        # Show active tasks
        if worker_status.active_tasks:
            console.print("\n[bold]Active Tasks:[/bold]")
            for task_id in worker_status.active_tasks:
                console.print(f"  • {task_id}")
        
        # Show active pipelines
        if worker_status.active_pipelines:
            console.print("\n[bold]Active Pipelines:[/bold]")
            for pipeline_id in worker_status.active_pipelines:
                console.print(f"  • {pipeline_id}")
        
        # Show queues
        if worker_status.queues:
            console.print("\n[bold]Listening Queues:[/bold]")
            for queue in worker_status.queues:
                console.print(f"  • {queue}")
        
    except Exception as e:
        console.print(f"[red]Failed to get worker status: {e}[/red]")


@cli.command()
def monitor():
    """Monitor worker in real-time"""
    try:
        config = get_config()
        
        def create_status_table():
            # Get worker status
            worker_status = db_ops.get_worker_status(config.worker.worker_id)
            
            if not worker_status:
                return Panel("[yellow]Worker not registered[/yellow]", title="Worker Monitor")
            
            # Create table
            table = Table(title=f"Worker Monitor: {worker_status.worker_id}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Status", "Active" if worker_status.is_active else "Inactive")
            table.add_row("Hostname", worker_status.hostname)
            table.add_row("Last Heartbeat", str(worker_status.last_heartbeat))
            table.add_row("Current Tasks", f"{worker_status.current_task_count}/{worker_status.max_concurrent_tasks}")
            table.add_row("Memory Usage", f"{worker_status.memory_usage:.1f} MB")
            table.add_row("CPU Usage", f"{worker_status.cpu_usage:.1f}%")
            table.add_row("Total Executed", str(worker_status.total_tasks_executed))
            table.add_row("Success Rate", f"{(worker_status.successful_tasks/max(worker_status.total_tasks_executed,1)*100):.1f}%")
            
            return table
        
        # Live monitoring
        with Live(create_status_table(), refresh_per_second=1) as live:
            try:
                while True:
                    live.update(create_status_table())
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Monitoring stopped[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Failed to monitor worker: {e}[/red]")


@cli.command()
def reload():
    """Reload worker configuration and tasks"""
    try:
        # Reload configuration
        config_manager.reload_config()
        console.print("[green]✓ Configuration reloaded[/green]")
        
        # Reload tasks
        task_registry.load_and_register_tasks()
        console.print("[green]✓ Tasks reloaded[/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to reload worker: {e}[/red]")


@cli.command()
@click.argument('task_id')
@click.argument('input_data')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='json', help='Input format')
@click.option('--sync', is_flag=True, help='Execute synchronously')
def execute(task_id, input_data, format, sync):
    """Execute a task"""
    try:
        import json
        
        # Parse input data
        if format == 'json':
            try:
                parsed_input = json.loads(input_data)
            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON input: {e}[/red]")
                return
        else:
            parsed_input = input_data
        
        console.print(f"[yellow]Executing task: {task_id}[/yellow]")
        
        if sync:
            # Execute synchronously
            from ..core.task_loader.loader import task_loader
            
            task_instance = task_loader.load_task(task_id)
            if not task_instance:
                console.print(f"[red]Task not found: {task_id}[/red]")
                return
            
            with Progress() as progress:
                exec_task = progress.add_task("Executing...", total=100)
                
                try:
                    result = task_instance.process(parsed_input)
                    progress.update(exec_task, advance=100)
                    
                    console.print("[green]✓ Task completed[/green]")
                    console.print(f"[cyan]Result:[/cyan] {result}")
                    
                except Exception as e:
                    progress.update(exec_task, advance=100)
                    console.print(f"[red]Task failed: {e}[/red]")
        else:
            # Execute asynchronously via Celery
            execution_id = task_registry.submit_task(task_id, parsed_input)
            
            if execution_id:
                console.print(f"[green]✓ Task submitted with execution ID: {execution_id}[/green]")
                console.print("[yellow]Use 'worker_cli executions' to monitor progress[/yellow]")
            else:
                console.print("[red]Failed to submit task[/red]")
        
    except Exception as e:
        console.print(f"[red]Failed to execute task: {e}[/red]")


@cli.command()
@click.option('--limit', '-l', type=int, default=20, help='Number of records to show')
@click.option('--status', '-s', help='Filter by status')
@click.option('--task-id', '-t', help='Filter by task ID')
def executions(limit, status, task_id):
    """Show execution history"""
    try:
        from ..core.database.models import TaskStatus
        
        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status)
            except ValueError:
                console.print(f"[red]Invalid status: {status}[/red]")
                return
        
        # Get execution records
        records = db_ops.list_execution_records(
            task_id=task_id,
            status=status_filter,
            limit=limit
        )
        
        if not records:
            console.print("[yellow]No execution records found[/yellow]")
            return
        
        # Create table
        table = Table(title="Execution History")
        table.add_column("Execution ID", style="cyan")
        table.add_column("Task/Pipeline", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Duration", style="blue")
        table.add_column("Worker", style="magenta")
        table.add_column("Started", style="white")
        
        for record in records:
            duration = ""
            if record.duration:
                duration = f"{record.duration:.2f}s"
            
            task_name = record.task_id or record.pipeline_id or "Unknown"
            
            # Color status
            status_color = {
                "success": "green",
                "failed": "red",
                "running": "yellow",
                "pending": "blue"
            }.get(record.status.value, "white")
            
            table.add_row(
                record.execution_id[:8] + "...",
                task_name,
                f"[{status_color}]{record.status.value}[/{status_color}]",
                duration,
                record.worker_id,
                record.started_at.strftime("%H:%M:%S") if record.started_at else ""
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Failed to get execution history: {e}[/red]")


@cli.command()
def workers():
    """List all active workers"""
    try:
        workers = db_ops.list_active_workers()
        
        if not workers:
            console.print("[yellow]No active workers found[/yellow]")
            return
        
        # Create table
        table = Table(title="Active Workers")
        table.add_column("Worker ID", style="cyan")
        table.add_column("Hostname", style="green")
        table.add_column("Tasks", style="yellow")
        table.add_column("Memory", style="blue")
        table.add_column("CPU", style="magenta")
        table.add_column("Last Heartbeat", style="white")
        
        for worker in workers:
            memory_str = f"{worker.memory_usage:.1f} MB" if worker.memory_usage else "N/A"
            cpu_str = f"{worker.cpu_usage:.1f}%" if worker.cpu_usage else "N/A"
            
            table.add_row(
                worker.worker_id,
                worker.hostname,
                f"{worker.current_task_count}/{worker.max_concurrent_tasks}",
                memory_str,
                cpu_str,
                worker.last_heartbeat.strftime("%H:%M:%S") if worker.last_heartbeat else "N/A"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Failed to list workers: {e}[/red]")


@cli.command()
def health():
    """Check worker health"""
    try:
        from ..worker.worker_manager import worker_manager
        from ..core.database.connection import get_mongodb_connection
        from ..core.storage.connection import get_minio_connection
        
        console.print("[yellow]Checking worker health...[/yellow]")
        
        health_status = {
            "database": False,
            "storage": False,
            "worker": False,
            "tasks": 0,
            "pipelines": 0
        }
        
        # Check database connection
        try:
            db_conn = get_mongodb_connection()
            health_status["database"] = db_conn.health_check()
        except Exception:
            pass
        
        # Check storage connection
        try:
            storage_conn = get_minio_connection()
            health_status["storage"] = storage_conn.health_check()
        except Exception:
            pass
        
        # Check worker health
        health_status["worker"] = worker_manager.is_healthy()
        
        # Check loaded tasks and pipelines
        health_status["tasks"] = len(task_registry.get_registered_tasks())
        health_status["pipelines"] = len(task_registry.get_registered_pipelines())
        
        # Create health report
        health_text = f"""
[bold cyan]Database Connection:[/bold cyan] {"✓ Connected" if health_status["database"] else "✗ Failed"}
[bold cyan]Storage Connection:[/bold cyan] {"✓ Connected" if health_status["storage"] else "✗ Failed"}
[bold cyan]Worker Health:[/bold cyan] {"✓ Healthy" if health_status["worker"] else "✗ Unhealthy"}
[bold cyan]Registered Tasks:[/bold cyan] {health_status["tasks"]}
[bold cyan]Registered Pipelines:[/bold cyan] {health_status["pipelines"]}
        """
        
        # Determine overall health
        overall_healthy = (
            health_status["database"] and 
            health_status["storage"] and 
            health_status["worker"]
        )
        
        border_style = "green" if overall_healthy else "red"
        title = "Health Check: Healthy" if overall_healthy else "Health Check: Issues Detected"
        
        panel = Panel(health_text.strip(), title=title, border_style=border_style)
        console.print(panel)
        
        if not overall_healthy:
            console.print("[red]✗ Worker has health issues that need attention[/red]")
            sys.exit(1)
        else:
            console.print("[green]✓ Worker is healthy[/green]")
        
    except Exception as e:
        console.print(f"[red]Health check failed: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    cli()