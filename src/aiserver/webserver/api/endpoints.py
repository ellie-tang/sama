import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from models.schemas import (
    FaceRecognitionResponse,
    ErrorResponse,
    KnownFacesResponse,
    FaceInfo
)
from services.face_recognition_service import face_recognition_service
from utils.config import Config

logger = logging.getLogger(__name__)
router = APIRouter()


def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    if not file.filename:
        return False

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in Config.ALLOWED_EXTENSIONS:
        return False

    # Check file size
    if hasattr(file, 'size') and file.size > Config.MAX_FILE_SIZE:
        return False

    return True


async def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file and return the file path"""
    if not validate_image_file(file):
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_ext = Path(file.filename).suffix.lower()
    filename = f"vuzix_image_{timestamp}{file_ext}"
    file_path = Config.UPLOAD_DIR / filename

    try:
        # Save the file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved uploaded image: {filename}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Error saving file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")


def delete_file(file_path: Optional[str]) -> None:
    """Attempt to delete a temporary image file without raising."""
    if not file_path:
        return

    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.debug(f"Deleted uploaded image: {path.name}")
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"Failed to delete temporary file {file_path}: {e}")


@router.post("/process-image", response_model=FaceRecognitionResponse)
async def process_image(
    file: UploadFile = File(...)
):
    """
    Main endpoint for processing images from Vuzix Blade II Glass

    Receives an image, writes it to a temporary file for processing,
    performs face recognition, and removes the file immediately afterwards.
    """
    image_path: Optional[str] = None
    try:
        # Save the uploaded image so the legacy face manager can read it
        image_path = await save_uploaded_file(file)

        # Process the image with face recognition
        try:
            # Run face recognition in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                face_recognition_service.process_image,
                image_path
            )

            response = FaceRecognitionResponse(
                success=result["success"],
                person_name=result.get("person_name"),
                relationship=result.get("relationship"),
                confidence=result.get("confidence"),
                faces_detected=result.get("faces_detected", 0),
                message=result.get("message", "Image processed"),
                timestamp=datetime.now()
            )

            logger.info(f"Processed image {Path(image_path).name}: "
                       f"faces={response.faces_detected}, "
                       f"person={response.person_name}")

            return response

        except asyncio.TimeoutError:
            logger.error(f"Face recognition timeout for {image_path}")
            raise HTTPException(
                status_code=408,
                detail="Face recognition processing timeout"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing image: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during image processing"
        )
    finally:
        delete_file(image_path)


@router.get("/faces", response_model=KnownFacesResponse)
async def get_known_faces():
    """Get list of all known faces (optional management endpoint)"""
    try:
        known_faces = face_recognition_service.get_known_faces()

        face_info_list = [
            FaceInfo(
                face_id=face["face_id"],
                name=face["name"],
                last_seen=face.get("last_seen")
            )
            for face in known_faces
        ]

        return KnownFacesResponse(
            success=True,
            faces=face_info_list,
            total_count=len(face_info_list),
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error getting known faces: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve known faces"
        )


@router.get("/system-status")
async def get_system_status():
    """Get detailed system status"""
    try:
        face_recognition_available = face_recognition_service.is_available()

        return {
            "face_recognition_available": face_recognition_available,
            "upload_directory": str(Config.UPLOAD_DIR),
            "face_system_directory": str(Config.FACE_SYSTEM_DIR),
            "max_file_size": Config.MAX_FILE_SIZE,
            "allowed_extensions": list(Config.ALLOWED_EXTENSIONS),
            "timestamp": datetime.now()
        }

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get system status"
        )
