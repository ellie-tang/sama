from __future__ import annotations

import io
import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")

from fastapi.testclient import TestClient

from server.router import app


def test_ingest_endpoint_accepts_labelable_sample():
    client = TestClient(app)
    payload = {
        "conversation_id": "conv-test",
        "device_id": "blade2-demo",
        "captured_at": "2026-03-18T10:30:00Z",
        "utterances": [
            {
                "utterance_id": "u1",
                "source_file_name": "u1.wav",
                "start_ms": 0,
                "end_ms": 600,
                "transcript_hint": "tons of tv",
                "speaker_tag": "wearer",
            },
            {
                "utterance_id": "u2",
                "source_file_name": "u2.wav",
                "start_ms": 900,
                "end_ms": 1600,
                "transcript_hint": "do you mean turn off tv?",
                "speaker_tag": "partner",
            },
            {
                "utterance_id": "u3",
                "source_file_name": "u3.wav",
                "start_ms": 1800,
                "end_ms": 2200,
                "transcript_hint": "yes",
                "speaker_tag": "wearer",
            },
        ],
        "context_frames": [],
        "preferred_target_utterance_id": "u1",
        "metadata": {"device": "blade2"},
    }

    response = client.post(
        "/audio-training/ingest",
        data={"payload_json": json.dumps(payload)},
        files=[
            ("audio_files", ("u1.wav", io.BytesIO(b"RIFFu1"), "audio/wav")),
            ("audio_files", ("u2.wav", io.BytesIO(b"RIFFu2"), "audio/wav")),
            ("audio_files", ("u3.wav", io.BytesIO(b"RIFFu3"), "audio/wav")),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "saved"
    assert body["decision"]["canonical_label"] == "turn off tv"


def test_health_endpoint_reports_current_model_configuration():
    client = TestClient(app)

    response = client.get("/audio-training/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["whisper_model"] == "whisper-large-v3"
    assert body["qwen_model"] == "qwen3.5-9b"
