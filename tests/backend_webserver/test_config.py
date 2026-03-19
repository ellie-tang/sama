from __future__ import annotations

from pathlib import Path

from utils.config import Config


def test_config_uses_expected_api_prefix():
    assert Config.API_PREFIX == "/api"


def test_config_allows_common_image_extensions():
    assert {".jpg", ".jpeg", ".png"}.issubset(Config.ALLOWED_EXTENSIONS)


def test_ensure_directories_creates_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "UPLOAD_DIR", tmp_path / "uploads")

    Config.ensure_directories()

    assert Config.UPLOAD_DIR.exists()
    assert Config.UPLOAD_DIR.is_dir()


def test_get_face_system_path_returns_configured_path(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "FACE_SYSTEM_DIR", tmp_path / "face-system")

    result = Config.get_face_system_path()

    assert result == tmp_path / "face-system"
