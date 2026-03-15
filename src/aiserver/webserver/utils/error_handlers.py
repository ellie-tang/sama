"""Error handling utilities for the web server"""

import logging
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from models.schemas import ErrorResponse
from utils.exceptions import (
    FaceRecognitionError,
    FileValidationError,
    ServiceUnavailableError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


async def face_recognition_error_handler(request: Request, exc: FaceRecognitionError):
    """Handle face recognition errors"""
    logger.error(f"Face recognition error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=f"Face recognition failed: {str(exc)}",
            timestamp=datetime.now()
        ).dict()
    )


async def file_validation_error_handler(request: Request, exc: FileValidationError):
    """Handle file validation errors"""
    logger.warning(f"File validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=f"Invalid file: {str(exc)}",
            timestamp=datetime.now()
        ).dict()
    )


async def service_unavailable_error_handler(request: Request, exc: ServiceUnavailableError):
    """Handle service unavailable errors"""
    logger.error(f"Service unavailable: {exc}")
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error=f"Service unavailable: {str(exc)}",
            timestamp=datetime.now()
        ).dict()
    )


async def configuration_error_handler(request: Request, exc: ConfigurationError):
    """Handle configuration errors"""
    logger.error(f"Configuration error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=f"Configuration error: {str(exc)}",
            timestamp=datetime.now()
        ).dict()
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=f"Request validation failed: {str(exc)}",
            timestamp=datetime.now()
        ).dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            timestamp=datetime.now()
        ).dict()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            timestamp=datetime.now()
        ).dict()
    )