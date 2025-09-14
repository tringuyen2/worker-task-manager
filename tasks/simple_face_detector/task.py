"""
simple_face_detector - Simple AI Task
"""
from tasks.base.task_base import TaskBase
from typing import Any
import cv2
import numpy as np

class Task(TaskBase):
    def process(self, input_data):
        # Direct implementation without MLTask complexity
        if isinstance(input_data, str):
            image = cv2.imread(input_data)
        else:
            raise ValueError("Input must be image path")
            
        # Face detection logic
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        
        return {
            "faces": [{"bbox": [int(x), int(y), int(w), int(h)]} for x, y, w, h in faces],
            "face_count": len(faces)
        }
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data"""
        # TODO: Add input validation logic
        return input_data is not None
    
    def get_requirements(self) -> list:
        """Get required packages"""
        return []
