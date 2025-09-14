#!/usr/bin/env python3
"""
Pipeline CLI Tool for Multi-Worker System
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
from worker.multi_worker_manager import multi_worker_manager
from pipeline.router import pipeline_executor

console = Console()


@click.group()
@click.option('--config', '-c', default='config.json', help='Configuration file path')
def cli(config):
    """AI Pipeline CLI for Multi-Worker System"""
    config_manager.config_path = Path(config)


@cli.command()
def start_multi():
    """Start multi-worker system"""
    try:
        console.print("[yellow]Starting multi-worker system...[/yellow]")
        
        with Progress() as progress:
            task = progress.add_task("Starting workers...", total=100)
            
            # Start all task workers
            if multi_worker_manager.start_all_task_workers():
                progress.update(task, advance=100)
                console.print("[green]✓ Multi-worker system started successfully[/green]")
                
                # Show worker status
                status = multi_worker_manager.get_worker_status()
                console.print(f"[cyan]Started {status['alive_workers']}/{status['total_workers']} workers[/cyan]")
                
            else:
                progress.update(task, advance=100)
                console.print("[red]✗ Failed to start some workers[/red]")
                
    except Exception as e:
        console.print(f"[red]Failed to start multi-worker system: {e}[/red]")


@cli.command()
def stop_multi():
    """Stop multi-worker system"""
    try:
        console.print("[yellow]Stopping multi-worker system...[/yellow]")
        
        with Progress() as progress:
            task = progress.add_task("Stopping workers...", total=100)
            
            if multi_worker_manager.stop_all_task_workers():
                progress.update(task, advance=100)
                console.print("[green]✓ Multi-worker system stopped successfully[/green]")
            else:
                progress.update(task, advance=100)
                console.print("[red]✗ Failed to stop some workers[/red]")
                
    except Exception as e:
        console.print(f"[red]Failed to stop multi-worker system: {e}[/red]")


@cli.command()
@click.argument('task_id')
def start_worker(task_id):
    """Start worker for specific task"""
    try:
        console.print(f"[yellow]Starting worker for task: {task_id}[/yellow]")
        
        if multi_worker_manager.start_task_worker(task_id):
            console.print(f"[green]✓ Worker started for task: {task_id}[/green]")
        else:
            console.print(f"[red]✗ Failed to start worker for task: {task_id}[/red]")
            
    except Exception as e:
        console.print(f"[red]Failed to start worker: {e}[/red]")


@cli.command()
@click.argument('task_id')
def stop_worker(task_id):
    """Stop worker for specific task"""
    try:
        console.print(f"[yellow]Stopping worker for task: {task_id}[/yellow]")
        
        if multi_worker_manager.stop_task_worker(task_id):
            console.print(f"[green]✓ Worker stopped for task: {task_id}[/green]")
        else:
            console.print(f"[red]✗ Failed to stop worker for task: {task_id}[/red]")
            
    except Exception as e:
        console.print(f"[red]Failed to stop worker: {e}[/red]")


@cli.command()
def status():
    """Show multi-worker system status"""
    try:
        status = multi_worker_manager.get_worker_status()
        
        # Create status table
        table = Table(title="Multi-Worker System Status")
        table.add_column("Task ID", style="cyan")
        table.add_column("Worker Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("PID", style="blue")
        table.add_column("Memory (MB)", style="magenta")
        table.add_column("CPU %", style="red")
        table.add_column("Queue", style="white")
        
        for task_id, worker_info in status.get("workers", {}).items():
            status_color = "green" if worker_info["is_alive"] else "red"
            status_text = "Running" if worker_info["is_alive"] else "Stopped"
            
            table.add_row(
                task_id,
                worker_info["worker_name"],
                f"[{status_color}]{status_text}[/{status_color}]",
                str(worker_info.get("pid", "N/A")),
                f"{worker_info.get('memory_mb', 0):.1f}",
                f"{worker_info.get('cpu_percent', 0):.1f}",
                worker_info["config"].get("queue", "N/A")
            )
        
        console.print(table)
        
        # Summary panel
        summary_text = f"""
[bold cyan]Total Workers:[/bold cyan] {status['total_workers']}
[bold green]Running Workers:[/bold green] {status['alive_workers']}
[bold red]Stopped Workers:[/bold red] {status['total_workers'] - status['alive_workers']}
        """
        
        panel = Panel(summary_text.strip(), title="System Summary", border_style="blue")
        console.print(panel)
        
    except Exception as e:
        console.print(f"[red]Failed to get worker status: {e}[/red]")


@cli.command()
def health():
    """Check health of multi-worker system"""
    try:
        health_status = multi_worker_manager.health_check()
        
        # Create health report
        if health_status["healthy"]:
            console.print("[green]✓ Multi-worker system is healthy[/green]")
        else:
            console.print("[red]✗ Multi-worker system has issues[/red]")
            
            if health_status["unhealthy_workers"]:
                console.print(f"[red]Unhealthy workers: {', '.join(health_status['unhealthy_workers'])}[/red]")
        
        # Health details
        health_text = f"""
[bold cyan]Total Workers:[/bold cyan] {health_status['total_workers']}
[bold green]Healthy Workers:[/bold green] {health_status['healthy_workers']}
[bold red]Unhealthy Workers:[/bold red] {len(health_status['unhealthy_workers'])}
        """
        
        border_style = "green" if health_status["healthy"] else "red"
        panel = Panel(health_text.strip(), title="Health Status", border_style=border_style)
        console.print(panel)
        
    except Exception as e:
        console.print(f"[red]Health check failed: {e}[/red]")


@cli.command()
@click.argument('pipeline_id')
@click.argument('input_data')
@click.option('--format', '-f', type=click.Choice(['json', 'file']), default='json', help='Input format')
def execute(pipeline_id, input_data, format):
    """Execute pipeline"""
    try:
        # Parse input data
        if format == 'json':
            try:
                parsed_input = json.loads(input_data)
            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON input: {e}[/red]")
                return
        else:
            parsed_input = input_data
        
        console.print(f"[yellow]Executing pipeline: {pipeline_id}[/yellow]")
        console.print(f"[yellow]Input: {parsed_input}[/yellow]")
        
        # Execute pipeline
        with Progress() as progress:
            pipeline_task = progress.add_task("Executing pipeline...", total=100)
            
            if pipeline_id == "face_processing":
                result = pipeline_executor.execute_face_processing_pipeline(parsed_input)
                progress.update(pipeline_task, advance=100)
                
                if result["status"] == "completed":
                    console.print("[green]✓ Pipeline execution completed successfully[/green]")
                    
                    # Display results summary
                    if "result" in result:
                        faces_count = len(result["result"].get("faces", []))
                        console.print(f"[cyan]Processed {faces_count} faces[/cyan]")
                    
                    # Show execution summary
                    if "execution_summary" in result:
                        summary = result["execution_summary"]
                        summary_text = f"""
[bold green]Tasks Executed:[/bold green] {summary.get('total_tasks_executed', 0)}
[bold green]Successful:[/bold green] {summary.get('successful_tasks', 0)}
[bold red]Failed:[/bold red] {summary.get('failed_tasks', 0)}
[bold blue]Stages:[/bold blue] {summary.get('stages_completed', 0)}
                        """
                        panel = Panel(summary_text.strip(), title="Execution Summary", border_style="green")
                        console.print(panel)
                    
                    # Show detailed results if requested
                    console.print(f"[cyan]Full Result:[/cyan]")
                    console.print(json.dumps(result, indent=2))
                    
                else:
                    console.print(f"[red]Pipeline execution failed: {result.get('error')}[/red]")
                    
            else:
                progress.update(pipeline_task, advance=100)
                console.print(f"[red]Unknown pipeline: {pipeline_id}[/red]")
                console.print("[yellow]Available pipelines: face_processing[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Failed to execute pipeline: {e}[/red]")


@cli.command()
def demo():
    """Run complete face processing demo"""
    try:
        console.print("[bold blue]🎬 Face Processing Pipeline Demo[/bold blue]")
        console.print()
        
        # Check if multi-worker system is running
        status = multi_worker_manager.get_worker_status()
        if status["alive_workers"] == 0:
            console.print("[yellow]⚠ No workers running. Starting multi-worker system...[/yellow]")
            if not multi_worker_manager.start_all_task_workers():
                console.print("[red]✗ Failed to start workers. Running in single-process mode.[/red]")
        
        # Demo with sample data (since we don't have actual image)
        demo_input = {
            "image_path": "demo_face.jpg",
            "demo_mode": True
        }
        
        console.print("[cyan]📸 Processing demo image with face processing pipeline...[/cyan]")
        console.print()
        
        # Execute the demo
        result = pipeline_executor.execute_face_processing_pipeline(demo_input)
        
        if result["status"] == "completed":
            console.print("[green]✅ Demo completed successfully![/green]")
            console.print()
            
            # Display demo results
            demo_results = result.get("result", {})
            faces = demo_results.get("faces", [])
            
            console.print(f"[bold cyan]📊 Demo Results Summary:[/bold cyan]")
            console.print(f"   • Faces detected: {len(faces)}")
            console.print(f"   • Faces with attributes: {demo_results.get('processing_summary', {}).get('faces_with_attributes', 0)}")
            console.print(f"   • Faces with features: {demo_results.get('processing_summary', {}).get('faces_with_features', 0)}")
            console.print()
            
            # Show pipeline execution flow
            execution_summary = result.get("execution_summary", {})
            console.print(f"[bold yellow]⚙️ Pipeline Execution:[/bold yellow]")
            console.print(f"   • Total tasks: {execution_summary.get('total_tasks_executed', 0)}")
            console.print(f"   • Successful: {execution_summary.get('successful_tasks', 0)}")
            console.print(f"   • Failed: {execution_summary.get('failed_tasks', 0)}")
            console.print(f"   • Stages: {execution_summary.get('stages_completed', 0)}")
            console.print()
            
            console.print("[green]🎉 Face processing pipeline demo completed![/green]")
            console.print("[yellow]This demo shows the multi-worker pipeline in action:[/yellow]")
            console.print("   1. Face Detection → finds faces in image")
            console.print("   2. Parallel Processing:")
            console.print("      • Face Attribute Analysis (age, gender, emotion)")
            console.print("      • Face Feature Extraction (128D embeddings)")
            console.print("   3. Result Aggregation → combined face analysis")
            console.print()
            
        else:
            console.print(f"[red]Demo failed: {result.get('error')}[/red]")
            
    except Exception as e:
        console.print(f"[red]Demo execution failed: {e}[/red]")


if __name__ == '__main__':
    cli()