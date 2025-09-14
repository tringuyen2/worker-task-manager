#!/usr/bin/env python3
"""
Pipeline Registration Walkthrough
Step-by-step demonstration of how pipeline registration works
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pipeline.models import BasePipeline, TaskStep
from pipeline.registry import pipeline_registry


def show_step_1_create_pipeline_class():
    """Step 1: Define a custom pipeline class"""
    print("\n" + "="*80)
    print("STEP 1: CREATE PIPELINE CLASS")
    print("="*80)

    print("Create a pipeline class that inherits from BasePipeline:")
    print("""
class FaceProcessingPipeline(BasePipeline):
    def __init__(self):
        super().__init__(
            pipeline_id="face_processing_pipeline",  # Unique identifier
            name="Face Processing Pipeline",         # Display name
            description="Detect faces and extract attributes/features in parallel"
        )

    def define_steps(self) -> List[TaskStep]:
        '''Define the pipeline execution steps'''
        return [
            # Step 1: Face Detection (runs first, sequential)
            TaskStep(
                task_id="face_detection",
                input_data=None,  # Set at runtime
                timeout=30
            ),
            # Step 2: Face Attribute Analysis (parallel, waits for face_detection)
            TaskStep(
                task_id="face_attribute",
                input_data=None,
                depends_on=["face_detection"],      # Wait for this task
                parallel_group="face_analysis",    # Group for parallel execution
                timeout=15
            ),
            # Step 3: Face Feature Extraction (parallel, waits for face_detection)
            TaskStep(
                task_id="face_extractor",
                input_data=None,
                depends_on=["face_detection"],      # Wait for this task
                parallel_group="face_analysis",    # Same group = runs in parallel
                timeout=20
            )
        ]
    """)


def show_step_2_pipeline_registration():
    """Step 2: Register the pipeline"""
    print("\n" + "="*80)
    print("STEP 2: REGISTER PIPELINE")
    print("="*80)

    print("Registration happens in pipeline_registry.register_builtin_pipelines():")
    print("""
def register_builtin_pipelines(self):
    # Create pipeline instance
    face_pipeline = FaceProcessingPipeline()

    # Register it
    self.register_pipeline(face_pipeline)

def register_pipeline(self, pipeline: BasePipeline) -> bool:
    try:
        # Store pipeline in registry dictionary
        self.registered_pipelines[pipeline.pipeline_id] = pipeline
        logger.info(f"Registered pipeline: {pipeline.pipeline_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to register pipeline {pipeline.pipeline_id}: {e}")
        return False
    """)

    # Demonstrate actual registration
    from pipeline.face_processing_pipeline import FaceProcessingPipeline

    print("\nActual registration:")
    face_pipeline = FaceProcessingPipeline()
    success = pipeline_registry.register_pipeline(face_pipeline)

    print(f"✓ Pipeline registered: {success}")
    print(f"✓ Pipeline ID: {face_pipeline.pipeline_id}")
    print(f"✓ Pipeline Name: {face_pipeline.name}")
    print(f"✓ Steps defined: {len(face_pipeline.define_steps())}")


def show_step_3_step_structure():
    """Step 3: Show step structure and dependencies"""
    print("\n" + "="*80)
    print("STEP 3: STEP STRUCTURE AND DEPENDENCIES")
    print("="*80)

    from pipeline.face_processing_pipeline import FaceProcessingPipeline

    face_pipeline = FaceProcessingPipeline()
    steps = face_pipeline.define_steps()

    print("Pipeline Steps:")
    for i, step in enumerate(steps, 1):
        print(f"\nStep {i}: {step.task_id}")
        print(f"  ├─ Timeout: {step.timeout}s")
        print(f"  ├─ Depends on: {step.depends_on or 'None (runs first)'}")
        print(f"  ├─ Parallel group: {step.parallel_group or 'None (sequential)'}")
        print(f"  └─ Input data: {'Dynamic (set at runtime)' if step.input_data is None else step.input_data}")

    print("\nExecution Flow:")
    print("┌─────────────────────┐")
    print("│   face_detection    │  ← Runs first (no dependencies)")
    print("└──────────┬──────────┘")
    print("           │")
    print("           ▼")
    print("┌─────────────────────┐    ┌─────────────────────┐")
    print("│   face_attribute    │    │   face_extractor    │  ← Run in parallel")
    print("│ (parallel_group:    │    │ (parallel_group:    │    (same group)")
    print("│  face_analysis)     │    │  face_analysis)     │")
    print("└─────────────────────┘    └─────────────────────┘")


def show_step_4_execution_process():
    """Step 4: Show how execution works"""
    print("\n" + "="*80)
    print("STEP 4: EXECUTION PROCESS")
    print("="*80)

    print("When execute_pipeline() is called:")
    print("""
1. Get pipeline from registry:
   pipeline = self.registered_pipelines.get(pipeline_id)

2. Validate input:
   if not pipeline.validate_input(input_data):
       raise ValueError("Pipeline input validation failed")

3. Get steps and execute in dependency order:
   steps = pipeline.define_steps()
   step_results = self._execute_steps(pipeline, steps, input_data, execution_id)

4. Process final results:
   final_result = pipeline.process_results(step_results)
    """)

    print("\nStep execution logic:")
    print("• Group steps by dependencies")
    print("• Execute ready steps (dependencies satisfied)")
    print("• Handle parallel groups (same parallel_group runs together)")
    print("• Collect results and pass to next steps")


def show_step_5_task_input_preparation():
    """Step 5: Show task input preparation"""
    print("\n" + "="*80)
    print("STEP 5: TASK INPUT PREPARATION")
    print("="*80)

    print("Each step gets input via prepare_step_input():")
    print("""
def prepare_step_input(self, step: TaskStep, input_data: Any, step_results: Dict[str, Any]) -> Any:
    if step.task_id == "face_detection":
        # First step gets original input
        return input_data  # {"image_path": "test.jpg"}

    elif step.task_id in ["face_attribute", "face_extractor"]:
        # These steps need face regions from detection
        detection_result = step_results.get("face_detection", {})
        faces = detection_result.get("faces", [])

        # Extract image source from input
        if isinstance(input_data, dict) and "image_path" in input_data:
            image_source = input_data["image_path"]  # "test.jpg"

        # Create face inputs for parallel processing
        face_inputs = []
        for i, face in enumerate(faces):
            face_inputs.append({
                "face_bbox": face.get("bbox"),      # [84, 24, 78, 78]
                "original_image": image_source,     # "test.jpg"
                "face_index": i                     # 0
            })

        return face_inputs  # List of face data for each detected face
    """)


def show_step_6_result_aggregation():
    """Step 6: Show result aggregation"""
    print("\n" + "="*80)
    print("STEP 6: RESULT AGGREGATION")
    print("="*80)

    print("Final results are processed via process_results():")
    print("""
def process_results(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
    # Extract results from each step
    detection_result = step_results.get("face_detection", {})
    attribute_results = step_results.get("face_attribute", [])
    feature_results = step_results.get("face_extractor", [])

    # Get detected faces
    detected_faces = detection_result.get("faces", [])

    # Combine results by face_index
    final_faces = []
    for i, face in enumerate(detected_faces):
        face_info = {
            "face_id": i,
            "bbox": face.get("bbox"),
            "confidence": face.get("confidence", 1.0),
            "attributes": None,  # Will be filled from attribute_results
            "features": None     # Will be filled from feature_results
        }

        # Match attributes and features by face_index
        for attr_result in attribute_results:
            if attr_result.get("face_index") == i:
                face_info["attributes"] = attr_result.get("attributes")

        for feat_result in feature_results:
            if feat_result.get("face_index") == i:
                face_info["features"] = feat_result.get("features")

        final_faces.append(face_info)

    return {
        "faces": final_faces,
        "processing_summary": {
            "total_faces_detected": len(final_faces),
            "faces_with_attributes": len([f for f in final_faces if f["attributes"]]),
            "faces_with_features": len([f for f in final_faces if f["features"]])
        }
    }
    """)


def show_complete_example():
    """Show complete registration and execution example"""
    print("\n" + "="*80)
    print("COMPLETE EXAMPLE: REGISTRATION TO EXECUTION")
    print("="*80)

    # Step 1: Register pipeline
    from pipeline.face_processing_pipeline import FaceProcessingPipeline
    pipeline_registry.register_builtin_pipelines()

    # Step 2: Show registered pipelines
    pipelines = pipeline_registry.list_pipelines()
    print(f"Registered pipelines: {pipelines}")

    # Step 3: Get pipeline info
    info = pipeline_registry.get_pipeline_info("face_processing_pipeline")
    print(f"\nPipeline Info:")
    print(f"  ├─ ID: {info.get('pipeline_id')}")
    print(f"  ├─ Name: {info.get('name')}")
    print(f"  ├─ Description: {info.get('description')}")
    print(f"  └─ Steps: {info.get('steps')}")

    # Step 4: Show step details
    pipeline = pipeline_registry.get_pipeline("face_processing_pipeline")
    steps = pipeline.define_steps()

    print(f"\nStep Execution Order:")
    sequential_steps = [s for s in steps if not s.parallel_group]
    parallel_groups = {}
    for s in steps:
        if s.parallel_group:
            if s.parallel_group not in parallel_groups:
                parallel_groups[s.parallel_group] = []
            parallel_groups[s.parallel_group].append(s)

    print(f"  1. Sequential: {[s.task_id for s in sequential_steps]}")
    for group, group_steps in parallel_groups.items():
        print(f"  2. Parallel group '{group}': {[s.task_id for s in group_steps]}")


def main():
    """Run the complete walkthrough"""
    print("PIPELINE REGISTRATION WALKTHROUGH")
    print("="*80)
    print("This shows how pipeline registration works step by step")

    show_step_1_create_pipeline_class()
    show_step_2_pipeline_registration()
    show_step_3_step_structure()
    show_step_4_execution_process()
    show_step_5_task_input_preparation()
    show_step_6_result_aggregation()
    show_complete_example()

    print("\n" + "="*80)
    print("WALKTHROUGH COMPLETED!")
    print("="*80)
    print("Key Points:")
    print("✓ Pipelines inherit from BasePipeline")
    print("✓ Steps define task_id, dependencies, and parallel groups")
    print("✓ Registration stores pipeline in registry dictionary")
    print("✓ Execution respects dependencies and runs parallel groups together")
    print("✓ Input preparation customizes data for each step")
    print("✓ Result aggregation combines outputs from all steps")


if __name__ == "__main__":
    main()