#!/usr/bin/env python3
"""
Pipeline CLI with Registry Support
Execute pipelines using the pipeline registry system
"""
import sys
import json
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.json import JSON
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.registry import pipeline_registry
from worker.task_registry import task_registry
from core.config.manager import get_config
from core.logging import get_logger

console = Console()


@click.group()
def cli():
    """Pipeline Registry CLI - Execute and manage custom pipelines"""
    pass


@cli.command()
def list():
    """List all registered pipelines"""
    try:
        # Register built-in pipelines
        pipeline_registry.register_builtin_pipelines()

        pipelines = pipeline_registry.list_pipelines()

        if not pipelines:
            console.print("[yellow]No pipelines registered[/yellow]")
            return

        table = Table(title="Registered Pipelines")
        table.add_column("Pipeline ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="white")
        table.add_column("Steps", justify="center")

        for pipeline_id in pipelines:
            info = pipeline_registry.get_pipeline_info(pipeline_id)
            if info:
                table.add_row(
                    pipeline_id,
                    info.get('name', 'N/A'),
                    info.get('description', 'N/A')[:50] + ('...' if len(info.get('description', '')) > 50 else ''),
                    str(info.get('steps', 0))
                )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing pipelines: {e}[/red]")


@cli.command()
@click.argument('pipeline_id')
def info(pipeline_id):
    """Get detailed information about a pipeline"""
    try:
        # Register built-in pipelines
        pipeline_registry.register_builtin_pipelines()

        info = pipeline_registry.get_pipeline_info(pipeline_id)

        if not info:
            console.print(f"[red]Pipeline not found: {pipeline_id}[/red]")
            return

        console.print(Panel.fit(JSON.from_data(info), title=f"Pipeline Info: {pipeline_id}"))

    except Exception as e:
        console.print(f"[red]Error getting pipeline info: {e}[/red]")


@cli.command()
@click.argument('pipeline_id')
@click.argument('input_data')
@click.option('--format', 'input_format', default='json',
              type=click.Choice(['json', 'file']),
              help='Input data format')
@click.option('--workers/--no-workers', default=False,
              help='Use Celery workers for execution')
def execute(pipeline_id, input_data, input_format, workers):
    """Execute a pipeline with input data"""
    try:
        # Register all pipelines (built-in + JSON)
        pipeline_registry.register_all_pipelines()

        if workers:
            task_registry.load_and_register_tasks()

        # Parse input data
        if input_format == 'json':
            try:
                parsed_input = json.loads(input_data)
            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON input: {e}[/red]")
                return
        else:
            # Treat as file path
            parsed_input = input_data

        console.print(f"[blue]Executing pipeline: {pipeline_id}[/blue]")
        console.print(f"[blue]Input: {parsed_input}[/blue]")

        # Execute pipeline with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Executing pipeline...", total=None)

            try:
                result = pipeline_registry.execute_pipeline(pipeline_id, parsed_input)
                progress.update(task, description="Pipeline completed")

                # Display results
                console.print("\n" + "="*50)
                console.print(f"[green]✓ Pipeline execution completed successfully[/green]")

                if result.results:
                    faces = result.results.get('faces', [])
                    summary = result.results.get('processing_summary', {})

                    console.print(f"[cyan]Processed {summary.get('total_faces_detected', 0)} faces[/cyan]")

                    # Create execution summary table
                    summary_table = Table(title="Execution Summary")
                    summary_table.add_column("Metric", style="cyan")
                    summary_table.add_column("Value", style="white")

                    summary_table.add_row("Execution Time", f"{result.execution_time:.2f}s")
                    summary_table.add_row("Status", result.status.value)
                    summary_table.add_row("Total Faces", str(summary.get('total_faces_detected', 0)))
                    summary_table.add_row("Faces with Attributes", str(summary.get('faces_with_attributes', 0)))
                    summary_table.add_row("Faces with Features", str(summary.get('faces_with_features', 0)))

                    console.print(summary_table)

                    # Show face details if available
                    if faces:
                        face_table = Table(title="Face Detection Results")
                        face_table.add_column("Face ID", justify="center")
                        face_table.add_column("Bounding Box", style="cyan")
                        face_table.add_column("Confidence", justify="center")
                        face_table.add_column("Has Attributes", justify="center")
                        face_table.add_column("Has Features", justify="center")

                        for face in faces:
                            bbox = face.get('bbox', [])
                            bbox_str = f"[{', '.join(map(str, bbox))}]" if bbox else "N/A"

                            face_table.add_row(
                                str(face.get('face_id', 'N/A')),
                                bbox_str,
                                f"{face.get('confidence', 0.0):.2f}",
                                "✓" if face.get('attributes') else "✗",
                                "✓" if face.get('features') else "✗"
                            )

                        console.print(face_table)

                # Show full result if requested
                console.print("\n[dim]Full Result:[/dim]")
                console.print(Panel(JSON.from_data(result.results), title="Pipeline Results"))

            except Exception as e:
                progress.update(task, description=f"Pipeline failed: {e}")
                console.print(f"[red]Failed to execute pipeline: {e}[/red]")
                return

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--json-config', type=str, help='Path to JSON pipeline configuration file')
@click.option('--builtin-only', is_flag=True, help='Register only built-in pipelines')
def register(json_config, builtin_only):
    """Register pipelines from JSON config or built-in pipelines"""
    try:
        if builtin_only:
            console.print("[blue]Registering built-in pipelines only...[/blue]")
            pipeline_registry.register_builtin_pipelines()
        elif json_config:
            console.print(f"[blue]Registering pipelines from: {json_config}[/blue]")
            count = pipeline_registry.register_json_pipelines(json_config)
            console.print(f"[green]Registered {count} pipelines from JSON config[/green]")
        else:
            console.print("[blue]Registering all pipelines (built-in + JSON)...[/blue]")
            total = pipeline_registry.register_all_pipelines(json_config)
            console.print(f"[green]Total registered: {total} pipelines[/green]")

        pipelines = pipeline_registry.list_pipelines()
        if pipelines:
            for pipeline_id in pipelines:
                console.print(f"  • {pipeline_id}")
        else:
            console.print("[yellow]No pipelines registered[/yellow]")

    except Exception as e:
        console.print(f"[red]Error registering pipelines: {e}[/red]")


@cli.command()
@click.option('--config-path', type=str, default='config_pipeline.json',
              help='Path to JSON pipeline configuration file')
def show_config(config_path):
    """Show pipeline configuration from JSON file"""
    try:
        from pipeline.json_loader import json_pipeline_loader

        if not json_pipeline_loader.load_config(config_path):
            console.print(f"[red]Failed to load config: {config_path}[/red]")
            return

        # Show global settings
        global_settings = json_pipeline_loader.get_global_settings()
        if global_settings:
            console.print(Panel.fit(JSON.from_data(global_settings), title="Global Settings"))

        # Show pipeline configs
        pipeline_configs = json_pipeline_loader.get_pipeline_configs()

        table = Table(title=f"Pipeline Configurations ({config_path})")
        table.add_column("Pipeline ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Enabled", justify="center")
        table.add_column("Steps", justify="center")
        table.add_column("Description", style="white")

        for pipeline_id, config in pipeline_configs.items():
            table.add_row(
                pipeline_id,
                config.get('name', 'N/A'),
                "✓" if config.get('enabled', True) else "✗",
                str(len(config.get('steps', []))),
                config.get('description', 'N/A')[:50] + ('...' if len(config.get('description', '')) > 50 else '')
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error showing config: {e}[/red]")


@cli.command()
def tasks():
    """List available tasks"""
    try:
        config = get_config().worker

        table = Table(title="Available Tasks")
        table.add_column("Task ID", style="cyan")
        table.add_column("Enabled", justify="center")
        table.add_column("Queue", style="green")
        table.add_column("Priority", justify="center")
        table.add_column("Timeout", justify="center")

        for task_id in config.active_tasks:
            task_config = config.task_configs.get(task_id)
            if task_config:
                table.add_row(
                    task_id,
                    "✓" if getattr(task_config, 'enabled', True) else "✗",
                    getattr(task_config, 'queue', 'default'),
                    str(getattr(task_config, 'priority', 5)),
                    f"{getattr(task_config, 'timeout', 300)}s"
                )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing tasks: {e}[/red]")


if __name__ == '__main__':
    cli()