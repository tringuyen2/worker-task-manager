"""
Face Processing Pipeline - Detects faces and extracts attributes/features in parallel
"""
from typing import Any, Dict, List, Optional
from loguru import logger

from .models import BasePipeline, TaskStep, PipelineStage
from worker.task_registry import task_registry


class FaceProcessingPipeline(BasePipeline):
    """Face processing pipeline with parallel attribute and feature extraction"""

    def __init__(self):
        super().__init__(
            pipeline_id="face_processing_pipeline",
            name="Face Processing Pipeline",
            description="Detect faces and extract attributes/features in parallel"
        )

    def define_steps(self) -> List[TaskStep]:
        """Define the pipeline execution steps"""
        return [
            # Step 1: Face Detection (sequential)
            TaskStep(
                task_id="face_detection",
                input_data=None,  # Will be set at runtime
                timeout=30
            ),
            # Step 2: Face Attribute Analysis (parallel, depends on face_detection)
            TaskStep(
                task_id="face_attribute",
                input_data=None,  # Will be set at runtime
                depends_on=["face_detection"],
                parallel_group="face_analysis",
                timeout=15
            ),
            # Step 3: Face Feature Extraction (parallel, depends on face_detection)
            TaskStep(
                task_id="face_extractor",
                input_data=None,  # Will be set at runtime
                depends_on=["face_detection"],
                parallel_group="face_analysis",
                timeout=20
            )
        ]

    def validate_input(self, input_data: Any) -> bool:
        """Validate input data for face processing"""
        if isinstance(input_data, str):
            # File path provided
            import os
            return os.path.exists(input_data)
        elif isinstance(input_data, dict):
            # Dictionary with image_path or image_data
            return ('image_path' in input_data or 'image_data' in input_data)
        elif hasattr(input_data, 'shape'):
            # Numpy array
            return len(input_data.shape) == 3
        return False

    def process_results(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process and aggregate results from all steps"""
        try:
            # Extract results from each step
            detection_result = step_results.get("face_detection", {})
            attribute_results = step_results.get("face_attribute", [])
            feature_results = step_results.get("face_extractor", [])

            # Handle single results vs lists
            if not isinstance(attribute_results, list):
                attribute_results = [attribute_results] if attribute_results else []
            if not isinstance(feature_results, list):
                feature_results = [feature_results] if feature_results else []

            # Get detected faces from detection result
            detected_faces = []
            if isinstance(detection_result, dict):
                detected_faces = detection_result.get("faces", [])

            # Combine results
            final_faces = []
            for i, face in enumerate(detected_faces):
                face_info = {
                    "face_id": i,
                    "bbox": face.get("bbox"),
                    "confidence": face.get("confidence", 1.0),
                    "attributes": None,
                    "features": None
                }

                # Match attributes by face_index
                for attr_result in attribute_results:
                    if isinstance(attr_result, dict) and attr_result.get("face_index") == i:
                        face_info["attributes"] = attr_result.get("attributes")
                        break

                # Match features by face_index
                for feat_result in feature_results:
                    if isinstance(feat_result, dict) and feat_result.get("face_index") == i:
                        face_info["features"] = feat_result.get("features")
                        break

                final_faces.append(face_info)

            # Create processing summary
            processing_summary = {
                "total_faces_detected": len(final_faces),
                "faces_with_attributes": len([f for f in final_faces if f["attributes"]]),
                "faces_with_features": len([f for f in final_faces if f["features"]]),
            }

            return {
                "faces": final_faces,
                "processing_summary": processing_summary
            }

        except Exception as e:
            logger.error(f"Error processing pipeline results: {e}")
            return {
                "faces": [],
                "processing_summary": {
                    "total_faces_detected": 0,
                    "faces_with_attributes": 0,
                    "faces_with_features": 0
                },
                "error": str(e)
            }

    def prepare_step_input(self, step: TaskStep, input_data: Any,
                          step_results: Dict[str, Any]) -> Any:
        """Prepare input data for a specific step"""
        if step.task_id == "face_detection":
            # First step gets original input
            return input_data

        elif step.task_id in ["face_attribute", "face_extractor"]:
            # These steps need face regions from detection
            detection_result = step_results.get("face_detection", {})
            faces = detection_result.get("faces", []) if isinstance(detection_result, dict) else []

            # Get original image path
            original_image_path = None
            if isinstance(input_data, dict) and "image_path" in input_data:
                original_image_path = input_data["image_path"]
            elif isinstance(input_data, str):
                original_image_path = input_data
            else:
                raise ValueError("Could not determine image path for parallel processing")

            # Return list of face data for parallel processing
            face_inputs = []
            for i, face in enumerate(faces):
                face_input = {
                    "face_bbox": face.get("bbox"),
                    "original_image": original_image_path,  # Pass image path directly
                    "face_index": i
                }
                face_inputs.append(face_input)
                logger.info(f"Prepared input for {step.task_id} face {i} with image path: {original_image_path}")
                logger.info(f"Face input data keys: {list(face_input.keys())}")
                logger.info(f"Face input data: {face_input}")
                logger.info(f"Face input face_bbox: {face_input.get('face_bbox')}")
                logger.info(f"Face input original_image: {face_input.get('original_image')}")
                logger.info(f"Face input face_index: {face_input.get('face_index')}")

            return face_inputs

        return input_data

    def get_info(self) -> Dict[str, Any]:
        """Get pipeline information"""
        info = super().get_info()
        info.update({
            "input_formats": [
                "Image file path (string)",
                "Dict with 'image_path' or 'image_data'",
                "Numpy array (H, W, C)"
            ],
            "output_format": {
                "faces": "List of detected faces with attributes and features",
                "processing_summary": "Summary statistics"
            },
            "stages": [
                "Face Detection",
                "Parallel: Face Attribute Analysis + Feature Extraction",
                "Result Aggregation"
            ],
            "capabilities": [
                "Multi-face detection",
                "Age/gender/emotion analysis",
                "Face feature extraction",
                "Parallel processing"
            ]
        })
        return info