"""
Face Detection Task - Computer Vision Example
"""
import cv2
import numpy as np
from typing import Any, List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tasks.base.task_base import MLTask


class Task(MLTask):
    """Face detection using OpenCV Haar Cascades"""
    
    def __init__(self):
        super().__init__()
        self.face_cascade = None
    
    def load_model(self):
        """Load face detection model"""
        self.log_info("Loading Haar Cascade face detection model...")
        
        # Load pre-trained Haar cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load Haar cascade classifier")
        
        self.log_info("Face detection model loaded successfully")
        return self.face_cascade
    
    def predict(self, preprocessed_input: np.ndarray) -> Dict[str, Any]:
        """Detect faces in image - IMPLEMENT THIS METHOD"""
        self.log_info("Running face detection...")
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(preprocessed_input, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        self.log_info(f"Detected {len(faces)} faces")
        
        # Convert faces to list format
        face_list = []
        for (x, y, w, h) in faces:
            face_list.append({
                "bbox": [int(x), int(y), int(w), int(h)],
                "confidence": 1.0,
                "center": [int(x + w/2), int(y + h/2)]
            })
        
        return {
            "faces": face_list,
            "face_count": len(faces),
            "image_size": [preprocessed_input.shape[1], preprocessed_input.shape[0]]
        }
    
    def preprocess_input(self, input_data: Any) -> np.ndarray:
        """Preprocess input image"""
        self.log_info("Preprocessing input image...")
        
        if isinstance(input_data, str):
            # Load image from file path
            image = cv2.imread(input_data)
            if image is None:
                raise ValueError(f"Could not load image from path: {input_data}")
        
        elif isinstance(input_data, dict) and 'image_path' in input_data:
            # Load from dict with image_path
            image = cv2.imread(input_data['image_path'])
            if image is None:
                raise ValueError(f"Could not load image from path: {input_data['image_path']}")
        
        elif isinstance(input_data, dict) and 'image_data' in input_data:
            # Load from base64 or binary data
            import base64
            
            image_data = input_data['image_data']
            if isinstance(image_data, str):
                # Decode base64
                image_bytes = base64.b64decode(image_data)
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                # Assume numpy array
                image = np.array(image_data)
        
        elif isinstance(input_data, np.ndarray):
            image = input_data
        
        else:
            raise ValueError(
                "Input must be image path (str), numpy array, or dict with 'image_path'/'image_data'"
            )
        
        if image is None:
            raise ValueError("Failed to decode image")
        
        # Validate image dimensions
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError("Image must be a 3-channel (BGR) image")
        
        self.log_info(f"Image preprocessed: {image.shape}")
        return image
    
    def postprocess_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess detection results"""
        self.log_info("Postprocessing detection results...")
        
        # Add additional metadata
        result = {
            "task_id": self._task_id,
            "task_type": "face_detection",
            "timestamp": self._get_timestamp(),
            **output_data
        }
        
        # Add summary
        result["summary"] = {
            "faces_detected": output_data["face_count"],
            "has_faces": output_data["face_count"] > 0,
            "detection_status": "success"
        }
        
        return result
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data"""
        if isinstance(input_data, str):
            # Check if file exists
            import os
            return os.path.exists(input_data)
        
        elif isinstance(input_data, dict):
            return 'image_path' in input_data or 'image_data' in input_data
        
        elif isinstance(input_data, np.ndarray):
            return len(input_data.shape) == 3 and input_data.shape[2] == 3
        
        return False
    
    def get_requirements(self) -> List[str]:
        """Get required packages"""
        return [
            "opencv-python>=4.8.0",
            "numpy>=1.24.0"
        ]
    
    def get_info(self) -> Dict[str, Any]:
        """Get task information"""
        return {
            **super().get_info(),
            "description": "Face detection using OpenCV Haar Cascades",
            "input_formats": [
                "Image file path (string)",
                "Numpy array (H, W, C)",
                "Dict with 'image_path' or 'image_data' (base64)"
            ],
            "output_format": {
                "faces": "List of detected faces with bounding boxes",
                "face_count": "Number of faces detected",
                "image_size": "Original image dimensions [width, height]"
            },
            "model_type": "OpenCV Haar Cascade",
            "supported_formats": ["jpg", "png", "bmp", "tiff"]
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()