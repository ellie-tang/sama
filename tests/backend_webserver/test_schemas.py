from __future__ import annotations

import pytest

pytest.importorskip("pydantic")

from models.schemas import FaceInfo, FaceRecognitionResponse, HealthResponse, KnownFacesResponse


def test_face_recognition_response_defaults():
    payload = FaceRecognitionResponse(
        success=True,
        message="ok",
        timestamp="2026-03-18T12:00:00Z",
    )

    assert payload.person_name is None
    assert payload.faces_detected == 0
    assert payload.relationship is None


def test_known_faces_response_round_trips_face_entries():
    response = KnownFacesResponse(
        success=True,
        faces=[FaceInfo(face_id="face-1", name="Alice")],
        total_count=1,
        timestamp="2026-03-18T12:00:00Z",
    )

    assert response.total_count == 1
    assert response.faces[0].face_id == "face-1"
    assert response.faces[0].name == "Alice"


def test_health_response_requires_availability_flag():
    response = HealthResponse(
        status="healthy",
        timestamp="2026-03-18T12:00:00Z",
        face_recognition_available=True,
    )

    assert response.status == "healthy"
    assert response.face_recognition_available is True
