"""
JSON Pipeline Loader
Load and create pipeline instances from JSON configuration files
"""
import json
import os
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from loguru import logger

from .models import BasePipeline, TaskStep, CustomPipeline


class JSONPipelineLoader:
    """Load pipelines from JSON configuration"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config_pipeline.json"
        self.config_data: Dict[str, Any] = {}
        self.input_validators: Dict[str, Callable] = {}
        self.result_processors: Dict[str, Callable] = {}

    def load_config(self, config_path: Optional[str] = None) -> bool:
        """Load pipeline configuration from JSON file"""
        try:
            if config_path:
                self.config_path = config_path

            if not os.path.exists(self.config_path):
                logger.error(f"Pipeline config file not found: {self.config_path}")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)

            logger.info(f"Loaded pipeline config from: {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load pipeline config: {e}")
            return False

    def get_pipeline_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all pipeline configurations"""
        return self.config_data.get("pipelines", {})

    def get_enabled_pipelines(self) -> Dict[str, Dict[str, Any]]:
        """Get only enabled pipeline configurations"""
        all_pipelines = self.get_pipeline_configs()
        return {
            pipeline_id: config
            for pipeline_id, config in all_pipelines.items()
            if config.get("enabled", True)
        }

    def create_pipeline(self, pipeline_id: str) -> Optional[BasePipeline]:
        """Create a pipeline instance from configuration"""
        try:
            pipeline_configs = self.get_pipeline_configs()
            if pipeline_id not in pipeline_configs:
                logger.error(f"Pipeline config not found: {pipeline_id}")
                return None

            config = pipeline_configs[pipeline_id]

            # Check if pipeline is enabled
            if not config.get("enabled", True):
                logger.warning(f"Pipeline is disabled: {pipeline_id}")
                return None

            # Create task steps
            steps = self._create_steps(config.get("steps", []))

            # Create input validator
            input_validator = self._create_input_validator(config.get("input_validation", {}))

            # Create result processor
            result_processor = self._create_result_processor(pipeline_id, config.get("output_format", {}))

            # Create custom pipeline
            pipeline = CustomPipeline(
                pipeline_id=config["pipeline_id"],
                name=config.get("name", pipeline_id),
                description=config.get("description", ""),
                step_definitions=steps,
                input_validator=input_validator,
                result_processor=result_processor
            )

            # Add metadata
            pipeline.metadata = config.get("metadata", {})

            logger.info(f"Created pipeline: {pipeline_id} with {len(steps)} steps")
            return pipeline

        except Exception as e:
            logger.error(f"Failed to create pipeline {pipeline_id}: {e}")
            return None

    def create_all_enabled_pipelines(self) -> List[BasePipeline]:
        """Create all enabled pipeline instances"""
        pipelines = []
        enabled_configs = self.get_enabled_pipelines()

        for pipeline_id in enabled_configs:
            pipeline = self.create_pipeline(pipeline_id)
            if pipeline:
                pipelines.append(pipeline)

        logger.info(f"Created {len(pipelines)} pipelines from config")
        return pipelines

    def _create_steps(self, step_configs: List[Dict[str, Any]]) -> List[TaskStep]:
        """Create TaskStep instances from configuration"""
        steps = []

        for step_config in step_configs:
            step = TaskStep(
                task_id=step_config["task_id"],
                input_data=None,  # Set at runtime
                depends_on=step_config.get("depends_on"),
                parallel_group=step_config.get("parallel_group"),
                timeout=step_config.get("timeout"),
                retry_count=step_config.get("retry_count", 3)
            )
            steps.append(step)

        return steps

    def _create_input_validator(self, validation_config: Dict[str, Any]) -> Callable:
        """Create input validation function from configuration"""
        required_fields = validation_config.get("required_fields", [])
        optional_fields = validation_config.get("optional_fields", [])
        supported_formats = validation_config.get("supported_formats", [])

        def validate_input(input_data: Any) -> bool:
            try:
                # Handle string input (file path)
                if isinstance(input_data, str):
                    if "image_path" in required_fields:
                        # Check if file exists
                        return os.path.exists(input_data)
                    return True

                # Handle dictionary input
                elif isinstance(input_data, dict):
                    # Check required fields
                    for field in required_fields:
                        if field not in input_data:
                            return False

                    # Validate file formats if image_path is provided
                    if "image_path" in input_data and supported_formats:
                        file_ext = Path(input_data["image_path"]).suffix.lower().lstrip('.')
                        if file_ext not in supported_formats:
                            return False

                    return True

                # Handle numpy array
                elif hasattr(input_data, 'shape'):
                    return len(input_data.shape) >= 2

                return True

            except Exception as e:
                logger.error(f"Input validation error: {e}")
                return False

        return validate_input

    def _create_result_processor(self, pipeline_id: str, output_config: Dict[str, Any]) -> Callable:
        """Create result processing function from configuration"""

        def process_results(step_results: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # Handle face processing pipeline
                if "face" in pipeline_id.lower():
                    return self._process_face_results(step_results)

                # Handle text analysis pipeline
                elif "text" in pipeline_id.lower():
                    return self._process_text_results(step_results)

                # Default: return combined results
                else:
                    return self._process_default_results(step_results)

            except Exception as e:
                logger.error(f"Result processing error: {e}")
                return {"error": str(e), "step_results": step_results}

        return process_results

    def _process_face_results(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process face processing pipeline results"""
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

    def _process_text_results(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process text analysis pipeline results"""
        preprocessing_result = step_results.get("text_preprocessing", {})
        sentiment_result = step_results.get("text_sentiment", {})
        features_result = step_results.get("text_features", {})

        return {
            "preprocessing": preprocessing_result,
            "sentiment": sentiment_result,
            "features": features_result,
            "analysis_summary": {
                "has_preprocessing": bool(preprocessing_result),
                "has_sentiment": bool(sentiment_result),
                "has_features": bool(features_result)
            }
        }

    def _process_default_results(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
        """Default result processing"""
        return {
            "step_results": step_results,
            "summary": {
                "total_steps": len(step_results),
                "successful_steps": len([r for r in step_results.values() if r]),
                "failed_steps": len([r for r in step_results.values() if not r])
            }
        }

    def get_pipeline_info(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline information from config"""
        pipeline_configs = self.get_pipeline_configs()
        if pipeline_id in pipeline_configs:
            config = pipeline_configs[pipeline_id]

            return {
                "pipeline_id": pipeline_id,
                "name": config.get("name", pipeline_id),
                "description": config.get("description", ""),
                "enabled": config.get("enabled", True),
                "steps": len(config.get("steps", [])),
                "step_details": config.get("steps", []),
                "input_validation": config.get("input_validation", {}),
                "output_format": config.get("output_format", {}),
                "metadata": config.get("metadata", {})
            }

        return None

    def get_global_settings(self) -> Dict[str, Any]:
        """Get global pipeline settings"""
        return self.config_data.get("global_settings", {})

    def reload_config(self) -> bool:
        """Reload configuration from file"""
        return self.load_config()

    def validate_config(self) -> bool:
        """Validate pipeline configuration"""
        try:
            if not self.config_data:
                logger.error("No configuration loaded")
                return False

            # Check required top-level keys
            if "pipelines" not in self.config_data:
                logger.error("Missing 'pipelines' section in config")
                return False

            pipelines = self.config_data["pipelines"]

            # Validate each pipeline
            for pipeline_id, config in pipelines.items():
                if not self._validate_pipeline_config(pipeline_id, config):
                    return False

            logger.info("Pipeline configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Config validation error: {e}")
            return False

    def _validate_pipeline_config(self, pipeline_id: str, config: Dict[str, Any]) -> bool:
        """Validate individual pipeline configuration"""
        required_fields = ["pipeline_id", "name", "steps"]

        for field in required_fields:
            if field not in config:
                logger.error(f"Pipeline {pipeline_id} missing required field: {field}")
                return False

        # Validate steps
        steps = config.get("steps", [])
        if not isinstance(steps, list) or len(steps) == 0:
            logger.error(f"Pipeline {pipeline_id} must have at least one step")
            return False

        for i, step in enumerate(steps):
            if "task_id" not in step:
                logger.error(f"Pipeline {pipeline_id} step {i} missing task_id")
                return False

        return True


# Global JSON pipeline loader instance
json_pipeline_loader = JSONPipelineLoader()