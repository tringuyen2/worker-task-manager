#!/usr/bin/env python3
"""
Simple Pipeline Registration Demo - No special characters
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def show_registration_steps():
    print("PIPELINE REGISTRATION STEPS")
    print("="*50)

    print("\nSTEP 1: Create Pipeline Class")
    print("-" * 30)
    print("Create a class that inherits from BasePipeline:")
    print("- Define pipeline_id, name, description")
    print("- Implement define_steps() method")
    print("- Implement validate_input() method")
    print("- Implement process_results() method")

    print("\nSTEP 2: Define Steps with Dependencies")
    print("-" * 30)
    print("TaskStep structure:")
    print("- task_id: Which task to execute")
    print("- depends_on: List of tasks that must complete first")
    print("- parallel_group: Tasks in same group run in parallel")
    print("- timeout: Maximum execution time")

    print("\nFor face_processing_pipeline:")
    print("Step 1: face_detection (no dependencies)")
    print("Step 2: face_attribute (depends_on=['face_detection'], parallel_group='face_analysis')")
    print("Step 3: face_extractor (depends_on=['face_detection'], parallel_group='face_analysis')")

    print("\nSTEP 3: Register Pipeline")
    print("-" * 30)
    print("pipeline_registry.register_pipeline(pipeline_instance)")
    print("- Stores pipeline in registry dictionary")
    print("- Uses pipeline_id as key")
    print("- Logs registration success/failure")

    print("\nSTEP 4: Execution Flow")
    print("-" * 30)
    print("1. face_detection runs first (no dependencies)")
    print("2. face_attribute and face_extractor run in parallel")
    print("   (both depend on face_detection, same parallel_group)")
    print("3. Results are aggregated by process_results()")

def demonstrate_registration():
    print("\nACTUAL REGISTRATION DEMO")
    print("=" * 50)

    # Import and register
    from pipeline.registry import pipeline_registry
    from pipeline.face_processing_pipeline import FaceProcessingPipeline

    # Create pipeline instance
    face_pipeline = FaceProcessingPipeline()
    print(f"Created pipeline: {face_pipeline.pipeline_id}")
    print(f"Pipeline name: {face_pipeline.name}")

    # Show steps
    steps = face_pipeline.define_steps()
    print(f"Number of steps: {len(steps)}")

    for i, step in enumerate(steps, 1):
        print(f"\nStep {i}: {step.task_id}")
        print(f"  Depends on: {step.depends_on}")
        print(f"  Parallel group: {step.parallel_group}")
        print(f"  Timeout: {step.timeout}s")

    # Register pipeline
    success = pipeline_registry.register_pipeline(face_pipeline)
    print(f"\nRegistration successful: {success}")

    # Verify registration
    registered_pipelines = pipeline_registry.list_pipelines()
    print(f"Registered pipelines: {registered_pipelines}")

    # Get pipeline back from registry
    retrieved = pipeline_registry.get_pipeline("face_processing_pipeline")
    print(f"Retrieved from registry: {retrieved is not None}")
    print(f"Same instance: {retrieved is face_pipeline}")

def show_task_flow():
    print("\nTASK EXECUTION FLOW")
    print("=" * 50)

    print("Input: {'image_path': 'test.jpg'}")
    print("")
    print("STAGE 1 (Sequential):")
    print("  face_detection task")
    print("  Input: {'image_path': 'test.jpg'}")
    print("  Output: {'faces': [{'bbox': [84, 24, 78, 78], ...}], ...}")
    print("")
    print("STAGE 2 (Parallel - same parallel_group):")
    print("  face_attribute task              face_extractor task")
    print("  Input: {                         Input: {")
    print("    'face_bbox': [84, 24, 78, 78],    'face_bbox': [84, 24, 78, 78],")
    print("    'original_image': 'test.jpg',     'original_image': 'test.jpg',")
    print("    'face_index': 0                   'face_index': 0")
    print("  }                                }")
    print("  Output: attributes data          Output: features data")
    print("")
    print("STAGE 3 (Aggregation):")
    print("  Combine results by face_index")
    print("  Final output: {")
    print("    'faces': [{")
    print("      'face_id': 0,")
    print("      'bbox': [84, 24, 78, 78],")
    print("      'attributes': {...},")
    print("      'features': {...}")
    print("    }],")
    print("    'processing_summary': {...}")
    print("  }")

if __name__ == "__main__":
    show_registration_steps()
    demonstrate_registration()
    show_task_flow()