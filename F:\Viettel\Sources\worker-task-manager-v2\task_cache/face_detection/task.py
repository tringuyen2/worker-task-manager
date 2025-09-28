"""
Face Detection Task - Computer Vision Example
"""
import cv2
import numpy as np
from typing import Any, List, Dict
from tasks.base.task_base import TaskBase


class Task(TaskBase):
    """Face detection using OpenCV Haar Cascades"""
    
    def __init__(self):
        super().__init__()
        self.face_cascade = None
        self._is_setup = False
    
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Detect faces in image
        
        Args:
            input_data: Input image data
            
        Returns:
            Face detection results
        """
        try:
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError("Input validation failed")
            
            # Setup if needed
            if not self._is_setup:
                self.setup()
                self._is_setup = True
            
            self.log_info("Starting face detection...")
            
            # Preprocess input
            image = self._preprocess_input(input_data)
            
            # Detect faces
            faces = self._detect_faces(image)
            
            # Postprocess results
            result = self._postprocess_output(faces, image.shape)
            
            self.log_info(f"Face detection completed - found {len(faces)} faces")
            
            return result
            
        except Exception as e:
            self.log_error(f"Face detection failed: {e}")
            raise
        finally:
            # Cleanup if needed
            try:
                self.cleanup()
            except Exception as e:
                self.log_warning(f"Cleanup failed: {e}")
    
    def setup(self):
        """Setup face detection model"""
        try:
            self.log_info("Loading Haar Cascade face detection model...")
            
            # Load pre-trained Haar cascade for face detection
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            if self.face_cascade.empty():
                raise RuntimeError("Failed to load Haar cascade classifier")
            
            self._is_setup = True
            self.log_info("Face detection model loaded successfully")
            
        except Exception as e:
            self.log_error(f"Failed to setup face detection: {e}")
            raise
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.face_cascade is not None:
                self.face_cascade = None
                self._is_setup = False
                self.log_info("Face detection resources cleaned up")
        except Exception as e:
            self.log_warning(f"Failed to cleanup: {e}")
    
    def _preprocess_input(self, input_data: Any) -> np.ndarray:
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
        
        elif isinstance(input_data, dict) and input_data.get("demo_mode"):
            # Create a demo image with simulated faces
            image = self._create_demo_image()
        
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
    
    def _create_demo_image(self) -> np.ndarray:
        """Create a demo image with simulated face regions for testing"""
        # Create a 640x480 demo image
        height, width = 480, 640
        image = np.random.randint(50, 200, (height, width, 3), dtype=np.uint8)
        
        # Add some face-like rectangular regions
        face_regions = [
            (150, 100, 120, 150),  # x, y, w, h
            (400, 200, 100, 120),
            (250, 300, 110, 130)
        ]
        
        for x, y, w, h in face_regions:
            # Create face-like region with different color
            face_color = np.random.randint(120, 255, 3)
            image[y:y+h, x:x+w] = face_color
            
            # Add some facial features (eyes, nose, mouth simulation)
            eye_color = np.random.randint(50, 150, 3)
            # Left eye
            image[y+h//4:y+h//4+10, x+w//4:x+w//4+20] = eye_color
            # Right eye  
            image[y+h//4:y+h//4+10, x+3*w//4-20:x+3*w//4] = eye_color
            # Mouth
            image[y+3*h//4:y+3*h//4+8, x+w//3:x+2*w//3] = eye_color
        
        return image
    
    def _detect_faces(self, image: np.ndarray) -> List[List[int]]:
        """Detect faces in image"""
        if not self._is_setup or self.face_cascade is None:
            raise RuntimeError("Face cascade not loaded")
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Convert to list format
        face_list = []
        for (x, y, w, h) in faces:
            face_list.append([int(x), int(y), int(w), int(h)])
        
        return face_list
    
    def _postprocess_output(self, faces: List[List[int]], image_shape: tuple) -> Dict[str, Any]:
        """Postprocess detection results"""
        self.log_info("Postprocessing detection results...")
        
        # Convert faces to detailed format
        face_details = []
        for i, (x, y, w, h) in enumerate(faces):
            face_details.append({
                "face_id": i,
                "bbox": [x, y, w, h],
                "confidence": 1.0,  # Haar cascades don't provide confidence scores
                "center": [x + w//2, y + h//2],
                "area": w * h
            })
        
        result = {
            "task_id": self._task_id,
            "task_type": "face_detection",
            "timestamp": self._get_timestamp(),
            "faces": face_details,
            "face_count": len(faces),
            "image_size": [image_shape[1], image_shape[0]],  # [width, height]
            "summary": {
                "faces_detected": len(faces),
                "has_faces": len(faces) > 0,
                "detection_status": "success",
                "largest_face_area": max([f["area"] for f in face_details]) if face_details else 0
            },
            "detection_info": {
                "method": "opencv_haar_cascade",
                "model": "haarcascade_frontalface_default",
                "min_face_size": [30, 30],
                "scale_factor": 1.1,
                "min_neighbors": 5
            }
        }
        
        return result
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data"""
        if isinstance(input_data, str):
            # Check if file exists
            import os
            return os.path.exists(input_data)
        
        elif isinstance(input_data, dict):
            return ('image_path' in input_data or 
                   'image_data' in input_data or 
                   input_data.get('demo_mode', False))
        
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
                "Dict with 'image_path' or 'image_data' (base64)",
                "Dict with 'demo_mode': True for testing"
            ],
            "output_format": {
                "faces": "List of detected faces with bounding boxes and metadata",
                "face_count": "Number of faces detected",
                "image_size": "Original image dimensions [width, height]",
                "summary": "Detection summary with statistics"
            },
            "model_type": "OpenCV Haar Cascade",
            "supported_formats": ["jpg", "png", "bmp", "tiff"],
            "capabilities": [
                "Multi-face detection",
                "Bounding box localization", 
                "Face area calculation",
                "Detection confidence (simulated)",
                "Demo mode for testing"
            ]
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()