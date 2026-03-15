import sys
import os
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add the LLM_Facial_Memory_System to the path
current_dir = Path(__file__).parent.parent.parent
face_system_path = current_dir / "LLM_Facial_Memory_System"
sys.path.insert(0, str(face_system_path))

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    """Service to integrate with the existing LLM_Facial_Memory_System"""

    def __init__(self):
        self.face_manager = None
        self.initialization_lock = threading.Lock()
        self.is_initialized = False

    def _initialize_face_manager(self):
        """Initialize the FaceManager from the existing system"""
        if self.is_initialized:
            return

        with self.initialization_lock:
            if self.is_initialized:
                return

            try:
                # Change to the face system directory for proper initialization
                original_cwd = os.getcwd()
                os.chdir(face_system_path)

                # Import and initialize the FaceManager
                from app import FaceManager, ensure_csv_files_exist

                # Ensure the required files and directories exist
                ensure_csv_files_exist()

                # Initialize the face manager
                self.face_manager = FaceManager()
                self.is_initialized = True

                logger.info("FaceManager initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize FaceManager: {e}")
                raise
            finally:
                # Restore original working directory
                os.chdir(original_cwd)

    def process_image(self, image_path: str) -> Dict:
        """
        Process an image and return face recognition results

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing recognition results
        """
        if not self.is_initialized:
            self._initialize_face_manager()

        try:
            # Change to face system directory for processing
            original_cwd = os.getcwd()
            os.chdir(face_system_path)

            # Process the image using the existing FaceManager
            # Use auto_add_unknown=True for webserver to maintain compatibility
            detected_faces, unknown_embeddings = self.face_manager.process_image(image_path, auto_add_unknown=False)

            # Get information about detected faces
            faces_info = self.face_manager.get_active_faces_info()

            # Format the results
            result = {
                "success": True,
                "faces_detected": len(detected_faces),
                "faces_info": faces_info,
                "message": "Image processed successfully"
            }

            if faces_info:
                # Get the primary face (first detected)
                primary_face = faces_info[0]
                result.update({
                    "person_name": primary_face.get("name", "Unknown"),
                    "face_id": primary_face.get("id"),
                    "confidence": 0.8  # Placeholder - real confidence would come from the face system
                })

                # Determine relationship (this would need to be configured in your system)
                result["relationship"] = self._determine_relationship(primary_face.get("name", "Unknown"))
            else:
                result.update({
                    "person_name": None,
                    "relationship": None,
                    "confidence": None,
                    "message": "No faces detected in image"
                })

            return result

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return {
                "success": False,
                "faces_detected": 0,
                "message": f"Error processing image: {str(e)}",
                "person_name": None,
                "relationship": None,
                "confidence": None
            }
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def _determine_relationship(self, person_name: str) -> str:
        """
        Determine the relationship of the detected person to the glass owner
        This is a placeholder - you would customize this based on your requirements
        """
        # This could be enhanced to read from a configuration file or database
        relationships = {
            "Unknown": "Stranger",
            "John": "Friend",
            "Jane": "Colleague",
            "Bob": "Family",
            # Add more relationships as needed
        }

        return relationships.get(person_name, "Unknown")

    def get_known_faces(self) -> List[Dict]:
        """Get list of all known faces"""
        if not self.is_initialized:
            self._initialize_face_manager()

        try:
            original_cwd = os.getcwd()
            os.chdir(face_system_path)

            known_faces = []
            for face_id, face_data in self.face_manager.known_faces.items():
                known_faces.append({
                    "face_id": face_id,
                    "name": face_data.get("name", "Unknown"),
                    "last_seen": None  # This could be enhanced to track last seen timestamps
                })

            return known_faces

        except Exception as e:
            logger.error(f"Error getting known faces: {e}")
            return []
        finally:
            os.chdir(original_cwd)

    def is_available(self) -> bool:
        """Check if the face recognition service is available"""
        try:
            if not self.is_initialized:
                self._initialize_face_manager()
            return self.face_manager is not None
        except:
            return False


# Global instance
face_recognition_service = FaceRecognitionService()
