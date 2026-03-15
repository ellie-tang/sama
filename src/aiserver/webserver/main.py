import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from datetime import datetime

from utils.config import Config
from models.schemas import HealthResponse
from api.endpoints import router as api_router
from utils.error_handlers import (
    face_recognition_error_handler,
    file_validation_error_handler,
    service_unavailable_error_handler,
    configuration_error_handler,
    validation_error_handler,
    http_exception_handler,
    general_exception_handler
)
from utils.exceptions import (
    FaceRecognitionError,
    FileValidationError,
    ServiceUnavailableError,
    ConfigurationError
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Vuzix Blade II Face Recognition Server",
    description="REST API server for processing images from Vuzix Blade II Glass and performing face recognition",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(FaceRecognitionError, face_recognition_error_handler)
app.add_exception_handler(FileValidationError, file_validation_error_handler)
app.add_exception_handler(ServiceUnavailableError, service_unavailable_error_handler)
app.add_exception_handler(ConfigurationError, configuration_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(api_router, prefix=Config.API_PREFIX)

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Starting Vuzix Blade II Face Recognition Server")

    # Ensure directories exist
    Config.ensure_directories()
    logger.info(f"Upload directory: /home/ellie/dev/aiserver/LLM_Facial_Memory_System")
    logger.info(f"Face system directory: /home/ellie/dev/aiserver/LLM_Facial_Memory_System")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check if face recognition system is available
        face_recognition_available = Config.get_face_system_path().exists()

        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            face_recognition_available=face_recognition_available
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Vuzix Blade II Face Recognition Server",
        "version": "1.0.0",
        "timestamp": datetime.now()
    }

if __name__ == "__main__":
    logger.info(f"Starting server on {Config.HOST}:{Config.PORT}")
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower()
    )
