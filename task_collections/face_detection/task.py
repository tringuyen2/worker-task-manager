# tasks/face_detection/task.py
import cv2
import numpy as np
from typing import List, Any
import os
import sys
from abc import ABC, abstractmethod

# BaseTask class definition (copied to avoid import issues)
class BaseTask(ABC):
    """Base class cho tất cả AI tasks"""
    
    def __init__(self):
        self.task_name = self.__class__.__name__
        
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Xử lý input và trả về kết quả"""
        pass
    
    @abstractmethod
    def get_requirements(self) -> List[str]:
        """Trả về list các thư viện cần thiết"""
        pass
    
    def get_description(self) -> str:
        """Mô tả task"""
        return f"AI Task: {self.task_name}"

class FaceDetectionTask(BaseTask):
    """Face Detection using OpenCV"""
    
    def __init__(self):
        super().__init__()
        self.cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = None
        self._load_model()
    
    def _load_model(self):
        """Load face detection model"""
        try:
            self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
            print("Face detection model loaded successfully")
        except Exception as e:
            print(f"Error loading face detection model: {e}")
    
    def process(self, input_data: Any) -> Any:
        """
        Process input image and detect faces
        Args:
            input_data: Path to image file or image array
        Returns:
            List of face bounding boxes and processed image info
        """
        try:
            # Load image
            if isinstance(input_data, str):
                if not os.path.exists(input_data):
                    return {"error": f"Image file not found: {input_data}"}
                image = cv2.imread(input_data)
            else:
                image = input_data
            
            if image is None:
                return {"error": "Could not load image"}
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Draw rectangles around faces
            result_image = image.copy()
            face_info = []
            
            for (x, y, w, h) in faces:
                cv2.rectangle(result_image, (x, y), (x+w, y+h), (255, 0, 0), 2)
                face_info.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'confidence': 1.0  # Haar cascades don't provide confidence scores
                })
            
            # Save result image
            if isinstance(input_data, str):
                output_path = input_data.replace('.', '_faces.')
                cv2.imwrite(output_path, result_image)
                
                return {
                    'faces_detected': len(faces),
                    'faces': face_info,
                    'input_image': input_data,
                    'output_image': output_path,
                    'image_shape': image.shape
                }
            else:
                return {
                    'faces_detected': len(faces),
                    'faces': face_info,
                    'result_image': result_image,
                    'image_shape': image.shape
                }
                
        except Exception as e:
            return {"error": f"Face detection failed: {str(e)}"}
    
    def get_requirements(self) -> List[str]:
        """Return required packages"""
        return ['opencv-python', 'numpy']
    
    def get_description(self) -> str:
        """Task description"""
        return "Detect faces in images using OpenCV Haar Cascades"

# Test function
if __name__ == "__main__":
    task = FaceDetectionTask()
    
    # Test with sample image path
    test_image = "test_image.jpg"
    if os.path.exists(test_image):
        result = task.process(test_image)
        print("Face Detection Result:", result)
    else:
        print("Please provide a test image file named 'test_image.jpg'")