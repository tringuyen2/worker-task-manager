#!/usr/bin/env python3
"""
Simple test script to verify the face processing pipeline works
"""
import json
from pipeline.registry import PipelineRegistry

def test_pipeline():
    registry = PipelineRegistry()

    # Register all pipelines
    registry.register_all_pipelines()

    # Test input
    input_data = {"image_path": "test.jpg"}

    print("Testing face_processing_pipeline...")
    print(f"Input: {input_data}")

    try:
        result = registry.execute_pipeline("face_processing_pipeline", input_data)
        print("\n" + "="*60)
        print("PIPELINE EXECUTION COMPLETED!")
        print("="*60)

        # Convert result to dict if it's a PipelineResult object
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
        elif hasattr(result, '__dict__'):
            result_dict = vars(result)
        else:
            result_dict = result

        # Log all detection output
        print("\nDETECTION RESULTS:")
        print("-" * 40)

        if isinstance(result_dict, dict):
            # Check if results are nested
            if "results" in result_dict:
                nested_results = result_dict["results"]
                if "faces" in nested_results:
                    faces = nested_results.get("faces", [])
                else:
                    faces = []
            elif "faces" in result_dict:
                faces = result_dict.get("faces", [])
            else:
                faces = []

            # Print faces data
            if faces:
                print(f"Total faces found: {len(faces)}")

                for i, face in enumerate(faces):
                    print(f"\nFACE #{i}:")
                    print(f"  * Face ID: {face.get('face_id', 'N/A')}")

                    # Format bounding box nicely
                    bbox = face.get('bbox', [])
                    if bbox and len(bbox) >= 4:
                        print(f"  * Bounding Box: [x={bbox[0]}, y={bbox[1]}, w={bbox[2]}, h={bbox[3]}]")
                    else:
                        print(f"  * Bounding Box: {bbox}")

                    print(f"  * Confidence: {face.get('confidence', 'N/A')}")
                    print(f"  * Has Attributes: {'YES' if face.get('attributes') else 'NO'}")
                    print(f"  * Has Features: {'YES' if face.get('features') else 'NO'}")

                    # Show attributes if available
                    if face.get('attributes'):
                        attrs = face['attributes']
                        print(f"  * Attributes:")
                        if 'age' in attrs:
                            print(f"    - Age: {attrs['age'].get('estimated_age', 'N/A')}")
                        if 'gender' in attrs:
                            print(f"    - Gender: {attrs['gender'].get('predicted_gender', 'N/A')}")
                        if 'emotion' in attrs:
                            print(f"    - Emotion: {attrs['emotion'].get('dominant_emotion', 'N/A')}")

                    # Show features if available
                    if face.get('features'):
                        features = face['features']
                        print(f"  * Features:")
                        if 'feature_vector' in features:
                            vec_len = len(features['feature_vector'])
                            print(f"    - Feature Vector: {vec_len}-dimensional")
                        if 'quality_metrics' in features:
                            quality = features['quality_metrics'].get('overall_quality', 'N/A')
                            print(f"    - Quality Score: {quality}")
            else:
                print("No faces data in results")

            # Print processing summary
            if "results" in result_dict and "processing_summary" in result_dict["results"]:
                summary = result_dict["results"]["processing_summary"]
            elif "processing_summary" in result_dict:
                summary = result_dict["processing_summary"]
            else:
                summary = None

            if summary:
                print(f"\nPROCESSING SUMMARY:")
                print("-" * 30)
                print(f"* Total faces detected: {summary.get('total_faces_detected', 0)}")
                print(f"* Faces with attributes: {summary.get('faces_with_attributes', 0)}")
                print(f"* Faces with features: {summary.get('faces_with_features', 0)}")

            # Print raw result structure for debugging
            print(f"\nRAW RESULT STRUCTURE:")
            print("-" * 30)
            def print_nested_keys(obj, prefix=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, (dict, list)):
                            print(f"{prefix}{key}: {type(value).__name__}")
                            if isinstance(value, dict):
                                print_nested_keys(value, prefix + "  ")
                            elif isinstance(value, list) and value and isinstance(value[0], dict):
                                print(f"{prefix}  [0]: {type(value[0]).__name__}")
                                print_nested_keys(value[0], prefix + "    ")
                        else:
                            print(f"{prefix}{key}: {value}")

            print_nested_keys(result_dict)
        else:
            print(f"Result type: {type(result_dict)}")
            print(f"Result: {result_dict}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_pipeline()
    if success:
        print("\nPipeline test completed successfully!")
    else:
        print("\nPipeline test failed!")