from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")

from api.endpoints import delete_file, save_uploaded_file, validate_image_file
from utils.config import Config


class DummyUploadFile:
    def __init__(self, filename: str, content: bytes, size: int | None = None):
        self.filename = filename
        self._content = content
        self.size = size if size is not None else len(content)

    async def read(self) -> bytes:
        return self._content


def test_validate_image_file_accepts_supported_extension():
    file = DummyUploadFile("person.jpg", b"image-bytes")

    assert validate_image_file(file) is True


def test_validate_image_file_rejects_unsupported_extension():
    file = DummyUploadFile("person.txt", b"not-an-image")

    assert validate_image_file(file) is False


def test_validate_image_file_rejects_oversized_payload(monkeypatch):
    monkeypatch.setattr(Config, "MAX_FILE_SIZE", 4)
    file = DummyUploadFile("person.jpg", b"12345", size=5)

    assert validate_image_file(file) is False


def test_save_uploaded_file_persists_upload(monkeypatch, tmp_path):
    monkeypatch.setattr(Config, "UPLOAD_DIR", tmp_path)
    file = DummyUploadFile("person.jpg", b"abc123")

    result = asyncio.run(save_uploaded_file(file))

    saved_path = Path(result)
    assert saved_path.exists()
    assert saved_path.parent == tmp_path
    assert saved_path.read_bytes() == b"abc123"


def test_delete_file_removes_existing_path(tmp_path):
    target = tmp_path / "temporary.jpg"
    target.write_bytes(b"123")

    delete_file(str(target))

    assert not target.exists()


def test_delete_file_ignores_missing_path(tmp_path):
    target = tmp_path / "missing.jpg"

    delete_file(str(target))

    assert not target.exists()
