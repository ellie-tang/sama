"""
Minimal face recognition service for testing without insightface
This can be used to test the web server before installing the full face recognition system
"""

import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class MinimalFaceRecognitionService:
    """Minimal service for testing web server without full face recognition"""

    def __init__(self):
        self.is_initialized = True

    def process_image(self, image_path: str) -> Dict:
        """Mock image processing for testing"""
        logger.info(f"Processing image: {image_path}")

        # Mock response
        return {
            "success": True,
            "faces_detected": 1,
            "faces_info": [{"name": "Test Person", "id": "test-123"}],
            "message": "Mock processing successful",
            "person_name": "Test Person",
            "face_id": "test-123",
            "confidence": 0.95
        }

    def _determine_relationship(self, person_name: str) -> str:
        """Mock relationship determination"""
        return "Friend"

    def get_known_faces(self) -> List[Dict]:
        """Mock known faces list"""
        return [
            {
                "face_id": "test-123",
                "name": "Test Person",
                "last_seen": None
            }
        ]

    def is_available(self) -> bool:
        """Always available for testing"""
        return True

# Export the minimal service for testing
face_recognition_service = MinimalFaceRecognitionService()