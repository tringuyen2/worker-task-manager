#!/usr/bin/env python3
"""
Test the FaceProcessingPipeline class directly to see input data
"""
from pipeline.face_processing_pipeline import FaceProcessingPipeline
from pipeline.models import TaskStep

def test_direct_pipeline():
    print("=== TESTING DIRECT PIPELINE CLASS ===")

    # Create the pipeline instance directly
    pipeline = FaceProcessingPipeline()
    print(f"Pipeline class: {pipeline.__class__.__name__}")
    print(f"Pipeline ID: {pipeline.pipeline_id}")

    # Test input
    input_data = {"image_path": "test.jpg"}
    print(f"Input data: {input_data}")

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
        print(f"Prepared input length: {len(prepared_input) if isinstance(prepared_input, list) else 'Not a list'}")
        print(f"Prepared input: {prepared_input}")

        if isinstance(prepared_input, list) and len(prepared_input) > 0:
            face_input = prepared_input[0]
            print(f"\n=== FIRST FACE INPUT DETAILS ===")
            print(f"  Type: {type(face_input)}")
            print(f"  Keys: {list(face_input.keys()) if isinstance(face_input, dict) else 'Not a dict'}")

            if isinstance(face_input, dict):
                print(f"  face_bbox: {face_input.get('face_bbox')}")
                print(f"  original_image: {face_input.get('original_image')}")
                print(f"  face_index: {face_input.get('face_index')}")

                # Check if original_image exists and is valid
                orig_img = face_input.get('original_image')
                if orig_img:
                    import os
                    print(f"  original_image exists as file: {os.path.exists(orig_img) if isinstance(orig_img, str) else 'Not a string path'}")

    except Exception as e:
        print(f"Error in prepare_step_input: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_pipeline()