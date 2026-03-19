from __future__ import annotations

from pathlib import Path

import services.face_recognition_service as service_module
from services.face_recognition_service import FaceRecognitionService


class StubFaceManager:
    def __init__(self, detected_faces, active_faces, known_faces=None, error=None):
        self._detected_faces = detected_faces
        self._active_faces = active_faces
        self.known_faces = known_faces or {}
        self._error = error

    def process_image(self, image_path, auto_add_unknown=False):
        if self._error is not None:
            raise self._error
        return self._detected_faces, []

    def get_active_faces_info(self):
        return self._active_faces


def test_process_image_formats_primary_face(monkeypatch, tmp_path):
    monkeypatch.setattr(service_module, "face_system_path", tmp_path)
    tmp_path.mkdir(exist_ok=True)

    service = FaceRecognitionService()
    service.is_initialized = True
    service.face_manager = StubFaceManager(
        detected_faces=[object()],
        active_faces=[{"name": "John", "id": "face-1"}],
    )

    result = service.process_image(str(tmp_path / "image.jpg"))

    assert result["success"] is True
    assert result["faces_detected"] == 1
    assert result["person_name"] == "John"
    assert result["relationship"] == "Friend"
    assert result["confidence"] == 0.8


def test_process_image_handles_no_detected_faces(monkeypatch, tmp_path):
    monkeypatch.setattr(service_module, "face_system_path", tmp_path)
    tmp_path.mkdir(exist_ok=True)

    service = FaceRecognitionService()
    service.is_initialized = True
    service.face_manager = StubFaceManager(detected_faces=[], active_faces=[])

    result = service.process_image(str(tmp_path / "image.jpg"))

    assert result["success"] is True
    assert result["faces_detected"] == 0
    assert result["person_name"] is None
    assert result["relationship"] is None
    assert result["confidence"] is None
    assert result["message"] == "No faces detected in image"


def test_process_image_returns_failure_payload_on_exception(monkeypatch, tmp_path):
    monkeypatch.setattr(service_module, "face_system_path", tmp_path)
    tmp_path.mkdir(exist_ok=True)

    service = FaceRecognitionService()
    service.is_initialized = True
    service.face_manager = StubFaceManager(
        detected_faces=[],
        active_faces=[],
        error=RuntimeError("boom"),
    )

    result = service.process_image(str(tmp_path / "image.jpg"))

    assert result["success"] is False
    assert result["faces_detected"] == 0
    assert result["person_name"] is None
    assert result["relationship"] is None
    assert result["confidence"] is None
    assert "boom" in result["message"]


def test_get_known_faces_formats_face_manager_records(monkeypatch, tmp_path):
    monkeypatch.setattr(service_module, "face_system_path", tmp_path)
    tmp_path.mkdir(exist_ok=True)

    service = FaceRecognitionService()
    service.is_initialized = True
    service.face_manager = StubFaceManager(
        detected_faces=[],
        active_faces=[],
        known_faces={
            "face-1": {"name": "Alice"},
            "face-2": {"name": "Bob"},
        },
    )

    result = service.get_known_faces()

    assert result == [
        {"face_id": "face-1", "name": "Alice", "last_seen": None},
        {"face_id": "face-2", "name": "Bob", "last_seen": None},
    ]


def test_determine_relationship_falls_back_to_unknown():
    service = FaceRecognitionService()

    assert service._determine_relationship("John") == "Friend"
    assert service._determine_relationship("Unmapped Person") == "Unknown"
