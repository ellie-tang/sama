import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuration class for the web server"""

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # File upload settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

    # Directory paths
    BASE_DIR = Path(__file__).parent.parent.parent
    UPLOAD_DIR = BASE_DIR / "webserver" / "images" / "uploads"
    FACE_SYSTEM_DIR = BASE_DIR / "LLM_Facial_Memory_System"

    # Face recognition settings
    FACE_RECOGNITION_TIMEOUT: float = float(os.getenv("FACE_RECOGNITION_TIMEOUT", "30.0"))

    # API settings
    API_PREFIX: str = "/api"

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_face_system_path(cls) -> Path:
        """Get the path to the face recognition system"""
        return cls.FACE_SYSTEM_DIR