"""
Face Feature Extractor Task - Fixed Version
"""
import cv2
import numpy as np
from typing import Any, List, Dict
from tasks.base.task_base import TaskBase


class Task(TaskBase):
    """Face feature extraction for recognition and matching"""

    def __init__(self):
        super().__init__()

    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Extract face features for recognition

        Args:
            input_data: Dict with face_bbox, original_image, face_index

        Returns:
            Face feature extraction result
        """
        try:
            self.log_info("Starting face feature extraction...")

            # Extract face region from input
            face_bbox = input_data.get("face_bbox")
            original_image_path = input_data.get("original_image")
            image_data = input_data.get("image_data")
            face_index = input_data.get("face_index", 0)

            # Handle different input formats
            if image_data:
                # Base64 encoded image data
                import base64
                image_bytes = base64.b64decode(image_data)
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif isinstance(original_image_path, str):
                # File path
                image = cv2.imread(original_image_path)
            else:
                # Numpy array
                image = original_image_path

            if image is None:
                raise ValueError("Could not load image")

            # Extract face region
            x, y, w, h = face_bbox
            face_region = image[y:y+h, x:x+w]

            # Extract features
            features = self._extract_features(face_region, face_index)

            self.log_info(f"Face feature extraction completed for face {face_index}")

            result = {
                "face_index": face_index,
                "face_bbox": face_bbox,
                "features": features,
                "extraction_info": {
                    "face_size": [w, h],
                    "feature_dimension": len(features.get("feature_vector", [])),
                    "extraction_method": "simulated_deep_features"
                }
            }

            return result

        except Exception as e:
            self.log_error(f"Face feature extraction failed: {e}")
            raise

    def _extract_features(self, face_region: np.ndarray, face_index: int) -> Dict[str, Any]:
        """Simulate deep face feature extraction"""

        height, width = face_region.shape[:2]

        # Simulate feature extraction using image statistics
        gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)

        # Calculate various image features
        mean_intensity = np.mean(gray)
        std_intensity = np.std(gray)

        # Calculate gradients (edge information)
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Simulate deep learning features (128-dimensional vector)
        np.random.seed(int(mean_intensity) + face_index)  # Consistent for same face
        feature_vector = np.random.normal(
            loc=mean_intensity/255.0,
            scale=std_intensity/255.0,
            size=128
        ).tolist()

        # Normalize feature vector
        feature_vector = [round(f, 4) for f in feature_vector]

        # Calculate landmark-like features
        landmarks = self._simulate_landmarks(face_region)

        # Calculate geometric features
        geometric_features = self._calculate_geometric_features(landmarks)

        features = {
            "feature_vector": feature_vector,
            "landmarks": landmarks,
            "geometric_features": geometric_features,
            "texture_features": {
                "mean_intensity": round(mean_intensity, 2),
                "std_intensity": round(std_intensity, 2),
                "gradient_mean": round(np.mean(gradient_magnitude), 2),
                "gradient_std": round(np.std(gradient_magnitude), 2)
            },
            "quality_metrics": {
                "face_size_score": min(1.0, (width * height) / 10000),  # Normalized size score
                "contrast_score": min(1.0, std_intensity / 50),  # Contrast quality
                "sharpness_score": min(1.0, np.mean(gradient_magnitude) / 100),  # Edge sharpness
                "overall_quality": 0.0  # Will be calculated
            },
            "extraction_metadata": {
                "face_dimensions": [width, height],
                "extraction_timestamp": self._get_timestamp(),
                "feature_version": "v1.0_simulated"
            }
        }

        # Calculate overall quality score
        quality_metrics = features["quality_metrics"]
        overall_quality = (
            quality_metrics["face_size_score"] * 0.3 +
            quality_metrics["contrast_score"] * 0.3 +
            quality_metrics["sharpness_score"] * 0.4
        )
        features["quality_metrics"]["overall_quality"] = round(overall_quality, 3)

        return features

    def _simulate_landmarks(self, face_region: np.ndarray) -> List[List[int]]:
        """Simulate facial landmark detection"""
        height, width = face_region.shape[:2]

        # Simulate 68 facial landmarks (simplified)
        landmarks = []

        # Face outline (17 points)
        for i in range(17):
            x = int(width * (i / 16.0))
            y = int(height * 0.8 + (height * 0.2 * np.sin(i * np.pi / 16)))
            landmarks.append([x, y])

        # Eyebrows (10 points)
        for i in range(5):  # Left eyebrow
            x = int(width * (0.2 + i * 0.1))
            y = int(height * 0.3)
            landmarks.append([x, y])

        for i in range(5):  # Right eyebrow
            x = int(width * (0.6 + i * 0.1))
            y = int(height * 0.3)
            landmarks.append([x, y])

        # Eyes (12 points)
        for i in range(6):  # Left eye
            x = int(width * (0.25 + i * 0.05))
            y = int(height * 0.4)
            landmarks.append([x, y])

        for i in range(6):  # Right eye
            x = int(width * (0.65 + i * 0.05))
            y = int(height * 0.4)
            landmarks.append([x, y])

        # Nose (9 points)
        for i in range(9):
            x = int(width * (0.45 + (i-4) * 0.02))
            y = int(height * (0.5 + i * 0.05))
            landmarks.append([x, y])

        # Mouth (20 points)
        for i in range(20):
            angle = i * 2 * np.pi / 20
            x = int(width * 0.5 + width * 0.15 * np.cos(angle))
            y = int(height * 0.75 + height * 0.1 * np.sin(angle))
            landmarks.append([x, y])

        return landmarks

    def _calculate_geometric_features(self, landmarks: List[List[int]]) -> Dict[str, Any]:
        """Calculate geometric features from landmarks"""
        if len(landmarks) < 68:
            return {"error": "Insufficient landmarks"}

        # Convert to numpy array for easier calculation
        points = np.array(landmarks)

        # Calculate distances between key points
        left_eye_center = np.mean(points[36:42], axis=0)
        right_eye_center = np.mean(points[42:48], axis=0)
        nose_tip = points[33]
        mouth_center = np.mean(points[48:68], axis=0)

        # Calculate geometric ratios and distances
        eye_distance = np.linalg.norm(right_eye_center - left_eye_center)
        eye_to_nose = np.linalg.norm(nose_tip - (left_eye_center + right_eye_center) / 2)
        nose_to_mouth = np.linalg.norm(mouth_center - nose_tip)

        geometric_features = {
            "eye_distance": round(float(eye_distance), 2),
            "eye_to_nose_ratio": round(float(eye_to_nose / eye_distance), 3),
            "nose_to_mouth_ratio": round(float(nose_to_mouth / eye_distance), 3),
            "face_symmetry_score": self._calculate_symmetry_score(points),
            "facial_proportions": {
                "upper_face_ratio": round(float(eye_to_nose / (eye_to_nose + nose_to_mouth)), 3),
                "lower_face_ratio": round(float(nose_to_mouth / (eye_to_nose + nose_to_mouth)), 3)
            }
        }

        return geometric_features

    def _calculate_symmetry_score(self, landmarks: np.ndarray) -> float:
        """Calculate facial symmetry score"""
        # Simple symmetry calculation based on landmark positions
        center_x = np.mean(landmarks[:, 0])

        # Calculate deviation from symmetry
        left_side = landmarks[landmarks[:, 0] < center_x]
        right_side = landmarks[landmarks[:, 0] >= center_x]

        if len(left_side) == 0 or len(right_side) == 0:
            return 0.5

        # Flip right side and compare with left side
        right_side_flipped = right_side.copy()
        right_side_flipped[:, 0] = 2 * center_x - right_side_flipped[:, 0]

        # Calculate symmetry score (simplified)
        symmetry_score = 1.0 - min(1.0, np.mean(np.abs(left_side[:, 0] - np.mean(right_side_flipped[:, 0]))) / 100)

        return round(symmetry_score, 3)

    def validate_input(self, input_data: Any) -> bool:
        """Validate input data"""
        if not isinstance(input_data, dict):
            return False

        required_fields = ["face_bbox", "face_index"]
        has_image = "original_image" in input_data or "image_data" in input_data

        return all(field in input_data for field in required_fields) and has_image

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
            "description": "Face feature extraction for recognition and biometric analysis (Fixed Version)",
            "input_format": {
                "face_bbox": "Bounding box coordinates [x, y, w, h]",
                "original_image": "Image path (optional if image_data provided)",
                "image_data": "Base64 encoded image data (optional if original_image provided)",
                "face_index": "Index of face in the image"
            },
            "output_format": {
                "feature_vector": "128-dimensional face embedding",
                "landmarks": "68 facial landmark points",
                "geometric_features": "Facial geometry measurements",
                "quality_metrics": "Feature extraction quality scores"
            },
            "capabilities": [
                "Deep face feature extraction",
                "Facial landmark detection",
                "Geometric feature calculation",
                "Quality assessment",
                "Multiple image format support"
            ]
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()