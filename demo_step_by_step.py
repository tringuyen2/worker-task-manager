#!/usr/bin/env python3
"""
Step-by-Step Demo for Worker Task Manager
Shows task registration, pipeline setup, and execution flow using JSON configurations.
"""

import json
import os
from pathlib import Path

def print_step(step_num, title):
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print(f"{'='*60}")

def print_substep(title):
    print(f"\n{'-'*40}")
    print(f"{title}")
    print(f"{'-'*40}")

def show_file_content(filename, description):
    """Display JSON file content with description."""
    print(f"\n📄 {description}")
    print(f"File: {filename}")

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = json.load(f)
        print("Status: ✅ EXISTS")
        print(f"Key fields: {list(content.keys())[:5]}...")
    else:
        print("Status: ❌ NOT FOUND")

def simulate_task_registration():
    """Simulate task registration process."""
    print_step(1, "REGISTER TASKS")

    tasks = [
        ("demo_face_detection_task.json", "Face Detection Task"),
        ("demo_face_attribute_task.json", "Face Attribute Task"),
        ("demo_face_extractor_task.json", "Face Extractor Task")
    ]

    print("In a production environment, you would run:")
    for filename, description in tasks:
        show_file_content(filename, description)
        task_name = filename.replace("_task.json", "").replace("demo_", "")
        print(f"Command: python -m tools.task_manager register {filename}")
        print(f"Result: {task_name} task registered with unique input/output IDs")

def simulate_task_verification():
    """Simulate task verification."""
    print_step(2, "VERIFY TASKS EXIST")

    print("Command: python -m tools.task_manager list")
    print("Expected output:")
    print("✅ demo_face_detection (input_001 → output_001)")
    print("✅ demo_face_attribute (input_002 ← output_001)")
    print("✅ demo_face_extractor (input_003 ← output_001)")

    print("\nCommand: python -m tools.task_manager info demo_face_detection")
    print("Expected output:")
    print("- Input ID: face_detection_input_001")
    print("- Output ID: face_detection_output_001")
    print("- Primary output: output_001_faces_array")

def simulate_pipeline_registration():
    """Simulate pipeline registration."""
    print_step(3, "REGISTER PIPELINE")

    show_file_content("demo_pipeline_config.json", "Pipeline Configuration")

    print("\nCommand: python -m tools.pipeline_cli_registry register --json-config demo_pipeline_config.json")
    print("Expected output:")
    print("✅ demo_face_processing_pipeline registered")
    print("✅ Data flow mapping configured:")
    print("   - output_001_faces_array → input_002_faces_array")
    print("   - output_001_faces_array → input_003_faces_array")

def simulate_pipeline_verification():
    """Simulate pipeline verification."""
    print_step(4, "VERIFY PIPELINE")

    print("Command: python -m tools.pipeline_cli_registry list")
    print("Expected output:")
    print("✅ demo_face_processing_pipeline (enabled)")
    print("   - 3 steps: face_detection → (face_attribute + face_extractor)")
    print("   - Parallel group: parallel_analysis")

    print("\nCommand: python -m tools.pipeline_cli_registry info demo_face_processing_pipeline")
    print("Expected output:")
    print("- Pipeline ID: demo_face_processing_pipeline")
    print("- Steps: 3 (1 sequential, 2 parallel)")
    print("- Data flow: Explicit ID mapping configured")

def simulate_pipeline_execution():
    """Simulate pipeline execution."""
    print_step(5, "EXECUTE PIPELINE")

    print("Command: python -m tools.pipeline_cli_registry execute demo_face_processing_pipeline '{\"image_path\": \"test.jpg\"}'")

    print("\n📋 Execution Flow:")
    print("1. Input Processing:")
    print("   - image_path → input_001_image_path")

    print("\n2. Step 1 - Face Detection:")
    print("   - Task: demo_face_detection")
    print("   - Input ID: face_detection_input_001")
    print("   - Output ID: face_detection_output_001")
    print("   - Primary output: output_001_faces_array")

    print("\n3. Step 2 & 3 - Parallel Processing:")
    print("   - Both tasks receive output_001_faces_array")
    print("   - Face Attribute: input_002_faces_array ← output_001_faces_array")
    print("   - Face Extractor: input_003_faces_array ← output_001_faces_array")

def show_expected_results():
    """Show expected execution results."""
    print_step(6, "EXPECTED RESULTS")

    result = {
        "pipeline_id": "demo_face_processing_pipeline",
        "execution_status": "completed",
        "total_time": "0.8s",
        "steps_completed": 3,
        "data_flow": {
            "step_1_output": "output_001_faces_array",
            "step_2_input": "input_002_faces_array (mapped from output_001)",
            "step_3_input": "input_003_faces_array (mapped from output_001)"
        },
        "final_output": {
            "faces": [
                {
                    "face_id": 0,
                    "detection": "from output_001",
                    "attributes": "from output_002",
                    "features": "from output_003"
                }
            ],
            "processing_summary": {
                "face_detection_time": "0.3s",
                "parallel_processing_time": "0.5s (face_attr + face_extr)",
                "total_speedup": "2x (vs sequential)"
            }
        }
    }

    print("Final Pipeline Output:")
    print(json.dumps(result, indent=2))

def show_data_flow_mapping():
    """Show the complete data flow mapping."""
    print_step(7, "DATA FLOW MAPPING SUMMARY")

    print("🔄 Complete ID-based Data Flow:")
    print("""
    Input: {"image_path": "test.jpg"}
        ↓ mapped to input_001_image_path

    ┌─────────────────────────────────────┐
    │ demo_face_detection                  │
    │ Input ID:  face_detection_input_001 │
    │ Output ID: face_detection_output_001│
    │ Key Output: output_001_faces_array  │
    └─────────────────────────────────────┘
        ↓ output_001_faces_array
        ├─────────────────────┬─────────────────────┐
        ↓                     ↓                     ↓
    ┌─────────────────┐   ┌─────────────────┐
    │ demo_face_attr  │   │ demo_face_extr  │
    │ Input: 002      │   │ Input: 003      │
    │ (maps from 001) │   │ (maps from 001) │
    │ Output: 002     │   │ Output: 003     │
    └─────────────────┘   └─────────────────┘
    """)

    print("✅ Key Achievements:")
    print("- Each task has unique input/output IDs")
    print("- Explicit field mapping: output_001_faces_array → input_002_faces_array")
    print("- Explicit field mapping: output_001_faces_array → input_003_faces_array")
    print("- Both parallel tasks receive the same source data")
    print("- Complete data lineage tracking")

def main():
    """Main demo function."""
    print("🚀 WORKER TASK MANAGER - STEP BY STEP DEMO")
    print("Demonstrating ID-based Data Flow Management")

    # Check if our demo files exist
    files_status = []
    demo_files = [
        "demo_face_detection_task.json",
        "demo_face_attribute_task.json",
        "demo_face_extractor_task.json",
        "demo_pipeline_config.json"
    ]

    print(f"\n📋 Demo Files Status:")
    for file in demo_files:
        exists = "✅" if os.path.exists(file) else "❌"
        files_status.append(exists == "✅")
        print(f"{exists} {file}")

    if all(files_status):
        print("✅ All demo configuration files are ready!")
    else:
        print("❌ Some demo files are missing. Please run the JSON generation script first.")
        return

    # Run demo steps
    simulate_task_registration()
    simulate_task_verification()
    simulate_pipeline_registration()
    simulate_pipeline_verification()
    simulate_pipeline_execution()
    show_expected_results()
    show_data_flow_mapping()

    print(f"\n{'='*60}")
    print("🎯 DEMO COMPLETE!")
    print("This demonstrates how to:")
    print("1. ✅ Register tasks with unique input/output IDs")
    print("2. ✅ Map data flow between tasks explicitly")
    print("3. ✅ Execute parallel tasks with shared inputs")
    print("4. ✅ Track data lineage through the pipeline")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()