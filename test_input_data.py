#!/usr/bin/env python3
"""
Test script to see what input data is being passed to parallel tasks
"""
import json
from pipeline.registry import PipelineRegistry

def test_input_data():
    registry = PipelineRegistry()
    registry.register_all_pipelines()

    # Test input
    input_data = {"image_path": "test.jpg"}

    print("=== TESTING PIPELINE INPUT DATA FLOW ===")
    print(f"Pipeline input: {input_data}")

    # Get the pipeline instance to test the input preparation
    pipeline = registry.get_pipeline("face_processing_pipeline")
    if pipeline:
        print(f"Pipeline found: {pipeline.__class__.__name__}")

        # Simulate face detection results
        fake_face_detection_result = {
            "faces": [
                {
                    "bbox": [84, 24, 78, 78],
                    "confidence": 1.0
                }
            ]
        }

        fake_step_results = {
            "face_detection": fake_face_detection_result
        }

        # Create mock task step for face_attribute
        from pipeline.models import TaskStep
        mock_step = TaskStep(
            task_id="face_attribute",
            input_data=None,
            depends_on=["face_detection"],
            parallel_group="face_analysis",
            timeout=15
        )

        print("\n=== TESTING prepare_step_input ===")
        try:
            prepared_input = pipeline.prepare_step_input(mock_step, input_data, fake_step_results)
            print(f"Prepared input type: {type(prepared_input)}")
            print(f"Prepared input: {prepared_input}")

            if isinstance(prepared_input, list) and len(prepared_input) > 0:
                face_input = prepared_input[0]
                print(f"\nFirst face input:")
                print(f"  Keys: {list(face_input.keys())}")
                print(f"  face_bbox: {face_input.get('face_bbox')}")
                print(f"  original_image: {face_input.get('original_image')}")
                print(f"  face_index: {face_input.get('face_index')}")

        except Exception as e:
            print(f"Error in prepare_step_input: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Pipeline not found!")

if __name__ == "__main__":
    test_input_data()