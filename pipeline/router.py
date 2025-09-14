"""
Pipeline Router for task chaining and parallel processing
"""
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from loguru import logger

from core.config.manager import get_config
from worker.task_registry import task_registry


@dataclass
class TaskResult:
    """Result from task execution"""
    task_id: str
    execution_id: str
    status: str
    result: Any
    error: Optional[str] = None


@dataclass
class PipelineExecution:
    """Pipeline execution state"""
    pipeline_id: str
    execution_id: str
    input_data: Any
    current_stage: str
    completed_tasks: Dict[str, TaskResult]
    pending_tasks: List[str]
    failed_tasks: List[str]
    final_result: Optional[Any] = None


class TaskRouter:
    """Router for managing task execution and data flow in pipelines"""
    
    def __init__(self):
        self.active_executions: Dict[str, PipelineExecution] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def submit_task_to_worker(self, task_id: str, input_data: Any, execution_id: Optional[str] = None) -> str:
        """Submit task to specific worker queue"""
        try:
            if not execution_id:
                execution_id = str(uuid.uuid4())
            
            # Submit task to dedicated worker
            result_execution_id = task_registry.submit_task(task_id, input_data)
            
            if result_execution_id:
                logger.info(f"Submitted task {task_id} to worker, execution_id: {result_execution_id}")
                return result_execution_id
            else:
                raise RuntimeError(f"Failed to submit task {task_id}")
                
        except Exception as e:
            logger.error(f"Failed to submit task {task_id} to worker: {e}")
            raise
    
    def execute_task_sync(self, task_id: str, input_data: Any) -> TaskResult:
        """Execute task synchronously and return result"""
        try:
            execution_id = str(uuid.uuid4())
            logger.info(f"Executing task {task_id} synchronously")
            
            # Load and execute task directly (bypass worker for demo)
            from core.task_loader.loader import task_loader
            task_instance = task_loader.load_task(task_id)
            
            if not task_instance:
                raise RuntimeError(f"Failed to load task: {task_id}")
            
            result = task_instance.process(input_data)
            
            return TaskResult(
                task_id=task_id,
                execution_id=execution_id,
                status="success",
                result=result
            )
            
        except Exception as e:
            logger.error(f"Task {task_id} execution failed: {e}")
            return TaskResult(
                task_id=task_id,
                execution_id=execution_id,
                status="failed",
                result=None,
                error=str(e)
            )
    
    def execute_tasks_parallel(self, task_data_pairs: List[Tuple[str, Any]]) -> List[TaskResult]:
        """Execute multiple tasks in parallel"""
        try:
            logger.info(f"Executing {len(task_data_pairs)} tasks in parallel")
            
            # Submit all tasks to thread pool
            future_to_task = {
                self.executor.submit(
                    self.execute_task_sync,
                    task_id,
                    input_data
                ): task_id 
                for task_id, input_data in task_data_pairs
            }
            
            results = []
            for future in as_completed(future_to_task):
                task_id = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Parallel task {task_id} completed: {result.status}")
                except Exception as e:
                    logger.error(f"Parallel task {task_id} failed: {e}")
                    results.append(TaskResult(
                        task_id=task_id,
                        execution_id=str(uuid.uuid4()),
                        status="failed",
                        result=None,
                        error=str(e)
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            return []
    
    def route_task_output(self, pipeline_config: Dict[str, Any], completed_task: str, output: Any) -> List[str]:
        """Determine next tasks based on pipeline routing configuration"""
        try:
            routing = pipeline_config.get('routing', {})
            next_tasks = routing.get(completed_task, [])
            
            logger.info(f"Task {completed_task} routes to: {next_tasks}")
            return next_tasks
            
        except Exception as e:
            logger.error(f"Failed to route task output for {completed_task}: {e}")
            return []
    
    def aggregate_results(self, task_results: List[TaskResult], aggregation_strategy: str = "combine") -> Any:
        """Aggregate results from multiple tasks"""
        try:
            if aggregation_strategy == "combine":
                # Combine all successful results
                combined_result = {
                    "aggregated_results": {},
                    "successful_tasks": [],
                    "failed_tasks": [],
                    "summary": {}
                }
                
                for result in task_results:
                    if result.status == "success":
                        combined_result["aggregated_results"][result.task_id] = result.result
                        combined_result["successful_tasks"].append(result.task_id)
                    else:
                        combined_result["failed_tasks"].append({
                            "task_id": result.task_id,
                            "error": result.error
                        })
                
                combined_result["summary"] = {
                    "total_tasks": len(task_results),
                    "successful_count": len(combined_result["successful_tasks"]),
                    "failed_count": len(combined_result["failed_tasks"]),
                    "success_rate": len(combined_result["successful_tasks"]) / len(task_results) * 100
                }
                
                return combined_result
                
            elif aggregation_strategy == "merge_faces":
                # Custom aggregation for face processing pipeline
                return self._aggregate_face_results(task_results)
            
            else:
                # Default: return all results as-is
                return [result.result for result in task_results if result.status == "success"]
                
        except Exception as e:
            logger.error(f"Failed to aggregate results: {e}")
            return {"error": f"Aggregation failed: {e}"}
    
    def _aggregate_face_results(self, task_results: List[TaskResult]) -> Dict[str, Any]:
        """Custom aggregation for face processing results"""
        try:
            face_data = {
                "faces": [],
                "processing_summary": {
                    "total_faces_detected": 0,
                    "faces_with_attributes": 0,
                    "faces_with_features": 0
                }
            }
            
            detection_result = None
            attribute_results = []
            feature_results = []
            
            # Separate results by task type
            for result in task_results:
                if result.status == "success":
                    if result.task_id == "face_detection":
                        detection_result = result.result
                    elif result.task_id == "face_attribute":
                        attribute_results.append(result.result)
                    elif result.task_id == "face_extractor":
                        feature_results.append(result.result)
            
            # Combine face detection with attributes and features
            if detection_result:
                detected_faces = detection_result.get("faces", [])
                face_data["processing_summary"]["total_faces_detected"] = len(detected_faces)
                
                for i, face in enumerate(detected_faces):
                    face_info = {
                        "face_id": i,
                        "bbox": face.get("bbox"),
                        "confidence": face.get("confidence", 1.0),
                        "attributes": None,
                        "features": None
                    }
                    
                    # Add attributes if available
                    if i < len(attribute_results):
                        face_info["attributes"] = attribute_results[i]
                        face_data["processing_summary"]["faces_with_attributes"] += 1
                    
                    # Add features if available
                    if i < len(feature_results):
                        face_info["features"] = feature_results[i]
                        face_data["processing_summary"]["faces_with_features"] += 1
                    
                    face_data["faces"].append(face_info)
            
            return face_data
            
        except Exception as e:
            logger.error(f"Failed to aggregate face results: {e}")
            return {"error": f"Face aggregation failed: {e}"}


class PipelineExecutor:
    """Execute complete pipelines with task routing"""
    
    def __init__(self):
        self.router = TaskRouter()
        self.config = get_config()
    
    def execute_face_processing_pipeline(self, input_data: Any) -> Dict[str, Any]:
        """Execute the face processing pipeline demo"""
        try:
            pipeline_id = "face_processing"
            execution_id = str(uuid.uuid4())
            
            logger.info(f"Starting face processing pipeline execution: {execution_id}")
            
            # Stage 1: Face Detection
            logger.info("Stage 1: Running face detection...")
            detection_result = self.router.execute_task_sync("face_detection", input_data)
            
            if detection_result.status != "success":
                return {
                    "pipeline_id": pipeline_id,
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": f"Face detection failed: {detection_result.error}",
                    "stage": "face_detection"
                }
            
            # Check if faces were detected
            faces = detection_result.result.get("faces", [])
            if not faces:
                return {
                    "pipeline_id": pipeline_id,
                    "execution_id": execution_id,
                    "status": "completed",
                    "result": {
                        "faces_detected": 0,
                        "message": "No faces detected in image"
                    }
                }
            
            logger.info(f"Detected {len(faces)} faces, proceeding to parallel processing...")
            
            # Stage 2: Parallel processing of face attributes and features
            parallel_tasks = []
            
            # For each detected face, run attribute analysis and feature extraction
            for i, face in enumerate(faces):
                # Extract the image path from input_data
                if isinstance(input_data, dict) and "image_path" in input_data:
                    image_source = input_data["image_path"]
                elif isinstance(input_data, str):
                    image_source = input_data
                else:
                    image_source = input_data

                face_region_data = {
                    "face_bbox": face.get("bbox"),
                    "original_image": image_source,
                    "face_index": i
                }
                
                # Add tasks for this face
                parallel_tasks.extend([
                    ("face_attribute", face_region_data),
                    ("face_extractor", face_region_data)
                ])
            
            logger.info(f"Stage 2: Running {len(parallel_tasks)} parallel tasks...")
            parallel_results = self.router.execute_tasks_parallel(parallel_tasks)
            
            # Stage 3: Aggregate all results
            logger.info("Stage 3: Aggregating results...")
            all_results = [detection_result] + parallel_results
            final_result = self.router.aggregate_results(all_results, "merge_faces")
            
            logger.info(f"Pipeline execution completed successfully")
            
            return {
                "pipeline_id": pipeline_id,
                "execution_id": execution_id,
                "status": "completed",
                "result": final_result,
                "execution_summary": {
                    "total_tasks_executed": len(all_results),
                    "successful_tasks": len([r for r in all_results if r.status == "success"]),
                    "failed_tasks": len([r for r in all_results if r.status == "failed"]),
                    "stages_completed": 3
                }
            }
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return {
                "pipeline_id": pipeline_id,
                "execution_id": execution_id,
                "status": "failed",
                "error": str(e)
            }


# Global instances
task_router = TaskRouter()
pipeline_executor = PipelineExecutor()