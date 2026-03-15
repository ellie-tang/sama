from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FaceRecognitionResponse(BaseModel):
    """Response model for face recognition results"""
    success: bool
    person_name: Optional[str] = None
    relationship: Optional[str] = None
    confidence: Optional[float] = None
    faces_detected: int = 0
    message: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    timestamp: datetime


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    face_recognition_available: bool


class FaceInfo(BaseModel):
    """Model for face information"""
    face_id: str
    name: str
    last_seen: Optional[datetime] = None


class KnownFacesResponse(BaseModel):
    """Response model for listing known faces"""
    success: bool
    faces: List[FaceInfo]
    total_count: int
    timestamp: datetime