from __future__ import annotations

from pathlib import Path


MAIN_PATH = Path("src/aiserver/webserver/main.py")


def test_main_registers_api_router():
    source = MAIN_PATH.read_text(encoding="utf-8")

    assert "app.include_router(api_router, prefix=Config.API_PREFIX)" in source


def test_main_exposes_health_endpoint():
    source = MAIN_PATH.read_text(encoding="utf-8")

    assert '@app.get("/health"' in source
    assert "face_recognition_available = Config.get_face_system_path().exists()" in source


def test_main_enables_cors_for_client_requests():
    source = MAIN_PATH.read_text(encoding="utf-8")

    assert "CORSMiddleware" in source
    assert 'allow_origins=["*"]' in source
