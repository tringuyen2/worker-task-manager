#!/usr/bin/env python3
"""
Simple Demo Script for Worker Task Manager
Shows the JSON configurations created for face processing tasks and pipeline.
"""

import json
import os
from pathlib import Path

def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_json_config(file_path, description):
    """Print JSON configuration in a formatted way."""
    if os.path.exists(file_path):
        print(f"\n📄 {description}")
        print(f"File: {file_path}")
        print("-" * 40)

        with open(file_path, 'r') as f:
            config = json.load(f)

        print(json.dumps(config, indent=2))
    else:
        print(f"❌ File not found: {file_path}")

def simulate_task_execution():
    """Simulate what the task execution would look like."""
    print_separator("SIMULATED TASK EXECUTION")

    # Simulate face detection
    print("🔍 Step 1: Face Detection")
    print("Input: {'image_path': 'test.jpg'}")
    simulated_face_detection = {
        "faces": [
            {
                "face_id": 0,
                "bbox": [120, 80, 180, 220],
                "confidence": 0.95,
                "center": [210, 190],
                "area": 39600
            }
        ],
        "face_count": 1,
        "image_size": [640, 480],
        "processing_time": 0.34,
        "summary": {
            "faces_detected": 1,
            "has_faces": True,
            "detection_status": "success"
        }
    }
    print("Output:", json.dumps(simulated_face_detection, indent=2))

    # Simulate face attribute analysis
    print("\n👤 Step 2: Face Attribute Analysis (Parallel)")
    print("Input: face detection results")
    simulated_attributes = {
        "faces": [
            {
                "face_id": 0,
                "bbox": [120, 80, 180, 220],
                "attributes": {
                    "age": 28,
                    "gender": "male",
                    "emotion": "happy",
                    "confidence": 0.89
                }
            }
        ],
        "processing_summary": {
            "total_faces_processed": 1,
            "successful_analyses": 1,
            "failed_analyses": 0,
            "processing_time": 0.22
        }
    }
    print("Output:", json.dumps(simulated_attributes, indent=2))

    # Simulate face feature extraction
    print("\n🧠 Step 3: Face Feature Extraction (Parallel)")
    print("Input: face detection results")
    simulated_features = {
        "faces": [
            {
                "face_id": 0,
                "bbox": [120, 80, 180, 220],
                "features": {
                    "feature_vector": [0.1, 0.2, 0.3, 0.4, 0.5, "... (512 dimensions)"],
                    "feature_dimension": 512,
                    "is_normalized": True,
                    "extraction_confidence": 0.92
                }
            }
        ],
        "processing_summary": {
            "total_faces_processed": 1,
            "successful_extractions": 1,
            "failed_extractions": 0,
            "average_feature_dimension": 512,
            "processing_time": 0.45
        }
    }
    print("Output:", json.dumps(simulated_features, indent=2))

def demo_pipeline_workflow():
    """Show the complete pipeline workflow."""
    print_separator("PIPELINE WORKFLOW DEMONSTRATION")

    print("🔄 Demo Face Processing Pipeline Workflow:")
    print("1. Input: {'image_path': 'test.jpg'}")
    print("2. Step 1: demo_face_detection → Face detection with bounding boxes")
    print("3. Step 2 & 3 (Parallel): demo_face_attribute + demo_face_extractor")
    print("4. Output: Combined results with detection + attributes + features")

    print("\n⚡ Parallel Execution Benefits:")
    print("- Face attribute analysis and feature extraction run simultaneously")
    print("- Expected speedup: ~2x faster than sequential execution")
    print("- Better resource utilization")

    print("\n📊 Expected Performance:")
    print("- Face detection: ~0.3-0.5s")
    print("- Face attributes: ~0.2-0.4s (parallel)")
    print("- Face features: ~0.4-0.6s (parallel)")
    print("- Total time: ~0.6-0.8s (vs ~1.0-1.5s sequential)")

def main():
    """Main demo function."""
    print_separator("WORKER TASK MANAGER DEMO")
    print("🚀 Demonstrating JSON-based Task and Pipeline Registration")

    # Show task configurations
    print_separator("TASK CONFIGURATIONS")

    print_json_config(
        "demo_face_detection_task.json",
        "Demo Face Detection Task Configuration"
    )

    print_json_config(
        "demo_face_attribute_task.json",
        "Demo Face Attribute Analysis Task Configuration"
    )

    print_json_config(
        "demo_face_extractor_task.json",
        "Demo Face Feature Extractor Task Configuration"
    )

    # Show pipeline configuration
    print_separator("PIPELINE CONFIGURATION")

    print_json_config(
        "demo_pipeline_config.json",
        "Demo Pipeline Configuration"
    )

    # Show workflow demonstration
    demo_pipeline_workflow()

    # Show simulated execution
    simulate_task_execution()

    # Final summary
    print_separator("DEMO SUMMARY")
    print("✅ Successfully created JSON configurations for:")
    print("   - demo_face_detection task")
    print("   - demo_face_attribute task")
    print("   - demo_face_extractor task")
    print("   - demo_face_processing_pipeline")
    print("   - demo_simple_face_pipeline")

    print("\n🔧 Key Features Demonstrated:")
    print("   - Detailed input/output schemas")
    print("   - Parallel task execution")
    print("   - Comprehensive metadata")
    print("   - Task dependencies")
    print("   - Queue management")
    print("   - Error handling and retries")

    print("\n📋 Files Created:")
    files = [
        "demo_face_detection_task.json",
        "demo_face_attribute_task.json",
        "demo_face_extractor_task.json",
        "demo_pipeline_config.json"
    ]

    for file in files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")

    print("\n🎯 Next Steps:")
    print("   1. Install required dependencies (celery, redis, etc.)")
    print("   2. Start MongoDB, Redis, and MinIO services")
    print("   3. Register tasks: python -m tools.task_manager register <task_dir>")
    print("   4. Register pipelines: python -m tools.pipeline_cli_registry register")
    print("   5. Execute pipeline: python -m tools.pipeline_cli_registry execute demo_face_processing_pipeline")

if __name__ == "__main__":
    main()