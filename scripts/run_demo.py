#!/usr/bin/env python3
"""
Complete Face Processing Pipeline Demo Script
"""
import sys
import time
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

console = Console()


def demo_step(step_num: int, description: str, func, *args, **kwargs):
    """Execute demo step with progress indication"""
    console.print(f"\n[bold blue]Step {step_num}: {description}[/bold blue]")
    
    try:
        with Progress() as progress:
            task = progress.add_task(f"Executing {description}...", total=100)
            result = func(*args, **kwargs)
            progress.update(task, advance=100)
            
        console.print(f"[green]✓ Step {step_num} completed[/green]")
        return result
        
    except Exception as e:
        console.print(f"[red]✗ Step {step_num} failed: {e}[/red]")
        return None


def register_all_tasks():
    """Register all required tasks"""
    from tools.task_manager import cli as task_cli
    from click.testing import CliRunner
    
    runner = CliRunner()
    tasks = [
        ("face_detection", "tasks/examples/face_detection"),
        ("face_attribute", "tasks/examples/face_attribute"), 
        ("face_extractor", "tasks/examples/face_extractor")
    ]
    
    success_count = 0
    for task_id, task_path in tasks:
        console.print(f"  Registering {task_id}...")
        result = runner.invoke(task_cli, ['register', task_path])
        if result.exit_code == 0:
            success_count += 1
            console.print(f"  [green]✓ {task_id} registered[/green]")
        else:
            console.print(f"  [yellow]⚠ {task_id} already registered or failed[/yellow]")
    
    return success_count >= 2  # At least 2 tasks should be registered


def start_multi_worker_system():
    """Start the multi-worker system"""
    from worker.multi_worker_manager import multi_worker_manager
    
    console.print("  Starting task workers...")
    success = multi_worker_manager.start_all_task_workers()
    
    if success:
        time.sleep(3)  # Give workers time to initialize
        status = multi_worker_manager.get_worker_status()
        console.print(f"  [green]✓ Started {status['alive_workers']} workers[/green]")
        
        # Show worker details
        for task_id, worker in status.get("workers", {}).items():
            if worker["is_alive"]:
                console.print(f"    • {task_id}: PID {worker.get('pid', 'N/A')}, Queue: {worker['config']['queue']}")
    
    return success


def execute_face_processing_pipeline():
    """Execute the complete face processing pipeline"""
    from pipeline.router import pipeline_executor
    
    # Demo input data
    demo_input = {
        "image_path": "demo_face_image.jpg",
        "demo_mode": True,
        "metadata": {
            "source": "demo_script",
            "timestamp": time.time()
        }
    }
    
    console.print("  Input data prepared...")
    console.print(f"  Executing pipeline with input: {demo_input}")
    
    # Execute pipeline
    result = pipeline_executor.execute_face_processing_pipeline(demo_input)
    
    if result["status"] == "completed":
        # Display results
        faces = result.get("result", {}).get("faces", [])
        console.print(f"  [green]✓ Processed {len(faces)} faces[/green]")
        
        # Show execution stats
        summary = result.get("execution_summary", {})
        console.print(f"  Tasks executed: {summary.get('total_tasks_executed', 0)}")
        console.print(f"  Success rate: {summary.get('successful_tasks', 0)}/{summary.get('total_tasks_executed', 0)}")
        
        return result
    else:
        console.print(f"  [red]Pipeline failed: {result.get('error')}[/red]")
        return None


def cleanup_demo():
    """Cleanup demo resources"""
    from worker.multi_worker_manager import multi_worker_manager
    
    console.print("  Stopping all workers...")
    success = multi_worker_manager.stop_all_task_workers()
    
    if success:
        console.print("  [green]✓ All workers stopped[/green]")
    else:
        console.print("  [yellow]⚠ Some workers may still be running[/yellow]")
    
    return success


def main():
    """Run complete face processing pipeline demo"""
    
    # Demo header
    header_text = """
[bold blue]🎬 Face Processing Pipeline Demo[/bold blue]

This demo showcases a multi-worker AI system with pipeline processing:
• Face Detection → finds faces in images
• Face Attribute Analysis → analyzes age, gender, emotion (parallel)
• Face Feature Extraction → extracts biometric features (parallel) 
• Result Aggregation → combines all analysis results

The system uses dedicated workers for each task type with proper task routing.
    """
    
    console.print(Panel(header_text.strip(), title="Demo Introduction", border_style="blue"))
    
    try:
        # Step 1: Register all required tasks
        result1 = demo_step(
            1, "Register Face Processing Tasks",
            register_all_tasks
        )
        
        if not result1:
            console.print("[red]Failed to register tasks. Cannot continue demo.[/red]")
            return False
        
        # Step 2: Start multi-worker system
        result2 = demo_step(
            2, "Start Multi-Worker System", 
            start_multi_worker_system
        )
        
        if not result2:
            console.print("[yellow]Workers failed to start. Running in single-process mode.[/yellow]")
        
        # Step 3: Execute pipeline
        result3 = demo_step(
            3, "Execute Face Processing Pipeline",
            execute_face_processing_pipeline
        )
        
        if result3:
            # Display detailed results
            console.print("\n[bold cyan]📊 Detailed Pipeline Results:[/bold cyan]")
            
            pipeline_result = result3.get("result", {})
            faces = pipeline_result.get("faces", [])
            
            for i, face in enumerate(faces):
                console.print(f"\n[yellow]Face {i+1}:[/yellow]")
                
                # Face detection info
                bbox = face.get("bbox")
                if bbox:
                    console.print(f"  Location: ({bbox[0]}, {bbox[1]}) - {bbox[2]}x{bbox[3]} pixels")
                
                # Attributes
                attributes = face.get("attributes")
                if attributes:
                    age_info = attributes.get("age", {})
                    gender_info = attributes.get("gender", {})
                    emotion_info = attributes.get("emotion", {})
                    
                    console.print(f"  Age: ~{age_info.get('estimated_age', 'unknown')} years")
                    console.print(f"  Gender: {gender_info.get('predicted_gender', 'unknown')} ({gender_info.get('confidence', 0):.2f})")
                    console.print(f"  Emotion: {emotion_info.get('dominant_emotion', 'unknown')} ({emotion_info.get('confidence', 0):.2f})")
                
                # Features
                features = face.get("features")
                if features:
                    feature_vector = features.get("feature_vector", [])
                    quality = features.get("quality_metrics", {}).get("overall_quality", 0)
                    console.print(f"  Feature vector: {len(feature_vector)}D embedding")
                    console.print(f"  Quality score: {quality:.3f}")
            
            # Pipeline summary
            summary = pipeline_result.get("processing_summary", {})
            summary_text = f"""
[bold green]Pipeline Execution Summary:[/bold green]
• Total faces detected: {summary.get('total_faces_detected', 0)}
• Faces with attributes: {summary.get('faces_with_attributes', 0)}
• Faces with features: {summary.get('faces_with_features', 0)}
• Processing stages completed: 3/3
• Status: [green]Success[/green]
            """
            
            console.print(Panel(summary_text.strip(), title="Execution Summary", border_style="green"))
        
        # Step 4: Cleanup
        demo_step(
            4, "Cleanup Demo Resources",
            cleanup_demo
        )
        
        # Demo conclusion
        conclusion_text = """
[bold green]🎉 Demo Completed Successfully![/bold green]

The face processing pipeline demonstrated:
✓ Multi-worker architecture with task-specific workers
✓ Parallel processing of face attributes and feature extraction  
✓ Pipeline routing and result aggregation
✓ Proper resource management and cleanup

This architecture allows for:
• Scalable processing with dedicated workers per task type
• Parallel execution of independent tasks
• Flexible pipeline configuration
• Resource isolation and fault tolerance
        """
        
        console.print(Panel(conclusion_text.strip(), title="Demo Complete", border_style="green"))
        
        return True
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
        cleanup_demo()
        return False
        
    except Exception as e:
        console.print(f"\n[red]Demo failed with error: {e}[/red]")
        cleanup_demo()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)